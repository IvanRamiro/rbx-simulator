-- The breakthrough as it is drawn in the world: what every client sees round a cultivator when they break through, and the clock
-- that times it. BreakthroughShow adds the player's own camera, screen, sound and title card on top of this for their own.
--
-- The timeline (seconds from the rank changing; Styles.Grades has each grade's beats):
--   gather   the world quiets: streams of Qi run in to the chest from every side, threads of light spiral in, rings collapse
--            on the ground, the realm's own signature builds (a core beating, belts of current, a black core growing ...) and a
--            light grows in the chest
--   build    (a realm or above) a column of light rises, rings climb the body
--   hold     a breath: everything slows to a fifth, the core is a pinpoint, the sound drops out
--   break    a flash, shockwaves roll across the ground and the sky, rays, shards and dust, the pillar surges, particles run in
--            slow motion for a beat (TimeScale), the realm's signature breaks
--   reveal   motes fall through the column, embers rise, the column stands over the cultivator
--   settle   everything thins out and ends; nothing is left behind (the whole effect is one folder, destroyed at the end)
-- Others see it shorter and lighter (grade.Near: no threads, no dimming, a quieter break) and only within the controller's reach.
--
--   BreakthroughFx.start(spec)  -> effect   spec: Parent (a Folder in the workspace), Character, Root, Info (Styles.describe), Own,
--                                           Calm (Reduced Effects), Low (the phone tier), and callbacks OnBreak, OnReveal, OnBeat(kind, power),
--                                           OnDone. Starts running at once on its own Heartbeat.
--   effect.t, effect.pace, effect.beats, effect.broke   read by BreakthroughShow
--   BreakthroughFx.skip(effect)   jump to the settle (the break's callbacks still run)
--   BreakthroughFx.stop(effect)   end now, everything destroyed
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Styles = require(script.Parent:WaitForChild("BreakthroughStyles"))

local Fx = {}
-- QA only: scales the clock and every emitter's TimeScale so a still can be taken inside an instant (Studio checks; 1 in the game)
Fx.TimeScale = 1

local T = Styles.Textures
local FULL = 2 * math.pi
local GROUND_REACH = 40

-- ---------- small helpers ----------
local function nseq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2], p[3] or 0))
    end
    return NumberSequence.new(keys)
end

local function cseq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, ColorSequenceKeypoint.new(p[1], p[2]))
    end
    return ColorSequence.new(keys)
end

local function clamp01(x)
    return math.clamp(x, 0, 1)
end

local function smooth(x)
    x = clamp01(x)
    return x * x * (3 - 2 * x)
end

local function outCubic(x)
    return 1 - (1 - clamp01(x)) ^ 3
end

local function ramp(t, a, b)
    return clamp01((t - a) / (b - a))
end

local function lerp(a, b, k)
    return a + (b - a) * k
end

-- the realm's hot-to-deep gradient, for particles and light
local function gradient(theme, a, b, c)
    return cseq({ { 0, a or theme.Hot }, { 0.45, b or theme.Main }, { 1, c or theme.Deep } })
end

local function lightOf(color)
    return color:Lerp(Color3.new(1, 1, 1), 0.55)
end

-- ---------- instances ----------
local function newPart(S, name, size)
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Transparency = 1
    part.Size = size or Vector3.new(0.2, 0.2, 0.2)
    part.Parent = S.folder
    return part
end

local function newEmitter(S, parent, props)
    local emitter = Instance.new("ParticleEmitter")
    emitter.Rate = 0
    emitter.LightInfluence = 0
    emitter.LightEmission = 1
    emitter.Texture = T.Glow
    emitter.Lifetime = NumberRange.new(1)
    emitter.Speed = NumberRange.new(0)
    emitter.Size = nseq({ { 0, 1 }, { 1, 1 } })
    emitter.Transparency = nseq({ { 0, 1 }, { 0.1, 0.1 }, { 0.8, 0.3 }, { 1, 1 } })
    emitter.Color = gradient(S.theme)
    for key, value in props do
        emitter[key] = value
    end
    emitter.Parent = parent
    table.insert(S.emitters, emitter)
    return emitter
end

-- a burst count, thinned on a phone and with Reduced Effects (never to nothing)
local function count(S, n)
    return math.max(1, math.floor(n * S.cut + 0.5))
end

local function newBeam(S, parent, a0, a1, props)
    local beam = Instance.new("Beam")
    beam.Attachment0 = a0
    beam.Attachment1 = a1
    beam.FaceCamera = true
    beam.LightInfluence = 0
    beam.LightEmission = 1
    beam.Segments = 8
    beam.Width0 = 0
    beam.Width1 = 0
    for key, value in props do
        beam[key] = value
    end
    beam.Parent = parent
    table.insert(S.beams, beam)
    return beam
end

local function newAttachment(parent, position)
    local attachment = Instance.new("Attachment")
    attachment.Position = position or Vector3.zero
    attachment.Parent = parent
    return attachment
end

-- a soft glow image that always faces the camera, sized in studs (the core's light, the flash, the Void's black core)
local function newGlow(S, name, color, image)
    local gui = Instance.new("BillboardGui")
    gui.Name = name
    gui.Adornee = S.core
    gui.Size = UDim2.fromScale(0.01, 0.01)
    gui.AlwaysOnTop = false
    gui.LightInfluence = 0
    gui.MaxDistance = 500
    gui.Active = false
    local label = Instance.new("ImageLabel")
    label.BackgroundTransparency = 1
    label.Size = UDim2.fromScale(1, 1)
    label.Image = image or T.Glow
    label.ImageColor3 = color
    label.ImageTransparency = 1
    label.Parent = gui
    gui.Parent = S.folder
    return { gui = gui, label = label }
end

local function setGlow(glow, studs, transparency)
    glow.gui.Size = UDim2.fromScale(studs, studs)
    glow.label.ImageTransparency = transparency
end

-- ---------- the timeline's machinery ----------
local function track(S, from, to, fn)
    table.insert(S.tracks, { from = from, to = to, fn = fn, done = false })
end

local function at(S, time, fn, essential)
    table.insert(S.events, { time = time, fn = fn, done = false, essential = essential })
end

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Exclude
groundParams.IgnoreWater = true

local function chestOf(S)
    local character = S.character
    local torso = character and (character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso"))
    return (torso or S.root).Position
end

local function refreshGround(S)
    local root = S.root
    groundParams.FilterDescendantsInstances = { S.character, S.parent }
    local hit = Workspace:Raycast(root.Position, Vector3.new(0, -GROUND_REACH, 0), groundParams)
    S.groundY = if hit then hit.Position.Y else root.Position.Y - 3
end

local function place(S)
    local chest = chestOf(S)
    local root = S.root.Position
    S.core.CFrame = CFrame.new(chest)
    S.ground.CFrame = CFrame.new(root.X, S.groundY + 0.15, root.Z)
    S.chest = chest
    S.base = Vector3.new(root.X, S.groundY, root.Z)
end

-- ---------- the layers ----------
-- the world's own light in the chest and the glow that grows there
local function buildLight(S)
    local theme = S.theme
    local light = Instance.new("PointLight")
    light.Color = lightOf(theme.Main)
    light.Brightness = 0
    light.Range = 12
    light.Shadows = false
    light.Parent = S.core
    S.light = light
    S.coreGlow = newGlow(S, "CoreGlow", theme.Hot:Lerp(Color3.new(1, 1, 1), 0.3))
    S.flare = newGlow(S, "Flare", Color3.new(1, 1, 1), T.Flare)
end

-- streams of Qi from every side into the chest: streaks born on a sphere and flying inward, thicker and faster as it builds
local function buildInflow(S)
    local grade, theme = S.grade, S.theme
    local radius = S.inflowRadius
    local draw = newPart(S, "Draw", Vector3.one * radius * 2)
    local emitter = newEmitter(S, draw, {
        Texture = T.Streak,
        Shape = Enum.ParticleEmitterShape.Sphere,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward,
        Orientation = Enum.ParticleOrientation.VelocityParallel,
        Lifetime = NumberRange.new(0.8, 0.95),
        Speed = NumberRange.new(radius * 1.1, radius * 1.3),
        Size = nseq({ { 0, 1 }, { 0.3, 3.6 * S.K, 1 }, { 1, 1 } }),
        Transparency = nseq({ { 0, 1 }, { 0.15, 0.15 }, { 0.8, 0.25 }, { 1, 1 } }),
        Color = cseq({ { 0, theme.Deep }, { 0.4, theme.Main }, { 1, theme.Hot } }),
    })
    S.draw = draw
    -- under the streaks, soft round motes of the same colour make them a body of light instead of hairlines
    local body = newEmitter(S, draw, {
        Texture = T.SoftGlow,
        Shape = Enum.ParticleEmitterShape.Sphere,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward,
        Lifetime = NumberRange.new(0.8, 1.0),
        Speed = NumberRange.new(radius * 1.0, radius * 1.2),
        Size = nseq({ { 0, 0.6 }, { 0.4, 2.4 * S.K, 0.6 }, { 1, 0.5 } }),
        Transparency = nseq({ { 0, 1 }, { 0.2, 0.5 }, { 0.85, 0.55 }, { 1, 1 } }),
        Color = cseq({ { 0, theme.Deep }, { 0.5, theme.Main }, { 1, theme.Hot } }),
    })
    local peak = math.min(S.maxRate, grade.Inflow * S.cut)
    local from, hold = 0.12 * S.B, S.B - S.H
    track(S, 0, S.B + 0.2, function(u, dt)
        local t = S.t
        local build = smooth(ramp(t, from, hold))
        local rate = if t >= S.B then 0 else peak * (0.15 + 0.85 * build) * (if t >= hold then 0.4 else 1)
        emitter.Rate = rate
        body.Rate = rate * 0.4
    end)
    S.inflowEmitter = emitter
end

-- threads of light that spiral in to the chest and start again, like water going down a drain made of light
local function buildThreads(S, countThreads)
    local theme = S.theme
    local world = S.world
    local list = {}
    for i = 1, countThreads do
        local top = newAttachment(world)
        local bottom = newAttachment(world)
        local trail = Instance.new("Trail")
        trail.Attachment0 = top
        trail.Attachment1 = bottom
        trail.Texture = T.SoftGlow
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.Lifetime = 0.5
        trail.MinLength = 0.05
        trail.FaceCamera = true
        trail.LightEmission = 1
        trail.LightInfluence = 0
        trail.Color = cseq({ { 0, theme.Hot }, { 0.4, theme.Main }, { 1, theme.Deep } })
        trail.Transparency = nseq({ { 0, 0.1 }, { 0.7, 0.45 }, { 1, 1 } })
        trail.WidthScale = nseq({ { 0, 1 }, { 1, 0 } })
        trail.Enabled = false
        trail.Parent = world
        table.insert(S.trails, trail)
        local seed = i / countThreads
        table.insert(list, {
            top = top, bottom = bottom, trail = trail, seed = seed, last = 1,
            tilt = (i % 2 == 0 and 1 or -1), lift = 2.5 + 3.5 * ((i * 7) % 5) / 4, gap = 0,
        })
    end
    local radius = S.inflowRadius * 0.85
    local hold = S.B - S.H
    track(S, 0.2 * S.B, S.B + 0.1, function(u, dt)
        local t = S.t
        local on = smooth(ramp(t, 0.2 * S.B, 0.5 * S.B))
        local fast = 1 + 1.6 * smooth(ramp(t, 0.4 * S.B, hold)) -- they quicken as it builds
        for _, th in list do
            local cycle = (t * 0.72 * fast + th.seed) % 1
            if cycle < th.last then
                th.trail.Enabled = false
                th.trail:Clear()
                th.gap = 2
            end
            th.last = cycle
            local k = (1 - cycle)
            local r = radius * k ^ 1.7 + 0.45
            local angle = th.seed * FULL + cycle * 4.4 * th.tilt + t * 0.9 * th.tilt
            local rise = th.lift * k ^ 1.3 - 0.4
            local centre = S.chest
            local position = centre + Vector3.new(math.cos(angle) * r, rise, math.sin(angle) * r)
            th.top.Position = position + Vector3.new(0, 0.28, 0)
            th.bottom.Position = position - Vector3.new(0, 0.28, 0)
            th.trail.Lifetime = 0.12 + 0.5 * on
            if th.gap > 0 then
                th.gap -= 1
            elseif t < S.B and on > 0.02 then
                th.trail.Enabled = true
            else
                th.trail.Enabled = false
            end
        end
    end)
    S.threadList = list
end

local function killThreads(S)
    for _, th in S.threadList or {} do
        th.trail.Enabled = false
    end
end

-- the column of light: a soft wide sheath and a bright core, from the ground to the sky; grows as it builds, surges at the break
local function buildPillar(S)
    local theme = S.theme
    local height = S.pillarHeight
    local bottom = newAttachment(S.ground)
    local top = newAttachment(S.ground, Vector3.new(0, height, 0))
    local haze = newBeam(S, S.ground, bottom, top, {
        Texture = T.HeavenHaze, TextureMode = Enum.TextureMode.Stretch, TextureSpeed = 0.15, Brightness = 1, ZOffset = 0.9,
        Color = cseq({ { 0, theme.Main }, { 1, theme.Deep } }),
        Transparency = nseq({ { 0, 0.55 }, { 0.5, 0.7 }, { 1, 1 } }), Segments = 10,
    })
    local core = newBeam(S, S.ground, bottom, top, {
        Texture = T.HeavenBeam, TextureMode = Enum.TextureMode.Stretch, TextureSpeed = 0.35, Brightness = 1.8, ZOffset = 1,
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
        Transparency = nseq({ { 0, 0.2 }, { 0.4, 0.45 }, { 0.85, 0.6 }, { 1, 1 } }), Segments = 10,
    })
    S.pillar = { haze = haze, core = core, top = top, wide = (if S.own then 14 else 11) * S.K, h = 0, w = 0 }
end

-- the shockwave emitters, made once: rings that lie on the ground or in the air (flat: velocity perpendicular, drifting up)
local function ringEmitter(S, parent, o)
    return newEmitter(S, parent, {
        Texture = T.Ring,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
        EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(o.rise or 0.02),
        SpreadAngle = Vector2.zero,
        Lifetime = NumberRange.new(o.life),
        Rotation = NumberRange.new(0, 360),
        Size = nseq({ { 0, o.from }, { 0.22, o.from + (o.to - o.from) * 0.62 }, { 1, o.to } }),
        Transparency = o.transparency or nseq({ { 0, 0.05 }, { 0.5, 0.35 }, { 1, 1 } }),
        Color = o.color or cseq({ { 0, S.theme.Hot }, { 1, S.theme.Main } }),
        ZOffset = o.z or 0,
    })
end

local function buildRings(S)
    local theme = S.theme
    local span = S.span
    local K = S.K
    local ground = S.ground
    local rings = {}
    -- collapsing, in the gather: a ring that closes in on the cultivator
    rings.Collapse = ringEmitter(S, ground, {
        life = 0.9, from = span * 0.55, to = 1.5,
        transparency = nseq({ { 0, 1 }, { 0.3, 0.45 }, { 0.85, 0.15 }, { 1, 1 } }),
        color = cseq({ { 0, theme.Deep }, { 1, theme.Hot } }),
    })
    rings.Collapse.Size = nseq({ { 0, span * 0.6 }, { 0.5, span * 0.28 }, { 1, 1.5 } })
    -- the break's, one after another: each its own colour, speed and size (never all one ring)
    local palette = S.ringColors
    rings.Hot = ringEmitter(S, ground, { life = 1.5, from = 3, to = span, color = palette[1] })
    rings.Main = ringEmitter(S, ground, { life = 1.9, from = 3, to = span * 1.25, color = palette[2], z = 0.1 })
    rings.Deep = ringEmitter(S, ground, {
        life = 2.4, from = 3, to = span * 1.6, color = palette[3],
        transparency = nseq({ { 0, 0.2 }, { 0.5, 0.55 }, { 1, 1 } }),
    })
    -- the light on the floor as the wave leaves: a flat soft disc that flashes and is gone
    rings.Disc = newEmitter(S, ground, {
        Texture = T.Glow, Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.02), SpreadAngle = Vector2.zero, Lifetime = NumberRange.new(0.9),
        Size = nseq({ { 0, span * 0.2 }, { 0.3, span * 0.9 }, { 1, span * 1.3 } }),
        Transparency = nseq({ { 0, 0.2 }, { 0.35, 0.6 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.25, theme.Hot }, { 1, theme.Main } }), ZOffset = -0.2,
    })
    -- rising through the body in the build: flat rings that climb from the feet past the head
    rings.Rise = ringEmitter(S, ground, {
        life = 1.1, from = 3.4 * K, to = 5.2 * K, rise = 15,
        transparency = nseq({ { 0, 1 }, { 0.2, 0.35 }, { 0.8, 0.5 }, { 1, 1 } }),
        color = cseq({ { 0, theme.Hot }, { 1, theme.Main } }),
    })
    -- across the sky: two wider rings in the air, higher and fainter
    if S.grade.Name ~= "Step" then
        local sky1 = newPart(S, "Sky1")
        local sky2 = newPart(S, "Sky2")
        S.sky = { sky1, sky2 }
        rings.Sky1 = ringEmitter(S, sky1, {
            life = 1.7, from = 4, to = span * 1.5, color = cseq({ { 0, theme.Hot }, { 1, theme.Main } }),
            transparency = nseq({ { 0, 0.15 }, { 0.5, 0.5 }, { 1, 1 } }),
        })
        rings.Sky2 = ringEmitter(S, sky2, {
            life = 2.1, from = 4, to = span * 1.9, color = cseq({ { 0, theme.Main }, { 1, theme.Deep } }),
            transparency = nseq({ { 0, 0.3 }, { 0.5, 0.6 }, { 1, 1 } }),
        })
    end
    -- a halo that faces the camera: the break's first sharp ring, in front of everything
    rings.Halo = newEmitter(S, S.core, {
        Texture = T.Ring,
        Lifetime = NumberRange.new(0.75),
        Size = nseq({ { 0, 2 }, { 0.2, span * 0.55 }, { 1, span * 0.9 } }),
        Transparency = nseq({ { 0, 0.05 }, { 0.4, 0.4 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
        ZOffset = 0.5,
    })
    S.rings = rings
end

-- the break's own particles: rays, shards, the flash on the core, dust along the ground, and the falling motes of the reveal
local function buildBurstEmitters(S)
    local theme, K = S.theme, S.K
    local core, ground = S.core, S.ground
    local burst = {}
    burst.Flash = newEmitter(S, core, {
        Lifetime = NumberRange.new(0.5), Size = nseq({ { 0, 6 * K }, { 0.2, 34 * K }, { 1, 50 * K } }),
        Transparency = nseq({ { 0, 0.1 }, { 0.3, 0.5 }, { 1, 1 } }), Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 1, theme.Hot } }),
    })
    burst.Rays = newEmitter(S, core, {
        Texture = T.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Lifetime = NumberRange.new(0.45, 0.8), Speed = NumberRange.new(60 * K, 120 * K), SpreadAngle = Vector2.new(180, 180),
        Drag = 2.2,
        Size = nseq({ { 0, 2 * K }, { 0.2, 11 * K }, { 1, 1.5 } }), Squash = nseq({ { 0, 1.5 }, { 1, 1.5 } }),
        Transparency = nseq({ { 0, 0.05 }, { 0.6, 0.35 }, { 1, 1 } }), Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
    })
    burst.Shards = newEmitter(S, core, {
        Texture = T.Spike, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Lifetime = NumberRange.new(0.8, 1.5), Speed = NumberRange.new(30 * K, 70 * K), SpreadAngle = Vector2.new(180, 180),
        Acceleration = Vector3.new(0, -34, 0), Drag = 1,
        Size = nseq({ { 0, 3.5 * K }, { 0.5, 2.6 * K }, { 1, 0.5 } }),
        Transparency = nseq({ { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } }), Color = gradient(theme),
    })
    burst.Dust = newEmitter(S, ground, {
        Texture = T.Fog, LightEmission = 0.12, LightInfluence = 0.5,
        EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(84, 84), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-20, 20),
        Lifetime = NumberRange.new(1.4, 2.3), Speed = NumberRange.new(14 * K, 34 * K), Drag = 2.6,
        Size = nseq({ { 0, 2.4 * K }, { 1, 9 * K } }),
        Transparency = nseq({ { 0, 0.68 }, { 0.4, 0.82 }, { 1, 1 } }),
        Color = cseq({ { 0, theme.Main:Lerp(Color3.fromRGB(120, 120, 130), 0.55) }, { 1, Color3.fromRGB(90, 90, 100) } }),
    })
    -- the reveal: motes of the realm's light falling through the column, and embers rising from the floor
    local motes = newPart(S, "Motes", Vector3.new(S.span * 0.35, 1, S.span * 0.35))
    S.motesPart = motes
    burst.Motes = newEmitter(S, motes, {
        Texture = T.Spark, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(2.4, 3.6), Speed = NumberRange.new(0.5, 2), Acceleration = Vector3.new(0, -2.5, 0), Drag = 0.5,
        EmissionDirection = Enum.NormalId.Bottom, SpreadAngle = Vector2.new(25, 25),
        Size = nseq({ { 0, 0 }, { 0.15, 0.9 * K }, { 1, 0.1 } }), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-60, 60),
        Transparency = nseq({ { 0, 1 }, { 0.12, 0.1 }, { 0.8, 0.25 }, { 1, 1 } }), Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
    })
    burst.Embers = newEmitter(S, ground, {
        Texture = T.Glow, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(1.6, 2.6), Speed = NumberRange.new(2, 6), Acceleration = Vector3.new(0, 4, 0), Drag = 0.8,
        EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(18, 18),
        Size = nseq({ { 0, 0.5 * K }, { 0.4, 0.7 * K }, { 1, 0 } }),
        Transparency = nseq({ { 0, 1 }, { 0.1, 0.2 }, { 0.7, 0.4 }, { 1, 1 } }), Color = cseq({ { 0, theme.Hot }, { 1, theme.Deep } }),
    })
    S.burst = burst
end

-- ---------- the realms' signatures ----------
-- Each returns nothing; it registers its own tracks and events through track/at. S.B is the break, S.H the hold, S.span the size of
-- the main shockwave, S.chest the cultivator's chest (updated every frame), S.power(kind, strength) tells BreakthroughShow
-- to kick the camera or the sound on a beat.
local Motifs = {}

-- two or three tilted belts of current round the body; they tighten, then fly out
local function belts(S, tex, glowTex, countBelts, colorA, colorB)
    local theme = S.theme
    local list = {}
    for i = 1, countBelts do
        local part = newPart(S, "Belt" .. i)
        local l0 = newAttachment(part, Vector3.new(-1, 0, 0))
        local l1 = newAttachment(part, Vector3.new(1, 0, 0))
        local pair = {}
        for side = 1, 2 do
            local flip = if side == 1 then 1 else -1
            local current = newBeam(S, part, l0, l1, {
                Texture = tex, TextureMode = Enum.TextureMode.Wrap, TextureLength = 2.2, TextureSpeed = (if i % 2 == 0 then -1.6 else 1.6),
                Brightness = 3, CurveSize0 = -3 * flip, CurveSize1 = 3 * flip, Segments = 20, ZOffset = 1.5,
                Color = cseq({ { 0, colorA }, { 0.5, colorB }, { 1, colorA } }),
                Transparency = nseq({ { 0, 1 }, { 0.2, 0.15 }, { 0.8, 0.15 }, { 1, 1 } }),
            })
            local glow = newBeam(S, part, l0, l1, {
                Texture = glowTex, TextureMode = Enum.TextureMode.Stretch, Brightness = 1.5,
                CurveSize0 = -3 * flip, CurveSize1 = 3 * flip, Segments = 20, ZOffset = 1.3,
                Color = cseq({ { 0, theme.Main }, { 1, theme.Deep } }),
                Transparency = nseq({ { 0, 1 }, { 0.25, 0.7 }, { 0.75, 0.7 }, { 1, 1 } }),
            })
            table.insert(pair, { current, glow, flip })
        end
        table.insert(list, { part = part, a0 = l0, a1 = l1, beams = pair, seed = i / countBelts })
    end
    local hold = S.B - S.H
    track(S, 0.18 * S.B, S.B + 1.6, function(u)
        local t = S.t
        local build = smooth(ramp(t, 0.18 * S.B, hold))
        local out = ramp(t, S.B, S.B + 1.3)
        for i, belt in list do
            local radius = lerp(S.K * 6, 1.7, build) + out * out * S.span * 0.5
            local spin = t * (1.6 + 2.4 * build) * (if i % 2 == 0 then -1 else 1) + belt.seed * FULL
            belt.part.CFrame = CFrame.new(S.chest + Vector3.new(0, (i - (countBelts + 1) / 2) * 1.35 * (1 - out) + out * out * 6 * (i - 1), 0))
                * CFrame.Angles(0.35 * math.sin(t * 1.3 + i), spin, 0.25 * math.cos(t + i))
            belt.a0.Position = Vector3.new(-radius, 0, 0)
            belt.a1.Position = Vector3.new(radius, 0, 0)
            local width = (1 - out) * (0.15 + 0.85 * build)
            for _, pair in belt.beams do
                pair[1].Width0, pair[1].Width1 = 1.1 * width, 1.1 * width
                pair[2].Width0, pair[2].Width1 = 2.9 * width, 2.9 * width
                pair[1].CurveSize0, pair[1].CurveSize1 = -radius * 0.55 * pair[3], radius * 0.55 * pair[3]
                pair[2].CurveSize0, pair[2].CurveSize1 = -radius * 0.55 * pair[3], radius * 0.55 * pair[3]
            end
        end
    end)
end

-- a shell of soft particles pulled in over the gather, and one let out at the break
local function shell(S, tex, radius, rate, colorSeq, sizeSeq, inward)
    local host = newPart(S, "Shell", Vector3.one * radius * 2)
    S.shells = S.shells or {}
    table.insert(S.shells, host)
    local emitter = newEmitter(S, host, {
        Texture = tex, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = if inward then Enum.ParticleEmitterShapeInOut.Inward else Enum.ParticleEmitterShapeInOut.Outward,
        Lifetime = NumberRange.new(1.1, 1.5), Speed = NumberRange.new(radius * 0.7, radius * 0.9),
        Size = sizeSeq, Color = colorSeq, Rotation = NumberRange.new(0, 360),
    })
    return emitter, host
end

-- 1 Qi Awakening: a long breath. Soft shells of jade light are drawn in, and let out
function Motifs.Breath(S)
    local theme, K = S.theme, S.K
    local inEmitter = shell(S, T.SoftGlow, 7 * K, 0, cseq({ { 0, theme.Deep }, { 0.5, theme.Main }, { 1, theme.Hot } }),
        nseq({ { 0, 2.5 * K }, { 0.5, 3.4 * K }, { 1, 1 } }), true)
    inEmitter.Transparency = nseq({ { 0, 1 }, { 0.2, 0.55 }, { 0.85, 0.5 }, { 1, 1 } })
    inEmitter.Lifetime = NumberRange.new(1.2, 1.5)
    inEmitter.Speed = NumberRange.new(5 * K, 6 * K)
    track(S, 0.2 * S.B, S.B, function(u)
        inEmitter.Rate = math.min(S.maxRate, 14 * S.cut) * smooth(u) * (if S.t > S.B - S.H then 0.3 else 1)
    end)
    local outEmitter = shell(S, T.SoftGlow, 2, 0, cseq({ { 0, theme.Hot }, { 1, theme.Main } }),
        nseq({ { 0, 3 * K }, { 0.4, 6 * K }, { 1, 10 * K } }), false)
    outEmitter.Speed = NumberRange.new(30 * K, 38 * K)
    outEmitter.Drag = 3.2
    outEmitter.Lifetime = NumberRange.new(1.0, 1.4)
    outEmitter.Transparency = nseq({ { 0, 0.1 }, { 0.5, 0.45 }, { 1, 1 } })
    at(S, S.B, function()
        outEmitter:Emit(count(S, 22))
    end)
end

-- 2 Qi Foundation: belts of Meridian current round the waist and chest
function Motifs.Current(S)
    belts(S, T.Current, T.HeavenHaze, 3, S.theme.Deep, Color3.fromRGB(190, 255, 245))
end

-- 3 Spirit Core: a core that beats, faster and faster, then bursts
function Motifs.Core(S)
    local theme, K = S.theme, S.K
    local pulse = newEmitter(S, S.core, {
        Texture = T.CorePulse, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-20, 20),
        Lifetime = NumberRange.new(1.1, 1.3), Size = nseq({ { 0, 1 }, { 0.3, 5 * K }, { 1, 7.5 * K } }),
        Transparency = nseq({ { 0, 1 }, { 0.06, 0.2 }, { 0.45, 0.55 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.fromRGB(255, 235, 140) }, { 1, Color3.fromRGB(255, 185, 20) } }),
    })
    local big = newEmitter(S, S.core, {
        Texture = T.CorePulse, Rotation = NumberRange.new(0, 360),
        Lifetime = NumberRange.new(1.3), Size = nseq({ { 0, 4 }, { 0.2, 24 * K }, { 1, 40 * K } }),
        Transparency = nseq({ { 0, 0.05 }, { 0.5, 0.45 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
    })
    -- the beats: slow, then quicker, and the last ones nearly a trill
    local gap, when, beats = 0.95, 0.3 * S.B, {}
    while when < S.B - S.H * 0.6 do
        table.insert(beats, when)
        when += gap
        gap = math.max(0.18, gap * 0.74)
    end
    for index, time in beats do
        local power = 0.5 + 0.5 * index / #beats
        at(S, time, function()
            pulse:Emit(1)
            S.beat("core", power)
        end)
    end
    at(S, S.B, function()
        big:Emit(1)
        big:Emit(count(S, 2))
    end)
end

-- 4 Spirit Soul: soul flames climb the body, then a ring of them is thrown out
function Motifs.Flame(S)
    local theme, K = S.theme, S.K
    local host = newPart(S, "Flames", Vector3.new(4.8 * K, 4 * K, 4.8 * K))
    S.flameHost = host
    local flames = newEmitter(S, host, {
        Texture = T.SoulFlame, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
        FlipbookFramerate = NumberRange.new(24, 30),
        Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        Orientation = Enum.ParticleOrientation.FacingCameraWorldUp, EmissionDirection = Enum.NormalId.Top, LightEmission = 0.85,
        Lifetime = NumberRange.new(0.9, 1.4), Speed = NumberRange.new(3, 6), Acceleration = Vector3.new(0, 4, 0),
        Size = nseq({ { 0, 2.4 * K }, { 0.5, 4.2 * K }, { 1, 2 * K } }), Rotation = NumberRange.new(-8, 8),
        Transparency = nseq({ { 0, 1 }, { 0.12, 0.1 }, { 0.75, 0.3 }, { 1, 1 } }),
        Color = cseq({ { 0, theme.Hot }, { 0.4, theme.Main }, { 1, theme.Deep } }),
    })
    track(S, 0.18 * S.B, S.B, function(u)
        flames.Rate = math.min(S.maxRate, 44 * S.cut) * smooth(u) * (if S.t > S.B - S.H then 0.35 else 1)
    end)
    local ring = newEmitter(S, S.core, {
        Texture = T.SoulFlame, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
        FlipbookFramerate = NumberRange.new(24, 30),
        Orientation = Enum.ParticleOrientation.FacingCameraWorldUp, LightEmission = 0.85,
        Lifetime = NumberRange.new(0.9, 1.4), Speed = NumberRange.new(24 * K, 40 * K), SpreadAngle = Vector2.new(180, 180), Drag = 2.4,
        Acceleration = Vector3.new(0, 6, 0),
        Size = nseq({ { 0, 3 * K }, { 0.4, 7 * K }, { 1, 3 * K } }), Rotation = NumberRange.new(-8, 8),
        Transparency = nseq({ { 0, 0.1 }, { 0.7, 0.4 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.2, theme.Hot }, { 0.6, theme.Main }, { 1, theme.Deep } }),
    })
    at(S, S.B, function()
        ring:Emit(count(S, 34))
    end)
end

-- 5 Ascendant: the Ascending Gale, a column of rising wind-streaks that blows the sky open
function Motifs.Gale(S)
    local theme, K = S.theme, S.K
    local host = newPart(S, "Gale", Vector3.new(4.4 * K, 2, 4.4 * K))
    S.galeHost = host
    local function galeEmitter(speed)
        return newEmitter(S, host, {
            Texture = T.GaleStreak, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Orientation = Enum.ParticleOrientation.VelocityParallel, EmissionDirection = Enum.NormalId.Top,
            Rotation = NumberRange.new(90, 90), Lifetime = NumberRange.new(0.6, 1.1), Speed = NumberRange.new(speed * 0.7, speed),
            Acceleration = Vector3.new(0, 34, 0), Drag = 3,
            Size = nseq({ { 0, 1.2 * K }, { 0.5, 2 * K }, { 1, 0.7 * K } }), Squash = nseq({ { 0, 1 }, { 1, 2 } }),
            Transparency = nseq({ { 0, 1 }, { 0.1, 0.15 }, { 0.7, 0.4 }, { 1, 1 } }),
            Color = cseq({ { 0, Color3.fromRGB(255, 250, 235) }, { 0.6, Color3.fromRGB(255, 225, 160) }, { 1, theme.Main } }),
        })
    end
    local gale = galeEmitter(5)
    track(S, 0.15 * S.B, S.B, function(u)
        gale.Rate = math.min(S.maxRate, 56 * S.cut) * smooth(u) * (if S.t > S.B - S.H then 0.3 else 1)
    end)
    local blow = galeEmitter(34)
    blow.Lifetime = NumberRange.new(0.9, 1.5)
    at(S, S.B, function()
        blow:Emit(count(S, 70))
    end)
end

-- 6 Immortal: Heaven's Light. Three pillars fall from the sky, close in, and are one at the break
function Motifs.Pillars(S)
    local theme, K = S.theme, S.K
    local shafts = {}
    for i = 1, 3 do
        local part = newPart(S, "Shaft" .. i)
        local bottom = newAttachment(part)
        local top = newAttachment(part, Vector3.new(0, 80, 0))
        local haze = newBeam(S, part, bottom, top, {
            Texture = T.HeavenHaze, TextureSpeed = 0.15, Brightness = 1, ZOffset = 0.8,
            Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 1, theme.Main } }), Transparency = nseq({ { 0, 0.8 }, { 0.5, 0.85 }, { 1, 1 } }),
        })
        local core = newBeam(S, part, bottom, top, {
            Texture = T.HeavenBeam, TextureSpeed = 0.35, Brightness = 1.8, ZOffset = 1,
            Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 1, theme.Main } }), Transparency = nseq({ { 0, 0.4 }, { 0.3, 0.6 }, { 0.85, 0.5 }, { 1, 1 } }),
        })
        table.insert(shafts, { part = part, haze = haze, core = core, seed = (i - 1) / 3 })
    end
    local hold = S.B - S.H
    track(S, 0.25 * S.B, S.B + 0.4, function(u)
        local t = S.t
        local build = smooth(ramp(t, 0.25 * S.B, hold))
        local merge = ramp(t, hold - 0.2, S.B)
        for _, shaft in shafts do
            local angle = shaft.seed * FULL + t * 0.55
            local radius = lerp(9 * K, 0, outCubic(merge)) * (1 - 0.35 * build) + (1 - merge) * 0
            local width = (0.2 + 0.8 * build) * (1 - ramp(t, S.B, S.B + 0.4))
            shaft.part.CFrame = CFrame.new(S.base + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius))
            shaft.haze.Width0, shaft.haze.Width1 = 5 * K * width, 4 * K * width
            shaft.core.Width0, shaft.core.Width1 = 1.8 * K * width, 1.4 * K * width
        end
    end)
end

-- 7 Divine: Divine Lightning. Crimson bolts crack closer and closer, then strike all round
function Motifs.Bolts(S)
    local theme, K = S.theme, S.K
    local host = newPart(S, "Bolts", Vector3.one * 12 * K)
    local bolts = newEmitter(S, host, {
        Texture = T.Bolt, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(0.08, 0.16), Rotation = NumberRange.new(0, 360),
        Size = nseq({ { 0, 3 * K }, { 0.3, 5 * K }, { 1, 4 * K } }),
        Transparency = nseq({ { 0, 0 }, { 0.6, 0 }, { 1, 0.6 } }),
        Color = cseq({ { 0, Color3.fromRGB(255, 130, 110) }, { 1, theme.Main } }),
    })
    S.boltHost = host
    -- the cracks come in clusters that tighten
    local when = 0.3 * S.B
    local gap = 0.8
    local index = 0
    while when < S.B - S.H * 0.5 do
        index += 1
        local power = clamp01(when / S.B)
        at(S, when, function()
            bolts:Emit(count(S, 3 + 4 * power))
            S.beat("bolt", 0.4 + 0.6 * power)
        end)
        when += gap
        gap = math.max(0.14, gap * 0.78)
    end
    local strike = newEmitter(S, S.core, {
        Texture = T.Bolt, Shape = Enum.ParticleEmitterShape.Sphere, Rotation = NumberRange.new(0, 360),
        Lifetime = NumberRange.new(0.12, 0.3), Speed = NumberRange.new(10, 30), SpreadAngle = Vector2.new(180, 180),
        Size = nseq({ { 0, 12 * K }, { 0.3, 20 * K }, { 1, 14 * K } }), Transparency = nseq({ { 0, 0 }, { 0.5, 0.1 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, Color3.fromRGB(255, 130, 110) }, { 1, theme.Main } }),
    })
    at(S, S.B, function()
        strike:Emit(count(S, 24))
    end)
    at(S, S.B + 0.18, function()
        strike:Emit(count(S, 14))
    end)
end

-- 8 Cosmic: Star Drift. Stars are drawn in from a wide sky and thrown back as a shower
function Motifs.Stars(S)
    local theme, K = S.theme, S.K
    local function starSizes()
        return nseq({ { 0, 0 }, { 0.15, 1.4 * K }, { 0.3, 0.7 * K }, { 0.5, 1.6 * K }, { 0.7, 0.6 * K }, { 0.85, 1.2 * K }, { 1, 0 } })
    end
    local pull = shell(S, T.Star, S.inflowRadius * 0.9, 0, cseq({ { 0, Color3.fromRGB(220, 190, 255) }, { 1, theme.Main } }), starSizes(), true)
    pull.Transparency = nseq({ { 0, 1 }, { 0.08, 0 }, { 0.9, 0 }, { 1, 1 } })
    pull.Lifetime = NumberRange.new(1.2, 1.7)
    pull.Speed = NumberRange.new(S.inflowRadius * 0.55, S.inflowRadius * 0.75)
    pull.Rotation = NumberRange.new(0, 45)
    local dust = shell(S, T.StarDust, S.inflowRadius * 0.7, 0, cseq({ { 0, Color3.new(1, 1, 1) }, { 1, theme.Hot } }),
        nseq({ { 0, 0 }, { 0.2, 0.9 * K }, { 1, 0 } }), true)
    dust.Lifetime = NumberRange.new(1.2, 1.8)
    dust.Speed = NumberRange.new(S.inflowRadius * 0.4, S.inflowRadius * 0.6)
    track(S, 0.15 * S.B, S.B, function(u)
        local k = smooth(u) * (if S.t > S.B - S.H then 0.3 else 1)
        pull.Rate = math.min(S.maxRate, 26 * S.cut) * k
        dust.Rate = math.min(S.maxRate, 22 * S.cut) * k
    end)
    local shower = newEmitter(S, S.core, {
        Texture = T.Star, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        Lifetime = NumberRange.new(2.2, 3.4), Speed = NumberRange.new(18 * K, 46 * K), SpreadAngle = Vector2.new(180, 180), Drag = 1.4,
        Acceleration = Vector3.new(0, -2, 0), Rotation = NumberRange.new(0, 45), Size = starSizes(),
        Transparency = nseq({ { 0, 1 }, { 0.06, 0 }, { 0.9, 0 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, Color3.fromRGB(220, 190, 255) }, { 1, theme.Main } }),
    })
    at(S, S.B, function()
        shower:Emit(count(S, 64))
    end)
end

-- 9 Void: Void Pull. Dark shards and ice streaks are sucked into a black core, which grows, implodes, and shocks out
function Motifs.Void(S)
    local theme, K = S.theme, S.K
    local shards = shell(S, T.VoidShards, S.inflowRadius * 0.8, 0, cseq({ { 0, Color3.fromRGB(20, 30, 60) }, { 1, Color3.fromRGB(6, 8, 20) } }),
        nseq({ { 0, 1.2 * K }, { 0.3, 3.2 * K }, { 1, 0.5 * K } }), true)
    shards.LightEmission = 0
    shards.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2
    shards.FlipbookMode = Enum.ParticleFlipbookMode.Random
    shards.RotSpeed = NumberRange.new(-300, 300)
    shards.Transparency = nseq({ { 0, 1 }, { 0.2, 0.1 }, { 0.8, 0.2 }, { 1, 1 } })
    shards.Lifetime = NumberRange.new(0.9, 1.2)
    shards.Speed = NumberRange.new(S.inflowRadius * 0.7, S.inflowRadius * 0.85)
    track(S, 0.15 * S.B, S.B, function(u)
        shards.Rate = math.min(S.maxRate, 30 * S.cut) * smooth(u) * (if S.t > S.B - S.H then 0.3 else 1)
    end)
    -- the black core: a dark soft disc in front of the chest, growing as it feeds, shrinking to a point at the hold
    S.voidCore = newGlow(S, "VoidCore", theme.Dark, T.Glow)
    S.voidCore.label.ZIndex = 2
    local ice = newEmitter(S, S.core, {
        Texture = T.VoidStreak, Orientation = Enum.ParticleOrientation.VelocityParallel, Lifetime = NumberRange.new(0.5, 0.9), Speed = NumberRange.new(50 * K, 100 * K), SpreadAngle = Vector2.new(180, 180), Drag = 2,
        Size = nseq({ { 0, 2 * K }, { 0.2, 9 * K }, { 1, 1.5 } }), Transparency = nseq({ { 0, 0 }, { 0.6, 0.3 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
    })
    at(S, S.B, function()
        ice:Emit(count(S, 60))
    end)
end

-- 10 Heavenly Dao: Radiant Rays. A fan of rose rays opens behind the body, then sweeps all round
function Motifs.Rays(S)
    local K = S.K
    local total = if S.low then 9 else 13
    local rays = {}
    for i = 1, total do
        local a0 = newAttachment(S.world)
        local a1 = newAttachment(S.world)
        local beam = newBeam(S, S.world, a0, a1, {
            Texture = T.RayBeam, TextureMode = Enum.TextureMode.Stretch, TextureSpeed = 0.15, Brightness = 4, Segments = 4,
            Color = cseq({ { 0, Color3.fromRGB(255, 235, 245) }, { 0.35, Color3.fromRGB(255, 150, 205) }, { 1, Color3.fromRGB(255, 70, 160) } }),
            Transparency = nseq({ { 0, 0.2 }, { 0.6, 0.45 }, { 1, 1 } }),
        })
        table.insert(rays, { a0 = a0, a1 = a1, beam = beam, seed = (i - 0.5) / total })
    end
    local hold = S.B - S.H
    track(S, 0.2 * S.B, S.B + 1.5, function(u)
        local t = S.t
        local build = smooth(ramp(t, 0.2 * S.B, hold))
        local sweep = ramp(t, S.B, S.B + 1.1)
        local fade = 1 - ramp(t, S.B + 0.7, S.B + 1.5)
        -- the fan: behind the body (opposite the camera), opening wider as it builds; at the break it closes round the whole body
        local camera = Workspace.CurrentCamera
        local behind = Vector3.new(0, 0, -1)
        if camera then
            local look = camera.CFrame.LookVector * Vector3.new(1, 0, 1)
            if look.Magnitude > 0.01 then
                behind = look.Unit
            end
        end
        local back = math.atan2(behind.Z, behind.X)
        for _, ray in rays do
            local spread = lerp(1.0, 2.6, build) * (ray.seed - 0.5) + lerp(0, FULL * (ray.seed - 0.5), outCubic(sweep))
            local angle = back + spread
            local length = (lerp(3, 16 * K, build) + outCubic(sweep) * S.span * 0.9)
            local lift = lerp(0.3, 0.9, build) * length * 0.25 * (1 - sweep) + (ray.seed - 0.5) * 6 * sweep
            local from = S.chest + Vector3.new(math.cos(angle), 0, math.sin(angle)) * 1.2
            ray.a0.Position = from
            ray.a1.Position = from + Vector3.new(math.cos(angle) * length, lift + length * 0.12 * (1 - sweep), math.sin(angle) * length)
            local width = (0.2 + 0.8 * build) * fade * (1 + 1.6 * sweep)
            ray.beam.Width0 = 1.1 * K * width
            ray.beam.Width1 = 5 * K * width
        end
    end)
end

-- 11 Primordial: Magma Rise. The floor cracks and glows; the break throws magma up
function Motifs.Magma(S)
    local K = S.K
    local cracks = newEmitter(S, S.ground, {
        Texture = T.Streak, Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.02), SpreadAngle = Vector2.zero, Rotation = NumberRange.new(0, 360),
        Lifetime = NumberRange.new(2.4, 3.6),
        Size = nseq({ { 0, 2 * K }, { 0.25, 11 * K }, { 1, 13 * K } }),
        Transparency = nseq({ { 0, 1 }, { 0.1, 0.1 }, { 0.8, 0.3 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.fromRGB(255, 200, 70) }, { 0.4, Color3.fromRGB(255, 110, 20) }, { 1, Color3.fromRGB(185, 35, 5) } }),
    })
    local chunks = newEmitter(S, S.ground, {
        Texture = T.Magma, EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(36, 36), Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-220, 220), Lifetime = NumberRange.new(1.4, 2.4), Speed = NumberRange.new(30 * K, 62 * K),
        Acceleration = Vector3.new(0, -52, 0), LightEmission = 0.6,
        Size = nseq({ { 0, 1.4 * K }, { 0.15, 2.4 * K }, { 1, 1.5 * K } }),
        Transparency = nseq({ { 0, 1 }, { 0.05, 0 }, { 0.85, 0 }, { 1, 1 } }),
        Color = cseq({ { 0, Color3.fromRGB(255, 200, 70) }, { 0.35, Color3.fromRGB(255, 110, 20) }, { 0.7, Color3.fromRGB(185, 35, 5) }, { 1, Color3.fromRGB(40, 5, 0) } }),
    })
    local smoke = newEmitter(S, S.ground, {
        Texture = T.HeatSmoke, LightEmission = 0, LightInfluence = 0.6, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30),
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume, EmissionDirection = Enum.NormalId.Top,
        Lifetime = NumberRange.new(1.8, 2.8), Speed = NumberRange.new(4, 9), Drag = 1,
        Size = nseq({ { 0, 3 * K }, { 1, 12 * K } }),
        Transparency = nseq({ { 0, 1 }, { 0.15, 0.55 }, { 1, 1 } }), Color = cseq({ { 0, Color3.fromRGB(70, 40, 30) }, { 1, Color3.fromRGB(25, 15, 15) } }),
    })
    -- the floor cracks open in pulses through the gather
    local when = 0.25 * S.B
    while when < S.B - S.H * 0.5 do
        local grow = clamp01(when / S.B)
        at(S, when, function()
            cracks:Emit(count(S, 3 + 4 * grow))
            smoke:Emit(count(S, 2))
        end)
        when += 0.55
    end
    at(S, S.B, function()
        chunks:Emit(count(S, 38))
        cracks:Emit(count(S, 16))
        smoke:Emit(count(S, 14))
    end)
end

-- 12 Eternal: Eternal Orbits. Three rings of gold, cyan and magenta spin in, then fly out as the shockwave
function Motifs.Orbits(S)
    local theme = S.theme
    local colors = { theme.Gold, theme.Cyan, theme.Magenta }
    local orbits = {}
    for i = 1, 3 do
        local part = newPart(S, "Orbit" .. i)
        local a0 = newAttachment(part, Vector3.new(-1, 0, 0))
        local a1 = newAttachment(part, Vector3.new(1, 0, 0))
        local halves = {}
        for side = 1, 2 do
            local flip = if side == 1 then 1 else -1
            table.insert(halves, newBeam(S, part, a0, a1, {
                Texture = T.OrbitBeam, TextureMode = Enum.TextureMode.Wrap, TextureLength = 9.4, TextureSpeed = (if i % 2 == 0 then -3.3 else 3.3) * flip,
                Brightness = 2, Segments = 28, ZOffset = 0.6, CurveSize0 = -4 * flip, CurveSize1 = 4 * flip,
                Color = cseq({ { 0, colors[i] }, { 0.5, colors[i]:Lerp(Color3.new(1, 1, 1), 0.5) }, { 1, colors[i] } }),
                Transparency = nseq({ { 0, 0.25 }, { 1, 0.25 } }),
            }))
        end
        table.insert(orbits, { part = part, a0 = a0, a1 = a1, halves = halves, turn = (i - 1) / 3 * FULL })
    end
    local hold = S.B - S.H
    track(S, 0.15 * S.B, S.B + 1.8, function()
        local t = S.t
        local build = smooth(ramp(t, 0.15 * S.B, hold))
        local out = ramp(t, S.B, S.B + 1.5)
        local fade = 1 - ramp(t, S.B + 0.9, S.B + 1.8)
        for i, orbit in orbits do
            local radius = lerp(9 * S.K, 3, build) + outCubic(out) * S.span * 0.75
            orbit.part.CFrame = CFrame.new(S.chest) * CFrame.Angles(0, orbit.turn + t * (0.5 + 2.4 * build), 0)
                * CFrame.Angles(math.rad(62), 0, 0) * CFrame.Angles(0, 0, t * 0.9 * (if i % 2 == 0 then -1 else 1))
            orbit.a0.Position = Vector3.new(-radius, 0, 0)
            orbit.a1.Position = Vector3.new(radius, 0, 0)
            local width = (0.2 + 0.8 * build) * fade * (1 + out)
            for side, beam in orbit.halves do
                local flip = if side == 1 then 1 else -1
                beam.Width0, beam.Width1 = 1.1 * width, 1.1 * width
                beam.CurveSize0, beam.CurveSize1 = -radius * 0.55 * flip, radius * 0.55 * flip
            end
        end
    end)
end

-- ---------- the sequence ----------
local function applyPace(S)
    local scale = S.pace * Fx.TimeScale
    if scale ~= S.appliedPace then
        S.appliedPace = scale
        for _, emitter in S.emitters do
            emitter.TimeScale = scale
        end
    end
end

local function finish(S, instant)
    if S.finished then
        return
    end
    S.finished = true
    S.connection:Disconnect()
    for _, emitter in S.emitters do
        emitter.Enabled = false
    end
    S.folder:Destroy()
    if S.spec.OnDone then
        S.spec.OnDone(instant)
    end
end

local function breakNow(S)
    if S.broke then
        return
    end
    S.broke = true
    if S.spec.OnBreak then
        S.spec.OnBreak()
    end
end

-- the break and what follows it, as events at B
local function scheduleBreak(S)
    local B = S.B
    local grade = S.grade
    local rings, burst = S.rings, S.burst

    at(S, B, function()
        breakNow(S)
        -- the flash on the core and the first rings together
        burst.Flash:Emit(1)
        rings.Halo:Emit(1)
        rings.Hot:Emit(1)
        rings.Disc:Emit(1)
        burst.Rays:Emit(count(S, 26 + 10 * (S.grade.Size - 0.7)))
        burst.Shards:Emit(count(S, 12 + 12 * (S.grade.Size - 0.7)))
        burst.Dust:Emit(count(S, 12 + 8 * S.grade.Size))
        S.light.Brightness = 5 * S.grade.Size
        S.light.Range = 34 * S.K
        S.surge = 1
        S.spike = 1
        if S.spec.OnImpact then
            S.spec.OnImpact()
        end
    end, true)
    at(S, B + 0.13, function()
        rings.Main:Emit(1)
        if rings.Sky1 then
            rings.Sky1:Emit(1)
        end
    end)
    at(S, B + 0.3, function()
        rings.Deep:Emit(1)
        if rings.Sky2 then
            rings.Sky2:Emit(1)
        end
    end)
    -- the reveal: embers and motes through the column
    at(S, B + 0.45, function()
        burst.Embers.Rate = math.min(S.maxRate, 22 * S.cut)
        burst.Motes.Rate = if grade.Pillar > 0 then math.min(S.maxRate, 24 * S.cut) else 0
    end)
end

local function stepPillarAndLight(S, dt)
    local t, B, H = S.t, S.B, S.H
    local grade, light = S.grade, S.light
    -- the column: rises in the build, surges at the break, then stands, and thins away in the settle
    local pillar = S.pillar
    if pillar then
        local settle = 1 - smooth(ramp(t, S.settle0, S.beats.End))
        S.surge = (S.surge or 0) * math.exp(-dt * 2.6)
        local h, w
        if t < B then
            h = 0.55 * smooth(ramp(t, 0.42 * B, B - H * 0.3))
            w = 0.3 * smooth(ramp(t, 0.42 * B, B - H))
            S.preH = h
        else
            h = lerp(S.preH or 0.5, 1, outCubic(ramp(t, B, B + 0.3)))
            w = 0.5 * settle + 1.5 * S.surge
        end
        pillar.top.Position = Vector3.new(0, math.max(0.5, S.pillarHeight * h), 0)
        local wide = pillar.wide
        pillar.haze.Width0, pillar.haze.Width1 = wide * w, wide * 0.7 * w
        pillar.core.Width0, pillar.core.Width1 = wide * 0.3 * w, wide * 0.2 * w
    end
    -- the chest light: grows in the build, pinpoint in the hold, a spike at the break, the realm's glow after
    local charge = smooth(ramp(t, 0, B - H)) ^ 1.4
    local brightness, range
    if t < B - H then
        brightness, range = 0.4 + 2.6 * charge, 10 + 12 * charge
        brightness *= 0.85 + 0.15 * math.sin(t * 17 + math.sin(t * 5))
    elseif t < B then
        brightness, range = 2.4 + 5 * ramp(t, B - H, B), lerp(22, 8, ramp(t, B - H, B))
    else
        local after = S.spike or 0
        S.spike = after * math.exp(-dt * 2.2)
        local settle = 1 - smooth(ramp(t, S.settle0, S.beats.End))
        brightness = (0.7 * settle + 6 * S.spike * grade.Size)
        range = (18 + 18 * S.spike) * S.K
    end
    light.Brightness = brightness
    light.Range = range
    -- the glow: a growing ball of the realm's hot colour, a pinpoint in the hold, a flare at the break
    if t < B - H then
        setGlow(S.coreGlow, (1.2 + 4.2 * charge) * S.K, 0.35 - 0.2 * charge)
    elseif t < B then
        local k = ramp(t, B - H, B)
        setGlow(S.coreGlow, lerp(5, 0.9, outCubic(k)) * S.K, 0.05)
    else
        local k = ramp(t, B, B + 0.9)
        local settle = 1 - smooth(ramp(t, S.settle0, S.beats.End))
        setGlow(S.coreGlow, lerp(9, 4, smooth(k)) * S.K * (0.4 + 0.6 * settle), 0.25 + 0.75 * smooth(ramp(t, B + 0.1, B + 1.2)) + 0.2 * (1 - settle))
    end
    local flareK = ramp(t, B, B + 0.55)
    if t >= B then
        setGlow(S.flare, lerp(6, if S.own then 20 else 55, outCubic(flareK)) * S.K * (0.6 + 0.4 * grade.Size), 1)
        S.flare.label.ImageTransparency = if flareK >= 1 then 1 else math.max(0.15, smooth(ramp(t, B + 0.1, B + 0.55)))
    end
    if S.voidCore then
        local k = ramp(t, 0.15 * S.B, B - H)
        if t < B - H then
            setGlow(S.voidCore, (0.5 + 3.4 * smooth(k)) * S.K, 0)
        elseif t < B + 0.1 then
            setGlow(S.voidCore, lerp(3.9, 0.3, outCubic(ramp(t, B - H, B + 0.1))) * S.K, 0)
        else
            setGlow(S.voidCore, 0.3, 1)
        end
    end
end

local function stepPace(S)
    local t, B, H = S.t, S.B, S.H
    local grade = S.grade
    local pace = 1
    if t >= B - H and t < B and H > 0 then
        pace = 0.2 -- the held breath
    elseif t >= B and grade.Slow > 0 then
        local length = 0.25 + 0.7 * grade.Slow
        pace = lerp(0.14, 1, smooth(ramp(t, B + 0.06 + 0.2 * grade.Slow, B + length)))
        if t < B + 0.06 + 0.2 * grade.Slow then
            pace = 0.14
        end
    end
    S.pace = pace
    applyPace(S)
end

local function step(S, dt)
    if S.finished then
        return
    end
    if not (S.root and S.root.Parent) or (S.character and not S.character.Parent) then
        finish(S, true)
        return
    end
    dt = math.min(dt, 0.1) * Fx.TimeScale
    S.groundClock -= dt
    if S.groundClock <= 0 then
        S.groundClock = 0.3
        refreshGround(S)
    end
    place(S)
    S.t += dt
    local t = S.t
    if S.skipAt and not S.skipped then
        S.skipped = true
        if not S.broke then
            breakNow(S)
        end
        S.t = math.max(S.t, S.beats.Out or (S.beats.End - 1.2))
        t = S.t
        S.settle0 = t
        S.beats.End = math.min(S.beats.End, t + 0.7)
        for _, event in S.events do
            if event.time <= t and not event.done then
                event.done = true
            end
        end
        for _, emitter in S.emitters do
            emitter.Rate = 0
        end
        killThreads(S)
    end
    stepPace(S)
    for _, e in S.events do
        if not e.done and t >= e.time then
            e.done = true
            e.fn()
        end
    end
    for _, tr in S.tracks do
        if t >= tr.from and not tr.done then
            if t >= tr.to then
                tr.done = true
                tr.fn(1, dt)
            else
                tr.fn((t - tr.from) / (tr.to - tr.from), dt)
            end
        end
    end
    stepPillarAndLight(S, dt)
    -- the host parts that follow the cultivator
    S.motesPart.CFrame = CFrame.new(S.base + Vector3.new(0, S.pillarHeight * 0.45, 0))
    if S.sky then
        S.sky[1].CFrame = CFrame.new(S.base + Vector3.new(0, 8 * S.K, 0))
        S.sky[2].CFrame = CFrame.new(S.base + Vector3.new(0, 24 * S.K, 0))
    end
    S.draw.CFrame = CFrame.new(S.chest)
    if S.flameHost then
        S.flameHost.CFrame = CFrame.new(S.base + Vector3.new(0, 1.4, 0))
    end
    if S.galeHost then
        S.galeHost.CFrame = CFrame.new(S.base + Vector3.new(0, 0.6, 0))
    end
    if S.boltHost then
        S.boltHost.CFrame = CFrame.new(S.chest)
    end
    for _, shellPart in S.shells or {} do
        shellPart.CFrame = CFrame.new(S.chest)
    end
    -- the settle: the emitters' rates thin out, the threads go
    if t >= S.settle0 then
        for _, emitter in S.emitters do
            if emitter.Rate > 0 then
                emitter.Rate *= 0.9
            end
        end
        for _, trail in S.trails do
            trail.Enabled = false
        end
    end
    if t >= S.beats.End then
        finish(S, false)
    end
end

-- ---------- starting ----------
function Fx.start(spec)
    local info = spec.Info
    local grade, theme = info.Grade, info.Theme
    local own = spec.Own == true
    local beats = table.clone(if own then grade.Own else grade.Near)
    local S = {
        spec = spec, parent = spec.Parent, character = spec.Character, root = spec.Root, info = info, grade = grade, theme = theme,
        own = own, low = spec.Low == true, calm = spec.Calm == true,
        beats = beats, B = beats.Break, H = beats.Hold, t = 0, pace = 1, appliedPace = -1,
        emitters = {}, beams = {}, trails = {}, tracks = {}, events = {}, groundClock = 0, groundY = 0,
    }
    S.cut = (if S.low then 0.6 else 1) * (if S.calm then 0.45 else 1) * (if own then 1 else 0.7)
    S.maxRate = if S.low then 40 else 80
    S.K = theme.Scale * grade.Size
    S.span = 46 * S.K * (if own then 1 else 0.8)
    S.inflowRadius = math.max(7, 15 * S.K) * (if own then 1 else 0.8)
    S.pillarHeight = grade.Pillar * (if own then 1 else 0.7) * (0.8 + 0.2 * theme.Scale)
    S.settle0 = beats.Out or (beats.End - 1.4)
    S.beat = function(kind, power)
        if spec.OnBeat then
            spec.OnBeat(kind, power)
        end
    end
    S.ringColors = {
        cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Hot }, { 1, theme.Main } }),
        cseq({ { 0, theme.Hot }, { 1, theme.Main } }),
        cseq({ { 0, theme.Main }, { 1, theme.Deep } }),
    }
    if theme.Motif == "Orbits" then -- the prismatic realm's three break rings are its three colours
        S.ringColors = {
            cseq({ { 0, Color3.new(1, 1, 1) }, { 0.3, theme.Gold }, { 1, theme.Gold } }),
            cseq({ { 0, theme.Cyan:Lerp(Color3.new(1, 1, 1), 0.3) }, { 1, theme.Cyan } }),
            cseq({ { 0, theme.Magenta:Lerp(Color3.new(1, 1, 1), 0.2) }, { 1, theme.Magenta } }),
        }
    end

    local folder = Instance.new("Folder")
    folder.Name = "Breakthrough"
    S.folder = folder
    S.world = newPart(S, "World") -- at the origin: attachments' positions in it are world positions
    S.world.CFrame = CFrame.identity
    S.core = newPart(S, "Core")
    S.ground = newPart(S, "Ground", Vector3.new(2, 0.2, 2))
    folder.Parent = spec.Parent
    refreshGround(S)
    place(S)

    buildLight(S)
    buildRings(S)
    buildBurstEmitters(S)
    buildInflow(S)
    if grade.Threads > 0 and own then
        buildThreads(S, math.max(2, math.floor(grade.Threads * (if S.low then 0.5 else 1) * (if S.calm then 0.6 else 1) + 0.5)))
    end
    if grade.Pillar > 0 then
        buildPillar(S)
    end
    local motif = Motifs[theme.Motif]
    if motif and own then -- (others see the shared grammar in the realm's colours: a pillar, shockwaves, a flash; the signature is the player's own)
        motif(S)
    end

    -- the gather's ground rings closing in, and the climbing rings of the build
    local pulses = if grade.Name == "Step" then 1 elseif grade.Name == "Milestone" then 2 else 3
    for i = 1, pulses do
        local when = S.B * (0.3 + 0.55 * (i - 1) / math.max(1, pulses - 1)) * (if pulses == 1 then 0.9 else 1)
        at(S, when, function()
            S.rings.Collapse:Emit(1)
        end)
    end
    if grade.Rings > 1 and own then
        local from = 0.5 * S.B
        local to = S.B - S.H
        local total = grade.Rings * 2
        for i = 1, total do
            local u = (i - 1) / total
            at(S, from + (to - from) * u ^ 0.8, function()
                S.rings.Rise:Emit(1)
            end)
        end
    end
    scheduleBreak(S)
    -- a flat-out end: the effect may not outlive its beats
    S.connection = RunService.Heartbeat:Connect(function(dt)
        step(S, dt)
    end)
    return S
end

function Fx.skip(effect)
    if not effect.finished then
        effect.skipAt = true
    end
end

function Fx.stop(effect)
    finish(effect, true)
end

return Fx

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))

local TidecallerAura = {}

local SETTINGS = AuraStyles.CharacterAura
local STYLE = AuraStyles.Tidecaller
local TAU = 2 * math.pi
local FADE_IN = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(1.1, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local MAX_GROUND_DROP = 14

local function numberSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, NumberSequenceKeypoint.new(point[1], point[2]))
    end
    return NumberSequence.new(keypoints)
end

local function smoothstep(edge0, edge1, x)
    local t = math.clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
end

local function approach(current, target, rate, deltaTime)
    return current + (target - current) * (1 - math.exp(-rate * deltaTime))
end

local function prepare(part)
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Massless = true
end

local function newPart(aura, name, size, shape)
    local part = Instance.new("Part")
    part.Name = name
    part.Shape = shape or Enum.PartType.Block
    part.Size = size
    part.Transparency = 1
    prepare(part)
    part.CFrame = aura.rootPart.CFrame
    part.Parent = aura.model
    return part
end

local function meshTemplate(name)
    local folder = ReplicatedStorage:FindFirstChild("AuraMeshes")
    local model = folder and folder:FindFirstChild("AquaTide")
    return model and model:FindFirstChild("AquaTide_" .. name, true)
end

local function look(part, kind)
    local material = STYLE.Materials[kind]
    part.Material = material.Material
    part.Color = material.Color
    part.Reflectance = material.Reflectance or 0
    if part:IsA("MeshPart") then
        part.TextureID = ""
    end
    for _, child in part:GetChildren() do
        child:Destroy()
    end
end

local function meshPart(aura, name, scale, kind)
    local template = meshTemplate(name)
    local part = template:Clone()
    part.Size = template.Size * scale
    prepare(part)
    look(part, kind)
    part.Transparency = 1
    part.Parent = aura.model
    table.insert(aura.meshes, { Part = part, Base = STYLE.Materials[kind].Transparency })
    return part
end

local function addEmitter(aura, parent, rate, properties, minStage)
    local emitter = Instance.new("ParticleEmitter")
    emitter.LightInfluence = 0
    emitter.Rate = 0
    for property, value in properties do
        emitter[property] = value
    end
    emitter.Parent = parent
    if rate > 0 then
        table.insert(aura.emitters, { Emitter = emitter, Rate = rate * aura.detail * aura.boost, MinStage = minStage or 1 })
    end
    return emitter
end

local function surfaceImage(gui, image, size, color, transparency)
    local label = Instance.new("ImageLabel")
    label.AnchorPoint = Vector2.new(0.5, 0.5)
    label.Position = UDim2.fromScale(0.5, 0.5)
    label.Size = UDim2.fromScale(size, size)
    label.BackgroundTransparency = 1
    label.Image = image
    label.ImageColor3 = color
    label.ImageTransparency = 1
    label.Parent = gui
    return { Image = label, Transparency = transparency }
end

local function buildLotus(aura)
    local s = aura.k
    local template = meshTemplate("Petal")
    aura.petals = {}
    for ring, settings in STYLE.Lotus do
        for index = 1, settings.Count do
            local scale = settings.Length * s / math.max(template.Size.X, template.Size.Y, template.Size.Z)
            local part = meshPart(aura, "Petal", scale, settings.Kind)
            table.insert(aura.petals, {
                Part = part,
                Ring = ring,
                Angle = (index - 1) / settings.Count * TAU + (settings.Offset or 0),
                Radius = settings.Radius * s,
                Open = settings.Open,
                Length = part.Size.Y,
                Delay = (index - 1) / settings.Count * 0.25 + (ring - 1) * 0.15,
            })
        end
    end
    aura.pearl = newPart(aura, "Pearl", Vector3.one * 0.55 * s, Enum.PartType.Ball)
    aura.pearl.Material = Enum.Material.Neon
    aura.pearl.Color = STYLE.Colors.Core
    table.insert(aura.meshes, { Part = aura.pearl, Base = 0.25 })
end

local function buildVortex(aura)
    local s = aura.k
    local template = meshTemplate("Spiral")
    aura.spirals = {}
    for index, settings in STYLE.Spirals do
        local scale = settings.Radius * 2 * s / math.max(template.Size.X, template.Size.Z)
        local part = meshPart(aura, "Spiral", scale, settings.Kind)
        table.insert(aura.spirals, { Part = part, Kind = settings.Kind, Speed = settings.Speed, Phase = index * 2.1, Lift = settings.Lift * s, Height = part.Size.Y })
    end
end

local function buildKoi(aura)
    local s = aura.k
    local body, tail, eye = meshTemplate("Koi"), meshTemplate("KoiTail"), meshTemplate("KoiEye")
    local scale = STYLE.Koi.Length * s / math.max(body.Size.X, body.Size.Y, body.Size.Z)
    local function relative(cframe)
        local offset = body.CFrame:ToObjectSpace(cframe)
        return offset.Rotation + offset.Position * scale
    end
    local pivot = relative(tail.CFrame * CFrame.new(0, 0, -tail.Size.Z / 2))
    local tailFromPivot = CFrame.new(0, 0, tail.Size.Z / 2 * scale)
    local eyeOffset = relative(eye.CFrame)

    aura.koi = {}
    for index, settings in STYLE.Koi.Fish do
        local fish = {
            Kind = settings.Kind,
            Body = meshPart(aura, "Koi", scale, settings.Kind),
            Tail = meshPart(aura, "KoiTail", scale, settings.Kind),
            Eye = meshPart(aura, "KoiEye", scale, "Eye"),
            Pivot = pivot,
            TailFromPivot = tailFromPivot,
            EyeOffset = eyeOffset,
            Phase = (index - 1) * math.pi,
            Direction = settings.Direction,
            Radius = settings.Radius * s,
            Height = settings.Height,
        }
        local top = Instance.new("Attachment")
        top.Position = Vector3.new(0, 0.12 * s, 0)
        top.Parent = fish.Tail
        local bottom = Instance.new("Attachment")
        bottom.Position = Vector3.new(0, -0.12 * s, 0)
        bottom.Parent = fish.Tail
        local trail = Instance.new("Trail")
        trail.Attachment0 = top
        trail.Attachment1 = bottom
        trail.Texture = STYLE.Textures.Trail
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.FaceCamera = true
        trail.Lifetime = 0.9
        trail.LightInfluence = 0
        trail.LightEmission = 0.8
        trail.Brightness = 2
        trail.Color = ColorSequence.new(settings.Trail, STYLE.Colors.Deep)
        trail.Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } })
        trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0.1 } })
        trail.Enabled = false
        trail.Parent = fish.Tail
        fish.Trail = trail
        table.insert(aura.koi, fish)
    end
end

local function buildHalo(aura)
    local s = aura.k
    local template = meshTemplate("WaveHalo")
    local scale = STYLE.Halo.Diameter * s / math.max(template.Size.X, template.Size.Y)
    aura.halo = meshPart(aura, "WaveHalo", scale, "Halo")
    aura.haloSize = aura.halo.Size
end

local function buildDroplets(aura)
    local s = aura.k
    local template = meshTemplate("Droplet")
    local scale = STYLE.Droplets.Size * s / math.max(template.Size.X, template.Size.Y, template.Size.Z)
    local random = Random.new(aura.player.UserId)
    aura.droplets = {}
    for index = 1, STYLE.Droplets.Count do
        local part = meshPart(aura, "Droplet", scale * random:NextNumber(0.7, 1.15), "Droplet")
        table.insert(aura.droplets, {
            Part = part,
            Size = part.Size,
            Angle = (index - 1) / STYLE.Droplets.Count * TAU,
            Radius = STYLE.Droplets.Radius * s * random:NextNumber(0.9, 1.1),
            Height = random:NextNumber(0.35, 0.65),
            Phase = random:NextNumber(0, TAU),
        })
    end
end

local function buildRipples(aura)
    local template = meshTemplate("Ripple")
    aura.rippleBase = template.Size / math.max(template.Size.X, template.Size.Z)
    aura.ripples = {}
    for index = 1, STYLE.Ripples.Count do
        local part = meshPart(aura, "Ripple", 1, "Ripple")
        table.insert(aura.ripples, { Part = part, Born = -math.huge })
    end
    aura.nextRipple = 0
    aura.rippleIndex = 1
end

local function buildSpouts(aura)
    local s = aura.k
    local template = meshTemplate("Spout")
    local scale = STYLE.Spouts.Height * s / template.Size.Y
    aura.spouts = {}
    for index = 1, STYLE.Spouts.Count do
        local part = meshPart(aura, "Spout", scale, "Spout")
        part.Size *= Vector3.new(STYLE.Spouts.Width, 1, STYLE.Spouts.Width)
        local top = Instance.new("Attachment")
        top.Parent = part
        local spray = addEmitter(aura, top, 0, {
            Texture = STYLE.Textures.Streak,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Color = ColorSequence.new(STYLE.Colors.Core, STYLE.Colors.Main),
            LightEmission = 0.7,
            Brightness = 2.5,
            Size = numberSequence({ { 0, 0.7 * s }, { 1, 0.25 * s } }),
            Lifetime = NumberRange.new(0.6, 0.9),
            Speed = NumberRange.new(6 * s, 10 * s),
            SpreadAngle = Vector2.new(40, 40),
            Acceleration = Vector3.new(0, -26 * s, 0),
            EmissionDirection = Enum.NormalId.Top,
        })
        table.insert(aura.spouts, {
            Part = part,
            Size = part.Size,
            Top = top,
            Spray = spray,
            Angle = (index - 1) / STYLE.Spouts.Count * TAU + math.pi / STYLE.Spouts.Count,
            Phase = index * 1.7,
        })
    end
end

local function buildPool(aura)
    local s = aura.k
    local diameter = STYLE.Pool.Diameter * s
    local pool = newPart(aura, "Pool", Vector3.new(diameter, 0.05, diameter))
    aura.pool = pool
    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Top
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = 40
    gui.LightInfluence = 0
    gui.Brightness = 2.2
    gui.MaxDistance = 400
    gui.Parent = pool
    aura.poolImages = {
        surfaceImage(gui, STYLE.Textures.Glow, 1.05, STYLE.Colors.Deep, 0.35),
        surfaceImage(gui, STYLE.Textures.Glow, 0.55, STYLE.Colors.Main, 0.45),
        surfaceImage(gui, STYLE.Textures.Caustics, 1, STYLE.Colors.Core, 0.1),
        surfaceImage(gui, STYLE.Textures.Caustics, 0.78, STYLE.Colors.Main, 0.25),
    }
    aura.caustics = { aura.poolImages[3].Image, aura.poolImages[4].Image }

    aura.basin = newPart(aura, "Basin", Vector3.new(diameter * 0.5, 0.4 * s, diameter * 0.5))
    addEmitter(aura, aura.basin, 9, {
        Texture = STYLE.Textures.Bubble,
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Color = ColorSequence.new(STYLE.Colors.Core),
        LightEmission = 0.5,
        Brightness = 2,
        Size = numberSequence({ { 0, 0 }, { 0.15, 0.32 * s }, { 0.85, 0.4 * s }, { 1, 0 } }),
        Transparency = numberSequence({ { 0, 0.2 }, { 1, 0.6 } }),
        Lifetime = NumberRange.new(2.2, 3.4),
        Speed = NumberRange.new(1.2 * s, 2.4 * s),
        SpreadAngle = Vector2.new(12, 12),
        Acceleration = Vector3.new(0, 0.6 * s, 0),
        EmissionDirection = Enum.NormalId.Top,
    })
    aura.mist = addEmitter(aura, aura.basin, 4, {
        Texture = STYLE.Textures.Smoke,
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Color = ColorSequence.new(STYLE.Colors.Mist),
        LightEmission = 0.3,
        Size = numberSequence({ { 0, 2.4 * s }, { 1, 4.6 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.3, 0.82 }, { 1, 1 } }),
        Lifetime = NumberRange.new(3, 4.5),
        Speed = NumberRange.new(0.4 * s, 0.9 * s),
        SpreadAngle = Vector2.new(80, 80),
        Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-12, 12),
        EmissionDirection = Enum.NormalId.Top,
    })
end

local function buildAir(aura)
    local s = aura.k
    aura.volume = newPart(aura, "Volume", Vector3.new(3.4 * s, 4 * s, 3.4 * s))
    addEmitter(aura, aura.volume, 12, {
        Texture = STYLE.Textures.Sparkle,
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Color = ColorSequence.new(STYLE.Colors.Core, STYLE.Colors.Main),
        LightEmission = 1,
        Brightness = 3,
        Size = numberSequence({ { 0, 0 }, { 0.3, 0.3 * s }, { 1, 0 } }),
        Lifetime = NumberRange.new(1.2, 2),
        Speed = NumberRange.new(0.5 * s, 1.5 * s),
        SpreadAngle = Vector2.new(180, 180),
        Acceleration = Vector3.new(0, 1.2 * s, 0),
        Rotation = NumberRange.new(0, 360),
    })

    aura.splash = addEmitter(aura, aura.volume, 0, {
        Texture = STYLE.Textures.Streak,
        Orientation = Enum.ParticleOrientation.VelocityParallel,
        Color = ColorSequence.new(STYLE.Colors.Core, STYLE.Colors.Main),
        LightEmission = 0.8,
        Brightness = 3,
        Size = numberSequence({ { 0, 0.9 * s }, { 1, 0.3 * s } }),
        Lifetime = NumberRange.new(0.7, 1.1),
        Speed = NumberRange.new(14 * s, 22 * s),
        SpreadAngle = Vector2.new(38, 38),
        Acceleration = Vector3.new(0, -38 * s, 0),
        EmissionDirection = Enum.NormalId.Top,
    })

    aura.cloud = newPart(aura, "Cloud", Vector3.new(7 * s, 0.4 * s, 7 * s))
    addEmitter(aura, aura.cloud, 14, {
        Texture = STYLE.Textures.Streak,
        Orientation = Enum.ParticleOrientation.VelocityParallel,
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Color = ColorSequence.new(STYLE.Colors.Core, STYLE.Colors.Main),
        LightEmission = 0.8,
        Brightness = 2.5,
        Size = numberSequence({ { 0, 0.55 * s }, { 1, 0.35 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.3 }, { 1, 0.6 } }),
        Lifetime = NumberRange.new(0.7, 1),
        Speed = NumberRange.new(9 * s, 13 * s),
        SpreadAngle = Vector2.new(4, 4),
        EmissionDirection = Enum.NormalId.Bottom,
    }, 3)

    aura.streams = {}
    for index = 1, STYLE.Streams do
        local point = newPart(aura, "Stream" .. index, Vector3.one * 0.2)
        local top = Instance.new("Attachment")
        top.Position = Vector3.new(0, 0.22 * s, 0)
        top.Parent = point
        local bottom = Instance.new("Attachment")
        bottom.Position = Vector3.new(0, -0.22 * s, 0)
        bottom.Parent = point
        local trail = Instance.new("Trail")
        trail.Attachment0 = top
        trail.Attachment1 = bottom
        trail.Texture = STYLE.Textures.Trail
        trail.FaceCamera = true
        trail.Lifetime = 0.45
        trail.LightInfluence = 0
        trail.LightEmission = 0.9
        trail.Brightness = 3
        trail.Color = ColorSequence.new(STYLE.Colors.Core, STYLE.Colors.Main)
        trail.Transparency = numberSequence({ { 0, 0 }, { 1, 1 } })
        trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0.2 } })
        trail.Enabled = false
        trail.Parent = point
        table.insert(aura.streams, { Part = point, Trail = trail, Angle = (index - 1) / STYLE.Streams * TAU })
    end

    local light = Instance.new("PointLight")
    light.Color = STYLE.Colors.Main
    light.Range = 18 * s
    light.Brightness = 0
    light.Shadows = false
    light.Parent = aura.volume
    aura.light = light

    local glow = Instance.new("Highlight")
    glow.Name = "AuraGlow"
    glow.Adornee = aura.character
    glow.DepthMode = Enum.HighlightDepthMode.Occluded
    glow.FillColor = STYLE.Colors.Main
    glow.OutlineColor = STYLE.Colors.Core
    glow.FillTransparency = 1
    glow.OutlineTransparency = 1
    glow.Parent = aura.model
    aura.highlight = glow
end

function TidecallerAura.isReady()
    for _, name in { "Petal", "Spiral", "Droplet", "Ripple", "Koi", "KoiTail", "KoiEye", "WaveHalo", "Spout" } do
        if not meshTemplate(name) then
            return false
        end
    end
    return true
end

function TidecallerAura.build(player, character, rootPart, petId, rankId)
    if not TidecallerAura.isReady() then
        return nil
    end
    local _, boxSize = character:GetBoundingBox()
    local height = math.clamp(boxSize.Y, 3, 12)
    local boost = AuraStyles.getBoost(rankId)
    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"

    local aura = {
        player = player,
        character = character,
        rootPart = rootPart,
        model = model,
        boost = boost,
        k = height / 5 * (1 + (boost - 1) * 0.35),
        detail = if player == Players.LocalPlayer then 1 else SETTINGS.OtherPlayers,
        random = Random.new(),
        meshes = {},
        emitters = {},
        stage = 0,
        power = 0,
        bloom = 0,
        koiLevel = 0,
        haloLevel = 0,
        spoutLevel = 0,
        spin = 0,
        rush = 0,
        surgeAt = -math.huge,
        nextGroundCheck = 0,
        hiding = false,
        destroyed = false,
    }

    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Parent = model
    aura.fader = fader

    buildPool(aura)
    buildLotus(aura)
    buildVortex(aura)
    buildDroplets(aura)
    buildRipples(aura)
    buildKoi(aura)
    buildHalo(aura)
    buildSpouts(aura)
    buildAir(aura)
    return aura
end

local function splash(aura, strength)
    if aura.destroyed or aura.hiding then
        return
    end
    aura.splash:Emit(math.round(36 * strength * aura.detail))
    aura.surgeAt = os.clock()
    aura.surgeStrength = strength
    aura.nextRipple = 0
end

function TidecallerAura.show(aura)
    local now = os.clock()
    aura.shownAt = now
    TweenService:Create(aura.fader, FADE_IN, { Value = 1 }):Play()
    for _, stream in aura.streams do
        stream.Trail.Enabled = true
    end
    task.delay(SETTINGS.ChargeSeconds, function()
        if aura.destroyed or aura.hiding then
            return
        end
        aura.stage = 1
        for _, stream in aura.streams do
            stream.Trail.Enabled = false
        end
        splash(aura, 1)
    end)
end

function TidecallerAura.hide(aura)
    if aura.hiding then
        return
    end
    aura.hiding = true
    aura.hiddenAt = os.clock()
    TweenService:Create(aura.fader, FADE_OUT, { Value = 0 }):Play()
    for _, stream in aura.streams do
        stream.Trail.Enabled = false
    end
    for _, fish in aura.koi do
        fish.Trail.Enabled = false
    end
    if aura.stage > 0 then
        aura.splash:Emit(math.round(20 * aura.detail))
    end
end

function TidecallerAura.pulse(aura)
    splash(aura, 1)
end

function TidecallerAura.destroy(aura)
    aura.destroyed = true
    aura.model:Destroy()
end

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Exclude
groundParams.IgnoreWater = true

local function updateStage(aura, now)
    if aura.stage == 0 or aura.hiding then
        return SETTINGS.Stages[math.max(aura.stage, 1)]
    end
    local elapsed = now - aura.shownAt - SETTINGS.ChargeSeconds
    local nextStage = SETTINGS.Stages[aura.stage + 1]
    if nextStage and elapsed >= nextStage.After then
        aura.stage += 1
        splash(aura, 1)
        if aura.stage == 2 then
            for _, fish in aura.koi do
                fish.Trail.Enabled = true
            end
        end
    end
    local settings = SETTINGS.Stages[aura.stage]
    if settings.SurgeEvery and now >= (aura.nextSurge or 0) then
        if aura.nextSurge then
            splash(aura, 0.7)
        end
        aura.nextSurge = now + settings.SurgeEvery * aura.random:NextNumber(0.85, 1.2)
    end
    return settings
end

function TidecallerAura.update(aura, now, parts, cframes)
    local s = aura.k
    local deltaTime = math.min(now - (aura.lastUpdate or now), 0.1)
    aura.lastUpdate = now
    local rootCFrame = aura.rootPart.CFrame
    local fade = aura.fader.Value
    local settings = updateStage(aura, now)
    local live = not aura.hiding

    aura.power = approach(aura.power, if aura.stage == 0 then 0.25 else settings.Power, 2, deltaTime)
    local level = fade * aura.power
    local surge = math.max(0, 1 - (now - aura.surgeAt) / 1.2) * (aura.surgeStrength or 1)
    aura.bloom = approach(aura.bloom, if live and aura.stage > 0 then 1 else 0, if live then 2.2 else 3.5, deltaTime)
    aura.koiLevel = approach(aura.koiLevel, if live and aura.stage >= 2 then 1 else 0, 2, deltaTime)
    aura.haloLevel = approach(aura.haloLevel, if live and aura.stage >= 3 then 1 else 0, 1.6, deltaTime)
    aura.spoutLevel = approach(aura.spoutLevel, if live and aura.stage >= 3 then 1 else 0, 1.8, deltaTime)
    aura.spin += deltaTime * (0.6 + 0.5 * aura.power + 2.2 * surge)

    for _, entry in aura.emitters do
        entry.Emitter.Rate = if aura.stage >= entry.MinStage and live then entry.Rate * level else 0
    end

    if now >= aura.nextGroundCheck then
        aura.nextGroundCheck = now + 0.25
        local boxCFrame, boxSize = aura.character:GetBoundingBox()
        aura.seatY = boxCFrame.Position.Y - boxSize.Y / 2
        groundParams.FilterDescendantsInstances = { aura.character, aura.model, workspace:FindFirstChild("PetCompanions") }
        local hit = workspace:Raycast(aura.rootPart.Position, Vector3.new(0, -MAX_GROUND_DROP, 0), groundParams)
        aura.groundY = if hit then hit.Position.Y else nil
    end
    local position = rootCFrame.Position
    local seat = Vector3.new(position.X, aura.seatY - 0.1 * s, position.Z)
    local floorY = aura.groundY or (seat.Y - 1.2 * s)
    local floor = Vector3.new(position.X, floorY + 0.06, position.Z)
    local facing = CFrame.lookAt(Vector3.zero, Vector3.new(rootCFrame.LookVector.X, 0, rootCFrame.LookVector.Z))
    local spin = aura.spin

    local function place(part, cframe)
        table.insert(parts, part)
        table.insert(cframes, cframe)
    end
    local function show(part, base, amount)
        if part.Material == Enum.Material.Glass then
            part.Transparency = if amount > 0.04 then base else 1
        else
            part.Transparency = 1 - (1 - base) * math.clamp(amount, 0, 1)
        end
    end

    place(aura.pool, CFrame.new(floor) * CFrame.Angles(0, spin * 0.05, 0))
    for _, entry in aura.poolImages do
        entry.Image.ImageTransparency = 1 - (1 - entry.Transparency) * fade * (0.75 + 0.25 * aura.power + 0.3 * surge)
    end
    aura.caustics[1].Rotation = math.deg(now * 0.07) % 360
    aura.caustics[2].Rotation = -math.deg(now * 0.11) % 360
    aura.caustics[2].Size = UDim2.fromScale(0.78 + 0.04 * math.sin(now * 0.8), 0.78 + 0.04 * math.sin(now * 0.8))
    place(aura.basin, CFrame.new(floor + Vector3.new(0, 0.2 * s, 0)))
    place(aura.volume, CFrame.new(seat + Vector3.new(0, 2 * s, 0)))
    place(aura.cloud, CFrame.new(seat + Vector3.new(0, 7.5 * s, 0)))

    local charge = if aura.shownAt then math.clamp((now - aura.shownAt) / SETTINGS.ChargeSeconds, 0, 1) else 0
    for _, stream in aura.streams do
        local radius = (1 - charge) * 7 * s + 0.3 * s
        local angle = stream.Angle + charge * 2.6 + spin * 0.2
        place(stream.Part, CFrame.new(seat + Vector3.new(math.cos(angle) * radius, charge * 2.2 * s, math.sin(angle) * radius)))
    end

    for _, petal in aura.petals do
        local open = smoothstep(petal.Delay, petal.Delay + 0.75, aura.bloom)
        local tilt = 0.18 + (petal.Open - 0.18) * open + 0.05 * math.sin(now * 1.3 + petal.Angle * 2) + 0.12 * surge
        local turn = petal.Angle + spin * (if petal.Ring == 1 then 0.08 else -0.12)
        place(petal.Part, CFrame.new(seat) * CFrame.Angles(0, turn, 0) * CFrame.new(0, 0, -petal.Radius)
            * CFrame.Angles(-tilt, 0, 0) * CFrame.new(0, petal.Length / 2, 0))
        show(petal.Part, STYLE.Materials[STYLE.Lotus[petal.Ring].Kind].Transparency, fade * (0.3 + 0.7 * aura.bloom))
    end
    place(aura.pearl, CFrame.new(seat + Vector3.new(0, 0.35 * s + 0.05 * s * math.sin(now * 2), 0)))
    show(aura.pearl, 0.25, fade * aura.bloom)
    aura.pearl.Size = Vector3.one * (0.5 + 0.12 * math.sin(now * 2.4) + 0.4 * surge) * s

    for _, spiral in aura.spirals do
        local rise = 0.35 + 0.65 * aura.bloom
        place(spiral.Part, CFrame.new(seat + Vector3.new(0, spiral.Height / 2 * rise + spiral.Lift + 0.12 * s * math.sin(now * 0.9 + spiral.Phase), 0))
            * CFrame.Angles(0, spiral.Phase + spin * spiral.Speed, 0))
        show(spiral.Part, STYLE.Materials[spiral.Kind].Transparency, fade * aura.bloom * (0.7 + 0.3 * aura.power))
    end

    for index, drop in aura.droplets do
        local angle = drop.Angle + spin * 0.55
        local tiltCF = CFrame.Angles(math.rad(16), 0, math.rad(9))
        local orbit = Vector3.new(math.cos(angle), 0, math.sin(angle)) * drop.Radius * (0.6 + 0.4 * aura.bloom)
        local offset = tiltCF:VectorToWorldSpace(orbit) + Vector3.new(0, (drop.Height * 4 + 0.15 * math.sin(now * 1.7 + drop.Phase)) * s, 0)
        local velocity = tiltCF:VectorToWorldSpace(Vector3.new(-math.sin(angle), 0, math.cos(angle)))
        local at = seat + offset
        place(drop.Part, CFrame.lookAt(at, at + velocity) * CFrame.Angles(math.pi / 2, 0, 0))
        local presence = fade * aura.bloom
        drop.Part.Size = drop.Size * math.max(0.05, presence)
        show(drop.Part, STYLE.Materials.Droplet.Transparency, presence)
    end

    if live and aura.stage > 0 and now >= aura.nextRipple then
        aura.nextRipple = now + STYLE.Ripples.Every / (0.6 + 0.6 * aura.power)
        aura.ripples[aura.rippleIndex].Born = now
        aura.rippleIndex = aura.rippleIndex % #aura.ripples + 1
    end
    for _, ripple in aura.ripples do
        local age = (now - ripple.Born) / STYLE.Ripples.Seconds
        if age < 1 then
            local radius = (0.8 + STYLE.Ripples.Reach * age ^ 0.7) * s
            ripple.Part.Size = aura.rippleBase * radius * 2 * Vector3.new(1, 1 + 2 * (1 - age), 1)
            place(ripple.Part, CFrame.new(floor + Vector3.new(0, 0.05, 0)))
            show(ripple.Part, STYLE.Materials.Ripple.Transparency, fade * (1 - age) ^ 1.3)
        else
            ripple.Part.Transparency = 1
        end
    end

    for _, fish in aura.koi do
        local speed = 0.75 + 0.25 * aura.power + 0.8 * surge
        fish.Angle = (fish.Angle or fish.Phase) + deltaTime * speed * fish.Direction
        local angle = fish.Angle
        local radius = fish.Radius * (0.5 + 0.5 * aura.koiLevel) * (1 + 0.12 * math.sin(angle * 2))
        local height = (fish.Height * 4 + 0.6 * math.sin(angle * 2 + fish.Phase)) * s - (1 - aura.koiLevel) * 2 * s
        local at = seat + Vector3.new(math.cos(angle) * radius, height, math.sin(angle) * radius)
        local ahead = angle + 0.15 * fish.Direction
        local nextRadius = fish.Radius * (0.5 + 0.5 * aura.koiLevel) * (1 + 0.12 * math.sin(ahead * 2))
        local target = seat + Vector3.new(math.cos(ahead) * nextRadius, (fish.Height * 4 + 0.6 * math.sin(ahead * 2 + fish.Phase)) * s, math.sin(ahead) * nextRadius)
        local swim = now * 7 + fish.Phase
        local bodyCF = CFrame.lookAt(at, target) * CFrame.Angles(0, 0.12 * math.sin(swim), 0.18 * math.sin(angle) * fish.Direction)
        place(fish.Body, bodyCF)
        place(fish.Eye, bodyCF * fish.EyeOffset)
        place(fish.Tail, bodyCF * fish.Pivot * CFrame.Angles(0, 0.45 * math.sin(swim - 0.9), 0) * fish.TailFromPivot)
        for _, part in { fish.Body, fish.Tail } do
            show(part, STYLE.Materials[fish.Kind].Transparency, fade * aura.koiLevel)
        end
        show(fish.Eye, STYLE.Materials.Eye.Transparency, fade * aura.koiLevel)
    end

    local head = aura.character:FindFirstChild("Head")
    local headPosition = if head and head:IsA("BasePart") then head.Position else seat + Vector3.new(0, 3 * s, 0)
    local haloGrow = 0.2 + 0.8 * smoothstep(0, 1, aura.haloLevel) + 0.15 * surge
    local haloCF = CFrame.new(headPosition) * facing * CFrame.new(0, STYLE.Halo.Lift * s, STYLE.Halo.Back * s)
    aura.halo.Size = aura.haloSize * haloGrow
    place(aura.halo, haloCF * CFrame.Angles(0, 0, -spin * 0.45))
    show(aura.halo, STYLE.Materials.Halo.Transparency, fade * aura.haloLevel)

    for _, spout in aura.spouts do
        local rise = smoothstep(0, 1, aura.spoutLevel) * (0.9 + 0.1 * math.sin(now * 1.6 + spout.Phase)) + 0.15 * surge * aura.spoutLevel
        local angle = spout.Angle + spin * 0.12
        local base = floor + Vector3.new(math.cos(angle), 0, math.sin(angle)) * STYLE.Spouts.Radius * s
        local size = Vector3.new(spout.Size.X, spout.Size.Y * math.max(rise, 0.02), spout.Size.Z)
        spout.Part.Size = size
        local sway = CFrame.Angles(0.06 * math.sin(now * 1.1 + spout.Phase), 0, 0.06 * math.cos(now * 0.9 + spout.Phase))
        local cframe = CFrame.new(base) * sway * CFrame.new(0, size.Y / 2, 0) * CFrame.Angles(0, now * 1.4 + spout.Phase, 0)
        place(spout.Part, cframe)
        spout.Top.Position = Vector3.new(0, size.Y / 2, 0)
        show(spout.Part, STYLE.Materials.Spout.Transparency, fade * math.min(1, aura.spoutLevel * 1.5))
        spout.Spray.Rate = if live and aura.spoutLevel > 0.6 then 10 * aura.detail else 0
    end

    local breathe = 0.85 + 0.15 * math.sin(now * 2)
    aura.light.Brightness = (1.4 * level * breathe + 3 * surge) * fade
    aura.highlight.FillTransparency = 1 - math.min(0.9, (0.06 * level + 0.15 * surge) * fade)
    aura.highlight.OutlineTransparency = 1 - math.min(1, (0.35 * level + 0.3 * surge) * fade)
end

return TidecallerAura

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))
local TidecallerAura = require(script.Parent:WaitForChild("TidecallerAura"))
local EmberCrucibleAura = require(script.Parent:WaitForChild("EmberCrucibleAura"))
local VerdantGaleAura = require(script.Parent:WaitForChild("VerdantGaleAura"))

local CharacterAura = {}

CharacterAura.REMOVE_DELAY = 2.2

local SETTINGS = AuraStyles.CharacterAura
local DESIGNS = {
    AquaWisp = TidecallerAura,
    EmberWyrm = EmberCrucibleAura,
}
local TEXTURES = SETTINGS.Textures
local TAU = 2 * math.pi
local FADE_IN = TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(0.9, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local POP_IN = TweenInfo.new(0.55, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local POP_OUT = TweenInfo.new(0.6, Enum.EasingStyle.Back, Enum.EasingDirection.In)
local GROUND_CHECK_SECONDS = 0.3
local MAX_GROUND_DROP = 14

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence
local newPart = AuraKit.newPart

local function newAttachment(parent, position)
    local attachment = Instance.new("Attachment")
    attachment.Position = position or Vector3.zero
    attachment.Parent = parent
    return attachment
end

local addEmitter = AuraKit.addEmitter

local function flameProperties(aura, size, colors, extra)
    local k = aura.k
    local properties = {
        Texture = TEXTURES.Flame,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
        FlipbookMode = Enum.ParticleFlipbookMode.Loop,
        FlipbookFramerate = NumberRange.new(18, 26),
        FlipbookStartRandom = true,
        Color = colors,
        LightEmission = 0.7,
        Brightness = 2.6,
        Size = numberSequence({ { 0, size * 0.35 * k }, { 0.3, size * k }, { 0.75, size * 0.8 * k }, { 1, size * 0.35 * k } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.12, 0.2 }, { 0.7, 0.45 }, { 1, 1 } }),
        Rotation = NumberRange.new(-10, 10),
        RotSpeed = NumberRange.new(-25, 25),
        EmissionDirection = Enum.NormalId.Top,
    }
    for property, value in extra do
        properties[property] = value
    end
    return properties
end

local function measureBody(character, rootPart)
    local rootCFrame = rootPart.CFrame
    local boxCFrame, boxSize = character:GetBoundingBox()
    local feetY = rootCFrame:PointToObjectSpace(boxCFrame.Position).Y - boxSize.Y / 2
    local head = character:FindFirstChild("Head")
    local headTopY = if head and head:IsA("BasePart")
        then rootCFrame:PointToObjectSpace(head.Position).Y + head.Size.Y / 2
        else feetY + 5.3
    return { FeetY = feetY, Height = math.clamp(headTopY - feetY, 3, 12) }
end

local function bodyPart(character, names, fallback)
    for _, name in names do
        local part = character:FindFirstChild(name)
        if part and part:IsA("BasePart") then
            return part
        end
    end
    return fallback
end

local function ringPart(aura, name, diameter, color, transparency, faces)
    local part = newPart(aura, name, Vector3.new(diameter, 0.05, diameter))
    local images = {}
    for _, face in faces do
        local gui = Instance.new("SurfaceGui")
        gui.Face = face
        gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
        gui.PixelsPerStud = 48
        gui.LightInfluence = 0
        gui.Brightness = 2.4
        gui.MaxDistance = 300
        gui.Parent = part
        local image = Instance.new("ImageLabel")
        image.AnchorPoint = Vector2.new(0.5, 0.5)
        image.Position = UDim2.fromScale(0.5, 0.5)
        image.Size = UDim2.fromScale(1, 1)
        image.BackgroundTransparency = 1
        image.Image = TEXTURES.Ring
        image.ImageColor3 = color
        image.ImageTransparency = 1
        image.Parent = gui
        local scale = Instance.new("UIScale")
        scale.Scale = 0
        scale.Parent = image
        table.insert(images, { Image = image, Scale = scale, Transparency = transparency })
    end
    return part, images
end

local function buildFlames(aura)
    local body, colors, k = aura.body, aura.colors, aura.k
    local flameColors = colorSequence({ { 0, colors.Core }, { 0.35, colors.Main }, { 1, colors.Deep } })

    local base = newPart(aura, "FlameBase", Vector3.new(aura.width * 1.5, body.Height * 0.35, aura.width * 1.5))
    aura.flameBase = base

    aura.flames = addEmitter(aura, base, 26, flameProperties(aura, 4, flameColors, {
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(0.75, 1.05),
        Speed = NumberRange.new(4, 6),
        SpreadAngle = Vector2.new(10, 10),
        Acceleration = Vector3.new(0, 5, 0),
        Drag = 1,
        ZOffset = -1,
    }))
    aura.frontFlames = addEmitter(aura, base, 9, flameProperties(aura, 2.4, flameColors, {
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(0.6, 0.85),
        Speed = NumberRange.new(4, 5.5),
        SpreadAngle = Vector2.new(8, 8),
        Acceleration = Vector3.new(0, 5, 0),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.55 }, { 0.7, 0.7 }, { 1, 1 } }),
        ZOffset = 0.6,
    }))

    for _, names in { { "UpperTorso", "Torso" }, { "LowerTorso" }, { "LeftUpperArm", "Left Arm" }, { "RightUpperArm", "Right Arm" },
        { "LeftUpperLeg", "Left Leg" }, { "RightUpperLeg", "Right Leg" }, { "Head" } } do
        local part = bodyPart(aura.character, names, nil)
        if part then
            local emitter = addEmitter(aura, part, if names[1] == "Head" then 4 else 6, flameProperties(aura, 2.3, flameColors, {
                Lifetime = NumberRange.new(0.45, 0.7),
                Speed = NumberRange.new(2.5, 3.5),
                SpreadAngle = Vector2.new(25, 25),
                Acceleration = Vector3.new(0, 5, 0),
                Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.3 }, { 0.7, 0.5 }, { 1, 1 } }),
                ZOffset = -0.8,
            }))
            table.insert(aura.limbAttachments, emitter)
        end
    end

    local torso = bodyPart(aura.character, { "UpperTorso", "Torso" }, aura.rootPart)
    local chest = newAttachment(torso)
    table.insert(aura.limbAttachments, chest)
    aura.coreFlames = addEmitter(aura, chest, 11, flameProperties(aura, 2, colorSequence({ { 0, colors.Core }, { 1, colors.Main } }), {
        Lifetime = NumberRange.new(0.45, 0.65),
        Speed = NumberRange.new(2, 3),
        SpreadAngle = Vector2.new(20, 20),
        Acceleration = Vector3.new(0, 4, 0),
        LightEmission = 0.85,
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.35 }, { 1, 1 } }),
        ZOffset = -0.3,
    }))

    for _, names in { { "RightHand", "Right Arm" }, { "LeftHand", "Left Arm" } } do
        local hand = bodyPart(aura.character, names, nil)
        if hand then
            local point = newAttachment(hand)
            table.insert(aura.limbAttachments, point)
            addEmitter(aura, point, 7, flameProperties(aura, 0.9, flameColors, {
                Lifetime = NumberRange.new(0.35, 0.55),
                Speed = NumberRange.new(1.5, 2.5),
                SpreadAngle = Vector2.new(15, 15),
                Acceleration = Vector3.new(0, 3, 0),
            }))
        end
    end

    aura.sparks = addEmitter(aura, base, 14, {
        Texture = TEXTURES.Spark,
        Orientation = Enum.ParticleOrientation.VelocityParallel,
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Color = ColorSequence.new(colors.Core, colors.Main),
        LightEmission = 0.9,
        Brightness = 3.5,
        Size = numberSequence({ { 0, 0.55 * k }, { 1, 0.15 * k } }),
        Lifetime = NumberRange.new(0.35, 0.7),
        Speed = NumberRange.new(7, 12),
        SpreadAngle = Vector2.new(18, 18),
        Acceleration = Vector3.new(0, 4, 0),
        EmissionDirection = Enum.NormalId.Top,
    })

    addEmitter(aura, aura.volume, 12, {
        Texture = TEXTURES.Glow,
        Shape = Enum.ParticleEmitterShape.Box,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Color = ColorSequence.new(colors.Core, colors.Main),
        LightEmission = 0.8,
        Brightness = 3,
        Size = numberSequence({ { 0, 0 }, { 0.2, 0.28 * k }, { 0.5, 0.14 * k }, { 0.8, 0.26 * k }, { 1, 0 } }),
        Lifetime = NumberRange.new(1.5, 2.5),
        Speed = NumberRange.new(0.5, 1.5),
        SpreadAngle = Vector2.new(180, 180),
        Acceleration = Vector3.new(0, 1.2, 0),
        Drag = 0.5,
    })

    local gather = newPart(aura, "Gather", Vector3.one * body.Height * 1.7)
    aura.gatherPart = gather
    aura.gather = Instance.new("ParticleEmitter")
    local gatherEmitter = aura.gather
    gatherEmitter.Texture = TEXTURES.Spark
    gatherEmitter.Orientation = Enum.ParticleOrientation.VelocityParallel
    gatherEmitter.Shape = Enum.ParticleEmitterShape.Sphere
    gatherEmitter.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
    gatherEmitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    gatherEmitter.Color = ColorSequence.new(colors.Core, colors.Main)
    gatherEmitter.LightInfluence = 0
    gatherEmitter.LightEmission = 0.9
    gatherEmitter.Brightness = 3.5
    gatherEmitter.Size = numberSequence({ { 0, 0.2 * k }, { 0.6, 0.7 * k }, { 1, 0 } })
    gatherEmitter.Lifetime = NumberRange.new(0.32, 0.42)
    gatherEmitter.Speed = NumberRange.new(10, 13)
    gatherEmitter.Rate = 0
    gatherEmitter.Parent = gather
end

local function buildTongues(aura)
    local body, colors, k = aura.body, aura.colors, aura.k
    local ring = newPart(aura, "Tongues", Vector3.one * 0.2)
    aura.tongueRing = ring
    aura.tongues = {}
    local count = SETTINGS.Tongues
    local radius = aura.width * 0.72
    for index = 1, count do
        local angle = (index - 1) / count * TAU
        local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
        local tall = if index % 2 == 0 then 1.35 else 1.05
        local bottom = Instance.new("Attachment")
        bottom.CFrame = CFrame.lookAt(out * radius, out * radius + (out + Vector3.new(0, 2.2, 0)).Unit)
            * CFrame.Angles(0, math.rad(90), 0)
        bottom.Parent = ring
        local topBase = out * radius * 0.55 + Vector3.new(0, body.Height * tall, 0)
        local top = Instance.new("Attachment")
        top.CFrame = CFrame.new(topBase) * CFrame.Angles(0, 0, math.rad(90))
        top.Parent = ring

        local beam = Instance.new("Beam")
        beam.Attachment0 = bottom
        beam.Attachment1 = top
        beam.CurveSize0 = body.Height * 0.3
        beam.CurveSize1 = body.Height * 0.25
        beam.Segments = 16
        beam.FaceCamera = true
        beam.Texture = TEXTURES.Streak
        beam.TextureMode = Enum.TextureMode.Wrap
        beam.TextureLength = 2.6 * k
        beam.TextureSpeed = 1.3
        beam.LightInfluence = 0
        beam.LightEmission = 0.65
        beam.Brightness = 2.4
        beam.Color = colorSequence({ { 0, colors.Deep }, { 0.45, colors.Main }, { 1, colors.Core } })
        beam.Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.35 }, { 0.6, 0.45 }, { 1, 1 } })
        beam.Width0 = 0
        beam.Width1 = 0
        beam.ZOffset = -0.5
        beam.Parent = ring
        table.insert(aura.tongues, { Beam = beam, Top = top, TopBase = topBase, Width = 0.95 * k * (if tall > 1.2 then 1.1 else 1), Phase = index * 1.9 })
    end
end

local function buildRibbons(aura)
    local colors, k = aura.colors, aura.k
    aura.ribbons = {}
    for index = 1, SETTINGS.Ribbons do
        local point = newPart(aura, "Ribbon" .. index, Vector3.one * 0.2)
        local top = newAttachment(point, Vector3.new(0, 0.18 * k, 0))
        local bottom = newAttachment(point, Vector3.new(0, -0.18 * k, 0))
        local trail = Instance.new("Trail")
        trail.Attachment0 = top
        trail.Attachment1 = bottom
        trail.Texture = TEXTURES.Streak
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.FaceCamera = true
        trail.Lifetime = 0.55
        trail.MinLength = 0.05
        trail.LightInfluence = 0
        trail.LightEmission = 0.85
        trail.Brightness = 2.6
        trail.Color = ColorSequence.new(colors.Core, colors.Main)
        trail.Transparency = numberSequence({ { 0, 0.05 }, { 1, 1 } })
        trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0.15 } })
        trail.Enabled = false
        trail.Parent = point
        table.insert(aura.ribbons, { Part = point, Trail = trail, Offset = (index - 1) / SETTINGS.Ribbons, Last = 0 })
    end
end

local function buildRings(aura)
    local body, colors = aura.body, aura.colors
    local faces = { Enum.NormalId.Top, Enum.NormalId.Bottom }
    aura.waistRing, aura.waistImages = ringPart(aura, "WaistRing", aura.width * 2.1, colors.Main, 0.1, faces)
    aura.halo, aura.haloImages = ringPart(aura, "Halo", body.Height * 0.75, colors.Core, 0.05, faces)
    for _, list in { aura.waistImages, aura.haloImages } do
        for _, entry in list do
            entry.Image.Parent.Brightness = 4
        end
    end
end

local function buildGround(aura)
    local body, colors, k = aura.body, aura.colors, aura.k
    local diameter = math.min(body.Height * 2.4, 24)
    local ground, images = ringPart(aura, "Ground", diameter, colors.Main, 0.25, { Enum.NormalId.Top })
    aura.ground = ground
    aura.groundImages = images
    local gui = images[1].Image.Parent
    local pool = Instance.new("ImageLabel")
    pool.AnchorPoint = Vector2.new(0.5, 0.5)
    pool.Position = UDim2.fromScale(0.5, 0.5)
    pool.Size = UDim2.fromScale(1.1, 1.1)
    pool.BackgroundTransparency = 1
    pool.Image = TEXTURES.Glow
    pool.ImageColor3 = colors.Deep
    pool.ImageTransparency = 1
    pool.ZIndex = 0
    pool.Parent = gui
    table.insert(aura.groundImages, { Image = pool, Transparency = 0.55 })
    local inner = images[1].Image:Clone()
    inner.Size = UDim2.fromScale(0.45, 0.45)
    inner.ImageColor3 = colors.Core
    inner.Parent = gui
    table.insert(aura.groundImages, { Image = inner, Scale = inner:FindFirstChildOfClass("UIScale"), Transparency = 0.2 })
    aura.innerSigil = inner

    local center = newAttachment(ground)
    aura.shockwave = Instance.new("ParticleEmitter")
    local shock = aura.shockwave
    shock.Texture = TEXTURES.Shockwave
    shock.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
    shock.EmissionDirection = Enum.NormalId.Top
    shock.Speed = NumberRange.new(0.01)
    shock.Color = ColorSequence.new(colors.Core, colors.Main)
    shock.LightInfluence = 0
    shock.LightEmission = 0.8
    shock.Brightness = 3
    shock.Size = numberSequence({ { 0, 0.6 * k }, { 1, 6.5 * k } })
    shock.Transparency = numberSequence({ { 0, 0.05 }, { 0.6, 0.5 }, { 1, 1 } })
    shock.Lifetime = NumberRange.new(0.9)
    shock.LockedToPart = true
    shock.Rate = 0
    shock.Parent = center

    aura.dust = addEmitter(aura, center, 6, {
        Texture = TEXTURES.Smoke,
        Color = ColorSequence.new(colors.Deep:Lerp(Color3.new(0.75, 0.75, 0.78), 0.55)),
        LightEmission = 0,
        Size = numberSequence({ { 0, 0.8 * k }, { 1, 2.6 * k } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.78 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1, 1.6),
        Speed = NumberRange.new(3, 5),
        SpreadAngle = Vector2.new(85, 85),
        Drag = 3,
        Acceleration = Vector3.new(0, 0.6, 0),
        Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-30, 30),
    })

    aura.rocks = {}
    local random = Random.new(aura.player.UserId)
    for index = 1, SETTINGS.Rocks do
        local size = random:NextNumber(0.22, 0.48) * k
        local shapes = { Enum.PartType.Wedge, Enum.PartType.CornerWedge, Enum.PartType.Block }
        local rock = newPart(aura, "Rock" .. index, Vector3.new(size, size * random:NextNumber(0.5, 0.9), size * random:NextNumber(0.7, 1.3)),
            shapes[(index - 1) % #shapes + 1])
        rock.Material = Enum.Material.Slate
        rock.Color = Color3.fromRGB(78, 76, 84):Lerp(colors.Deep, 0.15)
        table.insert(aura.rocks, {
            Part = rock,
            Angle = (index - 1) / SETTINGS.Rocks * TAU + random:NextNumber(-0.3, 0.3),
            Distance = aura.width * random:NextNumber(0.9, 1.5),
            Height = body.Height * random:NextNumber(0.25, 0.8),
            Spin = Vector3.new(random:NextNumber(-1, 1), random:NextNumber(-1, 1), random:NextNumber(-1, 1)),
            Phase = random:NextNumber(0, TAU),
        })
    end
end

local function buildLightning(aura)
    local colors, k = aura.colors, aura.k
    aura.arcs = {}
    for index = 1, SETTINGS.Arcs do
        local points = {}
        for point = 1, 7 do
            points[point] = newAttachment(aura.volume)
        end
        local beams = {}
        for segment = 1, 6 do
            local beam = Instance.new("Beam")
            beam.Attachment0 = points[segment]
            beam.Attachment1 = points[segment + 1]
            beam.Segments = 1
            beam.FaceCamera = true
            beam.Width0 = 0.13 * k
            beam.Width1 = 0.13 * k
            beam.LightInfluence = 0
            beam.LightEmission = 1
            beam.Brightness = 5
            beam.Color = ColorSequence.new(colors.Core)
            beam.Transparency = NumberSequence.new(1)
            beam.Parent = aura.volume
            beams[segment] = beam
        end
        aura.arcs[index] = { Points = points, Beams = beams, Ends = 0, Rejag = 0 }
    end
end

local function buildGlow(aura)
    local colors = aura.colors
    local light = Instance.new("PointLight")
    light.Color = colors.Main
    light.Range = 16 * aura.k
    light.Brightness = 0
    light.Shadows = false
    light.Parent = aura.volume
    aura.light = light

    local glow = Instance.new("Highlight")
    glow.Name = "AuraGlow"
    glow.Adornee = aura.character
    glow.DepthMode = Enum.HighlightDepthMode.Occluded
    glow.FillColor = colors.Main
    glow.OutlineColor = colors.Core
    glow.FillTransparency = 1
    glow.OutlineTransparency = 1
    glow.Parent = aura.model
    aura.highlight = glow
end

local function strikeArc(aura, arc, now)
    local body, width = aura.body, aura.width
    local random = aura.random
    local angle = random:NextNumber(0, TAU)
    local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
    local start = out * width * 0.3 + Vector3.new(0, random:NextNumber(-0.3, 0.3) * body.Height, 0)
    local finish = (out * math.cos(0.5) + Vector3.new(-out.Z, 0, out.X) * math.sin(0.5) * random:NextNumber(-1, 1)).Unit
        * width * random:NextNumber(1.1, 1.6) + Vector3.new(0, random:NextNumber(-0.45, 0.5) * body.Height, 0)
    arc.Start, arc.Finish = start, finish
    arc.Ends = now + 0.2
    arc.Rejag = 0
end

local function jagArc(aura, arc)
    local random = aura.random
    local count = #arc.Points
    local direction = arc.Finish - arc.Start
    local side = direction:Cross(Vector3.yAxis)
    side = if side.Magnitude > 0.01 then side.Unit else Vector3.xAxis
    local up = side:Cross(direction).Unit
    for index, point in arc.Points do
        local t = (index - 1) / (count - 1)
        local jitter = math.sin(t * math.pi) * 0.45 * aura.k
        point.Position = arc.Start:Lerp(arc.Finish, t)
            + side * random:NextNumber(-jitter, jitter) + up * random:NextNumber(-jitter, jitter)
    end
end

local function surge(aura, strength)
    if aura.destroyed or aura.hiding then
        return
    end
    local now = os.clock()
    aura.flames:Emit(math.round(16 * strength * aura.detail))
    aura.coreFlames:Emit(math.round(6 * strength))
    aura.sparks:Emit(math.round(22 * strength * aura.detail))
    aura.shockwave:Emit(1)
    task.delay(0.18, function()
        if not aura.destroyed then
            aura.shockwave:Emit(1)
        end
    end)
    for index, arc in aura.arcs do
        if index <= math.ceil(#aura.arcs * strength) then
            task.delay((index - 1) * 0.05, function()
                if not aura.destroyed then
                    strikeArc(aura, arc, os.clock())
                end
            end)
        end
    end
    aura.flashUntil = now + 0.7
    aura.flashStrength = strength
    aura.spinBoostUntil = now + 1.2
    for _, entry in aura.allImages do
        if entry.Scale then
            entry.Scale.Scale = 1.25
            TweenService:Create(entry.Scale, POP_IN, { Scale = 1 }):Play()
        end
    end
end

-- Whether a pet has its own aura design (Tidecaller, Ember Crucible): those layer over the realm
-- aura (RealmAura) while the player meditates; every other look is the realm aura's now.
function CharacterAura.hasPetDesign(petId)
    return petId ~= nil and DESIGNS[petId] ~= nil
end

function CharacterAura.build(player, character, rootPart, petId, rankId)
    local design = if petId then DESIGNS[petId] else VerdantGaleAura
    if design then
        local designed = design.build(player, character, rootPart, petId, rankId)
        if designed then
            designed.design = design
            return designed
        end
    end
    local colors = AuraStyles.Elements[petId or "Neutral"] or AuraStyles.Elements.Neutral
    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"
    local body = measureBody(character, rootPart)
    local boost = AuraStyles.getBoost(rankId)

    local aura = {
        player = player,
        character = character,
        rootPart = rootPart,
        model = model,
        colors = colors,
        body = body,
        boost = boost,
        k = body.Height / 5 * (1 + (boost - 1) * 0.35),
        width = body.Height * 0.45,
        detail = if player == Players.LocalPlayer then 1 else SETTINGS.OtherPlayers,
        random = Random.new(),
        emitters = {},
        limbAttachments = {},
        stage = 0,
        power = 0,
        nextPulse = math.huge,
        nextGroundCheck = 0,
        haloLevel = 0,
        rockLevel = 0,
        phase = math.random() * TAU,
        hiding = false,
        destroyed = false,
    }

    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Value = 0
    fader.Parent = model
    aura.fader = fader

    aura.volume = newPart(aura, "Volume", Vector3.new(aura.width, body.Height * 0.9, aura.width))
    buildFlames(aura)
    buildTongues(aura)
    buildRibbons(aura)
    buildRings(aura)
    buildGround(aura)
    buildLightning(aura)
    buildGlow(aura)

    aura.allImages = {}
    for _, list in { aura.waistImages, aura.haloImages, aura.groundImages } do
        for _, entry in list do
            table.insert(aura.allImages, entry)
        end
    end
    return aura
end

function CharacterAura.show(aura)
    if aura.design then
        aura.design.show(aura)
        return
    end
    local now = os.clock()
    aura.shownAt = now
    aura.nextPulse = now + SETTINGS.ChargeSeconds
    aura.nextGroundCheck = 0
    TweenService:Create(aura.fader, FADE_IN, { Value = 1 }):Play()
    aura.gather.Rate = 70 * aura.detail

    task.delay(SETTINGS.ChargeSeconds, function()
        if aura.destroyed or aura.hiding then
            return
        end
        aura.gather.Rate = 0
        aura.stage = 1
        for _, entry in aura.waistImages do
            TweenService:Create(entry.Scale, POP_IN, { Scale = 1 }):Play()
        end
        for _, entry in aura.groundImages do
            if entry.Scale then
                TweenService:Create(entry.Scale, POP_IN, { Scale = 1 }):Play()
            end
        end
        for _, trail in aura.ribbons do
            trail.Trail.Enabled = true
        end
        surge(aura, 1)
    end)
end

function CharacterAura.hide(aura)
    if aura.design then
        aura.design.hide(aura)
        return
    end
    if aura.hiding then
        return
    end
    aura.hiding = true
    aura.gather.Rate = 0
    TweenService:Create(aura.fader, FADE_OUT, { Value = 0 }):Play()
    for _, entry in aura.allImages do
        if entry.Scale then
            TweenService:Create(entry.Scale, POP_OUT, { Scale = 0 }):Play()
        end
    end
    for _, ribbon in aura.ribbons do
        ribbon.Trail.Enabled = false
    end
    if aura.stage > 0 then
        aura.shockwave:Emit(1)
    end
end

function CharacterAura.pulse(aura)
    if aura.design then
        aura.design.pulse(aura)
        return
    end
    surge(aura, 1)
end

function CharacterAura.destroy(aura)
    if aura.design then
        aura.design.destroy(aura)
        return
    end
    aura.destroyed = true
    for _, point in aura.limbAttachments do
        point:Destroy()
    end
    aura.model:Destroy()
end

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Exclude
groundParams.IgnoreWater = true

function CharacterAura.update(aura, now, parts, cframes)
    if aura.design then
        aura.design.update(aura, now, parts, cframes)
        return
    end
    local body, width, k = aura.body, aura.width, aura.k
    local rootCFrame = aura.rootPart.CFrame
    local fade = aura.fader.Value
    local stageSettings = SETTINGS.Stages[math.max(aura.stage, 1)]

    if aura.stage > 0 and not aura.hiding then
        local elapsed = now - aura.shownAt - SETTINGS.ChargeSeconds
        local nextStage = SETTINGS.Stages[aura.stage + 1]
        if nextStage and elapsed >= nextStage.After then
            aura.stage += 1
            stageSettings = nextStage
            surge(aura, 1)
        end
        if stageSettings.SurgeEvery and now >= (aura.nextSurge or 0) then
            if aura.nextSurge then
                surge(aura, 0.7)
            end
            aura.nextSurge = now + stageSettings.SurgeEvery * aura.random:NextNumber(0.85, 1.2)
        end
        if now >= aura.nextPulse then
            aura.shockwave:Emit(1)
            aura.nextPulse = now + stageSettings.PulseEvery
        end
        if stageSettings.LightningEvery and now >= (aura.nextArc or 0) then
            if aura.nextArc then
                strikeArc(aura, aura.arcs[aura.random:NextInteger(1, #aura.arcs)], now)
            end
            aura.nextArc = now + stageSettings.LightningEvery * aura.random:NextNumber(0.6, 1.4)
        end
    end

    local deltaTime = math.min(now - (aura.lastUpdate or now), 0.1)
    aura.lastUpdate = now

    local targetPower = if aura.stage == 0 then 0.15 else stageSettings.Power
    aura.power = AuraKit.approach(aura.power, targetPower, 3.1, deltaTime)
    local level = fade * aura.power
    local flash = 0
    if aura.flashUntil and now < aura.flashUntil then
        flash = (aura.flashUntil - now) / 0.7 * aura.flashStrength
    end

    for _, entry in aura.emitters do
        entry.Emitter.Rate = if aura.stage >= entry.MinStage then entry.Rate * level else 0
    end

    local velocity = aura.rootPart.AssemblyLinearVelocity
    local lean = Vector3.new(-velocity.X, 0, -velocity.Z) * 0.6
    aura.flames.Acceleration = Vector3.new(0, 5, 0) + lean
    aura.frontFlames.Acceleration = aura.flames.Acceleration

    local feet = rootCFrame * CFrame.new(0, body.FeetY, 0)
    table.insert(parts, aura.volume)
    table.insert(cframes, rootCFrame * CFrame.new(0, body.FeetY + body.Height * 0.5, 0))
    table.insert(parts, aura.flameBase)
    table.insert(cframes, rootCFrame * CFrame.new(0, body.FeetY + body.Height * 0.2, 0))
    table.insert(parts, aura.gatherPart)
    table.insert(cframes, rootCFrame * CFrame.new(0, body.FeetY + body.Height * 0.5, 0))

    local spinBoost = if aura.spinBoostUntil and now < aura.spinBoostUntil then 3 else 1
    aura.spin = (aura.spin or aura.phase) + deltaTime * spinBoost
    local spin = aura.spin

    table.insert(parts, aura.tongueRing)
    table.insert(cframes, feet * CFrame.Angles(0, spin * 0.35, 0))
    for _, tongue in aura.tongues do
        local wobble = math.noise(now * 2.2, tongue.Phase)
        local tongueWidth = tongue.Width * level * (0.8 + 0.35 * wobble + 0.4 * flash)
        tongue.Beam.Width0 = math.max(tongueWidth, 0)
        tongue.Beam.Width1 = math.max(tongueWidth * 0.05, 0)
        tongue.Top.Position = tongue.TopBase + Vector3.new(
            math.noise(now * 1.3, tongue.Phase, 1) * 0.5 * k,
            (math.noise(now * 1.7, tongue.Phase, 2) * 0.4 + 0.25 * flash) * body.Height * aura.power,
            math.noise(now * 1.3, tongue.Phase, 3) * 0.5 * k)
    end

    for _, ribbon in aura.ribbons do
        local progress = (now / 2.4 + ribbon.Offset) % 1
        if progress < ribbon.Last then
            ribbon.Trail.Enabled = false
        elseif not ribbon.Trail.Enabled and aura.stage > 0 and not aura.hiding then
            ribbon.Trail.Enabled = true
        end
        ribbon.Last = progress
        local angle = aura.phase + ribbon.Offset * TAU + progress * TAU * 1.5
        local distance = width * 0.95 * (1 - 0.35 * progress)
        table.insert(parts, ribbon.Part)
        table.insert(cframes, feet * CFrame.new(math.cos(angle) * distance, body.Height * (0.05 + 1.15 * progress), math.sin(angle) * distance))
    end

    table.insert(parts, aura.waistRing)
    table.insert(cframes, feet * CFrame.new(0, body.Height * 0.42, 0)
        * CFrame.Angles(math.rad(18 + 5 * math.sin(now * 0.6)), 0, math.rad(8 * math.cos(now * 0.45)))
        * CFrame.Angles(0, spin * 0.7, 0))
    aura.haloLevel = AuraKit.approach(aura.haloLevel, if stageSettings.Halo and not aura.hiding then 1 else 0, 2.45, deltaTime)
    table.insert(parts, aura.halo)
    table.insert(cframes, feet * CFrame.new(0, body.Height * (0.86 + 0.015 * math.sin(now * 1.4)), 0.45 * k)
        * CFrame.Angles(math.rad(90), 0, 0) * CFrame.Angles(0, -spin * 1.2, 0))
    for _, entry in aura.waistImages do
        entry.Image.ImageTransparency = 1 - (1 - entry.Transparency) * fade
    end
    for _, entry in aura.haloImages do
        entry.Image.ImageTransparency = 1 - (1 - entry.Transparency) * fade * aura.haloLevel
        entry.Scale.Scale = aura.haloLevel
    end

    if now >= aura.nextGroundCheck then
        aura.nextGroundCheck = now + GROUND_CHECK_SECONDS
        groundParams.FilterDescendantsInstances = { aura.character, aura.model, workspace:FindFirstChild("PetCompanions") }
        local hit = workspace:Raycast(aura.rootPart.Position, Vector3.new(0, -MAX_GROUND_DROP, 0), groundParams)
        aura.groundY = if hit then hit.Position.Y else nil
    end
    local hasGround = aura.groundY ~= nil
    if not hasGround then
        aura.dust.Rate = 0
    end
    local groundCenter = Vector3.new(rootCFrame.Position.X, (aura.groundY or 0) + 0.06, rootCFrame.Position.Z)
    table.insert(parts, aura.ground)
    table.insert(cframes, CFrame.new(groundCenter) * CFrame.Angles(0, -spin * 0.25, 0))
    for _, entry in aura.groundImages do
        entry.Image.ImageTransparency = if hasGround then 1 - (1 - entry.Transparency) * fade else 1
    end
    aura.innerSigil.Rotation = math.deg(spin * 0.9) % 360

    aura.rockLevel = AuraKit.approach(aura.rockLevel, if stageSettings.Rocks and hasGround and not aura.hiding then 1 else 0, 1.2, deltaTime)
    for _, rock in aura.rocks do
        local lift = aura.rockLevel * (rock.Height + math.sin(now * 1.1 + rock.Phase) * 0.15 * body.Height)
        local angle = rock.Angle + spin * 0.15
        rock.Part.Transparency = if aura.rockLevel > 0.02 then 0 else 1
        table.insert(parts, rock.Part)
        table.insert(cframes, CFrame.new(groundCenter + Vector3.new(math.cos(angle) * rock.Distance, lift + rock.Part.Size.Y / 2, math.sin(angle) * rock.Distance))
            * CFrame.Angles(rock.Spin.X * now * 0.6, rock.Spin.Y * now * 0.6, rock.Spin.Z * now * 0.6))
    end

    for _, arc in aura.arcs do
        local visible = now < arc.Ends and not aura.hiding
        if visible and now >= arc.Rejag then
            jagArc(aura, arc)
            arc.Rejag = now + 0.07
        end
        local transparency = if visible then 0 else 1
        if arc.Shown ~= visible then
            arc.Shown = visible
            for _, beam in arc.Beams do
                beam.Transparency = NumberSequence.new(transparency)
            end
        end
    end

    local breathe = 0.85 + 0.15 * math.sin(now * 2.2)
    aura.light.Brightness = (1.6 * level * breathe + 3 * flash) * fade
    aura.highlight.FillTransparency = 1 - math.min(0.9, (0.16 * level + 0.25 * flash) * fade)
    aura.highlight.OutlineTransparency = 1 - math.min(1, (0.7 * level + 0.3 * flash) * fade)
end

return CharacterAura

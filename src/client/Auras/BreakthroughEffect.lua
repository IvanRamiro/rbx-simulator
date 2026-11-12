local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

local BreakthroughEffect = {}

local SPARK_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"
local FIRE_TEXTURE = "rbxasset://textures/particles/fire_main.dds"
local SPARKS_TEXTURE = "rbxasset://textures/particles/fire_sparks_main.dds"
local FULL_TURN = 2 * math.pi
local QUARTER_ARC_HANDLE = 0.5523
local SHOCKWAVE_PIXELS_PER_STUD = 16
local GROUND_SEARCH = 14

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local function tween(effect, instance, tweenInfo, goal)
    local created = TweenService:Create(instance, tweenInfo, goal)
    created:Play()
    table.insert(effect.tweens, created)
    return created
end

local function later(effect, delay, step)
    task.delay(delay, function()
        if not effect.stopped then
            step()
        end
    end)
end

local function createAnchor(effect, position)
    local part = Instance.new("Part")
    part.Name = "Anchor"
    part.Size = Vector3.new(0.2, 0.2, 0.2)
    part.CFrame = CFrame.new(position)
    part.Anchored = true
    part.Transparency = 1
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Parent = effect.folder
    return part
end

local function createEmitter(parent, properties)
    local emitter = Instance.new("ParticleEmitter")
    emitter.Rate = 0
    emitter.LightInfluence = 0
    emitter.Texture = SPARK_TEXTURE
    for property, value in properties do
        emitter[property] = value
    end
    emitter.Parent = parent
    return emitter
end

local function addFlash(effect, anchor, look)
    local light = Instance.new("PointLight")
    light.Color = look.Element.Main
    light.Brightness = 0
    light.Range = 20 * look.Breakthrough.Scale
    light.Shadows = false
    light.Parent = anchor

    tween(effect, light, TweenInfo.new(0.08), { Brightness = look.Breakthrough.Flash }).Completed:Connect(function()
        if not effect.stopped then
            tween(effect, light, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 })
        end
    end)
end

local function addBursts(effect, anchor, look)
    local element, scale = look.Element, look.Breakthrough.Scale

    local burst = createEmitter(anchor, {
        Color = ColorSequence.new(element.Core, element.Main),
        LightEmission = 1,
        Size = numberSequence({ { 0, 0.55 * scale, 0.2 }, { 1, 0 } }),
        Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Lifetime = NumberRange.new(0.6, 1),
        Speed = NumberRange.new(10 * scale, 16 * scale),
        SpreadAngle = Vector2.new(180, 180),
        Drag = 4,
    })
    burst:Emit(look.Breakthrough.Burst)

    if element.Particles == "Ember" then
        createEmitter(anchor, {
            Texture = FIRE_TEXTURE,
            Color = colorSequence({ { 0, element.Core }, { 0.4, element.Main }, { 1, element.Deep } }),
            LightEmission = 0.9,
            Size = numberSequence({ { 0, 2 * scale, 0.5 }, { 1, 0.4 } }),
            Transparency = numberSequence({ { 0, 0.2 }, { 0.7, 0.5 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.5, 0.8),
            Speed = NumberRange.new(6, 10),
            SpreadAngle = Vector2.new(35, 35),
            Acceleration = Vector3.new(0, 6, 0),
            Rotation = NumberRange.new(0, 360),
            RotSpeed = NumberRange.new(-120, 120),
        }):Emit(math.floor(10 * scale))
    elseif element.Particles == "Droplet" then
        createEmitter(anchor, {
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.8,
            Size = numberSequence({ { 0, 0.45 * scale, 0.15 }, { 1, 0.15 } }),
            Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.9, 1.3),
            Speed = NumberRange.new(8, 12),
            SpreadAngle = Vector2.new(60, 60),
            Acceleration = Vector3.new(0, -25, 0),
            Drag = 0.5,
        }):Emit(math.floor(18 * scale))
    elseif element.Particles == "Crystal" then
        createEmitter(anchor, {
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.9,
            Size = numberSequence({ { 0, 1.4 * scale, 0.3 }, { 1, 0 } }),
            Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.4, 0.6),
            Speed = NumberRange.new(10, 14),
            SpreadAngle = Vector2.new(180, 180),
            Drag = 5,
            Rotation = NumberRange.new(45),
        }):Emit(math.floor(8 * scale))
    elseif element.Particles == "Spark" then
        createEmitter(anchor, {
            Texture = SPARKS_TEXTURE,
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.7,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Size = numberSequence({ { 0, 1 * scale }, { 1, 0.1 } }),
            Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.2, 0.4),
            Speed = NumberRange.new(20, 30),
            SpreadAngle = Vector2.new(180, 180),
            Drag = 6,
        }):Emit(math.floor(24 * scale))
    else
        createEmitter(anchor, {
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 1,
            Size = numberSequence({ { 0, 0.6 * scale, 0.2 }, { 1, 0 } }),
            Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.8),
            Speed = NumberRange.new(3, 6),
            SpreadAngle = Vector2.new(180, 180),
            Acceleration = Vector3.new(0, 2, 0),
            Drag = 1,
        }):Emit(math.floor(14 * scale))
    end
end

local function addPillar(effect, anchor, look, groundOffset)
    local height = look.Breakthrough.PillarHeight
    if height <= 0 then
        return
    end

    local element, scale = look.Element, look.Breakthrough.Scale
    local bottom = Instance.new("Attachment")
    bottom.Position = Vector3.new(0, groundOffset, 0)
    bottom.Parent = anchor
    local top = Instance.new("Attachment")
    top.Position = Vector3.new(0, groundOffset + height, 0)
    top.Parent = anchor

    for layer = 1, 2 do
        local isCore = layer == 2
        local beam = Instance.new("Beam")
        beam.Attachment0 = bottom
        beam.Attachment1 = top
        beam.Segments = 1
        beam.FaceCamera = true
        beam.LightInfluence = 0
        beam.LightEmission = if isCore then 0.7 else 0.8
        beam.Brightness = if isCore then 1.6 else 1.3
        beam.ZOffset = if isCore then 0.1 else 0
        beam.Color = if isCore
            then ColorSequence.new(element.Core, element.Main)
            else colorSequence({ { 0, element.Main }, { 0.6, element.Main }, { 1, element.Deep } })
        beam.Transparency = numberSequence({ { 0, 0.15 }, { 0.6, 0.45 }, { 1, 1 } })
        beam.Width0 = 0
        beam.Width1 = 0
        beam.Parent = anchor

        local width = (if isCore then 0.5 else 3) * scale
        tween(effect, beam, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Width0 = width,
            Width1 = width * 0.5,
        }).Completed:Connect(function()
            if not effect.stopped then
                tween(effect, beam, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Width0 = 0, Width1 = 0 })
            end
        end)
    end
end

local function addExpandingRing(effect, anchor, look, height, endRadius, tilt)
    local element = look.Element
    local sides = if element.RingShape == "Polygon" then element.RingSides else nil
    local count = sides or 4
    local startRadius = 0.8
    local tiltCFrame = CFrame.Angles(math.rad(tilt), 0, math.rad(tilt * 0.5))
    local info = TweenInfo.new(0.8, Enum.EasingStyle.Quart, Enum.EasingDirection.Out)

    local points = {}
    for index = 0, count - 1 do
        local angle = index / count * FULL_TURN
        local outward = tiltCFrame * Vector3.new(math.cos(angle), 0, math.sin(angle))
        local tangent = tiltCFrame * Vector3.new(-math.sin(angle), 0, math.cos(angle))
        local center = Vector3.new(0, height, 0)

        local point = Instance.new("Attachment")
        point.CFrame = CFrame.fromMatrix(center + outward * startRadius, tangent, tangent:Cross(outward).Unit)
        point.Parent = anchor
        tween(effect, point, info, { Position = center + outward * endRadius })
        table.insert(points, point)
    end

    local width = 0.5 * look.Breakthrough.Scale
    for index = 1, count do
        local beam = Instance.new("Beam")
        beam.Attachment0 = points[index]
        beam.Attachment1 = points[index % count + 1]
        beam.Segments = if sides then 1 else 16
        beam.FaceCamera = true
        beam.LightInfluence = 0
        beam.LightEmission = 0.7
        beam.Brightness = 2
        beam.Color = colorSequence({ { 0, element.Deep }, { 0.5, element.Main }, { 1, element.Deep } })
        beam.Transparency = NumberSequence.new(0.1)
        beam.CurveSize0 = if sides then 0 else startRadius * QUARTER_ARC_HANDLE
        beam.CurveSize1 = beam.CurveSize0
        beam.Width0 = width
        beam.Width1 = width
        beam.Parent = anchor

        local handle = if sides then 0 else endRadius * QUARTER_ARC_HANDLE
        tween(effect, beam, info, { CurveSize0 = handle, CurveSize1 = handle, Width0 = 0, Width1 = 0 })
    end
end

local function addStreak(effect, anchor, look, angle, radius, groundOffset)
    local element, scale = look.Element, look.Breakthrough.Scale
    local start = Vector3.new(math.cos(angle) * radius, groundOffset, math.sin(angle) * radius)
    local rise = Vector3.new(0, 10 * scale, 0)
    local halfWidth = Vector3.new(0, 0.15 * scale, 0)

    local above = Instance.new("Attachment")
    above.Position = start + halfWidth
    above.Parent = anchor
    local below = Instance.new("Attachment")
    below.Position = start - halfWidth
    below.Parent = anchor

    local trail = Instance.new("Trail")
    trail.Attachment0 = above
    trail.Attachment1 = below
    trail.Lifetime = 0.25
    trail.FaceCamera = true
    trail.LightInfluence = 0
    trail.LightEmission = 0.9
    trail.Color = colorSequence({ { 0, element.Core }, { 0.3, element.Main }, { 1, element.Deep } })
    trail.Transparency = numberSequence({ { 0, 0 }, { 1, 1 } })
    trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0 } })
    trail.Parent = anchor

    local info = TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
    tween(effect, above, info, { Position = start + halfWidth + rise })
    tween(effect, below, info, { Position = start - halfWidth + rise })
end

local function prepareShockwave(effect, groundPosition, look, layer)
    local element = look.Element
    local part = Instance.new("Part")
    part.Name = "Shockwave"
    part.Size = Vector3.new(1, 0.05, 1)
    part.CFrame = CFrame.new(groundPosition + Vector3.new(0, 0.15 + layer * 0.01, 0))
    part.Anchored = true
    part.Transparency = 1
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Parent = effect.folder

    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Top
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = SHOCKWAVE_PIXELS_PER_STUD
    gui.LightInfluence = 0
    gui.Parent = part

    local ring = Instance.new("Frame")
    ring.Size = UDim2.fromScale(1, 1)
    ring.BackgroundColor3 = element.Main
    ring.BackgroundTransparency = 1
    ring.BorderSizePixel = 0
    ring.Parent = gui
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0.5, 0)
    corner.Parent = ring
    local stroke = Instance.new("UIStroke")
    stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
    stroke.Color = element.Main
    stroke.Thickness = 14
    stroke.Transparency = 1
    stroke.Parent = ring

    return function(diameter)
        stroke.Transparency = 0.05
        ring.BackgroundTransparency = 0.7
        local seconds = 0.9
        tween(effect, part, TweenInfo.new(seconds, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), {
            Size = Vector3.new(diameter, 0.05, diameter),
        })
        tween(effect, stroke, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
        tween(effect, ring, TweenInfo.new(seconds * 0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { BackgroundTransparency = 1 })
    end
end

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Exclude
groundParams.IgnoreWater = true

function BreakthroughEffect.play(container, character, rootPart, rankId, onFinished)
    local element = AuraStyles.Elements.Neutral -- (pets no longer colour it: SET AURA removed, the owner 2026-11-12)
    local breakthrough = AuraStyles.getBreakthrough(rankId)
    local look = { Element = element, Breakthrough = breakthrough }

    local folder = Instance.new("Folder")
    folder.Name = "Breakthrough"
    local effect = { folder = folder, tweens = {}, stopped = false, onFinished = onFinished }

    local center = rootPart.Position
    groundParams.FilterDescendantsInstances = { character, container }
    local hit = workspace:Raycast(center, Vector3.new(0, -GROUND_SEARCH, 0), groundParams)
    local groundPosition = if hit then hit.Position else center - Vector3.new(0, 3, 0)
    local groundOffset = groundPosition.Y - center.Y

    local anchor = createAnchor(effect, center)
    local scale = breakthrough.Scale

    local shockwaves = {}
    if hit then
        for layer = 1, breakthrough.Shockwaves do
            table.insert(shockwaves, prepareShockwave(effect, groundPosition, look, layer))
        end
    end

    folder.Parent = container

    addFlash(effect, anchor, look)
    addBursts(effect, anchor, look)
    addPillar(effect, anchor, look, groundOffset)

    for index, playShockwave in shockwaves do
        later(effect, (index - 1) * 0.3, function()
            playShockwave((14 + (index - 1) * 4) * scale)
        end)
    end

    for index = 1, breakthrough.Rings do
        local tilt = if index == 1 then 0 elseif index == 2 then 14 else -14
        later(effect, 0.1 + (index - 1) * 0.25, function()
            addExpandingRing(effect, anchor, look, -0.5 + (index - 1) * 0.8, (5 + index * 1.5) * scale, tilt)
        end)
    end

    for index = 1, breakthrough.Streaks do
        later(effect, 0.05 + index * 0.05, function()
            local angle = index / breakthrough.Streaks * FULL_TURN + index * 0.4
            addStreak(effect, anchor, look, angle, (1.6 + (index % 3) * 0.6) * scale, groundOffset)
        end)
    end

    later(effect, breakthrough.Duration, function()
        BreakthroughEffect.stop(effect)
    end)

    return effect
end

function BreakthroughEffect.stop(effect)
    if effect.stopped then
        return
    end
    effect.stopped = true

    for _, created in effect.tweens do
        created:Cancel()
    end
    table.clear(effect.tweens)
    effect.folder:Destroy()

    if effect.onFinished then
        effect.onFinished()
    end
end

return BreakthroughEffect

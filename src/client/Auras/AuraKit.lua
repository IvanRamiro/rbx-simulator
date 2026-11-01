local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))

local AuraKit = {}

AuraKit.TAU = 2 * math.pi
local SETTINGS = AuraStyles.CharacterAura
local FADE_IN = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(1.1, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local MAX_GROUND_DROP = 14

-- points: { { time, value, envelope? }, ... }
function AuraKit.numberSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, NumberSequenceKeypoint.new(point[1], point[2], point[3] or 0))
    end
    return NumberSequence.new(keypoints)
end

-- points: { { time, Color3 }, ... }
function AuraKit.colorSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, ColorSequenceKeypoint.new(point[1], point[2]))
    end
    return ColorSequence.new(keypoints)
end

function AuraKit.smoothstep(edge0, edge1, x)
    local t = math.clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
end

function AuraKit.approach(current, target, rate, deltaTime)
    return current + (target - current) * (1 - math.exp(-rate * deltaTime))
end

function AuraKit.prepare(part)
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Massless = true
end

function AuraKit.newPart(aura, name, size, shape)
    local part = Instance.new("Part")
    part.Name = name
    part.Shape = shape or Enum.PartType.Block
    part.Size = size
    part.Transparency = 1
    AuraKit.prepare(part)
    part.CFrame = aura.rootPart.CFrame
    part.Parent = aura.model
    return part
end

function AuraKit.template(set, name)
    local folder = ReplicatedStorage:FindFirstChild("AuraMeshes")
    local model = folder and folder:FindFirstChild(set)
    return model and model:FindFirstChild(set .. "_" .. name, true)
end

function AuraKit.hasTemplates(set, names)
    for _, name in names do
        if not AuraKit.template(set, name) then
            return false
        end
    end
    return true
end

function AuraKit.dress(part, material)
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

function AuraKit.meshPart(aura, name, scale, kind)
    local template = AuraKit.template(aura.set, name)
    local part = template:Clone()
    part.Size = template.Size * scale
    AuraKit.prepare(part)
    AuraKit.dress(part, aura.style.Materials[kind])
    part.Transparency = 1
    part.Parent = aura.model
    return part
end

function AuraKit.addEmitter(aura, parent, rate, properties, minStage)
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

-- An emitter whose particles lie flat on the ground and stay locked to their part (rings,
-- slashes, swirls). `defaults` are the design's own base settings, `properties` the emitter's.
function AuraKit.flatEmitter(aura, parent, rate, properties, defaults)
    local preset = {
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
        EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.01),
        LockedToPart = true,
    }
    for _, overrides in { defaults or {}, properties } do
        for property, value in overrides do
            preset[property] = value
        end
    end
    return AuraKit.addEmitter(aura, parent, rate, preset)
end

function AuraKit.surfaceGui(part, pixelsPerStud, brightness)
    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Top
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = pixelsPerStud
    gui.LightInfluence = 0
    gui.Brightness = brightness
    gui.MaxDistance = 400
    gui.Parent = part
    return gui
end

function AuraKit.surfaceImage(gui, image, size, color, transparency)
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

function AuraKit.trail(parent, halfWidth, texture, lifetime, color, brightness)
    local top = Instance.new("Attachment")
    top.Position = Vector3.new(0, halfWidth, 0)
    top.Parent = parent
    local bottom = Instance.new("Attachment")
    bottom.Position = Vector3.new(0, -halfWidth, 0)
    bottom.Parent = parent
    local trail = Instance.new("Trail")
    trail.Attachment0 = top
    trail.Attachment1 = bottom
    trail.Texture = texture
    trail.TextureMode = Enum.TextureMode.Stretch
    trail.FaceCamera = true
    trail.Lifetime = lifetime
    trail.LightInfluence = 0
    trail.LightEmission = 0.9
    trail.Brightness = brightness or 2
    trail.Color = color
    trail.Transparency = AuraKit.numberSequence({ { 0, 0.2 }, { 1, 1 } })
    trail.WidthScale = AuraKit.numberSequence({ { 0, 1 }, { 1, 0.1 } })
    trail.Enabled = false
    trail.Parent = parent
    return trail
end

function AuraKit.attachment(parent)
    local attachment = Instance.new("Attachment")
    attachment.Parent = parent
    return attachment
end

function AuraKit.beam(parent, attachment0, attachment1, properties)
    local beam = Instance.new("Beam")
    beam.Attachment0 = attachment0
    beam.Attachment1 = attachment1
    beam.TextureMode = Enum.TextureMode.Wrap
    beam.FaceCamera = true
    beam.LightInfluence = 0
    beam.Transparency = NumberSequence.new(1)
    for property, value in properties do
        beam[property] = value
    end
    beam.Parent = parent
    return beam
end

function AuraKit.fader(beam, points)
    return { Beam = beam, Points = points, Last = -1 }
end

function AuraKit.fadeBeam(state, amount)
    local step = math.floor(math.clamp(amount, 0, 1) * 20 + 0.5) / 20
    if step == state.Last then
        return
    end
    state.Last = step
    if step <= 0 then
        state.Beam.Transparency = NumberSequence.new(1)
        return
    end
    local keypoints = {}
    for _, point in state.Points do
        table.insert(keypoints, NumberSequenceKeypoint.new(point[1], 1 - (1 - point[2]) * step))
    end
    state.Beam.Transparency = NumberSequence.new(keypoints)
end

function AuraKit.glow(aura, main, core, range)
    local light = Instance.new("PointLight")
    light.Color = main
    light.Range = range
    light.Brightness = 0
    light.Shadows = false
    light.Parent = aura.volume
    aura.light = light

    local highlight = Instance.new("Highlight")
    highlight.Name = "AuraGlow"
    highlight.Adornee = aura.character
    highlight.DepthMode = Enum.HighlightDepthMode.Occluded
    highlight.FillColor = main
    highlight.OutlineColor = core
    highlight.FillTransparency = 1
    highlight.OutlineTransparency = 1
    highlight.Parent = aura.model
    aura.highlight = highlight
end

function AuraKit.newAura(player, character, rootPart, rankId, set, style)
    local _, boxSize = character:GetBoundingBox()
    local height = math.clamp(boxSize.Y, 3, 12)
    local boost = AuraStyles.getBoost(rankId)
    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"
    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Parent = model
    return {
        player = player,
        character = character,
        rootPart = rootPart,
        model = model,
        fader = fader,
        set = set,
        style = style,
        boost = boost,
        k = height / 5 * (1 + (boost - 1) * 0.35),
        detail = if player == Players.LocalPlayer then 1 else SETTINGS.OtherPlayers,
        random = Random.new(),
        emitters = {},
        stage = 0,
        power = 0,
        spin = 0,
        surgeAt = -math.huge,
        nextGroundCheck = 0,
        hiding = false,
        destroyed = false,
    }
end

function AuraKit.surge(aura, strength)
    if aura.destroyed or aura.hiding then
        return
    end
    aura.surgeAt = os.clock()
    aura.surgeStrength = strength
    if aura.onSurge then
        aura.onSurge(aura, strength)
    end
end

function AuraKit.show(aura)
    aura.shownAt = os.clock()
    TweenService:Create(aura.fader, FADE_IN, { Value = 1 }):Play()
    if aura.onCharge then
        aura.onCharge(aura)
    end
    task.delay(SETTINGS.ChargeSeconds, function()
        if aura.destroyed or aura.hiding then
            return
        end
        aura.stage = 1
        if aura.onStage then
            aura.onStage(aura, 1)
        end
        AuraKit.surge(aura, 1)
    end)
end

function AuraKit.hide(aura)
    if aura.hiding then
        return
    end
    aura.hiding = true
    TweenService:Create(aura.fader, FADE_OUT, { Value = 0 }):Play()
    if aura.onHide then
        aura.onHide(aura)
    end
end

function AuraKit.destroy(aura)
    aura.destroyed = true
    aura.model:Destroy()
end

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Exclude
groundParams.IgnoreWater = true

local function advanceStage(aura, now)
    if aura.stage == 0 or aura.hiding then
        return SETTINGS.Stages[math.max(aura.stage, 1)]
    end
    local elapsed = now - aura.shownAt - SETTINGS.ChargeSeconds
    local nextStage = SETTINGS.Stages[aura.stage + 1]
    if nextStage and elapsed >= nextStage.After then
        aura.stage += 1
        if aura.onStage then
            aura.onStage(aura, aura.stage)
        end
        AuraKit.surge(aura, 1)
    end
    local settings = SETTINGS.Stages[aura.stage]
    if settings.SurgeEvery and now >= (aura.nextSurge or 0) then
        if aura.nextSurge then
            AuraKit.surge(aura, 0.7)
        end
        aura.nextSurge = now + settings.SurgeEvery * aura.random:NextNumber(0.85, 1.2)
    end
    return settings
end

function AuraKit.step(aura, now)
    local deltaTime = math.min(now - (aura.lastUpdate or now), 0.1)
    aura.lastUpdate = now
    local settings = advanceStage(aura, now)
    local fade = aura.fader.Value
    local live = not aura.hiding

    aura.power = AuraKit.approach(aura.power, if aura.stage == 0 then 0.25 else settings.Power, 2, deltaTime)
    local level = fade * aura.power
    local surge = math.max(0, 1 - (now - aura.surgeAt) / 1.2) * (aura.surgeStrength or 1)
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

    local rootCFrame = aura.rootPart.CFrame
    local position = rootCFrame.Position
    local seat = Vector3.new(position.X, aura.seatY - 0.1 * aura.k, position.Z)
    local floorY = aura.groundY or (seat.Y - 1.2 * aura.k)
    return {
        deltaTime = deltaTime,
        fade = fade,
        live = live,
        level = level,
        surge = surge,
        spin = aura.spin,
        seat = seat,
        floor = Vector3.new(position.X, floorY + 0.06, position.Z),
        facing = CFrame.lookAt(Vector3.zero, Vector3.new(rootCFrame.LookVector.X, 0, rootCFrame.LookVector.Z)),
        charge = if aura.shownAt then math.clamp((now - aura.shownAt) / SETTINGS.ChargeSeconds, 0, 1) else 0,
    }
end

function AuraKit.showPart(part, base, amount)
    if part.Material == Enum.Material.Glass then
        part.Transparency = if amount > 0.04 then base else 1
    else
        part.Transparency = 1 - (1 - base) * math.clamp(amount, 0, 1)
    end
end

function AuraKit.finishGlow(aura, frame, brightness, fill, outline)
    local breathe = 0.85 + 0.15 * math.sin(os.clock() * 2)
    aura.light.Brightness = (brightness * frame.level * breathe + 3 * frame.surge) * frame.fade
    aura.highlight.FillTransparency = 1 - math.min(0.9, (fill * frame.level + 0.15 * frame.surge) * frame.fade)
    aura.highlight.OutlineTransparency = 1 - math.min(1, (outline * frame.level + 0.3 * frame.surge) * frame.fade)
end

return AuraKit

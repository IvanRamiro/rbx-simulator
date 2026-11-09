local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

-- Pet auras: an equipped pet of a cultivating player shows its element's aura, for the pets that
-- have one (ELEMENTS below; the rest show none). The player's own aura is CharacterAura.
local AuraBuilder = {}

local PET_AMOUNT = 0.6 -- pet auras are a lighter version of the element's full aura

AuraBuilder.REMOVE_DELAY = 3

local FADE_IN = TweenInfo.new(1.2, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local TRAIL_START_DELAY = 0.2
local FULL_TURN = 2 * math.pi

local numberSequence = AuraKit.numberSequence

local function addFade(aura, instance, property, visibleValue, hiddenValue)
    instance[property] = hiddenValue
    table.insert(aura.fades, { Instance = instance, Property = property, Visible = visibleValue, Hidden = hiddenValue })
end

local function addLoop(aura, instance, seconds, goal)
    local tween = TweenService:Create(instance, TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), goal)
    tween:Play()
    table.insert(aura.loops, tween)
end

local function measureBody(model, rootPart)
    local rootCFrame = rootPart.CFrame
    local low, high = AuraKit.bodyBounds(model, rootPart)
    local boxSize = high - low
    local feetY = low.Y
    local head = model:FindFirstChild("Head")
    local headTopY = if head and head:IsA("BasePart")
        then rootCFrame:PointToObjectSpace(head.Position).Y + head.Size.Y / 2
        else feetY + boxSize.Y
    local height = math.clamp(headTopY - feetY, 2, 12)
    return { FeetY = feetY, Height = height, Reach = math.max(boxSize.X, boxSize.Z) / 2 }
end

local function createDroplet(aura, style, index)
    local textures = style.Textures
    local part = AuraKit.newPart(aura, "Droplet" .. index, Vector3.one * style.DropletSize, Enum.PartType.Ball)
    part.Material = Enum.Material.Neon
    part.Color = style.Main:Lerp(style.Core, 0.3)
    addFade(aura, part, "Transparency", 0, 1)

    local halo = Instance.new("BillboardGui")
    halo.Name = "Halo"
    halo.Size = UDim2.fromScale(style.GlowSize, style.GlowSize)
    halo.LightInfluence = 0
    halo.Brightness = 2
    halo.MaxDistance = 250
    halo.Parent = part
    local image = Instance.new("ImageLabel")
    image.Size = UDim2.fromScale(1, 1)
    image.BackgroundTransparency = 1
    image.Image = textures.Glow
    image.ImageColor3 = style.Main
    image.Parent = halo
    addFade(aura, image, "ImageTransparency", 0.05, 1)
    task.delay(index * 0.37, function()
        if not aura.destroyed then
            addLoop(aura, halo, 1.4 + index * 0.07, { Size = UDim2.fromScale(style.GlowSize * 1.25, style.GlowSize * 1.25) })
        end
    end)

    local half = style.DropletSize * 0.5
    local top = Instance.new("Attachment")
    top.Position = Vector3.new(0, half, 0)
    top.Parent = part
    local bottom = Instance.new("Attachment")
    bottom.Position = Vector3.new(0, -half, 0)
    bottom.Parent = part
    local trail = Instance.new("Trail")
    trail.Attachment0 = top
    trail.Attachment1 = bottom
    trail.Texture = textures.Trail
    trail.TextureMode = Enum.TextureMode.Stretch
    trail.FaceCamera = true
    trail.Lifetime = style.TrailSeconds
    trail.MinLength = 0.02
    trail.LightInfluence = 0
    trail.LightEmission = 0.7
    trail.Brightness = 2
    trail.Color = ColorSequence.new({
        ColorSequenceKeypoint.new(0, style.Core),
        ColorSequenceKeypoint.new(0.35, style.Main),
        ColorSequenceKeypoint.new(1, style.Deep),
    })
    trail.Transparency = numberSequence({ { 0, 0.05 }, { 0.6, 0.55 }, { 1, 1 } })
    trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0 } })
    trail.Enabled = false
    trail.Parent = part
    table.insert(aura.trails, trail)

    return part
end

local addSoftGlow

local function buildAquaWisp(aura, style)
    local boost = aura.boost

    for index = 1, style.Droplets do
        table.insert(aura.droplets, createDroplet(aura, style, index))
    end

    local volume = aura.volume
    local textures = style.Textures

    local sparkles = Instance.new("ParticleEmitter")
    sparkles.Name = "Sparkles"
    sparkles.Texture = textures.Sparkle
    sparkles.Shape = Enum.ParticleEmitterShape.Box
    sparkles.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    sparkles.Color = ColorSequence.new(style.Core, style.Main)
    sparkles.LightInfluence = 0
    sparkles.LightEmission = 0.6
    sparkles.Brightness = 3
    sparkles.Size = numberSequence({ { 0, 0 }, { 0.25, 0.7 }, { 0.5, 0.25 }, { 0.75, 0.6 }, { 1, 0 } })
    sparkles.Lifetime = NumberRange.new(1.2, 2)
    sparkles.Speed = NumberRange.new(0.15, 0.5)
    sparkles.SpreadAngle = Vector2.new(180, 180)
    sparkles.Acceleration = Vector3.new(0, 0.5, 0)
    sparkles.Rotation = NumberRange.new(0, 45)
    sparkles.RotSpeed = NumberRange.new(-40, 40)
    sparkles.Parent = volume
    addFade(aura, sparkles, "Rate", style.SparkleRate * boost * aura.amount, 0)

    local bubbles = Instance.new("ParticleEmitter")
    bubbles.Name = "Bubbles"
    bubbles.Texture = textures.Bubble
    bubbles.Shape = Enum.ParticleEmitterShape.Box
    bubbles.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    bubbles.Color = ColorSequence.new(style.Core)
    bubbles.LightInfluence = 0
    bubbles.LightEmission = 0.25
    bubbles.Brightness = 1.6
    bubbles.Size = numberSequence({ { 0, 0 }, { 0.15, 0.38 }, { 0.85, 0.48 }, { 1, 0 } })
    bubbles.Transparency = numberSequence({ { 0, 0.15 }, { 0.8, 0.35 }, { 1, 1 } })
    bubbles.Lifetime = NumberRange.new(2, 3.2)
    bubbles.Speed = NumberRange.new(0.4, 0.9)
    bubbles.EmissionDirection = Enum.NormalId.Top
    bubbles.SpreadAngle = Vector2.new(25, 25)
    bubbles.Drag = 0.6
    bubbles.Parent = volume
    addFade(aura, bubbles, "Rate", style.BubbleRate * boost * aura.amount, 0)

    addSoftGlow(aura, style)
end

addSoftGlow = function(aura, style)
    local light = Instance.new("PointLight")
    light.Color = style.Main
    light.Range = style.LightRange
    light.Brightness = 0
    light.Shadows = false
    light.Parent = aura.volume
    aura.light = light
    aura.lightBrightness = style.LightBrightness * aura.boost * aura.amount
end

local function animateAquaWisp(aura, now, rootCFrame, parts, cframes)
    local style, body = aura.style, aura.body
    local count = #aura.droplets
    local radius = aura.orbitRadius
    local spin = aura.phase + now / style.OrbitSeconds * FULL_TURN

    for index, droplet in aura.droplets do
        local share = (index - 1) / math.max(count - 1, 1)
        local angle = spin + (index - 1) / count * FULL_TURN
        local height = body.FeetY + body.Height * (0.18 + 0.62 * share)
            + math.sin(now * 0.9 + index * 1.3) * style.SpiralTurn * body.Height
        local distance = radius * (1 + 0.08 * math.sin(now * 0.7 + index * 2.1))
        table.insert(parts, droplet)
        table.insert(cframes, rootCFrame * CFrame.new(math.cos(angle) * distance, height, math.sin(angle) * distance))
    end
end

local ELEMENTS = {
    AquaWisp = { Build = buildAquaWisp, Animate = animateAquaWisp },
}

function AuraBuilder.build(player, character, rootPart, petId, rankId)
    local style = AuraStyles.Auras[petId]
    if not style or not ELEMENTS[petId] then
        return nil
    end

    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"

    local body = measureBody(character, rootPart)
    local aura = {
        player = player,
        rootPart = rootPart,
        model = model,
        style = style,
        body = body,
        amount = PET_AMOUNT,
        orbitRadius = math.max(style.OrbitRadius * body.Height, body.Reach + 0.8),
        boost = AuraStyles.getBoost(rankId),
        fades = {},
        loops = {},
        trails = {},
        droplets = {},
        phase = math.random() * FULL_TURN,
        hiding = false,
        destroyed = false,
    }

    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Parent = model
    aura.fader = fader
    addFade(aura, fader, "Value", 1, 0)

    local width = math.max(body.Height * 0.8, body.Reach * 2)
    aura.volume = AuraKit.newPart(aura, "Volume", Vector3.new(width, body.Height * 0.9, width))

    local element = ELEMENTS[petId]
    element.Build(aura, style)
    aura.animate = element.Animate
    return aura
end

local function playFades(aura, toVisible)
    local tweenInfo = if toVisible then FADE_IN else FADE_OUT
    for _, fade in aura.fades do
        TweenService:Create(fade.Instance, tweenInfo, { [fade.Property] = if toVisible then fade.Visible else fade.Hidden }):Play()
    end
end

function AuraBuilder.show(aura)
    playFades(aura, true)
    task.delay(TRAIL_START_DELAY, function()
        if aura.destroyed or aura.hiding then
            return
        end
        for _, trail in aura.trails do
            trail.Enabled = true
        end
    end)
end

function AuraBuilder.hide(aura)
    aura.hiding = true
    playFades(aura, false)
    for _, trail in aura.trails do
        trail.Enabled = false
    end
end

function AuraBuilder.destroy(aura)
    aura.destroyed = true
    for _, tween in aura.loops do
        tween:Cancel()
    end
    table.clear(aura.loops)
    aura.model:Destroy()
end

function AuraBuilder.update(aura, now, parts, cframes)
    local body = aura.body
    local rootCFrame = aura.rootPart.CFrame
    aura.animate(aura, now, rootCFrame, parts, cframes)

    table.insert(parts, aura.volume)
    table.insert(cframes, rootCFrame * CFrame.new(0, body.FeetY + body.Height * 0.5, 0))

    aura.light.Brightness = aura.lightBrightness * aura.fader.Value * (0.85 + 0.15 * math.sin(now * 1.6))
end

return AuraBuilder

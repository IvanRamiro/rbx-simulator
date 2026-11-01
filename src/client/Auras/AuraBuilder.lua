local ReplicatedStorage = game:GetService("ReplicatedStorage")
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

local function newPart(aura, name, shape, size)
    local part = Instance.new("Part")
    part.Name = name
    part.Shape = shape
    part.Size = size
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Transparency = 1
    part.CFrame = aura.rootPart.CFrame
    part.Parent = aura.model
    return part
end

local function measureBody(model, rootPart)
    local rootCFrame = rootPart.CFrame
    local boxCFrame, boxSize = model:GetBoundingBox()
    local feetY = rootCFrame:PointToObjectSpace(boxCFrame.Position).Y - boxSize.Y / 2
    local head = model:FindFirstChild("Head")
    local headTopY = if head and head:IsA("BasePart")
        then rootCFrame:PointToObjectSpace(head.Position).Y + head.Size.Y / 2
        else feetY + boxSize.Y
    local height = math.clamp(headTopY - feetY, 2, 12)
    return { FeetY = feetY, Height = height, Reach = math.max(boxSize.X, boxSize.Z) / 2 }
end

local function createDroplet(aura, style, index)
    local textures = style.Textures
    local part = newPart(aura, "Droplet" .. index, Enum.PartType.Ball, Vector3.one * style.DropletSize)
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

local function meshPiece(aura, name, longest, fades)
    local folder = ReplicatedStorage:FindFirstChild("AuraMeshes")
    local template = folder and folder:FindFirstChild(name)
    if not (template and template:IsA("Model")) then
        return nil
    end
    local boxCFrame, boxSize = template:GetBoundingBox()
    local scale = longest / math.max(boxSize.X, boxSize.Y, boxSize.Z)
    local root = newPart(aura, name, Enum.PartType.Block, Vector3.one * 0.2)
    local piece = { Root = root, Parts = {} }
    for _, source in template:GetDescendants() do
        if not source:IsA("BasePart") then
            continue
        end
        local part = source:Clone()
        local hex = string.match(source.Name, "_Glow_(%x%x%x%x%x%x)$")
        for _, child in part:GetChildren() do
            if hex or not child:IsA("SurfaceAppearance") then
                child:Destroy()
            end
        end
        if hex then
            part.Color = Color3.fromHex(hex)
            part.Material = Enum.Material.Neon
            if part:IsA("MeshPart") then
                part.TextureID = ""
            end
        end
        local relative = boxCFrame:ToObjectSpace(source.CFrame)
        part.Size = source.Size * scale
        part.CFrame = root.CFrame * (relative.Rotation + relative.Position * scale)
        part.Anchored = false
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.CastShadow = false
        part.Massless = true
        local weld = Instance.new("WeldConstraint")
        weld.Part0 = root
        weld.Part1 = part
        weld.Parent = part
        part.Parent = aura.model
        if fades then
            addFade(aura, part, "Transparency", 0, 1)
        end
        table.insert(piece.Parts, part)
    end
    return piece
end

local function buildGoldenKirin(aura, style)
    local body, height = aura.body, aura.body.Height
    local random = Random.new(aura.player.UserId + 7)

    aura.ring = meshPiece(aura, "KirinVFX_Ring", (body.Reach + 0.4) * 2, true)
    aura.crown = meshPiece(aura, "KirinVFX_CrownLeaf", style.CrownSize * height, true)

    aura.leaves = {}
    local leafCount = math.max(3, math.round(style.Leaves * aura.amount))
    for index = 1, leafCount do
        local leaf = meshPiece(aura, if index % 2 == 0 then "KirinVFX_LeafGold" else "KirinVFX_LeafEmerald",
            style.LeafSize * height, false)
        if leaf then
            for _, part in leaf.Parts do
                part.Transparency = 1
            end
            leaf.Offset = (index - 1) / leafCount
            leaf.Tumble = random:NextNumber(0, FULL_TURN)
            table.insert(aura.leaves, leaf)
        end
    end

    aura.motes = {}
    local moteCount = math.max(3, math.round(style.Motes * aura.amount))
    for index = 1, moteCount do
        local mote = meshPiece(aura, "KirinVFX_Mote", style.MoteSize * height, true)
        if mote then
            mote.Angle = (index - 1) / moteCount * FULL_TURN + random:NextNumber(-0.3, 0.3)
            mote.Height = random:NextNumber(0.15, 0.95)
            mote.Distance = random:NextNumber(0.75, 1.05)
            mote.Phase = random:NextNumber(0, FULL_TURN)
            table.insert(aura.motes, mote)
        end
    end

    local glints = Instance.new("ParticleEmitter")
    glints.Name = "Glints"
    glints.Texture = style.Textures.Glint
    glints.Shape = Enum.ParticleEmitterShape.Box
    glints.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    glints.Color = ColorSequence.new(style.Core, style.Main)
    glints.LightInfluence = 0
    glints.LightEmission = 0.5
    glints.Brightness = 2.5
    glints.Size = numberSequence({ { 0, 0 }, { 0.35, 1.2 }, { 1, 0 } })
    glints.Lifetime = NumberRange.new(0.6, 1.1)
    glints.Speed = NumberRange.new(0, 0.3)
    glints.SpreadAngle = Vector2.new(180, 180)
    glints.Rotation = NumberRange.new(0, 45)
    glints.Parent = aura.volume
    addFade(aura, glints, "Rate", style.GlintRate * aura.boost * aura.amount, 0)

    addSoftGlow(aura, style)
end

local function animateGoldenKirin(aura, now, rootCFrame, parts, cframes)
    local style, body = aura.style, aura.body
    local height, feetY, radius = body.Height, body.FeetY, aura.orbitRadius
    local spin = aura.phase + now / style.RingSeconds * FULL_TURN
    local fade = aura.fader.Value

    if aura.ring then
        local tilt = CFrame.Angles(math.rad(6) * math.sin(now * 0.5), 0, math.rad(6) * math.cos(now * 0.4))
        table.insert(parts, aura.ring.Root)
        table.insert(cframes, rootCFrame * CFrame.new(0, feetY + height * style.RingHeight, 0) * tilt * CFrame.Angles(0, spin, 0))
    end

    if aura.crown then
        local bob = math.sin(now * 1.3) * 0.05 * height
        table.insert(parts, aura.crown.Root)
        table.insert(cframes, rootCFrame * CFrame.new(0, feetY + height * (1 + style.CrownLift) + bob, 0)
            * CFrame.Angles(0, -spin * 0.6, 0))
    end

    for _, leaf in aura.leaves do
        local progress = (now / style.LeafRiseSeconds + leaf.Offset) % 1
        local angle = aura.phase + leaf.Offset * FULL_TURN + progress * style.LeafTurns * FULL_TURN
        local distance = radius * (0.85 + 0.15 * math.sin(progress * math.pi))
        local position = Vector3.new(math.cos(angle) * distance, feetY + height * (0.05 + progress), math.sin(angle) * distance)
        local edge = math.min(progress / 0.15, (1 - progress) / 0.2, 1)
        local transparency = 1 - edge * fade
        for _, part in leaf.Parts do
            part.Transparency = transparency
        end
        local tumble = leaf.Tumble + now * 1.7
        table.insert(parts, leaf.Root)
        table.insert(cframes, rootCFrame * CFrame.new(position) * CFrame.Angles(0, -angle, 0)
            * CFrame.Angles(math.rad(35) + 0.4 * math.sin(tumble), 0, 0.6 * math.cos(tumble)))
    end

    for _, mote in aura.motes do
        local bob = math.sin(now * 1.1 + mote.Phase) * 0.06 * height
        local angle = mote.Angle + spin * 0.35
        table.insert(parts, mote.Root)
        table.insert(cframes, rootCFrame * CFrame.new(math.cos(angle) * radius * mote.Distance,
            feetY + height * mote.Height + bob, math.sin(angle) * radius * mote.Distance)
            * CFrame.Angles(0, now * 1.5 + mote.Phase, math.rad(12)))
    end
end

local ELEMENTS = {
    AquaWisp = { Build = buildAquaWisp, Animate = animateAquaWisp },
    GoldenKirin = { Build = buildGoldenKirin, Animate = animateGoldenKirin },
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
    aura.volume = newPart(aura, "Volume", Enum.PartType.Block, Vector3.new(width, body.Height * 0.9, width))

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

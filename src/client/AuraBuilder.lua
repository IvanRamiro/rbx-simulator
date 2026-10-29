-- Builds, animates and removes one cultivation aura. AuraController decides
-- when an aura should exist; this module decides how it looks.
--
-- Auras are being rebuilt one element at a time. AuraBuilder.build returns
-- nil for an element that has no aura yet (no entry in AuraStyles.Auras).
--
-- Auras form around cultivating characters (the aura pet's element) and
-- around each of their equipped pets (that pet's own element, see
-- PetCompanionController).
--
-- Aqua Wisp: six glowing water droplets orbit the body at different heights,
-- so together they trace a slowly turning spiral, each leaving a short
-- teardrop trail. Sparkling water motes and tiny bubbles drift up around the
-- body, and a soft cyan light and faint body glow make it look magical.
-- Textures were rendered in Blender (tools/blender/AquaWispAura.blend).
--
-- Moving pieces are anchored parts outside the character, placed relative to
-- it every frame (see AuraBuilder.update), so they can't affect movement.

local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))

local AuraBuilder = {}

AuraBuilder.REMOVE_DELAY = 3 -- Seconds after fading out before removal, so particles and trails can finish

local FADE_IN = TweenInfo.new(1.2, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local TRAIL_START_DELAY = 0.2 -- Trails start once the droplets are in place, so no streak flies in
local FULL_TURN = 2 * math.pi

-- Helpers --------------------------------------------------------------------

local function numberSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, NumberSequenceKeypoint.new(point[1], point[2]))
    end
    return NumberSequence.new(keypoints)
end

-- Records a property that tweens between hidden and visible as the aura
-- appears and disappears. It starts hidden.
local function addFade(aura, instance, property, visibleValue, hiddenValue)
    instance[property] = hiddenValue
    table.insert(aura.fades, { Instance = instance, Property = property, Visible = visibleValue, Hidden = hiddenValue })
end

-- An endless tween going back and forth, cancelled on removal
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
    part.CFrame = aura.rootPart.CFrame -- Start in place so nothing streaks in from far away
    part.Parent = aura.model
    return part
end

-- How big the body is, relative to its root part: where the bottom is, how
-- tall it is (feet to head top for characters) and how far it reaches out
-- sideways (for pets, which are long rather than tall)
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

-- Aqua Wisp --------------------------------------------------------------------

-- One droplet: a glowing core with a soft halo and a teardrop trail
local function createDroplet(aura, style, index)
    local textures = style.Textures
    local part = newPart(aura, "Droplet" .. index, Enum.PartType.Ball, Vector3.one * style.DropletSize)
    part.Material = Enum.Material.Neon
    part.Color = style.Main:Lerp(style.Core, 0.3) -- Neon brightens a lot, so the core starts from the cyan
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
    -- A gentle shimmer, out of step with the other droplets
    task.delay(index * 0.37, function()
        if not aura.destroyed then
            addLoop(aura, halo, 1.4 + index * 0.07, { Size = UDim2.fromScale(style.GlowSize * 1.25, style.GlowSize * 1.25) })
        end
    end)

    -- The trail spans the droplet's width and tapers to a point: a teardrop
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

local function buildAquaWisp(aura, style)
    local body = aura.body
    local boost = aura.boost

    for index = 1, style.Droplets do
        table.insert(aura.droplets, createDroplet(aura, style, index))
    end

    -- An invisible box around the body that the motes and bubbles drift out of
    local width = math.max(body.Height * 0.8, body.Reach * 2)
    local volume = newPart(aura, "MistVolume", Enum.PartType.Block, Vector3.new(width, body.Height * 0.9, width))
    aura.volume = volume
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
    sparkles.Size = numberSequence({ { 0, 0 }, { 0.25, 0.7 }, { 0.5, 0.25 }, { 0.75, 0.6 }, { 1, 0 } }) -- Twinkles twice
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

    -- Soft glow: a cyan light on the body and a faint tint over the character
    local light = Instance.new("PointLight")
    light.Color = style.Main
    light.Range = style.LightRange
    light.Brightness = 0
    light.Shadows = false
    light.Parent = volume
    aura.light = light
    aura.lightBrightness = style.LightBrightness * boost * aura.amount

    -- Characters only: a client can show at most 31 Highlights at once
    if aura.isPet then
        return
    end
    local glow = Instance.new("Highlight")
    glow.Name = "BodyGlow"
    glow.Adornee = aura.character
    glow.DepthMode = Enum.HighlightDepthMode.Occluded
    glow.FillColor = style.Main
    glow.OutlineColor = style.Core
    glow.Parent = aura.model
    addFade(aura, glow, "FillTransparency", 1 - style.BodyGlow, 1)
    addFade(aura, glow, "OutlineTransparency", 0.7, 1)
end

-- Public API ---------------------------------------------------------------

-- Builds a (still invisible) aura around a character or a pet companion, or
-- returns nil when the element has no aura yet. petId selects the element,
-- rankId (the owner's rank) how strong it is. For pets, pass isPet = true:
-- the aura is measured around the pet model, a little lighter, without the
-- body tint.
function AuraBuilder.build(player, character, rootPart, petId, rankId, isPet)
    local style = AuraStyles.Auras[petId or "Neutral"]
    if not style then
        return nil
    end

    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"

    local body = measureBody(character, rootPart)
    local aura = {
        player = player,
        character = character,
        rootPart = rootPart,
        model = model,
        style = style,
        body = body,
        isPet = isPet == true,
        amount = if isPet then 0.6 else 1, -- Particles and light, so a whole group isn't overwhelming
        -- Droplets orbit clear of the body: pets are often longer than they are tall
        orbitRadius = math.max(style.OrbitRadius * body.Height, body.Reach + 0.8),
        boost = AuraStyles.getBoost(rankId),
        fades = {}, -- Properties that tween as the aura appears and disappears
        loops = {}, -- Endless tweens, cancelled on removal
        trails = {},
        droplets = {},
        phase = math.random() * FULL_TURN,
        hiding = false,
        destroyed = false,
    }

    -- Drives the fade of what is set every frame (the light)
    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Parent = model
    aura.fader = fader
    addFade(aura, fader, "Value", 1, 0)

    buildAquaWisp(aura, style)
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

-- Fades the aura out. The controller removes it after REMOVE_DELAY.
function AuraBuilder.hide(aura)
    aura.hiding = true
    playFades(aura, false)
end

-- Briefly brightens the aura (used by breakthroughs)
function AuraBuilder.pulse(aura, seconds)
    aura.pulseSeconds = seconds
    aura.pulseEnd = os.clock() + seconds
end

function AuraBuilder.destroy(aura)
    aura.destroyed = true
    for _, tween in aura.loops do
        tween:Cancel()
    end
    table.clear(aura.loops)
    aura.model:Destroy()
end

-- Called every frame. Adds this aura's moving parts to parts/cframes (moved
-- in one BulkMoveTo call by the controller) and updates the light.
function AuraBuilder.update(aura, now, parts, cframes)
    local style, body = aura.style, aura.body
    local rootCFrame = aura.rootPart.CFrame
    local count = #aura.droplets
    local radius = aura.orbitRadius
    local spin = aura.phase + now / style.OrbitSeconds * FULL_TURN

    for index, droplet in aura.droplets do
        local share = (index - 1) / math.max(count - 1, 1) -- 0 for the lowest droplet, 1 for the highest
        -- Evenly spaced around the circle and stepped up in height: a spiral
        -- staircase that turns as a whole, each droplet bobbing gently
        local angle = spin + (index - 1) / count * FULL_TURN
        local height = body.FeetY + body.Height * (0.18 + 0.62 * share)
            + math.sin(now * 0.9 + index * 1.3) * style.SpiralTurn * body.Height
        local distance = radius * (1 + 0.08 * math.sin(now * 0.7 + index * 2.1))
        table.insert(parts, droplet)
        table.insert(cframes, rootCFrame * CFrame.new(math.cos(angle) * distance, height, math.sin(angle) * distance))
    end

    table.insert(parts, aura.volume)
    table.insert(cframes, rootCFrame * CFrame.new(0, body.FeetY + body.Height * 0.5, 0))

    -- A slow, breathing glow, briefly brighter after a breakthrough
    local brightness = aura.lightBrightness * aura.fader.Value * (0.85 + 0.15 * math.sin(now * 1.6))
    if aura.pulseEnd then
        local remaining = (aura.pulseEnd - now) / aura.pulseSeconds
        if remaining > 0 then
            brightness *= 1 + 2.5 * remaining
        else
            aura.pulseEnd = nil
        end
    end
    aura.light.Brightness = brightness
end

return AuraBuilder

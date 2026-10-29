-- Builds, animates and removes one PET aura (see PetCompanionController).
-- Cultivating characters get a different, anime aura: see CharacterAura.
--
-- Auras are being rebuilt one element at a time. AuraBuilder.build returns
-- nil for an element that has no aura yet (no entry in AuraStyles.Auras).
--
-- Each equipped pet of a cultivating player gets the aura of its own element
-- (PetCompanionController builds them with isPet = true).
--
-- Each element has its own builder and per-frame animation (ELEMENTS below).
--
-- Aqua Wisp: six glowing water droplets orbit the body at different heights,
-- so together they trace a slowly turning spiral, each leaving a short
-- teardrop trail. Sparkling water motes and tiny bubbles drift up around the
-- body, and a soft cyan light and faint body glow make it look magical.
-- Textures were rendered in Blender (tools/blender/AquaWispAura.blend).
--
-- Golden Kirin: an ornate golden ring turns around the waist, emerald and
-- gold leaves spiral up the body, golden diamond motes hover around it and a
-- small crown floats over the head, with jade-gold glints and a warm glow.
-- The pieces were modelled in Blender (tools/blender/GoldenKirinVFX.blend) and
-- imported into ReplicatedStorage.AuraMeshes; missing pieces are skipped.
--
-- Moving pieces are anchored parts outside the character, placed relative to
-- it every frame (see AuraBuilder.update), so they can't affect movement.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
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

local addSoftGlow -- Defined below

local function buildAquaWisp(aura, style)
    local body = aura.body
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

    addSoftGlow(aura, style)
end

-- Soft glow in the element's colour: a light on the body and a faint tint
-- over the character
addSoftGlow = function(aura, style)
    local light = Instance.new("PointLight")
    light.Color = style.Main
    light.Range = style.LightRange
    light.Brightness = 0
    light.Shadows = false
    light.Parent = aura.volume
    aura.light = light
    aura.lightBrightness = style.LightBrightness * aura.boost * aura.amount

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

local function animateAquaWisp(aura, now, rootCFrame, parts, cframes)
    local style, body = aura.style, aura.body
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
end

-- Golden Kirin -------------------------------------------------------------------

-- A piece modelled in Blender (tools/blender/GoldenKirinVFX.blend), imported
-- into ReplicatedStorage.AuraMeshes. Its parts are welded to an invisible
-- anchored root, so moving the root moves the whole piece. `longest` is its
-- size in studs. "<Name>_Glow_<rrggbb>" parts glow as Neon in that colour.
-- Returns nil if the piece hasn't been imported.
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
    local random = Random.new(aura.player.UserId + (if aura.isPet then 7 else 0))

    -- The ornate ring circling the waist; around a pet, just clear of its body
    -- (a pet is long, so sizing it like a character's would make it huge)
    local ringDiameter = if aura.isPet then (body.Reach + 0.4) * 2 else aura.orbitRadius * 2 * style.RingSize
    aura.ring = meshPiece(aura, "KirinVFX_Ring", ringDiameter, true)

    -- A crown ornament hovering over the head: spires for characters, a leaf
    -- crown for pets
    aura.crown = meshPiece(aura, if aura.isPet then "KirinVFX_CrownLeaf" else "KirinVFX_CrownSpire",
        style.CrownSize * height, true)

    -- Emerald and gold leaves spiralling up around the body (they fade at the
    -- ends of the climb themselves, see animateGoldenKirin)
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

    -- Golden diamond motes hovering in place around the body
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

    -- Jade-gold glints twinkling around the body
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
        -- Turning slowly, its tilt wandering gently so it catches the light
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

    -- Leaves climb in a spiral from the feet to above the head, tumbling,
    -- fading in at the bottom and out at the top
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
        -- Facing along the orbit, pitched up and rolling as it tumbles
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

-- Each element's builder and per-frame animation, keyed by pet ID
local ELEMENTS = {
    AquaWisp = { Build = buildAquaWisp, Animate = animateAquaWisp },
    GoldenKirin = { Build = buildGoldenKirin, Animate = animateGoldenKirin },
}

-- Public API ---------------------------------------------------------------

-- Builds a (still invisible) aura around a character or a pet companion, or
-- returns nil when the element has no aura yet. petId selects the element,
-- rankId (the owner's rank) how strong it is. For pets, pass isPet = true:
-- the aura is measured around the pet model, a little lighter, without the
-- body tint.
function AuraBuilder.build(player, character, rootPart, petId, rankId, isPet)
    local style = AuraStyles.Auras[petId or "Neutral"]
    if not style or not ELEMENTS[petId] then
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
        -- Orbiting pieces stay clear of the body: pets are often longer than they are tall
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

    -- An invisible box around the body: particles drift out of it and the light sits in it
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
    local body = aura.body
    local rootCFrame = aura.rootPart.CFrame
    aura.animate(aura, now, rootCFrame, parts, cframes)

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

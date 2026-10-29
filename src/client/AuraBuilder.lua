
-- Builds, animates and removes one cultivation aura. AuraController decides
-- when an aura should exist; this module decides how it looks.
--
-- Moving pieces sit on anchored, invisible "mover" parts that are placed
-- relative to the character every frame (see AuraBuilder.update). They live
-- outside the character, so they can't fall, break joints or affect movement.
-- The main silhouette is an "aura shell" of energy tongues wrapping the body.
-- Energy visibly flows through "comets": points that travel along each
-- stream every few seconds, leaving trails of light.

local ContentProvider = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))

local AuraBuilder = {}

AuraBuilder.REMOVE_DELAY = 2.6 -- Seconds after fading out before removal, so particles can finish

local FADE_IN = TweenInfo.new(1, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(0.7, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local TRAIL_START_DELAY = 0.15 -- Trails start once everything is in place, so no streak appears

local FULL_TURN = 2 * math.pi
local QUARTER_ARC_HANDLE = 0.5523 -- Curve handle (per stud of radius) for drawing a circle from quarter-arcs
local SIGIL_PIXELS_PER_STUD = 32
local SIGIL_MAX_DROP = 14 -- How far below the body to look for the ground
local MAX_SHEDDING_ORBS = 2 -- Orbs per aura that shed droplets or embers
local PULSE_SECONDS = 3.5 -- Time for a jade pulse to rise from the feet to above the head
local BEAM_GLOW_SCALE = 0.7 -- Multiplies every beam's LightEmission (see createBeam)

-- Built-in engine textures (not uploaded assets). Checked in Studio:
--   Fire's colour is dark, so fire particles need a high Brightness to show
--   Glow is a soft round dot, good for motes, droplets and embers
--   Sparks is a small streak for crackling electricity
local textures = {
    Spark = "rbxasset://textures/particles/sparkles_main.dds",
    Smoke = "rbxasset://textures/particles/smoke_main.dds",
    Fire = "rbxasset://textures/particles/fire_main.dds",
    Glow = "rbxasset://textures/particles/explosion01_implosion_main.dds",
    Sparks = "rbxasset://textures/particles/fire_sparks_main.dds",
}

-- Whether each texture loaded: true, false, or nil while still being checked.
-- Particles fall back to the default texture if one failed. Beams only use
-- the smoke texture once it's confirmed; otherwise they stay plain.
local textureLoaded = { Spark = true }

task.spawn(function()
    for _, name in { "Smoke", "Fire", "Glow", "Sparks" } do
        local loaded = true
        pcall(function()
            ContentProvider:PreloadAsync({ textures[name] }, function(_, status)
                loaded = status == Enum.AssetFetchStatus.Success
            end)
        end)

        textureLoaded[name] = loaded
        if not loaded then
            warn("AuraBuilder: the " .. name .. " texture didn't load, so it isn't used")
        end
    end
end)

local function particleTexture(name)
    return if textureLoaded[name] == false then textures.Spark else textures[name]
end

-- Optional uploaded textures from AuraStyles.CustomTextures (see there).
-- Slots that are empty, malformed or fail to load are simply not used.
local customTextures = {}
for name, id in AuraStyles.CustomTextures do
    if typeof(id) == "string" and string.match(id, "^rbxassetid://%d+$") then
        customTextures[name] = id
    elseif id ~= "" then
        warn("AuraStyles.CustomTextures." .. name .. " should look like rbxassetid://123456, so it isn't used")
    end
end

task.spawn(function()
    for name, id in customTextures do
        local loaded = true
        pcall(function()
            ContentProvider:PreloadAsync({ id }, function(_, status)
                loaded = status == Enum.AssetFetchStatus.Success
            end)
        end)

        if not loaded then
            customTextures[name] = nil
            warn("AuraBuilder: custom texture " .. name .. " (" .. id .. ") didn't load, so it isn't used")
        end
    end
end)

-- Texture for flowing beams: only the custom energy streak. (The built-in
-- smoke texture was tried and checked in Studio: wrapped along a wide beam
-- it is mostly transparent, so flame tongues almost disappeared.)
local function flowTexture()
    return customTextures.EnergyStreak
end

-- Texture for round glowing particles (orbs, motes, droplets)
local function glowTexture()
    return customTextures.SoftGlow or particleTexture("Glow")
end

-- Small helpers ------------------------------------------------------------

local warnedProperties = {}

-- Sets a property that may not exist in every Roblox version, without
-- breaking the aura if it doesn't (warns once instead)
local function trySet(instance, property, value)
    local ok = pcall(function()
        instance[property] = value
    end)

    local key = instance.ClassName .. "." .. property
    if not ok and not warnedProperties[key] then
        warnedProperties[key] = true
        warn("AuraBuilder: " .. key .. " isn't supported here, so it was skipped")
    end
end

-- numberSequence({ {time, value, variation}, ... }); variation is optional and
-- gives each particle a slightly different value
local function numberSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, NumberSequenceKeypoint.new(point[1], point[2], point[3] or 0))
    end
    return NumberSequence.new(keypoints)
end

-- colorSequence({ {time, color}, ... })
local function colorSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, ColorSequenceKeypoint.new(point[1], point[2]))
    end
    return ColorSequence.new(keypoints)
end

local function tangentAt(angle)
    return Vector3.new(-math.sin(angle), 0, math.cos(angle))
end

local function pointOnCircle(angle, radius, y)
    return Vector3.new(math.cos(angle) * radius, y or 0, math.sin(angle) * radius)
end

-- Records a property that tweens between hidden and visible as the aura
-- appears and disappears. It starts hidden.
local function addFade(aura, instance, property, visibleValue, hiddenValue)
    instance[property] = hiddenValue
    table.insert(aura.fades, {
        Instance = instance,
        Property = property,
        Visible = visibleValue,
        Hidden = hiddenValue,
    })
end

-- An endless tween (repeating, or going back and forth when reverses is true)
local function addLoop(aura, instance, seconds, goal, reverses)
    local easing = if reverses then Enum.EasingStyle.Sine else Enum.EasingStyle.Linear
    local tweenInfo = TweenInfo.new(math.abs(seconds), easing, Enum.EasingDirection.InOut, -1, reverses == true)
    local tween = TweenService:Create(instance, tweenInfo, goal)
    tween:Play()
    table.insert(aura.loops, tween)
    return tween
end

local function setUpInvisiblePart(part)
    part.Anchored = true
    part.Transparency = 1
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
end

-- An anchored invisible part that follows the character. Offset is relative
-- to the HumanoidRootPart; Spin (radians per second) turns it around its own
-- up axis; Sway (degrees) rocks it gently.
local function createMover(aura, name, offset, spin, sway, size)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size or Vector3.new(0.2, 0.2, 0.2)
    setUpInvisiblePart(part)
    part.CFrame = aura.rootPart.CFrame * offset -- Start in place so nothing streaks in from far away
    part.Parent = aura.model

    local mover = {
        Part = part,
        Offset = offset,
        Spin = spin or 0,
        Sway = math.rad(sway or 0),
        Phase = #aura.movers * 1.7,
    }
    table.insert(aura.movers, mover)
    return mover
end

-- An attachment at `position`. If `axis` is given, the attachment's Axis
-- points along it: a beam curves out of its first attachment along that Axis
-- and into its second attachment along it too.
local function createAttachment(parent, position, axis)
    local attachment = Instance.new("Attachment")
    if axis then
        local x = axis.Unit
        local reference = if math.abs(x.Y) > 0.99 then Vector3.xAxis else Vector3.yAxis
        local z = x:Cross(reference).Unit
        attachment.CFrame = CFrame.fromMatrix(position, x, z:Cross(x))
    else
        attachment.Position = position
    end
    attachment.Parent = parent
    return attachment
end

-- A camera-facing beam that grows from nothing as the aura appears.
-- settings: Width (or Width0 / Width1), Color, Transparency, LightEmission,
-- and optionally Curve0, Curve1, Segments, Brightness, ZOffset,
-- Flow = { Length, Speed } (soft texture scrolling along the beam) and
-- ManualWidth (width is set every frame by update instead of fading)
local function createBeam(aura, parent, attachment0, attachment1, settings)
    local beam = Instance.new("Beam")
    beam.Attachment0 = attachment0
    beam.Attachment1 = attachment1
    beam.CurveSize0 = settings.Curve0 or 0
    beam.CurveSize1 = settings.Curve1 or 0
    beam.Segments = settings.Segments or 12
    beam.FaceCamera = true
    beam.LightInfluence = 0
    -- Toned down from each beam's setting: in daylight, with the place's Bloom,
    -- strongly additive beams washed every element out to white (checked in Studio)
    beam.LightEmission = settings.LightEmission * BEAM_GLOW_SCALE
    beam.Color = settings.Color
    beam.Transparency = settings.Transparency
    beam.ZOffset = settings.ZOffset or 0
    trySet(beam, "Brightness", settings.Brightness or 1.5)

    local flowingTexture = settings.Flow and flowTexture()
    if flowingTexture then
        beam.Texture = flowingTexture
        beam.TextureMode = Enum.TextureMode.Wrap
        beam.TextureLength = settings.Flow.Length
        beam.TextureSpeed = settings.Flow.Speed
    end

    beam.Parent = parent

    if settings.ManualWidth then
        beam.Width0 = 0
        beam.Width1 = 0
    else
        addFade(aura, beam, "Width0", settings.Width0 or settings.Width, 0)
        addFade(aura, beam, "Width1", settings.Width1 or settings.Width, 0)
    end
    return beam
end

-- A particle emitter whose rate fades in and out with the aura
--
-- Glow note (checked in Studio): fully additive particles (LightEmission near
-- 1) vanish against the bright daytime sky and pale floors, so particles here
-- use a medium LightEmission and get their glow from Brightness instead.
local function createEmitter(aura, parent, rate, properties)
    local emitter = Instance.new("ParticleEmitter")
    emitter.LightInfluence = 0
    emitter.Texture = textures.Spark
    for property, value in properties do
        if property == "Brightness" then
            trySet(emitter, property, value)
        else
            emitter[property] = value
        end
    end
    emitter.Parent = parent
    addFade(aura, emitter, "Rate", rate, 0)
    return emitter
end

-- A camera-facing light trail between two attachments. It switches on just
-- after the aura appears (see AuraBuilder.show).
local function createTrail(aura, parent, attachment0, attachment1, settings)
    local trail = Instance.new("Trail")
    trail.Attachment0 = attachment0
    trail.Attachment1 = attachment1
    trail.Enabled = false
    trail.Lifetime = settings.Lifetime
    trail.FaceCamera = true
    trail.LightInfluence = 0
    trail.LightEmission = settings.LightEmission or 0.7
    trail.Color = settings.Color
    trail.Transparency = settings.Transparency
    trail.WidthScale = settings.WidthScale or numberSequence({ { 0, 1 }, { 1, 0.2 } })
    if customTextures.EnergyStreak then
        trail.Texture = customTextures.EnergyStreak
        trail.TextureMode = Enum.TextureMode.Stretch
    end
    trySet(trail, "Brightness", settings.Brightness or 1.5)
    trail.Parent = parent
    table.insert(aura.trails, trail)
    return trail
end

-- A comet: a point that travels along `path` (progress 0 to 1 -> position on
-- the mover) every FlowSeconds, leaving a light trail, so energy visibly
-- flows. `sideways` is the direction the trail's width spans (default up).
-- `options` can override Seconds, Width and Lifetime.
local function addComet(aura, mover, look, path, phase, sideways, options)
    local element, tier = look.Element, look.Tier
    local start = path(0)
    local above = createAttachment(mover.Part, start)
    local below = createAttachment(mover.Part, start)

    local trail = createTrail(aura, mover.Part, above, below, {
        Lifetime = if options and options.Lifetime then options.Lifetime else 0.35 * tier.Flow,
        Color = colorSequence({ { 0, element.Core }, { 0.35, element.Main }, { 1, element.Deep } }),
        Transparency = numberSequence({ { 0, 0 }, { 0.4, 0.35 }, { 1, 1 } }),
        WidthScale = numberSequence({ { 0, 1 }, { 1, 0.15 } }),
        LightEmission = 0.8,
        Brightness = 2,
    })

    table.insert(aura.comets, {
        Above = above,
        Below = below,
        Trail = trail,
        Path = path,
        Seconds = if options and options.Seconds then options.Seconds else element.FlowSeconds / tier.Flow,
        Phase = phase,
        Offset = (sideways or Vector3.yAxis) * ((if options and options.Width then options.Width else element.CometWidth) * tier.Size / 2),
        LastProgress = 0,
        Paused = false,
    })
end

-- A path winding up around the body (matches createSpiralPoints). `curl`
-- optionally makes the radius weave in and out, like a curling flame.
local function helixPath(startAngle, sweep, bottomY, topY, bottomRadius, topRadius, curl)
    return function(progress)
        local radius = bottomRadius + (topRadius - bottomRadius) * progress
        if curl then
            radius += math.sin(progress * math.pi * 3) * curl
        end
        return pointOnCircle(startAngle + sweep * progress, radius, bottomY + (topY - bottomY) * progress)
    end
end

-- Body measurements --------------------------------------------------------

-- Measures the avatar relative to its HumanoidRootPart, so the aura fits
-- R6, R15 and differently sized avatars.
local function measureBody(character, rootPart)
    local rootCFrame = rootPart.CFrame
    local boxCFrame, boxSize = character:GetBoundingBox()
    local feetY = rootCFrame:PointToObjectSpace(boxCFrame.Position).Y - boxSize.Y / 2

    local head = character:FindFirstChild("Head")
    local headTopY = if head and head:IsA("BasePart")
        then rootCFrame:PointToObjectSpace(head.Position).Y + head.Size.Y / 2
        else feetY + 5.3

    local height = math.clamp(headTopY - feetY, 3, 12)
    return { FeetY = feetY, HeadTopY = feetY + height, Height = height }
end

-- The space around the body that body-wide particles are emitted from
local function bodyVolume(aura, look)
    local height, size = aura.body.Height, look.Tier.Size
    return Vector3.new(0.5 * height * size, 0.8 * height, 0.5 * height * size)
end

-- Rings and orbs -----------------------------------------------------------

-- Draws a ring of light on a mover: a bright core line plus a wide soft glow.
-- Circles are four curved quarter-arcs; polygons are straight edges.
-- Returns the attachments at the ring's points (the corners, for polygons).
local function addRingLines(aura, mover, look, radius, sides)
    local element, tier = look.Element, look.Tier
    local isPolygon = sides ~= nil
    local count = sides or 4

    local points = {}
    for index = 0, count - 1 do
        local angle = index / count * FULL_TURN
        local axis = if isPolygon then nil else tangentAt(angle)
        table.insert(points, createAttachment(mover.Part, pointOnCircle(angle, radius), axis))
    end

    local handle = if isPolygon then 0 else radius * QUARTER_ARC_HANDLE
    local coreMiddle = 0.05 + (1 - tier.Intensity) * 0.3
    local coreTransparency = numberSequence({ { 0, coreMiddle + 0.15 }, { 0.5, coreMiddle }, { 1, coreMiddle + 0.15 } })
    local glowTransparency = NumberSequence.new(1 - 0.22 * tier.Intensity)

    for index = 1, count do
        local startPoint = points[index]
        local endPoint = points[index % count + 1]

        createBeam(aura, mover.Part, startPoint, endPoint, {
            Curve0 = handle,
            Curve1 = handle,
            Segments = if isPolygon then 1 else 12,
            Width = element.RingWidth * tier.Size,
            Color = ColorSequence.new(element.Core),
            Transparency = coreTransparency,
            LightEmission = 0.5,
            Brightness = 1.2,
            ZOffset = 0.1, -- Draw the core in front of its glow
        })

        createBeam(aura, mover.Part, startPoint, endPoint, {
            Curve0 = handle,
            Curve1 = handle,
            Segments = if isPolygon then 1 else 12,
            Width = element.GlowWidth * tier.Size,
            Color = ColorSequence.new(element.Main),
            Transparency = glowTransparency,
            LightEmission = 0.6,
        })
    end

    return points
end

-- Particles that orbs shed as they travel (droplets for water, embers for fire)
local function addOrbShedding(aura, point, look)
    local element, size = look.Element, look.Tier.Size

    if element.Particles == "Droplet" then
        createEmitter(aura, point, 4 + look.Tier.Particles, {
            Texture = glowTexture(),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.45,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.45 * size, 0.15 * size }, { 1, 0.15 * size } }),
            Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.8),
            Speed = NumberRange.new(1, 2),
            SpreadAngle = Vector2.new(70, 70),
            Acceleration = Vector3.new(0, -4, 0), -- Droplets arc up and fall away
            Drag = 0.5,
        })
    elseif element.Particles == "Ember" then
        createEmitter(aura, point, 5 + look.Tier.Particles, {
            Texture = glowTexture(),
            Color = colorSequence({ { 0, element.Core }, { 0.5, element.Main }, { 1, element.Deep } }),
            LightEmission = 0.5,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.32 * size, 0.12 * size }, { 1, 0.05 } }),
            Transparency = numberSequence({ { 0, 0 }, { 0.3, 0.4 }, { 0.5, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.8, 1.4),
            Speed = NumberRange.new(1.5, 3),
            SpreadAngle = Vector2.new(40, 40),
            Acceleration = Vector3.new(0, 3, 0),
            Drag = 0.8,
        })
    elseif element.Particles == "Spark" then
        createEmitter(aura, point, 6 + look.Tier.Particles, {
            Texture = particleTexture("Sparks"),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.6,
            Brightness = 2.5,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Size = numberSequence({ { 0, 0.3 * size }, { 1, 0.05 } }),
            Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.12, 0.25),
            Speed = NumberRange.new(5, 9),
            SpreadAngle = Vector2.new(180, 180),
            Drag = 6,
        })
    end
end

-- Orbs travelling around a ring. Orbs with heads get a bright glow and (for
-- the first few) shed particles; every orb leaves a light trail if the
-- element has trails.
local function addOrbs(aura, mover, look, radius, count, withHeads)
    local element, size = look.Element, look.Tier.Size
    local sheds = element.Particles == "Droplet" or element.Particles == "Ember" or element.Particles == "Spark"

    for index = 1, count do
        local position = pointOnCircle(index / count * FULL_TURN, radius)
        local point = createAttachment(mover.Part, position)

        if withHeads then
            -- Short-lived particles locked to the point make a glowing head
            createEmitter(aura, point, 16, {
                Texture = glowTexture(),
                LockedToPart = true,
                -- Core fading to Main: the pale Core alone read as plain white balls
                Color = ColorSequence.new(element.Core, element.Main),
                LightEmission = 0.6,
                Brightness = 2.5,
                Size = NumberSequence.new(0.9 * size),
                Transparency = numberSequence({ { 0, 0.5 }, { 0.3, 0.1 }, { 1, 1 } }),
                Lifetime = NumberRange.new(0.25),
                Speed = NumberRange.new(0),
                Rotation = NumberRange.new(0, 360),
                ZOffset = 0.5,
            })

            if sheds and aura.sheddingOrbs < MAX_SHEDDING_ORBS then
                aura.sheddingOrbs += 1
                addOrbShedding(aura, point, look)
            end
        end

        if element.TrailLifetime > 0 then
            createTrail(
                aura,
                mover.Part,
                createAttachment(mover.Part, position + Vector3.new(0, 0.22 * size, 0)),
                createAttachment(mover.Part, position - Vector3.new(0, 0.22 * size, 0)),
                {
                    Lifetime = element.TrailLifetime,
                    Color = ColorSequence.new(element.Core, element.Main),
                    Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
                    LightEmission = 0.6,
                }
            )
        end
    end
end

-- Small crystal glints at a polygon ring's corners (every `step`-th corner,
-- default every one; each glint is a particle emitter, so this saves budget)
local function addCornerGlints(aura, points, look, step)
    for index = 1, #points, step or 1 do
        local point = points[index]
        createEmitter(aura, point, 10, {
            LockedToPart = true,
            Color = ColorSequence.new(look.Element.Core, look.Element.Main),
            LightEmission = 0.6,
            Brightness = 2,
            Size = NumberSequence.new(0.8 * look.Tier.Size),
            Transparency = numberSequence({ { 0, 0.4 }, { 0.5, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.3),
            Speed = NumberRange.new(0),
            Rotation = NumberRange.new(45),
            ZOffset = 0.5,
        })
    end
end

local function createRings(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local sides = if element.RingShape == "Polygon" then element.RingSides else nil

    for index = 1, tier.Rings do
        local layout = AuraStyles.RingLayout[index]
        local radius = layout.Radius * body.Height * tier.Size
        local offset = CFrame.new(0, body.FeetY + layout.Height * body.Height, 0)
            * CFrame.Angles(math.rad(layout.TiltX), 0, math.rad(layout.TiltZ))
        local mover = createMover(aura, "Ring" .. index, offset, layout.Spin * element.Spin, element.Sway)
        local points = addRingLines(aura, mover, look, radius, sides)

        -- Only the first ring gets glowing heads or corner glints, to keep the
        -- number of emitters low; outer rings rely on trails and lines
        if sides then
            if index == 1 then
                addCornerGlints(aura, points, look)
            end
        else
            addOrbs(aura, mover, look, radius, tier.Orbs[index] or 0, index == 1)
        end
    end
end

-- Rising streams -----------------------------------------------------------

-- Points along a curve that winds up around the body. Each point's curve
-- handle follows the circle and leans upward, so beams between consecutive
-- points form a smooth spiral.
local function createSpiralPoints(mover, startAngle, sweep, segments, bottomY, topY, bottomRadius, topRadius)
    local points = {}
    local segmentSweep = sweep / segments
    local lift = (topY - bottomY) / segments / 3

    for index = 0, segments do
        local progress = index / segments
        local angle = startAngle + sweep * progress
        local radius = bottomRadius + (topRadius - bottomRadius) * progress
        local y = bottomY + (topY - bottomY) * progress
        local handle = tangentAt(angle) * (4 / 3 * math.tan(segmentSweep / 4) * radius) + Vector3.new(0, lift, 0)

        table.insert(points, {
            Attachment = createAttachment(mover.Part, pointOnCircle(angle, radius, y), handle),
            Curve = handle.Magnitude,
        })
    end

    return points
end

local function streamRange(aura, look)
    local body, size = aura.body, look.Tier.Size
    return body.FeetY - 1.2, body.HeadTopY + 1.4 * size
end

-- The streams' mover also serves as the volume that body-wide particles
-- are emitted from
local function createStreamMover(aura, look, spin)
    local mover = createMover(aura, "Streams", CFrame.new(), spin, 0, bodyVolume(aura, look))
    aura.bodyPart = mover.Part
    aura.streamMover = mover
    return mover
end

-- Neutral: spirals of light with a thin bright core and a soft flowing glow,
-- and comets climbing them. The formation turns in the direction that makes
-- the spirals appear to climb too.
local function createSpiralStreams(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local bottomY, topY = streamRange(aura, look)
    local bottomRadius, topRadius = 0.6 * body.Height * tier.Size, 0.45 * body.Height * tier.Size
    local sweep = math.rad(220)
    local mover = createStreamMover(aura, look, 0.5 * element.Spin)

    for index = 1, tier.Streams do
        local startAngle = index / tier.Streams * FULL_TURN
        local points = createSpiralPoints(mover, startAngle, sweep, 2, bottomY, topY, bottomRadius, topRadius)

        for segment = 1, 2 do
            local from, to = points[segment], points[segment + 1]
            local isFirst = segment == 1

            createBeam(aura, mover.Part, from.Attachment, to.Attachment, {
                Curve0 = from.Curve,
                Curve1 = to.Curve,
                Segments = 16,
                Width0 = (if isFirst then 0.04 else 0.09) * tier.Size,
                Width1 = (if isFirst then 0.09 else 0.05) * tier.Size,
                Color = ColorSequence.new(element.Core),
                Transparency = numberSequence(if isFirst
                    then { { 0, 1 }, { 0.5, 0.2 }, { 1, 0.1 } }
                    else { { 0, 0.1 }, { 0.6, 0.25 }, { 1, 1 } }),
                LightEmission = 0.6,
                Brightness = 1.5,
                ZOffset = 0.1,
            })

            createBeam(aura, mover.Part, from.Attachment, to.Attachment, {
                Curve0 = from.Curve,
                Curve1 = to.Curve,
                Segments = 16,
                Width0 = (if isFirst then 0.3 else 0.75) * tier.Size,
                Width1 = (if isFirst then 0.75 else 0.4) * tier.Size,
                Color = ColorSequence.new(element.Main),
                Transparency = numberSequence(if isFirst
                    then { { 0, 1 }, { 0.5, 0.65 }, { 1, 0.55 } }
                    else { { 0, 0.55 }, { 0.6, 0.65 }, { 1, 1 } }),
                LightEmission = 0.8,
                Flow = { Length = 3, Speed = 1.2 * tier.Flow },
            })
        end

        addComet(aura, mover, look, helixPath(startAngle, sweep, bottomY, topY, bottomRadius, topRadius), index * 0.9)
    end
end

-- Water: wide flowing ribbons with a bright spine. Their middle points
-- ripple every frame, so the ribbons undulate instead of sitting rigidly.
local function createRibbonStreams(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local bottomY, topY = streamRange(aura, look)
    local bottomRadius, topRadius = 0.62 * body.Height * tier.Size, 0.48 * body.Height * tier.Size
    local sweep = math.rad(300)
    local mover = createStreamMover(aura, look, 0.3 * element.Spin)
    local count = math.max(2, tier.Streams - 1)

    local widths = { 0.1, 0.65, 0.55, 0.08 }
    local colors = { element.Deep, element.Main, element.Main, element.Core }

    for index = 1, count do
        local startAngle = index / count * FULL_TURN
        local points = createSpiralPoints(mover, startAngle, sweep, 3, bottomY, topY, bottomRadius, topRadius)

        for segment = 1, 3 do
            local from, to = points[segment], points[segment + 1]
            local ribbonFade = if segment == 1
                then { { 0, 1 }, { 1, 0.5 } }
                elseif segment == 3 then { { 0, 0.5 }, { 1, 1 } }
                else { { 0, 0.5 }, { 1, 0.5 } }
            local spineFade = if segment == 1
                then { { 0, 1 }, { 1, 0.3 } }
                elseif segment == 3 then { { 0, 0.3 }, { 1, 1 } }
                else { { 0, 0.3 }, { 1, 0.3 } }

            createBeam(aura, mover.Part, from.Attachment, to.Attachment, {
                Curve0 = from.Curve,
                Curve1 = to.Curve,
                Segments = 16,
                Width0 = widths[segment] * tier.Size,
                Width1 = widths[segment + 1] * tier.Size,
                Color = ColorSequence.new(colors[segment], colors[segment + 1]),
                Transparency = numberSequence(ribbonFade),
                LightEmission = 0.5,
                Brightness = 1.6,
                Flow = { Length = 4, Speed = 1.4 * tier.Flow },
            })

            createBeam(aura, mover.Part, from.Attachment, to.Attachment, {
                Curve0 = from.Curve,
                Curve1 = to.Curve,
                Segments = 16,
                Width = 0.05 * tier.Size,
                Color = ColorSequence.new(element.Core),
                Transparency = numberSequence(spineFade),
                LightEmission = 0.6,
                Brightness = 1.5,
                ZOffset = 0.1,
            })
        end

        for pointIndex = 2, 3 do
            local attachment = points[pointIndex].Attachment
            local base = attachment.Position
            table.insert(aura.waves, {
                Attachment = attachment,
                Base = base,
                Outward = Vector3.new(base.X, 0, base.Z).Unit,
                Phase = index * 1.3 + pointIndex,
                Amount = 0.35 * tier.Size,
            })
        end

        addComet(aura, mover, look, helixPath(startAngle, sweep, bottomY, topY, bottomRadius, topRadius), index * 1.1)
    end
end

-- One tongue of flame from `base` upward: a soft outer flame with smoke
-- flowing up through it, and a brighter hot core. Its tip sways every frame.
local function addFlameTongue(aura, mover, look, base, height, width)
    local element = look.Element
    local root = createAttachment(mover.Part, base, Vector3.yAxis)
    local tipBase = base + Vector3.new(0, height, 0)
    local tip = createAttachment(mover.Part, tipBase)

    createBeam(aura, mover.Part, root, tip, {
        Curve0 = height * 0.35,
        Segments = 10,
        Width0 = width,
        Width1 = 0.06,
        Color = colorSequence({ { 0, element.Main }, { 0.5, element.Main }, { 1, element.Deep } }),
        Transparency = numberSequence({ { 0, 0.6 }, { 0.2, 0.25 }, { 0.75, 0.5 }, { 1, 1 } }),
        LightEmission = 0.85,
        Brightness = 1.8,
        Flow = { Length = 2.5, Speed = 2.2 * look.Tier.Flow },
    })

    createBeam(aura, mover.Part, root, tip, {
        Curve0 = height * 0.35,
        Segments = 10,
        Width0 = width * 0.4,
        Width1 = 0.03,
        Color = colorSequence({ { 0, element.Core }, { 0.6, element.Main }, { 1, element.Main } }),
        Transparency = numberSequence({ { 0, 0.45 }, { 0.15, 0.05 }, { 0.55, 0.35 }, { 1, 1 } }),
        LightEmission = 0.6,
        Brightness = 2.5,
        ZOffset = 0.1,
    })

    table.insert(aura.flames, {
        Tip = tip,
        TipBase = tipBase,
        Phase = #aura.flames * 2.3,
        Amount = 0.25 + height * 0.06,
        Speed = 1,
        Stretch = 0.25,
    })
end

-- Fire: thick swirls of flame winding quickly up around the body, with a hot
-- core, plus curling fire wisps. (The aura shell provides the flame tongues.)
local function createFlameStreams(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local bottomY, topY = streamRange(aura, look)
    local bottomRadius, topRadius = 0.58 * body.Height * tier.Size, 0.42 * body.Height * tier.Size
    local sweep = math.rad(240)
    local mover = createStreamMover(aura, look, 0.9)
    local widths = { 0.1, 0.6, 0.08 }
    local colors = { element.Deep, element.Main, element.Core }

    for index = 1, tier.Streams do
        local startAngle = index / tier.Streams * FULL_TURN
        local points = createSpiralPoints(mover, startAngle, sweep, 2, bottomY, topY, bottomRadius, topRadius)

        for segment = 1, 2 do
            local from, to = points[segment], points[segment + 1]
            local isFirst = segment == 1

            createBeam(aura, mover.Part, from.Attachment, to.Attachment, {
                Curve0 = from.Curve,
                Curve1 = to.Curve,
                Segments = 16,
                Width0 = widths[segment] * tier.Size,
                Width1 = widths[segment + 1] * tier.Size,
                Color = ColorSequence.new(colors[segment], colors[segment + 1]),
                Transparency = numberSequence(if isFirst
                    then { { 0, 1 }, { 0.4, 0.45 }, { 1, 0.35 } }
                    else { { 0, 0.35 }, { 0.6, 0.5 }, { 1, 1 } }),
                LightEmission = 0.9,
                Brightness = 2,
                Flow = { Length = 2.5, Speed = 3 * tier.Flow },
            })

            createBeam(aura, mover.Part, from.Attachment, to.Attachment, {
                Curve0 = from.Curve,
                Curve1 = to.Curve,
                Segments = 16,
                Width = 0.06 * tier.Size,
                Color = ColorSequence.new(element.Core),
                Transparency = numberSequence(if isFirst then { { 0, 1 }, { 1, 0.2 } } else { { 0, 0.2 }, { 1, 1 } }),
                LightEmission = 0.6,
                Brightness = 1.5,
                ZOffset = 0.1,
            })
        end

        local curl = helixPath(
            startAngle + math.pi,
            math.rad(270),
            bottomY,
            topY,
            0.55 * body.Height * tier.Size,
            0.4 * body.Height * tier.Size,
            0.5 * tier.Size
        )
        addComet(aura, mover, look, curl, index * 0.47)
    end
end

-- Jade: hexagonal rings of light that rise steadily from the feet to above
-- the head and fade (their position and width are set every frame), plus
-- crystal comets climbing three straight lines
local function createPulseStreams(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local bottomY, topY = streamRange(aura, look)
    local mover = createStreamMover(aura, look, 0.2 * element.Spin)

    local lineRadius = 0.5 * body.Height * tier.Size
    for index = 1, 3 do
        local angle = index / 3 * FULL_TURN + FULL_TURN / 12
        local outward = Vector3.new(math.cos(angle), 0, math.sin(angle))
        addComet(aura, mover, look, function(progress)
            return pointOnCircle(angle, lineRadius, bottomY + (topY - bottomY) * progress)
        end, index * 0.93, outward)
    end

    local pulseCount = if tier.Streams >= 4 then 2 else 1
    local radius = 0.45 * body.Height * tier.Size
    for index = 1, pulseCount do
        local pulseMover = createMover(aura, "Pulse" .. index, CFrame.new(0, bottomY, 0), 0.3 * element.Spin)

        local corners = {}
        for corner = 0, 5 do
            table.insert(corners, createAttachment(pulseMover.Part, pointOnCircle(corner / 6 * FULL_TURN, radius)))
        end

        local beams = {}
        for corner = 1, 6 do
            table.insert(beams, createBeam(aura, pulseMover.Part, corners[corner], corners[corner % 6 + 1], {
                Segments = 1,
                ManualWidth = true,
                Color = ColorSequence.new(element.Core, element.Main),
                Transparency = NumberSequence.new(0.15),
                LightEmission = 0.6,
                Brightness = 2,
            }))
        end

        table.insert(aura.pulses, {
            Mover = pulseMover,
            Beams = beams,
            Width = 0.14 * tier.Size,
            BottomY = bottomY,
            TopY = topY,
            Phase = (index - 1) * PULSE_SECONDS / pulseCount,
        })
    end
end

-- Fast streaks of light shooting straight up close around the body
local function createRiseLines(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    if not element.RiseLines or tier.RiseLines <= 0 or not aura.streamMover then
        return
    end

    local bottomY = body.FeetY
    local topY = body.HeadTopY + 1.5 * tier.Size
    local radius = 0.35 * body.Height * tier.Size

    for index = 1, tier.RiseLines do
        local angle = index * 2.4 -- Spread unevenly around the body
        local outward = Vector3.new(math.cos(angle), 0, math.sin(angle))
        addComet(aura, aura.streamMover, look, function(progress)
            return pointOnCircle(angle, radius, bottomY + (topY - bottomY) * progress)
        end, index * 0.31, outward, { Seconds = 0.9 / tier.Flow, Width = 0.18, Lifetime = 0.18 })
    end
end

-- Aura shell ---------------------------------------------------------------

-- The aura's main silhouette: tapered tongues of energy rising around the
-- whole body, each a soft outer layer with energy flowing up through it and a
-- brighter core. The element's Shell settings shape them (flames, waves,
-- crystal shards or wisps); the rank sets how many, how tall and how wide.
local function createShell(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local shell = element.Shell
    local mover = createMover(aura, "Shell", CFrame.new(), shell.Spin)
    local baseRadius = 0.42 * body.Height * tier.Size
    local baseY = body.FeetY - 0.4
    local width = shell.Width * tier.ShellWidth * tier.Size
    local tipColor = element[shell.TipColor]
    local coreOpacity = math.min(0.85, shell.Opacity * 1.4)

    local outerColor = colorSequence({ { 0, element.Main }, { 0.5, element.Main }, { 1, tipColor } })
    local coreColor = colorSequence({ { 0, element.Core }, { 0.7, element.Main }, { 1, tipColor } })
    local outerFade = numberSequence({ { 0, 1 }, { 0.12, 1 - shell.Opacity }, { 0.75, 1 - shell.Opacity * 0.85 }, { 1, 1 } })
    local coreFade = numberSequence({ { 0, 1 }, { 0.12, 1 - coreOpacity }, { 0.5, 1 - coreOpacity * 0.7 }, { 1, 1 } })
    -- Straight shards still need a few segments: a beam's Transparency is only
    -- sampled at segment points, and with one segment both ends are fully
    -- faded, so the whole shard disappeared (checked in Studio)
    local segments = if shell.Curve > 0 then 12 else 6

    for index = 1, tier.ShellTongues do
        local angle = index / tier.ShellTongues * FULL_TURN
        -- Alternate tall and short tongues so the outline isn't uniform
        local heightScale = if index % 2 == 0 then 1 else 1 - shell.HeightVariety
        local height = body.Height * tier.ShellHeight * heightScale
        local base = pointOnCircle(angle, baseRadius, baseY)
        local tipBase = pointOnCircle(angle + shell.Twist, baseRadius * shell.TipRadius, baseY + height)

        -- The curve leaves the base upward, leaning along the circle for wrapping shapes
        local root = createAttachment(mover.Part, base, Vector3.yAxis + tangentAt(angle) * shell.Lean)
        local tip = createAttachment(mover.Part, tipBase)

        createBeam(aura, mover.Part, root, tip, {
            Curve0 = height * shell.Curve,
            Segments = segments,
            Width0 = width,
            Width1 = shell.TipWidth * tier.Size,
            Color = outerColor,
            Transparency = outerFade,
            LightEmission = 0.45,
            Brightness = 1.2,
            Flow = { Length = 3, Speed = shell.FlowSpeed * tier.Flow },
        })

        createBeam(aura, mover.Part, root, tip, {
            Curve0 = height * shell.Curve,
            Segments = segments,
            Width0 = width * 0.18,
            Width1 = shell.TipWidth * 0.5 * tier.Size,
            Color = coreColor,
            Transparency = coreFade,
            LightEmission = 0.7,
            Brightness = 1.5,
            ZOffset = 0.1,
        })

        if shell.Sway > 0 then
            table.insert(aura.flames, {
                Tip = tip,
                TipBase = tipBase,
                Phase = index * 2.1,
                Amount = shell.Sway * tier.Size,
                Speed = shell.SwaySpeed,
                Stretch = shell.Stretch * tier.Size,
            })
        end
    end
end

local STREAM_BUILDERS = {
    Spiral = createSpiralStreams,
    Ribbon = createRibbonStreams,
    Flame = createFlameStreams,
    Pulse = createPulseStreams,
}

-- Crowns (top rank) --------------------------------------------------------

local function createHaloCrown(aura, look)
    local element, size, body = look.Element, look.Tier.Size, aura.body
    local radius = 0.3 * body.Height * size
    local offset = CFrame.new(0, body.HeadTopY + 0.1, 0.55) * CFrame.Angles(math.rad(90), 0, 0)
    local mover = createMover(aura, "Crown", offset, 0.25)
    addRingLines(aura, mover, look, radius)

    -- Rays of alternating length around the halo
    for ray = 1, 12 do
        local angle = ray / 12 * FULL_TURN
        local length = (if ray % 2 == 0 then 1 else 0.5) * size
        createBeam(
            aura,
            mover.Part,
            createAttachment(mover.Part, pointOnCircle(angle, radius + 0.2)),
            createAttachment(mover.Part, pointOnCircle(angle, radius + 0.2 + length)),
            {
                Segments = 1,
                Width0 = 0.1 * size,
                Width1 = 0.01,
                Color = ColorSequence.new(element.Core, element.Main),
                Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
                LightEmission = 0.8,
                Brightness = 2,
            }
        )
    end
end

local function createFlameCrown(aura, look)
    local size, body = look.Tier.Size, aura.body
    local radius = 0.2 * body.Height * size
    local mover = createMover(aura, "Crown", CFrame.new(0, body.HeadTopY + 0.45, 0), 0.5)
    addRingLines(aura, mover, look, radius)

    for index = 1, 6 do
        local height = (if index % 2 == 0 then 1.6 else 1) * size
        addFlameTongue(aura, mover, look, pointOnCircle(index / 6 * FULL_TURN, radius), height, 0.4 * size)
    end
end

local function createMoonHalo(aura, look)
    local size, body = look.Tier.Size, aura.body
    local outerRadius = 0.42 * body.Height * size
    local offset = CFrame.new(0, body.HeadTopY - 0.4, 0.75) * CFrame.Angles(math.rad(90), 0, 0)
    local mover = createMover(aura, "Crown", offset, 0.35, 5)
    addRingLines(aura, mover, look, outerRadius)
    addRingLines(aura, mover, look, 0.3 * body.Height * size)
    addOrbs(aura, mover, look, outerRadius, 3, true)
end

local function createCrystalCrown(aura, look)
    local element, size, body = look.Element, look.Tier.Size, aura.body
    local radius = 0.22 * body.Height * size
    local mover = createMover(aura, "Crown", CFrame.new(0, body.HeadTopY + 0.4, 0), 0.25)
    local corners = addRingLines(aura, mover, look, radius, 6)
    addCornerGlints(aura, corners, look, 2)

    -- Crystal spikes of alternating height rising from each corner
    for index, corner in corners do
        local height = (if index % 2 == 0 then 1.5 else 0.9) * size
        createBeam(aura, mover.Part, corner, createAttachment(mover.Part, corner.Position + Vector3.new(0, height, 0)), {
            Segments = 1,
            Width0 = 0.22 * size,
            Width1 = 0.02,
            Color = ColorSequence.new(element.Core, element.Main),
            Transparency = numberSequence({ { 0, 0.1 }, { 1, 0.5 } }),
            LightEmission = 0.6,
            Brightness = 2,
        })
    end
end

local CROWN_BUILDERS = {
    Halo = createHaloCrown,
    FlameCrown = createFlameCrown,
    MoonHalo = createMoonHalo,
    CrystalCrown = createCrystalCrown,
}

-- Particles and light ------------------------------------------------------

-- Each element's own particles. `base` is a flat area around the feet and
-- `bodyPart` is the space around the body.
local ELEMENT_PARTICLES = {
    -- Soft motes drifting up around the body
    Mote = function(aura, look, base, bodyPart)
        local element, size = look.Element, look.Tier.Size
        createEmitter(aura, bodyPart, 6 * look.Tier.Particles, {
            Texture = glowTexture(),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.5,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.45 * size, 0.2 * size }, { 1, 0 } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(2, 3),
            Speed = NumberRange.new(1, 2),
            SpreadAngle = Vector2.new(25, 25),
            Acceleration = Vector3.new(0, 0.5, 0),
        })
    end,

    -- Licks of flame at the feet, curling as they rise, a solid flame body
    -- under them, and drifting embers
    Ember = function(aura, look, base, bodyPart)
        local element, size, amount = look.Element, look.Tier.Size, look.Tier.Particles
        local licks = createEmitter(aura, base, 6 * amount, {
            Texture = particleTexture("Fire"),
            Color = colorSequence({ { 0, element.Core }, { 0.4, element.Main }, { 1, element.Deep } }),
            LightEmission = 0.4,
            Brightness = 4.5,
            Size = numberSequence({ { 0, 1 * size, 0.3 * size }, { 0.4, 1.8 * size, 0.5 * size }, { 1, 0.2 } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.12, 0.3 }, { 0.6, 0.55 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.6, 1.1),
            Speed = NumberRange.new(2.5, 4.5),
            SpreadAngle = Vector2.new(14, 14),
            Acceleration = Vector3.new(0, 3, 0),
            Drag = 1,
            Rotation = NumberRange.new(0, 360),
            RotSpeed = NumberRange.new(-80, 80), -- Curling
        })
        if customTextures.FlameFlipbook then
            -- Plays the 16 flame frames once over each particle's life
            local ok = pcall(function()
                licks.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
                licks.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
                licks.Texture = customTextures.FlameFlipbook
            end)
            if not ok then
                licks.Texture = particleTexture("Fire")
            end
        end
        -- The fire texture is wispy, so soft dots stretched along their path
        -- give the flames a solid, glowing body
        createEmitter(aura, base, 10 * amount, {
            Texture = glowTexture(),
            Color = colorSequence({ { 0, element.Core }, { 0.4, element.Main }, { 1, element.Deep } }),
            LightEmission = 0.3,
            Brightness = 2,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Squash = numberSequence({ { 0, -0.3 }, { 1, -1.2 } }),
            Size = numberSequence({ { 0, 0.9 * size }, { 0.4, 1.1 * size }, { 1, 0.2 } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.35 }, { 0.7, 0.5 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.5, 0.8),
            Speed = NumberRange.new(2, 3.5),
            SpreadAngle = Vector2.new(14, 14),
            Acceleration = Vector3.new(0, 8, 0),
            Drag = 1,
            ZOffset = -0.5, -- Behind the character, so the face isn't covered
        })
        createEmitter(aura, bodyPart, 7 * amount, {
            Texture = glowTexture(),
            Color = colorSequence({ { 0, element.Core }, { 0.5, element.Main }, { 1, element.Deep } }),
            LightEmission = 0.5,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.3 * size, 0.15 * size }, { 1, 0.05 } }),
            Transparency = numberSequence({ { 0, 0 }, { 0.15, 0.4 }, { 0.3, 0.05 }, { 0.5, 0.5 }, { 0.65, 0.1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.6, 2.8),
            Speed = NumberRange.new(2, 4.5),
            SpreadAngle = Vector2.new(35, 35),
            Acceleration = Vector3.new(0, 2.5, 0),
            Drag = 1.2,
        })
    end,

    -- Slow luminous bubbles rising around the body
    Droplet = function(aura, look, base, bodyPart)
        local element, size = look.Element, look.Tier.Size
        createEmitter(aura, bodyPart, 4 * look.Tier.Particles, {
            Texture = glowTexture(),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.45,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.25 * size, 0.1 * size }, { 0.5, 0.5 * size, 0.2 * size }, { 1, 0.1 } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.2 }, { 0.85, 0.35 }, { 1, 1 } }),
            Lifetime = NumberRange.new(2.5, 3.5),
            Speed = NumberRange.new(0.8, 1.4),
            SpreadAngle = Vector2.new(20, 20),
            Acceleration = Vector3.new(0, 0.4, 0),
        })
    end,

    -- Crystal glints held at a diamond angle, pulsing as they rise
    Crystal = function(aura, look, base, bodyPart)
        local element, size = look.Element, look.Tier.Size
        createEmitter(aura, bodyPart, 5 * look.Tier.Particles, {
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.5,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.6 * size, 0.25 * size }, { 0.8, 0.45 * size, 0.15 * size }, { 1, 0 } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.1 }, { 0.4, 0.45 }, { 0.6, 0.1 }, { 0.85, 0.3 }, { 1, 1 } }),
            Lifetime = NumberRange.new(2.5, 3.5),
            Speed = NumberRange.new(0.5, 0.9),
            SpreadAngle = Vector2.new(8, 8),
            Rotation = NumberRange.new(45),
            RotSpeed = NumberRange.new(-15, 15),
        })
    end,

    -- Lightning: short crackling arcs snapping out in every direction and a
    -- few slower violet charge motes
    Spark = function(aura, look, base, bodyPart)
        local element, size, amount = look.Element, look.Tier.Size, look.Tier.Particles
        createEmitter(aura, bodyPart, 10 * amount, {
            Texture = particleTexture("Sparks"),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.6,
            Brightness = 2.5,
            Orientation = Enum.ParticleOrientation.VelocityParallel, -- Streaks point the way they fly
            Size = numberSequence({ { 0, 0.4 * size }, { 1, 0.05 } }),
            Transparency = numberSequence({ { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.15, 0.35),
            Speed = NumberRange.new(8, 14),
            SpreadAngle = Vector2.new(180, 180),
            Drag = 6,
        })
        createEmitter(aura, bodyPart, 4 * amount, {
            Texture = glowTexture(),
            Color = ColorSequence.new(element.Main, element.Deep),
            LightEmission = 0.45,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.3 * size, 0.1 * size }, { 1, 0 } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.2 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.8, 1.2),
            Speed = NumberRange.new(0.5, 1),
            SpreadAngle = Vector2.new(180, 180),
            Acceleration = Vector3.new(0, 1.5, 0),
        })
    end,
}

-- How each element's occasional burst looks (Flowing Meridians and above)
local SPARK_BURSTS = {
    Mote = {
        Count = 10,
        Properties = {
            Size = numberSequence({ { 0, 0.4, 0.15 }, { 1, 0 } }),
            Lifetime = NumberRange.new(0.5, 0.9),
            Speed = NumberRange.new(6, 10),
            SpreadAngle = Vector2.new(75, 75),
            Drag = 3.5,
            Acceleration = Vector3.new(0, -2, 0),
        },
    },
    -- Hot sparks shooting upward
    Ember = {
        Count = 12,
        Properties = {
            Size = numberSequence({ { 0, 0.4, 0.15 }, { 1, 0 } }),
            Lifetime = NumberRange.new(0.5, 0.9),
            Speed = NumberRange.new(7, 11),
            SpreadAngle = Vector2.new(60, 60),
            Drag = 3,
            Acceleration = Vector3.new(0, 4, 0),
        },
    },
    -- A splash of droplets that falls back down
    Droplet = {
        Count = 14,
        Properties = {
            Size = numberSequence({ { 0, 0.35, 0.1 }, { 1, 0.1 } }),
            Lifetime = NumberRange.new(0.8, 1.2),
            Speed = NumberRange.new(5, 8),
            SpreadAngle = Vector2.new(50, 50),
            Drag = 1,
            Acceleration = Vector3.new(0, -12, 0),
        },
    },
    -- A crackle of electricity snapping outward
    Spark = {
        Count = 16,
        Properties = {
            Texture = textures.Sparks,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Size = numberSequence({ { 0, 0.6 }, { 1, 0.1 } }),
            Lifetime = NumberRange.new(0.15, 0.3),
            Speed = NumberRange.new(14, 22),
            SpreadAngle = Vector2.new(180, 180),
            Drag = 6,
        },
    },
    -- A few large crystal flashes
    Crystal = {
        Count = 6,
        Properties = {
            Size = numberSequence({ { 0, 1.2, 0.3 }, { 1, 0 } }),
            Lifetime = NumberRange.new(0.35, 0.5),
            Speed = NumberRange.new(0.5, 1.5),
            SpreadAngle = Vector2.new(180, 180),
            Rotation = NumberRange.new(45),
        },
    },
}

-- Mist, element particles, bursts and the local light
local function createParticlesAndLight(aura, look)
    local element, tier, body = look.Element, look.Tier, aura.body
    local size, amount = tier.Size, tier.Particles
    local width = 0.8 * body.Height * size

    local base = createMover(aura, "Base", CFrame.new(0, body.FeetY + 0.3, 0), 0, 0, Vector3.new(width, 0.4, width))
    local bodyPart = aura.bodyPart or base.Part

    -- Soft mist that gives the aura its overall shape (kept light so the
    -- character stays readable)
    local opacity = element.WispOpacity
    local riseSpeed = if element.Particles == "Ember" then 1.5 else 1
    createEmitter(aura, base.Part, 2 + amount, {
        Texture = particleTexture("Smoke"),
        Color = ColorSequence.new(element.Main, element.Core),
        LightEmission = 0.35,
        Size = numberSequence({ { 0, 1 * size, 0.3 * size }, { 0.5, 2.4 * size, 0.6 * size }, { 1, 3.2 * size, 0.6 * size } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.2, 1 - opacity }, { 0.7, 1 - opacity * 0.6 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2.2, 3),
        Speed = NumberRange.new(1.2 * riseSpeed, 2 * riseSpeed),
        Acceleration = Vector3.new(0, 1.2, 0),
        Drag = 0.6,
        Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-30, 30),
        SpreadAngle = Vector2.new(8, 8),
    })

    -- Aura pressure: soft energy blowing outward along the ground at the feet
    createEmitter(aura, base.Part, 2 + 2 * amount, {
        Texture = particleTexture("Smoke"),
        Color = ColorSequence.new(element.Main),
        LightEmission = 0.4,
        Size = numberSequence({ { 0, 0.6 * size, 0.2 * size }, { 1, 2.4 * size, 0.6 * size } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.75 }, { 1, 1 } }),
        Lifetime = NumberRange.new(0.6, 1),
        Speed = NumberRange.new(3, 5),
        SpreadAngle = Vector2.new(85, 85), -- Fans out sideways in every direction
        Drag = 2.5,
        Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-60, 60),
    })

    ELEMENT_PARTICLES[element.Particles](aura, look, base.Part, bodyPart)

    -- Occasional bursts (see update), not a constant stream
    if tier.Sparks then
        local burst = SPARK_BURSTS[element.Particles]
        local sparks = Instance.new("ParticleEmitter")
        sparks.Texture = textures.Spark
        sparks.Rate = 0
        sparks.LightInfluence = 0
        sparks.LightEmission = 0.6
        trySet(sparks, "Brightness", 2)
        sparks.Color = ColorSequence.new(element.Core, element.Main)
        sparks.Transparency = numberSequence({ { 0, 0 }, { 1, 1 } })
        for property, value in burst.Properties do
            sparks[property] = value
        end
        sparks.Parent = bodyPart
        aura.sparks = sparks
        aura.burstCount = burst.Count
        aura.nextBurst = os.clock() + 1.5
    end

    -- Soft local light at chest height. Its brightness is set every frame so
    -- it can fade, flicker (fire), pulse steadily (jade) or breathe.
    local lightPoint = createAttachment(base.Part, Vector3.new(0, body.Height * 0.6, 0))
    local light = Instance.new("PointLight")
    light.Color = element.Main
    light.Range = 12 * size
    light.Brightness = 0
    light.Shadows = false
    light.Parent = lightPoint
    aura.light = light
    aura.lightBrightness = tier.Light
    aura.lightStyle = if element.Flicker then "Flicker" elseif element.Particles == "Crystal" then "Pulse" else "Breathe"
end

-- Small effects on both hands, so the aura reads on the limbs too and moves
-- with them. Each returns { Rate, Properties } for the hand's emitter.
local HAND_ACCENTS = {
    -- A small flame held in each hand
    Ember = function(element, size)
        return 14, {
            Texture = particleTexture("Fire"),
            Color = colorSequence({ { 0, element.Core }, { 0.4, element.Main }, { 1, element.Deep } }),
            LightEmission = 0.4,
            Brightness = 5,
            Size = numberSequence({ { 0, 0.9 * size }, { 1, 0.2 } }),
            Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.45, 0.7),
            Speed = NumberRange.new(1, 2),
            SpreadAngle = Vector2.new(15, 15),
            Acceleration = Vector3.new(0, 7, 0),
            Rotation = NumberRange.new(0, 360),
            RotSpeed = NumberRange.new(-90, 90),
            ZOffset = 1, -- In front of the arm the flame rises past
        }
    end,
    -- Water dripping from the fingertips
    Droplet = function(element, size)
        return 4, {
            Texture = glowTexture(),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.45,
            Brightness = 2,
            EmissionDirection = Enum.NormalId.Bottom,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Squash = NumberSequence.new(-0.5), -- Teardrop-shaped
            Size = NumberSequence.new(0.15 * size),
            Lifetime = NumberRange.new(0.6, 0.9),
            Speed = NumberRange.new(0.3, 0.8),
            Acceleration = Vector3.new(0, -8, 0),
        }
    end,
    -- Motes floating up from the palms
    Mote = function(element, size)
        return 4, {
            Texture = glowTexture(),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.5,
            Brightness = 2,
            Size = numberSequence({ { 0, 0.22 * size }, { 1, 0 } }),
            Lifetime = NumberRange.new(1, 1.5),
            Speed = NumberRange.new(0.3, 0.8),
            SpreadAngle = Vector2.new(40, 40),
            Acceleration = Vector3.new(0, 1, 0),
        }
    end,
    -- Crystal glints flashing on the hands
    Crystal = function(element, size)
        return 3, {
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.6,
            Brightness = 2,
            Size = numberSequence({ { 0, 0 }, { 0.4, 0.4 * size }, { 1, 0 } }),
            Lifetime = NumberRange.new(0.4),
            Speed = NumberRange.new(0),
            Rotation = NumberRange.new(0, 45),
        }
    end,
    -- Tiny arcs of electricity crackling around the hands
    Spark = function(element, size)
        return 12, {
            Texture = particleTexture("Sparks"),
            Color = ColorSequence.new(element.Core, element.Main),
            LightEmission = 0.6,
            Brightness = 2.5,
            Orientation = Enum.ParticleOrientation.VelocityParallel,
            Size = numberSequence({ { 0, 0.25 * size }, { 1, 0.05 } }),
            Lifetime = NumberRange.new(0.12, 0.25),
            Speed = NumberRange.new(5, 9),
            SpreadAngle = Vector2.new(180, 180),
            Drag = 6,
        }
    end,
}

-- Attachments go inside the character's hands (R15) or arms (R6). They are
-- outside the aura's folder, so AuraBuilder.destroy removes them itself.
local function createHandAccents(aura, look)
    local rate, properties
    for _, names in { { "RightHand", "Right Arm" }, { "LeftHand", "Left Arm" } } do
        local hand = aura.character:FindFirstChild(names[1]) or aura.character:FindFirstChild(names[2])
        if hand and hand:IsA("BasePart") then
            local point = Instance.new("Attachment")
            point.Name = "AuraHand"
            -- R6 arms are long, so use their bottom end
            point.Position = if hand.Name == names[1] then Vector3.new(0, -0.2, 0) else Vector3.new(0, -hand.Size.Y / 2, 0)
            point.Parent = hand
            table.insert(aura.limbAttachments, point)

            rate, properties = HAND_ACCENTS[look.Element.Particles](look.Element, look.Tier.Size)
            createEmitter(aura, point, rate, properties)
        end
    end
end

local function createOutline(aura, look)
    local highlight = Instance.new("Highlight")
    highlight.Adornee = aura.character
    highlight.DepthMode = Enum.HighlightDepthMode.Occluded
    highlight.FillTransparency = 1 -- Outline only, so the character stays fully visible
    highlight.OutlineColor = look.Element.Main
    highlight.Parent = aura.model
    addFade(aura, highlight, "OutlineTransparency", 0.5, 1)
end

-- Ground sigil -------------------------------------------------------------

local function guiFrame(parent, size, rotation)
    local frame = Instance.new("Frame")
    frame.AnchorPoint = Vector2.new(0.5, 0.5)
    frame.Position = UDim2.fromScale(0.5, 0.5)
    frame.Size = size
    frame.Rotation = rotation or 0
    frame.BackgroundTransparency = 1
    frame.BorderSizePixel = 0
    frame.Parent = parent
    return frame
end

local function rounded(frame)
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0.5, 0)
    corner.Parent = frame
    return frame
end

local function circle(parent, diameter)
    return rounded(guiFrame(parent, UDim2.fromScale(diameter, diameter)))
end

local function square(parent, side, rotation)
    return guiFrame(parent, UDim2.fromScale(side, side), rotation)
end

-- A rotating layer that fills the whole sigil
local function turningLayer(aura, parent, secondsPerTurn)
    local layer = guiFrame(parent, UDim2.fromScale(1, 1))
    addLoop(aura, layer, secondsPerTurn, { Rotation = if secondsPerTurn > 0 then 360 else -360 })
    return layer
end

local function outline(aura, frame, color, thickness, opacity)
    local stroke = Instance.new("UIStroke")
    stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
    stroke.Color = color
    stroke.Thickness = thickness
    stroke.Parent = frame
    addFade(aura, stroke, "Transparency", 1 - opacity, 1)
    return stroke
end

local function fill(aura, frame, color, opacity)
    frame.BackgroundColor3 = color
    addFade(aura, frame, "BackgroundTransparency", 1 - opacity, 1)
    return frame
end

-- `count` marks spaced around a circle of `radius` (fraction of the sigil),
-- each turned to point outward
local function marks(aura, parent, count, radius, size, color, opacity, isRound, extraRotation)
    for mark = 1, count do
        local angle = mark / count * 360
        local radians = math.rad(angle)
        local frame = guiFrame(parent, size, angle + (extraRotation or 0))
        frame.Position = UDim2.fromScale(0.5 + radius * math.sin(radians), 0.5 - radius * math.cos(radians))
        if isRound then
            rounded(frame)
        end
        fill(aura, frame, color, opacity)
    end
end

-- A bright section that sweeps around a ring outline
local function sweep(aura, stroke, secondsPerTurn)
    local gradient = Instance.new("UIGradient")
    gradient.Transparency = numberSequence({ { 0, 0 }, { 0.35, 0.3 }, { 0.6, 0.85 }, { 1, 1 } })
    gradient.Parent = stroke
    addLoop(aura, gradient, secondsPerTurn, { Rotation = 360 })
end

-- A ring that repeatedly spreads outward from the middle and fades, starting
-- after `delay` seconds. Ripples aren't in the normal fades, so they're hidden separately.
local function addRipple(aura, canvas, color, thickness, opacity, seconds, delay)
    local ripple = circle(canvas, 0.3)
    local stroke = Instance.new("UIStroke")
    stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
    stroke.Color = color
    stroke.Thickness = thickness
    stroke.Transparency = 1
    stroke.Parent = ripple

    task.delay(delay, function()
        if aura.destroyed or aura.hiding then
            return
        end
        local info = TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.Out, -1)
        stroke.Transparency = 1 - opacity
        local grow = TweenService:Create(ripple, info, { Size = UDim2.fromScale(0.97, 0.97) })
        local fadeAway = TweenService:Create(stroke, info, { Transparency = 1 })
        grow:Play()
        fadeAway:Play()
        table.insert(aura.loops, grow)
        table.insert(aura.loops, fadeAway)
    end)

    table.insert(aura.onHide, function()
        TweenService:Create(stroke, FADE_OUT, { Transparency = 1 }):Play()
    end)
end

-- Neutral: rune ticks, beads and an eight-pointed star
local function runeSigil(aura, canvas, element, detail, opacity)
    local ticks = turningLayer(aura, canvas, 60)
    marks(aura, ticks, if detail >= 3 then 36 else 24, 0.42, UDim2.new(0, 5, 0.05, 0), element.Core, opacity)

    if detail >= 2 then
        local inner = turningLayer(aura, canvas, -90)
        local innerRing = outline(aura, circle(canvas, 0.5), element.Main, 6, opacity)
        marks(aura, inner, 8, 0.25, UDim2.fromOffset(14, 14), element.Core, opacity, false, 45)

        if detail >= 3 then
            outline(aura, square(inner, 0.56, 0), element.Main, 5, opacity * 0.9)
            outline(aura, square(inner, 0.56, 45), element.Main, 5, opacity * 0.9)
        end
        if detail >= 4 then
            sweep(aura, innerRing, 4)
        end
    end

    if detail >= 5 then
        marks(aura, turningLayer(aura, canvas, -120), 48, 0.47, UDim2.fromOffset(8, 8), element.Core, opacity, true)
    end
end

-- Fire: flame petals pointing outward, a sun ring with rays
local function flameSigil(aura, canvas, element, detail, opacity)
    marks(aura, turningLayer(aura, canvas, 40), 12, 0.37, UDim2.fromScale(0.035, 0.11), element.Main, opacity, true)

    if detail >= 2 then
        local sunRing = outline(aura, circle(canvas, 0.5), element.Core, 5, opacity)
        marks(aura, turningLayer(aura, canvas, -60), 24, 0.29, UDim2.new(0, 4, 0.06, 0), element.Core, opacity)
        if detail >= 4 then
            sweep(aura, sunRing, 3)
        end
    end

    if detail >= 3 then
        marks(aura, turningLayer(aura, canvas, -30), 8, 0.17, UDim2.fromScale(0.03, 0.08), element.Core, opacity, true)
    end

    if detail >= 5 then
        marks(aura, turningLayer(aura, canvas, 90), 36, 0.465, UDim2.new(0, 4, 0.03, 0), element.Core, opacity)
    end
end

-- Water: ripples spreading outward and two crescents chasing each other
local function rippleSigil(aura, canvas, element, detail, opacity)
    local rippleCount = if detail >= 3 then 3 else 2
    local rippleSeconds = 4

    for index = 1, rippleCount do
        -- Start each ripple at a different time so they spread one after another
        addRipple(aura, canvas, element.Core, 5, opacity, rippleSeconds, (index - 1) * rippleSeconds / rippleCount)
    end

    if detail >= 2 then
        local crescents = turningLayer(aura, canvas, 10)
        for _, rotation in { 0, 180 } do
            local stroke = outline(aura, circle(crescents, 0.6), element.Main, 9, opacity)
            local shape = Instance.new("UIGradient")
            shape.Rotation = rotation
            shape.Transparency = numberSequence({ { 0, 0 }, { 0.45, 0.1 }, { 0.55, 1 }, { 1, 1 } })
            shape.Parent = stroke
        end
    end

    if detail >= 4 then
        sweep(aura, outline(aura, circle(canvas, 0.3), element.Core, 5, opacity), 5)
    end

    if detail >= 5 then
        marks(aura, turningLayer(aura, canvas, -80), 24, 0.44, UDim2.fromOffset(10, 10), element.Core, opacity, true)
    end
end

-- Jade: a slow, steady octagram lattice with compass marks
local function latticeSigil(aura, canvas, element, detail, opacity)
    local lattice = turningLayer(aura, canvas, 120)
    outline(aura, square(lattice, 0.62, 0), element.Main, 6, opacity)
    outline(aura, square(lattice, 0.62, 45), element.Main, 6, opacity)

    if detail >= 2 then
        local inner = turningLayer(aura, canvas, -90)
        outline(aura, square(inner, 0.34, 45), element.Core, 4, opacity)
        marks(aura, canvas, 8, 0.44, UDim2.new(0, 10, 0.06, 0), element.Core, opacity)

    end

    if detail >= 4 then
        marks(aura, lattice, 8, 0.438, UDim2.fromOffset(14, 14), element.Core, opacity, false, 45)
    end

    if detail >= 5 then
        sweep(aura, outline(aura, circle(canvas, 0.22), element.Core, 5, opacity), 6)
    end
end

local SIGIL_MOTIFS = {
    Rune = runeSigil,
    Flame = flameSigil,
    Ripple = rippleSigil,
    Lattice = latticeSigil,
}

local sigilRaycastParams = RaycastParams.new()
sigilRaycastParams.FilterType = Enum.RaycastFilterType.Exclude
sigilRaycastParams.IgnoreWater = true

local function findGround(aura)
    sigilRaycastParams.FilterDescendantsInstances = { aura.character, aura.model }
    return workspace:Raycast(aura.rootPart.Position, Vector3.new(0, -SIGIL_MAX_DROP, 0), sigilRaycastParams)
end

local function placeSigil(aura, hitPosition)
    aura.sigil.Center = hitPosition
    aura.sigil.Part.CFrame = CFrame.new(hitPosition + Vector3.new(0, 0.12, 0))
end

-- A large flat pattern of light on the ground under the character. It stays
-- on the ground while the body hovers, and moves only if the character does.
local function createSigil(aura, look)
    local element, tier = look.Element, look.Tier
    local hit = findGround(aura)
    if not hit then
        return -- Nothing below (for example over the void)
    end

    local diameter = math.min(tier.SigilSize * aura.body.Height, 24)
    local part = Instance.new("Part")
    part.Name = "Sigil"
    part.Size = Vector3.new(diameter, 0.05, diameter)
    setUpInvisiblePart(part)
    part.Parent = aura.model

    aura.sigil = { Part = part, Center = hit.Position, NextCheck = 0 }
    placeSigil(aura, hit.Position)

    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Top
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = SIGIL_PIXELS_PER_STUD
    gui.LightInfluence = 0 -- Even glow in shade and sunlight
    gui.MaxDistance = 200
    trySet(gui, "Brightness", 1.3)
    gui.Parent = part

    -- Centred, so the bloom below scales from the middle of the sigil
    local canvas = guiFrame(gui, UDim2.fromScale(1, 1))
    local bloom = Instance.new("UIScale")
    bloom.Parent = canvas
    addFade(aura, bloom, "Scale", 1, 0.6)

    local opacity = 0.55 + 0.4 * tier.Intensity

    -- A pool of coloured light, denser towards the middle
    for _, poolDiameter in { 0.95, 0.65, 0.35 } do
        fill(aura, circle(canvas, poolDiameter), element.Deep, 0.14)
    end

    -- Bold outer ring with a thin inner rim
    outline(aura, circle(canvas, 0.97), element.Main, 12, opacity)
    outline(aura, circle(canvas, 0.9), element.Core, 4, opacity * 0.9)

    SIGIL_MOTIFS[element.Sigil](aura, canvas, element, tier.SigilDetail, opacity)

    -- From Qi Gathering up, a shockwave spreads across the ground every few
    -- seconds (water already has its own ripples)
    if tier.SigilDetail >= 3 and element.Sigil ~= "Ripple" then
        addRipple(aura, canvas, element.Core, 8, opacity, 2.6, 0.5)
    end
end

-- Public API ---------------------------------------------------------------

-- Builds a (still invisible) aura for this character. petId selects the
-- element (nil or unknown = Neutral) and rankId selects the tier.
function AuraBuilder.build(player, character, rootPart, petId, rankId)
    local element = AuraStyles.Elements[petId or "Neutral"] or AuraStyles.Elements.Neutral
    local tier = AuraStyles.getTier(rankId)
    local look = { Element = element, Tier = tier }

    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"

    local aura = {
        player = player,
        character = character,
        rootPart = rootPart,
        model = model,
        body = measureBody(character, rootPart),
        fades = {}, -- Properties that tween as the aura appears and disappears
        loops = {}, -- Endless tweens, cancelled on removal
        onHide = {}, -- Extra steps to run when fading out
        movers = {}, -- Parts placed relative to the character every frame
        flames = {}, -- Flame tips that sway every frame
        comets = {}, -- Points travelling along streams every frame
        waves = {}, -- Ribbon points that ripple every frame
        pulses = {}, -- Jade rings that rise every frame
        trails = {},
        limbAttachments = {}, -- Attachments inside the character's hands
        sheddingOrbs = 0,
        trailsOn = false,
        hiding = false,
        destroyed = false,
    }

    -- Drives the fade of everything that's updated every frame (light, pulses)
    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Parent = model
    aura.fader = fader
    addFade(aura, fader, "Value", 1, 0)

    createSigil(aura, look)
    STREAM_BUILDERS[element.Streams](aura, look) -- First: it sets aura.bodyPart and aura.streamMover
    createShell(aura, look)
    createRiseLines(aura, look)
    createParticlesAndLight(aura, look)
    createHandAccents(aura, look)
    createRings(aura, look)

    if tier.Crown then
        CROWN_BUILDERS[element.Crown](aura, look)
    end
    if tier.Outline then
        createOutline(aura, look)
    end

    -- Properties changed every frame, for the performance budget
    local pulseBeams = 0
    for _, pulse in aura.pulses do
        pulseBeams += #pulse.Beams
    end
    aura.frameUpdates = #aura.movers + #aura.flames + #aura.waves + #aura.comets * 2 + pulseBeams * 2 + 1

    return aura
end

local function playFades(aura, toVisible)
    local tweenInfo = if toVisible then FADE_IN else FADE_OUT
    for _, fade in aura.fades do
        local goal = { [fade.Property] = if toVisible then fade.Visible else fade.Hidden }
        TweenService:Create(fade.Instance, tweenInfo, goal):Play()
    end
end

function AuraBuilder.show(aura)
    playFades(aura, true)

    task.delay(TRAIL_START_DELAY, function()
        if aura.destroyed or aura.hiding then
            return
        end
        aura.trailsOn = true
        for _, trail in aura.trails do
            trail.Enabled = true
        end
    end)
end

-- Fades the aura out. The controller removes it after REMOVE_DELAY.
function AuraBuilder.hide(aura)
    aura.hiding = true
    aura.trailsOn = false
    playFades(aura, false)
    for _, trail in aura.trails do
        trail.Enabled = false
    end
    for _, step in aura.onHide do
        step()
    end
end

-- Briefly brightens the aura's light (used by breakthroughs). Changes no
-- other part of the aura, so nothing is rebuilt.
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
    for _, point in aura.limbAttachments do
        point:Destroy()
    end
    aura.model:Destroy()
end

-- Called every frame. Adds this aura's movers to parts/cframes (moved in one
-- BulkMoveTo call by the controller) and updates everything else that moves.
-- It only changes properties of existing instances; it never creates any.
function AuraBuilder.update(aura, now, parts, cframes)
    local rootCFrame = aura.rootPart.CFrame
    local fade = aura.fader.Value

    -- Jade pulses rise from the feet to above the head, swelling and fading
    for _, pulse in aura.pulses do
        local progress = ((now + pulse.Phase) / PULSE_SECONDS) % 1
        pulse.Mover.Offset = CFrame.new(0, pulse.BottomY + (pulse.TopY - pulse.BottomY) * progress, 0)
        local width = pulse.Width * math.sin(progress * math.pi) * fade
        for _, beam in pulse.Beams do
            beam.Width0 = width
            beam.Width1 = width
        end
    end

    for _, mover in aura.movers do
        local placement = rootCFrame * mover.Offset
        if mover.Sway ~= 0 then
            placement *= CFrame.Angles(mover.Sway * math.sin(now * 0.7 + mover.Phase), 0, 0)
        end
        table.insert(parts, mover.Part)
        table.insert(cframes, placement * CFrame.Angles(0, now * mover.Spin + mover.Phase, 0))
    end

    for _, flame in aura.flames do
        local time = now * flame.Speed
        flame.Tip.Position = flame.TipBase + Vector3.new(
            math.sin(time * 6.3 + flame.Phase) * flame.Amount,
            math.sin(time * 9.1 + flame.Phase) * flame.Stretch,
            math.cos(time * 5.1 + flame.Phase) * flame.Amount
        )
    end

    for _, wave in aura.waves do
        local swell = math.sin(now * 1.2 + wave.Phase) * wave.Amount
        local bob = math.sin(now * 0.9 + wave.Phase) * 0.2
        wave.Attachment.Position = wave.Base + wave.Outward * swell + Vector3.new(0, bob, 0)
    end

    for _, comet in aura.comets do
        local progress = ((now + comet.Phase) / comet.Seconds) % 1
        local position = comet.Path(progress)
        comet.Above.Position = position + comet.Offset
        comet.Below.Position = position - comet.Offset

        if progress < comet.LastProgress then
            -- Back at the start: pause the trail for a frame so it doesn't
            -- draw a line straight back down
            comet.Trail.Enabled = false
            comet.Paused = true
        elseif comet.Paused then
            comet.Paused = false
            comet.Trail.Enabled = aura.trailsOn
        end
        comet.LastProgress = progress
    end

    local brightness = aura.lightBrightness * fade
    if aura.lightStyle == "Flicker" then
        brightness *= 0.8 + 0.4 * math.noise(now * 5, aura.lightBrightness)
    elseif aura.lightStyle == "Pulse" then
        brightness *= 0.8 + 0.2 * math.sin(now * (2 * math.pi / PULSE_SECONDS))
    else
        brightness *= 0.9 + 0.1 * math.sin(now * 1.6)
    end
    -- A brief extra glow after a breakthrough (see AuraBuilder.pulse)
    if aura.pulseEnd then
        local remaining = (aura.pulseEnd - now) / aura.pulseSeconds
        if remaining > 0 then
            brightness *= 1 + 2.5 * remaining
        else
            aura.pulseEnd = nil
        end
    end
    aura.light.Brightness = brightness

    if aura.sparks and not aura.hiding and now >= aura.nextBurst then
        aura.sparks:Emit(aura.burstCount)
        aura.nextBurst = now + 2 + math.random() * 1.5
    end

    -- If the character has moved away (for example after a teleport), move
    -- the sigil to the ground under its new position. Checked a few times a second.
    local sigil = aura.sigil
    if sigil and now >= sigil.NextCheck then
        sigil.NextCheck = now + 0.25
        local position = aura.rootPart.Position
        local offset = Vector2.new(position.X - sigil.Center.X, position.Z - sigil.Center.Z)
        if offset.Magnitude > 2 or math.abs(position.Y - sigil.Center.Y) > SIGIL_MAX_DROP then
            local hit = findGround(aura)
            if hit then
                placeSigil(aura, hit.Position)
            end
        end
    end
end

return AuraBuilder

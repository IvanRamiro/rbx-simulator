-- Build-time only: builds each egg stand's aura in the Workspace, out of particle emitters,
-- trails, beams, billboards, glowing image planes and lights (textures from VFX Studio's library,
-- the PDS kit and our own), so it
-- can be seen and tuned in Studio (VFX Studio works on the instances directly) and is saved in the
-- place. Require a clone, as with WorldBuilder:
--
--   local VFX = require(game.ServerStorage.WorldBuild.EggAuraVFX:Clone())
--   VFX.build("StartingIsland")   -- (re)builds FloatingIslands.StartingIsland.EggAuras
--
-- Each aura is a Model tagged "EggAura" (attribute EggId) whose Root part sits at the egg's resting
-- point, facing the front of the stand. The client (src/client/EggAura.lua) animates it from
-- attributes, so an aura tuned by hand keeps working:
--   Attachment  Orbit (deg/s), Radius, Height, Tilt (Vector3 degrees), Phase (deg),
--               Bob (studs), BobPeriod (s): moves round the egg (trails on it draw arcs)
--   Part        Spin (deg/s): turns about its own up axis (formations and rings);
--               Wobble (deg), WobblePeriod (s), Phase (deg): its tilt precesses like a top;
--               SwellScale, GatherScale: how far its image swells (as the aura breathes, and
--               further on the hatch burst) and draws in while a hatch gathers;
--               Ripple (s), HatchEmit: a ring that runs outward that many times on the hatch
--   ImageLabel  Sway (deg), SwayPeriod (s), Phase (deg): rocks to and fro (the crystals)
--   Emitter     HatchEmit (particles on the hatch burst),
--               GatherRate (its rate while a hatch gathers)
--   Model       Gather (s), Tint (the egg's glow while it hatches),
--               Breath (fraction), BreathPeriod (s): the slow swell of speed, glow and rings
-- Measures are studs, for eggs placed 1.3 studs per egg unit (about 3.5 studs tall, centred
-- 1.75 above the Root).
local CollectionService = game:GetService("CollectionService")
local Workspace = game:GetService("Workspace")

local EggAuraVFX = {}

local TAG = "EggAura"
local EGG_CENTRE = 1.75

-- textures: VFX Studio library (VS), PDS' Particles & Models Kit (PDS), ours (QA)
local T = {
    LotusMandala = "rbxassetid://12403102126",   -- VS: eight-petal lotus mandala
    OrnateMandala = "rbxassetid://12402928708",  -- VS: ornate mandala
    BrokenRing = "rbxassetid://14850595833",     -- VS: broken wind ring
    SoftRing = "rbxassetid://16505105356",       -- VS: soft smoke ring
    WindArc = "rbxassetid://13131393513",        -- VS: crescent wind arc
    SoftGlow = "rbxassetid://187823474",         -- VS: soft round glow
    SmallGlow = "rbxassetid://6673021984",       -- VS: small glow
    Dot = "rbxassetid://11037546803",            -- VS: glowing dot
    Star4 = "rbxassetid://5946093983",           -- VS: four-point star
    Cross = "rbxassetid://6909741538",           -- VS: cross sparkle
    Burst = "rbxassetid://15773612675",          -- VS: radial burst
    Flare = "rbxassetid://14054628491",          -- PDS: starburst
    Fog = "rbxassetid://14050223758",            -- PDS: fog
    GlitterFog = "rbxassetid://14049414463",     -- PDS: glittering fog
    Ribbon = "rbxassetid://99893839045856",      -- QA: Qi silk ribbon
    WindRose = "rbxassetid://98026121929653",    -- QA: wind-rose sigil
    Wuxing = "rbxassetid://84064944874395",      -- QA: five-element sigil
    Cloud = "rbxassetid://133757754897450",      -- QA: auspicious cloud
    Feather = "rbxassetid://131662968027624",    -- QA: feather
    Crystal = "rbxassetid://91364093647932",     -- QA: faceted crystal shard (rendered in Blender)
    QiRing = "rbxassetid://136096136498575",     -- QA: bold Qi ring with comet streaks
    ElementBand = "rbxassetid://76030932893410", -- QA: gyroscope band with five element nodes
    Stream = "rbxassetid://129943358163696",     -- QA: braided element stream (tiles along a beam)
}

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

local function seq(points)
    local keypoints = {}
    for _, p in points do
        table.insert(keypoints, NumberSequenceKeypoint.new(p[1], p[2], p[3] or 0))
    end
    return NumberSequence.new(keypoints)
end

local function colors(points)
    local keypoints = {}
    for _, p in points do
        table.insert(keypoints, ColorSequenceKeypoint.new(p[1], p[2]))
    end
    return ColorSequence.new(keypoints)
end

local function set(instance, properties, attributes)
    for property, value in properties or {} do
        instance[property] = value
    end
    for name, value in attributes or {} do
        instance:SetAttribute(name, value)
    end
    return instance
end

-- ---------- building blocks ----------
local function part(aura, name, offset, size)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.CanCollide = false
    p.CanQuery = false
    p.CanTouch = false
    p.CastShadow = false
    p.Transparency = 1
    p.Size = size
    p.CFrame = aura.root.CFrame * offset
    p.Parent = aura.model
    return p
end

local function attachment(aura, name, offset)
    local a = Instance.new("Attachment")
    a.Name = name
    a.CFrame = offset
    a.Parent = aura.root
    return a
end

local function emitter(name, properties, attributes)
    local e = Instance.new("ParticleEmitter")
    e.Name = name
    e.LightInfluence = 0
    e.LightEmission = 1
    return set(e, properties, attributes)
end

local function finish(e, parent)
    e.Parent = parent
    return e
end

-- Rotation for a plane or ring: turned `yaw` degrees about the egg, then tilted `x` degrees about
-- X and `z` about Z. A negative `x` dips the ring's front toward the viewer: players see the eggs
-- from the front and above, so a ring tilted that way opens up instead of going edge-on.
local function tilt(x, z, yaw)
    return CFrame.Angles(0, math.rad(yaw or 0), 0) * CFrame.Angles(math.rad(x), 0, math.rad(z or 0))
end

-- Flat elements (formations, rings, ripples) are glowing images on SurfaceGuis: flat
-- (VelocityPerpendicular) particles do not render in these auras (tested in Play). The image
-- fills 1/HEADROOM of its part, leaving room to swell as the aura breathes and on the hatch.
local HEADROOM = 1.5

local function plane(aura, name, cframe, diameter, texture, color, brightness, attrs, bothFaces, transparency)
    local p = part(aura, name, cframe, Vector3.new(diameter * HEADROOM, 0.05, diameter * HEADROOM))
    set(p, nil, attrs)
    for _, face in bothFaces and { Enum.NormalId.Top, Enum.NormalId.Bottom } or { Enum.NormalId.Top } do
        local gui = Instance.new("SurfaceGui")
        gui.Face = face
        gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
        gui.PixelsPerStud = 40
        gui.LightInfluence = 0
        gui.Brightness = brightness
        gui.MaxDistance = 200
        gui.Parent = p
        local label = Instance.new("ImageLabel")
        label.AnchorPoint = Vector2.new(0.5, 0.5)
        label.Position = UDim2.fromScale(0.5, 0.5)
        label.Size = UDim2.fromScale(1 / HEADROOM, 1 / HEADROOM)
        label.BackgroundTransparency = 1
        label.Image = texture
        label.ImageColor3 = color
        label.ImageTransparency = transparency or 0
        label.Parent = gui
    end
    return p
end

-- A flat glowing formation lying just above the pedestal's rim, turning at `spin` deg/s.
local function formation(aura, name, texture, radius, color, spin, brightness, lift)
    return plane(aura, name, CFrame.new(0, aura.rim + (lift or 0.06), 0), radius * 2, texture, color, brightness,
        { Spin = spin, SwellScale = 1.06, GatherScale = 0.9 })
end

-- A ring of light at `height` on a plane turned by `rotation` (see tilt), turning in that plane at
-- `spin` deg/s; seen from both sides. It swells as the aura breathes and draws in while a hatch
-- gathers.
local function ring(aura, name, height, rotation, texture, diameter, color, spin, brightness, transparency, wobble)
    local attrs = { Spin = spin, SwellScale = 1.14, GatherScale = 0.68 }
    if wobble then -- { degrees, period, phase }: the ring's tilt precesses
        attrs.Wobble, attrs.WobblePeriod, attrs.Phase = wobble[1], wobble[2], wobble[3]
    end
    return plane(aura, name, CFrame.new(0, height, 0) * rotation, diameter, texture, color, brightness or 2.6, attrs, true, transparency)
end

-- A pair of movers on the same orbit, `halfWidth` above and below it, with a trail between them:
-- as they orbit, the trail draws an arc of energy round the egg.
local function arc(aura, name, orbit, halfWidth, properties)
    local function mover(suffix, dy)
        local attrs = table.clone(orbit)
        attrs.Height = (orbit.Height or EGG_CENTRE) + dy
        local a = attachment(aura, name .. suffix, CFrame.new(0, attrs.Height, orbit.Radius))
        set(a, nil, attrs)
        return a
    end
    local a0, a1 = mover("Top", halfWidth), mover("Bottom", -halfWidth)
    local trail = Instance.new("Trail")
    trail.Name = name
    trail.Attachment0, trail.Attachment1 = a0, a1
    trail.FaceCamera = true
    trail.LightInfluence = 0
    trail.LightEmission = 1
    set(trail, properties)
    trail.Parent = aura.root
    return trail, a0
end

local function light(aura, color, range, brightness)
    local l = Instance.new("PointLight")
    l.Color = color
    l.Range = range
    l.Brightness = brightness
    l.Shadows = false
    l.Parent = attachment(aura, "Light", CFrame.new(0, EGG_CENTRE, 0))
    return l
end

-- A soft glow behind and round the egg: a few large faint sprites turning slowly, drawn behind
-- the egg (ZOffset) so they never veil its design.
local function halo(aura, color, size, transparency)
    local a = attachment(aura, "Halo", CFrame.new(0, EGG_CENTRE, 0))
    return finish(emitter("Halo", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(2.5, 3.5), Rate = 1.4,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-10, 10), ZOffset = -2.5,
        Size = seq({ { 0, size * 0.8 }, { 0.5, size * 1.05 }, { 1, size * 0.92 } }), Color = ColorSequence.new(color),
        Transparency = seq({ { 0, 1 }, { 0.4, transparency }, { 1, 1 } }),
    }), a)
end

-- The hatch's gathering: particles drawn in from a sphere round the egg (idle rate 0).
local function drawIn(aura, texture, color, size, rate)
    local p = part(aura, "DrawIn", CFrame.new(0, EGG_CENTRE, 0), Vector3.new(9, 9, 9))
    return finish(emitter("DrawIn", {
        Texture = texture, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Speed = NumberRange.new(7, 9), Lifetime = NumberRange.new(0.45, 0.55),
        Rate = 0, Size = seq({ { 0, size }, { 1, size * 0.2 } }), Color = ColorSequence.new(color),
        Transparency = seq({ { 0, 1 }, { 0.2, 0.05 }, { 1, 0.5 } }),
    }, { GatherRate = rate }), p)
end

-- The hatch's burst: a starburst flash and a ripple across the rim.
local function burst(aura, color, size)
    local a = attachment(aura, "Burst", CFrame.new(0, EGG_CENTRE, 0))
    finish(emitter("Flash", {
        Texture = T.Flare, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.4), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, size * 0.3 }, { 0.25, size }, { 1, size * 1.15 } }), Color = ColorSequence.new(color),
        Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 3,
    }, { HatchEmit = 1 }), a)
end

-- A ring that runs out across the rim `hatch` times on the hatch, out to `reach` studs across. Its
-- image is a hidden template the client copies for each ripple.
local function ripple(aura, color, reach, hatch)
    local p = plane(aura, "Ripple", CFrame.new(0, aura.rim + 0.12, 0), reach / HEADROOM, T.SoftRing, color, 3,
        { Ripple = 1.1, HatchEmit = hatch }, false, 0.05)
    for _, label in p:GetDescendants() do
        if label:IsA("ImageLabel") then
            label.Visible = false
        end
    end
    return p
end

-- A crystal shard floating round the egg on `orbit` (mover attributes): a billboard of the
-- AuraCrystal sprite (a faceted crystal modelled and rendered in Blender) on a soft glow, rocking
-- gently as it goes round.
local function crystal(aura, name, orbit, size, color, brightness)
    local a = attachment(aura, name, CFrame.new(0, orbit.Height, orbit.Radius))
    set(a, nil, orbit)
    local gui = Instance.new("BillboardGui")
    gui.Size = UDim2.fromScale(size * 1.5, size * 1.5) -- studs
    gui.LightInfluence = 0
    gui.Brightness = brightness
    gui.MaxDistance = 200
    gui.Parent = a
    local glow = Instance.new("ImageLabel")
    glow.Name = "Glow"
    glow.Size = UDim2.fromScale(1, 1)
    glow.BackgroundTransparency = 1
    glow.Image = T.SoftGlow
    glow.ImageColor3 = color
    glow.ImageTransparency = 0.55
    glow.Parent = gui
    local shard = Instance.new("ImageLabel")
    shard.Name = "Shard"
    shard.AnchorPoint = Vector2.new(0.5, 0.5)
    shard.Position = UDim2.fromScale(0.5, 0.5)
    shard.Size = UDim2.fromScale(0.72, 0.72)
    shard.BackgroundTransparency = 1
    shard.Image = T.Crystal
    shard.ImageColor3 = color
    shard.ZIndex = 2
    set(shard, nil, { Sway = 18, SwayPeriod = orbit.BobPeriod or 3, Phase = orbit.Phase or 0 })
    shard.Parent = gui
    return a
end

-- An energy stream: a beam from a point sweeping round the rim on `orbit`, rising and arcing in
-- to meet the others at `apex` above the egg, its texture flowing upward. Both ends point their
-- axis up, so the beam leaves the rim straight up and reaches the apex from below.
local UP_AXIS = CFrame.Angles(0, 0, math.rad(90))
local function stream(aura, name, orbit, apex, properties)
    local a = attachment(aura, name .. "Base", CFrame.new(0, orbit.Height, orbit.Radius) * UP_AXIS)
    set(a, nil, orbit)
    local beam = Instance.new("Beam")
    beam.Name = name
    beam.Attachment0, beam.Attachment1 = a, apex
    beam.FaceCamera = true
    beam.LightInfluence = 0
    beam.LightEmission = 1
    beam.Segments = 16
    set(beam, properties)
    beam.Parent = aura.root
    return beam
end

-- A camera-facing updraft of mist rising through the egg, its texture flowing upward at `speed`.
local function column(aura, color0, color1, speed, width)
    local base = attachment(aura, "ColumnBase", CFrame.new(0, 0.9, 0))
    local top = attachment(aura, "ColumnTop", CFrame.new(0, 6.5, 0))
    local b = Instance.new("Beam")
    b.Name = "Column"
    b.Attachment0, b.Attachment1 = base, top
    set(b, {
        Texture = T.Fog, TextureMode = Enum.TextureMode.Wrap, TextureLength = 3.5, TextureSpeed = speed,
        Width0 = width, Width1 = width * 0.4, FaceCamera = true, LightEmission = 0.5, LightInfluence = 0,
        Brightness = 2, Segments = 10, ZOffset = -1, Color = ColorSequence.new(color0, color1),
        Transparency = seq({ { 0, 1 }, { 0.12, 0.45 }, { 0.6, 0.6 }, { 1, 1 } }),
    })
    b.Parent = aura.root
    return b
end

-- Soft puffs of mist curling up off the rim (emitted from `area`, a flat part over the rim).
local function mist(area, color0, color1, rate, rise)
    return finish(emitter("Mist", {
        Texture = T.GlitterFog, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        EmissionDirection = Enum.NormalId.Top, Rate = rate, Lifetime = NumberRange.new(2.5, 3.5),
        Speed = NumberRange.new(rise * 0.6, rise), SpreadAngle = Vector2.new(15, 15), Drag = 0.3,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-25, 25), Size = seq({ { 0, 0.8 }, { 0.5, 2 }, { 1, 2.6 } }),
        Color = ColorSequence.new(color0, color1), Transparency = seq({ { 0, 1 }, { 0.25, 0.45 }, { 1, 1 } }),
        LightEmission = 0.5, ZOffset = -0.5,
    }, { HatchEmit = 6 }), area)
end

-- ---------- the eggs ----------
local RECIPES = {}

-- Beginner Qi Egg: calm, welcoming Qi. A lotus formation turning slowly beneath, two rings of Qi
-- on gently tilted planes, two silk arcs of Qi gliding round the egg, three Qi crystals drifting
-- round it (after the egg's crystal plates), motes rising like breath, star glints, a soft halo.
RECIPES.BeginnerQiEgg = function(aura)
    local QI, PALE, DEEP = rgb(80, 195, 255), rgb(200, 240, 255), rgb(40, 120, 255)
    aura.model:SetAttribute("Gather", 1.3)
    aura.model:SetAttribute("Tint", rgb(120, 210, 255))
    set(aura.model, nil, { Breath = 0.15, BreathPeriod = 5 }) -- a calm breath
    formation(aura, "Formation", T.LotusMandala, 3.6, rgb(110, 205, 255), 8, 3)
    ring(aura, "RingQi", EGG_CENTRE + 0.35, tilt(-26, 8), T.QiRing, 5.8, QI, 25, 2.2, nil, { 9, 7 })
    ring(aura, "RingBreath", EGG_CENTRE + 0.1, tilt(-14, -32), T.BrokenRing, 6.6, PALE, -40, 2.4, 0.2, { 12, 9, 120 })
    -- two silk arcs counter-rotating on different radii, weaving up and down, each shedding Qi dust
    for k, arcOrbit in { { Orbit = 115, Radius = 2.4, Bob = 0.45, BobPeriod = 2.6 }, { Orbit = -80, Radius = 3.0, Bob = 0.6, BobPeriod = 3.4 } } do
        arcOrbit.Height, arcOrbit.Phase = EGG_CENTRE, (k - 1) * 180
        arcOrbit.Tilt = Vector3.new(k == 1 and 20 or -26, 0, k == 1 and 0 or 12)
        local _, head = arc(aura, "QiArc" .. k, arcOrbit, 0.45, {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.1, Brightness = 3,
            Color = colors({ { 0, PALE }, { 0.5, QI }, { 1, DEEP } }), Transparency = seq({ { 0, 0.05 }, { 0.5, 0.35 }, { 1, 1 } }),
            WidthScale = seq({ { 0, 0.5 }, { 0.12, 1 }, { 0.6, 0.55 }, { 1, 0 } }),
        })
        finish(emitter("ArcDust", {
            Texture = T.Dot, Rate = 14, Lifetime = NumberRange.new(0.8, 1.4), Speed = NumberRange.new(0.2, 0.6),
            SpreadAngle = Vector2.new(180, 180), Drag = 1.5, Acceleration = Vector3.new(0, 0.8, 0),
            Size = seq({ { 0, 0.28 }, { 1, 0 } }), Color = ColorSequence.new(PALE, QI), Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 2,
        }, { HatchEmit = 12 }), head)
    end
    -- three crystals, each on its own orbit, height and drift; one goes the other way
    for k, c in { { 18, 2.9, 2.7, 0.5, 3.0, 1.5 }, { 27, 3.5, 1.6, 0.4, 3.8, 1.15 }, { -14, 3.2, 2.2, 0.55, 4.6, 1.3 } } do
        crystal(aura, "Crystal" .. k, { Orbit = c[1], Radius = c[2], Height = c[3], Phase = (k - 1) * 120 + 40, Bob = c[4], BobPeriod = c[5] },
            c[6], rgb(110, 200, 255), 1.6)
    end
    local motes = part(aura, "MoteArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(5, 0.2, 5))
    finish(emitter("Motes", {
        Texture = T.Dot, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.8, 1.8), SpreadAngle = Vector2.new(25, 25),
        Acceleration = Vector3.new(0, 0.6, 0), Drag = 0.6, Lifetime = NumberRange.new(2.2, 3.4), Rate = 10,
        Size = seq({ { 0, 0 }, { 0.15, 0.4 }, { 0.6, 0.25 }, { 1, 0 } }), Brightness = 2,
        Color = colors({ { 0, PALE }, { 1, QI } }), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }),
    }, { HatchEmit = 30 }), motes)
    local glints = part(aura, "GlintArea", CFrame.new(0, EGG_CENTRE + 0.3, 0), Vector3.new(6, 4.5, 6))
    finish(emitter("Glints", {
        Texture = T.Star4, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.3, 0.8), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.4, 0),
        Lifetime = NumberRange.new(0.8, 1.2), Rate = 4, Rotation = NumberRange.new(0, 45),
        Size = seq({ { 0, 0 }, { 0.5, 0.6 }, { 1, 0 } }), Color = ColorSequence.new(PALE), Transparency = NumberSequence.new(0.1), Brightness = 2,
    }, { HatchEmit = 16 }), glints)
    halo(aura, QI, 6.5, 0.7)
    column(aura, QI, PALE, 0.35, 4.2)
    mist(motes, QI, PALE, 4, 1)
    ripple(aura, rgb(130, 215, 255), 9, 2)
    drawIn(aura, T.Dot, PALE, 0.5, 60)
    burst(aura, rgb(170, 230, 255), 9)
    light(aura, QI, 13, 1.3)
end

-- Spirit Breeze Egg: wind. A wind rose turning beneath, light-blue and white wind rings whirling
-- round the egg on three planes (two crescent gusts and a broken ring of breeze), three white
-- wind trails spiralling up and down round it, auspicious clouds drifting off the rim, feathers
-- riding the updraught.
RECIPES.SpiritBreezeEgg = function(aura)
    local SKY, WHITE = rgb(110, 215, 255), rgb(225, 245, 255)
    aura.model:SetAttribute("Gather", 1.2)
    aura.model:SetAttribute("Tint", rgb(170, 230, 255))
    set(aura.model, nil, { Breath = 0.25, BreathPeriod = 3.5 }) -- gusty
    formation(aura, "Formation", T.WindRose, 3.6, rgb(130, 220, 255), -25, 2.8)
    ring(aura, "GustLow", EGG_CENTRE - 0.1, tilt(-12, 8), T.WindArc, 6.8, SKY, 150, 2.6, nil, { 10, 4 })
    ring(aura, "GustHigh", EGG_CENTRE + 0.6, tilt(-20, -16), T.WindArc, 5.6, WHITE, -190, 2.4, nil, { 14, 5, 90 })
    ring(aura, "BreezeRing", EGG_CENTRE - 0.7, tilt(-6, 6), T.BrokenRing, 7.4, rgb(165, 228, 255), 60, 2.2, 0.15, { 6, 6, 200 })
    -- three wind trails on a helix of widening radii; feathers shed from the first one's head
    for k = 1, 3 do
        local _, head = arc(aura, "Wind" .. k, { Orbit = 235 - k * 25, Radius = 1.5 + 0.6 * k, Height = EGG_CENTRE, Phase = (k - 1) * 120,
            Bob = 1.1 + 0.25 * k, BobPeriod = 2 + 0.4 * k }, 0.12, {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.8, Brightness = 2.5,
            Color = colors({ { 0, WHITE }, { 1, SKY } }), Transparency = seq({ { 0, 0.05 }, { 0.6, 0.4 }, { 1, 1 } }),
            WidthScale = seq({ { 0, 0.4 }, { 0.1, 1 }, { 1, 0 } }),
        })
        if k == 1 then
            finish(emitter("Shed", {
                Texture = T.Feather, Rate = 2, Lifetime = NumberRange.new(1.5, 2.2), Speed = NumberRange.new(0.3, 0.8),
                SpreadAngle = Vector2.new(180, 180), Drag = 1.2, Acceleration = Vector3.new(0, -0.3, 0),
                Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120), Size = seq({ { 0, 0.4 }, { 1, 0.5 } }),
                Color = ColorSequence.new(WHITE), Transparency = seq({ { 0, 0.1 }, { 0.7, 0.3 }, { 1, 1 } }), LightEmission = 0.6,
            }), head)
        end
    end
    local base = part(aura, "CloudArea", CFrame.new(0, aura.rim + 0.3, 0), Vector3.new(5.5, 0.2, 5.5))
    finish(emitter("Clouds", {
        Texture = T.Cloud, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.4, 0.8),
        Lifetime = NumberRange.new(3, 4), Rate = 1.5, Drag = 0.4, SpreadAngle = Vector2.new(20, 20),
        Rotation = NumberRange.new(-8, 8), RotSpeed = NumberRange.new(-6, 6),
        Size = seq({ { 0, 1 }, { 0.4, 2.2 }, { 1, 2.6 } }), LightEmission = 0.4,
        Color = colors({ { 0, WHITE }, { 1, rgb(140, 210, 255) } }), Transparency = seq({ { 0, 1 }, { 0.2, 0.3 }, { 1, 1 } }),
    }, { HatchEmit = 12 }), base)
    finish(emitter("Feathers", {
        Texture = T.Feather, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(1, 1.8), SpreadAngle = Vector2.new(35, 35),
        Acceleration = Vector3.new(0.4, 0.3, 0), Drag = 0.5,
        Lifetime = NumberRange.new(3, 4), Rate = 2.5, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-140, 140),
        Size = seq({ { 0, 0.45 }, { 1, 0.6 } }), LightEmission = 0.6, Color = colors({ { 0, WHITE }, { 1, SKY } }),
        Transparency = seq({ { 0, 1 }, { 0.15, 0.1 }, { 1, 1 } }),
    }, { HatchEmit = 20 }), base)
    halo(aura, rgb(150, 225, 255), 6, 0.8)
    column(aura, rgb(150, 220, 255), rgb(235, 248, 255), 0.9, 4) -- a fast updraft: wind, not Qi
    drawIn(aura, T.Feather, WHITE, 0.7, 30)
    burst(aura, rgb(200, 240, 255), 8)
    ripple(aura, WHITE, 9, 1)
    light(aura, SKY, 12, 0.55) -- the pale egg washes out under a stronger light
end

-- Elemental Core Egg: concentrated elements. Two formations turning against each other beneath
-- (the five-element cycle and a gold mandala), four element streams rising off the formation and
-- converging in a turning cage of light above the crown, where their power gathers in a bright
-- point, a gyroscope of three gold element bands on steep axes, four element orbs (cyan,
-- gold, blue, amber) racing round on their own orbits, blue and gold motes rising, sparks
-- crackling off the core; on the hatch the core gem flares.
local ELEMENTS = { rgb(40, 225, 255), rgb(255, 195, 60), rgb(70, 120, 255), rgb(255, 150, 40) }
RECIPES.ElementalCoreEgg = function(aura)
    local CORE, GOLD = rgb(50, 215, 255), rgb(255, 205, 90)
    aura.model:SetAttribute("Gather", 1.4)
    aura.model:SetAttribute("Tint", rgb(90, 220, 255))
    set(aura.model, nil, { Breath = 0.12, BreathPeriod = 2.5 }) -- a quick thrum of power
    formation(aura, "Formation", T.Wuxing, 3.8, rgb(80, 195, 255), 10, 3)
    formation(aura, "FormationGold", T.OrnateMandala, 2.9, GOLD, -16, 2.2, 0.1)
    for k, spin in { 70, -55, 45 } do
        ring(aura, "Gyro" .. k, EGG_CENTRE, tilt(68, 0, 60 * (k - 1)), T.ElementBand, 6.2 + 0.4 * k, GOLD, spin, 1.8, nil, { 6, 5 + k, 120 * k })
    end
    local apex = attachment(aura, "Apex", CFrame.new(0, EGG_CENTRE + 2.6, 0) * UP_AXIS)
    for k, color in ELEMENTS do
        stream(aura, "Stream" .. k, { Orbit = 12, Radius = 3.5, Height = aura.rim + 0.5, Phase = 90 * (k - 1) + 45 }, apex, {
            Texture = T.Stream, TextureMode = Enum.TextureMode.Wrap, TextureLength = 2, TextureSpeed = 1.2,
            CurveSize0 = 3, CurveSize1 = 1.5, Width0 = 0.9, Width1 = 0.3, Brightness = 2,
            LightEmission = 0.35, -- mostly opaque colour, so the elements hold their hue in daylight
            Color = colors({ { 0, color }, { 1, color:Lerp(rgb(255, 255, 255), 0.45) } }),
            Transparency = seq({ { 0, 1 }, { 0.12, 0.1 }, { 0.85, 0.1 }, { 1, 0.5 } }),
        })
    end
    finish(emitter("ApexGlow", {
        Texture = T.SmallGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.4, 0.6), Rate = 10,
        Size = seq({ { 0, 1 }, { 0.5, 1.5 }, { 1, 1 } }), Color = ColorSequence.new(rgb(150, 235, 255)),
        Transparency = seq({ { 0, 1 }, { 0.3, 0.2 }, { 1, 1 } }), Brightness = 3,
    }, { HatchEmit = 6 }), apex)
    for k, color in ELEMENTS do
        local orbit = { Orbit = ({ 120, -95, 80, -130 })[k], Radius = ({ 2.6, 3.4, 2.9, 3.6 })[k], Height = EGG_CENTRE + (k % 2 == 0 and 0.9 or -0.5),
            Tilt = Vector3.new(({ 15, -20, 25, -10 })[k], 0, 0), Phase = 90 * (k - 1),
            Bob = ({ 0.3, 0.5, 0.4, 0.35 })[k], BobPeriod = ({ 2.2, 2.9, 3.4, 2.6 })[k] }
        local _, head = arc(aura, "OrbTrail" .. k, orbit, 0.18, {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.5, Brightness = 3,
            Color = ColorSequence.new(color), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), WidthScale = seq({ { 0, 1 }, { 1, 0.1 } }),
        })
        finish(emitter("Orb" .. k, {
            Texture = T.SmallGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.25), Rate = 30,
            Size = seq({ { 0, 1.1 }, { 1, 0.6 } }), Color = ColorSequence.new(color), Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 3,
        }), head)
    end
    local motes = part(aura, "MoteArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(6, 0.2, 6))
    for name, color in { MotesBlue = rgb(90, 200, 255), MotesGold = GOLD } do
        finish(emitter(name, {
            Texture = T.Dot, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(1.2, 2), SpreadAngle = Vector2.new(30, 30),
            Acceleration = Vector3.new(0, 0.6, 0), Drag = 0.5,
            Lifetime = NumberRange.new(1.6, 2.4), Rate = 6, Size = seq({ { 0, 0 }, { 0.2, 0.3 }, { 1, 0 } }), Brightness = 3,
            Color = ColorSequence.new(color), Transparency = seq({ { 0, 0.05 }, { 1, 1 } }),
        }, { HatchEmit = 15 }), motes)
    end
    local sparks = part(aura, "SparkArea", CFrame.new(0, EGG_CENTRE, 0), Vector3.new(3.2, 3.6, 3.2))
    finish(emitter("Sparks", {
        Texture = T.Cross, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        Speed = NumberRange.new(0.8, 2.4), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(0.3, 0.5), Rate = 6,
        Rotation = NumberRange.new(0, 90),
        Size = seq({ { 0, 0 }, { 0.3, 0.7 }, { 1, 0 } }), Color = colors({ { 0, rgb(200, 245, 255) }, { 1, CORE } }),
        Transparency = NumberSequence.new(0), Brightness = 3,
    }, { HatchEmit = 30 }), sparks)
    local front = attachment(aura, "CoreFlare", CFrame.new(0, EGG_CENTRE - 0.05, -1.5))
    finish(emitter("CoreFlare", {
        Texture = T.Burst, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, 1 }, { 0.3, 4.5 }, { 1, 5 } }), Color = ColorSequence.new(CORE), Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 3,
    }, { HatchEmit = 2 }), front)
    halo(aura, CORE, 7, 0.68)
    ripple(aura, GOLD, 10, 2)
    drawIn(aura, T.Cross, rgb(170, 235, 255), 0.6, 50)
    burst(aura, rgb(160, 235, 255), 11)
    light(aura, CORE, 14, 1.4)
end

-- ---------- building ----------
function EggAuraVFX.has(eggId)
    return RECIPES[eggId] ~= nil
end

-- How high the pedestal rises round the egg (its cup or rim), in studs above the egg's resting point.
local function rimHeight(stand, origin)
    local pedestal = stand:FindFirstChild("Pedestal")
    if not pedestal then
        return 0
    end
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Include
    params.FilterDescendantsInstances = { pedestal }
    local top = 0
    for k = 0, 7 do
        local a = k * math.pi / 4
        local from = origin * CFrame.new(math.cos(a) * 2.1, 10, math.sin(a) * 2.1)
        local hit = Workspace:Raycast(from.Position, Vector3.new(0, -20, 0), params)
        if hit then
            top = math.max(top, hit.Position.Y - origin.Position.Y)
        end
    end
    return top
end

-- (Re)builds the auras of every egg stand on the island that has a recipe.
function EggAuraVFX.build(island)
    local model = Workspace.FloatingIslands[island]
    local old = model:FindFirstChild("EggAuras")
    if old then
        old:Destroy()
    end
    local folder = Instance.new("Folder")
    folder.Name = "EggAuras"
    local built = {}
    for _, stand in model.EggStands:GetChildren() do
        local eggId = stand:GetAttribute("EggId")
        local origin = stand:GetAttribute("AuraOrigin")
        if RECIPES[eggId] and typeof(origin) == "CFrame" then
            local aura = Instance.new("Model")
            aura.Name = eggId
            aura:SetAttribute("EggId", eggId)
            aura.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- streams in whole, so the client sees it complete
            local root = Instance.new("Part")
            root.Name = "Root"
            root.Anchored = true
            root.CanCollide = false
            root.CanQuery = false
            root.CanTouch = false
            root.CastShadow = false
            root.Transparency = 1
            root.Size = Vector3.new(0.2, 0.2, 0.2)
            root.CFrame = origin
            root.Parent = aura
            aura.PrimaryPart = root
            RECIPES[eggId]({ model = aura, root = root, rim = rimHeight(stand, origin) })
            CollectionService:AddTag(aura, TAG)
            aura.Parent = folder
            table.insert(built, eggId)
        end
    end
    folder.Parent = model
    return built
end

return EggAuraVFX

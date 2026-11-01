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
local ServerStorage = game:GetService("ServerStorage")
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
    -- Jade Grove
    Leaf = "rbxassetid://6475162564",            -- VS: a single veined leaf
    GlowRing = "rbxassetid://12386390257",       -- VS: glowing ring with a soft corona
    JadeLeaf = "rbxassetid://123839325562421",   -- QA: vine ring round a six-leaf jade rosette
    BlossomSigil = "rbxassetid://104690771337528", -- QA: blossom mandala
    TreeRings = "rbxassetid://97314964323991",   -- QA: an ancient tree's growth rings crossed by roots
    Petal = "rbxassetid://122668143134554",      -- QA: one blossom petal
    Blossom = "rbxassetid://100572808754853",    -- QA: five-petal blossom
    Vortex = "rbxassetid://82549101989057",      -- QA: a soft vortex of five thin arms of Qi
    BloomLight = "rbxassetid://80600586960187",  -- QA: a bloom of light, rays in petal-shaped lobes
    -- (VFX Studio's swirl vortex and radial burst are white on black, with no alpha: they show as
    -- black squares on a SurfaceGui plane, so ours replace them)
    -- Ember Peak
    Fireburst = "rbxassetid://15811794808",      -- VS: a fiery burst (single frame)
    GoldFeather = "rbxassetid://7244584563",     -- VS: a golden flame feather
    Lava = "rbxassetid://1112726928",            -- VS: molten lava (tiles along a beam)
    Fissure = "rbxassetid://139285675827924",    -- QA: a caldera of broken crust and branching fissures
    CrystalForge = "rbxassetid://113317746351445", -- QA: six crystal points round a forge hexagon
    PhoenixSigil = "rbxassetid://114119118263415", -- QA: a phoenix with spread wings in a ring of flame
    FlameTongue = "rbxassetid://86422452019290", -- QA: one flame tongue, hot at its root
    Rock = "rbxassetid://137469228900771",       -- QA: an obsidian chunk with lava veins (Blender render)
    Vessel = "rbxassetid://80498467493439",      -- QA: a molten artery, coloured: white-hot core, blood-red body, dark rim
    CrustRing = "rbxassetid://125397922605343",  -- QA: dark basalt crust ring, molten in its breaks (coloured)
    Ash = "rbxassetid://117440820612388",        -- QA: one flake of ash
    FireMain = "rbxasset://textures/particles/fire_main.dds",          -- Roblox's built-in flame
    FireSparks = "rbxasset://textures/particles/fire_sparks_main.dds", -- Roblox's built-in fire sparks
    Spark = "rbxassetid://121337217386887",      -- QA: one spark, a hot drop with real alpha (keeps its colour on a bright sky)
}

-- Maps Studio's importer does not read, set on the stored meshes' SurfaceAppearances (storeMeshes).
local MAPS = {
    InfernoFragments = { Roughness = "rbxassetid://118527493596655", Metalness = "rbxassetid://127031228999225" },
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

-- A sprite floating round the egg on `orbit` (mover attributes): a billboard of `texture` (the
-- AuraCrystal shard by default, a faceted crystal modelled and rendered in Blender) on a soft
-- glow, rocking `sway` degrees as it goes round.
local function crystal(aura, name, orbit, size, color, brightness, texture, sway, glowColor)
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
    glow.ImageColor3 = glowColor or color
    glow.ImageTransparency = 0.55
    glow.Parent = gui
    local shard = Instance.new("ImageLabel")
    shard.Name = "Shard"
    shard.AnchorPoint = Vector2.new(0.5, 0.5)
    shard.Position = UDim2.fromScale(0.5, 0.5)
    shard.Size = UDim2.fromScale(0.72, 0.72)
    shard.BackgroundTransparency = 1
    shard.Image = texture or T.Crystal
    shard.ImageColor3 = color
    shard.ZIndex = 2
    set(shard, nil, { Sway = sway or 18, SwayPeriod = orbit.BobPeriod or 3, Phase = orbit.Phase or 0 })
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


-- ---------- fitting an aura to its egg model ----------
-- A point on the egg model, given as an offset from the centre of its body's bounding box in the
-- egg's Blender build (Roblox axes, egg units, measured in egg_bake's output), in the Root's
-- space. Studio's importer turns models half round, so x and z flip.
local function modelPoint(aura, offset)
    local world = aura.egg.CFrame:PointToWorldSpace(Vector3.new(-offset.X, offset.Y, -offset.Z) * 1.3)
    return aura.root.CFrame:PointToObjectSpace(world)
end

local function anchor(aura, name, offset)
    local a = Instance.new("Attachment")
    a.Name = name
    a.Position = modelPoint(aura, offset)
    a.Parent = aura.root
    return a
end

-- Raises everything that orbits or turns round the egg by `dy` studs, for an egg taller than the
-- recipe's measures (the detailed eggs). The ground formations stay on the rim.
local function lift(aura, dy)
    for _, d in aura.model:GetDescendants() do
        if d:IsA("Attachment") and d:GetAttribute("Orbit") and d.Parent == aura.root then
            d:SetAttribute("Height", d:GetAttribute("Height") + dy)
            if d.CFrame.Rotation == CFrame.identity then
                d.Position += Vector3.new(0, dy, 0)
            end
        elseif d:IsA("Attachment") and (d.Name == "Halo" or d.Name == "Light" or d.Name == "Burst") then
            d.Position += Vector3.new(0, dy, 0)
        elseif d:IsA("BasePart") and d:GetAttribute("Spin") and d.Name ~= "Formation" and d.Name ~= "Bloom" and d.Name ~= "Vortex" then
            d.CFrame += Vector3.new(0, dy, 0)
        elseif d:IsA("BasePart") and (d.Name == "GlintArea" or d.Name == "DrawIn" or d.Name == "SparkArea") then
            d.CFrame += Vector3.new(0, dy, 0)
        end
    end
    aura.model:SetAttribute("Lifted", dy)
end

-- ---------- Jade Grove ----------
-- Things that shed from an orbiting head (leaves, petals): they hang where they were shed,
-- tumbling and fading, so the head leaves a spiral wake round the egg.
local function shed(head, name, texture, color, rate, size, fall) -- size: { born, full, at death }
    return finish(emitter(name, {
        Texture = texture, Rate = rate, Lifetime = NumberRange.new(1.4, 2.2), Speed = NumberRange.new(0.2, 0.6),
        SpreadAngle = Vector2.new(180, 180), Drag = 1.6, Acceleration = Vector3.new(0, -fall, 0),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-150, 150),
        Size = seq({ { 0, size[1] }, { 0.15, size[2] }, { 1, size[3] } }), Color = color,
        Transparency = seq({ { 0, 0.6 }, { 0.12, 0.05 }, { 0.7, 0.2 }, { 1, 1 } }), LightEmission = 0.15, Brightness = 1.6, -- solid, not glowing: they read in daylight
    }, { HatchEmit = 4 }), head)
end

-- A vine of light twining up round the egg: a beam from a point sweeping round the rim to a point
-- circling above the crown at another speed, so the vine twists as the two drift apart.
local function tendril(aura, name, base, top, properties)
    local a0 = attachment(aura, name .. "Base", CFrame.new(0, base.Height, base.Radius) * UP_AXIS)
    set(a0, nil, base)
    local a1 = attachment(aura, name .. "Top", CFrame.new(0, top.Height, top.Radius) * UP_AXIS)
    set(a1, nil, top)
    local beam = Instance.new("Beam")
    beam.Name = name
    beam.Attachment0, beam.Attachment1 = a0, a1
    beam.FaceCamera = true
    beam.LightInfluence = 0
    beam.Segments = 20
    set(beam, properties)
    beam.Parent = aura.root
    return beam
end

-- Jade Spirit Egg: living jade. A vine-and-leaf formation turning beneath; a jade ring and a
-- swooshing crescent of Qi crossing round the egg; three vines of light twining up from the rim to
-- the crown, each at its own pace; three currents of Qi racing round on their own planes, shedding
-- leaves that tumble in their wake; three broad leaves drifting round, rocking; jade motes rising.
RECIPES.JadeSpiritEgg = function(aura)
    local JADE, MINT, DEEP = rgb(40, 220, 110), rgb(170, 255, 200), rgb(10, 140, 70)
    aura.model:SetAttribute("Gather", 1.3)
    aura.model:SetAttribute("Tint", rgb(70, 235, 130))
    set(aura.model, nil, { Breath = 0.18, BreathPeriod = 4.5 }) -- a green, growing breath
    -- the stands here are 7.5 studs apart: everything stays within about 3.3 studs of the egg
    formation(aura, "Formation", T.JadeLeaf, 3.2, rgb(60, 230, 120), 10, 3)
    ring(aura, "JadeRing", EGG_CENTRE + 0.2, tilt(-24, 10), T.GlowRing, 6.2, JADE, 28, 2.4, nil, { 10, 6 })
    ring(aura, "Swoosh", EGG_CENTRE - 0.2, tilt(-14, -28), T.WindArc, 6.4, MINT, -130, 2.6, nil, { 14, 4.5, 140 })
    -- vines of light twining up round the egg
    for k = 1, 3 do
        tendril(aura, "Vine" .. k,
            { Orbit = 14, Radius = 2.2, Height = aura.rim + 0.15, Phase = (k - 1) * 120 },
            { Orbit = 14 + 22 * k, Radius = 0.9, Height = 4.2, Phase = (k - 1) * 120 + 150, Bob = 0.2, BobPeriod = 3 + k }, {
            -- the braided stream reads as twining vine; low light emission keeps it green in daylight
            Texture = T.Stream, TextureMode = Enum.TextureMode.Wrap, TextureLength = 2, TextureSpeed = 0.6,
            CurveSize0 = 1.8, CurveSize1 = 1.4, Width0 = 0.5, Width1 = 0.16, LightEmission = 0.25, Brightness = 2,
            Color = colors({ { 0, rgb(20, 150, 60) }, { 0.6, JADE }, { 1, rgb(150, 255, 190) } }),
            Transparency = seq({ { 0, 1 }, { 0.1, 0.05 }, { 0.85, 0.1 }, { 1, 1 } }),
        })
    end
    -- three currents of Qi on their own planes and speeds, each shedding leaves
    for k, c in { { 120, 2.3, 22, 0, 0.4, 2.8 }, { -95, 2.8, -18, 14, 0.6, 3.6 }, { 140, 3.1, 8, -20, 0.5, 2.3 } } do
        local _, head = arc(aura, "Current" .. k, { Orbit = c[1], Radius = c[2], Height = EGG_CENTRE, Tilt = Vector3.new(c[3], 0, c[4]),
            Phase = (k - 1) * 120, Bob = c[5], BobPeriod = c[6] }, 0.2, {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.9, Brightness = 3, LightEmission = 0.35,
            Color = colors({ { 0, rgb(150, 255, 190) }, { 0.5, JADE }, { 1, DEEP } }), Transparency = seq({ { 0, 0.05 }, { 0.6, 0.4 }, { 1, 1 } }),
            WidthScale = seq({ { 0, 0.4 }, { 0.1, 1 }, { 1, 0 } }),
        })
        shed(head, "Leaves", T.Leaf, ColorSequence.new(rgb(90, 220, 90), rgb(20, 150, 70)), 4, { 0.35, 0.6, 0.5 }, 0.25)
    end
    -- three broad leaves drifting round, rocking like leaves on water
    for k, l in { { 12, 3.0, 3.0, 0.45, 3.4, 1.3 }, { -9, 3.3, 1.4, 0.35, 4.1, 1.05 }, { 16, 2.8, 2.2, 0.5, 3.0, 1.15 } } do
        crystal(aura, "FloatLeaf" .. k, { Orbit = l[1], Radius = l[2], Height = l[3], Phase = (k - 1) * 120 + 60, Bob = l[4], BobPeriod = l[5] },
            l[6], rgb(110, 230, 130), 1.4, T.Leaf, 32, rgb(60, 220, 110))
    end
    local motes = part(aura, "MoteArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(5.5, 0.2, 5.5))
    finish(emitter("Motes", {
        Texture = T.Dot, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.8, 1.6), SpreadAngle = Vector2.new(25, 25),
        Acceleration = Vector3.new(0, 0.5, 0), Drag = 0.6, Lifetime = NumberRange.new(2.2, 3.2), Rate = 8,
        Size = seq({ { 0, 0 }, { 0.15, 0.35 }, { 0.6, 0.22 }, { 1, 0 } }), Brightness = 2,
        Color = colors({ { 0, MINT }, { 1, JADE } }), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }),
    }, { HatchEmit = 25 }), motes)
    local glints = part(aura, "GlintArea", CFrame.new(0, EGG_CENTRE + 0.4, 0), Vector3.new(6, 4.5, 6))
    finish(emitter("Glints", {
        Texture = T.Star4, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.3, 0.7), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(0.8, 1.2), Rate = 3,
        Rotation = NumberRange.new(0, 45), Size = seq({ { 0, 0 }, { 0.5, 0.55 }, { 1, 0 } }), Color = ColorSequence.new(MINT),
        Transparency = NumberSequence.new(0.1), Brightness = 2,
    }, { HatchEmit = 14 }), glints)
    halo(aura, JADE, 6.5, 0.72)
    column(aura, DEEP, MINT, 0.5, 4)
    mist(motes, JADE, MINT, 3, 0.9)
    ripple(aura, rgb(90, 240, 150), 9.5, 2)
    drawIn(aura, T.Leaf, rgb(140, 240, 150), 0.6, 40)
    burst(aura, rgb(150, 255, 190), 9)
    light(aura, JADE, 13, 1.2)
    -- fitted to the detailed egg (4.3 studs tall): everything rides 0.3 higher, the vines of light
    -- reach over its crown, and Qi breathes out of the jade-leaf gem in its front
    lift(aura, 0.3)
    for k = 1, 3 do
        local top = aura.root["Vine" .. k .. "Top"]
        set(top, nil, { Height = 5, Radius = 0.8 })
        top.Position = Vector3.new(0, 5, 0.8)
    end
    local gem = anchor(aura, "Gem", Vector3.new(-0.06, -0.277, 1.385))
    finish(emitter("GemBreath", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(2.2, 2.8), Rate = 1.2,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-15, 15), ZOffset = 0.4,
        Size = seq({ { 0, 1.2 }, { 0.5, 2.3 }, { 1, 2.6 } }), Color = ColorSequence.new(rgb(60, 255, 150)),
        Transparency = seq({ { 0, 1 }, { 0.35, 0.6 }, { 1, 1 } }), Brightness = 2,
    }, { HatchEmit = 3 }), gem)
    finish(emitter("GemQi", {
        Texture = T.Dot, Speed = NumberRange.new(0.3, 0.7), SpreadAngle = Vector2.new(180, 180), Drag = 1.2,
        Acceleration = Vector3.new(0, 0.7, 0), Lifetime = NumberRange.new(1.6, 2.4), Rate = 5,
        Size = seq({ { 0, 0 }, { 0.2, 0.22 }, { 1, 0 } }), Color = ColorSequence.new(rgb(170, 255, 205), rgb(40, 220, 110)),
        Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Brightness = 2.5,
    }, { HatchEmit = 16 }), gem)
end

-- Bloomwood Egg: eternal blossom. A blossom mandala over a slow bloom of golden light beneath; a
-- pink ring and a gold breeze crossing round the egg; two streams of blossom wind circling it,
-- shedding petals; petals thrown up from the rim in a fountain, drifting back down; four blossoms
-- floating round, rocking; golden pollen rising. Its breath is slow and dreamy.
RECIPES.BloomwoodEgg = function(aura)
    local PINK, BLUSH, GOLDEN = rgb(255, 110, 190), rgb(255, 200, 230), rgb(255, 205, 110)
    aura.model:SetAttribute("Gather", 1.4)
    aura.model:SetAttribute("Tint", rgb(255, 140, 205))
    set(aura.model, nil, { Breath = 0.14, BreathPeriod = 6 }) -- dreamy
    formation(aura, "Formation", T.BlossomSigil, 3.2, rgb(255, 120, 200), 6, 3)
    formation(aura, "Bloom", T.BloomLight, 2.8, GOLDEN, -12, 1.6, 0.1)
    ring(aura, "BlossomRing", EGG_CENTRE + 0.25, tilt(-20, 12), T.GlowRing, 6.2, PINK, 20, 2.3, nil, { 8, 8 })
    ring(aura, "GoldBreeze", EGG_CENTRE - 0.3, tilt(-10, -24), T.BrokenRing, 6.4, GOLDEN, -35, 2, 0.15, { 10, 7, 160 })
    -- two streams of blossom wind circling the egg, shedding petals
    for k, c in { { 70, 2.5, 16, 0, 0.8, 3.4 }, { -55, 3.0, -12, 18, 0.6, 4.2 } } do
        local _, head = arc(aura, "Breeze" .. k, { Orbit = c[1], Radius = c[2], Height = EGG_CENTRE + 0.2, Tilt = Vector3.new(c[3], 0, c[4]),
            Phase = (k - 1) * 180, Bob = c[5], BobPeriod = c[6] }, 0.22, {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.2, Brightness = 2.5, LightEmission = 0.3,
            Color = colors({ { 0, rgb(255, 170, 215) }, { 0.5, rgb(255, 90, 170) }, { 1, rgb(190, 50, 150) } }), Transparency = seq({ { 0, 0.05 }, { 0.6, 0.45 }, { 1, 1 } }),
            WidthScale = seq({ { 0, 0.4 }, { 0.1, 1 }, { 1, 0 } }),
        })
        shed(head, "Petals", T.Petal, ColorSequence.new(rgb(255, 140, 200), rgb(235, 80, 160)), 5, { 0.3, 0.48, 0.4 }, 0.4)
    end
    -- the petal fountain: petals thrown up off the rim, arcing out and drifting down
    local rim = part(aura, "PetalRim", CFrame.new(0, aura.rim + 0.2, 0), Vector3.new(4.4, 0.2, 4.4))
    finish(emitter("Fountain", {
        Texture = T.Petal, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(2.2, 3.2), SpreadAngle = Vector2.new(22, 22), Acceleration = Vector3.new(0, -1.6, 0), Drag = 0.9,
        Lifetime = NumberRange.new(2.6, 3.4), Rate = 5, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-180, 180),
        Size = seq({ { 0, 0.3 }, { 0.2, 0.48 }, { 1, 0.42 } }), Color = ColorSequence.new(rgb(255, 150, 205), rgb(235, 90, 165)),
        Transparency = seq({ { 0, 0.5 }, { 0.1, 0.05 }, { 0.75, 0.2 }, { 1, 1 } }), LightEmission = 0.15, Brightness = 1.6,
    }, { HatchEmit = 18 }), rim)
    -- four blossoms floating round at different heights, rocking
    for k, b in { { 10, 2.9, 3.3, 0.4, 3.6, 1.1 }, { -8, 3.2, 1.6, 0.35, 4.4, 0.9 }, { 13, 2.7, 2.4, 0.5, 3.1, 1.0 }, { -11, 3.3, 3.0, 0.3, 5.0, 0.8 } } do
        local floater = crystal(aura, "FloatBlossom" .. k, { Orbit = b[1], Radius = b[2], Height = b[3], Phase = (k - 1) * 90 + 30, Bob = b[4], BobPeriod = b[5] },
            b[6], rgb(255, 165, 215), 1.5, T.Blossom, 24, PINK)
        floater.BillboardGui.Glow.ImageTransparency = 0.78
    end
    local pollen = part(aura, "PollenArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(5, 0.2, 5))
    finish(emitter("Pollen", {
        Texture = T.Dot, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.6, 1.3), SpreadAngle = Vector2.new(30, 30),
        Acceleration = Vector3.new(0, 0.4, 0), Drag = 0.7, Lifetime = NumberRange.new(2.4, 3.4), Rate = 7,
        Size = seq({ { 0, 0 }, { 0.15, 0.28 }, { 0.6, 0.2 }, { 1, 0 } }), Brightness = 2.5,
        Color = ColorSequence.new(rgb(255, 230, 150), GOLDEN), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }),
    }, { HatchEmit = 25 }), pollen)
    local glints = part(aura, "GlintArea", CFrame.new(0, EGG_CENTRE + 0.4, 0), Vector3.new(6, 4.5, 6))
    finish(emitter("Glints", {
        Texture = T.Star4, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.3, 0.7), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(0.8, 1.2), Rate = 3,
        Rotation = NumberRange.new(0, 45), Size = seq({ { 0, 0 }, { 0.5, 0.55 }, { 1, 0 } }), Color = ColorSequence.new(BLUSH),
        Transparency = NumberSequence.new(0.1), Brightness = 2,
    }, { HatchEmit = 14 }), glints)
    -- no halo: on the pale crystal egg it reads as a milky veil
    column(aura, rgb(255, 140, 200), BLUSH, 0.3, 4).Transparency = seq({ { 0, 1 }, { 0.2, 0.82 }, { 0.6, 0.88 }, { 1, 1 } })
    mist(pollen, PINK, BLUSH, 3, 0.8)
    ripple(aura, rgb(255, 150, 210), 9.5, 2)
    drawIn(aura, T.Petal, BLUSH, 0.6, 40)
    burst(aura, rgb(255, 200, 230), 9)
    light(aura, rgb(255, 120, 190), 13, 0.5)
    -- fitted to the detailed egg: 0.2 higher, golden pollen rising out of both lotus hearts, and a
    -- soft glow round the emblem's heart
    lift(aura, 0.2)
    for name, offset in { LotusL = Vector3.new(-0.746, -1.032, 0.453), LotusR = Vector3.new(0.779, -1.032, 0.429) } do
        local a = anchor(aura, name, offset)
        finish(emitter("Pollen", {
            Texture = T.Dot, Speed = NumberRange.new(0.3, 0.7), SpreadAngle = Vector2.new(35, 35), Drag = 0.8,
            Acceleration = Vector3.new(0, 1, 0), Lifetime = NumberRange.new(1.8, 2.8), Rate = 6,
            Size = seq({ { 0, 0 }, { 0.15, 0.24 }, { 1, 0 } }), Color = ColorSequence.new(rgb(255, 235, 150), rgb(255, 180, 70)),
            Transparency = seq({ { 0, 0.05 }, { 1, 1 } }), Brightness = 2.5,
        }, { HatchEmit = 12 }), a)
        finish(emitter("LotusGlow", {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(1.8, 2.4), Rate = 1,
            Size = seq({ { 0, 0.6 }, { 0.5, 1.1 }, { 1, 1.3 } }), Color = ColorSequence.new(rgb(255, 190, 80)),
            Transparency = seq({ { 0, 1 }, { 0.4, 0.82 }, { 1, 1 } }), Brightness = 2,
        }, { HatchEmit = 2 }), a)
    end
    finish(emitter("HeartGlow", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(2.4, 3), Rate = 1,
        Rotation = NumberRange.new(0, 360), ZOffset = 0.4,
        Size = seq({ { 0, 0.7 }, { 0.5, 1.3 }, { 1, 1.5 } }), Color = ColorSequence.new(rgb(255, 60, 170)),
        Transparency = seq({ { 0, 1 }, { 0.4, 0.8 }, { 1, 1 } }), Brightness = 2,
    }, { HatchEmit = 3 }), anchor(aura, "Heart", Vector3.new(0.008, -0.244, 1.289)))
end

-- Ancient Grove Egg: the world tree's heartbeat. The growth rings of an ancient tree turning
-- slowly beneath a counter-turning vortex of green Qi; five roots of light crawling in over the
-- rim and up into the egg, drawing the grove's Qi in; a spiral of Qi climbing round the egg; four
-- forest spirits wandering round it on their own slow, looping paths; leaves drifting down from the
-- branches; a wide ring of old light. Its breath is deep and slow.
RECIPES.AncientGroveEgg = function(aura)
    local LEAFG, SPIRIT, AMBER, BARK = rgb(110, 240, 70), rgb(200, 255, 170), rgb(240, 200, 90), rgb(120, 200, 60)
    aura.model:SetAttribute("Gather", 1.6)
    aura.model:SetAttribute("Tint", rgb(130, 245, 90))
    set(aura.model, nil, { Breath = 0.16, BreathPeriod = 7 }) -- deep and slow, an ancient pulse of life
    formation(aura, "Formation", T.TreeRings, 3.4, rgb(150, 230, 80), 4, 2.8)
    formation(aura, "Vortex", T.Vortex, 3.8, LEAFG, -28, 2.4, 0.1)        -- its arms sweep out past the rings
    ring(aura, "OldLight", EGG_CENTRE + 0.6, tilt(-8, 6), T.GlowRing, 6.8, AMBER, 9, 1.8, nil, { 5, 11 })
    -- roots of light rising from low on the pedestal (the Jade Grove pedestals are cones of golden
    -- roots, about 2 studs below the egg 4 studs out) and climbing up into the egg's heart
    local heart = attachment(aura, "Heart", CFrame.new(0, EGG_CENTRE * 0.8, 0) * UP_AXIS)
    for k = 1, 5 do
        stream(aura, "Root" .. k, { Orbit = 5, Radius = 3.9, Height = -2, Phase = (k - 1) * 72 + 20 }, heart, {
            Texture = T.Stream, TextureMode = Enum.TextureMode.Wrap, TextureLength = 1.6, TextureSpeed = 0.9,
            CurveSize0 = 2.2, CurveSize1 = -0.4, Width0 = 0.75, Width1 = 0.3, Brightness = 2.5, LightEmission = 0.2,
            Color = colors({ { 0, rgb(230, 170, 40) }, { 0.5, rgb(120, 230, 50) }, { 1, rgb(190, 255, 140) } }),
            Transparency = seq({ { 0, 1 }, { 0.08, 0.05 }, { 0.85, 0.1 }, { 1, 1 } }),
        })
    end
    -- a spiral of Qi climbing round the egg: a fast-circling head bobbing up and down, its motes
    -- rising as they fade
    local spiralHead = attachment(aura, "SpiralHead", CFrame.new(0, EGG_CENTRE, 1.7))
    set(spiralHead, nil, { Orbit = 200, Radius = 1.95, Height = EGG_CENTRE, Bob = 1.2, BobPeriod = 5 })
    finish(emitter("Spiral", {
        Texture = T.Dot, Rate = 22, Lifetime = NumberRange.new(1.2, 1.6), Speed = NumberRange.new(0.05),
        Acceleration = Vector3.new(0, 0.9, 0), Size = seq({ { 0, 0.45 }, { 1, 0 } }), Brightness = 3,
        Color = ColorSequence.new(rgb(140, 255, 90), rgb(60, 210, 40)), Transparency = seq({ { 0, 0 }, { 1, 1 } }),
    }, { HatchEmit = 20 }), spiralHead)
    -- forest spirits: soft orbs with trails wandering round on slow looping paths
    for k, w in { { 38, 3.0, 2.6, 18, 1.2, 4.2 }, { -46, 3.4, 3.6, -14, 0.9, 5.1 }, { 52, 2.8, 1.6, 26, 1.0, 3.6 }, { -33, 3.6, 4.4, -8, 1.4, 6 } } do
        local _, head = arc(aura, "Spirit" .. k, { Orbit = w[1], Radius = w[2], Height = w[3], Tilt = Vector3.new(w[4], 0, -w[4] * 0.5),
            Phase = (k - 1) * 90 + 45, Bob = w[5], BobPeriod = w[6] }, 0.12, {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.3, Brightness = 2.5, LightEmission = 0.8,
            Color = colors({ { 0, SPIRIT }, { 1, LEAFG } }), Transparency = seq({ { 0, 0.1 }, { 0.5, 0.5 }, { 1, 1 } }),
            WidthScale = seq({ { 0, 1 }, { 1, 0 } }),
        })
        finish(emitter("Orb", {
            Texture = T.SmallGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.3), Rate = 14,
            Size = seq({ { 0, 0.55 }, { 1, 0.3 } }), Color = ColorSequence.new(rgb(170, 255, 120)), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Brightness = 3,
        }), head)
    end
    local motes = part(aura, "MoteArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(7, 0.2, 7))
    halo(aura, LEAFG, 7.5, 0.74)
    column(aura, BARK, SPIRIT, 0.25, 5)
    mist(motes, LEAFG, SPIRIT, 3, 0.7)
    ripple(aura, rgb(150, 240, 110), 11, 3)
    drawIn(aura, T.Leaf, rgb(170, 245, 120), 0.65, 45)
    burst(aura, rgb(190, 255, 150), 11)
    light(aura, LEAFG, 15, 1.2)
    -- fitted to the detailed egg: 0.15 higher, and the egg's own five leaf crowns come alive: light
    -- glowing inside each, fireflies drifting out of it, leaves falling from it (gold and green
    -- by turns)
    lift(aura, 0.15)
    local CROWNS = { { Vector3.new(1.661, 0.284, 0.304), 0.422 }, { Vector3.new(-1.753, 0.757, 0.581), 0.344 },
        { Vector3.new(0.644, 1.487, -0.358), 0.364 }, { Vector3.new(-1.627, 0.99, -0.374), 0.431 }, { Vector3.new(-0.262, 1.71, -0.244), 0.312 } }
    for k, c in CROWNS do
        local a = anchor(aura, "Crown" .. k, c[1])
        local r = c[2] * 1.3
        finish(emitter("Leaves", {
            Texture = T.Leaf, Speed = NumberRange.new(0.2, 0.6), SpreadAngle = Vector2.new(180, 180), Drag = 0.6,
            Acceleration = Vector3.new(0.3, -0.55, 0.12), Lifetime = NumberRange.new(3.5, 4.5), Rate = 1 + 0.3 * (k % 2),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-110, 110), LightEmission = 0.15, Brightness = 1.6,
            Size = seq({ { 0, 0.3 }, { 0.1, 0.42 }, { 1, 0.38 } }),
            Color = k % 2 == 0 and ColorSequence.new(rgb(215, 215, 80), rgb(150, 190, 60)) or ColorSequence.new(rgb(120, 225, 80), rgb(60, 170, 50)),
            Transparency = seq({ { 0, 1 }, { 0.08, 0.05 }, { 0.8, 0.2 }, { 1, 1 } }),
        }, { HatchEmit = 6 }), a)
        finish(emitter("Glow", {   -- drawn in front of the leaves (ZOffset): light shining through the crown
            Texture = T.SmallGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(1.6, 2.2), Rate = 1.2,
            Size = seq({ { 0, r * 3 }, { 0.5, r * 3.8 }, { 1, r * 3.3 } }), Color = ColorSequence.new(rgb(140, 255, 90)),
            Transparency = seq({ { 0, 1 }, { 0.45, 0.55 }, { 1, 1 } }), Brightness = 2, ZOffset = 1.2,
        }, { HatchEmit = 2 }), a)
        finish(emitter("Fireflies", {
            Texture = T.Dot, Speed = NumberRange.new(0.3, 0.8), SpreadAngle = Vector2.new(180, 180), Drag = 1.4,
            Acceleration = Vector3.new(0, 0.15, 0), Lifetime = NumberRange.new(1.8, 2.6), Rate = 3,
            Size = seq({ { 0, 0 }, { 0.2, 0.26 }, { 0.6, 0.18 }, { 1, 0 } }), Color = ColorSequence.new(rgb(220, 255, 140)),
            Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 3, ZOffset = 1.5,
        }, { HatchEmit = 8 }), a)
    end
end


-- ---------- Ember Peak ----------
-- The Phoenix Altar's stands are basalt columns about 6 studs apart, so an aura stays within about
-- 3.3 studs of its egg.

local function group(aura, name)
    local f = Instance.new("Folder")
    f.Name = name
    f.Parent = aura.model
    return f
end

-- Moves meshes imported from Blender into ServerStorage.AuraMeshes.<name>: "<x>_Glow_<rrggbb>"
-- pieces become Neon in that colour, the rest get the maps the importer does not read (MAPS).
function EggAuraVFX.storeMeshes(model, name)
    local folder = ServerStorage:FindFirstChild("AuraMeshes") or Instance.new("Folder")
    folder.Name = "AuraMeshes"
    folder.Parent = ServerStorage
    local old = folder:FindFirstChild(name)
    if old then
        old:Destroy()
    end
    local stored = Instance.new("Model")
    stored.Name = name
    for _, m in model:GetDescendants() do
        if m:IsA("MeshPart") then
            local hex = m.Name:match("_Glow_(%x%x%x%x%x%x)$")
            if hex then
                m.Material = Enum.Material.Neon
                m.Color = Color3.fromHex(hex)
                local sa = m:FindFirstChildOfClass("SurfaceAppearance")
                if sa then
                    sa:Destroy()
                end
            else
                local sa = m:FindFirstChildOfClass("SurfaceAppearance")
                if sa and MAPS[name] then
                    sa.RoughnessMap = MAPS[name].Roughness
                    sa.MetalnessMap = MAPS[name].Metalness
                end
            end
            m.Anchored = true
            m.CanCollide, m.CanQuery, m.CanTouch, m.CastShadow = false, false, false, false
            m.Parent = stored
        end
    end
    model:Destroy()
    stored.Parent = folder
    return #stored:GetChildren()
end

-- Magma Heart Egg: a blazing fire round the egg, the owner's test fire from the Starting Island
-- fitted to the egg. Roblox's own fire textures, no Fire object, no flipbook. Eight flame columns
-- stand in a ring just inside the egg's widest girth (one emitter per unrotated attachment: a single
-- emitter on a bed under the egg starts its flames inside the egg, and a ring-shaped one scatters
-- them into thin smoke), so the flames lick up every side of it. Each column is a small copy of the
-- test fire: flames from bright yellow through orange and red to dark red, flickering, with a faster
-- yellow core in every other column; embers drift up from a bed under the egg. Together the columns
-- emit what the test fire did (about 190 flames and 120 core flames a second). Half light emission,
-- not full: fully additive flames wash out to pale smoke against the day sky.
RECIPES.MagmaHeartEgg = function(aura)
    local size = aura.egg and aura.egg.Size or Vector3.new(3.8, 5.25, 3.95)
    local girth = math.max(size.X, size.Z)
    set(aura.model, nil, { Gather = 1.4, Tint = rgb(255, 110, 25) })
    local flames = {
        Texture = T.FireMain, EmissionDirection = Enum.NormalId.Top, Rate = 24, Lifetime = NumberRange.new(0.5, 1.2),
        Speed = NumberRange.new(5, 10), SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 8, 0), Drag = 2,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-60, 60), LightEmission = 0.6, Brightness = 2.2,
        Size = seq({ { 0, 1.3 }, { 0.15, 1.7 }, { 1, 0 } }), Transparency = seq({ { 0, 0.15 }, { 0.5, 0.25 }, { 1, 1 } }),
        Color = colors({ { 0, rgb(255, 255, 190) }, { 0.2, rgb(255, 225, 40) }, { 0.45, rgb(255, 135, 10) }, { 0.75, rgb(220, 35, 5) }, { 1, rgb(90, 5, 0) } }),
    }
    local core = {
        Texture = T.FireMain, EmissionDirection = Enum.NormalId.Top, Rate = 30, Lifetime = NumberRange.new(0.3, 0.6),
        Speed = NumberRange.new(9, 14), SpreadAngle = Vector2.new(8, 8), Acceleration = Vector3.new(0, 10, 0), Drag = 2.5,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90), LightEmission = 0.6, Brightness = 3,
        Size = seq({ { 0, 0.7 }, { 1, 0 } }), Transparency = seq({ { 0, 0 }, { 1, 1 } }),
        Color = colors({ { 0, rgb(255, 255, 210) }, { 0.4, rgb(255, 235, 60) }, { 1, rgb(255, 150, 20) } }),
    }
    local radius = girth / 2 * 0.95
    for k = 1, 8 do
        local ang = (k - 0.5) * math.pi / 4
        local at = attachment(aura, "Fire" .. k, CFrame.new(math.cos(ang) * radius, 0.15, math.sin(ang) * radius))
        finish(emitter("Flames", flames, { FlickerRate = NumberRange.new(18, 28), FlickerSpeedMin = NumberRange.new(6, 9),
            FlickerSpeedMax = NumberRange.new(10, 15), FlickerPeriod = 0.15, HatchEmit = 8 }), at)
        if k % 2 == 0 then
            finish(emitter("Core", core, { HatchEmit = 8 }), at)
        end
    end
    local bed = part(aura, "FireBed", CFrame.new(0, 0.15, 0), Vector3.new(girth * 0.8, 0.2, girth * 0.8))
    finish(emitter("Embers", {
        Texture = T.FireSparks, EmissionDirection = Enum.NormalId.Top, Rate = 18, Lifetime = NumberRange.new(1.5, 3),
        Speed = NumberRange.new(3, 6), SpreadAngle = Vector2.new(30, 30), Acceleration = Vector3.new(0.6, 2.5, 0.3), Drag = 1.2,
        LightEmission = 0.6, Brightness = 4, Size = seq({ { 0, 0.32, 0.1 }, { 1, 0 } }),
        Transparency = seq({ { 0, 0 }, { 0.8, 0.2 }, { 1, 1 } }),
        Color = colors({ { 0, rgb(255, 220, 90) }, { 0.5, rgb(255, 120, 20) }, { 1, rgb(200, 30, 5) } }),
    }, { HatchEmit = 25 }), bed)
end

-- Phoenix Ash Egg: the Ash Cycle, an egg that dies and is reborn every CYCLE seconds (its rarest pet
-- is the Prismatic Phoenix). Ash: it cools, its veins and emblem dim to a smoulder, grey ash falls
-- round it (the one aura on the altar where things fall) and a curl of dark smoke rises from its
-- crown. Kindling: embers wink awake in the ash, the glow climbs back. Rebirth: the ash turns and
-- rushes up catching fire gold, two wings of light sweep open from behind it shedding golden
-- feathers, a sunburst blooms over its crown, its rim flashes through the prism's colours and a
-- near player's screen flashes warm. Burning down: the wings fold, their feathers falling and
-- greying into ash, and the cycle begins again. A hatch's burst is a rebirth.
-- Its right side (+X) faces the Magma Heart 5.9 studs away: the wings open beside the egg, clear of it.
RECIPES.PhoenixAshEgg = function(aura)
    local size = aura.egg and aura.egg.Size or Vector3.new(4.57, 4.67, 3.53)
    local C = size.Y / 2                             -- the egg's centre above its resting point
    local top = size.Y
    local GOLD, FLAME, EMBER = rgb(255, 215, 120), rgb(255, 140, 40), rgb(220, 60, 25)
    local R = 0.735                                  -- where in the cycle the rebirth bursts
    set(aura.model, nil, {
        Gather = 1.6, Tint = rgb(255, 170, 60), CyclePeriod = 15, CycleRebirth = R, CycleScreen = 22, CycleScreenFlash = 0.45,
        -- the egg's glowing parts: smouldering through the ash, white-gold at the rebirth
        CycleEggGlow = seq({ { 0, 0.3 }, { 0.55, 0.3 }, { 0.72, 1 }, { R + 0.01, 1.8 }, { 0.8, 1.5 }, { 0.9, 0.8 }, { 1, 0.3 } }),
        CycleEggCold = rgb(45, 14, 8), CycleEggHot = rgb(255, 225, 130),
        -- the rim: a dull ember, kindling, then the prism's colours racing round, then gold cooling to red
        CycleHighlight = colors({ { 0, rgb(120, 25, 15) }, { 0.6, rgb(150, 35, 15) }, { 0.72, rgb(255, 120, 40) },
            { R + 0.001, rgb(255, 70, 70) }, { 0.748, rgb(255, 170, 40) }, { 0.76, rgb(255, 240, 90) }, { 0.772, rgb(90, 255, 140) },
            { 0.784, rgb(80, 200, 255) }, { 0.796, rgb(190, 110, 255) }, { 0.81, rgb(255, 200, 120) }, { 0.88, rgb(255, 120, 40) },
            { 1, rgb(120, 25, 15) } }),
        CycleOutline = seq({ { 0, 0.85 }, { 0.6, 0.85 }, { 0.72, 0.5 }, { R + 0.005, 0.05 }, { 0.82, 0.15 }, { 0.92, 0.7 }, { 1, 0.85 } }),
        CycleFill = seq({ { 0, 1 }, { 0.72, 1 }, { R + 0.01, 0.82 }, { 0.8, 0.9 }, { 0.86, 1 }, { 1, 1 } }),   -- a faint fill: more hides its feathers
    })
    -- ash falling round it through the dormant phase; none while it burns
    local sky = part(aura, "AshSky", CFrame.new(0, top + 0.8, 0), Vector3.new(5.6, 0.4, 5.6))
    finish(emitter("AshFall", {
        Texture = T.Ash, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Bottom, Speed = NumberRange.new(0.3, 0.7), SpreadAngle = Vector2.new(25, 25), Drag = 0.6,
        Acceleration = Vector3.new(0.15, -0.45, 0.05), Lifetime = NumberRange.new(5, 7), Rate = 18, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-90, 90), Size = seq({ { 0, 0.3, 0.1 }, { 1, 0.25, 0.08 } }),   -- pale: dark flakes read as dirt on the sky
        Color = colors({ { 0, rgb(175, 168, 162) }, { 1, rgb(125, 118, 114) } }), LightEmission = 0, LightInfluence = 0.2,
        Transparency = seq({ { 0, 1 }, { 0.1, 0.15 }, { 0.85, 0.35 }, { 1, 1 } }),
    }, { CycleRate = seq({ { 0, 1 }, { 0.6, 1 }, { 0.725, 0.6 }, { R, 0 }, { 0.86, 0 }, { 1, 1 } }) }), sky)
    -- the body of air round the egg: embers kindle in it, and the ash rushes up out of it at the rebirth
    local air = part(aura, "AshAir", CFrame.new(0, C, 0), Vector3.new(5.6, size.Y, 5.6))
    finish(emitter("Kindling", {
        Texture = T.Spark, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0, 0.3), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(0.3, 0.7), Rate = 40,
        Rotation = NumberRange.new(0, 360), Size = seq({ { 0, 0 }, { 0.4, 0.22, 0.06 }, { 1, 0 } }),
        Color = ColorSequence.new(rgb(255, 200, 90), rgb(255, 90, 20)), LightEmission = 0.6, Brightness = 3,
    }, { CycleRate = seq({ { 0, 0.05 }, { 0.45, 0.05 }, { 0.6, 0.2 }, { 0.72, 1 }, { 0.745, 0.4 }, { 0.8, 0 }, { 0.9, 0 }, { 1, 0.05 } }) }), air)
    finish(emitter("AshRise", {
        Texture = T.Ash, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(4, 8), SpreadAngle = Vector2.new(20, 20), Drag = 1.2,
        Acceleration = Vector3.new(0, 2, 0), Lifetime = NumberRange.new(0.9, 1.5), Rate = 90, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-200, 200), Size = seq({ { 0, 0.18, 0.05 }, { 0.3, 0.26, 0.06 }, { 1, 0 } }),
        Color = colors({ { 0, rgb(120, 110, 105) }, { 0.18, GOLD }, { 0.5, FLAME }, { 1, EMBER } }), LightEmission = 0.6, Brightness = 3,
        Transparency = seq({ { 0, 0.1 }, { 0.75, 0.25 }, { 1, 1 } }),
    }, { CycleRate = seq({ { 0, 0 }, { R - 0.002, 0 }, { R + 0.003, 1 }, { 0.78, 1 }, { 0.82, 0 }, { 1, 0 } }), HatchEmit = 60 }), air)
    -- a thin curl of dark smoke from the crown while it lies in ash
    local crown = attachment(aura, "Crown", CFrame.new(0, top - 0.2, 0))
    finish(emitter("CrownSmoke", {
        Texture = T.Fog, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.8, 1.2), SpreadAngle = Vector2.new(8, 8),
        Acceleration = Vector3.new(0.2, 0.3, 0), Lifetime = NumberRange.new(2.5, 3.5), Rate = 4, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-30, 30), Size = seq({ { 0, 0.4, 0.1 }, { 1, 1.5, 0.3 } }),
        Color = colors({ { 0, rgb(80, 70, 66) }, { 1, rgb(70, 66, 66) } }), LightEmission = 0, LightInfluence = 0.2,
        Transparency = seq({ { 0, 1 }, { 0.15, 0.7 }, { 0.7, 0.82 }, { 1, 1 } }),
    }, { CycleRate = seq({ { 0, 1 }, { 0.6, 1 }, { 0.72, 0.3 }, { R, 0 }, { 0.9, 0 }, { 1, 1 } }) }), crown)
    -- the sunburst over its crown at the rebirth
    finish(emitter("Sunburst", {
        Texture = T.Flare, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.7), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, 1 }, { 0.25, 7 }, { 1, 8.5 } }), Color = ColorSequence.new(rgb(255, 220, 140)),
        Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Brightness = 2,
    }, { CycleEmit = 1, CycleAt = R + 0.003, HatchEmit = 2 }), attachment(aura, "Sun", CFrame.new(0, top + 0.6, 0)))

    -- the wings: on each side three feathers of light, each a trail between a still root inside the
    -- egg's shoulder and a tip that sweeps up and out from low at its flank, so the trail fans open
    -- like a wing; the tips fold back down as the wings burn out. The longest feather sheds golden
    -- feathers that grey into ash as they fall. The sweep stays in the egg's XY plane, just behind its
    -- middle: a sweep in depth collapses to a needle seen from the front. Swept by raycasts (the egg's
    -- CanQuery switched on for it), the wings keep 1.76 studs clear of the Magma Heart's egg, 3.3 of its stand.
    local sweep = seq({ { 0, 0 }, { R, 0 }, { 0.79, 1 }, { 0.86, 1 }, { 0.97, 0 }, { 1, 0 } })
    local wings = group(aura, "Wings")
    for _, side in { -1, 1 } do
        local root = attachment(aura, side < 0 and "WingRootL" or "WingRootR", CFrame.new(side * 1.4, C + 0.8, 0.7))
        for k, f in { { 3.4, C + 2.0, 1.2 }, { 4.0, C + 3.0, 1.35 }, { 4.4, C + 4.0, 1.5 } } do -- tip spread x, y; lifetime
            local from = Vector3.new(side * 1.9, C - 1.3 + 0.3 * k, 0.6)
            local to = Vector3.new(side * f[1], f[2], 0.5)
            local via = Vector3.new(side * (3.1 + 0.3 * k), C + 0.2 + 0.6 * k, 0.6)
            local tip = attachment(aura, (side < 0 and "WingTipL" or "WingTipR") .. k, CFrame.new(from))
            set(tip, nil, { SweepFrom = from, SweepVia = via, SweepTo = to, SweepCurve = sweep })
            local trail = Instance.new("Trail")
            trail.Name = (side < 0 and "WingL" or "WingR") .. k
            trail.Attachment0, trail.Attachment1 = root, tip
            set(trail, {
                -- solid: a textured trail (ribbon, feather) leaves only thin flicks past the egg's own sculpted
                -- wings. LightEmission over 0.15 washes it pale on the sky.
                Texture = "", Lifetime = f[3], FaceCamera = false, LightEmission = 0.15, LightInfluence = 0, Brightness = 2.4,
                Color = colors({ { 0, rgb(255, 215, 110) }, { 0.35, rgb(255, 140, 35) }, { 0.7, rgb(230, 60, 20) }, { 1, rgb(150, 25, 15) } }),
                Transparency = seq({ { 0, 0 }, { 0.5, 0.25 }, { 1, 1 } }),
            })
            trail.Parent = wings
            if k == 3 then
                finish(emitter("Feathers", {
                    Texture = T.GoldFeather, Speed = NumberRange.new(0.5, 1.5), SpreadAngle = Vector2.new(180, 180), Drag = 1,
                    Acceleration = Vector3.new(0, -1, 0), Lifetime = NumberRange.new(1.5, 2.2), Rate = 25, Rotation = NumberRange.new(0, 360),
                    RotSpeed = NumberRange.new(-120, 120), Size = seq({ { 0, 0.35 }, { 0.2, 0.5, 0.1 }, { 1, 0.4 } }),
                    Color = colors({ { 0, rgb(255, 225, 150) }, { 0.4, FLAME }, { 0.85, rgb(110, 104, 100) }, { 1, rgb(90, 86, 84) } }),
                    LightEmission = 0.25, Brightness = 2, Transparency = seq({ { 0, 0.4 }, { 0.1, 0 }, { 0.8, 0.2 }, { 1, 1 } }),
                }, { CycleRate = seq({ { 0, 0 }, { R, 0 }, { R + 0.005, 1 }, { 0.86, 0.6 }, { 0.97, 0 }, { 1, 0 } }), HatchEmit = 14 }), tip)
            end
        end
    end

    -- its light: a low red smoulder, a gold blaze at the rebirth
    local glow = light(aura, rgb(200, 50, 30), 12, 0.6)
    glow.Parent.Position = Vector3.new(0, C, 0)
    set(glow, nil, {
        CycleBrightness = seq({ { 0, 0.35 }, { 0.6, 0.35 }, { 0.72, 0.8 }, { R + 0.01, 3.2 }, { 0.8, 1.6 }, { 0.9, 0.6 }, { 1, 0.35 } }),
        CycleColor = colors({ { 0, rgb(200, 50, 30) }, { 0.6, rgb(200, 50, 30) }, { R + 0.005, rgb(255, 190, 90) }, { 0.85, rgb(255, 120, 50) }, { 1, rgb(200, 50, 30) } }),
    })
    drawIn(aura, T.Spark, rgb(255, 190, 90), 0.4, 50)
    burst(aura, rgb(255, 200, 110), 9)
    for _, d in aura.model:GetDescendants() do -- its whole hatch flare at the egg's height (the helpers assume a smaller egg)
        if d.Name == "Burst" and d:IsA("Attachment") then
            d.Position = Vector3.new(0, C, 0)
        elseif d.Name == "DrawIn" and d:IsA("BasePart") then
            d.CFrame = aura.root.CFrame * CFrame.new(0, C, 0)
        end
    end
end

-- Inferno Egg: a miniature volcano with an unstable molten core. Six systems, each with its own
-- motion and timing, and every few seconds an energy pulse runs through them in turn:
--   A. spark comets: three hot heads racing round it on tilted paths at their own speeds, shedding
--      streams of sparks that sketch rings of sparks round the egg;
--   B. magma fragments: broken volcanic rocks (modelled and baked in Blender) with lava glowing in
--      their cracks, orbiting at their own distances and speeds, tumbling, shedding embers;
--   C. a flame vortex: four molten ribbons spiralling round the egg on their own paths, flames
--      licking off them, sparks rising;
--   D. beneath: ripples of heat and three vents that erupt in turn on each pulse;
--   E. sparks spitting out of the egg's cracks, embers rising, ash drifting, burning cinders
--      thrown up now and then, sparks on each pulse;
--   F. the core's light: the egg's own lava cracks heat toward white-gold on each pulse, and a low
--      warm light.
-- On a pulse the aura speeds up, the comets throw sprays of sparks, the rocks are thrown out, flames
-- surge and the vents erupt, each a little after the last. While a hatch gathers, the rocks are pushed out and
-- energy is drawn in; on the burst everything erupts.
RECIPES.InfernoEgg = function(aura)
    local CRIMSON, MOLTEN, LAVA, GOLD = rgb(160, 22, 12), rgb(255, 90, 20), rgb(255, 175, 55), rgb(255, 215, 120)
    local C = 1.9                                    -- the egg stands 3.8 studs; its broken chunks fly off to its right
    set(aura.model, nil, {
        Gather = 1.8, Tint = rgb(255, 80, 20), Breath = 0.12, BreathPeriod = 3.2,
        PulseInterval = 6, PulseJitter = 1.5, PulseSpeed = 0.9, PulseGlow = 0.6, PulseEggGlow = rgb(255, 205, 110),
        -- settings, to tune by hand
        Intensity = 1, Density = 1, OrbitSpeed = 1, LightIntensity = 1, Visible = true,
    })
    local fire = colors({ { 0, LAVA }, { 0.45, MOLTEN }, { 1, CRIMSON } })

    -- A. spark comets: three heads racing round the egg on tilted paths, each at its own speed and
    -- direction, shedding a stream of hot sparks that hang back and fall, so the paths draw rings of
    -- sparks rather than solid bands; each throws a spray on the pulse and is drawn in on a hatch.
    -- (Attachments, so they sit on the Root.) The sparks use our spark texture, which has real alpha:
    -- the library's dots are white on black, so they only work fully additive, and over a bright sky
    -- additive orange turns pink and white. Camera-facing: motion-aligned particles do not render here.
    local sparkColors = colors({ { 0, rgb(255, 215, 90) }, { 0.35, rgb(255, 130, 25) }, { 0.75, rgb(230, 50, 12) }, { 1, rgb(140, 18, 8) } })
    for k, o in { -- orbit deg/s, radius, height, tilt x, tilt z, phase, rate, pulse delay
        { 95, 2.65, C + 0.15, -16, 10, 0, 44, 0.1 },
        { -75, 2.95, C - 0.4, 22, -18, 130, 38, 0.3 },
        { 120, 2.3, C + 1.05, 30, -25, 250, 32, 0.2 },
    } do
        local head = attachment(aura, "Comet" .. k, CFrame.new(0, o[3], o[2]))
        set(head, nil, { Orbit = o[1], Radius = o[2], Height = o[3], Tilt = Vector3.new(o[4], 0, o[5]), Phase = o[6],
            Bob = 0.12, BobPeriod = 2.5 + 0.7 * k, GatherPull = 0.45, PulseReach = 0.35, PulseDelay = o[8] })
        finish(emitter("Sparks", {
            Texture = T.Spark, Speed = NumberRange.new(0.2, 1.1), SpreadAngle = Vector2.new(180, 180), Drag = 2.2,
            Acceleration = Vector3.new(0, -1.6, 0), Lifetime = NumberRange.new(0.6, 1.1), Rate = o[7], Rotation = NumberRange.new(0, 360),
            Size = seq({ { 0, 0.3, 0.07 }, { 0.6, 0.2, 0.05 }, { 1, 0 } }), Color = sparkColors,
            Transparency = seq({ { 0, 0 }, { 0.7, 0.15 }, { 1, 1 } }), LightEmission = 0.35, Brightness = 2.2,
        }, { PulseEmit = 12, PulseDelay = o[8], HatchEmit = 16 }), head)
        finish(emitter("Flare", { -- the comet's hot head
            Texture = T.Spark, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.12, 0.18), Rate = 24,
            Size = seq({ { 0, 0.36, 0.06 }, { 1, 0.2 } }), Color = ColorSequence.new(rgb(255, 200, 80)),
            Transparency = seq({ { 0, 0.2 }, { 1, 1 } }), LightEmission = 0.5, Brightness = 2.5,
        }), head)
    end

    -- B. magma fragments (assets/eggs/InfernoFragments.fbx, stored by storeMeshes)
    local meshes = ServerStorage:FindFirstChild("AuraMeshes")
    local source = meshes and meshes:FindFirstChild("InfernoFragments")
    if source then
        local rocks = group(aura, "MagmaFragments")
        -- the nearest neighbouring egg (the Phoenix Altar's stands are 5.9 studs apart): the rocks pull in
        -- as they pass it, so they never cut into it. Swept in Play over every angle, bob, pulse and hatch
        -- push against both eggs' real surfaces: at least 0.33 studs clear of each.
        local avoidAngle, nearest
        local stands = aura.egg and aura.egg.Parent.Parent
        for _, stand in stands and stands:GetChildren() or {} do
            local egg = stand:FindFirstChild("Egg")
            if egg and egg ~= aura.egg then
                local rel = aura.root.CFrame:PointToObjectSpace(egg.Position)
                local d = Vector2.new(rel.X, rel.Z).Magnitude
                if not nearest or d < nearest then
                    nearest, avoidAngle = d, math.deg(math.atan2(rel.Z, rel.X))
                end
            end
        end
        for k, o in { -- orbit deg/s, radius, height, phase, bob, bob period, tumble (deg/s), pulse delay
            { 9, 3.05, C + 1.7, 20, 0.3, 4.2, Vector3.new(25, 40, 10), 0.25 },
            { -6, 3.25, C + 0.4, 85, 0.25, 5.1, Vector3.new(-15, 22, 35), 0.45 },
            { 12, 3.15, C - 0.7, 150, 0.35, 3.6, Vector3.new(40, -18, 20), 0.3 },
            { -8, 3.2, C + 1.1, 215, 0.2, 6.0, Vector3.new(10, 30, -25), 0.6 },
            { 7, 3.1, C - 0.2, 280, 0.3, 4.7, Vector3.new(-35, 15, 45), 0.4 },
            { -11, 3.05, C + 2.2, 330, 0.25, 3.9, Vector3.new(50, -30, 15), 0.2 },
        } do
            local body = source:FindFirstChild("Fragment" .. k)
            local core = source:FindFirstChild("Fragment" .. k .. "_Glow_ff5a14")
            if body then
                local rock = body:Clone()
                rock.Name = "Fragment" .. k
                local r = math.rad(o[4])
                rock.CFrame = aura.root.CFrame * CFrame.new(math.cos(r) * o[2], o[3], math.sin(r) * o[2]) * CFrame.Angles(r, 2 * r, 0)
                if core then
                    local glow = core:Clone()
                    glow.Name = "Core"
                    glow.CFrame = rock.CFrame * body.CFrame:ToObjectSpace(core.CFrame)
                    glow.Parent = rock
                end
                set(rock, nil, { Orbit = o[1], Radius = o[2], Height = o[3], Phase = o[4], Bob = o[5], BobPeriod = o[6],
                    Tumble = o[7], PulseReach = 0.7, PulseDelay = o[8], GatherPull = -0.45,
                    AvoidAngle = avoidAngle, AvoidRadius = avoidAngle and 3.05 or nil })
                finish(emitter("Embers", {
                    Texture = T.Dot, Speed = NumberRange.new(0.3, 0.8), SpreadAngle = Vector2.new(180, 180), Drag = 1,
                    Acceleration = Vector3.new(0, 1.4, 0), Lifetime = NumberRange.new(0.6, 1.1), Rate = 0.8,
                    Size = seq({ { 0, 0.12, 0.04 }, { 1, 0 } }), Color = ColorSequence.new(LAVA, MOLTEN), Brightness = 3,
                    Transparency = seq({ { 0, 0 }, { 1, 0.5 } }),
                }, { PulseEmit = 3, PulseDelay = o[8] }), rock)
                rock.Parent = rocks
            end
        end
    else
        warn("InfernoEgg aura: no ServerStorage.AuraMeshes.InfernoFragments yet (import assets/eggs/InfernoFragments.fbx, then EggAuraVFX.storeMeshes)")
    end

    -- C. the flame vortex: four molten ribbons on their own spiralling paths
    local vortex = group(aura, "FlameVortex")
    for k, o in { -- orbit deg/s, radius, height, bob, bob period, tilt x, tilt z, half width, pulse delay
        { 85, 2.2, C - 0.9, 1.1, 2.6, 8, -6, 0.14, 0.05 },
        { -70, 2.4, C - 0.3, 1.3, 3.1, -10, 12, 0.17, 0.2 },
        { 100, 2.15, C - 1.2, 0.9, 2.2, 14, 4, 0.12, 0.12 },
        { -60, 2.5, C + 0.2, 1.2, 3.4, -6, -14, 0.15, 0.32 },
    } do
        local trail, head = arc(aura, "Ribbon" .. k, { Orbit = o[1], Radius = o[2], Height = o[3], Phase = k * 90 + 15,
            Bob = o[4], BobPeriod = o[5], Tilt = Vector3.new(o[6], 0, o[7]), GatherPull = 0.35 }, o[8], {
            Texture = T.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.32 + 0.04 * k, LightEmission = 0.2,
            Brightness = 3, Color = colors({ { 0, rgb(255, 170, 40) }, { 0.35, rgb(255, 80, 15) }, { 1, rgb(150, 15, 5) } }),
            Transparency = seq({ { 0, 0.05 }, { 0.6, 0.35 }, { 1, 1 } }), WidthScale = seq({ { 0, 1 }, { 0.35, 0.7 }, { 1, 0 } }),
        })
        trail.Parent = vortex
        finish(emitter("Licks", {
            Texture = T.FlameTongue, Speed = NumberRange.new(0.4, 0.9), SpreadAngle = Vector2.new(20, 20), Drag = 0.8,
            Acceleration = Vector3.new(0, 3, 0), Lifetime = NumberRange.new(0.3, 0.5), Rate = 7, Rotation = NumberRange.new(-15, 15),
            RotSpeed = NumberRange.new(-40, 40), Size = seq({ { 0, 0.3, 0.08 }, { 0.3, 0.55, 0.1 }, { 1, 0.15 } }), Color = fire,
            Transparency = seq({ { 0, 1 }, { 0.12, 0.1 }, { 0.7, 0.35 }, { 1, 1 } }), LightEmission = 0.3, Brightness = 3,
        }, { PulseEmit = 8, PulseDelay = o[9] }), head)
        finish(emitter("Sparks", {
            Texture = T.Dot, Speed = NumberRange.new(0.6, 1.4), SpreadAngle = Vector2.new(40, 40), Drag = 0.6,
            Acceleration = Vector3.new(0.3, 3.2, 0), Lifetime = NumberRange.new(0.6, 1.1), Rate = 2.5,
            Size = seq({ { 0, 0.1, 0.04 }, { 1, 0 } }), Color = ColorSequence.new(GOLD, MOLTEN),
            Transparency = seq({ { 0, 0 }, { 1, 0.4 } }), Brightness = 3,
        }), aura.root[("Ribbon%dBottom"):format(k)])
    end

    -- D. beneath it: ripples of heat and three vents (the caldera sigil, the crust ring and the glow
    -- ring under the egg were removed at the owner's request)
    local ground = group(aura, "GroundFormation")
    local heat = ripple(aura, rgb(255, 110, 40), 7, 3)
    heat:SetAttribute("PulseEmit", 1)
    heat:SetAttribute("PulseDelay", 0.1)
    heat.Parent = ground
    for k, ang in { 125, 245, 5 } do -- three vents round the seal, erupting in turn
        local r = math.rad(ang)
        local vent = attachment(aura, "Vent" .. k, CFrame.new(math.cos(r) * 2.25, aura.rim + 0.15, math.sin(r) * 2.25))
        local delay = 0.35 + 0.2 * k
        finish(emitter("Eruption", {
            Texture = T.SmallGlow, Speed = NumberRange.new(4, 6.5), SpreadAngle = Vector2.new(14, 14), Drag = 0.3,
            Acceleration = Vector3.new(0, -13, 0), Lifetime = NumberRange.new(0.55, 0.9), Rate = 0,
            Size = seq({ { 0, 0.32, 0.1 }, { 1, 0.12 } }), Color = colors({ { 0, GOLD }, { 0.4, MOLTEN }, { 1, CRIMSON } }),
            Transparency = seq({ { 0, 0 }, { 0.8, 0.2 }, { 1, 1 } }), Brightness = 3,
        }, { PulseEmit = 7, PulseDelay = delay, HatchEmit = 12 }), vent)
        finish(emitter("VentFlame", {
            Texture = T.FlameTongue, Speed = NumberRange.new(0.8, 1.6), SpreadAngle = Vector2.new(10, 10),
            Acceleration = Vector3.new(0, 2.5, 0), Lifetime = NumberRange.new(0.3, 0.55), Rate = 1.2 + 0.3 * k,
            Size = seq({ { 0, 0.25 }, { 0.35, 0.5, 0.1 }, { 1, 0.15 } }), Color = fire, LightEmission = 0.3, Brightness = 3,
            Transparency = seq({ { 0, 1 }, { 0.12, 0.1 }, { 0.75, 0.3 }, { 1, 1 } }),
        }, { PulseEmit = 4, PulseDelay = delay }), vent)
        -- (dark smoke after each eruption was tried: it drifted up into a grey smudge beside the next
        -- stand's egg and added nothing, so the contrast comes from the crust and the rocks)
    end

    -- E. embers, ash, cinders, pulse sparks
    local air = group(aura, "Atmosphere")
    local area = part(aura, "EmberArea", CFrame.new(0, aura.rim + 0.2, 0), Vector3.new(4.4, 0.2, 4.4))
    finish(emitter("Embers", {
        Texture = T.Dot, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.8, 2.2), SpreadAngle = Vector2.new(35, 35),
        Acceleration = Vector3.new(0.2, 1.5, -0.1), Drag = 0.7, Lifetime = NumberRange.new(1.2, 2.6), Rate = 6,
        Size = seq({ { 0, 0.2, 0.07 }, { 0.5, 0.14, 0.05 }, { 1, 0 } }), Color = colors({ { 0, GOLD }, { 0.5, MOLTEN }, { 1, CRIMSON } }),
        Transparency = seq({ { 0, 0 }, { 0.4, 0.15 }, { 0.6, 0.05 }, { 1, 1 } }), Brightness = 3,
    }, { HatchEmit = 30 }), area)
    finish(emitter("Cinders", { -- burning fragments thrown up now and then
        Texture = T.Rock, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(3.5, 5.5), SpreadAngle = Vector2.new(25, 25),
        Acceleration = Vector3.new(0, -8, 0), Lifetime = NumberRange.new(1, 1.4), Rate = 0.4, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-220, 220), Size = seq({ { 0, 0.3, 0.1 }, { 1, 0.24 } }), LightEmission = 0, Brightness = 1,
        Transparency = seq({ { 0, 0 }, { 0.85, 0 }, { 1, 1 } }),
    }, { PulseEmit = 2, PulseDelay = 0.5, HatchEmit = 6 }), area)
    area.Parent = air
    local ashArea = part(aura, "AshArea", CFrame.new(0, C + 0.6, 0), Vector3.new(6.2, 4.6, 6.2))
    finish(emitter("Ash", {
        Texture = T.Ash, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.1, 0.4), SpreadAngle = Vector2.new(180, 180), Drag = 0.5, Acceleration = Vector3.new(0.18, 0.22, 0.06),
        Lifetime = NumberRange.new(3, 5), Rate = 4, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-80, 80),
        Size = seq({ { 0, 0.12, 0.05 }, { 1, 0.1, 0.04 } }), Color = colors({ { 0, rgb(70, 62, 60) }, { 1, rgb(40, 36, 36) } }),
        LightEmission = 0, LightInfluence = 0.2, -- lit by the sky any more and it reads as pale glass Transparency = seq({ { 0, 1 }, { 0.15, 0.25 }, { 0.8, 0.4 }, { 1, 1 } }),
    }), ashArea)
    ashArea.Parent = air
    -- sparks spitting out of the egg's own cracks: from the surface of a sphere the size of the egg's
    -- glowing core, outward, falling; a burst of them on each pulse
    local glowCore
    for _, d in aura.egg and aura.egg.Parent:GetChildren() or {} do
        if d:IsA("BasePart") and d.Name:find("_Glow_") then
            glowCore = d
        end
    end
    if glowCore then
        local cracks = part(aura, "CrackSparks", aura.root.CFrame:ToObjectSpace(glowCore.CFrame), glowCore.Size * 1.02)
        finish(emitter("Spit", {
            Texture = T.Spark, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, Speed = NumberRange.new(1.5, 3.2), Drag = 1.2,
            Acceleration = Vector3.new(0, -4.5, 0), Lifetime = NumberRange.new(0.5, 0.9), Rate = 14, Rotation = NumberRange.new(0, 360),
            Size = seq({ { 0, 0.26, 0.06 }, { 0.6, 0.17, 0.04 }, { 1, 0 } }), Color = sparkColors,
            Transparency = seq({ { 0, 0 }, { 0.7, 0.15 }, { 1, 1 } }), LightEmission = 0.35, Brightness = 2.2,
        }, { PulseEmit = 30, PulseDelay = 0.05, HatchEmit = 40 }), cracks)
        cracks.Parent = air
    end
    local heart = attachment(aura, "Heart", CFrame.new(0, C, 0))
    finish(emitter("PulseSparks", {
        Texture = T.Cross, Speed = NumberRange.new(6, 10), SpreadAngle = Vector2.new(180, 180), Drag = 3.5,
        Lifetime = NumberRange.new(0.4, 0.7), Rate = 0, Rotation = NumberRange.new(0, 90), RotSpeed = NumberRange.new(-180, 180),
        Size = seq({ { 0, 0.3, 0.1 }, { 1, 0 } }), Color = ColorSequence.new(GOLD, MOLTEN), Brightness = 3,
        Transparency = seq({ { 0, 0 }, { 1, 0.3 } }),
    }, { PulseEmit = 14, HatchEmit = 30 }), heart)

    -- F. the core's light: the egg's own lava cracks (they heat on each pulse: PulseEggGlow) and a
    -- low warm light on the Root. No glow halo behind the egg: the owner keeps the light to the
    -- cracks. The stand already lights the egg, so this light stays low.
    light(aura, rgb(255, 120, 45), 12, 0.5)

    -- the hatch: energy drawn in, then the eruption
    local gathering = drawIn(aura, T.Dot, rgb(255, 150, 70), 0.35, 60)
    gathering.Parent.Parent = air -- its sphere part
    burst(aura, rgb(255, 160, 80), 10)
    finish(emitter("Eruption", {
        Texture = T.Fireburst, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.7), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, 2 }, { 0.3, 9 }, { 1, 10.5 } }), Transparency = seq({ { 0, 0 }, { 0.6, 0.3 }, { 1, 1 } }), Brightness = 2,
    }, { HatchEmit = 2 }), attachment(aura, "EruptionCore", CFrame.new(0, C, 0)))
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
            RECIPES[eggId]({ model = aura, root = root, rim = rimHeight(stand, origin), egg = stand:FindFirstChild("Egg") })
            CollectionService:AddTag(aura, TAG)
            aura.Parent = folder
            table.insert(built, eggId)
        end
    end
    folder.Parent = model
    return built
end

return EggAuraVFX

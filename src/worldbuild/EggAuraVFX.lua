-- Build-time only: builds each egg stand's aura in the Workspace from particle emitters, trails,
-- beams, glowing image planes and lights, so it can be tuned in Studio and saved in the place.
-- Require a clone, as with WorldBuilder:
--
--   local VFX = require(game.ServerStorage.WorldBuild.EggAuraVFX:Clone())
--   VFX.build("Yggdrasil")   -- (re)builds FloatingIslands.Yggdrasil.EggAuras
--
-- Each aura is a Model tagged "EggAura" (attribute EggId) whose Root part sits at the egg's resting
-- point, facing the front of the stand. The client (src/client/Auras/EggAura.lua) animates it from
-- these attributes:
--   Attachment  Orbit (deg/s), Radius, Height, Tilt (Vector3 deg), Phase (deg), Bob (studs), BobPeriod (s)
--   Part        Spin (deg/s); Wobble (deg), WobblePeriod (s), Phase (deg); SwellScale, GatherScale;
--               Ripple (s), HatchEmit (ripples on the hatch)
--   ImageLabel  Sway (deg), SwayPeriod (s), Phase (deg)
--   Emitter     HatchEmit (particles on the hatch burst), GatherRate (rate while a hatch gathers)
--   Model       Gather (s), Tint (glow while hatching), Breath (fraction), BreathPeriod (s)
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
    LotusMandala = "rbxassetid://12403102126",   -- VS
    OrnateMandala = "rbxassetid://12402928708",  -- VS
    BrokenRing = "rbxassetid://14850595833",     -- VS
    SoftRing = "rbxassetid://16505105356",       -- VS
    WindArc = "rbxassetid://13131393513",        -- VS
    SoftGlow = "rbxassetid://187823474",         -- VS
    SmallGlow = "rbxassetid://6673021984",       -- VS
    Dot = "rbxassetid://11037546803",            -- VS
    Star4 = "rbxassetid://5946093983",           -- VS
    Cross = "rbxassetid://6909741538",           -- VS
    Burst = "rbxassetid://15773612675",          -- VS
    Flare = "rbxassetid://14054628491",          -- PDS
    Fog = "rbxassetid://14050223758",            -- PDS
    GlitterFog = "rbxassetid://14049414463",     -- PDS
    Ribbon = "rbxassetid://99893839045856",      -- QA
    WindRose = "rbxassetid://98026121929653",    -- QA
    Wuxing = "rbxassetid://84064944874395",      -- QA
    Cloud = "rbxassetid://133757754897450",      -- QA
    Feather = "rbxassetid://131662968027624",    -- QA
    Crystal = "rbxassetid://91364093647932",     -- QA
    QiRing = "rbxassetid://136096136498575",     -- QA
    ElementBand = "rbxassetid://76030932893410", -- QA
    Stream = "rbxassetid://129943358163696",     -- QA: tiles along a beam
    -- Jade Grove
    Leaf = "rbxassetid://6475162564",            -- VS
    GlowRing = "rbxassetid://12386390257",       -- VS
    JadeLeaf = "rbxassetid://123839325562421",   -- QA
    BlossomSigil = "rbxassetid://104690771337528", -- QA
    TreeRings = "rbxassetid://97314964323991",   -- QA
    Petal = "rbxassetid://122668143134554",      -- QA
    Blossom = "rbxassetid://100572808754853",    -- QA
    Vortex = "rbxassetid://82549101989057",      -- QA
    BloomLight = "rbxassetid://80600586960187",  -- QA
    -- (VFX Studio's swirl vortex and radial burst have no alpha and show as black squares on a
    -- SurfaceGui, so ours replace them)
    -- Ember Peak
    Fireburst = "rbxassetid://15811794808",      -- VS
    GoldFeather = "rbxassetid://7244584563",     -- VS
    Lava = "rbxassetid://1112726928",            -- VS: tiles along a beam
    Fissure = "rbxassetid://139285675827924",    -- QA
    CrystalForge = "rbxassetid://113317746351445", -- QA
    PhoenixSigil = "rbxassetid://114119118263415", -- QA
    FlameTongue = "rbxassetid://86422452019290", -- QA
    Rock = "rbxassetid://137469228900771",       -- QA
    Vessel = "rbxassetid://80498467493439",      -- QA: coloured
    CrustRing = "rbxassetid://125397922605343",  -- QA: coloured
    Ash = "rbxassetid://117440820612388",        -- QA
    FireMain = "rbxasset://textures/particles/fire_main.dds",
    FireSparks = "rbxasset://textures/particles/fire_sparks_main.dds",
    Spark = "rbxassetid://121337217386887",      -- QA: real alpha, keeps its colour on a bright sky
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

-- Flat elements are glowing images on SurfaceGuis: flat (VelocityPerpendicular) particles do not
-- render in these auras (tested in Play). The image fills 1/HEADROOM of its part, leaving room to swell.
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

-- A soft glow round the egg, drawn behind it (ZOffset) so it never veils the egg's design.
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

-- The hatch's burst: a starburst flash (or `texture`, such as a soft bloom).
local function burst(aura, color, size, texture)
    local a = attachment(aura, "Burst", CFrame.new(0, EGG_CENTRE, 0))
    finish(emitter("Flash", {
        Texture = texture or T.Flare, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.4), Rate = 0, Rotation = NumberRange.new(0, 360),
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

-- An energy stream: a beam from a point sweeping round the rim to `apex` above the egg. Both ends
-- point their axis up, so the beam leaves the rim straight up and reaches the apex from below.
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

-- Beginner Qi Egg: calm, welcoming Qi, soft and slow. Two wisps of Qi glide round the egg shedding
-- dust, motes rise like breath, soft twinkles, a soft halo and a gentle updraft.
RECIPES.BeginnerQiEgg = function(aura)
    local QI, PALE, DEEP = rgb(80, 195, 255), rgb(200, 240, 255), rgb(40, 120, 255)
    aura.model:SetAttribute("Gather", 1.3)
    aura.model:SetAttribute("Tint", rgb(120, 210, 255))
    set(aura.model, nil, { Breath = 0.15, BreathPeriod = 5 })
    for k, arcOrbit in { { Orbit = 55, Radius = 2.4, Bob = 0.45, BobPeriod = 4.2 }, { Orbit = -40, Radius = 3.0, Bob = 0.6, BobPeriod = 5.4 } } do
        arcOrbit.Height, arcOrbit.Phase = EGG_CENTRE + 0.8, (k - 1) * 180   -- any lower and the stand's wide bowl hides them
        arcOrbit.Tilt = Vector3.new(k == 1 and 20 or -26, 0, k == 1 and 0 or 12)
        local _, head = arc(aura, "QiArc" .. k, arcOrbit, 0.45, { -- the deep blue egg takes more light than the pale ones
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.8, Brightness = 3, LightEmission = 0.7,
            Color = colors({ { 0, PALE }, { 0.5, QI }, { 1, DEEP } }), Transparency = seq({ { 0, 0.05 }, { 0.5, 0.25 }, { 1, 0.7 } }),
            WidthScale = seq({ { 0, 0.6 }, { 0.3, 1 }, { 1, 0.5 } }),
        })
        finish(emitter("ArcDust", {
            Texture = T.Dot, Rate = 14, Lifetime = NumberRange.new(0.8, 1.4), Speed = NumberRange.new(0.2, 0.6),
            SpreadAngle = Vector2.new(180, 180), Drag = 1.5, Acceleration = Vector3.new(0, 0.8, 0),
            Size = seq({ { 0, 0.28 }, { 1, 0 } }), Color = ColorSequence.new(PALE, QI), Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 2,
        }, { HatchEmit = 12 }), head)
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
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.2, 0.5), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.3, 0),
        Lifetime = NumberRange.new(1.4, 2), Rate = 3, Size = seq({ { 0, 0 }, { 0.5, 0.45 }, { 1, 0 } }),
        Color = ColorSequence.new(PALE), Transparency = NumberSequence.new(0.3), Brightness = 2, LightEmission = 0.6,
    }, { HatchEmit = 16 }), glints)
    halo(aura, QI, 6.5, 0.78)
    column(aura, QI, PALE, 0.35, 4.2)
    mist(motes, QI, PALE, 4, 1)
    drawIn(aura, T.Dot, PALE, 0.5, 60)
    burst(aura, rgb(170, 230, 255), 9, T.SoftGlow)
    light(aura, QI, 13, 1.3)
end

-- Spirit Breeze Egg: a soft breeze. Three wisps of wind drift round it on a slow helix, clouds
-- billow off the bowl's lip and feathers ride a gentle updraught under a faint halo.
RECIPES.SpiritBreezeEgg = function(aura)
    local SKY, WHITE = rgb(110, 215, 255), rgb(225, 245, 255)
    aura.model:SetAttribute("Gather", 1.2)
    aura.model:SetAttribute("Tint", rgb(170, 230, 255))
    set(aura.model, nil, { Breath = 0.15, BreathPeriod = 5 })
    for k = 1, 3 do
        local _, head = arc(aura, "Wind" .. k, { Orbit = 105 - k * 15, Radius = 1.5 + 0.6 * k, Height = EGG_CENTRE, Phase = (k - 1) * 120,
            Bob = 0.9 + 0.25 * k, BobPeriod = 3.2 + 0.7 * k }, 0.3, {
            -- LightEmission over 0.3 or Brightness over 2 washes the pale egg white as a wisp crosses it
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.6, Brightness = 2, LightEmission = 0.3,
            Color = colors({ { 0, rgb(240, 250, 255) }, { 0.35, rgb(130, 210, 255) }, { 1, rgb(70, 160, 240) } }),
            Transparency = seq({ { 0, 0.25 }, { 0.5, 0.4 }, { 1, 0.75 } }), WidthScale = seq({ { 0, 0.6 }, { 0.3, 1 }, { 1, 0.5 } }),
        })
        if k == 1 then
            finish(emitter("Shed", {
                Texture = T.Feather, Rate = 2, Lifetime = NumberRange.new(1.5, 2.2), Speed = NumberRange.new(0.3, 0.8),
                SpreadAngle = Vector2.new(180, 180), Drag = 1.2, Acceleration = Vector3.new(0, -0.3, 0),
                Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-50, 50), Size = seq({ { 0, 0.4 }, { 1, 0.5 } }),
                Color = ColorSequence.new(WHITE), Transparency = seq({ { 0, 0.1 }, { 0.7, 0.3 }, { 1, 1 } }), LightEmission = 0.6,
            }), head)
        end
    end
    local base = part(aura, "CloudArea", CFrame.new(0, aura.rim + 0.8, 0), Vector3.new(5.5, 0.2, 5.5)) -- above the bowl's lip, which hid them
    finish(emitter("Clouds", {
        Texture = T.Cloud, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.3, 0.6),
        Lifetime = NumberRange.new(4, 5), Rate = 1.2, Drag = 0.4, SpreadAngle = Vector2.new(20, 20),
        Rotation = NumberRange.new(-8, 8), RotSpeed = NumberRange.new(-6, 6),
        Size = seq({ { 0, 1 }, { 0.4, 2 }, { 1, 2.4 } }), LightEmission = 0.2,
        Color = colors({ { 0, WHITE }, { 1, rgb(140, 210, 255) } }), Transparency = seq({ { 0, 1 }, { 0.2, 0.35 }, { 1, 1 } }),
    }, { HatchEmit = 12 }), base)
    finish(emitter("Feathers", {
        Texture = T.Feather, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.7, 1.2), SpreadAngle = Vector2.new(35, 35),
        Acceleration = Vector3.new(0.3, 0.2, 0), Drag = 0.5,
        Lifetime = NumberRange.new(3.5, 4.5), Rate = 2, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-50, 50),
        Size = seq({ { 0, 0.45 }, { 1, 0.6 } }), LightEmission = 0.25, Color = colors({ { 0, WHITE }, { 1, SKY } }),
        Transparency = seq({ { 0, 1 }, { 0.15, 0.1 }, { 1, 1 } }),
    }, { HatchEmit = 20 }), base)
    halo(aura, rgb(150, 225, 255), 6, 0.86)
    column(aura, rgb(150, 220, 255), rgb(235, 248, 255), 0.45, 4)
    drawIn(aura, T.Feather, WHITE, 0.7, 30)
    burst(aura, rgb(200, 240, 255), 8, T.SoftGlow)
    light(aura, SKY, 12, 0.55) -- the pale egg washes out under a stronger light
end

-- Elemental Core Egg: concentrated elements. Four element streams rise off the rim and meet in a
-- glow above the crown, four element orbs glide round with soft tails, and on the hatch the core gem flares.
local ELEMENTS = { rgb(40, 225, 255), rgb(255, 195, 60), rgb(70, 120, 255), rgb(255, 150, 40) }
RECIPES.ElementalCoreEgg = function(aura)
    local CORE, GOLD = rgb(50, 215, 255), rgb(255, 205, 90)
    aura.model:SetAttribute("Gather", 1.4)
    aura.model:SetAttribute("Tint", rgb(90, 220, 255))
    set(aura.model, nil, { Breath = 0.12, BreathPeriod = 4 })
    local apex = attachment(aura, "Apex", CFrame.new(0, EGG_CENTRE + 2.6, 0) * UP_AXIS)
    for k, color in ELEMENTS do
        stream(aura, "Stream" .. k, { Orbit = 12, Radius = 3.5, Height = aura.rim + 0.5, Phase = 90 * (k - 1) + 45 }, apex, {
            -- soft glow: the braided stream texture read as spiky fringes
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, CurveSize0 = 3, CurveSize1 = 1.5, Width0 = 0.9, Width1 = 0.3,
            Brightness = 2, LightEmission = 0.45,
            Color = colors({ { 0, color }, { 1, color:Lerp(rgb(255, 255, 255), 0.45) } }),
            Transparency = seq({ { 0, 1 }, { 0.15, 0.25 }, { 0.8, 0.3 }, { 1, 0.8 } }),
        })
    end
    finish(emitter("ApexGlow", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(1.4, 1.8), Rate = 2,
        Size = seq({ { 0, 0.8 }, { 0.5, 1.4 }, { 1, 1.2 } }), Color = ColorSequence.new(rgb(150, 235, 255)),
        Transparency = seq({ { 0, 1 }, { 0.4, 0.45 }, { 1, 1 } }), Brightness = 2, LightEmission = 0.6,
    }, { HatchEmit = 6 }), apex)
    for k, color in ELEMENTS do
        local orbit = { Orbit = ({ 60, -48, 42, -64 })[k], Radius = ({ 2.6, 3.4, 2.9, 3.6 })[k], Height = EGG_CENTRE + (k % 2 == 0 and 0.9 or -0.5),
            Tilt = Vector3.new(({ 15, -20, 25, -10 })[k], 0, 0), Phase = 90 * (k - 1),
            Bob = ({ 0.3, 0.5, 0.4, 0.35 })[k], BobPeriod = ({ 2.2, 2.9, 3.4, 2.6 })[k] }
        local _, head = arc(aura, "OrbTrail" .. k, orbit, 0.18, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.2, Brightness = 2, LightEmission = 0.4,
            Color = ColorSequence.new(color), Transparency = seq({ { 0, 0.15 }, { 0.5, 0.45 }, { 1, 1 } }), WidthScale = seq({ { 0, 1 }, { 1, 0.3 } }),
        })
        finish(emitter("Orb" .. k, {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 12,
            Size = seq({ { 0, 0.55 }, { 1, 0.2 } }), Color = ColorSequence.new(color), Transparency = seq({ { 0, 0.2 }, { 1, 1 } }),
            Brightness = 2, LightEmission = 0.5,
        }), head)
    end
    local motes = part(aura, "MoteArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(6, 0.2, 6))
    for name, color in { MotesBlue = rgb(90, 200, 255), MotesGold = GOLD } do
        finish(emitter(name, {
            Texture = T.Dot, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.8, 1.4), SpreadAngle = Vector2.new(30, 30),
            Acceleration = Vector3.new(0, 0.5, 0), Drag = 0.5,
            Lifetime = NumberRange.new(2.2, 3.2), Rate = 5, Size = seq({ { 0, 0 }, { 0.2, 0.3 }, { 1, 0 } }), Brightness = 3,
            Color = ColorSequence.new(color), Transparency = seq({ { 0, 0.05 }, { 1, 1 } }),
        }, { HatchEmit = 15 }), motes)
    end
    local sparks = part(aura, "SparkArea", CFrame.new(0, EGG_CENTRE, 0), Vector3.new(3.2, 3.6, 3.2))
    finish(emitter("Sparks", {
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        Speed = NumberRange.new(0.3, 0.6), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(1.2, 1.8), Rate = 4,
        Size = seq({ { 0, 0 }, { 0.4, 0.4 }, { 1, 0 } }), Color = colors({ { 0, rgb(200, 245, 255) }, { 1, CORE } }),
        Transparency = NumberSequence.new(0.25), Brightness = 2, LightEmission = 0.6,
    }, { HatchEmit = 30 }), sparks)
    local front = attachment(aura, "CoreFlare", CFrame.new(0, EGG_CENTRE - 0.05, -1.5))
    finish(emitter("CoreFlare", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, 1 }, { 0.3, 4.5 }, { 1, 5 } }), Color = ColorSequence.new(CORE), Transparency = seq({ { 0, 0 }, { 1, 1 } }), Brightness = 3,
    }, { HatchEmit = 2 }), front)
    halo(aura, CORE, 7, 0.76)
    drawIn(aura, T.SoftGlow, rgb(170, 235, 255), 0.5, 50)
    burst(aura, rgb(160, 235, 255), 11, T.SoftGlow)
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
        Transparency = seq({ { 0, 0.6 }, { 0.12, 0.05 }, { 0.7, 0.2 }, { 1, 1 } }), LightEmission = 0.15, Brightness = 1.6, -- solid, not glowing, so they read in daylight
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

-- Jade Spirit Egg: living jade. Three vines of light twine up from the rim to the crown, three
-- currents of Qi drift round shedding leaves, and jade motes rise among soft twinkles.
RECIPES.JadeSpiritEgg = function(aura)
    local JADE, MINT, DEEP = rgb(40, 220, 110), rgb(170, 255, 200), rgb(10, 140, 70)
    aura.model:SetAttribute("Gather", 1.3)
    aura.model:SetAttribute("Tint", rgb(70, 235, 130))
    set(aura.model, nil, { Breath = 0.18, BreathPeriod = 4.5 })
    -- the stands here are 7.5 studs apart: everything stays within about 3.3 studs of the egg
    for k = 1, 3 do
        tendril(aura, "Vine" .. k,
            { Orbit = 14, Radius = 2.2, Height = aura.rim + 0.15, Phase = (k - 1) * 120 },
            { Orbit = 14 + 22 * k, Radius = 0.9, Height = 4.2, Phase = (k - 1) * 120 + 150, Bob = 0.2, BobPeriod = 3 + k }, {
            -- soft glow (the braided stream read as spiky fringes); low emission keeps it green in daylight
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch,
            CurveSize0 = 1.8, CurveSize1 = 1.4, Width0 = 0.6, Width1 = 0.2, LightEmission = 0.35, Brightness = 2,
            Color = colors({ { 0, rgb(20, 150, 60) }, { 0.6, JADE }, { 1, rgb(150, 255, 190) } }),
            Transparency = seq({ { 0, 1 }, { 0.12, 0.2 }, { 0.85, 0.25 }, { 1, 1 } }),
        })
    end
    for k, c in { { 60, 2.3, 22, 0, 0.4, 4.4 }, { -48, 2.8, -18, 14, 0.6, 5.6 }, { 70, 3.1, 8, -20, 0.5, 3.8 } } do
        local _, head = arc(aura, "Current" .. k, { Orbit = c[1], Radius = c[2], Height = EGG_CENTRE, Tilt = Vector3.new(c[3], 0, c[4]),
            Phase = (k - 1) * 120, Bob = c[5], BobPeriod = c[6] }, 0.3, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.6, Brightness = 2, LightEmission = 0.35,
            Color = colors({ { 0, rgb(150, 255, 190) }, { 0.5, JADE }, { 1, DEEP } }), Transparency = seq({ { 0, 0.2 }, { 0.5, 0.4 }, { 1, 0.8 } }),
            WidthScale = seq({ { 0, 0.6 }, { 0.3, 1 }, { 1, 0.5 } }),
        })
        shed(head, "Leaves", T.Leaf, ColorSequence.new(rgb(90, 220, 90), rgb(20, 150, 70)), 3, { 0.35, 0.6, 0.5 }, 0.2).RotSpeed =
            NumberRange.new(-60, 60)
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
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.2, 0.5), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(1.4, 2), Rate = 3,
        Size = seq({ { 0, 0 }, { 0.5, 0.45 }, { 1, 0 } }), Color = ColorSequence.new(MINT),
        Transparency = NumberSequence.new(0.3), Brightness = 2, LightEmission = 0.6,
    }, { HatchEmit = 14 }), glints)
    halo(aura, JADE, 6.5, 0.78)
    column(aura, DEEP, MINT, 0.35, 4)
    mist(motes, JADE, MINT, 3, 0.9)
    drawIn(aura, T.Leaf, rgb(140, 240, 150), 0.6, 40)
    burst(aura, rgb(150, 255, 190), 9, T.SoftGlow)
    light(aura, JADE, 13, 1.2)
    -- fitted to the detailed egg (4.3 studs tall)
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

-- Bloomwood Egg: eternal blossom. Two streams of blossom wind drift round it shedding petals,
-- petals float up off the rim and drift back down, and golden pollen rises.
RECIPES.BloomwoodEgg = function(aura)
    local PINK, BLUSH, GOLDEN = rgb(255, 110, 190), rgb(255, 200, 230), rgb(255, 205, 110)
    aura.model:SetAttribute("Gather", 1.4)
    aura.model:SetAttribute("Tint", rgb(255, 140, 205))
    set(aura.model, nil, { Breath = 0.14, BreathPeriod = 6 })
    for k, c in { { 45, 2.5, 16, 0, 0.8, 4.4 }, { -36, 3.0, -12, 18, 0.6, 5.4 } } do
        local _, head = arc(aura, "Breeze" .. k, { Orbit = c[1], Radius = c[2], Height = EGG_CENTRE + 0.2, Tilt = Vector3.new(c[3], 0, c[4]),
            Phase = (k - 1) * 180, Bob = c[5], BobPeriod = c[6] }, 0.3, {
            -- soft glow: the ribbon texture read as a blocky band with hard ends
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.8, Brightness = 2, LightEmission = 0.3,
            Color = colors({ { 0, rgb(255, 170, 215) }, { 0.5, rgb(255, 90, 170) }, { 1, rgb(190, 50, 150) } }),
            Transparency = seq({ { 0, 0.2 }, { 0.5, 0.35 }, { 1, 0.75 } }), WidthScale = seq({ { 0, 0.6 }, { 0.3, 1 }, { 1, 0.5 } }),
        })
        shed(head, "Petals", T.Petal, ColorSequence.new(rgb(255, 140, 200), rgb(235, 80, 160)), 4, { 0.3, 0.48, 0.4 }, 0.3).RotSpeed =
            NumberRange.new(-60, 60)
    end
    local rim = part(aura, "PetalRim", CFrame.new(0, aura.rim + 0.2, 0), Vector3.new(4.4, 0.2, 4.4))
    finish(emitter("Fountain", {
        Texture = T.Petal, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(1.3, 1.9), SpreadAngle = Vector2.new(22, 22), Acceleration = Vector3.new(0, -0.6, 0), Drag = 0.9,
        Lifetime = NumberRange.new(3.2, 4.2), Rate = 4, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-60, 60),
        Size = seq({ { 0, 0.3 }, { 0.2, 0.48 }, { 1, 0.42 } }), Color = ColorSequence.new(rgb(255, 150, 205), rgb(235, 90, 165)),
        Transparency = seq({ { 0, 0.5 }, { 0.1, 0.05 }, { 0.75, 0.2 }, { 1, 1 } }), LightEmission = 0.15, Brightness = 1.6,
    }, { HatchEmit = 18 }), rim)
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
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.2, 0.5), SpreadAngle = Vector2.new(180, 180), Lifetime = NumberRange.new(1.4, 2), Rate = 3,
        Size = seq({ { 0, 0 }, { 0.5, 0.45 }, { 1, 0 } }), Color = ColorSequence.new(BLUSH),
        Transparency = seq({ { 0, 0.3 }, { 1, 0.3 } }), Brightness = 2,
    }, { HatchEmit = 14 }), glints)
    -- no halo: on the pale crystal egg it reads as a milky veil
    column(aura, rgb(255, 140, 200), BLUSH, 0.3, 4).Transparency = seq({ { 0, 1 }, { 0.2, 0.82 }, { 0.6, 0.88 }, { 1, 1 } })
    mist(pollen, PINK, BLUSH, 3, 0.8)
    drawIn(aura, T.Petal, BLUSH, 0.6, 40)
    burst(aura, rgb(255, 200, 230), 9, T.SoftGlow)
    light(aura, rgb(255, 120, 190), 13, 0.5)
    -- fitted to the detailed egg
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

-- Ancient Grove Egg: the world tree's heartbeat. Five roots of light climb into the egg, a spiral
-- of Qi climbs round it, four forest spirits wander on looping paths and leaves drift from its crowns.
RECIPES.AncientGroveEgg = function(aura)
    local LEAFG, SPIRIT, BARK = rgb(110, 240, 70), rgb(200, 255, 170), rgb(120, 200, 60)
    aura.model:SetAttribute("Gather", 1.6)
    aura.model:SetAttribute("Tint", rgb(130, 245, 90))
    set(aura.model, nil, { Breath = 0.16, BreathPeriod = 7 })
    -- the Jade Grove pedestals are cones of roots, about 2 studs below the egg 4 studs out
    local heart = attachment(aura, "Heart", CFrame.new(0, EGG_CENTRE * 0.8, 0) * UP_AXIS)
    for k = 1, 5 do
        stream(aura, "Root" .. k, { Orbit = 5, Radius = 3.9, Height = -2, Phase = (k - 1) * 72 + 20 }, heart, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, -- the braided stream read as spiky fringes
            CurveSize0 = 2.2, CurveSize1 = -0.4, Width0 = 0.85, Width1 = 0.35, Brightness = 2.5, LightEmission = 0.3,
            Color = colors({ { 0, rgb(230, 170, 40) }, { 0.5, rgb(120, 230, 50) }, { 1, rgb(190, 255, 140) } }),
            Transparency = seq({ { 0, 1 }, { 0.1, 0.2 }, { 0.85, 0.25 }, { 1, 1 } }),
        })
    end
    local spiralHead = attachment(aura, "SpiralHead", CFrame.new(0, EGG_CENTRE, 1.7))
    set(spiralHead, nil, { Orbit = 90, Radius = 1.95, Height = EGG_CENTRE, Bob = 1.2, BobPeriod = 7 })
    finish(emitter("Spiral", {
        Texture = T.Dot, Rate = 14, Lifetime = NumberRange.new(1.8, 2.4), Speed = NumberRange.new(0.05),
        Acceleration = Vector3.new(0, 0.6, 0), Size = seq({ { 0, 0.45 }, { 1, 0 } }), Brightness = 2,
        Color = ColorSequence.new(rgb(140, 255, 90), rgb(60, 210, 40)), Transparency = seq({ { 0, 0 }, { 1, 1 } }),
    }, { HatchEmit = 20 }), spiralHead)
    for k, w in { { 30, 3.0, 2.6, 18, 1.2, 5.4 }, { -36, 3.4, 3.6, -14, 0.9, 6.5 }, { 40, 2.8, 1.6, 26, 1.0, 4.8 }, { -26, 3.6, 4.4, -8, 1.4, 7.6 } } do
        local _, head = arc(aura, "Spirit" .. k, { Orbit = w[1], Radius = w[2], Height = w[3], Tilt = Vector3.new(w[4], 0, -w[4] * 0.5),
            Phase = (k - 1) * 90 + 45, Bob = w[5], BobPeriod = w[6] }, 0.16, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.8, Brightness = 2, LightEmission = 0.4,
            Color = colors({ { 0, SPIRIT }, { 1, LEAFG } }), Transparency = seq({ { 0, 0.15 }, { 0.5, 0.45 }, { 1, 0.9 } }),
            WidthScale = seq({ { 0, 1 }, { 1, 0.3 } }),
        })
        finish(emitter("Orb", {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 12,
            Size = seq({ { 0, 0.5 }, { 1, 0.15 } }), Color = ColorSequence.new(rgb(170, 255, 120)), Transparency = seq({ { 0, 0.25 }, { 1, 1 } }),
            Brightness = 2, LightEmission = 0.5,
        }), head)
    end
    local motes = part(aura, "MoteArea", CFrame.new(0, aura.rim + 0.15, 0), Vector3.new(7, 0.2, 7))
    halo(aura, LEAFG, 7.5, 0.74)
    column(aura, BARK, SPIRIT, 0.25, 5)
    mist(motes, LEAFG, SPIRIT, 3, 0.7)
    drawIn(aura, T.Leaf, rgb(170, 245, 120), 0.65, 45)
    burst(aura, rgb(190, 255, 150), 11, T.SoftGlow)
    light(aura, LEAFG, 15, 1.2)
    -- fitted to the detailed egg: light, fireflies and leaves from its five leaf crowns
    lift(aura, 0.15)
    local CROWNS = { { Vector3.new(1.661, 0.284, 0.304), 0.422 }, { Vector3.new(-1.753, 0.757, 0.581), 0.344 },
        { Vector3.new(0.644, 1.487, -0.358), 0.364 }, { Vector3.new(-1.627, 0.99, -0.374), 0.431 }, { Vector3.new(-0.262, 1.71, -0.244), 0.312 } }
    for k, c in CROWNS do
        local a = anchor(aura, "Crown" .. k, c[1])
        local r = c[2] * 1.3
        finish(emitter("Leaves", {
            Texture = T.Leaf, Speed = NumberRange.new(0.2, 0.6), SpreadAngle = Vector2.new(180, 180), Drag = 0.6,
            Acceleration = Vector3.new(0.3, -0.55, 0.12), Lifetime = NumberRange.new(3.5, 4.5), Rate = 1 + 0.3 * (k % 2),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-60, 60), LightEmission = 0.15, Brightness = 1.6,
            Size = seq({ { 0, 0.3 }, { 0.1, 0.42 }, { 1, 0.38 } }),
            Color = k % 2 == 0 and ColorSequence.new(rgb(215, 215, 80), rgb(150, 190, 60)) or ColorSequence.new(rgb(120, 225, 80), rgb(60, 170, 50)),
            Transparency = seq({ { 0, 1 }, { 0.08, 0.05 }, { 0.8, 0.2 }, { 1, 1 } }),
        }, { HatchEmit = 6 }), a)
        finish(emitter("Glow", {
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

-- Magma Heart Egg: the owner's test fire fitted to the egg, eight flame columns round its girth. One
-- emitter per unrotated attachment: a bed emitter starts flames inside the egg, a ring one scatters
-- them into smoke. Half light emission: fully additive flames wash out to pale smoke on the day sky.
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

-- Phoenix Ash Egg: an egg that dies and is reborn every CyclePeriod seconds. Ash falls and smoke curls
-- while it lies cold, embers kindle, then at the rebirth the ash rushes up gold, wings of light sweep
-- open and a sunburst blooms. Its right side (+X) faces the Magma Heart 5.9 studs away.
RECIPES.PhoenixAshEgg = function(aura)
    local size = aura.egg and aura.egg.Size or Vector3.new(4.57, 4.67, 3.53)
    local C = size.Y / 2
    local top = size.Y
    local GOLD, FLAME, EMBER = rgb(255, 215, 120), rgb(255, 140, 40), rgb(220, 60, 25)
    local R = 0.735                                  -- where in the cycle the rebirth bursts
    set(aura.model, nil, {
        Gather = 1.6, Tint = rgb(255, 170, 60), CyclePeriod = 15, CycleRebirth = R, CycleScreen = 22, CycleScreenFlash = 0.45,
        CycleEggGlow = seq({ { 0, 0.3 }, { 0.55, 0.3 }, { 0.72, 1 }, { R + 0.01, 1.8 }, { 0.8, 1.5 }, { 0.9, 0.8 }, { 1, 0.3 } }),
        CycleEggCold = rgb(45, 14, 8), CycleEggHot = rgb(255, 225, 130),
        CycleHighlight = colors({ { 0, rgb(120, 25, 15) }, { 0.6, rgb(150, 35, 15) }, { 0.72, rgb(255, 120, 40) },
            { R + 0.001, rgb(255, 70, 70) }, { 0.748, rgb(255, 170, 40) }, { 0.76, rgb(255, 240, 90) }, { 0.772, rgb(90, 255, 140) },
            { 0.784, rgb(80, 200, 255) }, { 0.796, rgb(190, 110, 255) }, { 0.81, rgb(255, 200, 120) }, { 0.88, rgb(255, 120, 40) },
            { 1, rgb(120, 25, 15) } }),
        CycleOutline = seq({ { 0, 0.85 }, { 0.6, 0.85 }, { 0.72, 0.5 }, { R + 0.005, 0.05 }, { 0.82, 0.15 }, { 0.92, 0.7 }, { 1, 0.85 } }),
        CycleFill = seq({ { 0, 1 }, { 0.72, 1 }, { R + 0.01, 0.82 }, { 0.8, 0.9 }, { 0.86, 1 }, { 1, 1 } }),   -- more fill hides its feathers
    })
    local sky = part(aura, "AshSky", CFrame.new(0, top + 0.8, 0), Vector3.new(5.6, 0.4, 5.6))
    finish(emitter("AshFall", {
        Texture = T.Ash, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Bottom, Speed = NumberRange.new(0.3, 0.7), SpreadAngle = Vector2.new(25, 25), Drag = 0.6,
        Acceleration = Vector3.new(0.15, -0.45, 0.05), Lifetime = NumberRange.new(5, 7), Rate = 18, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-90, 90), Size = seq({ { 0, 0.3, 0.1 }, { 1, 0.25, 0.08 } }),   -- pale: dark flakes read as dirt on the sky
        Color = colors({ { 0, rgb(175, 168, 162) }, { 1, rgb(125, 118, 114) } }), LightEmission = 0, LightInfluence = 0.2,
        Transparency = seq({ { 0, 1 }, { 0.1, 0.15 }, { 0.85, 0.35 }, { 1, 1 } }),
    }, { CycleRate = seq({ { 0, 1 }, { 0.6, 1 }, { 0.725, 0.6 }, { R, 0 }, { 0.86, 0 }, { 1, 1 } }) }), sky)
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
    local crown = attachment(aura, "Crown", CFrame.new(0, top - 0.2, 0))
    finish(emitter("CrownSmoke", {
        Texture = T.Fog, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.8, 1.2), SpreadAngle = Vector2.new(8, 8),
        Acceleration = Vector3.new(0.2, 0.3, 0), Lifetime = NumberRange.new(2.5, 3.5), Rate = 4, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-30, 30), Size = seq({ { 0, 0.4, 0.1 }, { 1, 1.5, 0.3 } }),
        Color = colors({ { 0, rgb(80, 70, 66) }, { 1, rgb(70, 66, 66) } }), LightEmission = 0, LightInfluence = 0.2,
        Transparency = seq({ { 0, 1 }, { 0.15, 0.7 }, { 0.7, 0.82 }, { 1, 1 } }),
    }, { CycleRate = seq({ { 0, 1 }, { 0.6, 1 }, { 0.72, 0.3 }, { R, 0 }, { 0.9, 0 }, { 1, 1 } }) }), crown)
    finish(emitter("Sunburst", {
        Texture = T.Flare, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.7), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, 1 }, { 0.25, 7 }, { 1, 8.5 } }), Color = ColorSequence.new(rgb(255, 220, 140)),
        Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Brightness = 2,
    }, { CycleEmit = 1, CycleAt = R + 0.003, HatchEmit = 2 }), attachment(aura, "Sun", CFrame.new(0, top + 0.6, 0)))

    -- wings: trails from a still root to a sweeping tip, kept in the egg's XY plane (a sweep in depth
    -- reads as a needle from the front). Checked by raycasts: 1.76 studs clear of the Magma Heart's egg.
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
                -- solid: a textured trail leaves only thin flicks past the egg's sculpted wings;
                -- LightEmission over 0.15 washes it pale on the sky
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

    local glow = light(aura, rgb(200, 50, 30), 12, 0.6)
    glow.Parent.Position = Vector3.new(0, C, 0)
    set(glow, nil, {
        CycleBrightness = seq({ { 0, 0.35 }, { 0.6, 0.35 }, { 0.72, 0.8 }, { R + 0.01, 3.2 }, { 0.8, 1.6 }, { 0.9, 0.6 }, { 1, 0.35 } }),
        CycleColor = colors({ { 0, rgb(200, 50, 30) }, { 0.6, rgb(200, 50, 30) }, { R + 0.005, rgb(255, 190, 90) }, { 0.85, rgb(255, 120, 50) }, { 1, rgb(200, 50, 30) } }),
    })
    drawIn(aura, T.Spark, rgb(255, 190, 90), 0.4, 50)
    burst(aura, rgb(255, 200, 110), 9)
    for _, d in aura.model:GetDescendants() do -- the hatch flare at the egg's height: the helpers assume a smaller egg
        if d.Name == "Burst" and d:IsA("Attachment") then
            d.Position = Vector3.new(0, C, 0)
        elseif d.Name == "DrawIn" and d:IsA("BasePart") then
            d.CFrame = aura.root.CFrame * CFrame.new(0, C, 0)
        end
    end
end

-- Inferno Egg: a miniature volcano with an unstable molten core: spark comets (A), magma fragments (B),
-- a flame vortex (C), heat ripples and vents (D), sparks, embers and ash (E) and the core's light (F).
-- Every few seconds a pulse runs through them in turn; on the hatch burst everything erupts.
RECIPES.InfernoEgg = function(aura)
    local CRIMSON, MOLTEN, LAVA, GOLD = rgb(160, 22, 12), rgb(255, 90, 20), rgb(255, 175, 55), rgb(255, 215, 120)
    local C = 1.9                                    -- the egg stands 3.8 studs
    set(aura.model, nil, {
        Gather = 1.8, Tint = rgb(255, 80, 20), Breath = 0.12, BreathPeriod = 3.2,
        PulseInterval = 6, PulseJitter = 1.5, PulseSpeed = 0.9, PulseGlow = 0.6, PulseEggGlow = rgb(255, 205, 110),
        -- settings, to tune by hand
        Intensity = 1, Density = 1, OrbitSpeed = 1, LightIntensity = 1, Visible = true,
    })
    local fire = colors({ { 0, LAVA }, { 0.45, MOLTEN }, { 1, CRIMSON } })

    -- A. spark comets. Our spark texture has real alpha: the library's dots only work fully additive,
    -- which turns orange pink and white on a bright sky. Motion-aligned particles do not render here.
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
        finish(emitter("Flare", {
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
        -- the rocks pull in as they pass the nearest egg; swept in Play, they keep 0.33 studs clear of both
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

    -- C. the flame vortex
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

    -- D. heat ripples and three vents erupting in turn
    local ground = group(aura, "GroundFormation")
    local heat = ripple(aura, rgb(255, 110, 40), 7, 3)
    heat:SetAttribute("PulseEmit", 1)
    heat:SetAttribute("PulseDelay", 0.1)
    heat.Parent = ground
    for k, ang in { 125, 245, 5 } do
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
    finish(emitter("Cinders", {
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
        LightEmission = 0, LightInfluence = 0.2, -- lit by the sky any more and it reads as pale glass
        Transparency = seq({ { 0, 1 }, { 0.15, 0.25 }, { 0.8, 0.4 }, { 1, 1 } }),
    }), ashArea)
    ashArea.Parent = air
    -- sparks spitting out of the egg's own cracks
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

    -- F. the core's light: kept low, as the stand already lights the egg
    light(aura, rgb(255, 120, 45), 12, 0.5)

    local gathering = drawIn(aura, T.Dot, rgb(255, 150, 70), 0.35, 60)
    gathering.Parent.Parent = air
    burst(aura, rgb(255, 160, 80), 10)
    finish(emitter("Eruption", {
        Texture = T.Fireburst, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.7), Rate = 0, Rotation = NumberRange.new(0, 360),
        Size = seq({ { 0, 2 }, { 0.3, 9 }, { 1, 10.5 } }), Transparency = seq({ { 0, 0 }, { 0.6, 0.3 }, { 1, 1 } }), Brightness = 2,
    }, { HatchEmit = 2 }), attachment(aura, "EruptionCore", CFrame.new(0, C, 0)))
end

-- ---------- Moonlit Isle ----------
-- Soft and smooth, by the owner's direction: only soft glows, gliding light and slow drift (T.SoftGlow:
-- T.SmallGlow is a speck at mote sizes). The isle is bright, so motes carry deeper colour at lower
-- light emission. Stands are about 6 studs apart: auras stay within about 2.9 studs of the egg.
-- Points on the eggs are measured in eggs_moon.py's build (see modelPoint).

-- Moves the egg-centred pieces (halo, light, the hatch's gathering and burst) to `c` studs above
-- the Root, for an egg whose centre is not EGG_CENTRE.
local function centreAt(aura, c)
    for _, d in aura.model:GetDescendants() do
        if d:IsA("Attachment") and d.Parent == aura.root and (d.Name == "Halo" or d.Name == "Light" or d.Name == "Burst") then
            d.Position = Vector3.new(0, c, 0)
        elseif d:IsA("BasePart") and d.Name == "DrawIn" then
            d.CFrame = aura.root.CFrame * CFrame.new(0, c, 0)
        end
    end
end

-- A soft glow breathing slowly on a point of the egg (a pearl, an orb, a jewel).
local function breathe(at, color, size, transparency, zOffset)
    return finish(emitter("Breath", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(2.4, 3), Rate = 0.8,
        Rotation = NumberRange.new(0, 360), ZOffset = zOffset or 0.4, Brightness = 2,
        Size = seq({ { 0, size * 0.45 }, { 0.5, size }, { 1, size * 1.15 } }), Color = ColorSequence.new(color),
        Transparency = seq({ { 0, 1 }, { 0.45, transparency }, { 1, 1 } }),
    }, { HatchEmit = 2 }), at)
end

-- Celestial Egg: the night breathing. Soft points of starlight swell and fade as they drift
-- slowly up round it; two soft shooting stars glide round it on tilted paths, each a glowing head
-- with a soft tail; the pearl on its crescent breathes a blue glow; a faint night-blue haze.
RECIPES.CelestialEgg = function(aura)
    local NIGHT, STAR = rgb(70, 110, 255), rgb(225, 235, 255)
    local C = modelPoint(aura, Vector3.new(0.101, 0.197, 0)).Y   -- the egg's centre, in its crescent
    set(aura.model, nil, { Gather = 1.4, Tint = rgb(120, 170, 255), Breath = 0.12, BreathPeriod = 6 })
    local sky = part(aura, "StarArea", CFrame.new(0, C + 0.3, 0), Vector3.new(5.2, 4.6, 5.2))
    finish(emitter("Starlight", {
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(0.1, 0.3), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.15, 0), Drag = 0.5,
        Lifetime = NumberRange.new(2.5, 4), Rate = 7, Size = seq({ { 0, 0 }, { 0.5, 0.45, 0.12 }, { 1, 0 } }),
        Color = ColorSequence.new(STAR, rgb(150, 190, 255)), Transparency = NumberSequence.new(0.2), Brightness = 2,
    }, { HatchEmit = 24 }), sky)
    for k, c in { { 38, 2.5, 24, -10, 0.5, 5.5, 1.6 }, { -27, 2.85, -18, 22, 0.4, 7, 2 } } do
        local _, head = arc(aura, "Comet" .. k, { Orbit = c[1], Radius = c[2], Height = C + 0.2, Tilt = Vector3.new(c[3], 0, c[4]),
            Phase = (k - 1) * 170, Bob = c[5], BobPeriod = c[6] }, 0.16, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = c[7], Brightness = 2, LightEmission = 0.4,
            Color = colors({ { 0, STAR }, { 0.4, rgb(140, 180, 255) }, { 1, NIGHT } }), Transparency = seq({ { 0, 0.1 }, { 0.5, 0.4 }, { 1, 0.85 } }),
            WidthScale = seq({ { 0, 1 }, { 1, 0.2 } }),
        })
        finish(emitter("Head", {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 12,
            Size = seq({ { 0, 0.5 }, { 1, 0.15 } }), Color = ColorSequence.new(rgb(175, 205, 255)), Transparency = seq({ { 0, 0.3 }, { 1, 1 } }), Brightness = 2,
        }, { HatchEmit = 4 }), head)
    end
    breathe(anchor(aura, "Pearl", Vector3.new(-0.68, 1.103, 0)), rgb(80, 160, 255), 1.4, 0.55)
    halo(aura, NIGHT, 6, 0.86)
    light(aura, rgb(110, 150, 255), 12, 0.9)
    drawIn(aura, T.SoftGlow, STAR, 0.5, 50)
    burst(aura, rgb(190, 215, 255), 8, T.SoftGlow)
    centreAt(aura, C)
end

-- Astral Sanctum Egg: light from the sanctum. Soft violet light drifts out through its windows
-- and up; three lantern spirits circle it slowly at their own heights and paces, each a soft glow
-- leaving a fading tail of light; the orb on its spire breathes; a faint violet haze.
RECIPES.AstralSanctumEgg = function(aura)
    local VIOLET, LILAC = rgb(110, 60, 255), rgb(180, 145, 255)   -- bluer: Neon and the bright isle push violet to pink
    local C = modelPoint(aura, Vector3.new(0, -0.234, 0)).Y
    set(aura.model, nil, { Gather = 1.4, Tint = rgb(170, 120, 255), Breath = 0.14, BreathPeriod = 5.5 })
    -- born just inside the shell round the window band, so the light seems to come out through it
    local sanctum = part(aura, "Sanctum", CFrame.new(0, C - 0.1, 0), Vector3.new(2.7, 1.7, 2.7))
    finish(emitter("Spill", {
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, Speed = NumberRange.new(0.3, 0.6), Drag = 0.4,
        Acceleration = Vector3.new(0, 0.25, 0), Lifetime = NumberRange.new(2.5, 3.5), Rate = 8,
        Size = seq({ { 0, 0 }, { 0.3, 0.5, 0.1 }, { 1, 0 } }), Color = ColorSequence.new(rgb(170, 130, 255), VIOLET),
        Transparency = NumberSequence.new(0.2), Brightness = 2, LightEmission = 0.4,
    }, { HatchEmit = 20 }), sanctum)
    for k, l in { { 30, 2.3, 0.9, 0.35, 4.2 }, { -22, 2.6, -0.2, 0.3, 5.1 }, { 26, 2.8, 0.3, 0.4, 3.6 } } do
        local lantern = attachment(aura, "Lantern" .. k, CFrame.new(0, C + l[3], l[2]))
        set(lantern, nil, { Orbit = l[1], Radius = l[2], Height = C + l[3], Phase = (k - 1) * 120 + 20, Bob = l[4], BobPeriod = l[5] })
        finish(emitter("Glow", {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.9, 1.1), Rate = 14,
            Size = seq({ { 0, 0.85 }, { 1, 0 } }), Color = ColorSequence.new(rgb(185, 150, 255), VIOLET),
            Transparency = seq({ { 0, 0.25 }, { 1, 1 } }), Brightness = 2, LightEmission = 0.5,
        }, { HatchEmit = 4 }), lantern)
    end
    breathe(anchor(aura, "Orb", Vector3.new(0, 1.336, 0)), VIOLET, 1.1, 0.5)
    halo(aura, VIOLET, 6, 0.86)
    light(aura, VIOLET, 12, 1)
    drawIn(aura, T.SoftGlow, LILAC, 0.5, 50)
    burst(aura, rgb(205, 175, 255), 8, T.SoftGlow)
    centreAt(aura, C)
end

-- Heavenly Throne Egg: radiance. A soft gold glow breathes behind the egg, filling its mandorla;
-- golden dust rises slowly off its cushion of cloud, and soft wisps of cloud drift from it; the
-- sun jewel on its front breathes. Its breath is the slowest on the isle.
RECIPES.HeavenlyThroneEgg = function(aura)
    local GOLD, SUN = rgb(255, 190, 70), rgb(255, 225, 140)
    local C = modelPoint(aura, Vector3.new(0, -0.493, 0.214)).Y
    set(aura.model, nil, { Gather = 1.5, Tint = rgb(255, 210, 110), Breath = 0.12, BreathPeriod = 7 })
    finish(emitter("Radiance", {
        -- a deep gold at low light emission: brighter, it hazes the pearl egg to white
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(3, 4), Rate = 0.7, ZOffset = -3,
        Rotation = NumberRange.new(0, 360), Size = seq({ { 0, 3.2 }, { 0.5, 4.2 }, { 1, 4.6 } }), Color = ColorSequence.new(rgb(255, 165, 40)),
        Transparency = seq({ { 0, 1 }, { 0.4, 0.78 }, { 1, 1 } }), Brightness = 2, LightEmission = 0.35,
    }, { HatchEmit = 2 }), anchor(aura, "Mandorla", Vector3.new(0, 0.057, -1.026)))
    local cushion = part(aura, "Cushion", CFrame.new(modelPoint(aura, Vector3.new(0, -1.593, 0.214))), Vector3.new(3.4, 0.3, 3.4))
    finish(emitter("Dust", {
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.4, 0.8), SpreadAngle = Vector2.new(25, 25),
        Acceleration = Vector3.new(0, 0.2, 0), Drag = 0.5, Lifetime = NumberRange.new(3, 4.5), Rate = 6,
        Size = seq({ { 0, 0 }, { 0.3, 0.4, 0.08 }, { 1, 0 } }), Color = ColorSequence.new(SUN, GOLD),
        Transparency = NumberSequence.new(0.15), Brightness = 2,
    }, { HatchEmit = 25 }), cushion)
    finish(emitter("Wisps", {
        Texture = T.Fog, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, Speed = NumberRange.new(0.2, 0.4), Drag = 0.3,
        Acceleration = Vector3.new(0, 0.1, 0), Lifetime = NumberRange.new(3.5, 5), Rate = 0.8, Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-10, 10), Size = seq({ { 0, 1 }, { 1, 2.4 } }), Color = ColorSequence.new(rgb(255, 250, 235)),
        LightEmission = 0.15, Transparency = seq({ { 0, 1 }, { 0.3, 0.75 }, { 1, 1 } }),
    }, { HatchEmit = 6 }), cushion)
    breathe(anchor(aura, "Sun", Vector3.new(0, -0.619, 1.292)), GOLD, 1, 0.55)
    light(aura, GOLD, 13, 0.6) -- the pearl egg washes out under a stronger light
    drawIn(aura, T.SoftGlow, SUN, 0.5, 50)
    burst(aura, rgb(255, 230, 160), 9, T.SoftGlow)
    centreAt(aura, C)
end

-- ---------- Origin Abyss ----------
-- The same soft direction as Moonlit Isle. The thorns curve close round each egg (about 1.6 studs
-- from its axis low down) and stands are 6.2 studs apart, so circling things stay high or within 2.6
-- studs. No PointLights: coloured light paints the bronze thorns red. Points from eggs_origin.py.

-- Forbidden Origin Egg: the seal drinking light. Soft violet motes are drawn in toward the seal
-- from all round it; every few seconds a slow soft swell of violet spreads from the seal and
-- fades, as if something behind it stirs; a faint violet haze.
RECIPES.ForbiddenOriginEgg = function(aura)
    local VIOLET, LILAC = rgb(100, 60, 255), rgb(185, 150, 255)
    local C = modelPoint(aura, Vector3.new(0, 0, -0.008)).Y
    set(aura.model, nil, { Gather = 1.5, Tint = rgb(150, 100, 255), Breath = 0.12, BreathPeriod = 6.5 })
    local seal = anchor(aura, "Seal", Vector3.new(0, 0.01, 1.112))
    finish(emitter("Stir", {
        Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(2.6, 3), Rate = 0.35, ZOffset = 0.5,
        Size = seq({ { 0, 0.5 }, { 1, 3.2 } }), Color = ColorSequence.new(VIOLET),
        Transparency = seq({ { 0, 1 }, { 0.15, 0.55 }, { 1, 1 } }), Brightness = 2, LightEmission = 0.5,
    }, { HatchEmit = 2 }), seal)
    local around = part(aura, "SealDraw", CFrame.new(seal.Position), Vector3.new(4.4, 4.4, 4.4))
    finish(emitter("Drawn", {
        Texture = T.SoftGlow, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Speed = NumberRange.new(0.6, 0.8), Lifetime = NumberRange.new(2.6, 3),
        Rate = 6, Size = seq({ { 0, 0 }, { 0.3, 0.42, 0.08 }, { 0.85, 0.2 }, { 1, 0 } }), Color = ColorSequence.new(LILAC, VIOLET),
        Transparency = NumberSequence.new(0.2), Brightness = 2, LightEmission = 0.45,
    }, { HatchEmit = 20 }), around)
    halo(aura, VIOLET, 6, 0.86)
    drawIn(aura, T.SoftGlow, LILAC, 0.5, 50)
    burst(aura, rgb(200, 170, 255), 8, T.SoftGlow)
    centreAt(aura, C)
end

-- Void Rift Egg: the rift breathing. Blue void light seeps out through the tear and drifts away;
-- the heart breathes in the void inside; two deep-blue wisps loop slowly round it on steep tilts,
-- like space folding; a faint blue haze.
RECIPES.VoidRiftEgg = function(aura)
    local BLUE, ICE = rgb(60, 100, 255), rgb(150, 185, 255)
    local C = modelPoint(aura, Vector3.new(0, 0, -0.059)).Y
    set(aura.model, nil, { Gather = 1.5, Tint = rgb(90, 130, 255), Breath = 0.14, BreathPeriod = 5 })
    local heart = modelPoint(aura, Vector3.new(0, 0, -0.159))
    -- up axis out of the egg's front (local -Z), through the tear
    local seep = attachment(aura, "Seep", CFrame.new(heart) * CFrame.Angles(-math.pi / 2, 0, 0))
    finish(emitter("Seep", {
        Texture = T.SoftGlow, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.5, 0.9), SpreadAngle = Vector2.new(18, 35),
        Drag = 0.4, Acceleration = Vector3.new(0, 0.15, 0), Lifetime = NumberRange.new(2.5, 3.5), Rate = 7,
        Size = seq({ { 0, 0 }, { 0.35, 0.45, 0.1 }, { 1, 0 } }), Color = ColorSequence.new(ICE, BLUE),
        Transparency = NumberSequence.new(0.2), Brightness = 2, LightEmission = 0.5,
    }, { HatchEmit = 20 }), seep)
    breathe(anchor(aura, "Heart", Vector3.new(0, 0, -0.159)), BLUE, 1.2, 0.45, 0)
    for k, c in { { 30, 2.1, 62, 0, 0.3, 6 }, { -22, 2.3, -48, 30, 0.4, 7.5 } } do
        local _, head = arc(aura, "Fold" .. k, { Orbit = c[1], Radius = c[2], Height = C + 0.6, Tilt = Vector3.new(c[3], 0, c[4]),
            Phase = (k - 1) * 150, Bob = c[5], BobPeriod = c[6] }, 0.16, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 1.8, Brightness = 2, LightEmission = 0.35,
            Color = colors({ { 0, ICE }, { 0.4, BLUE }, { 1, rgb(30, 30, 140) } }), Transparency = seq({ { 0, 0.15 }, { 0.5, 0.4 }, { 1, 0.85 } }),
            WidthScale = seq({ { 0, 1 }, { 1, 0.3 } }),
        })
        finish(emitter("Head", {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 12,
            Size = seq({ { 0, 0.45 }, { 1, 0.15 } }), Color = ColorSequence.new(ICE), Transparency = seq({ { 0, 0.3 }, { 1, 1 } }),
            Brightness = 2, LightEmission = 0.5,
        }, { HatchEmit = 4 }), head)
    end
    halo(aura, BLUE, 6, 0.86)
    drawIn(aura, T.SoftGlow, ICE, 0.5, 50)
    burst(aura, rgb(160, 190, 255), 8, T.SoftGlow)
    centreAt(aura, C)
end

-- Primordial Abyss Egg: deep time. Three soft lights sweep round it like a clock's hands, each a
-- third the speed of the one below; the ammonite's mouth breathes magenta and pink motes drift out.
RECIPES.PrimordialAbyssEgg = function(aura)
    local MAGENTA, ROSE, WARM = rgb(255, 60, 180), rgb(255, 160, 215), rgb(255, 200, 150)
    local C = modelPoint(aura, Vector3.new(0, 0, -0.051)).Y
    set(aura.model, nil, { Gather = 1.6, Tint = rgb(255, 110, 200), Breath = 0.12, BreathPeriod = 8 })
    for k, h in { { 27, 2.0, 0.9 }, { 9, 2.3, 1.5 }, { 3, 2.6, 2.1 } } do
        local _, head = arc(aura, "Hand" .. k, { Orbit = h[1], Radius = h[2], Height = C + h[3], Phase = (k - 1) * 130 }, 0.08, {
            Texture = T.SoftGlow, TextureMode = Enum.TextureMode.Stretch, Lifetime = 2.4, Brightness = 2, LightEmission = 0.4,
            Color = colors({ { 0, WARM }, { 0.5, ROSE }, { 1, MAGENTA } }), Transparency = seq({ { 0, 0.15 }, { 0.6, 0.5 }, { 1, 1 } }),
            WidthScale = seq({ { 0, 1 }, { 1, 0.4 } }),
        })
        finish(emitter("Head", {
            Texture = T.SoftGlow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5), Rate = 12,
            -- rose, not warm white: brighter heads bloom into white blobs
            Size = seq({ { 0, 0.38 }, { 1, 0.12 } }), Color = ColorSequence.new(rgb(255, 130, 200)), Transparency = seq({ { 0, 0.3 }, { 1, 1 } }),
            Brightness = 2, LightEmission = 0.35,
        }, { HatchEmit = 4 }), head)
    end
    breathe(anchor(aura, "Mouth", Vector3.new(-0.513, 0.007, 0.91)), MAGENTA, 1, 0.5)
    local spiral = modelPoint(aura, Vector3.new(0, 0.005, 1.019))
    finish(emitter("Spiral", {
        Texture = T.SoftGlow, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.3, 0.5), SpreadAngle = Vector2.new(50, 50),
        Drag = 0.4, Acceleration = Vector3.new(0, 0.2, 0), Lifetime = NumberRange.new(2.5, 3.5), Rate = 3,
        Size = seq({ { 0, 0 }, { 0.35, 0.38, 0.08 }, { 1, 0 } }), Color = ColorSequence.new(ROSE, MAGENTA),
        Transparency = NumberSequence.new(0.2), Brightness = 2, LightEmission = 0.5,
    }, { HatchEmit = 16 }), attachment(aura, "Spiral", CFrame.new(spiral) * CFrame.Angles(-math.pi / 2, 0, 0)))
    halo(aura, MAGENTA, 6, 0.87)
    drawIn(aura, T.SoftGlow, ROSE, 0.5, 50)
    burst(aura, rgb(255, 180, 225), 8, T.SoftGlow)
    centreAt(aura, C)
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
            aura.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- so the client sees it complete
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

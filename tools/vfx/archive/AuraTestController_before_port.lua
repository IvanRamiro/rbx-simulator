-- The owner's layer progression with sub-rank scaling (test). Each dummy's realm (CultivationTier,
-- 1-12) picks its colours from AuraConfig and its layers by realm group; its sub-rank (SubRank,
-- 1-5) moves it along one continuous level, t = (realm - 1 + progress) / 11, progress =
-- (SubRank - 1) / 5: Peak (0.8) sits just short of the next realm's base, so a breakthrough never
-- looks weaker. Every size, rate and speed follows t (rates capped at 60 per emitter for mobile);
-- the layers a realm adds are the visible jump.
--   Early (1-2): a soft glow close to the torso, glints rising round the body.
--   Mid (3-6): + a stream rising from a ring at the feet; ribbon arcs (one from Spirit Soul, two
--   from Immortal).
--   High (7-12): + a turning ground sigil, a rising column; a dark void core inside a bright rim
--   for Cosmic, Void and Eternal; a third ribbon and a second sigil ring from Heavenly Dao.
--   Signature pieces (TopTierMeshes): a crown of flames (Divine), an orrery (Cosmic), drifting
--   shards (Void), twin coils (Primordial); Heavenly Dao and Eternal have whole rigs (topTier).
-- The project's own textures stand in for the pasted IDs (a lace decoration, and a place).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local AuraConfig = require(script.Parent:WaitForChild("AuraConfig"))

local TEX = {
    Glow = "rbxassetid://135169457468310",
    Streak = "rbxassetid://115312010132075",
    Ribbon = "rbxassetid://99893839045856",
    Formation = "rbxassetid://86025672711867",
    Ring = "rbxassetid://130173906719836",
    Glitter = "rbxassetid://14049414463",
    DaoRunes = "rbxassetid://80369515975276",   -- tools/vfx/top_tier_aura_textures.py
    LawStreak = "rbxassetid://75983337371298",
    Nebula = "rbxassetid://128568519603570",
    -- Realm 1, picked by the owner (Creator Store images)
    SoftOrb = "rbxassetid://196969716",        -- a soft radial gradient (Corecii)
    OrbShine = "rbxassetid://98986384327358",   -- a bright core in coiling filaments (XxOmqxXNerd)
    LightOrbs = "rbxassetid://917181007",       -- scattered soft light dots (JDLENL)
    OrbMist = "rbxassetid://15753665886",       -- a soft blurred wisp (troPSDtroPSD)
    SmokePuffs = "rbxassetid://16503766653",    -- an 8x8 flipbook of smoke puffs (Quantum1zed)
    -- Realm 1, from the PDS' Particles & Models Kit (Workspace)
    Mote = "rbxassetid://16512006463",         -- one tiny core with a faint halo (Sparkles&Debris)
    QiThread = "rbxassetid://11829306338",     -- one soft waving thread (Beams)
    Wisp = "rbxassetid://7216854921",          -- a faint soft smoke wisp (Fogs)
    Spiral = "rbxassetid://14050124950",        -- a soft spiral (Fogs)
    -- Realm 2, from the PDS kit
    Spark = "rbxassetid://16511998441",         -- a small dot with a faint cross flare (Sparkles&Debris)
    RiseStreak = "rbxassetid://7216847852",     -- a thin upright streak (Sparkles&Debris; replaced)
    RiseDrops = "rbxassetid://14919963322",     -- droplets with tails, on black (bryselee811; tried, replaced)
    RiseStar = "rbxassetid://12363775390",      -- a small six-ray star (PDS, Sparkles&Debris)
    -- Realm 3, from the PDS kit (Rings)
    EnergyRing = "rbxassetid://12403112662",    -- a thin glowing ring with brighter arcs
    SwirlRing = "rbxassetid://6250126210",      -- a thin ring of wispy strokes
    CrescentSwirl = "rbxassetid://15999331354", -- a 4x4 flipbook: a crescent ring forms and breaks up (sappVFX; tried, replaced)
    -- our own (tools/vfx/mist_ribbon_textures.py)
    MistRibbon = "rbxassetid://106430686548190", -- smoke streaming along its length, no edge anywhere
    MistHaze = "rbxassetid://139629863109215",   -- a wider, fainter veil under it
    GlowLine = "rbxassetid://102421798899318",   -- a soft line, even along its length, upright (lightning glow)
    RuneGlyphs = "rbxassetid://118226937399588", -- 16 original runes, 4x4 (tools/vfx/rune_glyphs.py; no text)
    -- the owner's Realm 4 layout, textures from the PDS kit (Shines)
    SoulMist = "rbxassetid://9345352897",        -- a soft swirling ghost-like mist (CoreGlow)
    SoulWisp = "rbxassetid://14590122278",       -- a small soft spiral wisp (Wisps)
    SoulRing = "rbxassetid://17426702695",       -- a ring of swirling strokes (GroundRing)
    SoulShock = "rbxassetid://14197762397",      -- a shockwave ring with streaks (EnergyShockwave)
    -- the owner's own body aura (built by the owner on the AuraWorkbench dummy, approved 2026-11-03)
    BodySmoke = "rbxassetid://17332831347",     -- an 8x8 flipbook of rolling smoke
    BodySpark = "rbxassetid://9997556038",      -- a small round spark
    BodyStar = "rbxassetid://12363796862",      -- a four-point star glint
    -- the owner's vortex ripple for Realm 4 (their picks, Creator Store)
    VortexRings = "rbxassetid://18281460865",   -- a 4x4 flipbook: a glinting ring forms and breaks up (realkilometers)
    VortexCloud = "rbxassetid://12683695494",   -- an 8x8 flipbook: a small rolling smoke cloud (Isathyst)
    -- Realm 4's smoke orbs (the owner's design): their star and lightning, smoke from the PDS kit (Fogs)
    OrbStar = "rbxassetid://84556863870846",      -- our own short cross flare (tools/vfx/soul_orb_textures.py)
    SoulSeal = "rbxassetid://93159167451330",     -- our own ground circle: three soul nodes, soul flames (same tool)
    SmokePuff = "rbxassetid://80021798595720",    -- our own 4x4 flipbook: a puff billows, tears and dissolves
                                                  -- (inside 78% of each frame: a clear margin, so no cell edges show)
    ElectricRing = "rbxassetid://6900421398",     -- a crackling electric ring (PDS Rings)
    BoltBurst = "rbxassetid://7216850580",        -- a small burst of lightning (PDS Fogs)
    OrbLightning = "rbxassetid://14431633138",    -- 4x4 flipbook lightning (Clazite_VFX; tried, replaced by procedural bolts)
    OrbSmoke = "rbxassetid://1084987899",         -- a dense soft cloud puff
    GroundSmoke = "rbxassetid://8779210242",      -- a very soft round fog, no edges (PDS Fogs; replaced)
    SmokeRipple = "rbxassetid://133636855384267", -- our own ripple of smoke strands, zero at its border (tools/vfx/soul_orb_textures.py;
                                                  -- the PDS ring 12878479033's faint border showed as a square at 19 studs)
    RollingSmoke = "rbxassetid://14050526759",    -- 2x2 billowy torn smoke puffs (PDS Fogs)
}
-- the top realms' meshes (tools/vfx/top_tier_aura_meshes.py, imported into TopTierMeshes): where
-- each sits round the root, as built
local MESHES = {
    DaoRing_Outer = Vector3.new(0, -1.6, 0),
    DaoRing_Inner = Vector3.new(0, -2.85, 0),
    LawPillars = Vector3.new(0, 0.1, 0),
    EventHorizon = Vector3.new(0, 0, 0),
    OrbitalHelices = Vector3.new(0, 0.3, 0),
    TranscendenceCrown = Vector3.new(0, 2.4, 0.9),
    DivineFlameCrown = Vector3.new(0, 0.999, 0),
    CosmicOrrery = Vector3.new(0, 0.574, 0),
    VoidShards = Vector3.new(0.022, 0.978, -0.041),
    PrimordialCoils = Vector3.new(0, 0.9, 0),
}
local TOP = { [10] = true, [12] = true }
-- one signature piece each for the realms between: its mesh, look and motion. Colours from each
-- realm's palette, saturated: Neon blooms paler ones to yellow or white
local SIGNATURE = {
    [7] = { mesh = "DivineFlameCrown", material = Enum.Material.Neon, color = Color3.fromRGB(255, 100, 50), transparency = 0.15, kind = "flicker", speed = 0.3 },
    [8] = { mesh = "CosmicOrrery", material = Enum.Material.Neon, color = Color3.fromRGB(140, 80, 255), transparency = 0.2, kind = "mesh", speed = 0.5 },
    [9] = { mesh = "VoidShards", material = Enum.Material.Glass, color = Color3.fromRGB(10, 12, 24), transparency = 0.15, kind = "mesh", speed = 0.25,
        edge = { material = Enum.Material.ForceField, color = Color3.fromRGB(90, 160, 220), scale = 1.06 } },
    [11] = { mesh = "PrimordialCoils", material = Enum.Material.Neon, color = Color3.fromRGB(210, 40, 25), transparency = 0.1, kind = "mesh", speed = 1.1 },
}
local VOID_CORE = { [8] = true, [9] = true, [12] = true }
local MAX_RATE = 60

local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end

local function lastColor(colors)
    return colors.Keypoints[#colors.Keypoints].Value
end

local function emitter(parent, props)
    local e = Instance.new("ParticleEmitter")
    for k, v in props do
        e[k] = v
    end
    e.Parent = parent
    return e
end

-- an invisible part for a ring-shaped emitter (from an attachment an emitter emits from a point)
local function host(fx, root, r, h, y)
    local part = Instance.new("Part")
    part.Name = "EmitterHost"
    part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch = true, false, false, false
    part.Transparency = 1
    part.Size = Vector3.new(r * 2, h, r * 2)
    part.CFrame = root.CFrame * CFrame.new(0, y, 0)
    part.Parent = fx
    return part
end

-- a copy of a realm's mesh, placed round the root (nil until the meshes are imported)
local function meshPart(name, fx, root)
    local library = script.Parent:FindFirstChild("TopTierMeshes")
    local template = library and library:FindFirstChild(name, true)
    if not template then
        return nil
    end
    local part = template:Clone()
    part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch = true, false, false, false
    part.CastShadow = false
    part.CFrame = root.CFrame * CFrame.new(MESHES[name])
    part.Parent = fx
    return part
end

local function hasMesh(name)
    local library = script.Parent:FindFirstChild("TopTierMeshes")
    return library ~= nil and library:FindFirstChild(name, true) ~= nil
end

local spinners = {}

local topTier, signature -- below

-- mist ribbons revolving round the body (the owner's brief: "smooth, no edge, not flat, mist or
-- smoke, long length"). Each is a Trail behind a point racing round its own tilted circle and
-- weaving up and down; the ribbons run opposite each other. Each has a mist core standing upright
-- and a wider, fainter haze lying flat across it: crossed, so from any angle one of them is broad
-- (never flat), thinning to the tail. Not FaceCamera: where a camera-facing trail runs straight at
-- the camera its width has no direction, and the pieces fan out into spikes.
local function mistRibbons(root, fx, main, count, speed, alpha)
    for i = 1, count do
        local layers = {}
        for _, L in { { tex = TEX.MistHaze, hw = 1, flat = true, head = math.min(0.95, alpha + 0.3), tail = math.min(0.97, alpha + 0.42) },
                      { tex = TEX.MistRibbon, hw = 0.65, flat = false, head = alpha, tail = alpha + 0.15 } } do
            local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
            a0.Name, a1.Name = "MistA", "MistB"
            a0.Parent, a1.Parent = root, root
            local trail = Instance.new("Trail")
            trail.Attachment0, trail.Attachment1 = a0, a1
            trail.Texture = L.tex
            trail.TextureMode = Enum.TextureMode.Stretch
            trail.Color = ColorSequence.new(main)
            trail.LightEmission = 0.35
            trail.LightInfluence = 0
            trail.FaceCamera = false
            trail.Lifetime = 1.6
            trail.MinLength = 0.05
            -- the head tapers in from a point and fades in, so no end is ever a straight cut
            trail.Transparency = seq({ { 0, 1 }, { 0.22, L.head }, { 0.6, L.tail }, { 1, 1 } })
            trail.WidthScale = seq({ { 0, 0.15 }, { 0.2, 1 }, { 1, 0.35 } })
            trail.Parent = fx
            table.insert(layers, { a0 = a0, a1 = a1, hw = L.hw, flat = L.flat })
        end
        table.insert(spinners, { kind = "mist", layers = layers, root = root, speed = speed, angle = (i - 1) * math.tau / count,
            tilt = if i % 2 == 1 then 0.35 else -0.35, radius = 2.8, clock = i * 1.7 })
    end
end

-- Realm 1, Qi Awakening: the first breath of Qi. Motes revolve round the body the full 360 degrees
-- on two rings turning opposite ways; a faint mist rises off the shoulders; from Qi Adept, arcs of
-- Qi circle the body; a faint outline, a fainter fill and a soft PointLight breathe together.
-- Nothing gathers on the body's middle (the owner's calls). Each sub-rank adds more.
-- every realm's body glow (the owner's must-haves): a faint outline round the whole body with a
-- fainter fill, and a soft PointLight on the body and the ground; all breathe together (4 s in,
-- 4 s out)
local function bodyGlow(root, fx, main, line, fill, glow, range)
    local centre = Instance.new("Attachment")
    centre.Name = "AuraCentre"
    centre.Parent = root
    local outline = Instance.new("Highlight")
    outline.Adornee = root.Parent
    outline.FillColor = main
    outline.OutlineColor = main
    outline.DepthMode = Enum.HighlightDepthMode.Occluded
    outline.Parent = fx
    local light = Instance.new("PointLight")
    light.Color = main
    light.Range = range
    light.Shadows = false
    light.Parent = centre
    table.insert(spinners, { kind = "outline", highlight = outline, light = light, root = root, speed = 0, angle = 0, clock = 0,
        line = line, fill = fill, glow = glow })
end

-- arcs of Qi circling the body (each end's axis is the circle's tangent, so the beam's curve
-- follows the circle)
local function qiArcs(root, tint, count, alpha, speedK)
    for i = 1, count do
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Name, a1.Name = "ThreadA", "ThreadB"
        a0.Parent, a1.Parent = root, root
        local span, radius = 1.9, 3
        local curve = 4 / 3 * math.tan(span / 4) * radius
        local beam = Instance.new("Beam")
        beam.Attachment0, beam.Attachment1 = a0, a1
        beam.Texture = TEX.QiThread
        beam.TextureMode = Enum.TextureMode.Stretch
        beam.TextureSpeed = 0.6
        beam.Color = tint
        beam.LightEmission = 1
        beam.Transparency = seq({ { 0, 1 }, { 0.3, alpha }, { 0.7, alpha }, { 1, 1 } })
        beam.Width0, beam.Width1 = 1.2, 1.2
        beam.CurveSize0, beam.CurveSize1 = curve, curve
        beam.Segments = 20
        beam.FaceCamera = true
        beam.Parent = root
        table.insert(spinners, { kind = "arc", a0 = a0, a1 = a1, root = root, speed = (0.7 + 0.2 * i) * speedK * (if i % 2 == 0 then -1 else 1),
            angle = i * math.tau / 3, span = span, radius = radius, height = ({ 0.8, -0.8, 1.9 })[i], tilt = ({ 0.2, -0.25, 0.35 })[i] })
    end
end

-- Realm 1, Qi Awakening: the first breath of Qi. Motes revolve round the body the full 360 degrees
-- on two rings turning opposite ways; a faint mist rises off the shoulders; from Qi Adept, arcs of
-- Qi circle the body. Nothing gathers on the body's middle, and nothing is too bright (the owner's
-- calls). Each sub-rank adds more.
local function realm1(root, fx, tint, p)
    local main = lastColor(tint)
    for i, ring in { { r = 2.7, rate = 12 + 10 * p, turn = 0.9 + 0.4 * p, y = -0.3 }, { r = 2.1, rate = 6 + 6 * p, turn = -(0.6 + 0.3 * p), y = 0.4 } } do
        local part = host(fx, root, ring.r, 5, ring.y)
        emitter(part, { Texture = TEX.Mote, Color = tint, LightEmission = 0.6, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0 }, { 0.2, 3.4 }, { 0.8, 2.8 }, { 1, 0 } }),
            Transparency = seq({ { 0, 1 }, { 0.2, 0.3 }, { 0.8, 0.45 }, { 1, 1 } }), Lifetime = NumberRange.new(3, 4),
            Rate = ring.rate, Speed = NumberRange.new(0), Acceleration = Vector3.new(0, 0.35, 0) })
        table.insert(spinners, { kind = "mesh", part = part, root = root, offset = Vector3.new(0, ring.y, 0), speed = ring.turn,
            angle = i * 1.3 })
    end
    qiArcs(root, tint, if p >= 0.8 then 3 elseif p >= 0.6 then 2 else 0, 0.35, 1)
    emitter(host(fx, root, 1.1, 0.3, 1.5), { Texture = TEX.Wisp, Color = ColorSequence.new(main:Lerp(Color3.new(1, 1, 1), 0.4)),
        LightEmission = 0.4, EmissionDirection = Enum.NormalId.Top, Size = seq({ { 0, 1.6 }, { 1, 3.2 } }),
        Transparency = seq({ { 0, 1 }, { 0.35, 0.2 - 0.1 * p }, { 1, 1 } }), Lifetime = NumberRange.new(2.2, 3),
        Rate = 1.2 + 0.8 * p, Speed = NumberRange.new(0.5, 0.9), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-12, 12) })
    bodyGlow(root, fx, main, 0.55 - 0.25 * p, 0.92 - 0.08 * p, 0.6 + 0.5 * p, 9 + 3 * p)
end

-- Realm 2, Qi Foundation: the foundation is laid, and Qi now circulates in steady orbits. Two
-- tilted rings of small energy sparks circle the body, turning opposite ways (the signature);
-- Realm 1's arcs keep turning, quicker; small sparks rise round the legs, the first Qi flowing
-- out. Every value starts a step above Realm 1's Peak.
local function realm2(root, fx, tint, p)
    local main = lastColor(tint)
    for i, o in { { r = 2.7, y = 0.3, tilt = 0.35, turn = 2.2 }, { r = 2.4, y = -0.7, tilt = -0.45, turn = -1.8 } } do
        local ring = host(fx, root, o.r, 0.15, o.y)
        emitter(ring, { Texture = TEX.Spark, Color = tint, LightEmission = 0.4, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0 }, { 0.25, 1.6 + 0.4 * p }, { 1, 0 } }), Transparency = seq({ { 0, 1 }, { 0.25, 0.45 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.6), Rate = 18 + 10 * p, Speed = NumberRange.new(0) })
        table.insert(spinners, { kind = "orbit", part = ring, root = root, offset = Vector3.new(0, o.y, 0), tilt = o.tilt,
            speed = o.turn * (1 + 0.3 * p), angle = i * 1.7 })
    end
    qiArcs(root, tint, 3, 0.3 - 0.05 * p, 1.3 + 0.3 * p)
    -- rising sparks: small six-ray stars spinning as they rise and slow; few and soft
    emitter(host(fx, root, 2.2, 0.2, -2.9), { Texture = TEX.RiseStar, Color = tint, LightEmission = 0.4,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, EmissionDirection = Enum.NormalId.Top,
        Size = seq({ { 0, 0 }, { 0.15, 0.9 + 0.2 * p }, { 0.7, 0.7 + 0.2 * p }, { 1, 0 } }),
        Transparency = seq({ { 0, 1 }, { 0.15, 0.45 }, { 0.75, 0.6 }, { 1, 1 } }), Lifetime = NumberRange.new(1.4, 2),
        Rate = 4 + 4 * p, Speed = NumberRange.new(2, 3.2), SpreadAngle = Vector2.new(12, 12), Drag = 0.6,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90) })
    bodyGlow(root, fx, main, 0.3 - 0.12 * p, 0.85 - 0.06 * p, 1.05 + 0.4 * p, 12 + 2 * p)
end
-- Realm 3, Spirit Core: the Qi condenses into a core, and its orbits close into rings. Rings swirl
-- round the body like a gyroscope, each at its own tilt, turning while the tilt swings round (a
-- third from sub-rank 4). Each ring is an invisible part: Realm 2's sparks ride its edge, and from
-- two of our own mist ribbons revolve round the body (they replaced the owner's borrowed crescent
-- flipbook at their request for our own asset). Small stars keep rising round the legs. Every value starts a step above Realm 2's Peak (the sparks are
-- fewer: they ride the rings now, and the owner wants particles sparse).
local function realm3(root, fx, tint, p)
    -- jade, as the design doc gives Spirit Core (the owner didn't want AuraConfig's yellow)
    local main = Color3.fromRGB(0, 190, 120)
    tint = ColorSequence.new(main)
    local rings = {
        { r = 2.9, y = 0.2, tilt = 0.5, turn = 0.5, spin = 1.6, tex = TEX.EnergyRing },
        { r = 3.2, y = -0.3, tilt = -0.62, turn = -0.4, spin = -1.2, tex = TEX.SwirlRing },
        { r = 2.6, y = 0.6, tilt = 0.25, turn = 0.7, spin = 2.1, tex = TEX.EnergyRing },
    }
    for i = 1, if p >= 0.6 then 3 else 2 do
        local o = rings[i]
        local ring = Instance.new("Part")
        ring.Name = "EnergyRing"
        ring.Anchored, ring.CanCollide, ring.CanQuery, ring.CanTouch = true, false, false, false
        ring.CastShadow = false
        ring.Transparency = 1
        ring.Size = Vector3.new(o.r * 2, 0.05, o.r * 2)
        ring.CFrame = root.CFrame * CFrame.new(0, o.y, 0)
        emitter(ring, { Texture = TEX.Spark, Color = tint, LightEmission = 0.4, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0 }, { 0.25, 2 + 0.3 * p }, { 1, 0 } }), Transparency = seq({ { 0, 1 }, { 0.25, 0.4 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.6), Rate = 14 + 8 * p, Speed = NumberRange.new(0) })
        ring.Parent = fx
        table.insert(spinners, { kind = "gyro", part = ring, root = root, offset = Vector3.new(0, o.y, 0), tilt = o.tilt,
            speed = o.turn * (1 + 0.3 * p), angle = i * 2.1, spin = 0, spinSpeed = o.spin * (1 + 0.3 * p) })
    end
    mistRibbons(root, fx, main, 2, 2.5 + 0.5 * p, 0.5 - 0.05 * p)
    emitter(host(fx, root, 2.2, 0.2, -2.9), { Texture = TEX.RiseStar, Color = tint, LightEmission = 0.4,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, EmissionDirection = Enum.NormalId.Top,
        Size = seq({ { 0, 0 }, { 0.15, 1.1 + 0.2 * p }, { 0.7, 0.9 + 0.2 * p }, { 1, 0 } }),
        Transparency = seq({ { 0, 1 }, { 0.15, 0.42 }, { 0.75, 0.58 }, { 1, 1 } }), Lifetime = NumberRange.new(1.5, 2.1),
        Rate = 7.5 + 4 * p, Speed = NumberRange.new(2.2, 3.4), SpreadAngle = Vector2.new(12, 12), Drag = 0.6,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90) })
    bodyGlow(root, fx, main, 0.2 - 0.08 * p, 0.88 - 0.03 * p, 1.4 + 0.3 * p, 14 + 2 * p) -- gold fills strongly: kept light
end

-- Realm 4, Spirit Soul: the soul awakens and begins to show outside the body (the doc's "floating
-- runes and a translucent spirit silhouette"). Original runes revolve round the body in two bands
-- turning opposite ways, each fading in and out (one rune per particle, picked at random from
-- the sheet); a translucent copy of the body, a little larger, stands just behind it and sways out
-- of step, like the soul pulling free (fainter at Initiate). The mist ribbons and rising stars
-- carry on from Realm 3, a step up. Violet, AuraConfig's colour (the doc's jade is Realm 3's).
local function realm4Runes(root, fx, tint, p)
    local main = lastColor(tint)
    for i, band in { { r = 2.6, y = 0.9, turn = 0.7 }, { r = 2.4, y = -1.3, turn = -0.55 } } do
        local part = host(fx, root, band.r, 0.6, band.y)
        emitter(part, { Texture = TEX.RuneGlyphs, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
            FlipbookMode = Enum.ParticleFlipbookMode.Loop, FlipbookFramerate = NumberRange.new(0.001), FlipbookStartRandom = true,
            Color = tint, LightEmission = 0.4, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0.9 + 0.2 * p }, { 1, 1 + 0.2 * p } }),
            Transparency = seq({ { 0, 1 }, { 0.25, 0.35 }, { 0.75, 0.45 }, { 1, 1 } }), Lifetime = NumberRange.new(3, 4),
            Rate = 2.5 + 1.5 * p, Speed = NumberRange.new(0), Acceleration = Vector3.new(0, 0.2, 0) })
        table.insert(spinners, { kind = "mesh", part = part, root = root, offset = Vector3.new(0, band.y, 0),
            speed = band.turn * (1 + 0.3 * p), angle = i * 1.4 })
    end
    -- the spirit: the body's own visible parts copied in a shimmering field, kept outside the
    -- character (so its outline doesn't take them) and removed with the aura
    local body = root.Parent
    if body and body:IsA("Model") and body:FindFirstChildOfClass("Humanoid") then
        local ghost = Instance.new("Folder")
        ghost.Name = "Spirit_" .. body.Name
        local pairs_ = {}
        for _, part in body:GetChildren() do
            if part:IsA("BasePart") and part ~= root and part.Transparency < 1 then
                local copy = part:Clone()
                copy:ClearAllChildren()
                copy.Anchored, copy.CanCollide, copy.CanQuery, copy.CanTouch = true, false, false, false
                copy.CastShadow = false
                copy.Material = Enum.Material.ForceField
                copy.Color = main
                copy.Size *= 1.1
                copy.Parent = ghost
                table.insert(pairs_, { part = part, copy = copy })
            end
        end
        ghost.Parent = workspace.CurrentCamera
        fx.Destroying:Connect(function() ghost:Destroy() end)
        table.insert(spinners, { kind = "spirit", pairs = pairs_, root = root, speed = 0, angle = 0, clock = 0,
            base = 0.6 - 0.15 * p })
    end
    mistRibbons(root, fx, main, 2, 3 + 0.5 * p, 0.44 - 0.05 * p)
    emitter(host(fx, root, 2.2, 0.2, -2.9), { Texture = TEX.RiseStar, Color = tint, LightEmission = 0.4,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, EmissionDirection = Enum.NormalId.Top,
        Size = seq({ { 0, 0 }, { 0.15, 1.3 + 0.2 * p }, { 0.7, 1.1 + 0.2 * p }, { 1, 0 } }),
        Transparency = seq({ { 0, 1 }, { 0.15, 0.4 }, { 0.75, 0.56 }, { 1, 1 } }), Lifetime = NumberRange.new(1.6, 2.2),
        Rate = 11 + 4 * p, Speed = NumberRange.new(2.4, 3.6), SpreadAngle = Vector2.new(12, 12), Drag = 0.6,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90) })
    bodyGlow(root, fx, main, 0.13 - 0.05 * p, 0.86 - 0.03 * p, 1.65 + 0.3 * p, 16 + 2 * p)
end

-- Realm 4, Spirit Soul: the owner's layout (2026-11-03). On the root, SoulRootAttachment holds
-- CoreGlow, Wisps and GroundRing; SoulBurstAttachment at the feet (0, -2.5, 0) holds
-- EnergyShockwave, a burst fired on demand (E for the local player; in the test range every
-- 4 s, as the dummies can't press E). Rate, Lifetime, Size, Speed, LightEmission, ZOffset and
-- Transparency are the owner's table; textures (PDS kit), colour, spread, spin, drag and the
-- rings lying flat are mine. Emitters switch off past 75 studs from the camera (the owner's
-- culling).
local CULL_DISTANCE = 75
local function realm4Layout(root, fx, tint, p)
    local main = lastColor(tint)
    local soul = Instance.new("Attachment")
    soul.Name = "SoulRootAttachment"
    soul.Parent = root
    local burst = Instance.new("Attachment")
    burst.Name = "SoulBurstAttachment"
    burst.Position = Vector3.new(0, -2.5, 0)
    burst.Parent = root
    local flat = { Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top }
    local emitters = {
        emitter(soul, { Name = "CoreGlow", Texture = TEX.SoulMist, Color = tint, Rate = 12, Lifetime = NumberRange.new(1.5, 2.5),
            Size = seq({ { 0, 3 }, { 1, 5 } }), Speed = NumberRange.new(0.5, 1), LightEmission = 0.6, ZOffset = 0,
            Transparency = seq({ { 0, 0.5 }, { 1, 1 } }), SpreadAngle = Vector2.new(180, 180),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30) }),
        emitter(soul, { Name = "Wisps", Texture = TEX.SoulWisp, Color = tint, Rate = 25, Lifetime = NumberRange.new(1, 1.8),
            Size = seq({ { 0, 0.5 }, { 1, 1.2 } }), Speed = NumberRange.new(3, 6), LightEmission = 0.8, ZOffset = 2,
            Transparency = seq({ { 0, 0.2 }, { 1, 0.8 } }), SpreadAngle = Vector2.new(35, 35), Drag = 1.2,
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120) }),
        emitter(soul, { Name = "GroundRing", Texture = TEX.SoulRing, Color = tint, Rate = 4, Lifetime = NumberRange.new(2, 3),
            Size = seq({ { 0, 6 }, { 1, 10 } }), Speed = NumberRange.new(0.01), LightEmission = 0.4, ZOffset = -1,
            Transparency = seq({ { 0, 0.3 }, { 1, 1 } }), Orientation = flat.Orientation, EmissionDirection = flat.EmissionDirection,
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-20, 20) }),
    }
    local shock = emitter(burst, { Name = "EnergyShockwave", Texture = TEX.SoulShock, Color = tint, Rate = 0,
        Lifetime = NumberRange.new(0.6, 0.8), Size = seq({ { 0, 1 }, { 1, 12 } }), Speed = NumberRange.new(0.5), LightEmission = 1,
        ZOffset = 3, Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Orientation = flat.Orientation, EmissionDirection = flat.EmissionDirection,
        Rotation = NumberRange.new(0, 360) })
    table.insert(emitters, shock)
    table.insert(spinners, { kind = "soul", root = root, emitters = emitters, shock = shock, speed = 0, angle = 0, clock = 0 })
    bodyGlow(root, fx, main, 0.13 - 0.05 * p, 0.86 - 0.03 * p, 1.65 + 0.3 * p, 16 + 2 * p)
end

-- Realm 4, Spirit Soul: the owner's design (2026-11-03). Smoke rings the ground at the feet; three
-- spheres of black smoke revolve round the character in a fixed triangle (a third of a circle
-- apart on one tilted path, 4.2 studs out), rising and dipping together. The smoke is locked
-- inside each sphere, so it holds its shape. Its star stays at the centre of the smoke, riding
-- with the sphere and turning steadily; a crackling electric ring (PDS) hugs the cloud's edge, with bursts
-- flashing from the rim. Star and lightning are on a billboard, so they draw over the smoke (the
-- owner: "the lightning should be the edge of the cloud, not the cloud overlapping it"). The spiral wisps rise round
-- the body; nothing sits on its middle.
-- Under the feet, the Soul Seal lies still.
-- The owner's own body aura (designed on workspace.AuraWorkbench, approved 2026-11-03: "now that's
-- perfect"), added over the whole body of every realm, on top of the realm's own layers (the owner:
-- "Apply that as default to all aura"): a smoke of the realm's colour over a black smoke, sparks of
-- both, a few star glints. The smoke follows the level (the owner: "Weaker qi fainter smoke, Higher
-- Qi bigger smoke"): faint and small at the first realm, exactly the approved look at Realm 4's
-- middle sub-rank (t = 0.31), denser and larger towards Eternal. Every body part emits (a Box volume emits through the part). An R6 part's
-- rate is split across its R15 pieces by height, so an R15 body is as dense as an R6 one (one rate
-- per piece made it 2.5x too much). The emitters sit on the body parts, outside fx, so they go when
-- fx goes.
local BODY_SHARE = {
    Head = 1, UpperTorso = 0.81, LowerTorso = 0.19,
    LeftUpperArm = 0.46, LeftLowerArm = 0.42, LeftHand = 0.12,
    RightUpperArm = 0.46, RightLowerArm = 0.42, RightHand = 0.12,
    LeftUpperLeg = 0.46, LeftLowerLeg = 0.44, LeftFoot = 0.10,
    RightUpperLeg = 0.46, RightLowerLeg = 0.44, RightFoot = 0.10,
    Torso = 1, ["Left Arm"] = 1, ["Right Arm"] = 1, ["Left Leg"] = 1, ["Right Leg"] = 1,
}

local BODY_COLOR = {
    [3] = Color3.fromRGB(0, 190, 120),     -- the owner's jade for Spirit Core (the config's gold was rejected)
    [6] = Color3.fromRGB(255, 240, 200),   -- Immortal: its beam's warm white, not pure white (glare)
    [8] = Color3.fromRGB(120, 40, 200),    -- Cosmic: its violet, not the white its gradient ends in
    [10] = Color3.fromRGB(200, 230, 255),  -- Heavenly Dao: its beam's pale blue, not near-white
}

-- a at the first realm (t = 0), b at Realm 4's middle sub-rank (the approved look), c at t = 1
local function byLevel(t, a, b, c)
    if t <= 0.31 then
        return a + (b - a) * t / 0.31
    end
    return b + (c - b) * math.min(1, (t - 0.31) / 0.69)
end

local function bodyAura(root, fx, color, t)
    local glow = ColorSequence.new(color)
    local black = ColorSequence.new(Color3.new(0, 0, 0))
    local spread = byLevel(t, 45, 60, 75)
    local function smoke(c, light, peak, z)
        return { Texture = TEX.BodySmoke, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8,
            FlipbookFramerate = NumberRange.new(10, 40), FlipbookStartRandom = true, Color = c, LightEmission = light,
            Brightness = 3, LightInfluence = 0, Size = seq({ { 0, byLevel(t, 0.9, 1.2, 1.8) }, { 1, byLevel(t, 2.4, 4, 6.5) } }),
            Transparency = seq({ { 0, peak + (1 - peak) * 0.97 }, { 0.2, peak }, { 1, 1 } }),
            Lifetime = NumberRange.new(byLevel(t, 0.5, 0.6, 0.8), byLevel(t, 0.9, 1.1, 1.4)),
            Speed = NumberRange.new(byLevel(t, 1, 1.5, 2.5), byLevel(t, 3, 4.5, 6.5)), SpreadAngle = Vector2.new(spread, spread), Drag = 2.5,
            Rotation = NumberRange.new(-360, 360), Orientation = Enum.ParticleOrientation.VelocityParallel, ZOffset = z }
    end
    local function spark(c, light)
        return { Texture = TEX.BodySpark, Color = c, LightEmission = light, Brightness = 3, LightInfluence = 0,
            Size = seq({ { 0, 0 }, { 0.05, 0.5 }, { 1, 0 } }), Transparency = NumberSequence.new(0),
            Lifetime = NumberRange.new(0.4, 0.9), Speed = NumberRange.new(2, 9), SpreadAngle = Vector2.new(90, 90), Drag = 2.5,
            Rotation = NumberRange.new(-360, 360), Orientation = Enum.ParticleOrientation.VelocityParallel }
    end
    local layers = {
        { "BodySmoke", 25, smoke(glow, 1, byLevel(t, 0.62, 0.3, 0.15), -1) },
        { "BodyShadow", 5, smoke(black, 0, byLevel(t, 0.78, 0.5, 0.4), -1.5) },          -- the dark core under the colour
        { "BodySpark", 12, spark(glow, 1) },
        { "BodyAsh", 12, spark(black, 0) },
        -- a glint that flashes three or four times in its short life
        { "BodyStar", 3, { Texture = TEX.BodyStar, Color = glow, LightEmission = 1, Brightness = 3, LightInfluence = 0,
            Size = seq({ { 0, 0 }, { 0.04, 0.3 }, { 0.099, 0.313 }, { 0.118, 2.2 }, { 0.131, 0.25 }, { 0.245, 0.188 }, { 0.263, 1.6 },
                { 0.284, 0.188 }, { 0.493, 0.125 }, { 0.508, 1.37 }, { 0.526, 0.063 }, { 0.705, 0.063 }, { 0.723, 1 }, { 0.739, 0.063 }, { 1, 0 } }),
            Transparency = NumberSequence.new(0), Lifetime = NumberRange.new(0.1, 0.5), Speed = NumberRange.new(0, 9),
            SpreadAngle = Vector2.new(360, 360), Drag = 2.5, Rotation = NumberRange.new(45), ZOffset = 1 } },
    }
    local made = {}
    local function dress(part)
        local share = BODY_SHARE[part.Name]
        if not share or not part:IsA("BasePart") or part:FindFirstChild("BodySmoke") then
            return
        end
        for _, layer in layers do
            local e = emitter(part, layer[3])
            e.Name = layer[1]
            e.Rate = math.floor(layer[2] * share * 10 + 0.5) / 10
            table.insert(made, e)
        end
    end
    local model = root.Parent
    for _, part in model:GetChildren() do
        dress(part)
    end
    -- with streaming on, a far body part can reach the client after the build, or stream out and
    -- come back as a new part: dress it when it arrives
    local arrived = model.ChildAdded:Connect(dress)
    fx.Destroying:Connect(function()
        arrived:Disconnect()
        for _, e in made do
            e:Destroy()
        end
    end)
end

local function realm4(root, fx, tint, p)
    local main = lastColor(tint)
    local black = ColorSequence.new(Color3.fromRGB(18, 10, 28))
    local bright = ColorSequence.new(main:Lerp(Color3.new(1, 1, 1), 0.45))
    local GAP = math.tau / 3                           -- a triangle: a third of a circle apart
    local balls = {}
    for i = 1, 3 do
        -- a small invisible part that the spinner moves, its X axis along the path (the links' beams
        -- curve along it); everything on it rides with it
        local ball = Instance.new("Part")
        ball.Name = "SmokeOrb"
        ball.Anchored, ball.CanCollide, ball.CanQuery, ball.CanTouch = true, false, false, false
        ball.Transparency = 1
        ball.Size = Vector3.new(0.2, 0.2, 0.2)
        ball.CFrame = root.CFrame
        ball.Parent = fx
        local orb = Instance.new("Attachment")
        orb.Parent = ball
        emitter(orb, { Name = "OrbSmoke", Texture = TEX.SmokePuff, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
            FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = black, LightEmission = 0, LightInfluence = 0, LockedToPart = true, ZOffset = -1.5,
            Size = NumberSequence.new(2.95 + 0.13 * p), Transparency = NumberSequence.new(0.15),
            Lifetime = NumberRange.new(1.2, 1.6), Rate = 10 + 2 * p, Speed = NumberRange.new(0.05, 0.15), SpreadAngle = Vector2.new(180, 180),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40) })
        -- the star and the lightning: billboard images on the sphere (a billboard draws over the smoke,
        -- which hid them as particles, and still hides behind the body). The lightning plays its 16
        -- frames through a clipping window; the star turns slowly
        local gui = Instance.new("BillboardGui")
        gui.Name = "OrbCore"
        gui.Adornee = ball
        gui.Size = UDim2.fromScale(2.6 + 0.2 * p, 2.6 + 0.2 * p)
        gui.LightInfluence = 0
        gui.Brightness = 2.4
        gui.MaxDistance = 250
        gui.StudsOffset = Vector3.new(0, 0, 1.6)      -- toward the camera: always drawn over the smoke
        gui.Parent = ball
        emitter(orb, { Name = "OrbGlow", Texture = TEX.SmokePuff, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
            FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = tint, LightEmission = 0.5, LightInfluence = 0, LockedToPart = true, ZOffset = -1.5,
            Size = NumberSequence.new(4 + 0.25 * p), Transparency = NumberSequence.new(0.55),
            Lifetime = NumberRange.new(1.3, 1.7), Rate = 6, Speed = NumberRange.new(0.05, 0.15), SpreadAngle = Vector2.new(180, 180),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30) })
        -- the lightning (the owner: "a ring or better lightning"): a crackling electric ring hugging the
        -- cloud's edge, a fainter one turning the other way, and bursts flashing out from the rim
        local function image(id, size, z)
            local img = Instance.new("ImageLabel")
            img.BackgroundTransparency = 1
            img.AnchorPoint = Vector2.new(0.5, 0.5)
            img.Position = UDim2.fromScale(0.5, 0.5)
            img.Size = UDim2.fromScale(size, size)
            img.Image = id
            img.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.55)
            img.ZIndex = z
            img.Parent = gui
            return img
        end
        local ringA = image(TEX.ElectricRing, 0.88, 1)
        local ringB = image(TEX.ElectricRing, 0.78, 1)
        ringB.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.2)
        local spark = image(TEX.BoltBurst, 0.42, 1)
        spark.Visible = false
        local star = Instance.new("ImageLabel")
        star.BackgroundTransparency = 1
        star.AnchorPoint = Vector2.new(0.5, 0.5)
        star.Position = UDim2.fromScale(0.5, 0.5)
        star.Size = UDim2.fromScale(1, 1)
        star.ZIndex = 3
        star.ImageTransparency = 0.5                  -- softer (the owner: "increase the light transparency of the star")

        star.Image = TEX.OrbStar
        star.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.85)
        star.ZIndex = 2
        star.Parent = gui
        table.insert(balls, orb)
        table.insert(spinners, { kind = "orb", ball = ball, ringA = ringA, ringB = ringB, spark = spark, boltClock = 0,
            sparkAt = math.random() * 0.5, star = star, root = root, speed = 1.4 + 0.3 * p,
            angle = -(i - 1) * GAP, tilt = 0.3, radius = 4.2, height = 0.4, clock = 0 })
    end
    -- the Soul Seal: the ground circle under the aura (our own). It stays still under the feet (the
    -- owner: "don't rotate the ground ring"); it only follows the character
    local seal = Instance.new("Part")
    seal.Name = "SoulSeal"
    seal.Anchored, seal.CanCollide, seal.CanQuery, seal.CanTouch = true, false, false, false
    seal.Transparency = 1
    seal.Size = Vector3.new(9.6, 0.05, 9.6)
    seal.CFrame = root.CFrame * CFrame.new(0, -2.95, 0)
    local sealGui = Instance.new("SurfaceGui")
    sealGui.Face = Enum.NormalId.Top
    sealGui.LightInfluence = 0
    sealGui.Brightness = 1.3 + 0.3 * p
    sealGui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    sealGui.PixelsPerStud = 60
    sealGui.Parent = seal
    local sealImage = Instance.new("ImageLabel")
    sealImage.BackgroundTransparency = 1
    sealImage.Size = UDim2.fromScale(1, 1)
    sealImage.Image = TEX.SoulSeal
    sealImage.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.2)
    sealImage.ImageTransparency = 0.35 - 0.1 * p
    sealImage.Parent = sealGui
    seal.Parent = fx
    -- two ground smokes rippling out past the seal (the owner: "2 different type of smoke in the
    -- ground, bigger than the circle, like a ripple"):
    -- 1. the ripple: a wispy ring of smoke lying flat, expanding from 6 to ~19 studs as it fades
    local rippleHost = host(fx, root, 0.1, 0.1, -2.85)
    local ripple = emitter(rippleHost, { Name = "SmokeRipple", Texture = TEX.SmokeRipple,
        Color = ColorSequence.new(Color3.fromRGB(150, 95, 230)), LightEmission = 0.45, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        -- (the owner: "twice the size of the ground ring": it had reached 2.7 times)
        -- (the owner: "trim the smoke similar to the distance of vortex": out to 7.5, not 14.2)
        Size = seq({ { 0, 2 }, { 1, 7.5 } }), Transparency = seq({ { 0, 1 }, { 0.12, 0.3 }, { 0.6, 0.55 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1.6, 1.9), Rate = 1.8 + 0.4 * p, Speed = NumberRange.new(0.01),  -- the owner: more, faster
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-12, 12) })
    -- 2. the rolling mist: billowy torn puffs born round the seal's rim, lying flat just above the
    -- ground and swelling outward as they turn and fade. Flat, because a camera-facing puff this
    -- low dips into the floor, which cuts it with a hard straight line (Roblox has no soft particles)
    local mistHost = Instance.new("Part")
    mistHost.Name = "EmitterHost"
    mistHost.Anchored, mistHost.CanCollide, mistHost.CanQuery, mistHost.CanTouch = true, false, false, false
    mistHost.Transparency = 1
    mistHost.Size = Vector3.new(4.6, 0.1, 4.6)               -- trimmed to the vortex (it was 9.4)
    mistHost.CFrame = root.CFrame * CFrame.new(0, -2.88, 0)
    mistHost.Parent = fx
    local mist = emitter(mistHost, { Name = "GroundSmoke", Texture = TEX.SmokePuff,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        Color = ColorSequence.new(Color3.fromRGB(115, 75, 180)), LightEmission = 0.2, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume, ShapePartial = 0.6,
        Size = seq({ { 0, 2 }, { 1, 4.2 } }), Transparency = seq({ { 0, 1 }, { 0.15, 0.1 }, { 0.7, 0.35 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2.4, 3), Rate = 10 + 2 * p, Speed = NumberRange.new(0.02),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30) })
    -- 3. the owner's vortex ripple (their idea, built on the AuraWorkbench, 2026-11-03): glinting
    -- rings swirling out from the feet over a dark cloud. On the ripple host, so it follows the floor.
    -- The rings grow fast and slow down as they pass the seal's rim, turn one way, and fade in and
    -- out (they had popped off); the cloud lies just under the seal, a dark ground for it (above it,
    -- an alpha cloud would cover the seal)
    local vortexAt = Instance.new("Attachment")
    vortexAt.Name = "Vortex"
    vortexAt.Parent = rippleHost
    local cloudAt = Instance.new("Attachment")
    cloudAt.Name = "VortexCloud"
    cloudAt.Position = Vector3.new(0, -0.13, 0)              -- 0.02 above the floor, below the seal
    cloudAt.Parent = rippleHost
    local vortex = emitter(vortexAt, { Name = "VortexRings", Texture = TEX.VortexRings,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        -- Brightness 5 (the owner's 10 burned the thin rings white; 2 lost them on the seal)
        Color = ColorSequence.new(main), LightEmission = 1, Brightness = 5, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.01), SpreadAngle = Vector2.new(0, 0),
        -- the owner's own timing, which reads as a ripple: each ring grows steadily from the centre
        -- and stays whole until its flipbook breaks it up (eased, faded rings read as loose arcs).
        -- Smaller and denser than their first (the owner: "it spread too wide, reduce it, increase
        -- the rate"): out to 7 studs, not 10
        Size = seq({ { 0, 0 }, { 1, 7 } }), Transparency = seq({ { 0, 0 }, { 0.85, 0 }, { 1, 1 } }),
        Lifetime = NumberRange.new(0.8, 3), Rate = 22 + 4 * p, Rotation = NumberRange.new(-360, 360), RotSpeed = NumberRange.new(5),
        ZOffset = 0.2 })
    emitter(cloudAt, { Name = "VortexCloud", Texture = TEX.VortexCloud,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        Color = ColorSequence.new(main:Lerp(Color3.new(0, 0, 0), 0.72)), LightEmission = 0, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.01), SpreadAngle = Vector2.new(0, 0),
        Size = NumberSequence.new(12), Transparency = seq({ { 0, 1 }, { 0.15, 0.2 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2.5, 4), Rate = 2.5, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(10),
        ZOffset = -0.5 })
    -- the ground pieces (the seal, the mist, the ripples) follow the floor under the feet, so they sit
    -- on slopes and steps. (The ground wind that raced out across the floor was removed at the
    -- owner's word, 2026-11-03: "REMOVE THE GROUND WIND".)
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = { root.Parent, fx }
    table.insert(spinners, { kind = "ground", root = root, fx = fx, rayParams = rayParams,
        grounded = { { seal, 0.03, true }, { mistHost, 0.08, false }, { rippleHost, 0.15, false } },
        rayClock = 0, speed = 0, angle = 0 })
    -- the ground smoke follows meditation (the owner): calm while idle, the ripple quickening and the
    -- mist rushing out while the player cultivates (the player's IsCultivating; a test dummy's own
    -- attribute), easing between the two
    table.insert(spinners, { kind = "meditate", root = root, model = root.Parent, ripple = ripple, mist = mist, vortex = vortex, k = -1,
        p = p, speed = 0, angle = 0 })
    -- the spiral wisps from the owner's first layout, rising round the body (from a ring, not the middle)
    emitter(host(fx, root, 2, 0.2, -1), { Name = "Wisps", Texture = TEX.SoulWisp, Color = tint, Rate = 12 + 6 * p,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, EmissionDirection = Enum.NormalId.Top,
        Lifetime = NumberRange.new(1, 1.8), Size = seq({ { 0, 0.5 }, { 1, 1.2 } }), Speed = NumberRange.new(3, 6), LightEmission = 0.6,
        Transparency = seq({ { 0, 0.3 }, { 1, 1 } }), SpreadAngle = Vector2.new(20, 20), Drag = 1.2,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120) })
    bodyGlow(root, fx, main, 0.13 - 0.05 * p, 0.86 - 0.03 * p, 1.65 + 0.3 * p, 16 + 2 * p)
end

local function build(root, tier, sub)
    tier = math.clamp(tier or 1, 1, 12)
    sub = math.clamp(sub or 1, 1, 5)
    local config = AuraConfig.Tiers[tier]
    local old = root:FindFirstChild("ActiveAuraFX")
    if old then old:Destroy() end
    local fx = Instance.new("Folder")
    fx.Name = "ActiveAuraFX"
    fx.Parent = root

    local p = (sub - 1) / 5                   -- the sub-rank: 0 (Initiate) to 0.8 (Peak)
    local t = (tier - 1 + p) / 11             -- the level: 0 at the first realm, 1 at the last's base
    local function rate(base)
        return math.min(MAX_RATE, base)
    end
    local mid, high = tier >= 3, tier >= 7
    local tint = config.Color
    local light = math.clamp(config.LightEmission, 0, 1)

    local core = Instance.new("Attachment")
    core.Name = "Core"
    core.Parent = root

    -- the owner's body aura, on every realm (its colour and scale by realm and level)
    bodyAura(root, fx, BODY_COLOR[tier] or lastColor(tint), t)

    -- the glow close to the torso (in front of the body: behind it, the body hides it), or a dark
    -- void core inside a bright rim
    if VOID_CORE[tier] then
        emitter(core, { Texture = TEX.Glow, Color = ColorSequence.new(Color3.fromRGB(4, 2, 12)), LightEmission = 0,
            Size = seq({ { 0, 2.6 + 0.6 * t }, { 1, 3.2 + 0.8 * t } }), Transparency = seq({ { 0, 0.15 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.6, 0.9), Rate = rate(8), Speed = NumberRange.new(0), LockedToPart = true, ZOffset = 1 })
        if tier ~= 12 then emitter(core, { Texture = TEX.Ring, Color = tint, LightEmission = 1, Size = seq({ { 0, 4.5 + 1 * t }, { 1, 7 + 1.5 * t } }),
            Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Lifetime = NumberRange.new(0.7, 1), Rate = rate(6),
            Speed = NumberRange.new(0), LockedToPart = true, Rotation = NumberRange.new(0, 360), ZOffset = 0.5 }) end
    elseif tier == 1 then
        realm1(root, fx, tint, p)
    elseif tier == 2 then
        realm2(root, fx, tint, p)
    elseif tier == 3 then
        realm3(root, fx, tint, p)
    elseif tier == 4 then
        realm4(root, fx, tint, p)
    else
        emitter(core, { Texture = TEX.Glow, Color = tint, LightEmission = if mid then 1 else 0.6,
            Size = seq({ { 0, 4.5 + 2 * t }, { 1, 5.5 + 2.5 * t } }),
            Transparency = seq({ { 0, 0.4 - 0.15 * t }, { 0.5, 0.55 }, { 1, 1 } }), Lifetime = NumberRange.new(0.8, 1.2),
            Rate = rate(6 + 4 * t), Speed = NumberRange.new(0), LockedToPart = true, ZOffset = 1.5 })
    end

    -- glints rising round the body (Realms 1 to 4 have their own)
    if tier > 4 then emitter(host(fx, root, 1.9, 5, -0.4), { Texture = TEX.Glow, Color = tint, LightEmission = light,
        Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, Size = seq({ { 0, 0 }, { 0.2, 0.6 + 0.3 * t }, { 1, 0 } }),
        Transparency = seq({ { 0, 0 }, { 1, 1 } }), Lifetime = NumberRange.new(1.2, 1.8), Rate = rate(10 + 30 * t),
        Speed = NumberRange.new(0.3), Acceleration = Vector3.new(0, 2.5 + 3 * t, 0) }) end

    local feet = host(fx, root, 2.3, 0.2, -2.9) -- a ring at the feet

    -- mid: a stream of streaks rising from the ring. A Disc emits along its axis (a Cylinder emits
    -- out through its sides, along the floor); the streak image is upright, so it faces the camera
    -- world-up (VelocityParallel laid it flat)
    if mid and tier > 4 then -- (Realms 3 and 4 have their own)
        emitter(feet, { Texture = TEX.Streak, Color = tint, LightEmission = light, Orientation = Enum.ParticleOrientation.FacingCameraWorldUp,
            Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 2 + 1.2 * t }, { 1, 0.4 } }), Transparency = seq({ { 0, 0 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.5, 0.9), Rate = rate(14 + 30 * t),
            Speed = NumberRange.new(6 + 4 * t, 10 + 5 * t), EmissionDirection = Enum.NormalId.Top })
    end

    -- ribbon arcs orbiting the body: one from Spirit Soul, two from Immortal, three from Heavenly Dao;
    -- one beside a signature piece, none round the top two realms' rigs
    local ribbons = if TOP[tier] then 0
        elseif SIGNATURE[tier] and hasMesh(SIGNATURE[tier].mesh) then 1
        elseif tier >= 10 then 3 elseif tier >= 6 then 2 elseif tier >= 5 then 1 else 0
    for i = 1, ribbons do
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Parent, a1.Parent = root, root
        local beam = Instance.new("Beam")
        beam.Attachment0, beam.Attachment1 = a0, a1
        beam.Texture = TEX.Ribbon
        beam.TextureMode = Enum.TextureMode.Stretch
        beam.TextureSpeed = 0.8 + 2 * t
        beam.Color = ColorSequence.new((config.BeamColor or lastColor(tint)):Lerp(Color3.new(1, 1, 1), 0.25))
        beam.LightEmission = 1
        beam.Transparency = seq({ { 0, 1 }, { 0.2, 0.05 }, { 0.8, 0.05 }, { 1, 1 } })
        local width = 0.9 + 0.9 * t
        beam.Width0, beam.Width1 = width, width
        beam.CurveSize0, beam.CurveSize1 = 2.2 + t, -(2.2 + t)
        beam.Segments = 24
        beam.Parent = root
        table.insert(spinners, { kind = "ribbon", a0 = a0, a1 = a1,
            speed = (1.55 + 1.65 * t) * (if i % 2 == 0 then -1 else 1),
            height = ({ 0.4, -0.9, 1.6 })[i], tilt = ({ 0.25, -0.35, 0.5 })[i], radius = 2.4 + 0.25 * i + 0.5 * t,
            angle = i * 2.1, root = root })
    end

    -- high: a turning ground sigil (a second ring from Heavenly Dao) and a rising column
    if high then
        for ring = 1, if tier >= 10 then 2 else 1 do
            local disc = Instance.new("Part")
            disc.Name = "Sigil"
            disc.Anchored, disc.CanCollide, disc.CanQuery, disc.CanTouch = true, false, false, false
            disc.Transparency = 1
            local size = (if ring == 1 then 9 else 13) + 4 * t
            disc.Size = Vector3.new(size, 0.05, size)
            disc.CFrame = root.CFrame * CFrame.new(0, -2.95, 0)
            local gui = Instance.new("SurfaceGui")
            gui.Face = Enum.NormalId.Top
            gui.LightInfluence = 0
            gui.Brightness = 1.5 + 2 * t
            gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
            gui.PixelsPerStud = 40
            gui.Parent = disc
            local image = Instance.new("ImageLabel")
            image.BackgroundTransparency = 1
            image.Size = UDim2.fromScale(1, 1)
            image.Image = if ring == 1 then (if tier == 10 then TEX.DaoRunes else TEX.Formation) else TEX.Ring
            image.ImageColor3 = lastColor(tint)
            image.ImageTransparency = if ring == 1 then 0.15 else 0.4
            image.Parent = gui
            disc.Parent = fx
            table.insert(spinners, { kind = "sigil", part = disc, root = root, speed = (if ring == 1 then 0.5 else -0.8) * (1 + 0.4 * t), angle = 0 })
        end
        -- the column; the top two realms' rigs rise their own way (law streaks, nebula), and their pale
        -- colours turn a column into a white wall over the body
        if not TOP[tier] then
            emitter(feet, { Texture = TEX.Glitter, Color = tint, LightEmission = light, Shape = Enum.ParticleEmitterShape.Disc,
                ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, Size = seq({ { 0, 0 }, { 0.3, 2 + 1 * t }, { 1, 0 } }),
                Transparency = seq({ { 0, 0.15 }, { 1, 1 } }), Lifetime = NumberRange.new(1, 1.6), Rate = rate(24 + 30 * t),
                Speed = NumberRange.new(5, 8 + 4 * t), EmissionDirection = Enum.NormalId.Top,
                Rotation = NumberRange.new(0, 360) })
        end
    end
    -- the realm's own piece grows a little through its sub-ranks (it isn't carried past a breakthrough)
    local grow = 1 + 0.3 * p
    if TOP[tier] then
        topTier(root, tier, fx, tint, grow, grow, p)
    elseif SIGNATURE[tier] then
        signature(root, SIGNATURE[tier], fx, grow)
    end
end

function signature(root, sig, fx, grow)
    local part = meshPart(sig.mesh, fx, root)
    if not part then
        return
    end
    part.Material, part.Color, part.Transparency = sig.material, sig.color, sig.transparency
    table.insert(spinners, { kind = sig.kind, part = part, root = root, offset = MESHES[sig.mesh], speed = sig.speed * grow,
        angle = 0, clock = 0, base = sig.transparency })
    if sig.edge then
        -- a slightly larger copy in a shimmering field, turning with it: the shards' glowing edges
        local edge = meshPart(sig.mesh, fx, root)
        edge.Size *= sig.edge.scale
        edge.Material, edge.Color, edge.Transparency = sig.edge.material, sig.edge.color, 0
        table.insert(spinners, { kind = sig.kind, part = edge, root = root, offset = MESHES[sig.mesh], speed = sig.speed * grow, angle = 0 })
    end
end

function topTier(root, tier, fx, tint, sizeK, speedK, p)
    local main = lastColor(tint)
    if tier == 10 then
        -- the law: a cone band of runes, rings turning against it, shards drifting, and streaks of law into the sky
        local outer = meshPart("DaoRing_Outer", fx, root)
        if outer then
            outer.Material = Enum.Material.ForceField
            outer.TextureID = TEX.DaoRunes
            outer.Color = Color3.fromRGB(150, 210, 255)
            outer.Transparency = 0 -- the templates are hidden; each copy sets its own
            table.insert(spinners, { kind = "mesh", part = outer, root = root, offset = MESHES.DaoRing_Outer, speed = 0.35 * speedK, angle = 0 })
        end
        local inner = meshPart("DaoRing_Inner", fx, root)
        if inner then
            inner.Material = Enum.Material.Neon
            inner.Color = Color3.fromRGB(205, 232, 255)
            inner.Transparency = 0.25
            table.insert(spinners, { kind = "mesh", part = inner, root = root, offset = MESHES.DaoRing_Inner, speed = -0.6 * speedK, angle = 0 })
        end
        local pillars = meshPart("LawPillars", fx, root)
        if pillars then
            pillars.Material = Enum.Material.Neon
            pillars.Color = Color3.fromRGB(225, 240, 255)
            pillars.Transparency = 0.35
            table.insert(spinners, { kind = "bob", part = pillars, root = root, offset = MESHES.LawPillars, speed = 0.2 * speedK, angle = 0, clock = 0 })
        end
        emitter(host(fx, root, 3, 0.2, -2.9), { Texture = TEX.LawStreak, Color = ColorSequence.new(Color3.fromRGB(225, 240, 255)),
            LightEmission = 1, Orientation = Enum.ParticleOrientation.FacingCameraWorldUp, Shape = Enum.ParticleEmitterShape.Disc,
            ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, Size = seq({ { 0, 0.7 * sizeK }, { 1, 0.4 * sizeK } }),
            Transparency = seq({ { 0, 0.1 }, { 0.7, 0.3 }, { 1, 1 } }), Lifetime = NumberRange.new(0.6, 0.9),
            Rate = math.min(MAX_RATE, 14 * (1 + p)), Speed = NumberRange.new(45 * speedK, 70 * speedK), EmissionDirection = Enum.NormalId.Top })
    else
        -- eternity: a breathing event horizon of nebula, two knots of light in orbit, a crown behind the head
        local horizon = meshPart("EventHorizon", fx, root)
        if horizon then
            horizon.Material = Enum.Material.ForceField
            horizon.TextureID = TEX.Nebula
            horizon.Color = Color3.fromRGB(255, 120, 230)
            table.insert(spinners, { kind = "breathe", part = horizon, root = root, offset = MESHES.EventHorizon, speed = 0.25, angle = 0, clock = 0 })
        end
        local helices = meshPart("OrbitalHelices", fx, root)
        if helices then
            helices.Material = Enum.Material.Neon
            helices.Color = Color3.fromRGB(255, 225, 150)
            helices.Transparency = 0.15
            table.insert(spinners, { kind = "mesh", part = helices, root = root, offset = MESHES.OrbitalHelices, speed = 0.9 * speedK, angle = 0 })
        end
        local crown = meshPart("TranscendenceCrown", fx, root)
        if crown then
            crown.Material = Enum.Material.Neon
            crown.Color = Color3.fromRGB(255, 236, 190)
            crown.Transparency = 0.1
            table.insert(spinners, { kind = "crown", part = crown, root = root, offset = MESHES.TranscendenceCrown, speed = 0.4 * speedK, angle = 0 })
        end
        -- cosmic depth round the core
        emitter(root:FindFirstChild("Core") or root, { Texture = TEX.Nebula, Color = tint, LightEmission = 0.6,
            Size = seq({ { 0, 5 * sizeK }, { 1, 7 * sizeK } }), Transparency = seq({ { 0, 1 }, { 0.3, 0.55 }, { 1, 1 } }),
            Lifetime = NumberRange.new(2, 3), Rate = 2.5, Speed = NumberRange.new(0), LockedToPart = true,
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-15, 15), ZOffset = 0.8 })
    end
end

-- the test's measuring hook: the layers built for (tier, sub), read back as numbers (built on a
-- temporary root, removed after)
local LAYER = { -- by emitter texture and where it sits
    Core = { Glow = "glow", Ring = "rim", Nebula = "nebula" },
    Host = { Glow = "glints", Streak = "stream", Glitter = "column", LawStreak = "law" },
}
local measure = Instance.new("BindableFunction")
measure.Name = "AuraTestMeasure"
measure.OnInvoke = function(tier, sub)
    local root = Instance.new("Part")
    root.Name = "MeasureRoot"
    root.Anchored, root.CanCollide, root.CanQuery, root.Transparency = true, false, false, 1
    root.CFrame = CFrame.new(0, -400, 0)
    root.Parent = script.Parent
    build(root, tier, sub)
    local texName = {}
    for k, v in TEX do
        texName[v] = k
    end
    local out, total, ribbons = {}, 0, 0
    for _, x in root:GetDescendants() do
        if x:IsA("ParticleEmitter") then
            local layer = LAYER[if x.Parent:IsA("Attachment") then "Core" else "Host"][texName[x.Texture]]
                or texName[x.Texture] or x.Texture
            if layer == "glow" and x.LightEmission == 0 then
                layer = "void"
            end
            local size = 0
            for _, k in x.Size.Keypoints do
                size = math.max(size, k.Value)
            end
            out[layer .. ".rate"], out[layer .. ".size"], out[layer .. ".speed"] = x.Rate, size, x.Speed.Max
            total += x.Rate
        elseif x:IsA("Beam") then
            ribbons += 1
            out["ribbon.width"], out["ribbon.scroll"], out["ribbon.curve"] = x.Width0, x.TextureSpeed, x.CurveSize0
        elseif x:IsA("SurfaceGui") and x.Parent.Name == "Sigil" then
            local ring = if x:FindFirstChildOfClass("ImageLabel").Image == TEX.Ring then "sigil2" else "sigil1"
            out[ring .. ".size"], out[ring .. ".bright"] = x.Parent.Size.X, x.Brightness
        end
    end
    for i = #spinners, 1, -1 do
        local s = spinners[i]
        if s.root == root then
            if s.kind == "ribbon" then
                out["ribbon.speed"], out["ribbon.radius"] = math.abs(s.speed), s.radius
            end
            table.remove(spinners, i)
        end
    end
    root:Destroy()
    out.totalRate, out.ribbons = total, ribbons
    return out
end
measure.Parent = script.Parent

-- test only: the Realm 4 dummies can't meditate, so they toggle their own IsCultivating every 6 s
-- (in the game it is the player's attribute, set by QiService)
task.spawn(function()
    local on = false
    while script.Parent do
        for _, d in script.Parent:GetDescendants() do
            if d:IsA("Model") and d:GetAttribute("CultivationTier") == 4 then
                d:SetAttribute("IsCultivating", on)
            end
        end
        on = not on
        task.wait(6 / (script.Parent:GetAttribute("TimeScale") or 1))
    end
end)

-- every dummy in this folder and its sub-folders (the sub-rank range)
for _, dummy in script.Parent:GetDescendants() do
    if dummy:IsA("Model") and dummy:GetAttribute("CultivationTier") then
        build(dummy:WaitForChild("HumanoidRootPart"), dummy:GetAttribute("CultivationTier"), dummy:GetAttribute("SubRank"))
    end
end

game:GetService("UserInputService").InputBegan:Connect(function(input, processed)
    if processed or input.KeyCode ~= Enum.KeyCode.E then
        return
    end
    for _, s in spinners do
        if s.kind == "soul" then s.shock:Emit(40) end
    end
end)

-- test only: slow motion for review. Set the AuraTestRange's TimeScale attribute (0.05 to 1) on the
-- client: particles, beam scrolling, trail life and every spinner follow it
local function slowMo(inst, k)
    if inst:IsA("ParticleEmitter") then
        inst.TimeScale = k
    elseif inst:IsA("Beam") then
        local base = inst:GetAttribute("BaseTextureSpeed")
        if base == nil then
            base = inst.TextureSpeed
            inst:SetAttribute("BaseTextureSpeed", base)
        end
        inst.TextureSpeed = base * k
    elseif inst:IsA("Trail") then
        local base = inst:GetAttribute("BaseLifetime")
        if base == nil then
            base = inst.Lifetime
            inst:SetAttribute("BaseLifetime", base)
        end
        inst.Lifetime = math.min(20, base / k)
    end
end
local function timeScale()
    return math.clamp(script.Parent:GetAttribute("TimeScale") or 1, 0.05, 1)
end
script.Parent:GetAttributeChangedSignal("TimeScale"):Connect(function()
    local k = timeScale()
    for _, inst in script.Parent:GetDescendants() do
        slowMo(inst, k)
    end
end)
script.Parent.DescendantAdded:Connect(function(inst)
    local k = timeScale()
    if k < 1 then
        slowMo(inst, k)
    end
end)

RunService.RenderStepped:Connect(function(dt)
    dt *= timeScale()
    for _, s in spinners do
        s.angle += dt * s.speed
        if s.kind == "ribbon" then
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            local a = s.angle
            s.a0.Position = tiltCF * Vector3.new(math.cos(a) * s.radius, s.height, math.sin(a) * s.radius)
            s.a1.Position = tiltCF * Vector3.new(math.cos(a + math.pi) * s.radius, s.height, math.sin(a + math.pi) * s.radius)
        elseif s.kind == "mesh" then        -- turning round the body
            s.part.CFrame = s.root.CFrame * CFrame.Angles(0, s.angle, 0) * CFrame.new(s.offset)
        elseif s.kind == "bob" then         -- turning slowly and drifting up and down
            s.clock += dt
            s.part.CFrame = s.root.CFrame * CFrame.Angles(0, s.angle, 0) * CFrame.new(s.offset + Vector3.new(0, math.sin(s.clock * 1.3) * 0.35, 0))
        elseif s.kind == "breathe" then     -- slowly turning, its field breathing
            s.clock += dt
            s.part.CFrame = s.root.CFrame * CFrame.Angles(0, s.angle, 0) * CFrame.new(s.offset)
            s.part.Transparency = 0.15 + 0.25 * (0.5 + 0.5 * math.sin(s.clock * 1.6))
        elseif s.kind == "flicker" then     -- turning slowly, its flames flickering
            s.clock += dt
            s.part.CFrame = s.root.CFrame * CFrame.Angles(0, s.angle, 0) * CFrame.new(s.offset)
            s.part.Transparency = s.base + 0.25 * (0.5 + 0.5 * math.noise(s.clock * 3, 0.5))
        elseif s.kind == "orbit" then       -- a tilted ring turning round the body
            s.part.CFrame = s.root.CFrame * CFrame.new(s.offset) * CFrame.Angles(s.tilt, 0, 0) * CFrame.Angles(0, s.angle, 0)
        elseif s.kind == "mist" then        -- a mist ribbon's head racing round its tilted circle
            s.clock += dt
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            local pos = tiltCF * Vector3.new(math.cos(s.angle) * s.radius, 0.3 + 0.6 * math.sin(s.clock * 1.3), math.sin(s.angle) * s.radius)
            local up = tiltCF * Vector3.yAxis
            local out = tiltCF * Vector3.new(math.cos(s.angle), 0, math.sin(s.angle))
            for _, L in s.layers do
                local across = if L.flat then out else up
                L.a0.Position = pos + across * L.hw
                L.a1.Position = pos - across * L.hw
            end
        elseif s.kind == "spirit" then      -- Realm 4's spirit, a step behind the body and out of step
            s.clock += dt
            local t = s.clock
            local sway = CFrame.new(math.sin(t * 0.8) * 0.15, 0.2 + math.sin(t * 1.1) * 0.1, 0.5) * CFrame.Angles(0, math.sin(t * 0.6) * 0.06, 0)
            local base = s.root.CFrame * sway
            local shimmer = s.base + 0.05 * math.sin(t * math.pi / 4)
            for _, pr in s.pairs do
                local rel = s.root.CFrame:ToObjectSpace(pr.part.CFrame)
                pr.copy.CFrame = base * (rel - rel.Position) + base:VectorToWorldSpace(rel.Position * 1.1)
                pr.copy.Transparency = shimmer
            end
        elseif s.kind == "soul" then        -- Realm 4: the timed burst (the dummies' E) and the owner's culling
            s.clock += dt
            local near = (workspace.CurrentCamera.CFrame.Position - s.root.Position).Magnitude <= CULL_DISTANCE
            for _, e in s.emitters do
                if e.Name ~= "EnergyShockwave" then e.Enabled = near end
            end
            if s.clock >= 4 then
                s.clock = 0
                if near then s.shock:Emit(40) end
            end
        elseif s.kind == "orb" then         -- a smoke orb racing round its tilted circle, rising and dipping
            s.clock += dt
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            local pos = tiltCF * Vector3.new(math.cos(s.angle) * s.radius, s.height + 0.5 * math.sin(s.clock * 1.2), math.sin(s.angle) * s.radius)
            local tangent = tiltCF * Vector3.new(-math.sin(s.angle), 0, math.cos(s.angle))
            s.ball.CFrame = s.root.CFrame * CFrame.fromMatrix(pos, tangent, tiltCF * Vector3.yAxis)
            -- the electric rings: spinning, with a small jump and a flicker every few frames (crackle)
            s.boltClock += dt
            if s.boltClock >= 0.06 then
                s.boltClock = 0
                s.ringA.Rotation = (s.ringA.Rotation + 35 + math.random() * 50) % 360
                s.ringA.ImageTransparency = 0.05 + math.random() * 0.3
                local j = 0.86 + math.random() * 0.05
                s.ringA.Size = UDim2.fromScale(j, j)
                s.ringB.Rotation = (s.ringB.Rotation - 20 - math.random() * 40) % 360
                s.ringB.ImageTransparency = 0.45 + math.random() * 0.4
            end
            -- a burst flashes out from a random point on the rim for a moment
            s.sparkAt -= dt
            if s.sparkAt <= 0 then
                if s.spark.Visible then
                    s.spark.Visible = false
                    s.sparkAt = 0.25 + math.random() * 0.5
                else
                    local a = math.random() * math.pi * 2
                    s.spark.Position = UDim2.fromScale(0.5 + math.cos(a) * 0.42, 0.5 + math.sin(a) * 0.42)
                    s.spark.Rotation = math.deg(a) + 90
                    s.spark.Visible = true
                    s.sparkAt = 0.08 + math.random() * 0.06
                end
            end
        elseif s.kind == "seal" then        -- Realm 4's seal: still, following the character
            s.part.CFrame = s.root.CFrame * CFrame.new(0, -2.95, 0)
        elseif s.kind == "meditate" then    -- Realm 4's ground smoke: idle or meditating
            local player = s.model and Players:GetPlayerFromCharacter(s.model)
            local on = if player then player:GetAttribute("IsCultivating") == true
                else s.model ~= nil and s.model:GetAttribute("IsCultivating") == true
            local target = if on then 1 else 0
            local k = if s.k < 0 then target else s.k + (target - s.k) * math.min(1, dt * 3)
            if math.abs(k - s.k) > 0.002 then
                s.k = k
                local function mix(a, b) return a + (b - a) * k end
                s.ripple.Rate = mix(2 + 0.3 * s.p, 3.5 + 0.5 * s.p)                -- the owner: "faster loop ripple"
                s.ripple.Lifetime = NumberRange.new(mix(1.5, 0.9), mix(1.7, 1.1))
                s.mist.Rate = mix(9 + 2 * s.p, 16 + 3 * s.p)                      -- denser (the owner)
                s.mist.Lifetime = NumberRange.new(mix(3.2, 1.9), mix(3.8, 2.3))   -- shorter: swells out faster
                local spin = mix(20, 55)
                s.mist.RotSpeed = NumberRange.new(-spin, spin)
                if s.vortex then                                              -- the owner's vortex quickens and spins up
                    s.vortex.Rate = mix(22 + 4 * s.p, 30 + 5 * s.p)
                    s.vortex.Lifetime = NumberRange.new(mix(0.8, 0.6), mix(3, 2.2))
                    s.vortex.RotSpeed = NumberRange.new(mix(5, 12))
                end
            end
        elseif s.kind == "ground" then      -- Realm 4's ground pieces kept on the floor under the feet
            if s.fx.Parent then
                s.rayClock -= dt
                if s.rayClock <= 0 then                                      -- the floor under the feet, 10 times a second
                    s.rayClock = 0.1
                    local centre = s.root.Position
                    local hit = workspace:Raycast(centre, Vector3.new(0, -12, 0), s.rayParams)
                    local groundY = if hit then hit.Position.Y else centre.Y - 3
                    local _, yaw = s.root.CFrame:ToOrientation()
                    for _, g in s.grounded do
                        local cf = CFrame.new(centre.X, groundY + g[2], centre.Z)
                        g[1].CFrame = if g[3] then cf * CFrame.fromOrientation(0, yaw, 0) else cf
                    end
                end
            end
        elseif s.kind == "gyro" then        -- a tilted ring: turning in its plane, its tilt swinging round
            s.spin += dt * s.spinSpeed
            s.part.CFrame = s.root.CFrame * CFrame.new(s.offset) * CFrame.Angles(0, s.angle, 0) * CFrame.Angles(s.tilt, 0, 0) * CFrame.Angles(0, s.spin, 0)
        elseif s.kind == "arc" then         -- a Qi thread circling the body: both ends on the circle
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            for j, at in { s.a0, s.a1 } do
                local ang = s.angle + (j - 1) * s.span
                local pos = Vector3.new(math.cos(ang) * s.radius, s.height, math.sin(ang) * s.radius)
                local tangent = Vector3.new(-math.sin(ang), 0, math.cos(ang))
                at.CFrame = tiltCF * CFrame.fromMatrix(pos, tangent, Vector3.yAxis)
            end
        elseif s.kind == "outline" then     -- Realm 1's outline, breathing (4 s in, 4 s out)
            s.clock += dt
            local out = 0.5 + 0.5 * math.cos(s.clock * math.pi / 4)
            s.highlight.OutlineTransparency = s.line + 0.18 * out
            s.highlight.FillTransparency = s.fill + 0.04 * out
            s.light.Brightness = s.glow * (1 - 0.35 * out)
        elseif s.kind == "crown" then       -- turning in its own plane, behind the head
            s.part.CFrame = s.root.CFrame * CFrame.new(s.offset) * CFrame.Angles(0, 0, s.angle)
        else
            s.part.CFrame = s.root.CFrame * CFrame.new(0, -2.95, 0) * CFrame.Angles(0, s.angle, 0)
        end
    end
end)

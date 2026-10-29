
-- How the cultivation aura looks. Purely visual: nothing here affects Qi or
-- progression.
--
-- The selected aura pet decides the aura's ELEMENT (colours, shapes, motion).
-- The cultivation rank decides its TIER (size, layers and intensity).
-- Every rank keeps the pet's element, so a top-rank Aqua Wisp aura still looks aquatic.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local AuraStyles = {}

-- Elements, keyed by pet ID in GameConfig.Pets ("Neutral" = no aura pet selected)
--   Core / Main / Deep    Brightest, main and darkest colours
--   RingShape             "Circle", or "Polygon" with RingSides straight edges
--   RingWidth, GlowWidth  Ring line and soft glow widths in studs (before rank scaling)
--   TrailLifetime         Seconds of light trail behind orbs (0 = no trails)
--   Spin                  Speed multiplier for rings and streams
--   Sway                  Degrees the rings gently rock back and forth (0 = steady)
--   Flicker               The aura's light flickers like fire
--   Streams               Rising energy: "Spiral", "Flame", "Ribbon" or "Pulse"
--   FlowSeconds           Seconds for a bright comet to travel up a stream (lower = faster)
--   CometWidth            Width of those comets' light trails, in studs
--   Particles             "Mote", "Ember", "Droplet", "Crystal" or "Spark" (also sets the hand effects)
--   Sigil                 Ground pattern: "Rune", "Flame", "Ripple" or "Lattice"
--   Crown                 Top-rank formation: "Halo", "FlameCrown", "MoonHalo" or "CrystalCrown"
--   WispOpacity           How visible the soft rising mist is (0 to 1)
--   RiseLines             Fast streaks of light shooting straight up (at higher ranks)
--   Shell                 The aura's main silhouette: tongues of energy wrapping the body
--     Width, TipWidth       Tongue width at the base and tip (studs, before rank scaling)
--     Opacity               How solid the tongues are (keep low so the character stays visible)
--     Curve                 How much tongues bulge as they rise (0 = straight shards)
--     Lean, Twist           How much tongues lean and wrap around the body (Twist in radians)
--     TipRadius             Tip distance from the centre, compared with the base (below 1 = taper inward)
--     HeightVariety         How much tongue heights differ from each other (0 to 1)
--     Sway, SwaySpeed, Stretch  Tip movement: side to side, how fast, and up and down
--     Spin                  How fast the whole shell drifts around the body
--     FlowSpeed             How fast energy flows up through each tongue
--     TipColor              "Core", "Main" or "Deep": the colour tongues fade to at the tip
AuraStyles.Elements = {
    Neutral = {
        Core = Color3.fromRGB(235, 248, 255),
        Main = Color3.fromRGB(125, 200, 255),
        Deep = Color3.fromRGB(55, 120, 210),
        RingShape = "Circle",
        RingWidth = 0.14,
        GlowWidth = 0.45,
        TrailLifetime = 0.8,
        Spin = 1,
        Sway = 0,
        Flicker = false,
        Streams = "Spiral",
        FlowSeconds = 2.2,
        CometWidth = 0.35,
        Particles = "Mote",
        Sigil = "Rune",
        Crown = "Halo",
        WispOpacity = 0.3,
        RiseLines = true,
        Shell = {
            Width = 1.1, TipWidth = 0.1, Opacity = 0.35, Curve = 0.4, Lean = 0.2, Twist = 0.35,
            TipRadius = 0.9, HeightVariety = 0.15, Sway = 0.35, SwaySpeed = 0.6, Stretch = 0.2,
            Spin = 0.25, FlowSpeed = 1.5, TipColor = "Core",
        },
    },

    -- Fire: warm flame tongues that lick upward, drifting embers, a flickering glow
    EmberWyrm = {
        Core = Color3.fromRGB(255, 205, 110),
        Main = Color3.fromRGB(255, 125, 35),
        Deep = Color3.fromRGB(215, 45, 20),
        RingShape = "Circle",
        RingWidth = 0.18,
        GlowWidth = 0.55,
        TrailLifetime = 0.6,
        Spin = 1.4,
        Sway = 0,
        Flicker = true,
        Streams = "Flame",
        FlowSeconds = 1.4,
        CometWidth = 0.45,
        Particles = "Ember",
        Sigil = "Flame",
        Crown = "FlameCrown",
        WispOpacity = 0.28,
        RiseLines = true,
        -- Jagged, flickering flames that taper inward like a bonfire
        Shell = {
            Width = 1.4, TipWidth = 0.04, Opacity = 0.45, Curve = 0.35, Lean = 0.1, Twist = 0.2,
            TipRadius = 0.8, HeightVariety = 0.35, Sway = 0.55, SwaySpeed = 1.4, Stretch = 0.45,
            Spin = 0.35, FlowSpeed = 3, TipColor = "Deep",
        },
    },

    -- Water: wide flowing ribbons, gently rocking rings, droplets and ripples
    AquaWisp = {
        Core = Color3.fromRGB(165, 232, 255),
        Main = Color3.fromRGB(55, 185, 255),
        Deep = Color3.fromRGB(35, 85, 215),
        RingShape = "Circle",
        RingWidth = 0.16,
        GlowWidth = 0.7,
        TrailLifetime = 1.4,
        Spin = 0.8,
        Sway = 8,
        Flicker = false,
        Streams = "Ribbon",
        FlowSeconds = 3.2,
        CometWidth = 0.5,
        Particles = "Droplet",
        Sigil = "Ripple",
        Crown = "Halo",
        WispOpacity = 0.3,
        RiseLines = false,
        -- Rounded tongues that curl around the body like breaking waves
        Shell = {
            Width = 1.2, TipWidth = 0.35, Opacity = 0.38, Curve = 0.5, Lean = 0.8, Twist = 0.9,
            TipRadius = 0.95, HeightVariety = 0.1, Sway = 0.4, SwaySpeed = 0.5, Stretch = 0.15,
            Spin = 0.45, FlowSpeed = 1.6, TipColor = "Core",
        },
    },

    -- Nature and heaven: slow, steady hexagonal rings in jade and gold, rising
    -- hexagonal pulses and crystal glints
    GoldenKirin = {
        Core = Color3.fromRGB(235, 225, 140),
        Main = Color3.fromRGB(110, 210, 105),
        Deep = Color3.fromRGB(205, 160, 50),
        RingShape = "Polygon",
        RingSides = 6,
        RingWidth = 0.16,
        GlowWidth = 0.4,
        TrailLifetime = 0,
        Spin = 0.5,
        Sway = 0,
        Flicker = false,
        Streams = "Pulse",
        FlowSeconds = 2.8,
        CometWidth = 0.3,
        Particles = "Crystal",
        Sigil = "Lattice",
        Crown = "CrystalCrown",
        WispOpacity = 0.25,
        RiseLines = false,
        -- Straight antler-like shards of alternating height that flare slightly outward
        Shell = {
            Width = 1.3, TipWidth = 0, Opacity = 0.55, Curve = 0, Lean = 0, Twist = 0,
            TipRadius = 1.2, HeightVariety = 0.4, Sway = 0, SwaySpeed = 0, Stretch = 0,
            Spin = 0.08, FlowSpeed = 0.8, TipColor = "Main",
        },
    },

    -- Lightning: fast, jittery shards of yellow light with violet edges,
    -- quick comets, crackling arcs of electricity and a flickering glow
    VoltFox = {
        Core = Color3.fromRGB(255, 240, 120),
        Main = Color3.fromRGB(255, 215, 60),
        Deep = Color3.fromRGB(150, 95, 255),
        RingShape = "Circle",
        RingWidth = 0.14,
        GlowWidth = 0.45,
        TrailLifetime = 0.35,
        Spin = 2,
        Sway = 0,
        Flicker = true,
        Streams = "Spiral",
        FlowSeconds = 0.9,
        CometWidth = 0.3,
        Particles = "Spark",
        Sigil = "Rune",
        Crown = "Halo",
        WispOpacity = 0.15,
        RiseLines = true,
        -- Thin, straight, uneven shards that twitch quickly like arcs of electricity
        Shell = {
            Width = 0.9, TipWidth = 0, Opacity = 0.42, Curve = 0.05, Lean = 0.15, Twist = 0.1,
            TipRadius = 0.85, HeightVariety = 0.5, Sway = 0.7, SwaySpeed = 3, Stretch = 0.5,
            Spin = 0.6, FlowSpeed = 4, TipColor = "Deep",
        },
    },

    -- Moonlight: pale silver-violet tails that sweep around the body, slow
    -- ribbons, soft motes, ripples and a crescent halo
    NineTailMoonfox = {
        Core = Color3.fromRGB(225, 210, 255),
        Main = Color3.fromRGB(195, 175, 255),
        Deep = Color3.fromRGB(110, 85, 215),
        RingShape = "Circle",
        RingWidth = 0.14,
        GlowWidth = 0.6,
        TrailLifetime = 1.6,
        Spin = 0.7,
        Sway = 6,
        Flicker = false,
        Streams = "Ribbon",
        FlowSeconds = 3,
        CometWidth = 0.45,
        Particles = "Mote",
        Sigil = "Ripple",
        Crown = "MoonHalo",
        WispOpacity = 0.32,
        RiseLines = false,
        -- Long, curving tails that lean and wrap around the body
        Shell = {
            Width = 1, TipWidth = 0.2, Opacity = 0.36, Curve = 0.6, Lean = 0.9, Twist = 1.1,
            TipRadius = 1.05, HeightVariety = 0.2, Sway = 0.5, SwaySpeed = 0.45, Stretch = 0.2,
            Spin = 0.3, FlowSpeed = 1.3, TipColor = "Core",
        },
    },

    -- Primordial: deep violet energy with ancient amber cores, octagonal
    -- rings, coiling serpent-like tongues and glyph sigils
    OriginSerpent = {
        Core = Color3.fromRGB(255, 200, 120),
        Main = Color3.fromRGB(165, 85, 235),
        Deep = Color3.fromRGB(70, 25, 120),
        RingShape = "Polygon",
        RingSides = 8,
        RingWidth = 0.16,
        GlowWidth = 0.5,
        TrailLifetime = 0.9,
        Spin = 0.9,
        Sway = 0,
        Flicker = false,
        Streams = "Spiral",
        FlowSeconds = 2,
        CometWidth = 0.4,
        Particles = "Mote",
        Sigil = "Rune",
        Crown = "Halo",
        WispOpacity = 0.3,
        RiseLines = true,
        -- Broad tongues that coil tightly around the body like a serpent
        Shell = {
            Width = 1.2, TipWidth = 0.06, Opacity = 0.42, Curve = 0.5, Lean = 0.6, Twist = 1.3,
            TipRadius = 0.85, HeightVariety = 0.25, Sway = 0.3, SwaySpeed = 0.5, Stretch = 0.25,
            Spin = 0.5, FlowSpeed = 2, TipColor = "Deep",
        },
    },
}

-- Aura tiers 1 to 5, from faint to most powerful. Each rank in GameConfig.Ranks
-- picks one with its AuraTier.
--   Size          Scales rings, streams and particles
--   Intensity     0 to 1: how bright and solid the lines are
--   Rings         How many rings from RingLayout are used (accents; the shell is the main shape)
--   Orbs          Orbs travelling on each ring, in RingLayout order
--   Streams       Rising streams (fire adds extra flame tongues; jade uses 1 or 2 rising pulses)
--   Flow          How long and bright the travelling comets are, and how fast the energy flows
--   ShellTongues, ShellHeight, ShellWidth  Number of shell tongues, their height (in character
--                 heights) and a width multiplier
--   RiseLines     Fast upward light streaks (for elements that use them)
--   SigilSize     Ground sigil diameter, in character heights
--   SigilDetail   1 to 5: how many sigil layers are drawn
--   Particles     Multiplier for particle amounts
--   Sparks        Occasional bursts of sparks
--   Crown         Shows the element's crown or halo above the head
--   Outline       Faint outline glow around the body
--   Light         Brightness of the soft local light
AuraStyles.Tiers = {
    { -- 1: faint glow
        Size = 1, Intensity = 0.75, Rings = 1, Orbs = { 2 }, Streams = 2, Flow = 1,
        ShellTongues = 4, ShellHeight = 1.1, ShellWidth = 0.75, RiseLines = 0,
        SigilSize = 2, SigilDetail = 1, Particles = 1, Sparks = false,
        Crown = false, Outline = false, Light = 0.8,
    },
    { -- 2
        Size = 1.08, Intensity = 0.85, Rings = 1, Orbs = { 3 }, Streams = 2, Flow = 1.15,
        ShellTongues = 5, ShellHeight = 1.2, ShellWidth = 0.85, RiseLines = 1,
        SigilSize = 2.3, SigilDetail = 2, Particles = 1.3, Sparks = false,
        Crown = false, Outline = false, Light = 1,
    },
    { -- 3: brighter, more particles
        Size = 1.15, Intensity = 0.9, Rings = 1, Orbs = { 3 }, Streams = 2, Flow = 1.3,
        ShellTongues = 6, ShellHeight = 1.35, ShellWidth = 0.95, RiseLines = 2,
        SigilSize = 2.6, SigilDetail = 3, Particles = 1.6, Sparks = false,
        Crown = false, Outline = false, Light = 1.15,
    },
    { -- 4: second ring, sparks
        Size = 1.22, Intensity = 0.95, Rings = 2, Orbs = { 4, 2 }, Streams = 3, Flow = 1.45,
        ShellTongues = 7, ShellHeight = 1.5, ShellWidth = 1.05, RiseLines = 3,
        SigilSize = 2.9, SigilDetail = 4, Particles = 1.9, Sparks = true,
        Crown = false, Outline = false, Light = 1.35,
    },
    { -- 5: crown and outline
        Size = 1.3, Intensity = 1, Rings = 2, Orbs = { 4, 3 }, Streams = 3, Flow = 1.6,
        ShellTongues = 8, ShellHeight = 1.7, ShellWidth = 1.2, RiseLines = 4,
        SigilSize = 3.3, SigilDetail = 5, Particles = 2.2, Sparks = true,
        Crown = true, Outline = true, Light = 1.5,
    },
}

-- Where rings sit, as fractions of the character's height (Height is
-- measured up from the feet). Spin is in radians per second; negative spins
-- the other way. Lower ranks use only the first rings.
AuraStyles.RingLayout = {
    { Height = 0.5, Radius = 0.78, TiltX = 6, TiltZ = 0, Spin = 0.7 }, -- Waist
    { Height = 0.12, Radius = 0.9, TiltX = -5, TiltZ = 4, Spin = -0.5 }, -- Around the feet, spinning the other way
    { Height = 0.85, Radius = 0.55, TiltX = -14, TiltZ = -8, Spin = 1.1 }, -- Chest (spare)
}

-- Per-player limits for the most elaborate aura (tier 5). In Studio,
-- AuraController warns if a built aura goes over any of them.
--   FrameUpdates counts properties changed every frame (positions, widths, light).
AuraStyles.Budget = {
    Beams = 88,
    ParticleEmitters = 16,
    Trails = 16,
    MovingParts = 10,
    FrameUpdates = 48,
    Lights = 1,
}

-- Breakthrough (rank-up) effect strength. AuraStyles.getBreakthrough picks
-- one from the rank being reached: Step for most levels, Milestone for each
-- realm's fifth level, NewRealm for the first level of a new realm.
-- The selected aura pet's element sets the colours and accents.
--   Duration      Seconds until everything is cleaned up
--   Scale         Overall size multiplier
--   Shockwaves    Ground shockwaves spreading outward, one after another
--   Rings         Expanding rings of energy around the body
--   Streaks       Fast streaks of light shooting upward
--   Burst         Particles released at the moment of breakthrough
--   PillarHeight  Height of the brief column of light in studs (0 = none)
--   Flash         Peak brightness of the brief flash of light
AuraStyles.Breakthroughs = {
    Step = { Duration = 1.6, Scale = 1, Shockwaves = 1, Rings = 1, Streaks = 4, Burst = 14, PillarHeight = 0, Flash = 3 },
    Milestone = { Duration = 2.4, Scale = 1.3, Shockwaves = 2, Rings = 2, Streaks = 8, Burst = 26, PillarHeight = 18, Flash = 5 },
    NewRealm = { Duration = 3, Scale = 1.5, Shockwaves = 3, Rings = 3, Streaks = 10, Burst = 32, PillarHeight = 26, Flash = 6 },
}

-- Per-breakthrough limits (for the biggest one). In Studio, AuraController
-- warns if a breakthrough goes over any of them.
AuraStyles.BreakthroughBudget = {
    Beams = 24,
    ParticleEmitters = 3,
    Trails = 10,
    Lights = 1,
    SurfaceGuis = 4,
}

-- Optional custom textures. Leave a slot as "" to use built-in effects.
-- tools/generate_aura_textures.py makes original textures in assets/aura.
-- To use them: in Studio open View > Asset Manager, import the PNGs, then
-- right-click each image > Copy Asset ID and paste it here as "rbxassetid://<number>".
--   EnergyStreak   Flowing streaks for energy tongues, streams and light trails
--   FlameFlipbook  Animated 4x4 flame frames for Ember Wyrm's fire
--   SoftGlow       Soft round glow for orbs, motes, droplets and bubbles
AuraStyles.CustomTextures = {
    EnergyStreak = "",
    FlameFlipbook = "",
    SoftGlow = "",
}

-- The aura tier for a rank Id (the lowest tier if the rank is unknown)
function AuraStyles.getTier(rankId)
    local rank = Ranks.getRankById(rankId)
    return AuraStyles.Tiers[if rank then rank.AuraTier else 1]
end

-- The breakthrough played when a player reaches this rank Id
function AuraStyles.getBreakthrough(rankId)
    local rank = Ranks.getRankById(rankId)
    if rank and rank.Level == 1 then
        return AuraStyles.Breakthroughs.NewRealm
    elseif rank and rank.Level == 5 then
        return AuraStyles.Breakthroughs.Milestone
    end
    return AuraStyles.Breakthroughs.Step
end

-- Catch config mistakes as soon as the game starts
for _, rank in GameConfig.Ranks do
    assert(AuraStyles.Tiers[rank.AuraTier], "Rank " .. rank.Id .. " has an AuraTier with no entry in AuraStyles.Tiers")
end

for index, tier in AuraStyles.Tiers do
    assert(tier.Rings <= #AuraStyles.RingLayout, "AuraStyles: tier " .. index .. " uses more rings than RingLayout has")
end

for elementId in AuraStyles.Elements do
    assert(elementId == "Neutral" or GameConfig.Pets[elementId], "AuraStyles.Elements has an unknown pet ID: " .. elementId)
end

for petId in GameConfig.Pets do
    assert(AuraStyles.Elements[petId], "AuraStyles.Elements has no element for pet " .. petId)
end

return AuraStyles

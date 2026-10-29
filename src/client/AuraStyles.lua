-- How cultivation auras and breakthroughs look. Purely visual: nothing here
-- affects Qi or progression.
--
-- Auras are being rebuilt one element at a time (see AuraStyles.Auras and
-- AuraBuilder). An element without an entry in Auras shows no aura yet.
-- The old aura system is in git history (commit 0ca3d48) and the unfinished
-- Golden Kirin version in tools/aura_archive.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local AuraStyles = {}

-- Each element's colours, keyed by pet ID ("Neutral" = no aura pet selected).
-- Breakthrough (rank-up) effects use these too.
--   Core / Main / Deep   Brightest, main and darkest colours
--   Particles            Breakthrough burst style: "Mote", "Ember", "Droplet", "Crystal" or "Spark"
--   RingShape            Breakthrough rings: "Circle", or "Polygon" with RingSides edges
AuraStyles.Elements = {
    Neutral = { Core = Color3.fromRGB(235, 248, 255), Main = Color3.fromRGB(125, 200, 255), Deep = Color3.fromRGB(55, 120, 210), Particles = "Mote", RingShape = "Circle" },
    EmberWyrm = { Core = Color3.fromRGB(255, 205, 110), Main = Color3.fromRGB(255, 125, 35), Deep = Color3.fromRGB(215, 45, 20), Particles = "Ember", RingShape = "Circle" },
    AquaWisp = { Core = Color3.fromRGB(165, 232, 255), Main = Color3.fromRGB(55, 185, 255), Deep = Color3.fromRGB(35, 85, 215), Particles = "Droplet", RingShape = "Circle" },
    GoldenKirin = { Core = Color3.fromRGB(255, 236, 170), Main = Color3.fromRGB(245, 190, 70), Deep = Color3.fromRGB(80, 210, 160), Particles = "Crystal", RingShape = "Polygon", RingSides = 6 },
    VoltFox = { Core = Color3.fromRGB(255, 240, 120), Main = Color3.fromRGB(255, 215, 60), Deep = Color3.fromRGB(150, 95, 255), Particles = "Spark", RingShape = "Circle" },
    NineTailMoonfox = { Core = Color3.fromRGB(225, 210, 255), Main = Color3.fromRGB(195, 175, 255), Deep = Color3.fromRGB(110, 85, 215), Particles = "Mote", RingShape = "Circle" },
    OriginSerpent = { Core = Color3.fromRGB(215, 255, 245), Main = Color3.fromRGB(60, 210, 180), Deep = Color3.fromRGB(35, 95, 120), Particles = "Mote", RingShape = "Polygon", RingSides = 8 },
    MossGolem = { Core = Color3.fromRGB(200, 230, 140), Main = Color3.fromRGB(110, 165, 75), Deep = Color3.fromRGB(110, 85, 55), Particles = "Mote", RingShape = "Polygon", RingSides = 5 },
    MyceliumSprite = { Core = Color3.fromRGB(190, 255, 235), Main = Color3.fromRGB(70, 215, 195), Deep = Color3.fromRGB(80, 90, 190), Particles = "Mote", RingShape = "Circle" },
    JadeSpiritPanda = { Core = Color3.fromRGB(215, 255, 225), Main = Color3.fromRGB(70, 200, 135), Deep = Color3.fromRGB(25, 70, 55), Particles = "Crystal", RingShape = "Circle" },
    JadeAntlerDeer = { Core = Color3.fromRGB(235, 255, 175), Main = Color3.fromRGB(165, 215, 80), Deep = Color3.fromRGB(150, 110, 60), Particles = "Mote", RingShape = "Circle" },
    MagmaCub = { Core = Color3.fromRGB(255, 185, 80), Main = Color3.fromRGB(235, 80, 25), Deep = Color3.fromRGB(70, 30, 25), Particles = "Ember", RingShape = "Circle" },
    SunscaleDragon = { Core = Color3.fromRGB(255, 245, 170), Main = Color3.fromRGB(255, 195, 50), Deep = Color3.fromRGB(235, 115, 30), Particles = "Ember", RingShape = "Polygon", RingSides = 12 },
    DawnPhoenix = { Core = Color3.fromRGB(255, 225, 140), Main = Color3.fromRGB(255, 115, 55), Deep = Color3.fromRGB(215, 35, 85), Particles = "Ember", RingShape = "Circle" },
    LunarHopper = { Core = Color3.fromRGB(225, 220, 255), Main = Color3.fromRGB(150, 140, 255), Deep = Color3.fromRGB(85, 80, 200), Particles = "Mote", RingShape = "Circle" },
    AstralWhale = { Core = Color3.fromRGB(195, 225, 255), Main = Color3.fromRGB(90, 125, 255), Deep = Color3.fromRGB(135, 75, 225), Particles = "Mote", RingShape = "Circle" },
}

-- The cultivation auras, keyed by pet ID. Textures were rendered in Blender
-- (tools/blender/<Pet>Aura.blend, PNGs in assets/aura/<pet>) and uploaded.
-- AquaWisp: six glowing droplets orbiting in a gentle spiral, sparkling
-- water motes and tiny bubbles drifting around the body, and a soft cyan glow.
--   Droplets          How many droplets orbit
--   OrbitRadius       Orbit distance from the body's centre line, as a share of body height
--   OrbitSeconds      Seconds for one full orbit
--   SpiralTurn        How far each droplet's height drifts up and down (share of body height)
--   DropletSize       Glowing core diameter in studs; GlowSize the soft halo around it
--   TrailSeconds      How long each droplet's trail lingers
--   SparkleRate, BubbleRate   Particles per second (multiplied by the rank's AuraTier boost)
--   LightBrightness, LightRange   The soft cyan light on the body
--   BodyGlow          How strongly the body is tinted by the glow (0 = off, 1 = solid)
AuraStyles.Auras = {
    AquaWisp = {
        Core = Color3.fromRGB(225, 250, 255),
        Main = Color3.fromRGB(70, 210, 255),
        Deep = Color3.fromRGB(20, 120, 235),
        Droplets = 6,
        OrbitRadius = 0.6,
        OrbitSeconds = 4.2,
        SpiralTurn = 0.12,
        DropletSize = 0.5,
        GlowSize = 1.35,
        TrailSeconds = 0.75,
        SparkleRate = 12,
        BubbleRate = 4,
        LightBrightness = 1.4,
        LightRange = 11,
        BodyGlow = 0.12,
        Textures = {
            Glow = "rbxassetid://135169457468310",
            Sparkle = "rbxassetid://90854757913450",
            Bubble = "rbxassetid://113245936322739",
            Trail = "rbxassetid://85921257601970",
        },
    },
}

-- Rank boost: higher AuraTier ranks get a slightly denser, brighter aura
function AuraStyles.getBoost(rankId)
    local rank = Ranks.getRankById(rankId)
    local tier = if rank then rank.AuraTier else 1
    return 1 + (tier - 1) * 0.15
end

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

for petId in GameConfig.Pets do
    assert(AuraStyles.Elements[petId], "AuraStyles.Elements has no colours for pet " .. petId)
end
for petId in AuraStyles.Auras do
    assert(AuraStyles.Elements[petId], "AuraStyles.Auras has an aura for an unknown pet: " .. petId)
end

return AuraStyles

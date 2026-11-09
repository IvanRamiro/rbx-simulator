local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local AuraStyles = {}

AuraStyles.Elements = {
    Neutral = { Core = Color3.fromRGB(235, 248, 255), Main = Color3.fromRGB(125, 200, 255), Deep = Color3.fromRGB(55, 120, 210), Particles = "Mote", RingShape = "Circle" },
    EmberWyrm = { Core = Color3.fromRGB(255, 205, 110), Main = Color3.fromRGB(255, 125, 35), Deep = Color3.fromRGB(215, 45, 20), Particles = "Ember", RingShape = "Circle" },
    AquaWisp = { Core = Color3.fromRGB(165, 232, 255), Main = Color3.fromRGB(55, 185, 255), Deep = Color3.fromRGB(35, 85, 215), Particles = "Droplet", RingShape = "Circle" },
    GoldenKirin = { Core = Color3.fromRGB(255, 244, 206), Main = Color3.fromRGB(245, 190, 70), Deep = Color3.fromRGB(210, 140, 40), Particles = "Crystal", RingShape = "Polygon", RingSides = 6 },
    VoltFox = { Core = Color3.fromRGB(255, 240, 120), Main = Color3.fromRGB(255, 215, 60), Deep = Color3.fromRGB(150, 95, 255), Particles = "Spark", RingShape = "Circle" },
    NineTailMoonfox = { Core = Color3.fromRGB(225, 210, 255), Main = Color3.fromRGB(195, 175, 255), Deep = Color3.fromRGB(110, 85, 215), Particles = "Mote", RingShape = "Circle" },
    OriginSerpent = { Core = Color3.fromRGB(200, 240, 255), Main = Color3.fromRGB(150, 100, 255), Deep = Color3.fromRGB(40, 30, 140), Particles = "Mote", RingShape = "Polygon", RingSides = 8 },
    MossGolem = { Core = Color3.fromRGB(200, 230, 140), Main = Color3.fromRGB(110, 165, 75), Deep = Color3.fromRGB(110, 85, 55), Particles = "Mote", RingShape = "Polygon", RingSides = 5 },
    MyceliumSprite = { Core = Color3.fromRGB(190, 255, 235), Main = Color3.fromRGB(70, 215, 195), Deep = Color3.fromRGB(80, 90, 190), Particles = "Mote", RingShape = "Circle" },
    JadeSpiritPanda = { Core = Color3.fromRGB(215, 255, 225), Main = Color3.fromRGB(70, 200, 135), Deep = Color3.fromRGB(25, 70, 55), Particles = "Crystal", RingShape = "Circle" },
    JadeAntlerDeer = { Core = Color3.fromRGB(235, 255, 175), Main = Color3.fromRGB(165, 215, 80), Deep = Color3.fromRGB(150, 110, 60), Particles = "Mote", RingShape = "Circle" },
    MagmaCub = { Core = Color3.fromRGB(255, 185, 80), Main = Color3.fromRGB(235, 80, 25), Deep = Color3.fromRGB(70, 30, 25), Particles = "Ember", RingShape = "Circle" },
    SunscaleDragon = { Core = Color3.fromRGB(255, 245, 170), Main = Color3.fromRGB(255, 195, 50), Deep = Color3.fromRGB(235, 115, 30), Particles = "Ember", RingShape = "Polygon", RingSides = 12 },
    DawnPhoenix = { Core = Color3.fromRGB(255, 225, 140), Main = Color3.fromRGB(255, 115, 55), Deep = Color3.fromRGB(215, 35, 85), Particles = "Ember", RingShape = "Circle" },
    LunarHopper = { Core = Color3.fromRGB(225, 220, 255), Main = Color3.fromRGB(150, 140, 255), Deep = Color3.fromRGB(85, 80, 200), Particles = "Mote", RingShape = "Circle" },
    AstralWhale = { Core = Color3.fromRGB(195, 225, 255), Main = Color3.fromRGB(90, 125, 255), Deep = Color3.fromRGB(135, 75, 225), Particles = "Mote", RingShape = "Circle" },
    WindSprite = { Core = Color3.fromRGB(220, 255, 245), Main = Color3.fromRGB(120, 230, 200), Deep = Color3.fromRGB(50, 150, 140), Particles = "Mote", RingShape = "Circle" },
    CloudSheep = { Core = Color3.fromRGB(240, 250, 255), Main = Color3.fromRGB(150, 210, 245), Deep = Color3.fromRGB(120, 125, 200), Particles = "Mote", RingShape = "Circle" },
    SpiritCrane = { Core = Color3.fromRGB(225, 250, 250), Main = Color3.fromRGB(60, 215, 205), Deep = Color3.fromRGB(30, 110, 120), Particles = "Mote", RingShape = "Circle" },
    AzureSkyDragon = { Core = Color3.fromRGB(220, 245, 255), Main = Color3.fromRGB(90, 170, 255), Deep = Color3.fromRGB(40, 80, 200), Particles = "Spark", RingShape = "Circle" },
    StormhornKirin = { Core = Color3.fromRGB(255, 250, 200), Main = Color3.fromRGB(150, 160, 255), Deep = Color3.fromRGB(70, 60, 170), Particles = "Spark", RingShape = "Polygon", RingSides = 6 },
    GlacierPuff = { Core = Color3.fromRGB(240, 252, 255), Main = Color3.fromRGB(150, 215, 255), Deep = Color3.fromRGB(80, 140, 220), Particles = "Crystal", RingShape = "Circle" },
    StormBumblebee = { Core = Color3.fromRGB(255, 250, 200), Main = Color3.fromRGB(255, 220, 80), Deep = Color3.fromRGB(170, 110, 255), Particles = "Spark", RingShape = "Circle" },
    CrystalBeetle = { Core = Color3.fromRGB(220, 250, 255), Main = Color3.fromRGB(130, 220, 255), Deep = Color3.fromRGB(90, 60, 170), Particles = "Crystal", RingShape = "Polygon", RingSides = 6 },
    GravityImp = { Core = Color3.fromRGB(240, 210, 255), Main = Color3.fromRGB(170, 100, 255), Deep = Color3.fromRGB(70, 30, 140), Particles = "Mote", RingShape = "Circle" },
    ThunderclawDrake = { Core = Color3.fromRGB(255, 250, 190), Main = Color3.fromRGB(255, 215, 60), Deep = Color3.fromRGB(120, 90, 220), Particles = "Spark", RingShape = "Circle" },
    FrostfangSerpent = { Core = Color3.fromRGB(240, 252, 255), Main = Color3.fromRGB(130, 210, 255), Deep = Color3.fromRGB(60, 120, 210), Particles = "Crystal", RingShape = "Polygon", RingSides = 6 },
    DreamMoth = { Core = Color3.fromRGB(255, 235, 250), Main = Color3.fromRGB(230, 170, 255), Deep = Color3.fromRGB(140, 90, 210), Particles = "Mote", RingShape = "Circle" },
    CrystalSnail = { Core = Color3.fromRGB(210, 255, 240), Main = Color3.fromRGB(110, 230, 200), Deep = Color3.fromRGB(40, 140, 130), Particles = "Crystal", RingShape = "Circle" },
    PrismArmadillo = { Core = Color3.fromRGB(240, 230, 255), Main = Color3.fromRGB(190, 150, 255), Deep = Color3.fromRGB(100, 80, 190), Particles = "Crystal", RingShape = "Polygon", RingSides = 8 },
    LanternWarden = { Core = Color3.fromRGB(255, 245, 200), Main = Color3.fromRGB(255, 200, 100), Deep = Color3.fromRGB(180, 110, 40), Particles = "Ember", RingShape = "Circle" },
    JadeWyrmTurtle = { Core = Color3.fromRGB(210, 255, 230), Main = Color3.fromRGB(80, 210, 150), Deep = Color3.fromRGB(30, 110, 80), Particles = "Crystal", RingShape = "Polygon", RingSides = 6 },
    EchoBat = { Core = Color3.fromRGB(230, 220, 255), Main = Color3.fromRGB(160, 140, 230), Deep = Color3.fromRGB(70, 60, 130), Particles = "Mote", RingShape = "Circle" },
    QiClockworkFinch = { Core = Color3.fromRGB(230, 255, 245), Main = Color3.fromRGB(210, 180, 110), Deep = Color3.fromRGB(120, 90, 50), Particles = "Spark", RingShape = "Polygon", RingSides = 8 },
    MoonfangTiger = { Core = Color3.fromRGB(240, 240, 255), Main = Color3.fromRGB(170, 175, 240), Deep = Color3.fromRGB(90, 95, 180), Particles = "Mote", RingShape = "Circle" },
    ThousandEyedGuardian = { Core = Color3.fromRGB(255, 240, 200), Main = Color3.fromRGB(230, 180, 90), Deep = Color3.fromRGB(120, 70, 150), Particles = "Mote", RingShape = "Polygon", RingSides = 8 },
    NinefoldSpiritSerpent = { Core = Color3.fromRGB(230, 255, 248), Main = Color3.fromRGB(120, 240, 200), Deep = Color3.fromRGB(50, 140, 140), Particles = "Mote", RingShape = "Circle" },
    WorldrootColossus = { Core = Color3.fromRGB(220, 255, 210), Main = Color3.fromRGB(120, 210, 100), Deep = Color3.fromRGB(60, 100, 50), Particles = "Crystal", RingShape = "Polygon", RingSides = 5 },
    SandPhantom = { Core = Color3.fromRGB(255, 240, 200), Main = Color3.fromRGB(225, 185, 110), Deep = Color3.fromRGB(150, 100, 50), Particles = "Mote", RingShape = "Circle" },
    SolarButterfly = { Core = Color3.fromRGB(255, 245, 190), Main = Color3.fromRGB(255, 190, 70), Deep = Color3.fromRGB(230, 110, 40), Particles = "Ember", RingShape = "Circle" },
    ObsidianGuardian = { Core = Color3.fromRGB(230, 200, 255), Main = Color3.fromRGB(150, 80, 240), Deep = Color3.fromRGB(50, 30, 90), Particles = "Crystal", RingShape = "Polygon", RingSides = 6 },
    GoldenManeLion = { Core = Color3.fromRGB(255, 245, 200), Main = Color3.fromRGB(255, 190, 70), Deep = Color3.fromRGB(210, 110, 30), Particles = "Ember", RingShape = "Polygon", RingSides = 12 },
    DreadfangCerberus = { Core = Color3.fromRGB(200, 250, 255), Main = Color3.fromRGB(40, 210, 255), Deep = Color3.fromRGB(40, 25, 90), Particles = "Ember", RingShape = "Circle" },
    BonefireDragon = { Core = Color3.fromRGB(225, 240, 255), Main = Color3.fromRGB(110, 175, 255), Deep = Color3.fromRGB(35, 60, 170), Particles = "Ember", RingShape = "Circle" },
    PrismaticPhoenix = { Core = Color3.fromRGB(255, 250, 240), Main = Color3.fromRGB(255, 150, 220), Deep = Color3.fromRGB(120, 120, 255), Particles = "Ember", RingShape = "Circle" },
    StarfallFox = { Core = Color3.fromRGB(255, 250, 220), Main = Color3.fromRGB(150, 160, 255), Deep = Color3.fromRGB(60, 60, 160), Particles = "Mote", RingShape = "Circle" },
    CosmicJellyfish = { Core = Color3.fromRGB(255, 230, 250), Main = Color3.fromRGB(200, 140, 255), Deep = Color3.fromRGB(90, 60, 190), Particles = "Mote", RingShape = "Circle" },
    NebulaOwl = { Core = Color3.fromRGB(245, 230, 255), Main = Color3.fromRGB(190, 140, 255), Deep = Color3.fromRGB(80, 50, 170), Particles = "Mote", RingShape = "Circle" },
    CelestialSnowLeopard = { Core = Color3.fromRGB(245, 250, 255), Main = Color3.fromRGB(160, 200, 255), Deep = Color3.fromRGB(90, 120, 210), Particles = "Crystal", RingShape = "Circle" },
    CometStag = { Core = Color3.fromRGB(235, 250, 255), Main = Color3.fromRGB(130, 200, 255), Deep = Color3.fromRGB(60, 70, 180), Particles = "Spark", RingShape = "Circle" },
    CelestialPearlDragon = { Core = Color3.fromRGB(255, 250, 235), Main = Color3.fromRGB(255, 215, 150), Deep = Color3.fromRGB(200, 150, 90), Particles = "Mote", RingShape = "Polygon", RingSides = 8 },
    EclipseCat = { Core = Color3.fromRGB(255, 235, 190), Main = Color3.fromRGB(230, 170, 90), Deep = Color3.fromRGB(40, 30, 70), Particles = "Mote", RingShape = "Circle" },
    TimekeeperTortoise = { Core = Color3.fromRGB(255, 245, 210), Main = Color3.fromRGB(230, 200, 120), Deep = Color3.fromRGB(110, 100, 70), Particles = "Mote", RingShape = "Polygon", RingSides = 12 },
    GalaxyManta = { Core = Color3.fromRGB(240, 225, 255), Main = Color3.fromRGB(150, 110, 255), Deep = Color3.fromRGB(50, 40, 150), Particles = "Mote", RingShape = "Circle" },
    Shadowcoil = { Core = Color3.fromRGB(220, 190, 255), Main = Color3.fromRGB(130, 70, 230), Deep = Color3.fromRGB(40, 20, 80), Particles = "Mote", RingShape = "Circle" },
    RuneSphinx = { Core = Color3.fromRGB(255, 240, 200), Main = Color3.fromRGB(255, 180, 80), Deep = Color3.fromRGB(60, 45, 30), Particles = "Mote", RingShape = "Polygon", RingSides = 4 },
    ThousandYearDreamEater = { Core = Color3.fromRGB(255, 230, 250), Main = Color3.fromRGB(200, 140, 255), Deep = Color3.fromRGB(90, 50, 160), Particles = "Mote", RingShape = "Circle" },
    HeavenbreakerApe = { Core = Color3.fromRGB(255, 245, 200), Main = Color3.fromRGB(255, 180, 70), Deep = Color3.fromRGB(150, 70, 30), Particles = "Ember", RingShape = "Circle" },
    AbyssAnomalocaris = { Core = Color3.fromRGB(255, 210, 240), Main = Color3.fromRGB(225, 50, 175), Deep = Color3.fromRGB(70, 30, 80), Particles = "Mote", RingShape = "Circle" },
    VoidscaleHydra = { Core = Color3.fromRGB(220, 190, 255), Main = Color3.fromRGB(120, 60, 240), Deep = Color3.fromRGB(30, 10, 80), Particles = "Mote", RingShape = "Circle" },
    TheNamelessOne = { Core = Color3.fromRGB(255, 255, 255), Main = Color3.fromRGB(200, 170, 255), Deep = Color3.fromRGB(40, 20, 90), Particles = "Mote", RingShape = "Polygon", RingSides = 8 },
    EternalClockworkDragon = { Core = Color3.fromRGB(235, 255, 255), Main = Color3.fromRGB(220, 190, 110), Deep = Color3.fromRGB(110, 80, 40), Particles = "Spark", RingShape = "Polygon", RingSides = 12 },
}

AuraStyles.Auras = {} -- per-pet aura styles (AuraBuilder); the old Aqua Wisp and Golden Kirin ones went with their old designs

AuraStyles.CharacterAura = {
    Textures = {
        Flame = "rbxassetid://125999209006478",
        Streak = "rbxassetid://122993805328140",
        Ring = "rbxassetid://81408609196943",
        Shockwave = "rbxassetid://81927825399672",
        Glow = "rbxassetid://118436603702034",
        Spark = "rbxassetid://112814194154292",
        Smoke = "rbxasset://textures/particles/smoke_main.dds",
    },
    ChargeSeconds = 1.3,
    Stages = {
        { Name = "Idle", After = 0, Power = 0.5, PulseEvery = 2.6 },
        { Name = "Charged", After = 6, Power = 0.78, PulseEvery = 1.8, LightningEvery = 2.6, Rocks = true },
        { Name = "Awakened", After = 15, Power = 1, PulseEvery = 1.2, LightningEvery = 1.1, SurgeEvery = 9, Rocks = true, Halo = true },
    },
    Tongues = 8,
    Ribbons = 3,
    Rocks = 7,
    Arcs = 3,
    OtherPlayers = 0.6,
}

function AuraStyles.getBoost(rankId)
    local rank = Ranks.getRankById(rankId)
    local tier = if rank then rank.AuraTier else 1
    return 1 + (tier - 1) * 0.15
end

AuraStyles.Breakthroughs = {
    Step = { Duration = 1.6, Scale = 1, Shockwaves = 1, Rings = 1, Streaks = 4, Burst = 14, PillarHeight = 0, Flash = 3 },
    Milestone = { Duration = 2.4, Scale = 1.3, Shockwaves = 2, Rings = 2, Streaks = 8, Burst = 26, PillarHeight = 18, Flash = 5 },
    NewRealm = { Duration = 3, Scale = 1.5, Shockwaves = 3, Rings = 3, Streaks = 10, Burst = 32, PillarHeight = 26, Flash = 6 },
}

-- Checked in Studio after each breakthrough (AuraController). A 12-sided ring element's realm
-- breakthrough uses 3 x 12 + 2 = 38 beams, for three seconds.
AuraStyles.BreakthroughBudget = {
    Beams = 40,
    ParticleEmitters = 3,
    Trails = 10,
    Lights = 1,
    SurfaceGuis = 4,
}

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

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local AuraStyles = {}

-- The breakthrough flash's colours. Pets used to give their own (SET AURA); the owner removed that on 2026-11-12, so
-- every breakthrough uses Neutral, and each realm's own aura (RealmAura) carries the variety.
AuraStyles.Elements = {
    Neutral = { Core = Color3.fromRGB(235, 248, 255), Main = Color3.fromRGB(125, 200, 255), Deep = Color3.fromRGB(55, 120, 210), Particles = "Mote", RingShape = "Circle" },
}

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

return AuraStyles

-- Which Murim territory a player stands in (the owner, 2026-11-24: "give each territory its own sound"). Pure numbers, no Instances, so the spec can run it:
-- the client reads each Territory folder's "Centre" and "Radius" (written by DawnspireBuilder, WindriftBuilder, NightfallBuilder) and asks `which`.
--
--   TerritoryRules.which(x, z, territories, current)   -> a name or nil
--       territories  { [name] = { X = number, Z = number, Radius = number } }
--       current      the territory the player was in a moment ago (or nil): it is kept until they are well outside it (the border doesn't flicker)
--   TerritoryRules.SOUND   what each territory plays (names in client/Audio/SoundCatalog)
local TerritoryRules = {}

TerritoryRules.EnterAt = 1.0 -- of a territory's Radius from its centre: inside this, you are in it
TerritoryRules.LeaveAt = 1.18 -- the one you are in is kept until this far out

-- each territory's bed, music and the little sounds that come now and then (a name, the seconds between the next one: min, max)
TerritoryRules.SOUND = {
    Orthodox = { Ambience = "AmbDawnspire", Music = "MusicJade", Accent = { Name = "ShrineChime", Min = 14, Max = 28 } },     -- falls in the ravine, flute, chimes
    Unorthodox = { Ambience = "AmbWindrift", Music = "MusicMoon", Accent = nil },                                              -- the gorge's wind, a wanderer's tune
    Demonic = { Ambience = "AmbEmber", Music = "MusicEmber", Accent = nil },                                                   -- the fissure's rumble, tense drums
}

local function distance(x, z, t)
    local dx, dz = x - t.X, z - t.Z
    return math.sqrt(dx * dx + dz * dz) / t.Radius
end

function TerritoryRules.which(x, z, territories, current)
    local held = current and territories[current]
    if held and distance(x, z, held) <= TerritoryRules.LeaveAt then
        -- still inside the one we are in, unless another is clearly nearer and has really been entered
        local best, bestD = current, distance(x, z, held)
        for name, t in territories do
            local d = distance(x, z, t)
            if name ~= current and d <= TerritoryRules.EnterAt and d < bestD - 0.25 then
                best, bestD = name, d
            end
        end
        return best
    end
    local best, bestD = nil, math.huge
    for name, t in territories do
        local d = distance(x, z, t)
        if d <= TerritoryRules.EnterAt and d < bestD then
            best, bestD = name, d
        end
    end
    return best
end

return TerritoryRules

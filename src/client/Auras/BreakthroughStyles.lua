-- The breakthrough sequence's data: which grade a rank-up is (Step, Milestone, Realm, Apex), each grade's beats in seconds,
-- each realm's look (its aura's own palette and its own signature), and the plain words the title card says (describe).
-- Used by BreakthroughFx (what is drawn), BreakthroughShow (the player's own camera, screen, sound and card) and AuraController.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local AuraConfig = require(ReplicatedStorage:WaitForChild("AuraConfig"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local Styles = {}

-- ---------- the grades ----------
-- Grandeur grows with how much the step means: a plain step (levels 2 to 4 of a realm), the fifth level that ends a realm
-- (Milestone), a new realm (Realm, after the Tribulation), and the climax (Apex: entering the last realm, and its top rank).
-- Beats, in seconds from the moment the rank changes:
--   Hold   the held breath just before the break (it ends at Break)
--   Break  the flash, the shockwave, the hit-pause
--   Card   when the title card comes in, and Out when it leaves; End when everything has settled and control is fully back
-- Own: the player's own cinematic (the camera, screen and sound too). Near: what others see (the world only, shorter).
-- Gather and Rise are the build's bulk (inflow streaks, threads, rings) as shares of 0..Break.
Styles.Grades = {
    Step = {
        Name = "Step",
        Own = { Hold = 0.0, Break = 1.3, Card = 1.7, Out = 3.7, End = 4.3 },
        Near = { Hold = 0, Break = 0.6, End = 1.9 },
        Threads = 0, Inflow = 26, Rings = 1, Pillar = 0, Bars = 0, Hud = false, Dim = 0.05, Shake = 0.12, Dolly = 0.6, Orbit = 0, Fov = 5,
        Flash = 0.34, Slow = 0, Size = 0.7, Tap = false,
    },
    Milestone = {
        Name = "Milestone",
        Own = { Hold = 0.3, Break = 2.8, Card = 3.5, Out = 6.1, End = 7.0 },
        Near = { Hold = 0, Break = 1.0, End = 3.2 },
        Threads = 4, Inflow = 40, Rings = 3, Pillar = 60, Bars = 0.07, Hud = true, Dim = 0.18, Shake = 0.3, Dolly = 3.2, Orbit = 10, Fov = 9,
        Flash = 0.62, Slow = 0.25, Size = 1.0, Tap = true,
    },
    Realm = {
        Name = "Realm",
        Own = { Hold = 0.7, Break = 4.6, Card = 5.9, Out = 9.0, End = 10.2 },
        Near = { Hold = 0, Break = 1.3, End = 4.2 },
        Threads = 6, Inflow = 52, Rings = 4, Pillar = 110, Bars = 0.1, Hud = true, Dim = 0.26, Shake = 0.55, Dolly = 4.5, Orbit = 22, Fov = 13,
        Flash = 0.85, Slow = 0.45, Size = 1.35, Tap = true,
    },
    Apex = {
        Name = "Apex",
        Own = { Hold = 1.1, Break = 6.0, Card = 7.7, Out = 12.2, End = 13.6 },
        Near = { Hold = 0, Break = 1.6, End = 5.4 },
        Threads = 8, Inflow = 60, Rings = 5, Pillar = 170, Bars = 0.11, Hud = true, Dim = 0.3, Shake = 0.7, Dolly = 6.5, Orbit = 34, Fov = 16,
        Flash = 1, Slow = 0.6, Size = 1.7, Tap = true,
    },
}

-- Checked in Studio after each breakthrough (AuraController): the most instances one breakthrough may hold at a time.
Styles.Budget = {
    Own = { ParticleEmitters = 36, Beams = 40, Trails = 8, Lights = 1, Billboards = 4, Parts = 16 },
    Near = { ParticleEmitters = 22, Beams = 12, Trails = 0, Lights = 1, Billboards = 3, Parts = 10 },
}

-- ---------- the realms' looks ----------
-- Each realm takes its aura's palette (AuraConfig) and its own signature, drawn from the textures of that realm's own unique
-- piece (ReplicatedStorage.AuraMeshes.RealmUnique.TierNN): the same ideas the aura has, told as an event.
--   Qi Awakening      a long breath out: the Jade Qi Vortex's strands, soft shells of light
--   Qi Foundation     Meridian Current: belts of flowing light round the waist and chest, rippling out
--   Spirit Core       Core Pulse: a golden core beating faster, then bursting
--   Spirit Soul       Soul Flames: blue flames climbing the body, then a ring of them thrown out
--   Ascendant         Ascending Gale: a rising column of wind-streaks that blows the sky open
--   Immortal          Heaven's Light: three pillars fall from the sky and join in one
--   Divine            Divine Lightning: crimson bolts crack closer and closer, then strike all round
--   Cosmic            Star Drift: stars pulled in from a wide sky, then thrown back as a shower
--   Void              Void Pull: shards sucked into a black core that implodes, then an ice-blue shock
--   Heavenly Dao      Radiant Rays: a fan of rose rays opens behind the body, then sweeps all round
--   Primordial        Magma Rise: the ground cracks and glows, magma is thrown up in the break
--   Eternal           Eternal Orbits: three rings of gold, cyan and magenta spin in, then fly out as the shockwave
Styles.Motifs = { "Breath", "Current", "Core", "Flame", "Gale", "Pillars", "Bolts", "Stars", "Void", "Rays", "Magma", "Orbits" }

local TEXTURES = {
    Glow = "rbxassetid://135169457468310",
    SoftGlow = "rbxassetid://243664672",
    Streak = "rbxassetid://115312010132075",
    Ring = "rbxassetid://130173906719836",
    Spike = "rbxassetid://89522570963572",
    Spark = "rbxassetid://112814194154292",
    Flare = "rbxassetid://14054628491",
    Fog = "rbxassetid://14050223758",
    GlitterFog = "rbxassetid://14049414463",
    Vortex = "rbxassetid://14050094484",
    HeavenBeam = "rbxassetid://2316283203",
    HeavenHaze = "rbxassetid://1470871817",
    Current = "rbxassetid://14050898403",
    CorePulse = "rbxassetid://14197762397",
    SoulFlame = "rbxassetid://112972240265890",
    GaleStreak = "rbxassetid://12363818754",
    Bolt = "rbxassetid://12781757438",
    Star = "rbxassetid://14198353638",
    StarDust = "rbxassetid://917181007",
    VoidShards = "rbxassetid://14052683457",
    VoidStreak = "rbxassetid://12363817291",
    RayBeam = "rbxassetid://12363861398",
    Magma = "rbxassetid://14052938411",
    HeatSmoke = "rbxassetid://9345352897",
    OrbitBeam = "rbxassetid://14191603094",
}
Styles.Textures = TEXTURES

-- the look of a realm (1 to 12)
function Styles.theme(realm)
    local tier = AuraConfig.Tiers[realm] or AuraConfig.Tiers[1]
    local palette = tier.Palette
    local theme = {
        Realm = realm,
        Hot = palette.Hot,
        Main = palette.Main,
        Deep = palette.Deep,
        Glow = palette.Glow,
        Motif = Styles.Motifs[realm] or "Breath",
        -- how big this realm's events run: 0.8 at the first realm to 1.25 at the last
        Scale = 0.8 + 0.45 * (realm - 1) / 11,
    }
    if realm == 9 then -- the Void's rim is ice blue round a black core: its light is the rim, its dark is the core
        theme.Deep = Color3.fromRGB(40, 90, 170)
        theme.Dark = Color3.fromRGB(4, 6, 16)
    elseif realm == 6 then -- silver-white blooms to white: leave a little blue in the middle
        theme.Main = Color3.fromRGB(190, 208, 245)
    elseif realm == 12 then -- prismatic: gold, cyan, magenta
        theme.Gold, theme.Cyan, theme.Magenta = palette.Hot, palette.Main, palette.Deep
    end
    return theme
end

-- ---------- grades and words ----------
local realmNumbers = {}
for _, rank in GameConfig.Ranks do
    if not realmNumbers[rank.Realm] then
        local count = 0
        for _ in realmNumbers do
            count += 1
        end
        realmNumbers[rank.Realm] = count + 1
    end
end

function Styles.realmNumber(realmName)
    return realmNumbers[realmName]
end

-- each realm's aura colour in a word, for "Your aura turns ..." on the card
local AURA_WORDS = { "jade green", "teal", "gold", "royal blue", "solar orange", "silver-white", "crimson", "violet", "ice blue", "rose pink", "lava red", "rainbow" }

local LAST_RANK_ID = GameConfig.Ranks[#GameConfig.Ranks].Id
local LAST_REALM = realmNumbers[GameConfig.Ranks[#GameConfig.Ranks].Realm]

-- the grade of a breakthrough into the rank with this id (the rank's level in its realm: 1 is a new realm, 5 the realm's last)
function Styles.gradeOf(rankId)
    local rank = Ranks.getRankById(rankId)
    if not rank then
        return Styles.Grades.Step
    elseif rankId == LAST_RANK_ID or (rank.Level == 1 and realmNumbers[rank.Realm] == LAST_REALM) then
        return Styles.Grades.Apex -- the last realm's door and its top rank: the climax
    elseif rank.Level == 1 then
        return Styles.Grades.Realm
    elseif rank.Level == 5 then
        return Styles.Grades.Milestone
    end
    return Styles.Grades.Step
end

-- everything one breakthrough needs: the grade, the realm's look, and the words for the card (plain, short)
--   rankId       the rank just reached; fromName the name of the rank before it (may be nil)
function Styles.describe(rankId, fromName)
    local rank = Ranks.getRankById(rankId)
    if not rank then
        return nil
    end
    local grade = Styles.gradeOf(rankId)
    local realm = realmNumbers[rank.Realm] or 1
    local from = if fromName then Ranks.getRank(fromName) else nil
    local nextRank = Ranks.getNextRank(rank.Name)

    local lines = {}
    if rank.Level == 1 and realmNumbers[rank.Realm] then -- a new realm: the aura changes (the thing seen the next time they meditate)
        table.insert(lines, "Your aura turns " .. AURA_WORDS[realmNumbers[rank.Realm]])
    end
    if from and rank.QiMultiplier > from.QiMultiplier then
        table.insert(lines, string.format("Qi power  x%d  to  x%d", from.QiMultiplier, rank.QiMultiplier))
    elseif rank.QiMultiplier > 1 and grade.Name ~= "Step" then
        table.insert(lines, string.format("Qi power  x%d", rank.QiMultiplier))
    end
    if from then
        local was, now = Ranks.getQinggong(from.Name), Ranks.getQinggong(rank.Name)
        if now.AirLeaps > was.AirLeaps then
            table.insert(lines, string.format("Air leaps  %d  to  %d", was.AirLeaps, now.AirLeaps))
        end
        if now.RunSpeed > was.RunSpeed then
            table.insert(lines, "You run faster")
        end
        if Ranks.canFly(rank.Name) and not Ranks.canFly(from.Name) then
            table.insert(lines, "Sword flight unlocked")
        elseif Ranks.canFly(rank.Name) and now.FlightSpeed > was.FlightSpeed then
            table.insert(lines, "Your sword flies faster")
        end
    end
    if #lines == 0 then
        table.insert(lines, "Your Qi grows stronger")
    end
    if #lines > 3 then
        local run = table.find(lines, "You run faster")
        if run then
            table.remove(lines, run) -- (the least of them goes first)
        end
    end
    while #lines > 4 do
        table.remove(lines)
    end

    local nextLine
    if nextRank then
        nextLine = string.format("Next: %s at %s Qi", nextRank.Name, NumberFormat.compact(nextRank.QiRequired))
    else
        nextLine = "Nothing is above you now."
    end

    local headline, subline
    if rank.Level == 1 then
        headline, subline = string.upper(rank.Realm), "NEW REALM"
    elseif grade.Name == "Apex" then
        headline, subline = string.upper(rank.Name), "THE HIGHEST RANK"
    elseif grade.Name == "Milestone" then
        headline, subline = string.upper(rank.Name), string.upper(rank.Realm) .. "  COMPLETE"
    else
        headline, subline = string.upper(rank.Name), string.upper(rank.Realm) .. "  ·  LEVEL " .. rank.Level .. " OF 5"
    end

    return {
        Grade = grade,
        Rank = rank,
        RankId = rankId,
        Realm = realm,
        Theme = Styles.theme(realm),
        Headline = headline,
        Subline = subline,
        -- the rank's own name under a realm's headline
        RankName = rank.Name,
        Lines = lines,
        Next = nextLine,
    }
end

return Styles

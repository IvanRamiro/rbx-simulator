-- Faction standing and the weekly rivalry's rules (GameConfig.Renown), shared so the page shows exactly what the server counts and pays.
--
--   StandingRules.rankOf(renown)             the rank number, 1 to 5
--   StandingRules.nextRank(renown)           the next rank's number and renown, or nil at the top
--   StandingRules.rankName(faction, rank)    the faction's name for a rank
--   StandingRules.rankStones(rank, realm)    the stones paid once on reaching a rank (realm-scaled)
--   StandingRules.cacheStones(rank, realm)   the daily cache at a rank
--   StandingRules.warStones(realm)           the victory share (and BoostMinutes: GameConfig.Renown.War)
--   StandingRules.score(entry)               a faction's weekly score from { Renown, Members }
--   StandingRules.winner(totals)             the faction that won a week from { [faction] = { Renown, Members } }, or nil (nothing earned, or a tie)
--   StandingRules.sanitize(raw)              a saved state cleaned
--   StandingRules.roll(data, week)           a new week: what was earned is kept as last week's, this week's starts empty
--   StandingRules.earn(data, week, amount)   adds renown; returns whether this was the player's first of the week (they count as a member of the week's score)
--   StandingRules.owed(data)                 the rank numbers reached and not yet paid, lowest first
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local CONFIG = GameConfig.Renown
local StandingRules = {}

StandingRules.ranks = #CONFIG.Thresholds
local MAX = 1e9

function StandingRules.rankOf(renown)
    local rank = 1
    if typeof(renown) == "number" then
        for index, need in CONFIG.Thresholds do
            if renown >= need then
                rank = index
            end
        end
    end
    return rank
end

function StandingRules.nextRank(renown)
    local rank = StandingRules.rankOf(renown) + 1
    local need = CONFIG.Thresholds[rank]
    if need then
        return rank, need
    end
    return nil, nil
end

function StandingRules.rankName(faction, rank)
    local names = typeof(faction) == "string" and CONFIG.RankNames[faction]
    return if names then names[rank] else nil
end

local function scaled(base, realmIndex)
    return math.max(1, Shop.roundNice(base * GameConfig.SpiritStones.RealmFactor ^ ((realmIndex or 1) - 1)))
end

function StandingRules.rankStones(rank, realmIndex)
    local base = CONFIG.RankStones[rank]
    return if base and base > 0 then scaled(base, realmIndex) else 0
end

function StandingRules.cacheStones(rank, realmIndex)
    return scaled(CONFIG.CacheStones * (1 + CONFIG.CacheStep * (math.clamp(rank, 1, StandingRules.ranks) - 1)), realmIndex)
end

function StandingRules.warStones(realmIndex)
    return scaled(CONFIG.War.Stones, realmIndex)
end

function StandingRules.score(entry)
    if typeof(entry) ~= "table" or typeof(entry.Renown) ~= "number" then
        return 0
    end
    return entry.Renown / math.max(CONFIG.War.MinMembers, if typeof(entry.Members) == "number" then entry.Members else 0)
end

function StandingRules.winner(totals)
    if typeof(totals) ~= "table" then
        return nil
    end
    local best, bestScore, tied = nil, 0, false
    for _, faction in GameConfig.Faction.Order do
        local score = StandingRules.score(totals[faction])
        if score > bestScore then
            best, bestScore, tied = faction, score, false
        elseif score == bestScore and score > 0 then
            tied = true
        end
    end
    return if tied then nil else best
end

local function whole(value)
    return if typeof(value) == "number" and value == value and value >= 0 and value <= MAX then math.floor(value) else 0
end

-- { Renown, Paid (ranks paid), CacheDay, Week, WeekRenown, LastWeek, LastRenown, WarClaimed (the week whose victory was taken) }
function StandingRules.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local renown = whole(raw.Renown)
    return {
        Renown = renown, Paid = math.clamp(whole(raw.Paid), 0, StandingRules.rankOf(renown)), CacheDay = whole(raw.CacheDay),
        Week = whole(raw.Week), WeekRenown = whole(raw.WeekRenown), LastWeek = whole(raw.LastWeek), LastRenown = whole(raw.LastRenown),
        WarClaimed = whole(raw.WarClaimed),
    }
end

function StandingRules.roll(data, week)
    if data.Week ~= week then
        if data.Week > 0 then -- (a first ever week has nothing to keep)
            data.LastWeek, data.LastRenown = data.Week, data.WeekRenown
        end
        data.Week, data.WeekRenown = week, 0
    end
end

function StandingRules.earn(data, week, amount)
    if typeof(amount) ~= "number" or amount ~= amount or amount <= 0 then
        return false
    end
    StandingRules.roll(data, week)
    local first = data.WeekRenown == 0
    data.Renown = math.min(data.Renown + math.floor(amount), MAX)
    data.WeekRenown = math.min(data.WeekRenown + math.floor(amount), MAX)
    return first
end

function StandingRules.owed(data)
    local out = {}
    for rank = data.Paid + 1, StandingRules.rankOf(data.Renown) do
        table.insert(out, rank)
    end
    return out
end

return StandingRules

-- The guardian bounty's rules (GameConfig.Bounty), shared so the board shows exactly what the server counts and pays.
--
--   BountyRules.marked(dayKey)            the guardian marked for that day (every player the same; it walks through GameConfig.Bounty.Order)
--   BountyRules.tiers                     GameConfig.Bounty.Tiers
--   BountyRules.tierStones(tier, realm)   one tier's stones, scaled by realm as the goals' are
--   BountyRules.dailyStones(realm)        the marked guardian's first conquest of the day
--   BountyRules.reached(count)            how many tiers `count` conquests have reached
--   BountyRules.nextTier(count)           the next tier's index and table, or nil past the last
--   BountyRules.threshold()               the damage a player must have dealt to a guardian's weakening to be counted (by guardian config)
--   BountyRules.sanitize(raw)             a saved state cleaned: only known guardians, whole counts, a paid count no higher than the tiers reached
--   BountyRules.roll(data, day)           the day's flag started afresh when the day moved on
--   BountyRules.owed(data)                { { guardianId, tierIndex } } tiers reached and not yet paid, lowest first
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local BountyRules = {}

local CONFIG = GameConfig.Bounty
BountyRules.tiers = CONFIG.Tiers
BountyRules.order = CONFIG.Order

local MAX_COUNT = 1e6

function BountyRules.marked(dayKey)
    local order = CONFIG.Order
    if typeof(dayKey) ~= "number" or dayKey ~= dayKey then
        return order[1]
    end
    return order[(math.floor(dayKey) % #order) + 1]
end

local function scaled(base, realmIndex)
    return math.max(1, Shop.roundNice(base * GameConfig.SpiritStones.RealmFactor ^ ((realmIndex or 1) - 1)))
end

function BountyRules.tierStones(tier, realmIndex)
    local entry = CONFIG.Tiers[tier]
    return if entry then scaled(entry.Stones, realmIndex) else 0
end

function BountyRules.dailyStones(realmIndex)
    return scaled(CONFIG.DailyStones, realmIndex)
end

function BountyRules.reached(count)
    local n = 0
    if typeof(count) == "number" then
        for index, entry in CONFIG.Tiers do
            if count >= entry.Conquests then
                n = index
            end
        end
    end
    return n
end

function BountyRules.nextTier(count)
    local index = BountyRules.reached(count) + 1
    local entry = CONFIG.Tiers[index]
    if entry then
        return index, entry
    end
    return nil, nil
end

-- the damage that counts as a share of the fight: ConquestShare of what weakening takes
function BountyRules.threshold(guardianConfig)
    return guardianConfig.MaxHealth * (1 - guardianConfig.WeakenedAt) * CONFIG.ConquestShare
end

local function whole(value)
    return if typeof(value) == "number" and value == value and value >= 0 and value <= MAX_COUNT then math.floor(value) else 0
end

-- { Counts = { [guardianId] = n }, Paid = { [guardianId] = tiers paid }, Day = n, DayPaid = bool }
function BountyRules.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local counts, paid = {}, {}
    local rawCounts, rawPaid = if typeof(raw.Counts) == "table" then raw.Counts else {}, if typeof(raw.Paid) == "table" then raw.Paid else {}
    for _, id in CONFIG.Order do
        local count = whole(rawCounts[id])
        if count > 0 then
            counts[id] = count
        end
        local tiers = math.min(whole(rawPaid[id]), BountyRules.reached(count), #CONFIG.Tiers)
        if tiers > 0 then
            paid[id] = tiers
        end
    end
    return { Counts = counts, Paid = paid, Day = whole(raw.Day), DayPaid = raw.DayPaid == true }
end

function BountyRules.roll(data, day)
    if data.Day ~= day then
        data.Day, data.DayPaid = day, false
    end
end

function BountyRules.owed(data)
    local out = {}
    for _, id in CONFIG.Order do
        for tier = (data.Paid[id] or 0) + 1, BountyRules.reached(data.Counts[id] or 0) do
            table.insert(out, { id, tier })
        end
    end
    return out
end

return BountyRules

-- The daily and weekly goals' rules (GameConfig.Goals), shared so the window shows exactly what the server counts and pays. A day is a UTC calendar day (as
-- RewardRules); a week is a UTC week starting on Monday. Which goals a player gets is decided from their id and the period's number alone, with a small hash
-- (not Random: the server and the client must agree to the last goal, and nothing is stored for it).
--
--   GoalRules.dayKey() / weekKey()                  the current period's number
--   GoalRules.pick(scope, userId, key)              the scope's goals for this player and period: an array of { Id, Kind, Mode, Target, Unit, Text } (scope "Daily" or "Weekly")
--   GoalRules.label(goal)                           the goal in words ("Cultivate for 20 minutes")
--   GoalRules.stones(scope, realmIndex)             one goal's Spirit Stones (scaled by realm as the login reward is)
--   GoalRules.bonus(scope, realmIndex)              the stones and the minutes of timed boost for finishing all of a scope's goals
--   GoalRules.advance(progress, goal, amount)       the progress after `amount` more (sum) or a new best (max), never past the target
--   GoalRules.secondsLeft(scope)                    seconds until the scope's period ends
--   GoalRules.sanitize(raw) / roll(data)            a saved state cleaned (unknown ids, odd numbers dropped); a period's tables started afresh when its number moved on
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local GoalRules = {}

local DAY = 86400

function GoalRules.dayKey()
    return math.floor(os.time() / DAY)
end

-- (1970-01-01 was a Thursday: day 0 is three days before the first Monday)
function GoalRules.weekKey()
    return math.floor((GoalRules.dayKey() + 3) / 7)
end

function GoalRules.secondsLeft(scope)
    local now = os.time()
    if scope == "Weekly" then
        return (GoalRules.weekKey() + 1) * 7 * DAY - 3 * DAY - now
    end
    return (GoalRules.dayKey() + 1) * DAY - now
end

-- a small deterministic generator (a linear congruential step over 2^31 - 1), seeded from numbers
local function stream(seed)
    local state = (seed % 2147483646) + 1
    return function(n)
        state = (state * 48271) % 2147483647
        return (state % n) + 1
    end
end

function GoalRules.pick(scope, userId, key)
    local config = GameConfig.Goals[scope]
    if not config or typeof(userId) ~= "number" or typeof(key) ~= "number" then
        return {}
    end
    local next = stream(userId * 7919 + key * 104729 + (if scope == "Weekly" then 17 else 3))
    next(1) -- (the first step of a congruential stream follows the seed too closely)
    next(1)
    -- the kinds the pool has, in a fixed order, shuffled; then one goal of each kind for as many kinds as the scope shows
    local kinds, byKind = {}, {}
    for _, goal in config.Pool do
        if not byKind[goal.Kind] then
            byKind[goal.Kind] = {}
            table.insert(kinds, goal.Kind)
        end
        table.insert(byKind[goal.Kind], goal)
    end
    for i = #kinds, 2, -1 do
        local j = next(i)
        kinds[i], kinds[j] = kinds[j], kinds[i]
    end
    local picks = {}
    for i = 1, math.min(config.Count, #kinds) do
        local variants = byKind[kinds[i]]
        table.insert(picks, variants[next(#variants)])
    end
    return picks
end

function GoalRules.label(goal)
    return string.format(goal.Text, math.floor(goal.Target / goal.Unit))
end

local function scaled(base, realmIndex)
    return math.max(1, Shop.roundNice(base * GameConfig.SpiritStones.RealmFactor ^ ((realmIndex or 1) - 1)))
end

function GoalRules.stones(scope, realmIndex)
    return scaled(GameConfig.Goals[scope].Stones, realmIndex)
end

function GoalRules.bonus(scope, realmIndex)
    local bonus = GameConfig.Goals[scope].Bonus
    return scaled(bonus.Stones, realmIndex), bonus.BoostMinutes
end

function GoalRules.advance(progress, goal, amount)
    if typeof(amount) ~= "number" or amount ~= amount or amount <= 0 then
        return progress
    end
    local now = if goal.Mode == "max" then math.max(progress, amount) else progress + amount
    return math.min(goal.Target, math.floor(now))
end


-- ---------- the saved state ----------
-- { Day, DayProgress = { [goalId] = n }, DayClaimed = { [goalId] = true }, DayBonus = bool, Week, WeekProgress, WeekClaimed, WeekBonus } (server/Rewards/GoalBook saves it)
local MAX_ENTRIES = 16
local MAX_VALUE = 1e9

local function whole(value)
    return if typeof(value) == "number" and value == value and value >= 0 and value <= MAX_VALUE then math.floor(value) else 0
end

-- only goals this config's pool holds: an id it no longer has could only be garbage or an old week's
local function known(scope)
    local ids = {}
    for _, goal in GameConfig.Goals[scope].Pool do
        ids[goal.Id] = goal
    end
    return ids
end

local function cleanProgress(raw, scope)
    local out, ids, n = {}, known(scope), 0
    if typeof(raw) == "table" then
        for id, value in raw do
            local goal = ids[id]
            if goal and n < MAX_ENTRIES then
                out[id] = math.min(whole(value), goal.Target)
                n += 1
            end
        end
    end
    return out
end

local function cleanClaimed(raw, scope)
    local out, ids, n = {}, known(scope), 0
    if typeof(raw) == "table" then
        for id, value in raw do
            if ids[id] and value == true and n < MAX_ENTRIES then
                out[id] = true
                n += 1
            end
        end
    end
    return out
end

function GoalRules.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    return {
        Day = whole(raw.Day), DayProgress = cleanProgress(raw.DayProgress, "Daily"), DayClaimed = cleanClaimed(raw.DayClaimed, "Daily"), DayBonus = raw.DayBonus == true,
        Week = whole(raw.Week), WeekProgress = cleanProgress(raw.WeekProgress, "Weekly"), WeekClaimed = cleanClaimed(raw.WeekClaimed, "Weekly"), WeekBonus = raw.WeekBonus == true,
    }
end

-- starts a period afresh when its number has moved on
function GoalRules.roll(data)
    local day, week = GoalRules.dayKey(), GoalRules.weekKey()
    if data.Day ~= day then
        data.Day, data.DayProgress, data.DayClaimed, data.DayBonus = day, {}, {}, false
    end
    if data.Week ~= week then
        data.Week, data.WeekProgress, data.WeekClaimed, data.WeekBonus = week, {}, {}, false
    end
end

return GoalRules

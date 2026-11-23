-- RewardRules (the daily reward) and SpinRules (the Spin Wheel): what the windows show is what the server pays.
local t = require("@env/t")
local Random = require("@env/globals").Random
local GameConfig = require("@shared/GameConfig")
local RewardRules = require("@shared/RewardRules")
local SpinRules = require("@shared/SpinRules")

local DAILY = GameConfig.Rewards.Daily

-- ---------- the daily reward ----------
t.test("today is the UTC day number", function()
    t.eq(RewardRules.today(), math.floor(os.time() / 86400))
end)

t.test("the streak continues after yesterday's claim, wraps after the last day, and restarts after a missed day", function()
    local today = RewardRules.today()
    t.eq(RewardRules.nextDay(today - 1, 0), 1, "first claim after yesterday's: day 1")
    t.eq(RewardRules.nextDay(today - 1, 1), 2)
    t.eq(RewardRules.nextDay(today - 1, 3), 4)
    t.eq(RewardRules.nextDay(today - 1, #DAILY), 1, "after the last day the week starts again")
    t.eq(RewardRules.nextDay(today - 1, nil), 1, "no streak saved")
    t.eq(RewardRules.nextDay(today - 2, 5), 1, "a missed day resets the streak")
    t.eq(RewardRules.nextDay(today - 30, 5), 1)
    t.eq(RewardRules.nextDay(nil, 5), 1, "never claimed")
end)

t.test("daily stones pay at least 5, are whole numbers, and grow with the realm", function()
    for day = 1, #DAILY do
        local last = 0
        for realm = 1, 12 do
            local stones, qiMinutes, boostMinutes = RewardRules.daily(day, realm, nil)
            t.ok(stones >= 5, "day " .. day .. " realm " .. realm .. " pays under 5")
            t.eq(stones, math.floor(stones), "whole stones")
            t.ok(stones >= last, "day " .. day .. " must not pay less in a higher realm")
            t.ok(qiMinutes >= 0 and boostMinutes >= 0)
            last = stones
        end
    end
    local stonesNoRealm = RewardRules.daily(1, nil, nil)
    t.eq(stonesNoRealm, (RewardRules.daily(1, 1, nil)), "no realm counts as the first")
end)

-- ---------- the Spin Wheel ----------
t.test("the wheel's geometry", function()
    t.eq(SpinRules.Count, #SpinRules.Segments)
    t.near(SpinRules.Step * SpinRules.Count, 360, 1e-9)
    t.eq(SpinRules.angleOf(1), 0, "segment 1 is at the top")
    t.near(SpinRules.angleOf(SpinRules.Count), 360 - SpinRules.Step, 1e-9)
    local total = 0
    for _, segment in SpinRules.Segments do
        total += segment.Weight
    end
    t.near(SpinRules.TotalWeight, total, 1e-9)
end)

t.test("roll follows the weights over many spins, and always returns a real segment", function()
    local random = Random.new(11)
    local n = 80000
    local counts = {}
    for _ = 1, n do
        local index = SpinRules.roll(random)
        t.ok(index >= 1 and index <= SpinRules.Count and index == math.floor(index), "roll out of range")
        counts[index] = (counts[index] or 0) + 1
    end
    for index, segment in SpinRules.Segments do
        local expected = segment.Weight / SpinRules.TotalWeight
        t.near((counts[index] or 0) / n, expected, 0.01, "segment " .. index .. " share")
    end
end)

t.test("secondsToReset counts down to the next UTC midnight", function()
    t.eq(SpinRules.secondsToReset(0), 86400)
    t.eq(SpinRules.secondsToReset(1), 86399)
    t.eq(SpinRules.secondsToReset(86399), 1)
    t.eq(SpinRules.secondsToReset(86400), 86400)
    t.eq(SpinRules.secondsToReset(86400 * 5 + 3600), 86400 - 3600)
end)

t.test("free spins: a new day or no record gives the daily spins; used and extra spins adjust today's", function()
    local daily = GameConfig.SpinWheel.DailySpins
    local today = SpinRules.today()
    t.eq(SpinRules.freeLeft(nil), daily)
    t.eq(SpinRules.freeLeft({ Day = today - 1, Used = 99, Extra = 0 }), daily, "an old day's record is forgotten")
    t.eq(SpinRules.freeLeft({ Day = today, Used = 0, Extra = 0 }), daily)
    t.eq(SpinRules.freeLeft({ Day = today, Used = 1, Extra = 0 }), daily - 1)
    t.eq(SpinRules.freeLeft({ Day = today, Used = 1, Extra = 2 }), daily + 1, "a won spin adds one")
    t.eq(SpinRules.freeLeft({ Day = today, Used = daily + 50, Extra = 0 }), 0, "never negative")
    t.eq(SpinRules.freeLeft({ Day = today }), daily, "missing counters count as zero")
end)

t.test("bought spins never run out at midnight", function()
    local daily = GameConfig.SpinWheel.DailySpins
    local today = SpinRules.today()
    t.eq(SpinRules.spinsLeft(nil), daily)
    t.eq(SpinRules.spinsLeft({ Day = today, Used = daily, Extra = 0, Bought = 3 }), 3)
    t.eq(SpinRules.spinsLeft({ Day = today - 1, Used = daily, Extra = 0, Bought = 3 }), daily + 3, "yesterday's used spins are forgotten, bought ones stay")
    t.eq(SpinRules.spinsLeft({ Day = today, Used = 0, Extra = 0 }), daily)
end)

t.test("every segment can be described for every rank", function()
    for _, rank in GameConfig.Ranks do
        for index = 1, SpinRules.Count do
            local info = SpinRules.describe(index, rank.Name, nil)
            t.ok(info ~= nil and info.Kind ~= nil, "segment " .. index .. " for " .. rank.Name)
            t.ok(info.Chance > 0 and info.Chance <= 1)
        end
    end
end)

t.finish("rewards")

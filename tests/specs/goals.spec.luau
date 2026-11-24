-- The daily and weekly goals' rules (shared/GoalRules, GameConfig.Goals): the picks, the counting, the rewards, the saved state.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local GoalRules = require("@shared/GoalRules")

local function ids(picks)
    local list = {}
    for _, g in picks do
        table.insert(list, g.Id)
    end
    return table.concat(list, ",")
end

t.test("every goal in the config is well formed", function()
    for scope, config in GameConfig.Goals do
        local seen = {}
        t.ok(config.Count >= 1 and config.Stones >= 1 and config.Bonus.Stones >= 1 and config.Bonus.BoostMinutes >= 0, scope .. ": rewards")
        for _, goal in config.Pool do
            t.ok(not seen[goal.Id], scope .. ": duplicate id " .. goal.Id)
            seen[goal.Id] = true
            t.ok(#goal.Id <= 40, goal.Id .. ": id too long to be claimed (the server refuses over 40)")
            t.ok(goal.Mode == "sum" or goal.Mode == "max", goal.Id .. ": mode")
            t.ok(goal.Target >= 1 and goal.Unit >= 1 and goal.Target % goal.Unit == 0, goal.Id .. ": a whole number of its unit")
            t.ok(string.find(goal.Text, "%%d") ~= nil, goal.Id .. ": its words need a number")
        end
        local kinds = {}
        for _, goal in config.Pool do
            kinds[goal.Kind] = true
        end
        local n = 0
        for _ in kinds do
            n += 1
        end
        t.ok(n >= config.Count, scope .. ": the pool must hold at least " .. config.Count .. " kinds")
    end
end)

t.test("a pick is the same for the same player and period, differs across players and periods, and never repeats a kind", function()
    for _, scope in { "Daily", "Weekly" } do
        local a = GoalRules.pick(scope, 12345, 20000)
        local b = GoalRules.pick(scope, 12345, 20000)
        t.eq(ids(a), ids(b), scope .. ": not deterministic")
        t.eq(#a, GameConfig.Goals[scope].Count, scope .. ": the wrong number of goals")
        local kinds = {}
        for _, g in a do
            t.ok(not kinds[g.Kind], scope .. ": a kind twice: " .. g.Kind)
            kinds[g.Kind] = true
        end
        local players, days = {}, {}
        for u = 1, 60 do
            players[ids(GoalRules.pick(scope, u * 977, 20000))] = true
        end
        for d = 20000, 20059 do
            days[ids(GoalRules.pick(scope, 12345, d))] = true
        end
        local np, nd = 0, 0
        for _ in players do np += 1 end
        for _ in days do nd += 1 end
        t.ok(np >= 4, scope .. ": 60 players got only " .. np .. " different sets")
        t.ok(nd >= 4, scope .. ": 60 periods gave only " .. nd .. " different sets")
    end
    t.eq(#GoalRules.pick("Monthly", 1, 1), 0, "an unknown scope gives nothing")
    t.eq(#GoalRules.pick("Daily", "x", 1), 0, "a garbage id gives nothing")
end)

t.test("over many players every goal of the pool comes up (none is unreachable)", function()
    for _, scope in { "Daily", "Weekly" } do
        local seen = {}
        for u = 1, 400 do
            for _, g in GoalRules.pick(scope, u * 31, 20100) do
                seen[g.Id] = true
            end
        end
        for _, goal in GameConfig.Goals[scope].Pool do
            t.ok(seen[goal.Id], scope .. ": " .. goal.Id .. " is never picked")
        end
    end
end)

t.test("progress adds up or keeps the best, stops at the target, and ignores garbage", function()
    local sum = { Mode = "sum", Target = 10 }
    local max = { Mode = "max", Target = 10 }
    t.eq(GoalRules.advance(0, sum, 3), 3)
    t.eq(GoalRules.advance(3, sum, 4), 7)
    t.eq(GoalRules.advance(8, sum, 5), 10, "never past the target")
    t.eq(GoalRules.advance(0, max, 4), 4)
    t.eq(GoalRules.advance(4, max, 2), 4, "a lesser combo does not lower the best")
    t.eq(GoalRules.advance(4, max, 99), 10, "never past the target")
    for _, bad in { -5, 0, 0 / 0, "5", true } do
        t.eq(GoalRules.advance(3, sum, bad), 3, "garbage must not move progress: " .. tostring(bad))
    end
end)

t.test("rewards scale by realm as the login reward does and stay small", function()
    for _, scope in { "Daily", "Weekly" } do
        local one = GoalRules.stones(scope, 1)
        t.ok(one >= 1, scope .. ": a goal pays something")
        t.ok(GoalRules.stones(scope, 6) > GoalRules.stones(scope, 3) and GoalRules.stones(scope, 3) > one, scope .. ": it must grow with the realm")
        local stones, minutes = GoalRules.bonus(scope, 1)
        t.ok(stones > GoalRules.stones(scope, 1), scope .. ": the bonus is worth more than one goal")
        t.ok(minutes >= 0 and minutes <= GameConfig.TimedBoost.MaxMinutes, scope .. ": the boost fits the bank")
    end
    -- a free week of goals (all of them) must stay a small share of the timed boost: under the login reward's week of boost twice over
    local boostPerWeek = 7 * GameConfig.Goals.Daily.Bonus.BoostMinutes + GameConfig.Goals.Weekly.Bonus.BoostMinutes
    local loginBoost = 0
    for _, day in GameConfig.Rewards.Daily do
        loginBoost += day.BoostMinutes or 0
    end
    t.ok(boostPerWeek <= loginBoost * 1.5, "goals add " .. boostPerWeek .. " min of 2x Qi a week against the login's " .. loginBoost)
    -- and a week of stones, at realm 1, under what the login reward pays in a week
    local loginStones = 0
    for _, day in GameConfig.Rewards.Daily do
        loginStones += day.Stones
    end
    local goalStones = 7 * (3 * GameConfig.Goals.Daily.Stones + GameConfig.Goals.Daily.Bonus.Stones) + 3 * GameConfig.Goals.Weekly.Stones + GameConfig.Goals.Weekly.Bonus.Stones
    t.ok(goalStones <= loginStones, "a week of goals pays " .. goalStones .. " stones against the login's " .. loginStones)
end)

t.test("the periods: a week is seven days, the clocks run out within their period", function()
    t.eq(GoalRules.weekKey(), math.floor((GoalRules.dayKey() + 3) / 7))
    local day, week = GoalRules.secondsLeft("Daily"), GoalRules.secondsLeft("Weekly")
    t.ok(day > 0 and day <= 86400, "the day's clock")
    t.ok(week > 0 and week <= 7 * 86400 and week >= day, "the week's clock")
end)

t.test("a saved state is cleaned: unknown ids, odd numbers and flags are dropped, and a new period starts afresh", function()
    local clean = GoalRules.sanitize({
        Day = 5, DayProgress = { D_Cultivate10 = 400, D_Hit20 = 9999, Fake = 3, D_Spin1 = -2, D_Combo6 = "x" }, DayClaimed = { D_Hit20 = true, Fake = true, D_Spin1 = "yes" },
        DayBonus = "true", Week = 9, WeekProgress = { W_Hatch5 = 2 }, WeekClaimed = { W_Hatch5 = true }, WeekBonus = true,
    })
    t.eq(clean.DayProgress.D_Cultivate10, 400)
    t.eq(clean.DayProgress.D_Hit20, 20, "clamped to its target")
    t.eq(clean.DayProgress.Fake, nil, "an unknown id")
    t.eq(clean.DayProgress.D_Spin1, 0, "a negative number")
    t.eq(clean.DayProgress.D_Combo6, 0, "a string")
    t.eq(clean.DayClaimed.D_Hit20, true)
    t.eq(clean.DayClaimed.Fake, nil)
    t.eq(clean.DayClaimed.D_Spin1, nil, "only true counts as a claim")
    t.eq(clean.DayBonus, false, "only true counts as the bonus")
    t.eq(clean.WeekBonus, true)
    for _, junk in { 5, "x", true } do
        local empty = GoalRules.sanitize(junk)
        t.eq(next(empty.DayProgress), nil, "junk becomes an empty state")
    end
    -- more entries than there are goals cannot grow the save
    local many = {}
    for i = 1, 200 do
        many["Junk" .. i] = 1
    end
    t.eq(next(GoalRules.sanitize({ DayProgress = many }).DayProgress), nil, "ids not in the pool never get in")
    -- a period that has moved on starts empty; the current one is kept
    local old = GoalRules.sanitize({ Day = GoalRules.dayKey() - 1, DayProgress = { D_Hit20 = 5 }, DayClaimed = { D_Hit20 = true }, DayBonus = true,
        Week = GoalRules.weekKey(), WeekProgress = { W_Hatch5 = 3 } })
    GoalRules.roll(old)
    t.eq(old.Day, GoalRules.dayKey())
    t.eq(next(old.DayProgress), nil, "yesterday's progress is gone")
    t.eq(next(old.DayClaimed), nil, "yesterday's claims are gone")
    t.eq(old.DayBonus, false, "yesterday's bonus is gone")
    t.eq(old.WeekProgress.W_Hatch5, 3, "this week's progress stays")
end)

t.finish("goals")

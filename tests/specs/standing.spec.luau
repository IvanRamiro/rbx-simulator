-- Faction standing and the weekly rivalry's rules (shared/StandingRules, GameConfig.Renown).
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local StandingRules = require("@shared/StandingRules")

local CONFIG = GameConfig.Renown

t.test("the config is well formed: five ranks that climb, a name for each in every faction", function()
    t.eq(#CONFIG.Thresholds, #CONFIG.RankStones)
    t.eq(CONFIG.Thresholds[1], 0)
    for index = 2, #CONFIG.Thresholds do
        t.ok(CONFIG.Thresholds[index] > CONFIG.Thresholds[index - 1], "rank " .. index .. " needs more renown")
    end
    for _, faction in GameConfig.Faction.Order do
        local names = CONFIG.RankNames[faction]
        t.ok(names ~= nil, faction .. " has rank names")
        t.eq(#names, #CONFIG.Thresholds, faction .. ": a name for every rank")
        local seen = {}
        for _, name in names do
            t.ok(not seen[name], faction .. ": " .. name .. " twice")
            seen[name] = true
        end
    end
    t.ok(CONFIG.War.MinMembers >= 1 and CONFIG.War.MinRenown >= 1 and CONFIG.War.Stones >= 1)
end)

t.test("a rank is reached at its renown and not before", function()
    t.eq(StandingRules.rankOf(0), 1)
    for index, need in CONFIG.Thresholds do
        t.eq(StandingRules.rankOf(need), index)
        if need > 0 then
            t.eq(StandingRules.rankOf(need - 1), index - 1)
        end
    end
    t.eq(StandingRules.rankOf(1e9), #CONFIG.Thresholds)
    t.eq(StandingRules.rankOf("9"), 1)
    local rank, need = StandingRules.nextRank(0)
    t.eq(rank, 2)
    t.eq(need, CONFIG.Thresholds[2])
    t.eq(StandingRules.nextRank(CONFIG.Thresholds[#CONFIG.Thresholds]), nil, "the top rank has no next")
    t.eq(StandingRules.rankName("Demonic", 5), "Dread Blade")
    t.eq(StandingRules.rankName("Nobody", 1), nil)
end)

t.test("stones grow with the realm, and the daily cache with the rank", function()
    t.eq(StandingRules.rankStones(1, 1), 0, "the first rank pays nothing")
    for rank = 2, StandingRules.ranks do
        t.ok(StandingRules.rankStones(rank, 1) >= 1)
        t.ok(StandingRules.rankStones(rank, 5) > StandingRules.rankStones(rank, 1))
    end
    t.ok(StandingRules.cacheStones(5, 1) > StandingRules.cacheStones(1, 1), "a higher rank has a bigger cache")
    t.ok(StandingRules.cacheStones(1, 6) > StandingRules.cacheStones(1, 1))
    t.ok(StandingRules.warStones(4) > StandingRules.warStones(1))
end)

t.test("a faction's score is its renown per member, never over fewer than MinMembers", function()
    local min = CONFIG.War.MinMembers
    t.near(StandingRules.score({ Renown = 300, Members = min * 10 }), 300 / (min * 10), 1e-9)
    t.near(StandingRules.score({ Renown = 90, Members = 1 }), 90 / min, 1e-9, "one member is counted as MinMembers")
    t.eq(StandingRules.score(nil), 0)
    t.eq(StandingRules.score({ Renown = "x" }), 0)
    t.eq(StandingRules.score({ Renown = 50 }), 50 / min)
end)

t.test("the winner is the highest score; nothing earned or a tie has none", function()
    t.eq(StandingRules.winner({ Orthodox = { Renown = 100, Members = 10 }, Unorthodox = { Renown = 100, Members = 5 }, Demonic = { Renown = 10, Members = 5 } }), "Unorthodox",
        "fewer members earning the same wins: a crowd does not")
    t.eq(StandingRules.winner({ Orthodox = { Renown = 500, Members = 100 }, Unorthodox = { Renown = 80, Members = 4 } }), "Unorthodox", "per member, not in all")
    t.eq(StandingRules.winner({}), nil)
    t.eq(StandingRules.winner(nil), nil)
    t.eq(StandingRules.winner({ Orthodox = { Renown = 0, Members = 0 } }), nil, "nothing earned")
    t.eq(StandingRules.winner({ Orthodox = { Renown = 60, Members = 3 }, Demonic = { Renown = 60, Members = 3 } }), nil, "a tie")
    t.eq(StandingRules.winner({ Orthodox = { Renown = 60, Members = 3 }, Demonic = { Renown = 60, Members = 3 }, Unorthodox = { Renown = 90, Members = 3 } }), "Unorthodox")
end)

t.test("a saved state is cleaned and paid ranks never pass the ranks reached", function()
    local clean = StandingRules.sanitize(nil)
    t.eq(clean.Renown, 0)
    t.eq(clean.Paid, 0)
    local dirty = StandingRules.sanitize({ Renown = 70.9, Paid = 99, CacheDay = -4, Week = "x", WeekRenown = 0 / 0, LastWeek = 5, LastRenown = 1e12, WarClaimed = 5 })
    t.eq(dirty.Renown, 70)
    t.eq(dirty.Paid, StandingRules.rankOf(70), "paid is held to what 70 renown reached")
    t.eq(dirty.CacheDay, 0)
    t.eq(dirty.Week, 0)
    t.eq(dirty.WeekRenown, 0)
    t.eq(dirty.LastRenown, 0, "an impossible number is garbage")
    t.eq(dirty.LastWeek, 5)
    t.eq(StandingRules.sanitize("junk").Renown, 0)
end)

t.test("earning adds to the total and the week, and reports the first of a week", function()
    local data = StandingRules.sanitize(nil)
    t.ok(StandingRules.earn(data, 100, 4), "the first renown of a week")
    t.falsy(StandingRules.earn(data, 100, 3), "the second is not")
    t.eq(data.Renown, 7)
    t.eq(data.WeekRenown, 7)
    t.eq(data.Week, 100)
    t.falsy(StandingRules.earn(data, 100, -5))
    t.falsy(StandingRules.earn(data, 100, 0 / 0))
    t.eq(data.Renown, 7, "a bad amount adds nothing")
end)

t.test("a new week keeps what was earned as last week's and starts this week empty", function()
    local data = StandingRules.sanitize({ Renown = 50, Week = 100, WeekRenown = 30 })
    StandingRules.roll(data, 100)
    t.eq(data.WeekRenown, 30)
    StandingRules.roll(data, 101)
    t.eq(data.Week, 101)
    t.eq(data.WeekRenown, 0)
    t.eq(data.LastWeek, 100)
    t.eq(data.LastRenown, 30)
    t.eq(data.Renown, 50, "the total stays")
    StandingRules.roll(data, 103) -- (two weeks away: last week is the one before, which had nothing)
    t.eq(data.LastWeek, 101)
    t.eq(data.LastRenown, 0)
    local fresh = StandingRules.sanitize(nil)
    StandingRules.roll(fresh, 50)
    t.eq(fresh.LastWeek, 0, "a first ever week has nothing to keep")
end)

t.test("owed lists the ranks reached and not yet paid", function()
    local data = StandingRules.sanitize({ Renown = 210, Paid = 2 })
    local owed = StandingRules.owed(data)
    t.eq(#owed, 1)
    t.eq(owed[1], 3)
    data.Paid = 3
    t.eq(#StandingRules.owed(data), 0)
    t.eq(#StandingRules.owed(StandingRules.sanitize({ Renown = 5000 })), StandingRules.ranks)
end)

t.finish("standing")

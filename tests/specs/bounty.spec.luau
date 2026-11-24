-- The guardian bounty's rules (shared/BountyRules, GameConfig.Bounty): the marked guardian, the tiers, the rewards, the saved state.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local BountyRules = require("@shared/BountyRules")
local TitleRules = require("@shared/TitleRules")

t.test("the config is well formed: known guardians, ascending tiers, positive stones", function()
    local config = GameConfig.Bounty
    t.ok(#config.Order >= 2)
    local seen = {}
    for _, id in config.Order do
        t.ok(GameConfig.Guardians[id] ~= nil, id .. " is a guardian")
        t.ok(not seen[id], id .. " listed twice")
        seen[id] = true
    end
    for id in GameConfig.Guardians do
        t.ok(seen[id], id .. " is on the board")
    end
    local last = 0
    for index, tier in config.Tiers do
        t.ok(tier.Conquests > last, "tier " .. index .. " needs more conquests than the one before")
        t.ok(tier.Stones >= 1)
        last = tier.Conquests
    end
    t.ok(config.ConquestShare > GameConfig.EggTheft.TakeShare, "a conquest asks for more than an egg's share")
    t.ok(config.ConquestShare > 0 and config.ConquestShare <= 1)
    t.ok(config.Cooldown > 0 and config.DailyStones >= 1)
end)

t.test("every guardian has a conquest title and no title is shared", function()
    local seen = {}
    for _, id in GameConfig.Bounty.Order do
        local title = TitleRules.ConquestTitleIds[id]
        t.ok(title ~= nil, id .. " has a title")
        t.ok(TitleRules.ById[title] ~= nil)
        t.ok(not seen[title])
        seen[title] = true
        t.eq(TitleRules.ById[title].Bonus, nil, "no bonus")
    end
end)

t.test("the marked guardian walks through the order, one a day, the same for everyone", function()
    local order = GameConfig.Bounty.Order
    for day = 20000, 20000 + #order * 3 do
        t.eq(BountyRules.marked(day), order[(day % #order) + 1])
        t.eq(BountyRules.marked(day + #order), BountyRules.marked(day), "a full round repeats")
    end
    local week = {}
    for day = 20000, 20000 + #order - 1 do
        week[BountyRules.marked(day)] = true
    end
    local n = 0
    for _ in week do
        n += 1
    end
    t.eq(n, #order, "a round visits every guardian once")
    t.eq(BountyRules.marked(nil), order[1])
    t.eq(BountyRules.marked(0 / 0), order[1])
end)

t.test("tiers are reached at their counts and not before", function()
    local tiers = BountyRules.tiers
    t.eq(BountyRules.reached(0), 0)
    for index, tier in tiers do
        t.eq(BountyRules.reached(tier.Conquests - 1), index - 1)
        t.eq(BountyRules.reached(tier.Conquests), index)
        t.eq(BountyRules.reached(tier.Conquests + 1000 * 0), index)
    end
    t.eq(BountyRules.reached(1e9), #tiers)
    t.eq(BountyRules.reached("5"), 0)
    local index, tier = BountyRules.nextTier(0)
    t.eq(index, 1)
    t.eq(tier.Conquests, tiers[1].Conquests)
    t.eq(BountyRules.nextTier(tiers[#tiers].Conquests), nil, "past the last tier")
end)

t.test("stones grow with the realm and never fall under one", function()
    t.ok(BountyRules.dailyStones(1) >= 1)
    t.ok(BountyRules.dailyStones(5) > BountyRules.dailyStones(1))
    for tier = 1, #BountyRules.tiers do
        t.ok(BountyRules.tierStones(tier, 1) >= 1)
        t.ok(BountyRules.tierStones(tier, 6) > BountyRules.tierStones(tier, 1))
    end
    t.eq(BountyRules.tierStones(99, 1), 0, "no such tier")
    local total = 0
    for tier = 1, #BountyRules.tiers do
        total += GameConfig.Bounty.Tiers[tier].Stones
    end
    t.ok(total * #GameConfig.Bounty.Order <= 500, "the ladders are a long chase, not a fortune (realm-1 stones, all five)")
end)

t.test("the damage that counts as a share is ConquestShare of what weakening takes", function()
    local lion = GameConfig.Guardians.StoneLion
    local need = BountyRules.threshold(lion)
    t.near(need, lion.MaxHealth * (1 - lion.WeakenedAt) * GameConfig.Bounty.ConquestShare, 1e-9)
    t.ok(need > lion.MaxHealth * (1 - lion.WeakenedAt) * GameConfig.EggTheft.TakeShare)
end)

t.test("a saved state is cleaned: known guardians, whole counts, a paid count never past what the count reached", function()
    local clean = BountyRules.sanitize(nil)
    t.eq(next(clean.Counts), nil)
    t.eq(next(clean.Paid), nil)
    t.eq(clean.DayPaid, false)
    local dirty = BountyRules.sanitize({
        Counts = { StoneLion = 7.9, MantisSage = -3, Nobody = 50, EmberXuanwu = "9", Tiangou = 1e12, Pangu = 0 / 0 },
        Paid = { StoneLion = 99, MantisSage = 2, Tiangou = 2 },
        Day = 5, DayPaid = true,
    })
    t.eq(dirty.Counts.StoneLion, 7)
    t.eq(dirty.Counts.MantisSage, nil)
    t.eq(dirty.Counts.Nobody, nil)
    t.eq(dirty.Counts.EmberXuanwu, nil)
    t.eq(dirty.Counts.Tiangou, nil, "an impossible count is garbage")
    t.eq(dirty.Counts.Pangu, nil)
    t.eq(dirty.Paid.StoneLion, BountyRules.reached(7), "paid is held to what 7 conquests reached")
    t.eq(dirty.Paid.MantisSage, nil, "paid without any conquest")
    t.eq(dirty.Day, 5)
    t.eq(dirty.DayPaid, true)
    t.eq(BountyRules.sanitize("junk").Day, 0)
    t.eq(BountyRules.sanitize({ Counts = "x", Paid = 3 }).Counts.StoneLion, nil)
end)

t.test("the day's flag starts afresh when the day moves on, the counts stay", function()
    local data = BountyRules.sanitize({ Counts = { StoneLion = 3 }, Day = 10, DayPaid = true })
    BountyRules.roll(data, 10)
    t.eq(data.DayPaid, true)
    BountyRules.roll(data, 11)
    t.eq(data.DayPaid, false)
    t.eq(data.Day, 11)
    t.eq(data.Counts.StoneLion, 3)
end)

t.test("owed lists the tiers reached and not paid, lowest first, and nothing once they are paid", function()
    local data = BountyRules.sanitize({ Counts = { StoneLion = 6, Pangu = 1 }, Paid = { StoneLion = 1 } })
    local owed = BountyRules.owed(data)
    t.eq(#owed, 2)
    t.eq(owed[1][1], "StoneLion")
    t.eq(owed[1][2], 2)
    t.eq(owed[2][1], "Pangu")
    t.eq(owed[2][2], 1)
    data.Paid.StoneLion, data.Paid.Pangu = 2, 1
    t.eq(#BountyRules.owed(data), 0)
    local all = BountyRules.sanitize({ Counts = { StoneLion = 1000 } })
    t.eq(#BountyRules.owed(all), #BountyRules.tiers)
end)

t.finish("bounty")

-- GameConfig.Ranks (60 ranks in 12 realms of 5) and the look-ups over them (Ranks).
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local Ranks = require("@shared/Ranks")

local ranks = GameConfig.Ranks

t.test("sixty ranks in twelve realms of five", function()
    t.eq(#ranks, 60)
    local realms, order = {}, {}
    for _, rank in ranks do
        if not realms[rank.Realm] then
            realms[rank.Realm] = 0
            table.insert(order, rank.Realm)
        end
        realms[rank.Realm] += 1
    end
    t.eq(#order, 12, "realms")
    for _, realm in order do
        t.eq(realms[realm], 5, realm .. " should have five ranks")
    end
end)

t.test("ids and names are unique", function()
    local ids, names = {}, {}
    for _, rank in ranks do
        t.falsy(ids[rank.Id], "duplicate id " .. rank.Id)
        t.falsy(names[rank.Name], "duplicate name " .. rank.Name)
        ids[rank.Id], names[rank.Name] = true, true
    end
end)

t.test("the Qi needed and the Qi multiplier never go down, and the Qi needed always goes up", function()
    t.eq(ranks[1].QiRequired, 0, "the first rank costs nothing")
    for i = 2, #ranks do
        t.ok(ranks[i].QiRequired > ranks[i - 1].QiRequired, ranks[i].Name .. " needs more Qi than " .. ranks[i - 1].Name)
        t.ok(ranks[i].QiMultiplier >= ranks[i - 1].QiMultiplier, ranks[i].Name .. " must not lower the Qi multiplier")
    end
end)

t.test("the aura tier is a whole number from 1 to 5 that never goes down", function()
    -- (the older five-step aura ladder: it climbs over the first ranks and stays at 5; the realm auras use the realm, not this)
    t.eq(ranks[1].AuraTier, 1)
    t.eq(ranks[#ranks].AuraTier, 5)
    for i, rank in ranks do
        t.ok(rank.AuraTier >= 1 and rank.AuraTier <= 5 and rank.AuraTier == math.floor(rank.AuraTier), rank.Name .. " aura tier " .. tostring(rank.AuraTier))
        if i > 1 then
            t.ok(rank.AuraTier >= ranks[i - 1].AuraTier, rank.Name .. " must not lower the aura tier")
        end
    end
end)

t.test("lookups agree with each other for every rank", function()
    for index, rank in ranks do
        t.eq(Ranks.getIndex(rank.Name), index)
        t.eq(Ranks.getRank(rank.Name), rank)
        t.eq(Ranks.getRankById(rank.Id), rank)
        t.eq(Ranks.getNextRank(rank.Name), ranks[index + 1])
    end
end)

t.test("unknown ranks", function()
    t.eq(Ranks.getIndex("Nobody"), nil)
    t.eq(Ranks.getRank("Nobody"), nil)
    t.eq(Ranks.getRankById("Nobody"), nil)
    t.eq(Ranks.getNextRank("Nobody"), nil)
    t.eq(Ranks.getNextRank(ranks[#ranks].Name), nil, "the top rank has no next")
    t.eq(Ranks.getQiMultiplier("Nobody"), 1, "an unknown rank multiplies by 1")
    t.falsy(Ranks.isAtLeast("Nobody", ranks[1].Id), "an unknown rank is at least nothing")
    t.falsy(Ranks.isAtLeast(ranks[1].Name, "Nobody"), "nothing is below an unknown rank id")
end)

t.test("isAtLeast follows the order", function()
    local middle = ranks[30]
    t.ok(Ranks.isAtLeast(middle.Name, middle.Id))
    t.ok(Ranks.isAtLeast(ranks[31].Name, middle.Id))
    t.falsy(Ranks.isAtLeast(ranks[29].Name, middle.Id))
end)

t.test("Qinggong levels belong to ranks, in order, and the lookup is monotonic", function()
    local levels = GameConfig.Qinggong.Levels
    local lastIndex = 0
    for _, level in levels do
        local rank = Ranks.getRankById(level.RankId)
        t.ok(rank ~= nil, "Qinggong level for an unknown rank " .. tostring(level.RankId))
        local index = Ranks.getIndex(rank.Name)
        t.ok(index > lastIndex, "Qinggong levels must rise with the rank")
        lastIndex = index
    end
    local previous = 0
    for _, rank in ranks do
        local current = Ranks.getQinggong(rank.Name)
        local at = table.find(levels, current)
        t.ok(at ~= nil and at >= previous, "the Qinggong level never drops as the rank rises (" .. rank.Name .. ")")
        previous = at
    end
    local current, nextLevel = Ranks.getQinggong("Nobody")
    t.eq(current, levels[1], "an unknown rank counts as the first level")
    t.eq(nextLevel, levels[2])
    local top, after = Ranks.getQinggong(ranks[#ranks].Name)
    t.eq(top, levels[#levels])
    t.eq(after, nil, "no level after the last")
end)

t.test("flight needs the unlock rank and gives a speed only then", function()
    local unlock = Ranks.getRankById(GameConfig.SwordFlight.UnlockRank)
    t.ok(unlock ~= nil, "SwordFlight.UnlockRank must be a rank id")
    local index = Ranks.getIndex(unlock.Name)
    t.ok(Ranks.canFly(unlock.Name))
    t.ok(Ranks.canFly(ranks[#ranks].Name))
    t.ok(Ranks.getFlightSpeed(unlock.Name) > 0)
    t.falsy(Ranks.canFly(ranks[index - 1].Name))
    t.eq(Ranks.getFlightSpeed(ranks[index - 1].Name), 0)
end)

t.finish("ranks")

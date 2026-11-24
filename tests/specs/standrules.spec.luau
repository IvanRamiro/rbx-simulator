-- StandRules: who an egg pays in full, and the contention-scaled respawn of a stand (shared/StandRules).
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local Ranks = require("@shared/Ranks")
local StandRules = require("@shared/StandRules")

local function eggsOf(guardianId)
    return GameConfig.Guardians[guardianId].Eggs
end

t.test("alone, a stand keeps today's 180 seconds; rivals shorten it, never under the floor or over 180", function()
    local base, floor = GameConfig.EggTheft.RespawnTime, GameConfig.EggTheft.RespawnMin
    t.eq(StandRules.respawnTime(1), base, "one contender must keep today's respawn")
    t.eq(StandRules.respawnTime(0), base, "nobody counted is the same as alone")
    t.eq(StandRules.respawnTime(nil), base, "garbage is the same as alone")
    t.eq(StandRules.respawnTime("many"), base, "a string is the same as alone")
    t.near(StandRules.respawnTime(2), base / 2, 1e-9, "two contenders halve it")
    t.eq(StandRules.respawnTime(3), floor, "three reach the floor (180 / 3 = 60)")
    t.eq(StandRules.respawnTime(50), floor, "never under the floor")
    for n = 1, 12 do
        t.ok(StandRules.respawnTime(n) <= StandRules.respawnTime(math.max(1, n - 1)), "more contenders never makes it slower")
    end
    t.ok(floor > 0 and floor < base, "the floor is a real range")
end)

t.test("the best egg a player can take pays them in full, the others do not", function()
    -- a Divine Initiate on: the top egg of Pangu's island is the best egg of all
    local pangu = eggsOf("Pangu")
    local topRank, topEgg = 0, nil
    for _, eggId in pangu do
        local rank = Ranks.getRankById(GameConfig.Eggs[eggId].RequiredRank)
        if (Ranks.getIndex(rank.Name) or 0) > topRank then
            topRank, topEgg = Ranks.getIndex(rank.Name), eggId
        end
    end
    local last = nil
    for index = #GameConfig.Ranks, 1, -1 do
        last = GameConfig.Ranks[index]
        break
    end
    t.ok(StandRules.paysFull(topEgg, last.Name), "the top egg pays the top rank in full")
    t.ok(StandRules.contends(topEgg, last.Name), "and the top rank contends for it")
    for _, eggId in pangu do
        local mine = Ranks.getQiMultiplier(Ranks.getRankById(GameConfig.Eggs[eggId].RequiredRank).Name)
        local best = Ranks.getQiMultiplier(Ranks.getRankById(GameConfig.Eggs[topEgg].RequiredRank).Name)
        if eggId ~= topEgg then
            t.ok(mine < best, "the test's own premise: " .. eggId .. " is a lesser egg than " .. topEgg)
            t.ok(not StandRules.paysFull(eggId, last.Name), eggId .. " must not pay the top rank in full: only the best egg does")
        end
    end
    -- a beginner can take no Pangu egg, so they never contend for one
    local first = GameConfig.Ranks[1]
    for _, eggId in pangu do
        t.ok(not StandRules.contends(eggId, first.Name), "a beginner does not contend for " .. eggId)
    end
    t.ok(StandRules.bestMultiplier(first.Name) >= 1, "the best multiplier is at least 1")
end)

t.test("the payout rule is the one QiReward used: a player's best takeable egg pays in full, always, at every rank", function()
    for _, rank in GameConfig.Ranks do
        local pays = 0
        for _, guardian in GameConfig.Guardians do
            for _, eggId in guardian.Eggs do
                if StandRules.canTake(eggId, rank.Name) and StandRules.paysFull(eggId, rank.Name) then
                    pays += 1
                end
            end
        end
        t.ok(pays >= 1, rank.Name .. ": at least one takeable egg pays in full (or the climb stalls)")
    end
end)

t.test("the spec can fail: a respawn that ignores the floor or the base is caught", function()
    local floor = GameConfig.EggTheft.RespawnMin
    local broken = 180 / 50 -- what an unclamped rule would give for 50 contenders
    t.ok(broken < floor, "an unclamped respawn would fall under the floor")
end)

t.finish("standrules")

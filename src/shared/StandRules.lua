-- Who an egg stand's egg pays in full, and how soon a stand refills (2026-11-24, from the economy re-simulation: tools/economy/resim.py, section G).
--
-- An egg's Qi burst is capped at the egg's own realm, except that the BEST egg a player can take pays their own realm in full (server/Cultivation/QiReward;
-- release balance 2026-11-12: the top realms have no egg of their own, so without this the climb stalled). From the Divine Realm on, that best egg is always the
-- top one on Pangu's island, one stand that refills every EggTheft.RespawnTime for the whole server. Alone that is fine; with rivals after the same stand a free
-- player's climb went from 4.9 to 6.9 days (the model's bound). So a stand refills sooner the more players it is the full-paying egg for:
--
--   respawnTime(contenders) = RespawnTime / contenders, never under RespawnMin and never over RespawnTime. One contender (alone on the server, or nobody else
--   at that realm) keeps today's 180 s exactly; two get 90 s; three or more 60 s. The values of every egg and every realm multiplier stay as they are.
--
--   StandRules.bestMultiplier(rankName)       the highest realm multiplier among the eggs a player of this rank can take (1 if none)
--   StandRules.paysFull(eggId, rankName)      whether this egg pays a player of this rank their own realm in full
--   StandRules.contends(eggId, rankName)      whether this player is after this egg: they can take it and it pays them in full
--   StandRules.respawnTime(contenders)        seconds a stand stays empty after its egg is secured
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local StandRules = {}

local function eggRank(eggId)
    local egg = GameConfig.Eggs[eggId]
    return egg and Ranks.getRankById(egg.RequiredRank) or nil
end

function StandRules.canTake(eggId, rankName)
    local rank = eggRank(eggId)
    return rank ~= nil and (Ranks.getIndex(rankName) or 1) >= (Ranks.getIndex(rank.Name) or math.huge)
end

function StandRules.bestMultiplier(rankName)
    local best = 1
    for _, guardian in GameConfig.Guardians do
        for _, eggId in guardian.Eggs or {} do
            local rank = eggRank(eggId)
            if rank and StandRules.canTake(eggId, rankName) then
                best = math.max(best, Ranks.getQiMultiplier(rank.Name))
            end
        end
    end
    return best
end

function StandRules.paysFull(eggId, rankName)
    local rank = eggRank(eggId)
    return rank ~= nil and Ranks.getQiMultiplier(rank.Name) >= StandRules.bestMultiplier(rankName)
end

function StandRules.contends(eggId, rankName)
    return StandRules.canTake(eggId, rankName) and StandRules.paysFull(eggId, rankName)
end

function StandRules.respawnTime(contenders)
    local theft = GameConfig.EggTheft
    local n = if typeof(contenders) == "number" and contenders >= 1 then contenders else 1
    return math.clamp(theft.RespawnTime / n, theft.RespawnMin, theft.RespawnTime)
end

return StandRules

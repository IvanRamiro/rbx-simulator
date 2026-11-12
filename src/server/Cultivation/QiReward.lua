-- Qi from outside meditation, all at the cultivating rate (the player's pets and Qi passes count, the Qi Spring
-- doesn't). Securing a stolen egg pays a burst worth EggTheft.SecureQiMinutes, so the chase is the
-- fastest way to grow and meditation stays the steady base. Its realm multiplier is the lower of the
-- player's and the egg's, so a high realm farming a beginner's guardian earns a beginner's Qi, and
-- the way forward is the next island. RewardService also pays offline Qi and daily minutes here.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Server = script.Parent.Parent
local PetInventory = require(Server:WaitForChild("Pets"):WaitForChild("PetInventory"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))

local QiReward = {}

-- Grants `seconds` of cultivating, its realm multiplier capped at `maxMultiplier` if given; returns
-- the Qi paid (0 if the player's stats aren't there).
function QiReward.grantAtRate(player, seconds, maxMultiplier)
    local qi, rankValue = PlayerData.getStats(player)
    if not (qi and rankValue) then
        return 0
    end
    local multiplier = math.min(Ranks.getQiMultiplier(rankValue.Value), maxMultiplier or math.huge) * PassRules.qiMultiplier(player)
    local perSecond = GameConfig.CultivationQiReward / GameConfig.CultivationInterval * multiplier
        * (100 + PetInventory.getQiBonusPercent(player)) / 100
    local amount = math.floor(perSecond * seconds)
    qi.Value += amount
    return amount
end

function QiReward.grantMinutes(player, minutes)
    return QiReward.grantAtRate(player, minutes * 60)
end

-- The highest realm multiplier among the guardians' eggs a player of this rank can take.
local function bestEggMultiplier(rankName)
    local index = Ranks.getIndex(rankName) or 1
    local best = 1
    for _, guardian in GameConfig.Guardians do
        for _, eggId in guardian.Eggs or {} do
            local egg = GameConfig.Eggs[eggId]
            local eggRank = egg and Ranks.getRankById(egg.RequiredRank)
            if eggRank and (Ranks.getIndex(eggRank.Name) or math.huge) <= index then
                best = math.max(best, Ranks.getQiMultiplier(eggRank.Name))
            end
        end
    end
    return best
end

-- The burst for securing this egg. Its multiplier is capped at the egg's own realm, so a high realm farming a beginner's egg earns a
-- beginner's Qi; but the best egg a player can take pays their own realm in full. (Release balance, 2026-11-12: the Cosmic, Heavenly Dao
-- and Eternal realms have no egg of their own, so the best egg there paid half the realm and the climb stalled each time.)
function QiReward.grantEggBurst(player, eggId)
    local egg = GameConfig.Eggs[eggId]
    local eggRank = egg and Ranks.getRankById(egg.RequiredRank)
    local _, rankValue = PlayerData.getStats(player)
    local cap = if eggRank then Ranks.getQiMultiplier(eggRank.Name) else 1
    if rankValue and cap >= bestEggMultiplier(rankValue.Value) then
        cap = nil
    end
    return QiReward.grantAtRate(player, GameConfig.EggTheft.SecureQiMinutes * 60, cap)
end

return QiReward

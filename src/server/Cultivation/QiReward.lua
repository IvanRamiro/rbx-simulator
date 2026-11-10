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

-- The burst for securing this egg.
function QiReward.grantEggBurst(player, eggId)
    local egg = GameConfig.Eggs[eggId]
    local eggRank = egg and Ranks.getRankById(egg.RequiredRank)
    return QiReward.grantAtRate(player, GameConfig.EggTheft.SecureQiMinutes * 60, if eggRank then Ranks.getQiMultiplier(eggRank.Name) else 1)
end

return QiReward

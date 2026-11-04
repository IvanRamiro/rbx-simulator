-- Qi from play rather than meditation. Securing a stolen egg pays a burst worth
-- EggTheft.SecureQiMinutes of cultivating (the player's pets count, the Qi Spring doesn't), so the
-- chase is the fastest way to grow and meditation stays the steady base. The realm multiplier is the
-- lower of the player's and the egg's, so a high realm farming a beginner's guardian earns a
-- beginner's Qi, and the way forward is the next island.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Server = script.Parent.Parent
local PetInventory = require(Server:WaitForChild("Pets"):WaitForChild("PetInventory"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))

local QiReward = {}

-- Grants the burst for securing this egg; returns the Qi paid (0 if the player's stats aren't there).
function QiReward.grantEggBurst(player, eggId)
    local egg = GameConfig.Eggs[eggId]
    local qi, rankValue = PlayerData.getStats(player)
    if not (egg and qi and rankValue) then
        return 0
    end
    local eggRank = Ranks.getRankById(egg.RequiredRank)
    local multiplier = math.min(Ranks.getQiMultiplier(rankValue.Value), if eggRank then Ranks.getQiMultiplier(eggRank.Name) else 1)
    local perSecond = GameConfig.CultivationQiReward / GameConfig.CultivationInterval * multiplier
        * (100 + PetInventory.getQiBonusPercent(player)) / 100
    local amount = math.floor(perSecond * 60 * GameConfig.EggTheft.SecureQiMinutes)
    qi.Value += amount
    return amount
end

return QiReward

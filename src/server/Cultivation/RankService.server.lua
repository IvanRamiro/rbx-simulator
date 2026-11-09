local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))
local Tribulation = require(script.Parent:WaitForChild("Tribulation"))

-- Ranks the player up to nextRank if they still have its Qi and are still just below it.
local function rankUp(player, fromName, nextRank)
    local qi, rank = PlayerData.getStats(player)
    if player.Parent ~= Players or not (qi and rank) or rank.Value ~= fromName or qi.Value < nextRank.QiRequired then
        return
    end
    rank.Value = nextRank.Name
    PlayerData.saveSoon(player)
    Analytics.event(player, "RankUp", Ranks.getIndex(nextRank.Name), nextRank.Id)
end

-- A breakthrough: within a realm, at once; into a new realm, only by surviving its Heavenly Tribulation (Tribulation).
local function tryRankUp(player)
    if player.Parent ~= Players then
        return
    end

    local qi, rank = PlayerData.getStats(player)
    if not (qi and rank) then
        return
    end

    local nextRank = Ranks.getNextRank(rank.Value)
    if not nextRank then
        return
    end

    if qi.Value < nextRank.QiRequired then
        return
    end

    local current = Ranks.getRank(rank.Value)
    local fromName = rank.Value
    if current and current.Realm ~= nextRank.Realm then
        Tribulation.start(player, Tribulation.realmNumber(nextRank.Realm), function()
            rankUp(player, fromName, nextRank)
        end)
        return
    end
    rankUp(player, fromName, nextRank)
end

RemoteEvents.RankUpEvent.OnServerEvent:Connect(tryRankUp)

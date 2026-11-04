-- Reasons to come back (GameConfig.Rewards), all decided here:
--   offline Qi    on joining, a share of the player's cultivating rate for the time they were away,
--                 from MinMinutes up to MaxHours
--   daily reward  one claim a UTC day; the streak climbs to day 7 and starts over, and a missed day
--                 goes back to day 1 (shared/RewardRules)
--   codes         each once per save (Codes, never sent to clients)
--   group reward  once, for members of Group.GroupId (off while it's 0)
-- RewardEvent, client to server: "ClaimDaily" | "Redeem" code | "ClaimGroup".
-- Server to client: "Offline" qi seconds | "Daily" stones qi day | "Code" ok message | "Group" ok message.
-- Attributes for the window: "DailyReady", "DailyDay" (the next claim's day), "GroupClaimed".
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local RewardRules = require(ReplicatedStorage:WaitForChild("RewardRules"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local QiReward = require(Server:WaitForChild("Cultivation"):WaitForChild("QiReward"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(Server:WaitForChild("Pets"):WaitForChild("PetInventory"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local Codes = require(script.Parent:WaitForChild("Codes"))
local Rewards = require(script.Parent:WaitForChild("Rewards"))

local THROTTLE = 0.5
local config = GameConfig.Rewards

local ready = {}
local lastRequest = {}

local function publish(player)
    local data = Rewards.get(player)
    if not data then
        return
    end
    player:SetAttribute("DailyReady", data.LastDay ~= RewardRules.today())
    player:SetAttribute("DailyDay", if data.LastDay == RewardRules.today()
        then data.Streak else RewardRules.nextDay(data.LastDay, data.Streak))
    player:SetAttribute("GroupClaimed", data.GroupClaimed)
end

local function grantOffline(player, lastSeen)
    if lastSeen <= 0 then
        return
    end
    local seconds = math.min(os.time() - lastSeen, config.Offline.MaxHours * 3600)
    if seconds < config.Offline.MinMinutes * 60 then
        return
    end
    local qi = QiReward.grantAtRate(player, config.Offline.Share * seconds)
    if qi > 0 then
        RemoteEvents.RewardEvent:FireClient(player, "Offline", qi, seconds)
        Analytics.event(player, "OfflineQi", qi)
        PlayerData.saveSoon(player)
    end
end

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    Rewards.setupPlayer(player, if isNewPlayer then nil else progress)
    -- offline Qi needs the player's Qi and pets (their services set them up alongside this one)
    local deadline = os.clock() + 15
    while not ((PlayerData.getStats(player)) and PetInventory.exportData(player)) and os.clock() < deadline do
        task.wait(0.2)
    end
    if player.Parent ~= Players then
        return
    end
    publish(player)
    ready[player] = true
    grantOffline(player, Rewards.get(player).LastSeen)
end

local actions = {}

function actions.ClaimDaily(player)
    local data = Rewards.get(player)
    local today = RewardRules.today()
    if data.LastDay == today then
        return
    end
    local day = RewardRules.nextDay(data.LastDay, data.Streak)
    local stones, minutes = RewardRules.daily(day, Shop.playerRealmIndex(player))
    data.LastDay, data.Streak = today, day
    Wallet.add(player, stones, "Daily", "Day" .. day)
    local qi = if minutes > 0 then QiReward.grantMinutes(player, minutes) else 0
    publish(player)
    PlayerData.saveSoon(player)
    Analytics.event(player, "DailyClaimed", day)
    RemoteEvents.RewardEvent:FireClient(player, "Daily", stones, qi, day)
end

function actions.Redeem(player, raw)
    if typeof(raw) ~= "string" or #raw > 40 then
        return
    end
    local code = string.upper((string.gsub(raw, "%s", "")))
    local reward = Codes[code]
    local data = Rewards.get(player)
    if not reward then
        RemoteEvents.RewardEvent:FireClient(player, "Code", false, "That code isn't valid.")
    elseif table.find(data.Codes, code) then
        RemoteEvents.RewardEvent:FireClient(player, "Code", false, "You've already used that code.")
    else
        table.insert(data.Codes, code)
        Wallet.add(player, reward.Stones, "Code", code)
        PlayerData.saveSoon(player)
        Analytics.event(player, "CodeRedeemed", 1, code)
        RemoteEvents.RewardEvent:FireClient(player, "Code", true, "Code redeemed: +" .. reward.Stones .. " Spirit Stones.")
    end
end

function actions.ClaimGroup(player)
    local data = Rewards.get(player)
    if config.Group.GroupId <= 0 or data.GroupClaimed then
        return
    end
    local ok, member = pcall(player.IsInGroup, player, config.Group.GroupId)
    if not ok then
        RemoteEvents.RewardEvent:FireClient(player, "Group", false, "Couldn't check the group. Try again in a moment.")
    elseif not member or data.GroupClaimed or player.Parent ~= Players then
        RemoteEvents.RewardEvent:FireClient(player, "Group", false, "Join the group first, then claim.")
    else
        data.GroupClaimed = true
        Wallet.add(player, config.Group.Stones, "Group")
        publish(player)
        PlayerData.saveSoon(player)
        RemoteEvents.RewardEvent:FireClient(player, "Group", true, "Thanks for joining: +" .. config.Group.Stones .. " Spirit Stones.")
    end
end

RemoteEvents.RewardEvent.OnServerEvent:Connect(function(player, action, argument)
    local handler = typeof(action) == "string" and actions[action]
    if not (handler and ready[player]) or os.clock() - (lastRequest[player] or 0) < THROTTLE then
        return
    end
    lastRequest[player] = os.clock()
    handler(player, argument)
end)

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    ready[player], lastRequest[player] = nil, nil
end)

-- a new UTC day reaches players already online
while true do
    task.wait(60)
    for player in ready do
        publish(player)
    end
end

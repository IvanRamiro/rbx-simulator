-- The System's quests (GameConfig.Quests), from the first steps out across every island, decided
-- here on the server: each player's current quest is checked a few times a second against what they
-- really did (their Qi and rank, pets, weapons, relics, the island they're on, the egg they carry)
-- and the moments the server sees (an air leap, a strike on a guardian, a secured egg).
-- A finished quest pays its Spirit Stones, moves the player to the next (Quests) and tells their
-- client (QuestEvent "Complete", step, reward). The client may only ask to skip them all
-- (QuestEvent "Skip"). The player's "QuestProgress" attribute (0 to 1) feeds the tracker's bar.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Server = script.Parent.Parent
local Quests = require(script.Parent:WaitForChild("Quests"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(Server:WaitForChild("Pets"):WaitForChild("PetInventory"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local Combat = require(Server:WaitForChild("Combat"):WaitForChild("Combat"))
local WeaponInventory = require(Server:WaitForChild("Shop"):WaitForChild("WeaponInventory"))
local Discoveries = require(Server:WaitForChild("World"):WaitForChild("Discoveries"))
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))

local CHECK_EVERY = 0.25

local ready = {}    -- [player] = true once their quests are loaded
local seen = {}     -- [player] = { [Kind] = true }: the moments seen during the current quest
local baseline = {} -- [player] = pets owned when the current quest began (a "Hatch" counts new ones)

local function petCount(player)
    local data = PetInventory.exportData(player)
    return data and #data.Pets or 0
end

-- the current quest starts afresh: no moments seen yet, pets counted from now
local function begin(player)
    seen[player] = {}
    baseline[player] = petCount(player)
end

-- whether the quest is done, and how far along it is (0 to 1)
local function check(player, quest)
    local leaderstats = player:FindFirstChild("leaderstats")
    local qi = leaderstats and leaderstats:FindFirstChild("Qi")
    local rank = leaderstats and leaderstats:FindFirstChild("Rank")
    if not (qi and rank) then
        return false, 0
    end
    local kind = quest.Kind
    if kind == "Qi" then
        return qi.Value >= quest.Goal, qi.Value / quest.Goal
    elseif kind == "Rank" then
        local done = Ranks.isAtLeast(rank.Value, quest.Goal)
        return done, if done then 1 else qi.Value / Ranks.getRankById(quest.Goal).QiRequired
    elseif kind == "Equip" then
        local data = PetInventory.exportData(player)
        return data ~= nil and #data.EquippedPetIds > 0, 0
    elseif kind == "TakeEgg" then
        return player:GetAttribute("CarryingEgg") ~= nil, 0
    elseif kind == "Hatch" then
        return petCount(player) > (baseline[player] or math.huge), 0
    elseif kind == "BuyWeapon" then
        local data = WeaponInventory.exportData(player)
        return data ~= nil and #data.Weapons >= 2, 0
    elseif kind == "Forge" then
        local data = WeaponInventory.exportData(player)
        for _, weapon in (if data then data.Weapons else {}) do
            if weapon.Element then
                return true, 0
            end
        end
        return false, 0
    elseif kind == "Relic" then
        local found = Discoveries.exportData(player)
        return found ~= nil and table.find(found, quest.Goal) ~= nil, 0
    elseif kind == "Visit" then
        return player:GetAttribute("Island") == quest.Goal, 0
    end
    return seen[player] ~= nil and seen[player][kind] == true, 0 -- "Leap", "GuardianHit", "Secure"
end

local function complete(player, step)
    local quest = GameConfig.Quests[step]
    Wallet.add(player, quest.Reward, "Quest", quest.Id)
    Analytics.questStep(player, step, quest.Id)
    Quests.set(player, step + 1)
    begin(player)
    player:SetAttribute("QuestProgress", 0)
    RemoteEvents.QuestEvent:FireClient(player, "Complete", step, quest.Reward)
    PlayerData.saveSoon(player)
end

-- a moment the server saw: it counts only toward the quest the player is on
local function saw(player, kind, goal)
    local step = ready[player] and Quests.get(player)
    local quest = step and GameConfig.Quests[step]
    if quest and quest.Kind == kind and (quest.Goal == nil or quest.Goal == goal) and seen[player] then
        seen[player][kind] = true
    end
end

RemoteEvents.QinggongFxEvent.OnServerEvent:Connect(function(player, kind)
    if kind == "Leap" then
        saw(player, "Leap")
    end
end)

Combat.Hit.Event:Connect(function(player, target)
    if typeof(player) == "Instance" and player:IsA("Player") and typeof(target) == "Instance"
        and CollectionService:HasTag(target, GameConfig.GuardianTag) then
        saw(player, "GuardianHit")
    end
end)

Quests.Moment.Event:Connect(saw)

RemoteEvents.QuestEvent.OnServerEvent:Connect(function(player, action)
    if action == "Skip" and ready[player] and Quests.get(player) < Quests.DONE then
        Analytics.event(player, "QuestsSkipped", Quests.get(player))
        Quests.set(player, Quests.DONE)
        PlayerData.saveSoon(player)
    end
end)

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    Quests.setupPlayer(player, if isNewPlayer then nil else progress)
    begin(player)
    player:SetAttribute("QuestProgress", 0)
    ready[player] = true
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    ready[player], seen[player], baseline[player] = nil, nil, nil
end)

while true do
    task.wait(CHECK_EVERY)
    for player in ready do
        local step = Quests.get(player)
        local quest = step and GameConfig.Quests[step]
        if quest and player.Parent == Players then
            local done, share = check(player, quest)
            player:SetAttribute("QuestProgress", math.clamp(share, 0, 1))
            if done then
                complete(player, step)
            end
        end
    end
end

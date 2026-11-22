-- The Murim factions (GameConfig.Faction, shared/FactionRules; the pledge itself is FactionBook). The client only asks; this decides.
--
-- FactionEvent (client -> server):
--   "Join", factionId     take the pledge. Refused unless the player: has had their record read, belongs to no faction, is at least at
--                         GameConfig.Faction.JoinRealm, is alive and within RepRange of that faction's representative (a model tagged
--                         FactionRules.RepTag whose "Faction" attribute names it), and isn't asking too fast. Then the one set-once write
--                         (FactionBook.join). A refusal says why in plain words; nothing ever changes or removes a faction.
--   "Take"                take the faction's secret weapon from its vault, once the trial is passed (FactionBook.markTrial) and the
--                         player is at their own faction's vault (tagged FactionRules.VaultTag). A member holding the weapon is
--                         refused; one who lost it (a bound weapon can't be sold, so only a rolled-back save) may take it again.
-- FactionEvent (server -> client): "Joined" (faction id), "Taken" (weapon id), "Refused" (text).
-- Every member's "FactionTrial" attribute (shared/FactionRules) is kept right here, every couple of seconds.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local FactionRules = require(ReplicatedStorage:WaitForChild("FactionRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local serverRoot = script.Parent.Parent
local FactionBook = require(script.Parent:WaitForChild("FactionBook"))
local PlayerData = require(serverRoot:WaitForChild("Data"):WaitForChild("PlayerData"))
local WeaponInventory = require(serverRoot:WaitForChild("Shop"):WaitForChild("WeaponInventory"))
local PromptRules = require(serverRoot:WaitForChild("World"):WaitForChild("PromptRules"))

local Event = RemoteEvents.FactionEvent
local THROTTLE = 1.2
local REFRESH_EVERY = 2

local lastRequest = {}
local busy = {} -- [player] = true while their join or vault write runs

local function tell(player, text)
    if player.Parent == Players then
        Event:FireClient(player, "Refused", text)
    end
end

local function partOf(model)
    if model:IsA("BasePart") then
        return model
    end
    return model.PrimaryPart or model:FindFirstChild("HumanoidRootPart") or model:FindFirstChildWhichIsA("BasePart", true)
end

-- whether the player is alive and within reach of one of the tagged models of that faction
local function nearTagged(player, tag, factionId)
    for _, model in CollectionService:GetTagged(tag) do
        if model:GetAttribute("Faction") == factionId and model:IsDescendantOf(workspace) then
            local part = partOf(model)
            if part and PromptRules.isAliveAndNear(player, part, GameConfig.Faction.RepRange + 6) then
                return true
            end
        end
    end
    return false
end

local function weaponIdOf(factionId)
    return FactionRules.get(factionId).Weapon.Id
end

local function join(player, factionId)
    if not FactionRules.isFaction(factionId) then
        return
    end
    local info = FactionRules.get(factionId)
    if not FactionBook.ready(player) then
        tell(player, "Your faction record is still loading. Try again in a moment.")
        return
    end
    local own = FactionBook.factionOf(player)
    if own then
        tell(player, "You already belong to the " .. FactionRules.get(own).DisplayName .. ". A faction is for good.")
        return
    end
    if FactionBook.record(player) or FactionBook.hasUnreadable(player) then
        tell(player, "Your faction record can't be read right now, so you can't join. Please try again later.")
        return
    end
    if not FactionRules.canJoin(Ranks.getPlayerRankName(player)) then
        tell(player, "Reach " .. GameConfig.Faction.JoinRealm .. " to join a faction.")
        return
    end
    if not nearTagged(player, FactionRules.RepTag, factionId) then
        tell(player, "Walk up to " .. info.Master .. " to join.")
        return
    end
    local outcome, record = FactionBook.join(player, factionId)
    if player.Parent ~= Players then
        return
    end
    if outcome == "Set" then
        Event:FireClient(player, "Joined", factionId)
    elseif outcome == "Taken" and record and FactionRules.isFaction(record.Faction) then
        -- (another server, or an earlier try of this one, took it first: they are told what they are)
        tell(player, "You already belong to the " .. FactionRules.get(record.Faction).DisplayName .. ". A faction is for good.")
    else
        tell(player, "The faction couldn't be reached right now. Please try again in a moment.")
    end
end

local function take(player)
    local factionId = FactionBook.factionOf(player)
    local record = FactionBook.record(player)
    if not factionId or not record then
        return
    end
    local info = FactionRules.get(factionId)
    if not record.Trial then
        tell(player, "Pass " .. info.Master .. "'s trial first.")
        return
    end
    local weaponId = weaponIdOf(factionId)
    if WeaponInventory.owns(player, weaponId) then
        tell(player, "You already hold the " .. info.Weapon.Name .. ".")
        return
    end
    if not nearTagged(player, FactionRules.VaultTag, factionId) then
        tell(player, "Go to your faction's vault to take your weapon.")
        return
    end
    if WeaponInventory.isFull(player) then
        tell(player, "Your weapon rack is full. Sell one, then take the " .. info.Weapon.Name .. ".")
        return
    end
    if not PlayerData.canSave(player) then
        tell(player, "Your progress can't be saved right now, so the weapon can't be given yet. Please try again in a moment.")
        return
    end
    if not WeaponInventory.grant(player, weaponId) then
        tell(player, "The weapon couldn't be given. Please try again.")
        return
    end
    -- written now, so a crash can't lose it (and a rolled-back save is made good by taking it again)
    PlayerData.saveConfirmed(player)
    if player.Parent == Players then
        Event:FireClient(player, "Taken", weaponId)
    end
end

Event.OnServerEvent:Connect(function(player, action, argument)
    if typeof(action) ~= "string" then
        return
    end
    local now = os.clock()
    if now - (lastRequest[player] or 0) < THROTTLE or busy[player] then
        return
    end
    lastRequest[player] = now
    busy[player] = true
    local ok, err = pcall(function()
        if action == "Join" then
            join(player, argument)
        elseif action == "Take" then
            take(player)
        end
    end)
    busy[player] = nil
    if not ok then
        warn("FactionService: " .. tostring(err))
    end
end)

-- ---------- what the clients show of the trial ----------
local function trialState(player)
    local factionId = FactionBook.factionOf(player)
    if not factionId then
        return nil
    end
    if WeaponInventory.owns(player, weaponIdOf(factionId)) then
        return "Done"
    end
    local record = FactionBook.record(player)
    if record and record.Trial then
        return "Passed"
    end
    local endsAt = FactionBook.runEnds(player)
    if endsAt and endsAt > workspace:GetServerTimeNow() then
        return "Running", endsAt
    end
    return if FactionRules.canTrial(Ranks.getPlayerRankName(player)) then "Open" else "Locked"
end

local racked = {} -- [player] = true once their weapon rack is in (ShopService sets it up after the save loads)

local function refresh(player)
    -- (their rack is read only once it is in: before that a member who holds the weapon would show "Passed")
    if not racked[player] then
        if WeaponInventory.snapshot(player) == nil then
            return
        end
        racked[player] = true
    end
    local state, endsAt = trialState(player)
    FactionBook.setTrial(player, state, endsAt)
end

Players.PlayerAdded:Connect(FactionBook.setup)
for _, player in Players:GetPlayers() do
    task.spawn(FactionBook.setup, player)
end
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    busy[player] = nil
    racked[player] = nil
    FactionBook.forget(player)
end)

task.spawn(function()
    while true do
        task.wait(REFRESH_EVERY)
        for _, player in Players:GetPlayers() do
            refresh(player)
        end
    end
end)

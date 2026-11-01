local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local EggInventory = require(script.Parent:WaitForChild("EggInventory"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local PromptRules = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("PromptRules"))

local random = Random.new()

local lastHatchTime = {}

local function sendInventory(player)
    local snapshot = PetInventory.getSnapshot(player)
    RemoteEvents.PetInventoryUpdatedEvent:FireClient(player, snapshot)

    local auraPetId = nil
    if snapshot and snapshot.AuraPetInstanceId then
        for _, pet in snapshot.Pets do
            if pet.InstanceId == snapshot.AuraPetInstanceId then
                auraPetId = pet.PetId
            end
        end
    end
    player:SetAttribute("AuraPetId", auraPetId)

    local equippedPetIds = {}
    if snapshot then
        for _, pet in snapshot.Pets do
            if pet.Equipped then
                table.insert(equippedPetIds, pet.PetId)
            end
        end
    end
    player:SetAttribute("EquippedPetIds", table.concat(equippedPetIds, ","))
end

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress then
        return
    end

    PetInventory.setupPlayer(player, if isNewPlayer then nil else progress)
    EggInventory.setupPlayer(player, if isNewPlayer then nil else progress)
    sendInventory(player)
end

local function handleRequest(remoteEvent, action)
    remoteEvent.OnServerEvent:Connect(function(player, instanceId)
        if action(player, instanceId) then
            sendInventory(player)
        end
    end)
end

local function rollEggPet(egg)
    local pool = egg.Pool

    local totalWeight = 0
    for _, entry in pool do
        totalWeight += entry.Weight
    end

    local roll = random:NextNumber() * totalWeight
    for _, entry in pool do
        if roll < entry.Weight then
            return entry.PetId, entry.Weight / totalWeight
        end
        roll -= entry.Weight
    end

    local lastEntry = pool[#pool]
    return lastEntry.PetId, lastEntry.Weight / totalWeight
end

-- The guardian standing in the world that guards this egg, if any: while it stands, the egg is
-- only hatched from the player's egg inventory (eggs taken from it), never for free.
local function guardianOf(eggId)
    for _, model in CollectionService:GetTagged(GameConfig.GuardianTag) do
        local config = GameConfig.Guardians[model:GetAttribute("GuardianId")]
        if config and model:IsDescendantOf(workspace) and table.find(config.Eggs, eggId) then
            return config
        end
    end
    return nil
end

local function onEggTriggered(player, eggId, eggPart, maxDistance)
    local egg = GameConfig.Eggs[eggId]
    if not egg or player.Parent ~= Players or not PromptRules.isAliveAndNear(player, eggPart, maxDistance) then
        return
    end

    local _, rankValue = PlayerData.getStats(player)
    if not (rankValue and Ranks.isAtLeast(rankValue.Value, egg.RequiredRank)) then
        RemoteEvents.EggHatchResultEvent:FireClient(player, {
            EggId = eggId,
            Reason = "Locked",
            RequiredRank = Ranks.getRankById(egg.RequiredRank).Name,
        })
        return
    end

    -- a guarded egg comes from the inventory and was earned, so it skips the cooldown
    local guardian = guardianOf(eggId)
    local now = os.clock()
    local playerHatchTimes = lastHatchTime[player] or {}
    lastHatchTime[player] = playerHatchTimes
    if guardian then
        if EggInventory.count(player, eggId) < 1 then
            RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = "Guarded", Guardian = guardian.DisplayName })
            return
        end
    else
        local lastTime = playerHatchTimes[eggId]
        if lastTime and now - lastTime < egg.Cooldown then
            local secondsLeft = math.ceil(egg.Cooldown - (now - lastTime))
            RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = "Cooldown", SecondsLeft = secondsLeft })
            return
        end
    end

    if PetInventory.isFull(player) then
        RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = "InventoryFull" })
        return
    end

    if guardian and not EggInventory.take(player, eggId) then
        return
    end
    local petId, chance = rollEggPet(egg)
    if not PetInventory.grantPet(player, petId) then
        if guardian then
            EggInventory.grant(player, eggId)
        end
        return
    end

    playerHatchTimes[eggId] = now
    sendInventory(player)
    PlayerData.saveSoon(player)
    RemoteEvents.EggHatchResultEvent:FireClient(player, {
        EggId = eggId,
        PetId = petId,
        ChancePercent = math.round(chance * 1000) / 10,
    })
end

local connectedStands = {}

local function connectEggStand(stand)
    local eggId = stand:GetAttribute("EggId")
    local prompt = stand:FindFirstChildWhichIsA("ProximityPrompt", true)
    if connectedStands[stand] or not (typeof(eggId) == "string" and GameConfig.Eggs[eggId] and prompt) then
        return
    end
    connectedStands[stand] = true

    local eggPart = prompt.Parent
    local maxDistance = PromptRules.maxDistance(prompt)

    prompt.Triggered:Connect(function(player)
        onEggTriggered(player, eggId, eggPart, maxDistance)
    end)
end

handleRequest(RemoteEvents.EquipPetEvent, PetInventory.equip)
handleRequest(RemoteEvents.UnequipPetEvent, PetInventory.unequip)
handleRequest(RemoteEvents.SetAuraPetEvent, PetInventory.setAuraPet)

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastHatchTime[player] = nil
end)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

CollectionService:GetInstanceAddedSignal(GameConfig.EggTag):Connect(connectEggStand)
for _, stand in CollectionService:GetTagged(GameConfig.EggTag) do
    connectEggStand(stand)
end

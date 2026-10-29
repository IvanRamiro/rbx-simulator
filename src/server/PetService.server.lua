
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

-- Extra distance allowed beyond the prompt's range, for network delay
local PROMPT_DISTANCE_TOLERANCE = 6

local random = Random.new()

-- Last successful hatch time of each egg, per player: lastHatchTime[player][eggId]
local lastHatchTime = {}

local function sendInventory(player)
    local snapshot = PetInventory.getSnapshot(player)
    RemoteEvents.PetInventoryUpdatedEvent:FireClient(player, snapshot)

    -- Every client reads this to show the right aura element. It's cosmetic
    -- only and always follows the server's own aura pet selection.
    local auraPetId = nil
    if snapshot and snapshot.AuraPetInstanceId then
        for _, pet in snapshot.Pets do
            if pet.InstanceId == snapshot.AuraPetInstanceId then
                auraPetId = pet.PetId
            end
        end
    end
    player:SetAttribute("AuraPetId", auraPetId)

    -- Every client shows these pets following the player, e.g. "AquaWisp,VoltFox".
    -- Also cosmetic only.
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

-- Waits for saved data first. Only brand-new players get the starter pets.
local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress then
        return
    end

    PetInventory.setupPlayer(player, if isNewPlayer then nil else progress)
    sendInventory(player)
end

-- Clients only send a pet instance ID. PetInventory validates it, and the
-- client is sent a fresh inventory only when something actually changed.
local function handleRequest(remoteEvent, action)
    remoteEvent.OnServerEvent:Connect(function(player, instanceId)
        if action(player, instanceId) then
            sendInventory(player)
        end
    end)
end

-- Pet eggs -------------------------------------------------------------------

-- Picks a pet from an egg's pool using the weights.
-- Returns the pet ID and its chance (0 to 1).
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

    -- Only reached through rounding; fall back to the last entry
    local lastEntry = pool[#pool]
    return lastEntry.PetId, lastEntry.Weight / totalWeight
end

-- Uses the server's own view of the character's position, never a position
-- sent by the client
local function isAliveAndNear(player, part, maxDistance)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 then
        return false
    end

    return (rootPart.Position - part.Position).Magnitude <= maxDistance
end

local function onEggTriggered(player, eggId, eggPart, maxDistance)
    local egg = GameConfig.Eggs[eggId]
    if not egg or player.Parent ~= Players or not isAliveAndNear(player, eggPart, maxDistance) then
        return
    end

    local leaderstats = player:FindFirstChild("leaderstats")
    local rankValue = leaderstats and leaderstats:FindFirstChild("Rank")
    if not (rankValue and Ranks.isAtLeast(rankValue.Value, egg.RequiredRank)) then
        RemoteEvents.EggHatchResultEvent:FireClient(player, {
            EggId = eggId,
            Reason = "Locked",
            RequiredRank = Ranks.getRankById(egg.RequiredRank).Name,
        })
        return
    end

    -- Each egg has its own cooldown
    local now = os.clock()
    local playerHatchTimes = lastHatchTime[player] or {}
    lastHatchTime[player] = playerHatchTimes
    local lastTime = playerHatchTimes[eggId]
    if lastTime and now - lastTime < egg.Cooldown then
        local secondsLeft = math.ceil(egg.Cooldown - (now - lastTime))
        RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = "Cooldown", SecondsLeft = secondsLeft })
        return
    end

    if PetInventory.isFull(player) then
        RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = "InventoryFull" })
        return
    end

    local petId, chance = rollEggPet(egg)
    if not PetInventory.grantPet(player, petId) then
        return
    end

    playerHatchTimes[eggId] = now
    sendInventory(player)
    PlayerData.saveSoon(player)
    RemoteEvents.EggHatchResultEvent:FireClient(player, {
        EggId = eggId,
        PetId = petId,
        ChancePercent = math.round(chance * 1000) / 10, -- e.g. 0.27 -> 27
    })
end

local connectedStands = {}

-- Egg stands are built by IslandService and tagged, so this finds every one,
-- on any island, whenever it's built
local function connectEggStand(stand)
    local eggId = stand:GetAttribute("EggId")
    local prompt = stand:FindFirstChildWhichIsA("ProximityPrompt", true)
    if connectedStands[stand] or not (typeof(eggId) == "string" and GameConfig.Eggs[eggId] and prompt) then
        return
    end
    connectedStands[stand] = true

    local eggPart = prompt.Parent
    local maxDistance = prompt.MaxActivationDistance + PROMPT_DISTANCE_TOLERANCE

    -- Triggered fires on the server, after the player has held the prompt
    prompt.Triggered:Connect(function(player)
        onEggTriggered(player, eggId, eggPart, maxDistance)
    end)
end

handleRequest(RemoteEvents.EquipPetEvent, PetInventory.equip)
handleRequest(RemoteEvents.UnequipPetEvent, PetInventory.unequip)
handleRequest(RemoteEvents.SetAuraPetEvent, PetInventory.setAuraPet)

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    -- Pet data itself is removed by PlayerData, after its final save snapshot
    lastHatchTime[player] = nil
end)

-- Handle players who joined before this script finished loading
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

CollectionService:GetInstanceAddedSignal(GameConfig.EggTag):Connect(connectEggStand)
for _, stand in CollectionService:GetTagged(GameConfig.EggTag) do
    connectEggStand(stand)
end

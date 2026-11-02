local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local PetInventory = {}

local playerData = {}

local function findOwnedPet(data, instanceId)
    for _, pet in data.ownedPets do
        if pet.InstanceId == instanceId then
            return pet
        end
    end

    return nil
end

local function addPet(data, petId)
    table.insert(data.ownedPets, {
        InstanceId = HttpService:GenerateGUID(false),
        PetId = petId,
    })
end

function PetInventory.setupPlayer(player, savedProgress)
    if playerData[player] then
        return
    end

    local data = {
        ownedPets = {},
        equipped = {},
        auraPetInstanceId = nil,
    }
    playerData[player] = data

    if savedProgress then
        for _, pet in savedProgress.Pets do
            table.insert(data.ownedPets, { InstanceId = pet.InstanceId, PetId = pet.PetId })
        end
        data.equipped = table.clone(savedProgress.EquippedPetIds)
        data.auraPetInstanceId = savedProgress.AuraPetInstanceId
        return
    end

    for _, petId in GameConfig.StarterPetIds do
        addPet(data, petId)
    end

    if GameConfig.GrantDevTestPets and RunService:IsStudio() then
        for _, petId in GameConfig.DevTestPetIds do
            addPet(data, petId)
        end
    end
end

function PetInventory.removePlayer(player)
    playerData[player] = nil
end

function PetInventory.isFull(player)
    local data = playerData[player]
    return data == nil or #data.ownedPets >= GameConfig.MaxOwnedPets
end

function PetInventory.grantPet(player, petId)
    if PetInventory.isFull(player) or not GameConfig.Pets[petId] then
        return false
    end

    addPet(playerData[player], petId)
    return true
end

function PetInventory.equip(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return false
    end

    if not findOwnedPet(data, instanceId) then
        return false
    end

    if table.find(data.equipped, instanceId) then
        return false
    end

    if #data.equipped >= GameConfig.MaxEquippedPets then
        return false
    end

    table.insert(data.equipped, instanceId)
    return true
end

function PetInventory.unequip(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return false
    end

    local index = table.find(data.equipped, instanceId)
    if not index then
        return false
    end

    table.remove(data.equipped, index)

    if data.auraPetInstanceId == instanceId then
        data.auraPetInstanceId = nil
    end

    return true
end

-- Takes a pet out of the inventory (unequipping it first); its PetId, or nil when it isn't theirs.
function PetInventory.take(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return nil
    end
    for index, pet in data.ownedPets do
        if pet.InstanceId == instanceId then
            PetInventory.unequip(player, instanceId)
            table.remove(data.ownedPets, index)
            return pet.PetId
        end
    end
    return nil
end

function PetInventory.setAuraPet(player, instanceId)
    local data = playerData[player]
    if not data then
        return false
    end

    if instanceId ~= nil then
        if typeof(instanceId) ~= "string" or not table.find(data.equipped, instanceId) then
            return false
        end
    end

    if data.auraPetInstanceId == instanceId then
        return false
    end

    data.auraPetInstanceId = instanceId
    return true
end

function PetInventory.getQiBonusPercent(player)
    local data = playerData[player]
    if not data then
        return 0
    end

    local totalPercent = 0
    for _, instanceId in data.equipped do
        local pet = findOwnedPet(data, instanceId)
        local definition = pet and GameConfig.Pets[pet.PetId]
        if definition then
            totalPercent += definition.QiBonusPercent
        end
    end

    return totalPercent
end

function PetInventory.exportData(player)
    local data = playerData[player]
    if not data then
        return nil
    end

    local pets = {}
    for _, pet in data.ownedPets do
        table.insert(pets, { InstanceId = pet.InstanceId, PetId = pet.PetId })
    end

    return {
        Pets = pets,
        EquippedPetIds = table.clone(data.equipped),
        AuraPetInstanceId = data.auraPetInstanceId,
    }
end

function PetInventory.getSnapshot(player)
    local data = playerData[player]
    if not data then
        return nil
    end

    local pets = {}
    for _, pet in data.ownedPets do
        table.insert(pets, {
            InstanceId = pet.InstanceId,
            PetId = pet.PetId,
            Equipped = table.find(data.equipped, pet.InstanceId) ~= nil,
        })
    end

    return {
        Pets = pets,
        AuraPetInstanceId = data.auraPetInstanceId,
    }
end

for _, petIds in { GameConfig.StarterPetIds, GameConfig.DevTestPetIds } do
    for _, petId in petIds do
        assert(GameConfig.Pets[petId], "Unknown pet ID in GameConfig: " .. tostring(petId))
    end
end

for petId, definition in GameConfig.Pets do
    assert(GameConfig.PetRarityColors[definition.Rarity], "Pet " .. petId .. " has an unknown Rarity: " .. tostring(definition.Rarity))
end

for eggId, egg in GameConfig.Eggs do
    for _, entry in egg.Pool do
        assert(GameConfig.Pets[entry.PetId], "Unknown pet ID in GameConfig.Eggs." .. eggId .. ".Pool: " .. tostring(entry.PetId))
        assert(entry.Weight > 0, "GameConfig.Eggs." .. eggId .. ".Pool weights must be greater than 0")
    end
end

-- Sends the player their inventory (PetInventoryUpdatedEvent) and sets the attributes every client
-- reads: "AuraPetId" and "EquippedPetIds" (comma-separated PetIds).
function PetInventory.publish(player)
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

return PetInventory

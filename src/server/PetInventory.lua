
-- Server-only record of each player's pets: which they own, which are
-- equipped, and which is their aura pet. PlayerData loads it from and saves
-- it to the DataStore. Instance IDs passed to these functions come straight
-- from client requests, so every function checks them before changing anything.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local PetInventory = {}

-- playerData[player] = {
--     ownedPets = { { InstanceId = "...", PetId = "AquaWisp" }, ... },
--     equipped = { instanceId, ... }, -- at most GameConfig.MaxEquippedPets
--     auraPetInstanceId = instanceId or nil, -- always one of the equipped pets
-- }
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

-- Call once after a player's data has loaded. savedProgress is the validated
-- progress from PlayerData, or nil for a brand-new player, who gets the
-- starter pets instead. Safe to call again: it never grants twice.
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

    -- Extra test pets, only when explicitly turned on and only in Studio
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

-- Gives the player a new copy of a catalogue pet with a new unique instance ID.
-- Only call this with a petId chosen by server code (like the egg hatch roll),
-- never one sent by a client.
function PetInventory.grantPet(player, petId)
    if PetInventory.isFull(player) or not GameConfig.Pets[petId] then
        return false
    end

    addPet(playerData[player], petId)
    return true
end

-- equip, unequip and setAuraPet return true only if something changed

function PetInventory.equip(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return false
    end

    if not findOwnedPet(data, instanceId) then
        return false
    end

    if table.find(data.equipped, instanceId) then
        return false -- Already equipped
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

    -- The aura pet must be equipped, so unequipping it clears the aura pet
    if data.auraPetInstanceId == instanceId then
        data.auraPetInstanceId = nil
    end

    return true
end

-- instanceId must be one of the player's equipped pets, or nil to clear it
function PetInventory.setAuraPet(player, instanceId)
    local data = playerData[player]
    if not data then
        return false
    end

    -- Only owned pets can be equipped, so this also checks ownership
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

-- Total bonus from all equipped pets, e.g. 35 means +35% cultivation Qi
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

-- A copy of the player's pets for saving, or nil if they aren't set up
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

-- A copy of the player's inventory to send to their client
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

-- Catch config mistakes as soon as the game starts
for _, petIds in { GameConfig.StarterPetIds, GameConfig.DevTestPetIds } do
    for _, petId in petIds do
        assert(GameConfig.Pets[petId], "Unknown pet ID in GameConfig: " .. tostring(petId))
    end
end

for petId, definition in GameConfig.Pets do
    assert(GameConfig.PetRarityColors[definition.Rarity], "Pet " .. petId .. " has an unknown Rarity: " .. tostring(definition.Rarity))
end

for _, entry in GameConfig.BeginnerEgg.Pool do
    assert(GameConfig.Pets[entry.PetId], "Unknown pet ID in GameConfig.BeginnerEgg.Pool: " .. tostring(entry.PetId))
    assert(entry.Weight > 0, "GameConfig.BeginnerEgg.Pool weights must be greater than 0")
end

return PetInventory

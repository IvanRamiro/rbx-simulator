local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Codex = require(script.Parent:WaitForChild("Codex"))

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
    local definition = GameConfig.Pets[petId]
    table.insert(data.ownedPets, {
        InstanceId = HttpService:GenerateGUID(false),
        PetId = petId,
        Level = 1,
        Locked = GameConfig.PetFusion.AutoLock[definition.Rarity] == true,
    })
end

function PetInventory.setupPlayer(player, savedProgress)
    if playerData[player] then
        return
    end

    local data = {
        ownedPets = {},
        equipped = {},
    }
    playerData[player] = data
    Codex.setupPlayer(player, savedProgress)

    if savedProgress then
        for _, pet in savedProgress.Pets do
            table.insert(data.ownedPets, {
                InstanceId = pet.InstanceId,
                PetId = pet.PetId,
                Level = PetRules.level(pet),
                Locked = pet.Locked == true,
            })
        end
        data.equipped = table.clone(savedProgress.EquippedPetIds)
    else
        for _, petId in GameConfig.StarterPetIds do
            addPet(data, petId)
        end

        if GameConfig.GrantDevTestPets and RunService:IsStudio() then
            for _, petId in GameConfig.DevTestPetIds do
                addPet(data, petId)
            end
        end
    end

    -- a creator always holds the pets in GameConfig.CreatorPets (one each, if they have none; never past the inventory's cap)
    local creatorPets = GameConfig.CreatorPets
    if creatorPets and table.find(creatorPets.UserIds, player.UserId) then
        for _, petId in creatorPets.PetIds do
            local owned = false
            for _, pet in data.ownedPets do
                if pet.PetId == petId then
                    owned = true
                    break
                end
            end
            if not owned and GameConfig.Pets[petId] and #data.ownedPets < GameConfig.MaxOwnedPets then
                addPet(data, petId)
            end
        end
    end

    -- whatever they hold is in the book, including every pet from before the Codex existed
    for _, pet in data.ownedPets do
        Codex.discover(player, pet.PetId)
    end
end

function PetInventory.isSetUp(player)
    return playerData[player] ~= nil
end

-- Unequips the last-equipped beasts over their limit (PassRules.maxEquipped): once a player is known not to own the slots
-- pass, its extra beasts come off (a save may hold up to PassRules.MostEquipped). True if any did.
function PetInventory.trimEquipped(player)
    local data = playerData[player]
    if not data then
        return false
    end
    local limit = PassRules.maxEquipped(player)
    local changed = false
    while #data.equipped > limit do
        table.remove(data.equipped)
        changed = true
    end
    return changed
end

function PetInventory.removePlayer(player)
    playerData[player] = nil
    Codex.removePlayer(player)
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
    Codex.discover(player, petId)
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

    if #data.equipped >= PassRules.maxEquipped(player) then
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

    return true
end

-- Locks or unlocks a pet: a locked pet can't be sold or fused away.
function PetInventory.toggleLock(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return false
    end
    local pet = findOwnedPet(data, instanceId)
    if not pet then
        return false
    end
    pet.Locked = not pet.Locked
    return true
end

-- One pet's snapshot record ({ InstanceId, PetId, Equipped, Level, Locked }), or nil when it isn't theirs.
function PetInventory.get(player, instanceId)
    local snapshot = PetInventory.getSnapshot(player)
    for _, pet in if snapshot then snapshot.Pets else {} do
        if pet.InstanceId == instanceId then
            return pet
        end
    end
    return nil
end

-- Fuses a spare copy into a pet: returns ok, a message to show, and on success { InstanceId, PetId, Level }.
-- The server picks the copy (PetRules.findMaterial): never a locked or equipped one, and a Secret one only when confirmed.
function PetInventory.fuse(player, targetId, confirmSecret)
    local data = playerData[player]
    local target = PetInventory.get(player, targetId)
    if not (data and target) then
        return false, "That pet isn't yours."
    end
    local material, reason = PetRules.findMaterial(PetInventory.getSnapshot(player).Pets, target)
    if not material then
        return false, PetRules.refusal(reason)
    end
    local definition = GameConfig.Pets[target.PetId]
    if (definition.Rarity == "Secret" or definition.Rarity == "Divine") and confirmSecret ~= true then
        return false, "A " .. definition.Rarity .. " pet needs your confirmation to fuse."
    end
    for index, pet in data.ownedPets do
        if pet.InstanceId == material.InstanceId then
            table.remove(data.ownedPets, index)
            break
        end
    end
    local record = findOwnedPet(data, targetId)
    record.Level = PetRules.level(record) + PetRules.level(material)
    return true, definition.DisplayName .. " reached Level " .. record.Level .. "! +" .. PetRules.qiBonus(record.PetId, record.Level) .. "% Qi",
        { InstanceId = targetId, PetId = record.PetId, Level = record.Level }
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

function PetInventory.getQiBonusPercent(player)
    local data = playerData[player]
    if not data then
        return 0
    end

    local totalPercent = Codex.qiPercent(player)
    for _, instanceId in data.equipped do
        local pet = findOwnedPet(data, instanceId)
        if pet then
            totalPercent += PetRules.qiBonus(pet.PetId, pet.Level)
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
        table.insert(pets, { InstanceId = pet.InstanceId, PetId = pet.PetId, Level = pet.Level, Locked = pet.Locked })
    end

    return {
        Pets = pets,
        EquippedPetIds = table.clone(data.equipped),
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
            Level = pet.Level,
            Locked = pet.Locked,
        })
    end

    return {
        Pets = pets,
        CodexQiPercent = Codex.qiPercent(player),
    }
end

for _, petIds in { GameConfig.StarterPetIds, GameConfig.DevTestPetIds, GameConfig.CreatorPets.PetIds } do
    for _, petId in petIds do
        assert(GameConfig.Pets[petId], "Unknown pet ID in GameConfig: " .. tostring(petId))
    end
end

for petId, definition in GameConfig.Pets do
    assert(GameConfig.PetRarityColors[definition.Rarity], "Pet " .. petId .. " has an unknown Rarity: " .. tostring(definition.Rarity))
end

for eggId, egg in GameConfig.Eggs do
    local total = 0
    for _, entry in egg.Pool do
        assert(GameConfig.Pets[entry.PetId], "Unknown pet ID in GameConfig.Eggs." .. eggId .. ".Pool: " .. tostring(entry.PetId))
        assert(entry.HatchChance > 0, "GameConfig.Eggs." .. eggId .. ".Pool chances must be greater than 0")
        total += entry.HatchChance
    end
    assert(math.abs(total - 100) < 0.001, "GameConfig.Eggs." .. eggId .. ".Pool chances add up to " .. total .. ", not 100")
end

-- Sends the player their inventory (PetInventoryUpdatedEvent) and sets the attributes every client
-- reads: "EquippedPetIds" (comma-separated PetIds).
function PetInventory.publish(player)
    local snapshot = PetInventory.getSnapshot(player)
    RemoteEvents.PetInventoryUpdatedEvent:FireClient(player, snapshot)

    player:SetAttribute("AuraPetId", nil) -- (SET AURA removed, the owner 2026-11-12: clears it for anyone who had one)

    local equippedPetIds = {}
    if snapshot then
        for _, pet in snapshot.Pets do
            if pet.Equipped then
                table.insert(equippedPetIds, pet.PetId)
            end
        end
    end
    player:SetAttribute("EquippedPetIds", table.concat(equippedPetIds, ","))

    local owned = {}
    for _, pet in if snapshot then snapshot.Pets else {} do
        local entry = owned[pet.PetId] or { Count = 0, Level = 1 }
        entry.Count += 1
        entry.Level = math.max(entry.Level, PetRules.level(pet))
        owned[pet.PetId] = entry
    end
    Codex.publish(player, owned)
end

return PetInventory

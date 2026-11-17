-- Each player's pets on the server: their owned pets (InstanceId, PetId, Size, Mutation, Level, Locked), which are equipped and which
-- stand in their pen, and the Qi bonus they give. Loaded from and exported to PlayerData; published to the client as attributes
-- and PetInventoryUpdatedEvent.
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Codex = require(script.Parent:WaitForChild("Codex"))

local PetInventory = {}

local playerData = {}

-- The beast pen (PenService, shared/PenLayout): each player has one, of a level (1 to PenLayout.Max) that sets how many of their pets
-- it holds; the pets in it are an ordered list of InstanceIds. A pet in the pen is never equipped (equipping takes it out), and selling
-- it takes it out; fusing never spends one (PetRules.findMaterial).
PetInventory.onPublish = nil -- set by PenService: called with the player after each publish, to show their pen's beasts

local function findOwnedPet(data, instanceId)
    for _, pet in data.ownedPets do
        if pet.InstanceId == instanceId then
            return pet
        end
    end

    return nil
end

-- Whether a pet of this rarity, size and mutation arrives locked (so a quick tap can never sell or fuse it away): the rarities in
-- GameConfig.PetFusion.AutoLock, any Colossal, and the grand mutations (Rainbow and up: PetRules.Mutations' Grand).
function PetInventory.hatchesLocked(rarity, size, mutation)
    return GameConfig.PetFusion.AutoLock[rarity] == true or PetRules.size(size) == "Colossal"
        or PetRules.mutationInfo(mutation).Grand == true
end

local function penIndex(data, instanceId)
    return table.find(data.pen, instanceId)
end

-- `paid`: it came from Robux (a paid egg: EggInventory), so it is a paid item wherever it goes (Paid, save schema 24; the Auction
-- House keeps it from players whose region doesn't allow trading paid items). It stays paid through fusing, the pen and auctions.
-- `mutation`: its hatch mutation (PetRules.Mutations; nil: none), saved as Mutation (save schema 26).
local function addPet(data, petId, size, paid, mutation)
    local definition = GameConfig.Pets[petId]
    local instanceId = HttpService:GenerateGUID(false)
    table.insert(data.ownedPets, {
        InstanceId = instanceId,
        PetId = petId,
        Level = 1,
        Locked = PetInventory.hatchesLocked(definition.Rarity, size, mutation),
        Size = PetRules.size(size),
        Mutation = PetRules.mutation(mutation),
        Worth = PetRules.copyValue(size, mutation),
        Paid = if paid == true then true else nil,
    })
    return instanceId
end

function PetInventory.setupPlayer(player, savedProgress)
    if playerData[player] then
        return
    end

    local data = {
        ownedPets = {},
        equipped = {},
        pen = {},
        penLevel = 1,
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
                Size = PetRules.size(pet),
                Mutation = PetRules.mutation(pet),
                Worth = PetRules.worth(pet),
                Paid = if pet.Paid == true then true else nil,
            })
        end
        data.equipped = table.clone(savedProgress.EquippedPetIds)
        -- (PlayerData's sanitize already kept only owned, unequipped pets, once each, up to the level's capacity; checked again here)
        local level = tonumber(savedProgress.PenLevel)
        data.penLevel = if level and level == level then math.clamp(math.floor(level), 1, PenLayout.Max) else 1
        for _, instanceId in if typeof(savedProgress.Pen) == "table" then savedProgress.Pen else {} do
            if #data.pen < PenLayout.capacity(data.penLevel) and typeof(instanceId) == "string" and findOwnedPet(data, instanceId)
                and not table.find(data.equipped, instanceId) and not penIndex(data, instanceId) then
                table.insert(data.pen, instanceId)
            end
        end
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
        Codex.discover(player, pet.PetId, pet.Mutation)
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

-- Gives a new pet (size: its hatch size; nil, a bought or given pet: Normal; paid: it came from Robux; mutation: its hatch mutation,
-- nil for none). True and its InstanceId, or false when full.
function PetInventory.grantPet(player, petId, size, paid, mutation)
    if PetInventory.isFull(player) or not GameConfig.Pets[petId] then
        return false
    end

    local instanceId = addPet(playerData[player], petId, size, paid, mutation)
    Codex.discover(player, petId, PetRules.mutation(mutation))
    return true, instanceId
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

    local inPen = penIndex(data, instanceId)
    if inPen then -- equipping a penned pet takes it out of the pen
        table.remove(data.pen, inPen)
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

-- Puts one of the player's pets in their pen (add = true) or takes it out (add = false). Returns true, or false and why: "NotYours",
-- "Equipped", "Full", "Already", "NotIn".
function PetInventory.setInPen(player, instanceId, add)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" or not findOwnedPet(data, instanceId) then
        return false, "NotYours"
    end
    local at = penIndex(data, instanceId)
    if not add then
        if not at then
            return false, "NotIn"
        end
        table.remove(data.pen, at)
        return true
    end
    if at then
        return false, "Already"
    end
    if table.find(data.equipped, instanceId) then
        return false, "Equipped"
    end
    if #data.pen >= PenLayout.capacity(data.penLevel) then
        return false, "Full"
    end
    table.insert(data.pen, instanceId)
    return true
end

function PetInventory.penLevel(player)
    local data = playerData[player]
    return if data then data.penLevel else nil
end

-- Raises the pen one level (PenService has charged for it). True if it rose.
function PetInventory.raisePen(player, fromLevel)
    local data = playerData[player]
    if not data or data.penLevel ~= fromLevel or data.penLevel >= PenLayout.Max then
        return false
    end
    data.penLevel += 1
    return true
end

-- The pen's beasts, in order, as { PetId, Size, Level, Mutation }.
function PetInventory.penPets(player)
    local data = playerData[player]
    if not data then
        return nil
    end
    local shown = {}
    for _, instanceId in data.pen do
        local pet = findOwnedPet(data, instanceId)
        if pet then
            table.insert(shown, { PetId = pet.PetId, Size = PetRules.size(pet), Level = PetRules.level(pet), Mutation = PetRules.mutation(pet) })
        end
    end
    return shown
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

-- One pet's snapshot record ({ InstanceId, PetId, Equipped, Level, Locked, Size, Worth, InPen }), or nil when it isn't theirs.
function PetInventory.get(player, instanceId)
    local snapshot = PetInventory.getSnapshot(player)
    for _, pet in if snapshot then snapshot.Pets else {} do
        if pet.InstanceId == instanceId then
            return pet
        end
    end
    return nil
end

-- Fuses a spare copy into a pet: returns ok, a message to show, and on success { InstanceId, PetId, Level, Size, Mutation, Grew,
-- Mutated }. The fused pet keeps the larger size of the two (a Giant copy is never lost by fusing it) and the rarer mutation (a
-- Void copy is never lost either), and nothing else about it changes.
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
    local materialPen = penIndex(data, material.InstanceId) -- (never one: findMaterial passes over penned pets; kept tidy anyway)
    if materialPen then
        table.remove(data.pen, materialPen)
    end
    local record = findOwnedPet(data, targetId)
    record.Worth = PetRules.worth(record) + PetRules.worth(material) -- (each copy keeps what it was worth: fusing makes no stones)
    if material.Paid then
        record.Paid = true -- (a paid copy fused in makes the whole pet a paid item: it can never wash the mark off)
    end
    record.Level = PetRules.level(record) + PetRules.level(material)
    local size = PetRules.bigger(record.Size, material.Size)
    local grew = size ~= PetRules.size(record.Size)
    record.Size = size
    local mutation = PetRules.better(record.Mutation, material.Mutation)
    local mutated = mutation ~= PetRules.mutation(record.Mutation)
    record.Mutation = mutation
    local qi = PetRules.qiBonus(record.PetId, record.Level, record.Size, record.Mutation)
    local became = {}
    if grew then
        table.insert(became, size)
    end
    if mutated then
        table.insert(became, mutation)
    end
    return true, definition.DisplayName .. " reached Level " .. record.Level .. (if #became > 0 then " and became " .. table.concat(became, " ") else "")
        .. "! +" .. qi .. "% Qi",
        { InstanceId = targetId, PetId = record.PetId, Level = record.Level, Size = record.Size, Mutation = record.Mutation, Grew = grew,
            Mutated = mutated }
end

-- Takes a pet out of the inventory (unequipping it and emptying its pen first); its PetId, or nil when it isn't theirs.
function PetInventory.take(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return nil
    end
    for index, pet in data.ownedPets do
        if pet.InstanceId == instanceId then
            PetInventory.unequip(player, instanceId)
            local inPen = penIndex(data, instanceId)
            if inPen then
                table.remove(data.pen, inPen)
            end
            table.remove(data.ownedPets, index)
            return pet.PetId
        end
    end
    return nil
end

-- The Auction House (server/Auction): takes a free pet out whole, its full record ({ InstanceId, PetId, Level, Locked, Size, Mutation,
-- Worth, Paid }),
-- or nil when it isn't theirs or isn't free (locked, equipped or in the pen: the player frees it first).
function PetInventory.takeRecord(player, instanceId)
    local data = playerData[player]
    if not data or typeof(instanceId) ~= "string" then
        return nil
    end
    for index, pet in data.ownedPets do
        if pet.InstanceId == instanceId then
            if pet.Locked or table.find(data.equipped, instanceId) or penIndex(data, instanceId) then
                return nil
            end
            table.remove(data.ownedPets, index)
            return { InstanceId = pet.InstanceId, PetId = pet.PetId, Level = pet.Level, Locked = false, Size = pet.Size,
                Mutation = pet.Mutation, Worth = pet.Worth, Paid = pet.Paid }
        end
    end
    return nil
end

-- Puts a pet record back or gives one won at the Auction House: its level, size, mutation and worth kept (a new InstanceId if the
-- player somehow holds that one already). A rarity that hatches locked arrives locked. True, or false when the inventory is full,
-- or when the record holds a size or mutation this server doesn't know (newer content, from a newer server during a release's
-- rollout): it waits, in the mailbox, for a server that knows it, rather than arriving stripped.
function PetInventory.restore(player, record)
    local data = playerData[player]
    if not data or typeof(record) ~= "table" or not GameConfig.Pets[record.PetId] or #data.ownedPets >= GameConfig.MaxOwnedPets then
        return false
    end
    if (typeof(record.Size) == "string" and not PetRules.Sizes[record.Size])
        or (typeof(record.Mutation) == "string" and not PetRules.Mutations[record.Mutation]) then
        return false
    end
    local instanceId = record.InstanceId
    if typeof(instanceId) ~= "string" or instanceId == "" or #instanceId > 64 or findOwnedPet(data, instanceId) then
        instanceId = HttpService:GenerateGUID(false)
    end
    local rarity = GameConfig.Pets[record.PetId].Rarity
    local pet = { InstanceId = instanceId, PetId = record.PetId, Level = PetRules.level(record), Size = PetRules.size(record),
        Mutation = PetRules.mutation(record), Locked = PetInventory.hatchesLocked(rarity, record.Size, record.Mutation),
        Paid = if record.Paid == true then true else nil }
    pet.Worth = PetRules.worth({ Level = pet.Level, Size = pet.Size, Mutation = pet.Mutation, Worth = record.Worth })
    table.insert(data.ownedPets, pet)
    Codex.discover(player, record.PetId, pet.Mutation)
    return true
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
            totalPercent += PetRules.qiBonus(pet.PetId, pet.Level, pet.Size, pet.Mutation)
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
        table.insert(pets, { InstanceId = pet.InstanceId, PetId = pet.PetId, Level = pet.Level, Locked = pet.Locked, Size = pet.Size,
            Mutation = pet.Mutation, Worth = pet.Worth, Paid = pet.Paid })
    end

    return {
        Pets = pets,
        EquippedPetIds = table.clone(data.equipped),
        Pen = table.clone(data.pen),
        PenLevel = data.penLevel,
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
            Size = pet.Size,
            Mutation = pet.Mutation,
            Worth = pet.Worth,
            InPen = penIndex(data, pet.InstanceId) ~= nil,
            Paid = pet.Paid == true,
        })
    end

    return {
        Pets = pets,
        Pen = table.clone(data.pen),
        PenLevel = data.penLevel,
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
-- reads: "EquippedPetIds" (comma-separated PetIds) and "EquippedPets" (the same pets as "PetId:Size" or "PetId:Size:Mutation", in
-- the same order: what PetCompanionController builds, so every client shows each pet at its size, with its mutation's look).
function PetInventory.publish(player)
    local snapshot = PetInventory.getSnapshot(player)
    RemoteEvents.PetInventoryUpdatedEvent:FireClient(player, snapshot)

    player:SetAttribute("AuraPetId", nil) -- (SET AURA removed, the owner 2026-11-12: clears it for anyone who had one)

    local equippedPetIds, equippedPets = {}, {}
    local data = playerData[player]
    if data then
        for _, instanceId in data.equipped do -- (in the order equipped: each keeps its follow slot)
            local pet = findOwnedPet(data, instanceId)
            if pet then
                table.insert(equippedPetIds, pet.PetId)
                local mutation = PetRules.mutation(pet)
                table.insert(equippedPets, pet.PetId .. ":" .. PetRules.size(pet) .. (if mutation then ":" .. mutation else ""))
            end
        end
    end
    player:SetAttribute("EquippedPets", table.concat(equippedPets, ","))
    player:SetAttribute("EquippedPetIds", table.concat(equippedPetIds, ","))

    local owned = {}
    for _, pet in if snapshot then snapshot.Pets else {} do
        local entry = owned[pet.PetId] or { Count = 0, Level = 1 }
        entry.Count += 1
        entry.Level = math.max(entry.Level, PetRules.level(pet))
        owned[pet.PetId] = entry
    end
    Codex.publish(player, owned)
    if PetInventory.onPublish then
        PetInventory.onPublish(player)
    end
end

return PetInventory

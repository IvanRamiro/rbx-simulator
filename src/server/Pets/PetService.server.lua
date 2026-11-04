local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local EggInventory = require(script.Parent:WaitForChild("EggInventory"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PromptRules = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("PromptRules"))
local EggModel = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("EggModel"))

local random = Random.new()
local REQUEST_COOLDOWN = 0.2 -- seconds between a player's equip/unequip/aura requests

local lastRequest = {}

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress then
        return
    end

    PetInventory.setupPlayer(player, if isNewPlayer then nil else progress)
    EggInventory.setupPlayer(player, if isNewPlayer then nil else progress)
    PetInventory.publish(player)
end

-- Each accepted request rebuilds the player's aura and pets on every client, so they are throttled.
local function handleRequest(remoteEvent, action)
    remoteEvent.OnServerEvent:Connect(function(player, instanceId)
        local now = os.clock()
        if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
            return
        end
        lastRequest[player] = now
        if action(player, instanceId) then
            PetInventory.publish(player)
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

-- ---------- hatching, at the Hatching Altar ----------
-- Eggs are carried home from the guardians' stands (Guardian.lua) into the egg inventory and hatched
-- here, at Yggdrasil's Hatching Altar (WorldBuilder.buildAltar): its prompt opens the hatching
-- window on the client, which asks for one egg at a time (HatchEggEvent). Each hatch is staged:
-- the egg is laid in the altar's cradle for everyone to see, and taken away when it breaks open.
local HATCH_STAGE = GameConfig.HatchingAltar.Stage -- seconds the egg rests in the cradle before it breaks
local hatching = {}     -- [player] = true while their egg is in the cradle

-- The altar (FloatingIslands.<HatchingAltar.Island>.HatchingAltar), its prompt's part and prompt.
local function altarParts()
    local folder = workspace:FindFirstChild("FloatingIslands")
    local island = folder and folder:FindFirstChild(GameConfig.HatchingAltar.Island)
    local altar = island and island:FindFirstChild("HatchingAltar")
    local promptPart = altar and altar:FindFirstChild("Prompt")
    local prompt = promptPart and promptPart:FindFirstChildWhichIsA("ProximityPrompt")
    return altar, promptPart, prompt
end

local function stageEgg(altar, eggId)
    local cradle = altar:FindFirstChild("Cradle")
    if not cradle then
        return nil
    end
    local model = EggModel.build(eggId, 3.6)
    model.Name = "HatchingEgg"
    model.ModelStreamingMode = Enum.ModelStreamingMode.Persistent -- it rides in the remote: it must be there
    model:PivotTo(cradle.CFrame * CFrame.new(0, 1.8, 0))
    model.PrimaryPart.Anchored = true
    model.Parent = altar
    task.delay(HATCH_STAGE + 0.4, function()
        model:Destroy()
    end)
    return model
end

local function onHatchRequest(player, eggId)
    local egg = typeof(eggId) == "string" and GameConfig.Eggs[eggId]
    local altar, promptPart, prompt = altarParts()
    if not egg or hatching[player] or player.Parent ~= Players or not promptPart
        or not PromptRules.isAliveAndNear(player, promptPart, PromptRules.maxDistance(prompt)) then
        return
    end
    if EggInventory.count(player, eggId) < 1 then
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
    if PetInventory.isFull(player) then
        RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = "InventoryFull" })
        return
    end
    if not EggInventory.take(player, eggId) then
        return
    end
    local petId, chance = rollEggPet(egg)
    if not PetInventory.grantPet(player, petId) then
        EggInventory.grant(player, eggId)
        return
    end
    hatching[player] = true
    task.delay(HATCH_STAGE, function()
        hatching[player] = nil
    end)
    PetInventory.publish(player)
    PlayerData.saveSoon(player)
    Analytics.event(player, "EggHatched", 1, eggId, petId)
    RemoteEvents.EggHatchResultEvent:FireClient(player, {
        EggId = eggId,
        PetId = petId,
        ChancePercent = math.round(chance * 1000) / 10,
        Staged = stageEgg(altar, eggId),
        BreakAt = workspace:GetServerTimeNow() + HATCH_STAGE, -- server time: the client breaks it on time, however late this arrives
    })
end

RemoteEvents.HatchEggEvent.OnServerEvent:Connect(onHatchRequest)

handleRequest(RemoteEvents.EquipPetEvent, PetInventory.equip)
handleRequest(RemoteEvents.UnequipPetEvent, PetInventory.unequip)
handleRequest(RemoteEvents.SetAuraPetEvent, PetInventory.setAuraPet)

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    hatching[player] = nil
end)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end


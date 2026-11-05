local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local Codex = require(script.Parent:WaitForChild("Codex"))
local EggInventory = require(script.Parent:WaitForChild("EggInventory"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local Wallet = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Wallet"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PromptRules = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("PromptRules"))
local EggModel = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("EggModel"))

local random = Random.new()
local REQUEST_COOLDOWN = 0.5 -- seconds between a player's equip/unequip/aura requests: each rebuilds models on every client

local lastRequest = {}
local lastHatchRequest = {}
local HATCH_REQUEST_COOLDOWN = 0.25

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
    local now = os.clock()
    if now - (lastHatchRequest[player] or -1) < HATCH_REQUEST_COOLDOWN then
        return
    end
    lastHatchRequest[player] = now
    local egg = typeof(eggId) == "string" and GameConfig.Eggs[eggId]
    local altar, promptPart, prompt = altarParts()
    if not egg or player.Parent ~= Players or not promptPart then
        return
    end
    -- every refusal is answered: the player has pressed Hatch and is waiting to see an egg
    local function refuse(reason)
        RemoteEvents.EggHatchResultEvent:FireClient(player, { EggId = eggId, Reason = reason })
    end
    if hatching[player] then
        refuse("HatchBusy")
        return
    end
    if not PromptRules.isAliveAndNear(player, promptPart, PromptRules.maxDistance(prompt)) then
        refuse("NotAtAltar")
        return
    end
    if EggInventory.count(player, eggId) < 1 then
        refuse("NoEgg")
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
    local isNew = not Codex.isFound(player, petId)
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
        IsNew = isNew,
        Staged = stageEgg(altar, eggId),
        BreakAt = workspace:GetServerTimeNow() + HATCH_STAGE, -- server time: the client breaks it on time, however late this arrives
    })
end

RemoteEvents.HatchEggEvent.OnServerEvent:Connect(onHatchRequest)

handleRequest(RemoteEvents.EquipPetEvent, PetInventory.equip)
handleRequest(RemoteEvents.UnequipPetEvent, PetInventory.unequip)
handleRequest(RemoteEvents.SetAuraPetEvent, PetInventory.setAuraPet)

-- ---------- duplicates and the Codex ----------
-- Each changes what's saved, so an accepted one saves soon. Every reply is sent after the new inventory, so the window has redrawn by then.
local function throttled(player)
    local now = os.clock()
    if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
        return true
    end
    lastRequest[player] = now
    return false
end

RemoteEvents.TogglePetLockEvent.OnServerEvent:Connect(function(player, instanceId)
    if not throttled(player) and PetInventory.toggleLock(player, instanceId) then
        PetInventory.publish(player)
        PlayerData.saveSoon(player)
    end
end)

RemoteEvents.FusePetEvent.OnServerEvent:Connect(function(player, instanceId, confirmSecret)
    if throttled(player) then
        return
    end
    local ok, message, fused = PetInventory.fuse(player, instanceId, confirmSecret)
    if ok then
        PetInventory.publish(player)
        PlayerData.saveSoon(player)
        Analytics.event(player, "PetFused", fused.Level, fused.PetId)
    end
    RemoteEvents.PetActionResultEvent:FireClient(player, ok, message, fused)
end)

RemoteEvents.CodexEvent.OnServerEvent:Connect(function(player, action, rewardId)
    if action ~= "Claim" or throttled(player) or Wallet.balance(player) == nil then
        return
    end
    local reward = Codex.claim(player, rewardId)
    if not reward then
        return
    end
    local stones = CodexRules.stones(reward, Shop.playerRealmIndex(player))
    Wallet.add(player, stones, "Codex", reward.Id)
    PetInventory.publish(player) -- its Qi bonus shows in the pets window, the claim in the Codex
    PlayerData.saveSoon(player)
    Analytics.event(player, "CodexReward", stones, reward.Id)
    RemoteEvents.CodexEvent:FireClient(player, "Claimed", { Id = reward.Id, Stones = stones, QiPercent = reward.QiPercent })
end)

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    lastHatchRequest[player] = nil
    hatching[player] = nil
end)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end


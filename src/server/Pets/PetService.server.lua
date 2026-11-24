-- The pet remotes: equip, unequip, lock and fuse requests, hatching an egg at the Hatching Altar (the roll, staged on its
-- cradle), and the Codex's reward claims. Everything is checked here; PetInventory holds the pets.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local TitleRules = require(ReplicatedStorage:WaitForChild("TitleRules"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Codex = require(script.Parent:WaitForChild("Codex"))
local EggInventory = require(script.Parent:WaitForChild("EggInventory"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local Wallet = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Wallet"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PromptRules = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("PromptRules"))
local EggModel = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("EggModel"))
local RecordBook = require(script.Parent.Parent:WaitForChild("Records"):WaitForChild("RecordBook"))
local GoalBook = require(script.Parent.Parent:WaitForChild("Rewards"):WaitForChild("GoalBook"))

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

-- A pet from the egg's pool, by its HatchChance (percents that add up to 100, PetInventory checks) with the player's luck
-- (the Luck pass: PassRules.luckyPool), and that chance. An Exclusive egg takes no luck: its odds are the ones shown when it was bought.
local function rollEggPet(egg, player)
    local pool = if egg.Exclusive then egg.Pool else PassRules.luckyPool(egg.Pool, PassRules.luck(player))
    local roll = random:NextNumber() * 100
    for _, entry in pool do
        if roll < entry.HatchChance then
            return entry.PetId, entry.HatchChance
        end
        roll -= entry.HatchChance
    end

    local lastEntry = pool[#pool]
    return lastEntry.PetId, lastEntry.HatchChance
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

-- (its attributes let everyone else near hear it break: HatcheryController)
local function stageEgg(altar, eggId, player, petId, size, mutation)
    local cradle = altar:FindFirstChild("Cradle")
    if not cradle then
        return nil
    end
    -- the pet is already granted: a missing egg mesh must not stop the result reaching the client
    local ok, model = pcall(EggModel.build, eggId, 3.6)
    if not ok then
        warn("PetService: couldn't stage the egg: " .. tostring(model))
        return nil
    end
    model.Name = "HatchingEgg"
    model.ModelStreamingMode = Enum.ModelStreamingMode.Persistent -- it rides in the remote: it must be there
    model:PivotTo(cradle.CFrame * CFrame.new(0, 1.8, 0))
    model.PrimaryPart.Anchored = true
    local pet = GameConfig.Pets[petId]
    model:SetAttribute("HatcherId", player.UserId)
    model:SetAttribute("BreakAt", workspace:GetServerTimeNow() + HATCH_STAGE)
    model:SetAttribute("Rarity", pet and pet.Rarity or "Common")
    model:SetAttribute("Size", size) -- (a Colossal or a grand mutation is told to the whole server too: HatcheryController)
    model:SetAttribute("Mutation", mutation)
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
    if not egg or player.Parent ~= Players or not promptPart or not prompt then
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
    if (player:GetAttribute("PurchaseSaving") or 0) > 0 then
        refuse("PurchaseSaving") -- (a purchase is being saved: ProductService; the egg they bought must not be used before the save holds it)
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
    local took, paidEgg = EggInventory.take(player, eggId) -- (a paid egg first while any is held: EggInventory)
    if not took then
        return
    end
    local petId, chance = rollEggPet(egg, player)
    -- its size, rolled apart from the beast at PetRules.Sizes' chances (no luck: the Luck pass changes which beast, not its size)
    local size = PetRules.rollSize(random)
    -- and its mutation, a third roll apart from both (PetRules.Mutations; nil for most). The Luck pass makes the Grand ones likelier
    -- (PetRules.mutationChance); an Exclusive egg takes no luck, as with its beasts
    local mutation = PetRules.rollMutation(random, if egg.Exclusive then 1 else PassRules.luck(player), TitleRules.multiplier(player, "Mutation"))
    local isNew = not Codex.isFound(player, petId)
    -- a pet from a paid egg (the Exclusive Egg, or an egg won on a bought spin) is a paid item for good (PetInventory: Paid)
    if not PetInventory.grantPet(player, petId, size, paidEgg or egg.Exclusive == true, mutation) then
        EggInventory.grant(player, eggId, paidEgg)
        return
    end
    hatching[player] = true
    task.delay(HATCH_STAGE, function()
        hatching[player] = nil
    end)
    PetInventory.publish(player)
    PlayerData.saveSoon(player)
    Analytics.event(player, "EggHatched", 1, eggId, petId)
    GoalBook.count(player, "Hatch", 1)
    if size ~= "Normal" then
        Analytics.event(player, "PetSizeHatched", 1, size, petId)
    end
    if mutation then
        Analytics.event(player, "PetMutationHatched", 1, mutation, petId)
    end
    RecordBook.hatched(player, eggId, petId, size, mutation) -- (the Hall of Records: the rarest hatches, the firsts, the Chronicle)
    RemoteEvents.EggHatchResultEvent:FireClient(player, {
        EggId = eggId,
        PetId = petId,
        ChancePercent = chance,
        Size = size,
        Mutation = mutation,
        IsNew = isNew,
        Staged = stageEgg(altar, eggId, player, petId, size, mutation),
        BreakAt = workspace:GetServerTimeNow() + HATCH_STAGE, -- server time: the client breaks it on time, however late this arrives
    })
end

RemoteEvents.HatchEggEvent.OnServerEvent:Connect(onHatchRequest)

handleRequest(RemoteEvents.EquipPetEvent, PetInventory.equip)
handleRequest(RemoteEvents.UnequipPetEvent, PetInventory.unequip)
-- EQUIP BEST takes no argument (a client can't name pets: the server picks them), and is throttled like every request that rebuilds pets
RemoteEvents.EquipBestPetsEvent.OnServerEvent:Connect(function(player)
    local now = os.clock()
    if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
        return
    end
    lastRequest[player] = now
    if PetInventory.equipBest(player) then
        PetInventory.publish(player)
    end
end)

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
    -- (the wallet must be set up, or the claim would be marked and its stones lost)
    if action ~= "Claim" or throttled(player) or Wallet.exportData(player) == nil then
        return
    end
    local reward, realm = Codex.claim(player, rewardId)
    if not reward then
        return
    end
    local stones = CodexRules.stones(reward, realm) -- (the realm it was earned in: Codex.lua)
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


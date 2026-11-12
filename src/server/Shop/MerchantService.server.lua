-- The Wandering Merchant (GameConfig.WanderingMerchant, shared/Merchant.lua): in Yggdrasil for the first 10 minutes of
-- every UTC hour, the same in every server, with 3 or 4 deals that change each visit.
--
-- When he arrives, ServerStorage.WanderingMerchant (a Model built at edit time, already standing at his camp: Placements/
-- Yggdrasil.lua's Merchant) is copied into FloatingIslands.Yggdrasil; its ProximityPrompt gets the attribute Merchant = true.
-- When he leaves the copy is removed. Without the template he still keeps his hours, his deals and this remote (it warns
-- once); in Studio a plain stand takes his place, so he can be tested before the model exists.
--
-- Workspace attributes every client reads: MerchantOpen (bool), MerchantLeavesAt (while open) and MerchantArrivesAt (the
-- next visit), in unix seconds. Everyone is told when he arrives and LeaveWarning seconds before he leaves.
--
-- MerchantEvent, server to client:
--   "Open", state                    his prompt was triggered: the window opens
--   "Result", ok, message, state     the answer to a purchase
--   "Announce", text                 a notice for everyone (or for a player who joins while he is here)
-- client to server:
--   "Buy", dealId                    one of this visit's deals, once a visit, within REACH of his prompt
-- state = { Deals = { { Id, Kind, ItemId, Name, Count, Price, FullPrice, Rarity, Locked = why or nil, Bought } },
--           Stones, LeavesAt }
--
-- Studio: with ServerStorage's MerchantTest attribute set to true he is always here (with the usual deals of the hour).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Merchant = require(ReplicatedStorage:WaitForChild("Merchant"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local serverRoot = script.Parent.Parent
local PlayerData = require(serverRoot:WaitForChild("Data"):WaitForChild("PlayerData"))
local EggInventory = require(serverRoot:WaitForChild("Pets"):WaitForChild("EggInventory"))
local PetInventory = require(serverRoot:WaitForChild("Pets"):WaitForChild("PetInventory"))
local MovementGuard = require(serverRoot:WaitForChild("Security"):WaitForChild("MovementGuard"))
local WorldConfig = require(serverRoot:WaitForChild("World"):WaitForChild("WorldConfig"))
local MerchantLedger = require(script.Parent:WaitForChild("MerchantLedger"))
local Wallet = require(script.Parent:WaitForChild("Wallet"))

local CONFIG = GameConfig.WanderingMerchant
local REACH = 45 -- studs from his prompt, as the shops (ShopService)
local REQUEST_COOLDOWN = 0.25
local TEMPLATE_NAME = "WanderingMerchant"

local MerchantEvent = RemoteEvents.MerchantEvent

local ready = {}
local lastRequest = {}

local current = { visit = nil, model = nil, prompt = nil, warned = false }
local warnedMissing, warnedNoPrompt = false, false

local function testing()
    return RunService:IsStudio() and ServerStorage:GetAttribute("MerchantTest") == true
end

local function isOpen(now)
    return Merchant.isOpen(now) or testing()
end

-- when this visit ends; held over by MerchantTest, he stays until the hour's deals change
local function leavesAt(now)
    return if testing() then Merchant.nextArrival(now) else Merchant.leavesAt(now)
end

local function minutes(seconds)
    local count = math.max(1, math.ceil(seconds / 60))
    return count .. (if count == 1 then " minute" else " minutes")
end

-- ---------- his camp ----------
local function hub()
    local islands = workspace:FindFirstChild(WorldConfig.FolderName)
    return islands and islands:FindFirstChild(WorldConfig.StartIsland)
end

local function findPrompt(model)
    for _, descendant in model:GetDescendants() do
        if descendant:IsA("ProximityPrompt") then
            return descendant
        end
    end
    return nil
end

local function promptPosition(prompt)
    local parent = prompt and prompt.Parent
    if parent and parent:IsA("BasePart") then
        return parent.Position
    elseif parent and parent:IsA("Attachment") then
        return parent.WorldPosition
    end
    return nil
end

-- Studio only, while the template is missing: a plain stand at his camp, so his window can be tried
local function placeholder()
    local placements = ServerStorage:FindFirstChild("WorldBuild")
    placements = placements and placements:FindFirstChild("Placements")
    placements = placements and placements:FindFirstChild(WorldConfig.StartIsland)
    local ok, data = pcall(require, placements)
    local camp = ok and typeof(data) == "table" and data.Merchant
    local island = WorldConfig.Islands[WorldConfig.StartIsland]
    if not (camp and island) then
        return nil
    end
    local model = Instance.new("Model")
    local stand = Instance.new("Part")
    stand.Name = "Stand"
    stand.Anchored = true
    stand.Size = Vector3.new(4, 6, 4)
    stand.Material = Enum.Material.Marble
    stand.Color = Color3.fromRGB(225, 235, 250)
    stand.CFrame = CFrame.new(island.Centre + camp.Centre + Vector3.new(0, 3, 0)) * CFrame.Angles(0, camp.Yaw or 0, 0)
    stand.Parent = model
    local prompt = Instance.new("ProximityPrompt")
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.Parent = stand
    model.PrimaryPart = stand
    return model
end

local function state(player)
    local now = os.time()
    local visit = Merchant.visitIndex(now)
    local rankName = Ranks.getPlayerRankName(player)
    local deals = {}
    for _, deal in Merchant.dealsFor(visit) do
        local locked = nil
        if not Ranks.isAtLeast(rankName, deal.RequiredRank) then
            locked = "Needs " .. Ranks.getRankById(deal.RequiredRank).Name
        elseif deal.Kind == "Egg" and EggInventory.count(player, deal.ItemId) + deal.Count > EggInventory.MAX_PER_EGG then
            locked = "No room for " .. deal.Count .. " more"
        elseif deal.Kind == "Pet" and PetInventory.isFull(player) then
            locked = "Your pets are full"
        end
        table.insert(deals, {
            Id = deal.Id, Kind = deal.Kind, ItemId = deal.ItemId, Name = deal.Name, Count = deal.Count, Price = deal.Price,
            FullPrice = deal.FullPrice, Rarity = deal.Rarity, Locked = locked,
            Bought = MerchantLedger.hasBought(player, visit, deal.Id),
        })
    end
    return { Deals = deals, Stones = Wallet.balance(player), LeavesAt = leavesAt(now) }
end

local function onTriggered(player)
    if ready[player] and current.visit then
        MerchantEvent:FireClient(player, "Open", state(player))
    end
end

local function spawnCamp()
    local island = hub()
    local template = ServerStorage:FindFirstChild(TEMPLATE_NAME)
    if not (template and template:IsA("Model")) and not warnedMissing then
        warnedMissing = true
        warn("MerchantService: ServerStorage." .. TEMPLATE_NAME .. " (a Model) is missing: the Wandering Merchant keeps his hours"
            .. " and deals, but has no model" .. (if RunService:IsStudio() then " (a plain stand stands in, in Studio)" else ""))
    end
    if not island then
        return
    end
    local model = if template and template:IsA("Model") then template:Clone()
        elseif RunService:IsStudio() then placeholder()
        else nil
    if not model then
        return
    end
    model.Name = TEMPLATE_NAME
    local prompt = findPrompt(model)
    if prompt then
        prompt:SetAttribute("Merchant", true)
        if prompt.ObjectText == "" then
            prompt.ObjectText = "Wandering Merchant"
        end
        if prompt.ActionText == "" or prompt.ActionText == "Interact" then
            prompt.ActionText = "Trade"
        end
        prompt.Triggered:Connect(onTriggered)
    elseif not warnedNoPrompt then
        warnedNoPrompt = true
        warn("MerchantService: " .. TEMPLATE_NAME .. " has no ProximityPrompt: nobody can open his wares")
    end
    model.Parent = island
    current.model, current.prompt = model, prompt
end

local function nearMerchant(player)
    local spot = promptPosition(current.prompt)
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return spot ~= nil and root ~= nil and current.prompt:IsDescendantOf(workspace) and not MovementGuard.isSuspect(player)
        and (root.Position - spot).Magnitude <= REACH
end

-- ---------- his hours ----------
local function arrive(visit, now)
    current.visit = visit
    spawnCamp()
    local leaves = leavesAt(now)
    workspace:SetAttribute("MerchantOpen", true)
    workspace:SetAttribute("MerchantLeavesAt", leaves)
    workspace:SetAttribute("MerchantArrivesAt", Merchant.nextArrival(now))
    current.warned = leaves - now <= CONFIG.LeaveWarning -- (a server that starts in his last minute: the arrival says it)
    MerchantEvent:FireAllClients("Announce", "The Wandering Merchant has arrived at " .. WorldConfig.StartIsland .. "! Leaves in "
        .. minutes(leaves - now) .. ".")
end

local function depart(now)
    if current.model then
        current.model:Destroy()
    end
    current.visit, current.model, current.prompt = nil, nil, nil
    workspace:SetAttribute("MerchantOpen", false)
    workspace:SetAttribute("MerchantLeavesAt", nil)
    workspace:SetAttribute("MerchantArrivesAt", Merchant.nextArrival(now))
end

local function tick()
    local now = os.time()
    local open = isOpen(now)
    local visit = Merchant.visitIndex(now)
    if current.visit and (not open or current.visit ~= visit) then
        depart(now)
    end
    if open and not current.visit then
        arrive(visit, now)
    end
    if current.visit then
        local leaves = leavesAt(now)
        workspace:SetAttribute("MerchantLeavesAt", leaves) -- (MerchantTest, set or cleared while he is here, moves it)
        if not current.warned and leaves - now <= CONFIG.LeaveWarning then
            current.warned = true
            MerchantEvent:FireAllClients("Announce", "The Wandering Merchant leaves in " .. minutes(leaves - now) .. ".")
        end
    end
end

workspace:SetAttribute("MerchantOpen", false)
workspace:SetAttribute("MerchantArrivesAt", Merchant.nextArrival(os.time()))
task.spawn(function()
    while true do
        local ok, err = pcall(tick)
        if not ok then
            warn("MerchantService: " .. tostring(err))
        end
        task.wait(1)
    end
end)

-- ---------- buying ----------
local function buy(player, dealId)
    local now = os.time()
    if not (isOpen(now) and current.visit) then
        return false, "The Wandering Merchant has moved on. He returns at the top of the hour."
    end
    local visit = Merchant.visitIndex(now)
    local deal = Merchant.deal(dealId)
    if not (deal and Merchant.isOffered(visit, deal.Id)) then
        return false, "He isn't selling that this visit."
    end
    if not nearMerchant(player) then
        return false, "Walk up to the Wandering Merchant to trade."
    end
    if MerchantLedger.hasBought(player, visit, deal.Id) then
        return false, "You've bought that deal already. He brings new wares every visit."
    end
    if not Ranks.isAtLeast(Ranks.getPlayerRankName(player), deal.RequiredRank) then
        return false, "That deal needs " .. Ranks.getRankById(deal.RequiredRank).Name .. "."
    end
    if deal.Kind == "Egg" and EggInventory.count(player, deal.ItemId) + deal.Count > EggInventory.MAX_PER_EGG then
        return false, "You can't hold " .. deal.Count .. " more of that egg."
    end
    if deal.Kind == "Pet" and PetInventory.isFull(player) then
        return false, "Your pet inventory is full (" .. GameConfig.MaxOwnedPets .. " pets). Fuse or sell your spares."
    end
    if not Wallet.spend(player, deal.Price, "Merchant", deal.Id) then
        return false, "You need " .. NumberFormat.compact(deal.Price) .. " Spirit Stones."
    end
    if deal.Kind == "Egg" then
        local granted = 0
        for _ = 1, deal.Count do
            if not EggInventory.grant(player, deal.ItemId) then
                break
            end
            granted += 1
        end
        if granted < deal.Count then
            for _ = 1, granted do
                EggInventory.take(player, deal.ItemId)
            end
            Wallet.add(player, deal.Price, "MerchantRefund", deal.Id)
            return false, "You can't hold " .. deal.Count .. " more of that egg."
        end
    else
        if not PetInventory.grantPet(player, deal.ItemId) then
            Wallet.add(player, deal.Price, "MerchantRefund", deal.Id)
            return false, "Your pet inventory is full (" .. GameConfig.MaxOwnedPets .. " pets). Fuse or sell your spares."
        end
        PetInventory.publish(player)
    end
    MerchantLedger.markBought(player, visit, deal.Id)
    if deal.Kind == "Egg" then
        local eggs = if deal.Count == 1 then "a " .. deal.Name else deal.Count .. " " .. deal.Name .. "s"
        return true, "Bought " .. eggs .. ". Hatch " .. (if deal.Count == 1 then "it" else "them") .. " at the Hatching Sanctum."
    end
    return true, "The " .. deal.Name .. " is yours! Find it in your Pets window."
end

MerchantEvent.OnServerEvent:Connect(function(player, action, dealId)
    if action ~= "Buy" or not ready[player] then
        return
    end
    local now = os.clock()
    if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
        return
    end
    lastRequest[player] = now
    local ok, message = buy(player, dealId)
    if ok then
        PlayerData.saveSoon(player)
    end
    MerchantEvent:FireClient(player, "Result", ok, message, state(player))
end)

-- ---------- players ----------
local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    MerchantLedger.setupPlayer(player, if isNewPlayer then nil else progress)
    ready[player] = true
    if current.visit then
        MerchantEvent:FireClient(player, "Announce", "The Wandering Merchant is at " .. WorldConfig.StartIsland .. "! Leaves in "
            .. minutes(leavesAt(os.time()) - os.time()) .. ".")
    end
end

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    ready[player] = nil
    lastRequest[player] = nil
end)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

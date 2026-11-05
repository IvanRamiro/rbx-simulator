-- The Blacksmith, Buy & Sell and the Marketplace on Yggdrasil. Each shop's building carries a
-- ProximityPrompt with a "Shop" attribute ("Blacksmith", "BuySell" or "Marketplace") on its "Prompt" part,
-- at the Blacksmith's anvil, the foot of the Jade Scale and the money tree's plinth
-- (WorldBuilder.buildShops); triggering it sends the player
-- ShopEvent("Open", shop, snapshot). The client then asks with
-- ShopEvent(action, id):
--   "Buy" weaponId            at the Blacksmith: a weapon of the player's realm or below (Shop.lua)
--   "Forge" instanceId, { Element, Name }
--                             at the Blacksmith: gives an owned weapon an unlocked element (Elements) and
--                             a name (run through Roblox's text filter), for Shop.forgePrice
--   "Equip" instanceId        anywhere: an owned weapon, or nil for the Qi Palm
--   "SellPet" instanceId, { ConfirmSecret }
--                             at Buy & Sell, for Shop.petValue: never a locked or equipped pet, and a Secret one only when confirmed
--   "SellSpares"              at Buy & Sell: every duplicate PetRules.spares names
--   "SellWeapon" instanceId   at Buy & Sell, for Shop.weaponRefund (never the equipped one)
--   "BuyEgg" eggId            at the Marketplace: an egg the player's rank can carry, for Shop.marketEggPrice
-- and is answered ShopEvent("Result", ok, message, snapshot). Buying and selling need the player
-- within REACH of that shop's prompt, and every request is throttled.
--
-- Also sets up each player's Spirit Stones (Wallet), weapons (WeaponInventory) and forge elements
-- (Elements) once their data has loaded.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextService = game:GetService("TextService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("PetInventory"))
local EggInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("EggInventory"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))
local Elements = require(script.Parent:WaitForChild("Elements"))
local Wallet = require(script.Parent:WaitForChild("Wallet"))
local Quests = require(script.Parent.Parent:WaitForChild("Quests"):WaitForChild("Quests"))
local WeaponInventory = require(script.Parent:WaitForChild("WeaponInventory"))

local REACH = 45 -- studs from a shop's prompt
local REQUEST_COOLDOWN = 0.25
local FORGE_COOLDOWN = 2 -- seconds between name checks: they use Roblox's filter, which has a quota
local SHOPS = { Blacksmith = true, BuySell = true, Marketplace = true }

local lastRequest = {}
local lastForge = {}
local MovementGuard = require(script.Parent.Parent:WaitForChild("Security"):WaitForChild("MovementGuard"))
local ready = {}

local function snapshot(player)
    local pets = PetInventory.getSnapshot(player)
    local eggs = {}
    for eggId in GameConfig.Eggs do
        eggs[eggId] = EggInventory.count(player, eggId)
    end
    return {
        Eggs = eggs,
        Stones = Wallet.balance(player),
        Weapons = WeaponInventory.snapshot(player),
        Elements = Elements.list(player),
        Pets = pets and pets.Pets or {},
    }
end

local function nearShop(player, shop)
    local spot = workspace:FindFirstChild(WorldConfig.FolderName)
    spot = spot and spot:FindFirstChild(WorldConfig.StartIsland)
    spot = spot and spot:FindFirstChild("Shops")
    spot = spot and spot:FindFirstChild(shop)
    spot = spot and spot:FindFirstChild("Prompt")
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return spot ~= nil and root ~= nil and not MovementGuard.isSuspect(player) and (root.Position - spot.Position).Magnitude <= REACH
end

-- How a message names a weapon: by the name its owner forged it with, or as "the <its name>".
local MAX_RAW_NAME = 200 -- bytes a forged name may arrive with, before it's tidied

local function nameOf(record)
    local weapon = Shop.weapon(record.WeaponId)
    return record.Name or ("the " .. (weapon and weapon.Name or "weapon"))
end

-- A forged weapon's name, tidied and filtered; or nil and why not.
local function filterName(player, raw)
    -- the length first: stripping a huge run of spaces is slow enough to stall the server
    if typeof(raw) ~= "string" or #raw > MAX_RAW_NAME then
        return nil, "Name your weapon first."
    end
    local name = string.gsub(string.gsub(string.gsub(raw, "^%s+", ""), "%s+$", ""), "%s+", " ")
    local length = utf8.len(name)
    local limits = GameConfig.Forge.NameLength
    if not length or length < limits.Min or length > limits.Max then
        return nil, ("A name of %d to %d letters, please."):format(limits.Min, limits.Max)
    end
    local ok, filtered = pcall(function()
        return TextService:FilterStringAsync(name, player.UserId, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
    end)
    if not ok then
        return nil, "Names can't be checked right now: try again soon."
    end
    if filtered ~= name then
        return nil, "That name can't be used."
    end
    return name
end

local actions = {}

function actions.Buy(player, weaponId)
    local weapon = Shop.weapon(weaponId)
    if not weapon then
        return false, "There's no such weapon."
    end
    if not nearShop(player, "Blacksmith") then
        return false, "Visit the Blacksmith to buy weapons."
    end
    if weapon.Tier > Shop.playerRealmIndex(player) then
        return false, weapon.Name .. " needs the " .. weapon.Realm .. "."
    end
    if WeaponInventory.owns(player, weapon.Id) then
        return false, "You already own the " .. weapon.Name .. "."
    end
    if WeaponInventory.isFull(player) then
        return false, "Your weapon rack is full: sell one first."
    end
    if not Wallet.spend(player, weapon.Price, "BuyWeapon", weapon.Id) then
        return false, "You need " .. weapon.Price .. " Spirit Stones."
    end
    WeaponInventory.equip(player, WeaponInventory.grant(player, weapon.Id))
    Quests.Moment:Fire(player, "BuyWeapon")
    return true, "Forged the " .. weapon.Name .. "!"
end

function actions.Equip(player, instanceId)
    if instanceId ~= nil and typeof(instanceId) ~= "string" then
        return false, "That isn't yours."
    end
    if not WeaponInventory.equip(player, instanceId) then
        return false, "That isn't yours."
    end
    local record = instanceId and WeaponInventory.get(player, instanceId)
    return true, if record then "Wielding " .. nameOf(record) .. "." else "Fighting with the Qi Palm."
end

local forging = {} -- [player] = true while their name is being checked (it yields)

function actions.Forge(player, instanceId, spec)
    if forging[player] then
        return false, "The forge is already at work."
    end
    if not nearShop(player, "Blacksmith") then
        return false, "Visit the Blacksmith's forge."
    end
    local record = typeof(instanceId) == "string" and WeaponInventory.get(player, instanceId)
    if not record then
        return false, "That weapon isn't yours."
    end
    local element = typeof(spec) == "table" and spec.Element
    local info = Shop.element(element)
    if not info then
        return false, "Choose an element."
    end
    if not Elements.has(player, element) then
        return false, "Find " .. info.Source .. " to forge with " .. info.DisplayName .. "."
    end
    local price = Shop.forgePrice(record.WeaponId)
    if Wallet.balance(player) < price then
        return false, "You need " .. price .. " Spirit Stones."
    end
    if os.clock() - (lastForge[player] or -FORGE_COOLDOWN) < FORGE_COOLDOWN then
        return false, "The forge is still cooling. Try again in a moment."
    end
    lastForge[player] = os.clock()
    forging[player] = true
    local name, why = filterName(player, spec.Name)
    forging[player] = nil
    if not name then
        return false, why
    end
    -- the name check yields, so the weapon and the stones are checked again before charging
    if not WeaponInventory.get(player, instanceId) then
        return false, "That weapon isn't yours."
    end
    if not Wallet.spend(player, price, "Forge", element) then
        return false, "You need " .. price .. " Spirit Stones."
    end
    WeaponInventory.forge(player, instanceId, element, name)
    return true, "Forged " .. name .. ", a " .. info.DisplayName .. " " .. Shop.weapon(record.WeaponId).Name .. "!"
end

function actions.SellPet(player, instanceId, extra)
    if not nearShop(player, "BuySell") then
        return false, "Visit Buy & Sell to sell pets."
    end
    local pets = PetInventory.exportData(player)
    if pets and #pets.Pets <= 1 then
        return false, "You can't sell your last companion."
    end
    local pet = PetInventory.get(player, instanceId)
    if not pet then
        return false, "That pet isn't yours."
    end
    if pet.Locked then
        return false, "That pet is locked: unlock it in your Pets window first."
    end
    if pet.Equipped then
        return false, "Unequip that pet before selling it."
    end
    local definition = GameConfig.Pets[pet.PetId]
    if definition.Rarity == "Secret" and not (typeof(extra) == "table" and extra.ConfirmSecret == true) then
        return false, "A Secret pet needs your confirmation to sell."
    end
    PetInventory.take(player, instanceId)
    local value = Shop.petValue(pet.PetId, PetRules.level(pet))
    Wallet.add(player, value, "SellPet", pet.PetId)
    PetInventory.publish(player)
    return true, "Sold the " .. definition.DisplayName .. " for " .. value .. " Spirit Stones."
end

function actions.SellSpares(player)
    if not nearShop(player, "BuySell") then
        return false, "Visit Buy & Sell to sell pets."
    end
    local snapshot = PetInventory.getSnapshot(player)
    local spares = if snapshot then PetRules.spares(snapshot.Pets) else {}
    if #spares == 0 then
        return false, "You have no spare pets to sell."
    end
    local total = 0
    for _, pet in spares do
        PetInventory.take(player, pet.InstanceId)
        total += Shop.petValue(pet.PetId, PetRules.level(pet))
    end
    Wallet.add(player, total, "SellPet", "Spares")
    PetInventory.publish(player)
    return true, "Sold " .. #spares .. " spare " .. (if #spares == 1 then "pet" else "pets") .. " for " .. total .. " Spirit Stones."
end

function actions.SellWeapon(player, instanceId)
    if not nearShop(player, "BuySell") then
        return false, "Visit Buy & Sell to sell weapons."
    end
    local record = WeaponInventory.take(player, instanceId)
    if not record then
        return false, "Put the weapon down before selling it."
    end
    local value = Shop.weaponRefund(record.WeaponId, record.Element)
    Wallet.add(player, value, "SellWeapon", record.WeaponId)
    return true, "Sold " .. nameOf(record) .. " for " .. value .. " Spirit Stones."
end

function actions.BuyEgg(player, eggId)
    local egg = typeof(eggId) == "string" and GameConfig.Eggs[eggId]
    if not egg then
        return false, "That egg isn't for sale."
    end
    if not nearShop(player, "Marketplace") then
        return false, "You're too far from the Marketplace."
    end
    if not Ranks.isAtLeast(Ranks.getPlayerRankName(player), egg.RequiredRank) then
        return false, "That egg needs " .. Ranks.getRankById(egg.RequiredRank).Name .. "."
    end
    if EggInventory.count(player, eggId) >= EggInventory.MAX_PER_EGG then
        return false, "You can't hold any more of that egg."
    end
    local price = Shop.marketEggPrice(eggId)
    if not Wallet.spend(player, price, "BuyEgg", eggId) then
        return false, "You need " .. price .. " Spirit Stones."
    end
    if not EggInventory.grant(player, eggId) then
        Wallet.add(player, price, "BuyEggRefund", eggId)
        return false, "You can't hold any more of that egg."
    end
    return true, "Bought a " .. egg.DisplayName .. ". Hatch it at the Hatching Altar."
end

RemoteEvents.ShopEvent.OnServerEvent:Connect(function(player, action, id, extra)
    local handler = typeof(action) == "string" and actions[action]
    if not (handler and ready[player]) then
        return
    end
    local now = os.clock()
    if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
        return
    end
    lastRequest[player] = now
    local ok, message = handler(player, id, extra)
    if ok then
        PlayerData.saveSoon(player)
    end
    RemoteEvents.ShopEvent:FireClient(player, "Result", ok, message, snapshot(player))
end)

-- The shops' prompts (WorldBuilder.buildShops).
local function watchPrompt(prompt)
    if prompt:IsA("ProximityPrompt") and SHOPS[prompt:GetAttribute("Shop")] then
        prompt.Triggered:Connect(function(player)
            if ready[player] then
                RemoteEvents.ShopEvent:FireClient(player, "Open", prompt:GetAttribute("Shop"), snapshot(player))
            end
        end)
    end
end
task.spawn(function()
    local island = workspace:WaitForChild(WorldConfig.FolderName):WaitForChild(WorldConfig.StartIsland)
    local shops = island:WaitForChild("Shops", 30)
    if not shops then
        warn("ShopService: " .. WorldConfig.StartIsland .. " has no Shops (WorldBuilder.buildShops)")
        return
    end
    shops.DescendantAdded:Connect(watchPrompt)
    for _, descendant in shops:GetDescendants() do
        watchPrompt(descendant)
    end
end)

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    Wallet.setupPlayer(player, if isNewPlayer then nil else progress)
    WeaponInventory.setupPlayer(player, if isNewPlayer then nil else progress)
    Elements.setupPlayer(player, if isNewPlayer then nil else progress)
    ready[player] = true
end

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    lastForge[player] = nil
    forging[player] = nil
    ready[player] = nil
end)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

-- The Blacksmith and Buy & Sell on Yggdrasil. Each shop's plot has a notice board carrying a
-- ProximityPrompt with a "Shop" attribute ("Blacksmith" or "BuySell", WorldBuilder.buildPlots);
-- triggering it sends the player ShopEvent("Open", shop, snapshot). The client then asks with
-- ShopEvent(action, id):
--   "Buy" weaponId            at the Blacksmith: a weapon of the player's realm or below (Shop.lua)
--   "Equip" instanceId        anywhere: an owned weapon, or nil for the Qi Palm
--   "SellPet" instanceId      at Buy & Sell, for Shop.petValue
--   "SellWeapon" instanceId   at Buy & Sell, for Shop.weaponRefund (never the equipped one)
-- and is answered ShopEvent("Result", ok, message, snapshot). Buying and selling need the player
-- within REACH of that shop's plot, and every request is throttled.
--
-- Also sets up each player's Spirit Stones (Wallet) and weapons (WeaponInventory) once their data
-- has loaded.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("PetInventory"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))
local Wallet = require(script.Parent:WaitForChild("Wallet"))
local WeaponInventory = require(script.Parent:WaitForChild("WeaponInventory"))

local REACH = 45 -- studs from a shop's plot centre
local REQUEST_COOLDOWN = 0.25
local SHOPS = { Blacksmith = "Plot_Blacksmith", BuySell = "Plot_BuySell" }

local lastRequest = {}
local ready = {}

local function snapshot(player)
    local pets = PetInventory.getSnapshot(player)
    return {
        Stones = Wallet.balance(player),
        Weapons = WeaponInventory.snapshot(player),
        Pets = pets and pets.Pets or {},
    }
end

local function nearShop(player, shop)
    local plots = workspace:FindFirstChild(WorldConfig.FolderName)
    plots = plots and plots:FindFirstChild(WorldConfig.StartIsland)
    plots = plots and plots:FindFirstChild("Plots")
    local area = plots and plots:FindFirstChild(SHOPS[shop])
    area = area and area:FindFirstChild("Area")
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return area ~= nil and root ~= nil and (root.Position - area.Position).Magnitude <= REACH
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
    if not Wallet.spend(player, weapon.Price) then
        return false, "You need " .. weapon.Price .. " Spirit Stones."
    end
    WeaponInventory.equip(player, WeaponInventory.grant(player, weapon.Id))
    return true, "Forged the " .. weapon.Name .. "!"
end

function actions.Equip(player, instanceId)
    if instanceId ~= nil and typeof(instanceId) ~= "string" then
        return false, "That isn't yours."
    end
    if not WeaponInventory.equip(player, instanceId) then
        return false, "That isn't yours."
    end
    local weapon = WeaponInventory.equipped(player)
    return true, if weapon then "Wielding the " .. weapon.Name .. "." else "Fighting with the Qi Palm."
end

function actions.SellPet(player, instanceId)
    if not nearShop(player, "BuySell") then
        return false, "Visit Buy & Sell to sell pets."
    end
    local petId = PetInventory.take(player, instanceId)
    if not petId then
        return false, "That pet isn't yours."
    end
    local value = Shop.petValue(petId)
    Wallet.add(player, value)
    PetInventory.publish(player)
    return true, "Sold the " .. GameConfig.Pets[petId].DisplayName .. " for " .. value .. " Spirit Stones."
end

function actions.SellWeapon(player, instanceId)
    if not nearShop(player, "BuySell") then
        return false, "Visit Buy & Sell to sell weapons."
    end
    local weaponId = WeaponInventory.take(player, instanceId)
    if not weaponId then
        return false, "Put the weapon down before selling it."
    end
    local value = Shop.weaponRefund(weaponId)
    Wallet.add(player, value)
    return true, "Sold the " .. Shop.weapon(weaponId).Name .. " for " .. value .. " Spirit Stones."
end

RemoteEvents.ShopEvent.OnServerEvent:Connect(function(player, action, id)
    local handler = typeof(action) == "string" and actions[action]
    if not (handler and ready[player]) then
        return
    end
    local now = os.clock()
    if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
        return
    end
    lastRequest[player] = now
    local ok, message = handler(player, id)
    if ok then
        PlayerData.saveSoon(player)
    end
    RemoteEvents.ShopEvent:FireClient(player, "Result", ok, message, snapshot(player))
end)

-- The shops' prompts (WorldBuilder.buildPlots puts them on the notice boards).
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
    local plots = island:WaitForChild("Plots", 30)
    if not plots then
        warn("ShopService: " .. WorldConfig.StartIsland .. " has no Plots (WorldBuilder.buildPlots)")
        return
    end
    plots.DescendantAdded:Connect(watchPrompt)
    for _, descendant in plots:GetDescendants() do
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
    ready[player] = true
end

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    ready[player] = nil
end)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

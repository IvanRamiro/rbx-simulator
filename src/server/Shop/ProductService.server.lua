-- Robux purchases of developer products: the game's one MarketplaceService.ProcessReceipt handler.
--
-- Each product in PRODUCTS gives its item and returns a way to take it back. A purchase is confirmed to Roblox
-- (PurchaseGranted) only once the save holding it is written (PlayerData.saveConfirmed); if the save fails, the item is taken
-- back and Roblox is told NotProcessedYet, so it offers the purchase again. Receipts keeps every PurchaseId given, so a purchase
-- offered again (in this server or another) is never given twice. A player who isn't here, or whose data isn't ready, is
-- answered NotProcessedYet: Roblox offers it again when they next join.
--
-- The Exclusive Egg (GameConfig.ExclusiveEgg, the owner 2026-11-13: 149 Robux): one egg into the player's eggs, hatched at the
-- Hatching Altar like any other. Its odds are shown before the purchase (the Shop); where paid random items are restricted
-- the Shop never offers it (PolicyService), and a purchase that arrives anyway is still given: it was paid for.
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local EggInventory = require(Server:WaitForChild("Pets"):WaitForChild("EggInventory"))
local Receipts = require(script.Parent:WaitForChild("Receipts"))

local READY_WAIT = 30 -- seconds a purchase waits for the buyer's data to load

-- [productId] = function(player): true and an undo function, or false (not given: offered again later)
local PRODUCTS = {}

local exclusive = GameConfig.ExclusiveEgg
if (exclusive.ProductId or 0) > 0 then
    PRODUCTS[exclusive.ProductId] = function(player)
        if not EggInventory.grant(player, exclusive.EggId) then
            return false -- (holding the most of it: given once they have hatched some)
        end
        return true, function()
            EggInventory.take(player, exclusive.EggId)
        end
    end
end

local function ready(player)
    return Receipts.isSetUp(player) and EggInventory.exportData(player) ~= nil
end

local function processReceipt(info)
    local give = PRODUCTS[info.ProductId]
    if not give then
        warn("ProductService: no product " .. tostring(info.ProductId))
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    local player = Players:GetPlayerByUserId(info.PlayerId)
    if not player then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    local deadline = os.clock() + READY_WAIT
    while player.Parent == Players and not ready(player) and os.clock() < deadline do
        task.wait(0.5)
    end
    if player.Parent ~= Players or not ready(player) or not PlayerData.canSave(player) then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    local purchaseId = tostring(info.PurchaseId)
    if Receipts.has(player, purchaseId) then
        return Enum.ProductPurchaseDecision.PurchaseGranted -- given before; Roblox hadn't heard
    end

    local ok, undo = give(player)
    if not ok then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    Receipts.add(player, purchaseId)
    if not PlayerData.saveConfirmed(player) then
        undo()
        Receipts.remove(player, purchaseId)
        warn("ProductService: couldn't save purchase " .. purchaseId .. " for " .. player.Name .. "; Roblox will offer it again")
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    Analytics.event(player, "ProductBought", 1, tostring(info.ProductId), tostring(info.CurrencySpent))
    return Enum.ProductPurchaseDecision.PurchaseGranted
end

MarketplaceService.ProcessReceipt = processReceipt

-- the purchases each player has been given, from their save
local function onPlayerAdded(player)
    local progress = PlayerData.waitForData(player) -- (nil when the load failed: then nothing is saved, so nothing is given)
    if player.Parent == Players then
        Receipts.setupPlayer(player, progress)
    end
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
    task.spawn(onPlayerAdded, player)
end

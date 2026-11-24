-- Robux purchases of developer products: the game's one MarketplaceService.ProcessReceipt handler.
--
-- Each product in PRODUCTS gives its item and returns a way to take it back. A purchase is confirmed to Roblox
-- (PurchaseGranted) only once the save holding it is written (PlayerData.saveConfirmed); if the save fails, the item is taken
-- back and Roblox is told NotProcessedYet, so it offers the purchase again. Receipts keeps every PurchaseId given, so a purchase
-- offered again (in this server or another) is never given twice; one offered again while its save is still being written is
-- answered NotProcessedYet, so it is never confirmed before the save holds it. A player who isn't here, or whose data isn't ready, is
-- answered NotProcessedYet: Roblox offers it again when they next join.
--
-- The Exclusive Egg (GameConfig.ExclusiveEgg, the owner 2026-11-13: 149 Robux): one egg into the player's eggs, hatched at the
-- Hatching Altar like any other. Its odds are shown before the purchase (the Shop); where paid random items are restricted
-- the Shop never offers it (PolicyService), and a purchase that arrives anyway is still given: it was paid for.
--
-- Spin Wheel spins (GameConfig.SpinWheel.SpinProducts, the owner 2026-11-16: 1 for 5 Robux, 5 for 20): added to the player's
-- bought spins (SpinLedger), which never run out. A paid spin is a paid random item, so the same rules as the egg: the wheel
-- shows every prize's chance beside the buttons, offers none where paid random items are restricted, and still gives a
-- purchase that arrives anyway. The buyer is told ("Bought" on SpinEvent) once it is saved.
--
-- Timed Qi boosts (GameConfig.TimedBoost.Products): minutes of 2x Qi added to the player's boost (QiBoost); told on BoostEvent.
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local EggInventory = require(Server:WaitForChild("Pets"):WaitForChild("EggInventory"))
local SpinLedger = require(Server:WaitForChild("Rewards"):WaitForChild("SpinLedger"))
local Receipts = require(script.Parent:WaitForChild("Receipts"))
local QiBoost = require(script.Parent:WaitForChild("QiBoost"))

local READY_WAIT = 30 -- seconds a purchase waits for the buyer's data to load

-- [productId] = function(player): true and an undo function, or false (not given: offered again later)
local PRODUCTS = {}

local exclusive = GameConfig.ExclusiveEgg
if (exclusive.ProductId or 0) > 0 then
    PRODUCTS[exclusive.ProductId] = function(player)
        if not EggInventory.grant(player, exclusive.EggId, true) then -- (a paid egg: bought with Robux)
            return false -- (holding the most of it: given once they have hatched some)
        end
        return true, function()
            EggInventory.revoke(player, exclusive.EggId, true)
        end
    end
end

-- [productId] = function(player): run once the purchase is saved (a word to the buyer)
local AFTER = {}

for _, product in GameConfig.SpinWheel.SpinProducts do
    if (product.ProductId or 0) > 0 then
        PRODUCTS[product.ProductId] = function(player)
            if not SpinLedger.addBought(player, product.Spins) then
                return false -- (holding the most bought spins: given once they have used some)
            end
            return true, function()
                SpinLedger.addBought(player, -product.Spins)
            end
        end
        AFTER[product.ProductId] = function(player)
            RemoteEvents.SpinEvent:FireClient(player, "Bought", { Spins = product.Spins })
        end
    end
end

-- Timed Qi boosts (GameConfig.TimedBoost.Products, the owner 2026-11-16: "a consumable multiplier like 2x qi multiplier per 5 mins"):
-- minutes added to the player's boost (QiBoost), which runs while they play. Not random, so no PolicyService rule. Over MaxMinutes
-- banked the purchase waits (NotProcessedYet) until the boost has run down enough; the Shop doesn't offer one that won't fit.
for _, product in GameConfig.TimedBoost.Products do
    if (product.ProductId or 0) > 0 then
        PRODUCTS[product.ProductId] = function(player)
            if not QiBoost.add(player, product.Minutes) then
                return false
            end
            return true, function()
                QiBoost.add(player, -product.Minutes)
            end
        end
        AFTER[product.ProductId] = function(player)
            RemoteEvents.BoostEvent:FireClient(player, "Bought", product.Minutes)
        end
    end
end

-- [PurchaseId] = true while its grant waits on the save: Roblox may offer the same purchase again meanwhile, and that offer must
-- neither give it twice nor answer PurchaseGranted before the save is known to hold it
local inFlight = {}

local function ready(player)
    return Receipts.isSetUp(player) and EggInventory.exportData(player) ~= nil and SpinLedger.isSetUp(player) and QiBoost.isSetUp(player)
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
    if inFlight[purchaseId] then
        return Enum.ProductPurchaseDecision.NotProcessedYet -- (offered again once that save is done: then Receipts has it)
    end
    if Receipts.has(player, purchaseId) then
        return Enum.ProductPurchaseDecision.PurchaseGranted -- given before; Roblox hadn't heard
    end

    local ok, undo = give(player)
    if not ok then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    Receipts.add(player, purchaseId)
    inFlight[purchaseId] = true
    -- while the save is awaited (up to 20 s) the buyer can neither hatch nor spin what they bought: if the save failed the undo below could take back
    -- nothing they had already used, and Roblox would offer the purchase again: a free copy (bug audit, 2026-11-24). PurchaseSaving counts the
    -- purchases being saved; it is cleared whatever happens.
    player:SetAttribute("PurchaseSaving", (player:GetAttribute("PurchaseSaving") or 0) + 1)
    local savedOk, saved = pcall(PlayerData.saveConfirmed, player)
    saved = savedOk and saved
    if player.Parent == Players then
        player:SetAttribute("PurchaseSaving", math.max((player:GetAttribute("PurchaseSaving") or 1) - 1, 0))
    end
    inFlight[purchaseId] = nil
    if not saved then
        undo()
        Receipts.remove(player, purchaseId)
        warn("ProductService: couldn't save purchase " .. purchaseId .. " for " .. player.Name .. "; Roblox will offer it again")
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    Analytics.event(player, "ProductBought", 1, tostring(info.ProductId), tostring(info.CurrencySpent))
    if AFTER[info.ProductId] then
        AFTER[info.ProductId](player)
    end
    return Enum.ProductPurchaseDecision.PurchaseGranted
end

MarketplaceService.ProcessReceipt = processReceipt

-- the purchases each player has been given, and their timed boost's time left, from their save
local function onPlayerAdded(player)
    local progress, isNewPlayer = PlayerData.waitForData(player) -- (nil when the load failed: then nothing is saved, so nothing is given)
    if player.Parent == Players then
        Receipts.setupPlayer(player, progress)
        QiBoost.setupPlayer(player, if isNewPlayer then nil else progress)
    end
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
    task.spawn(onPlayerAdded, player)
end

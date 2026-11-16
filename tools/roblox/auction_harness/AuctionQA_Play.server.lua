-- QA TEMP (Studio Play only, never in src): drives the Auction House's Play pass. Commands through workspace attribute
-- "AuctionQA"; answers in "AuctionQAOut".
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local RS = game:GetService("ReplicatedStorage")
local SSS = game:GetService("ServerScriptService")
if not RunService:IsStudio() then
    return
end
local PetInventory = require(SSS.Pets.PetInventory)
local Wallet = require(SSS.Shop.Wallet)
local PlayerData = require(SSS.Data.PlayerData)
local AuctionCore = require(SSS.Auction.AuctionCore)
local AuctionStores = require(SSS.Auction.AuctionStores)
local AuctionRules = require(RS.AuctionRules)
local GameConfig = require(RS.GameConfig)

local core = AuctionCore.new({
    now = os.time, guid = function()
        return HttpService:GenerateGUID(false)
    end,
    listings = AuctionStores.listings, mail = AuctionStores.mail, index = AuctionStores.index, notify = AuctionStores.notify,
    rules = { minBid = AuctionRules.minBid, saleTax = AuctionRules.saleTax }, config = GameConfig.AuctionHouse,
})

local function fake(userId, name, stones, items)
    local mem = { stones = stones, items = items or {} }
    local p = { userId = userId, name = name, paidOk = true, pending = {}, mem = mem,
        ledger = { Out = {}, Bids = {}, Claimed = {}, Mine = {}, Watch = {} } }
    function p.takeItem(_, id)
        for i, item in mem.items do
            if item.InstanceId == id then
                return table.remove(mem.items, i)
            end
        end
        return nil
    end
    function p.restoreItem(_, item)
        table.insert(mem.items, item)
        return true
    end
    function p.spend(n)
        if mem.stones < n then
            return false
        end
        mem.stones -= n
        return true
    end
    function p.add(n)
        mem.stones += n
    end
    function p.saveConfirmed()
        return true
    end
    function p.saveSoon() end
    return p
end

local fakeSeller = fake(-424242, "Mira", 1000, {})
local fakeBidder = fake(-434343, "Toren", 10 ^ 9, {})
local state = { listing = nil }

local function out(text)
    workspace:SetAttribute("AuctionQAOut", text)
    print("AuctionQA: " .. text)
end

local commands = {}

function commands.setup()
    local player = Players:GetPlayers()[1]
    local qi, rank = PlayerData.getStats(player)
    qi.Value = 70000
    rank.Value = "Core Initiate"
    for _, petId in { "VoltFox", "GoldenKirin", "LunarHopper", "AzureSkyDragon" } do
        PetInventory.grantPet(player, petId, "Large")
    end
    PetInventory.publish(player)
    Wallet.add(player, 20000, "QA", "QA")
    out("setup done: " .. rank.Value .. ", stones " .. Wallet.balance(player))
end

function commands.walk()
    local player = Players:GetPlayers()[1]
    local holder = workspace.FloatingIslands.Yggdrasil.Shops.Marketplace.Prompt
    local root = player.Character.HumanoidRootPart
    root.CFrame = CFrame.new(holder.Position + holder.CFrame.LookVector * 0 + Vector3.new(0, 3, 0)) * CFrame.new(0, 0, 5)
    out("walked: " .. string.format("%.1f", (root.Position - holder.Position).Magnitude) .. " studs from the prompt")
end

-- a listing from another (fake) player, on the test stores: something for the real player to bid on
function commands.fakeListing()
    local item = { InstanceId = HttpService:GenerateGUID(false), PetId = "StormhornKirin", Level = 2, Size = "Giant", Worth = 3 }
    table.insert(fakeSeller.mem.items, item)
    local low = AuctionRules.startRange("Pet", item)
    local ok, id, status = core:list(fakeSeller, { Kind = "Pet", InstanceId = item.InstanceId, StartBid = low, Hours = 1,
        Fee = AuctionRules.listingFee(low), Paid = false, Rarity = "Legendary", Value = AuctionRules.value("Pet", item),
        Cap = AuctionRules.priceCap("Pet", item), SellerName = "Mira" })
    state.listing = id
    out("fake listing " .. tostring(ok) .. " " .. tostring(status) .. " " .. tostring(id) .. " start " .. low)
end

-- the fake bidder outbids whoever is on top of the fake listing
function commands.fakeOutbid()
    local _, record = AuctionStores.listings.get(state.listing)
    local amount = AuctionRules.minBid(record)
    local _, outcome = core:bid(fakeBidder, state.listing, amount)
    out("fake outbid " .. tostring(outcome) .. " at " .. amount)
end

function commands.read()
    local player = Players:GetPlayers()[1]
    local _, box = AuctionStores.mail.get("M_" .. player.UserId)
    local items, done = 0, 0
    for _ in (box and box.Items) or {} do
        items += 1
    end
    for _ in (box and box.Done) or {} do
        done += 1
    end
    local snapshot = PetInventory.getSnapshot(player)
    out("stones " .. Wallet.balance(player) .. ", pets " .. #snapshot.Pets .. ", mailbox items " .. items .. " done " .. done
        .. ", prefix " .. AuctionStores.prefix)
end

workspace:GetAttributeChangedSignal("AuctionQA"):Connect(function()
    local command = workspace:GetAttribute("AuctionQA")
    if command and commands[command] then
        local ok, err = pcall(commands[command])
        if not ok then
            out("ERROR " .. tostring(err))
        end
        workspace:SetAttribute("AuctionQA", nil)
    end
end)
out("ready")

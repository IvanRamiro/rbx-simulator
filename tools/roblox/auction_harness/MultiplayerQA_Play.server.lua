-- QA (Studio Local Server only; injected as a Script into a running server, never shipped): helps the 2-player Auction House test
-- on the live modules. Commands through workspace attribute "AHMP" (a string "command arg"); answers in "AHMPOut".
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local RS = game:GetService("ReplicatedStorage")
local SSS = game:GetService("ServerScriptService")
if not RunService:IsStudio() then
    return
end
local GameConfig = require(RS.GameConfig)
local AuctionRules = require(RS.AuctionRules)
local AuctionCore = require(SSS.Auction.AuctionCore)
local AuctionStores = require(SSS.Auction.AuctionStores)
local AuctionLedger = require(SSS.Auction.AuctionLedger)
local PetInventory = require(SSS.Pets.PetInventory)
local WeaponInventory = require(SSS.Shop.WeaponInventory)
local Wallet = require(SSS.Shop.Wallet)
local PlayerData = require(SSS.Data.PlayerData)

local function out(text)
    workspace:SetAttribute("AHMPOut", text)
    print("AHMP: " .. text)
end

local saved = {}
local commands = {}

local function byName(name)
    return Players:FindFirstChild(name)
end

function commands.setup()
    saved.age = saved.age or GameConfig.AuctionHouse.MinAccountAgeDays
    GameConfig.AuctionHouse.MinAccountAgeDays = 0 -- (this session's code predates the Studio rule; put back by "restore")
    local lines = {}
    local gifts = { Player1 = { "GoldenKirin", "VoltFox" }, Player2 = { "LunarHopper", "AzureSkyDragon" } }
    for _, p in Players:GetPlayers() do
        local qi, rank = PlayerData.getStats(p)
        qi.Value = math.max(qi.Value, 70000)
        rank.Value = "Core Initiate"
        Wallet.add(p, 20000, "QA", "QA")
        for _, petId in gifts[p.Name] or {} do
            PetInventory.grantPet(p, petId, "Normal")
        end
        if p.Name == "Player1" then
            WeaponInventory.grant(p, "Sword2")
        end
        PetInventory.publish(p)
        table.insert(lines, p.Name .. " stones " .. Wallet.balance(p) .. " pets " .. #PetInventory.getSnapshot(p).Pets)
    end
    out(table.concat(lines, "; "))
end

function commands.walk()
    local holder = workspace.FloatingIslands.Yggdrasil.Shops.Marketplace.Prompt
    local i = 0
    for _, p in Players:GetPlayers() do
        i += 1
        p.Character.HumanoidRootPart.CFrame = CFrame.new(holder.Position + Vector3.new(i * 3 - 4.5, 3, 0)) * CFrame.new(0, 0, 5)
    end
    out("walked")
end

-- every listing the players have, with its state
function commands.state()
    local lines = {}
    for _, p in Players:GetPlayers() do
        local ledger = AuctionLedger.get(p)
        local ids = {}
        for _, id in ledger.Mine do
            local _, r = AuctionStores.listings.get(id)
            table.insert(ids, "mine " .. string.sub(id, 1, 8) .. " " .. (r and (r.State .. " " .. (r.Item and (r.Item.PetId or r.Item.WeaponId) or "?")
                .. " top " .. tostring(r.High and r.High.Amount) .. " ends in " .. (r.Ends - os.time())) or "?"))
        end
        for _, id in ledger.Watch do
            local _, r = AuctionStores.listings.get(id)
            table.insert(ids, "watch " .. string.sub(id, 1, 8) .. " " .. (r and r.State or "?"))
        end
        local _, box = AuctionStores.mail.get("M_" .. p.UserId)
        local items = 0
        for _ in (box and box.Items) or {} do
            items += 1
        end
        table.insert(lines, p.Name .. ": stones " .. Wallet.balance(p) .. ", pets " .. #PetInventory.getSnapshot(p).Pets .. ", weapons "
            .. #WeaponInventory.snapshot(p).Weapons .. ", mail waiting " .. items .. ", out " .. AuctionCore.count(ledger.Out)
            .. ", bids " .. AuctionCore.count(ledger.Bids) .. " | " .. table.concat(ids, "; "))
    end
    out(table.concat(lines, "\n"))
end

-- moves a listing's end to `seconds` from now on the test store (its first end too, so the anti-snipe cap counts from here)
function commands.shift(arg)
    local prefix, seconds = string.match(arg, "^(%S+)%s+(%-?%d+)$")
    seconds = tonumber(seconds)
    local target
    for _, p in Players:GetPlayers() do
        for _, list in { AuctionLedger.get(p).Mine, AuctionLedger.get(p).Watch } do
            for _, id in list do
                if string.sub(id, 1, #prefix) == prefix then
                    target = id
                end
            end
        end
    end
    if not target then
        return out("no listing " .. prefix)
    end
    local record
    AuctionStores.listings.update(target, function(old)
        if not old or old.State ~= "Active" then
            return nil
        end
        old.Ends = os.time() + seconds
        old.FirstEnds = old.Ends
        record = old
        return old
    end)
    if record then
        AuctionStores.index.put(AuctionCore.summary(record))
    end
    out("shifted " .. string.sub(target, 1, 8) .. " to end in " .. seconds .. " s: " .. tostring(record ~= nil))
end

function commands.restore()
    if saved.age then
        GameConfig.AuctionHouse.MinAccountAgeDays = saved.age
    end
    out("restored: age rule " .. GameConfig.AuctionHouse.MinAccountAgeDays)
end

workspace:GetAttributeChangedSignal("AHMP"):Connect(function()
    local raw = workspace:GetAttribute("AHMP")
    if not raw then
        return
    end
    local command, arg = string.match(raw, "^(%S+)%s*(.*)$")
    if commands[command] then
        local ok, err = pcall(commands[command], arg)
        if not ok then
            out("ERROR " .. tostring(err))
        end
    end
    workspace:SetAttribute("AHMP", nil)
end)
out("ready")

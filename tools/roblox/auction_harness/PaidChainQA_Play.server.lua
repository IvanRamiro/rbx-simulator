-- QA (Studio Play only; copied into src/server/Auction for a test and removed after, never shipped): the paid-item chain on the
-- live modules. A spin bought with Robux wins an egg (the wheel forced onto its Egg segment), the egg is paid, the pet hatched from
-- it is paid, and the Auction House keeps it from a player who may not trade paid items. Commands through workspace attribute
-- "PaidQA" (answers in "PaidQAOut"); the client presses the wheel and the altar itself.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local RS = game:GetService("ReplicatedStorage")
local SSS = game:GetService("ServerScriptService")
if not RunService:IsStudio() then
    return
end
local EggInventory = require(SSS.Pets.EggInventory)
local PetInventory = require(SSS.Pets.PetInventory)
local SpinLedger = require(SSS.Rewards.SpinLedger)
local SpinRules = require(RS.SpinRules)
local AuctionChecks = require(SSS.Auction.AuctionChecks)
local AuctionCore = require(SSS.Auction.AuctionCore)
local AuctionStores = require(SSS.Auction.AuctionStores)
local AuctionRules = require(RS.AuctionRules)
local GameConfig = require(RS.GameConfig)
local Ranks = require(RS.Ranks)

local function out(text)
    workspace:SetAttribute("PaidQAOut", text)
    print("PaidQA: " .. text)
end

local state = {}
local commands = {}

local function player()
    return Players:GetPlayers()[1]
end

local function moveTo(part)
    local root = player().Character.HumanoidRootPart
    root.CFrame = CFrame.new(part.Position + Vector3.new(0, 3, 0)) * CFrame.new(0, 0, 4)
end

-- what the old save brought in: the pets, the eggs, the paid counts
function commands.inspect()
    local p = player()
    local lines = {}
    for _, pet in PetInventory.getSnapshot(p).Pets do
        table.insert(lines, pet.PetId .. (if pet.Paid then "(paid)" else "") .. (if AuctionRules.isPaid("Pet", pet) then "[auction: paid]" else ""))
    end
    local eggs = {}
    for eggId in GameConfig.Eggs do
        local n = EggInventory.count(p, eggId)
        if n > 0 then
            table.insert(eggs, eggId .. "=" .. n .. " paid " .. EggInventory.paidCount(p, eggId))
        end
    end
    out("pets: " .. table.concat(lines, ", ") .. " | eggs: " .. table.concat(eggs, ", "))
end

-- a bought spin, today's free ones used, the wheel forced onto the Egg segment; the player walks to the wheel
function commands.spinSetup()
    local p = player()
    local data = SpinLedger.today(p)
    data.Used = GameConfig.SpinWheel.DailySpins + data.Extra
    SpinLedger.addBought(p, 1)
    local eggIndex
    for index, segment in GameConfig.SpinWheel.Segments do
        if segment.Kind == "Egg" then
            eggIndex = index
        end
    end
    state.oldRoll = state.oldRoll or SpinRules.roll
    SpinRules.roll = function()
        return eggIndex
    end
    state.eggId = SpinRules.bestEgg(Ranks.getPlayerRankName(p))
    state.before = EggInventory.paidCount(p, state.eggId)
    state.countBefore = EggInventory.count(p, state.eggId)
    moveTo(workspace.FloatingIslands.Yggdrasil.SpinWheel.Prompt)
    out("spin ready: free left " .. SpinRules.freeLeft(data) .. ", bought " .. data.Bought .. ", egg " .. state.eggId
        .. " held " .. state.countBefore .. " paid " .. state.before)
end

function commands.spinCheck()
    local p = player()
    SpinRules.roll = state.oldRoll or SpinRules.roll
    out("after the bought spin: " .. state.eggId .. " held " .. EggInventory.count(p, state.eggId) .. " (was " .. state.countBefore
        .. "), paid " .. EggInventory.paidCount(p, state.eggId) .. " (was " .. state.before .. ")")
end

function commands.altar()
    local p = player()
    state.petsBefore = {}
    for _, pet in PetInventory.getSnapshot(p).Pets do
        state.petsBefore[pet.InstanceId] = true
    end
    moveTo(workspace.FloatingIslands.Yggdrasil.HatchingAltar.Prompt)
    out("at the altar, egg " .. tostring(state.eggId))
end

function commands.hatchCheck()
    local p = player()
    local new
    for _, pet in PetInventory.getSnapshot(p).Pets do
        if not state.petsBefore[pet.InstanceId] then
            new = pet
        end
    end
    if not new then
        return out("no new pet")
    end
    state.newPet = new
    local blocked = AuctionChecks.item({ kind = "Pet", pet = new, petCount = 5, paidOk = false })
    local allowed = AuctionChecks.item({ kind = "Pet", pet = new, petCount = 5, paidOk = true })
    out("hatched " .. new.PetId .. " Paid=" .. tostring(new.Paid) .. ", paid eggs left " .. EggInventory.paidCount(p, state.eggId)
        .. " | where paid trading isn't allowed: " .. tostring(blocked) .. " | elsewhere: " .. tostring(allowed))
end

-- the hatched pet on the real (test) stores: listed with Paid, a bidder who may not trade paid items refused, one who may accepted
function commands.listing()
    local p = player()
    local pet = state.newPet
    local record = PetInventory.takeRecord(p, pet.InstanceId)
    PetInventory.publish(p)
    local core = AuctionCore.new({
        now = os.time, guid = function()
            return HttpService:GenerateGUID(false)
        end,
        listings = AuctionStores.listings, mail = AuctionStores.mail, index = AuctionStores.index, notify = function() end,
        rules = { minBid = AuctionRules.minBid, saleTax = AuctionRules.saleTax }, config = GameConfig.AuctionHouse,
    })
    local function fake(userId, paidOk, items)
        local mem = { stones = 1e6, items = items or {} }
        local f = { userId = userId, name = "Tester" .. -userId, paidOk = paidOk, pending = {}, mem = mem,
            ledger = { Out = {}, Bids = {}, Claimed = {}, Mine = {}, Watch = {} } }
        function f.takeItem(_, id)
            for i, item in mem.items do
                if item.InstanceId == id then
                    return table.remove(mem.items, i)
                end
            end
            return nil
        end
        function f.restoreItem(_, item)
            table.insert(mem.items, item)
            return true
        end
        function f.spend(n)
            mem.stones -= n
            return true
        end
        function f.add(n)
            mem.stones += n
        end
        function f.saveConfirmed()
            return true
        end
        function f.saveSoon() end
        return f
    end
    local seller = fake(-515151, true, { record })
    local low = AuctionRules.startRange("Pet", record)
    local _, id = core:list(seller, { Kind = "Pet", InstanceId = record.InstanceId, StartBid = low, Hours = 1, Fee = AuctionRules.listingFee(low),
        Paid = AuctionRules.isPaid("Pet", record), Rarity = AuctionRules.rarity("Pet", record), Value = AuctionRules.value("Pet", record),
        Cap = AuctionRules.priceCap("Pet", record), SellerName = "Tester" })
    local _, listing = AuctionStores.listings.get(id)
    local _, refused, why = core:bid(fake(-525252, false), id, low)
    local _, accepted = core:bid(fake(-535353, true), id, low)
    local _, after = AuctionStores.listings.get(id)
    out("listing Paid=" .. tostring(listing.Paid) .. " item Paid=" .. tostring(listing.Item.Paid) .. " | bidder not allowed: " .. tostring(refused)
        .. "/" .. tostring(why) .. " | bidder allowed: " .. tostring(accepted) .. " | top " .. tostring(after.High and after.High.Name))
end

-- fusing: a paid copy fused into a free pet makes it paid; and the unit rules of the paid egg counts (a stand-in player)
function commands.fuse()
    local p = player()
    local _, target = PetInventory.grantPet(p, "CloudSheep", "Normal", false)
    PetInventory.grantPet(p, "CloudSheep", "Normal", true)
    local ok, text = PetInventory.fuse(p, target)
    local fused = PetInventory.get(p, target)
    local _, target2 = PetInventory.grantPet(p, "GlacierPuff", "Normal", false)
    PetInventory.grantPet(p, "GlacierPuff", "Normal", false)
    PetInventory.fuse(p, target2)
    local free = PetInventory.get(p, target2)
    -- out to the auction's escrow and back (takeRecord, restore): the mark stays
    local escrowed = PetInventory.takeRecord(p, target)
    PetInventory.restore(p, escrowed)
    local back = PetInventory.get(p, target)
    PetInventory.publish(p)
    -- the egg counts, on a stand-in player (EggInventory only sets attributes on it)
    local fakePlayer = { SetAttribute = function() end }
    EggInventory.setupPlayer(fakePlayer, { Eggs = { BeginnerQiEgg = 2 }, PaidEggs = { BeginnerQiEgg = 5 } })
    local clamped = EggInventory.paidCount(fakePlayer, "BeginnerQiEgg")
    EggInventory.grant(fakePlayer, "BeginnerQiEgg", true)
    local _, first = EggInventory.take(fakePlayer, "BeginnerQiEgg")
    local _, second = EggInventory.take(fakePlayer, "BeginnerQiEgg")
    local _, third = EggInventory.take(fakePlayer, "BeginnerQiEgg")
    local _, fourth = EggInventory.take(fakePlayer, "BeginnerQiEgg")
    EggInventory.grant(fakePlayer, "BeginnerQiEgg", true)
    EggInventory.grant(fakePlayer, "BeginnerQiEgg", false)
    EggInventory.revoke(fakePlayer, "BeginnerQiEgg", false)
    local afterRevoke = EggInventory.paidCount(fakePlayer, "BeginnerQiEgg")
    EggInventory.removePlayer(fakePlayer)
    out("fuse " .. tostring(ok) .. ": free + paid copy -> Paid=" .. tostring(fused and fused.Paid) .. "; free + free -> Paid=" .. tostring(free and free.Paid) .. "; escrow record Paid=" .. tostring(escrowed and escrowed.Paid)
        .. ", back in the inventory Paid=" .. tostring(back and back.Paid)
        .. " | eggs: saved paid 5 of 2 read as " .. clamped .. "; takes paid-first " .. tostring(first) .. "," .. tostring(second) .. ","
        .. tostring(third) .. ", none left " .. tostring(fourth) .. "; an unpaid grant undone keeps the paid one: " .. afterRevoke)
end

workspace:GetAttributeChangedSignal("PaidQA"):Connect(function()
    local command = workspace:GetAttribute("PaidQA")
    if command and commands[command] then
        local ok, err = pcall(commands[command])
        if not ok then
            out("ERROR " .. tostring(err))
        end
        workspace:SetAttribute("PaidQA", nil)
    end
end)
out("ready")

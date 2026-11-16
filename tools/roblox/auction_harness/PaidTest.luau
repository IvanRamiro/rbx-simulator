-- The paid-item chain on the real modules (bundled by paid_cli.py): eggs from Robux are counted per kind and hatched first, the
-- pet they give is marked Paid and keeps the mark through fusing, the save, the auction's journal and escrow, and the Auction
-- House refuses it to a player who may not trade paid items. Old saves load with nothing marked.
local EggInventory = require("EggInventory")
local SpinLedger = require("SpinLedger")
local PetInventory = require("PetInventory")
local AuctionRules = require("AuctionRules")
local AuctionChecks = require("AuctionChecks")
local AuctionLedger = require("AuctionLedger")
local GameConfig = require("GameConfig")

local passed, failed = 0, 0
local function check(cond, what)
    if cond then
        passed += 1
    else
        failed += 1
        print("FAIL: " .. what)
    end
end
local function fakePlayer(id)
    return { UserId = id, Name = "P" .. id, SetAttribute = function() end, GetAttribute = function() return nil end,
        FindFirstChild = function() return nil end }
end

-- ---------- the paid egg counts ----------
local p = fakePlayer(10)
EggInventory.setupPlayer(p, { Eggs = { BeginnerQiEgg = 2 }, PaidEggs = { BeginnerQiEgg = 5, NotAnEgg = 1 } })
check(EggInventory.paidCount(p, "BeginnerQiEgg") == 2, "a saved paid count over the held count is cut to it")
check(EggInventory.exportPaid(p).NotAnEgg == nil, "a paid count of an egg not held is dropped")
EggInventory.setupPlayer(fakePlayer(11), nil)
local q = fakePlayer(12)
EggInventory.setupPlayer(q, { Eggs = { BeginnerQiEgg = 3 } }) -- (an old save: no PaidEggs)
check(EggInventory.paidCount(q, "BeginnerQiEgg") == 0, "OLD SAVE: eggs from before the mark are not paid")
EggInventory.grant(q, "BeginnerQiEgg", true) -- a bought spin's egg
check(EggInventory.count(q, "BeginnerQiEgg") == 4 and EggInventory.paidCount(q, "BeginnerQiEgg") == 1, "a paid grant counts one paid egg")
local ok1, paid1 = EggInventory.take(q, "BeginnerQiEgg")
local ok2, paid2 = EggInventory.take(q, "BeginnerQiEgg")
check(ok1 and paid1 == true, "a hatch takes the paid egg first")
check(ok2 and paid2 == false, "then the free ones")
check(EggInventory.paidCount(q, "BeginnerQiEgg") == 0 and EggInventory.count(q, "BeginnerQiEgg") == 2, "counts after two hatches")
EggInventory.grant(q, "BeginnerQiEgg", true)
EggInventory.grant(q, "BeginnerQiEgg", false) -- a Merchant deal...
EggInventory.revoke(q, "BeginnerQiEgg", false) -- ...taken back
check(EggInventory.paidCount(q, "BeginnerQiEgg") == 1 and EggInventory.count(q, "BeginnerQiEgg") == 3,
    "undoing a free grant never removes a paid egg")
EggInventory.revoke(q, "BeginnerQiEgg", true) -- a Robux purchase taken back
check(EggInventory.paidCount(q, "BeginnerQiEgg") == 0 and EggInventory.count(q, "BeginnerQiEgg") == 2, "undoing a paid grant removes the paid egg")
for _ = 1, 2 do
    EggInventory.take(q, "BeginnerQiEgg")
end
local none, nonePaid = EggInventory.take(q, "BeginnerQiEgg")
check(none == false and nonePaid == false, "no egg left: nothing taken")

-- ---------- the spin ledger: which spin was a bought one ----------
local s = fakePlayer(20)
SpinLedger.setupPlayer(s, { Spin = { Day = 0, Used = 0, Extra = 0, Bought = 1 } })
local free = GameConfig.SpinWheel.DailySpins
for i = 1, free do
    local okSpin, bought = SpinLedger.take(s)
    check(okSpin and bought == false, "free spin " .. i .. " is not a bought one")
end
local okBought, wasBought = SpinLedger.take(s)
check(okBought and wasBought == true, "the bought spin is reported as bought")
local okNone = SpinLedger.take(s)
check(okNone == false, "no spin left")
local pending = SpinLedger.sanitize({ Pending = { Segment = 5, Day = 3, EggId = "BeginnerQiEgg", Paid = true } }).Pending
check(pending and pending.Paid == true, "a pending reward from a bought spin keeps Paid through the save")
local pendingFree = SpinLedger.sanitize({ Pending = { Segment = 5, Day = 3, EggId = "BeginnerQiEgg" } }).Pending
check(pendingFree and pendingFree.Paid == nil, "a free spin's pending reward is not paid")

-- ---------- the pet: marked, kept through fusing, the save and the escrow ----------
local owner = fakePlayer(30)
PetInventory.setupPlayer(owner, { Pets = {
    { InstanceId = "OLD1", PetId = "VoltFox", Level = 1, Size = "Normal", Worth = 1 },           -- an old save's pet: no mark
    { InstanceId = "OLD2", PetId = "Crysalith", Level = 1, Size = "Normal", Worth = 1 },          -- an Exclusive Egg beast, no mark
}, EquippedPetIds = {}, Pen = {}, PenLevel = 1 })
check(PetInventory.get(owner, "OLD1").Paid == false, "OLD SAVE: an old pet is not paid")
check(not AuctionRules.isPaid("Pet", PetInventory.get(owner, "OLD1")), "OLD SAVE: and trades everywhere")
check(AuctionRules.isPaid("Pet", PetInventory.get(owner, "OLD2")), "OLD SAVE: an Exclusive Egg beast is still paid by kind")
-- the chain: a bought spin's egg hatched (PetService passes the egg's paid flag to grantPet)
local okGrant, paidId = PetInventory.grantPet(owner, "CloudSheep", "Large", paid1)
check(okGrant and PetInventory.get(owner, paidId).Paid == true, "CHAIN: the pet hatched from the paid egg is marked Paid")
local _, freeId = PetInventory.grantPet(owner, "CloudSheep", "Normal", false)
check(PetInventory.get(owner, freeId).Paid == false, "a pet from a free egg is not")
-- policy: listing it
local facts = function(pet, paidOk)
    return { kind = "Pet", pet = pet, petCount = 5, paidOk = paidOk, rankName = "Core Initiate", ageDays = 400, activeListings = 0,
        startBid = (AuctionRules.startRange("Pet", pet)), hours = 4, stones = 1e6 }
end
local blocked, why = AuctionChecks.list(facts(PetInventory.get(owner, paidId), false))
check(not blocked and string.find(why, "Robux") ~= nil, "CHAIN: listing it is refused where paid items can't be traded")
local allowed, info = AuctionChecks.list(facts(PetInventory.get(owner, paidId), true))
check(allowed == true and info.Paid == true, "CHAIN: allowed elsewhere, and the listing is marked Paid")
check(AuctionChecks.list(facts(PetInventory.get(owner, freeId), false)) == true, "a free pet lists everywhere")
-- fusing a paid copy into the free one: the result is paid
local _, target = PetInventory.grantPet(owner, "GlacierPuff", "Normal", false)
PetInventory.grantPet(owner, "GlacierPuff", "Normal", true)
local fused = PetInventory.fuse(owner, target)
check(fused and PetInventory.get(owner, target).Paid == true, "fusing a paid copy in makes the pet paid")
local _, target2 = PetInventory.grantPet(owner, "MossGolem", "Normal", false)
PetInventory.grantPet(owner, "MossGolem", "Normal", false)
PetInventory.fuse(owner, target2)
check(PetInventory.get(owner, target2).Paid == false, "two free copies stay free")
-- the save
local saved = PetInventory.exportData(owner)
local savedPaid
for _, pet in saved.Pets do
    if pet.InstanceId == paidId then
        savedPaid = pet.Paid
    end
end
check(savedPaid == true, "the mark is saved")
local reloaded = fakePlayer(31)
PetInventory.setupPlayer(reloaded, saved)
check(PetInventory.get(reloaded, paidId).Paid == true, "and loads back")
-- the escrow: out to the journal and back from the mail
local record = PetInventory.takeRecord(owner, paidId)
check(record and record.Paid == true, "the escrowed record keeps the mark")
local journal = AuctionLedger.sanitize({ Out = { L1 = { Kind = "Pet", Item = record, StartBid = 10, Hours = 1, Fee = 2 } } })
check(journal.Out.L1 and journal.Out.L1.Item.Paid == true, "the save's auction journal keeps the mark")
local winner = fakePlayer(32)
PetInventory.setupPlayer(winner, nil)
check(PetInventory.restore(winner, journal.Out.L1.Item), "delivered to the winner")
check(PetInventory.get(winner, paidId).Paid == true, "the winner's pet is still paid")

print(string.format("PAID CHAIN: %d passed, %d failed", passed, failed))

-- ---------- and the request checks against the real config ----------
local checks = require("ChecksTest")
local p2, f2, lines = checks(require("AuctionChecks"), require("AuctionRules"), require("GameConfig"))
for _, line in lines do
    print(line)
end
if failed + f2 > 0 then
    error((failed + f2) .. " checks failed")
end

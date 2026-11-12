-- The Wandering Merchant's timetable and wares (GameConfig.WanderingMerchant), shared so the server and every client agree
-- on when he is in the hub, what he sells this visit and for how much. Times are unix seconds (os.time()).
--
--   Merchant.isOpen(now)          whether he is in the hub: the first Stay seconds of every Every
--   Merchant.visitIndex(now)      which visit `now` falls in (the hours since 1970): it seeds the visit's deals
--   Merchant.leavesAt(now)        when the visit `now` falls in ends
--   Merchant.nextArrival(now)     when the next visit after `now` begins
--   Merchant.dealsFor(visit)      that visit's deals, in the order shown: Deals.Min to Deals.Max of the Pool, no repeats
--   Merchant.isOffered(visit, id) whether that deal is among that visit's
--   Merchant.deal(id)             a deal by its Id: { Id, Kind, ItemId, Name, Count, Price, FullPrice, Rarity, RequiredRank }
--   Merchant.price(deal)          what a deal costs, in Spirit Stones
--
-- A deal's Id is its Kind and its item ("Egg_BeginnerQiEgg", "Pet_GoldenKirin"), so a saved purchase stays readable.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local Merchant = {}

local CONFIG = GameConfig.WanderingMerchant
local SEED_STEP = 7919 -- odd (a prime): a visit's number times this seeds its draw
-- a brand-new cultivator's rank: every visit offers at least one deal it can buy
local FIRST_RANK = GameConfig.Ranks[1].Id

assert(CONFIG.Stay > 0 and CONFIG.Stay < CONFIG.Every, "WanderingMerchant.Stay must be shorter than Every")
assert(CONFIG.LeaveWarning < CONFIG.Stay, "WanderingMerchant.LeaveWarning must be shorter than Stay")
assert(CONFIG.Deals.Min >= 1 and CONFIG.Deals.Max >= CONFIG.Deals.Min and CONFIG.Deals.Max <= #CONFIG.Pool,
    "WanderingMerchant.Deals must be between 1 and the size of its Pool")

-- ---------- the timetable ----------
function Merchant.visitIndex(now)
    return math.floor(now) // CONFIG.Every
end

function Merchant.isOpen(now)
    return math.floor(now) % CONFIG.Every < CONFIG.Stay
end

function Merchant.leavesAt(now)
    return Merchant.visitIndex(now) * CONFIG.Every + CONFIG.Stay
end

function Merchant.nextArrival(now)
    return (Merchant.visitIndex(now) + 1) * CONFIG.Every
end

-- ---------- the wares ----------
local byId = {}
local pool = {} -- the Pool's deals, in its order

for index, entry in CONFIG.Pool do
    local deal
    if entry.Kind == "Egg" then
        local egg = GameConfig.Eggs[entry.EggId]
        assert(egg, "WanderingMerchant.Pool[" .. index .. "]: unknown egg " .. tostring(entry.EggId))
        local count = entry.Count or 1
        assert(count >= 1 and count == math.floor(count), "WanderingMerchant.Pool[" .. index .. "]: Count must be a whole number of eggs")
        local full = Shop.marketEggPrice(entry.EggId) * count
        local price = Shop.roundNice(full * (1 - entry.Discount))
        -- the economy's rule, after rounding: never deeper than MaxEggDiscount (see GameConfig.WanderingMerchant)
        assert(entry.Discount > 0 and price >= full * (1 - CONFIG.MaxEggDiscount) and price < full,
            "WanderingMerchant.Pool[" .. index .. "] (" .. entry.EggId .. "): its discount must be above 0 and at most "
                .. CONFIG.MaxEggDiscount * 100 .. "%")
        deal = {
            Id = "Egg_" .. entry.EggId, Kind = "Egg", ItemId = entry.EggId, Name = egg.DisplayName, Count = count,
            Price = price, FullPrice = full, Rarity = nil, RequiredRank = egg.RequiredRank,
        }
    elseif entry.Kind == "Pet" then
        local pet = GameConfig.Pets[entry.PetId]
        assert(pet, "WanderingMerchant.Pool[" .. index .. "]: unknown pet " .. tostring(entry.PetId))
        assert(CONFIG.PetRarities[pet.Rarity], "WanderingMerchant.Pool[" .. index .. "] (" .. entry.PetId .. "): "
            .. pet.Rarity .. " beasts aren't sold")
        local rank = Shop.petEggRank(entry.PetId)
        assert(rank, "WanderingMerchant.Pool[" .. index .. "] (" .. entry.PetId .. "): no egg hatches it, so no rank can buy it")
        local value = Shop.petValue(entry.PetId, 1)
        local price = Shop.roundNice(value * CONFIG.PetMarkup)
        assert(price >= value * CONFIG.MinPetMarkup, "WanderingMerchant.Pool[" .. index .. "] (" .. entry.PetId .. "): "
            .. price .. " is under " .. CONFIG.MinPetMarkup .. " times what it sells for (" .. value .. ")")
        deal = {
            Id = "Pet_" .. entry.PetId, Kind = "Pet", ItemId = entry.PetId, Name = pet.DisplayName, Count = 1,
            Price = price, FullPrice = nil, Rarity = pet.Rarity, RequiredRank = rank,
        }
    else
        error("WanderingMerchant.Pool[" .. index .. "]: unknown Kind " .. tostring(entry.Kind))
    end
    assert(not byId[deal.Id], "WanderingMerchant.Pool has " .. deal.Id .. " twice")
    byId[deal.Id] = deal
    table.insert(pool, deal)
end

function Merchant.deal(id)
    return if typeof(id) == "string" then byId[id] else nil
end

function Merchant.price(deal)
    return deal.Price
end

local cached = { visit = nil, deals = nil }

function Merchant.dealsFor(visit)
    if cached.visit == visit then
        return cached.deals
    end
    local rng = Random.new(visit * SEED_STEP)
    local count = rng:NextInteger(CONFIG.Deals.Min, CONFIG.Deals.Max)
    local order = {}
    for i = 1, #pool do
        order[i] = i
    end
    local deals = {}
    for i = 1, count do -- the first `count` of a shuffle: no repeats
        local j = rng:NextInteger(i, #pool)
        order[i], order[j] = order[j], order[i]
        table.insert(deals, pool[order[i]])
    end
    -- every visit has something a brand-new player can buy (Studio, 2026-11-12: one visit's four deals were all locked to a
    -- new player): if none needs only the first rank, the last deal drawn gives way to one that does, the next in the shuffle
    local function beginner(deal)
        return deal.RequiredRank == FIRST_RANK
    end
    local any = false
    for _, deal in deals do
        any = any or beginner(deal)
    end
    if not any then
        for k = count + 1, #pool do
            local j = rng:NextInteger(k, #pool)
            order[k], order[j] = order[j], order[k]
            if beginner(pool[order[k]]) then
                deals[count] = pool[order[k]]
                break
            end
        end
    end
    cached.visit, cached.deals = visit, deals
    return deals
end

-- whether a deal is among a visit's
function Merchant.isOffered(visit, id)
    for _, deal in Merchant.dealsFor(visit) do
        if deal.Id == id then
            return true
        end
    end
    return false
end

return Merchant

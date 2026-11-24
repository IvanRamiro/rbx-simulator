-- What the Auction House checks before it touches anything (AuctionService gathers the facts; AuctionCore checks the parts that
-- can change again inside its atomic writes). Plain facts in, ok or a plain-words reason out, so the harness can test them.
--
--   AuctionChecks.item(f)    why this item can't be put up right now, or nil
--       f = { kind, pet (a PetInventory snapshot record) | weapon (a WeaponInventory record), equippedWeapon, petCount,
--             paidOk, isCreatorPet }
--   AuctionChecks.list(f)    ok, why | info { Item, Fee, Value, Cap, Rarity, Paid, Low, High }
--       f = item's facts + { rankName, ageDays, activeListings, startBid, hours, stones }
--   AuctionChecks.bid(f)     ok, why
--       f = { rankName, ageDays, paidOk, userId, record (the listing as just read), amount, stones, bidOn, watching, now }
--   AuctionChecks.refusalText(why, record)   AuctionCore's refusal, in plain words
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local AuctionRules = require(ReplicatedStorage:WaitForChild("AuctionRules"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local CONFIG = AuctionRules.Config

local AuctionChecks = {}

local function stones(n)
    return NumberFormat.compact(n) .. " Spirit Stones"
end

local PAID = "Beasts that came from Robux (the Exclusive Egg or a bought spin) can't be traded where you live."
AuctionChecks.PaidText = PAID
AuctionChecks.BoundText = "A beta gift beast is yours for good. It can't be given away, sold or auctioned."

function AuctionChecks.item(f)
    if f.kind == "Pet" then
        local pet = f.pet
        if not pet then
            return "That pet isn't yours."
        end
        if pet.Locked then
            return "Unlock this pet first (in your Pets window)."
        end
        if pet.Equipped then
            return "Unequip this pet first."
        end
        if pet.InPen then
            return "Take this pet out of your pen first."
        end
        if (f.petCount or 0) <= 1 then
            return "You can't sell your last pet."
        end
        if f.isCreatorPet then
            return "This pet always comes back to you, so it can't be sold."
        end
        if AuctionRules.isBoundGift(pet) then
            return AuctionChecks.BoundText
        end
        if AuctionRules.isPaid("Pet", pet) and not f.paidOk then
            return PAID
        end
        return nil
    elseif f.kind == "Weapon" then
        local weapon = f.weapon
        if not weapon then
            return "That weapon isn't yours."
        end
        if Shop.isBound(weapon.WeaponId) then
            return "A faction's secret weapon is yours for good. It can't be sold."
        end
        if weapon.InstanceId == f.equippedWeapon then
            return "Unequip this weapon first."
        end
        return nil
    end
    return "Choose a pet or a weapon to sell."
end

function AuctionChecks.list(f)
    local ok, why = AuctionRules.canUse(f.rankName, f.ageDays)
    if not ok then
        return false, why
    end
    why = AuctionChecks.item(f)
    if why then
        return false, why
    end
    if (f.activeListings or 0) >= CONFIG.MaxListings then
        return false, "You can have " .. CONFIG.MaxListings .. " items for sale at once."
    end
    if not AuctionRules.isDuration(f.hours) then
        return false, "Choose how long the auction lasts."
    end
    local item = if f.kind == "Pet" then f.pet else f.weapon
    local low, high = AuctionRules.startRange(f.kind, item)
    local start = AuctionRules.whole(f.startBid)
    if not start or start < low or start > high then
        return false, "The starting bid must be from " .. NumberFormat.compact(low) .. " to " .. stones(high) .. "."
    end
    local fee = AuctionRules.listingFee(start)
    if (f.stones or 0) < fee then
        return false, "You need " .. stones(fee) .. " for the listing fee."
    end
    return true, {
        Item = item, Fee = fee, Value = AuctionRules.value(f.kind, item), Cap = AuctionRules.priceCap(f.kind, item),
        Rarity = AuctionRules.rarity(f.kind, item), Paid = AuctionRules.isPaid(f.kind, item), Low = low, High = high,
    }
end

function AuctionChecks.refusalText(why, record)
    if why == "Ended" then
        return "This auction has ended."
    elseif why == "Own" then
        return "You can't bid on your own item."
    elseif why == "Top" then
        return "You already have the top bid."
    elseif why == "Paid" then
        return PAID
    elseif why == "Low" then
        return if record then "Someone bid first. The lowest bid now is " .. stones(AuctionRules.minBid(record)) .. "."
            else "Someone bid first. Try a higher bid."
    elseif why == "Cap" then
        return "Bids on this item stop at " .. stones(record and record.Cap or 0) .. "."
    elseif why == "Missing" then
        return "That auction is gone."
    end
    return "That bid didn't go through. Your stones are back."
end

function AuctionChecks.bid(f)
    local ok, why = AuctionRules.canUse(f.rankName, f.ageDays)
    if not ok then
        return false, why
    end
    local record = f.record
    if not record or record.State == "Void" or not record.Item then
        return false, "That auction is gone."
    end
    if record.State ~= "Active" or f.now >= record.Ends then
        return false, "This auction has ended."
    end
    if record.Seller == f.userId then
        return false, "You can't bid on your own item."
    end
    if record.High and record.High.UserId == f.userId then
        return false, "You already have the top bid."
    end
    if record.Paid and not f.paidOk then
        return false, PAID
    end
    ok, why = AuctionRules.canOwn(f.rankName, record.Kind, record.Item)
    if not ok then
        return false, why
    end
    local amount = AuctionRules.whole(f.amount)
    local least = AuctionRules.minBid(record)
    if not amount or amount < least then
        return false, "The lowest bid now is " .. stones(least) .. "."
    end
    if amount > record.Cap then
        return false, "Bids on this item stop at " .. stones(record.Cap) .. "."
    end
    if (f.stones or 0) < amount then
        return false, "You need " .. stones(amount) .. "."
    end
    if not f.watching and (f.bidOn or 0) >= CONFIG.MaxBidOn then
        return false, "You can bid on " .. CONFIG.MaxBidOn .. " auctions at once."
    end
    return true
end

return AuctionChecks

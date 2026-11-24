-- Gifting a pet (the owner's improvement list, item 19): the checks that need no Instances, so the spec runs them. GiftService gathers the facts and does the move;
-- what makes a pet giftable at all is the Auction House's own rule (server/Auction/AuctionChecks.item), so the two can never drift apart.
--
--   GiftRules.offerIssue(f)     why this offer can't be made, in plain words, or nil
--       f = { senderId, receiverId, receiverHere (bool), sent (gifts sent this visit), senderWaiting (bool: an offer of theirs is unanswered),
--             receiverWaiting (bool: they already have a gift to answer), receiverIssue (a plain-words reason the receiver can't take a pet, or nil) }
--   GiftRules.expired(offer, now)   whether an offer ({ At }) has waited too long
--   GiftRules.describe(pet)     what to call the gift, "a Large Dawn Phoenix (Level 3)"
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))

local CONFIG = GameConfig.Gifts

local GiftRules = {}
GiftRules.Config = CONFIG

function GiftRules.offerIssue(f)
    if f.senderId == f.receiverId then
        return "You can't gift a pet to yourself."
    end
    if not f.receiverHere then
        return "That player isn't here any more."
    end
    if (f.sent or 0) >= CONFIG.MaxPerVisit then
        return "You've sent " .. CONFIG.MaxPerVisit .. " gifts this visit. Come back in another server."
    end
    if f.senderWaiting then
        return "Wait for your last gift to be answered."
    end
    if f.receiverWaiting then
        return "That player already has a gift to answer. Try again in a moment."
    end
    if f.receiverIssue then
        return f.receiverIssue
    end
    return nil
end

function GiftRules.expired(offer, now)
    return typeof(offer) ~= "table" or typeof(offer.At) ~= "number" or now - offer.At > CONFIG.OfferSeconds
end

function GiftRules.describe(pet)
    local name = PetRules.displayName(pet.PetId, PetRules.mutation(pet))
    local size = PetRules.size(pet)
    local level = PetRules.level(pet)
    return (if size ~= "Normal" then size .. " " else "") .. name .. (if level > 1 then " (Level " .. level .. ")" else "")
end

return GiftRules

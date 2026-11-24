-- Gifting a pet (shared/GiftRules, GameConfig.Gifts): who may offer, when an offer lapses, how a gift is named.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local GiftRules = require("@shared/GiftRules")

local AuctionRules = require("@shared/AuctionRules")

local C = GameConfig.Gifts

local function facts(over)
    local f = { senderId = 1, receiverId = 2, receiverHere = true, sent = 0, sentToday = 0, offered = 0, senderWaiting = false, receiverWaiting = false, blocked = false, receiverIssue = nil }
    for k, v in over or {} do
        f[k] = v
    end
    return f
end

t.test("the config is sane: an offer waits long enough to read and not forever, and a visit's gifts are capped", function()
    t.ok(C.OfferSeconds >= 20 and C.OfferSeconds <= 120, "long enough to answer, short enough not to pile up")
    t.ok(C.MaxPerVisit >= 1 and C.MaxPerVisit <= 20, "a cap that is a cap")
    t.ok(C.AskEvery > 0)
    t.ok(C.MaxPerDay >= C.MaxPerVisit, "the day's cap is not under the visit's")
    t.ok(C.MaxOffersPerVisit >= C.MaxPerVisit and C.DeclineBlock > 0)
end)

t.test("a plain offer between two players is fine", function()
    t.eq(GiftRules.offerIssue(facts()), nil)
end)

t.test("no gift to yourself, to someone who left, or past the cap", function()
    t.ok(GiftRules.offerIssue(facts({ receiverId = 1 })) ~= nil, "yourself")
    t.ok(GiftRules.offerIssue(facts({ receiverHere = false })) ~= nil, "gone")
    t.eq(GiftRules.offerIssue(facts({ sent = C.MaxPerVisit - 1 })), nil, "one under the cap")
    t.ok(GiftRules.offerIssue(facts({ sent = C.MaxPerVisit })) ~= nil, "at the cap")
end)

t.test("one offer at a time each way, and the receiver's own reason is never passed on", function()
    t.ok(GiftRules.offerIssue(facts({ senderWaiting = true })) ~= nil, "yours is unanswered")
    t.ok(GiftRules.offerIssue(facts({ receiverWaiting = true })) ~= nil, "theirs is busy")
    local why = GiftRules.offerIssue(facts({ receiverIssue = "Their pets are full." }))
    t.ok(why ~= nil, "refused")
    t.ok(not string.find(why, "full"), "the sender is not told why (it would reveal someone else's rank, region or pets)")
end)

t.test("a day's gifts are capped across servers, offers are capped, and a decline blocks the same sender", function()
    t.eq(GiftRules.offerIssue(facts({ sentToday = C.MaxPerDay - 1 })), nil, "one under the day's cap")
    t.ok(GiftRules.offerIssue(facts({ sentToday = C.MaxPerDay })) ~= nil, "at the day's cap")
    t.eq(GiftRules.offerIssue(facts({ offered = C.MaxOffersPerVisit - 1 })), nil, "one under the offer cap")
    t.ok(GiftRules.offerIssue(facts({ offered = C.MaxOffersPerVisit })) ~= nil, "at the offer cap (answered or not)")
    t.ok(GiftRules.offerIssue(facts({ blocked = true })) ~= nil, "turned down a moment ago")
end)

t.test("a free copy of a paid kind of beast (the beta gift) is bound: never gifted, sold or auctioned; a marked paid one and an ordinary pet are not", function()
    local paidKind
    for _, egg in GameConfig.Eggs do
        if egg.Exclusive then
            paidKind = egg.Pool[1].PetId
            break
        end
    end
    t.ok(paidKind ~= nil, "the config has an Exclusive egg")
    t.eq(AuctionRules.isBoundGift({ PetId = paidKind }), true, "a beta gift beast (no Paid mark)")
    t.eq(AuctionRules.isBoundGift({ PetId = paidKind, Paid = true }), false, "a bought one is governed by the paid-item rule instead")
    local ordinary
    for id, def in GameConfig.Pets do
        if not AuctionRules.isPaidPet(id) then
            ordinary = id
            break
        end
    end
    t.eq(AuctionRules.isBoundGift({ PetId = ordinary }), false, "an ordinary pet")
    t.eq(AuctionRules.isBoundGift(nil), false)
    t.eq(AuctionRules.isBoundGift("x"), false)
end)

t.test("an offer lapses after the config's seconds, and a broken one counts as lapsed", function()
    t.eq(GiftRules.expired({ At = 100 }, 100 + C.OfferSeconds), false, "still waiting at the last second")
    t.eq(GiftRules.expired({ At = 100 }, 100 + C.OfferSeconds + 1), true)
    t.eq(GiftRules.expired(nil, 5), true)
    t.eq(GiftRules.expired({ At = "x" }, 5), true)
end)

t.test("a gift is named with its size and level", function()
    local petId = nil
    for id in GameConfig.Pets do
        petId = id
        break
    end
    local plain = GiftRules.describe({ PetId = petId })
    t.ok(type(plain) == "string" and #plain > 0 and not plain:find("Level"), "a level 1 normal pet is just its name: " .. plain)
    local big = GiftRules.describe({ PetId = petId, Level = 4, Size = "Giant" })
    t.ok(big:find("Giant") and big:find("Level 4"), "a big levelled pet says so: " .. big)
end)

t.finish("gift")

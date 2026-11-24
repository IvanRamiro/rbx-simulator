-- Gifting a pet (shared/GiftRules, GameConfig.Gifts): who may offer, when an offer lapses, how a gift is named.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local GiftRules = require("@shared/GiftRules")

local C = GameConfig.Gifts

local function facts(over)
    local f = { senderId = 1, receiverId = 2, receiverHere = true, sent = 0, senderWaiting = false, receiverWaiting = false, receiverIssue = nil }
    for k, v in over or {} do
        f[k] = v
    end
    return f
end

t.test("the config is sane: an offer waits long enough to read and not forever, and a visit's gifts are capped", function()
    t.ok(C.OfferSeconds >= 20 and C.OfferSeconds <= 120, "long enough to answer, short enough not to pile up")
    t.ok(C.MaxPerVisit >= 1 and C.MaxPerVisit <= 20, "a cap that is a cap")
    t.ok(C.AskEvery > 0)
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

t.test("one offer at a time each way, and the receiver's own reason is passed on", function()
    t.ok(GiftRules.offerIssue(facts({ senderWaiting = true })) ~= nil, "yours is unanswered")
    t.ok(GiftRules.offerIssue(facts({ receiverWaiting = true })) ~= nil, "theirs is busy")
    t.eq(GiftRules.offerIssue(facts({ receiverIssue = "Their pets are full." })), "Their pets are full.")
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

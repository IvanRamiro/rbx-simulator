-- The beta gift (the owner, 2026-11-17: "GIVE A BETA TESTER AN OPTION TO CHOOSE WHAT KIND OF EXCLUSIVE THEY WANT / EITHER DREADWING,
-- MOONFOX, OR CRYSALITH", then "They just need one then it will not show up again, unless they purchase a gamepass / so we will give 1
-- FREE of their choice for beta tester"): while GameConfig.Beta is Active, every Roblox account may take ONE of the Exclusive Egg's
-- three beasts, free, once and never again. More of them come only from the Exclusive Egg (the Shop's EXCLUSIVE EGG tab).
-- The server (server/Rewards/BetaGiftService) keeps who has taken theirs in its own DataStore, not in the save; the window and
-- its round button are client/Rewards/BetaGiftController. The player's "BetaGift" attribute is "Open" while theirs is waiting.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local BetaGift = {
    -- the choices, in the window's order (the owner's)
    PetIds = { "EclipseDreadwing", "NineTailMoonfox", "Crysalith" },
    -- the claims: key "U_<UserId>" = { Status = "pending" | "done", PetId, At, Had, DoneAt } (In Studio the name starts with the
    -- StudioTestSave name, or "Studio", as the Hall of Records' stores do.)
    Store = "BetaRewardClaims",
    KeyPrefix = "U_",
}

for _, petId in BetaGift.PetIds do
    assert(GameConfig.Pets[petId], "BetaGift: unknown pet " .. petId)
end

function BetaGift.isChoice(petId)
    return typeof(petId) == "string" and table.find(BetaGift.PetIds, petId) ~= nil
end

-- whether the gift is offered (to anyone who hasn't taken theirs)
function BetaGift.active()
    local beta = GameConfig.Beta
    return typeof(beta) == "table" and beta.Active == true
end

function BetaGift.key(userId)
    return BetaGift.KeyPrefix .. tostring(userId)
end

return BetaGift

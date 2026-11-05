-- The rules of duplicate pets, shared so the windows always show what the server will do
-- (GameConfig.PetFusion). A pet here is a record of PetInventory.getSnapshot: { InstanceId, PetId, Equipped, Level, Locked }.
--
--   PetRules.level(pet)                   its level, 1 to MaxLevel (a fused pet carries the copies it took in)
--   PetRules.qiBonus(petId, level)        the Qi bonus a pet gives at that level
--   PetRules.findMaterial(pets, target)   the copy fusing `target` would use, or nil and why not
--   PetRules.spares(pets)                 the copies "sell spares" would sell
--   PetRules.refusal(reason)              what to tell the player about a findMaterial reason
--
-- Fusing and selling never touch a locked or equipped pet.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local PetRules = {}

local RULES = GameConfig.PetFusion
PetRules.MaxLevel = RULES.MaxLevel

function PetRules.level(pet)
    local level = pet and pet.Level
    if typeof(level) ~= "number" or level ~= level then
        return 1
    end
    return math.clamp(math.floor(level), 1, RULES.MaxLevel)
end

function PetRules.qiBonus(petId, level)
    local pet = GameConfig.Pets[petId]
    if not pet then
        return 0
    end
    return math.round(pet.QiBonus * (1 + RULES.QiPerLevel * ((level or 1) - 1)))
end

-- The cheapest copy that can go into `target`: the lowest level first, so a levelled copy is never spent while a plain one will do.
function PetRules.findMaterial(pets, target)
    local level = PetRules.level(target)
    if level >= RULES.MaxLevel then
        return nil, "MaxLevel"
    end
    local best, reason = nil, "NoSpare"
    for _, pet in pets do
        if pet.PetId == target.PetId and pet.InstanceId ~= target.InstanceId then
            if pet.Locked or pet.Equipped then
                reason = "Protected"
            elseif level + PetRules.level(pet) > RULES.MaxLevel then
                if reason == "NoSpare" then
                    reason = "TooHigh"
                end
            elseif not best or PetRules.level(pet) < PetRules.level(best) then
                best = pet
            end
        end
    end
    if best then
        return best
    end
    return nil, reason
end

local REFUSALS = {
    MaxLevel = "This pet has reached its highest level.",
    NoSpare = "You have no other copy of this pet to fuse.",
    Protected = "Your other copies are locked or equipped: free one first.",
    TooHigh = "That copy's level would take this pet past its highest level.",
}

function PetRules.refusal(reason)
    return REFUSALS[reason] or "That pet can't be fused."
end

-- Every copy past the one worth keeping, of the rarities GameConfig.PetFusion.SpareRarities names. A species
-- with a locked or equipped copy keeps that one; otherwise its highest level stays. Rarer pets are only ever sold one by one.
function PetRules.spares(pets)
    local kinds = {}
    for _, pet in pets do
        local info = GameConfig.Pets[pet.PetId]
        if info and RULES.SpareRarities[info.Rarity] then
            kinds[pet.PetId] = kinds[pet.PetId] or {}
            table.insert(kinds[pet.PetId], pet)
        end
    end
    local out = {}
    for _, copies in kinds do
        local keeper = nil
        for _, pet in copies do
            if pet.Locked or pet.Equipped then
                keeper = pet
                break
            end
            if not keeper or PetRules.level(pet) > PetRules.level(keeper) then
                keeper = pet
            end
        end
        for _, pet in copies do
            if pet ~= keeper and not pet.Locked and not pet.Equipped then
                table.insert(out, pet)
            end
        end
    end
    return out
end

return PetRules

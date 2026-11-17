-- The rules of duplicate pets, shared so the windows always show what the server will do
-- (GameConfig.PetFusion). A pet here is a record of PetInventory.getSnapshot: { InstanceId, PetId, Equipped, Level, Locked,
-- Size, Mutation, Worth, InPen, Paid }.
--
--   PetRules.level(pet)                   its level, 1 to MaxLevel (a fused pet carries the copies it took in)
--   PetRules.qiBonus(petId, level, size, mutation)  the Qi bonus a pet gives at that level, size and mutation
--   PetRules.findMaterial(pets, target)   the copy fusing `target` would use, or nil and why not
--   PetRules.spares(pets)                 the copies "sell spares" would sell
--   PetRules.refusal(reason)              what to tell the player about a findMaterial reason
--   PetRules.size(pet)                    its size name ("Small", "Normal", "Large", "Giant", "Colossal"); anything unknown is "Normal"
--   PetRules.sizeInfo(size)               that size's entry of PetRules.Sizes
--   PetRules.scaleFor(size, length)       how many times its Normal size a pet of that size is shown, for a species `length` studs
--                                         long (its longest side) at Normal (nil: the size's plain Scale)
--   PetRules.rollSize(random)             a size for a fresh hatch, at PetRules.Sizes' chances (the server rolls it)
--   PetRules.bigger(a, b)                 the larger of two sizes (a fusion keeps it)
--   PetRules.worth(pet)                   what its copies are worth together, in Normal copies (Shop.petValue: its sell value)
--   PetRules.mutation(pet)                its mutation's id (PetRules.Mutations), or nil for none or one this server doesn't know
--   PetRules.mutationInfo(mutation)       that mutation's entry (none: Value, Qi and Cap 1, Order 0)
--   PetRules.rollMutation(random)         a mutation for a fresh hatch, or nil (the server rolls it)
--   PetRules.better(a, b)                 the rarer of two mutations (a fusion keeps it)
--   PetRules.copyValue(size, mutation)    a fresh copy's worth: its size's Value times its mutation's
--   PetRules.displayName(petId, mutation) "Golden Moonfox"
--
-- Fusing and selling never touch a locked or equipped pet. A pet's record may also carry Size and InPen (in one of its
-- owner's pens): a pen pet is never picked as fusion material nor sold as a spare.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local PetRules = {}

local RULES = GameConfig.PetFusion

-- Hatch sizes (the owner, 2026-11-15: "Small, Normal, Large, and Giant", randomized at hatching with rarity chances). Each is rolled on
-- the server for every egg, the Exclusive Egg included, and saved on the pet. Scale: the model's size (rig, glows, effects, gait).
-- Value: what one copy of that size is worth, in Normal copies; a pet's Worth is its copies' Values added up as they are fused in
-- (PetInventory.fuse), so fusing neither makes nor loses Spirit Stones whatever the sizes (Shop.petValue sells base * Worth).
-- Qi: its Qi bonus multiplier (the pet's own size, whatever it took in). Chances add up to 100.
-- RevealHold: seconds the hatch reveal stays longer for it (HatchCeremony; the altar window waits as long).
-- Economy (measured in Play, 2026-11-15, with the Luck pass): the Wandering Merchant's discounted Void Rift Egg already sold back
-- for 0.949 of its price before sizes, so the brief's Values (Large 1.5, Giant 3: an average of 1.10 a hatch) would have made buying
-- it to sell its pets pay (1.044). The Values are lowered to average 1.018 a hatch: at most 0.966 of a Merchant egg's price and
-- 0.72 of an egg's reference price (Shop.marketEggPrice). The Merchant's pets are always Normal, so its MinPetMarkup holds. Re-check if any of these change.
-- Color: the size's colour in the windows (its pill, the hatch reveal's badge).
-- How big a size is shown (the owner, 2026-11-17: "the size of our pet is really small despite getting large pet / so I want you to
-- make something really huge or colossal"; at 1.35 and 1.8 a Giant Dawn Phoenix spanned 13 studs beside a 5-stud player): Scale,
-- times its Normal size; MinLength and MaxLength, the least and the most studs its longest side may span whatever the species (a tiny
-- Aqua Wisp still towers, a Divine drake doesn't fill the island); Least, the smallest Scale those may bring it to. Visual only: the
-- economy reads Value and Qi, never these.
PetRules.Sizes = {
    Small = { Order = 1, Scale = 0.75, Chance = 25, Value = 0.8, Qi = 0.9, RevealHold = 0, Color = Color3.fromRGB(150, 226, 255) },
    Normal = { Order = 2, Scale = 1, Chance = 56.6, Value = 1, Qi = 1, RevealHold = 0, Color = Color3.fromRGB(172, 170, 204) },
    Large = { Order = 3, Scale = 1.9, MinLength = 10, MaxLength = 24, Least = 1.5, Chance = 14, Value = 1.2, Qi = 1.15, RevealHold = 0.7,
        Color = Color3.fromRGB(255, 226, 140) },
    Giant = { Order = 4, Scale = 3.4, MinLength = 18, MaxLength = 36, Least = 2.4, Chance = 4, Value = 2, Qi = 1.4, RevealHold = 1.8,
        Color = Color3.fromRGB(255, 184, 48) },
    -- (the owner, 2026-11-17: "YES I AGREED FOR COLOSSAL PETS": a fifth size, its 0.4% taken from Normal; with it a hatch averages
    -- 1.026 in Values, so a Merchant egg still sells back under its price: about 0.974 before mutations, 0.992 with them)
    Colossal = { Order = 5, Scale = 5, MinLength = 30, MaxLength = 54, Least = 3.4, Chance = 0.4, Value = 3, Qi = 1.8, RevealHold = 2.6,
        Color = Color3.fromRGB(255, 92, 96) },
}
PetRules.SizeOrder = { "Small", "Normal", "Large", "Giant", "Colossal" }
do
    local total = 0
    for _, name in PetRules.SizeOrder do
        total += PetRules.Sizes[name].Chance
    end
    assert(math.abs(total - 100) < 1e-6, "PetRules.Sizes chances add up to " .. total .. ", not 100")
end

-- Hatch mutations (the owner, 2026-11-17: "SO LET'S ALSO ADD PET MUTATION, SO THERE PET WILL LOOK COOLER", then "let's combine
-- other roblox mutation + our own original set of mutation"; vault: Pet Mutations Design 2026-11-17). Rolled on the server at
-- every hatch apart from the beast and its size (no luck, no egg or realm changes it), saved on the pet as Mutation (nil: none).
-- Six classic kinds (our own looks: client Pets/MutationLook) and three of our own at the top. Chance: percent of all hatches.
-- Value: what a copy of it is worth, times its size's Value (it goes into Worth at the hatch, so fusing makes no stones). Qi: its Qi
-- bonus multiplier, times its size's. Cap: the Auction House's price cap multiplier (AuctionRules.priceCap). Hold: seconds more
-- the hatch reveal stays. Stamp: the hatch card's stamp. Color: its badge's colour. Economy: a hatch averages 1.019 in mutation
-- Values, so a Merchant egg sells back for about 0.992 of its price (under 1). Re-check if any of these change.
PetRules.Mutations = {
    Shiny = { Order = 1, Chance = 3, Value = 1.05, Qi = 1.05, Cap = 1.1, Hold = 0.4, Stamp = "SHINY!", Color = Color3.fromRGB(255, 246, 200) },
    Golden = { Order = 2, Chance = 2, Value = 1.15, Qi = 1.1, Cap = 1.2, Hold = 0.5, Stamp = "GOLDEN!", Color = Color3.fromRGB(255, 200, 60) },
    Jade = { Order = 3, Chance = 1.4, Value = 1.2, Qi = 1.12, Cap = 1.25, Hold = 0.6, Stamp = "JADE!", Color = Color3.fromRGB(70, 224, 140) },
    Frozen = { Order = 4, Chance = 1, Value = 1.25, Qi = 1.15, Cap = 1.3, Hold = 0.6, Stamp = "FROZEN!", Color = Color3.fromRGB(170, 228, 255) },
    Molten = { Order = 5, Chance = 0.8, Value = 1.3, Qi = 1.18, Cap = 1.35, Hold = 0.7, Stamp = "MOLTEN!", Color = Color3.fromRGB(255, 112, 32) },
    Shocked = { Order = 6, Chance = 0.5, Value = 1.4, Qi = 1.22, Cap = 1.45, Hold = 0.8, Stamp = "SHOCKED!", Color = Color3.fromRGB(96, 170, 255) },
    Rainbow = { Order = 7, Chance = 0.3, Value = 1.8, Qi = 1.35, Cap = 1.7, Hold = 1.1, Stamp = "RAINBOW!", Color = Color3.fromRGB(255, 120, 210),
        Grand = true },
    Celestial = { Order = 8, Chance = 0.12, Value = 2.2, Qi = 1.5, Cap = 1.85, Hold = 1.4, Stamp = "CELESTIAL!", Color = Color3.fromRGB(160, 150, 255),
        Grand = true },
    Void = { Order = 9, Chance = 0.05, Value = 2.8, Qi = 1.7, Cap = 2, Hold = 1.6, Stamp = "VOID!", Color = Color3.fromRGB(184, 92, 255),
        Grand = true },
}
PetRules.MutationOrder = { "Shiny", "Golden", "Jade", "Frozen", "Molten", "Shocked", "Rainbow", "Celestial", "Void" }
do
    local total = 0
    for index, name in PetRules.MutationOrder do
        local info = PetRules.Mutations[name]
        assert(info and info.Order == index, "PetRules.MutationOrder and PetRules.Mutations disagree at " .. name)
        total += info.Chance
    end
    assert(total < 100, "PetRules.Mutations chances add up to " .. total)
end
local NO_MUTATION = { Order = 0, Chance = 0, Value = 1, Qi = 1, Cap = 1, Hold = 0 }

-- its mutation's id, or nil (none, or one this server doesn't know: PlayerData refuses a newer save holding one)
function PetRules.mutation(pet)
    local mutation = if type(pet) == "table" then pet.Mutation else pet
    return if type(mutation) == "string" and PetRules.Mutations[mutation] then mutation else nil
end

-- its mutation's entry of PetRules.Mutations, or one that changes nothing (Value, Qi and Cap 1, Order 0) for none
function PetRules.mutationInfo(mutation)
    local id = PetRules.mutation(mutation)
    return if id then PetRules.Mutations[id] else NO_MUTATION
end

function PetRules.rollMutation(random)
    local roll = (if random then random:NextNumber() else math.random()) * 100
    for _, name in PetRules.MutationOrder do
        roll -= PetRules.Mutations[name].Chance
        if roll < 0 then
            return name
        end
    end
    return nil
end

-- the rarer of two mutations (a fusion keeps it), or nil if neither has one
function PetRules.better(a, b)
    return if PetRules.mutationInfo(b).Order > PetRules.mutationInfo(a).Order then PetRules.mutation(b) else PetRules.mutation(a)
end

-- a fresh copy's worth in Normal copies: its size's Value times its mutation's
function PetRules.copyValue(size, mutation)
    return PetRules.sizeInfo(size).Value * PetRules.mutationInfo(mutation).Value
end

-- "Golden Moonfox", "Moonfox"; a beast whose name already starts with the word keeps its name ("Golden Kirin", not "Golden Golden
-- Kirin": its badge says Golden)
function PetRules.displayName(petId, mutation)
    local pet = GameConfig.Pets[petId]
    local name = if pet then pet.DisplayName else tostring(petId)
    local id = PetRules.mutation(mutation)
    if not id or string.sub(name, 1, #id + 1) == id .. " " then
        return name
    end
    return id .. " " .. name
end

function PetRules.size(pet)
    local size = if type(pet) == "table" then pet.Size else pet
    return if type(size) == "string" and PetRules.Sizes[size] then size else "Normal"
end

function PetRules.sizeInfo(size)
    return PetRules.Sizes[PetRules.size(size)]
end

function PetRules.scaleFor(size, length)
    local info = PetRules.sizeInfo(size)
    local scale = info.Scale
    if type(length) == "number" and length > 0 then
        if info.MinLength then
            scale = math.max(scale, info.MinLength / length)
        end
        if info.MaxLength then
            scale = math.min(scale, info.MaxLength / length)
        end
    end
    return math.max(scale, info.Least or 0)
end

function PetRules.rollSize(random)
    local roll = (if random then random:NextNumber() else math.random()) * 100
    for _, name in PetRules.SizeOrder do
        roll -= PetRules.Sizes[name].Chance
        if roll < 0 then
            return name
        end
    end
    return "Normal"
end

function PetRules.bigger(a, b)
    return if PetRules.sizeInfo(b).Order > PetRules.sizeInfo(a).Order then PetRules.size(b) else PetRules.size(a)
end

-- Its copies' worth together, in Normal copies: its saved Worth, if it is one a pet of its level could have (each copy worth between
-- the smallest and the largest size's Value); otherwise as if every fused copy were Normal and it its own size.
-- (a copy is worth its size's Value times its mutation's: between the smallest size with none and the largest with the rarest)
local LEAST_VALUE, MOST_VALUE = math.huge, 0
local MOST_MUTATION = 1
for _, info in PetRules.Mutations do
    MOST_MUTATION = math.max(MOST_MUTATION, info.Value)
end
for _, info in PetRules.Sizes do
    LEAST_VALUE, MOST_VALUE = math.min(LEAST_VALUE, info.Value), math.max(MOST_VALUE, info.Value * MOST_MUTATION)
end
function PetRules.worth(pet)
    local level = PetRules.level(pet)
    local worth = type(pet) == "table" and pet.Worth
    if type(worth) == "number" and worth == worth and worth >= level * LEAST_VALUE - 1e-6 and worth <= level * MOST_VALUE + 1e-6 then
        return math.round(worth * 100) / 100
    end
    return level - 1 + PetRules.copyValue(pet, pet)
end

function PetRules.level(pet)
    local level = pet and pet.Level
    if typeof(level) ~= "number" or level ~= level then
        return 1
    end
    return math.clamp(math.floor(level), 1, RULES.MaxLevel)
end

-- its size (nil: Normal) and its mutation (nil: none) multiply the whole bonus
function PetRules.qiBonus(petId, level, size, mutation)
    local pet = GameConfig.Pets[petId]
    if not pet then
        return 0
    end
    return math.round(pet.QiBonus * (1 + RULES.QiPerLevel * ((level or 1) - 1)) * PetRules.sizeInfo(size).Qi
        * PetRules.mutationInfo(mutation).Qi)
end

-- The cheapest copy that can go into `target`: the lowest level first, so a levelled copy is never spent while a plain one will do;
-- of those, the smallest, so a big copy is spent last (the fused pet keeps the larger size of the two: PetInventory.fuse); then the
-- plainer, so a mutated copy is spent last too (the fused pet keeps the better mutation of the two).
local function cheaper(a, b)
    local la, lb = PetRules.level(a), PetRules.level(b)
    if la ~= lb then
        return la < lb
    end
    local sa, sb = PetRules.sizeInfo(a).Order, PetRules.sizeInfo(b).Order
    if sa ~= sb then
        return sa < sb
    end
    return PetRules.mutationInfo(a).Order < PetRules.mutationInfo(b).Order
end

function PetRules.findMaterial(pets, target)
    local level = PetRules.level(target)
    if level >= RULES.MaxLevel then
        return nil, "MaxLevel"
    end
    local best, reason = nil, "NoSpare"
    for _, pet in pets do
        if pet.PetId == target.PetId and pet.InstanceId ~= target.InstanceId then
            if pet.Locked or pet.Equipped or pet.InPen then
                reason = "Protected"
            elseif level + PetRules.level(pet) > RULES.MaxLevel then
                if reason == "NoSpare" then
                    reason = "TooHigh"
                end
            elseif not best or cheaper(pet, best) then
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
    Protected = "Your other copies are locked, equipped or in a pen: free one first.",
    TooHigh = "That copy's level would take this pet past its highest level.",
}

function PetRules.refusal(reason)
    return REFUSALS[reason] or "That pet can't be fused."
end

-- Every copy past the one worth keeping, of the rarities GameConfig.PetFusion.SpareRarities names. A species
-- with a locked, equipped or penned copy keeps that one; otherwise its highest level (then its largest) stays. Rarer pets are only
-- ever sold one by one, and so are Large, Giant and Colossal ones and mutated ones (a showpiece is never swept up with the duplicates).
local function protected(pet)
    return pet.Locked or pet.Equipped or pet.InPen
end

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
            if protected(pet) then
                keeper = pet
                break
            end
            if not keeper or cheaper(keeper, pet) then
                keeper = pet
            end
        end
        for _, pet in copies do
            if pet ~= keeper and not protected(pet) and PetRules.sizeInfo(pet).Order <= PetRules.Sizes.Normal.Order
                and not PetRules.mutation(pet) then
                table.insert(out, pet)
            end
        end
    end
    return out
end

return PetRules

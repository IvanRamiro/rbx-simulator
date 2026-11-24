-- PetRules: hatch sizes and mutations (the odds the owner approved), names, worth and scale. The server rolls with these; the windows show them.
local t = require("@env/t")
local Random = require("@env/globals").Random -- (the modules get it from the header; a spec asks for it)
local GameConfig = require("@shared/GameConfig")
local PetRules = require("@shared/PetRules")

local function frequencies(draw, n)
    local counts = {}
    for _ = 1, n do
        local key = draw() or "none"
        counts[key] = (counts[key] or 0) + 1
    end
    return counts
end

t.test("size chances add up to 100 and the order table lists every size once", function()
    local total = 0
    for _, name in PetRules.SizeOrder do
        total += PetRules.Sizes[name].Chance
        t.eq(PetRules.Sizes[name].Order, table.find(PetRules.SizeOrder, name), name .. " order")
    end
    t.near(total, 100, 1e-9)
    t.eq(#PetRules.SizeOrder, 5)
end)

t.test("rollSize follows the chances over many hatches", function()
    local random = Random.new(2026)
    local n = 60000
    local counts = frequencies(function()
        return PetRules.rollSize(random)
    end, n)
    for _, name in PetRules.SizeOrder do
        local share = (counts[name] or 0) / n * 100
        t.near(share, PetRules.Sizes[name].Chance, 1.0, name .. " share of hatches")
    end
end)

t.test("rollMutation: about nine in a hundred hatches mutate, in the stated proportions", function()
    local random = Random.new(7)
    local n = 200000
    local counts = frequencies(function()
        return PetRules.rollMutation(random, 1, 1)
    end, n)
    local expectedMutated = 0
    for _, info in PetRules.Mutations do
        expectedMutated += info.Chance
    end
    t.near(100 - (counts.none or 0) / n * 100, expectedMutated, 0.4, "share of hatches that mutate")
    t.near((counts.Shiny or 0) / n * 100, PetRules.Mutations.Shiny.Chance, 0.3, "Shiny share")
    t.ok((counts.Void or 0) < (counts.Shiny or 0), "Void must be rarer than Shiny")
end)

t.test("the Luck pass multiplies only the three Grand mutations", function()
    t.near(PetRules.mutationChance("Rainbow", 1), 0.3, 1e-9)
    t.near(PetRules.mutationChance("Rainbow", 2), 0.6, 1e-9)
    t.near(PetRules.mutationChance("Celestial", 2), 0.24, 1e-9)
    t.near(PetRules.mutationChance("Void", 2), 0.1, 1e-9)
    t.near(PetRules.mutationChance("Shiny", 2), 3, 1e-9, "a classic mutation ignores luck")
    t.near(PetRules.mutationChance("Rainbow", 0.5), 0.3, 1e-9, "luck below 1 never lowers a chance")
    t.near(PetRules.mutationChance("Rainbow", "lots"), 0.3, 1e-9, "a bad luck value is ignored")
    t.near(PetRules.mutationChance("Shiny", 1, 2), 6, 1e-9, "a title's boost multiplies any mutation")
    t.eq(PetRules.mutationChance("Nonsense", 5, 5), 0)
end)

t.test("mutations: order table agrees, and a roll never hands out an unknown one", function()
    for index, name in PetRules.MutationOrder do
        t.eq(PetRules.Mutations[name].Order, index)
    end
    local random = Random.new(99)
    for _ = 1, 5000 do
        local m = PetRules.rollMutation(random, 3, 2)
        t.ok(m == nil or PetRules.Mutations[m] ~= nil)
    end
end)

t.test("mutation and size accept a pet record or a bare id, and refuse junk", function()
    t.eq(PetRules.mutation({ Mutation = "Golden" }), "Golden")
    t.eq(PetRules.mutation("Golden"), "Golden")
    t.eq(PetRules.mutation({ Mutation = "FromTheFuture" }), nil, "an unknown mutation (a newer save) is none")
    t.eq(PetRules.mutation(nil), nil)
    t.eq(PetRules.size({ Size = "Giant" }), "Giant")
    t.eq(PetRules.size({ Size = "Humongous" }), "Normal")
    t.eq(PetRules.size(nil), "Normal")
    t.eq(PetRules.mutationInfo(nil).Value, 1, "no mutation changes nothing")
end)

t.test("better and bigger keep the rarer and the larger", function()
    t.eq(PetRules.better("Shiny", "Void"), "Void")
    t.eq(PetRules.better("Void", "Shiny"), "Void")
    t.eq(PetRules.better(nil, "Jade"), "Jade")
    t.eq(PetRules.better("Jade", nil), "Jade")
    t.eq(PetRules.better(nil, nil), nil)
    t.eq(PetRules.bigger("Small", "Giant"), "Giant")
    t.eq(PetRules.bigger("Colossal", "Large"), "Colossal")
    t.eq(PetRules.bigger(nil, "Small"), "Normal", "an unknown size counts as Normal, which is bigger than Small")
end)

t.test("copyValue is the size's value times the mutation's", function()
    t.near(PetRules.copyValue("Normal", nil), 1, 1e-9)
    t.near(PetRules.copyValue("Giant", "Golden"), 2 * 1.15, 1e-9)
    t.near(PetRules.copyValue("Small", "Void"), 0.8 * 2.8, 1e-9)
end)

t.test("display names: the mutation goes in front, unless the name already starts with it", function()
    local volt = GameConfig.Pets.VoltFox.DisplayName
    t.eq(PetRules.displayName("VoltFox", nil), volt)
    t.eq(PetRules.displayName("VoltFox", "Golden"), "Golden " .. volt)
    t.eq(PetRules.displayName("GoldenKirin", "Golden"), GameConfig.Pets.GoldenKirin.DisplayName, "no 'Golden Golden Kirin'")
    t.eq(PetRules.displayName("NoSuchPet", nil), "NoSuchPet", "an unknown pet shows its id")
end)

t.test("scaleFor clamps a size's studs to its length range", function()
    t.near(PetRules.scaleFor("Normal", 5), 1, 1e-9)
    t.near(PetRules.scaleFor("Small", 5), 0.75, 1e-9)
    t.near(PetRules.scaleFor("Giant", 5), 3.6, 1e-9, "a 5-stud pet at least 18 studs: 18 / 5")
    t.near(PetRules.scaleFor("Giant", 2), 9, 1e-9, "a 2-stud pet at least 18 studs: 18 / 2")
    t.near(PetRules.scaleFor("Giant", 100), 2.4, 1e-9, "a huge pet never goes below the size's least scale")
    t.near(PetRules.scaleFor("Large", nil), 1.9, 1e-9, "no length: the size's own scale")
end)

t.test("level and worth", function()
    t.eq(PetRules.level(nil), 1)
    t.eq(PetRules.level({ Level = 4 }), 4)
    t.eq(PetRules.level({ Level = 0 / 0 }), 1, "NaN is level 1")
    t.eq(PetRules.level({ Level = "9" }), 1, "a string is level 1")
    t.near(PetRules.worth({ Level = 1 }), 1, 1e-9, "a fresh Normal pet is worth one copy")
    t.near(PetRules.worth({ Level = 1, Size = "Giant", Mutation = "Golden" }), 2.3, 1e-9)
    t.near(PetRules.worth({ Level = 3, Worth = 3.5 }), 3.5, 1e-9, "a saved worth in range is kept")
    t.near(PetRules.worth({ Level = 3, Worth = 9999 }), 2 + 1, 1e-9, "a worth no pet of this level could have is recomputed")
    t.near(PetRules.worth({ Level = 3, Worth = 0 / 0 }), 3, 1e-9, "NaN worth is recomputed")
end)

t.test("bestPicks: the most Qi first, no more than the slots, equal pets in a stable order, an unknown pet never", function()
    local strongest, weakest
    for petId, def in GameConfig.Pets do
        if def.QiBonus > 0 then
            if not strongest or def.QiBonus > GameConfig.Pets[strongest].QiBonus then
                strongest = petId
            end
            if not weakest or def.QiBonus < GameConfig.Pets[weakest].QiBonus then
                weakest = petId
            end
        end
    end
    t.ok(GameConfig.Pets[strongest].QiBonus > GameConfig.Pets[weakest].QiBonus, "the config has a strongest and a weaker pet")
    local owned = {
        { InstanceId = "w1", PetId = weakest },
        { InstanceId = "s1", PetId = strongest },
        { InstanceId = "s3", PetId = strongest, Level = 3 },
        { InstanceId = "s2", PetId = strongest },
        { InstanceId = "x1", PetId = "NoSuchPet" },
    }
    local picks = PetRules.bestPicks(owned, 3)
    t.eq(picks[1], "s3", "a levelled copy gives more, so it goes first")
    t.eq(picks[2], "s1", "equal copies keep a stable order by id")
    t.eq(picks[3], "s2")
    t.eq(#PetRules.bestPicks(owned, 2), 2, "no more than the slots")
    local all = PetRules.bestPicks(owned, 10)
    t.eq(#all, 4, "every pet that gives Qi, and not the unknown one")
    t.eq(all[4], "w1", "the weakest last")
    t.eq(#PetRules.bestPicks(owned, 0), 0, "no slots, no picks")
    t.eq(#PetRules.bestPicks({}, 5), 0, "no pets, no picks")
end)

t.finish("pets")

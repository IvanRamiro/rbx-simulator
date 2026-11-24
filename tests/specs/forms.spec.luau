-- Combat forms (shared/FormRules), by weapon family: every sword shares the sword forms and every spear the spear forms (bare hands have their own).
-- The chain data is complete, every form keeps the weapon's own damage per second (the balance rule that keeps guardian fights and the egg heist at
-- their pace), the chain advances and lapses as designed, forms unlock by realm, and the combo counter counts.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local FormRules = require("@shared/FormRules")

-- the base strike of each family, as Combat.strikeOf gives it for the first realm's weapon (the Palm from GameConfig.Combat)
local function baseOf(family)
    if family == "Palm" then
        local p = GameConfig.Combat.Palm
        return { Damage = p.Damage, Range = p.Range, Arc = p.Arc, Cooldown = p.Cooldown }
    end
    local kind = GameConfig.WeaponKinds[family]
    return { Damage = 16 * kind.DamageScale, Range = kind.Range, Arc = kind.Arc, Cooldown = kind.Cooldown }
end

t.test("every weapon kind, and bare hands, has forms and a default form for everyone", function()
    for kind in GameConfig.WeaponKinds do
        t.ok(FormRules.Families[kind] ~= nil and #FormRules.Families[kind] >= 1, "no forms for the " .. kind)
    end
    t.ok(FormRules.Families.Palm ~= nil, "bare hands have no form")
    for family, ids in FormRules.Families do
        t.eq(FormRules.Forms[ids[1]].UnlockRealm, 1, family .. "'s first form must be there from the start")
        local realm = 0
        for _, id in ids do
            t.eq(FormRules.familyOf(id), family)
            t.ok(FormRules.Forms[id].UnlockRealm >= realm, family .. " forms must unlock in order")
            realm = FormRules.Forms[id].UnlockRealm
        end
    end
    t.eq(#FormRules.Families.Sword, 3)
    t.eq(#FormRules.Families.Spear, 3)
end)

t.test("every form is complete and its words are plain", function()
    local names = {}
    for family, ids in FormRules.Families do
        for _, id in ids do
            local form = FormRules.Forms[id]
            t.ok(form.Id == id and form.Family == family, id .. " Id or Family")
            t.ok(#form.Name > 0 and #form.Identity > 0, id .. " has no name or identity")
            t.ok(#form.Chain >= 3 and #form.Chain <= 6, id .. " chain length")
            for index, step in form.Chain do
                t.ok(step.Name:match("^[%a' ]+$") ~= nil, id .. " step " .. index .. " name must be plain letters")
                t.falsy(names[step.Name], "two strikes share the name " .. step.Name)
                names[step.Name] = true
                t.ok(step.Dmg > 0 and step.Cd > 0 and step.Range > 0 and step.Arc > 0, id .. " step " .. index .. " numbers")
                t.ok(step.Reaction == "Light" or step.Reaction == "Heavy" or step.Reaction == "Launch", id .. " reaction")
                t.ok(index == #form.Chain or step.Reaction ~= "Launch", id .. ": only the finisher launches")
            end
            local last = form.Chain[#form.Chain]
            t.eq(last.Reaction, "Launch", id .. " finisher must launch")
            for index = 1, #form.Chain - 1 do
                t.ok(form.Chain[index].Dmg < last.Dmg, id .. ": the finisher must hit hardest")
            end
        end
    end
end)

t.test("each form deals the weapon's own damage per second (the balance rule)", function()
    for _, ids in FormRules.Families do
        for _, id in ids do
            t.near(FormRules.dps(id), 1, FormRules.DPS_BAND, id .. " damage per second against the weapon's own")
        end
    end
end)

t.test("run in full on a real weapon of its family, each form deals that weapon's damage over its time", function()
    for family, ids in FormRules.Families do
        local base = baseOf(family)
        local own = base.Damage / base.Cooldown
        for _, id in ids do
            local damage, time = 0, 0
            for step = 1, #FormRules.Forms[id].Chain do
                local s = FormRules.strike(id, step, base)
                damage += s.Damage
                time += s.Cooldown
                t.eq(s.Family, family)
            end
            t.near(damage / time, own, own * FormRules.DPS_BAND, id)
        end
    end
end)

t.test("a spear's sweep keeps today's slash reach (13 studs, 85 degrees) and no strike reaches behind", function()
    local spear = baseOf("Spear")
    local sweep = FormRules.strike("Lancer", 3, spear)
    t.near(sweep.Range, 13, 0.1, "the Lancer's sweep range")
    t.near(sweep.Arc, 85, 1.5, "the Lancer's sweep arc")
    for _, ids in FormRules.Families do
        for _, id in ids do
            for step = 1, #FormRules.Forms[id].Chain do
                for _, base in { baseOf("Sword"), baseOf("Spear"), baseOf("Palm") } do
                    local s = FormRules.strike(id, step, base)
                    t.ok(s.Arc <= FormRules.MAX_ARC and s.Range >= 3, id .. " step " .. step .. " reach")
                end
            end
        end
    end
end)

t.test("unlocking by realm, and which form a player fights with", function()
    t.ok(FormRules.unlocked("Crescent", 1))
    t.falsy(FormRules.unlocked("Gale", 2))
    t.ok(FormRules.unlocked("Gale", 3))
    t.falsy(FormRules.unlocked("Mountain", 5))
    t.ok(FormRules.unlocked("Mountain", 12))
    t.falsy(FormRules.unlocked("Mountain", nil), "no realm means locked")
    t.falsy(FormRules.unlocked("Nope", 12))
    t.falsy(FormRules.unlocked(42, 12))
    t.eq(FormRules.familyOf("Tiger"), "Spear")
    t.eq(FormRules.familyOf("Nope"), nil)
    -- the chosen form is used when it is this weapon's and unlocked; otherwise the family's first
    t.eq(FormRules.resolve("Sword", "Gale", 3), "Gale")
    t.eq(FormRules.resolve("Sword", "Gale", 2), "Crescent", "still locked")
    t.eq(FormRules.resolve("Sword", "Tiger", 12), "Crescent", "a spear form on a sword")
    t.eq(FormRules.resolve("Spear", "Tiger", 12), "Tiger")
    t.eq(FormRules.resolve("Spear", nil, 12), "Lancer")
    t.eq(FormRules.resolve("Palm", "Gale", 12), "Fist")
    t.eq(FormRules.resolve("Hammer", "Gale", 12), nil, "an unknown family")
end)

t.test("the chain advances inside the window, wraps, and starts again outside it", function()
    local cd = 0.55
    local last = nil
    local steps = {}
    local now = 100
    for _ = 1, 8 do
        local step = FormRules.stepOf("Gale", last, now, cd)
        table.insert(steps, step)
        last = { Form = "Gale", Step = step, At = now }
        now += cd * FormRules.Forms.Gale.Chain[step].Cd -- the very next strike the moment the cooldown is up
    end
    t.eq(table.concat(steps, ","), "1,2,3,4,5,1,2,3", "a Gale chain of five wraps round")
    local late = { Form = "Mountain", Step = 1, At = 50 }
    t.eq(FormRules.stepOf("Mountain", late, 50 + cd * 1.0 + FormRules.GRACE + 0.01, cd), 1, "a late strike starts again")
    t.eq(FormRules.stepOf("Mountain", late, 50 + cd * 1.0 + FormRules.GRACE - 0.01, cd), 2, "just inside the grace continues")
    t.eq(FormRules.stepOf("Crescent", { Form = "Gale", Step = 2, At = 50 }, 50.5, cd), 1, "a changed form starts its own chain")
    t.eq(FormRules.stepOf("Nope", late, 51, cd), 1)
    t.eq(FormRules.stepOf("Mountain", { Form = "Mountain", Step = 99, At = 50 }, 50.5, cd), 1)
    t.eq(FormRules.stepOf("Mountain", { Form = "Mountain", Step = 1, At = 60 }, 50, cd), 1, "a clock that went backwards")
    t.eq(FormRules.stepOf("Mountain", { Form = "Mountain", Step = 1, At = "x" }, 50, cd), 1)
end)

t.test("a strike's numbers come from the weapon's and the step's", function()
    local weapon = { Damage = 16, Range = 12, Arc = 80, Cooldown = 0.55 }
    local s = FormRules.strike("Mountain", 3, weapon)
    t.eq(s.Name, "Mountain Fall")
    t.ok(s.Finisher)
    t.near(s.Damage, 16 * 2.8, 1e-9)
    t.near(s.Cooldown, 0.55 * 2.6, 1e-9)
    t.near(s.Range, 12 * 1.1, 1e-9)
    t.near(s.Arc, 80 * 1.2, 1e-9)
    t.falsy(FormRules.strike("Mountain", 1, weapon).Finisher)
    t.eq(FormRules.strike("Mountain", 4, weapon), nil, "no fourth strike")
    t.eq(FormRules.strike("Nope", 1, weapon), nil)
    t.eq(FormRules.strike("Gale", 5, { Damage = 1, Range = 12, Arc = 150, Cooldown = 1 }).Arc, FormRules.MAX_ARC)
    t.eq(FormRules.strike("Gale", 1, { Damage = 1, Range = 2, Arc = 80, Cooldown = 1 }).Range, 3)
end)

t.test("plan: the strike a player makes now, chain and all", function()
    local base = { Damage = 16, Range = 12, Arc = 80, Cooldown = 0.55 }
    local last, now, names = nil, 10, {}
    for _ = 1, 4 do
        local s = FormRules.plan("Sword", "Crescent", 1, base, last, now)
        table.insert(names, s.Name)
        last = { Form = s.Form, Step = s.Step, At = now }
        now += s.Cooldown
    end
    t.eq(table.concat(names, ","), "Rising Cut,Falling Cut,Heaven Splitter,Rising Cut")
    -- a form chosen but still locked is not used: the family's first is
    t.eq(FormRules.plan("Sword", "Mountain", 2, base, nil, 0).Form, "Crescent")
    -- changing form in the middle of a chain starts the new one at its first strike
    local mid = { Form = "Crescent", Step = 2, At = 10 }
    local gale = FormRules.plan("Sword", "Gale", 3, base, mid, 10.4)
    t.eq(gale.Form, "Gale")
    t.eq(gale.Step, 1)
    -- a spear form on a sword is ignored; an unknown family has no strike
    t.eq(FormRules.plan("Sword", "Tiger", 12, base, nil, 0).Form, "Crescent")
    t.eq(FormRules.plan("Hammer", "Gale", 12, base, nil, 0), nil)
    -- a different realm of the same weapon gives the same chain: forms follow the weapon's family, not its tier
    local a = FormRules.plan("Spear", "Swallow", 6, { Damage = 16, Range = 18, Arc = 35, Cooldown = 0.85 }, nil, 0)
    local b = FormRules.plan("Spear", "Swallow", 6, { Damage = 69, Range = 18, Arc = 35, Cooldown = 0.85 }, nil, 0)
    t.eq(a.Name, b.Name)
    t.near(b.Damage / a.Damage, 69 / 16, 1e-9, "damage follows the weapon's tier")
end)

t.test("the combo counter adds inside the window and starts again outside it", function()
    local c = FormRules.countHit(nil, 10)
    t.eq(c.Hits, 1)
    c = FormRules.countHit(c, 10.5)
    c = FormRules.countHit(c, 12.4)
    t.eq(c.Hits, 3)
    t.eq(FormRules.countHit(c, 12.4 + FormRules.Counter.WINDOW + 0.01).Hits, 1, "a gap starts it again")
    t.eq(FormRules.countHit(c, 12.4 + FormRules.Counter.WINDOW - 0.01).Hits, 4, "just inside the window still counts")
    t.eq(FormRules.countHit({ Hits = 5, At = 20 }, 10).Hits, 1, "a clock that went backwards")
    t.eq(FormRules.countHit({ Hits = 5, At = "x" }, 10).Hits, 1)
end)

t.test("the counter survives the slowest finisher's recovery, so a heavy form keeps its combo", function()
    local slowest = 0
    for family, ids in FormRules.Families do
        local base = family == "Sword" and 0.55 or family == "Spear" and 0.85 or 0.45
        for _, id in ids do
            local chain = FormRules.Forms[id].Chain
            slowest = math.max(slowest, base * chain[#chain].Cd)
        end
    end
    t.ok(FormRules.Counter.WINDOW > slowest + 0.4, "a window of " .. FormRules.Counter.WINDOW .. " s is not clear of a finisher recovery of " .. slowest .. " s")
end)

t.test("combo tiers", function()
    t.eq(FormRules.tierOf(1), nil)
    t.eq(FormRules.tierOf(4), nil)
    t.eq(FormRules.tierOf(5), "Nice")
    t.eq(FormRules.tierOf(19), "Great")
    t.eq(FormRules.tierOf(20), "Amazing")
    t.eq(FormRules.tierOf(999), "Legendary")
end)

t.test("saved form choices are cleaned: only a form of its own family survives", function()
    local clean = FormRules.sanitizeChoices({ Sword = "Gale", Spear = "Tiger", Palm = "Fist" })
    t.eq(clean.Sword, "Gale")
    t.eq(clean.Spear, "Tiger")
    t.eq(clean.Palm, "Fist")
    local mixed = FormRules.sanitizeChoices({ Sword = "Tiger", Spear = "Gale", Palm = 5, Bow = "Gale" })
    t.eq(mixed.Sword, nil, "a spear form under Sword")
    t.eq(mixed.Spear, nil, "a sword form under Spear")
    t.eq(mixed.Palm, nil, "a number under Palm")
    t.eq(mixed.Bow, nil, "a family that does not exist")
    t.eq(next(FormRules.sanitizeChoices(nil)), nil, "nil")
    t.eq(next(FormRules.sanitizeChoices("Gale")), nil, "a string")
    t.eq(next(FormRules.sanitizeChoices({ Sword = { "Gale" }, Spear = true })), nil, "a table and a boolean")
    t.eq(FormRules.sanitizeChoices({ Sword = "Gale" }).Sword, "Gale", "a form not yet unlocked is kept (unlocking is checked where it is used)")
end)

t.test("the choice survives a round trip through the attributes the server keeps it in", function()
    local saved = { Sword = "Mountain", Spear = "Swallow" }
    local attrs = {}
    for family, id in FormRules.sanitizeChoices(saved) do
        attrs["Form" .. family] = id -- (CombatService restores them on join)
    end
    t.eq(FormRules.resolve("Sword", attrs.FormSword, 6), "Mountain")
    t.eq(FormRules.resolve("Spear", attrs.FormSpear, 3), "Swallow")
    t.eq(FormRules.resolve("Sword", attrs.FormSword, 2), "Crescent", "a form the realm has not unlocked falls back to the first")
end)

t.finish("forms")

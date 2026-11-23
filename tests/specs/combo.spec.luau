-- ComboRules: which strike of its weapon's chain a strike is (the server counts it for every client), and when a chain starts over.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local ComboRules = require("@shared/ComboRules")

local function strike(weapon, step, at)
    return { Weapon = weapon, Step = step, At = at }
end

t.test("a first strike, or one after a pause, is step 1", function()
    t.eq(ComboRules.step("Sword", nil, 100), 1)
    t.eq(ComboRules.step("Sword", strike("Sword", 1, 90), 100), 1, "10 s later: a new chain")
    t.eq(ComboRules.step("Spear", strike("Spear", 1, 99), 100), 2, "inside the spear window")
    t.eq(ComboRules.step("Palm", nil, 5), 1)
end)

t.test("the sword's chain runs 1, 2, 3 and starts over", function()
    local last, now = nil, 100
    local got = {}
    for _ = 1, 7 do
        local step = ComboRules.step("Sword", last, now)
        table.insert(got, step)
        last = strike("Sword", step, now)
        now += GameConfig.WeaponKinds.Sword.Cooldown
    end
    t.eq(table.concat(got, ","), "1,2,3,1,2,3,1")
end)

t.test("the spear's chain is a thrust then a slash, the fists' a right then a left", function()
    local last, now, got = nil, 10, {}
    for _ = 1, 5 do
        local step = ComboRules.step("Spear", last, now)
        table.insert(got, step)
        last, now = strike("Spear", step, now), now + 0.85
    end
    t.eq(table.concat(got, ","), "1,2,1,2,1")
    last, now, got = nil, 10, {}
    for _ = 1, 5 do
        local step = ComboRules.step("Palm", last, now)
        table.insert(got, step)
        last, now = strike("Palm", step, now), now + 0.45
    end
    t.eq(table.concat(got, ","), "1,2,1,2,1")
end)

t.test("a strike just inside the window continues the chain, one just outside does not", function()
    local window = GameConfig.WeaponKinds.Sword.ComboWindow
    t.eq(ComboRules.step("Sword", strike("Sword", 1, 50), 50 + window - 0.01), 2)
    t.eq(ComboRules.step("Sword", strike("Sword", 2, 50), 50 + window), 1)
    t.eq(ComboRules.step("Sword", strike("Sword", 2, 50), 50 + window + 5), 1)
end)

t.test("changing weapon starts a new chain", function()
    t.eq(ComboRules.step("Spear", strike("Sword", 2, 99.9), 100), 1)
    t.eq(ComboRules.step("Sword", strike("Palm", 1, 99.9), 100), 1)
    t.eq(ComboRules.step("Palm", strike("Spear", 1, 99.9), 100), 1)
end)

t.test("a clock that went backwards, or a bad record, never continues a chain", function()
    t.eq(ComboRules.step("Sword", strike("Sword", 1, 200), 100), 1)
    t.eq(ComboRules.step("Sword", { Weapon = "Sword", Step = 1, At = "now" }, 100), 1)
    t.eq(ComboRules.step("Sword", {}, 100), 1)
end)

t.test("the finisher is the last strike of each chain", function()
    t.ok(ComboRules.isFinisher("Sword", 3))
    t.falsy(ComboRules.isFinisher("Sword", 2))
    t.ok(ComboRules.isFinisher("Spear", 2))
    t.falsy(ComboRules.isFinisher("Spear", 1))
    t.ok(ComboRules.isFinisher("Palm", 2))
    t.falsy(ComboRules.isFinisher("Staff", 1), "an unknown weapon has no chain")
end)

t.test("every weapon kind's window is a sensible time, and the fists' matches the client", function()
    for weapon in ComboRules.Steps do
        local window = ComboRules.window(weapon)
        t.ok(window >= 0.6 and window <= 3, weapon .. " window " .. tostring(window))
        t.ok(ComboRules.Steps[weapon] >= 2 and ComboRules.Steps[weapon] <= 4)
    end
    t.eq(ComboRules.window("Staff"), 0)
end)

t.finish("combo")

-- How a guardian answers being fought (shared/ReactRules, GameConfig.GuardianReact): stagger, guard, dodge, shove.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local ReactRules = require("@shared/ReactRules")

local C = GameConfig.GuardianReact

t.test("the config is sane: a combo needs several strikes, a guard lets only a share through, a reaction has a cooldown", function()
    t.ok(C.HitsToReact >= 3, "a few strikes are free")
    t.ok(C.Pass > 0 and C.Pass < 1, "a guard lets some through, never all or none")
    t.ok(C.Cooldown > C.Raise + C.Guard, "a guard ends before the next can begin")
    t.ok(C.Raise >= 0.3, "the guard is telegraphed long enough to see")
    t.ok(C.Stagger > 0 and C.Stagger < 1.5 and C.StaggerCooldown >= C.Stagger, "a stagger delays, never locks")
    t.ok(C.DodgeTime < C.Cooldown and C.DodgeStep > 0)
    t.ok(C.Shove > 0 and C.ShoveTime > 0)
end)

t.test("strikes are counted inside the window and old ones fall out", function()
    local hits = {}
    for i = 1, 4 do
        hits = ReactRules.record(hits, i * 0.3)
    end
    t.eq(#hits, 4)
    hits = ReactRules.record(hits, 1.2 + C.HitWindow + 0.1)
    t.eq(#hits, 1, "everything older than the window is gone")
    t.eq(#ReactRules.record({ 5 }, 3), 1, "a time in the future is not counted")
end)

t.test("a guardian has had enough after HitsToReact strikes, if ready and not already guarding", function()
    local hits = {}
    for i = 1, C.HitsToReact - 1 do
        hits = ReactRules.record(hits, i * 0.3)
    end
    t.falsy(ReactRules.due(hits, 2, 0, false), "one short")
    hits = ReactRules.record(hits, 2)
    t.ok(ReactRules.due(hits, 2, 0, false))
    t.falsy(ReactRules.due(hits, 2, 5, false), "its reaction is on cooldown")
    t.falsy(ReactRules.due(hits, 2, 0, true), "already guarding")
end)

t.test("a guard is up only once its telegraph is over, and down again after", function()
    t.falsy(ReactRules.blocking(1.0, 1.45, 2.45), "still being raised")
    t.ok(ReactRules.blocking(2.0, 1.45, 2.45))
    t.falsy(ReactRules.blocking(2.5, 1.45, 2.45), "down again")
end)

t.test("a finisher staggers and shoves, a heavy blow delays a little, a light one does nothing, and a guard is never staggered", function()
    local delay, shove = ReactRules.stagger("Launch", false, 10, 0)
    t.eq(delay, C.Stagger)
    t.ok(shove)
    delay, shove = ReactRules.stagger("Launch", false, 10, 12)
    t.eq(delay, 0, "the stagger is on cooldown")
    t.falsy(shove)
    delay, shove = ReactRules.stagger("Heavy", false, 10, 12)
    t.eq(delay, C.HeavyStagger)
    t.falsy(shove)
    t.eq((ReactRules.stagger("Light", false, 10, 0)), 0)
    t.eq((ReactRules.stagger("Launch", true, 10, 0)), 0, "guarding: not staggered")
    t.eq((ReactRules.stagger(nil, false, 10, 0)), 0)
end)

t.test("a shove goes out and back along a half sine and is over after its time", function()
    local shove = { Distance = 4, Start = 10, Time = 0.4 }
    t.eq(ReactRules.shoveAmount(nil, 10), nil)
    t.near(ReactRules.shoveAmount(shove, 10), 0, 1e-9)
    t.near(ReactRules.shoveAmount(shove, 10.2), 4, 1e-9, "the furthest at the middle")
    t.ok(ReactRules.shoveAmount(shove, 10.1) > 0 and ReactRules.shoveAmount(shove, 10.1) < 4)
    t.eq(ReactRules.shoveAmount(shove, 10.4), nil, "over")
    t.eq(ReactRules.shoveAmount(shove, 9), nil, "not begun")
end)

t.finish("reactrules")

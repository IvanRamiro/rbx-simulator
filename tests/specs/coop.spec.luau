-- Fighting and stealing together (shared/CoopRules, GameConfig.EggTheft.Coop): who is a helper, what they are paid, when one may carry a dropped egg on.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local CoopRules = require("@shared/CoopRules")

local C = GameConfig.EggTheft.Coop

local function who(id)
    return { UserId = id, Name = "P" .. id }
end

t.test("the config is sane: a helper's share is a real part of the egg, never all of it, and the relay waits a moment", function()
    t.ok(C.StonesShare > 0 and C.StonesShare < 1, "a share, not the whole egg")
    t.ok(C.MaxHelpers >= 1 and C.MaxHelpers <= 6)
    t.ok(C.RelayAfter >= 2 and C.RelayAfter < GameConfig.Guardians.StoneLion.DropTime, "the thief has a moment, and the helper's chance comes before the egg goes home")
    -- (all of them are paid together: the thief keeps the egg itself, so the helpers' shares can't swallow the stones)
    t.ok(C.StonesShare * C.MaxHelpers <= 1.5, "three helpers can't be paid far more than the thief")
end)

t.test("a helper dealt the share, is still here, and is not the thief", function()
    local a, b, c, thief = who(1), who(2), who(3), who(4)
    local damageBy = { [a] = 500, [b] = 80, [c] = 300, [thief] = 900 }
    local list = CoopRules.helpers(damageBy, 100, thief, nil)
    t.eq(#list, 2, "b dealt too little, the thief is not a helper")
    t.eq(list[1], a, "the biggest share first")
    t.eq(list[2], c)
    local gone = CoopRules.helpers(damageBy, 100, thief, function(p)
        return p ~= a
    end)
    t.eq(#gone, 1, "someone who left isn't paid")
    t.eq(gone[1], c)
end)

t.test("no more than MaxHelpers are paid, the biggest first, and a tie breaks the same way every time", function()
    local damageBy = {}
    for i = 1, 8 do
        damageBy[who(i)] = 1000 - i * 10
    end
    local list = CoopRules.helpers(damageBy, 1, nil, nil)
    t.eq(#list, C.MaxHelpers)
    t.ok(damageBy[list[1]] >= damageBy[list[#list]], "ordered")
    local tied = { [who(7)] = 50, [who(3)] = 50 }
    local one = CoopRules.helpers(tied, 1, nil, nil)
    t.eq(one[1].UserId, 3, "the lower id first on a tie")
end)

t.test("nothing dealt, nothing paid; garbage is ignored", function()
    t.eq(#CoopRules.helpers({}, 10, nil, nil), 0)
    t.eq(#CoopRules.helpers({ [who(1)] = 0 }, 0, nil, nil), 0, "zero is not a share even when nothing is needed")
    t.eq(#CoopRules.helpers({ [who(1)] = "lots" }, 10, nil, nil), 0)
end)

t.test("a helper's pay is their share of the stones, at least 1 for a real egg, never for nothing", function()
    t.eq(CoopRules.share(100), math.floor(100 * C.StonesShare))
    t.eq(CoopRules.share(1), 1, "a tiny egg still pays a helper something")
    t.eq(CoopRules.share(0), 0)
    t.eq(CoopRules.share(-5), 0)
    t.eq(CoopRules.share("x"), 0)
    t.ok(CoopRules.share(1000) < 1000, "less than the whole")
end)

t.test("a dropped egg: its dropper can always take it back; a helper only after the wait; nobody else, never a full-handed or too-low player", function()
    local function f(over)
        local x = { state = "Dropped", isDropper = false, isHelper = true, now = 100, relayAt = 100 - 1, carrying = false, canCarryEgg = true }
        for k, v in over or {} do
            x[k] = v
        end
        return x
    end
    t.eq(CoopRules.canRelay(f()), true, "a helper after the wait")
    t.eq(CoopRules.canRelay(f({ now = 99 - 3 })), false, "a helper too early")
    t.eq(CoopRules.canRelay(f({ isDropper = true, isHelper = false, now = 0 })), true, "the dropper, at once")
    t.eq(CoopRules.canRelay(f({ isHelper = false })), false, "someone who didn't fight")
    t.eq(CoopRules.canRelay(f({ carrying = true })), false, "already carrying an egg")
    t.eq(CoopRules.canRelay(f({ canCarryEgg = false })), false, "an egg their rank can't carry")
    t.eq(CoopRules.canRelay(f({ state = "Carried" })), false, "only a dropped egg")
    t.eq(CoopRules.canRelay(f({ relayAt = "soon" })), false, "a broken time is no")
end)

t.finish("coop")

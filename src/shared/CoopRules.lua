-- Fighting and stealing together (the owner's improvement list, item 18): who counts as a helper, what a helper is paid, and when one may pick up a dropped egg.
-- Pure, so the spec runs it; server/Guardians/Guardian applies it.
--
--   CoopRules.helpers(damageBy, need, thief, here)   the players (not the thief) who dealt at least `need` and are `here(player)`, biggest share first, at most MaxHelpers
--   CoopRules.share(stones)                           what each helper is paid for an egg worth `stones` (0 for nothing; never less than 1 for something)
--   CoopRules.canRelay(f)                             whether a helper may pick a dropped egg up now
--       f = { state, isDropper, isHelper, now, relayAt, carrying, canCarryEgg }
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local CONFIG = GameConfig.EggTheft.Coop

local CoopRules = {}
CoopRules.Config = CONFIG

function CoopRules.helpers(damageBy, need, thief, here)
    local list = {}
    for player, dealt in damageBy do
        if player ~= thief and typeof(dealt) == "number" and dealt >= need and dealt > 0 and (here == nil or here(player)) then
            table.insert(list, { Player = player, Dealt = dealt })
        end
    end
    table.sort(list, function(a, b)
        if a.Dealt ~= b.Dealt then
            return a.Dealt > b.Dealt
        end
        return (a.Player.UserId or 0) < (b.Player.UserId or 0) -- (a tie always breaks the same way)
    end)
    local out = {}
    for i = 1, math.min(#list, CONFIG.MaxHelpers) do
        out[i] = list[i].Player
    end
    return out
end

function CoopRules.share(stones)
    if typeof(stones) ~= "number" or stones <= 0 then
        return 0
    end
    return math.max(1, math.floor(stones * CONFIG.StonesShare))
end

function CoopRules.canRelay(f)
    if f.state ~= "Dropped" or f.carrying or not f.canCarryEgg then
        return false
    end
    if f.isDropper then
        return true -- the one who dropped it can always pick it up again
    end
    return f.isHelper == true and typeof(f.now) == "number" and typeof(f.relayAt) == "number" and f.now >= f.relayAt
end

return CoopRules

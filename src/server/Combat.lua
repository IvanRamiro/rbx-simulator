-- Combat rules shared by the server's systems (CombatService resolves strikes; guardians and any
-- other target listen for hits).
--
--   Combat.weaponOf(player)  "Palm" before the flying sword is earned, "Sword" after
--   Combat.damageOf(player)  the weapon's damage times the rank's power
--   Combat.Hit               a BindableEvent (ServerStorage.CombatHit): (player, target, damage, position)
--                            fired for every strike that lands on a target tagged GameConfig.Combat.TargetTag
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local Combat = {}

-- one event instance for every script that requires this module
local hit = ServerStorage:FindFirstChild("CombatHit")
if not hit then
    hit = Instance.new("BindableEvent")
    hit.Name = "CombatHit"
    hit.Parent = ServerStorage
end
Combat.Hit = hit

function Combat.weaponOf(player)
    return if Ranks.isAtLeast(Ranks.getPlayerRankName(player), GameConfig.SwordFlight.UnlockRank) then "Sword" else "Palm"
end

function Combat.powerOf(player)
    local index = Ranks.getIndex(Ranks.getPlayerRankName(player)) or 1
    return 1 + (index - 1) * GameConfig.Combat.RankPowerStep
end

function Combat.damageOf(player)
    return GameConfig.Combat[Combat.weaponOf(player)].Damage * Combat.powerOf(player)
end

return Combat

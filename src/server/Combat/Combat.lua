-- Combat rules shared by the server's systems (CombatService resolves strikes; guardians and any
-- other target listen for hits).
--
--   Combat.strikeOf(player)  the player's strike: { Kind = "Palm" | "Sword" | "Spear", Range, Arc,
--                            Cooldown, Damage (before rank power), WeaponId, Element }: their equipped
--                            weapon (WeaponInventory; a forged one GameConfig.Forge.DamageBonus harder),
--                            or the Qi Palm with none
--   Combat.damageOf(player)  the strike's damage times the rank's power
--   Combat.Hit               a BindableEvent (ServerStorage.CombatHit): (player, target, damage, position)
--                            fired for every strike that lands on a target tagged GameConfig.Combat.TargetTag
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local WeaponInventory = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("WeaponInventory"))

local Combat = {}

-- one event instance for every script that requires this module
local hit = ServerStorage:FindFirstChild("CombatHit")
if not hit then
    hit = Instance.new("BindableEvent")
    hit.Name = "CombatHit"
    hit.Parent = ServerStorage
end
Combat.Hit = hit

function Combat.strikeOf(player)
    local weapon, element = WeaponInventory.equipped(player)
    if not weapon then
        local palm = GameConfig.Combat.Palm
        return { Kind = "Palm", Range = palm.Range, Arc = palm.Arc, Cooldown = palm.Cooldown, Damage = palm.Damage }
    end
    local kind = GameConfig.WeaponKinds[weapon.Kind]
    local damage = weapon.Damage * (if element then 1 + GameConfig.Forge.DamageBonus else 1)
    return { Kind = weapon.Kind, Range = kind.Range, Arc = kind.Arc, Cooldown = kind.Cooldown, Damage = damage, WeaponId = weapon.Id,
        Element = element }
end

function Combat.powerOf(player)
    local index = Ranks.getIndex(Ranks.getPlayerRankName(player)) or 1
    return 1 + (index - 1) * GameConfig.Combat.RankPowerStep
end

function Combat.damageOf(player)
    return Combat.strikeOf(player).Damage * Combat.powerOf(player)
end

return Combat

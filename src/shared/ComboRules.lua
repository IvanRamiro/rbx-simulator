-- How a weapon's strikes chain into a combo (the owner, 2026-11-23: "make combos flow naturally from one attack into another"). The server counts every
-- player's combo (CombatService) and tells every client which strike of the chain just fell, so what each player sees is the same chain everywhere: before,
-- only the spear's step came from the server, and a sword's or a fist's was counted again by every client, which drifted whenever one of them missed a strike.
--
--   Sword   three strikes: a diagonal cut, a backhand, an overhead finisher
--   Spear   two: a thrust, then a slash (the slash's reach is the server's)
--   Palm    two: the right fist, then the left
-- A strike continues the chain when it comes within the weapon's window of the last one (and is the same weapon); otherwise it is the first strike again.
-- The strike after the last is the first. The numbers: GameConfig.WeaponKinds[...].ComboWindow for the sword and the spear, ComboRules.PalmWindow for the fists.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local ComboRules = {}

ComboRules.Steps = { Sword = 3, Spear = 2, Palm = 2 }
ComboRules.PalmWindow = 1.1 -- seconds (the fists have no weapon kind, so their window is kept here; CombatFx and CombatService both read it)

-- the longest, in seconds, between two strikes of one weapon's chain
function ComboRules.window(weapon)
    if weapon == "Palm" then
        return ComboRules.PalmWindow
    end
    local kind = GameConfig.WeaponKinds[weapon]
    return kind and kind.ComboWindow or 0
end

-- The strike's place in the chain, 1 to Steps[weapon]. last = { Weapon, Step, At } (the player's previous strike) or nil; now in the same clock as At.
-- A weapon with no chain (an unknown name) is always step 1.
function ComboRules.step(weapon, last, now)
    local steps = ComboRules.Steps[weapon]
    if not steps then
        return 1
    end
    if last and last.Weapon == weapon and typeof(last.At) == "number" and now - last.At >= 0 and now - last.At < ComboRules.window(weapon) then
        return last.Step % steps + 1
    end
    return 1
end

-- whether this strike is the one that ends the chain: the finisher (the sword's overhead, the spear's slash, the left fist)
function ComboRules.isFinisher(weapon, step)
    return ComboRules.Steps[weapon] ~= nil and step == ComboRules.Steps[weapon]
end

return ComboRules

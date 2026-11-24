-- The rules of how a guardian answers being fought (GameConfig.GuardianReact), pure so they can be tested; server/Guardians/Guardian applies them.
--
--   ReactRules.record(hits, now)                   the list of strike times with `now` added and any older than HitWindow dropped (a new list)
--   ReactRules.due(hits, now, readyAt, guarding)   whether the guardian has had enough: HitsToReact strikes in the window, its reaction ready, not already guarding
--   ReactRules.blocking(now, raiseUntil, guardUntil)         whether the guard is up
--   ReactRules.stagger(reaction, guarding, now, readyAt)     the seconds a blow delays the guardian's next attack (0 for none) and whether it shoves it: delay, shove
--   ReactRules.shoveAmount(shove, now)             how far along its direction a shove has taken the guardian from its post (out and back along a half sine), nil when over
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local CONFIG = GameConfig.GuardianReact
local ReactRules = {}

function ReactRules.record(hits, now)
    local out = {}
    for _, at in hits do
        if now - at <= CONFIG.HitWindow and now >= at then
            table.insert(out, at)
        end
    end
    table.insert(out, now)
    return out
end

function ReactRules.due(hits, now, readyAt, guarding)
    return #hits >= CONFIG.HitsToReact and now >= readyAt and not guarding
end

function ReactRules.blocking(now, raiseUntil, guardUntil)
    return now >= raiseUntil and now < guardUntil
end

function ReactRules.stagger(reaction, guarding, now, readyAt)
    if guarding then
        return 0, false
    end
    if reaction == "Launch" and now >= readyAt then
        return CONFIG.Stagger, true
    elseif reaction == "Heavy" then
        return CONFIG.HeavyStagger, false
    end
    return 0, false
end

function ReactRules.shoveAmount(shove, now)
    if not shove then
        return nil
    end
    local t = (now - shove.Start) / shove.Time
    if t >= 1 or t < 0 then
        return nil
    end
    return shove.Distance * math.sin(math.pi * t)
end

return ReactRules

-- A guardian takes a blow (client-only, cosmetic: the server decides every hit, Guardian.lua).
--
-- Each blow the player lands (CombatFx.landHit) kicks the guardian's body: a short, sharp tilt of a few joints away from the striker, a
-- little rebound, and for a heavy blow or a critical one a small shove of the whole body as well. It is a tremor, added after the springs
-- (GuardianAnim), so it rides on top of whatever the guardian is doing and never replaces it.
--
-- Super armour: while an attack, a wake or a stagger of the guardian's own is playing, a blow only shivers it (ARMOURED of the
-- strength, no shove), so no hit ever cancels, delays or hides an attack.
--
-- A rig names what moves in Rig.Hit = { Body = the joint that is shoved, Joints = { [joint] = { share, lag seconds } }, Scale = how
-- much of the blow this guardian shows (heavier ones show less) }.
--
--   GuardianReact.bind(model, anim, rig) / unbind(model)   the guardian's animation and rig (GuardianController)
--   GuardianReact.hit(model, direction, grade)             a blow travelling along `direction` (world): grade "Normal", "Heavy" or
--                                                          "Critical". True if the guardian showed it.
--   GuardianReact.style(model)                             the rig's effect style (its debris), or nil
local GameConfig = require(game:GetService("ReplicatedStorage"):WaitForChild("GameConfig"))

local GuardianReact = {}

-- degrees at the lead joint, seconds it lasts, studs the body is shoved (measured on the Stone Lion in Play: 1.6, 3.4 and 4.6 degrees moved its
-- head 0.2 studs at most, lost in its breathing; these move a head 0.3 to 0.8, 0.8 to 1.6 and 2.7 to 5 studs on the lion, Pangu, Tiangou and the Mantis)
local GRADES = {
    Normal = { Degrees = 5, Time = 0.16, Shove = 0.12 },
    Heavy = { Degrees = 9, Time = 0.24, Shove = 0.4 },
    Critical = { Degrees = 11.5, Time = 0.30, Shove = 0.6 },
}
local ARMOURED = 0.3
local MAX_KICKS = 4
local WAKE_TIME = { Awaken = 2.8, Weaken = 1.9, Enrage = 1.5, SitDown = 1.5, Land = 1.2 }

-- [model] = { anim, rig, kicks }
local bound = setmetatable({}, { __mode = "k" })

-- Whether one of the guardian's own moves is under way: an attack's wind-up, its blow and recovery, a leap and its landing, a wake.
local function armoured(anim, now)
    local attacks = (GameConfig.Guardians[anim.model:GetAttribute("GuardianId")] or {}).Attacks or {}
    for name, action in anim.actions do
        local age = now - action.start
        local length = WAKE_TIME[name]
        if not length then
            local spec = attacks[name]
            if spec then
                length = (action.args[1] or spec.WindUp or 0.6) + (action.args[2] or spec.Air or 0) + 0.6
            end
        end
        if length and age < length then
            return true
        end
    end
    return false
end

local function apply(anim, now)
    local entry = bound[anim.model]
    if not entry or #entry.kicks == 0 then
        return
    end
    local hit = entry.rig.Hit
    local safe = armoured(anim, now)
    for i = #entry.kicks, 1, -1 do
        local kick = entry.kicks[i]
        local t = now - kick.start
        if t >= kick.time + 0.1 then
            table.remove(entry.kicks, i)
        else
            local damping, omega = 3 / kick.time, 2 * math.pi / (kick.time * 0.9)
            local strength = if safe then ARMOURED else 1
            for joint, spec in entry.joints do
                local u = t - spec[2]
                if u > 0 then
                    -- a quick rise, then a damped swing back with a little rebound
                    local g = (1 - math.exp(-u / 0.02)) * math.exp(-damping * u) * math.cos(omega * u) * spec[1] * strength
                    local degrees = kick.degrees * g
                    -- a push toward the guardian's back (+Z) tips its top back (a positive pitch); a push to its right (+X) leans it right
                    anim:tremor(joint, degrees * kick.local_.Z, -degrees * 0.5 * kick.local_.X, -degrees * 0.8 * kick.local_.X)
                end
            end
            if kick.shove > 0 and not safe then
                local u = math.max(t, 0)
                local g = (1 - math.exp(-u / 0.03)) * math.exp(-damping * u) * math.cos(omega * u)
                -- the whole body rocks as it is shoved: a lean along the blow at the hips, and a push back or down
                local rock = kick.degrees * g * 0.4
                anim:tremor(hit.Body, rock * kick.local_.Z, -rock * 0.5 * kick.local_.X, -rock * 0.8 * kick.local_.X,
                    kick.shove * g * 0.6 * kick.local_.Y, kick.shove * g * kick.local_.Z)
            end
        end
    end
end

function GuardianReact.bind(model, anim, rig)
    if not rig.Hit then
        return
    end
    -- only joints the rig has (a wrong name would break its animation every frame)
    local joints = {}
    for joint, spec in rig.Hit.Joints do
        if anim.springs[joint] then
            joints[joint] = spec
        else
            warn("GuardianReact: " .. model.Name .. " has no joint " .. joint)
        end
    end
    if not anim.springs[rig.Hit.Body] then
        warn("GuardianReact: " .. model.Name .. " has no joint " .. rig.Hit.Body)
        return
    end
    bound[model] = { anim = anim, rig = rig, kicks = {}, joints = joints }
    anim.reaction = apply
end

function GuardianReact.unbind(model)
    local entry = bound[model]
    if entry then
        entry.anim.reaction = nil
        bound[model] = nil
    end
end

function GuardianReact.style(model)
    local entry = bound[model]
    return entry and entry.rig.Style
end

function GuardianReact.hit(model, direction, grade)
    local entry = bound[model]
    local spec = GRADES[grade]
    if not (entry and spec) then
        return false
    end
    local root = entry.anim.root
    if not (root and root.Parent) then
        return false
    end
    local scale = entry.rig.Hit.Scale or 1
    local look = root.CFrame:VectorToObjectSpace(direction)
    if look.Magnitude < 1e-3 then
        return false
    end
    if #entry.kicks >= MAX_KICKS then
        table.remove(entry.kicks, 1)
    end
    table.insert(entry.kicks, {
        start = os.clock(), time = spec.Time, degrees = spec.Degrees * scale, shove = spec.Shove * scale, local_ = look.Unit,
    })
    return true
end

return GuardianReact

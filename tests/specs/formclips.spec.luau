-- The combat forms' clips (shared/FormClips, the keyed clips in client/Character/WeaponClips): every chain step has a clip, every clip exists and is
-- sound, and each fits its strike's cooldown within the retiming CombatFx allows.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local FormRules = require("@shared/FormRules")
local FormClips = require("@shared/FormClips")
local WeaponClips = require("@shared/WeaponClips")

local SPEED_MIN, SPEED_MAX = 0.75, 1.8 -- CombatFx: the clip's speed against the cooldown it must fit
local FIT = 0.92 -- CombatFx.retimed: a strike's clip is fitted to this share of its cooldown

local function baseCooldown(family)
    return if family == "Palm" then GameConfig.Combat.Palm.Cooldown else GameConfig.WeaponKinds[family].Cooldown
end

-- every (form, step, clip name) the game can play
local function allSteps()
    local list = {}
    for _, group in { FormClips.Own, FormClips.Borrowed } do
        for form, names in group do
            for step, name in names do
                table.insert(list, { form = form, step = step, name = name })
            end
        end
    end
    return list
end

t.test("every form has its clips, one per chain step", function()
    for form, data in FormRules.Forms do
        local names = FormClips.Own[form] or FormClips.Borrowed[form]
        t.ok(names ~= nil, form .. " has no clip table")
        t.eq(#names, #data.Chain, form .. ": a clip for every chain step")
    end
    for form in FormClips.Own do
        t.ok(FormRules.Forms[form] ~= nil, "clips for unknown form " .. form)
        t.ok(FormClips.Borrowed[form] == nil, form .. " is both own and borrowed")
    end
end)

t.test("every clip exists in WeaponClips and is sound", function()
    for _, entry in allSteps() do
        local clip = WeaponClips.Clips[entry.name]
        t.ok(clip ~= nil, entry.form .. " step " .. entry.step .. ": no clip " .. entry.name)
        t.ok(type(clip.Length) == "number" and clip.Length > 0.2 and clip.Length < 3, entry.name .. ": odd length")
        t.ok(type(clip.Hit) == "number" and clip.Hit > 0 and clip.Hit < clip.Length, entry.name .. ": the blow is not inside the clip")
        local frames = math.floor(clip.Length * WeaponClips.Fps + 0.5) + 1
        t.eq(#clip.Root, frames * 4, entry.name .. ": Root has the wrong number of frames")
        t.eq(#clip.RootPos, frames * 3, entry.name .. ": RootPos has the wrong number of frames")
        for _, joint in { "Waist", "Neck", "RightShoulder", "RightElbow", "LeftShoulder", "LeftElbow", "RightHip", "LeftHip" } do
            t.eq(#clip[joint], frames * 4, entry.name .. ": " .. joint .. " has the wrong number of frames")
        end
        if clip.SwingStart then
            t.ok(clip.SwingStart < clip.Hit + 0.001 and clip.Hit < clip.SwingEnd + 0.03 and clip.SwingEnd < clip.Length, entry.name .. ": the swing marks are out of order")
        end
    end
end)

t.test("a clip fits its strike's cooldown within the retime range", function()
    for _, entry in allSteps() do
        local form = FormRules.Forms[entry.form]
        local step = form.Chain[entry.step]
        local clip = WeaponClips.Clips[entry.name]
        local speed = clip.Length / (baseCooldown(form.Family) * step.Cd * FIT)
        t.ok(speed >= SPEED_MIN and speed <= SPEED_MAX,
            string.format("%s step %d (%s): the clip would play at %.2fx: outside %.2f to %.2f", entry.form, entry.step, entry.name, speed, SPEED_MIN, SPEED_MAX))
    end
end)

t.test("the clip test can fail: a clip too long for its cooldown is caught", function()
    local form = FormRules.Forms.Gale
    local speed = 1.3 / (baseCooldown(form.Family) * form.Chain[1].Cd * FIT) -- (a 1.3 s clip in a 0.33 s strike)
    t.ok(speed > SPEED_MAX, "the range check would pass a clip four times too long")
end)

t.finish("formclips")

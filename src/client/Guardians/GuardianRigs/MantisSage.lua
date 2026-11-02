-- The Bamboo Mantis Sage's rig (GuardianAnim) and effects (GuardianFx).
--
-- Joints: Body (from the root), Mantle (the leaf robe), Neck (the long prothorax), Head, an Upper and
-- a Blade per forearm (folded in prayer at rest), an Upper and a Lower per walking leg.
--   Dormant   meditating: head bowed, its amber eyes dark (closed);
--   Guardian  awake, swaying gently side to side;
--   Weakened  crouched, its blades lowered to the ground;
--   Enraged   the threat display: robe flared, blades raised and open, eyes red.
-- It walks on four legs, alternate pairs together. Its debris is bamboo leaves, its Qi jade.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}

Rig.Joints = {
    "Body", "Mantle", "Neck", "Head",
    "LeftArmUpper", "LeftArmBlade", "RightArmUpper", "RightArmBlade",
    "MidLeftUpper", "MidLeftLower", "MidRightUpper", "MidRightLower",
    "HindLeftUpper", "HindLeftLower", "HindRightUpper", "HindRightLower",
}
-- the walking legs: alternate pairs step together; side +1 right, -1 left (a forward swing is a yaw
-- of side * angle, a lift a roll of side * angle)
local LEGS = {
    { "MidLeft", -1, 0 }, { "HindRight", 1, 0 }, { "MidRight", 1, 0.5 }, { "HindLeft", -1, 0.5 },
}

Rig.Poses = {
    Dormant = { Neck = { -3 }, Head = { -16 } },
    Guardian = { Body = { 0, 0, 0, -0.3 }, Head = { 0 } },
    Weakened = {
        Body = { 0, 0, 0, -2.5 }, Neck = { -20 }, Head = { -8 },
        LeftArmUpper = { -12, 0, -12 }, RightArmUpper = { -12, 0, 12 },
        LeftArmBlade = { -140 }, RightArmBlade = { -140 },
    },
    Enraged = {
        Body = { 0, 0, 0, 0.8 }, Mantle = { 28 }, Neck = { 6 }, Head = { 8 },
        LeftArmUpper = { 35, 0, -16 }, RightArmUpper = { 35, 0, 16 },
        LeftArmBlade = { -55 }, RightArmBlade = { -55 },
    },
    Returning = { Body = { 0, 0, 0, -0.3 }, Head = { -6 } },
    Resting = { Neck = { -3 }, Head = { -16 } },
}
Rig.LeapAction = "Leap"
Rig.Look = { Joint = "Head", Share = 0.8, Body = "Neck", BodyShare = 0.2, Limit = 50 }
-- springs (GuardianAnim): a light body, the leaf robe flapping behind every move, the long neck
-- and the head trailing it like a stalk, the blades quick
Rig.Springs = {
    Body = { Freq = 4, Damping = 0.55, Drag = 0 },
    Mantle = { Freq = 2.4, Damping = 0.32, Drag = 0.8 },
    Neck = { Freq = 3.6, Damping = 0.45, Drag = 0.35 },
    Head = { Freq = 4.5, Damping = 0.5, Drag = 0.4 },
    LeftArmUpper = { Freq = 7, Damping = 0.55, Drag = 0.15 },
    RightArmUpper = { Freq = 7, Damping = 0.55, Drag = 0.15 },
    LeftArmBlade = { Freq = 9, Damping = 0.5, Drag = 0 },
    RightArmBlade = { Freq = 9, Damping = 0.5, Drag = 0 },
}
Rig.Lean = { Joint = "Body", Accel = 0.1, Bank = 0.06, Max = 6 }
-- planted feet (GuardianAnim): the sprawling legs bend on roll, the left ones folding on a positive
-- Lower turn and the right on a negative one (measured in Play)
Rig.Legs = {
    { Name = "MidLeft", Upper = "MidLeftUpper", Lower = "MidLeftLower", Axis = 3, Bend = 1 },
    { Name = "MidRight", Upper = "MidRightUpper", Lower = "MidRightLower", Axis = 3, Bend = -1 },
    { Name = "HindLeft", Upper = "HindLeftUpper", Lower = "HindLeftLower", Axis = 3, Bend = 1 },
    { Name = "HindRight", Upper = "HindRightUpper", Lower = "HindRightLower", Axis = 3, Bend = -1 },
}
Rig.Style = { Debris = "Leaves", Qi = Color3.fromRGB(0, 200, 110), QiCore = Color3.fromRGB(170, 255, 210) }

local STRIDE = 16

function Rig.gait(anim, pose, dt)
    anim.phase = (anim.phase + dt * anim.stepSpeed / STRIDE) % 1
    local amplitude = 20 * anim.moving
    for _, leg in LEGS do
        local name, side, offset = leg[1], leg[2], leg[3]
        local a = 2 * math.pi * (anim.phase + offset)
        local lift = math.max(0, math.cos(a)) * anim.moving
        add(pose, name .. "Upper", 0, side * amplitude * math.sin(a), side * 16 * lift)
        add(pose, name .. "Lower", 0, 0, -side * 8 * lift)
        anim:lift(name, math.min(1, lift * 2))
    end
    add(pose, "Body", 0, 0, 0, 0.3 * math.abs(math.sin(4 * math.pi * anim.phase)) * anim.moving)
end

-- breathing, and the leaf-in-the-wind sway while it is awake
function Rig.life(anim, pose, state, now)
    if state == "Dormant" or state == "Resting" then
        add(pose, "Body", 0, 0, 0, 0.08 * math.sin(now * 0.8))
        return
    end
    local sway = if state == "Enraged" then 1.6 else 0.7
    local amount = if state == "Weakened" then 1.5 else 2.6
    add(pose, "Body", 0, 0, amount * math.sin(now * sway), 0.12 * math.sin(now * 1.4))
    add(pose, "Neck", 0, 0, -amount * 0.6 * math.sin(now * sway - 0.4))
    add(pose, "Mantle", 1.2 * math.sin(now * 2.1))
end

-- both arms as a key pose: the upper arms' pitch and spread, the blades' fold
local function armKey(key, pitch, roll, blade)
    key.LeftArmUpper = { pitch, 0, -roll }
    key.RightArmUpper = { pitch, 0, roll }
    key.LeftArmBlade = { blade }
    key.RightArmBlade = { blade }
    return key
end

local function arms(pose, pitch, roll, blade)
    add(pose, "LeftArmUpper", pitch, 0, -roll)
    add(pose, "RightArmUpper", pitch, 0, roll)
    add(pose, "LeftArmBlade", blade)
    add(pose, "RightArmBlade", blade)
end

function Rig.actions(anim, pose, now)
    -- waking: the head lifts from its meditation, the robe shivers, the blades twitch
    local t = anim:action("Awaken", 1.8)
    if t then
        local rise = envelope(t, 0.7, 1.8, 0.5)
        add(pose, "Head", 18 * rise)
        anim:tremor("Mantle", 10 * envelope(t, 0.2, 1.2, 0.4) * math.sin(t * 22))
        arms(pose, 0, 0, -22 * envelope(t - 0.6, 0.15, 0.6, 0.3))
    end

    -- faltering: a stagger, the neck dipping
    t = anim:action("Weaken", 1.9)
    if t then
        local w = envelope(t, 0.2, 1.9, 0.6)
        add(pose, "Body", 0, 0, 6 * math.sin(t * 8) * w)
        add(pose, "Neck", -10 * w)
    end

    -- the scythes: drawn back and opened high, the body rising on its legs; then snapped shut across
    -- the front (fastest as they close), the body dropping into the strike, and held
    local scythe = anim.actions.Scythe
    if scythe then
        local w = scythe.args[1] or 0.6
        t = anim:action("Scythe", w + 0.7)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w - 0.12, armKey({ Body = { 2, 0, 0, 0.2 }, Neck = { 6 }, Head = { 4 }, Mantle = { 12 } }, 55, 12, -85) },
                { w + 0.02, armKey({ Body = { -5, 0, 0, -0.9, -0.8 }, Neck = { -8 }, Head = { -8 }, Mantle = { 18 } }, -18, 0, 28), "in" },
                { w + 0.25, armKey({ Body = { -4, 0, 0, -0.8, -0.6 }, Neck = { -6 }, Head = { -6 }, Mantle = { 12 } }, -12, 0, 22), "out" },
                { w + 0.7, {} },
            })
        end
    end

    -- the blade wave: it coils low, blades folded tight to its chest; rises tall, blades crossed high,
    -- the robe lifting; at the release it flings them down and out, lunging into it, the robe
    -- flaring, holds, and gathers itself again
    local wave = anim.actions.BladeWave
    if wave then
        local w = wave.args[1] or 0.9
        t = anim:action("BladeWave", w + 1.1)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.3, armKey({ Body = { -4, 0, 0, -1.2 }, Neck = { -10 }, Head = { -6 }, Mantle = { -6 } }, 10, 0, -60), "out" },
                { w - 0.12, armKey({ Body = { 6, 0, 0, 0.3 }, Neck = { 12 }, Head = { 8 }, Mantle = { 22 } }, 80, -12, -35) },
                { w + 0.04, armKey({ Body = { -8, 0, 0, -1.4, -1.2 }, Neck = { -12 }, Head = { -6 }, Mantle = { 34 } }, -30, 40, -25), "in" },
                { w + 0.4, armKey({ Body = { -6, 0, 0, -1.2, -1.0 }, Neck = { -10 }, Head = { -4 }, Mantle = { 26 } }, -26, 36, -22), "out" },
                { w + 1.1, {} },
            })
            local build = smooth((t - w * 0.45) / (w * 0.55)) * (if t < w then 1 else 0)
            anim:tremor("Mantle", 3 * build * math.sin(t * 31))
        end
    end

    -- the leap: a crouch, then sailing, robe spread like wings, blades reaching
    local leap = anim.actions.Leap
    if leap then
        local windUp, air = leap.args[1] or 0.5, leap.args[2] or 1.1
        t = anim:action("Leap", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", -4 * crouch, 0, 0, -3 * crouch)
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local spread = envelope(u, 0.12, 1, 0.25)
                add(pose, "Mantle", 40 * spread)
                add(pose, "Body", (8 - 16 * u) * spread)
                arms(pose, 55 * spread, 8 * spread, -40 * spread)
                for _, leg in LEGS do
                    add(pose, leg[1] .. "Upper", 0, -leg[2] * 25 * spread, -leg[2] * 6 * spread)
                end
            end
        end
    end

    -- landing: it sinks deep onto its legs, the robe settling after it, and rises
    t = anim:action("Land", 0.7)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.08, { Body = { -4, 0, 0, -2.4 }, Neck = { -8 }, Mantle = { 18 } }, "out" },
            { 0.32, { Body = { 1, 0, 0, 0.1 }, Neck = { 3 } } },
            { 0.7, {} },
        })
    end
end

-- The pupils and the blades' Qi edges. Asleep its eyes are closed (dark stone) and the edges dull
-- jade glass; awake, Neon (dark Neon renders as a flat black disc).
local PUPIL = Color3.fromRGB(255, 144, 0)
local RAGE = Color3.fromRGB(255, 40, 20)
local EDGE = Color3.fromRGB(0, 200, 110)

function Rig.setup(anim)
    anim.pupils = anim.model:FindFirstChild("Pupils")
    anim.edges = { anim.model:FindFirstChild("LeftEdge"), anim.model:FindFirstChild("RightEdge") }
    anim.pupilSize = anim.pupils and anim.pupils.Size
end

function Rig.glow(anim, state, now)
    local awaken = anim:action("Awaken", 1.8)
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local pupil = if state == "Enraged" then RAGE else PUPIL
    if state == "Weakened" then
        pupil = Color3.fromRGB(150, 80, 0):Lerp(PUPIL, 0.5 + 0.5 * math.sin(now * 11) * math.sin(now * 4.3))
    end
    local pupils = anim.pupils
    if pupils then
        local material = if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon
        if pupils.Material ~= material then
            pupils.Material = material
        end
        pupils.Color = if asleep then Color3.fromRGB(70, 52, 26) else pupils.Color:Lerp(pupil, 0.25)
        local size = anim.pupilSize * (if state == "Enraged" then 1.35 else 1)
        if (pupils.Size - size).Magnitude > 0.01 then
            pupils.Size = pupils.Size:Lerp(size, 0.2)
        end
    end
    local scythe = anim.actions.Scythe
    local cut = 0
    if scythe then
        cut = envelope(now - scythe.start - (scythe.args[1] or 0.6), 0.03, 0.4, 0.3)
    end
    local edge = if state == "Enraged" then Color3.fromRGB(60, 255, 160) else EDGE
    edge = edge:Lerp(Color3.fromRGB(190, 255, 225), cut)
    for _, part in anim.edges do
        local material = if asleep then Enum.Material.Glass else Enum.Material.Neon
        if part.Material ~= material then
            part.Material = material
        end
        part.Color = if asleep then Color3.fromRGB(20, 90, 60) else part.Color:Lerp(edge, 0.3)
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local CUTS = { CFrame.new(-3.6, 14, -19), CFrame.new(3.6, 14, -19) }   -- where the scythes cut (mantis-local)
local CHEST = CFrame.new(0, 19, -13)

Rig.Fx = {
    Awaken = function(model)
        GuardianFx.shed(model:FindFirstChild("Mantle"), style, 24)
        GuardianFx.shake(model:GetPivot().Position, 0.8, 0.6)
    end,
    Scythe = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            for _, cut in CUTS do
                GuardianFx.crescent(pivot * cut, style, 14)
            end
            GuardianFx.puff(pivot * CFrame.new(0, 2, -18), style, 14, 16, 70, 3, 1.2)
            GuardianFx.shake(pivot.Position, 1.3, 0.4)
        end)
    end,
    BladeWave = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * CHEST, style, 22)
            GuardianFx.streaks(pivot * CHEST, style, 12, 55, 40)
            GuardianFx.shake(pivot.Position, 1.8, 0.7)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 50, style)
        end)
    end,
    Leap = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 20, 18, Vector2.new(180, 10), 3, 1.2)
        end)
    end,
    Land = function(model, position)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 34, 30, Vector2.new(180, 8), 3, 1.4)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 16)
        GuardianFx.shake(position, 2.6, 0.6)
    end,
}

return Rig

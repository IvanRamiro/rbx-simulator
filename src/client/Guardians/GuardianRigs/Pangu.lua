-- Pangu the World-Splitter's rig (GuardianAnim) and effects (GuardianFx).
--
-- Joints: Body (from the root: the pelvis), Chest, Head, an UpperArm and a Forearm per arm (the
-- left palm open, the right hand holding the axe on his shoulder) and a Thigh and a Shin per
-- leg. Limbs hang down, so a positive X turn swings a limb's far end forward and up; the right
-- forearm points forward and up to the fist, so on it a positive turn lifts the fist back toward the
-- shoulder and a negative one swings the axe forward and down.
--   Dormant   a statue: head bowed, eyes shut, the void in his cracks burning low;
--   Guardian  upright, watching, breathing slow;
--   Weakened  sunk to one knee, head down, the void guttering;
--   Enraged   squared up, axe lifted from the shoulder, eyes narrowed and red.
-- He walks on two legs, heavily, the shoulders swinging against the hips. His debris is chaos (dark
-- violet), his Qi void.
--
-- The eyes are deep-set violet almonds with dark pupils under heavy lids (guardian_kit.eye): he
-- blinks slowly, glares enraged, widens and flickers weakened, shuts them asleep.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}

Rig.Joints = {
    "Body", "Chest", "Head", "LeftUpperArm", "LeftForearm", "RightUpperArm", "RightForearm",
    "LeftThigh", "LeftShin", "RightThigh", "RightShin",
}

Rig.Poses = {
    Dormant = { Chest = { -5 }, Head = { -20 } },
    Guardian = { Chest = { 2 } },
    Weakened = {
        -- down on his right knee (its shin flat behind him), the left thigh level and its foot planted
        -- before him: the hips drop by a thigh's height less the knee (measured: -4.2 left the foot afloat)
        Body = { 0, 0, 0, -8.4 }, Chest = { -14 }, Head = { -14 },
        LeftThigh = { 86 }, LeftShin = { -86 }, RightThigh = { 0 }, RightShin = { -86 },
        LeftUpperArm = { -8 }, RightUpperArm = { -6 },
    },
    Enraged = {
        Body = { 0, 0, 0, -0.6 }, Chest = { 6 }, Head = { 4 },
        RightUpperArm = { 35 }, RightForearm = { -20 }, LeftUpperArm = { 8 },
        LeftThigh = { 10 }, LeftShin = { -14 }, RightThigh = { -6 }, RightShin = { -8 },
    },
    Returning = { Head = { -4 } },
    Resting = { Chest = { -5 }, Head = { -20 } },
}
Rig.LeapAction = "TitanLeap"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Chest", BodyShare = 0.3, Limit = 45 }
Rig.Style = { Debris = "Void", Qi = Color3.fromRGB(140, 40, 255), QiCore = Color3.fromRGB(225, 190, 255) }

local STRIDE = 16

function Rig.gait(anim, pose, dt)
    anim.phase = (anim.phase + dt * anim.speed / STRIDE) % 1
    local a = 2 * math.pi * anim.phase
    local swing = 26 * anim.moving
    for _, leg in { { "Left", 0 }, { "Right", math.pi } } do
        local t = a + leg[2]
        add(pose, leg[1] .. "Thigh", swing * math.sin(t))
        add(pose, leg[1] .. "Shin", -38 * math.max(0, math.cos(t)) * anim.moving)    -- the knee bends as the leg comes through
    end
    -- the hips bob and roll over each step, the chest turning against them
    add(pose, "Body", 0, 5 * math.sin(a) * anim.moving, 2 * math.sin(a) * anim.moving, 0.5 * math.abs(math.sin(a)) * anim.moving)
    add(pose, "Chest", 2 * anim.moving, -8 * math.sin(a) * anim.moving, -1.5 * math.sin(a) * anim.moving)
    add(pose, "Head", 0, 3 * math.sin(a) * anim.moving)
end

function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 0.7 elseif asleep then 0.12 else 0.22
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Chest", 1.2 * breath)
    add(pose, "Head", -0.8 * breath)
    add(pose, "LeftUpperArm", 0.8 * breath)
    add(pose, "RightUpperArm", 0.8 * breath)
end

function Rig.actions(anim, pose, now)
    -- waking: the head lifts, the chest heaves, and the axe's haft strikes the ground once
    local t = anim:action("Awaken", 2.2)
    if t then
        local rise = envelope(t, 0.8, 2.2, 0.6)
        add(pose, "Head", 22 * rise)
        add(pose, "Chest", 8 * rise)
        local stamp = envelope(t - 0.9, 0.25, 0.9, 0.4)
        add(pose, "RightUpperArm", 30 * stamp)
        add(pose, "RightForearm", -40 * stamp)
    end

    -- faltering: he reels, then goes down to his knee (the pose)
    t = anim:action("Weaken", 1.6)
    if t then
        local reel = envelope(t, 0.15, 1.0, 0.5)
        add(pose, "Chest", -10 * reel, 0, 6 * math.sin(t * 7) * reel)
        add(pose, "Head", 12 * reel)
    end

    -- the cleave: the axe lifts off his shoulder, his chest winds back, then the whole body brings it
    -- down across the ground before him
    local cleave = anim.actions.AxeCleave
    if cleave then
        local windUp = cleave.args[1] or 0.9
        t = anim:action("AxeCleave", windUp + 0.8)
        if t then
            local cock = if t < windUp - 0.22 then smooth(t / (windUp - 0.22)) elseif t < windUp then 1 - (t - windUp + 0.22) / 0.22 else 0
            local strike = envelope(t - windUp + 0.22, 0.2, 0.9, 0.45)   -- lands as the hit does
            -- raised high off the shoulder, then the forearm rolls forward and down (a negative turn),
            -- bringing the head over the top and into the ground before him, his body bending into it
            add(pose, "RightUpperArm", 70 * cock + 20 * strike, 0, 10 * cock)
            add(pose, "RightForearm", -20 * cock - 150 * strike)
            add(pose, "Chest", 4 * cock - 24 * strike, -18 * cock + 22 * strike)
            add(pose, "Body", -12 * strike, 0, 0, -1.2 * strike)
            add(pose, "LeftThigh", 14 * strike)
            add(pose, "LeftShin", -18 * strike)
        end
    end

    -- the sky-splitter: the axe raised high in both arms, then slammed into the ground before him
    local split = anim.actions.SkySplitter
    if split then
        local windUp = split.args[1] or 1.2
        t = anim:action("SkySplitter", windUp + 0.9)
        if t then
            local raise = if t < windUp - 0.22 then smooth(t / (windUp - 0.22)) elseif t < windUp then 1 - (t - windUp + 0.22) / 0.22 else 0
            local slam = envelope(t - windUp + 0.22, 0.2, 1.0, 0.5)
            add(pose, "RightUpperArm", 110 * raise + 40 * slam)
            add(pose, "RightForearm", 20 * raise - 155 * slam)
            add(pose, "LeftUpperArm", 30 * raise)
            add(pose, "Chest", 10 * raise - 30 * slam)
            add(pose, "Head", 6 * raise - 8 * slam)
            add(pose, "Body", -14 * slam, 0, 0, -1.5 * slam)
            add(pose, "LeftThigh", 18 * slam)
            add(pose, "LeftShin", -24 * slam)
            add(pose, "RightThigh", -10 * slam)
        end
    end

    -- the chaos nova: the open left palm raised high, the chest thrown open, the void bursting out
    local nova = anim.actions.ChaosNova
    if nova then
        local windUp = nova.args[1] or 1.4
        t = anim:action("ChaosNova", windUp + 1.0)
        if t then
            local raise = envelope(t, windUp * 0.9, windUp + 1.0, 0.6)
            local burst = envelope(t - windUp, 0.05, 0.6, 0.4)
            add(pose, "LeftUpperArm", 70 * raise)
            add(pose, "LeftForearm", 20 * raise)
            add(pose, "Chest", 8 * raise - 4 * burst, 0, 0)
            add(pose, "Head", 14 * raise)
            add(pose, "Body", 0, 0, 0, 0.6 * raise - 1.0 * burst)
        end
    end

    -- the titan leap: a deep crouch, then up, knees drawn, the axe high
    local leap = anim.actions.TitanLeap
    if leap then
        local windUp, air = leap.args[1] or 0.8, leap.args[2] or 1.5
        t = anim:action("TitanLeap", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", 0, 0, 0, -2.5 * crouch)
            for _, side in { "Left", "Right" } do
                add(pose, side .. "Thigh", 40 * crouch)
                add(pose, side .. "Shin", -70 * crouch)
            end
            add(pose, "Chest", -10 * crouch)
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local tuck = envelope(u, 0.15, 1, 0.3)
                add(pose, "LeftThigh", 50 * tuck)
                add(pose, "LeftShin", -60 * tuck)
                add(pose, "RightThigh", 20 * tuck)
                add(pose, "RightShin", -80 * tuck)
                add(pose, "RightUpperArm", 90 * tuck)
                add(pose, "RightForearm", -20 * tuck)
                add(pose, "Chest", 6 * tuck)
            end
        end
    end

    -- landing: the knees take it
    t = anim:action("Land", 0.7)
    if t then
        local give = envelope(t, 0.05, 0.7, 0.5)
        add(pose, "Body", 0, 0, 0, -1.8 * give)
        for _, side in { "Left", "Right" } do
            add(pose, side .. "Thigh", 28 * give)
            add(pose, side .. "Shin", -50 * give)
        end
        add(pose, "Chest", -8 * give)
    end
end

-- ---------- the eyes and the void ----------
-- Asleep his eyes are shut (iris and pupil hidden: the stone behind them is the closed lid) and the
-- void in his cracks burns low (Neon fades with transparency; a darker colour would turn black).
local EYE = Color3.fromRGB(154, 100, 255)
local RAGE = Color3.fromRGB(255, 50, 60)
local VOID = Color3.fromRGB(140, 40, 255)
local VOID_HOT = Color3.fromRGB(190, 90, 255)
local OPEN = { Guardian = 1, Weakened = 1.15, Enraged = 0.72, Returning = 0.9 }

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.pupils = model:FindFirstChild("Pupils")
    anim.irisSize = anim.iris and anim.iris.Size
    anim.pupilSize = anim.pupils and anim.pupils.Size
    anim.void = {}
    for _, part in model:GetChildren() do
        if part:IsA("BasePart") and string.sub(part.Name, -4) == "Void" then
            table.insert(anim.void, part)
        end
    end
    anim.nextBlink = os.clock() + 2
end

local function open(part, base, amount)
    if part then
        local size = Vector3.new(base.X, math.max(base.Y * amount, 0.02), base.Z)
        if (part.Size - size).Magnitude > 0.005 then
            part.Size = part.Size:Lerp(size, 0.6)   -- quick enough for a full blink
        end
    end
end

function Rig.glow(anim, state, now)
    local awaken = anim:action("Awaken", 2.2)
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local amount = OPEN[state] or 1
    if not asleep and now >= anim.nextBlink then
        anim.blinkAt = now
        anim.nextBlink = now + 4 + 3 * math.random()
    end
    if anim.blinkAt then
        local b = (now - anim.blinkAt) / 0.34
        if b >= 1 then
            anim.blinkAt = nil
        else
            amount *= 1 - math.min(1, math.sin(math.pi * b) * 1.6) * 0.95   -- shut for a moment at its middle
        end
    end
    if awaken then
        amount *= smooth((awaken - 0.6) / 0.6)
    end
    local color = if state == "Enraged" then RAGE else EYE
    if state == "Weakened" then
        color = Color3.fromRGB(80, 40, 150):Lerp(EYE, 0.5 + 0.5 * math.sin(now * 10) * math.sin(now * 3.9))
    end
    for _, part in { anim.iris, anim.pupils } do
        if part then
            part.Transparency = if asleep then 1 else 0
        end
    end
    if anim.iris then
        anim.iris.Color = anim.iris.Color:Lerp(color, 0.25)
    end
    open(anim.iris, anim.irisSize, if asleep then 0.02 else amount)
    open(anim.pupils, anim.pupilSize, if asleep then 0.02 else amount)

    -- the void in his cracks: low asleep, pulsing with his breath, guttering weakened, hot enraged,
    -- flaring as he strikes
    local breath = 0.5 + 0.5 * math.sin(now * 0.22 * 2 * math.pi)
    local fade = if asleep then 0.5 elseif state == "Weakened" then 0.2 + 0.3 * math.abs(math.sin(now * 5) * math.sin(now * 1.9))
        else 0.15 * (1 - breath)
    local hot = if state == "Enraged" then 0.6 + 0.4 * breath else 0.2 * breath
    for _, name in { "SkySplitter", "ChaosNova", "AxeCleave" } do
        local action = anim.actions[name]
        if action then
            local flare = envelope(now - action.start - (action.args[1] or 1), 0.05, 0.9, 0.6)
            hot = math.max(hot, flare)
            fade *= 1 - flare
        end
    end
    local tint = VOID:Lerp(VOID_HOT, hot)
    for _, part in anim.void do
        part.Transparency += (fade - part.Transparency) * 0.3
        part.Color = part.Color:Lerp(tint, 0.3)
    end
end

-- ---------- his effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local PALM = CFrame.new(-5.9, 25.8, -6.6)       -- over his open left palm, where the nova bursts (titan-local)
local CLEAVE = CFrame.new(3, 0.6, -16)          -- where the axe comes down
local SPLIT = CFrame.new(1, 0.6, -14)           -- where the sky-splitter strikes the ground

Rig.Fx = {
    Awaken = function(model)
        task.delay(1.2, function()
            if model.Parent then
                local pivot = model:GetPivot()
                GuardianFx.puff(pivot * CFrame.new(8, 0.6, -4), style, 18, 16, Vector2.new(180, 8), 4, 1.3)
                GuardianFx.shake(pivot.Position, 1.6, 0.8)
            end
        end)
    end,
    AxeCleave = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * CLEAVE * CFrame.new(0, 6, 0), style, 26)
            GuardianFx.puff(pivot * CLEAVE, style, 22, 22, Vector2.new(90, 8), 4, 1.2)
            GuardianFx.flash(pivot * CLEAVE, style, 14)
            GuardianFx.shake(pivot.Position, 2, 0.5)
        end)
    end,
    SkySplitter = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * SPLIT, style, 22)
            GuardianFx.streaks(pivot * SPLIT, style, 16, 70, 8)
            GuardianFx.puff(pivot * SPLIT, style, 30, 26, Vector2.new(60, 10), 5, 1.4)
            GuardianFx.shake(pivot.Position, 3, 1)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 15, style)
        end)
    end,
    ChaosNova = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * PALM * CFrame.new(0, 6, 0), style, 34)
            GuardianFx.streaks(pivot * PALM * CFrame.Angles(math.rad(90), 0, 0), style, 20, 50, 70)
            GuardianFx.shake(pivot.Position, 2.4, 1)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 180, style)
        end)
    end,
    TitanLeap = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 26, 22, Vector2.new(180, 10), 4, 1.3)
            GuardianFx.shake(from, 1.6, 0.5)
        end)
    end,
    Land = function(model, position)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 44, 36, Vector2.new(180, 6), 5, 1.6)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 20)
        GuardianFx.shake(position, 3.4, 0.9)
    end,
}

return Rig

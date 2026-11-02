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

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}

Rig.Joints = {
    "Body", "Chest", "Head", "LeftUpperArm", "LeftForearm", "RightUpperArm", "RightForearm",
    "LeftThigh", "LeftShin", "RightThigh", "RightShin",
}

-- awake, he stands on slightly bent knees (the planted feet need the slack)
Rig.Poses = {
    Dormant = { Chest = { -5 }, Head = { -20 } },
    Guardian = { Body = { 0, 0, 0, -0.6 }, Chest = { 2 } },
    Weakened = {
        -- down on his right knee (its shin flat behind him), the left thigh level and its foot planted
        -- before him: the hips drop by a thigh's height less the knee (measured: -4.2 left the foot afloat)
        Body = { 0, 0, 0, -8.4 }, Chest = { -14 }, Head = { -14 },
        LeftThigh = { 86 }, LeftShin = { -86 }, RightThigh = { 0 }, RightShin = { -86 },
        LeftUpperArm = { -8 }, RightUpperArm = { -6 },
    },
    Enraged = {
        Body = { 0, 0, 0, -0.9 }, Chest = { 6 }, Head = { 4 },
        RightUpperArm = { 35 }, RightForearm = { -20 }, LeftUpperArm = { 8 },
    },
    Returning = { Body = { 0, 0, 0, -0.6 }, Head = { -4 } },
    Resting = { Chest = { -5 }, Head = { -20 } },
}
Rig.LeapAction = "TitanLeap"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Chest", BodyShare = 0.3, Limit = 45 }
-- springs (GuardianAnim): a titan's slow hips and chest, the head trailing them, the open left arm
-- hanging loose and swinging after them; the axe arm stays quick (its strikes are timed to the
-- effects)
Rig.Springs = {
    Body = { Freq = 3.2, Damping = 0.6, Drag = 0 },
    Chest = { Freq = 3.2, Damping = 0.5, Drag = 0.25 },
    Head = { Freq = 4.2, Damping = 0.5, Drag = 0.3 },
    LeftUpperArm = { Freq = 3.2, Damping = 0.4, Drag = 0.5 },
    LeftForearm = { Freq = 3.6, Damping = 0.38, Drag = 0.5 },
    RightUpperArm = { Freq = 8, Damping = 0.6, Drag = 0 },
    RightForearm = { Freq = 8, Damping = 0.6, Drag = 0 },
}
Rig.Lean = { Joint = "Chest", Accel = 0.1, Bank = 0.04, Max = 5 }
-- planted feet (GuardianAnim): the shins fold on a negative turn (measured in Play)
Rig.Legs = {
    { Name = "Left", Upper = "LeftThigh", Lower = "LeftShin", Axis = 1, Bend = -1 },
    { Name = "Right", Upper = "RightThigh", Lower = "RightShin", Axis = 1, Bend = -1 },
}
Rig.Style = { Debris = "Void", Qi = Color3.fromRGB(140, 40, 255), QiCore = Color3.fromRGB(225, 190, 255) }

local STRIDE = 16

function Rig.gait(anim, pose, dt)
    anim.phase = (anim.phase + dt * anim.stepSpeed / STRIDE) % 1
    local a = 2 * math.pi * anim.phase
    -- measured in Play: a 22 degree stride, a 55 degree knee bend through the swing and the hips
    -- about 1.4 studs low (with the awake poses') keep the planted foot down and the swinging one clear
    local swing = 22 * anim.moving
    for _, leg in { { "Left", 0 }, { "Right", math.pi } } do
        local t = a + leg[2]
        local lift = math.max(0, math.cos(t))
        add(pose, leg[1] .. "Thigh", swing * math.sin(t))
        add(pose, leg[1] .. "Shin", -55 * lift * anim.moving)    -- the knee bends as the leg comes through
        anim:lift(leg[1], math.min(1, lift * 2) * anim.moving)
    end
    -- the hips roll over each step, lowest with the legs apart (the foot coming down) and highest as
    -- they pass; the chest turns against them
    local passing = math.abs(math.cos(a))
    add(pose, "Body", 0, 5 * math.sin(a) * anim.moving, 2.5 * math.sin(a) * anim.moving, (0.6 * passing - 1.1) * anim.moving)
    add(pose, "Chest", 2 * anim.moving, -8 * math.sin(a) * anim.moving, -1.5 * math.sin(a) * anim.moving)
    add(pose, "Head", 0, 3 * math.sin(a) * anim.moving)
    -- the open left arm swings against the left leg; the axe arm only rocks on the shoulder
    add(pose, "LeftUpperArm", -16 * math.sin(a) * anim.moving)
    add(pose, "LeftForearm", (8 - 6 * math.sin(a)) * anim.moving)
    add(pose, "RightUpperArm", 3 * math.sin(a) * anim.moving)
end

-- slow, deep breaths that lift the chest and shoulders, his weight shifting from foot to foot over
-- the planted feet, the head turning slowly as he watches
function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 0.7 elseif asleep then 0.12 else 0.22
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Chest", 2.2 * breath)
    add(pose, "Body", 0, 0, 0, 0.25 * breath)
    add(pose, "Head", -1.4 * math.sin(now * rate * 2 * math.pi + 0.8))
    add(pose, "LeftUpperArm", 1.6 * breath, 0, 1.2 * breath)
    add(pose, "RightUpperArm", 1.2 * breath)
    if not asleep then
        local idle = 1 - anim.moving
        add(pose, "Body", 0, 2 * math.sin(now * 0.27) * idle, 2 * math.sin(now * 0.35) * idle)
        add(pose, "Chest", 0, -1.5 * math.sin(now * 0.27 - 0.5) * idle, -1.2 * math.sin(now * 0.35 - 0.4) * idle)
    end
    -- weakened, the right knee is down on the ground: only the left foot is planted
    anim:lift("Right", anim.weights.Weakened or 0)
end

function Rig.actions(anim, pose, now)
    -- waking: the head lifts, the chest heaves, and the axe's haft strikes the ground once
    local t = anim:action("Awaken", 2.2)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.8, { Body = { 0, 0, 0, -0.4 }, Chest = { 10 }, Head = { 24 } }, "out" },
            { 1.15, { Body = { 0, 0, 0, -0.9 }, Chest = { 4 }, Head = { 16 }, RightUpperArm = { 34 }, RightForearm = { -44 } }, "in" },
            { 1.5, { Body = { 0, 0, 0, -0.6 }, Chest = { 6 }, Head = { 18 }, RightUpperArm = { 28 }, RightForearm = { -36 } }, "out" },
            { 2.2, {} },
        })
    end

    -- faltering: he reels, then goes down to his knee (the pose)
    t = anim:action("Weaken", 1.6)
    if t then
        local reel = envelope(t, 0.15, 1.0, 0.5)
        add(pose, "Chest", -10 * reel, 0, 6 * math.sin(t * 7) * reel)
        add(pose, "Head", 12 * reel)
    end

    -- the cleave: a short gather, the axe cocked off his shoulder, his chest winding back; then the
    -- whole body drives it down (fastest at the strike, which lands as the hit does), his weight
    -- dropping over his planted feet, and holds before he straightens
    local cleave = anim.actions.AxeCleave
    if cleave then
        local w = cleave.args[1] or 0.9
        t = anim:action("AxeCleave", w + 0.9)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.3, { Body = { 0, 0, 0, -0.6 }, Chest = { -4, 10 }, RightUpperArm = { 20 } }, "out" },
                { w - 0.22, { Chest = { 4, -18 }, Head = { 4 }, RightUpperArm = { 70, 0, 10 }, RightForearm = { -20 } } },
                { w, { Body = { -12, 0, 0, -1.8 }, Chest = { -24, 22 }, Head = { -6 }, RightUpperArm = { 20 }, RightForearm = { -150 } }, "in" },
                { w + 0.25, { Body = { -10, 0, 0, -1.6 }, Chest = { -20, 18 }, Head = { -4 }, RightUpperArm = { 18 }, RightForearm = { -145 } }, "out" },
                { w + 0.9, {} },
            })
            anim:tremor("Chest", 1.5 * envelope(t - w, 0.02, 0.3, 0.2) * math.sin(t * 50))
        end
    end

    -- the sky-splitter: he dips, then rises with the axe raised high in both hands; it comes down
    -- into the ground before him at the release, his body driving after it, and he holds the impact
    local split = anim.actions.SkySplitter
    if split then
        local w = split.args[1] or 1.2
        t = anim:action("SkySplitter", w + 1.0)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.35, { Body = { 0, 0, 0, -1.0 }, Chest = { -8 }, Head = { -6 }, RightUpperArm = { 40 }, RightForearm = { -10 }, LeftUpperArm = { 20 } }, "out" },
                { w - 0.22, { Body = { 0, 0, 0, 0.2 }, Chest = { 12 }, Head = { 8 }, RightUpperArm = { 115 }, RightForearm = { 20 },
                    LeftUpperArm = { 40 }, LeftForearm = { 30 } } },
                { w, { Body = { -14, 0, 0, -2.2 }, Chest = { -32 }, Head = { -10 }, RightUpperArm = { 40 }, RightForearm = { -155 }, LeftUpperArm = { 10 } }, "in" },
                { w + 0.35, { Body = { -12, 0, 0, -2.0 }, Chest = { -28 }, Head = { -8 }, RightUpperArm = { 38 }, RightForearm = { -150 }, LeftUpperArm = { 8 } }, "out" },
                { w + 1.0, {} },
            })
            anim:tremor("Chest", 2 * envelope(t - w, 0.02, 0.35, 0.25) * math.sin(t * 46))
        end
    end

    -- the chaos nova: he hunches, the open left palm drawn in to his chest, gathering the void; he
    -- rises as the palm lifts; at the release the palm is thrust up to the sky, chest thrown open,
    -- head back, and he holds it there shaking before it fades
    local nova = anim.actions.ChaosNova
    if nova then
        local w = nova.args[1] or 1.4
        t = anim:action("ChaosNova", w + 1.3)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.35, { Body = { 0, 0, 0, -1.6 }, Chest = { -14 }, Head = { -10 }, LeftUpperArm = { 10 }, LeftForearm = { 70 },
                    RightUpperArm = { -4 } }, "out" },
                { w - 0.15, { Body = { 0, 0, 0, -0.6 }, Chest = { 8 }, Head = { 12 }, LeftUpperArm = { 100 }, LeftForearm = { 25 } } },
                -- 140 with the chest leaning back 16 holds the arm straight up (160 went behind his head)
                { w + 0.05, { Body = { 0, 0, 0, -1.2 }, Chest = { 16 }, Head = { 20 }, LeftUpperArm = { 140 }, LeftForearm = { 0 },
                    RightUpperArm = { 24 } }, "out" },
                { w + 0.65, { Body = { 0, 0, 0, -1.1 }, Chest = { 14 }, Head = { 18 }, LeftUpperArm = { 134 }, LeftForearm = { 2 },
                    RightUpperArm = { 20 } }, "linear" },
                { w + 1.3, {} },
            })
            local build = smooth((t - w * 0.4) / (w * 0.6)) * (if t < w then 1 else 0)
            anim:tremor("Chest", 0.8 * build * math.sin(t * 41), 0, 0.6 * build * math.sin(t * 33))
            anim:tremor("LeftUpperArm", 2 * envelope(t - w, 0.05, 0.6, 0.3) * math.sin(t * 38))
        end
    end

    -- the titan leap: a deep crouch (the planted feet fold his knees), then up, knees drawn, the axe high
    local leap = anim.actions.TitanLeap
    if leap then
        local windUp, air = leap.args[1] or 0.8, leap.args[2] or 1.5
        t = anim:action("TitanLeap", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", 0, 0, 0, -2.5 * crouch)
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

    -- landing: the knees take it, deep, and he rises out of it
    t = anim:action("Land", 0.8)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.1, { Body = { 0, 0, 0, -2.6 }, Chest = { -12 }, Head = { -6 }, LeftUpperArm = { 14, 0, 8 } }, "out" },
            { 0.35, { Body = { 0, 0, 0, -0.4 }, Chest = { 2 } } },
            { 0.8, {} },
        })
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

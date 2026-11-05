-- Pangu the World-Splitter on a real skeleton (tools/blender/guardians/pangu_v2.py): one skin over 41 bones, the axe locked in his
-- right hand, the left arm free. He holds no egg: no guardian does. The legs and the blows were solved in Blender and approved
-- there; PanguClips.lua (generated) is that work as data, and this rig plays it through GuardianAnim's springs.
--   Dormant   a statue: head bowed, eyes shut, the void burning low;
--   Guardian  upright, the axe on his shoulder, watching, breathing slow;
--   Weakened  down on his right knee, the left hand braced on the raised knee, the axe lowered, the void guttering;
--   Enraged   squared up, the axe off the shoulder, the free hand clawed, eyes narrowed and red.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))
local Clips = require(script.Parent:WaitForChild("PanguClips"))

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}
Rig.Skinned = true
Rig.ExtraBones = { "Eyes" }

Rig.Joints = {
    "Hips", "Spine", "Chest", "Neck", "Head", "Jaw", "Beard1", "Beard2",
    "LoinFront1", "LoinFront2", "LoinBack1", "LoinBack2", "MantleMid1", "MantleMid2",
}
for _, part in { "Clavicle", "UpperArm", "Forearm", "Hand", "Fingers", "Thumb", "Thigh", "Shin", "Foot", "Toe", "Mantle1", "Mantle2" } do
    table.insert(Rig.Joints, "Left" .. part)
end
for _, part in { "Clavicle", "UpperArm", "Forearm", "Hand", "Thigh", "Shin", "Foot", "Toe", "Mantle1", "Mantle2" } do
    table.insert(Rig.Joints, "Right" .. part)
end
table.insert(Rig.Joints, "Axe")

Rig.Poses = Clips.Poses
Rig.Gallop = { 14, 22 } -- walking below the first, running past the second
Rig.LeapAction = "TitanLeap"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Chest", BodyShare = 0.3, Limit = 45 }

-- a titan's slow hips and chest, the head trailing them, the free arm loose; the axe arm stays quick (its blows are timed to the
-- effects); the hangings and beard lag behind everything
local HANG = { Freq = 2.6, Damping = 0.32, Drag = 0.6 }
local HANG_TIP = { Freq = 2.3, Damping = 0.3, Drag = 0.75 }
local LEG = { Freq = 30, Damping = 0.9, Drag = 0 }
local QUICK = { Freq = 18, Damping = 0.75, Drag = 0 }
Rig.Springs = {
    Hips = { Freq = 10, Damping = 0.7, Drag = 0 },
    Spine = { Freq = 9, Damping = 0.65, Drag = 0 },
    Chest = { Freq = 8, Damping = 0.6, Drag = 0 },
    Neck = { Freq = 7, Damping = 0.55, Drag = 0.12 },
    Head = { Freq = 7, Damping = 0.5, Drag = 0.22 },
    Jaw = { Freq = 12, Damping = 0.6, Drag = 0 },
    Beard1 = { Freq = 3.4, Damping = 0.36, Drag = 0.45 },
    Beard2 = { Freq = 3.0, Damping = 0.34, Drag = 0.6 },
    LoinFront1 = HANG, LoinFront2 = HANG_TIP, LoinBack1 = HANG, LoinBack2 = HANG_TIP,
    MantleMid1 = HANG, MantleMid2 = HANG_TIP, LeftMantle1 = HANG, LeftMantle2 = HANG_TIP, RightMantle1 = HANG, RightMantle2 = HANG_TIP,
    LeftClavicle = QUICK, RightClavicle = QUICK,
    LeftUpperArm = { Freq = 6, Damping = 0.5, Drag = 0.3 },
    LeftForearm = { Freq = 6.5, Damping = 0.45, Drag = 0.25 },
    LeftHand = { Freq = 10, Damping = 0.5, Drag = 0 },
    LeftFingers = QUICK, LeftThumb = QUICK,
    RightUpperArm = QUICK, RightForearm = QUICK, RightHand = QUICK,
    Axe = { Freq = 40, Damping = 0.9, Drag = 0 },
    LeftThigh = LEG, LeftShin = LEG, LeftFoot = LEG, LeftToe = LEG, RightThigh = LEG, RightShin = LEG, RightFoot = LEG, RightToe = LEG,
}
Rig.Lean = { Joint = "Chest", Accel = 0.1, Bank = 0.04, Max = 5 }
-- planted feet: the shins fold on a negative turn. His stance is staggered and posed, so Pin 0 keeps a foot where the pose puts it
Rig.Legs = {
    { Name = "Left", Upper = "LeftThigh", Lower = "LeftShin", Foot = "LeftFoot", Flat = { "LeftFoot" }, Axis = 1, Bend = -1, Pin = 0 },
    { Name = "Right", Upper = "RightThigh", Lower = "RightShin", Foot = "RightFoot", Flat = { "RightFoot" }, Axis = 1, Bend = -1, Pin = 0 },
}
Rig.Style = { Debris = "Void", Qi = Color3.fromRGB(140, 40, 255), QiCore = Color3.fromRGB(225, 190, 255) }

-- ---------- the gaits ----------
local WALK, RUN = Clips.Gaits.walk, Clips.Gaits.run
local GAIT_JOINTS = {}
for joint in WALK do
    GAIT_JOINTS[joint] = true
end
for joint in RUN do
    GAIT_JOINTS[joint] = true
end

local function sampled(rows, i, j, u, k)
    if not rows then
        return 0
    end
    local a, b = rows[i][k] or 0, rows[j][k] or 0
    return a + (b - a) * u
end

function Rig.gait(anim, pose, dt)
    local g, moving = anim.gallop, anim.moving
    local stride = Clips.Strides.walk + (Clips.Strides.run - Clips.Strides.walk) * g
    anim.phase = (anim.phase + dt * anim.stepSpeed / stride) % 1
    local at = anim.phase * 24
    local i = math.floor(at) % 24 + 1
    local j = i % 24 + 1
    local u = at - math.floor(at)
    for joint in GAIT_JOINTS do
        local w, r = WALK[joint], RUN[joint]
        local p = pose[joint]
        for k = 1, 5 do
            local a = sampled(w, i, j, u, k)
            p[k] += (a + (sampled(r, i, j, u, k) - a) * g) * moving
        end
    end
    -- a foot is held to the ground from when its sole is flat until its heel lifts
    local stance = Clips.Stance.walk + (Clips.Stance.run - Clips.Stance.walk) * g
    for _, leg in { { "Left", 0 }, { "Right", 0.5 } } do
        local p = ((anim.phase + leg[2]) % 1) / stance
        local held = smooth((p - 0.12) / 0.06) * (1 - smooth((p - 0.68) / 0.06))
        anim:lift(leg[1], moving * (1 - held))
    end
end

-- slow, deep breaths that lift the chest and shoulders, his weight shifting, the head turning slowly as he watches
function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 0.7 elseif asleep then 0.12 else 0.22
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Chest", 1.8 * breath)
    add(pose, "Hips", 0, 0, 0, 0.2 * breath)
    add(pose, "Head", -1.2 * math.sin(now * rate * 2 * math.pi + 0.8))
    add(pose, "LeftClavicle", 0, 0, -1.5 * breath)
    add(pose, "RightClavicle", 0, 0, 1.5 * breath)
    add(pose, "LeftFingers", 0, 0, 4 + 3 * math.sin(now * 0.4)) -- curling toward the palm
    if not asleep then
        local idle = 1 - anim.moving
        add(pose, "Hips", 0, 1.6 * math.sin(now * 0.27) * idle, 1.6 * math.sin(now * 0.35) * idle)
        add(pose, "Spine", 0, -0.8 * math.sin(now * 0.27 - 0.5) * idle, -0.7 * math.sin(now * 0.35 - 0.4) * idle)
        add(pose, "Chest", 0, -0.8 * math.sin(now * 0.27 - 0.5) * idle, -0.7 * math.sin(now * 0.35 - 0.4) * idle)
    end
    -- weakened, the right knee is on the ground: only the left foot is planted
    anim:lift("Right", anim.weights.Weakened or 0)
end

-- ---------- the moves ----------
-- A whole pose from the table at clip time `clock`, laid over everything else by `weight`
local function playMove(pose, name, clock, weight)
    local frames = Clips.Moves[name]
    local at = math.clamp(clock * Clips.Fps, 0, #frames - 1)
    local i = math.floor(at)
    local a, b = frames[i + 1], frames[math.min(i + 2, #frames)]
    local u = at - i
    for joint, values in a do
        local p, other = pose[joint], b[joint]
        if p then
            for k = 1, #values do
                local gap = values[k] + (other[k] - values[k]) * u - p[k]
                if k <= 3 then
                    gap = (gap + 180) % 360 - 180 -- the clip may have come round a whole turn: blended the short way, not spun back
                end
                p[k] += gap * weight
            end
        end
    end
end

local function blend(t, total)
    return math.min(smooth(t / 0.1), smooth((total - t) / 0.25))
end

-- each strike's wind-up comes from the server; its clip was made for this long, and scaled to fit
local STRIKES = { AxeCleave = { 0.9, 1.95 }, SkySplitter = { 1.2, 2.2 }, ChaosNova = { 1.4, 2.7 } }
local BLOW_LEAD = 0.1 -- the springs carry a blow in this late (measured in Play): the clip runs this far ahead, so it lands with its effect

function Rig.actions(anim, pose, now)
    -- waking: the head lifts, the chest heaves, he settles the axe on his shoulder
    local t = anim:action("Awaken", 2.2)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.8, { Hips = { 0, 0, 0, -0.5 }, Chest = { 10 }, Neck = { 8 }, Head = { 22 } }, "out" },
            { 1.2, { Hips = { 0, 0, 0, -1.0 }, Chest = { 2 }, Neck = { 4 }, Head = { 14 } }, "in" },
            { 1.5, { Hips = { 0, 0, 0, -0.6 }, Chest = { 5 }, Head = { 16 } }, "out" },
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

    for name, spec in STRIKES do
        local action = anim.actions[name]
        if action then
            local w = action.args[1] or spec[1]
            local rate = spec[1] / w
            local total = spec[2] / rate
            t = anim:action(name, total)
            if t then
                playMove(pose, name, (t + BLOW_LEAD) * rate, blend(t, total))
                if t > w then
                    local shake = envelope(t - w, 0.02, 0.35, 0.25)
                    anim:tremor("Chest", 1.6 * shake * math.sin(t * 48), 0, 0.8 * shake * math.sin(t * 37))
                end
            end
        end
    end

    -- the leap: its clip's crouch is the wind-up, the rest the time in the air
    local leap = anim.actions.TitanLeap
    if leap then
        local windUp, air = leap.args[1] or 0.8, leap.args[2] or 1.5
        t = anim:action("TitanLeap", windUp + air + 0.1)
        if t then
            local clock = if t < windUp then t * (0.84 / windUp) else 0.84 + (t - windUp) * (1.56 / air)
            playMove(pose, "TitanLeap", clock, math.min(smooth(t / 0.1), 1))
        end
    end

    -- landing: the knees take it, deep, and he rises out of it
    t = anim:action("Land", 0.9)
    if t then
        playMove(pose, "Land", t, smooth((0.9 - t) / 0.25))
    end
end

-- ---------- the eyes and the void ----------
-- Eyes sink into their sockets to close (a bone slides them back: the lids are the skin's). The void burns low asleep, pulses with
-- his breath, gutters weakened and flares as he strikes.
local EYE = Color3.fromRGB(154, 100, 255)
local RAGE = Color3.fromRGB(255, 50, 60)
local VOID = Color3.fromRGB(140, 40, 255)
local VOID_HOT = Color3.fromRGB(190, 90, 255)
local OPEN = { Guardian = 1, Weakened = 1, Enraged = 0.6, Returning = 0.9 }
local SOCKET_DEPTH = 0.24

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.pupils = model:FindFirstChild("Pupils")
    anim.void = {}
    for _, part in model:GetChildren() do
        if part:IsA("BasePart") and string.sub(part.Name, -4) == "Void" then
            table.insert(anim.void, part)
        end
    end
end

function Rig.glow(anim, state, now)
    local awaken = anim:action("Awaken", 2.2)
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local amount = (OPEN[state] or 1) * anim:blink(now, asleep, 4, 0.34)
    if awaken then
        amount *= smooth((awaken - 0.6) / 0.6)
    end
    anim:poseBone("Eyes", CFrame.new(0, 0, SOCKET_DEPTH * (1 - math.clamp(amount, 0, 1))))
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
local function anchor(name)
    local a = Clips.Anchors[name]
    return CFrame.new(a[1], a[2], a[3])
end
local CLEAVE, SPLIT, PALM = anchor("AxeCleave"), anchor("SkySplitter"), anchor("ChaosNova")

Rig.Fx = {
    Awaken = function(model)
        task.delay(1.2, function()
            if model.Parent then
                local pivot = model:GetPivot()
                GuardianFx.puff(pivot * CFrame.new(5, 0.6, -2), style, 18, 16, Vector2.new(180, 8), 4, 1.3)
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
            GuardianFx.flash(pivot * PALM * CFrame.new(0, 3, 0), style, 34)
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

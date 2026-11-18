-- The Awakened Stone Lion on a real skeleton (tools/blender/guardians/stone_lion_v2.py): a lion carved in granite, each foreleg a shoulder
-- blade, an upper arm, a forearm, a pastern and toes, each hind leg a thigh, a shin, a hock and toes. It holds no egg: no guardian does. Its
-- walk, its gallop and its moves were solved in Blender so the paws stay on their spots; StoneLionClips.lua (generated) is that work as data,
-- and this rig plays it through GuardianAnim's springs.
--   Dormant   a temple statue, seated on its haunches: carved stone eyes, a dull jade orb, no breath at all;
--   Guardian  on its feet, head level, watching, slow breaths, the tail stirring, an ear turning now and then;
--   Weakened  the left paw held off the ground, head hanging, panting, a tremble in the planted legs;
--   Enraged   low on its legs, head low and forward, lips back, ears flat, the tail up and lashing, eyes red-orange.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))
local Clips = require(script.Parent:WaitForChild("StoneLionClips"))

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}
Rig.Skinned = true
Rig.ExtraBones = { "Eyes" }

local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }
Rig.Joints = { "Hips", "Spine", "Chest", "Neck1", "Neck2", "Head", "Jaw", "LeftEar", "RightEar", "ManeTop", "LeftMane", "RightMane", "ManeChest" }
for _, leg in { "FrontLeft", "FrontRight" } do
    for _, part in { "Scapula", "Upper", "Lower", "Paw", "Toes" } do
        table.insert(Rig.Joints, leg .. part)
    end
end
for _, leg in { "BackLeft", "BackRight" } do
    for _, part in { "Thigh", "Shin", "Meta", "Toes" } do
        table.insert(Rig.Joints, leg .. part)
    end
end
for k = 1, 6 do
    table.insert(Rig.Joints, "Tail" .. k)
end

Rig.Poses = Clips.Poses
Rig.Gallop = { 14, 19 } -- walking below the first, galloping past the second
Rig.LeapAction = "Pounce"
Rig.Look = { Joint = "Head", Share = 0.6, Body = "Neck2", BodyShare = 0.3, Limit = 45 }
-- a blow taken (GuardianReact): the chest takes it, the neck and head follow a beat later; the hips are shoved
Rig.Hit = { Body = "Hips", Joints = { Chest = { 1, 0 }, Neck1 = { 0.7, 0.02 }, Head = { 1, 0.04 }, ManeChest = { 1.2, 0.03 } }, Scale = 1 }

-- the body and legs follow closely, so the paws stay planted under them; the neck and head trail a little; the mane's weight lags and swings,
-- and the tail is a rope, every joint later and looser than the last
local LEG = { Freq = 30, Damping = 0.9, Drag = 0 }
local MANE = { Freq = 3.0, Damping = 0.38, Drag = 0.5 }
Rig.Springs = {
    Hips = { Freq = 16, Damping = 0.8, Drag = 0 },
    Spine = { Freq = 15, Damping = 0.78, Drag = 0 },
    Chest = { Freq = 14, Damping = 0.75, Drag = 0 },
    Neck1 = { Freq = 8, Damping = 0.62, Drag = 0.08 },
    Neck2 = { Freq = 7, Damping = 0.58, Drag = 0.14 },
    Head = { Freq = 7, Damping = 0.55, Drag = 0.22 },
    Jaw = { Freq = 14, Damping = 0.6, Drag = 0 },
    LeftEar = { Freq = 12, Damping = 0.42, Drag = 0 },
    RightEar = { Freq = 12, Damping = 0.42, Drag = 0 },
    ManeTop = MANE, LeftMane = MANE, RightMane = MANE,
    ManeChest = { Freq = 3.4, Damping = 0.36, Drag = 0.4 },
    Tail1 = { Freq = 5, Damping = 0.5, Drag = 0.15 },
    Tail2 = { Freq = 4.2, Damping = 0.45, Drag = 0.3 },
    Tail3 = { Freq = 3.6, Damping = 0.4, Drag = 0.45 },
    Tail4 = { Freq = 3.1, Damping = 0.36, Drag = 0.6 },
    Tail5 = { Freq = 2.7, Damping = 0.33, Drag = 0.75 },
    Tail6 = { Freq = 2.4, Damping = 0.3, Drag = 0.88 },
}
for _, leg in LEGS do
    for _, part in { "Scapula", "Upper", "Lower", "Paw", "Thigh", "Shin", "Meta", "Toes" } do
        Rig.Springs[leg .. part] = LEG
    end
end
Rig.Lean = { Joint = "Chest", Accel = 0.06, Bank = 0.04, Max = 5 }
-- planted feet: the toes' knuckle stays on the ground. A foreleg folds on a positive turn, a hind leg on a negative one; each has one more
-- joint below (its Chain), and its pose already puts each paw where it belongs, so Pin 0 keeps it there. While it walks or runs, a paw that
-- has landed is locked to that spot in the world until it lifts (Lock)
Rig.Legs = {
    { Name = "FrontLeft", Upper = "FrontLeftUpper", Lower = "FrontLeftLower", Chain = { "FrontLeftPaw" }, Foot = "FrontLeftToes", Flat = { "FrontLeftToes" }, Axis = 1, Bend = 1, Pin = 0, Lock = true },
    { Name = "FrontRight", Upper = "FrontRightUpper", Lower = "FrontRightLower", Chain = { "FrontRightPaw" }, Foot = "FrontRightToes", Flat = { "FrontRightToes" }, Axis = 1, Bend = 1, Pin = 0, Lock = true },
    { Name = "BackLeft", Upper = "BackLeftThigh", Lower = "BackLeftShin", Chain = { "BackLeftMeta" }, Foot = "BackLeftToes", Flat = { "BackLeftToes" }, Axis = 1, Bend = -1, Pin = 0, Lock = true },
    { Name = "BackRight", Upper = "BackRightThigh", Lower = "BackRightShin", Chain = { "BackRightMeta" }, Foot = "BackRightToes", Flat = { "BackRightToes" }, Axis = 1, Bend = -1, Pin = 0, Lock = true },
}
Rig.Style = { Debris = "Dust", Qi = Color3.fromRGB(0, 110, 255), QiCore = Color3.fromRGB(150, 210, 255) }

-- ---------- the gaits ----------
local WALK, RUN = Clips.Gaits.walk, Clips.Gaits.run
local STEPS = Clips.Steps
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

-- how firmly a paw is held to the ground at this point of its gait
local function held(phase, offset, duty)
    local p = ((phase - offset) % 1) / duty
    return smooth(p / 0.05) * (1 - smooth((p - 0.96) / 0.04))
end

function Rig.gait(anim, pose, dt)
    local g, moving = anim.gallop, anim.moving
    local stride = Clips.Strides.walk + (Clips.Strides.run - Clips.Strides.walk) * g
    anim.phase = (anim.phase + dt * anim.stepSpeed / stride) % 1
    local at = anim.phase * STEPS
    local i = math.floor(at) % STEPS + 1
    local j = i % STEPS + 1
    local u = at - math.floor(at)
    for joint in GAIT_JOINTS do
        local w, r = WALK[joint], RUN[joint]
        local p = pose[joint]
        for k = 1, 5 do
            local a = sampled(w, i, j, u, k)
            local gap = sampled(r, i, j, u, k) - a
            if k <= 3 then
                gap = (gap + 180) % 360 - 180
            end
            p[k] += (a + gap * g) * moving
        end
    end
    for _, leg in LEGS do
        local down = held(anim.phase, Clips.Phase.walk[leg], Clips.Duty.walk)
        down += (held(anim.phase, Clips.Phase.run[leg], Clips.Duty.run) - down) * g
        anim:lift(leg, moving * (1 - down))
    end
end

-- A dormant lion is stone: nothing moves. Awake: a slow breath that lifts the chest and shoulders, a shift of weight from side to side, the tail
-- stirring from its root and an ear turning now and then. Weakened: fast panting and a tremble. Enraged: the tail lashes.
local BREATH = { Dormant = 0, Guardian = 1, Weakened = 2.2, Enraged = 1.5, Returning = 1, Resting = 0.5 }
local RATE = { Guardian = 0.26, Weakened = 1.5, Enraged = 0.5, Returning = 0.3, Resting = 0.14 }

function Rig.life(anim, pose, state, now)
    add(pose, "Jaw", 0, 0, 0, 0.12, 0.45) -- seated up and back under the upper lip, its hinge inside the cheek
    local breath = BREATH[state] or 0
    if breath == 0 then
        return
    end
    local b = math.sin(now * (RATE[state] or 0.26) * 2 * math.pi)
    add(pose, "Chest", 1.0 * breath * b)
    add(pose, "Hips", 0, 0, 0, 0.1 * breath * b)
    add(pose, "Neck1", -0.5 * breath * b)
    add(pose, "FrontLeftScapula", 0, 0, -0.6 * breath * b)
    add(pose, "FrontRightScapula", 0, 0, 0.6 * breath * b)
    if state == "Resting" then
        return
    end
    local idle = 1 - anim.moving
    add(pose, "Hips", 0, 1.1 * math.sin(now * 0.29) * idle, 1.3 * math.sin(now * 0.37) * idle)
    add(pose, "Chest", 0, -1.1 * math.sin(now * 0.29 - 0.6) * idle, -1.0 * math.sin(now * 0.37 - 0.5) * idle)
    local lash = if state == "Enraged" then 2.3 else 0.55
    local reach = if state == "Enraged" then 3.4 else 1.5
    for k = 1, 6 do
        add(pose, "Tail" .. k, 0, reach * k * math.sin(now * lash - k * 0.5) * (if state == "Weakened" then 0.2 else 1), 0)
    end
    -- an ear turns to something, holds and comes back
    for ear, seed in { LeftEar = 0, RightEar = 2.7 } do
        local flick = math.max(0, math.sin(now * 0.31 + seed) - 0.93) / 0.07
        add(pose, ear, 22 * flick * idle, 0, 0)
    end
    if state == "Weakened" then
        local pant = math.sin(now * 1.5 * 2 * math.pi)
        add(pose, "Jaw", -6 * pant)
        anim:tremor("Hips", 0.25 * math.sin(now * 37), 0, 0.2 * math.sin(now * 29))
        anim:lift("FrontLeft", anim.weights.Weakened or 0)
    end
end

-- ---------- the moves ----------
-- A whole pose from the table at clip time `clock`, laid over everything else by `weight`; a paw the clip lifts lets go of the ground
local function playMove(anim, pose, name, clock, weight)
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
                    gap = (gap + 180) % 360 - 180 -- blended the short way round
                end
                p[k] += gap * weight
            end
        end
    end
    local plants = Clips.Plants[name]
    for _, leg in LEGS do
        if plants[leg][i + 1] == 0 then
            anim:lift(leg, weight)
        end
    end
end

local function blend(t, total)
    return math.min(smooth(t / 0.12), smooth((total - t) / 0.3))
end

-- each strike's wind-up comes from the server; its clip was made for this long, and scaled to fit
local STRIKES = { Slam = { 0.75, 1.6 }, Roar = { 1.1, 2.5 } }
local BLOW_LEAD = 0.1 -- the springs carry a blow in this late: the clip runs this far ahead, so it lands with its effect

function Rig.actions(anim, pose, now)
    -- it settles to sit when it goes back to sleep
    local state = anim.model:GetAttribute("State")
    local asleep = state == "Dormant" or state == "Resting"
    if asleep and anim.rigAwake then
        anim:play("SitDown")
    end
    anim.rigAwake = not asleep

    -- waking: the stone shudders, the head comes up, the chest fills; it rises and shakes the dust from its mane
    local t = anim:action("Awaken", 2.8)
    if t then
        playMove(anim, pose, "Awaken", t, smooth((2.8 - t) / 0.3))
        local shudder = envelope(t, 0.1, 0.9, 0.3)
        anim:tremor("Chest", 0.8 * shudder * math.sin(t * 61), 0, 0.6 * shudder * math.sin(t * 47))
        anim:tremor("Neck1", 0, 0.8 * shudder * math.sin(t * 53), 0)
    end
    t = anim:action("SitDown", 1.5)
    if t then
        playMove(anim, pose, "SitDown", t, smooth((1.5 - t) / 0.2) * smooth(t / 0.15))
    end

    -- faltering: the blow lands, the foreleg gives, it catches itself and draws the paw up
    t = anim:action("Weaken", 1.7)
    if t then
        playMove(anim, pose, "Weaken", t, math.min(smooth(t / 0.1), smooth((1.7 - t) / 0.2)))
    end

    -- oldest first, so the newest move is laid over the last and a blow that starts during another's recovery is seen
    local order = {}
    for name in STRIKES do
        if anim.actions[name] then
            table.insert(order, name)
        end
    end
    table.sort(order, function(x, y)
        return anim.actions[x].start < anim.actions[y].start
    end)
    for _, name in order do
        local spec, action = STRIKES[name], anim.actions[name]
        if action then
            local w = action.args[1] or spec[1]
            local rate = spec[1] / w
            local total = spec[2] / rate
            t = anim:action(name, total)
            if t then
                playMove(anim, pose, name, (t + BLOW_LEAD) * rate, blend(t, total))
                if t > w then
                    local shake = envelope(t - w, 0.02, 0.35, 0.25)
                    anim:tremor("Chest", 1.0 * shake * math.sin(t * 48), 0, 0.6 * shake * math.sin(t * 37))
                end
                if name == "Slam" then
                    -- the paw lands: the whole lion stops for an instant on it, its weight drops through the legs, and what hangs off it (the
                    -- mane, the tail) swings on past the stop
                    anim:contact("Slam", w, 0.08)
                    local after = t - w
                    local drop = envelope(after, 0.03, 0.4, 0.3)
                    add(pose, "Hips", 0, 0, 0, -0.55 * drop)
                    local k = GuardianAnim.damped(after, 2.4, 2.6)
                    add(pose, "ManeTop", 13 * k)
                    add(pose, "LeftMane", 9 * k, 0, 8 * k)
                    add(pose, "RightMane", 9 * k, 0, -8 * k)
                    add(pose, "ManeChest", 16 * k)
                    for i = 1, 6 do
                        add(pose, "Tail" .. i, -3 * i * k, 5 * i * k)
                    end
                end
                if name == "Roar" and t > w * 0.45 and t < w then
                    -- the chest swells, shaking, as the breath is drawn
                    local build = smooth((t - w * 0.45) / (w * 0.55))
                    anim:tremor("Chest", 0.5 * build * math.sin(t * 47), 0, 0.3 * build * math.sin(t * 39))
                elseif name == "Roar" and t >= w then
                    -- the roar itself, shuddering through the head and mane
                    local burst = envelope(t - w, 0.05, 0.8, 0.3)
                    anim:tremor("Head", 3 * burst * math.sin(t * 40), 1.6 * burst * math.sin(t * 29))
                    anim:tremor("Jaw", 2.4 * burst * math.sin(t * 53))
                end
            end
        end
    end

    -- the pounce: its clip's crouch is the wind-up, the rest the time in the air
    local pounce = anim.actions.Pounce
    if pounce then
        local windUp, air = pounce.args[1] or 0.6, pounce.args[2] or 0.95
        t = anim:action("Pounce", windUp + air + 0.1)
        if t then
            local clock = if t < windUp then t * (0.6 / windUp) else 0.6 + (t - windUp) * (0.95 / air)
            playMove(anim, pose, "Pounce", clock, smooth(t / 0.1))
        end
    end

    -- landing: the forelegs take it and fold, the hinds come through, it rises out of it; a stop on the landing, the mane flopping forward after it
    t = anim:action("Land", 1.2)
    if t then
        playMove(anim, pose, "Land", t, smooth((1.2 - t) / 0.25))
        anim:contact("Land", 0.05, 0.09)
        local k = GuardianAnim.damped(t - 0.05, 2.2, 2.3)
        add(pose, "ManeTop", 16 * k)
        add(pose, "LeftMane", 10 * k, 0, 8 * k)
        add(pose, "RightMane", 10 * k, 0, -8 * k)
        add(pose, "ManeChest", 14 * k)
        for i = 1, 6 do
            add(pose, "Tail" .. i, -3 * i * k, 0)
        end
    end

    -- it has seen the egg taken: the stone drops onto its haunches, head low, the mane up, ears flat, jaws open in a growl that shakes it
    -- from the chest out, the tail up and lashing; it holds, then rises out of it
    t = anim:action("Enrage", 1.4)
    if t then
        local snarl = { Hips = { -2, 0, 0, -1.5, 1.6 }, Spine = { -2 }, Chest = { -6 }, Neck1 = { -18 }, Neck2 = { -6 }, Jaw = { -36 }, ManeTop = { -14 },
            LeftMane = { -16 }, RightMane = { -16 }, Tail1 = { -26 }, Tail2 = { -12 }, Tail3 = { -8 }, Tail5 = { -22 }, Tail6 = { -26 }, LeftEar = { 40 }, RightEar = { 40 } }
        keyed(pose, t, {
            { 0, {} },
            { 0.16, snarl, "snap" },
            { 1.0, snarl, "linear" },
            { 1.4, {}, "inout" },
        })
        local growl = envelope(t - 0.16, 0.1, 0.8, 0.25)
        anim:tremor("Chest", 1.1 * growl * math.sin(t * 52), 0, 0.9 * growl * math.sin(t * 43))
        anim:tremor("Head", 1.6 * growl * math.sin(t * 61), 1.1 * growl * math.sin(t * 47))
        anim:tremor("Jaw", 3 * growl * math.sin(t * 37))
        for i = 1, 6 do
            anim:tremor("Tail" .. i, 0, 3 * i * growl * math.sin(t * 9 - i * 0.5))
        end
    end
end

-- ---------- the eyes and the orb ----------
-- Asleep: carved stone eyes (the pupil cut a shade darker) and a dull jade orb. Awake: Neon Qi blue and jade, blinking (the eyes sink back behind
-- the lids); weakened, flickering; enraged, red-orange and narrowed. Set locally: the server never changes them.
local STONE = Color3.fromRGB(120, 116, 106)
local STONE_PUPIL = Color3.fromRGB(70, 67, 62)
local PUPIL = Color3.fromRGB(6, 16, 28)
local DULL_JADE = Color3.fromRGB(46, 116, 88)
local EYES = { Guardian = Color3.fromRGB(0, 110, 255), Weakened = Color3.fromRGB(0, 110, 255), Enraged = Color3.fromRGB(255, 70, 20), Returning = Color3.fromRGB(0, 110, 255) }
local OPEN = { Guardian = 1, Weakened = 1, Enraged = 0.7, Returning = 0.9 }
local ORB = Color3.fromRGB(0, 160, 95)
local ORB_DIM = Color3.fromRGB(0, 90, 55)
local SOCKET_DEPTH = 0.3

function Rig.setup(anim)
    anim.iris = anim.model:FindFirstChild("Eyes")
    anim.pupils = anim.model:FindFirstChild("Pupils")
    anim.orb = anim.model:FindFirstChild("Orb")
end

local function material(part, wanted)
    if part and part.Material ~= wanted then
        part.Material = wanted
    end
end

function Rig.glow(anim, state, now)
    local waking = anim:action("Awaken", 2.8)
    local asleep = (state == "Dormant" or state == "Resting") and not waking
    local amount = (OPEN[state] or 1) * anim:blink(now, asleep, 3, 0.3)
    anim:poseBone("Eyes", CFrame.new(0, 0, SOCKET_DEPTH * (1 - math.clamp(if asleep then 1 else amount, 0, 1))))
    local color = EYES[state] or EYES.Guardian
    if state == "Weakened" then
        local flicker = 0.5 + 0.5 * math.sin(now * 13) * math.sin(now * 5.3)
        color = Color3.fromRGB(0, 60, 150):Lerp(color, 0.35 + 0.65 * flicker)
    end
    if waking then
        color = Color3.fromRGB(0, 60, 150):Lerp(EYES.Guardian, smooth((waking - 0.3) / 0.5))
    end
    local lit = if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon
    material(anim.iris, lit)
    material(anim.pupils, lit)
    if anim.iris then
        anim.iris.Color = if asleep then STONE else anim.iris.Color:Lerp(color, 0.25)
    end
    if anim.pupils then
        anim.pupils.Color = if asleep then STONE_PUPIL else PUPIL
    end
    if anim.orb then
        material(anim.orb, if asleep then Enum.Material.Glass else Enum.Material.Neon)
        local jade = if asleep then DULL_JADE elseif state == "Weakened" then ORB_DIM:Lerp(ORB, 0.5 + 0.5 * math.sin(now * 7)) else ORB
        anim.orb.Color = if asleep then jade else anim.orb.Color:Lerp(jade, 0.2)
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local function anchor(name)
    local a = Clips.Anchors[name]
    return CFrame.new(a[1], a[2], a[3])
end
local SLAM_SPOT, MOUTH = anchor("Slam"), anchor("Roar")

Rig.Fx = {
    Awaken = function(model)
        local skin = model:FindFirstChild("Skin")
        GuardianFx.shed(skin, style, 30)
        if skin then
            GuardianFx.shake(model:GetPivot().Position, 1.2, 0.7)
        end
        task.delay(1.85, function()
            if model.Parent then
                GuardianFx.puff(model:GetPivot() * CFrame.new(0, 0.5, 8), style, 14, 16, Vector2.new(180, 8), 3, 1)
            end
        end)
    end,
    Slam = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local at = model:GetPivot() * SLAM_SPOT
            GuardianFx.puff(at, style, 22, 22, Vector2.new(80, 8), 3, 1)
            GuardianFx.shockRing(at.Position, style, 11, 0.45)
            GuardianFx.flash(at, style, 10)
            GuardianFx.shake(at.Position, 1.6, 0.45)
            GuardianFx.kick(at.Position, 0.8, 0, 0.3)
        end)
    end,
    Roar = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * MOUTH, style, 14)
            GuardianFx.streaks(pivot * MOUTH, style, 14, 60, 35)
            GuardianFx.shake(pivot.Position, 2.2, 0.9)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 180, style)
        end)
    end,
    Pounce = function(model, windUp, air, _, to)
        GuardianFx.telegraph(to, windUp + air, style)
    end,
    Enrage = function(model)
        GuardianFx.shed(model:FindFirstChild("Skin"), style, 22)
        GuardianFx.shake(model:GetPivot().Position, 1.0, 0.7)
        task.delay(0.16, function()
            if model.Parent then
                GuardianFx.flash(model:GetPivot() * MOUTH, style, 12)
            end
        end)
    end,
    Land = function(model, position)
        GuardianFx.shockRing(position, style, 18, 0.5)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 36, 34, Vector2.new(180, 6), 4, 1.3)
        GuardianFx.shake(position, 3, 0.7)
    end,
}

return Rig

-- The Bamboo Mantis Sage on a real skeleton (tools/blender/guardians/mantis_sage_v2.py): each foreleg a coxa, a spined femur, a tibia blade that shuts against
-- it like a jackknife, and a small tarsus; each walking leg a femur, a tibia and a tarsus on the ground. It holds no egg: no guardian does. Its walk, its run and
-- its moves were solved in Blender so a planted foot stays planted; MantisSageClips.lua (generated) is that work as data, and this rig plays it through
-- GuardianAnim's springs.
--   Dormant   meditating: low, the blades shut in prayer under the chin, head bowed, antennae laid back, its eyes dark;
--   Guardian  awake, blades half shut before its chest, rocking like a leaf in the wind, its head held still, snapping to look;
--   Weakened  sunk low, the blades let fall open, head hanging, trembling;
--   Enraged   the threat display: up on its legs, forelegs raised wide with their spines showing, the robe flared like wings, the abdomen curled up, eyes red.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))
local Clips = require(script.Parent:WaitForChild("MantisSageClips"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}
Rig.Skinned = true

local LEGS = { "MidLeft", "MidRight", "HindLeft", "HindRight" }
Rig.Joints = { "Hips", "Abd1", "Abd2", "Abd3", "Abd4", "Pro1", "Pro2", "Tassel", "Head", "Beard1", "Beard2", "RobeMid1", "RobeMid2" }
for _, tag in { "Left", "Right" } do
    for _, part in { "Coxa", "Femur", "Tibia", "Tarsus" } do
        table.insert(Rig.Joints, tag .. part)
    end
    for _, part in { "Mand", "Ant1", "Ant2" } do
        table.insert(Rig.Joints, tag .. part)
    end
    table.insert(Rig.Joints, "Robe" .. tag .. "1")
    table.insert(Rig.Joints, "Robe" .. tag .. "2")
end
for _, leg in LEGS do
    for _, part in { "Femur", "Tibia", "Tarsus" } do
        table.insert(Rig.Joints, leg .. part)
    end
end

Rig.Poses = Clips.Poses
Rig.Gallop = { 15, 21 } -- walking below the first, running past the second
Rig.LeapAction = "Leap"
Rig.Look = { Joint = "Head", Share = 0.85, Body = "Pro2", BodyShare = 0.15, Limit = 65 }

-- the body and legs follow closely so the feet stay planted; the prothorax trails like a stalk; the head snaps; the forelegs are very quick, as a mantis's are;
-- the robe, the beard, the antennae and the tassel lag behind everything
local LEG = { Freq = 30, Damping = 0.9, Drag = 0 }
local FORE = { Freq = 26, Damping = 0.72, Drag = 0 }
local ROBE = { Freq = 3.0, Damping = 0.34, Drag = 0.55 }
local ROBE_TIP = { Freq = 2.6, Damping = 0.3, Drag = 0.72 }
local ANT = { Freq = 3.4, Damping = 0.28, Drag = 0.4 }
Rig.Springs = {
    Hips = { Freq = 14, Damping = 0.75, Drag = 0 },
    Abd1 = { Freq = 6, Damping = 0.5, Drag = 0.2 },
    Abd2 = { Freq = 5, Damping = 0.45, Drag = 0.3 },
    Abd3 = { Freq = 4.2, Damping = 0.42, Drag = 0.4 },
    Abd4 = { Freq = 3.6, Damping = 0.4, Drag = 0.5 },
    Pro1 = { Freq = 12, Damping = 0.62, Drag = 0.05 },
    Pro2 = { Freq = 10, Damping = 0.58, Drag = 0.1 },
    Head = { Freq = 16, Damping = 0.7, Drag = 0.5 },
    Tassel = { Freq = 2.4, Damping = 0.22, Drag = 0.7 },
    Beard1 = { Freq = 3.2, Damping = 0.32, Drag = 0.5 },
    Beard2 = { Freq = 2.8, Damping = 0.3, Drag = 0.65 },
    RobeMid1 = ROBE, RobeMid2 = ROBE_TIP, RobeLeft1 = ROBE, RobeLeft2 = ROBE_TIP, RobeRight1 = ROBE, RobeRight2 = ROBE_TIP,
    LeftAnt1 = ANT, RightAnt1 = ANT, LeftAnt2 = { Freq = 2.8, Damping = 0.25, Drag = 0.6 }, RightAnt2 = { Freq = 2.8, Damping = 0.25, Drag = 0.6 },
    LeftMand = { Freq = 18, Damping = 0.6, Drag = 0 }, RightMand = { Freq = 18, Damping = 0.6, Drag = 0 },
    LeftCoxa = FORE, RightCoxa = FORE, LeftFemur = FORE, RightFemur = FORE, LeftTibia = { Freq = 34, Damping = 0.7, Drag = 0 }, RightTibia = { Freq = 34, Damping = 0.7, Drag = 0 },
    LeftTarsus = { Freq = 7, Damping = 0.4, Drag = 0.1 }, RightTarsus = { Freq = 7, Damping = 0.4, Drag = 0.1 },
}
for _, leg in LEGS do
    Rig.Springs[leg .. "Femur"] = LEG
    Rig.Springs[leg .. "Tibia"] = LEG
    Rig.Springs[leg .. "Tarsus"] = LEG
end
Rig.Lean = { Joint = "Hips", Accel = 0.05, Bank = 0.03, Max = 4 }
-- planted feet: three turns reach the foot anywhere (the femur's lift and swing, the tibia's bend); left tibias fold on a positive roll. Every pose keeps its
-- feet where it was bound, so when still they hold that spot (Pin); a foot that lands while it walks is locked to that spot in the world until it lifts
Rig.Legs = {}
for _, leg in LEGS do
    table.insert(Rig.Legs, {
        Name = leg, Upper = leg .. "Femur", Lower = leg .. "Tibia", Foot = leg .. "Tarsus", Flat = { leg .. "Tarsus" },
        Axis = 3, Bend = if string.find(leg, "Left") then 1 else -1, Yaw = true, Lock = true, Hop = true,
    })
end
Rig.Style = { Debris = "Leaves", Qi = Color3.fromRGB(0, 200, 110), QiCore = Color3.fromRGB(170, 255, 210) }

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

-- ---------- its life ----------
-- Awake it rocks like a leaf in a breeze, never quite regularly, while its head stays still in the world; the abdomen pumps as it breathes; every few seconds the
-- head snaps to look somewhere else and holds there, the way an insect's does; the antennae test the air. Meditating, only a slow breath moves it.
local RATE = { Guardian = 1.1, Weakened = 1.6, Enraged = 1.9, Returning = 0.9 }

local function gazeOf(anim, now, asleep)
    anim.gazeAt = anim.gazeAt or now
    anim.gaze = anim.gaze or { 0, 0, 0 }
    if not asleep and now >= anim.gazeAt then
        anim.gaze = { -4 + 8 * math.random(), -12 + 24 * math.random(), -9 + 18 * math.random() }
        anim.gazeAt = now + 1.6 + 3.4 * math.random()
    end
    return anim.gaze
end

function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local breath = math.sin(now * (if asleep then 0.9 else 1.5))
    add(pose, "Abd2", 0.8 * breath)
    add(pose, "Abd3", 1.1 * breath)
    if asleep then
        add(pose, "Pro1", 0.25 * breath)
        return
    end
    local idle = 1 - anim.moving
    local rate = RATE[state] or 1
    local reach = if state == "Weakened" then 1.3 elseif state == "Enraged" then 2.6 else 3.4
    -- two rhythms that never line up, so it never looks like a loop
    local rock = (math.sin(now * rate) + 0.45 * math.sin(now * rate * 2.37 + 1.1)) * reach * idle
    local fore = math.sin(now * rate * 0.73 + 0.6) * 0.3 * idle
    add(pose, "Hips", 0, 0.4 * rock, rock, 0, fore)
    add(pose, "Pro1", 0, -0.3 * rock, -0.65 * rock)
    add(pose, "Pro2", 0, -0.1 * rock, -0.35 * rock)
    add(pose, "Abd1", 0, -0.5 * rock, -0.3 * rock)
    add(pose, "Abd3", 0, 0.4 * rock, 0)
    local gaze = gazeOf(anim, now, false)
    local share = if state == "Enraged" then 0.3 else 1
    add(pose, "Head", gaze[1] * share * idle, gaze[2] * share * idle, gaze[3] * share * idle)
    for name, seed in { LeftAnt1 = 0, RightAnt1 = 1.7 } do
        add(pose, name, 5 * math.sin(now * 1.3 + seed) + 3 * math.sin(now * 3.1 + seed * 2), 4 * math.sin(now * 0.9 + seed))
    end
    local chew = math.max(0, math.sin(now * 0.7) - 0.8) / 0.2
    add(pose, "LeftMand", 0, 0, -5 * chew * math.abs(math.sin(now * 9)))
    add(pose, "RightMand", 0, 0, 5 * chew * math.abs(math.sin(now * 9)))
    if state == "Weakened" then
        anim:tremor("Hips", 0.35 * math.sin(now * 37), 0, 0.3 * math.sin(now * 29))
        anim:tremor("Pro1", 0.5 * math.sin(now * 23), 0, 0.4 * math.sin(now * 31))
        add(pose, "LeftTibia", 3 * math.sin(now * 2.1))
        add(pose, "RightTibia", 3 * math.sin(now * 2.6 + 1))
    elseif state == "Enraged" then
        -- the wings shiver and the blades open and close a little, restless
        local shiver = 0.6 + 0.4 * math.sin(now * 1.3)
        anim:tremor("RobeLeft1", 1.6 * shiver * math.sin(now * 41), 1.2 * shiver * math.sin(now * 37))
        anim:tremor("RobeRight1", 1.6 * shiver * math.sin(now * 43), -1.2 * shiver * math.sin(now * 39))
        add(pose, "LeftTibia", 5 * math.sin(now * 3.1))
        add(pose, "RightTibia", 5 * math.sin(now * 3.1 + 2))
    end
end

-- ---------- the moves ----------
-- A whole pose from the table at clip time `clock`, laid over everything else by `weight`; a foot the clip lifts lets go of the ground
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
    return math.min(smooth(t / 0.1), smooth((total - t) / 0.3))
end

local function wingBeat(anim, amount, t)
    if amount > 0 then
        anim:tremor("RobeLeft1", 6 * amount * math.sin(t * 95), 3 * amount * math.sin(t * 95))
        anim:tremor("RobeRight1", 6 * amount * math.sin(t * 95), -3 * amount * math.sin(t * 95))
        anim:tremor("RobeMid1", 3 * amount * math.sin(t * 95))
    end
end

-- each strike's wind-up comes from the server; its clip was made for this long, and scaled to fit
local STRIKES = { Scythe = { 0.6, 1.35 }, BladeWave = { 0.9, 2.0 } }
local BLOW_LEAD = 0.04 -- the springs carry a blow in this late: the clip runs this far ahead, so it lands with its effect

function Rig.actions(anim, pose, now)
    -- waking: the head lifts, the antennae rise, the blades part and click shut
    local t = anim:action("Awaken", 1.8)
    if t then
        playMove(anim, pose, "Awaken", t, smooth((1.8 - t) / 0.3))
        local shiver = envelope(t, 0.15, 1.2, 0.4)
        anim:tremor("RobeLeft1", 3 * shiver * math.sin(t * 47))
        anim:tremor("RobeRight1", 3 * shiver * math.sin(t * 43))
        anim:tremor("RobeMid1", 2 * shiver * math.sin(t * 51))
    end

    -- faltering: the head whips aside, the front of it drops, the blades fall open
    t = anim:action("Weaken", 1.7)
    if t then
        playMove(anim, pose, "Weaken", t, math.min(smooth(t / 0.08), smooth((1.7 - t) / 0.2)))
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
                -- the moment before it strikes, the raised blades quiver
                if t > w - 0.2 and t < w - 0.03 then
                    anim:tremor("LeftTibia", 2.5 * math.sin(t * 61))
                    anim:tremor("RightTibia", 2.5 * math.sin(t * 57))
                end
                if t > w then
                    local shake = envelope(t - w, 0.02, 0.3, 0.2)
                    anim:tremor("Pro1", 1.2 * shake * math.sin(t * 48), 0, 0.7 * shake * math.sin(t * 37))
                end
            end
        end
    end

    -- the leap: its crouch is the wind-up, the rest the time in the air; the wings beat while it flies
    local leap = anim.actions.Leap
    if leap then
        local windUp, air = leap.args[1] or 0.5, leap.args[2] or 1.1
        t = anim:action("Leap", windUp + air + 0.1)
        if t then
            local clock = if t < windUp then t * (0.5 / windUp) else 0.5 + (t - windUp) * (1.1 / air)
            playMove(anim, pose, "Leap", clock, math.min(smooth(t / 0.1), 1))
            wingBeat(anim, envelope(t - windUp, 0.1, air, 0.25), t)
        end
    end

    -- landing: it sinks deep on its legs, the robe flopping shut after it
    t = anim:action("Land", 0.9)
    if t then
        playMove(anim, pose, "Land", t, smooth((0.9 - t) / 0.25))
    end
end

-- ---------- the eyes and the blades' Qi ----------
-- Asleep its pupils are dark and the edges dull jade; awake, Neon (dark Neon renders as a flat black disc). Weakened they flicker, enraged the pupils go red.
local PUPIL = Color3.fromRGB(255, 144, 0)
local RAGE = Color3.fromRGB(255, 40, 20)
local EDGE = Color3.fromRGB(0, 200, 110)

function Rig.setup(anim)
    anim.pupils = anim.model:FindFirstChild("Pupils")
    anim.edges = { anim.model:FindFirstChild("LeftEdge"), anim.model:FindFirstChild("RightEdge") }
end

function Rig.glow(anim, state, now)
    local waking = anim:action("Awaken", 1.8)
    local asleep = (state == "Dormant" or state == "Resting") and not waking
    local pupil = if state == "Enraged" then RAGE else PUPIL
    if state == "Weakened" then
        pupil = Color3.fromRGB(150, 80, 0):Lerp(PUPIL, 0.5 + 0.5 * math.sin(now * 11) * math.sin(now * 4.3))
    end
    if waking then
        pupil = Color3.fromRGB(70, 52, 26):Lerp(PUPIL, smooth((waking - 0.4) / 0.6))
    end
    local pupils = anim.pupils
    if pupils then
        local material = if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon
        if pupils.Material ~= material then
            pupils.Material = material
        end
        pupils.Color = if asleep then Color3.fromRGB(70, 52, 26) else pupils.Color:Lerp(pupil, 0.25)
    end
    local cut = 0
    for name, wind in { Scythe = 0.6, BladeWave = 0.9 } do
        local action = anim.actions[name]
        if action then
            cut = math.max(cut, envelope(now - action.start - (action.args[1] or wind), 0.03, 0.4, 0.3))
        end
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
local function anchor(name)
    local a = Clips.Anchors[name]
    return CFrame.new(a[1], a[2], a[3])
end
local CUT_LEFT, CUT_RIGHT, CHEST = anchor("ScytheLeft"), anchor("ScytheRight"), anchor("Wave")

Rig.Fx = {
    Awaken = function(model)
        GuardianFx.shed(model:FindFirstChild("Robe"), style, 24)
        GuardianFx.shake(model:GetPivot().Position, 0.8, 0.6)
    end,
    Scythe = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * CUT_LEFT, style, 14)
            GuardianFx.crescent(pivot * CUT_RIGHT, style, 14)
            GuardianFx.puff(pivot * CFrame.new(0, 2, (CUT_LEFT.Z + CUT_RIGHT.Z) / 2), style, 14, 16, 70, 3, 1.2)
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

-- Tiangou the Moon-Eater, rebuilt, on a real skeleton (tools/blender/guardians/tiangou_v3.py): a powerful heavenly hound, 14 studs at the
-- shoulder, a deep chest and a heavy shoulder, a coat that is the midnight sky (stars, silvered where the moon falls), white fire for a ruff, a
-- plume and feathered legs, and above its shoulders the eclipse it made: a black disc ringed by a corona, floating on a stalk of fire. 69 bones,
-- four planted legs, a spine of four, ears and a tail of six that lag, a ring that drifts and eight streamers that whip. It holds no egg: no
-- guardian does. Its legs, its walk and gallop and every move were solved in Blender, planted feet and all; TiangouV3Clips.lua (written by the
-- tool) is that work as data, and this rig plays it through GuardianAnim's springs.
--   Dormant   asleep, curled on the cold court, the nose under the tail, the eyes shut, the corona banked low, a slow breath;
--   Guardian  awake and watchful: weight shifting from paw to paw, the ears swivelling alone, the head tracking you with a tilt, the plume
--             swaying, the eclipse turning slowly behind it;
--   Weakened  down on its belly, panting, the ruff flat, the corona guttering;
--   Enraged   the hunting crouch: low, the shoulders over a lowered head, the lips drawn back, the hackles up, the tail up, the eyes red;
--   Returning walking home, the head a little low.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))
local Clips = require(script.Parent:WaitForChild("TiangouV3Clips"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}
Rig.Skinned = true
Rig.ExtraBones = { "Eyes" }
Rig.Joints = Clips.Joints
Rig.Poses = Clips.Poses
Rig.Gallop = { 15, 22 } -- walking below the first (14), galloping past the second (27)
Rig.LeapAction = "MoonLeap"
Rig.Look = { Joint = "Neck3", Share = 0.4, Body = "Neck1", BodyShare = 0.25, Limit = 55 }
-- a blow taken (GuardianReact): the chest takes it, the neck follows in a whip, the head last; the ruff, the ears, the tail and the eclipse show it too
Rig.Hit = {
    Body = "Hips",
    Joints = {
        Chest = { 1, 0 }, Neck1 = { 0.7, 0.02 }, Neck2 = { 0.8, 0.035 }, Neck3 = { 0.9, 0.05 }, Head = { 1, 0.065 },
        Tail1 = { 0.6, 0.03 }, Tail3 = { 0.7, 0.06 }, RuffTopA = { 0.8, 0.05 }, LeftEarA = { 0.6, 0.04 }, RightEarA = { 0.6, 0.04 },
        EclipseRing = { 0.5, 0.08 }, FrontLeftScapula = { 0.5, 0.01 }, FrontRightScapula = { 0.5, 0.01 },
    },
    Scale = 0.9,
}

-- ---------- the springs ----------
-- the body and legs follow their clips closely so the blows land with their effects and the paws stay planted; the neck whips (each bone a beat
-- behind the one below); the ears, the ruff, the feathers, the tail, the stalk, the ring and the streamers trail behind everything (Drag keeps
-- an angle in the world while the parent turns, then lets it swing after)
local SPRING = {
    Hips = { Freq = 12, Damping = 0.75, Drag = 0 },
    SpineA = { Freq = 11, Damping = 0.72, Drag = 0 },
    SpineB = { Freq = 10.5, Damping = 0.7, Drag = 0 },
    Chest = { Freq = 10, Damping = 0.68, Drag = 0 },
    Neck1 = { Freq = 8, Damping = 0.58, Drag = 0.08 },
    Neck2 = { Freq = 8, Damping = 0.55, Drag = 0.14 },
    Neck3 = { Freq = 8.5, Damping = 0.52, Drag = 0.2 },
    Head = { Freq = 10, Damping = 0.55, Drag = 0.22 },
    Jaw = { Freq = 15, Damping = 0.6, Drag = 0 },
    RuffTopA = { Freq = 3.4, Damping = 0.34, Drag = 0.45 },
    RuffTopB = { Freq = 2.8, Damping = 0.3, Drag = 0.65 },
    ChestTuftA = { Freq = 3.4, Damping = 0.34, Drag = 0.4 },
    ChestTuftB = { Freq = 2.8, Damping = 0.3, Drag = 0.6 },
    Stalk1 = { Freq = 4, Damping = 0.42, Drag = 0.25 },
    Stalk2 = { Freq = 3.4, Damping = 0.36, Drag = 0.4 },
    EclipseRing = { Freq = 2.4, Damping = 0.32, Drag = 0.6 },
}
local LEG = { Freq = 30, Damping = 0.9, Drag = 0 }
for _, name in Clips.Joints do
    if not SPRING[name] then
        local spring
        if string.find(name, "Scapula$") then
            spring = { Freq = 14, Damping = 0.7, Drag = 0 }
        elseif string.find(name, "Toes$") then
            spring = { Freq = 22, Damping = 0.8, Drag = 0 }
        elseif string.find(name, "Feather$") then
            spring = { Freq = 3, Damping = 0.32, Drag = 0.55 }
        elseif string.find(name, "Upper$") or string.find(name, "Lower$") or string.find(name, "Paw$") or string.find(name, "Thigh$") or string.find(name, "Shin$")
            or string.find(name, "Meta$") then
            spring = LEG
        elseif string.find(name, "^Tail%d$") then
            local k = tonumber(string.sub(name, -1))
            spring = { Freq = 5.2 - 0.5 * k, Damping = 0.5 - 0.04 * k, Drag = 0.1 + 0.13 * k }
        elseif string.find(name, "Ear[AB]$") then
            spring = if string.find(name, "A$") then { Freq = 11, Damping = 0.42, Drag = 0.1 } else { Freq = 9, Damping = 0.36, Drag = 0.3 }
        elseif string.find(name, "^Stream%d") then
            spring = if string.find(name, "A$") then { Freq = 3.2, Damping = 0.3, Drag = 0.4 } else { Freq = 2.6, Damping = 0.26, Drag = 0.62 }
        elseif string.find(name, "Ruff") then
            spring = if string.find(name, "1$") then { Freq = 3.4, Damping = 0.34, Drag = 0.4 } else { Freq = 2.8, Damping = 0.3, Drag = 0.6 }
        end
        SPRING[name] = spring
    end
end
Rig.Springs = SPRING
Rig.Lean = { Joint = "Chest", Accel = 0.07, Bank = 0.05, Max = 6 }
-- planted feet: a foreleg folds on a positive turn (the elbow behind), a hind leg on a negative one (the stifle in front); a pastern or a metatarsus
-- below keeps its posed lean, the toes stay flat. A paw that has landed is held to its spot in the world until it lifts (Lock)
local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }
Rig.Legs = {}
for _, leg in LEGS do
    local front = string.sub(leg, 1, 5) == "Front"
    table.insert(Rig.Legs, {
        Name = leg,
        Upper = leg .. (if front then "Upper" else "Thigh"),
        Lower = leg .. (if front then "Lower" else "Shin"),
        Chain = { leg .. (if front then "Paw" else "Meta") },
        Foot = leg .. "Toes",
        Flat = { leg .. "Toes" },
        Axis = 1,
        Bend = if front then 1 else -1,
        Pin = 0,
        Lock = true,
    })
end
Rig.Style = { Debris = "Frost", Qi = Color3.fromRGB(110, 190, 255), QiCore = Color3.fromRGB(235, 248, 255) }

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

-- how firmly a paw is held to the ground at this point of its gait: from its touchdown (offset) for the stance (duty) of the cycle
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
-- Awake it stands square: its weight moves slowly from paw to paw, each ear swivels on its own, it studies what it watches (the head snaps to a new
-- angle, tilted, and holds, the body still under it), the plume of its tail sways and the eclipse turns behind it. Asleep, only the slow breath
-- and the banked corona.
local function gazeOf(anim, now, calm)
    anim.gazeAt = anim.gazeAt or now
    anim.gaze = anim.gaze or { 0, 0, 0 }
    local dt = math.clamp(now - (anim.gazeSeen or now), 0, 0.2)
    anim.gazeSeen = now
    if calm then
        local keep = math.exp(-3 * dt)
        for i = 1, 3 do
            anim.gaze[i] *= keep
        end
        anim.gazeAt = now + 1
    elseif now >= anim.gazeAt then
        local last = anim.gaze
        anim.gaze = { -4 + 7 * math.random(), (if last[2] > 0 then -1 else 1) * (5 + 14 * math.random()), (if last[3] > 0 then -1 else 1) * (3 + 9 * math.random()) }
        anim.gazeAt = now + 1.6 + 3.8 * math.random()
    end
    return anim.gaze
end

local EARS = { { "LeftEarA", "LeftEarB", 0 }, { "RightEarA", "RightEarB", 2.7 } }
local TAILS = { "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6" }
local FEATHERS = { "FrontLeftFeather", "FrontRightFeather", "BackLeftFeather", "BackRightFeather" }

function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 1.5 elseif asleep then 0.2 elseif state == "Enraged" then 0.5 else 0.3
    local breath = math.sin(now * rate * 2 * math.pi)
    local deep = if state == "Weakened" then 2 elseif asleep then 1.2 else 1
    add(pose, "Chest", 1.3 * breath * deep)
    add(pose, "SpineB", 0.6 * breath * deep)
    add(pose, "Hips", 0, 0, 0, 0.1 * breath * deep)
    add(pose, "Neck2", 0.5 * breath)
    -- a lying hound's legs are folded under it, not planted: the weights of its three lying states lift them from the ground
    local lying = math.clamp((anim.weights.Dormant or 0) + (anim.weights.Resting or 0) + (anim.weights.Weakened or 0), 0, 1)
    if lying > 0.01 then
        for _, leg in LEGS do
            anim:lift(leg, lying)
        end
    end
    -- the plume and the eclipse's drift: never quite still, out of step with each other
    local slow = if asleep then 0.3 else 1
    for i, joint in TAILS do
        add(pose, joint, 0.7 * slow * math.sin(now * 0.8 - i * 0.5), 2.2 * slow * math.sin(now * 0.55 - i * 0.6))
    end
    add(pose, "RuffTopA", 1.4 * math.sin(now * 1.1), 1.2 * math.sin(now * 0.7))
    add(pose, "RuffTopB", 2.0 * math.sin(now * 1.1 - 0.7), 1.6 * math.sin(now * 0.7 - 0.5))
    add(pose, "ChestTuftA", 1.5 * math.sin(now * 0.9 + 1))
    add(pose, "ChestTuftB", 2.2 * math.sin(now * 0.9 + 0.2))
    for k, joint in FEATHERS do
        add(pose, joint, 1.6 * math.sin(now * 0.8 + k), 0, 1.2 * math.sin(now * 0.6 + k * 1.7))
    end
    add(pose, "Stalk1", 1.0 * math.sin(now * 0.4), 1.5 * math.sin(now * 0.27))
    add(pose, "Stalk2", 1.4 * math.sin(now * 0.4 - 0.6), 2.0 * math.sin(now * 0.27 - 0.5))
    -- the ring floats: it turns slowly on its stalk and tilts, lagging whatever the body does
    add(pose, "EclipseRing", 2.0 * math.sin(now * 0.31), 16 * slow * math.sin(now * 0.17), 5 * math.sin(now * 0.23))
    for i = 1, 8 do
        add(pose, "Stream" .. i .. "A", 2.4 * math.sin(now * 0.9 + i), 1.5 * math.sin(now * 0.7 + i * 0.8))
        add(pose, "Stream" .. i .. "B", 4.0 * math.sin(now * 0.9 + i - 0.8), 2.5 * math.sin(now * 0.7 + i * 0.8 - 0.6))
    end
    if asleep then
        return
    end
    local idle = 1 - anim.moving
    -- the weight shifts from paw to paw, slowly and never quite regularly
    local shift = (math.sin(now * 0.23) + 0.5 * math.sin(now * 0.41 + 1.3)) * idle
    add(pose, "Hips", 0, 0.7 * shift, 1.5 * shift)
    add(pose, "SpineA", 0, -0.4 * shift, -0.7 * shift)
    add(pose, "Chest", 0, -0.5 * shift, -0.9 * shift)
    -- each ear swivels alone, and now and then flicks
    for _, ear in EARS do
        local flick = math.max(0, math.sin(now * 0.37 + ear[3]) - 0.94) / 0.06
        add(pose, ear[1], 6 * math.sin(now * 0.7 + ear[3]) + 22 * flick * idle, 0, 7 * math.sin(now * 0.53 + ear[3] * 1.3))
        add(pose, ear[2], 8 * flick * idle, 0, 3 * math.sin(now * 0.9 + ear[3]))
    end
    -- the studying look: the head snaps to a new angle, tilted, and holds; the neck and chest stay
    local gaze = gazeOf(anim, now, state == "Weakened" or state == "Enraged")
    local share = (if state == "Enraged" then 0.35 else 1) * idle
    add(pose, "Neck3", gaze[1] * 0.3 * share, gaze[2] * 0.3 * share, gaze[3] * 0.25 * share)
    add(pose, "Head", gaze[1] * 0.5 * share, gaze[2] * 0.5 * share, gaze[3] * 0.75 * share)
    if state == "Weakened" then
        local pant = math.abs(math.sin(now * 1.5 * math.pi))
        add(pose, "Jaw", -9 * pant)
        anim:tremor("Chest", 0.5 * math.sin(now * 31), 0, 0.4 * math.sin(now * 23))
        add(pose, "Head", 1.5 * math.sin(now * 1.8))
    elseif state == "Enraged" then
        -- restless: the tail lashes, the ruff quivers, the lip trembles over the teeth
        add(pose, "Tail1", 0, 6 * math.sin(now * 2.3))
        add(pose, "Tail3", 0, 10 * math.sin(now * 2.3 - 0.7))
        anim:tremor("RuffTopA", 2.2 * math.sin(now * 33))
        anim:tremor("RuffTopB", 2.8 * math.sin(now * 29 + 1))
        anim:tremor("Jaw", -3 * math.abs(math.sin(now * 17)))
        add(pose, "Neck3", 0, 3 * math.sin(now * 0.9))
    end
end

-- ---------- the moves ----------
-- A move's tracks are keyframes [frame, values...]: the pose at clip time `clock` is read between them and laid over everything else by
-- `weight`; a foot the clip lifts lets go of the ground.
local function trackAt(track, frame)
    local n = #track
    if frame <= track[1][1] then
        return track[1], track[1], 0
    end
    if frame >= track[n][1] then
        return track[n], track[n], 0
    end
    local lo, hi = 1, n
    while hi - lo > 1 do
        local mid = (lo + hi) // 2
        if track[mid][1] <= frame then
            lo = mid
        else
            hi = mid
        end
    end
    local a, b = track[lo], track[hi]
    return a, b, (frame - a[1]) / (b[1] - a[1])
end

local function playMove(anim, pose, name, clock, weight)
    local move = Clips.Moves[name]
    local frame = math.clamp(clock * Clips.Fps, 0, move.Length * Clips.Fps)
    for joint, track in move.Tracks do
        local p = pose[joint]
        if p then
            local a, b, u = trackAt(track, frame)
            for k = 2, #a do
                local value = a[k] + (b[k] - a[k]) * u
                local gap = value - p[k - 1]
                if k <= 4 then
                    gap = (gap + 180) % 360 - 180 -- the clip may have come round a whole turn: blended the short way
                end
                p[k - 1] += gap * weight
            end
        end
    end
    for _, leg in LEGS do
        for _, span in move.Plants[leg] do
            if frame >= span[1] and frame <= span[2] then
                anim:lift(leg, weight)
            end
        end
    end
end

local function blend(t, total)
    return math.min(smooth(t / 0.1), smooth((total - t) / 0.25))
end

-- what a blow leaves swinging: the plume and the ruff whip on past the stop, the ears snap, the corona's streamers ripple
local function followThrough(pose, after, strength)
    local k = GuardianAnim.damped(after, 3.0, 2.6) * strength
    for i, joint in TAILS do
        add(pose, joint, -2.5 * i * k, 3 * i * k)
    end
    add(pose, "RuffTopA", -12 * k)
    add(pose, "RuffTopB", -16 * k)
    add(pose, "ChestTuftA", 10 * k)
    add(pose, "ChestTuftB", 14 * k)
    add(pose, "LeftEarA", 14 * k, 0, -8 * k)
    add(pose, "RightEarA", 14 * k, 0, 8 * k)
    for i = 1, 8 do
        add(pose, "Stream" .. i .. "A", 6 * k, 3 * k)
        add(pose, "Stream" .. i .. "B", 10 * k, 5 * k)
    end
    for _, joint in FEATHERS do
        add(pose, joint, 8 * k)
    end
end

-- each strike's wind-up comes from the server; its clip was made for this long, and scaled to fit
local STRIKES = { Bite = { 0.5, 1.8 }, EclipseHowl = { 1.0, 2.6 } }
local HOLD = { Bite = 0.1, EclipseHowl = 0.11 }
local BLOW_LEAD = 0.03 -- the springs carry a blow in this late: the clip runs this far ahead, so it lands with its effect

function Rig.actions(anim, pose, now)
    -- waking: the head lifts from the curl, the forelegs push up and then the haunches, a shake from the nose to the tail throws the ruff and the
    -- plume out, a stretch, the ears coming up one after the other
    local t = anim:action("Awaken", 2.8)
    if t then
        playMove(anim, pose, "Awaken", t, smooth((2.8 - t) / 0.3))
        local shake = envelope(t - 1.85, 0.05, 0.5, 0.2)
        followThrough(pose, t - 2.3, 1.0 * shake)
        anim:tremor("Chest", 1.0 * shake * math.sin(t * 41), 0, 0.8 * shake * math.sin(t * 37))
        anim:tremor("Head", 0, 1.4 * envelope(t - 0.7, 0.1, 0.5, 0.2) * math.sin(t * 19))
    end

    -- faltering: the blow it cannot take: it staggers, the forelegs buckle, it sinks onto the court, the corona gutters
    t = anim:action("Weaken", 1.9)
    if t then
        playMove(anim, pose, "Weaken", t, math.min(smooth(t / 0.08), smooth((1.9 - t) / 0.2)))
        anim:contact("Weaken", 0.95, 0.09)
        followThrough(pose, t - 0.95, 0.9)
        anim:tremor("Chest", 0, 0, 2.4 * envelope(t, 0.15, 0.9, 0.4) * math.sin(t * 9))
    end

    -- it has seen the egg taken: it snaps round, drops into the hunting crouch with a snarl from the throat, the ruff and the tail bristling
    t = anim:action("Enrage", 1.3)
    if t then
        playMove(anim, pose, "Enrage", t, math.min(smooth(t / 0.06), smooth((1.3 - t) / 0.25)))
        local snarl = envelope(t - 0.2, 0.05, 0.8, 0.2)
        anim:tremor("Head", 2.0 * snarl * math.sin(t * 40), 1.4 * snarl * math.sin(t * 31))
        anim:tremor("Jaw", -5 * snarl * math.abs(math.sin(t * 22)))
        anim:tremor("RuffTopA", 4 * snarl * math.sin(t * 45))
        anim:tremor("Chest", 0.8 * snarl * math.sin(t * 37), 0, 0.6 * snarl * math.sin(t * 29))
        followThrough(pose, t - 0.14, 0.7)
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
                if name == "Bite" then
                    -- the held beat before the lunge: the drawn-back head trembles, the lips tight, the ruff bristling
                    local tense = envelope(t - 0.15 * w, 0.1, 0.45 * w, 0.06)
                    anim:tremor("Head", 0.8 * tense * math.sin(t * 43), 0.9 * tense * math.sin(t * 37))
                    anim:tremor("Neck2", 0.6 * tense * math.sin(t * 41))
                    anim:tremor("RuffTopA", 3 * tense * math.sin(t * 47))
                    anim:tremor("Chest", 0.5 * tense * math.sin(t * 39), 0, 0.3 * tense * math.sin(t * 31))
                else
                    -- the rear: the chest swells with the breath that is drawn, trembling; then the howl itself shudders through the head and ruff
                    local build = envelope(t - 0.3 * w, 0.2, 0.7 * w, 0.05)
                    anim:tremor("Chest", 1.0 * build * math.sin(t * 37), 0, 0.7 * build * math.sin(t * 29))
                    anim:tremor("Head", 1.2 * build * math.sin(t * 33))
                    if t >= w then
                        local burst = envelope(t - w, 0.04, 0.9, 0.3)
                        anim:tremor("Head", 2.4 * burst * math.sin(t * 40), 1.8 * burst * math.sin(t * 29))
                        anim:tremor("Jaw", 2.8 * burst * math.sin(t * 53))
                        anim:tremor("Chest", 1.6 * burst * math.sin(t * 47))
                        -- the eclipse swells and the ring leaps forward and up with the howl
                        local pulse = envelope(t - w, 0.04, 1.0, 0.4)
                        add(pose, "EclipseRing", 0, 0, 0, 1.4 * pulse, -1.6 * pulse)
                        for i = 1, 8 do
                            anim:tremor("Stream" .. i .. "B", 8 * burst * math.sin(t * (31 + i)), 4 * burst * math.sin(t * (23 + i)))
                        end
                    end
                end
                -- the blow lands: the whole hound stops for an instant on it (the heavier, the longer), then what hangs off it whips on past the stop
                anim:contact(name, w, HOLD[name])
                local after = t - w
                if after > 0 then
                    local shake = envelope(after, 0.02, 0.4, 0.25)
                    anim:tremor("Chest", 1.2 * shake * math.sin(t * 48), 0, 0.7 * shake * math.sin(t * 37))
                    followThrough(pose, after, if name == "EclipseHowl" then 1.1 else 1.0)
                    add(pose, "Hips", 0, 0, 0, -0.3 * envelope(after, 0.03, 0.4, 0.3))
                end
            end
        end
    end

    -- the leap: its crouch and spring are the wind-up, the rest the time in the air
    local leap = anim.actions.MoonLeap
    if leap then
        local windUp, air = leap.args[1] or 0.55, leap.args[2] or 1.2
        t = anim:action("MoonLeap", windUp + air + 0.1)
        if t then
            local clock = if t < windUp then t * (0.55 / windUp) else 0.55 + (t - windUp) * (1.2 / air)
            playMove(anim, pose, "MoonLeap", clock, math.min(smooth(t / 0.1), 1))
            -- coiled in the crouch the haunches tremble; in the air the plume and the streamers stream
            local coil = envelope(t - 0.3 * windUp, 0.1, 0.6 * windUp, 0.08)
            anim:tremor("Hips", 0.5 * coil * math.sin(t * 43), 0, 0.4 * coil * math.sin(t * 37))
            if t > windUp then
                local fly = envelope(t - windUp, 0.1, air, 0.25)
                for i, joint in TAILS do
                    anim:tremor(joint, 1.5 * fly * math.sin(t * (17 + 2 * i)), 2.0 * fly * math.sin(t * (13 + i)))
                end
                for i = 1, 8 do
                    anim:tremor("Stream" .. i .. "B", 3 * fly * math.sin(t * (21 + i)), 2 * fly * math.sin(t * (17 + i)))
                end
            end
        end
    end

    -- landing: the forepaws take the ground first, the forelegs absorb, the spine compresses, the hind legs come through, a skid and a settle
    t = anim:action("Land", 1.2)
    if t then
        playMove(anim, pose, "Land", t, smooth((1.2 - t) / 0.25))
        anim:contact("Land", 0.05, 0.1)
        followThrough(pose, t - 0.05, 1.2)
    end
end

-- ---------- the eyes and the eclipse ----------
-- The eyes are gold: lit awake, dark asleep; they slide back into their sockets to blink and go red when it rages. The corona is banked to embers
-- asleep, breathes awake, gutters weakened, runs red-white enraged and flares at every blow; the ring's gold edge follows it. The black disc stays black.
local EYE = Color3.fromRGB(255, 178, 30)
local EYE_RED = Color3.fromRGB(255, 56, 26)
local CORONA = Color3.fromRGB(220, 239, 255)
local CORONA_HOT = Color3.fromRGB(255, 252, 240)
local CORONA_RED = Color3.fromRGB(255, 168, 140)
local CORONA_EMBER = Color3.fromRGB(70, 84, 130)
local CORE = Color3.fromRGB(255, 233, 168)
local CORE_RED = Color3.fromRGB(255, 120, 80)
local CORE_EMBER = Color3.fromRGB(140, 70, 40)
local OPEN = { Guardian = 1, Weakened = 1, Enraged = 0.75, Returning = 0.95 }
local SOCKET_DEPTH = 0.22

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.pupils = model:FindFirstChild("Pupils")
    anim.corona = model:FindFirstChild("Corona")
    anim.core = model:FindFirstChild("CoronaCore")
    anim.disc = model:FindFirstChild("Eclipse")
end

function Rig.glow(anim, state, now)
    local waking = anim:action("Awaken", 2.8)
    local asleep = (state == "Dormant" or state == "Resting") and not waking
    local amount = (OPEN[state] or 1) * anim:blink(now, asleep, 4, 0.3)
    if waking then
        amount *= smooth((waking - 1.0) / 0.5) -- the eyes open gold as it raises its head
    end
    anim:poseBone("Eyes", CFrame.new(0, 0, SOCKET_DEPTH * (1 - math.clamp(amount, 0, 1))))
    local eye = if state == "Enraged" then EYE_RED else EYE
    for _, part in { anim.iris, anim.pupils } do
        if part then
            part.Transparency = if asleep then 1 else 0
        end
    end
    if anim.iris then
        anim.iris.Color = anim.iris.Color:Lerp(eye, 0.25)
    end
    -- the corona
    local breath = 0.5 + 0.5 * math.sin(now * 0.3 * 2 * math.pi)
    local fade = if asleep then 0.62 elseif state == "Weakened" then 0.3 + 0.45 * math.abs(math.sin(now * 5) * math.sin(now * 1.9))
        elseif state == "Enraged" then 0.04 + 0.14 * math.abs(math.sin(now * 11) * math.sin(now * 4.3)) else 0.1 + 0.12 * (1 - breath)
    local hot = if state == "Enraged" then 0.6 + 0.4 * breath else 0.12 * breath
    if waking then
        -- the corona catches light as the head comes up
        local lit = smooth((waking - 0.9) / 1.2)
        fade = fade + (0.1 - fade) * lit
        hot = math.max(hot, envelope(waking - 1.85, 0.1, 0.6, 0.4))
    end
    for name, wind in { Bite = 0.5, EclipseHowl = 1.0, Enrage = 0.2 } do
        local action = anim.actions[name]
        if action then
            local flare = envelope(now - action.start - (action.args[1] or wind), 0.05, if name == "EclipseHowl" then 1.2 else 0.5, 0.6)
            hot = math.max(hot, flare)
            fade *= 1 - flare
        end
    end
    local tint = (if state == "Enraged" then CORONA_RED else CORONA):Lerp(CORONA_HOT, hot * (if state == "Enraged" then 0.5 else 1))
    if asleep then
        tint = CORONA_EMBER
    end
    local coreTint = if asleep then CORE_EMBER elseif state == "Enraged" then CORE_RED else CORE
    if anim.corona then
        anim.corona.Transparency += (fade - anim.corona.Transparency) * 0.3
        anim.corona.Color = anim.corona.Color:Lerp(tint, 0.3)
    end
    if anim.core then
        anim.core.Transparency += (math.min(fade, 0.8) * 0.7 - anim.core.Transparency) * 0.3
        anim.core.Color = anim.core.Color:Lerp(coreTint, 0.3)
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local function anchor(name)
    local a = Clips.Anchors[name]
    return CFrame.new(a[1], a[2], a[3])
end
local BITE_MOUTH, BITE_GROUND = anchor("BiteMouth"), anchor("BiteGround")
local HOWL_MOUTH, ECLIPSE = anchor("HowlMouth"), anchor("Eclipse")
local MOUTH, CHEST = anchor("Mouth"), anchor("Chest")

Rig.Fx = {
    Awaken = function(model)
        local pelt = model:FindFirstChild("Pelt")
        GuardianFx.shed(pelt, style, 30)
        task.delay(1.85, function()
            if model.Parent then
                local p = model:GetPivot()
                -- the shake from the nose to the tail throws frost off its coat
                GuardianFx.shed(pelt, style, 40)
                GuardianFx.puff(p * CFrame.new(0, 0.6, 0), style, 18, 18, Vector2.new(180, 8), 4, 1.2)
                GuardianFx.flash(p * ECLIPSE, style, 22)
                GuardianFx.shake(p.Position, 1.2, 0.7)
            end
        end)
    end,
    Bite = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * BITE_MOUTH, style, 12)
            GuardianFx.streaks(pivot * BITE_MOUTH, style, 12, 50, 40)
            GuardianFx.puff(pivot * BITE_GROUND, style, 16, 16, Vector2.new(80, 8), 3, 1)
            GuardianFx.shake(pivot.Position, 1.6, 0.4)
            GuardianFx.kick(pivot.Position, 0.8, 0, 0.3)
        end)
    end,
    EclipseHowl = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * ECLIPSE, style, 34)
            GuardianFx.flash(pivot * HOWL_MOUTH, style, 16)
            GuardianFx.streaks(pivot * HOWL_MOUTH, style, 14, 60, 35)
            GuardianFx.shake(pivot.Position, 2.4, 0.9)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 360, style)
        end)
    end,
    MoonLeap = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 26, 22, Vector2.new(180, 10), 4, 1.3)
            GuardianFx.shake(from, 1.6, 0.5)
        end)
    end,
    Land = function(model, position)
        GuardianFx.shockRing(position, style, 20, 0.55)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 40, 34, Vector2.new(180, 6), 5, 1.5)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 16)
        GuardianFx.shake(position, 3.2, 0.9)
    end,
    Weaken = function(model)
        task.delay(0.95, function()
            if model.Parent then
                local pivot = model:GetPivot()
                GuardianFx.shockRing(pivot.Position, style, 12, 0.5)
                GuardianFx.puff(pivot * CHEST, style, 18, 16, Vector2.new(180, 6), 4, 1.2)
                GuardianFx.shake(pivot.Position, 1.8, 0.6)
            end
        end)
    end,
    Enrage = function(model)
        local pivot = model:GetPivot()
        GuardianFx.flash(pivot * ECLIPSE, style, 28)
        GuardianFx.flash(pivot * MOUTH, style, 12)
        task.delay(0.45, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.shockRing(p.Position, style, 14, 0.5)
                GuardianFx.puff(p * CFrame.new(0, 0.5, -5), style, 20, 18, Vector2.new(180, 6), 4, 1.2)
                GuardianFx.shake(p.Position, 1.8, 0.6)
            end
        end)
    end,
}

return Rig

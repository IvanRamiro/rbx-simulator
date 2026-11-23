-- The Cinder Roc on a real skeleton (tools/blender/guardians/cinder_roc.py): a fire-bird of charcoal plumage lit from underneath, on 78 bones,
-- two wings of a real arm (shoulder, upper arm, forearm, hand) carrying ten primaries and secondaries on chains that lag and ripple, a crest of
-- ember plumes, five ribbons of tail, digitigrade legs with feathered trousers and scythe talons. It holds no egg: no guardian does.
-- Its legs, its walk and run and every move were solved in Blender, planted feet and all; CinderRocClips.lua (written by the tool) is that
-- work as data, and this rig plays it through GuardianAnim's springs.
--   Dormant   roosting: low on its legs, the wings drawn round it like a cloak, the head tucked back under the near wing, the veins dim;
--   Guardian  awake and proud: weight on one leg, the head snapping to look and holding (the body still under it), a wing preened now and
--             then, the wings half spread when it is displeased;
--   Weakened  worn out: sunk onto its breast, one wing dragging, the head low, panting, the eyes flickering;
--   Enraged   the threat display: up on its legs, the wings half spread and held high, the head low on a coiled neck, the crest erect;
--   Returning walking home with the wings still half open.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))
local Clips = require(script.Parent:WaitForChild("CinderRocClips"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}
Rig.Skinned = true
Rig.ExtraBones = { "Eyes" }
Rig.Joints = Clips.Joints
Rig.Poses = Clips.Poses
Rig.Gallop = { 12, 18 } -- walking below the first, running past the second
Rig.LeapAction = "TalonDive"
Rig.Look = { Joint = "Neck2", Share = 0.5, Body = "Chest", BodyShare = 0.2, Limit = 55 }
-- a blow taken (GuardianReact): the chest takes it, the neck follows in a whip, the head last; the crest and the shoulders show it too
Rig.Hit = {
    Body = "Hips",
    Joints = {
        Chest = { 1, 0 }, Neck1 = { 0.7, 0.02 }, Neck2 = { 0.8, 0.035 }, Neck3 = { 0.9, 0.05 }, Head = { 1, 0.065 },
        TailBase = { 0.7, 0.04 }, CrestA = { 0.8, 0.08 }, LeftClavicle = { 0.5, 0.01 }, RightClavicle = { 0.5, 0.01 },
    },
    Scale = 0.85,
}

-- ---------- the springs ----------
-- the body follows its clips closely so the blows land with their effects; the neck whips (each bone a beat behind the one below); the wings'
-- arm bones are quick, their feathers lag and ripple on drag; the tail's ribbons, the crest and the trousers trail behind everything
local SPRING = {
    Hips = { Freq = 10, Damping = 0.7, Drag = 0 },
    Spine = { Freq = 9, Damping = 0.65, Drag = 0 },
    Chest = { Freq = 8.5, Damping = 0.6, Drag = 0 },
    Neck1 = { Freq = 8, Damping = 0.55, Drag = 0.08 },
    Neck2 = { Freq = 8, Damping = 0.5, Drag = 0.14 },
    Neck3 = { Freq = 8.5, Damping = 0.5, Drag = 0.2 },
    Head = { Freq = 11, Damping = 0.55, Drag = 0.24 },
    Jaw = { Freq = 14, Damping = 0.6, Drag = 0 },
    TailBase = { Freq = 6, Damping = 0.5, Drag = 0.1 },
}
local LEG = { Freq = 30, Damping = 0.9, Drag = 0 }
for _, name in Clips.Joints do
    if not SPRING[name] then
        local base = string.gsub(string.gsub(name, "^Left", ""), "^Right", "")
        local spring
        if base == "Clavicle" then
            spring = { Freq = 14, Damping = 0.7, Drag = 0 }
        elseif base == "UpperArm" then
            spring = { Freq = 15, Damping = 0.7, Drag = 0.04 }
        elseif base == "Forearm" then
            spring = { Freq = 15, Damping = 0.65, Drag = 0.08 }
        elseif base == "Hand" then
            spring = { Freq = 13, Damping = 0.6, Drag = 0.12 }
        elseif string.find(base, "^Prim%dA$") then
            spring = { Freq = 8, Damping = 0.4, Drag = 0.3 }
        elseif string.find(base, "^Prim%dB$") then
            spring = { Freq = 6.5, Damping = 0.32, Drag = 0.5 }
        elseif string.find(base, "^Sec%dA$") then
            spring = { Freq = 8, Damping = 0.4, Drag = 0.25 }
        elseif string.find(base, "^Sec%dB$") then
            spring = { Freq = 6, Damping = 0.3, Drag = 0.45 }
        elseif base == "Thigh" or base == "Shin" or base == "Tarsus" or base == "Foot" then
            spring = LEG
        elseif base == "Toes" or base == "Hallux" then
            spring = { Freq = 22, Damping = 0.8, Drag = 0 }
        elseif base == "Trouser" then
            spring = { Freq = 3, Damping = 0.32, Drag = 0.55 }
        elseif string.find(base, "Tail") then
            local last = string.sub(base, -1)
            spring = if last == "A" then { Freq = 3.4, Damping = 0.3, Drag = 0.4 }
                elseif last == "B" then { Freq = 3, Damping = 0.28, Drag = 0.6 }
                else { Freq = 2.6, Damping = 0.26, Drag = 0.75 }
        elseif string.find(base, "Crest") then
            spring = if string.sub(base, -1) == "A" then { Freq = 3.6, Damping = 0.3, Drag = 0.45 } else { Freq = 3, Damping = 0.26, Drag = 0.65 }
        end
        SPRING[name] = spring
    end
end
Rig.Springs = SPRING
Rig.Lean = { Joint = "Chest", Accel = 0.08, Bank = 0.04, Max = 5 }
-- planted feet: three bones fold the leg (the shin on a negative turn; the tarsus below it keeps its posed lean, a hock), the foot stays flat
Rig.Legs = {
    { Name = "Left", Upper = "LeftThigh", Lower = "LeftShin", Chain = { "LeftTarsus" }, Foot = "LeftFoot", Flat = { "LeftFoot" }, Axis = 1, Bend = -1, Pin = 0 },
    { Name = "Right", Upper = "RightThigh", Lower = "RightShin", Chain = { "RightTarsus" }, Foot = "RightFoot", Flat = { "RightFoot" }, Axis = 1, Bend = -1, Pin = 0 },
}
Rig.Style = { Debris = "Cinders", Qi = Color3.fromRGB(255, 96, 10), QiCore = Color3.fromRGB(255, 205, 110) }

-- ---------- the gaits ----------
local WALK, RUN = Clips.Gaits.walk, Clips.Gaits.run
local GAIT_JOINTS = {}
for joint in WALK do
    GAIT_JOINTS[joint] = true
end
for joint in RUN do
    GAIT_JOINTS[joint] = true
end
local CYCLE = 24

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
    local at = anim.phase * CYCLE
    local i = math.floor(at) % CYCLE + 1
    local j = i % CYCLE + 1
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
    -- a foot is held to the ground from touchdown to toe-off: the left comes down at phase 0, the right at a half
    local stance = Clips.Stance.walk + (Clips.Stance.run - Clips.Stance.walk) * g
    for _, leg in { { "Left", 0 }, { "Right", 0.5 } } do
        local p = ((anim.phase + leg[2]) % 1) / stance
        local held = smooth((p - 0.02) / 0.06) * (1 - smooth((p - 0.94) / 0.06))
        anim:lift(leg[1], moving * (1 - held))
    end
end

-- ---------- its life ----------
-- Awake it holds its weight on one leg and shifts it now and then; it studies what it watches one eye at a time: the head snaps to a new angle
-- (tilted, as a bird's is) and holds there while the body stays still under it; now and then it half spreads its wings, displeased, or turns
-- its head back to preen one; the ribbons of its tail and the plumes of its crest are never quite still.
local function lay(pose, table_, weight)
    for joint, values in table_ do
        local p = pose[joint]
        if p then
            for k = 1, #values do
                local gap = values[k] - p[k]
                if k <= 3 then
                    gap = (gap + 180) % 360 - 180
                end
                p[k] += gap * weight
            end
        end
    end
end

local GAZE_JOINTS = { { "Neck2", 0.25 }, { "Neck3", 0.3 }, { "Head", 0.45 } }

local function gazeOf(anim, now, calm)
    anim.gazeAt = anim.gazeAt or now
    anim.gaze = anim.gaze or { 0, 0, 0 }
    local dt = math.clamp(now - (anim.gazeSeen or now), 0, 0.2)
    anim.gazeSeen = now
    if calm then
        -- worn out or enraged: it stops studying, and the last tilt eases out instead of staying for the whole state
        local keep = math.exp(-3 * dt)
        for i = 1, 3 do
            anim.gaze[i] *= keep
        end
        anim.gazeAt = now + 1
    elseif now >= anim.gazeAt then
        local last = anim.gaze
        anim.gaze = { -5 + 9 * math.random(), (if last[2] > 0 then -1 else 1) * (6 + 18 * math.random()), (if last[3] > 0 then -1 else 1) * (4 + 12 * math.random()) }
        anim.gazeAt = now + 1.4 + 3.6 * math.random()
    end
    return anim.gaze
end

local function flourish(anim, now, state)
    -- a held flourish now and then, never while moving or in a move: { name, start, length }
    local idle = state == "Guardian" and anim.moving < 0.05 and next(anim.actions) == nil
    anim.nextFlourish = anim.nextFlourish or now + 8 + 8 * math.random()
    if idle and not anim.flourish and now >= anim.nextFlourish then
        anim.flourish = { if math.random() < 0.5 then "Display" else "Preen", now, if math.random() < 0.5 then 3.0 else 3.6 }
        anim.nextFlourish = now + 14 + 16 * math.random()
    end
    local f = anim.flourish
    if not f then
        return nil, 0
    end
    local t = now - f[2]
    if t > f[3] or not idle then
        anim.flourish = nil
        return nil, 0
    end
    return f[1], envelope(t, 0.8, f[3], 0.9), t
end

-- the tail ribbons' joints (TailnA, B, C), found once
local RIBBONS = {}
for _, name in Clips.Joints do
    if string.find(name, "Tail%d[ABC]$") then
        table.insert(RIBBONS, { Name = name, Seed = string.byte(name, #name - 1), Lag = if string.find(name, "B$") then 0.7 else 0 })
    end
end

function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 1.6 elseif asleep then 0.18 else 0.3
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Chest", 1.5 * breath)
    add(pose, "Hips", 0, 0, 0, 0.1 * breath)
    add(pose, "Neck2", 0.8 * breath)
    for tag, seed in { Left = 0, Right = 1.7 } do
        add(pose, tag .. "Clavicle", 0, 0, (if tag == "Left" then -1 else 1) * 1.2 * breath)
        add(pose, tag .. "Prim1A", 0, 0, 0.8 * math.sin(now * 0.9 + seed))
        add(pose, tag .. "Prim3A", 0, 0, 0.8 * math.sin(now * 0.8 + seed + 1))
    end
    -- the ribbons and the crest sway out of step with each other
    add(pose, "TailBase", 1.2 * math.sin(now * 0.7), 3 * math.sin(now * 0.5))
    for _, ribbon in RIBBONS do
        add(pose, ribbon.Name, 0.8 * math.sin(now * 1.1 + ribbon.Seed), 2.2 * math.sin(now * 0.9 + ribbon.Seed * 0.7 + ribbon.Lag))
    end
    add(pose, "CrestA", 1.4 * math.sin(now * 1.3), 1.6 * math.sin(now * 0.8))
    add(pose, "CrestB", 2.2 * math.sin(now * 1.3 - 0.8), 2 * math.sin(now * 0.8 - 0.6))
    if asleep then
        return
    end
    local idle = 1 - anim.moving
    -- the weight shifts from one leg to the other, slowly and never quite regularly
    local shift = (math.sin(now * 0.23) + 0.5 * math.sin(now * 0.41 + 1.3)) * idle
    add(pose, "Hips", 0, 0.8 * shift, 1.6 * shift)
    add(pose, "Spine", 0, -0.5 * shift, -0.8 * shift)
    add(pose, "Chest", 0, -0.5 * shift, -0.6 * shift)
    -- the studying look: the head snaps and holds, tilted; the body stays still
    local gaze = gazeOf(anim, now, state == "Weakened" or state == "Enraged")
    local share = (if state == "Enraged" then 0.4 else 1) * idle
    for _, pair in GAZE_JOINTS do
        add(pose, pair[1], gaze[1] * pair[2] * share, gaze[2] * pair[2] * share, gaze[3] * pair[2] * share)
    end
    local name, weight, t = flourish(anim, now, state)
    if name then
        lay(pose, Clips.Poses[name], weight * (if name == "Display" then 0.9 else 1))
        if name == "Preen" and t then
            -- nibbling at the feathers of the raised wing
            local nibble = envelope(t - 1.0, 0.2, 1.6, 0.3)
            add(pose, "Head", 7 * nibble * math.abs(math.sin(t * 8)), 5 * nibble * math.sin(t * 5.3))
            add(pose, "Jaw", -8 * nibble * math.abs(math.sin(t * 8)))
        end
    end
    if state == "Weakened" then
        anim:tremor("Chest", 0.5 * math.sin(now * 29), 0, 0.4 * math.sin(now * 23))
        add(pose, "Head", 1.5 * math.sin(now * 1.8))
    elseif state == "Enraged" then
        -- restless: the primaries rattle, the crest quivers, the head sways from side to side
        local rattle = 0.5 + 0.5 * math.sin(now * 1.7)
        for _, tag in { "Left", "Right" } do
            for g = 1, 5 do
                anim:tremor(tag .. "Prim" .. g .. "A", 0.8 * rattle * math.sin(now * (41 + 3 * g)), 1.2 * rattle * math.sin(now * (37 + 2 * g)))
            end
        end
        anim:tremor("CrestA", 1.6 * math.sin(now * 33))
        add(pose, "Neck3", 0, 4 * math.sin(now * 0.9))
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
    for _, tag in { "Left", "Right" } do
        for _, span in move.Plants[tag] do
            if frame >= span[1] and frame <= span[2] then
                anim:lift(tag, weight)
            end
        end
    end
end

local function blend(t, total)
    return math.min(smooth(t / 0.1), smooth((total - t) / 0.25))
end

local WINGS = { "Left", "Right" }
-- every feather of a wing, for what rattles and what trails
local function primaries(tag)
    return { tag .. "Prim1A", tag .. "Prim2A", tag .. "Prim3A", tag .. "Prim4A", tag .. "Prim5A" }
end

-- what a blow leaves swinging: the primaries and secondaries ripple shut, the ribbons of the tail and the plumes of the crest whip on past the stop
local function followThrough(anim, pose, after, strength, tags)
    local k = GuardianAnim.damped(after, 3.2, 2.6) * strength
    for _, tag in tags or WINGS do
        for g = 1, 5 do
            add(pose, tag .. "Prim" .. g .. "A", 0, 6 * k * (1 + 0.2 * g), 5 * k)
            add(pose, tag .. "Prim" .. g .. "B", 0, 8 * k * (1 + 0.2 * g), 9 * k)
        end
        for g = 1, 2 do
            add(pose, tag .. "Sec" .. g .. "A", 0, 5 * k, 4 * k)
            add(pose, tag .. "Sec" .. g .. "B", 0, 7 * k, 7 * k)
        end
    end
    add(pose, "TailBase", -10 * k, 6 * k)
    add(pose, "Tail0A", -8 * k)
    add(pose, "Tail0B", -10 * k)
    add(pose, "Tail0C", -12 * k)
    add(pose, "CrestA", -14 * k)
    add(pose, "CrestB", -18 * k)
end

local function quiver(anim, tags, amount, t)
    for _, tag in tags do
        for g, joint in primaries(tag) do
            anim:tremor(joint, 2.2 * amount * math.sin(t * (57 + 4 * g)), 2.8 * amount * math.sin(t * (49 + 3 * g)), 1.6 * amount * math.sin(t * 61))
        end
    end
end

-- each strike's wind-up comes from the server; its clip was made for this long, and scaled to fit
local STRIKES = { WingScythe = { 0.8, 1.9 }, CinderGale = { 1.3, 2.5 } }
local BLOW_LEAD = 0.03 -- the springs carry a blow in this late: the clip runs this far ahead, so it lands with its effect

function Rig.actions(anim, pose, now)
    -- waking: the head lifts from under the wing and shakes, the wings unfold to their span, a shiver runs through every feather, it stands tall
    local t = anim:action("Awaken", 2.8)
    if t then
        playMove(anim, pose, "Awaken", t, smooth((2.8 - t) / 0.3))
        local shiver = envelope(t - 2.05, 0.1, 0.5, 0.2)
        for _, tag in WINGS do
            for g, joint in primaries(tag) do
                anim:tremor(joint, 3 * shiver * math.sin(t * (47 + 3 * g)), 4 * shiver * math.sin(t * (43 + 2 * g)))
            end
        end
        anim:tremor("Chest", 1.2 * shiver * math.sin(t * 41), 0, 1.0 * shiver * math.sin(t * 37))
        anim:tremor("CrestA", 4 * shiver * math.sin(t * 39))
        anim:tremor("Head", 0, 1.4 * envelope(t - 1.1, 0.05, 0.5, 0.1) * math.sin(t * 25))
    end

    -- faltering: the blow it cannot take: the head snaps back, the weight lurches, the legs buckle, a wing falls and drags, it sinks onto its breast
    t = anim:action("Weaken", 1.9)
    if t then
        playMove(anim, pose, "Weaken", t, math.min(smooth(t / 0.08), smooth((1.9 - t) / 0.2)))
        anim:contact("Weaken", 0.95, 0.09)
        followThrough(anim, pose, t - 0.95, 0.8)
        local reel = envelope(t, 0.15, 0.9, 0.4)
        anim:tremor("Chest", 0, 0, 3 * reel * math.sin(t * 9))
    end

    -- it has seen the egg taken: it rears up on its toes, the wings flung wide, the head thrown back screeching, every primary rattling; then
    -- it slams down into the half-spread threat
    t = anim:action("Enrage", 1.4)
    if t then
        playMove(anim, pose, "Enrage", t, math.min(smooth(t / 0.06), smooth((1.4 - t) / 0.25)))
        local rattle = envelope(t - 0.2, 0.05, 0.75, 0.2)
        quiver(anim, WINGS, 1.6 * rattle, t)
        anim:tremor("CrestA", 5 * rattle * math.sin(t * 45))
        anim:tremor("Head", 2.4 * rattle * math.sin(t * 40), 1.6 * rattle * math.sin(t * 31))
        anim:tremor("Jaw", -6 * rattle * math.abs(math.sin(t * 22)))
        anim:contact("Enrage", 0.98, 0.08)
        followThrough(anim, pose, t - 0.98, 0.7)
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
                if name == "WingScythe" then
                    -- the cocked wing trembles before the cut: its primaries fanned open and shaking
                    quiver(anim, { "Right" }, envelope(t - 0.3 * w, 0.1, 0.34 * w, 0.08), t)
                    anim:tremor("Chest", 0.4 * envelope(t - 0.3 * w, 0.1, 0.3 * w, 0.05) * math.sin(t * 43))
                else
                    -- the wings held overhead shake with the breath that swells the chest
                    quiver(anim, WINGS, 1.2 * envelope(t - 0.6 * w, 0.2, 0.4 * w, 0.1), t)
                    anim:tremor("Chest", 0.8 * envelope(t - 0.6 * w, 0.2, 0.4 * w, 0.1) * math.sin(t * 37), 0, 0.5 * math.sin(t * 29) * envelope(t - 0.6 * w, 0.2, 0.4 * w, 0.1))
                    anim:tremor("Jaw", -4 * envelope(t - 0.6 * w, 0.2, 0.4 * w, 0.1) * math.abs(math.sin(t * 21)))
                end
                -- the blow lands: the whole bird stops for an instant on it (the heavier, the longer), then what hangs off it whips on past the stop
                anim:contact(name, w, if name == "CinderGale" then 0.12 else 0.1)
                local after = t - w
                if after > 0 then
                    local shake = envelope(after, 0.02, 0.4, 0.25)
                    anim:tremor("Chest", 1.6 * shake * math.sin(t * 48), 0, 0.8 * shake * math.sin(t * 37))
                    followThrough(anim, pose, after, if name == "CinderGale" then 1.1 else 1.0, if name == "WingScythe" then { "Right", "Left" } else nil)
                    add(pose, "Hips", 0, 0, 0, -0.4 * envelope(after, 0.03, 0.4, 0.3))
                end
            end
        end
    end

    -- the dive: its crouch and spring are the wind-up, the rest the time in the air
    local leap = anim.actions.TalonDive
    if leap then
        local windUp, air = leap.args[1] or 0.9, leap.args[2] or 1.0
        t = anim:action("TalonDive", windUp + air + 0.1)
        if t then
            local clock = if t < windUp then t * (0.9 / windUp) else 0.9 + (t - windUp) * (1.0 / air)
            playMove(anim, pose, "TalonDive", clock, math.min(smooth(t / 0.1), 1))
            -- coiled in the crouch, the wings cocked and trembling
            quiver(anim, WINGS, 1.3 * envelope(t - 0.35 * windUp, 0.1, 0.45 * windUp, 0.1), t)
            if t > windUp then
                -- in the glide the feathers stream
                local fly = envelope(t - windUp, 0.1, air, 0.25)
                for _, tag in WINGS do
                    for g, joint in primaries(tag) do
                        anim:tremor(joint, 1.2 * fly * math.sin(t * (31 + 2 * g)), 1.6 * fly * math.sin(t * (27 + g)))
                    end
                end
                anim:tremor("CrestA", 4 * fly * math.sin(t * 23))
            end
        end
    end

    -- landing: the talons take the ground ahead, the legs crush under it, a stop on it, the wings flaring for balance, the feathers whipping on
    t = anim:action("Land", 0.9)
    if t then
        playMove(anim, pose, "Land", t, smooth((0.9 - t) / 0.25))
        anim:contact("Land", 0.06, 0.1)
        followThrough(anim, pose, t - 0.06, 1.1)
    end
end

-- ---------- the eyes and the magma ----------
-- The eyes are fire: lit awake, dark asleep; they slide back into their sockets to blink. The magma along its feathers and in the cracks of its
-- armour burns low asleep, breathes with it awake, gutters weakened, runs white-hot enraged and flares as it strikes.
local EYE = Color3.fromRGB(255, 170, 40)
local EYE_HOT = Color3.fromRGB(255, 236, 170)
local MAGMA = Color3.fromRGB(255, 122, 20)
local MAGMA_HOT = Color3.fromRGB(255, 205, 80)
local OPEN = { Guardian = 1, Weakened = 1, Enraged = 0.7, Returning = 0.9 }
local SOCKET_DEPTH = 0.22

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.pupils = model:FindFirstChild("Pupils")
    anim.magma = {}
    for _, part in model:GetChildren() do
        if part:IsA("BasePart") and part.Name == "Magma" then
            table.insert(anim.magma, part)
        end
    end
end

function Rig.glow(anim, state, now)
    local waking = anim:action("Awaken", 2.8)
    local asleep = (state == "Dormant" or state == "Resting") and not waking
    local amount = (OPEN[state] or 1) * anim:blink(now, asleep, 4.5, 0.32)
    if waking then
        amount *= smooth((waking - 0.7) / 0.5)
    end
    anim:poseBone("Eyes", CFrame.new(0, 0, SOCKET_DEPTH * (1 - math.clamp(amount, 0, 1))))
    local color = if state == "Enraged" then EYE_HOT else EYE
    if state == "Weakened" then
        color = Color3.fromRGB(110, 60, 20):Lerp(EYE, 0.5 + 0.5 * math.sin(now * 10) * math.sin(now * 3.9))
    end
    for _, part in { anim.iris, anim.pupils } do
        if part then
            part.Transparency = if asleep then 1 else 0
        end
    end
    if anim.iris then
        anim.iris.Color = anim.iris.Color:Lerp(color, 0.25)
    end
    local breath = 0.5 + 0.5 * math.sin(now * 0.3 * 2 * math.pi)
    local fade = if asleep then 0.55 elseif state == "Weakened" then 0.3 + 0.4 * math.abs(math.sin(now * 5) * math.sin(now * 1.9))
        elseif state == "Enraged" then 0.02 else 0.1 + 0.12 * (1 - breath)
    local hot = if state == "Enraged" then 0.7 + 0.3 * breath else 0.15 * breath
    if waking then
        local lit = smooth((waking - 0.2) / 1.6)
        fade = fade + (0.1 - fade) * lit
        hot = math.max(hot, envelope(waking - 2.05, 0.1, 0.6, 0.4))
    end
    for name, wind in { WingScythe = 0.8, CinderGale = 1.3 } do
        local action = anim.actions[name]
        if action then
            local flare = envelope(now - action.start - (action.args[1] or wind), 0.05, 0.9, 0.6)
            hot = math.max(hot, flare)
            fade *= 1 - flare
        end
    end
    local tint = MAGMA:Lerp(MAGMA_HOT, hot)
    for _, part in anim.magma do
        part.Transparency += (fade - part.Transparency) * 0.3
        part.Color = part.Color:Lerp(tint, 0.3)
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local function anchor(name)
    local a = Clips.Anchors[name]
    return CFrame.new(a[1], a[2], a[3])
end
local SCYTHE_TIP, SCYTHE_MID = anchor("ScytheTip"), anchor("ScytheMid")
local GALE_LEFT, GALE_RIGHT, GALE_GROUND = anchor("GaleLeft"), anchor("GaleRight"), anchor("GaleGround")
local MOUTH, CROWN, KEEL = anchor("Mouth"), anchor("Crown"), anchor("Keel")

Rig.Fx = {
    Awaken = function(model)
        local pivot = model:GetPivot()
        GuardianFx.embers(pivot * CROWN, 14, 16, 70, 1.8)
        task.delay(2.05, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.embers(p * CFrame.new(0, 12, 0), 26, 20, 180, 2.2)
                GuardianFx.puff(p * CFrame.new(0, 0.6, -2), style, 16, 16, Vector2.new(180, 8), 4, 1.3)
                GuardianFx.flash(p * CFrame.new(0, 14, -3), style, 22)
                GuardianFx.shake(p.Position, 1.4, 0.8)
            end
        end)
    end,
    WingScythe = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * SCYTHE_MID, style, 30)
            GuardianFx.crescent(pivot * SCYTHE_TIP, style, 20)
            GuardianFx.streaks(pivot * SCYTHE_TIP, style, 14, 60, 50)
            GuardianFx.embers(pivot * SCYTHE_TIP, 18, 22, 80, 1.4)
            GuardianFx.puff(pivot * CFrame.new(SCYTHE_TIP.X * 0.7, 0.8, SCYTHE_TIP.Z * 0.7), style, 14, 14, 80, 3, 1.1)
            GuardianFx.shake(pivot.Position, 1.8, 0.45)
            GuardianFx.kick(pivot.Position, 0.8, 0, 0.3)
        end)
    end,
    CinderGale = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            for _, tip in { GALE_LEFT, GALE_RIGHT } do -- (the rings lie on the ground under each wingtip: the tips themselves are 4.5 studs up)
                local at = (pivot * tip).Position
                GuardianFx.shockRing(Vector3.new(at.X, pivot.Y, at.Z), style, 12, 0.5)
            end
            GuardianFx.embers(pivot * GALE_LEFT, 22, 26, 90, 1.6)
            GuardianFx.embers(pivot * GALE_RIGHT, 22, 26, 90, 1.6)
            GuardianFx.flash(pivot * GALE_GROUND * CFrame.new(0, 2, 0), style, 26)
            GuardianFx.puff(pivot * GALE_GROUND, style, 30, 26, Vector2.new(180, 10), 5, 1.4)
            GuardianFx.shake(pivot.Position, 2.8, 0.9)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 360, style)
        end)
    end,
    TalonDive = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 26, 22, Vector2.new(180, 10), 4, 1.3)
            GuardianFx.embers(CFrame.new(from + Vector3.new(0, 0.5, 0)), 16, 18, 120, 1.4)
            GuardianFx.shake(from, 1.6, 0.5)
        end)
    end,
    Land = function(model, position)
        GuardianFx.shockRing(position, style, 20, 0.55)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 40, 34, Vector2.new(180, 6), 5, 1.5)
        GuardianFx.embers(CFrame.new(position + Vector3.new(0, 0.5, 0)), 24, 24, 110, 1.6)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 18)
        GuardianFx.shake(position, 3.2, 0.9)
    end,
    Weaken = function(model)
        task.delay(0.95, function()
            if model.Parent then
                local pivot = model:GetPivot()
                GuardianFx.shockRing(pivot.Position, style, 14, 0.5)
                GuardianFx.puff(pivot * KEEL, style, 18, 18, Vector2.new(180, 6), 4, 1.2)
                GuardianFx.embers(pivot * KEEL, 14, 14, 140, 1.4)
                GuardianFx.shake(pivot.Position, 1.8, 0.6)
            end
        end)
    end,
    Enrage = function(model)
        local pivot = model:GetPivot()
        GuardianFx.flash(pivot * MOUTH, style, 28)
        GuardianFx.embers(pivot * MOUTH, 22, 20, 100, 1.6)
        task.delay(0.98, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.shockRing(p.Position, style, 18, 0.55)
                GuardianFx.puff(p * CFrame.new(0, 0.5, -5), style, 22, 20, Vector2.new(180, 6), 4, 1.3)
                GuardianFx.shake(p.Position, 2.2, 0.7)
            end
        end)
    end,
}

return Rig

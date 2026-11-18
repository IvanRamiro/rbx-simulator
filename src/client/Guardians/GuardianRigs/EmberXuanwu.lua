-- The Ember Xuanwu's rig (GuardianAnim) and effects (GuardianFx).
--
-- Joints: Body (from the root: the shell, its volcano and the serpent's coil), Neck, Head and Jaw (the
-- tortoise's), SerpentNeck and SerpentHead, Tail, and an upper and lower piece per leg. A negative X
-- turn on the Jaw opens the beak.
--   Dormant   a sleeping volcano: sunk on its plastron, head drawn in, eyes shut, the serpent's head
--             drowsing low over the shell, its eyes dulled, the magma dim;
--   Guardian  awake, the serpent swaying over the volcano, both heads watching the nearest player;
--   Weakened  sunk low, head down, the serpent's head hung to the ground before them;
--   Enraged   front reared, beak open, the serpent rearing high, eyes narrowed to a glare, magma hot.
-- It walks slowly, diagonal legs together, the shell rolling with each step. Its debris is volcanic
-- ash and embers, its Qi magma.
--
-- The eyes are the face (an almond iris, a dark Neon slit pupil, heavy lids carved in the mesh):
-- the tortoise blinks, slowly, every few seconds and narrows its eyes to a glare when enraged; the
-- serpent never blinks (snakes can't) and its stare narrows to a slit as it strikes.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}

Rig.Joints = {
    "Body", "Neck", "Head", "Jaw", "SerpentNeck", "SerpentHead", "Tail",
    "FrontLeftUpper", "FrontLeftLower", "FrontRightUpper", "FrontRightLower",
    "BackLeftUpper", "BackLeftLower", "BackRightUpper", "BackRightLower",
}
-- the legs: diagonal pairs step together; side +1 right, -1 left (its legs reach out sideways, so a
-- forward swing is a yaw of side * angle and a lift a roll of side * angle, as the mantis's)
local LEGS = {
    { "FrontLeft", -1, 0 }, { "BackRight", 1, 0 }, { "FrontRight", 1, 0.5 }, { "BackLeft", -1, 0.5 },
}

Rig.Poses = {
    Dormant = {
        Body = { 0, 0, 0, -0.9 }, Neck = { -10, 0, 0, 0, 2.2 }, Head = { -6 },
        SerpentNeck = { -16 }, SerpentHead = { -22 }, Tail = { -8 },
    },
    Guardian = { Body = { 0, 0, 0, -0.3 }, Head = { 0 } },
    Weakened = {
        Body = { -2, 0, 0, -1.4 }, Neck = { -16 }, Head = { -10 }, Jaw = { -5 },
        SerpentNeck = { -30, 6 }, SerpentHead = { -8 }, Tail = { -10 },   -- its head hung low to the ground (-38 buried it)
    },
    Enraged = {
        Body = { 4, 0, 0, -0.1 }, Neck = { 10 }, Head = { 6 }, Jaw = { -14 },
        SerpentNeck = { 10 }, SerpentHead = { 12 }, Tail = { 14 },
    },
    Returning = { Body = { 0, 0, 0, -0.3 }, Head = { -4 } },
    Resting = {
        Body = { 0, 0, 0, -0.9 }, Neck = { -10, 0, 0, 0, 2.2 }, Head = { -6 },
        SerpentNeck = { -16 }, SerpentHead = { -22 }, Tail = { -8 },
    },
}
Rig.LeapAction = "Charge"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Neck", BodyShare = 0.3, Limit = 35 }
-- a blow taken (GuardianReact): the shell barely moves, the neck and the serpent's head show it. The heaviest of the beasts but one
Rig.Hit = { Body = "Body", Joints = { Body = { 0.5, 0 }, Neck = { 0.8, 0.02 }, Head = { 1, 0.04 }, SerpentNeck = { 1, 0.03 }, SerpentHead = { 1, 0.06 } }, Scale = 0.9 }
-- springs (GuardianAnim): a slow, massive shell that rocks a long time after it stops, the
-- tortoise's head lagging it, and the serpent a heavy loose coil that sways behind every turn
Rig.Springs = {
    Body = { Freq = 2.8, Damping = 0.55, Drag = 0 },
    Neck = { Freq = 3.6, Damping = 0.5, Drag = 0.3 },
    Head = { Freq = 4.5, Damping = 0.5, Drag = 0.3 },
    Jaw = { Freq = 7, Damping = 0.45, Drag = 0 },
    SerpentNeck = { Freq = 3.4, Damping = 0.42, Drag = 0.9 },
    SerpentHead = { Freq = 4.0, Damping = 0.42, Drag = 0.7 },
    Tail = { Freq = 3, Damping = 0.35, Drag = 0.8 },
}
Rig.Lean = { Joint = "Body", Accel = 0.08, Bank = 0.04, Max = 5 }
-- planted feet (GuardianAnim): the sprawling legs bend on roll, the left ones folding on a positive
-- Lower turn and the right on a negative one (measured in Play)
Rig.Legs = {
    { Name = "FrontLeft", Upper = "FrontLeftUpper", Lower = "FrontLeftLower", Axis = 3, Bend = 1 },
    { Name = "FrontRight", Upper = "FrontRightUpper", Lower = "FrontRightLower", Axis = 3, Bend = -1 },
    { Name = "BackLeft", Upper = "BackLeftUpper", Lower = "BackLeftLower", Axis = 3, Bend = 1 },
    { Name = "BackRight", Upper = "BackRightUpper", Lower = "BackRightLower", Axis = 3, Bend = -1 },
}
Rig.Style = { Debris = "Cinders", Qi = Color3.fromRGB(255, 70, 0), QiCore = Color3.fromRGB(255, 190, 90) }

local STRIDE = 11

function Rig.gait(anim, pose, dt)
    anim.phase = (anim.phase + dt * anim.stepSpeed / STRIDE) % 1
    -- measured in Play: lifting each foot 26/18 degrees with the shell about 0.6 studs low (with the
    -- awake poses') plants the stance feet and gives a heavy, clear step
    local amplitude = 14 * anim.moving
    for _, leg in LEGS do
        local name, side, offset = leg[1], leg[2], leg[3]
        local a = 2 * math.pi * (anim.phase + offset)
        local lift = math.max(0, math.cos(a)) * anim.moving
        add(pose, name .. "Upper", 0, side * amplitude * math.sin(a), side * 26 * lift)
        add(pose, name .. "Lower", 0, 0, -side * 18 * lift)
        anim:lift(name, math.min(1, lift * 2))
    end
    -- the shell rolls from side to side over the stepping pairs, and bobs as each lands
    local step = 2 * math.pi * anim.phase
    add(pose, "Body", 0, 0, 1.6 * math.sin(step) * anim.moving, (0.35 * math.abs(math.sin(step)) - 0.3) * anim.moving)
    add(pose, "Head", -2 * math.sin(step * 2) * anim.moving, 0, -1.2 * math.sin(step) * anim.moving)
    add(pose, "SerpentNeck", 0, 3 * math.sin(step) * anim.moving)
    add(pose, "Tail", 0, 6 * math.sin(step) * anim.moving)
end

-- slow breaths through the shell, the serpent swaying over the volcano and watching too
function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 0.9 elseif asleep then 0.18 else 0.3
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Body", 0.4 * breath, 0, 0, 0.12 * breath)
    add(pose, "Neck", -0.8 * breath)
    if asleep then
        add(pose, "SerpentNeck", 1.2 * math.sin(now * 0.4))
        return
    end
    local sway = if state == "Enraged" then 1.3 else 0.55
    local amount = if state == "Weakened" then 1.5 else 4
    add(pose, "SerpentNeck", 2 * math.sin(now * sway * 0.7), amount * math.sin(now * sway), 0)
    add(pose, "SerpentHead", -1.5 * math.sin(now * sway * 0.7 + 0.8), anim.look * 0.6 - amount * 0.6 * math.sin(now * sway - 0.5), 0)
    add(pose, "Tail", 0, 4 * math.sin(now * 0.5))
end

local function legs(pose, front, back)
    for _, leg in LEGS do
        local isFront = string.sub(leg[1], 1, 5) == "Front"
        add(pose, leg[1] .. "Upper", 0, 0, leg[2] * (if isFront then front else back))
        add(pose, leg[1] .. "Lower", 0, 0, -leg[2] * (if isFront then front else back) * 0.8)
    end
end

-- the forelegs off the ground by `amount` (0 to 1): up and folded, and let go of the floor
local function raiseForelegs(anim, pose, amount, degrees)
    for _, leg in LEGS do
        if string.sub(leg[1], 1, 5) == "Front" then
            add(pose, leg[1] .. "Upper", 0, 0, leg[2] * (degrees or 30) * amount)
            add(pose, leg[1] .. "Lower", 0, 0, -leg[2] * (degrees or 30) * 0.7 * amount)
            anim:lift(leg[1], amount)
        end
    end
end

-- ---------- its moves ----------
-- Told as key poses (GuardianAnim.keyed). The shell is the mass: it dips and rears over its planted feet (Rig.Legs puts them back on the
-- ground), and the serpent, one rigid arch hinged at the back of the coil, is the whip: it rises to its full height over the volcano and
-- comes down on the ground ahead. Body = { pitch (+ tips the front up), yaw, roll, lift, shift (+ back) }.
function Rig.actions(anim, pose, now)
    -- waking: the volcano rumbles, the shell rises off its plastron shaking, the beak pushes out of the shell with a roar and the serpent
    -- unwinds up over the cone and holds there, hissing; the shell settles back to its feet with a thud
    local t = anim:action("Awaken", 2.2)
    if t then
        local shake = envelope(t, 0.1, 0.8, 0.3)
        anim:tremor("Body", 0, 0.8 * shake * math.sin(t * 60), 0.8 * shake * math.sin(t * 47))
        keyed(pose, t, {
            { 0, {} },
            { 0.7, { Body = { 5, 0, 0, 0.9, 0.6 }, Neck = { 12, 0, 0, 0, -1 }, Head = { 6 }, SerpentNeck = { 12 }, SerpentHead = { 6 } }, "out" },
            { 1.15, { Body = { 11, 0, 0, 1.4, 1.2 }, Neck = { 20, 0, 0, 0, -1.4 }, Head = { 12 }, Jaw = { -34 }, SerpentNeck = { 34 }, SerpentHead = { 20 }, Tail = { 14 } }, "back" },
            { 1.65, { Body = { 9, 0, 0, 1.0, 1.0 }, Neck = { 18 }, Head = { 10 }, Jaw = { -30 }, SerpentNeck = { 30 }, SerpentHead = { 16 }, Tail = { 10 } }, "linear" },
            { 1.95, { Body = { -3, 0, 0, -0.7 }, Neck = { -4 }, SerpentNeck = { 8 } }, "in" },
            { 2.2, {}, "back" },
        })
        raiseForelegs(anim, pose, envelope(t - 0.5, 0.4, 1.3, 0.25), 18)
        local roar = envelope(t - 1.0, 0.1, 0.8, 0.3)
        anim:tremor("Head", 1.8 * roar * math.sin(t * 41), 1.2 * roar * math.sin(t * 33))
        anim:tremor("SerpentHead", 2 * roar * math.sin(t * 29), 3 * roar * math.sin(t * 23))
        anim:contact("Awaken", 1.93, 0.07)
    end

    -- faltering: the blow it cannot take: the serpent whips up and screams, the shell lurches; then the legs give one after the other and the
    -- shell sinks onto its plastron, the serpent's head falling to the ground; a thud, a stop on it
    t = anim:action("Weaken", 1.9)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.18, { Body = { 5, 0, 5, 0.3 }, Neck = { 14 }, Head = { 6 }, Jaw = { -24 }, SerpentNeck = { 30 }, SerpentHead = { 14 }, Tail = { 12 } }, "snap" },
            { 0.7, { Body = { -2, 0, -4, -0.8 }, Neck = { -8 }, SerpentNeck = { 6 }, SerpentHead = { -6 } }, "inout" },
            { 1.15, { Body = { -4, 0, 3, -1.9 }, Neck = { -14 }, Head = { -8 }, Jaw = { -8 }, SerpentNeck = { -34 }, SerpentHead = { -12 }, Tail = { -10 } }, "in" },
            { 1.9, {}, "back" },
        })
        local w = envelope(t, 0.2, 1.9, 0.6)
        add(pose, "Body", 0, 0, 3 * math.sin(t * 7) * w)
        legs(pose, -9 * smooth((t - 0.5) / 0.6) * w, -7 * smooth((t - 0.8) / 0.5) * w)
        anim:contact("Weaken", 1.12, 0.09)
    end

    -- it has seen the egg taken: it rears onto its hind legs and bellows, the serpent flung up flaring over the volcano, the shell hot;
    -- then it comes down hard
    t = anim:action("Enrage", 1.4)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.28, { Body = { -2, 0, 0, -0.9 }, Neck = { -8 }, SerpentNeck = { -6 } }, "out" },
            { 0.6, { Body = { 17, 0, 0, 1.0, 0.8 }, Neck = { 22 }, Head = { 14 }, Jaw = { -34 }, SerpentNeck = { 42 }, SerpentHead = { 24 }, Tail = { 16 } }, "back" },
            { 1.05, { Body = { 15, 0, 0, 0.9, 0.8 }, Neck = { 20 }, Head = { 12 }, Jaw = { -30 }, SerpentNeck = { 38 }, SerpentHead = { 20 }, Tail = { 14 } }, "linear" },
            { 1.22, { Body = { -4, 0, 0, -1.2 }, Neck = { -6 }, SerpentNeck = { -10 } }, "in" },
            { 1.4, {}, "back" },
        })
        raiseForelegs(anim, pose, envelope(t - 0.3, 0.3, 0.9, 0.18), 30)
        local bellow = envelope(t - 0.6, 0.1, 0.5, 0.2)
        anim:tremor("Head", 2 * bellow * math.sin(t * 44), 1.4 * bellow * math.sin(t * 35))
        anim:tremor("Body", 0.7 * bellow * math.sin(t * 38), 0, 0.6 * bellow * math.sin(t * 31))
        anim:contact("Enrage", 1.2, 0.07)
    end

    -- the serpent's lash: the shell sinks and shifts its weight back; the serpent rises over the volcano to its whole height, coils its head
    -- back and holds, trembling; then it drops like a hammer onto the ground ahead, the shell lunging after it and pitching down; a stop on
    -- contact; it overshoots, the arch whipping, and drags itself back up
    local lash = anim.actions.SerpentLash
    if lash then
        local w = lash.args[1] or 0.8
        t = anim:action("SerpentLash", w + 1.0)
        if t then
            local lead = 0.09 -- the serpent's springs carry it in this late
            keyed(pose, t, {
                { 0, {} },
                { w * 0.3, { Body = { 1, 0, 0, -0.6, 1.2 }, Neck = { -4 }, SerpentNeck = { 12, -3 }, SerpentHead = { 8 } }, "out" },
                { w - 0.2, { Body = { 5, 0, 0, -0.2, 2.2 }, Neck = { 6, 8 }, Head = { 4 }, SerpentNeck = { 44, 6 }, SerpentHead = { 30 }, Tail = { 10 } }, "inout" },
                { w - lead - 0.02, { Body = { 6, 0, 0, -0.3, 2.6 }, Neck = { 6, 10 }, SerpentNeck = { 48, 7 }, SerpentHead = { 34 }, Tail = { 12 } }, "linear" },
                { w - lead, { Body = { -7, 0, 2, -1.7, -5.5 }, Neck = { -10, -4 }, Head = { -4 }, Jaw = { -12 }, SerpentNeck = { -62, -6, 0, 0, -5 }, SerpentHead = { -36 }, Tail = { -12 } }, "snap" },
                { w - lead + 0.1, { Body = { -8, 0, 2, -1.9, -6.2 }, Neck = { -12, -4 }, SerpentNeck = { -68, -6, 0, 0, -6 }, SerpentHead = { -40 }, Tail = { -14 } }, "out" },
                { w + 0.55, { Body = { -3, 0, 1, -0.9, -2 }, Neck = { -4 }, SerpentNeck = { -30 }, SerpentHead = { -14 } }, "inout" },
                { w + 1.0, {}, "inout" },
            })
            -- the wind-up shudders at its height
            local quiver = envelope(t - (w - 0.3), 0.08, 0.2, 0.06)
            anim:tremor("SerpentNeck", 1.6 * quiver * math.sin(t * 58), 1.2 * quiver * math.sin(t * 47))
            anim:tremor("SerpentHead", 2.6 * quiver * math.sin(t * 66))
            anim:contact("SerpentLash", w, 0.08)
            local shock = envelope(t - w, 0.02, 0.5, 0.3)
            anim:tremor("Body", 1.2 * shock * math.sin(t * 40), 0, 0.9 * shock * math.sin(t * 33))
            anim:tremor("SerpentHead", 3 * shock * math.sin(t * 36))
        end
    end

    -- the quake: it hunkers; the front rears off the ground, the forelegs high; at the release the whole shell slams down (a stop on it) and
    -- bounces on its legs, the serpent whipping up and over with the shock, the volcano shuddering
    local quake = anim.actions.Quake
    if quake then
        local w = quake.args[1] or 1.3
        t = anim:action("Quake", w + 1.3)
        if t then
            local lead = 0.08
            keyed(pose, t, {
                { 0, {} },
                { w * 0.28, { Body = { -4, 0, 0, -1.0, 0.6 }, Neck = { -12 }, Head = { -6 }, SerpentNeck = { -10 }, Tail = { -6 } }, "out" },
                { w - 0.26, { Body = { 22, 0, 0, 1.2, 2.0 }, Neck = { 18 }, Head = { 10 }, Jaw = { -30 }, SerpentNeck = { 36 }, SerpentHead = { 20 }, Tail = { 16 } }, "inout" },
                { w - lead - 0.02, { Body = { 23, 0, 0, 1.3, 2.1 }, Neck = { 20 }, Head = { 10 }, Jaw = { -32 }, SerpentNeck = { 38 }, SerpentHead = { 22 }, Tail = { 16 } }, "linear" },
                { w - lead, { Body = { -8, 0, 0, -1.8, -1.2 }, Neck = { -16 }, Head = { -10 }, Jaw = { -8 }, SerpentNeck = { -18 }, SerpentHead = { -12 }, Tail = { -14 } }, "snap" },
                { w - lead + 0.16, { Body = { 3, 0, 0, 0.3 }, Neck = { 4 }, SerpentNeck = { 26 }, SerpentHead = { 8 } }, "out" },
                { w + 0.5, { Body = { -2, 0, 0, -0.5 }, Neck = { -3 }, SerpentNeck = { 4 } }, "inout" },
                { w + 1.3, {}, "inout" },
            })
            -- the forelegs lift with the rear and come down with the stamp
            local up = if t < w - lead then smooth((t - w * 0.28) / (w * 0.72 - 0.26)) else 0
            raiseForelegs(anim, pose, up, 34)
            anim:contact("Quake", w, 0.1)
            local shock = envelope(t - w, 0.02, 0.6, 0.35)
            anim:tremor("Body", 1.5 * shock * math.sin(t * 46), 0, 1.0 * shock * math.sin(t * 37), 0.25 * shock * math.sin(t * 30))
            -- the build-up trembles the whole shell
            local build = smooth((t - w * 0.4) / (w * 0.5)) * (if t < w then 1 else 0)
            anim:tremor("Body", 0.5 * build * math.sin(t * 52), 0, 0.5 * build * math.sin(t * 43))
        end
    end

    -- the charge: it hunkers, head drawn in, the legs digging; then the shell drives forward low and heavy, nose down, legs scrambling, the
    -- serpent streaming behind it; it ends braced for the landing
    local charge = anim.actions.Charge
    if charge then
        local windUp, air = charge.args[1] or 0.9, charge.args[2] or 1
        t = anim:action("Charge", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.75, windUp + 0.1, 0.12)
            add(pose, "Body", -3 * crouch, 0, 0, -1.4 * crouch, 1.8 * crouch)
            add(pose, "Neck", -10 * crouch, 0, 0, 0, 2 * crouch)
            add(pose, "SerpentNeck", 16 * crouch)
            add(pose, "SerpentHead", 12 * crouch)
            add(pose, "Tail", 12 * crouch)
            anim:tremor("Body", 0.7 * crouch * math.sin(t * 49), 0, 0.6 * crouch * math.sin(t * 41))
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local stretch = envelope(u, 0.1, 1, 0.25)
                add(pose, "Body", (-9 + 6 * u) * stretch, 0, 0, 0.2 * stretch)
                add(pose, "Neck", 12 * stretch)
                add(pose, "Head", -6 * stretch)
                add(pose, "Jaw", -24 * stretch)
                for _, leg in LEGS do
                    local isFront = string.sub(leg[1], 1, 5) == "Front"
                    add(pose, leg[1] .. "Upper", 0, leg[2] * (if isFront then 24 else -24) * stretch, leg[2] * 10 * stretch)
                end
                add(pose, "SerpentNeck", 22 * stretch)
                add(pose, "SerpentHead", 16 * stretch)
                add(pose, "Tail", 18 * stretch)
            end
        end
    end

    -- landing: the shell slams down onto its legs, a stop on it, and rocks
    t = anim:action("Land", 0.9)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.08, { Body = { -5, 0, 0, -1.9 }, Neck = { -10 }, Head = { -4 }, SerpentNeck = { -18 }, SerpentHead = { -8 }, Tail = { -8 } }, "snap" },
            { 0.38, { Body = { 3, 0, 0, 0.2 }, Neck = { 4 }, SerpentNeck = { 20 } }, "back" },
            { 0.9, {}, "inout" },
        })
        anim:contact("Land", 0.06, 0.09)
    end
end

-- ---------- the eyes and the magma ----------
-- Asleep the tortoise's eyes are shut (iris and pupil hidden: the skull behind them is the closed
-- lid) and the serpent's dulled to unlit amber; the magma burns low. Set locally: the server never
-- changes them.
local MAGMA = Color3.fromRGB(255, 110, 0)         -- measured in Play: 255, 70, 0 reads red under bloom
local MAGMA_LOW = Color3.fromRGB(235, 72, 0)      -- asleep (dimmer Neon turns to a flat dark disc: no lower)
local MAGMA_HOT = Color3.fromRGB(255, 150, 20)
local EYE = Color3.fromRGB(255, 160, 0)
local SERPENT_EYE = Color3.fromRGB(255, 200, 0)
local RAGE = Color3.fromRGB(255, 52, 10)
local DULL = Color3.fromRGB(122, 74, 24)
local OPEN = { Guardian = 1, Weakened = 1.15, Enraged = 0.7, Returning = 0.9 }   -- the iris's height by state

function Rig.setup(anim)
    local model = anim.model
    anim.eyes = {
        tortoise = { iris = model:FindFirstChild("Eyes"), pupil = model:FindFirstChild("Pupils") },
        serpent = { iris = model:FindFirstChild("SerpentEyes"), pupil = model:FindFirstChild("SerpentPupils") },
    }
    for _, eye in anim.eyes do
        eye.irisSize = eye.iris and eye.iris.Size
        eye.pupilSize = eye.pupil and eye.pupil.Size
    end
    anim.magma = {}
    for _, name in { "Magma", "Throat", "SerpentLava", "SerpentMouth" } do
        local part = model:FindFirstChild(name)
        if part then
            table.insert(anim.magma, part)
        end
    end
end

local function shape(eye, open)
    for _, key in { "iris", "pupil" } do
        GuardianAnim.openEye(eye[key], eye[key .. "Size"], open)
    end
end

local function show(eye, visible, material, color)
    for _, key in { "iris", "pupil" } do
        local part = eye[key]
        if part then
            part.Transparency = if visible then 0 else 1
        end
    end
    if eye.iris then
        if eye.iris.Material ~= material then
            eye.iris.Material = material
        end
        eye.iris.Color = eye.iris.Color:Lerp(color, 0.25)
    end
end

function Rig.glow(anim, state, now)
    local awaken = anim:action("Awaken", 2.2)
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local eyes = anim.eyes

    -- the tortoise: a slow blink every few seconds; opening as it wakes
    local open = (OPEN[state] or 1) * anim:blink(now, asleep, 3, 0.32)
    if awaken then
        open *= smooth((awaken - 0.4) / 0.6)
    end
    local color = if state == "Enraged" then RAGE else EYE
    if state == "Weakened" then
        color = Color3.fromRGB(150, 70, 0):Lerp(EYE, 0.5 + 0.5 * math.sin(now * 11) * math.sin(now * 4.1))
    end
    show(eyes.tortoise, not asleep, Enum.Material.Neon, color)
    shape(eyes.tortoise, if asleep then 0.02 else open)

    -- the serpent: never blinks; dulled asleep, narrowed to a slit as it strikes or rages
    local stare = OPEN[state] or 1
    local lash = anim.actions.SerpentLash
    if lash then
        local windUp = lash.args[1] or 0.8
        stare *= 1 - 0.45 * envelope(now - lash.start, windUp * 0.6, windUp + 0.6, 0.3)
    end
    local serpentColor = if state == "Enraged" then RAGE else SERPENT_EYE
    show(eyes.serpent, true, if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon, if asleep then DULL else serpentColor)
    shape(eyes.serpent, if asleep then 0.6 else stare)

    -- the magma: breathing with the shell, low asleep, hot enraged, flaring as the volcano quakes
    local breath = 0.5 + 0.5 * math.sin(now * 0.3 * 2 * math.pi)
    local lava = if asleep then MAGMA_LOW:Lerp(MAGMA, 0.25 * breath)
        elseif state == "Enraged" then MAGMA:Lerp(MAGMA_HOT, 0.5 + 0.5 * breath)
        else MAGMA:Lerp(MAGMA_HOT, 0.3 * breath)
    local quake = anim.actions.Quake
    if quake then
        lava = lava:Lerp(MAGMA_HOT, envelope(now - quake.start - (quake.args[1] or 1.3), 0.05, 1.2, 0.8))
    end
    for _, part in anim.magma do
        part.Color = part.Color:Lerp(lava, 0.2)
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local CRATER = CFrame.new(0, 23.6, 1.5)          -- the volcano's mouth (xuanwu-local)
local STRIKE = CFrame.new(-5, 0.6, -23)          -- where the serpent's head comes down
local MOUTH = CFrame.new(0, 10, -27)             -- the beak

local function erupt(model, count)
    local crater = model:GetPivot() * CRATER
    GuardianFx.embers(crater, count, 34, 22, 1.8)
    GuardianFx.puff(crater, style, math.floor(count / 2), 16, 25, 5, 2.2)
end

Rig.Fx = {
    Awaken = function(model)
        GuardianFx.shed(model:FindFirstChild("Shell"), style, 30)
        GuardianFx.shake(model:GetPivot().Position, 1.4, 1.2)
        task.delay(0.9, function()
            if model.Parent then
                erupt(model, 26)
            end
        end)
    end,
    Weaken = function(model)
        GuardianFx.shed(model:FindFirstChild("Shell"), style, 20)
    end,
    SerpentLash = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local at = model:GetPivot() * STRIKE
            GuardianFx.crescent(at * CFrame.new(0, 4, 0), style, 16)
            GuardianFx.flash(at, style, 12)
            GuardianFx.puff(at, style, 18, 20, Vector2.new(80, 8), 3, 1.1)
            GuardianFx.embers(at, 18, 24, 50, 1.1)
            GuardianFx.shockRing(at.Position, style, 12, 0.45)
            GuardianFx.shake(at.Position, 1.8, 0.5)
            GuardianFx.kick(at.Position, 0.9, 0, 0.3)
        end)
    end,
    Quake = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 180, style)
            GuardianFx.puff(pivot * CFrame.new(0, 0.5, -12), style, 30, 26, Vector2.new(180, 6), 5, 1.4)
            GuardianFx.shockRing(pivot.Position, style, 22, 0.6)
            GuardianFx.shake(pivot.Position, 3, 1.1)
            GuardianFx.kick(pivot.Position, 1.4, 0, 0.4)
            erupt(model, 40)
        end)
    end,
    Charge = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 24, 20, Vector2.new(180, 10), 4, 1.3)
            GuardianFx.flash(model:GetPivot() * MOUTH, style, 10)
        end)
    end,
    Enrage = function(model)
        task.delay(0.6, function()
            if model.Parent then
                erupt(model, 30)
                GuardianFx.shake(model:GetPivot().Position, 1.6, 0.8)
            end
        end)
        task.delay(1.2, function()
            if model.Parent then
                GuardianFx.shockRing(model:GetPivot().Position, style, 16, 0.5)
                GuardianFx.puff(model:GetPivot() * CFrame.new(0, 0.5, -12), style, 20, 20, Vector2.new(180, 6), 4, 1.2)
            end
        end)
    end,
    Land = function(model, position)
        GuardianFx.shockRing(position, style, 20, 0.55)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 40, 34, Vector2.new(180, 6), 5, 1.5)
        GuardianFx.embers(CFrame.new(position + Vector3.new(0, 1, 0)), 24, 26, 70, 1.2)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 18)
        GuardianFx.shake(position, 3.2, 0.8)
        erupt(model, 16)
    end,
}

return Rig

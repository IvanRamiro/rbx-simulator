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

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

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
    Guardian = { Head = { 0 } },
    Weakened = {
        Body = { -2, 0, 0, -1.4 }, Neck = { -16 }, Head = { -10 }, Jaw = { -5 },
        SerpentNeck = { -30, 6 }, SerpentHead = { -8 }, Tail = { -10 },   -- its head hung low to the ground (-38 buried it)
    },
    Enraged = {
        Body = { 4, 0, 0, 0.6 }, Neck = { 10 }, Head = { 6 }, Jaw = { -14 },
        SerpentNeck = { 10 }, SerpentHead = { 12 }, Tail = { 14 },
    },
    Returning = { Head = { -4 } },
    Resting = {
        Body = { 0, 0, 0, -0.9 }, Neck = { -10, 0, 0, 0, 2.2 }, Head = { -6 },
        SerpentNeck = { -16 }, SerpentHead = { -22 }, Tail = { -8 },
    },
}
Rig.LeapAction = "Charge"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Neck", BodyShare = 0.3, Limit = 35 }
Rig.Style = { Debris = "Cinders", Qi = Color3.fromRGB(255, 70, 0), QiCore = Color3.fromRGB(255, 190, 90) }

local STRIDE = 11

function Rig.gait(anim, pose, dt)
    anim.phase = (anim.phase + dt * anim.speed / STRIDE) % 1
    local amplitude = 14 * anim.moving
    for _, leg in LEGS do
        local name, side, offset = leg[1], leg[2], leg[3]
        local a = 2 * math.pi * (anim.phase + offset)
        local lift = math.max(0, math.cos(a)) * anim.moving
        add(pose, name .. "Upper", 0, side * amplitude * math.sin(a), side * 12 * lift)
        add(pose, name .. "Lower", 0, 0, -side * 10 * lift)
    end
    -- the shell rolls from side to side over the stepping pairs, and bobs as each lands
    local step = 2 * math.pi * anim.phase
    add(pose, "Body", 0, 0, 1.6 * math.sin(step) * anim.moving, 0.35 * math.abs(math.sin(step)) * anim.moving)
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

function Rig.actions(anim, pose, now)
    -- waking: the volcano rumbles, the shell rises off its plastron, the head pushes out of the
    -- shell with a roar, the serpent uncoiling up over the cone
    local t = anim:action("Awaken", 2.2)
    if t then
        local shake = envelope(t, 0.1, 0.8, 0.3)
        add(pose, "Body", 0, 0.8 * shake * math.sin(t * 60), 0.8 * shake * math.sin(t * 47))
        local rise = envelope(t - 0.5, 0.6, 1.7, 0.6)
        add(pose, "Body", 3 * rise, 0, 0, 0.5 * rise)
        add(pose, "Neck", 14 * rise)
        add(pose, "Head", 10 * rise)
        add(pose, "Jaw", -26 * envelope(t - 0.9, 0.25, 1.1, 0.4))
        add(pose, "SerpentNeck", 14 * rise)
        add(pose, "SerpentHead", 16 * envelope(t - 0.8, 0.3, 1.2, 0.5))
    end

    -- faltering: the shell lurches and drops, the legs buckling
    t = anim:action("Weaken", 1.9)
    if t then
        local w = envelope(t, 0.2, 1.9, 0.6)
        add(pose, "Body", 0, 0, 4 * math.sin(t * 7) * w, -0.6 * w)
        legs(pose, -8 * w, -6 * w)
        add(pose, "Neck", -8 * w)
    end

    -- the serpent's lash: it rears back over the volcano, then strikes down at the ground before them
    local lash = anim.actions.SerpentLash
    if lash then
        local windUp = lash.args[1] or 0.8
        t = anim:action("SerpentLash", windUp + 0.8)
        if t then
            local cock = if t < windUp then smooth(t / windUp) elseif t < windUp + 0.1 then 1 - (t - windUp) / 0.1 else 0
            local strike = envelope(t - windUp + 0.1, 0.1, 0.8, 0.5)
            add(pose, "SerpentNeck", 22 * cock - 46 * strike, 0, 0)
            add(pose, "SerpentHead", 18 * cock - 22 * strike)
            add(pose, "Body", -1.5 * strike)
        end
    end

    -- the quake: the front rears, the forelegs lift, then they stamp down
    local quake = anim.actions.Quake
    if quake then
        local windUp = quake.args[1] or 1.3
        t = anim:action("Quake", windUp + 0.9)
        if t then
            local rear = if t < windUp then smooth(t / windUp) elseif t < windUp + 0.12 then 1 - (t - windUp) / 0.12 else 0
            local after = envelope(t - windUp, 0.05, 0.9, 0.5)
            add(pose, "Body", 11 * rear - 3 * after, 0, 0, 0.8 * rear - 0.5 * after)
            legs(pose, 26 * rear, -4 * rear)
            add(pose, "Neck", 8 * rear - 10 * after)
            add(pose, "Jaw", -24 * rear)
            add(pose, "SerpentNeck", 10 * rear)
        end
    end

    -- the charge: it hunkers down, head drawn in, then lunges, legs flung out
    local charge = anim.actions.Charge
    if charge then
        local windUp, air = charge.args[1] or 0.9, charge.args[2] or 1
        t = anim:action("Charge", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", -2 * crouch, 0, 0, -0.8 * crouch)
            add(pose, "Neck", -8 * crouch, 0, 0, 0, 1.4 * crouch)
            add(pose, "SerpentNeck", -10 * crouch)
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local stretch = envelope(u, 0.12, 1, 0.25)
                add(pose, "Body", (4 - 9 * u) * stretch)
                add(pose, "Neck", 10 * stretch)
                add(pose, "Jaw", -22 * stretch)
                for _, leg in LEGS do
                    local isFront = string.sub(leg[1], 1, 5) == "Front"
                    add(pose, leg[1] .. "Upper", 0, leg[2] * (if isFront then 22 else -22) * stretch, leg[2] * 8 * stretch)
                end
                add(pose, "SerpentNeck", 12 * stretch)
            end
        end
    end

    -- landing: the shell slams down onto its legs
    t = anim:action("Land", 0.7)
    if t then
        local give = envelope(t, 0.05, 0.7, 0.5)
        add(pose, "Body", -3 * give, 0, 0, -1.1 * give)
        legs(pose, -10 * give, -10 * give)
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
    anim.nextBlink = os.clock() + 2
end

local function shape(eye, open)
    for _, key in { "iris", "pupil" } do
        local part, base = eye[key], eye[key .. "Size"]
        if part then
            local size = Vector3.new(base.X, math.max(base.Y * open, 0.02), base.Z)
            if (part.Size - size).Magnitude > 0.005 then
                part.Size = part.Size:Lerp(size, 0.6)   -- quick enough for a full blink
            end
        end
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
    local open = OPEN[state] or 1
    if not asleep and now >= anim.nextBlink then
        anim.blinkAt = now
        anim.nextBlink = now + 3 + 3 * math.random()
    end
    if anim.blinkAt then
        local b = (now - anim.blinkAt) / 0.32
        if b >= 1 then
            anim.blinkAt = nil
        else
            open *= 1 - math.min(1, math.sin(math.pi * b) * 1.6) * 0.95   -- shut for a moment at its middle
        end
    end
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
local STRIKE = CFrame.new(-5, 0.6, -27)          -- where the serpent's head comes down
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
            GuardianFx.shake(at.Position, 1.6, 0.45)
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
            GuardianFx.shake(pivot.Position, 3, 1.1)
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
    Land = function(model, position)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 40, 34, Vector2.new(180, 6), 5, 1.5)
        GuardianFx.embers(CFrame.new(position + Vector3.new(0, 1, 0)), 24, 26, 70, 1.2)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 18)
        GuardianFx.shake(position, 3.2, 0.8)
        erupt(model, 16)
    end,
}

return Rig

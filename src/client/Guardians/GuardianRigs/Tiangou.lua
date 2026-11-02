-- Tiangou the Moon-Eater's rig (GuardianAnim) and effects (GuardianFx).
--
-- Joints: Body (from the root, with the eclipse over its shoulders), Neck (with the ruff), Head,
-- Jaw, Tail and TailTip, and an upper and lower piece per leg. A negative X turn on the Jaw opens
-- the mouth.
--   Dormant   asleep on its feet: head low, eyes shut, tail down, the corona burning low;
--   Guardian  alert, ears and eyes on whoever comes, the tail waving;
--   Weakened  crouched low, head down, panting, the corona guttering;
--   Enraged   the hunting crouch: head level, lips drawn back, tail up, eyes narrowed and red.
-- It trots, diagonal legs together, and gallops as it speeds up. Its leaps are long and high: in
-- the air it stretches out flat, tail streaming. Its debris is frost mist, its Qi moonlight.
--
-- The eyes are gold almonds with round black pupils under carved lids (guardian_kit.eye): it
-- blinks every few seconds, glares (narrowed, red) enraged, and widens and flickers weakened.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}

Rig.Joints = {
    "Body", "Neck", "Head", "Jaw", "Tail", "TailTip",
    "FrontLeftUpper", "FrontLeftLower", "FrontRightUpper", "FrontRightLower",
    "BackLeftUpper", "BackLeftLower", "BackRightUpper", "BackRightLower",
}
local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }

Rig.Poses = {
    Dormant = { Neck = { -24 }, Head = { -12 }, Tail = { -25 }, TailTip = { -15 } },
    Guardian = { Neck = { 4 }, Tail = { 8 } },
    Weakened = {
        Body = { -4, 0, 0, -1.5 }, Neck = { -22 }, Head = { -14 }, Jaw = { -8 }, Tail = { -30 }, TailTip = { -20 },
        FrontLeftUpper = { -10 }, FrontRightUpper = { -10 }, FrontLeftLower = { 16 }, FrontRightLower = { 16 },
    },
    Enraged = {
        Body = { -3, 0, 0, -0.6 }, Neck = { -8 }, Head = { 8 }, Jaw = { -22 }, Tail = { 25 }, TailTip = { 15 },
    },
    Returning = { Head = { -4 } },
    Resting = { Neck = { -24 }, Head = { -12 }, Tail = { -25 }, TailTip = { -15 } },
}
Rig.Gallop = { 14, 22 }
Rig.LeapAction = "MoonLeap"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Neck", BodyShare = 0.3, Limit = 50 }
Rig.Style = { Debris = "Frost", Qi = Color3.fromRGB(110, 190, 255), QiCore = Color3.fromRGB(235, 248, 255) }

local TROT_STRIDE, GALLOP_STRIDE = 14, 26

function Rig.gait(anim, pose, dt)
    local stride = TROT_STRIDE + (GALLOP_STRIDE - TROT_STRIDE) * anim.gallop
    anim.phase = (anim.phase + dt * anim.speed / stride) % 1
    local amplitude = (26 + 18 * anim.gallop) * anim.moving
    -- a trot pairs the diagonals; a gallop brings the fronts together and the hinds together
    local offsets = {
        FrontLeft = 0, FrontRight = 0.5 - 0.42 * anim.gallop,
        BackLeft = 0.5 + 0.0 * anim.gallop, BackRight = 0 + 0.58 * anim.gallop,
    }
    for _, leg in LEGS do
        local a = 2 * math.pi * (anim.phase + offsets[leg])
        local lift = math.max(0, math.cos(a))
        local front = string.sub(leg, 1, 5) == "Front"
        add(pose, leg .. "Upper", amplitude * math.sin(a))
        add(pose, leg .. "Lower", (if front then -1 else 1) * (34 + 16 * anim.gallop) * lift * anim.moving)
    end
    local bound = 2 * math.pi * anim.phase
    add(pose, "Body", 5 * anim.gallop * math.sin(bound) * anim.moving, 0, 0,
        (0.3 + 0.8 * anim.gallop) * math.abs(math.sin(bound * 2)) * anim.moving)
    add(pose, "Neck", -4 * anim.gallop * math.sin(bound) * anim.moving)
    add(pose, "Tail", -10 * anim.gallop * anim.moving, 0, 8 * math.sin(bound * 2) * anim.moving)
    add(pose, "TailTip", -12 * anim.gallop * anim.moving, 0, 12 * math.sin(bound * 2 - 0.6) * anim.moving)
end

-- breathing, the tail's wave and the ruff's stir while it is awake
function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 1.8 elseif asleep then 0.25 else 0.5
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Body", 0.5 * breath, 0, 0, 0.12 * breath)
    add(pose, "Neck", -0.8 * breath)
    if state == "Weakened" then
        add(pose, "Jaw", -6 * (0.5 + 0.5 * breath))      -- panting
    end
    if asleep then
        return
    end
    local wag = if state == "Enraged" then 3.2 else 1.1
    add(pose, "Tail", 0, 14 * math.sin(now * wag), 0)
    add(pose, "TailTip", 0, 20 * math.sin(now * wag - 0.7), 0)
end

local function legs(pose, front, back)
    for _, leg in LEGS do
        local isFront = string.sub(leg, 1, 5) == "Front"
        add(pose, leg .. "Upper", if isFront then front else back)
    end
end

function Rig.actions(anim, pose, now)
    -- waking: the head comes up from sleep and it howls once at the sky
    local t = anim:action("Awaken", 2.0)
    if t then
        local rise = envelope(t, 0.5, 2.0, 0.6)
        add(pose, "Neck", 26 * rise)
        add(pose, "Head", 14 * rise)
        local howl = envelope(t - 0.6, 0.3, 1.3, 0.4)
        add(pose, "Neck", 22 * howl)
        add(pose, "Head", 26 * howl)
        add(pose, "Jaw", -30 * howl)
    end

    -- faltering: it staggers, the forelegs buckling
    t = anim:action("Weaken", 1.9)
    if t then
        local w = envelope(t, 0.2, 1.9, 0.6)
        add(pose, "Body", -3 * w, 0, 5 * math.sin(t * 9) * w, -0.6 * w)
        legs(pose, -12 * w, 4 * w)
    end

    -- the bite: it draws back, then lunges and snaps
    local bite = anim.actions.Bite
    if bite then
        local windUp = bite.args[1] or 0.5
        t = anim:action("Bite", windUp + 0.6)
        if t then
            local cock = if t < windUp then smooth(t / windUp) elseif t < windUp + 0.08 then 1 - (t - windUp) / 0.08 else 0
            local snap = envelope(t - windUp + 0.06, 0.06, 0.6, 0.4)
            add(pose, "Body", 2 * cock - 4 * snap, 0, 0, 0, 1.2 * cock - 2.5 * snap)
            add(pose, "Neck", 10 * cock - 22 * snap)
            add(pose, "Head", 8 * cock - 6 * snap)
            add(pose, "Jaw", -34 * cock + 30 * snap)
            legs(pose, -6 * cock + 14 * snap, 0)
        end
    end

    -- the eclipse howl: head thrown back to the sky, jaw wide, then the cry
    local howl = anim.actions.EclipseHowl
    if howl then
        local windUp = howl.args[1] or 1.0
        t = anim:action("EclipseHowl", windUp + 1.0)
        if t then
            local w = envelope(t, windUp * 0.8, windUp + 1.0, 0.5)
            local burst = envelope(t - windUp, 0.05, 0.7, 0.4)
            add(pose, "Body", 6 * w, 0, 0, 0.4 * w)
            add(pose, "Neck", 34 * w)
            add(pose, "Head", 28 * w + 3 * burst * math.sin(t * 40))
            add(pose, "Jaw", -38 * w)
            add(pose, "Tail", 18 * w)
        end
    end

    -- the moon leap: a deep crouch, then stretched flat through the air, tail streaming
    local leap = anim.actions.MoonLeap
    if leap then
        local windUp, air = leap.args[1] or 0.55, leap.args[2] or 1.4
        t = anim:action("MoonLeap", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", -6 * crouch, 0, 0, -2 * crouch)
            for _, leg in LEGS do
                local front = string.sub(leg, 1, 5) == "Front"
                add(pose, leg .. "Upper", (if front then -16 else 18) * crouch)
                add(pose, leg .. "Lower", (if front then 28 else -30) * crouch)
            end
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local stretch = envelope(u, 0.12, 1, 0.22)
                add(pose, "Body", (12 - 24 * u) * stretch)
                legs(pose, 62 * stretch, -55 * stretch)
                add(pose, "Neck", -6 * stretch)
                add(pose, "Head", 10 * stretch)
                add(pose, "Jaw", -24 * stretch * u)
                add(pose, "Tail", -28 * stretch)
                add(pose, "TailTip", -20 * stretch)
            end
        end
    end

    -- landing: the shoulders take it
    t = anim:action("Land", 0.6)
    if t then
        local give = envelope(t, 0.05, 0.6, 0.45)
        add(pose, "Body", -5 * give, 0, 0, -1.6 * give)
        for _, leg in LEGS do
            local front = string.sub(leg, 1, 5) == "Front"
            add(pose, leg .. "Lower", (if front then 20 else -20) * give)
        end
    end
end

-- ---------- the eyes and the corona ----------
-- Asleep the eyes are shut (iris and pupil hidden: the skull behind them is the closed lid) and
-- the corona burns low (Neon fades with transparency; a darker colour would turn it black).
local EYE = Color3.fromRGB(255, 154, 0)
local RAGE = Color3.fromRGB(255, 60, 20)
local OPEN = { Guardian = 1, Weakened = 1.15, Enraged = 0.7, Returning = 0.9 }

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.pupils = model:FindFirstChild("Pupils")
    anim.corona = model:FindFirstChild("Corona")
    anim.irisSize = anim.iris and anim.iris.Size
    anim.pupilSize = anim.pupils and anim.pupils.Size
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
    local awaken = anim:action("Awaken", 2.0)
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local amount = OPEN[state] or 1
    if not asleep and now >= anim.nextBlink then
        anim.blinkAt = now
        anim.nextBlink = now + 3 + 3 * math.random()
    end
    if anim.blinkAt then
        local b = (now - anim.blinkAt) / 0.26
        if b >= 1 then
            anim.blinkAt = nil
        else
            amount *= 1 - math.min(1, math.sin(math.pi * b) * 1.6) * 0.95   -- shut for a moment at its middle
        end
    end
    if awaken then
        amount *= smooth((awaken - 0.3) / 0.5)
    end
    local color = if state == "Enraged" then RAGE else EYE
    if state == "Weakened" then
        color = Color3.fromRGB(150, 80, 0):Lerp(EYE, 0.5 + 0.5 * math.sin(now * 12) * math.sin(now * 4.7))
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

    -- the corona: low asleep, guttering weakened, flickering in its rage, flaring as it howls
    local corona = anim.corona
    if corona then
        local fade = if asleep then 0.55 elseif state == "Weakened" then 0.25 + 0.25 * math.abs(math.sin(now * 6) * math.sin(now * 2.3))
            elseif state == "Enraged" then 0.12 * math.abs(math.sin(now * 17))
            else 0.05
        local howl = anim.actions.EclipseHowl
        if howl then
            fade *= 1 - envelope(now - howl.start - (howl.args[1] or 1), 0.05, 0.8, 0.5)
        end
        corona.Transparency += (fade - corona.Transparency) * 0.3
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local ECLIPSE = CFrame.new(0, 27.5, -3.5)       -- the eclipse's centre (hound-local)
local MOUTH = CFrame.new(0, 21, -23)            -- before its jaws
local BITE = CFrame.new(0, 3, -24)              -- where the bite lands

Rig.Fx = {
    Awaken = function(model)
        local pivot = model:GetPivot()
        task.delay(0.7, function()
            if model.Parent then
                GuardianFx.flash(model:GetPivot() * ECLIPSE, style, 22)
                GuardianFx.streaks(model:GetPivot() * MOUTH * CFrame.Angles(math.rad(50), 0, 0), style, 10, 50, 25)
            end
        end)
        GuardianFx.shake(pivot.Position, 0.8, 0.6)
    end,
    Bite = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * MOUTH, style, 14)
            GuardianFx.puff(pivot * BITE, style, 14, 16, 70, 3, 1)
            GuardianFx.shake(pivot.Position, 1.2, 0.35)
        end)
    end,
    EclipseHowl = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * ECLIPSE, style, 30)
            GuardianFx.streaks(pivot * ECLIPSE * CFrame.Angles(math.rad(90), 0, 0), style, 18, 45, 60)
            GuardianFx.shake(pivot.Position, 2, 0.9)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 180, style)
        end)
    end,
    MoonLeap = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 22, 20, Vector2.new(180, 10), 3, 1.2)
        end)
    end,
    Land = function(model, position)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 34, 30, Vector2.new(180, 8), 4, 1.4)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 16)
        GuardianFx.shake(position, 2.6, 0.6)
    end,
}

return Rig

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

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}

Rig.Joints = {
    "Body", "Neck", "Head", "Jaw", "Tail", "TailTip",
    "FrontLeftUpper", "FrontLeftLower", "FrontRightUpper", "FrontRightLower",
    "BackLeftUpper", "BackLeftLower", "BackRightUpper", "BackRightLower",
}
local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }

-- awake, it stands a little low on flexed legs (the planted paws need the slack)
Rig.Poses = {
    Dormant = { Neck = { -24 }, Head = { -12 }, Tail = { -25 }, TailTip = { -15 } },
    Guardian = { Body = { 0, 0, 0, -0.8 }, Neck = { 4 }, Tail = { 8 } },
    Weakened = {
        Body = { -4, 0, 0, -1.5 }, Neck = { -22 }, Head = { -14 }, Jaw = { -8 }, Tail = { -30 }, TailTip = { -20 },
        FrontLeftUpper = { -10 }, FrontRightUpper = { -10 }, FrontLeftLower = { 16 }, FrontRightLower = { 16 },
    },
    Enraged = {
        Body = { -3, 0, 0, -0.8 }, Neck = { -8 }, Head = { 8 }, Jaw = { -22 }, Tail = { 25 }, TailTip = { 15 },
    },
    Returning = { Body = { 0, 0, 0, -0.8 }, Head = { -4 } },
    Resting = { Neck = { -24 }, Head = { -12 }, Tail = { -25 }, TailTip = { -15 } },
}
Rig.Gallop = { 14, 22 }
Rig.LeapAction = "MoonLeap"
Rig.Look = { Joint = "Head", Share = 0.7, Body = "Neck", BodyShare = 0.3, Limit = 50 }
-- springs (GuardianAnim): a supple hound's body, the neck and head trailing it, and the tail in
-- two loose lengths, the tip whipping after the root
Rig.Springs = {
    Body = { Freq = 4.5, Damping = 0.55, Drag = 0 },
    Neck = { Freq = 4.5, Damping = 0.5, Drag = 0.25 },
    Head = { Freq = 5.5, Damping = 0.5, Drag = 0.35 },
    Jaw = { Freq = 8, Damping = 0.45, Drag = 0 },
    Tail = { Freq = 2.6, Damping = 0.3, Drag = 1 },
    TailTip = { Freq = 2.2, Damping = 0.26, Drag = 1 },
}
Rig.Lean = { Joint = "Body", Accel = 0.14, Bank = 0.07, Max = 8 }
-- planted feet (GuardianAnim): the forelegs fold on a positive Lower turn, the hind legs on a
-- negative one (measured in Play)
Rig.Legs = {
    { Name = "FrontLeft", Upper = "FrontLeftUpper", Lower = "FrontLeftLower", Axis = 1, Bend = 1 },
    { Name = "FrontRight", Upper = "FrontRightUpper", Lower = "FrontRightLower", Axis = 1, Bend = 1 },
    { Name = "BackLeft", Upper = "BackLeftUpper", Lower = "BackLeftLower", Axis = 1, Bend = -1 },
    { Name = "BackRight", Upper = "BackRightUpper", Lower = "BackRightLower", Axis = 1, Bend = -1 },
}
Rig.Style = { Debris = "Frost", Qi = Color3.fromRGB(110, 190, 255), QiCore = Color3.fromRGB(235, 248, 255) }

local TROT_STRIDE, GALLOP_STRIDE = 14, 26

function Rig.gait(anim, pose, dt)
    local stride = TROT_STRIDE + (GALLOP_STRIDE - TROT_STRIDE) * anim.gallop
    anim.phase = (anim.phase + dt * anim.stepSpeed / stride) % 1
    -- measured in Play: a 22 degree swing, a 50 degree fold and the body about 1.4 studs low (with
    -- the awake poses' 0.8) keep the stance paws planted and the swing paws clear
    local amplitude = (22 + 18 * anim.gallop) * anim.moving
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
        add(pose, leg .. "Lower", (if front then 1 else -1) * (50 + 16 * anim.gallop) * lift * anim.moving)
        anim:lift(leg, math.min(1, lift * 2) * anim.moving)
    end
    local bound = 2 * math.pi * anim.phase
    -- trotting, the weight rolls onto each diagonal pair in turn; galloping, the back flexes instead
    add(pose, "Body", 5 * anim.gallop * math.sin(bound) * anim.moving, 0, 1.4 * math.sin(bound) * (1 - anim.gallop) * anim.moving,
        ((0.3 + 0.8 * anim.gallop) * math.abs(math.sin(bound * 2)) - 0.75) * anim.moving)
    add(pose, "Neck", -4 * anim.gallop * math.sin(bound) * anim.moving)
    add(pose, "Tail", -10 * anim.gallop * anim.moving, 0, 8 * math.sin(bound * 2) * anim.moving)
    add(pose, "TailTip", -12 * anim.gallop * anim.moving, 0, 12 * math.sin(bound * 2 - 0.6) * anim.moving)
end

-- breathing that heaves the body over its planted paws, a restless shift of weight, the tail's
-- wave while it is awake
function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 1.8 elseif asleep then 0.25 else 0.5
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Body", 1.2 * breath, 0, 0, 0.3 * breath)
    add(pose, "Neck", -1.6 * math.sin(now * rate * 2 * math.pi + 0.8))
    if not asleep then
        local idle = 1 - anim.moving
        add(pose, "Body", 0, 1.8 * math.sin(now * 0.37) * idle, 1.6 * math.sin(now * 0.51) * idle)
        add(pose, "Neck", 2 * math.sin(now * 0.29) * idle, 3 * math.sin(now * 0.23) * idle)
    end
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
        keyed(pose, t, {
            { 0, {} },
            { 0.5, { Body = { 2, 0, 0, -0.4 }, Neck = { 22 }, Head = { 10 } }, "out" },
            { 0.85, { Body = { 6, 0, 0, -0.8 }, Neck = { 46 }, Head = { 36 }, Jaw = { -34 }, Tail = { 14 } }, "out" },
            { 1.4, { Body = { 5, 0, 0, -0.7 }, Neck = { 42 }, Head = { 32 }, Jaw = { -30 }, Tail = { 12 } }, "linear" },
            { 2.0, {} },
        })
    end

    -- faltering: it staggers, the weight lurching side to side, the forelegs buckling
    t = anim:action("Weaken", 1.9)
    if t then
        local w = envelope(t, 0.2, 1.9, 0.6)
        add(pose, "Body", -3 * w, 0, 6 * math.sin(t * 7) * w, -1.2 * w)
        add(pose, "Neck", -10 * w, 0, -4 * math.sin(t * 7 - 0.6) * w)
    end

    -- the bite: it draws back, mouth opening, then lunges over its planted paws and snaps shut
    local bite = anim.actions.Bite
    if bite then
        local w = bite.args[1] or 0.5
        t = anim:action("Bite", w + 0.7)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w - 0.1, { Body = { 3, 0, 0, -0.5, 1.4 }, Neck = { 14 }, Head = { 10 }, Jaw = { -38 }, Tail = { 10 } } },
                { w + 0.02, { Body = { -6, 0, 0, -1.0, -2.8 }, Neck = { -24 }, Head = { -8 }, Jaw = { 4 }, Tail = { -6 } }, "in" },
                { w + 0.25, { Body = { -4, 0, 0, -0.8, -2.2 }, Neck = { -18 }, Head = { -6 }, Jaw = { 0 } }, "out" },
                { w + 0.7, {} },
            })
        end
    end

    -- the eclipse howl: it coils low, drawing breath; the chest rises; at the release it sits back
    -- and throws its head to the sky, jaws wide, holds the cry quivering, and lets it fade
    local howl = anim.actions.EclipseHowl
    if howl then
        local w = howl.args[1] or 1.0
        t = anim:action("EclipseHowl", w + 1.3)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.3, { Body = { -4, 0, 0, -1.4 }, Neck = { -18 }, Head = { -10 }, Tail = { -16 } }, "out" },
                { w - 0.12, { Body = { 6, 0, 0, -0.9 }, Neck = { 18 }, Head = { 10 }, Jaw = { -14 }, Tail = { 6 } } },
                { w + 0.06, { Body = { 10, 0, 0, -1.2 }, Neck = { 40 }, Head = { 32 }, Jaw = { -48 }, Tail = { 24 }, TailTip = { 14 } }, "out" },
                { w + 0.7, { Body = { 9, 0, 0, -1.1 }, Neck = { 38 }, Head = { 30 }, Jaw = { -44 }, Tail = { 20 }, TailTip = { 10 } }, "linear" },
                { w + 1.3, {} },
            })
            local build = smooth((t - w * 0.45) / (w * 0.55)) * (if t < w then 1 else 0)
            anim:tremor("Body", 0.6 * build * math.sin(t * 43), 0, 0.5 * build * math.sin(t * 37))
            local burst = envelope(t - w, 0.05, 0.7, 0.3)
            anim:tremor("Head", 3 * burst * math.sin(t * 40), 1.5 * burst * math.sin(t * 31))
        end
    end

    -- the moon leap: a deep crouch (its planted paws fold under it), then stretched flat through the
    -- air, tail streaming
    local leap = anim.actions.MoonLeap
    if leap then
        local windUp, air = leap.args[1] or 0.55, leap.args[2] or 1.4
        t = anim:action("MoonLeap", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", -6 * crouch, 0, 0, -2 * crouch)
            add(pose, "Neck", -10 * crouch)
            add(pose, "Tail", -14 * crouch)
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

    -- landing: the shoulders take it, sinking deep over the paws, and it rebounds
    t = anim:action("Land", 0.7)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.08, { Body = { -6, 0, 0, -2.2 }, Neck = { -12 }, Tail = { -14 } }, "out" },
            { 0.3, { Body = { 2, 0, 0, 0.1 }, Neck = { 4 } } },
            { 0.7, {} },
        })
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

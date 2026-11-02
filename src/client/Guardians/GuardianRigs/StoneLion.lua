-- The Awakened Stone Lion's rig (GuardianAnim) and effects (GuardianFx).
--
-- Joints: Body (from the root), Head, Jaw, Tail, and an upper and lower piece per leg. A negative X
-- turn on the Jaw opens the mouth.
--   Dormant   a statue before the Egg Garden;
--   Weakened  a forepaw drawn up, head low, panting;
--   Enraged   crouched, tail up, snarling.
-- It walks with diagonal legs together, breaking into a gallop as it speeds up. Its eyes and orb
-- are carved stone and dull jade while it sleeps, Neon blue and jade awake, flickering weakened,
-- red-orange and widened enraged; they blink. Its debris is stone dust, its Qi blue.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}

Rig.Joints = {
    "Body", "Head", "Jaw", "Tail",
    "FrontLeftUpper", "FrontLeftLower", "FrontRightUpper", "FrontRightLower",
    "BackLeftUpper", "BackLeftLower", "BackRightUpper", "BackRightLower",
}
local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }

-- awake, it stands a little low on flexed legs (the planted paws need the slack to stay down as it
-- breathes and shifts its weight)
Rig.Poses = {
    Dormant = { Head = { -4 } },
    Guardian = { Body = { 0, 0, 0, -0.8 }, Head = { 0 } },
    Weakened = {
        Body = { -3, 0, 0, -1.2 }, Head = { -16 }, Jaw = { -9 }, Tail = { -22 },
        -- a paw drawn up to the chest (the elbow folds on a positive turn)
        FrontRightUpper = { 40 }, FrontRightLower = { 95 },
    },
    Enraged = { Body = { -4, 0, 0, -0.8 }, Head = { -7 }, Jaw = { -16 }, Tail = { 38 } },
    Returning = { Body = { 0, 0, 0, -0.8 }, Head = { -6 } },
    Resting = { Body = { 0, 0, 0, -0.6 }, Head = { -10 } },
}
Rig.Gallop = { 13, 19 }          -- speeds (studs/s) where the walk turns into a gallop
Rig.LeapAction = "Pounce"
Rig.Look = { Joint = "Head", Share = 0.75, Body = "Body", BodyShare = 0.15, Limit = 40 }
-- springs (GuardianAnim): a heavy stone body that settles after each move, the head trailing it a
-- little, a snapping jaw, and the tail a loose rope that whips round on turns and rears
Rig.Springs = {
    Body = { Freq = 4, Damping = 0.6, Drag = 0 },
    Head = { Freq = 5, Damping = 0.55, Drag = 0.3 },
    Jaw = { Freq = 8, Damping = 0.45, Drag = 0 },
    Tail = { Freq = 2.2, Damping = 0.3, Drag = 1 },
}
Rig.Lean = { Joint = "Body", Accel = 0.12, Bank = 0.05, Max = 7 }
-- planted feet (GuardianAnim): every leg folds on a positive Lower turn, the forelegs' elbows
-- pointing back (measured in Play)
Rig.Legs = {
    { Name = "FrontLeft", Upper = "FrontLeftUpper", Lower = "FrontLeftLower", Axis = 1, Bend = 1 },
    { Name = "FrontRight", Upper = "FrontRightUpper", Lower = "FrontRightLower", Axis = 1, Bend = 1 },
    { Name = "BackLeft", Upper = "BackLeftUpper", Lower = "BackLeftLower", Axis = 1, Bend = 1 },
    { Name = "BackRight", Upper = "BackRightUpper", Lower = "BackRightLower", Axis = 1, Bend = 1 },
}
Rig.Style = { Debris = "Dust", Qi = Color3.fromRGB(0, 110, 255), QiCore = Color3.fromRGB(150, 210, 255) }

local BREATH = { Dormant = 0, Guardian = 1, Weakened = 1.7, Enraged = 1.3, Returning = 0.7, Resting = 0.4 }
local WALK_STRIDE, GALLOP_STRIDE = 13, 24

function Rig.gait(anim, pose, dt)
    local stride = WALK_STRIDE + (GALLOP_STRIDE - WALK_STRIDE) * anim.gallop
    anim.phase = (anim.phase + dt * anim.stepSpeed / stride) % 1
    -- each leg swings through, folding as it comes forward and leaving the ground quickly; the
    -- stance legs are planted (GuardianAnim). Measured in Play: a 20 degree swing and a body about
    -- 1.8 studs low (with the awake poses' 0.8) keep the stance feet on the ground, a 45 degree fold
    -- clears the swing feet
    local amplitude = (20 + 14 * anim.gallop) * anim.moving
    local offsets = {
        FrontLeft = 0 + 0.1 * anim.gallop, FrontRight = 0.5 - 0.4 * anim.gallop,
        BackLeft = 0.5, BackRight = 0 + 0.6 * anim.gallop,
    }
    for _, leg in LEGS do
        local a = 2 * math.pi * (anim.phase + offsets[leg])
        local lift = math.max(0, math.cos(a))
        add(pose, leg .. "Upper", amplitude * math.sin(a))
        add(pose, leg .. "Lower", (45 + 15 * anim.gallop) * lift * anim.moving)
        anim:lift(leg, math.min(1, lift * 2) * anim.moving)
    end
    local bound = 2 * math.pi * anim.phase
    -- walking, the weight rolls onto each diagonal pair in turn and the body dips as each lands;
    -- galloping, the back flexes and the body bounds
    add(pose, "Body", 4 * anim.gallop * math.sin(bound) * anim.moving, 0, 2.6 * math.sin(bound) * (1 - anim.gallop) * anim.moving,
        ((0.5 + 0.5 * anim.gallop) * math.abs(math.sin(bound * 2)) - 1.05) * anim.moving)
    add(pose, "Head", (2.5 * math.sin(bound * 2 + 0.8) - 3 * anim.gallop * math.sin(bound)) * anim.moving)
    add(pose, "Tail", 10 * anim.gallop * anim.moving, 0, 8 * math.sin(bound * 2) * anim.moving)
end

-- breathing that heaves the whole body over its planted paws, a slow shift of weight, the head
-- bobbing a beat behind, and the tail's sway while it is awake
function Rig.life(anim, pose, state, now)
    local breath = BREATH[state] or 0
    local rate = if state == "Weakened" then 1.6 else 0.45
    local b = math.sin(now * rate * 2 * math.pi)
    add(pose, "Body", 1.6 * breath * b, 0, 0, 0.4 * breath * b)
    add(pose, "Head", -1.8 * breath * math.sin(now * rate * 2 * math.pi + 0.9))
    if state ~= "Dormant" and state ~= "Resting" then
        local idle = 1 - anim.moving
        add(pose, "Body", 0, 1.5 * math.sin(now * 0.31) * idle, 1.8 * math.sin(now * 0.43) * idle)
        local sway = if state == "Enraged" then 2.6 else 0.9
        add(pose, "Tail", 0, 14 * math.sin(now * sway), 7 * math.sin(now * sway * 0.7))
    end
    -- weakened, a forepaw drawn up off the ground
    anim:lift("FrontRight", anim.weights.Weakened or 0)
end

function Rig.actions(anim, pose, now)
    -- waking: a tremble through the stone, the head shaking itself free, then rising into a roar
    local t = anim:action("Awaken", 1.8)
    if t then
        local shake = envelope(t, 0.1, 0.6, 0.2)
        anim:tremor("Body", 0, 1.5 * shake * math.sin(t * 70), 1.2 * shake * math.sin(t * 53))
        keyed(pose, t, {
            { 0, {} },
            { 0.35, { Body = { -3, 0, 0, -0.8 }, Head = { -12 } }, "out" },
            { 0.75, { Body = { 7, 0, 0, -0.6 }, Head = { 30 }, Jaw = { -40 }, Tail = { 20 } }, "out" },
            { 1.15, { Body = { 6, 0, 0, -0.5 }, Head = { 26 }, Jaw = { -34 }, Tail = { 16 } }, "linear" },
            { 1.8, {} },
        })
    end

    -- faltering: it rears, front paws pawing the air, then drops heavily back down
    t = anim:action("Weaken", 1.9)
    if t then
        local up = envelope(t, 0.4, 1.9, 0.6)
        keyed(pose, t, {
            { 0, {} },
            { 0.18, { Body = { -4, 0, 0, -1.2 }, Head = { -10 } }, "out" },
            { 0.6, { Body = { 22, 0, 0, -0.4 }, Head = { 18 }, Jaw = { -30 }, Tail = { -10 } }, "out" },
            { 1.3, { Body = { 18, 0, 0, -0.4 }, Head = { 12 }, Jaw = { -24 }, Tail = { -14 } }, "linear" },
            { 1.6, { Body = { -6, 0, 0, -1.6 }, Head = { -14 }, Jaw = { -8 } }, "in" },
            { 1.9, {} },
        })
        add(pose, "FrontLeftUpper", (30 + 14 * math.sin(t * 9)) * up)
        add(pose, "FrontRightUpper", (30 - 14 * math.sin(t * 9)) * up)
        add(pose, "FrontLeftLower", 40 * up)
        add(pose, "FrontRightLower", 40 * up)
        anim:lift("FrontLeft", up)
        anim:lift("FrontRight", up)
    end

    -- the slam: the weight rocks back onto the right, the left paw comes up high, hangs, then
    -- comes down hard (fastest at the strike), the body driving down behind it
    local slam = anim.actions.Slam
    if slam then
        local w = slam.args[1] or 0.75
        t = anim:action("Slam", w + 0.85)
        if t then
            keyed(pose, t, {
                { 0, {} },
                -- a negative roll puts the weight on the right paw (measured: it stays planted)
                { w * 0.3, { Body = { -3, 0, -4, -0.9 }, Head = { -6, 6 } }, "out" },
                { w - 0.12, { Body = { 8, 0, -6, -1.2 }, Head = { 12, -8 }, Jaw = { -12 }, Tail = { 14 },
                    FrontLeftUpper = { 88 }, FrontLeftLower = { 70 } } },
                { w, { Body = { -7, 0, 3, -1.3 }, Head = { -16 }, Jaw = { -34 }, FrontLeftUpper = { -6 } }, "in" },
                { w + 0.25, { Body = { -5, 0, 2, -1.0 }, Head = { -12 }, Jaw = { -28 }, FrontLeftUpper = { -4 } }, "out" },
                { w + 0.85, {} },
            })
            -- the striking paw is off the ground from the rock-back until it lands
            anim:lift("FrontLeft", envelope(t, w * 0.3, w, 0.04))
        end
    end

    -- the roar: it coils, head low, haunches dropping; the chest swells, shaking; at the release it
    -- sits back on its haunches and throws its head up, jaws wide, holds the roar quivering, and
    -- slowly lets it go
    local roar = anim.actions.Roar
    if roar then
        local w = roar.args[1] or 1.1
        t = anim:action("Roar", w + 1.3)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.3, { Body = { -5, 0, 0, -1.6 }, Head = { -18 }, Jaw = { -6 }, Tail = { -20 } }, "out" },
                { w - 0.14, { Body = { 7, 0, 0, -0.8 }, Head = { 8 }, Jaw = { -16 }, Tail = { 6 } } },
                { w + 0.05, { Body = { 12, 0, 0, -1.1 }, Head = { 36 }, Jaw = { -52 }, Tail = { 34 } }, "out" },
                { w + 0.6, { Body = { 11, 0, 0, -1.0 }, Head = { 32 }, Jaw = { -48 }, Tail = { 28 } }, "linear" },
                { w + 1.3, {} },
            })
            local build = smooth((t - w * 0.45) / (w * 0.55)) * (if t < w then 1 else 0)
            anim:tremor("Body", 0.7 * build * math.sin(t * 47), 0, 0.5 * build * math.sin(t * 39))
            local burst = envelope(t - w, 0.05, 0.6, 0.3)
            anim:tremor("Head", 4 * burst * math.sin(t * 40), 2 * burst * math.sin(t * 29))
        end
    end

    -- the pounce: a crouch (the planted paws fold under it), then stretched out through the air
    local pounce = anim.actions.Pounce
    if pounce then
        local windUp, air = pounce.args[1] or 0.6, pounce.args[2] or 0.95
        t = anim:action("Pounce", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", -6 * crouch, 0, 0, -2.4 * crouch)
            add(pose, "Head", -8 * crouch)
            add(pose, "Tail", -12 * crouch)
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local stretch = envelope(u, 0.15, 1, 0.25)
                add(pose, "Body", (10 - 20 * u) * stretch)
                add(pose, "FrontLeftUpper", 55 * stretch)
                add(pose, "FrontRightUpper", 55 * stretch)
                add(pose, "BackLeftUpper", -45 * stretch)
                add(pose, "BackRightUpper", -45 * stretch)
                add(pose, "Head", 8 * stretch)
                add(pose, "Jaw", -28 * stretch)
                add(pose, "Tail", -25 * stretch)
            end
        end
    end

    -- landing: the body takes the weight, sinking deep over its paws, and rebounds
    t = anim:action("Land", 0.7)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.08, { Body = { -6, 0, 0, -2.6 }, Head = { -10 }, Tail = { -14 } }, "out" },
            { 0.3, { Body = { 2, 0, 0, 0.2 }, Head = { 4 } }, "inout" },
            { 0.7, {} },
        })
    end
end

-- The eyes and orb. The eyes are a temple lion's (an almond iris, a dark Neon cat pupil, carved stone
-- lids in a frown): asleep they are carved stone, the pupil cut a shade darker, and the orb dull jade
-- (dark Neon renders as a flat black disc); awake, Neon blue, a slow blink every few seconds; weakened,
-- flickering and wide; enraged, red-orange and wider still. Set locally: the server never changes them.
local STONE = Color3.fromRGB(160, 156, 148)
local STONE_PUPIL = Color3.fromRGB(96, 92, 86)
local PUPIL = Color3.fromRGB(6, 16, 28)
local DULL_JADE = Color3.fromRGB(46, 116, 88)
local EYES = {
    Guardian = Color3.fromRGB(0, 110, 255),
    Weakened = Color3.fromRGB(0, 110, 255),
    Enraged = Color3.fromRGB(255, 70, 20),
    Returning = Color3.fromRGB(0, 110, 255),
}
local OPEN = { Weakened = 1.15, Enraged = 1.2 }   -- the iris's height by state (1 otherwise)
local ORB = Color3.fromRGB(0, 160, 95)
local ORB_DIM = Color3.fromRGB(0, 90, 55) -- dimmest it flickers to while weakened (darker Neon reads black)

function Rig.setup(anim)
    anim.eyes = anim.model:FindFirstChild("Eyes")
    anim.pupils = anim.model:FindFirstChild("Pupils")
    anim.orb = anim.model:FindFirstChild("Orb")
    anim.eyeSize = anim.eyes and anim.eyes.Size
    anim.pupilSize = anim.pupils and anim.pupils.Size
    anim.nextBlink = os.clock() + 2
end

-- a size change keeps the part's centre; its weld to the head is untouched
local function open(part, base, amount)
    if part then
        local size = Vector3.new(base.X, math.max(base.Y * amount, 0.02), base.Z)
        if (part.Size - size).Magnitude > 0.005 then
            part.Size = part.Size:Lerp(size, 0.6)   -- quick enough for a full blink
        end
    end
end

function Rig.glow(anim, state, now)
    local eyes, pupils, orb = anim.eyes, anim.pupils, anim.orb
    local color = EYES[state] or EYES.Guardian
    if state == "Weakened" then
        local flicker = 0.5 + 0.5 * math.sin(now * 13) * math.sin(now * 5.3)
        color = Color3.fromRGB(0, 60, 150):Lerp(color, 0.35 + 0.65 * flicker)
    end
    local awaken = anim:action("Awaken", 1.8)
    if awaken then
        color = Color3.fromRGB(0, 60, 150):Lerp(EYES.Guardian, smooth((awaken - 0.3) / 0.4))
    end
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local amount = OPEN[state] or 1
    if not asleep and now >= anim.nextBlink then
        anim.blinkAt = now
        anim.nextBlink = now + 2.5 + 3 * math.random()
    end
    if anim.blinkAt then
        local b = (now - anim.blinkAt) / 0.28
        if b >= 1 then
            anim.blinkAt = nil
        elseif not asleep then
            amount *= 1 - math.min(1, math.sin(math.pi * b) * 1.6) * 0.95   -- shut for a moment at its middle
        end
    end
    local material = if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon
    if eyes then
        if eyes.Material ~= material then
            eyes.Material = material
        end
        eyes.Color = if asleep then STONE else eyes.Color:Lerp(color, 0.25)
        open(eyes, anim.eyeSize, if asleep then 1 else amount)
    end
    if pupils then
        if pupils.Material ~= material then
            pupils.Material = material
        end
        pupils.Color = if asleep then STONE_PUPIL else PUPIL
        open(pupils, anim.pupilSize, if asleep then 1 else amount)
    end
    if orb then
        local orbMaterial = if asleep then Enum.Material.Glass else Enum.Material.Neon
        if orb.Material ~= orbMaterial then
            orb.Material = orbMaterial
        end
        local lit = if asleep then DULL_JADE
            elseif state == "Weakened" then ORB_DIM:Lerp(ORB, 0.5 + 0.5 * math.sin(now * 7))
            else ORB
        orb.Color = if asleep then lit else orb.Color:Lerp(lit, 0.2)
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local SLAM_SPOT = CFrame.new(-4.6, 0.3, -17)   -- where the left paw comes down (lion-local)
local MOUTH = CFrame.new(0, 21.5, -21)         -- the jaws

Rig.Fx = {
    Awaken = function(model)
        local body = model:FindFirstChild("Body")
        GuardianFx.shed(body, style, 30)
        if body then
            GuardianFx.shake(body.Position, 1.2, 0.7)
        end
    end,
    Slam = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local at = model:GetPivot() * SLAM_SPOT
            GuardianFx.puff(at, style, 22, 22, Vector2.new(80, 8), 3, 1)
            GuardianFx.flash(at, style, 10)
            GuardianFx.shake(at.Position, 1.6, 0.45)
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
    Land = function(model, position)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 36, 34, Vector2.new(180, 6), 4, 1.3)
        GuardianFx.shake(position, 3, 0.7)
    end,
}

return Rig

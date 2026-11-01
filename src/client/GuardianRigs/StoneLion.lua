-- The Awakened Stone Lion's rig (GuardianAnim) and effects (GuardianFx): how it moves and what its
-- moves look like.
--
-- Joints: Body (from the root), Head, Jaw, Tail, and an upper and lower piece per leg. A negative X
-- turn on the Jaw opens the mouth.
--   Dormant   a statue, its right paw pressed on the egg (the Hold);
--   Weakened  the paw drawn up off the egg, head low, panting;
--   Enraged   crouched, tail up, snarling.
-- It walks with diagonal legs together, breaking into a gallop as it speeds up. Its eyes and orb
-- are carved stone and dull jade while it sleeps, Neon blue and jade awake, flickering weakened,
-- red-orange and widened enraged. Its debris is stone dust, its Qi blue.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}

Rig.Joints = {
    "Body", "Head", "Jaw", "Tail",
    "FrontLeftUpper", "FrontLeftLower", "FrontRightUpper", "FrontRightLower",
    "BackLeftUpper", "BackLeftLower", "BackRightUpper", "BackRightLower",
}
local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }

Rig.Poses = {
    Dormant = { Head = { -4 } },
    Guardian = { Head = { 0 } },
    Weakened = {
        Body = { -3, 0, 0, -1.2 }, Head = { -16 }, Jaw = { -9 }, Tail = { -22 },
        -- the paw drawn up to the chest, off the egg
        FrontRightUpper = { 30 }, FrontRightLower = { -95 },
    },
    Enraged = { Body = { -4, 0, 0, -1.5 }, Head = { -7 }, Jaw = { -16 }, Tail = { 38 } },
    Returning = { Head = { -6 } },
    Resting = { Body = { 0, 0, 0, -0.6 }, Head = { -10 } },
}
-- The right paw pressed on the egg: measured in Studio, the sole rests 3.85 studs up, on a 4-stud egg.
Rig.Hold = { FrontRightUpper = { 66 }, FrontRightLower = { -66 } }
Rig.HoldStates = { Dormant = true, Guardian = true }
Rig.Gallop = { 13, 19 }          -- speeds (studs/s) where the walk turns into a gallop
Rig.LeapAction = "Pounce"
Rig.Look = { Joint = "Head", Share = 0.75, Body = "Body", BodyShare = 0.15, Limit = 40 }
Rig.Style = { Debris = "Dust", Qi = Color3.fromRGB(0, 110, 255), QiCore = Color3.fromRGB(150, 210, 255) }

local BREATH = { Dormant = 0, Guardian = 1, Weakened = 1.7, Enraged = 1.3, Returning = 0.7, Resting = 0.4 }
local WALK_STRIDE, GALLOP_STRIDE = 13, 24

function Rig.gait(anim, pose, dt)
    local stride = WALK_STRIDE + (GALLOP_STRIDE - WALK_STRIDE) * anim.gallop
    anim.phase = (anim.phase + dt * anim.speed / stride) % 1
    local amplitude = (24 + 16 * anim.gallop) * anim.moving
    local offsets = {
        FrontLeft = 0 + 0.1 * anim.gallop, FrontRight = 0.5 - 0.4 * anim.gallop,
        BackLeft = 0.5, BackRight = 0 + 0.6 * anim.gallop,
    }
    for _, leg in LEGS do
        local a = 2 * math.pi * (anim.phase + offsets[leg])
        local lift = math.max(0, math.cos(a)) -- the leg coming forward is lifted
        local front = string.sub(leg, 1, 5) == "Front"
        add(pose, leg .. "Upper", amplitude * math.sin(a))
        add(pose, leg .. "Lower", (if front then -1 else 1) * (30 + 15 * anim.gallop) * lift * anim.moving)
    end
    local bound = 2 * math.pi * anim.phase
    add(pose, "Body", 4 * anim.gallop * math.sin(bound) * anim.moving, 0, 0,
        (0.25 + 0.6 * anim.gallop) * math.abs(math.sin(bound * 2)) * anim.moving)
    add(pose, "Head", -3 * anim.gallop * math.sin(bound) * anim.moving)
    add(pose, "Tail", 10 * anim.gallop * anim.moving, 0, 8 * math.sin(bound * 2) * anim.moving)
end

-- breathing, and the tail's sway while it is awake
function Rig.life(anim, pose, state, now)
    local breath = BREATH[state] or 0
    local rate = if state == "Weakened" then 1.6 else 0.55
    add(pose, "Body", 0.8 * breath * math.sin(now * rate * 2 * math.pi), 0, 0, 0.18 * breath * math.sin(now * rate * 2 * math.pi))
    add(pose, "Head", -0.8 * breath * math.sin(now * rate * 2 * math.pi + 0.6))
    if state ~= "Dormant" and state ~= "Resting" then
        local sway = if state == "Enraged" then 2.6 else 0.9
        add(pose, "Tail", 0, 12 * math.sin(now * sway), 6 * math.sin(now * sway * 0.7))
    end
end

function Rig.actions(anim, pose, now)
    -- waking: a tremble through the stone, then the head comes up in a roar
    local t = anim:action("Awaken", 1.8)
    if t then
        local shake = envelope(t, 0.1, 0.6, 0.2)
        add(pose, "Body", 0, 1.5 * shake * math.sin(t * 70), 1.2 * shake * math.sin(t * 53))
        local roar = envelope(t - 0.45, 0.3, 1.3, 0.45)
        add(pose, "Head", 26 * roar)
        add(pose, "Jaw", -32 * roar)
        add(pose, "Body", 5 * roar)
    end

    -- faltering: it rears, the front rising, the hind legs planted, the front paws pawing the air
    t = anim:action("Weaken", 1.9)
    if t then
        local up = envelope(t, 0.45, 1.9, 0.7)
        add(pose, "Body", 20 * up)
        add(pose, "BackLeftUpper", -20 * up)
        add(pose, "BackRightUpper", -20 * up)
        add(pose, "FrontLeftUpper", (28 + 10 * math.sin(t * 9)) * up)
        add(pose, "FrontRightUpper", (28 - 10 * math.sin(t * 9)) * up)
        add(pose, "FrontLeftLower", -30 * up)
        add(pose, "FrontRightLower", -30 * up)
        add(pose, "Head", 14 * up)
        add(pose, "Jaw", -26 * up)
    end

    -- the left paw raised high, then slammed down
    local slam = anim.actions.Slam
    if slam then
        local windUp = slam.args[1] or 0.75
        t = anim:action("Slam", windUp + 0.6)
        if t then
            local raise
            if t < windUp then
                raise = smooth(t / windUp)
            elseif t < windUp + 0.1 then
                raise = 1 - (t - windUp) / 0.1
            else
                raise = 0
            end
            local after = envelope(t - windUp, 0.05, 0.6, 0.35)
            add(pose, "FrontLeftUpper", 78 * raise - 6 * after)
            add(pose, "FrontLeftLower", -55 * raise)
            add(pose, "Body", 6 * raise - 4 * after, 0, -3 * raise)
            add(pose, "BackLeftUpper", -6 * raise)
            add(pose, "BackRightUpper", -6 * raise)
            add(pose, "Head", 8 * raise - 12 * after)
            add(pose, "Jaw", -20 * after)
        end
    end

    -- the roar: chest up, head thrown back, jaw wide
    local roar = anim.actions.Roar
    if roar then
        local windUp = roar.args[1] or 1.1
        t = anim:action("Roar", windUp + 1.1)
        if t then
            local w = envelope(t, windUp * 0.8, windUp + 1.1, 0.5)
            local burst = envelope(t - windUp, 0.05, 0.6, 0.4)
            add(pose, "Body", 10 * w, 0, 0, 0.6 * w)
            add(pose, "Head", 24 * w + 4 * burst * math.sin(t * 40))
            add(pose, "Jaw", -36 * w)
            add(pose, "Tail", 20 * w)
        end
    end

    -- the pounce: a crouch, then stretched out through the air
    local pounce = anim.actions.Pounce
    if pounce then
        local windUp, air = pounce.args[1] or 0.6, pounce.args[2] or 0.95
        t = anim:action("Pounce", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Body", -6 * crouch, 0, 0, -2.4 * crouch)
            for _, leg in LEGS do
                local front = string.sub(leg, 1, 5) == "Front"
                add(pose, leg .. "Upper", (if front then -14 else 16) * crouch)
                add(pose, leg .. "Lower", (if front then 24 else -26) * crouch)
            end
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

    -- landing: the body takes the weight
    t = anim:action("Land", 0.6)
    if t then
        local give = envelope(t, 0.05, 0.6, 0.45)
        add(pose, "Body", -5 * give, 0, 0, -2 * give)
        for _, leg in LEGS do
            local front = string.sub(leg, 1, 5) == "Front"
            add(pose, leg .. "Lower", (if front then 18 else -18) * give)
        end
    end
end

-- The eyes and orb. Asleep they are carved stone and dull jade (dark Neon renders as a flat black
-- disc); awake, Neon. Set locally: the server never changes them.
local STONE = Color3.fromRGB(160, 156, 148)
local DULL_JADE = Color3.fromRGB(46, 116, 88)
local EYES = {
    Guardian = Color3.fromRGB(0, 110, 255),
    Weakened = Color3.fromRGB(0, 110, 255),
    Enraged = Color3.fromRGB(255, 70, 20),
    Returning = Color3.fromRGB(0, 110, 255),
}
local ORB = Color3.fromRGB(0, 160, 95)
local ORB_DIM = Color3.fromRGB(0, 90, 55) -- dimmest it flickers to while weakened (darker Neon reads black)

function Rig.setup(anim)
    anim.eyes = anim.model:FindFirstChild("Eyes")
    anim.orb = anim.model:FindFirstChild("Orb")
    anim.eyeSize = anim.eyes and anim.eyes.Size
end

function Rig.glow(anim, state, now)
    local eyes, orb = anim.eyes, anim.orb
    local color = EYES[state] or EYES.Guardian
    local open = 1
    if state == "Weakened" then
        local flicker = 0.5 + 0.5 * math.sin(now * 13) * math.sin(now * 5.3)
        color = Color3.fromRGB(0, 60, 150):Lerp(color, 0.35 + 0.65 * flicker)
    elseif state == "Enraged" then
        open = 1.7
    end
    local awaken = anim:action("Awaken", 1.8)
    if awaken then
        color = Color3.fromRGB(0, 60, 150):Lerp(EYES.Guardian, smooth((awaken - 0.3) / 0.4))
    end
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local material = if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon
    if eyes then
        if eyes.Material ~= material then
            eyes.Material = material
        end
        eyes.Color = if asleep then STONE else eyes.Color:Lerp(color, 0.25)
        -- (a size change keeps the part's centre; its weld to the head is untouched)
        local size = Vector3.new(anim.eyeSize.X, anim.eyeSize.Y * open, anim.eyeSize.Z)
        if (eyes.Size - size).Magnitude > 0.01 then
            eyes.Size = eyes.Size:Lerp(size, 0.2)
        end
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
            -- a blast of Qi from the jaws, thrown forward, then the wall of dust rolling out
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

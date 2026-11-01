-- Animates a guardian on the client: its joints (the Motor6Ds GuardianBuilder made, set through
-- Transform every frame; the server never animates) and its glowing eyes and orb.
--
-- The Stone Lion's joints: Body (from the root), Head, Jaw, Tail, and an upper and lower piece per
-- leg. Every Transform is in the lion's own axes (X to its right, Y up, -Z ahead): a positive X
-- turn swings a limb's far end forward and up; a negative one on the Jaw opens the mouth.
--
-- Layers, added together each frame:
--   the state's pose   blended over a fraction of a second when the state changes (Dormant: a
--                      statue, its right paw pressed on the egg; Weakened: the paw lifted off it,
--                      head low, panting; Enraged: crouched, tail up, snarling);
--   the gait           a walk (diagonal legs together) blending into a gallop as it speeds up,
--                      replacing the pinned paw while it moves;
--   life               breathing, the tail's sway, the head turned toward its target;
--   actions            one-shot moves from the server's events: Awaken, Rear, Slam, Roar, Pounce,
--                      Land.
local GuardianAnim = {}
GuardianAnim.__index = GuardianAnim

local Players = game:GetService("Players")

local LEGS = { "FrontLeft", "FrontRight", "BackLeft", "BackRight" }
local JOINTS = {
    "Body", "Head", "Jaw", "Tail",
    "FrontLeftUpper", "FrontLeftLower", "FrontRightUpper", "FrontRightLower",
    "BackLeftUpper", "BackLeftLower", "BackRightUpper", "BackRightLower",
}

-- Poses: per joint { pitch, yaw, roll (degrees), lift (studs up), shift (studs back) }.
-- The right paw pressed on the egg: measured in Studio, the sole rests 3.85 studs up, on a 4-stud egg.
local PIN = { FrontRightUpper = { 66 }, FrontRightLower = { -66 } }
local POSES = {
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
local PINNED = { Dormant = true, Guardian = true }
local BREATH = { Dormant = 0, Guardian = 1, Weakened = 1.7, Enraged = 1.3, Returning = 0.7, Resting = 0.4 }

-- the glow: eyes and orb by state. Asleep they are carved stone and dull jade (dark Neon renders as
-- a flat black disc); awake, Neon.
local STONE = Color3.fromRGB(160, 156, 148)
local DULL_JADE = Color3.fromRGB(46, 116, 88)
local EYES = {
    Dormant = Color3.fromRGB(0, 22, 60),
    Guardian = Color3.fromRGB(0, 110, 255),
    Weakened = Color3.fromRGB(0, 110, 255),
    Enraged = Color3.fromRGB(255, 70, 20),
    Returning = Color3.fromRGB(0, 110, 255),
    Resting = Color3.fromRGB(0, 22, 60),
}
local ORB = Color3.fromRGB(0, 160, 95)
local ORB_DIM = Color3.fromRGB(0, 90, 55) -- dimmest it flickers to while weakened (darker Neon reads black)

local WALK_STRIDE = 13   -- studs per walking cycle
local GALLOP_STRIDE = 24
local GALLOP_FROM, GALLOP_FULL = 13, 19 -- speeds (studs/s) where the walk turns into a gallop

local function smooth(x)
    x = math.clamp(x, 0, 1)
    return x * x * (3 - 2 * x)
end

-- 0 -> 1 over `rise`, held, then 1 -> 0 over the last `fall` of `total`
local function envelope(t, rise, total, fall)
    if t < 0 or t > total then
        return 0
    end
    return math.min(smooth(t / rise), smooth((total - t) / fall))
end

local function add(pose, joint, pitch, yaw, roll, lift, shift)
    local p = pose[joint]
    p[1] += pitch or 0
    p[2] += yaw or 0
    p[3] += roll or 0
    p[4] += lift or 0
    p[5] += shift or 0
end

local function blank()
    local pose = {}
    for _, joint in JOINTS do
        pose[joint] = { 0, 0, 0, 0, 0 }
    end
    return pose
end

local function addPose(pose, source, weight)
    for joint, values in source do
        add(pose, joint, (values[1] or 0) * weight, (values[2] or 0) * weight, (values[3] or 0) * weight,
            (values[4] or 0) * weight, (values[5] or 0) * weight)
    end
end

function GuardianAnim.new(model)
    local self = setmetatable({}, GuardianAnim)
    self.model = model
    self.root = model.PrimaryPart
    self.joints = {}
    for _, joint in JOINTS do
        self.joints[joint] = model:WaitForChild("Joints"):WaitForChild(joint)
    end
    self.eyes = model:FindFirstChild("Eyes")
    self.orb = model:FindFirstChild("Orb")
    self.eyeSize = self.eyes and self.eyes.Size
    self.weights = {} -- state -> blend weight
    self.pin = 1
    self.moving = 0
    self.gallop = 0
    self.phase = 0
    self.speed = 0
    self.lastPosition = self.root.Position
    self.look = 0
    self.actions = {}
    return self
end

-- A one-shot move (from the server's GuardianEvent).
function GuardianAnim:play(action, ...)
    self.actions[action] = { start = os.clock(), args = { ... } }
end

-- The move's time and arguments while it's playing, else nil.
function GuardianAnim:action(name, length)
    local action = self.actions[name]
    if not action then
        return nil
    end
    local t = os.clock() - action.start
    if t > length then
        self.actions[name] = nil
        return nil
    end
    return t, action.args
end

-- The yaw (degrees) that turns the head toward the target player, or 0.
function GuardianAnim:lookYaw()
    local id = self.model:GetAttribute("TargetId")
    local target = id and id ~= 0 and Players:GetPlayerByUserId(id)
    local root = target and target.Character and target.Character:FindFirstChild("HumanoidRootPart")
    if not root then
        return 0
    end
    local to = self.root.CFrame:PointToObjectSpace(root.Position)
    return math.clamp(math.deg(math.atan2(-to.X, -to.Z)), -40, 40)
end

function GuardianAnim:update(dt)
    local state = self.model:GetAttribute("State") or "Dormant"
    local now = os.clock()
    local follow = 1 - math.exp(-dt * 5)

    -- how fast it moves along the ground
    local position = self.root.Position
    local speed = ((position - self.lastPosition) * Vector3.new(1, 0, 1)).Magnitude / math.max(dt, 1e-3)
    self.lastPosition = position
    self.speed += (math.min(speed, 40) - self.speed) * (1 - math.exp(-dt * 8))
    local pounce = self.actions.Pounce
    local airborne = pounce ~= nil and now - pounce.start > (pounce.args[1] or 0)

    -- the state's pose, blended
    for name in POSES do
        local target = if name == state then 1 else 0
        self.weights[name] = (self.weights[name] or target) + (target - (self.weights[name] or target)) * follow
    end
    self.moving += ((if self.speed > 1.5 and not airborne then 1 else 0) - self.moving) * (1 - math.exp(-dt * 6))
    self.pin += ((if PINNED[state] and self.speed < 1 then 1 else 0) - self.pin) * follow
    self.gallop += (smooth((self.speed - GALLOP_FROM) / (GALLOP_FULL - GALLOP_FROM)) - self.gallop) * follow

    local pose = blank()
    for name, weight in self.weights do
        if weight > 0.001 then
            addPose(pose, POSES[name], weight)
        end
    end
    addPose(pose, PIN, self.pin * (1 - self.moving))

    -- the gait
    if self.moving > 0.01 then
        local stride = WALK_STRIDE + (GALLOP_STRIDE - WALK_STRIDE) * self.gallop
        self.phase = (self.phase + dt * self.speed / stride) % 1
        local amplitude = (24 + 16 * self.gallop) * self.moving
        local offsets = {
            FrontLeft = 0 + 0.1 * self.gallop, FrontRight = 0.5 - 0.4 * self.gallop,
            BackLeft = 0.5, BackRight = 0 + 0.6 * self.gallop,
        }
        for _, leg in LEGS do
            local a = 2 * math.pi * (self.phase + offsets[leg])
            local swing = math.sin(a)
            local lift = math.max(0, math.cos(a)) -- the leg coming forward is lifted
            local front = string.sub(leg, 1, 5) == "Front"
            add(pose, leg .. "Upper", amplitude * swing)
            add(pose, leg .. "Lower", (if front then -1 else 1) * (30 + 15 * self.gallop) * lift * self.moving)
        end
        local bound = 2 * math.pi * self.phase
        add(pose, "Body", 4 * self.gallop * math.sin(bound) * self.moving, 0, 0,
            (0.25 + 0.6 * self.gallop) * math.abs(math.sin(bound * 2)) * self.moving)
        add(pose, "Head", -3 * self.gallop * math.sin(bound) * self.moving)
        add(pose, "Tail", 10 * self.gallop * self.moving, 0, 8 * math.sin(bound * 2) * self.moving)
    end

    -- life: breathing, the tail, the head toward its target
    local breath = BREATH[state] or 0
    local rate = if state == "Weakened" then 1.6 else 0.55
    add(pose, "Body", 0.8 * breath * math.sin(now * rate * 2 * math.pi), 0, 0, 0.18 * breath * math.sin(now * rate * 2 * math.pi))
    add(pose, "Head", -0.8 * breath * math.sin(now * rate * 2 * math.pi + 0.6))
    if state ~= "Dormant" and state ~= "Resting" then
        local sway = if state == "Enraged" then 2.6 else 0.9
        add(pose, "Tail", 0, 12 * math.sin(now * sway), 6 * math.sin(now * sway * 0.7))
        self.look += (self:lookYaw() - self.look) * follow
    else
        self.look += (0 - self.look) * follow
    end
    add(pose, "Head", 0, self.look * 0.75)
    add(pose, "Body", 0, self.look * 0.15)

    self:applyActions(pose, now)

    for joint, p in pose do
        self.joints[joint].Transform = CFrame.new(0, p[4], p[5])
            * CFrame.Angles(math.rad(p[1]), math.rad(p[2]), math.rad(p[3]))
    end
    self:glow(state, now)
end

-- The one-shot moves, added onto the pose.
function GuardianAnim:applyActions(pose, now)
    -- waking: a tremble through the stone, then the head comes up in a roar
    local t = self:action("Awaken", 1.8)
    if t then
        local shake = envelope(t, 0.1, 0.6, 0.2)
        add(pose, "Body", 0, 1.5 * shake * math.sin(t * 70), 1.2 * shake * math.sin(t * 53))
        local roar = envelope(t - 0.45, 0.3, 1.3, 0.45)
        add(pose, "Head", 26 * roar)
        add(pose, "Jaw", -32 * roar)
        add(pose, "Body", 5 * roar)
    end

    -- rearing as it falters: the front rises, the hind legs stay planted, the front paws paw the air
    t = self:action("Rear", 1.9)
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
    local slam = self.actions.Slam
    if slam then
        local windUp = slam.args[1] or 0.75
        t = self:action("Slam", windUp + 0.6)
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
    local roar = self.actions.Roar
    if roar then
        local windUp = roar.args[1] or 1.1
        t = self:action("Roar", windUp + 1.1)
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
    local pounce = self.actions.Pounce
    if pounce then
        local windUp, air = pounce.args[1] or 0.6, pounce.args[2] or 0.95
        t = self:action("Pounce", windUp + air + 0.1)
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
    t = self:action("Land", 0.6)
    if t then
        local give = envelope(t, 0.05, 0.6, 0.45)
        add(pose, "Body", -5 * give, 0, 0, -2 * give)
        for _, leg in LEGS do
            local front = string.sub(leg, 1, 5) == "Front"
            add(pose, leg .. "Lower", (if front then 18 else -18) * give)
        end
    end
end

-- The eyes and orb: dark while it sleeps, flickering while weakened, burning red-orange and
-- widened while enraged (set locally; the server never changes them).
function GuardianAnim:glow(state, now)
    local eyes, orb = self.eyes, self.orb
    local color = EYES[state] or EYES.Guardian
    local open = 1
    if state == "Weakened" then
        local flicker = 0.5 + 0.5 * math.sin(now * 13) * math.sin(now * 5.3)
        color = Color3.fromRGB(0, 60, 150):Lerp(color, 0.35 + 0.65 * flicker)
    elseif state == "Enraged" then
        open = 1.7
    end
    local awaken = self:action("Awaken", 1.8)
    if awaken then
        color = EYES.Dormant:Lerp(EYES.Guardian, smooth((awaken - 0.3) / 0.4))
    end
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local material = if asleep then Enum.Material.SmoothPlastic else Enum.Material.Neon
    if eyes then
        if eyes.Material ~= material then
            eyes.Material = material
        end
        eyes.Color = if asleep then STONE else eyes.Color:Lerp(color, 0.25)
        -- (a size change keeps the part's centre; its weld to the head is untouched)
        local size = Vector3.new(self.eyeSize.X, self.eyeSize.Y * open, self.eyeSize.Z)
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

return GuardianAnim

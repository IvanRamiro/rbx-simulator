-- Animates a guardian on the client: its joints (the Motor6Ds GuardianBuilder made, set through
-- Transform every frame; the server never animates) and its glowing pieces, driven by its rig
-- (GuardianRigs/<GuardianId>).
--
-- Every Transform is in the guardian's own axes (X to its right, Y up, -Z ahead): a positive X turn
-- swings a limb's far end forward and up. Poses give per joint { pitch, yaw, roll (degrees),
-- lift (studs up), shift (studs back) }.
--
-- Layers, added together each frame:
--   the state's pose   (rig.Poses) blended over a fraction of a second when the state changes;
--   the hold           (rig.Hold) a pose kept while it keeps its egg and stands still (the lion's
--                      paw on the egg);
--   the gait           (rig.gait) while it moves, from its speed (self.speed, self.moving,
--                      self.gallop, self.phase);
--   life               (rig.life) breathing and sway; the head turned toward its target (rig.Look);
--   actions            (rig.actions) one-shot moves from the server's events.
-- Then rig.glow lights its glowing pieces for the state.
--
-- The helpers rigs use: GuardianAnim.add(pose, joint, pitch, yaw, roll, lift, shift),
-- GuardianAnim.envelope(t, rise, total, fall), GuardianAnim.smooth(x), and anim:action(name, length).
local GuardianAnim = {}
GuardianAnim.__index = GuardianAnim

local Players = game:GetService("Players")

local function smooth(x)
    x = math.clamp(x, 0, 1)
    return x * x * (3 - 2 * x)
end
GuardianAnim.smooth = smooth

-- 0 -> 1 over `rise`, held, then 1 -> 0 over the last `fall` of `total`
function GuardianAnim.envelope(t, rise, total, fall)
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
GuardianAnim.add = add

local function addPose(pose, source, weight)
    for joint, values in source do
        add(pose, joint, (values[1] or 0) * weight, (values[2] or 0) * weight, (values[3] or 0) * weight,
            (values[4] or 0) * weight, (values[5] or 0) * weight)
    end
end

function GuardianAnim.new(model, rig)
    local self = setmetatable({}, GuardianAnim)
    self.model = model
    self.rig = rig
    self.root = model.PrimaryPart
    self.joints = {}
    for _, joint in rig.Joints do
        self.joints[joint] = model:WaitForChild("Joints"):WaitForChild(joint)
    end
    self.weights = {} -- state -> blend weight
    self.hold = 1
    self.moving = 0
    self.gallop = 0
    self.phase = 0
    self.speed = 0
    self.lastPosition = self.root.Position
    self.look = 0
    self.actions = {}
    if rig.setup then
        rig.setup(self)
    end
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
function GuardianAnim:lookYaw(limit)
    local id = self.model:GetAttribute("TargetId")
    local target = id and id ~= 0 and Players:GetPlayerByUserId(id)
    local root = target and target.Character and target.Character:FindFirstChild("HumanoidRootPart")
    if not root then
        return 0
    end
    local to = self.root.CFrame:PointToObjectSpace(root.Position)
    return math.clamp(math.deg(math.atan2(-to.X, -to.Z)), -limit, limit)
end

function GuardianAnim:update(dt)
    local rig = self.rig
    local state = self.model:GetAttribute("State") or "Dormant"
    local now = os.clock()
    local follow = 1 - math.exp(-dt * 5)

    -- how fast it moves along the ground, and whether it is in the air (a leap)
    local position = self.root.Position
    local speed = ((position - self.lastPosition) * Vector3.new(1, 0, 1)).Magnitude / math.max(dt, 1e-3)
    self.lastPosition = position
    self.speed += (math.min(speed, 40) - self.speed) * (1 - math.exp(-dt * 8))
    local leap = self.actions[rig.LeapAction]
    local airborne = leap ~= nil and now - leap.start > (leap.args[1] or 0)

    for name in rig.Poses do
        local target = if name == state then 1 else 0
        self.weights[name] = (self.weights[name] or target) + (target - (self.weights[name] or target)) * follow
    end
    self.moving += ((if self.speed > 1.5 and not airborne then 1 else 0) - self.moving) * (1 - math.exp(-dt * 6))
    self.hold += ((if rig.HoldStates and rig.HoldStates[state] and self.speed < 1 then 1 else 0) - self.hold) * follow
    local gallop = rig.Gallop
    self.gallop += ((if gallop then smooth((self.speed - gallop[1]) / (gallop[2] - gallop[1])) else 0) - self.gallop) * follow

    local pose = {}
    for _, joint in rig.Joints do
        pose[joint] = { 0, 0, 0, 0, 0 }
    end
    for name, weight in self.weights do
        if weight > 0.001 then
            addPose(pose, rig.Poses[name], weight)
        end
    end
    if rig.Hold then
        addPose(pose, rig.Hold, self.hold * (1 - self.moving))
    end
    if self.moving > 0.01 then
        rig.gait(self, pose, dt)
    end
    rig.life(self, pose, state, now)

    -- the head toward its target while it is awake
    local look = rig.Look
    local awake = state ~= "Dormant" and state ~= "Resting"
    self.look += ((if awake then self:lookYaw(look.Limit) else 0) - self.look) * follow
    add(pose, look.Joint, 0, self.look * look.Share)
    if look.Body then
        add(pose, look.Body, 0, self.look * look.BodyShare)
    end

    rig.actions(self, pose, now)

    for joint, p in pose do
        self.joints[joint].Transform = CFrame.new(0, p[4], p[5])
            * CFrame.Angles(math.rad(p[1]), math.rad(p[2]), math.rad(p[3]))
    end
    rig.glow(self, state, now)
end

return GuardianAnim

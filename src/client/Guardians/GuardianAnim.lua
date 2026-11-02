-- Animates a guardian on the client (the server never animates): its joints, the Motor6Ds
-- GuardianBuilder made, set through Transform every frame, and its glowing pieces, driven by its
-- rig (GuardianRigs/<GuardianId>).
--
-- Transforms are in the guardian's own axes (X to its right, Y up, -Z ahead): a positive X turn
-- swings a limb's far end forward and up. Poses give per joint { pitch, yaw, roll (degrees),
-- lift (studs up), shift (studs back) }.
--
-- Layers, added together each frame:
--   pose     (rig.Poses) per state, blended over a fraction of a second on a state change;
--   gait     (rig.gait) while it moves or turns on the spot (self.stepSpeed drives self.phase;
--            self.speed, self.moving, self.gallop);
--   lean     (rig.Lean) the body tipping into speeding up and slowing down, and banking into turns;
--   life     (rig.life) breathing and sway, the head turned toward its target (rig.Look);
--   actions  (rig.actions) one-shot moves from the server's events.
-- Then every joint follows that pose through a spring (rig.Springs), so nothing moves as one rigid
-- piece: a joint eases into a move, overshoots a little and settles, and a loose one (a tail, the
-- serpent, the mantle) lags behind whatever it hangs from (its Drag: 1 keeps its angle in the world
-- while its parent turns, then lets it swing after), whipping round as the guardian turns or rears.
-- A tremor (anim:tremor, from actions: a shudder, a quivering roar) is added after the springs,
-- which would smooth it away. Then the planted feet (rig.Legs) are put back on the ground: each
-- leg's two joints are solved so its sole stays where it stood, so the body can crouch, rear, bob
-- and sway over its feet instead of carrying them along. A leg lifts out of it as the gait swings
-- it (anim:lift), in the air, or for a raised paw. Then rig.glow lights its glowing pieces.
--
-- Helpers for rigs: GuardianAnim.add(pose, joint, pitch, yaw, roll, lift, shift),
-- GuardianAnim.envelope(t, rise, total, fall), GuardianAnim.smooth(x), GuardianAnim.keyed(pose, t,
-- keys, scale), anim:action(name, length), anim:tremor(joint, pitch, yaw, roll), anim:lift(leg, amount).
local GuardianAnim = {}
GuardianAnim.__index = GuardianAnim

local Players = game:GetService("Players")

-- A joint not in rig.Springs: quick and a little springy (limbs), no drag.
local DEFAULT_SPRING = { Freq = 9, Damping = 0.75, Drag = 0 }
local SUBSTEP = 1 / 240      -- the springs' integration step (stable for any frequency used here)
local MAX_SWING = 60         -- degrees a dragged joint may lag its target
local SNAP_GAP = 0.25        -- seconds without an update (off-screen, a hitch) after which springs snap
local TURN_STEP = 0.1        -- studs of stepping per degree turned: turning on the spot steps its feet

local function smooth(x)
    x = math.clamp(x, 0, 1)
    return x * x * (3 - 2 * x)
end
GuardianAnim.smooth = smooth

local EASE = {
    linear = function(x)
        return x
    end,
    ["in"] = function(x) -- slow, then fast: a gather picking up speed
        return x * x * x
    end,
    out = function(x) -- fast, then slow: a strike that snaps out and settles
        return 1 - (1 - x) ^ 3
    end,
    inout = smooth,
}

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

local function transformOf(p)
    return CFrame.new(0, p[4], p[5]) * CFrame.Angles(math.rad(p[1]), math.rad(p[2]), math.rad(p[3]))
end

local function addPose(pose, source, weight)
    for joint, values in source do
        add(pose, joint, (values[1] or 0) * weight, (values[2] or 0) * weight, (values[3] or 0) * weight,
            (values[4] or 0) * weight, (values[5] or 0) * weight)
    end
end

-- A move told as key poses, the way an animator blocks it: `keys` = { { time, pose, ease }, ... } in
-- time order, the first at 0 (usually an empty pose), each pose { [joint] = { pitch, yaw, roll, lift,
-- shift } }. Between two keys the pose blends from the earlier key's to the later's along the later
-- key's ease ("in", "out", "inout", "linear"; inout if none); outside the keys nothing is added.
-- `scale` (default 1) multiplies the whole move.
function GuardianAnim.keyed(pose, t, keys, scale)
    if t < 0 or t >= keys[#keys][1] then
        return
    end
    scale = scale or 1
    for i = 2, #keys do
        local b = keys[i]
        if t < b[1] then
            local a = keys[i - 1]
            local e = EASE[b[3] or "inout"]((t - a[1]) / (b[1] - a[1]))
            addPose(pose, a[2], (1 - e) * scale)
            addPose(pose, b[2], e * scale)
            return
        end
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
    -- each joint's parent joint (nil: hangs from the root), from its motor
    local jointOf = {}
    for joint, motor in self.joints do
        jointOf[motor.Part1] = joint
    end
    self.parents = {}
    for joint, motor in self.joints do
        self.parents[joint] = jointOf[motor.Part0]
    end
    -- the springs walk rig.Joints in order, each joint after its parent
    local seen = {}
    for _, joint in rig.Joints do
        local parent = self.parents[joint]
        if parent and not seen[parent] then
            warn("GuardianAnim: " .. model.Name .. "'s " .. joint .. " is listed before its parent " .. parent)
            self.parents[joint] = nil
        end
        seen[joint] = true
    end
    self.springs = {} -- [joint] = { x = { 5 values }, v = { 5 values }, config }
    for _, joint in rig.Joints do
        self.springs[joint] = { config = rig.Springs and rig.Springs[joint] or DEFAULT_SPRING }
    end
    self.heading = 0       -- the root's yaw (degrees), unwrapped
    self.lastYaw = nil
    self.turnRate = 0      -- degrees per second, smoothed
    self.accel = 0         -- studs per second squared along its heading, smoothed
    self.lastUpdate = nil
    self.tremors = {}
    self.weights = {} -- state -> blend weight
    self.moving = 0
    self.gallop = 0
    self.phase = 0
    self.speed = 0
    self.stepSpeed = 0
    self.lastPosition = self.root.Position
    self.look = 0
    self.actions = {}
    self:setupLegs()
    if rig.setup then
        rig.setup(self)
    end
    return self
end

-- Each planted leg (rig.Legs: { Name, Upper, Lower, Axis = the turn it bends on (1 pitch, 3 roll),
-- Bend = the sign of the Lower turn that folds it }): its sole at rest, as a point on its lower piece,
-- and where it stands on the ground in the root's frame. The ground is the model's pivot.
function GuardianAnim:setupLegs()
    self.c0, self.c1inv = {}, {}
    for joint, motor in self.joints do
        self.c0[joint] = motor.C0
        self.c1inv[joint] = motor.C1:Inverse()
    end
    self.plant = {}
    self.air = 0
    self.legs = {}
    if not self.rig.Legs then
        return
    end
    self.groundY = self.root.CFrame:PointToObjectSpace(self.model:GetPivot().Position).Y
    local rest = {}
    local function restOf(joint)
        if not rest[joint] then
            local parent = self.parents[joint]
            rest[joint] = (if parent then restOf(parent) else CFrame.identity) * self.c0[joint] * self.c1inv[joint]
        end
        return rest[joint]
    end
    for _, def in self.rig.Legs do
        local lower = restOf(def.Lower)
        local stand = Vector3.new(lower.X, self.groundY, lower.Z)
        table.insert(self.legs, { def = def, sole = lower:PointToObjectSpace(stand), stand = stand })
    end
end

-- Lifts a leg off the ground this frame (0 planted .. 1 free), for a step's swing or a raised paw.
function GuardianAnim:lift(leg, amount)
    self.plant[leg] = math.min(self.plant[leg] or 1, 1 - math.clamp(amount, 0, 1))
end

-- Puts the planted feet back on the ground (see the header).
function GuardianAnim:plantFeet(pose)
    local frames = {}
    local function frameOf(joint) -- the joint's piece in the root's frame, as posed
        local f = frames[joint]
        if not f then
            local parent = self.parents[joint]
            f = (if parent then frameOf(parent) else CFrame.identity) * self.c0[joint] * transformOf(pose[joint]) * self.c1inv[joint]
            frames[joint] = f
        end
        return f
    end
    local grounded = 1 - self.air
    for _, leg in self.legs do
        local def = leg.def
        local planted = (self.plant[def.Name] or 1) * grounded
        local axis, bend = def.Axis or 1, def.Bend or 1
        local upper, lower = pose[def.Upper], pose[def.Lower]
        local hip = frameOf(self.parents[def.Upper]) * self.c0[def.Upper]
        local c1u, c0l, c1l = self.c1inv[def.Upper], self.c0[def.Lower], self.c1inv[def.Lower]
        local tu, tl = table.clone(upper), table.clone(lower)
        local function sole(a, b)
            tu[axis], tl[axis] = a, b
            return (hip * transformOf(tu) * c1u * c0l * transformOf(tl) * c1l):PointToWorldSpace(leg.sole)
        end
        local a0, b0 = upper[axis], lower[axis]
        local posed = sole(a0, b0)
        -- a lifted foot is never posed through the ground either: it's put back on top of it
        local weight = math.max(planted, if posed.Y < self.groundY - 0.05 then grounded else 0)
        if weight > 0.01 then
            -- where it stands: under its posed foot while it walks, on its own spot when still
            local target = Vector3.new(posed.X, self.groundY, posed.Z):Lerp(leg.stand, (1 - self.moving) * (def.Pin or 1) * planted)
            local floor = math.min(0, bend * b0) -- the knee never bends further backward than posed
            local a, b = a0, b0 + bend * 3       -- a slight bend, so a straight leg knows which way it folds
            -- solved in the leg's own swing plane: height and forward for a leg that bends on pitch,
            -- height and sideways for one that bends on roll (it can't reach out of that plane)
            local mask = if axis == 3 then Vector3.new(1, 1, 0) else Vector3.new(0, 1, 1)
            for _ = 1, 5 do
                local s = sole(a, b)
                local r = (target - s) * mask
                if r.Magnitude < 0.02 then
                    break
                end
                local ja = (sole(a + 0.5, b) - s) * mask / 0.5
                local jb = (sole(a, b + 0.5) - s) * mask / 0.5
                local aa, ab, bb = ja:Dot(ja) + 1e-3, ja:Dot(jb), jb:Dot(jb) + 1e-3
                local ra, rb = ja:Dot(r), jb:Dot(r)
                local det = aa * bb - ab * ab
                a += math.clamp((bb * ra - ab * rb) / det, -20, 20)
                b += math.clamp((aa * rb - ab * ra) / det, -20, 20)
                b = bend * math.max(bend * b, floor)
            end
            upper[axis] = a0 + (a - a0) * weight
            lower[axis] = b0 + (b - b0) * weight
        end
    end
    table.clear(self.plant)
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

-- A fast shake on a joint this frame, past its spring (call from rig.actions).
function GuardianAnim:tremor(joint, pitch, yaw, roll)
    local t = self.tremors[joint]
    if not t then
        t = { 0, 0, 0 }
        self.tremors[joint] = t
    end
    t[1] += pitch or 0
    t[2] += yaw or 0
    t[3] += roll or 0
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

    local snap = self.lastUpdate == nil or now - self.lastUpdate > SNAP_GAP
    self.lastUpdate = now

    local position = self.root.Position
    local speed = ((position - self.lastPosition) * Vector3.new(1, 0, 1)).Magnitude / math.max(dt, 1e-3)
    self.lastPosition = position
    if snap then
        speed = self.speed
    end
    local lastSpeed = self.speed
    self.speed += (math.min(speed, 40) - self.speed) * (1 - math.exp(-dt * 8))
    self:trackHeading(dt, lastSpeed, snap)
    local leap = self.actions[rig.LeapAction]
    local airborne = leap ~= nil and now - leap.start > (leap.args[1] or 0)
    self.air += ((if airborne then 1 else 0) - self.air) * (1 - math.exp(-dt * 14))

    for name in rig.Poses do
        local target = if name == state then 1 else 0
        self.weights[name] = (self.weights[name] or target) + (target - (self.weights[name] or target)) * follow
    end
    -- its feet step as it moves, and as it turns on the spot (stepSpeed drives the gait's phase)
    self.stepSpeed = math.max(self.speed, math.abs(self.turnRate) * TURN_STEP)
    self.moving += ((if self.stepSpeed > 1.5 and not airborne then 1 else 0) - self.moving) * (1 - math.exp(-dt * 6))
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
    if self.moving > 0.01 then
        rig.gait(self, pose, dt)
    end
    local lean = rig.Lean
    if lean then
        -- nose down speeding up, back on its haunches slowing down; banked into a turn at speed
        local pitch = math.clamp(-self.accel * lean.Accel, -lean.Max, lean.Max)
        local bank = math.clamp(self.turnRate * lean.Bank * math.min(self.speed / 20, 1), -lean.Max, lean.Max)
        add(pose, lean.Joint, pitch, 0, bank)
    end
    rig.life(self, pose, state, now)

    local look = rig.Look
    local awake = state ~= "Dormant" and state ~= "Resting"
    self.look += ((if awake then self:lookYaw(look.Limit) else 0) - self.look) * follow
    add(pose, look.Joint, 0, self.look * look.Share)
    if look.Body then
        add(pose, look.Body, 0, self.look * look.BodyShare)
    end

    rig.actions(self, pose, now)

    self:follow(pose, dt, snap)
    for joint, t in self.tremors do
        add(pose, joint, t[1], t[2], t[3])
    end
    table.clear(self.tremors)
    self:plantFeet(pose)
    for joint, p in pose do
        self.joints[joint].Transform = transformOf(p)
    end
    rig.glow(self, state, now)
end

-- The root's heading, its turn rate and its acceleration along it.
function GuardianAnim:trackHeading(dt, lastSpeed, snap)
    local look = self.root.CFrame.LookVector
    local yaw = math.deg(math.atan2(-look.X, -look.Z))
    if self.lastYaw and not snap then
        local delta = (yaw - self.lastYaw + 180) % 360 - 180
        self.heading += delta
        local rate = math.clamp(delta / math.max(dt, 1e-3), -400, 400)
        self.turnRate += (rate - self.turnRate) * (1 - math.exp(-dt * 6))
        local accel = (self.speed - lastSpeed) / math.max(dt, 1e-3)
        self.accel += (accel - self.accel) * (1 - math.exp(-dt * 5))
    else
        self.turnRate, self.accel = 0, 0
    end
    self.lastYaw = yaw
end

-- Every joint follows its pose through its spring. A dragged joint's angles are sprung in the world
-- (its parents' sprung angles and the root's heading added), so it keeps its angle while they turn.
function GuardianAnim:follow(pose, dt, snap)
    local world = {} -- [joint] = { pitch, yaw, roll } of the joint as sprung, summed down from the root
    local steps = math.clamp(math.ceil(dt / SUBSTEP), 1, 16)
    local h = dt / steps
    for _, joint in self.rig.Joints do
        local p = pose[joint]
        local spring = self.springs[joint]
        local config = spring.config
        local parent = self.parents[joint]
        local base = if parent then world[parent] else { 0, self.heading, 0 }
        local drag = config.Drag or 0
        local target = {
            p[1] + drag * base[1], p[2] + drag * base[2], p[3] + drag * base[3], p[4], p[5],
        }
        if snap or not spring.x then
            spring.x = table.clone(target)
            spring.v = { 0, 0, 0, 0, 0 }
        else
            local omega = 2 * math.pi * config.Freq
            local k, c = omega * omega, 2 * config.Damping * omega
            local x, v = spring.x, spring.v
            for i = 1, 5 do
                if i <= 3 and drag > 0 then
                    -- a dragged joint never trails its target by more than MAX_SWING
                    x[i] = target[i] + math.clamp(x[i] - target[i], -MAX_SWING, MAX_SWING)
                end
                local xi, vi, ti = x[i], v[i], target[i]
                for _ = 1, steps do
                    vi += (k * (ti - xi) - c * vi) * h
                    xi += vi * h
                end
                x[i], v[i] = xi, vi
            end
        end
        local x = spring.x
        p[1], p[2], p[3] = x[1] - drag * base[1], x[2] - drag * base[2], x[3] - drag * base[3]
        p[4], p[5] = x[4], x[5]
        world[joint] = { base[1] + p[1], base[2] + p[2], base[3] + p[3] }
    end
end

return GuardianAnim

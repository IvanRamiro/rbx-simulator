-- Blends whole-body poses into every R15 character's joints, before physics each frame: the
-- Qinggong poses (QinggongFx.pose: steps, tucks, the crane glide), the combat poses (CombatFx.pose)
-- and the lotus seat while cultivating. Each pose is a table of joint name -> target Transform;
-- poses fade in and out by weight, and the default animations stay underneath.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local QinggongFx = require(script.Parent.Parent:WaitForChild("Qinggong"):WaitForChild("QinggongFx"))
local CombatFx = require(script.Parent.Parent:WaitForChild("Combat"):WaitForChild("CombatFx"))

local BLEND_SPEED = 6
local FLYING_MOVE_SPEED = 4

local function deg(x, y, z)
    return CFrame.Angles(math.rad(x or 0), math.rad(y or 0), math.rad(z or 0))
end

local function pointLimb(direction)
    local down = Vector3.new(0, -1, 0)
    direction = direction.Unit
    local axis = down:Cross(direction)
    if axis.Magnitude < 1e-4 then
        return CFrame.identity
    end
    return CFrame.fromAxisAngle(axis.Unit, math.acos(math.clamp(down:Dot(direction), -1, 1)))
end

local function mirror(cframe)
    local x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 = cframe:GetComponents()
    return CFrame.new(-x, y, z, r00, -r01, -r02, -r10, r11, r12, -r20, r21, r22)
end

local function symmetric(pose)
    for name, cframe in table.clone(pose) do
        local left = string.gsub(name, "^Right", "Left")
        if left ~= name and pose[left] == nil then
            pose[left] = mirror(cframe)
        end
    end
    return pose
end

local LOTUS_HIP = deg(0, -50, 0) * deg(85, 0, 0)
local LOTUS = symmetric({
    RightHip = LOTUS_HIP,
    RightKnee = pointLimb(LOTUS_HIP:VectorToObjectSpace(Vector3.new(-0.95, -0.12, 0.25))),
    RightAnkle = deg(-20, 0, 0),
    RightShoulder = pointLimb(Vector3.new(0.16, -0.85, -0.5)),
    RightElbow = deg(25, 0, 0),
    RightWrist = deg(-15, 0, 0),
    Waist = deg(4, 0, 0),
    Neck = deg(-6, 0, 0),
})

-- Riding the flying sword: right foot forward, left back, both drawn in to stay on the blade;
-- the right hand before the chest in a sword gesture, the left behind the back. Moving, the
-- stance sinks lower and the left arm trails.
local RIDE_LEGS = {
    RightHip = pointLimb(Vector3.new(-0.07, -0.96, -0.26)),
    RightKnee = deg(-16, 0, 0),
    RightAnkle = deg(10, 0, 0),
    LeftHip = pointLimb(Vector3.new(0.07, -0.97, 0.22)),
    LeftKnee = deg(-10, 0, 0),
    LeftAnkle = deg(-4, 0, 0),
}
local HOVERING = table.clone(RIDE_LEGS)
HOVERING.RightShoulder = pointLimb(Vector3.new(-0.35, -0.5, -0.79))
HOVERING.RightElbow = deg(85, 0, 0)
HOVERING.RightWrist = deg(-10, 0, 0)
HOVERING.LeftShoulder = pointLimb(Vector3.new(0.2, -0.82, 0.54))
HOVERING.LeftElbow = deg(70, 0, 0)

local FLYING = table.clone(HOVERING)
FLYING.RightHip = pointLimb(Vector3.new(-0.07, -0.93, -0.36))
FLYING.RightKnee = deg(-28, 0, 0)
FLYING.LeftHip = pointLimb(Vector3.new(0.07, -0.95, 0.3))
FLYING.LeftKnee = deg(-20, 0, 0)
FLYING.LeftShoulder = pointLimb(Vector3.new(-0.15, -0.72, 0.68))
FLYING.LeftElbow = deg(15, 0, 0)
FLYING.Waist = deg(-6, 0, 0)

-- Strikes (CombatFx) pose only the arms and waist, so they combine with whatever the legs are
-- doing. Palm: the right palm thrust ahead, the left fist drawn back to the hip, the waist
-- turned into it. Sword: the right hand raised forward in a sword gesture, the left drawn back.
-- Spear: both hands driven forward low along the shaft, the waist turned hard into the thrust.
local STRIKES = {
    Palm = {
        RightShoulder = pointLimb(Vector3.new(-0.05, -0.12, -0.99)),
        RightElbow = deg(0, 0, 0),
        RightWrist = deg(-55, 0, 0),
        LeftShoulder = pointLimb(Vector3.new(0.12, -0.75, 0.65)),
        LeftElbow = deg(95, 0, 0),
        Waist = deg(0, -25, 0),
    },
    Sword = {
        RightShoulder = pointLimb(Vector3.new(0.05, 0.35, -0.94)),
        RightElbow = deg(10, 0, 0),
        RightWrist = deg(-20, 0, 0),
        LeftShoulder = pointLimb(Vector3.new(0.25, -0.8, 0.55)),
        LeftElbow = deg(60, 0, 0),
        Waist = deg(0, 15, 0),
    },
    Spear = {
        RightShoulder = pointLimb(Vector3.new(0.1, -0.25, -0.96)),
        RightElbow = deg(5, 0, 0),
        RightWrist = deg(-15, 0, 0),
        LeftShoulder = pointLimb(Vector3.new(0.35, -0.4, -0.85)),
        LeftElbow = deg(35, 0, 0),
        Waist = deg(0, -35, 0),
    },
}

-- The same pose for the other side of the body: every Right joint becomes the mirrored Left one
-- and every Left joint the mirrored Right one.
local function flipSides(pose)
    local flipped = {}
    for name, cframe in pose do
        local other = if string.match(name, "^Right") then string.gsub(name, "^Right", "Left")
            elseif string.match(name, "^Left") then string.gsub(name, "^Left", "Right")
            else name
        flipped[other] = mirror(cframe)
    end
    return flipped
end

-- Qinggong leaps alternate legs. Each starts with a stride (driving knee up and forward, the
-- other leg pushing off, arms opposite to the legs), then both knees tuck, the driving one higher.
local QINGGONG_STEP_RIGHT = {
    RightHip = pointLimb(Vector3.new(0.1, -0.22, -0.97)),
    RightKnee = deg(-118, 0, 0),
    RightAnkle = deg(-15, 0, 0),
    LeftHip = pointLimb(Vector3.new(-0.06, -0.92, 0.38)),
    LeftKnee = deg(-18, 0, 0),
    LeftAnkle = deg(-40, 0, 0),
    RightShoulder = pointLimb(Vector3.new(0.3, -0.72, 0.62)),
    RightElbow = deg(35, 0, 0),
    LeftShoulder = pointLimb(Vector3.new(-0.18, -0.4, -0.9)),
    LeftElbow = deg(30, 0, 0),
}
local QINGGONG_TUCK_RIGHT = {
    RightHip = pointLimb(Vector3.new(0.12, -0.35, -0.93)),
    RightKnee = deg(-120, 0, 0),
    LeftHip = pointLimb(Vector3.new(-0.1, -0.7, -0.45)),
    LeftKnee = deg(-95, 0, 0),
    RightShoulder = pointLimb(Vector3.new(0.6, -0.45, 0.65)),
    RightElbow = deg(20, 0, 0),
    LeftShoulder = pointLimb(Vector3.new(-0.6, -0.45, 0.65)),
    LeftElbow = deg(20, 0, 0),
}
-- The glide is a crane stance: one leg trailing straight, the other knee raised, arms spread
-- back like wings.
local QINGGONG_GLIDE = symmetric({
    RightHip = pointLimb(Vector3.new(0.05, -0.72, 0.69)),
    RightKnee = deg(-15, 0, 0),
    RightAnkle = deg(-35, 0, 0),
    LeftHip = pointLimb(Vector3.new(-0.08, -0.35, -0.93)),
    LeftKnee = deg(-95, 0, 0),
    RightShoulder = pointLimb(Vector3.new(0.92, -0.15, 0.36)),
    RightElbow = deg(10, 0, 0),
    RightWrist = deg(-15, 0, 0),
})
local QINGGONG_POSES = {
    Glide = QINGGONG_GLIDE,
    StepRight = QINGGONG_STEP_RIGHT,
    StepLeft = flipSides(QINGGONG_STEP_RIGHT),
    TuckRight = QINGGONG_TUCK_RIGHT,
    TuckLeft = flipSides(QINGGONG_TUCK_RIGHT),
}
local QINGGONG_BLEND_SPEED = 16 -- the leap poses snap in: a stride lasts only a fifth of a second

local useLotus = GameConfig.MeditationAnimationId == 0

local rigs = {}

local function findJoints(character)
    local joints = {}
    for _, joint in character:GetDescendants() do
        if (joint:IsA("Motor6D") or joint:IsA("AnimationConstraint")) and joint.Name ~= "Root" then
            joints[joint.Name] = joint
        end
    end
    return joints
end

-- a strike's arms laid over a riding pose, built once per pair
local combined = {}
local function withStrike(base, strike)
    local key = tostring(base) .. tostring(strike)
    if not combined[key] then
        local pose = table.clone(base)
        for name, cframe in strike do
            pose[name] = cframe
        end
        combined[key] = pose
    end
    return combined[key]
end

local function choosePose(player, character)
    if player:GetAttribute("IsCultivating") == true then
        return if useLotus then LOTUS else nil
    end
    local strike = STRIKES[CombatFx.pose(player)]
    if player:GetAttribute("IsFlying") == true then
        local rootPart = character:FindFirstChild("HumanoidRootPart")
        local speed = if rootPart then rootPart.AssemblyLinearVelocity.Magnitude else 0
        local ride = if speed > FLYING_MOVE_SPEED then FLYING else HOVERING
        return if strike then withStrike(ride, strike) else ride
    end
    if strike then
        return strike
    end
    local qinggong = QinggongFx.pose(player)
    return qinggong and QINGGONG_POSES[qinggong]
end

local QUICK_POSES = {}
for name, pose in QINGGONG_POSES do
    if name ~= "Glide" then
        QUICK_POSES[pose] = true
    end
end
for _, pose in STRIKES do
    QUICK_POSES[pose] = true
end

local function updatePoses(deltaTime)
    local normalStep = 1 - math.exp(-BLEND_SPEED * deltaTime)
    local quickStep = 1 - math.exp(-QINGGONG_BLEND_SPEED * deltaTime)
    -- characters that left the world (an old character isn't always destroyed on respawn)
    for character in rigs do
        if not character.Parent then
            rigs[character] = nil
        end
    end
    for _, player in Players:GetPlayers() do
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if not humanoid or humanoid.RigType ~= Enum.HumanoidRigType.R15 then
            continue
        end

        local rig = rigs[character]
        if not rig then
            rig = { joints = findJoints(character), weights = {}, written = {} }
            rigs[character] = rig
        end

        local wanted = if humanoid.Health > 0 then choosePose(player, character) else nil
        if wanted and rig.weights[wanted] == nil then
            rig.weights[wanted] = 0
        end
        for pose, weight in rig.weights do
            local step = if QUICK_POSES[pose] or (wanted and QUICK_POSES[wanted]) then quickStep else normalStep
            weight += ((if pose == wanted then 1 else 0) - weight) * step
            rig.weights[pose] = if pose ~= wanted and weight < 0.01 then nil else weight
        end

        local names = {}
        for pose in rig.weights do
            for name in pose do
                names[name] = true
            end
        end
        for name in rig.written do
            names[name] = true
        end

        for name in names do
            local joint = rig.joints[name]
            if not (joint and joint.Parent) then
                continue
            end
            local last = rig.written[name]
            local base = joint.Transform
            if last and base == last.cframe then
                base = last.base
            end
            local cframe = base
            for pose, weight in rig.weights do
                local target = pose[name]
                if target then
                    cframe = cframe:Lerp(target, weight)
                end
            end
            joint.Transform = cframe
            rig.written[name] = if cframe == base then nil else { cframe = cframe, base = base }
        end
    end
end

RunService.PreSimulation:Connect(updatePoses)


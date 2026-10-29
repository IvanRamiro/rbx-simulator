-- Poses every R15 character on this client: a lotus pose (legs crossed,
-- hands on knees) while cultivating, and a flying pose while flying (stretched
-- out like a diving hero when moving, legs dangling when hovering).
--
-- Purely visual. The server's replicated "IsCultivating" and "IsFlying"
-- attributes decide the pose, and each client poses everyone, so all players
-- see it. Each frame, after Roblox's animations have run, the pose is blended
-- over the joints' Transform (Motor6D or AnimationConstraint), so walking
-- animations take over again smoothly afterwards. R6 characters keep their
-- normal animations. With a MeditationAnimationId set in GameConfig, that
-- animation is used for meditating instead of the lotus pose.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local BLEND_SPEED = 6 -- Higher = poses take over faster
local FLYING_MOVE_SPEED = 4 -- Studs per second above which a flyer is stretched out

local function deg(x, y, z)
    return CFrame.Angles(math.rad(x or 0), math.rad(y or 0), math.rad(z or 0))
end

-- The rotation that turns a limb hanging straight down (-Y) to point along
-- `direction`, given in the frame of the part it hangs from
local function pointLimb(direction)
    local down = Vector3.new(0, -1, 0)
    direction = direction.Unit
    local axis = down:Cross(direction)
    if axis.Magnitude < 1e-4 then
        return CFrame.identity
    end
    return CFrame.fromAxisAngle(axis.Unit, math.acos(math.clamp(down:Dot(direction), -1, 1)))
end

-- The same pose for the other side of the body (mirrored left to right)
local function mirror(cframe)
    local x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 = cframe:GetComponents()
    return CFrame.new(-x, y, z, r00, -r01, -r02, -r10, r11, r12, -r20, r21, r22)
end

-- Builds a pose from right-side joints, adding the mirrored left side
local function symmetric(pose)
    for name, cframe in table.clone(pose) do
        local left = string.gsub(name, "^Right", "Left")
        if left ~= name and pose[left] == nil then
            pose[left] = mirror(cframe)
        end
    end
    return pose
end

-- Lotus: thighs forward and out, shins folded across, hands resting on the
-- knees. Directions are in the torso's frame (+X right, +Y up, -Z forward).
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

-- Flying fast: the body is tilted forward by FlightController, so arms
-- reach ahead and the legs stream out behind
local FLYING = symmetric({
    RightShoulder = deg(165, 0, -8),
    RightElbow = deg(10, 0, 0),
    LeftShoulder = deg(-20, 0, 10),
    LeftElbow = deg(15, 0, 0),
    RightHip = deg(-6, 0, 3),
    RightKnee = deg(-12, 0, 0),
    LeftHip = deg(4, 0, -3),
    LeftKnee = deg(-35, 0, 0),
    RightAnkle = deg(-30, 0, 0),
    Neck = deg(25, 0, 0),
})

-- Hovering in the air: legs dangling, arms out a little for balance
local HOVERING = symmetric({
    RightShoulder = deg(10, 0, 20),
    RightElbow = deg(20, 0, 0),
    RightHip = deg(12, 0, 4),
    RightKnee = deg(-25, 0, 0),
    LeftHip = deg(-4, 0, -4),
    LeftKnee = deg(-12, 0, 0),
    RightAnkle = deg(-25, 0, 0),
})

local useLotus = GameConfig.MeditationAnimationId == 0

-- rigs[character] = {
--     joints = { [name] = joint }, weights = { [pose] = 0..1 },
--     written = { [name] = { cframe = what this script set, base = what it blended over } },
-- }
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

local function choosePose(player, character)
    if player:GetAttribute("IsCultivating") == true then
        return if useLotus then LOTUS else nil
    end
    if player:GetAttribute("IsFlying") == true then
        local rootPart = character:FindFirstChild("HumanoidRootPart")
        local speed = if rootPart then rootPart.AssemblyLinearVelocity.Magnitude else 0
        return if speed > FLYING_MOVE_SPEED then FLYING else HOVERING
    end
    return nil
end

local function updatePoses(deltaTime)
    local step = 1 - math.exp(-BLEND_SPEED * deltaTime)
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
            character.Destroying:Connect(function()
                rigs[character] = nil
            end)
        end

        -- Fade the wanted pose in and every other pose out
        local wanted = if humanoid.Health > 0 then choosePose(player, character) else nil
        if wanted and rig.weights[wanted] == nil then
            rig.weights[wanted] = 0
        end
        for pose, weight in rig.weights do
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
            -- Blend over what the animations set this frame. No animation runs
            -- while flying (PlatformStand), so then the joint still holds what
            -- this script wrote: blend over the remembered base instead.
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

-- After the animations, so the pose is what gets drawn
RunService.PreSimulation:Connect(updatePoses)

Players.PlayerRemoving:Connect(function(player)
    if player.Character then
        rigs[player.Character] = nil
    end
end)

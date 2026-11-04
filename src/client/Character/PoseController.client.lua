-- Blends whole-body poses into every R15 character's joints, before physics each frame: the
-- Qinggong poses (QinggongFx.pose: steps, tucks, the crane glide), the combat poses (CombatFx.pose)
-- and each realm's meditation idle while cultivating (MeditationPoses). Each pose is a table of joint name -> target Transform;
-- poses fade in and out by weight, and the default animations stay underneath.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local QinggongFx = require(script.Parent.Parent:WaitForChild("Qinggong"):WaitForChild("QinggongFx"))
local CombatFx = require(script.Parent.Parent:WaitForChild("Combat"):WaitForChild("CombatFx"))
local MeditationPoses = require(script.Parent:WaitForChild("MeditationPoses"))

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
-- turned into it. Sword: the three slashes of the combo (SLASH_KEYS, below).
-- Spear: held in both hands, the left shoulder leading, the left hand up the shaft (SpearReady): the
-- hands draw back (SpearDraw), then drive forward together. The arm values were solved against an R15
-- rig so both hands land on the shaft (within a quarter stud at rest).
local STRIKES = {
    Palm = {
        RightShoulder = pointLimb(Vector3.new(-0.05, -0.12, -0.99)),
        RightElbow = deg(0, 0, 0),
        RightWrist = deg(-55, 0, 0),
        LeftShoulder = pointLimb(Vector3.new(0.12, -0.75, 0.65)),
        LeftElbow = deg(95, 0, 0),
        Waist = deg(0, -25, 0),
    },
    Spear = {
        RightShoulder = pointLimb(Vector3.new(-0.29, -0.62, -0.73)),
        RightElbow = deg(0, 45, 0),
        RightWrist = deg(40, -20, -15),
        LeftShoulder = pointLimb(Vector3.new(0.52, -0.32, -0.79)),
        LeftElbow = deg(0, 15, 0),
        Waist = deg(0, -22, 0),
    },
    SpearDraw = {
        RightShoulder = pointLimb(Vector3.new(-0.28, -0.96, 0.06)),
        RightElbow = deg(70, -15, 0),
        RightWrist = deg(-10, 10, -60),
        LeftShoulder = pointLimb(Vector3.new(0.6, -0.68, -0.43)),
        LeftElbow = deg(40, -60, 0),
        Waist = deg(0, -40, 0),
    },
    -- the ready stances, while a weapon is out after a strike. Sword: the right arm forward, the blade
    -- up before the body, the left drawn back. Spear: side-on, the shaft level at the hip, both hands on it.
    SwordReady = {
        RightShoulder = pointLimb(Vector3.new(0.3, -0.75, -0.59)),
        RightElbow = deg(55, 0, 0),
        RightWrist = deg(-10, 0, 0),
        LeftShoulder = pointLimb(Vector3.new(-0.32, -0.85, 0.42)),
        LeftElbow = deg(30, 0, 0),
        Waist = deg(0, 12, 0),
    },
    SpearReady = {
        RightShoulder = pointLimb(Vector3.new(-0.29, -0.73, -0.62)),
        RightElbow = deg(0, 30, 0),
        RightWrist = deg(50, -10, -30),
        LeftShoulder = pointLimb(Vector3.new(0.49, -0.42, -0.76)),
        LeftElbow = deg(0, -30, 0),
        Waist = deg(0, -30, 0),
    },
}

-- The sword's combo: each slash is a timeline of keys (seconds, a whole-upper-body pose), eased from
-- key to key, so it has anticipation, a fast swing and a follow-through; the sword is welded to the
-- right hand, so the blade goes where the arm takes it (CombatFx). The wrist cocks the blade out in
-- line with the forearm through the swing. Root leans the whole body. 1: a diagonal cut, high right to
-- low left. 2: a backhand rising from there to high right. 3: the finisher, overhead and straight down.
local function slashKey(rightArm, rightElbow, rightWrist, leftArm, leftElbow, waist, neck, root)
    return {
        RightShoulder = pointLimb(rightArm), RightElbow = rightElbow, RightWrist = rightWrist,
        LeftShoulder = pointLimb(leftArm), LeftElbow = leftElbow,
        Waist = waist, Neck = neck, Root = root or CFrame.identity,
    }
end
local SLASH_TIMES = { 0.1, 0.16, 0.25 } -- the wind-up reached, mid-swing, the end of the swing
local SLASH_KEYS = {
    {
        slashKey(Vector3.new(0, 0.97, 0.24), deg(90), deg(-90, 15, 0), Vector3.new(-0.25, -0.75, -0.6), deg(60), deg(0, 35, 0), deg(0, -20, 0)),
        slashKey(Vector3.new(-0.58, -0.58, -0.58), deg(60), deg(-90, -15, -15), Vector3.new(-0.2, -0.8, 0.1), deg(40), deg(0, 0, 0), deg(0, 0, 0)),
        slashKey(Vector3.new(-0.76, -0.46, -0.46), deg(0), deg(-90, 30, 0), Vector3.new(-0.45, -0.75, 0.5), deg(55), deg(0, -35, 0), deg(0, 25, 0)),
    },
    {
        slashKey(Vector3.new(-0.81, -0.32, -0.49), deg(0), deg(-90, 15, 0), Vector3.new(-0.45, -0.75, 0.5), deg(55), deg(0, -35, 0), deg(0, 25, 0)),
        slashKey(Vector3.new(-0.66, -0.53, -0.53), deg(70), deg(-80, -15, 0), Vector3.new(-0.2, -0.8, 0.1), deg(40), deg(0, 0, 0), deg(0, 0, 0)),
        slashKey(Vector3.new(-0.15, 0.77, -0.62), deg(130), deg(-90, -30, 0), Vector3.new(0.1, -0.7, -0.7), deg(50), deg(0, 35, 0), deg(0, -20, 0)),
    },
    {
        slashKey(Vector3.new(0.75, 0.3, -0.6), deg(90), deg(-30, -45, 45), Vector3.new(-0.15, 0.85, -0.3), deg(70), deg(8, 10, 0), deg(-6, 0, 0), deg(8, 0, 0)),
        slashKey(Vector3.new(0.32, 0.95, 0), deg(100), deg(-90, 0, 0), Vector3.new(-0.25, -0.5, -0.6), deg(30), deg(-8, 0, 0), deg(0, 0, 0), deg(-4, 0, 0)),
        slashKey(Vector3.new(-0.76, -0.46, -0.46), deg(80), deg(-90, -30, 0), Vector3.new(-0.3, -0.8, 0.5), deg(50), deg(-18, 0, 0), deg(10, 0, 0), deg(-14, 0, 0)),
    },
}

-- The spearman's stances (the owner's reference, 2026-11-04), whole-body, for a player standing still
-- on the ground: wide and low, side-on with the left leg leading, the head turned to look ahead, the
-- shaft in both hands. Guard: level across the body. Low: a deep lunge, the tip forward and down. Draw
-- and Thrust: the strike. A walking or airborne player uses STRIKES' arms-only versions. The values
-- were solved against an R15 rig: the hands on the shaft, the feet flat on the floor.
local function spearStance(drop, yaw, waist, neck, arms, legs)
    return {
        Root = CFrame.new(0, drop, 0) * deg(0, yaw, 0), Waist = waist, Neck = neck,
        RightShoulder = pointLimb(arms[1]), RightElbow = arms[2], RightWrist = arms[3],
        LeftShoulder = pointLimb(arms[4]), LeftElbow = arms[5],
        LeftHip = pointLimb(legs[1]) * legs[2], LeftKnee = legs[3], LeftAnkle = legs[4],
        RightHip = pointLimb(legs[5]) * legs[6], RightKnee = legs[7], RightAnkle = legs[8],
    }
end
local SPEAR_STANCES = {
    SpearReady = spearStance(-0.6, -62, deg(0, -8, 0), deg(0, 55, 0),
        { Vector3.new(-0.64, -0.64, -0.43), deg(50), deg(-25, 15, -45), Vector3.new(0.18, -0.37, -0.91), deg(0) },
        { Vector3.new(-0.68, -0.27, -0.68), deg(0, 30, 0), deg(-60), deg(-20, 15, 20),
          Vector3.new(0.97, -0.24, 0), deg(0, -75, 0), deg(-60), deg(0, 45, -20) }),
    SpearLow = spearStance(-0.8, -55, deg(-6, -5, 0), deg(0, 45, 0),
        { Vector3.new(-0.45, 0.89, 0), deg(130), deg(-45, 0, 45), Vector3.new(0.41, -0.41, -0.82), deg(30) },
        { Vector3.new(-0.83, 0, -0.55), deg(0, 60, 0), deg(-70), deg(-20, 0, 0),
          Vector3.new(0.87, -0.44, 0.22), deg(0, -60, 0), deg(-20), deg(-20, 15, -40) }),
    SpearDraw = spearStance(-0.65, -72, deg(0, -14, 0), deg(0, 60, 0),
        { Vector3.new(-0.44, -0.87, 0.22), deg(110), deg(-90, 0, -45), Vector3.new(0.49, -0.73, -0.49), deg(0) },
        { Vector3.new(-0.91, -0.18, -0.37), deg(0, 60, 0), deg(-70), deg(-10, 0, 10),
          Vector3.new(0.98, -0.2, 0), deg(0, -90, 0), deg(-60), deg(-20, 45, 0) }),
    Spear = spearStance(-0.6, -30, deg(-6, -10, 0), deg(0, 30, 0),
        { Vector3.new(-0.81, -0.32, -0.49), deg(20), deg(15, 30, -15), Vector3.new(0.24, -0.24, -0.94), deg(0) },
        { Vector3.new(-0.18, -0.37, -0.91), deg(0, -15, 0), deg(-50), deg(-30, 30, 30),
          Vector3.new(0.62, -0.62, 0.47), deg(0, -60, 0), deg(-20), deg(30, 30, -50) }),
}

-- The spear's slash. The arms stay locked as they are in the guard, so both hands stay on the shaft and
-- the whole body swings it: from coiled to the right, the tip behind the right shoulder's line, round to
-- the left. Standing still the legs turn with it; moving, only the waist does (the arms-only guard).
local SPEAR_SLASH_TIMES = { 0.1, 0.17, 0.3 } -- coiled, mid-sweep, the end of the sweep
local function spearSlashKey(rootYaw, waistYaw, neckYaw)
    local key = table.clone(SPEAR_STANCES.SpearReady)
    key.Root = CFrame.new(0, -0.6, 0) * deg(0, rootYaw, 0)
    key.Waist = deg(0, waistYaw, 0)
    key.Neck = deg(0, neckYaw, 0)
    return key
end
local function spearSlashMoving(waistYaw)
    local key = table.clone(STRIKES.SpearReady)
    key.Waist = deg(0, waistYaw, 0)
    return key
end
local SPEAR_SLASH_KEYS = {
    Still = { spearSlashKey(-105, -40, 60), spearSlashKey(-65, -12, 35), spearSlashKey(-18, 10, 5) },
    Moving = { spearSlashMoving(-75), spearSlashMoving(-30), spearSlashMoving(30) },
}

-- writes into `pose` a slash's timeline at `elapsed` seconds
local function slashPose(pose, keys, times, elapsed)
    table.clear(pose)
    local from, to, t = keys[1], keys[1], 0
    if elapsed >= times[3] then
        from, to = keys[3], keys[3]
    elseif elapsed >= times[2] then
        -- slowing out of the blow; easing both ways here would stop the blade dead at the middle key
        t = (elapsed - times[2]) / (times[3] - times[2])
        from, to, t = keys[2], keys[3], 1 - (1 - t) * (1 - t)
    elseif elapsed >= times[1] then
        -- gathering speed into the blow
        t = (elapsed - times[1]) / (times[2] - times[1])
        from, to, t = keys[1], keys[2], t * t
    end
    for name, cframe in from do
        pose[name] = cframe:Lerp(to[name], t)
    end
end

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
local SLASH_BLEND_SPEED = 34    -- a slash follows its keys closely: its swing lasts a tenth of a second
local STANCE_MAX_SPEED = 3      -- studs a second: above this, a spear's stance gives way to arms only

-- A meditation idle eases in slowly, on a smooth curve rather than the other poses' quick blend, so
-- the body settles into it (the owner, 2026-11-04: "keep the animation slow").
local MEDITATION_ENTER, MEDITATION_LEAVE = 3, 1.2 -- seconds

local rigs = {}

local function findJoints(character)
    local joints = {}
    for _, joint in character:GetDescendants() do
        if joint:IsA("Motor6D") or joint:IsA("AnimationConstraint") then
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

-- on the ground, hardly moving, not in sword flight: a spear's whole-body stances are for this
local function standingStill(player, character)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    return humanoid ~= nil and rootPart ~= nil and humanoid.FloorMaterial ~= Enum.Material.Air
        and rootPart.AssemblyLinearVelocity.Magnitude < STANCE_MAX_SPEED and player:GetAttribute("IsFlying") ~= true
end

local function choosePose(player, character, rig)
    if player:GetAttribute("IsCultivating") == true then
        return MeditationPoses.forPlayer(player)
    end
    local strikeName = CombatFx.pose(player)
    local strike = STRIKES[strikeName]
    if SPEAR_STANCES[strikeName] then
        if standingStill(player, character) then
            return SPEAR_STANCES[strikeName]
        end
        strike = strike or STRIKES.SpearReady
    elseif strikeName == "Slash" then
        local step, elapsed = CombatFx.slash(player)
        rig.slash = rig.slash or {}
        slashPose(rig.slash, SLASH_KEYS[step], SLASH_TIMES, elapsed)
        strike = rig.slash
    elseif strikeName == "SpearSlash" then
        local _, elapsed = CombatFx.slash(player)
        rig.slash = rig.slash or {}
        slashPose(rig.slash, if standingStill(player, character) then SPEAR_SLASH_KEYS.Still else SPEAR_SLASH_KEYS.Moving, SPEAR_SLASH_TIMES, elapsed)
        strike = rig.slash
    end
    if player:GetAttribute("IsFlying") == true then
        local rootPart = character:FindFirstChild("HumanoidRootPart")
        local speed = if rootPart then rootPart.AssemblyLinearVelocity.Magnitude else 0
        local ride = if speed > FLYING_MOVE_SPEED then FLYING else HOVERING
        if strike == rig.slash and strike then
            -- it changes every frame, so it can't be cached: one table, rewritten
            rig.slashRide = rig.slashRide or {}
            table.clear(rig.slashRide)
            for name, cframe in ride do
                rig.slashRide[name] = cframe
            end
            for name, cframe in strike do
                if name ~= "Root" then
                    rig.slashRide[name] = cframe
                end
            end
            return rig.slashRide
        end
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
for name, pose in STRIKES do
    -- a stance settles at the normal pace; the blows snap
    if name ~= "SwordReady" and name ~= "SpearReady" then
        QUICK_POSES[pose] = true
    end
end
QUICK_POSES[SPEAR_STANCES.SpearDraw] = true
QUICK_POSES[SPEAR_STANCES.Spear] = true

local function updatePoses(deltaTime)
    local now = os.clock()
    local normalStep = 1 - math.exp(-BLEND_SPEED * deltaTime)
    local quickStep = 1 - math.exp(-QINGGONG_BLEND_SPEED * deltaTime)
    local slashStep = 1 - math.exp(-SLASH_BLEND_SPEED * deltaTime)
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

        local wanted = if humanoid.Health > 0 then choosePose(player, character, rig) else nil
        local slashing = wanted ~= nil and (wanted == rig.slash or wanted == rig.slashRide)
        if wanted and rig.weights[wanted] == nil then
            rig.weights[wanted] = 0
        end
        for pose, weight in rig.weights do
            if MeditationPoses.isPose(pose) then
                MeditationPoses.refresh(pose, now)
                local rate = if wanted == pose then 1 / MEDITATION_ENTER else -1 / MEDITATION_LEAVE
                rig.settling = rig.settling or {}
                local progress = math.clamp((rig.settling[pose] or 0) + rate * deltaTime, 0, 1)
                rig.settling[pose] = progress
                rig.weights[pose] = if wanted ~= pose and progress <= 0 then nil else progress * progress * (3 - 2 * progress)
                continue
            end
            local step = if slashing or pose == rig.slash or pose == rig.slashRide then slashStep
                elseif QUICK_POSES[pose] or (wanted and QUICK_POSES[wanted]) then quickStep else normalStep
            weight += ((if pose == wanted then 1 else 0) - weight) * step
            rig.weights[pose] = if pose ~= wanted and weight < 0.01 then nil else weight
        end

        if next(rig.weights) == nil and next(rig.written) == nil then
            continue
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


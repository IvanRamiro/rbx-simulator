-- The meditation idle: the lotus seat, for every realm (the owner, 2026-11-11: "replace all the idle when
-- cultivating to lotus sit, this is for all realms", then "the character will remain floating even in lotus
-- sit while cultivating"; the twelve realm idles of 2026-11-04 were removed). Played by PoseController while
-- a player cultivates. The first four realms sit on the ground; from Ascendant on the seat floats, higher
-- with each realm, bobbing slowly on the air.
--
-- Each realm's pose is a whole-body table, rewritten each frame it's in use. The body places itself (Root):
-- the character's own height never changes, so the seat sinks the body to the ground or lifts it. Every
-- joint breathes a beat after the one it hangs from, so motion flows out through the body.
--
-- Rig numbers (an R15 character, from the HumanoidRootPart): the hips 0.9 below it, the ankle 2.63 below
-- it on the floor, a leg 1.73 long, an arm 1.68 long.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local MeditationPoses = {}

local FIRST_FLOATING = 5            -- Ascendant Realm: the first realm whose seat leaves the ground
local HOVER_FIRST, HOVER_LAST = 1.2, 2.2 -- studs between the floor and the seat, at Ascendant and at the last realm
local HOVER_BOB = 0.12              -- how far a floating seat rises and sinks on its slow bob

local ARM_UPPER, ARM_LOWER = 0.84, 0.84

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

-- Two-bone reach: the rotations that bring a limb's end to `target` (from its top joint, in its
-- parent's axes), the middle joint bending toward `hint`. A knee hinges backward, an elbow forward:
-- `sign` is -1 for a leg, 1 for an arm (only arms use it now: PoseController's weapon and carrying poses). Returns the top joint's and the middle joint's Transform.
local function limb(target, upper, lower, hint, sign)
    local distance = math.clamp(target.Magnitude, 0.2, upper + lower - 0.01)
    local toward = target.Unit
    local cosine = math.clamp((upper * upper + distance * distance - lower * lower) / (2 * upper * distance), -1, 1)
    local side = hint - toward * hint:Dot(toward)
    side = if side.Magnitude > 1e-3 then side.Unit else Vector3.new(0, 0, -1)
    local upperDir = toward * cosine + side * math.sqrt(1 - cosine * cosine)
    local lowerDir = (toward * distance - upperDir * upper).Unit
    local off = lowerDir - upperDir * lowerDir:Dot(upperDir)
    off = if off.Magnitude > 1e-3 then off.Unit else -side
    -- the upper bone's own axes: -Y down the bone; a leg's lower bone swings to +Z, an arm's to -Z
    local y = -upperDir
    local z = if sign < 0 then off else -off
    local x = y:Cross(z)
    local bend = math.deg(math.acos(math.clamp(lowerDir:Dot(upperDir), -1, 1)))
    return CFrame.fromMatrix(Vector3.zero, x, y, z), deg(sign * bend)
end

local function arm(target, hint)
    return limb(target, ARM_UPPER, ARM_LOWER, hint, 1)
end

-- ---------- the lotus seat: (pose, s, hover), s a sine with a lag and an amount, hover the studs off the floor ----------
-- The hands resting on the knees, the back straight; the only motion is the breath, slow and deep, lifting
-- the chest and shoulders, and on the air a slow bob
local SEAT_Y = -1.22 -- the root joint's drop that sets the seat on the floor
local LOTUS = { Loop = 5, Write = function(pose, s, hover)
    local bob = if hover > 0 then s(-1.2, HOVER_BOB) else 0
    pose.Root = CFrame.new(0, SEAT_Y + hover + bob + s(0, 0.015), 0)
    pose.Waist = deg(3 + s(0.3, 1.6))
    pose.Neck = deg(-7 + s(0.6, 1.2))
    local hip = deg(0, -50, 0) * deg(85, 0, 0)
    pose.RightHip = hip
    pose.RightKnee = pointLimb(hip:VectorToObjectSpace(Vector3.new(-0.95, -0.12, 0.25)))
    pose.RightAnkle = deg(-20)
    pose.LeftHip = deg(0, 50, 0) * deg(85, 0, 0)
    pose.LeftKnee = pointLimb(pose.LeftHip:VectorToObjectSpace(Vector3.new(0.95, -0.12, 0.25)))
    pose.LeftAnkle = deg(-20)
    pose.RightShoulder = pointLimb(Vector3.new(0.14, -0.84, -0.52 + s(0.5, 0.015)))
    pose.RightElbow = deg(28 + s(0.8, 1.5))
    pose.RightWrist = deg(-18)
    pose.LeftShoulder = pointLimb(Vector3.new(-0.14, -0.84, -0.52 + s(0.5, 0.015)))
    pose.LeftElbow = deg(28 + s(0.8, 1.5))
    pose.LeftWrist = deg(-18)
end }

-- ---------- use ----------
local realmCount = #GameConfig.WeaponTiers
local poses = {}   -- [realm number] = its pose table
local hoverOf = {} -- [pose table] = its seat's height off the floor
local stamps = {}  -- [pose table] = the clock it was last written at

local function write(pose, now)
    local hover = hoverOf[pose]
    if hover == nil or stamps[pose] == now then
        return
    end
    stamps[pose] = now
    local w = math.pi * 2 * now / LOTUS.Loop
    LOTUS.Write(pose, function(lag, amount)
        return amount * math.sin(w - lag)
    end, hover)
end

for realm = 1, realmCount do
    local pose = {}
    poses[realm] = pose
    hoverOf[pose] = if realm < FIRST_FLOATING then 0
        else HOVER_FIRST + (HOVER_LAST - HOVER_FIRST) * (realm - FIRST_FLOATING) / math.max(realmCount - FIRST_FLOATING, 1)
    write(pose, 0)
end

local realmNumbers = {} -- [realm name] = its number, in the order of the ranks
for index, tier in GameConfig.WeaponTiers do
    realmNumbers[tier.Realm] = index
end

-- the pose a cultivating player takes: the lotus seat, on the ground or floating by their realm
function MeditationPoses.forPlayer(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return poses[rank and realmNumbers[rank.Realm] or 1]
end

function MeditationPoses.isPose(pose)
    return hoverOf[pose] ~= nil
end

-- the limb solvers, for PoseController's weapon and carrying poses
MeditationPoses.arm = arm
MeditationPoses.pointLimb = pointLimb

-- brings a pose in use up to this frame (`now`: the frame's clock, so several players share one write)
MeditationPoses.refresh = write

return MeditationPoses

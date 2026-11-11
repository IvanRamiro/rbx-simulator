-- The meditation idles (the owner, 2026-11-04: "make 12 unique and different idle, there should be no
-- similar or reuse idle; the beginner idle should be lotus sit"): one for each realm, each its own
-- silhouette and its own motion, played by PoseController while a player cultivates.
--
--    1 Qi Awakening           the lotus seat, on the ground: a beginner can't leave it yet
--    2 Qi Foundation          standing post: knees bent, the arms round an unseen tree
--    3 Spirit Core            kneeling, the hands circling the core they hold at the belly
--    4 Spirit Soul            the crane, on one leg, the arms spread low like wings
--    5 Ascendant Realm        Floating Ascension: reclined on the air, a wide wingspan, a knee to the sky
--    6 Immortal Realm         standing on air: sword fingers before the chest, a hand behind the back
--    7 Divine Realm           kneeling on air, one arm thrust at the heavens
--    8 Cosmic Realm           upside down, legs crossed above, orbiting slowly
--    9 Void Realm             curled tight, tumbling end over end
--   10 Heavenly Dao           cloud hands: a low stance, the arms flowing in unbroken circles
--   11 Primordial Realm       a wide squat, both arms driving up, holding the sky up
--   12 Eternal Transcendence  spread as a star, turning
--
-- Each writes a whole-body pose into one table, rewritten each frame it's in use. The body places
-- itself (Root): the character's own height never changes, so a pose can sit on the ground or float.
-- Feet on the floor are solved (`limb`), so they stay planted while the body sinks and breathes. Every
-- joint breathes a beat after the one it hangs from, so motion flows out through the body.
--
-- Rig numbers (an R15 character, from the HumanoidRootPart): the hips 0.9 below it, the ankle 2.63 below
-- it on the floor, a leg 1.73 long, an arm 1.68 long.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local MeditationPoses = {}

-- shows one realm's idle (its number) on every player: a review hook, nil in the game
MeditationPoses.Preview = nil

local ARM_UPPER, ARM_LOWER = 0.84, 0.84
local LEG_UPPER, LEG_LOWER = 0.85, 0.88
local HIP_Y = -0.9
local FOOT_Y = -2.63 -- the ankle, with the foot flat on the floor

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
-- `sign` is -1 for a leg, 1 for an arm. Returns the top joint's and the middle joint's Transform.
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

local function leg(target, hint)
    return limb(target, LEG_UPPER, LEG_LOWER, hint, -1)
end

local function arm(target, hint)
    return limb(target, ARM_UPPER, ARM_LOWER, hint, 1)
end

-- the ankle that keeps a foot flat on the floor, under this hip and knee
local function flatAnkle(hip, knee)
    return (hip * knee).Rotation:Inverse()
end

-- a planted foot, from the hip, for a body lowered by `drop` and shifted by `shift`
local function plantedFoot(x, z, drop, shift)
    return Vector3.new(x, FOOT_Y - HIP_Y - drop, z) - (shift or Vector3.zero)
end

-- ---------- the idles: (pose, s, c, w), s and c a sine and a cosine with a lag and an amount, w the phase ----------
local IDLES = {}

-- 1: the lotus seat. Sits right on the ground, the hands resting on the knees, the back straight;
-- the only motion is the breath, slow and deep, lifting the chest and shoulders
IDLES[1] = { Loop = 5, Write = function(pose, s)
    pose.Root = CFrame.new(0, -1.22 + s(0, 0.015), 0)
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

-- 2: standing post. Feet a shoulder apart, knees soft, the arms rounded at the chest as if round an
-- unseen tree, the fingers a hand apart; the whole body sinks and rises on the breath
IDLES[2] = { Loop = 7, Write = function(pose, s)
    local drop = -0.42 + s(0, 0.06)
    pose.Root = CFrame.new(0, drop, 0)
    pose.Waist = deg(-3 + s(0.5, 1))
    pose.Neck = deg(3 + s(0.9, 1))
    pose.RightHip, pose.RightKnee = leg(plantedFoot(0.5, 0, drop), Vector3.new(0.4, 0, -1))
    pose.LeftHip, pose.LeftKnee = leg(plantedFoot(-0.5, 0, drop), Vector3.new(-0.4, 0, -1))
    pose.RightAnkle = flatAnkle(pose.RightHip, pose.RightKnee)
    pose.LeftAnkle = flatAnkle(pose.LeftHip, pose.LeftKnee)
    local open = s(0.7, 0.05)
    pose.RightShoulder, pose.RightElbow = arm(Vector3.new(-0.62 + open, -0.62 + s(0.7, 0.03), -1.15), Vector3.new(1, -0.6, 0))
    pose.LeftShoulder, pose.LeftElbow = arm(Vector3.new(0.62 - open, -0.62 + s(0.7, 0.03), -1.15), Vector3.new(-1, -0.6, 0))
    pose.RightWrist = deg(10, 0, 25)
    pose.LeftWrist = deg(10, 0, -25)
end }

-- 3: kneeling on the heels, leaning a little over the hands, which circle one another at the belly
-- round the core they hold; the head bows to watch it
IDLES[3] = { Loop = 6, Write = function(pose, s, c)
    pose.Root = CFrame.new(0, -1 + s(0, 0.02), 0)
    pose.Waist = deg(-8 + s(0.3, 1.5))
    pose.Neck = deg(-16 + s(0.6, 2))
    pose.RightHip, pose.RightKnee = leg(Vector3.new(0.05, -0.5, 0.15), Vector3.new(0, 0, -1))
    pose.LeftHip, pose.LeftKnee = leg(Vector3.new(-0.05, -0.5, 0.15), Vector3.new(0, 0, -1))
    pose.RightAnkle = deg(-55)
    pose.LeftAnkle = deg(-55)
    pose.RightShoulder, pose.RightElbow = arm(Vector3.new(-0.95 + c(0, 0.09), -0.98 + s(0, 0.09), -0.72), Vector3.new(1, -1, 0.3))
    pose.LeftShoulder, pose.LeftElbow = arm(Vector3.new(0.95 - c(0, 0.09), -0.98 - s(0, 0.09), -0.72), Vector3.new(-1, -1, 0.3))
    pose.RightWrist = deg(-30, 0, -30)
    pose.LeftWrist = deg(-30, 0, 30)
end }

-- 4: the crane. Balanced on the left leg, the right knee drawn up high, the arms spread low and back
-- like wings that lift as it breathes; the balance shifts a little over the standing foot
IDLES[4] = { Loop = 8, Write = function(pose, s)
    local drop = -0.08 + s(0, 0.03)
    local shift = Vector3.new(-0.18 + s(0.4, 0.04), 0, 0)
    pose.Root = CFrame.new(shift.X, drop, 0) * deg(0, 0, s(0.4, 1.4))
    pose.Waist = deg(-2 + s(0.7, 1), 0, s(0.8, -1.5))
    pose.Neck = deg(6 + s(1.1, 1.5), s(1.3, 3), 0)
    pose.LeftHip, pose.LeftKnee = leg(plantedFoot(0, -0.03, drop), Vector3.new(0, 0, -1))
    pose.LeftAnkle = flatAnkle(pose.LeftHip, pose.LeftKnee)
    pose.RightHip = deg(104 + s(0.5, 2), 0, 6)
    pose.RightKnee = deg(-118 + s(0.9, 2))
    pose.RightAnkle = deg(-46 + s(1.3, 4))
    local lift = s(0.9, 0.09)
    pose.RightShoulder = pointLimb(Vector3.new(0.82, -0.42 + lift, 0.32))
    pose.RightElbow = deg(14 + s(1.3, 4))
    pose.RightWrist = deg(0, 0, 20 + s(1.7, 8))
    pose.LeftShoulder = pointLimb(Vector3.new(-0.82, -0.42 + lift, 0.32))
    pose.LeftElbow = deg(14 + s(1.3, 4))
    pose.LeftWrist = deg(0, 0, -20 - s(1.7, 8))
end }

-- 5: Floating Ascension (the owner's; the values are the AuraWorkbench's KeyframeSequence, tools/roblox/
-- floating_ascension_idle.lua). The body reclines on the air, the head tipped far back to face the
-- sky, the chest arched; the arms spread wide; the right knee drawn up, the left leg reaching down.
IDLES[5] = { Loop = 4, Write = function(pose, s, c)
    pose.Root = CFrame.new(0, 1.3 + s(0, 0.22), 0) * deg(28 + s(0.4, 1.5), c(0, 1.5), 0)
    pose.Waist = deg(14 + s(0.6, 3), 0, c(0.6, 1.2))
    pose.Neck = deg(38 + s(1.0, 2.5), c(1.0, 3), 0)
    pose.LeftShoulder = deg(-6, 10, -84 + s(0.9, 4))
    pose.LeftElbow = deg(8 + s(1.5, 4), 0, -6)
    pose.LeftWrist = deg(0, 0, -10 + s(2.1, 6))
    pose.RightShoulder = deg(-6, -10, 84 - s(0.9, 4))
    pose.RightElbow = deg(8 + s(1.5, 4), 0, 6)
    pose.RightWrist = deg(0, 0, 10 - s(2.1, 6))
    pose.RightHip = deg(122 + s(0.5, 3), 0, 6)
    pose.RightKnee = deg(-118 + s(1.1, 4), 0, 0)
    pose.RightAnkle = deg(-25 + s(1.6, 3), 0, 0)
    pose.LeftHip = deg(-22 + s(0.8, 2), 0, -3)
    pose.LeftKnee = deg(-6 + s(1.4, 2), 0, 0)
    pose.LeftAnkle = deg(-42 + s(1.9, 4), 0, 0)
end }

-- 6: the immortal standing on air, upright and unhurried: the feet hanging pointed, one crossed behind
-- the other; sword fingers raised before the chest, the other hand folded behind the back; the chin up
IDLES[6] = { Loop = 6, Write = function(pose, s, c)
    pose.Root = CFrame.new(0, 1.15 + s(0, 0.14), 0) * deg(0, -18 + c(0.2, 4), 0)
    pose.Waist = deg(1 + s(0.4, 1), 6 + c(0.5, 2), 0)
    pose.Neck = deg(8 + s(0.8, 1.2), 12 + c(0.9, 3), 0)
    pose.RightHip = pointLimb(Vector3.new(0.05, -0.99, -0.12))
    pose.RightKnee = deg(-6 + s(0.7, 2))
    pose.RightAnkle = deg(-48 + s(1.1, 3))
    pose.LeftHip = pointLimb(Vector3.new(0.14, -0.96, 0.2))
    pose.LeftKnee = deg(-34 + s(0.9, 3))
    pose.LeftAnkle = deg(-52 + s(1.3, 3))
    pose.RightShoulder, pose.RightElbow = arm(Vector3.new(-0.72 + c(0.8, 0.03), -0.34 + s(0.8, 0.05), -0.92), Vector3.new(1, -1, 0.2))
    pose.RightWrist = deg(58, 0, -8)
    pose.LeftShoulder = pointLimb(Vector3.new(-0.3, -0.75, 0.58))
    pose.LeftElbow = deg(104 + s(1.1, 2), 40, 0)
    pose.LeftWrist = deg(-12)
end }

-- 7: down on one knee in the air, the right arm driven straight at the heavens, the fist of the left
-- at the hip, the face turned up to the strike it is calling; a pulse runs up the arm
IDLES[7] = { Loop = 3.5, Write = function(pose, s)
    pose.Root = CFrame.new(0, 0.95 + s(0, 0.1), 0) * deg(-4 + s(0.3, 1), 22, 0)
    pose.Waist = deg(10 + s(0.5, 1.5), -12, 0)
    pose.Neck = deg(30 + s(0.8, 2), -10, 0)
    pose.LeftHip = deg(86 + s(0.5, 1.5), 0, -4)
    pose.LeftKnee = deg(-88 + s(0.8, 2))
    pose.LeftAnkle = deg(-8)
    pose.RightHip = deg(-14 + s(0.6, 1.5), 0, 5)
    pose.RightKnee = deg(-96 + s(0.9, 2))
    pose.RightAnkle = deg(-40)
    pose.RightShoulder = pointLimb(Vector3.new(0.42 + s(0.9, 0.015), 0.9, -0.1))
    pose.RightElbow = deg(4 + s(1.2, 3))
    pose.RightWrist = deg(-6 + s(1.5, 5))
    pose.LeftShoulder = pointLimb(Vector3.new(-0.2, -0.72, 0.62))
    pose.LeftElbow = deg(98 + s(1, 2))
    pose.LeftWrist = deg(-10)
end }

-- 8: hanging upside down in space, the legs crossed above like a lotus turned over, the arms spread
-- like the arms of a galaxy; the whole figure orbits slowly round its own axis
IDLES[8] = { Loop = 16, Write = function(pose, s, _, w)
    pose.Root = CFrame.new(0, 2.5 + s(0, 0.14), 0) * deg(0, math.deg(w), 0) * deg(0, 0, 180)
    pose.Waist = deg(4 + s(1, 2))
    pose.Neck = deg(18 + s(1.5, 2))
    local hip = deg(0, -50, 0) * deg(85, 0, 0)
    pose.RightHip = hip
    pose.RightKnee = pointLimb(hip:VectorToObjectSpace(Vector3.new(-0.95, -0.12, 0.25)))
    pose.RightAnkle = deg(-25)
    pose.LeftHip = deg(0, 50, 0) * deg(85, 0, 0)
    pose.LeftKnee = pointLimb(pose.LeftHip:VectorToObjectSpace(Vector3.new(0.95, -0.12, 0.25)))
    pose.LeftAnkle = deg(-25)
    local sweep = s(2, 0.12)
    pose.RightShoulder = pointLimb(Vector3.new(0.86, 0.2 + sweep, 0.28))
    pose.RightElbow = deg(28 + s(2.5, 6))
    pose.RightWrist = deg(0, 0, 18 + s(3, 8))
    pose.LeftShoulder = pointLimb(Vector3.new(-0.86, 0.2 - sweep, -0.28))
    pose.LeftElbow = deg(28 - s(2.5, 6))
    pose.LeftWrist = deg(0, 0, -18 - s(3, 8))
end }

-- 9: curled tight in the void, knees to chest, the arms round the shins, the head tucked in, tumbling
-- slowly end over end; the curl loosens and tightens on a slow breath
IDLES[9] = { Loop = 18, Write = function(pose, s, _, w)
    local breath = s(0, 1) * math.cos(w * 3) -- quicker than the tumble, so it isn't locked to it
    pose.Root = CFrame.new(0, 1.7 + s(0, 0.12), 0) * deg(math.deg(w), 0, 0)
    pose.Waist = deg(-38 + breath * 3)
    pose.Neck = deg(-34 + breath * 3)
    pose.RightHip = deg(126 + breath * 2, 0, 4)
    pose.RightKnee = deg(-136 - breath * 2)
    pose.RightAnkle = deg(-30)
    pose.LeftHip = deg(126 + breath * 2, 0, -4)
    pose.LeftKnee = deg(-136 - breath * 2)
    pose.LeftAnkle = deg(-30)
    pose.RightShoulder, pose.RightElbow = arm(Vector3.new(-0.42, -0.88, -1.0), Vector3.new(1, 0, 0))
    pose.LeftShoulder, pose.LeftElbow = arm(Vector3.new(0.42, -0.88, -1.0), Vector3.new(-1, 0, 0))
    pose.RightWrist = deg(-20, 0, -25)
    pose.LeftWrist = deg(-20, 0, 25)
end }

-- 10: cloud hands. A low wide stance; the hands pass one another in never-ending circles before the
-- body, one rising past the face as the other sinks to the hip, the waist and eyes turning after them
IDLES[10] = { Loop = 7, Write = function(pose, s, c, w)
    local drop = -0.34 + c(0, 0.04) * math.cos(w)
    pose.Root = CFrame.new(math.sin(w) * 0.1, drop, 0)
    local shift = Vector3.new(math.sin(w) * 0.1, 0, 0)
    pose.Waist = deg(-2, math.sin(w - 0.3) * 24, 0)
    pose.Neck = deg(2, math.sin(w - 0.7) * 22, 0)
    pose.RightHip, pose.RightKnee = leg(plantedFoot(0.72, 0, drop, shift), Vector3.new(0.5, 0, -1))
    pose.LeftHip, pose.LeftKnee = leg(plantedFoot(-0.72, 0, drop, shift), Vector3.new(-0.5, 0, -1))
    pose.RightAnkle = flatAnkle(pose.RightHip, pose.RightKnee)
    pose.LeftAnkle = flatAnkle(pose.LeftHip, pose.LeftKnee)
    pose.RightShoulder, pose.RightElbow = arm(Vector3.new(-0.5 + math.sin(w) * 0.55, -0.72 + math.cos(w) * 0.42, -0.95), Vector3.new(1, -1, 0))
    pose.LeftShoulder, pose.LeftElbow = arm(Vector3.new(0.5 + math.sin(w) * 0.55, -0.72 - math.cos(w) * 0.42, -0.95), Vector3.new(-1, -1, 0))
    pose.RightWrist = deg(15, 0, math.sin(w) * 22)
    pose.LeftWrist = deg(15, 0, math.sin(w) * 22)
end }

-- 11: holding up the sky. A wide deep squat, both arms driven up over the head, the palms flat against
-- something immense; it presses up and gives a little, and the strain trembles through the body
IDLES[11] = { Loop = 5, Write = function(pose, s, _, w)
    local tremble = math.sin(w * 11) * 0.6
    local press = s(0, 1)
    local drop = -0.78 + press * 0.09
    pose.Root = CFrame.new(0, drop, 0) * deg(tremble * 0.4)
    pose.Waist = deg(7 + press * 2 + tremble)
    pose.Neck = deg(22 + press * 2)
    pose.RightHip, pose.RightKnee = leg(plantedFoot(0.92, 0, drop), Vector3.new(0.9, 0, -0.5))
    pose.LeftHip, pose.LeftKnee = leg(plantedFoot(-0.92, 0, drop), Vector3.new(-0.9, 0, -0.5))
    pose.RightAnkle = flatAnkle(pose.RightHip, pose.RightKnee)
    pose.LeftAnkle = flatAnkle(pose.LeftHip, pose.LeftKnee)
    pose.RightShoulder, pose.RightElbow = arm(Vector3.new(0.34, 1.4 + press * 0.1, -0.2), Vector3.new(1, 0.2, 0))
    pose.LeftShoulder, pose.LeftElbow = arm(Vector3.new(-0.34, 1.4 + press * 0.1, -0.2), Vector3.new(-1, 0.2, 0))
    pose.RightWrist = deg(72 + tremble, 0, 0)
    pose.LeftWrist = deg(72 + tremble, 0, 0)
end }

-- 12: the last realm, spread as a star: arms and legs flung wide and straight, the chest open, the face
-- to the sky; the figure rises high and turns, a slow wave running out along the limbs
IDLES[12] = { Loop = 20, Write = function(pose, s, _, w)
    local wave = w * 4
    local function ripple(lag, amount)
        return math.sin(wave - lag) * amount
    end
    pose.Root = CFrame.new(0, 1.9 + ripple(0, 0.12), 0) * deg(0, math.deg(w), 0) * deg(10 + ripple(0.3, 1.5))
    pose.Waist = deg(10 + ripple(0.5, 2))
    pose.Neck = deg(24 + ripple(0.8, 2))
    pose.RightShoulder = pointLimb(Vector3.new(0.94, 0.3 + ripple(0.8, 0.05), 0.05))
    pose.RightElbow = deg(4 + ripple(1.2, 4))
    pose.RightWrist = deg(0, 0, 10 + ripple(1.6, 8))
    pose.LeftShoulder = pointLimb(Vector3.new(-0.94, 0.3 + ripple(0.8, 0.05), 0.05))
    pose.LeftElbow = deg(4 + ripple(1.2, 4))
    pose.LeftWrist = deg(0, 0, -10 - ripple(1.6, 8))
    pose.RightHip = pointLimb(Vector3.new(0.5 + ripple(0.6, 0.03), -0.86, 0.04))
    pose.RightKnee = deg(-3 + ripple(1, -3))
    pose.RightAnkle = deg(-44 + ripple(1.4, 5))
    pose.LeftHip = pointLimb(Vector3.new(-0.5 - ripple(0.6, 0.03), -0.86, 0.04))
    pose.LeftKnee = deg(-3 + ripple(1, -3))
    pose.LeftAnkle = deg(-44 + ripple(1.4, 5))
end }

-- ---------- use ----------
local poses = {}    -- [realm number] = its pose table
local realmOf = {}  -- [pose table] = its realm number
local stamps = {}   -- [pose table] = the clock it was last written at

local function write(pose, now)
    if stamps[pose] == now then
        return
    end
    stamps[pose] = now
    local idle = IDLES[realmOf[pose]]
    local w = math.pi * 2 * now / idle.Loop
    idle.Write(pose, function(lag, amount)
        return amount * math.sin(w - lag)
    end, function(lag, amount)
        return amount * math.cos(w - lag)
    end, w)
end

for realm = 1, #IDLES do
    local pose = {}
    poses[realm] = pose
    realmOf[pose] = realm
    write(pose, 0)
end

local realmNumbers = {} -- [realm name] = its number, in the order of the ranks
for index, tier in GameConfig.WeaponTiers do
    realmNumbers[tier.Realm] = index
end

-- the pose a cultivating player takes: their realm's (the owner too, since 2026-11-11: their own
-- aura and its Floating Ascension pose were removed for the public test)
function MeditationPoses.forPlayer(player)
    if MeditationPoses.Preview then
        return poses[MeditationPoses.Preview]
    end
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return poses[rank and realmNumbers[rank.Realm] or 1]
end

function MeditationPoses.isPose(pose)
    return realmOf[pose] ~= nil
end

-- the limb solvers, for PoseController's weapon and carrying poses
MeditationPoses.arm = arm
MeditationPoses.pointLimb = pointLimb

-- brings a pose in use up to this frame (`now`: the frame's clock, so several players share one write)
MeditationPoses.refresh = write

return MeditationPoses

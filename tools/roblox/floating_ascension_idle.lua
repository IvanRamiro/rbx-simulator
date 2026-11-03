-- Floating Ascension idle (R15), a 4 s loop (120 frames at 30 fps), for the owner's brief
-- (2026-11-03): weightless floating suspension with a slow breathing hover; head tilted far back,
-- facing the sky; the upper torso gently arched; both arms spread wide in a horizontal wingspan; the
-- right knee bent and pointing up; the left leg reaching down, its foot pointed at the ground.
--
-- Run in Studio's command bar (Edit). It builds a KeyframeSequence, "FloatingAscensionIdle", in
-- ServerStorage and in the AuraWorkbench dummy's AnimSaves (so the Animation Editor lists it, to
-- tweak and publish). Keyframes every 0.5 s with Cubic InOut easing; every value is a base pose plus
-- a sine on the loop, each joint a little later than the one it hangs from, so the motion travels
-- out through the body (overlap): the root rises first, the chest follows, then the head, the arms
-- from shoulder to elbow to wrist, the legs from hip to knee to foot. The loop closes exactly.
--
-- Pose CFrames are joint transforms (as Motor6D.Transform / AnimationConstraint.Transform), in the
-- parent part's axes: +X turns the front (-Z) up (a head looking up, a body reclining, a thigh lifting
-- forward); Z rolls about the forward axis (an arm raising sideways).

local LENGTH = 4
local STEP = 0.5
local rad = math.rad

local function A(x, y, z)
    return CFrame.Angles(rad(x), rad(y or 0), rad(z or 0))
end

-- every joint's transform at time t (seconds)
local function pose(t)
    local w = math.pi * 2 * t / LENGTH
    local function s(lag, amp) return amp * math.sin(w - lag) end
    local function c(lag, amp) return amp * math.cos(w - lag) end
    return {
        -- the whole body reclines on the air and hovers (up 1.3 studs, bobbing 0.22 on the breath)
        LowerTorso = CFrame.new(0, 1.3 + s(0, 0.22), 0) * A(28 + s(0.4, 1.5), c(0, 1.5), 0),
        UpperTorso = A(14 + s(0.6, 3), 0, c(0.6, 1.2)),         -- the chest arches, opening on the in-breath
        Head = A(38 + s(1.0, 2.5), c(1.0, 3), 0),                -- far back: with the body's lean, the face is turned to the sky
        -- the wingspan: just below horizontal, swept a touch back, floating up and down a little;
        -- elbows soft, the wrists trailing behind the wave
        LeftUpperArm = A(-6, 10, -84 + s(0.9, 4)),
        LeftLowerArm = A(8 + s(1.5, 4), 0, -6),
        LeftHand = A(0, 0, -10 + s(2.1, 6)),
        RightUpperArm = A(-6, -10, 84 - s(0.9, 4)),
        RightLowerArm = A(8 + s(1.5, 4), 0, 6),
        RightHand = A(0, 0, 10 - s(2.1, 6)),
        -- the right knee up toward the sky, the shin folded under it, the foot softly pointed
        RightUpperLeg = A(122 + s(0.5, 3), 0, 6),       -- the thigh lifted high: with the lean, the knee points to the sky
        RightLowerLeg = A(-118 + s(1.1, 4), 0, 0),
        RightFoot = A(-25 + s(1.6, 3), 0, 0),
        -- the left leg reaching down (against the body's lean), the foot pointed at the ground
        LeftUpperLeg = A(-22 + s(0.8, 2), 0, -3),
        LeftLowerLeg = A(-6 + s(1.4, 2), 0, 0),
        LeftFoot = A(-42 + s(1.9, 4), 0, 0),
    }
end

-- the R15 tree: each pose under the pose of the part it hangs from
local TREE = {
    HumanoidRootPart = { "LowerTorso" },
    LowerTorso = { "UpperTorso", "LeftUpperLeg", "RightUpperLeg" },
    UpperTorso = { "Head", "LeftUpperArm", "RightUpperArm" },
    LeftUpperArm = { "LeftLowerArm" }, LeftLowerArm = { "LeftHand" },
    RightUpperArm = { "RightLowerArm" }, RightLowerArm = { "RightHand" },
    LeftUpperLeg = { "LeftLowerLeg" }, LeftLowerLeg = { "LeftFoot" },
    RightUpperLeg = { "RightLowerLeg" }, RightLowerLeg = { "RightFoot" },
}

local function build()
    local seq = Instance.new("KeyframeSequence")
    seq.Name = "FloatingAscensionIdle"
    seq.Loop = true
    seq.Priority = Enum.AnimationPriority.Action -- over the default idle, which would fight the pose
    for t = 0, LENGTH + 1e-6, STEP do
        local values = pose(t)
        local kf = Instance.new("Keyframe")
        kf.Time = t
        local function add(name, parent)
            local p = Instance.new("Pose")
            p.Name = name
            p.CFrame = values[name] or CFrame.identity
            p.EasingStyle = Enum.PoseEasingStyle.Cubic
            p.EasingDirection = Enum.PoseEasingDirection.InOut
            p.Weight = if values[name] then 1 else 0
            p.Parent = parent
            for _, child in TREE[name] or {} do
                add(child, p)
            end
        end
        add("HumanoidRootPart", kf)
        kf.Parent = seq
    end
    return seq
end

return { build = build, pose = pose, LENGTH = LENGTH }

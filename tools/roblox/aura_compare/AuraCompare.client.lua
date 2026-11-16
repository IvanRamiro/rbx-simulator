-- A TEMPLATE, not part of the game (kept in tools/, which Rojo doesn't sync). To compare a new
-- aura with the live one: build the stage (aura_compare_stage.lua, in Edit), then copy this script and
-- a candidate module (build(character, sub, options) -> aura; destroy(aura); TimeScale; clock) into
-- src/client/Auras/Candidates/, and take both out again once the owner has chosen. Realm 1's vortex
-- won this way on 2026-11-16 and now lives in RealmAura.
--
-- AuraCompare (Studio only): the live Realm 1 aura and a candidate side by side, for the owner to
-- choose. It does nothing unless the place is running in Studio AND Workspace.AuraCompare exists (the
-- comparison stage; tools/roblox/aura_compare_stage.lua builds it), so it never runs in the real game.
--
-- On the stage: LiveDummy wears the game's own Realm 1 (RealmAura.build, untouched), NewDummy wears
-- Realm1Candidate (the same base aura, with a jade Qi vortex in place of Realm 1's own layers). Both sit in the lotus seat cultivators take (MeditationPoses' LOTUS, breathing on
-- the same clock), on the same sub-rank.
--   1 to 5     both auras' sub-rank (Initiate .. Peak); also the stage's SubRank attribute
--   V          the camera: front, three-quarter, the game's third-person distance, 60 studs, back to normal
--   stage attributes (set on the client while playing): TimeScale (0.05 to 1, slow motion for both),
--   View (0 to 5, as V; 5 is from behind), Subject ("Live" or "New": the same views round one dummy;
--   empty: both), Facing (degrees: turns the stage, e.g. 180 for the open sky behind it)
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
    return
end
local stage = workspace:WaitForChild("AuraCompare", 10)
if not stage then
    return
end

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local auras = script.Parent.Parent
local RealmAura = require(auras:WaitForChild("RealmAura"))
local Realm1Candidate = require(script.Parent:WaitForChild("Realm1Candidate"))
local MeditationPoses = require(auras.Parent:WaitForChild("Character"):WaitForChild("MeditationPoses"))

local liveDummy = stage:WaitForChild("LiveDummy")
local newDummy = stage:WaitForChild("NewDummy")
local platform = stage:WaitForChild("Platform")

-- ---------- the review clock (slow motion moves the breath, the pose and both auras together) ----------
local clock = os.clock()
local function timeScale()
    return math.clamp(stage:GetAttribute("TimeScale") or 1, 0.05, 1)
end
Realm1Candidate.clock = function()
    return clock
end

-- ---------- the lotus seat (MeditationPoses' LOTUS, on the ground as at Realm 1) ----------
local pointLimb = MeditationPoses.pointLimb
local function deg(x, y, z)
    return CFrame.Angles(math.rad(x or 0), math.rad(y or 0), math.rad(z or 0))
end
local SEAT_Y, LOOP = -1.22, 5
local function lotus(s)
    local pose = {}
    pose.Root = CFrame.new(0, SEAT_Y + s(0, 0.015), 0)
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
    return pose
end

local function jointsOf(model)
    local joints = {}
    for _, j in model:GetDescendants() do
        if j:IsA("AnimationConstraint") or j:IsA("Motor6D") then
            joints[j.Name] = j
        end
    end
    return joints
end
local rigs = { jointsOf(liveDummy), jointsOf(newDummy) }

RunService.PreSimulation:Connect(function(dt)
    clock += dt * timeScale()
    local w = math.pi * 2 * clock / LOOP
    local pose = lotus(function(lag, amount)
        return amount * math.sin(w - lag)
    end)
    for _, joints in rigs do
        for name, cf in pose do
            local j = joints[name]
            if j then
                j.Transform = cf
            end
        end
    end
end)

-- ---------- the auras ----------
local live, candidate = nil, nil
local currentSub = nil

local function slowMo(inst, k)
    if inst:IsA("ParticleEmitter") then
        inst.TimeScale = k
    elseif inst:IsA("Beam") then
        local base = inst:GetAttribute("BaseTextureSpeed")
        if base == nil then
            base = inst.TextureSpeed
            inst:SetAttribute("BaseTextureSpeed", base)
        end
        inst.TextureSpeed = base * k
    elseif inst:IsA("Trail") then
        local base = inst:GetAttribute("BaseLifetime")
        if base == nil then
            base = inst.Lifetime
            inst:SetAttribute("BaseLifetime", base)
        end
        inst.Lifetime = math.min(20, base / k)
    end
end
local function applyTimeScale()
    local k = timeScale()
    Realm1Candidate.TimeScale = k
    for _, dummy in { liveDummy, newDummy } do
        for _, inst in dummy:GetDescendants() do
            if not string.find(inst.Name, "^Vortex") then -- the candidate's vortex follows Realm1Candidate.TimeScale
                slowMo(inst, k)
            end
        end
    end
end

local function build(sub)
    sub = math.clamp(math.floor(sub), 1, 5)
    if sub == currentSub then
        return
    end
    currentSub = sub
    if live and live.Parent then
        RealmAura.destroy(live)
    end
    if candidate then
        Realm1Candidate.destroy(candidate)
    end
    live = RealmAura.build(liveDummy:WaitForChild("HumanoidRootPart"), 1, sub, { isLocal = true })
    candidate = Realm1Candidate.build(newDummy, sub, { isLocal = true })
    stage:SetAttribute("SubRank", sub)
    applyTimeScale()
    print(string.format("[AuraCompare] Realm 1, sub-rank %d: LIVE (left) and NEW (right)", sub))
end

stage:GetAttributeChangedSignal("SubRank"):Connect(function()
    build(stage:GetAttribute("SubRank") or 3)
end)
stage:GetAttributeChangedSignal("TimeScale"):Connect(applyTimeScale)

-- ---------- the stage's turn ----------
local home = stage:GetPivot()
local function face()
    -- about the world's up, through the platform's centre
    stage:PivotTo(CFrame.new(home.Position) * CFrame.Angles(0, math.rad(stage:GetAttribute("Facing") or 0), 0) * home.Rotation)
end
-- the floor between the dummies, upright, its X the dummies' front (the platform is a cylinder,
-- stood up by a quarter turn about Z)
local function floorFrame()
    local upright = platform.CFrame * CFrame.Angles(0, 0, -math.pi / 2)
    return upright + Vector3.new(0, platform.Size.X / 2, 0)
end
stage:GetAttributeChangedSignal("Facing"):Connect(face)

-- ---------- the camera views ----------
local VIEWS = {
    -- { name, from (in the stage's frame: +X is the dummies' front), height to look at }, for both dummies
    -- at once; SOLO: the same views round one dummy (the stage's Subject attribute: "Live" or "New")
    { "front", Vector3.new(15, 2.2, 0), 1.6 },
    { "three-quarter", Vector3.new(11.5, 3.4, 10.5), 1.6 },
    { "third-person", Vector3.new(16, 7, 0), 1.2 },
    { "far", Vector3.new(58, 14, 6), 2 },
    { "behind", Vector3.new(-16, 6, 0), 1.6 },
}
local SOLO = {
    { "front", Vector3.new(10, 2.2, 0), 1.7 },
    { "three-quarter", Vector3.new(7.5, 3.2, 7), 1.7 },
    { "third-person", Vector3.new(-11, 4.6, 2.5), 1.9 }, -- the player's own camera, behind and above
    { "far", Vector3.new(58, 14, 0), 2 },
    { "behind", Vector3.new(-10, 3.5, 0), 1.7 },
}
local camera = workspace.CurrentCamera
local viewing = 0
local function setView(index)
    viewing = index
    RunService:UnbindFromRenderStep("AuraCompareView")
    if index == 0 then
        camera.CameraType = Enum.CameraType.Custom
        return
    end
    camera.CameraType = Enum.CameraType.Scriptable
    RunService:BindToRenderStep("AuraCompareView", Enum.RenderPriority.Camera.Value + 5, function()
        local frame = floorFrame()
        local subject = stage:GetAttribute("Subject")
        local dummy = if subject == "Live" then liveDummy elseif subject == "New" then newDummy else nil
        local v = VIEWS[index]
        if dummy then
            v = SOLO[index]
            local at = dummy.HumanoidRootPart.Position
            frame = CFrame.new(at.X, frame.Y, at.Z) * frame.Rotation
        end
        camera.CFrame = CFrame.lookAt((frame * CFrame.new(v[2])).Position, (frame * CFrame.new(0, v[3], 0)).Position)
    end)
end
stage:GetAttributeChangedSignal("View"):Connect(function()
    setView(math.clamp(stage:GetAttribute("View") or 0, 0, #VIEWS))
end)

local KEYS = {
    [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4, [Enum.KeyCode.Five] = 5,
    [Enum.KeyCode.KeypadOne] = 1, [Enum.KeyCode.KeypadTwo] = 2, [Enum.KeyCode.KeypadThree] = 3, [Enum.KeyCode.KeypadFour] = 4,
    [Enum.KeyCode.KeypadFive] = 5,
}
UserInputService.InputBegan:Connect(function(input, processed)
    if processed then
        return
    end
    local sub = KEYS[input.KeyCode]
    if sub then
        build(sub)
    elseif input.KeyCode == Enum.KeyCode.V then
        stage:SetAttribute("View", (viewing + 1) % (#VIEWS + 1))
    end
end)

Players.LocalPlayer.CharacterAdded:Connect(function()
    if viewing ~= 0 then
        setView(viewing)
    end
end)

face()
build(stage:GetAttribute("SubRank") or 3)

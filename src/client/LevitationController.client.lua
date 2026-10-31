local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local player = Players.LocalPlayer

local RISE_INFO = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local DESCEND_INFO = TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local LOTUS_HIP_HEIGHT = 0.6
local BOB_INFO = TweenInfo.new(GameConfig.LevitationBobTime, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)

local humanoid = nil
local normalHipHeight = nil
local normalWalkSpeed = nil
local meditationTrack = nil
local activeTween = nil
local isLevitating = false

local function cancelTween()
    if activeTween then
        activeTween:Cancel()
        activeTween = nil
    end
end

local function tweenHipHeight(targetHeight, tweenInfo)
    cancelTween()
    activeTween = TweenService:Create(humanoid, tweenInfo, { HipHeight = targetHeight })
    activeTween:Play()
    return activeTween
end

local function startLevitating()
    if isLevitating or not humanoid or humanoid.Health <= 0 then
        return
    end
    isLevitating = true

    if normalHipHeight == nil then
        normalHipHeight = humanoid.HipHeight
    end
    normalWalkSpeed = humanoid.WalkSpeed

    humanoid.WalkSpeed = 0
    humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)

    local legs = if humanoid.RigType == Enum.HumanoidRigType.R15 and GameConfig.MeditationAnimationId == 0
        then normalHipHeight * LOTUS_HIP_HEIGHT
        else normalHipHeight
    local hoverHeight = legs + GameConfig.LevitationHeight
    tweenHipHeight(hoverHeight, RISE_INFO).Completed:Connect(function(playbackState)
        if playbackState == Enum.PlaybackState.Completed and isLevitating then
            tweenHipHeight(hoverHeight + GameConfig.LevitationBobHeight, BOB_INFO)
        end
    end)

    if meditationTrack then
        meditationTrack:Play()
    end
end

local function stopLevitating()
    if not isLevitating then
        return
    end
    isLevitating = false

    if meditationTrack then
        meditationTrack:Stop()
    end

    tweenHipHeight(normalHipHeight, DESCEND_INFO)
    -- the rank may have changed while meditating, so prefer the current Qinggong run speed
    humanoid.WalkSpeed = player:GetAttribute("QinggongRunSpeed") or normalWalkSpeed
    humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, true)
end

local function updateLevitation()
    if player:GetAttribute("IsCultivating") == true then
        startLevitating()
    else
        stopLevitating()
    end
end

local function loadMeditationTrack()
    if GameConfig.MeditationAnimationId == 0 then
        return nil
    end

    local animator = humanoid:WaitForChild("Animator", 5)
    if not animator then
        return nil
    end

    local animation = Instance.new("Animation")
    animation.AnimationId = "rbxassetid://" .. GameConfig.MeditationAnimationId

    local track = animator:LoadAnimation(animation)
    track.Priority = Enum.AnimationPriority.Action
    track.Looped = true
    return track
end

local function onCharacterAdded(character)
    cancelTween()
    humanoid = nil
    normalHipHeight = nil
    meditationTrack = nil
    isLevitating = false

    local newHumanoid = character:WaitForChild("Humanoid")
    if player.Character ~= character then
        return
    end
    humanoid = newHumanoid
    meditationTrack = loadMeditationTrack()

    humanoid.Died:Connect(function()
        cancelTween()
        isLevitating = false
    end)

    updateLevitation()
end

player:GetAttributeChangedSignal("IsCultivating"):Connect(updateLevitation)
player.CharacterAdded:Connect(onCharacterAdded)

if player.Character then
    task.spawn(onCharacterAdded, player.Character)
end

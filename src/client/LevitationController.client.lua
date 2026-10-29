
-- Makes your own character hover gently while cultivating, and optionally plays
-- a meditation pose. The server decides whether you are cultivating (the
-- "IsCultivating" attribute); this script only changes how your character
-- moves and looks. Other players see the hover because your movement replicates.
--
-- Hovering works by smoothly raising Humanoid.HipHeight, which works for both
-- R6 and R15 characters without extra physics objects.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local player = Players.LocalPlayer

local RISE_INFO = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local DESCEND_INFO = TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
-- Repeats forever (-1) and reverses, giving a slow up-and-down bob
local BOB_INFO = TweenInfo.new(GameConfig.LevitationBobTime, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)

-- State for the current character. Reset on every respawn.
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

-- Only one HipHeight tween runs at a time
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

    -- Remember the normal height once per character so stopping can restore it
    if normalHipHeight == nil then
        normalHipHeight = humanoid.HipHeight
    end
    normalWalkSpeed = humanoid.WalkSpeed

    -- Stay still while meditating
    humanoid.WalkSpeed = 0
    humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)

    local hoverHeight = normalHipHeight + GameConfig.LevitationHeight
    tweenHipHeight(hoverHeight, RISE_INFO).Completed:Connect(function(playbackState)
        -- Start bobbing only if the rise finished (not cancelled by stopping)
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
    humanoid.WalkSpeed = normalWalkSpeed
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
    -- Forget the previous character; its tweens and pose stop with it
    cancelTween()
    humanoid = nil
    normalHipHeight = nil
    meditationTrack = nil
    isLevitating = false

    local newHumanoid = character:WaitForChild("Humanoid")
    if player.Character ~= character then
        return -- Respawned again while waiting
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

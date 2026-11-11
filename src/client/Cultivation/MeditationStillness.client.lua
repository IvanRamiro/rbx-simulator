-- While a player cultivates they stay put: no walking and no jumping. The body itself is placed by
-- their realm's meditation idle (MeditationPoses): on the ground, or up on the air.
-- One who tries to walk or jump is told how to stand up (a new player, told by the next quest to jump, pressed Space and
-- nothing happened: found in a new-player run, 2026-11-11). At most once every HINT_EVERY seconds.
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(game:GetService("ReplicatedStorage"):WaitForChild("GameConfig"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))

local player = Players.LocalPlayer
local HINT_EVERY = 8
local hint = Toast.new("MeditationHint", nil, 3.5)
local hintedAt = -math.huge

local humanoid = nil
local normalWalkSpeed = nil
local isStill = false

local function hold()
    if isStill or not humanoid or humanoid.Health <= 0 then
        return
    end
    isStill = true
    normalWalkSpeed = humanoid.WalkSpeed
    humanoid.WalkSpeed = 0
    humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
end

local function release()
    if not isStill then
        return
    end
    isStill = false
    -- the rank may have changed while meditating, so prefer the current Qinggong run speed
    humanoid.WalkSpeed = player:GetAttribute("QinggongRunSpeed") or normalWalkSpeed
    humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, true)
end

local function update()
    if player:GetAttribute("IsCultivating") == true then
        hold()
    else
        release()
    end
end

local function onCharacterAdded(character)
    humanoid = nil
    isStill = false
    local newHumanoid = character:WaitForChild("Humanoid")
    if player.Character ~= character then
        return
    end
    humanoid = newHumanoid
    update()
end

local function nudge()
    if not isStill or os.clock() - hintedAt < HINT_EVERY then
        return
    end
    hintedAt = os.clock()
    local key = GameConfig.CultivationKeybind.Name
    hint:show(if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
        then "You're meditating: tap CULTIVATE to stand up first."
        else "You're meditating: press " .. key .. " (or click CULTIVATE) to stand up first.", "Info")
end
UserInputService.JumpRequest:Connect(nudge)
-- walking: the move keys and the thumbstick still set MoveDirection while WalkSpeed holds the body still
task.spawn(function()
    while true do
        task.wait(0.3)
        if isStill and humanoid and humanoid.MoveDirection.Magnitude > 0.5 then
            nudge()
        end
    end
end)

player:GetAttributeChangedSignal("IsCultivating"):Connect(update)
player.CharacterAdded:Connect(onCharacterAdded)

if player.Character then
    task.spawn(onCharacterAdded, player.Character)
end

-- While a player cultivates they stay put: no walking and no jumping. The body itself is placed by
-- their realm's meditation idle (MeditationPoses): on the ground, or up on the air.
local Players = game:GetService("Players")

local player = Players.LocalPlayer

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

player:GetAttributeChangedSignal("IsCultivating"):Connect(update)
player.CharacterAdded:Connect(onCharacterAdded)

if player.Character then
    task.spawn(onCharacterAdded, player.Character)
end

-- Players pass through each other, so a hacked client can't spin its character into others to fling
-- them off an island, or knock an egg out of a thief's arms.
local Players = game:GetService("Players")
local PhysicsService = game:GetService("PhysicsService")

local GROUP = "PlayerCharacters"

PhysicsService:RegisterCollisionGroup(GROUP)
PhysicsService:CollisionGroupSetCollidable(GROUP, GROUP, false)

local function setGroup(instance)
    if instance:IsA("BasePart") then
        instance.CollisionGroup = GROUP
    end
end

local function watchCharacter(character)
    for _, descendant in character:GetDescendants() do
        setGroup(descendant)
    end
    character.DescendantAdded:Connect(setGroup)
end

local function watchPlayer(player)
    player.CharacterAdded:Connect(watchCharacter)
    if player.Character then
        watchCharacter(player.Character)
    end
end

Players.PlayerAdded:Connect(watchPlayer)
for _, player in Players:GetPlayers() do
    watchPlayer(player)
end

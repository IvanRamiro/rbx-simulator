local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")

local IslandBuilder = require(script.Parent:WaitForChild("IslandBuilder"))
local IslandConfig = require(script.Parent:WaitForChild("IslandConfig"))

local function applyLighting(settings)
    Lighting.ClockTime = settings.ClockTime
    Lighting.Brightness = settings.Brightness
    Lighting.Ambient = settings.Ambient
    Lighting.OutdoorAmbient = settings.OutdoorAmbient

    local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
    for property, value in settings.Atmosphere do
        atmosphere[property] = value
    end
    atmosphere.Parent = Lighting
end

if IslandConfig.Lighting.Enabled then
    applyLighting(IslandConfig.Lighting)
end

local island = IslandBuilder.build(IslandConfig)
local spawnLocation = island:FindFirstChild("IslandSpawn", true)

for _, outerIsland in IslandConfig.OuterIslands do
    local settings = table.clone(IslandConfig)
    settings.Platform = nil
    settings.EggStands = nil
    settings.TrainingStation = nil
    settings.Lighting = nil
    for key, value in outerIsland do
        settings[key] = value
    end
    for _, key in { "Trees", "Rocks", "Crystals", "LavaPools", "FloatingFragments", "Hills", "EggStands" } do
        settings[key] = outerIsland[key]
    end
    IslandBuilder.build(settings)
end
local spawnCFrame = spawnLocation.CFrame + Vector3.new(0, 4, 0)
local fallResetY = IslandConfig.Center.Y - IslandConfig.Safety.FallResetDepth

local function returnToSpawn(character)
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    if not rootPart then
        return
    end

    rootPart.AssemblyLinearVelocity = Vector3.zero
    character:PivotTo(spawnCFrame)
end

local function useIslandSpawn(player)
    player.RespawnLocation = spawnLocation
end

Players.PlayerAdded:Connect(useIslandSpawn)

for _, player in Players:GetPlayers() do
    useIslandSpawn(player)

    if player.Character then
        returnToSpawn(player.Character)
    end
end

while true do
    task.wait(IslandConfig.Safety.CheckInterval)

    for _, player in Players:GetPlayers() do
        local character = player.Character
        local rootPart = character and character:FindFirstChild("HumanoidRootPart")
        if rootPart and rootPart.Position.Y < fallResetY and player:GetAttribute("IsFlying") ~= true then
            returnToSpawn(character)
        end
    end
end

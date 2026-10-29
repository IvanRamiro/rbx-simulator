
-- Builds the starting island once when the server starts, makes players
-- spawn on its platform, and brings back anyone who falls off.

local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")

local IslandBuilder = require(script.Parent:WaitForChild("IslandBuilder"))
local IslandConfig = require(script.Parent:WaitForChild("IslandConfig"))

local function applyLighting(settings)
    Lighting.ClockTime = settings.ClockTime
    Lighting.Brightness = settings.Brightness
    Lighting.Ambient = settings.Ambient
    Lighting.OutdoorAmbient = settings.OutdoorAmbient

    -- Reuse the place's Atmosphere if it has one, so there's never two
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

-- The outer sky islands share the starting island's settings unless they set their own
for _, outerIsland in IslandConfig.OuterIslands do
    local settings = table.clone(IslandConfig)
    settings.Platform = nil
    settings.EggStand = nil
    settings.TrainingStation = nil
    settings.Lighting = nil
    for key, value in outerIsland do
        settings[key] = value
    end
    -- Decorations it doesn't list are skipped, not copied from the starting island
    for _, key in { "Trees", "Rocks", "Crystals", "LavaPools", "FloatingFragments", "Hills", "EggStand" } do
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

-- Players always (re)spawn on the island, even if the place has other SpawnLocations
local function useIslandSpawn(player)
    player.RespawnLocation = spawnLocation
end

Players.PlayerAdded:Connect(useIslandSpawn)

for _, player in Players:GetPlayers() do
    useIslandSpawn(player)

    -- This player may have spawned before the island existed
    if player.Character then
        returnToSpawn(player.Character)
    end
end

-- Safety net: anyone who falls well below the island is brought back.
-- A short timed check (not every frame) is plenty for this.
while true do
    task.wait(IslandConfig.Safety.CheckInterval)

    for _, player in Players:GetPlayers() do
        local character = player.Character
        local rootPart = character and character:FindFirstChild("HumanoidRootPart")
        -- Flying players may explore below the island; they're caught if they fall after landing
        if rootPart and rootPart.Position.Y < fallResetY and player:GetAttribute("IsFlying") ~= true then
            returnToSpawn(character)
        end
    end
end

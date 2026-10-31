-- Spawning, fall safety and lighting for the floating-island world. Each island in
-- Workspace.FloatingIslands provides a "Checkpoint" part (the Starting Island uses its
-- "IslandSpawn"); a player who falls far below the island they last stood on returns there.
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")

local WorldConfig = require(script.Parent:WaitForChild("WorldConfig"))

local islandsFolder = workspace:WaitForChild(WorldConfig.FolderName)
local lastIsland = {}

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

local function checkpointOf(islandName)
    local island = islandsFolder:FindFirstChild(islandName)
    return island and (island:FindFirstChild("Checkpoint") or island:FindFirstChild("IslandSpawn"))
end

-- The built island whose footprint covers this position, if any.
local function islandAt(position)
    for name, island in WorldConfig.Islands do
        local offset = Vector2.new(position.X - island.Centre.X, position.Z - island.Centre.Z)
        if offset.Magnitude <= island.Radius * 1.3 and islandsFolder:FindFirstChild(name) then
            return name
        end
    end
    return nil
end

local function returnToCheckpoint(character, islandName)
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    local checkpoint = checkpointOf(islandName) or checkpointOf(WorldConfig.StartIsland)
    if rootPart and checkpoint then
        rootPart.AssemblyLinearVelocity = Vector3.zero
        character:PivotTo(checkpoint.CFrame + Vector3.new(0, 4, 0))
    end
end

local function setupPlayer(player)
    lastIsland[player] = WorldConfig.StartIsland
    -- RespawnLocation needs the SpawnLocation itself, never a plain checkpoint part
    player.RespawnLocation = islandsFolder[WorldConfig.StartIsland]:FindFirstChild("IslandSpawn")
end

applyLighting(WorldConfig.Lighting)
assert(islandsFolder:WaitForChild(WorldConfig.StartIsland):FindFirstChild("IslandSpawn"),
    "Workspace." .. WorldConfig.FolderName .. "." .. WorldConfig.StartIsland .. " has no IslandSpawn")

-- Lava and other hazards: touching one returns the player to their island's checkpoint.
local lastBurn = {}
local function watchHazard(part)
    part.Touched:Connect(function(hit)
        local character = hit.Parent
        local player = character and Players:GetPlayerFromCharacter(character)
        if player and os.clock() - (lastBurn[player] or 0) > 1 then
            lastBurn[player] = os.clock()
            returnToCheckpoint(character, lastIsland[player] or WorldConfig.StartIsland)
        end
    end)
end
CollectionService:GetInstanceAddedSignal(WorldConfig.HazardTag):Connect(watchHazard)
for _, part in CollectionService:GetTagged(WorldConfig.HazardTag) do
    watchHazard(part)
end

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastIsland[player] = nil
    lastBurn[player] = nil
end)
for _, player in Players:GetPlayers() do
    setupPlayer(player)
end

while true do
    task.wait(WorldConfig.Safety.CheckInterval)

    for _, player in Players:GetPlayers() do
        local character = player.Character
        local rootPart = character and character:FindFirstChild("HumanoidRootPart")
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if rootPart and humanoid and humanoid.Health > 0 then
            if humanoid.FloorMaterial ~= Enum.Material.Air then
                lastIsland[player] = islandAt(rootPart.Position) or lastIsland[player]
            end
            local island = WorldConfig.Islands[lastIsland[player]]
            local fellFar = rootPart.Position.Y < island.Centre.Y - WorldConfig.Safety.FallDepth
            if fellFar and player:GetAttribute("IsFlying") ~= true then
                returnToCheckpoint(character, lastIsland[player])
            end
        end
    end
end

-- Spawning, fall safety, bridge access and lighting for the floating-island world. Each island in
-- Workspace.FloatingIslands provides a "Checkpoint" part (the Starting Island uses its
-- "IslandSpawn"); a player who falls far below the island they last stood on returns there.
-- Bridges (FloatingIslands.Bridges, built by WorldBuilder.buildBridges) lead to the other islands;
-- a player below a bridge's RankId who is on it past its Qi barrier, or on the island it leads to,
-- is put back in front of the barrier.
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
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

-- Bridge access: each bridge's zones (the deck past its barrier), its rank and where to send back
-- anyone below it.
local bridges = {}
local zoneParams = OverlapParams.new()
zoneParams.FilterType = Enum.RaycastFilterType.Include
do
    local folder = islandsFolder:FindFirstChild("Bridges")
    local zones = {}
    for _, bridge in folder and folder:GetChildren() or {} do
        local rank = Ranks.getRankById(bridge:GetAttribute("RankId"))
        local zoneFolder = bridge:FindFirstChild("Zones")
        if rank and zoneFolder then
            local entry = { Model = bridge, Index = Ranks.getIndex(rank.Name), Island = bridge:GetAttribute("Island"), ReturnTo = bridge:GetAttribute("ReturnTo") }
            bridges[bridge] = entry
            for _, zone in zoneFolder:GetChildren() do
                table.insert(zones, zone)
            end
        end
    end
    zoneParams.FilterDescendantsInstances = zones
end

local function rankIndex(player)
    local leaderstats = player:FindFirstChild("leaderstats")
    local rank = leaderstats and leaderstats:FindFirstChild("Rank")
    return rank and Ranks.getIndex(rank.Value)
end

-- The bridge a player is trespassing on (or on whose island), if any.
local function trespass(player, position)
    local index = rankIndex(player)
    if not index then
        return nil
    end
    for _, zone in workspace:GetPartBoundsInRadius(position, 0.5, zoneParams) do
        local entry = bridges[zone.Parent.Parent]
        if entry and index < entry.Index then
            return entry
        end
    end
    local island = islandAt(position)
    for _, entry in bridges do
        if entry.Island == island and index < entry.Index then
            return entry
        end
    end
    return nil
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
            local blocked = trespass(player, rootPart.Position)
            if blocked and blocked.ReturnTo then
                rootPart.AssemblyLinearVelocity = Vector3.zero
                character:PivotTo(CFrame.lookAt(blocked.ReturnTo, blocked.ReturnTo - (blocked.Model.Gate.QiBarrier.Position - blocked.ReturnTo) * Vector3.new(1, 0, 1)))
                lastIsland[player] = WorldConfig.StartIsland
                continue
            end
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

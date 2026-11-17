-- Spawning, fall safety and bridge access for the floating islands (the lighting is WeatherService's). Each player spawns on their own pen's spawn pad
-- in the hub, facing the pen (the hub's redesign, 2026-11-15: PenService's PenSpawn attribute, the pasture's "Spawn"
-- SpawnLocation); a player without a pen (a seventh, or before their pen is given) spawns at Yggdrasil's "IslandSpawn" on the
-- Arrival Plaza. Every other island has a "Checkpoint" part; a player who falls far below the island they last stood on returns
-- to its checkpoint (on the hub: to their own pad). A player below a bridge's RankId
-- (FloatingIslands.Bridges) who is past its Qi barrier, or on the island it leads to (at any height: a flyer too), is put back
-- in front of the barrier and told why (the "LockedOutNotice" attribute; BridgeBarriers.client shows it). The barrier itself
-- (BridgeBarriers.client) only stops feet: this is the rule. (Yggdrasil's named spawn slots went with the hub's rebuild of 2026-11-12;
-- their code was removed 2026-11-13.) On the stepping stones up to the Blossom Sanctuary (its Approach), a fall returns the
-- player to the last platform they stood on (or the hub's end of the climb, or the island's landing), not to their pen.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local WorldConfig = require(script.Parent:WaitForChild("WorldConfig"))
local MovementGuard = require(script.Parent.Parent:WaitForChild("Security"):WaitForChild("MovementGuard"))

local islandsFolder = workspace:WaitForChild(WorldConfig.FolderName)
local lastIsland = {}
local lockedOutCount = {} -- [player] = how many times they were put back at a gate (sayLockedOut)

-- ---------- spawning ----------
local startIsland = islandsFolder:WaitForChild(WorldConfig.StartIsland)
assert(startIsland:FindFirstChild("IslandSpawn"), "Workspace." .. WorldConfig.FolderName .. "." .. WorldConfig.StartIsland .. " has no IslandSpawn")

local function checkpointOf(player, islandName)
    local island = islandsFolder:FindFirstChild(islandName)
    return island and (island:FindFirstChild("Checkpoint") or island:FindFirstChild("IslandSpawn"))
end

-- The pasture "Spawn" (a SpawnLocation on the player's pen's pad) if they hold a pen, else nil.
local function penSpawnOf(player)
    local index = player:GetAttribute("PastureIndex")
    local pastures = typeof(index) == "number" and index > 0 and startIsland:FindFirstChild("BeastPastures")
    local pasture = pastures and pastures:FindFirstChild("Pasture" .. index)
    local point = pasture and pasture:FindFirstChild("Spawn")
    return if point and point:IsA("SpawnLocation") then point else nil
end

-- The built island whose footprint covers this position, if any (Reach: how far an island's ground runs from its centre, where its
-- Radius alone would fall short; otherwise 1.3 Radius).
-- Where two reaches overlap (the hub's and the Beginner Isle's, by the Lion Gate), the island the point is relatively nearest wins.
local function islandAt(position)
    local best, bestRatio = nil, math.huge
    for name, island in WorldConfig.Islands do
        local offset = Vector2.new(position.X - island.Centre.X, position.Z - island.Centre.Z)
        local ratio = offset.Magnitude / (island.Reach or island.Radius * 1.3)
        if ratio <= 1 and ratio < bestRatio and islandsFolder:FindFirstChild(name) then
            best, bestRatio = name, ratio
        end
    end
    return best
end

-- Stands a character where a CFrame on the ground says, facing as it does (the root part 3 studs over the feet).
local function standAt(player, character, at)
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    if not rootPart then
        return
    end
    rootPart.AssemblyLinearVelocity = Vector3.zero
    local to = at + Vector3.new(0, 3.2, 0)
    MovementGuard.reset(player, to.Position)
    character:PivotTo(to)
end

local function returnToCheckpoint(player, character, islandName)
    -- on the hub, a player with a pen goes back to their own pad
    local pen = player:GetAttribute("PenSpawn")
    if islandName == WorldConfig.StartIsland and typeof(pen) == "CFrame" then
        standAt(player, character, pen + Vector3.new(0, 0.45, 0))
        return
    end
    local checkpoint = checkpointOf(player, islandName) or checkpointOf(player, WorldConfig.StartIsland)
    if checkpoint then
        standAt(player, character, checkpoint.CFrame + Vector3.new(0, 0.8, 0))
    end
end

-- the island a player was last on, also as their "Island" attribute (their client's music follows it)
local function setIsland(player, name)
    lastIsland[player] = name
    player:SetAttribute("Island", name)
end

-- When a player's pen is given (or taken), their respawn follows it; a character that has only just arrived at the Arrival Plaza
-- (their first, before PenService knew their pen) is moved to the pad at once.
local spawnedAt = {}
local function followPen(player)
    player.RespawnLocation = penSpawnOf(player) or startIsland.IslandSpawn
    local pen = player:GetAttribute("PenSpawn")
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if typeof(pen) == "CFrame" and rootPart and os.clock() - (spawnedAt[player] or 0) < 15
        and (rootPart.Position - startIsland.IslandSpawn.Position).Magnitude < 30 then
        standAt(player, character, pen + Vector3.new(0, 0.45, 0))
    end
end

local function setupPlayer(player)
    setIsland(player, WorldConfig.StartIsland)
    -- RespawnLocation needs the SpawnLocation itself, never a plain checkpoint part
    player.RespawnLocation = startIsland.IslandSpawn
    player:GetAttributeChangedSignal("PenSpawn"):Connect(function()
        followPen(player)
    end)
    player.CharacterAdded:Connect(function()
        spawnedAt[player] = os.clock()
    end)
    if player.Character then
        spawnedAt[player] = os.clock()
    end
    followPen(player)
end

-- Lava and other hazards: touching one returns the player to their island's checkpoint.
local lastBurn = {}
local function watchHazard(part)
    part.Touched:Connect(function(hit)
        local character = hit.Parent
        local player = character and Players:GetPlayerFromCharacter(character)
        if player and os.clock() - (lastBurn[player] or 0) > 1 then
            lastBurn[player] = os.clock()
            returnToCheckpoint(player, character, lastIsland[player] or WorldConfig.StartIsland)
        end
    end)
end
CollectionService:GetInstanceAddedSignal(WorldConfig.HazardTag):Connect(watchHazard)
for _, part in CollectionService:GetTagged(WorldConfig.HazardTag) do
    watchHazard(part)
end

-- Each bridge's zones (the deck past its barrier), its rank and where to send back anyone below it.
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

-- The Blossom Sanctuary's climb (WorldBuilder.buildApproach): a "Route" zone over every stone and platform, and a "Check" zone
-- (its ReturnTo a CFrame on the ground) on the hub's verge where it starts, on each platform and on the island's landing.
-- Standing in a Check remembers it; a player who last stood on the climb and drops ROUTE_FALL below where they stood goes back
-- to it. Standing anywhere off the climb forgets it.
local ROUTE_FALL = 25 -- (the climb's own drops are at most 4 studs)
local routeParams = OverlapParams.new()
routeParams.FilterType = Enum.RaycastFilterType.Include
do
    local zones = {}
    for _, island in islandsFolder:GetChildren() do
        local approach = island:FindFirstChild("Approach")
        local folder = approach and approach:FindFirstChild("Zones")
        for _, zone in folder and folder:GetChildren() or {} do
            table.insert(zones, zone)
        end
    end
    routeParams.FilterDescendantsInstances = zones
end
local onRoute = {} -- [player] = { standY = where they last stood on it, returnTo = the last Check's CFrame }

-- True if the player fell off the climb and was put back.
local function routeFall(player, character, rootPart, humanoid)
    local state = onRoute[player]
    if humanoid.FloorMaterial ~= Enum.Material.Air then
        local zones = workspace:GetPartBoundsInRadius(rootPart.Position, 0.5, routeParams)
        if #zones == 0 then
            onRoute[player] = nil
            return false
        end
        state = state or {}
        state.standY = rootPart.Position.Y
        for _, zone in zones do
            local returnTo = zone.Name == "Check" and zone:GetAttribute("ReturnTo")
            if typeof(returnTo) == "CFrame" then
                state.returnTo = returnTo
            end
        end
        onRoute[player] = state
        return false
    end
    if state and state.returnTo and rootPart.Position.Y < state.standY - ROUTE_FALL and player:GetAttribute("IsFlying") ~= true then
        standAt(player, character, state.returnTo)
        state.standY = state.returnTo.Position.Y
        return true
    end
    return false
end

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    onRoute[player] = nil
    lastIsland[player] = nil
    lastBurn[player] = nil
    spawnedAt[player] = nil
    lockedOutCount[player] = nil
end)
for _, player in Players:GetPlayers() do
    setupPlayer(player)
end

-- Tells a player put back at a gate why (BridgeBarriers.client shows it): "<count>|<words>", so the same gate twice still
-- changes the attribute.
local function sayLockedOut(player, entry)
    local rank = GameConfig.Ranks[entry.Index]
    local place = entry.Model:GetAttribute("Destination") or entry.Island
    lockedOutCount[player] = (lockedOutCount[player] or 0) + 1
    player:SetAttribute("LockedOutNotice", string.format("%d|Locked. Reach %s to go to %s.", lockedOutCount[player], rank.Name, tostring(place)))
end

local function checkPlayer(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if not (rootPart and humanoid and humanoid.Health > 0) then
        return
    end
    local blocked = trespass(player, rootPart.Position)
    if blocked and blocked.ReturnTo then
        local barrier = blocked.Model:FindFirstChild("Gate") and blocked.Model.Gate:FindFirstChild("QiBarrier")
        local facing = if barrier then (barrier.Position - blocked.ReturnTo) * Vector3.new(1, 0, 1) else Vector3.zero
        rootPart.AssemblyLinearVelocity = Vector3.zero
        MovementGuard.reset(player, blocked.ReturnTo)
        character:PivotTo(if facing.Magnitude > 0.1 then CFrame.lookAt(blocked.ReturnTo, blocked.ReturnTo - facing) else CFrame.new(blocked.ReturnTo))
        setIsland(player, WorldConfig.StartIsland)
        sayLockedOut(player, blocked)
        return
    end
    if routeFall(player, character, rootPart, humanoid) then
        return
    end
    if humanoid.FloorMaterial ~= Enum.Material.Air then
        setIsland(player, islandAt(rootPart.Position) or lastIsland[player] or WorldConfig.StartIsland)
    end
    local islandName = lastIsland[player] or WorldConfig.StartIsland
    local island = WorldConfig.Islands[islandName]
    local fellFar = rootPart.Position.Y < island.Centre.Y - WorldConfig.Safety.FallDepth
    if fellFar and player:GetAttribute("IsFlying") ~= true then
        returnToCheckpoint(player, character, islandName)
    end
end

-- Every player is checked on their own: one player's error (a character half-built, a player leaving mid-check) is logged
-- and skipped, and never stops the gates and the fall safety for the rest of the server's life, as an error in this loop
-- once would have.
local lastWarned = 0
while true do
    task.wait(WorldConfig.Safety.CheckInterval)

    for _, player in Players:GetPlayers() do
        local ok, err = pcall(checkPlayer, player)
        if not ok and os.clock() - lastWarned > 30 then
            lastWarned = os.clock()
            warn("WorldService: check failed for " .. player.Name .. ": " .. tostring(err))
        end
    end
end

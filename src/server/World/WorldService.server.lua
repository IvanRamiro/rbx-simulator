-- Spawning, fall safety, bridge access and lighting for the floating islands. Each player holds one
-- of Yggdrasil's spawn slots while in the server (its ring lit, their name on its stone) and spawns
-- there; with every slot taken they spawn at Yggdrasil's "IslandSpawn". Every other island has a
-- "Checkpoint" part; a player who falls far below the island they last stood on returns to its
-- checkpoint (on Yggdrasil, to their slot). A player below a bridge's RankId (FloatingIslands.Bridges)
-- who is past its Qi barrier, or on the island it leads to, is put back in front of the barrier.
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local WorldConfig = require(script.Parent:WaitForChild("WorldConfig"))
local MovementGuard = require(script.Parent.Parent:WaitForChild("Security"):WaitForChild("MovementGuard"))

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

-- ---------- spawn slots ----------
local startIsland = islandsFolder:WaitForChild(WorldConfig.StartIsland)
assert(startIsland:FindFirstChild("IslandSpawn"), "Workspace." .. WorldConfig.FolderName .. "." .. WorldConfig.StartIsland .. " has no IslandSpawn")
local slotRules = WorldConfig.SpawnSlots
local slots = {}
-- (the slots are optional: without them everyone spawns at the IslandSpawn. The hub's rebuild of 2026-11-12 removed them;
-- waiting for the folder here stalled the whole script and nobody spawned anywhere)
local slotFolder = startIsland:FindFirstChild(slotRules.FolderName)
for _, slot in if slotFolder then slotFolder:GetChildren() else {} do
    table.insert(slots, slot)
end
table.sort(slots, function(a, b)
    return a:GetAttribute("Slot") < b:GetAttribute("Slot")
end)
local slotOf = {}

local function paintSlot(slot, player)
    local labels = slot.Plaque:FindFirstChildOfClass("SurfaceGui")
    slot.Ring.Color = if player then slotRules.TakenColor else slotRules.VacantColor
    labels.Title.Text = if player then player.DisplayName else slotRules.VacantTitle
    labels.Subtitle.Text = if player then "@" .. player.Name else slotRules.VacantSubtitle
    labels.Subtitle.TextColor3 = slot.Ring.Color
end

local function holderOf(slot)
    for player, held in slotOf do
        if held == slot then
            return player
        end
    end
    return nil
end

local function claimSlot(player)
    for _, slot in slots do
        if not holderOf(slot) then
            slotOf[player] = slot
            paintSlot(slot, player)
            return slot
        end
    end
    return nil
end

local function releaseSlot(player)
    local slot = slotOf[player]
    slotOf[player] = nil
    if slot then
        paintSlot(slot, nil)
    end
end

for _, slot in slots do
    paintSlot(slot, nil)
end

local function checkpointOf(player, islandName)
    if islandName == WorldConfig.StartIsland and slotOf[player] then
        return slotOf[player].Spawn
    end
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

local function returnToCheckpoint(player, character, islandName)
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    local checkpoint = checkpointOf(player, islandName) or checkpointOf(player, WorldConfig.StartIsland)
    if rootPart and checkpoint then
        rootPart.AssemblyLinearVelocity = Vector3.zero
        MovementGuard.reset(player)
        character:PivotTo(checkpoint.CFrame + Vector3.new(0, 4, 0))
    end
end

-- the island a player was last on, also as their "Island" attribute (their client's music follows it)
local function setIsland(player, name)
    lastIsland[player] = name
    player:SetAttribute("Island", name)
end

local function setupPlayer(player)
    setIsland(player, WorldConfig.StartIsland)
    -- RespawnLocation needs the SpawnLocation itself, never a plain checkpoint part
    local slot = claimSlot(player)
    player.RespawnLocation = if slot then slot.Spawn else startIsland.IslandSpawn
end

applyLighting(WorldConfig.Lighting)

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

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastIsland[player] = nil
    lastBurn[player] = nil
    releaseSlot(player)
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
                MovementGuard.reset(player)
                character:PivotTo(CFrame.lookAt(blocked.ReturnTo, blocked.ReturnTo - (blocked.Model.Gate.QiBarrier.Position - blocked.ReturnTo) * Vector3.new(1, 0, 1)))
                setIsland(player, WorldConfig.StartIsland)
                continue
            end
            if humanoid.FloorMaterial ~= Enum.Material.Air then
                setIsland(player, islandAt(rootPart.Position) or lastIsland[player])
            end
            local island = WorldConfig.Islands[lastIsland[player]]
            local fellFar = rootPart.Position.Y < island.Centre.Y - WorldConfig.Safety.FallDepth
            if fellFar and player:GetAttribute("IsFlying") ~= true then
                returnToCheckpoint(player, character, lastIsland[player])
            end
        end
    end
end

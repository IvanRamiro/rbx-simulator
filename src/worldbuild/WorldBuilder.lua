-- Build-time only: run from Studio (edit mode) to (re)build Workspace.FloatingIslands from the
-- data that tools/blender/world exports. Never required by game scripts. Require a clone so
-- Studio's module cache never serves an old copy:
--
--   local WB = require(game.ServerStorage.WorldBuild.WorldBuilder:Clone())
--
-- Starting Island, from scratch (FBX files in assets/world/StartingIsland, imported by hand):
--   WB.clearTerrain("StartingIsland"); WB.buildTerrain("StartingIsland")
--   WB.seatImport("StartingIsland", workspace.StartingIsland_Underside, "SI_Anchor", "Underside")
--   WB.storeKit("StartingIsland", workspace.StartingIsland_Kit)
--   WB.storeKit("StartingIsland", workspace.StartingIsland_Props, "SI_PropsAnchor")
--   WB.storeKit("StartingIsland", workspace.StartingIsland_Nature, "SI_NatureAnchor")
--   -- each import uploads its own copy of an atlas; point every piece at one copy:
--   --   SI_RootShelf and SI_CradleFloor share the underside's texture (set TextureID by hand),
--   WB.shareTexture("StartingIsland", "SI_QiCompass", { nature piece names and "SI_SpringSpillway" })
--   WB.placeKit("StartingIsland"); WB.buildEggStands("StartingIsland"); WB.buildWaystones("StartingIsland")
--   WB.buildSpawn("StartingIsland"); WB.buildQiSpring("StartingIsland")
--   WB.buildRelic("StartingIsland", "IslandRoot", <Placements.StartingIsland.Relic>)
-- Collision fidelity applies asynchronously; confirm with WB.checkCollision in a later call.
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

-- cloned so edits to GameConfig are never served from Studio's require cache
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"):Clone())

local WorldBuilder = {}

local VOXEL = 4

-- Terrain material colours are global to the place, so every island uses its own materials.
WorldBuilder.MaterialColors = {
    -- Starting Island
    Grass = Color3.fromRGB(96, 158, 82),
    Ground = Color3.fromRGB(122, 96, 70),
    Rock = Color3.fromRGB(118, 120, 128),
    Cobblestone = Color3.fromRGB(168, 160, 146),
    -- Jade Grove
    LeafyGrass = Color3.fromRGB(64, 116, 58),
    Mud = Color3.fromRGB(86, 68, 50),
    Sandstone = Color3.fromRGB(98, 124, 108),
}

-- Per-island terrain settings: how deep the terrain shell reaches below the island centre (the
-- underside meshes take over below that) and which material sits under the surface layer.
WorldBuilder.TerrainSettings = {
    StartingIsland = { ShellDepth = 9, SubMaterial = "Ground", KeepThrough = { Rock = true } },
    -- deep enough for the Whispering Hollow (floor about -9)
    JadeGrove = { ShellDepth = 14, SubMaterial = "Mud", KeepThrough = { Sandstone = true } },
}

local function terrainData(island)
    -- clone so a re-exported data module is never served from Studio's require cache
    return require(ServerStorage.WorldBuild.Terrain:FindFirstChild(island):Clone())
end

function WorldBuilder.applyMaterialColors()
    for name, color in WorldBuilder.MaterialColors do
        workspace.Terrain:SetMaterialColor(Enum.Material[name], color)
    end
end

-- Clears the terrain inside an island's grid footprint (plus a margin), from below the shell
-- to well above the highest ground.
function WorldBuilder.clearTerrain(island)
    local data = terrainData(island)
    local span = data.Size * data.Cell
    local min = Vector3.new(data.Origin.X - 8, data.Centre.Y - 80, data.Origin.Y - 8)
    local max = Vector3.new(data.Origin.X + span + 8, data.Centre.Y + 120, data.Origin.Y + span + 8)
    workspace.Terrain:FillBlock(CFrame.new((min + max) / 2), max - min, Enum.Material.Air)
end

function WorldBuilder.buildTerrain(island)
    local data = terrainData(island)
    local settings = WorldBuilder.TerrainSettings[island]
    local materials = {}
    for index, name in data.Materials do
        materials[index] = Enum.Material[name]
    end
    local subMaterial = Enum.Material[settings.SubMaterial]

    local lowest, highest = math.huge, -math.huge
    for _, h in data.Heights do
        if h then
            lowest = math.min(lowest, h)
            highest = math.max(highest, h)
        end
    end
    local bottomY = data.Centre.Y - settings.ShellDepth
    local minY = math.floor(bottomY / VOXEL) * VOXEL
    for _, level in data.WaterLevels or {} do
        if level then
            highest = math.max(highest, level)
        end
    end
    local maxY = math.ceil((data.Centre.Y + highest) / VOXEL) * VOXEL + VOXEL
    local layers = (maxY - minY) / VOXEL

    -- one voxel column per grid cell; the grid is already aligned to 4-stud voxels
    local cellsPerVoxel = data.Cell / VOXEL
    assert(cellsPerVoxel == 1, "WorldBuilder expects 4-stud heightfield cells")
    local size = data.Size
    local matGrid, occGrid = {}, {}
    for i = 1, size do
        local matCol, occCol = {}, {}
        for k = 1, layers do
            matCol[k], occCol[k] = {}, {}
            for j = 1, size do
                matCol[k][j] = Enum.Material.Air
                occCol[k][j] = 0
            end
        end
        matGrid[i], occGrid[i] = matCol, occCol
    end

    local filled = 0
    for j = 1, size do
        for i = 1, size do
            local index = (j - 1) * size + i
            local h = data.Heights[index]
            if h then
                local top = data.Centre.Y + h
                local surface = materials[data.MaterialIndex[index]]
                local keep = settings.KeepThrough[data.Materials[data.MaterialIndex[index]]]
                local waterLevel = data.WaterLevels and data.WaterLevels[index]
                local waterTop = waterLevel and data.Centre.Y + waterLevel
                for k = 1, layers do
                    local y0 = minY + (k - 1) * VOXEL
                    if y0 + VOXEL > bottomY then
                        -- Roblox renders a voxel's surface between its centre (occupancy 0) and
                        -- the centre of the voxel above (occupancy 1), measured in Studio
                        local occupancy = math.clamp((top - y0 - VOXEL / 2) / VOXEL, 0, 1)
                        if occupancy > 0 then
                            matGrid[i][k][j] = if keep or y0 + VOXEL >= top - VOXEL then surface else subMaterial
                            occGrid[i][k][j] = occupancy
                            filled += 1
                        elseif waterTop and y0 + VOXEL / 2 < waterTop then
                            -- pool water fills the air above the bed up to the water surface
                            matGrid[i][k][j] = Enum.Material.Water
                            occGrid[i][k][j] = math.clamp((waterTop - y0 - VOXEL / 2) / VOXEL, 0, 1)
                        end
                    end
                end
            end
        end
    end

    local regionMin = Vector3.new(data.Origin.X, minY, data.Origin.Y)
    local region = Region3.new(regionMin, regionMin + Vector3.new(size * VOXEL, layers * VOXEL, size * VOXEL))
    workspace.Terrain:WriteVoxels(region, VOXEL, matGrid, occGrid)
    return filled
end

-- ---------- imported meshes ----------

-- Studio's FBX importer turns a model 180 degrees about Y relative to the Blender layout
-- (Blender x maps to Roblox -x), so every imported piece is turned back by this.
local IMPORT_TURN = CFrame.Angles(0, math.pi, 0)

-- Collision per mesh-name prefix (first match wins). Long curving roots need decomposition so
-- their hull doesn't swallow the ledges along them; rocks and flat ledges are simple shapes.
WorldBuilder.Collision = {
    { Prefix = "SI_PathRoot", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "SI_Slab", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_Boulder", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_RootShelf", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "SI_CradleFloor", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "SI_StoneLantern", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_Waystone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_LotusStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_MossRock", Fidelity = Enum.CollisionFidelity.Hull },
    -- Jade Grove: the hollow, the walk-under root and the gate opening must stay passable
    { Prefix = "JG_ElderTrunk", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "JG_ElderPads", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "JG_GroveGate", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "JG_TreeShelf", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "JG_RouteStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_StandingStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_WhisperStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_JadeLantern", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_JadeOutcrop", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_FallenLog", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_GladeFloor", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "JG_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "SI_", Fidelity = Enum.CollisionFidelity.Default },
}

-- Surface overrides per mesh-name prefix: glowing inlays are Neon (saturated colours, since
-- Neon blooms pale colours to white) and the spring surface is tinted glass. Pieces without
-- collision use Box fidelity so they cost nothing to the physics engine.
local GLOW = { Material = Enum.Material.Neon, CanCollide = false, CastShadow = false }
WorldBuilder.Appearance = {
    SI_QiCompassGlow = table.clone(GLOW),
    SI_LanternLight = table.clone(GLOW),
    SI_EggGlowRing = table.clone(GLOW),
    SI_WaystoneGlow = table.clone(GLOW),
    SI_SpringWater = { Material = Enum.Material.Glass, Transparency = 0.3, CanCollide = false, CastShadow = false },
    SI_FlowersWhite = { CanCollide = false },
    SI_FlowersWarm = { CanCollide = false },
    SI_FlowersViolet = { CanCollide = false },
    -- the terrain shell gives Jade Grove's cliffs their collision; a hull of this open-topped
    -- mass would put an invisible floor over the Whispering Hollow
    JG_Underside = { CanCollide = false },
    JG_UnderCrystals = { CanCollide = false },
    JG_MossCurtains = { CanCollide = false },
    JG_Vines = { CanCollide = false },
    JG_ElderCanopy = { CanCollide = false },
    JG_EggGlowRing = table.clone(GLOW),
    JG_JadeLanternLight = table.clone(GLOW),
    JG_MushroomCaps = table.clone(GLOW),
    JG_HollowWater = { Material = Enum.Material.Glass, Transparency = 0.3, CanCollide = false, CastShadow = false },
    JG_Mushrooms = { CanCollide = false },
    JG_Fern = { CanCollide = false },
    JG_BambooClump = { CanCollide = false },
}
WorldBuilder.Appearance.SI_QiCompassGlow.Color = Color3.fromRGB(40, 210, 235)
WorldBuilder.Appearance.SI_LanternLight.Color = Color3.fromRGB(255, 150, 60)
WorldBuilder.Appearance.SI_SpringWater.Color = Color3.fromRGB(40, 165, 180)
WorldBuilder.Appearance.JG_JadeLanternLight.Color = Color3.fromRGB(255, 175, 80) -- warm, so the forest isn't washed green
WorldBuilder.Appearance.JG_MushroomCaps.Color = Color3.fromRGB(30, 230, 200)
WorldBuilder.Appearance.JG_HollowWater.Color = Color3.fromRGB(35, 160, 130)

-- Kit pieces that carry a PointLight (lights take the piece's colour).
WorldBuilder.Lights = {
    SI_LanternLight = { Range = 16, Brightness = 1.2 },
    JG_JadeLanternLight = { Range = 16, Brightness = 1.0 },
}

local function prepareMesh(part)
    part.Anchored = true
    part.CanTouch = false
    part.Massless = true
    local look = WorldBuilder.Appearance[part.Name]
    if look then
        if look.Material then
            part.TextureID = "" -- Neon and Glass pieces are coloured, not textured
        end
        for property, value in look do
            part[property] = value
        end
        if look.CanCollide == false then
            part.CanQuery = false
        end
    end
end

local function collisionRule(part)
    for _, rule in WorldBuilder.Collision do
        if string.sub(part.Name, 1, #rule.Prefix) == rule.Prefix then
            return rule.Fidelity
        end
    end
    return nil
end

-- Applies the collision rules to every MeshPart under a container. Studio applies a new
-- CollisionFidelity asynchronously, so check the result with checkCollision in a later call.
function WorldBuilder.applyCollision(container)
    for _, part in container:GetDescendants() do
        local fidelity = part:IsA("MeshPart") and collisionRule(part)
        if fidelity then
            part.CollisionFidelity = if part.CanCollide then fidelity else Enum.CollisionFidelity.Box
        end
    end
end

-- Names of the MeshParts under a container whose collision does not match its rule.
function WorldBuilder.checkCollision(container)
    local wrong = {}
    for _, part in container:GetDescendants() do
        local fidelity = part:IsA("MeshPart") and collisionRule(part)
        if fidelity and not part.CanCollide then
            fidelity = Enum.CollisionFidelity.Box
        end
        if fidelity and part.CollisionFidelity ~= fidelity then
            table.insert(wrong, part.Name)
        end
    end
    return wrong
end

-- Workspace.FloatingIslands.<island> with one child folder per kind of content.
function WorldBuilder.islandFolder(island, child)
    local root = workspace:FindFirstChild("FloatingIslands") or Instance.new("Folder")
    root.Name = "FloatingIslands"
    root.Parent = workspace
    local model = root:FindFirstChild(island)
    if not model then
        model = Instance.new("Model")
        model.Name = island
        model.Parent = root
    end
    if not child then
        return model
    end
    local folder = model:FindFirstChild(child) or Instance.new("Folder")
    folder.Name = child
    folder.Parent = model
    return folder
end

local function islandCentre(island)
    return terrainData(island).Centre
end

-- Seats an imported island-mesh model (exported with an anchor cube at the island centre) into
-- FloatingIslands.<island>.<child>, replacing what was there, and removes the import model.
function WorldBuilder.seatImport(island, model, anchorName, child)
    local anchor = model:FindFirstChild(anchorName)
    assert(anchor, "import is missing its anchor " .. anchorName)
    local target = CFrame.new(islandCentre(island)) * IMPORT_TURN
    local folder = WorldBuilder.islandFolder(island, child)
    folder:ClearAllChildren()
    local frame = anchor.CFrame
    anchor:Destroy()
    for _, part in model:GetChildren() do
        if part:IsA("MeshPart") then
            part.CFrame = target * frame:ToObjectSpace(part.CFrame)
            prepareMesh(part)
            part.Parent = folder
        end
    end
    model:Destroy()
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- Moves the meshes of an imported kit model (exported at the Blender origin) into
-- ServerStorage.WorldKit.<island> as templates, each CFrame relative to its authored origin.
-- The origin is the anchor cube when the export has one, otherwise the model pivot.
function WorldBuilder.storeKit(island, model, anchorName)
    local kit = ServerStorage:FindFirstChild("WorldKit") or Instance.new("Folder")
    kit.Name = "WorldKit"
    kit.Parent = ServerStorage
    local folder = kit:FindFirstChild(island) or Instance.new("Folder")
    folder.Name = island
    folder.Parent = kit
    local anchor = anchorName and model:FindFirstChild(anchorName)
    local origin = if anchor then anchor.CFrame else model:GetPivot()
    if anchor then
        anchor:Destroy()
    end
    for _, part in model:GetChildren() do
        if part:IsA("MeshPart") then
            local old = folder:FindFirstChild(part.Name)
            if old then
                old:Destroy()
            end
            part.CFrame = IMPORT_TURN * origin:ToObjectSpace(part.CFrame)
            prepareMesh(part)
            part.Parent = folder
        end
    end
    model:Destroy()
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

local function placementsFor(island)
    return require(ServerStorage.WorldBuild.Placements:FindFirstChild(island):Clone())
end

local function template(island, name)
    local part = ServerStorage.WorldKit[island]:FindFirstChild(name)
    assert(part, "missing kit template " .. name .. " (import and store the island's kit first)")
    return part
end

-- Places a template so its authored origin lands on `frame`, optionally scaled about that origin.
local function placeTemplate(island, name, frame, parent, scale)
    local source = template(island, name)
    local part = source:Clone()
    scale = scale or 1
    part.Size = source.Size * scale
    part.CFrame = frame * (source.CFrame.Rotation + source.CFrame.Position * scale)
    part.Parent = parent
    return part
end

-- Points templates that were exported with the same atlas at one uploaded copy of it, so the
-- texture is loaded once (each FBX import uploads its own copy).
function WorldBuilder.shareTexture(island, sourceName, names)
    local folder = ServerStorage.WorldKit[island]
    local textureId = template(island, sourceName).TextureID
    for _, name in names do
        local part = folder:FindFirstChild(name)
        if part and part.TextureID ~= "" then
            part.TextureID = textureId
        end
    end
end

local function standFrame(island, entry)
    return CFrame.new(islandCentre(island) + entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
end

local function addLight(parent, color, range, brightness)
    local light = Instance.new("PointLight")
    light.Color = color
    light.Range = range
    light.Brightness = brightness
    light.Shadows = false
    light.Parent = parent
    return light
end

local function addSparkles(parent, color, rate)
    local sparkles = Instance.new("ParticleEmitter")
    sparkles.Color = ColorSequence.new(color)
    sparkles.LightEmission = 1
    sparkles.LightInfluence = 0
    sparkles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 0) })
    sparkles.Transparency = NumberSequence.new(0.2, 1)
    sparkles.Lifetime = NumberRange.new(1, 1.6)
    sparkles.Speed = NumberRange.new(0.5, 1.5)
    sparkles.SpreadAngle = Vector2.new(180, 180)
    sparkles.Rate = rate
    sparkles.Parent = parent
    return sparkles
end

-- Clones the kit templates to every Kit placement in Placements.<island>
-- (FloatingIslands.<island>.Kit). Lantern lights get their PointLight here.
function WorldBuilder.placeKit(island)
    local placements = placementsFor(island)
    local centre = CFrame.new(islandCentre(island))
    local folder = WorldBuilder.islandFolder(island, "Kit")
    folder:ClearAllChildren()
    local placed = 0
    for name, list in placements.Kit do
        for index, entry in list do
            local part = placeTemplate(island, name, centre * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0), folder, entry.Scale)
            part.Name = name .. "_" .. index
            local light = WorldBuilder.Lights[name]
            if light then
                addLight(part, part.Color, light.Range, light.Brightness)
            end
            placed += 1
        end
    end
    WorldBuilder.applyCollision(folder)
    return placed
end

-- ---------- egg stands ----------

-- Saturated glow colours per egg (Neon blooms pale colours to white).
WorldBuilder.EggGlow = {
    BeginnerQiEgg = Color3.fromRGB(50, 180, 255),
    SpiritBreezeEgg = Color3.fromRGB(30, 225, 165),
    ElementalCoreEgg = Color3.fromRGB(140, 80, 255),
    JadeSpiritEgg = Color3.fromRGB(40, 225, 120),
    BloomwoodEgg = Color3.fromRGB(255, 80, 180),
    AncientGroveEgg = Color3.fromRGB(170, 240, 40),
}

local EGG_STUDS_PER_UNIT = 1.3

-- Places the egg mesh from ServerStorage.EggMeshes resting on `bottom`, facing `facing`.
local function placeEgg(stand, eggId, bottom, facing)
    local folder = ServerStorage:FindFirstChild("EggMeshes")
    local source = folder and folder:FindFirstChild(eggId)
    assert(source and source:IsA("Model"), "missing egg mesh ServerStorage.EggMeshes." .. eggId)
    local boxCFrame, boxSize = source:GetBoundingBox()
    local centre = bottom + Vector3.new(0, boxSize.Y * EGG_STUDS_PER_UNIT / 2, 0)
    local placement = CFrame.lookAt(centre, centre + Vector3.new(facing.X, 0, facing.Z))
    local primary
    for _, original in source:GetDescendants() do
        if original:IsA("BasePart") then
            local part = original:Clone()
            local hex = string.match(original.Name, "_Glow_(%x%x%x%x%x%x)$")
            for _, child in part:GetChildren() do
                if hex or not child:IsA("SurfaceAppearance") then
                    child:Destroy()
                end
            end
            if hex then
                part.Color = Color3.fromHex(hex)
                part.Material = Enum.Material.Neon
                if part:IsA("MeshPart") then
                    part.TextureID = ""
                end
            end
            local relative = boxCFrame:ToObjectSpace(original.CFrame)
            part.Size = original.Size * EGG_STUDS_PER_UNIT
            part.CFrame = placement * (relative.Rotation + relative.Position * EGG_STUDS_PER_UNIT)
            part.Anchored = true
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
            part.CastShadow = false
            part.Parent = stand
            if not hex and not primary then
                primary = part
            end
        end
    end
    primary.Name = "Egg"
    return primary
end

function WorldBuilder.buildEggStands(island)
    local placements = placementsFor(island)
    local pieces = placements.EggStandPieces or { Pedestal = "SI_EggPedestal", GlowRing = "SI_EggGlowRing" }
    local folder = WorldBuilder.islandFolder(island, "EggStands")
    folder:ClearAllChildren()
    for _, entry in placements.EggStands do
        local eggConfig = GameConfig.Eggs[entry.EggId]
        local glow = WorldBuilder.EggGlow[entry.EggId]
        assert(eggConfig and glow, "unknown egg " .. entry.EggId)
        local frame = standFrame(island, entry)

        local stand = Instance.new("Model")
        stand.Name = entry.EggId
        stand:SetAttribute("EggId", entry.EggId)
        stand.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
        local pedestal = placeTemplate(island, pieces.Pedestal, frame, stand)
        pedestal.Name = "Pedestal"
        local ring = placeTemplate(island, pieces.GlowRing, frame, stand)
        ring.Name = "GlowRing"
        ring.Color = glow

        local egg = placeEgg(stand, entry.EggId, frame.Position + Vector3.new(0, entry.EggRest, 0), frame.LookVector * -1)
        addLight(egg, glow, 12, 1.2)
        addSparkles(egg, glow, 4)

        local prompt = Instance.new("ProximityPrompt")
        prompt.ActionText = "Hatch"
        prompt.ObjectText = eggConfig.DisplayName
        prompt.KeyboardKeyCode = Enum.KeyCode.F
        prompt.HoldDuration = 1
        prompt.MaxActivationDistance = 10
        prompt.RequiresLineOfSight = false
        prompt.Parent = pedestal

        CollectionService:AddTag(stand, GameConfig.EggTag)
        stand.Parent = folder
    end
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- ---------- route waystones ----------

-- Where each waystone points: the destination, the rank whose air leaps reach it, and its glow.
WorldBuilder.Waystones = {
    JadeRoute = { Title = "Jade Grove", RankId = "QiGatherer", Color = Color3.fromRGB(40, 215, 110) },
    EmberRoute = { Title = "Ember Peak", RankId = "QiAwakener", Color = Color3.fromRGB(255, 105, 25) },
    MoonlitRoute = { Title = "Moonlit Isle", RankId = "FoundationInitiate", Color = Color3.fromRGB(120, 100, 255) },
    OriginRoute = { Title = "Origin Abyss", RankId = "DivineInitiate", Color = Color3.fromRGB(175, 45, 255) },
    RootPath = { Title = "Root of the Island", Subtitle = "Climb down the great root", Color = Color3.fromRGB(255, 170, 40) },
}

local function rankLine(rankId)
    local rankName, leaps
    for _, rank in GameConfig.Ranks do
        if rank.Id == rankId then
            rankName = rank.Name
        end
    end
    for _, level in GameConfig.Qinggong.Levels do
        if level.RankId == rankId then
            leaps = level.AirLeaps
        end
    end
    assert(rankName and leaps, "no rank or Qinggong level for " .. rankId)
    return string.format("%s\n%d air leaps", rankName, leaps)
end

local function inscribe(parent, panel, title, subtitle, color)
    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Back -- the panel part's +Z face, the stele's front
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = 60
    gui.LightInfluence = 0.4
    gui.MaxDistance = 90
    gui.Parent = panel
    local layout = Instance.new("UIListLayout")
    layout.FillDirection = Enum.FillDirection.Vertical
    layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
    layout.VerticalAlignment = Enum.VerticalAlignment.Center
    layout.Padding = UDim.new(0, 14)
    layout.Parent = gui
    for index, line in { { title, 0.55, Enum.Font.Garamond, Color3.fromRGB(240, 222, 170) }, { subtitle, 0.3, Enum.Font.Garamond, color } } do
        local label = Instance.new("TextLabel")
        label.LayoutOrder = index
        label.Size = UDim2.fromScale(0.94, line[2])
        label.BackgroundTransparency = 1
        label.Font = line[3]
        label.TextScaled = true
        label.TextWrapped = true
        label.TextColor3 = line[4]
        label.Text = line[1]
        label.Parent = gui
    end
    return gui
end

function WorldBuilder.buildWaystones(island)
    local placements = placementsFor(island)
    local folder = WorldBuilder.islandFolder(island, "Waystones")
    folder:ClearAllChildren()
    for _, entry in placements.Waystones do
        local info = WorldBuilder.Waystones[entry.Route]
        assert(info, "no waystone info for " .. entry.Route)
        local frame = standFrame(island, entry)
        local model = Instance.new("Model")
        model.Name = "Waystone_" .. entry.Route
        model:SetAttribute("Route", entry.Route)
        placeTemplate(island, "SI_Waystone", frame, model).Name = "Stele"
        local glow = placeTemplate(island, "SI_WaystoneGlow", frame, model)
        glow.Name = "Glow"
        glow.Color = info.Color
        addLight(glow, info.Color, 10, 0.8)

        local panel = Instance.new("Part")
        panel.Name = "Inscription"
        panel.Size = Vector3.new(placements.WaystonePanel.Size.X, placements.WaystonePanel.Size.Y, 0.05)
        panel.CFrame = frame * CFrame.new(placements.WaystonePanel.Centre)
        panel.Transparency = 1
        panel.Anchored = true
        panel.CanCollide = false
        panel.CanQuery = false
        panel.CanTouch = false
        panel.Parent = model
        inscribe(model, panel, info.Title, info.Subtitle or rankLine(info.RankId), info.Color)
        model.Parent = folder
    end
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- ---------- spawn, Qi Spring, relic ----------

local function marker(name, size, cframe, parent)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size
    part.CFrame = cframe
    part.Transparency = 1
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.Parent = parent
    return part
end

function WorldBuilder.buildSpawn(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("IslandSpawn")
    if old then
        old:Destroy()
    end
    local spawn = Instance.new("SpawnLocation")
    spawn.Name = "IslandSpawn"
    spawn.Size = Vector3.new(6, 1, 6)
    spawn.CFrame = CFrame.new(islandCentre(island) + placements.Spawn + Vector3.new(0, 0.5, 0))
    spawn.Transparency = 1
    spawn.Anchored = true
    spawn.CanCollide = false
    spawn.CanQuery = false
    spawn.Neutral = true
    spawn.Duration = 0
    for _, child in spawn:GetChildren() do
        child:Destroy() -- the default decal
    end
    spawn.Parent = model
    return spawn
end

function WorldBuilder.buildQiSpring(island)
    local placements = placementsFor(island)
    local stationRules = GameConfig.TrainingStation
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("QiSpring")
    if old then
        old:Destroy()
    end
    local glow = Color3.fromRGB(40, 210, 235)
    local station = Instance.new("Model")
    station.Name = "QiSpring"

    -- QiService measures the cultivation radius from this part
    local centre = islandCentre(island) + placements.SpringCentre
    local water = marker("SpringWater", Vector3.new(2, 0.2, 2), CFrame.new(centre), station)
    addLight(water, glow, 22, 0.9)

    -- Qi motes rising off the whole pool
    local mist = marker("QiMotes", Vector3.new(stationRules.Radius * 1.6, 0.2, stationRules.Radius * 1.6), CFrame.new(centre + Vector3.new(0, 0.3, 0)), station)
    local motes = Instance.new("ParticleEmitter")
    motes.Shape = Enum.ParticleEmitterShape.Box
    motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    motes.EmissionDirection = Enum.NormalId.Top
    motes.Color = ColorSequence.new(glow, Color3.fromRGB(150, 245, 255))
    motes.LightEmission = 0.8
    motes.LightInfluence = 0
    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.2, 0.22), NumberSequenceKeypoint.new(1, 0) })
    motes.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
    motes.Lifetime = NumberRange.new(2.5, 4)
    motes.Speed = NumberRange.new(0.8, 1.6)
    motes.SpreadAngle = Vector2.new(12, 12)
    motes.Rate = 10
    motes.Parent = mist

    local sign = Instance.new("BillboardGui")
    sign.Name = "Sign"
    sign.Size = UDim2.fromOffset(240, 56)
    sign.StudsOffsetWorldSpace = Vector3.new(0, 9, 0)
    sign.MaxDistance = 80
    sign.LightInfluence = 0
    sign.Parent = water
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.TextColor3 = Color3.fromRGB(150, 245, 255)
    label.TextStrokeTransparency = 0.4
    label.Text = stationRules.DisplayName .. "\nCultivate here: +" .. stationRules.QiBonusPercent .. "% Qi"
    label.Parent = sign

    WorldBuilder.buildWaterfall(station, islandCentre(island) + placements.SpillEnd, centre)
    station.Parent = model
    return station
end

-- Seamless vertical streaks (assets/world/StartingIsland/waterfall_streaks.png).
WorldBuilder.WaterfallTexture = "rbxassetid://84166602047979"

-- Water pouring off a lip: a short arc then a long fall that fades into the sky, with a wider
-- faint sheen layer scrolling at a different speed for depth, and mist drifting off the fall.
function WorldBuilder.buildWaterfall(parent, lip, from)
    local out = Vector3.new(lip.X - from.X, 0, lip.Z - from.Z).Unit
    local holder = marker("Waterfall", Vector3.new(1, 1, 1), CFrame.new(lip), parent)
    local function attach(name, offset)
        local a = Instance.new("Attachment")
        a.Name = name
        a.Parent = holder -- parent first: WorldPosition on an unparented attachment is taken as local
        a.WorldPosition = lip + offset
        return a
    end
    local top = attach("Lip", out * 0.4)
    local bend = attach("Bend", out * 3.2 + Vector3.new(0, -5, 0))
    local bottom = attach("Bottom", out * 5.5 + Vector3.new(0, -52, 0))

    local function beam(name, a0, a1, w0, w1, transparency, speed, length)
        local b = Instance.new("Beam")
        b.Name = name
        b.Attachment0, b.Attachment1 = a0, a1
        b.Width0, b.Width1 = w0, w1
        b.FaceCamera = true
        b.Texture = WorldBuilder.WaterfallTexture
        b.TextureMode = Enum.TextureMode.Wrap
        b.TextureLength = length
        b.TextureSpeed = speed
        b.Transparency = transparency
        b.Color = ColorSequence.new(Color3.fromRGB(205, 240, 250))
        b.LightEmission = 0.25
        b.LightInfluence = 0.7
        b.Segments = 12
        b.Parent = holder
        return b
    end
    beam("LipCore", top, bend, 2.4, 2.6, NumberSequence.new(0.05, 0.1), 1.6, 4)
    beam("FallCore", bend, bottom, 2.6, 4.2, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.45, 0.3), NumberSequenceKeypoint.new(1, 1) }), 1.6, 6)
    beam("FallSheen", bend, bottom, 3.6, 6.5, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.5, 0.7), NumberSequenceKeypoint.new(1, 1) }), 2.3, 9)

    local mistAt = attach("Mist", out * 4.5 + Vector3.new(0, -16, 0))
    local mist = Instance.new("ParticleEmitter")
    mist.Name = "Mist"
    mist.Texture = "rbxasset://textures/particles/smoke_main.dds"
    mist.Color = ColorSequence.new(Color3.fromRGB(225, 245, 255))
    mist.LightInfluence = 0.6
    mist.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 2), NumberSequenceKeypoint.new(1, 7) })
    mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.82), NumberSequenceKeypoint.new(1, 1) })
    mist.Lifetime = NumberRange.new(3, 5)
    mist.Speed = NumberRange.new(1, 2.5)
    mist.SpreadAngle = Vector2.new(60, 60)
    mist.EmissionDirection = Enum.NormalId.Bottom
    mist.Rotation = NumberRange.new(0, 360)
    mist.RotSpeed = NumberRange.new(-15, 15)
    mist.Rate = 5
    mist.Parent = mistAt

    local spray = Instance.new("ParticleEmitter")
    spray.Name = "LipSpray"
    spray.Color = ColorSequence.new(Color3.fromRGB(230, 250, 255))
    spray.LightEmission = 0.3
    spray.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18), NumberSequenceKeypoint.new(1, 0) })
    spray.Transparency = NumberSequence.new(0.2, 1)
    spray.Lifetime = NumberRange.new(0.5, 0.9)
    spray.Speed = NumberRange.new(2, 4)
    spray.SpreadAngle = Vector2.new(35, 35)
    spray.Acceleration = Vector3.new(0, -20, 0)
    spray.Rate = 14
    spray.Parent = bend
    return holder
end

WorldBuilder.Relics = {
    IslandRoot = { Color = Color3.fromRGB(255, 165, 40) },
    GroveHeart = { Color = Color3.fromRGB(40, 230, 120) },
    JadeSeed = { Color = Color3.fromRGB(150, 255, 60) },
    WhisperingSpring = { Color = Color3.fromRGB(40, 220, 210) },
}

-- Where WorldService returns a player who falls from this island (Placements.<island>.Checkpoint).
function WorldBuilder.buildCheckpoint(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("Checkpoint")
    if old then
        old:Destroy()
    end
    return marker("Checkpoint", Vector3.new(4, 1, 4), CFrame.new(islandCentre(island) + placements.Checkpoint), model)
end

-- Builds every relic listed in Placements.<island>.Relics.
function WorldBuilder.buildRelics(island)
    local placements = placementsFor(island)
    local count = 0
    for relicId, position in placements.Relics do
        WorldBuilder.buildRelic(island, relicId, position)
        count += 1
    end
    return count
end

function WorldBuilder.buildRelic(island, relicId, localPosition)
    local relicConfig
    for _, relic in GameConfig.Relics do
        if relic.Id == relicId then
            relicConfig = relic
        end
    end
    local look = WorldBuilder.Relics[relicId]
    assert(relicConfig and look, "unknown relic " .. relicId)
    local folder = WorldBuilder.islandFolder(island, "Relics")
    local old = folder:FindFirstChild("Relic_" .. relicId)
    if old then
        old:Destroy()
    end
    local model = Instance.new("Model")
    model.Name = "Relic_" .. relicId
    local crystal = Instance.new("Part")
    crystal.Name = "RelicCrystal"
    crystal.Size = Vector3.new(1.6, 1.6, 1.6)
    crystal.CFrame = CFrame.new(islandCentre(island) + localPosition) * CFrame.Angles(0, math.rad(45), math.rad(45))
    crystal.Material = Enum.Material.Neon
    crystal.Color = look.Color
    crystal.Anchored = true
    crystal.CanCollide = false
    crystal.CanTouch = false
    crystal.Parent = model
    addLight(crystal, look.Color, 16, 1.5)
    addSparkles(crystal, look.Color, 6).Name = "RelicSparkles"

    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Attune"
    prompt.ObjectText = relicConfig.DisplayName
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 1
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt.Parent = crystal

    model:SetAttribute("RelicId", relicId)
    model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
    CollectionService:AddTag(model, GameConfig.RelicTag)
    model.Parent = folder
    return model
end

return WorldBuilder

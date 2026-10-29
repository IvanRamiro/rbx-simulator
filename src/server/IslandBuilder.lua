
-- Builds the starting floating island from terrain and simple anchored parts.
-- Everything uses a fixed random seed, so the island looks the same on every
-- server. All settings live in IslandConfig.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local IslandBuilder = {}

local terrain = workspace.Terrain

-- Cylinder parts point along their X axis; this turns them upright
local UPRIGHT = CFrame.Angles(0, 0, math.rad(90))
local FULL_TURN = 2 * math.pi

-- Part helpers -------------------------------------------------------------

local function createFolder(parent, name)
    local folder = Instance.new("Folder")
    folder.Name = name
    folder.Parent = parent
    return folder
end

local function createPart(parent, name, size, cframe, material, color)
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.CanTouch = false
    part.Size = size
    part.CFrame = cframe
    part.Material = material
    part.Color = color
    part.TopSurface = Enum.SurfaceType.Smooth
    part.BottomSurface = Enum.SurfaceType.Smooth
    part.Parent = parent
    return part
end

-- An upright cylinder: a flat disc when short, a trunk or post when tall
local function createCylinder(parent, name, diameter, height, position, material, color)
    local size = Vector3.new(height, diameter, diameter)
    local cylinder = createPart(parent, name, size, CFrame.new(position) * UPRIGHT, material, color)
    cylinder.Shape = Enum.PartType.Cylinder
    return cylinder
end

local function createBall(parent, name, diameter, position, material, color)
    local ball = createPart(parent, name, Vector3.one * diameter, CFrame.new(position), material, color)
    ball.Shape = Enum.PartType.Ball
    return ball
end

local function createLight(parent, color, range, brightness)
    local light = Instance.new("PointLight")
    light.Color = color
    light.Range = range
    light.Brightness = brightness
    light.Shadows = false
    light.Parent = parent
end

-- Placement helpers --------------------------------------------------------

-- Picks a spot between minDistance and maxDistance from the centre that is at
-- least `spacing` studs from every spot in `taken`, and outside every
-- { Position, Radius } area in `blockedAreas` (optional). Gives up after a
-- fixed number of tries and returns nil, so it can never loop forever.
local function pickSpot(random, center, minDistance, maxDistance, taken, spacing, blockedAreas)
    for _ = 1, 30 do
        local angle = random:NextNumber(0, FULL_TURN)
        local distance = random:NextNumber(minDistance, maxDistance)
        local spot = center + Vector3.new(math.cos(angle) * distance, 0, math.sin(angle) * distance)

        local isClear = true
        for _, otherSpot in taken do
            if (spot - otherSpot).Magnitude < spacing then
                isClear = false
                break
            end
        end

        for _, area in blockedAreas or {} do
            if (spot - area.Position).Magnitude < area.Radius then
                isClear = false
                break
            end
        end

        if isClear then
            table.insert(taken, spot)
            return spot
        end
    end

    return nil
end

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Include
groundParams.FilterDescendantsInstances = { terrain }

-- Returns the point on the island's terrain surface at this spot, or nil
local function findGround(spot)
    local result = workspace:Raycast(spot + Vector3.new(0, 50, 0), Vector3.new(0, -100, 0), groundParams)
    return result and result.Position
end

-- A feature's fixed spot on the grass surface (before finding the exact
-- ground). `settings` is a config entry with Distance and AngleDegrees.
local function getFeatureSpot(config, settings)
    local angle = math.rad(settings.AngleDegrees)
    return config.Center + Vector3.new(math.cos(angle) * settings.Distance, 0, math.sin(angle) * settings.Distance)
end

-- Areas kept clear for the egg stand and the training station, each widened by `margin`
local function getFeatureAreas(config, margin)
    local areas = {}
    for _, settings in { config.BeginnerEgg, config.TrainingStation } do
        table.insert(areas, { Position = getFeatureSpot(config, settings), Radius = settings.ClearRadius + margin })
    end
    return areas
end

-- Picks a decoration spot on the island (away from the egg stand and the
-- training station) and returns its ground position
local function pickGroundSpot(random, config, taken)
    local spot = pickSpot(
        random,
        config.Center,
        config.DecorationClearRadius,
        config.Radius - config.EdgeMargin,
        taken,
        config.DecorationSpacing,
        getFeatureAreas(config, 0)
    )
    return spot and findGround(spot)
end

-- Island body (terrain) ----------------------------------------------------

local function buildBody(config, random)
    local center = config.Center
    local radius = config.Radius

    for material, color in config.TerrainColors do
        terrain:SetMaterialColor(material, color)
    end

    -- Grass on top, with its upper surface at Center.Y, and soil underneath
    local grassMiddle = center - Vector3.new(0, config.GrassDepth / 2, 0)
    terrain:FillCylinder(CFrame.new(grassMiddle), config.GrassDepth, radius, Enum.Material.Grass)

    local soilMiddle = center - Vector3.new(0, config.GrassDepth + config.SoilDepth / 2, 0)
    terrain:FillCylinder(CFrame.new(soilMiddle), config.SoilDepth, radius - 2, Enum.Material.Ground)

    -- Rocky underside: rings of rock that shrink as they go down, with
    -- boulders around each ring so the edge looks uneven and natural
    local undersideTop = center.Y - config.GrassDepth - config.SoilDepth
    local layerHeight = config.UndersideDepth / config.UndersideLayers

    for layer = 1, config.UndersideLayers do
        local progress = layer / config.UndersideLayers -- Near 0 at the top, 1 at the bottom
        local layerRadius = math.max(4, (radius - 4) * (1 - progress) ^ 0.7)
        local layerY = undersideTop - progress * config.UndersideDepth
        local material = if layer % 2 == 0 then Enum.Material.Slate else Enum.Material.Rock

        terrain:FillCylinder(CFrame.new(center.X, layerY, center.Z), layerHeight + 2, layerRadius, material)

        local boulderCount = math.clamp(math.floor(layerRadius / 8), 3, 12)
        for boulder = 1, boulderCount do
            local angle = boulder / boulderCount * FULL_TURN + random:NextNumber(-0.3, 0.3)
            local distance = layerRadius * random:NextNumber(0.75, 0.95)
            local boulderRadius = random:NextNumber(4, 8) * (1 - progress * 0.5)
            local position = Vector3.new(
                center.X + math.cos(angle) * distance,
                layerY + random:NextNumber(-2, 2),
                center.Z + math.sin(angle) * distance
            )
            terrain:FillBall(position, boulderRadius, material)
        end
    end

    -- A pointed tip at the very bottom
    local bottomY = undersideTop - config.UndersideDepth
    for step = 1, 3 do
        local position = Vector3.new(center.X, bottomY - step * 4, center.Z)
        terrain:FillBall(position, 6 - step * 1.2, Enum.Material.Rock)
    end
end

-- Gentle grassy bumps, built before decorations so they sit on top of them
local function buildHills(config, random)
    local settings = config.Hills
    local taken = {}
    -- Keep the ground flat around the egg stand and the training station
    local featureAreas = getFeatureAreas(config, settings.MaxRadius)

    for _ = 1, settings.Count do
        local spot = pickSpot(random, config.Center, config.DecorationClearRadius + 10, config.Radius - 15, taken, 25, featureAreas)
        if spot then
            local hillRadius = random:NextNumber(settings.MinRadius, settings.MaxRadius)
            -- Mostly buried, so only a low bump shows above the surface
            terrain:FillBall(spot - Vector3.new(0, hillRadius * 0.75, 0), hillRadius, Enum.Material.Grass)
        end
    end
end

-- Platform -----------------------------------------------------------------

local function buildPlatform(island, config)
    local settings = config.Platform
    local center = config.Center
    local folder = createFolder(island, "Platform")

    -- Three stacked discs: stone base, glowing ring, and floor. Each is a
    -- little taller than the last so their tops don't flicker against each other.
    local baseHeight = 3
    local discCenter = center + Vector3.new(0, 1 - baseHeight / 2, 0) -- Base top is 1 stud above the grass
    createCylinder(folder, "Base", settings.Diameter, baseHeight, discCenter, settings.BaseMaterial, settings.BaseColor)
    createCylinder(folder, "QiRing", settings.Diameter - 6, baseHeight + 0.1, discCenter, Enum.Material.Neon, settings.RingColor)
    createCylinder(folder, "Floor", settings.Diameter - 7.5, baseHeight + 0.2, discCenter, settings.FloorMaterial, settings.FloorColor)
    local floorTopY = discCenter.Y + (baseHeight + 0.2) / 2

    -- Lantern posts on the stone rim
    local lanternDistance = settings.Diameter / 2 - 1.5
    for lantern = 1, settings.LanternCount do
        local angle = (lantern - 0.5) / settings.LanternCount * FULL_TURN
        local postBottom = center + Vector3.new(math.cos(angle) * lanternDistance, 1, math.sin(angle) * lanternDistance)

        local postCFrame = CFrame.new(postBottom + Vector3.new(0, 3, 0))
        createPart(folder, "LanternPost", Vector3.new(1.6, 6, 1.6), postCFrame, settings.BaseMaterial, settings.BaseColor)

        local lampCFrame = CFrame.new(postBottom + Vector3.new(0, 6.8, 0)) * CFrame.Angles(math.rad(45), math.rad(45), 0)
        local lamp = createPart(folder, "Lantern", Vector3.new(1.3, 1.3, 1.3), lampCFrame, Enum.Material.Neon, settings.LanternColor)
        createLight(lamp, settings.LanternColor, 16, 1.2)
    end

    -- Invisible spawn point in the middle of the floor
    local spawnLocation = Instance.new("SpawnLocation")
    spawnLocation.Name = "IslandSpawn"
    spawnLocation.Anchored = true
    spawnLocation.CanCollide = false
    spawnLocation.CanTouch = false
    spawnLocation.Transparency = 1
    spawnLocation.Neutral = true
    spawnLocation.Duration = 0 -- No spawn force field
    spawnLocation.Size = Vector3.new(8, 1, 8)
    spawnLocation.CFrame = CFrame.new(center.X, floorTopY - 0.5, center.Z)
    spawnLocation.Parent = folder
end

-- Qi Spring training station -------------------------------------------------

-- A round pool of glowing spring water in a stone basin, ringed by four
-- pillars. Cultivating while standing in the water earns extra Qi; QiService
-- measures the distance from the "SpringWater" part's centre.
local function buildTrainingStation(island, config)
    local settings = config.TrainingStation
    local stationRules = GameConfig.TrainingStation
    local spot = getFeatureSpot(config, settings)
    local ground = findGround(spot) or spot
    local waterDiameter = stationRules.Radius * 2

    local station = Instance.new("Model")
    station.Name = settings.ModelName

    -- Stone basin with the water just inside its rim, both walkable
    local baseCenter = ground + Vector3.new(0, 0.25, 0)
    createCylinder(station, "Basin", waterDiameter + 4, 1.5, baseCenter, config.Platform.BaseMaterial, config.Platform.BaseColor)
    local water = createCylinder(station, "SpringWater", waterDiameter, 1.6, baseCenter, Enum.Material.Neon, settings.WaterColor)
    water.Transparency = 0.15
    createLight(water, settings.GlowColor, 18, 1)

    -- Qi mist rising from the water
    local mist = Instance.new("ParticleEmitter")
    mist.Color = ColorSequence.new(settings.GlowColor)
    mist.LightEmission = 0.6
    mist.LightInfluence = 0
    mist.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 0) })
    mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 1) })
    mist.Lifetime = NumberRange.new(2, 3)
    mist.Speed = NumberRange.new(1, 2)
    mist.EmissionDirection = Enum.NormalId.Right -- Cylinders point along X, so Right is up
    mist.Rate = 8
    mist.Parent = water

    -- Four pillars on the rim with glowing caps
    local pillarDistance = stationRules.Radius + 1
    for pillar = 1, 4 do
        local angle = (pillar - 0.5) / 4 * FULL_TURN
        local base = ground + Vector3.new(math.cos(angle) * pillarDistance, 1, math.sin(angle) * pillarDistance)
        createPart(station, "Pillar", Vector3.new(1.4, 5, 1.4), CFrame.new(base + Vector3.new(0, 2.5, 0)), config.Platform.BaseMaterial, config.Platform.BaseColor)
        local capCFrame = CFrame.new(base + Vector3.new(0, 5.6, 0)) * CFrame.Angles(math.rad(45), math.rad(45), 0)
        createPart(station, "PillarCap", Vector3.new(1, 1, 1), capCFrame, Enum.Material.Neon, settings.GlowColor)
    end

    -- Floating sign so players know what the spring does
    local sign = Instance.new("BillboardGui")
    sign.Name = "Sign"
    sign.Size = UDim2.fromOffset(220, 50)
    sign.StudsOffsetWorldSpace = Vector3.new(0, 7, 0)
    sign.MaxDistance = 80
    sign.LightInfluence = 0
    sign.Parent = water

    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.TextColor3 = settings.GlowColor
    label.TextStrokeTransparency = 0.4
    label.Text = stationRules.DisplayName .. "\nCultivate here: +" .. stationRules.QiBonusPercent .. "% Qi"
    label.Parent = sign

    station.Parent = island
end

-- Beginner Qi Egg -----------------------------------------------------------

-- A small stone stand with the glowing Beginner Qi Egg. PetService listens to
-- its ProximityPrompt and decides which pet (if any) hatches.
local function buildEggStand(island, config)
    local settings = config.BeginnerEgg
    local spot = getFeatureSpot(config, settings)
    local ground = findGround(spot) or spot

    local stand = Instance.new("Model")
    stand.Name = settings.ModelName

    -- Stone base with a glowing ring, like a small version of the platform
    local baseCenter = ground + Vector3.new(0, 0.25, 0)
    createCylinder(stand, "Base", 12, 1.5, baseCenter, config.Platform.BaseMaterial, config.Platform.BaseColor)
    createCylinder(stand, "GlowRing", 10, 1.6, baseCenter, Enum.Material.Neon, settings.GlowColor)
    createCylinder(stand, "Floor", 9, 1.7, baseCenter, config.Platform.FloorMaterial, config.Platform.FloorColor)
    local floorTopY = baseCenter.Y + 1.7 / 2

    local pedestalCenter = Vector3.new(ground.X, floorTopY + 1.5, ground.Z)
    local pedestal = createCylinder(stand, "Pedestal", 3, 3, pedestalCenter, config.Platform.BaseMaterial, config.Platform.BaseColor)

    -- The egg floats just above the pedestal. A built-in sphere mesh stretches
    -- the part into an egg shape (no uploaded asset needed).
    local eggCFrame = CFrame.new(pedestalCenter + Vector3.new(0, 3.6, 0))
    local egg = createPart(stand, "BeginnerQiEgg", Vector3.new(2.4, 3.2, 2.4), eggCFrame, Enum.Material.Neon, settings.EggColor)
    local eggMesh = Instance.new("SpecialMesh")
    eggMesh.MeshType = Enum.MeshType.Sphere
    eggMesh.Parent = egg
    createLight(egg, settings.GlowColor, 12, 1.2)

    local sparkles = Instance.new("ParticleEmitter")
    sparkles.Color = ColorSequence.new(settings.GlowColor)
    sparkles.LightEmission = 1
    sparkles.Size = NumberSequence.new(0.2, 0)
    sparkles.Transparency = NumberSequence.new(0.2, 1)
    sparkles.Lifetime = NumberRange.new(1, 1.5)
    sparkles.Speed = NumberRange.new(0.5, 1.5)
    sparkles.SpreadAngle = Vector2.new(180, 180)
    sparkles.Rate = 4
    sparkles.Parent = egg

    -- Three guardian crystals leaning outward around the edge
    for shard = 1, 3 do
        local angle = shard / 3 * FULL_TURN
        local cframe = CFrame.new(ground + Vector3.new(math.cos(angle) * 4.5, 0, math.sin(angle) * 4.5))
            * CFrame.Angles(0, -angle, 0)
            * CFrame.Angles(0, 0, -0.3)
            * CFrame.new(0, 2, 0)
        createPart(stand, "GuardianCrystal", Vector3.new(1, 4.5, 1), cframe, Enum.Material.Neon, settings.GlowColor)
    end

    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Hatch"
    prompt.ObjectText = "Beginner Qi Egg"
    prompt.KeyboardKeyCode = Enum.KeyCode.F -- E is used for cultivating
    prompt.HoldDuration = 1
    prompt.MaxActivationDistance = settings.PromptDistance
    prompt.RequiresLineOfSight = false
    prompt.Parent = pedestal

    stand.Parent = island
end

-- Decorations --------------------------------------------------------------

local function buildTrees(island, config, random, taken)
    local settings = config.Trees
    local folder = createFolder(island, "Trees")

    for _ = 1, settings.Count do
        local ground = pickGroundSpot(random, config, taken)
        if ground then
            local tree = Instance.new("Model")
            tree.Name = "SpiritTree"

            local height = random:NextNumber(settings.MinHeight, settings.MaxHeight)
            local trunkCenter = ground + Vector3.new(0, height / 2 - 0.5, 0)
            createCylinder(tree, "Trunk", 1.6, height, trunkCenter, Enum.Material.Wood, settings.TrunkColor)

            -- A rounded canopy made of three overlapping balls
            local canopyColor = settings.CanopyColors[random:NextInteger(1, #settings.CanopyColors)]
            local treeTop = ground + Vector3.new(0, height, 0)
            for leaf = 1, 3 do
                local diameter = random:NextNumber(6, 9) * (if leaf == 1 then 1.2 else 0.9)
                local offset = if leaf == 1
                    then Vector3.zero
                    else Vector3.new(random:NextNumber(-2.5, 2.5), random:NextNumber(-1, 1.5), random:NextNumber(-2.5, 2.5))
                createBall(tree, "Canopy", diameter, treeTop + offset, settings.CanopyMaterial, canopyColor)
            end

            tree.Parent = folder
        end
    end
end

local function buildRocks(island, config, random, taken)
    local settings = config.Rocks
    local folder = createFolder(island, "Rocks")

    for _ = 1, settings.Count do
        local ground = pickGroundSpot(random, config, taken)
        if ground then
            local size = Vector3.new(random:NextNumber(3, 7), random:NextNumber(2, 4.5), random:NextNumber(3, 6))
            local rotation = CFrame.Angles(random:NextNumber(-0.25, 0.25), random:NextNumber(0, FULL_TURN), random:NextNumber(-0.25, 0.25))
            local cframe = CFrame.new(ground + Vector3.new(0, size.Y * 0.3, 0)) * rotation -- Partly buried
            createPart(folder, "Rock", size, cframe, settings.Material, settings.Color)
        end
    end
end

local function buildCrystals(island, config, random, taken)
    local settings = config.Crystals
    local folder = createFolder(island, "Crystals")

    for _ = 1, settings.Count do
        local ground = pickGroundSpot(random, config, taken)
        if ground then
            local cluster = Instance.new("Model")
            cluster.Name = "QiCrystal"
            local color = settings.Colors[random:NextInteger(1, #settings.Colors)]

            for shard = 1, 3 do
                local height = random:NextNumber(3, 7) * (if shard == 1 then 1.3 else 1)
                local tilt = if shard == 1 then random:NextNumber(-0.1, 0.1) else random:NextNumber(-0.5, 0.5)
                -- Rotate around the base point, then move up so the shard's bottom sits in the ground
                local cframe = CFrame.new(ground)
                    * CFrame.Angles(0, random:NextNumber(0, FULL_TURN), 0)
                    * CFrame.Angles(tilt, 0, 0)
                    * CFrame.new(0, height / 2 - 0.5, 0)
                local crystal = createPart(cluster, "Shard", Vector3.new(1.2, height, 1.2), cframe, Enum.Material.Neon, color)

                if shard == 1 then
                    createLight(crystal, color, settings.LightRange, 1)
                end
            end

            cluster.Parent = folder
        end
    end
end

local function buildFloatingFragments(island, config, random)
    local settings = config.FloatingFragments
    local folder = createFolder(island, "FloatingFragments")
    local taken = {}

    for _ = 1, settings.Count do
        local minDistance = config.Radius + settings.MinDistance
        local maxDistance = config.Radius + settings.MaxDistance
        local spot = pickSpot(random, config.Center, minDistance, maxDistance, taken, 14)
        if spot then
            local fragment = Instance.new("Model")
            fragment.Name = "FloatingFragment"

            local position = spot + Vector3.new(0, random:NextNumber(settings.MinHeight, settings.MaxHeight), 0)
            local width = random:NextNumber(5, 12)
            local rockHeight = width * random:NextNumber(0.6, 0.9)
            local turn = CFrame.Angles(0, random:NextNumber(0, FULL_TURN), 0)

            local rockSize = Vector3.new(width, rockHeight, width * 0.8)
            createPart(fragment, "Rock", rockSize, CFrame.new(position) * turn, Enum.Material.Rock, settings.RockColor)

            local underside = position - Vector3.new(0, rockHeight / 2, 0)
            createBall(fragment, "Underside", width * 0.7, underside, Enum.Material.Rock, settings.RockColor)

            local grassSize = Vector3.new(width * 0.95, 0.8, width * 0.75)
            local grassCFrame = CFrame.new(position + Vector3.new(0, rockHeight / 2 + 0.2, 0)) * turn
            createPart(fragment, "Grass", grassSize, grassCFrame, Enum.Material.Grass, settings.GrassColor)

            fragment.Parent = folder
        end
    end
end

-- Builds the island once and returns its model. If it already exists (for
-- example, if this is called twice), the existing island is returned instead.
function IslandBuilder.build(config)
    local existing = workspace:FindFirstChild(config.ModelName)
    if existing then
        return existing
    end

    local random = Random.new(config.Seed)
    local island = Instance.new("Model")
    island.Name = config.ModelName

    buildBody(config, random)
    buildHills(config, random)
    buildPlatform(island, config)
    buildEggStand(island, config)
    buildTrainingStation(island, config)

    -- Trees, rocks and crystals share one list so they never overlap
    local decorationSpots = {}
    buildTrees(island, config, random, decorationSpots)
    buildRocks(island, config, random, decorationSpots)
    buildCrystals(island, config, random, decorationSpots)
    buildFloatingFragments(island, config, random)

    island.Parent = workspace
    return island
end

return IslandBuilder

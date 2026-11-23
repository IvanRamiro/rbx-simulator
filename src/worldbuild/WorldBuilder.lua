-- Build-time only: run from Studio (edit mode) to (re)build Workspace.FloatingIslands from the
-- data tools/blender/world exports. Require a clone so Studio's module cache never serves an old copy:
--
--   local WB = require(game.ServerStorage.WorldBuild.WorldBuilder:Clone())
--
-- Building an island (FBX files in assets/world/<Island>, imported by hand into Workspace; each
-- export's anchor cube marks the island centre or the kit origin):
--   WB.clearTerrain(island); WB.buildTerrain(island)
--   WB.seatImport(island, <island meshes import>, <anchor>, "Underside" or "Island")
--   WB.storeKit(island, <each kit/props import>, <anchor>)
--   -- each import uploads its own atlas copy: point all pieces at one (WB.shareTexture or TextureID)
--   WB.placeKit(island); WB.buildEggStands(island); WB.buildRelics(island)
--   Yggdrasil (the hub, the celestial city since 2026-11-12: tools/blender/world/hub_ground.py exports its terrain,
--   placements and Yggdrasil_Celestial.fbx; WB.storeKit("Yggdrasil", <import>, "HB_Anchor")): WB.buildTerrain,
--   WB.placeKit, WB.buildShops, WB.buildAltar, WB.buildHallOfRecords, WB.buildSpawn, WB.buildRootColliders,
--   WB.buildHubNpcs, WB.buildMerchantTemplate; the bridges (WB.buildBridges) take the hub's gate from its kit
--   the Hall of Records (2026-11-16; tools/blender/world/hall_layout.py and hall_records.py): WB.storeHallOfRecords(<hall import>,
--   <paving import>) stores assets/world/HallOfRecords/HallOfRecords.fbx and assets/world/Yggdrasil/Yggdrasil_Paving.fbx and places
--   both; before its import, WB.buildHallOfRecords("Yggdrasil") builds it as a blockout of plain parts with its boards
--   every other island: WB.buildCheckpoint(island); Ember Peak also WB.buildLavafall, Moonlit Isle
--   WB.buildStarWell
--   the Blossom Sanctuary (tools/blender/world/blossom_layout.py writes its terrain and placements; blossom_assets.py its four FBX
--   files in assets/world/BlossomSanctuary, each stored with WB.storeKit("BlossomSanctuary", <import>, "BS_Anchor")):
--   WB.buildTerrain("BlossomSanctuary") (never clearTerrain: its square takes in a corner of the hub's rim), WB.buildApproach,
--   WB.buildSanctuary, then, once its kit is stored, WB.placeKit and again WB.buildApproach and WB.buildSanctuary (the stones' caps
--   and the koi come from the kit)
--   Murim Crossing (the owner's faction map, 2026-11-22; tools/blender/world/murim_layout.py writes its terrain and placements, layout.py
--   the bridge): WB.buildTerrain("MurimCrossing") (never clearTerrain; terrain all the way down, each plateau hanging in its own rock),
--   WB.buildBridges("MurimRoute") (open to every rank: no barrier and no rank zones; it wears the Moon's stored deck kit under the hub's gate),
--   then the standing parts from CrossingBuilder: local CB = require(game.ServerStorage.WorldBuild.CrossingBuilder:Clone()); CB.build()
--   terrain colours (once, after any terrain build): WB.applyMaterialColors()
--
-- Bridges (assets/world/Bridges): WB.storeBridgeKit(<import>, theme), then WB.buildBridges().
--
-- Eggs (assets/eggs/<EggId>.fbx): WB.storeEgg(<import>, eggId), then WB.buildEggStands(island).
-- Collision fidelity applies asynchronously; confirm with WB.checkCollision in a later call.
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

-- Modules are required as clones so Studio's require cache never serves a stale copy.
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"):Clone())
local EggModel = require(game:GetService("ServerScriptService"):WaitForChild("Guardians"):WaitForChild("EggModel"):Clone())

local WorldBuilder = {}

local VOXEL = 4

-- Terrain material colours are global to the place, so every island uses its own materials.
WorldBuilder.MaterialColors = {
    -- Yggdrasil (the Starting Island's, which it replaced)
    Grass = Color3.fromRGB(96, 158, 82),
    Ground = Color3.fromRGB(122, 96, 70),
    Rock = Color3.fromRGB(118, 120, 128),
    Cobblestone = Color3.fromRGB(168, 160, 146),
    -- Jade Grove
    LeafyGrass = Color3.fromRGB(64, 116, 58),
    Mud = Color3.fromRGB(86, 68, 50),
    Sandstone = Color3.fromRGB(98, 124, 108),
    -- Ember Peak
    Basalt = Color3.fromRGB(46, 42, 44),
    CrackedLava = Color3.fromRGB(255, 96, 24),
    Asphalt = Color3.fromRGB(52, 48, 48), -- ash drifts; the Asphalt texture is bright, so keep this dark
    Sand = Color3.fromRGB(70, 56, 48),
    -- Moonlit Isle
    Limestone = Color3.fromRGB(198, 200, 214),
    Snow = Color3.fromRGB(226, 233, 248),
    Salt = Color3.fromRGB(176, 178, 196),
    Pavement = Color3.fromRGB(168, 172, 192),
    -- Origin Abyss
    Slate = Color3.fromRGB(46, 44, 56),
    Concrete = Color3.fromRGB(78, 76, 88),
    Glacier = Color3.fromRGB(92, 52, 160), -- void-crystal crust along the rift's lip
}

-- Per-island terrain settings: how deep the terrain shell reaches below the island centre (the
-- underside meshes take over below that) and which material sits under the surface layer.
WorldBuilder.TerrainSettings = {
    Yggdrasil = { ShellDepth = 9, SubMaterial = "Ground", KeepThrough = { Rock = true, Grass = true } },
    -- deep enough for the Whispering Hollow (floor about -9)
    JadeGrove = { ShellDepth = 14, SubMaterial = "Mud", KeepThrough = { Sandstone = true } },
    -- the lava river's channel reaches about -6 at the edge
    EmberPeak = { ShellDepth = 13, SubMaterial = "Basalt", KeepThrough = { CrackedLava = true } },
    -- deep enough for the Star Well's shaft (floor -18)
    MoonlitIsle = { ShellDepth = 22, SubMaterial = "Limestone", KeepThrough = { Pavement = true } },
    -- the void crust is only the lip's top layer; the rift walls below are dark slate
    OriginAbyss = { ShellDepth = 14, SubMaterial = "Slate", KeepThrough = {} },
    -- on Yggdrasil's palette: terrain colours are global to the place
    -- grass all the way down: on a slope the voxels under the top one show, and Ground there made brown patches
    BeginnerIsle = { ShellDepth = 9, SubMaterial = "Ground", KeepThrough = { Rock = true, Grass = true } },
    -- on Yggdrasil's palette (plus Jade Grove's LeafyGrass under the blossom, where no grass blades hide the fallen petals, and
    -- its Mud for the pond's bed); its rock underside is terrain too (Bottoms in its data), Rock with bands of Ground like strata
    BlossomSanctuary = { ShellDepth = 9, SubMaterial = "Ground", KeepThrough = { Rock = true, Grass = true, LeafyGrass = true, Mud = true },
        UndersideMaterial = "Rock", StrataMaterial = "Ground" },
    -- Murim Crossing (tools/blender/world/murim_layout.py): Limestone/Grass/Pavement, LeafyGrass/Mud/Ground/Sandstone/Rock and Slate/Asphalt (plus
    -- Basalt and CrackedLava on the Demonic mountains, where nothing is built), all already coloured for the other islands. Terrain all the way down, and each
    -- side of the island hangs in its own rock: its data names the underside's and the strata's material per column (UndersideIndex).
    -- Every surface material is kept through the second layer so a slope shows its own material, not Ground.
    MurimCrossing = { ShellDepth = 9, SubMaterial = "Ground", UndersideMaterial = "Rock", StrataMaterial = "Ground",
        KeepThrough = { Limestone = true, Grass = true, Pavement = true, Ground = true, Mud = true, LeafyGrass = true, Rock = true, Slate = true,
            Asphalt = true, Basalt = true, CrackedLava = true, Sandstone = true } },
}

-- An island's terrain data, its grids turned by its quarter turns (Turns, layout.py) about its
-- centre: the generator writes them unturned. Quarter turns map cells onto cells exactly.
-- A grid array written as a run-length string (Murim Crossing's: the grid is mostly sky): values joined by commas, "~N" for N entries of
-- `off` (false for heights and depths, 0 for material indices).
local function expand(text, off)
    local out, n = {}, 0
    for token in string.gmatch(text, "[^,]+") do
        if string.byte(token, 1) == 126 then
            for _ = 1, tonumber(string.sub(token, 2)) do
                n += 1
                out[n] = off
            end
        else
            n += 1
            out[n] = tonumber(token)
        end
    end
    return out
end

local function terrainData(island)
    local data = require(ServerStorage.WorldBuild.Terrain:FindFirstChild(island):Clone())
    if type(data.Heights) == "string" then
        data = table.clone(data)
        data.Heights = expand(data.Heights, false)
        data.MaterialIndex = expand(data.MaterialIndex, 0)
        data.Bottoms = data.Bottoms and expand(data.Bottoms, false)
        data.UndersideIndex = data.UndersideIndex and expand(data.UndersideIndex, 0)
    end
    local turns = (data.Turns or 0) % 4
    if turns == 0 or data.BakedTurn then -- BakedTurn: the generator wrote the grid already turned
        return data
    end
    local n, cell = data.Size, data.Cell
    local cx, cz = data.Centre.X, data.Centre.Z
    local ox, oz = data.Origin.X - cx, data.Origin.Y - cz
    local function turn(x, z, count)
        for _ = 1, count do
            x, z = -z, x
        end
        return x, z
    end
    local minX, minZ = math.huge, math.huge
    for _, corner in { { ox, oz }, { ox + n * cell, oz }, { ox, oz + n * cell }, { ox + n * cell, oz + n * cell } } do
        local x, z = turn(corner[1], corner[2], turns)
        minX, minZ = math.min(minX, x), math.min(minZ, z)
    end
    local function regrid(values)
        if not values then
            return nil
        end
        local out = table.create(n * n, false)
        for j = 1, n do
            for i = 1, n do
                local sx, sz = turn(minX + (i - 0.5) * cell, minZ + (j - 0.5) * cell, 4 - turns)
                local si = math.floor((sx - ox) / cell + 0.5 + 0.001)
                local sj = math.floor((sz - oz) / cell + 0.5 + 0.001)
                out[(j - 1) * n + i] = values[(sj - 1) * n + si]
            end
        end
        return out
    end
    local turned = table.clone(data)
    turned.Origin = Vector2.new(cx + minX, cz + minZ)
    turned.Heights = regrid(data.Heights)
    turned.MaterialIndex = regrid(data.MaterialIndex)
    turned.WaterLevels = regrid(data.WaterLevels)
    return turned
end

function WorldBuilder.applyMaterialColors()
    for name, color in WorldBuilder.MaterialColors do
        workspace.Terrain:SetMaterialColor(Enum.Material[name], color)
    end
end

-- Clears the terrain inside an island's grid footprint (plus a margin), from below the shell
-- to well above the highest ground. Footprints are squares and islands can sit in each other's
-- corners: Ember Peak's overlaps Jade Grove's, and clearing it once took 71 columns off Jade Grove
-- (found by a phone test, 2026-11-04). After clearing an island, rebuild any neighbour it overlaps.
function WorldBuilder.clearTerrain(island)
    local data = terrainData(island)
    local span = data.Size * data.Cell
    local min = Vector3.new(data.Origin.X - 8, data.Centre.Y - 80, data.Origin.Y - 8)
    local max = Vector3.new(data.Origin.X + span + 8, data.Centre.Y + 120, data.Origin.Y + span + 8)
    workspace.Terrain:FillBlock(CFrame.new((min + max) / 2), max - min, Enum.Material.Air)
end

-- Writes one column of a strip read with ReadVoxels back, alone: the island's own columns are written one by one, so no neighbour's column
-- in its grid's square (a corner of the hub's rim) is ever written back, and a write that rounds a voxel can't creep into it.
local function writeColumn(data, minY, layers, i, j, matGrid, occGrid, jj)
    local origin = Vector3.new(data.Origin.X + (i - 1) * VOXEL, minY, data.Origin.Y + (j - 1) * VOXEL)
    local region = Region3.new(origin, origin + Vector3.new(VOXEL, layers * VOXEL, VOXEL))
    local m, o = { {} }, { {} }
    for k = 1, layers do
        m[1][k] = { matGrid[i][k][jj] }
        o[1][k] = { occGrid[i][k][jj] }
    end
    workspace.Terrain:WriteVoxels(region, VOXEL, m, o)
end

-- An island whose data carries Bottoms (the Blossom Sanctuary) is terrain all the way down: each column runs from its ground to its
-- own depth, the underside rock with a band of Ground every 28 studs, written in strips so Studio stays responsive. Only the
-- island's own columns are written; the rest of its square (a corner of the hub's rim) stays as it is, so a rebuild is safe.
local function buildDeepTerrain(data, settings)
    local materials = {}
    for index, name in data.Materials do
        materials[index] = Enum.Material[name]
    end
    local subMaterial = Enum.Material[settings.SubMaterial]
    local underside = Enum.Material[settings.UndersideMaterial]
    local strata = settings.StrataMaterial and Enum.Material[settings.StrataMaterial]
    local lowest, highest = 0, -math.huge
    for index, h in data.Heights do
        if h then
            highest = math.max(highest, h, data.WaterLevels and data.WaterLevels[index] or -math.huge)
            lowest = math.min(lowest, data.Bottoms[index] or -settings.ShellDepth)
        end
    end
    local minY = math.floor((data.Centre.Y + lowest) / VOXEL) * VOXEL - VOXEL
    local maxY = math.ceil((data.Centre.Y + highest) / VOXEL) * VOXEL + VOXEL
    local layers = (maxY - minY) / VOXEL
    local size = data.Size
    local STRIP = 12
    local filled = 0
    for j0 = 1, size, STRIP do
        local rows = math.min(STRIP, size - j0 + 1)
        local owned = false
        for j = j0, j0 + rows - 1 do
            for i = 1, size do
                if data.Heights[(j - 1) * size + i] then
                    owned = true
                    break
                end
            end
        end
        if owned then
            local regionMin = Vector3.new(data.Origin.X, minY, data.Origin.Y + (j0 - 1) * VOXEL)
            local region = Region3.new(regionMin, regionMin + Vector3.new(size * VOXEL, layers * VOXEL, rows * VOXEL))
            local matGrid, occGrid = workspace.Terrain:ReadVoxels(region, VOXEL)
            for jj = 1, rows do
                local j = j0 + jj - 1
                for i = 1, size do
                    local index = (j - 1) * size + i
                    local h = data.Heights[index]
                    if h then
                        local top = data.Centre.Y + h
                        local bottom = data.Centre.Y + (data.Bottoms[index] or -settings.ShellDepth)
                        local surface = materials[data.MaterialIndex[index]]
                        local keep = settings.KeepThrough[data.Materials[data.MaterialIndex[index]]]
                        local waterLevel = data.WaterLevels and data.WaterLevels[index]
                        local waterTop = waterLevel and data.Centre.Y + waterLevel
                        -- (an island may give each column its own underside and strata: Murim Crossing's three plateaus hang in their own rock)
                        local under = data.UndersideIndex and data.UndersideIndex[index] or 0
                        local underHere = materials[under // 100] or underside
                        local strataHere = materials[under % 100] or strata
                        for k = 1, layers do
                            local y0 = minY + (k - 1) * VOXEL
                            local material, occupancy = Enum.Material.Air, 0
                            -- a voxel's surface renders from its centre (occupancy 0) to the next one up (1), measured in Studio
                            local solid = math.min(math.clamp((top - y0 - VOXEL / 2) / VOXEL, 0, 1), math.clamp((y0 + VOXEL - bottom) / VOXEL, 0, 1))
                            if solid > 0 then
                                local depth = top - (y0 + VOXEL / 2)
                                -- (two voxels deep: a top just over a voxel's boundary leaves the one under it showing, and at 4 the
                                -- paths' edges showed the Ground beneath as brown scars, seen after the import)
                                if depth <= 6 then
                                    material = surface
                                elseif depth < 10 then
                                    material = if keep then surface else subMaterial
                                elseif strataHere and math.floor((y0 - data.Centre.Y) / VOXEL) % 7 == 3 then
                                    material = strataHere
                                else
                                    material = underHere
                                end
                                occupancy = solid
                                filled += 1
                            elseif waterTop and y0 < waterTop and y0 + VOXEL > top - VOXEL then
                                -- (water's surface renders from the voxel's bottom, not its centre: measured in Studio)
                                material = Enum.Material.Water
                                occupancy = math.clamp((waterTop - y0) / VOXEL, 0, 1)
                            end
                            matGrid[i][k][jj] = material
                            occGrid[i][k][jj] = occupancy
                        end
                    end
                end
            end
            for jj = 1, rows do
                for i = 1, size do
                    if data.Heights[(j0 + jj - 2) * size + i] then
                        writeColumn(data, minY, layers, i, j0 + jj - 1, matGrid, occGrid, jj)
                    end
                end
            end
            task.wait()
        end
    end
    return filled
end

-- Takes an island with deep terrain (Bottoms in its data) away: exactly the columns its data owns, from its lowest underside to its highest
-- ground, every voxel to Air. The rest of the island's grid square (a corner of the hub's, a neighbour's) is read and written back as it
-- is, so this is safe where clearTerrain is not. Run it with the data the terrain was built from, BEFORE writing a new layout over that data.
function WorldBuilder.clearDeepTerrain(island)
    local data = terrainData(island)
    assert(data.Bottoms, island .. " has no deep terrain data")
    local lowest, highest = 0, -math.huge
    for index, h in data.Heights do
        if h then
            highest = math.max(highest, h, data.WaterLevels and data.WaterLevels[index] or -math.huge)
            lowest = math.min(lowest, data.Bottoms[index] or -9)
        end
    end
    local minY = math.floor((data.Centre.Y + lowest) / VOXEL) * VOXEL - VOXEL
    local maxY = math.ceil((data.Centre.Y + highest) / VOXEL) * VOXEL + VOXEL
    local layers = (maxY - minY) / VOXEL
    local size = data.Size
    local STRIP = 12
    local cleared = 0
    for j0 = 1, size, STRIP do
        local rows = math.min(STRIP, size - j0 + 1)
        local owned = false
        for j = j0, j0 + rows - 1 do
            for i = 1, size do
                if data.Heights[(j - 1) * size + i] then
                    owned = true
                    break
                end
            end
            if owned then
                break
            end
        end
        if owned then
            local regionMin = Vector3.new(data.Origin.X, minY, data.Origin.Y + (j0 - 1) * VOXEL)
            local region = Region3.new(regionMin, regionMin + Vector3.new(size * VOXEL, layers * VOXEL, rows * VOXEL))
            local matGrid, occGrid = workspace.Terrain:ReadVoxels(region, VOXEL)
            for jj = 1, rows do
                for i = 1, size do
                    if data.Heights[(j0 + jj - 2) * size + i] then
                        for k = 1, layers do
                            if occGrid[i][k][jj] > 0 then
                                cleared += 1
                            end
                            matGrid[i][k][jj] = Enum.Material.Air
                            occGrid[i][k][jj] = 0
                        end
                    end
                end
            end
            for jj = 1, rows do
                for i = 1, size do
                    if data.Heights[(j0 + jj - 2) * size + i] then
                        writeColumn(data, minY, layers, i, j0 + jj - 1, matGrid, occGrid, jj)
                    end
                end
            end
            task.wait()
        end
    end
    return cleared
end

function WorldBuilder.buildTerrain(island)
    local data = terrainData(island)
    local settings = WorldBuilder.TerrainSettings[island]
    if data.Bottoms then
        return buildDeepTerrain(data, settings)
    end
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

    local cellsPerVoxel = data.Cell / VOXEL
    assert(cellsPerVoxel == 1, "WorldBuilder expects 4-stud heightfield cells")
    local size = data.Size
    -- what's there already, so a column this island doesn't own (a neighbour's, in the corners of its square) stays as it is
    local regionMin = Vector3.new(data.Origin.X, minY, data.Origin.Y)
    local region = Region3.new(regionMin, regionMin + Vector3.new(size * VOXEL, layers * VOXEL, size * VOXEL))
    local matGrid, occGrid = workspace.Terrain:ReadVoxels(region, VOXEL)

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
                    matGrid[i][k][j] = Enum.Material.Air
                    occGrid[i][k][j] = 0
                    if y0 + VOXEL > bottomY then
                        -- a voxel's surface renders from its centre (occupancy 0) to the next one up (1), measured in Studio
                        local occupancy = math.clamp((top - y0 - VOXEL / 2) / VOXEL, 0, 1)
                        if occupancy > 0 then
                            matGrid[i][k][j] = if keep or y0 + VOXEL >= top - VOXEL then surface else subMaterial
                            occGrid[i][k][j] = occupancy
                            filled += 1
                        elseif waterTop and y0 + VOXEL / 2 < waterTop then
                            matGrid[i][k][j] = Enum.Material.Water
                            occGrid[i][k][j] = math.clamp((waterTop - y0 - VOXEL / 2) / VOXEL, 0, 1)
                        end
                    end
                end
            end
        end
    end

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
    { Prefix = "SI_RootShelf", Fidelity = Enum.CollisionFidelity.Box },
    -- the Beginner Isle: what you walk under or through keeps its shape
    { Prefix = "BI_LionGate", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BI_Hall", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BI_Pavilion", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BI_Bell", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BI_Dummy", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BI_WeaponRack", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BI_LiftingStones", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_CradleFloor", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "SI_StoneLantern", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_MossRock", Fidelity = Enum.CollisionFidelity.Hull },
    -- the outer islands' landmarks: you walk in and through them
    { Prefix = "JG_Hermitage", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "MI_MoonGate", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_Colonnade", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "EP_FirePylon", Fidelity = Enum.CollisionFidelity.Hull },
    -- Jade Grove: the hollow, the walk-under root and the gate opening must stay passable
    { Prefix = "JG_ElderTrunk", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "JG_ElderPads", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "JG_GroveGate", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "JG_TreeShelf", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "JG_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_StandingStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_WhisperStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_JadeLantern", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_JadeOutcrop", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_FallenLog", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_GladeFloor", Fidelity = Enum.CollisionFidelity.Box },
    -- Ember Peak: the gate between its column bundles must stay passable
    { Prefix = "EP_EmberGate", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "EP_BasaltStep", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_ForgeWalls", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "EP_AltarFloor", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "EP_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_Brazier", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_ForgeHearth", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_Anvil", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_SigilMonolith", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_FireCrystal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_EmberVent", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "EP_ObsidianShard", Fidelity = Enum.CollisionFidelity.Hull },
    -- Moonlit Isle: the Star Well's shaft, the mirror's bridge and dais, and the arch stay open
    { Prefix = "MI_StarWell", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "MI_MirrorRim", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "MI_CrescentArch", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "MI_MirrorPool", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "MI_MoonstoneSpire", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "MI_Pavilion", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "MI_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "MI_MoonstoneShards", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "MI_LunarRock", Fidelity = Enum.CollisionFidelity.Hull },
    -- Origin Abyss: a hull would roof over the bridge's gap, the gate, the altar ring and the ruins
    { Prefix = "OA_BrokenBridge", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_GateOfDescent", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_Altar", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_RuinFragment", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_ShardFloor", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_ThornCrown", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_Colossus", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_EggPedestal", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "OA_RuinPillar", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "OA_FallenDrums", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "OA_VoidCrystals", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "OA_SlateRock", Fidelity = Enum.CollisionFidelity.Hull },
    -- Yggdrasil: the roots arch over paths and carry the climb down, so they keep their shape;
    -- the stele's roof and the shops' open halls would close a hull over the space under them
    -- the celestial hub: you walk into the Sanctum, the Market's arcade, the forge and round the vault (longest names first: a
    -- prefix matches every piece that starts with it)
    -- (the hub's redesign, 2026-11-15) a hull would fill the arc in front of the parapet and the Merchant's screen
    { Prefix = "HB_RingParapet", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_MerchantDaisGlow", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_MerchantDais", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_SquareCompassGlow", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_SquareCompass", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "HB_SpawnPad", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_SanctumPlinth", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_HatchSanctum", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_HatchGlass", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "HB_MarketCanopy", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_MarketGlow", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_Market", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_BlacksmithCore", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_BlacksmithCrystal", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_Blacksmith", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_BuySellStones", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_BuySell", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_BridgeGateGlow", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_BridgeGate", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    -- the Hall of Records (hall_records.py): the court and the flags are flat; the banners' cloth doesn't collide (Banner)
    { Prefix = "HR_Court", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HR_PathFlag", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HR_", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "HB_CrystalLampGlow", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_CrystalLampLight", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "HB_CrystalLamp", Fidelity = Enum.CollisionFidelity.Hull },
    -- the Blossom Sanctuary: you walk under the trees' limbs and over the bridge's arch; the canopies, lilies, reeds and petals
    -- don't collide (their materials say so: MaterialLooks), so they get a plain box
    { Prefix = "BS_Tree", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BS_Bridge", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BS_SteppingStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BS_EdgeRock", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BS_KerbStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BS_SeatStone", Fidelity = Enum.CollisionFidelity.Hull },
    -- the shrine: you walk through the torii, up the hall's stair onto its floor and under the chozuya's roof
    { Prefix = "BS_Torii", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BS_ShrineHall", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BS_Chozuya", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BS_ShrineLantern", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BS_", Fidelity = Enum.CollisionFidelity.Box },
    { Prefix = "YG_MoundRoot", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_GripRoot", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_PathRoot", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_CradleRoot", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_Slab", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "BI_GripRoot", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "BI_Slab", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "YG_Taproot", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "JG_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "SI_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "BI_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "YG_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "EP_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "MI_", Fidelity = Enum.CollisionFidelity.Default },
    { Prefix = "OA_", Fidelity = Enum.CollisionFidelity.Default },
}

-- Surface overrides per mesh-name prefix: glowing inlays are Neon (saturated colours, since
-- Neon blooms pale colours to white). Pieces without collision use Box fidelity so they cost
-- nothing to the physics engine.
local GLOW = { Material = Enum.Material.Neon, CanCollide = false, CastShadow = false }
WorldBuilder.Appearance = {
    SI_LanternLight = table.clone(GLOW),
    SI_EggGlowRing = table.clone(GLOW),
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
    -- Ember Peak: the lava lake and river stay touchable (WorldService returns anyone touching them to the checkpoint)
    EP_UnderColumns = { CanCollide = false },
    EP_MagmaCore = table.clone(GLOW),
    EP_LavaLake = { Material = Enum.Material.Neon, CanCollide = false, CanTouch = true, CastShadow = false, Tag = "LavaHazard" },
    EP_LavaRiver = { Material = Enum.Material.Neon, CanCollide = false, CanTouch = true, CastShadow = false, Tag = "LavaHazard" },
    EP_LavaCrust = { CanCollide = false },
    EP_GateFire = table.clone(GLOW),
    EP_BrazierFire = table.clone(GLOW),
    EP_ForgeCoals = table.clone(GLOW),
    EP_VentGlow = table.clone(GLOW),
    EP_SigilGlow = table.clone(GLOW),
    EP_EggGlowRing = table.clone(GLOW),
    -- Moonlit Isle: the Moon Mirror is dark reflective glass you can walk on
    MI_MirrorPool = { Material = Enum.Material.Glass, Transparency = 0.15, Reflectance = 0.55, CastShadow = false },
    MI_CliffSkirt = { CanCollide = false },
    MI_CloudBank = { CanCollide = false, CastShadow = false },
    MI_Geode = { CanCollide = false },
    MI_GeodeGlow = table.clone(GLOW),
    MI_Armillary = { CanCollide = false },
    MI_StarLantern = { CanCollide = false },
    MI_StarLanternCore = table.clone(GLOW),
    MI_FrostLilies = { CanCollide = false },
    MI_LilyGlow = table.clone(GLOW),
    MI_EggGlowRing = table.clone(GLOW),
    -- Origin Abyss: void light glows through the shattered underside, the rift and the shard
    OA_UnderChunks = { CanCollide = false },
    OA_VoidCore = table.clone(GLOW),
    OA_RiftChains = { CanCollide = false },
    OA_RiftVeil = table.clone(GLOW),
    OA_AltarRunes = table.clone(GLOW),
    OA_TemplePaving = { CanCollide = false }, -- thin slabs over flat terrain, which carries the player
    OA_VoidShard = { Material = Enum.Material.Glass, Transparency = 0.3, Reflectance = 0.2, CanCollide = false, CastShadow = false },
    OA_ShardCore = table.clone(GLOW),
    OA_ShardChains = { CanCollide = false },
    OA_EggGlowRing = table.clone(GLOW),
    OA_ColossusEyes = table.clone(GLOW),
    OA_VoidCrystals = { Material = Enum.Material.Glass, Transparency = 0.35, Reflectance = 0.15, CastShadow = false },
    OA_VoidCrystalGlow = table.clone(GLOW),
    -- Yggdrasil: the crown and the aerial roots are out of reach; Qi glows in the trunk's grooves
    YG_CrownLower = { CanCollide = false },
    YG_CrownUpper = { CanCollide = false },
    YG_AerialRoots = { CanCollide = false },
    -- the three long roots arch over the paths (about 12 studs clear), but their collision closed the
    -- arches (the owner, 2026-11-11: "I still can't go through in the root near buy and sell"): the
    -- meshes don't collide; WB.buildRootColliders lays invisible cylinders along them instead
    YG_MoundRoot0 = { CanCollide = false },
    YG_MoundRoot2 = { CanCollide = false },
    YG_MoundRoot4 = { CanCollide = false },
    YG_TrunkVeins = table.clone(GLOW),
    YG_SeedLanterns = table.clone(GLOW),
}
-- the Lion Court's flagstones lie on level terrain: decoration underfoot, so nothing catches on them
WorldBuilder.Appearance.BI_CourtPaving = { CanCollide = false, CastShadow = false }
-- The outer islands' arena floors (tools/blender/world/island_upgrades.py): decoration on level ground, like the Lion Court's
WorldBuilder.Appearance.JG_ArenaFloor = { CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.EP_ArenaFloor = { CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.MI_ArenaFloor = { CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.OA_ArenaFloor = { CanCollide = false, CastShadow = false }
-- and the paved ground of the hub and the Beginner Isle
for _, name in { "BI_CourtApron", "BI_Roads", "BI_YardFloor" } do
    WorldBuilder.Appearance[name] = { CanCollide = false, CastShadow = false }
end
-- the celestial hub (tools/blender/world/hub_celestial.py, hub_ground.py; the hub rebuilt 2026-11-12): white crystal glows, blue runes,
-- glass, and paving you walk over the terrain beneath
do
    local CRYSTAL = Color3.fromRGB(226, 240, 255) -- white with a glow (the owner); Neon blooms it
    local RUNE = Color3.fromRGB(120, 200, 255)
    local glass = { Material = Enum.Material.Glass, Color = Color3.fromRGB(175, 215, 255), Transparency = 0.45, CastShadow = false }
    for _, name in { "HB_RingPlaza", "HB_Plazas", "HB_Avenues" } do
        WorldBuilder.Appearance[name] = { CanCollide = false, CastShadow = false }
    end
    -- the paving's gold lines: Metal on the flat, seen at a grazing angle, mirrored the blue sky and read olive (seen in Studio)
    for _, name in { "HB_RingPlaza__Gold", "HB_Plazas__Gold", "HB_Avenues__Gold" } do
        WorldBuilder.Appearance[name] = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(226, 176, 70) }
    end
    WorldBuilder.Appearance.HB_PavingRunes = { Material = Enum.Material.Neon, Color = RUNE, CanCollide = false, CastShadow = false }
    WorldBuilder.Appearance.HB_HatchRunes = { Material = Enum.Material.Neon, Color = RUNE, CanCollide = false, CastShadow = false }
    for _, name in { "HB_HatchCrystal", "HB_MarketGlow", "HB_BlacksmithCrystal", "HB_BuySellStones", "HB_CrystalLampGlow", "HB_CrystalLampLight" } do
        WorldBuilder.Appearance[name] = { Material = Enum.Material.Neon, Color = CRYSTAL, CanCollide = false, CastShadow = false }
    end
    -- the market's great egg: at full Neon it bloomed into a white blob that lost its egg shape (seen in Studio)
    WorldBuilder.Appearance.HB_MarketGlow = { Material = Enum.Material.Neon, Color = Color3.fromRGB(200, 226, 255), Transparency = 0.3, CanCollide = false, CastShadow = false }
    WorldBuilder.Appearance.HB_BlacksmithCore = { Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 110, 30), CanCollide = false, CastShadow = false }
    WorldBuilder.Appearance.HB_HatchGlass = table.clone(glass)
    WorldBuilder.Appearance.HB_MarketCanopy = table.clone(glass)
    WorldBuilder.Appearance.HB_MarketCanopy.CanCollide = false
    WorldBuilder.Appearance.HB_BridgeGateGlow = { Material = Enum.Material.Neon, CanCollide = false, CastShadow = false } -- (coloured per route)
    -- the hub's redesign (2026-11-15, tools/blender/world/hub_district.py and hub_ground.py): the Ring Road, the bridges' aprons and the
    -- parapet over the great root's cove; the spawn pads, the Merchant's dais, the Market Square's centrepiece and the Sanctum's plinth
    for _, name in { "HB_RingRoadNE", "HB_RingRoadSE", "HB_RingRoadSW", "HB_RingRoadNW", "HB_Aprons" } do
        WorldBuilder.Appearance[name] = { CanCollide = false, CastShadow = false }
        WorldBuilder.Appearance[name .. "__Gold"] = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(226, 176, 70) }
    end
    for _, name in { "HB_SpawnPadGlow", "HB_SquareCompassGlow", "HB_MerchantDaisGlow" } do
        WorldBuilder.Appearance[name] = { Material = Enum.Material.Neon, Color = CRYSTAL, CanCollide = false, CastShadow = false }
    end
    for _, name in { "HB_SpawnPad", "HB_SanctumPlinth" } do
        WorldBuilder.Appearance[name] = { CastShadow = false }
    end
end

-- the shrine's toro lanterns: a warm light, not the hub's cool crystal (the Glow material's colour)
WorldBuilder.Appearance.BS_ShrineLantern__Glow = { Color = Color3.fromRGB(255, 200, 130) }
WorldBuilder.Appearance.EP_ArenaGlow = { Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 78, 14), CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.EP_PylonFire = { Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 120, 20), Transparency = 0.35, CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.OA_ArenaGlow = { Material = Enum.Material.Neon, Color = Color3.fromRGB(115, 40, 255), CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.SI_LanternLight.Color = Color3.fromRGB(255, 150, 60)
WorldBuilder.Appearance.JG_JadeLanternLight.Color = Color3.fromRGB(255, 175, 80) -- warm, so the forest isn't washed green
WorldBuilder.Appearance.JG_MushroomCaps.Color = Color3.fromRGB(30, 230, 200)
WorldBuilder.Appearance.JG_HollowWater.Color = Color3.fromRGB(35, 160, 130)
WorldBuilder.Appearance.EP_MagmaCore.Color = Color3.fromRGB(255, 80, 15)
WorldBuilder.Appearance.EP_LavaLake.Color = Color3.fromRGB(255, 105, 20)
WorldBuilder.Appearance.EP_LavaRiver.Color = Color3.fromRGB(255, 120, 30)
WorldBuilder.Appearance.EP_GateFire.Color = Color3.fromRGB(255, 120, 20)
WorldBuilder.Appearance.EP_BrazierFire.Color = Color3.fromRGB(255, 120, 20)
-- flame meshes are a translucent core; their particles give the motion
WorldBuilder.Appearance.EP_GateFire.Transparency = 0.35
WorldBuilder.Appearance.EP_BrazierFire.Transparency = 0.35
WorldBuilder.Appearance.EP_ForgeCoals.Color = Color3.fromRGB(255, 70, 10)
WorldBuilder.Appearance.EP_VentGlow.Color = Color3.fromRGB(255, 70, 10)
WorldBuilder.Appearance.EP_SigilGlow.Color = Color3.fromRGB(255, 165, 40)
WorldBuilder.Appearance.MI_MirrorPool.Color = Color3.fromRGB(28, 36, 82)
WorldBuilder.Appearance.MI_GeodeGlow.Color = Color3.fromRGB(90, 140, 255)
WorldBuilder.Appearance.MI_StarLanternCore.Color = Color3.fromRGB(255, 210, 90)
WorldBuilder.Appearance.MI_LilyGlow.Color = Color3.fromRGB(110, 160, 255)
WorldBuilder.Appearance.OA_VoidCore.Color = Color3.fromRGB(140, 40, 255)
WorldBuilder.Appearance.OA_RiftVeil.Color = Color3.fromRGB(120, 30, 255)
WorldBuilder.Appearance.OA_RiftVeil.Transparency = 0.6
WorldBuilder.Appearance.OA_AltarRunes.Color = Color3.fromRGB(140, 55, 255)
WorldBuilder.Appearance.OA_VoidShard.Color = Color3.fromRGB(40, 18, 72)
WorldBuilder.Appearance.OA_ShardCore.Color = Color3.fromRGB(165, 50, 255)
WorldBuilder.Appearance.OA_ColossusEyes.Color = Color3.fromRGB(115, 40, 255) -- bluer violet: redder ones bloom pink
WorldBuilder.Appearance.OA_VoidCrystals.Color = Color3.fromRGB(55, 22, 100)
WorldBuilder.Appearance.OA_VoidCrystalGlow.Color = Color3.fromRGB(160, 55, 255)
WorldBuilder.Appearance.YG_TrunkVeins.Color = Color3.fromRGB(40, 210, 235) -- the compass's Qi
WorldBuilder.Appearance.YG_SeedLanterns.Color = Color3.fromRGB(255, 170, 40)

-- Kit pieces that carry a PointLight (lights take the piece's colour).
WorldBuilder.Lights = {
    SI_LanternLight = { Range = 16, Brightness = 1.2 },
    JG_JadeLanternLight = { Range = 16, Brightness = 1.0 },
    EP_GateFire = { Range = 18, Brightness = 1.1 },
    EP_BrazierFire = { Range = 14, Brightness = 0.9 },
    EP_ForgeCoals = { Range = 18, Brightness = 1.5 },
    MI_StarLanternCore = { Range = 14, Brightness = 0.9 },
    OA_ColossusEyes = { Range = 16, Brightness = 1.4 },
    EP_PylonFire = { Range = 26, Brightness = 1.6 },
    HB_CrystalLampLight = { Range = 16, Brightness = 0.8 },  -- (one lamp of each pair: hub_ground.write_placements)
    BS_ShrineLantern = { Range = 14, Brightness = 0.9 },     -- the shrine's toro (on its glow, warm)
    BS_ShrineHall = { Range = 18, Brightness = 0.45, Color = Color3.fromRGB(255, 196, 130) }, -- a soft warm glow in the hall (the toro
                                                                                             -- stand 25 studs down the path)
    HB_MarketGlow = { Range = 16, Brightness = 0.8 },
}

-- Kit pieces that throw off particles (one or more presets each).
WorldBuilder.Emitters = {
    EP_GateFire = { "Flames", "EmberSparks" },
    EP_BrazierFire = { "Flames", "EmberSparks" },
    EP_PylonFire = { "Flames", "EmberSparks" },
    EP_ForgeCoals = { "EmberSparks" },
    EP_VentGlow = { "EmberSparks" },
    OA_ColossusEyes = { "VoidWisps" },
    OA_VoidCrystalGlow = { "VoidMotes" },
    YG_TrunkVeins = { "QiMotes" },
}

local function addEmitterPreset(part, preset)
    if preset == "Flames" then
        local flames = Instance.new("ParticleEmitter")
        flames.Name = "Flames"
        flames.Texture = "rbxasset://textures/particles/fire_main.dds"
        flames.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 220, 120)),
            ColorSequenceKeypoint.new(0.4, Color3.fromRGB(255, 120, 30)), ColorSequenceKeypoint.new(1, Color3.fromRGB(180, 40, 10)) })
        flames.LightEmission = 1
        flames.LightInfluence = 0
        flames.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.4), NumberSequenceKeypoint.new(1, 0.2) })
        flames.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
        flames.Lifetime = NumberRange.new(0.6, 1)
        flames.Speed = NumberRange.new(3, 5)
        flames.SpreadAngle = Vector2.new(8, 8)
        flames.Rotation = NumberRange.new(-20, 20)
        flames.EmissionDirection = Enum.NormalId.Top
        flames.Rate = 22
        flames.Parent = part
    elseif preset == "EmberSparks" then
        local sparks = Instance.new("ParticleEmitter")
        sparks.Name = "EmberSparks"
        sparks.Color = ColorSequence.new(Color3.fromRGB(255, 200, 90), Color3.fromRGB(255, 70, 20))
        sparks.LightEmission = 1
        sparks.LightInfluence = 0
        sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18), NumberSequenceKeypoint.new(1, 0) })
        sparks.Transparency = NumberSequence.new(0, 1)
        sparks.Lifetime = NumberRange.new(1.2, 2.2)
        sparks.Speed = NumberRange.new(2, 4.5)
        sparks.SpreadAngle = Vector2.new(25, 25)
        sparks.Acceleration = Vector3.new(0, 1.5, 0)
        sparks.Drag = 0.6
        sparks.EmissionDirection = Enum.NormalId.Top
        sparks.Rate = 6
        sparks.Parent = part
    elseif preset == "VoidMotes" then
        local motes = Instance.new("ParticleEmitter")
        motes.Name = "VoidMotes"
        motes.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        motes.Color = ColorSequence.new(Color3.fromRGB(200, 120, 255), Color3.fromRGB(90, 30, 220))
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.35), NumberSequenceKeypoint.new(1, 0) })
        motes.Transparency = NumberSequence.new(0.1, 1)
        motes.Lifetime = NumberRange.new(2.5, 4)
        motes.Speed = NumberRange.new(1, 2.5)
        motes.SpreadAngle = Vector2.new(30, 30)
        motes.Rotation = NumberRange.new(0, 360)
        motes.RotSpeed = NumberRange.new(-40, 40)
        motes.Drag = 0.4
        motes.EmissionDirection = Enum.NormalId.Top
        motes.Rate = 5
        motes.Parent = part
    elseif preset == "VoidWisps" then
        local wisps = Instance.new("ParticleEmitter")
        wisps.Name = "VoidWisps"
        wisps.Texture = "rbxasset://textures/particles/smoke_main.dds"
        wisps.Orientation = Enum.ParticleOrientation.FacingCameraWorldUp
        wisps.Color = ColorSequence.new(Color3.fromRGB(175, 80, 255), Color3.fromRGB(40, 0, 90))
        wisps.LightEmission = 0.7
        wisps.LightInfluence = 0
        wisps.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(0.5, 0.9), NumberSequenceKeypoint.new(1, 1.3) })
        wisps.Squash = NumberSequence.new(1.4)
        wisps.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.55),
            NumberSequenceKeypoint.new(1, 1) })
        wisps.Lifetime = NumberRange.new(2.5, 3.5)
        wisps.Speed = NumberRange.new(1.2, 2.2)
        wisps.SpreadAngle = Vector2.new(12, 12)
        wisps.Acceleration = Vector3.new(0, 0.6, 0)
        wisps.Rotation = NumberRange.new(-10, 10)
        wisps.RotSpeed = NumberRange.new(-8, 8)
        wisps.EmissionDirection = Enum.NormalId.Top
        wisps.Rate = 4
        wisps.Parent = part
    elseif preset == "GoldenMotes" then
        -- rising from the Hatching Altar's pool of golden Qi
        local motes = Instance.new("ParticleEmitter")
        motes.Name = "GoldenMotes"
        motes.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        motes.Color = ColorSequence.new(Color3.fromRGB(255, 236, 160), Color3.fromRGB(255, 170, 40))
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.2, 0.4), NumberSequenceKeypoint.new(1, 0) })
        motes.Transparency = NumberSequence.new(0.1, 1)
        motes.Lifetime = NumberRange.new(2.5, 4)
        motes.Speed = NumberRange.new(1, 2.2)
        motes.SpreadAngle = Vector2.new(25, 25)
        motes.Rotation = NumberRange.new(0, 360)
        motes.RotSpeed = NumberRange.new(-40, 40)
        motes.Drag = 0.4
        motes.EmissionDirection = Enum.NormalId.Top
        motes.Rate = 10
        motes.Parent = part
    elseif preset == "QiMotes" then
        -- drifting up round the World Tree's trunk (the veins' part spans it)
        local motes = Instance.new("ParticleEmitter")
        motes.Name = "QiMotes"
        motes.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        motes.Color = ColorSequence.new(Color3.fromRGB(150, 245, 255), Color3.fromRGB(40, 210, 235))
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.25, 0.45), NumberSequenceKeypoint.new(1, 0) })
        motes.Transparency = NumberSequence.new(0.15, 1)
        motes.Lifetime = NumberRange.new(4, 6)
        motes.Speed = NumberRange.new(1.5, 3)
        motes.SpreadAngle = Vector2.new(20, 20)
        motes.Rotation = NumberRange.new(0, 360)
        motes.RotSpeed = NumberRange.new(-30, 30)
        motes.Drag = 0.3
        motes.EmissionDirection = Enum.NormalId.Top
        motes.Rate = 14
        motes.Parent = part
    elseif preset == "Smoke" then
        -- slow soft puffs that swell, thin out and lean downwind
        local smoke = Instance.new("ParticleEmitter")
        smoke.Name = "Smoke"
        smoke.Texture = "rbxasset://textures/particles/smoke_main.dds"
        smoke.Color = ColorSequence.new(Color3.fromRGB(70, 66, 66), Color3.fromRGB(150, 148, 150))
        smoke.LightEmission = 0
        smoke.LightInfluence = 1
        smoke.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(1, 6) })
        smoke.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.3, 0.6),
            NumberSequenceKeypoint.new(1, 1) })
        smoke.Lifetime = NumberRange.new(4, 6)
        smoke.Speed = NumberRange.new(2, 3)
        smoke.SpreadAngle = Vector2.new(10, 10)
        smoke.Acceleration = Vector3.new(1.2, 0.4, 0.5)
        smoke.Drag = 0.3
        smoke.Rotation = NumberRange.new(0, 360)
        smoke.RotSpeed = NumberRange.new(-15, 15)
        smoke.EmissionDirection = Enum.NormalId.Top
        smoke.Rate = 4
        smoke.Parent = part
    end
end

-- Pieces split by material (tools/blender/world/hub_finish.py: the hub since 2026-11-12) come as
-- <piece>__<Material>, one MeshPart each, untextured: each takes a real Roblox material, so the hub
-- reads as stone and metal, not painted plastic (the owner: "make it feel realistic").
WorldBuilder.MaterialLooks = {
    Marble = { Material = Enum.Material.Marble, Color = Color3.fromRGB(238, 236, 232) },
    Shade = { Material = Enum.Material.Marble, Color = Color3.fromRGB(176, 176, 180) }, -- grout lines, undersides
    Lapis = { Material = Enum.Material.Marble, Color = Color3.fromRGB(40, 62, 138) },
    Gold = { Material = Enum.Material.Metal, Color = Color3.fromRGB(255, 172, 48) }, -- warm, so Metal's sky reflection reads gold, not olive
                                                                                     -- (242, 194, 82 went olive on the vault's dome, seen in Studio 2026-11-15)
    GoldFlat = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(226, 176, 70) }, -- gold faces looking straight up: Metal mirrored the sky on them, green-olive
    Steel = { Material = Enum.Material.Metal, Color = Color3.fromRGB(170, 176, 186) },
    Slate = { Material = Enum.Material.Slate, Color = Color3.fromRGB(64, 66, 76) },
    Crystal = { Material = Enum.Material.Glass, Color = Color3.fromRGB(175, 215, 255), Transparency = 0.35, CastShadow = false },
    Glow = { Material = Enum.Material.Neon, Color = Color3.fromRGB(226, 240, 255), CastShadow = false, CanCollide = false },
    -- the Blossom Sanctuary (blossom_assets.py): a dark plum-brown bark, two tones of blossom, warm ivory water-worn stone, moss, the
    -- pond's life and the koi. Only the bark and the stone collide.
    Bark = { Material = Enum.Material.Wood, Color = Color3.fromRGB(86, 60, 58) },
    -- (judged in Studio after the import, 2026-11-16: the paler 250, 214, 226 read as white cotton; Sand and LeafyGrass greyed the
    -- pinks to a dusty mauve; a deeper rose in SmoothPlastic reads as blossom)
    Blossom = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(222, 118, 158), CanCollide = false },
    BlossomPale = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(244, 178, 204), CanCollide = false },
    Stone = { Material = Enum.Material.Limestone, Color = Color3.fromRGB(196, 186, 170) }, -- (222, 212, 192 read stark white in the sun)
    Moss = { Material = Enum.Material.LeafyGrass, Color = Color3.fromRGB(96, 126, 70), CanCollide = false },
    Lily = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(74, 124, 66), CanCollide = false, CastShadow = false },
    LilyFlower = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(252, 238, 242), CanCollide = false, CastShadow = false },
    Reed = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(102, 138, 78), CanCollide = false, CastShadow = false },
    KoiWhite = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(246, 243, 236), CanCollide = false, CastShadow = false },
    KoiRed = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(226, 82, 40), CanCollide = false, CastShadow = false },
    KoiBlack = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(32, 30, 32), CanCollide = false, CastShadow = false },
    KoiGold = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(240, 182, 72), Reflectance = 0.12, CanCollide = false, CastShadow = false },
    KoiFin = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(250, 238, 226), Transparency = 0.35, CanCollide = false, CastShadow = false },
    Ripple = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(235, 250, 255), Transparency = 1, CanCollide = false, CastShadow = false },
    -- the shrine on the Lookout (blossom_assets.py, 2026-11-16): a Japanese Shinto shrine in the sanctuary's palette: a matte
    -- vermilion on the torii and the railings, natural cedar, white plaster, a dark cypress-bark roof with verdigris copper trims,
    -- a straw shimenawa rope
    Lacquer = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(176, 58, 44) },
    RoofDark = { Material = Enum.Material.Wood, Color = Color3.fromRGB(58, 46, 44) },
    Copper = { Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(104, 140, 122) },
    Timber = { Material = Enum.Material.Wood, Color = Color3.fromRGB(150, 112, 82) },
    Plaster = { Material = Enum.Material.Plaster, Color = Color3.fromRGB(236, 230, 220) },
    Rope = { Material = Enum.Material.Fabric, Color = Color3.fromRGB(206, 182, 124), CanCollide = false },
    ShrineWater = { Material = Enum.Material.Glass, Color = Color3.fromRGB(110, 170, 170), Transparency = 0.35, CanCollide = false, CastShadow = false },
    -- the Hall of Records (hall_records.py, 2026-11-16): its own stone circle, not the celestial city's: near-black basalt, weathered
    -- bronze with green patina in its recesses, a dark slate court and flags, deep wine banners, the hourglass's glass and sand, the
    -- Chronicle's parchment, the notice board's timber (Timber, above). (Names of their own: Cloth and Glass are the hub's people's)
    Basalt = { Material = Enum.Material.Basalt, Color = Color3.fromRGB(66, 63, 66) },
    -- (judged in Studio after the import, 2026-11-17: 150, 100, 56 read as bright orange copper, CorrodedMetal as rust; a dark
    -- brown in Metal reads as old bronze, the sky's reflection lifting its edges)
    Bronze = { Material = Enum.Material.Metal, Color = Color3.fromRGB(108, 80, 50) },
    Patina = { Material = Enum.Material.CorrodedMetal, Color = Color3.fromRGB(92, 136, 116) },
    Flagstone = { Material = Enum.Material.Slate, Color = Color3.fromRGB(78, 76, 80) },
    Banner = { Material = Enum.Material.Fabric, Color = Color3.fromRGB(112, 30, 44), CanCollide = false },
    Parchment = { Material = Enum.Material.Fabric, Color = Color3.fromRGB(226, 208, 170) },
    SandGlass = { Material = Enum.Material.Glass, Color = Color3.fromRGB(226, 220, 204), Transparency = 0.55, CanCollide = false, CastShadow = false },
    Sand = { Material = Enum.Material.Sand, Color = Color3.fromRGB(222, 170, 92), CanCollide = false, CastShadow = false },
}

local function splitName(name)
    local base, material = string.match(name, "^(.-)__(%a+)$")
    return base or name, material
end
WorldBuilder.splitName = splitName

local function setLook(part, look)
    if look.Material then
        part.TextureID = "" -- Neon and Glass pieces are coloured, not textured
    end
    for property, value in look do
        if property == "Tag" then
            CollectionService:AddTag(part, value)
        else
            part[property] = value
        end
    end
    if look.CanCollide == false then
        part.CanQuery = false
    end
end

-- A piece's look: its material's (when split by material), then WorldBuilder.Appearance for the piece
-- (keyed by its template's name, without the material suffix), then for the exact part.
local function applyLook(part, name)
    name = name or part.Name
    local base, material = splitName(name)
    local matLook = material and WorldBuilder.MaterialLooks[material]
    if matLook then
        setLook(part, matLook)
    end
    if base ~= name and WorldBuilder.Appearance[base] then
        setLook(part, WorldBuilder.Appearance[base])
    end
    local look = WorldBuilder.Appearance[name]
    if look then
        setLook(part, look)
    end
end

local function prepareMesh(part)
    part.Anchored = true
    part.CanTouch = false
    part.Massless = true
    applyLook(part)
end

local function collisionRule(part)
    for _, rule in WorldBuilder.Collision do
        if string.sub(part.Name, 1, #rule.Prefix) == rule.Prefix then
            return rule.Fidelity
        end
    end
    return nil
end

-- Applies the collision rules to every MeshPart under a container. A piece that neither collides nor
-- can be touched gets a plain box; one that can be touched (the lava) keeps its rule, since Touched
-- uses the collision shape. Studio applies a new CollisionFidelity asynchronously, so check the
-- result with checkCollision in a later call.
function WorldBuilder.applyCollision(container)
    for _, part in container:GetDescendants() do
        local fidelity = part:IsA("MeshPart") and collisionRule(part)
        if fidelity then
            part.CollisionFidelity = if part.CanCollide or part.CanTouch then fidelity else Enum.CollisionFidelity.Box
        end
    end
end

-- Names of the MeshParts under a container whose collision does not match its rule.
function WorldBuilder.checkCollision(container)
    local wrong = {}
    for _, part in container:GetDescendants() do
        local fidelity = part:IsA("MeshPart") and collisionRule(part)
        if fidelity and not part.CanCollide and not part.CanTouch then
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

-- An island's frame: its centre, turned by its quarter turns. Island-local positions (the
-- placements, the meshes as authored) go through it into the world.
local frames = {} -- [island] = CFrame: a terrain module is large, so it is read once per require of this module
local function islandFrame(island)
    if not frames[island] then
        local data = require(ServerStorage.WorldBuild.Terrain:FindFirstChild(island):Clone())
        frames[island] = CFrame.new(data.Centre) * CFrame.Angles(0, -(data.Turns or 0) * math.pi / 2, 0)
    end
    return frames[island]
end
WorldBuilder.islandFrame = islandFrame

local function islandPoint(island, localPosition)
    return islandFrame(island):PointToWorldSpace(localPosition)
end

-- Seats an imported island-mesh model (exported with an anchor cube at the island centre) into
-- FloatingIslands.<island>.<child>, replacing what was there, and removes the import model.
function WorldBuilder.seatImport(island, model, anchorName, child)
    local anchor = model:FindFirstChild(anchorName)
    assert(anchor, "import is missing its anchor " .. anchorName)
    local target = islandFrame(island) * IMPORT_TURN
    local folder = WorldBuilder.islandFolder(island, child)
    folder:ClearAllChildren()
    local frame = anchor.CFrame
    anchor:Destroy()
    for _, part in model:GetChildren() do
        if part:IsA("MeshPart") then
            part.CFrame = target * frame:ToObjectSpace(part.CFrame)
            prepareMesh(part)
            for _, preset in WorldBuilder.Emitters[part.Name] or {} do
                addEmitterPreset(part, preset)
            end
            part.Parent = folder
        end
    end
    model:Destroy()
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- Every map's own templates (the owner, 2026-11-22: "every map must have its own dedicated asset collection"; none shared): one folder per map in
-- ServerStorage.WorldAssets, named as the owner asked. A kit is addressed by its key (an island's name, or a Murim territory's): the one place that
-- knows where it lives. WorldBuilder.assetPath(key) lists the folders, WorldBuilder.kitFolder(key, create) finds (or makes) it. Templates are
-- build-time only: the placed copies are saved in the place, and nothing here is replicated to players.
local KIT_PATHS = {
    Yggdrasil = { "YggdrasilAssets" },
    BeginnerIsle = { "BeginnerIslandAssets" },
    JadeGrove = { "JadeGroveAssets" },
    EmberPeak = { "EmberPeakAssets" },
    MoonlitIsle = { "MoonlitIsleAssets" },
    OriginAbyss = { "OriginAbyssAssets" },
    BlossomSanctuary = { "BlossomSanctuaryAssets" },
    Dawnspire = { "MurimAssets", "DawnspireAssets" },
    Windrift = { "MurimAssets", "WindriftAssets" },
    Nightfall = { "MurimAssets", "NightfallAssets" },
    Trial = { "MurimAssets", "TrialAssets" }, -- the three faction trials' props (TrialBuilder: a gate, a token, a dummy)
    HubNpcs = { "NpcAssets" }, -- people, not environment
}

function WorldBuilder.assetPath(key)
    return assert(KIT_PATHS[key], "no asset folder for " .. tostring(key))
end

function WorldBuilder.kitFolder(key, create)
    local folder = ServerStorage:FindFirstChild("WorldAssets")
    if not folder and create then
        folder = Instance.new("Folder")
        folder.Name = "WorldAssets"
        folder.Parent = ServerStorage
    end
    for _, name in WorldBuilder.assetPath(key) do
        local nextFolder = folder and folder:FindFirstChild(name)
        if not nextFolder and create then
            nextFolder = Instance.new("Folder")
            nextFolder.Name = name
            nextFolder.Parent = folder
        end
        folder = nextFolder
    end
    return folder
end
local kitFolder = WorldBuilder.kitFolder

-- Moves the meshes of an imported kit model (exported at the Blender origin) into
-- ServerStorage.WorldAssets.<its map's folder> (kitFolder) as templates, each CFrame relative to its authored origin.
-- The origin is the anchor cube when the export has one, otherwise the model pivot.
function WorldBuilder.storeKit(island, model, anchorName)
    local folder = kitFolder(island, true)
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

-- A piece's templates: the one named `name`, or its material parts (<name>__Marble, <name>__Gold, ...).
local function templates(island, name)
    local folder = kitFolder(island)
    local part = folder:FindFirstChild(name)
    if part then
        return { part }
    end
    local list = {}
    for _, child in folder:GetChildren() do
        if child:IsA("MeshPart") and splitName(child.Name) == name and child.Name ~= name then
            table.insert(list, child)
        end
    end
    assert(#list > 0, "missing kit template " .. name .. " (import and store the island's kit first)")
    table.sort(list, function(a, b) return a.Name < b.Name end)
    return list
end

local function template(island, name)
    return templates(island, name)[1]
end

-- Places a template (every material part of it) so its authored origin lands on `frame`, optionally scaled
-- about that origin (a number, or a Vector3 per axis for a template turned only about Y); returns its first part. Its look comes from the material and WorldBuilder.Appearance as
-- they are now, not as they were when the template was stored.
local function placeTemplate(island, name, frame, parent, scale)
    scale = scale or 1
    local first
    for _, source in templates(island, name) do
        local part = source:Clone()
        part.Size = source.Size * scale
        part.CFrame = frame * (source.CFrame.Rotation + source.CFrame.Position * scale)
        applyLook(part, source.Name)
        part.Parent = parent
        first = first or part
    end
    return first
end

-- The new pieces for the outer islands come in one import (assets/world/IslandUpgrades/IslandUpgrades.fbx, with no textures of its own): each goes to its
-- island's kit by its name's prefix, painted with the atlas that island's kit already has uploaded.
local UPGRADE_ISLANDS = {
    JG = { Island = "JadeGrove", Atlas = "JG_AncientTreeA" },
    EP = { Island = "EmberPeak", Atlas = "EP_BasaltClusterA" },
    MI = { Island = "MoonlitIsle", Atlas = "MI_LunarRock" },
    OA = { Island = "OriginAbyss", Atlas = "OA_SlateRock" },
    YG = { Island = "Yggdrasil", Atlas = "SI_MossRockA" },
    BI = { Island = "BeginnerIsle", Atlas = "SI_MossRockA" },
}
function WorldBuilder.storeUpgrades(model)
    local anchor = model:FindFirstChild("IU_Anchor")
    assert(anchor, "import is missing its anchor IU_Anchor")
    local origin = anchor.CFrame
    anchor:Destroy()
    local stored = {}
    for _, part in model:GetChildren() do
        if part:IsA("MeshPart") then
            local where = UPGRADE_ISLANDS[string.sub(part.Name, 1, 2)]
            assert(where, "no island for the piece " .. part.Name)
            local folder = kitFolder(where.Island)
            local old = folder:FindFirstChild(part.Name)
            if old then
                old:Destroy()
            end
            part.CFrame = IMPORT_TURN * origin:ToObjectSpace(part.CFrame)
            part.TextureID = folder[where.Atlas].TextureID
            for _, child in part:GetChildren() do
                if child:IsA("SurfaceAppearance") then
                    child:Destroy()
                end
            end
            prepareMesh(part)
            part.Parent = folder
            table.insert(stored, part.Name)
        end
    end
    model:Destroy()
    for _, where in UPGRADE_ISLANDS do
        WorldBuilder.applyCollision(kitFolder(where.Island))
    end
    return stored
end

-- Points templates that were exported with the same atlas at one uploaded copy of it, so the
-- texture is loaded once (each FBX import uploads its own copy).
function WorldBuilder.shareTexture(island, sourceName, names)
    local folder = kitFolder(island)
    local textureId = template(island, sourceName).TextureID
    for _, name in names do
        local part = folder:FindFirstChild(name)
        if part and part.TextureID ~= "" then
            part.TextureID = textureId
        end
    end
end

local function standFrame(island, entry)
    return islandFrame(island) * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
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

-- Decorative pieces that give way to a bridge: placeKit leaves out any standing where a bridge comes
-- onto an island (its span and its abutment), so moving or widening a bridge never needs
-- an island's seeded scatter re-run.
WorldBuilder.ClearOfBridges = {
    MI_MoonstoneSpire = true, MI_MoonstoneShards = true, MI_LunarRock = true, MI_FrostLilies = true, MI_LilyGlow = true,
    EP_ObsidianShard = true, EP_BasaltClusterA = true, EP_BasaltClusterB = true, EP_FireCrystal = true,
    EP_EmberVent = true, EP_VentGlow = true,
    JG_JadeOutcrop = true, JG_FallenLog = true, JG_Fern = true, JG_Mushrooms = true, JG_MushroomCaps = true,
    JG_AncientTreeA = true, JG_AncientTreeB = true, JG_BambooClump = true,
    OA_SlateRock = true, OA_VoidCrystals = true, OA_VoidCrystalGlow = true,
    SI_SpiritPineA = true, SI_SpiritPineB = true, SI_BlossomTreeA = true, SI_BlossomTreeB = true,
    SI_MossRockA = true, SI_MossRockB = true, SI_FlowersWarm = true, SI_FlowersWhite = true, SI_FlowersViolet = true,
}

-- Each bridge's span, flat, to 10 studs past its end (its abutment).
local function bridgeEnds()
    local bridges = require(ServerStorage.WorldBuild.Placements.Bridges:Clone())
    local ends = {}
    for _, bridge in bridges.Bridges do
        local nodes = bridge.Nodes
        local from = nodes[1].Position
        local run = (nodes[#nodes].Position - from) * Vector3.new(1, 0, 1)
        table.insert(ends, { From = from, Along = run.Unit, Length = run.Magnitude + 10, Half = bridges.DeckWidth / 2 + 2 })
    end
    return ends
end

local function onBridgeEnd(ends, position)
    for _, e in ends do
        local offset = (position - e.From) * Vector3.new(1, 0, 1)
        local along = offset:Dot(e.Along)
        if along >= 0 and along <= e.Length and (offset - e.Along * along).Magnitude <= e.Half then
            return true
        end
    end
    return false
end

-- Clones the kit templates to every Kit placement in Placements.<island> (FloatingIslands.<island>.Kit).
function WorldBuilder.placeKit(island)
    local placements = placementsFor(island)
    local centre = islandFrame(island)
    local folder = WorldBuilder.islandFolder(island, "Kit")
    folder:ClearAllChildren()
    local ends = bridgeEnds()
    local placed = 0
    local missing = {}
    for name, list in placements.Kit do
        -- a piece whose kit isn't stored yet (an FBX still to import) is left out and named, not an error
        if not pcall(templates, island, name) then
            table.insert(missing, name)
            continue
        end
        for index, entry in list do
            local frame = centre * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
            if WorldBuilder.ClearOfBridges[name] and onBridgeEnd(ends, frame.Position) then
                continue
            end
            local part = placeTemplate(island, name, frame, folder, entry.Scale)
            part.Name = name .. "_" .. index
            local light = WorldBuilder.Lights[name]
            if light then
                addLight(part, light.Color or part.Color, light.Range, light.Brightness)
            end
            for _, preset in WorldBuilder.Emitters[name] or {} do
                addEmitterPreset(part, preset)
            end
            placed += 1
        end
    end
    WorldBuilder.applyCollision(folder)
    if #missing > 0 then
        table.sort(missing)
        warn("placeKit(" .. island .. "): not in the kit yet, left out: " .. table.concat(missing, ", "))
    end
    return placed, missing
end

-- ---------- the hub's people (tools/blender/npcs/hub_npcs.py; the owner approved them 2026-11-12) ----------
-- Each NPC is Roblox's default R15 body, its part colours its base clothes, dressed in pieces stored from assets/npcs/HubNpcs.fbx
-- (WB.storeKit("HubNpcs", <import>, "NPC_Anchor")): ServerStorage.WorldAssets.NpcAssets.<Npc>_<Piece>__<Material>, each welded to the
-- body part Placements/HubNpcs.lua names, in the colour and Roblox material it gives. The stock painted face is cleared: each has
-- its own, modelled. Their root is anchored; NpcService plays their idle. Tagged "HubNpc".
--   WB.buildHubNpcs("Yggdrasil")       the Blacksmith's, the Auction House's and Buy & Sell's keepers and the Guide (who talks:
--                                      her prompt has the Guide attribute, GuideController)
--   WB.buildMerchantTemplate("Yggdrasil")  ServerStorage.WanderingMerchant: his camp and him, where MerchantService puts them
local function npcData()
    return require(ServerStorage.WorldBuild.Placements.HubNpcs:Clone())
end

local function dressPiece(template, data, owner, at, parent, weldTo)
    local base, material = splitName(template.Name)
    local piece = template:Clone()
    piece.CFrame = at * template.CFrame
    piece.TextureID = ""
    piece.Material = data.Materials[material] or Enum.Material.SmoothPlastic
    local colour = data.Colours[owner] and data.Colours[owner][string.sub(base, #owner + 2) .. "__" .. material]
    if colour then
        piece.Color = colour
    end
    piece.Transparency = if material == "Glass" then 0.35 else 0
    -- (a face's eyes, lashes, mouth and blush lie on the head: they cast no shadow anyone could see; performance pass, 2026-11-17)
    piece.CastShadow = material ~= "Glow" and material ~= "Glass" and material ~= "Face"
    piece.CanTouch = false
    if weldTo then
        piece.Anchored = false
        piece.Massless = true
        piece.CanCollide = false
        piece.CanQuery = false
        local weld = Instance.new("WeldConstraint")
        weld.Part0 = weldTo
        weld.Part1 = piece
        weld.Parent = piece
    else
        piece.Anchored = true
    end
    piece.Parent = parent
    return piece
end

function WorldBuilder.buildNpc(npc, rootCFrame, data)
    data = data or npcData()
    local body = data.Body[npc]
    assert(body, "no NPC " .. npc .. " in Placements.HubNpcs")
    local description = Instance.new("HumanoidDescription")
    description.HeadColor = body.Head
    description.TorsoColor = body.Torso
    description.LeftArmColor, description.RightArmColor = body.Arms, body.Arms
    description.LeftLegColor, description.RightLegColor = body.Legs, body.Legs
    local rig = Players:CreateHumanoidModelFromDescription(description, Enum.HumanoidRigType.R15)
    rig.Name = npc
    local stockAnimate = rig:FindFirstChild("Animate")
    if stockAnimate then
        stockAnimate:Destroy() -- (a LocalScript in the Workspace never runs; NpcService plays the idle on the server)
    end
    rig.Head.TextureID = "" -- the stock face: each NPC wears its own
    rig:PivotTo(rootCFrame)
    rig.HumanoidRootPart.Anchored = true
    local kit = kitFolder("HubNpcs")
    for _, template in kit:GetChildren() do
        local base = splitName(template.Name)
        if template:IsA("MeshPart") and string.sub(base, 1, #npc + 1) == npc .. "_" then
            local bodyPart = rig:FindFirstChild(data.Pieces[base] or "")
            assert(bodyPart, template.Name .. " rides no body part")
            dressPiece(template, data, npc, rootCFrame, rig, bodyPart)
        end
    end
    for _, part in rig:GetDescendants() do
        if part:IsA("BasePart") then
            part.CanTouch = false -- (nothing listens for an NPC being touched: only lava does, WorldService)
        end
    end
    local humanoid = rig:FindFirstChildOfClass("Humanoid")
    humanoid.DisplayName = data.Titles[npc] or npc
    humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
    humanoid.NameDisplayDistance = 45
    humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
    CollectionService:AddTag(rig, "HubNpc")
    return rig
end

function WorldBuilder.buildHubNpcs(island)
    local placements = placementsFor(island)
    local data = npcData()
    local folder = WorldBuilder.islandFolder(island, "Npcs")
    folder:ClearAllChildren()
    for npc, spot in placements.Npcs do
        local rig = WorldBuilder.buildNpc(npc, islandFrame(island) * CFrame.new(spot.Position) * CFrame.Angles(0, spot.Yaw, 0), data)
        if npc == "Guide" then
            local prompt = Instance.new("ProximityPrompt")
            prompt.ActionText = "Talk"
            prompt.ObjectText = data.Titles.Guide
            prompt.KeyboardKeyCode = Enum.KeyCode.F
            prompt.HoldDuration = 0
            prompt.MaxActivationDistance = 10
            prompt.RequiresLineOfSight = false
            prompt:SetAttribute("Guide", true)
            prompt.Parent = rig.HumanoidRootPart
        end
        rig.Parent = folder
    end
    return #folder:GetChildren()
end

function WorldBuilder.buildMerchantTemplate(island)
    local placements = placementsFor(island)
    local data = npcData()
    local spot = placements.Merchant
    local frame = islandFrame(island) * CFrame.new(spot.Centre) * CFrame.Angles(0, spot.Yaw, 0)
    local old = ServerStorage:FindFirstChild("WanderingMerchant")
    if old then
        old:Destroy()
    end
    local model = Instance.new("Model")
    model.Name = "WanderingMerchant"
    local camp = Instance.new("Model")
    camp.Name = "Camp"
    camp.Parent = model
    for _, template in kitFolder("HubNpcs"):GetChildren() do
        if template:IsA("MeshPart") and string.sub(template.Name, 1, 5) == "Camp_" then
            local piece = dressPiece(template, data, "Camp", frame, camp, nil)
            piece.CanCollide = string.find(template.Name, "Crates") ~= nil or string.find(template.Name, "Chest_") ~= nil
            if string.find(template.Name, "LanternLight") then
                addLight(piece, Color3.fromRGB(255, 196, 106), 14, 0.9)
            end
        end
    end
    -- he stands at the back of his rug, facing the tree (his front is -Z: turned half round)
    local merchant = WorldBuilder.buildNpc("Merchant", frame * CFrame.new(0, 3.192, -0.6) * CFrame.Angles(0, math.pi, 0), data)
    merchant.Parent = model
    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Trade"
    prompt.ObjectText = data.Titles.Merchant
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt.Parent = merchant.HumanoidRootPart
    model.PrimaryPart = merchant.HumanoidRootPart
    model.Parent = ServerStorage
    return model
end

-- ---------- egg stands ----------

-- Saturated glow colours per egg (Neon blooms pale colours to white).
WorldBuilder.EggGlow = GameConfig.EggGlow

-- The egg's light per island ({ range, brightness }) where the default (12, 1.2) is too much: on
-- Origin Abyss it painted the bronze thorn branches red and violet (seen in Play).
local EGG_LIGHT = { OriginAbyss = { 6, 0.8 } }

-- Places the egg on a stand exactly as the game does when one respawns there (EggStands.show), so the
-- two never differ: built by EggModel, its centre `height / 2` over the rest point, facing as `rest` does.
local function placeEgg(stand, eggId, rest)
    local folder = ServerStorage:FindFirstChild("EggMeshes")
    local source = folder and folder:FindFirstChild(eggId)
    assert(source and source:IsA("Model"), "missing egg mesh ServerStorage.EggMeshes." .. eggId)
    local _, boxSize = source:GetBoundingBox()
    local height = boxSize.Y * GameConfig.EggStudsPerUnit
    local model = EggModel.build(eggId, height)
    model:PivotTo(CFrame.new(rest.Position + Vector3.new(0, height / 2, 0)) * rest.Rotation)
    local body = model.PrimaryPart
    body.Anchored = true
    for _, part in model:GetChildren() do
        part.Parent = stand
    end
    model:Destroy()
    return body
end

-- Replaces ServerStorage.EggMeshes.<eggId> with an imported egg model (its parts keep their
-- names: <EggId>_Body and <EggId>_Glow_<hex>).
function WorldBuilder.storeEgg(model, eggId)
    assert(model:FindFirstChild(eggId .. "_Body", true), "the import has no " .. eggId .. "_Body")
    local folder = ServerStorage:FindFirstChild("EggMeshes")
    if not folder then
        folder = Instance.new("Folder")
        folder.Name = "EggMeshes"
        folder.Parent = ServerStorage
    end
    local old = folder:FindFirstChild(eggId)
    if old then
        old:Destroy()
    end
    local stored = Instance.new("Model")
    stored.Name = eggId
    for _, part in model:GetDescendants() do
        if part:IsA("MeshPart") then
            part.Anchored = true
            part.Parent = stored
        end
    end
    model:Destroy()
    stored.Parent = folder
    return #stored:GetChildren()
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
        local pedestal = placeTemplate(island, pieces.Pedestal, frame, stand, entry.Scale)
        pedestal.Name = "Pedestal"
        local ring = placeTemplate(island, pieces.GlowRing, frame, stand, entry.Scale)
        ring.Name = "GlowRing"
        ring.Position += Vector3.new(0, pieces.RingLift or 0, 0)
        ring.Color = glow

        -- where an egg rests on this stand, facing its front (EggStands puts any of the island's eggs here)
        local point = frame.Position + Vector3.new(0, entry.EggRest, 0)
        local rest = CFrame.lookAt(point, point - frame.LookVector)
        stand:SetAttribute("EggRest", rest)
        local egg = placeEgg(stand, entry.EggId, rest)
        local eggLight = EGG_LIGHT[island] or { 12, 1.2 }
        addLight(egg, glow, eggLight[1], eggLight[2])

        local prompt = Instance.new("ProximityPrompt")
        prompt.ActionText = "Take" -- EggStands drives it in play
        prompt.ObjectText = eggConfig.DisplayName
        prompt.KeyboardKeyCode = Enum.KeyCode.F
        prompt.HoldDuration = 0.5
        prompt.MaxActivationDistance = 10
        prompt.RequiresLineOfSight = false
        prompt.Parent = pedestal

        stand.Parent = folder
    end
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- ---------- route names ----------

-- Each bridge's destination: buildBridges writes it on the bridge (Destination, Island). (The waystones
-- that once carried these names, and buildWaystones, were removed 2026-11-13.)
WorldBuilder.Routes = {
    JadeRoute = { Island = "JadeGrove", Title = "Jade Grove" },
    EmberRoute = { Island = "EmberPeak", Title = "Ember Peak" },
    MoonlitRoute = { Island = "MoonlitIsle", Title = "Moonlit Isle" },
    BeginnerRoute = { Island = "BeginnerIsle", Title = "Beginner Isle" },
    OriginRoute = { Island = "OriginAbyss", Title = "Origin Abyss" },
    MurimRoute = { Island = "MurimCrossing", Title = "Murim Crossing" },
}

-- An invisible anchored part that nothing touches: a panel to write on, or a marker.
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

-- ---------- text panels (the shops' name boards) ----------

-- An invisible part carrying a SurfaceGui on its +Z face (the face a kit's text panel looks out of).
local function textPanel(name, size, cframe, parent, pixelsPerStud)
    local panel = marker(name, Vector3.new(size.X, size.Y, 0.05), cframe, parent)
    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Back
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = pixelsPerStud
    gui.LightInfluence = 0.2
    gui.MaxDistance = 160
    gui.Parent = panel
    return panel, gui
end

local function steleLabel(name, parent, size, position, alignment, color)
    local label = Instance.new("TextLabel")
    label.Name = name
    label.Size = size
    label.Position = position
    label.BackgroundTransparency = 1
    label.Font = Enum.Font.Garamond
    label.TextScaled = true
    label.TextColor3 = color
    label.TextXAlignment = alignment
    label.Text = ""
    label.Parent = parent
    return label
end


-- An invisible, neutral SpawnLocation (no decal, no forcefield).
local function spawnPoint(name, cframe, parent)
    local spawn = Instance.new("SpawnLocation")
    spawn.Name = name
    spawn.Size = Vector3.new(6, 1, 6)
    spawn.CFrame = cframe
    spawn.Transparency = 1
    spawn.Anchored = true
    spawn.CanCollide = false
    spawn.CanQuery = false
    spawn.Neutral = true
    spawn.Duration = 0
    for _, child in spawn:GetChildren() do
        child:Destroy() -- the default decal
    end
    spawn.Parent = parent
    return spawn
end

-- ---------- bridges ----------
-- The bridges from Yggdrasil to the other five islands (Placements/Bridges.lua). Each is a Model
-- in FloatingIslands.Bridges: one straight span, a deck along its nodes in pieces of up to Segment
-- studs, low rails, and at its start a gate whose Qi barrier (tagged
-- GameConfig.BridgeBarrierTag) stops everyone below its RankId (BridgeBarriers.client lets qualified
-- players through; WorldService returns the rest). Zone parts past the gate tell the server who is
-- on the bridge. The deck and rails are the collision, a plain blockout until the themed kit dresses
-- them.
-- The hub's bridge gates (hub_celestial.bridge_gate): the island each leads to, on the board under its arch, and where that board
-- sits in the gate's frame (hub_celestial.BG_PLAQUE, just off its lapis face).
WorldBuilder.GateNames = {
    BeginnerRoute = "Beginner Isle", JadeRoute = "Jade Grove", EmberRoute = "Ember Peak", MoonlitRoute = "Moonlit Isle", OriginRoute = "Origin Abyss",
    MurimRoute = "Murim Crossing",
}
WorldBuilder.GatePlaque = { Centre = Vector3.new(0, 18.2, 1.63), Size = Vector2.new(12, 2) }

WorldBuilder.BridgeThemes = {
    Jade = { Deck = Color3.fromRGB(150, 110, 70), DeckMaterial = Enum.Material.WoodPlanks, Rail = Color3.fromRGB(80, 160, 110), Glow = Color3.fromRGB(40, 215, 110) },
    Ember = { Deck = Color3.fromRGB(55, 48, 46), DeckMaterial = Enum.Material.Basalt, Rail = Color3.fromRGB(35, 30, 30), Glow = Color3.fromRGB(255, 105, 25) },
    Moon = { Deck = Color3.fromRGB(225, 225, 235), DeckMaterial = Enum.Material.Marble, Rail = Color3.fromRGB(215, 185, 110), Glow = Color3.fromRGB(120, 100, 255) },
    Lion = { Deck = Color3.fromRGB(176, 164, 142), DeckMaterial = Enum.Material.Slate, Rail = Color3.fromRGB(150, 40, 30), Glow = Color3.fromRGB(255, 170, 60) },
    Origin = { Deck = Color3.fromRGB(60, 58, 70), DeckMaterial = Enum.Material.Slate, Rail = Color3.fromRGB(40, 38, 50), Glow = Color3.fromRGB(175, 45, 255) },
    -- Murim Crossing's bridge (open to every rank: no Qi barrier, no rank): the Moonlit Isle's marble deck with gold rails, which sits well
    -- with the hub's own marble and gold and has nothing red or Chinese in it. Kit: which stored kit dresses it. Glow: the hub gate's crystal
    -- (and the supports' glow) in a warm ivory, apart from the other bridges' colours.
    Murim = { Kit = "Moon", Deck = Color3.fromRGB(225, 225, 235), DeckMaterial = Enum.Material.Marble, Rail = Color3.fromRGB(215, 185, 110), Glow = Color3.fromRGB(246, 226, 170) },
}
local BRIDGE = { Segment = 12, Thickness = 2, RailHeight = 3, RailWidth = 0.8, GateHeight = 14.4, GateInset = 5, ZoneHeight = 16,
    AbutmentLength = 8, AbutmentDepth = 7 }

local function bridgePart(name, size, cframe, parent, color, material)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = cframe
    p.Anchored = true
    p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
    p.Color = color
    p.Material = material or Enum.Material.SmoothPlastic
    p.CanTouch = false -- (nothing listens for a bridge being touched: the server finds players on it by querying its zones)
    p.Parent = parent
    return p
end

-- A solid block carrying a deck's end onto its island, so where the ground falls away at the rim
-- there is stone, not a gap; where the ground is higher it hides in the terrain.
local function abutment(model, theme, width, at, outward)
    local flat = Vector3.new(outward.X, 0, outward.Z).Unit
    local centre = at + flat * (BRIDGE.AbutmentLength / 2) - Vector3.new(0, BRIDGE.AbutmentDepth / 2, 0)
    return bridgePart("Abutment", Vector3.new(width, BRIDGE.AbutmentDepth, BRIDGE.AbutmentLength + 0.4),
        CFrame.lookAt(centre, centre + flat), model, theme.Deck, theme.DeckMaterial)
end

-- one straight piece of deck from a to b (top surface centre line), with its rails and zone
local function deckPiece(model, theme, width, a, b, zoneFolder)
    local length = (b - a).Magnitude
    local frame = CFrame.lookAt((a + b) / 2, b)
    local overlap = 0.4 -- pieces overlap a little so a change of slope leaves no gap
    local deck = bridgePart("Deck", Vector3.new(width, BRIDGE.Thickness, length + overlap), frame * CFrame.new(0, -BRIDGE.Thickness / 2, 0), model, theme.Deck, theme.DeckMaterial)
    model:SetAttribute("Pieces", (model:GetAttribute("Pieces") or 0) + 1)
    deck:SetAttribute("Order", model:GetAttribute("Pieces"))
    for side = -1, 1, 2 do
        bridgePart("Rail", Vector3.new(BRIDGE.RailWidth, BRIDGE.RailHeight, length + overlap),
            frame * CFrame.new(side * (width / 2 - BRIDGE.RailWidth / 2), BRIDGE.RailHeight / 2, 0), model, theme.Rail, Enum.Material.SmoothPlastic)
    end
    if zoneFolder then
        local zone = bridgePart("Zone", Vector3.new(width + 8, BRIDGE.ZoneHeight, length + overlap),
            frame * CFrame.new(0, BRIDGE.ZoneHeight / 2 - 3, 0), zoneFolder, theme.Glow)
        zone.Transparency = 1
        zone.Material = Enum.Material.Plastic -- (see hideCollision)
        zone.CanCollide, zone.CanTouch, zone.CastShadow = false, false, false
        zone.CanQuery = true -- the server finds players on the bridge by querying these
    end
end

-- The themed kits (assets/world/Bridges/<Theme>Bridge.fbx), imported by hand and stored with
-- WB.storeBridgeKit(<import>, theme) in ServerStorage.BridgeKits.<Theme>. Pieces named
-- "<x>_Glow_<rrggbb>" become Neon in that colour; the rest get the maps the importer does not read.
WorldBuilder.BridgeKitMaps = {
    Jade = { Roughness = "rbxassetid://140603311452129", Metalness = "rbxassetid://70674142166061" },
    Ember = { Roughness = "rbxassetid://123446572117201", Metalness = "rbxassetid://87497595865816" },
    Moon = { Roughness = "rbxassetid://108481130424902", Metalness = "rbxassetid://116564473666370" },
    Origin = { Roughness = "rbxassetid://70728910964549", Metalness = "rbxassetid://104078115058483" },
    Lion = { Roughness = "rbxassetid://79869889500676", Metalness = "rbxassetid://125423838770868" },
    -- Moon's extra kit (MoonBridgeExtra.fbx: its level deck), baked apart
    MoonExtra = { Roughness = "rbxassetid://108002843043070", Metalness = "rbxassetid://118382741100339" },
}

-- With `extra`, the import is the theme's extra kit: its pieces join the stored kit (replacing any
-- of the same name) instead of replacing it.
function WorldBuilder.storeBridgeKit(model, theme, extra)
    local root = ServerStorage:FindFirstChild("BridgeKits") or Instance.new("Folder")
    root.Name = "BridgeKits"
    root.Parent = ServerStorage
    local kit = root:FindFirstChild(theme)
    if kit and not extra then
        kit:Destroy()
        kit = nil
    end
    assert(kit or not extra, "store the " .. theme .. " kit before its extra kit")
    kit = kit or Instance.new("Folder")
    kit.Name = theme
    local maps = WorldBuilder.BridgeKitMaps[if extra then theme .. "Extra" else theme]
    for _, m in model:GetDescendants() do
        if m:IsA("MeshPart") then
            local hex = m.Name:match("_Glow_(%x%x%x%x%x%x)$")
            local sa = m:FindFirstChildOfClass("SurfaceAppearance")
            if hex then
                m.Material = Enum.Material.Neon
                m.Color = Color3.fromHex(hex)
                if sa then
                    sa:Destroy()
                end
            elseif sa and maps then
                sa.RoughnessMap, sa.MetalnessMap = maps.Roughness, maps.Metalness
            end
            m.Anchored = true
            m.CanCollide, m.CanQuery, m.CanTouch = false, false, false -- the blockout under it is the collision
            local old = kit:FindFirstChild(m.Name)
            if old then
                old:Destroy()
            end
            m.Parent = kit
        end
    end
    model:Destroy()
    kit.Parent = root
    return #kit:GetChildren()
end

-- A kit piece (and its glow piece, if it has one) placed with its origin at `frame` (the deck's top
-- centre), its length along the frame's Z scaled by `stretch`.
local kitInfo -- Placements/BridgeKits.lua, loaded once per build
local function placeKitPiece(theme, piece, frame, parent, stretch)
    local kits = ServerStorage:FindFirstChild("BridgeKits")
    local kit = kits and kits:FindFirstChild(theme)
    local info = kitInfo[theme]
    if not (kit and info and info[piece]) then
        return nil
    end
    stretch = stretch or 1
    local placed
    for _, entry in { { piece, info[piece] }, { piece .. "Glow", info[piece .. "Glow"] } } do
        local name, data = entry[1], entry[2]
        if data then
            local template = kit:FindFirstChild(theme .. piece .. (data.Hex and ("_Glow_" .. data.Hex) or ""))
            if template then
                local p = template:Clone()
                p.Name = name
                p.Size = Vector3.new(p.Size.X, p.Size.Y, p.Size.Z * stretch)
                -- Studio's importer turns a model half round (x and z flip, as with the eggs): turn it back
                p.CFrame = frame * CFrame.new(data.Offset.X, data.Offset.Y, data.Offset.Z * stretch) * CFrame.Angles(0, math.pi, 0)
                p.Parent = parent
                placed = placed or p
            end
        end
    end
    return placed
end

local SUPPORT_EVERY = { Jade = 3, Ember = 2, Moon = 4, Lion = 3, Origin = 3 } -- deck pieces between supports
local SUPPORT_CLEAR = 24 -- studs from either end with no support (they would sink into the islands)

-- A blockout piece left as invisible collision under the kit. Invisible parts still cost the renderer a batch for each material
-- they're in: all in Plastic, with their old material's footing kept, the hub's view drew about 250 fewer draw calls (2026-11-17).
local function hideCollision(part)
    part.Transparency = 1
    if part.Material ~= Enum.Material.Plastic then
        if part.CustomPhysicalProperties == nil then
            part.CustomPhysicalProperties = PhysicalProperties.new(part.Material)
        end
        part.Material = Enum.Material.Plastic
    end
end

-- Dress a built bridge with its theme's kit, if the kit is stored: a deck section on every
-- piece of deck, supports hanging under it, the gate. The blockout
-- stays as the invisible collision. Returns the number of pieces placed.
local function dressBridge(model, themeName)
    local themeInfo = WorldBuilder.BridgeThemes[themeName]
    local theme = themeInfo and themeInfo.Kit or themeName -- (a theme may wear another's stored kit: Murim wears the Moon's)
    local kits = ServerStorage:FindFirstChild("BridgeKits")
    if not (kits and kits:FindFirstChild(theme)) then
        return 0
    end
    local dressing = Instance.new("Folder")
    dressing.Name = "Kit"
    dressing.Parent = model
    local count = 0
    local decks = {}
    for _, c in model:GetChildren() do
        if c.Name == "Deck" then
            table.insert(decks, c)
        end
    end
    table.sort(decks, function(x, y)
        return x:GetAttribute("Order") < y:GetAttribute("Order")
    end)
    local total = 0
    for _, d in decks do
        total += d.Size.Z - 0.4
    end
    local run = 0
    local bareDeck = false
    for index, deck in decks do
        local length = deck.Size.Z - 0.4
        local top = deck.CFrame * CFrame.new(0, deck.Size.Y / 2, 0)
        if placeKitPiece(theme, "Deck", top, dressing, length / BRIDGE.Segment) then
            count += 1
        else
            bareDeck = true
        end
        local centreRun = run + length / 2
        if index % SUPPORT_EVERY[theme] == 0 and centreRun > SUPPORT_CLEAR and centreRun < total - SUPPORT_CLEAR then
            local flatLook = Vector3.new(top.LookVector.X, 0, top.LookVector.Z).Unit
            if placeKitPiece(theme, "Support", CFrame.lookAt(top.Position, top.Position + flatLook), dressing) then
                count += 1
            end
        end
        run += length
    end
    local gate = model:FindFirstChild("Gate")
    local barrier = gate and (gate:FindFirstChild("QiBarrier") or gate:FindFirstChild("GateAnchor")) -- (an open bridge has an anchor, no barrier)
    local hubKit = kitFolder("Yggdrasil")
    local hubGate = hubKit and (hubKit:FindFirstChild("HB_BridgeGate__Marble") ~= nil)
    if barrier and hubGate then
        -- the hub's side: the celestial city's gate (hub_celestial.bridge_gate; the islands' own gates there were Chinese,
        -- the owner 2026-11-12), its crystals in the island's colour, the island's name hung under its arch. Its front (+Z)
        -- faces the hub: the barrier's frame looks out along the bridge.
        local base = barrier.CFrame * CFrame.new(0, -barrier.Size.Y / 2, 0)
        for _, piece in { "HB_BridgeGate", "HB_BridgeGateGlow" } do
            for _, source in templates("Yggdrasil", piece) do
                local p = source:Clone()
                p.CFrame = base * source.CFrame
                applyLook(p, source.Name)
                if piece == "HB_BridgeGateGlow" and themeInfo then
                    p.Color = themeInfo.Glow
                end
                p.Parent = dressing
            end
        end
        local name = WorldBuilder.GateNames[model.Name]
        if themeInfo and themeInfo.Kit then
            for _, p in dressing:GetChildren() do
                if p.Name == "SupportGlow" or p.Name == "DeckGlow" then
                    p.Color = themeInfo.Glow -- (the borrowed kit's glow, in this bridge's colour)
                end
            end
        end
        if name then
            local _, gui = textPanel("GateName", WorldBuilder.GatePlaque.Size, base * CFrame.new(WorldBuilder.GatePlaque.Centre), dressing, 50)
            steleLabel("Text", gui, UDim2.fromScale(0.96, 0.86), UDim2.fromScale(0.02, 0.07), Enum.TextXAlignment.Center,
                Color3.fromRGB(240, 222, 170)).Text = name
        end
        count += 1
        for _, part in gate:GetChildren() do
            if part.Name == "Pillar" or part.Name == "Lintel" then
                hideCollision(part)
            end
        end
    elseif barrier then
        local base = barrier.CFrame * CFrame.new(0, -barrier.Size.Y / 2, 0)
        if placeKitPiece(theme, "Gate", base, dressing) then
            count += 1
            for _, part in gate:GetChildren() do
                if part.Name == "Pillar" or part.Name == "Lintel" then
                    hideCollision(part)
                end
            end
        end
    end
    -- the blockout becomes invisible collision under the kit, unless a deck section is bare: then the
    -- whole deck and its rails stay as they are
    if count > 0 and not bareDeck then
        for _, c in model:GetChildren() do
            if c.Name == "Deck" or c.Name == "Rail" then
                hideCollision(c)
                c.CastShadow = false
            end
        end
    end
    return count
end

-- With `only` (a route's name) just that bridge is rebuilt; the others stay as they are.
function WorldBuilder.buildBridges(only)
    local data = require(ServerStorage.WorldBuild.Placements.Bridges:Clone())
    kitInfo = require(ServerStorage.WorldBuild.Placements.BridgeKits:Clone())
    local folder = WorldBuilder.islandFolder("Bridges")
    if only then
        local old = folder:FindFirstChild(only)
        if old then
            old:Destroy()
        end
    else
        folder:ClearAllChildren()
    end
    for route, bridge in data.Bridges do
        if only and route ~= only then
            continue
        end
        local theme = WorldBuilder.BridgeThemes[bridge.Theme]
        local info = WorldBuilder.Routes[route]
        local width = data.DeckWidth
        local model = Instance.new("Model")
        model.Name = route
        model:SetAttribute("Route", route)
        model:SetAttribute("RankId", bridge.RankId) -- (nil on an open bridge: Murim Crossing's, with no barrier and no rank zones)
        model:SetAttribute("Destination", info.Title)
        model:SetAttribute("Island", info.Island) -- the island it leads to, closed below RankId too
        local ranked = bridge.RankId ~= nil
        local zones = Instance.new("Folder")
        zones.Name = "Zones"
        if ranked then
            zones.Parent = model
        end
        local nodes = bridge.Nodes
        local zoneFrom = BRIDGE.GateInset + 2 -- the zones start just past the gate: before it is the free approach
        local run = 0
        for i = 1, #nodes - 1 do
            local a, b = nodes[i].Position, nodes[i + 1].Position
            local length = (b - a).Magnitude
            -- up to Segment studs a piece, with a little give: layout.py's 12.1-stud spans stay whole
            local pieces = math.max(1, math.ceil(length / BRIDGE.Segment - 0.05))
            for k = 1, pieces do
                local d0 = length * (k - 1) / pieces
                deckPiece(model, theme, width, a:Lerp(b, (k - 1) / pieces), a:Lerp(b, k / pieces), (ranked and run + d0 >= zoneFrom) and zones or nil)
            end
            run += length
        end
        abutment(model, theme, width, nodes[1].Position, nodes[1].Position - nodes[2].Position)
        abutment(model, theme, width, nodes[#nodes].Position, nodes[#nodes].Position - nodes[#nodes - 1].Position)
        local a, b = nodes[1].Position, nodes[2].Position
        local dir = Vector3.new(b.X - a.X, 0, b.Z - a.Z).Unit
        local base = a + dir * BRIDGE.GateInset
        local frame = CFrame.lookAt(base, base + dir)
        local gate = Instance.new("Model")
        gate.Name = "Gate"
        for side = -1, 1, 2 do
            bridgePart("Pillar", Vector3.new(1.6, BRIDGE.GateHeight, 1.6), frame * CFrame.new(side * (width / 2 + 0.8), BRIDGE.GateHeight / 2, 0), gate, theme.Rail, theme.DeckMaterial)
        end
        bridgePart("Lintel", Vector3.new(width + 4.4, 1.4, 2), frame * CFrame.new(0, BRIDGE.GateHeight + 0.7, 0), gate, theme.Rail, theme.DeckMaterial)
        if ranked then
            local barrier = bridgePart("QiBarrier", Vector3.new(width, BRIDGE.GateHeight, 0.5), frame * CFrame.new(0, BRIDGE.GateHeight / 2, 0), gate, theme.Glow, Enum.Material.ForceField)
            barrier.Transparency = 0.2
            barrier.CastShadow = false
            barrier:SetAttribute("RankId", bridge.RankId)
            barrier:SetAttribute("Route", route)
            CollectionService:AddTag(barrier, GameConfig.BridgeBarrierTag)
            local light = Instance.new("PointLight")
            light.Color, light.Range, light.Brightness = theme.Glow, 12, 0.6
            light.Parent = barrier
        else
            -- an open bridge: the same gate, with nothing across it. Only a place for the hub's gate to be set round (dressBridge)
            local anchor = marker("GateAnchor", Vector3.new(width, BRIDGE.GateHeight, 0.5), frame * CFrame.new(0, BRIDGE.GateHeight / 2, 0), gate)
            anchor.Material = Enum.Material.Plastic
        end
        gate.Parent = model
        model:SetAttribute("ReturnTo", base - dir * 3 + Vector3.new(0, 3, 0))
        model:SetAttribute("KitPieces", dressBridge(model, bridge.Theme))
        model.Parent = folder
    end
    return #folder:GetChildren()
end

-- Whether the island's kit holds a template of this name (one part, or its material parts).
local function hasTemplate(island, name)
    local folder = kitFolder(island)
    if not folder then
        return false
    end
    if folder:FindFirstChild(name) then
        return true
    end
    for _, child in folder:GetChildren() do
        if splitName(child.Name) == name then
            return true
        end
    end
    return false
end

-- ---------- the Hall of Records (2026-11-16; tools/blender/world/hall_layout.py, hall_records.py) ----------
-- FloatingIslands.<island>.HallOfRecords: the hall's pieces at Placements.<island>.HallOfRecords (each from the kit once it is stored,
-- or as a blockout of plain parts until then), the slate flags of its path, a few warm lights, and one invisible face part per board,
-- tagged RecordsConfig.Tag with a Board attribute: the client draws each board's SurfaceGui on its front (client/World/HallOfRecords;
-- the data: server/Records/RecordsService).
WorldBuilder.HallLight = Color3.fromRGB(255, 196, 140)
local HALL_BLOCKOUT_FLAG = Vector3.new(4.6, 0.3, 2.6)

local function hallBlockout(name, box, frame, parent)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = box.Size
    part.CFrame = frame * CFrame.new(box.Centre) * CFrame.Angles(0, box.Yaw or 0, 0) * CFrame.Angles(box.Pitch or 0, 0, 0)
    part.Anchored = true
    part.CanTouch = false
    part.TopSurface, part.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
    for property, value in WorldBuilder.MaterialLooks[box.Look] or WorldBuilder.MaterialLooks.Basalt do
        part[property] = value -- (setLook is for MeshParts: a plain Part has no TextureID)
    end
    part.CanQuery = part.CanCollide
    part:SetAttribute("Blockout", true)
    part.Parent = parent
    return part
end

function WorldBuilder.buildHallOfRecords(island)
    local spec = placementsFor(island).HallOfRecords
    local folder = WorldBuilder.islandFolder(island, "HallOfRecords")
    folder:ClearAllChildren()
    local hall = islandFrame(island) * CFrame.new(spec.Centre) * CFrame.Angles(0, spec.Yaw, 0)
    local tag = require(ReplicatedStorage:WaitForChild("RecordsConfig"):Clone()).Tag
    local blockouts = 0
    for index, entry in spec.Pieces do
        local frame = hall * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
        local holder = Instance.new("Folder")
        holder.Name = entry.Piece .. "_" .. index
        holder.Parent = folder
        if hasTemplate(island, entry.Piece) then
            -- (Scale: the court's mesh as modelled, stretched in X and Z to the court's radius, its height kept)
            placeTemplate(island, entry.Piece, frame, holder, entry.Scale)
        elseif entry.Piece == "HR_Court" then
            local court = hallBlockout("HR_Court", { Centre = Vector3.new(0, 0.1, 0), Size = Vector3.new(0.3, spec.Court * 2, spec.Court * 2),
                Look = "Flagstone" }, frame, holder)
            court.Shape = Enum.PartType.Cylinder
            court.CFrame = frame * CFrame.new(0, 0.1, 0) * CFrame.Angles(0, 0, math.pi / 2)
            blockouts += 1
        else
            for k, box in spec.Blockout[entry.Piece] or {} do
                hallBlockout(entry.Piece .. "_Block" .. k, box, frame, holder)
                blockouts += 1
            end
        end
        for _, face in spec.Faces[entry.Piece] or {} do
            local centre = frame:PointToWorldSpace(face.Centre)
            local normal = frame:VectorToWorldSpace(face.Normal)
            local up = frame:VectorToWorldSpace(face.Up)
            local part = marker("Face_" .. face.Board, Vector3.new(face.Size.X, face.Size.Y, 0.05),
                CFrame.lookAt(centre, centre + normal, up), holder)
            part:SetAttribute("Board", face.Board)
            CollectionService:AddTag(part, tag)
        end
        local light = spec.Lights[entry.Piece]
        if light then
            addLight(marker("Light", Vector3.new(1, 1, 1), frame * CFrame.new(light.Offset), holder), WorldBuilder.HallLight,
                light.Range, light.Brightness)
        end
    end
    local flags = Instance.new("Folder")
    flags.Name = "Flags"
    flags.Parent = folder
    for index, flag in spec.Flags do
        local frame = hall * CFrame.new(flag.Position) * CFrame.Angles(0, flag.Yaw, 0)
        if hasTemplate(island, "HR_PathFlag") then
            placeTemplate(island, "HR_PathFlag", frame, flags).Name = "HR_PathFlag_" .. index
        else
            hallBlockout("HR_PathFlag_" .. index, { Centre = Vector3.new(0, 0.1, 0), Size = HALL_BLOCKOUT_FLAG, Look = "Flagstone" }, frame, flags)
            blockouts += 1
        end
    end
    WorldBuilder.applyCollision(folder)
    return folder, blockouts
end

-- After the owner's import of assets/world/HallOfRecords/HallOfRecords.fbx (anchor HR_Anchor) and
-- assets/world/Yggdrasil/Yggdrasil_Paving.fbx (anchor HB_Anchor: the avenues and plazas without the south-west avenue, the garden
-- court and the old leaderboard's disc): stores both in the hub's kit (the old avenue and plaza templates removed first, so no
-- material part of them is left behind), then lays the hub's kit and the hall again. Either import may be nil.
function WorldBuilder.storeHallOfRecords(hallImport, pavingImport)
    local stored = 0
    if pavingImport then
        local kit = kitFolder("Yggdrasil", true)
        for _, part in kit:GetChildren() do
            local base = splitName(part.Name)
            if base == "HB_Avenues" or base == "HB_Plazas" or base == "HB_PavingRunes" then
                part:Destroy()
            end
        end
        stored += WorldBuilder.storeKit("Yggdrasil", pavingImport, "HB_Anchor")
    end
    if hallImport then
        stored += WorldBuilder.storeKit("Yggdrasil", hallImport, "HR_Anchor")
    end
    local placed, missing = WorldBuilder.placeKit("Yggdrasil")
    local _, blockouts = WorldBuilder.buildHallOfRecords("Yggdrasil")
    return stored, placed, #missing, blockouts
end

-- ---------- spawn, relic ----------

function WorldBuilder.buildSpawn(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("IslandSpawn")
    if old then
        old:Destroy()
    end
    return spawnPoint("IslandSpawn", CFrame.new(islandPoint(island, placements.Spawn + Vector3.new(0, 0.5, 0))), model)
end

-- ---------- plots (Yggdrasil) ----------

-- Each shop plot's name (buildShops writes it on the building's sign and its prompt) and the building
-- that stands on it (Built).
WorldBuilder.Plots = {
    Blacksmith = { Title = "Blacksmith", Built = "Celestial Forge" },
    Marketplace = { Title = "Auction House", Built = "Crystal Market" }, -- (the Marketplace until 2026-11-16: the same building, its egg sales replaced by player auctions)
    BuySell = { Title = "Buy & Sell", Built = "Gilded Vault" },
}
-- ---------- the shops (Yggdrasil) ----------
-- Each shop's building (tools/blender/world/hub_district.py since the hub's redesign, 2026-11-15): its plot, the kit pieces it is made of
-- and what its prompt says. ShopService opens the shop named by the prompt's "Shop" attribute (AuctionService answers "Marketplace").
WorldBuilder.Shops = {
    Blacksmith = { Plot = "Blacksmith", Pieces = { "HB_Blacksmith", "HB_BlacksmithCore", "HB_BlacksmithCrystal" }, Action = "Shop" },
    BuySell = { Plot = "BuySell", Pieces = { "HB_BuySell", "HB_BuySellStones" }, Action = "Trade" },
    Marketplace = { Plot = "Marketplace", Pieces = { "HB_Market", "HB_MarketCanopy", "HB_MarketGlow" }, Action = "Open" }, -- the Auction House (AuctionService)
}
WorldBuilder.ForgeLight = Color3.fromRGB(255, 120, 40)
WorldBuilder.LanternLight = Color3.fromRGB(255, 130, 70) -- warm: a red light tints the paving pink

-- What goes on each of a shop's effect points (Placements.<island>.Shops.<Shop>.Fx).
local SHOP_FX = {
    -- flames licking up in the hearth's mouth (kept short so they stay under its slate hood) and
    -- sparks spat out of it toward the anvil (a part's Back face is its +Z, the shop's front)
    Forge = function(part)
        part.Size = Vector3.new(3.6, 0.6, 2)
        addEmitterPreset(part, "Flames")
        local flames = part:FindFirstChild("Flames")
        flames.Speed = NumberRange.new(1.2, 2)
        flames.Lifetime = NumberRange.new(0.4, 0.7)
        flames.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.3), NumberSequenceKeypoint.new(1, 0.1) })
        addEmitterPreset(part, "EmberSparks")
        part:FindFirstChild("EmberSparks").EmissionDirection = Enum.NormalId.Back
        addLight(part, WorldBuilder.ForgeLight, 16, 0.9) -- any brighter floods the pale hall orange
    end,
    Smoke = function(part)
        part.Size = Vector3.new(2.4, 0.4, 2.4)
        addEmitterPreset(part, "Smoke")
    end,
    Stones = function(part)
        addLight(part, WorldBuilder.MaterialLooks.Glow.Color, 14, 0.9)
    end,
    Lantern = function(part)
        addLight(part, WorldBuilder.LanternLight, 12, 0.5)
    end,
    Coins = function(part)
        addLight(part, WorldBuilder.MaterialLooks.Glow.Color, 14, 0.7)
    end,
}

-- The shops on their plots (FloatingIslands.<island>.Shops.<Shop>): the building's pieces, the name
-- board over the entrance ("Sign"), the prompt that opens the shop ("Prompt", at the Blacksmith's
-- anvil and the foot of the Jade Scale) and the effect points ("Fx").
-- ---------- the long roots' collision (Yggdrasil) ----------

-- Each long root's centre line and thickness, as tools/blender/world/ygg_tree.py builds the
-- mesh (root_points, catmull with 8 steps, radius 11 -> 3.5): island-local studs.
local function longRootCurve(k)
    local bearing = math.rad(38) + 2 * math.pi * k / 7
    local drift = 0.1 * (if k % 2 == 1 then 1 else -1)
    local function at(r, y, curl)
        local a = bearing + drift * curl
        return Vector3.new(math.cos(a) * r, y, math.sin(a) * r)
    end
    local pts = { at(14, 14, 0), at(30, 9, 0), at(44, 6, 0.2), at(56, 9, 0.5), at(67, 14.5, 0.8), at(77, 18.5, 1.0),
        at(87, 17.5, 1.1), at(98, 11, 1.1), at(109, 3, 0.9), at(119, -5, 0.7) }
    table.insert(pts, 1, pts[1] * 2 - pts[2])
    table.insert(pts, pts[#pts] * 2 - pts[#pts - 1])
    local curve = {}
    for i = 2, #pts - 2 do
        local p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for step = 0, 7 do
            local t = step / 8
            table.insert(curve, 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
        end
    end
    table.insert(curve, pts[#pts - 1])
    return curve
end

-- Invisible cylinders along the long roots (0, 2, 4), so players walk under their arches and
-- still meet their sides and can stand on them. Replaces any built before.
function WorldBuilder.buildRootColliders(island)
    island = island or "Yggdrasil"
    local folder = WorldBuilder.islandFolder(island, "RootColliders")
    folder:ClearAllChildren()
    local count = 0
    for _, k in { 0, 2, 4 } do
        local curve = longRootCurve(k)
        local n = #curve
        for i = 1, n - 1, 2 do
            local j = math.min(i + 2, n)
            local a, b = islandPoint(island, curve[i]), islandPoint(island, curve[j])
            local t = ((i + j) / 2 - 1) / (n - 1)
            local radius = 11 + (3.5 - 11) * t ^ 0.7
            local part = Instance.new("Part")
            part.Name = string.format("YG_RootCollider%d_%02d", k, count)
            part.Shape = Enum.PartType.Cylinder
            part.Size = Vector3.new((b - a).Magnitude + radius * 0.6, radius * 2, radius * 2)
            part.CFrame = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.rad(90), 0) -- a cylinder runs along its X
            part.Anchored, part.CanCollide, part.CanTouch, part.CastShadow = true, true, false, false
            part.Transparency = 1
            part.Parent = folder
            count += 1
        end
    end
    return count
end

function WorldBuilder.buildShops(island)
    local placements = placementsFor(island)
    local folder = WorldBuilder.islandFolder(island, "Shops")
    folder:ClearAllChildren()
    for shop, info in WorldBuilder.Shops do
        local plot = placements.Plots[info.Plot]
        local spots = placements.Shops[shop]
        local plotInfo = WorldBuilder.Plots[info.Plot]
        assert(plotInfo.Built, "Plots." .. info.Plot .. " should name its building (Built)")
        local frame = islandFrame(island) * CFrame.new(plot.Centre) * CFrame.Angles(0, plot.Yaw, 0)
        local model = Instance.new("Model")
        model.Name = shop
        for _, piece in info.Pieces do
            placeTemplate(island, piece, frame, model)
        end

        local _, signGui = textPanel("Sign", spots.Sign.Size, frame * CFrame.new(spots.Sign.Centre), model, 60)
        steleLabel("Text", signGui, UDim2.fromScale(0.96, 0.9), UDim2.fromScale(0.02, 0.05), Enum.TextXAlignment.Center,
            Color3.fromRGB(240, 222, 170)).Text = plotInfo.Title

        local holder = marker("Prompt", Vector3.new(1, 1, 1), frame * CFrame.new(spots.Prompt), model)
        local prompt = Instance.new("ProximityPrompt")
        prompt.ActionText = info.Action
        prompt.ObjectText = plotInfo.Title
        prompt.KeyboardKeyCode = Enum.KeyCode.F
        prompt.HoldDuration = 0
        prompt.MaxActivationDistance = 12
        prompt.RequiresLineOfSight = false
        prompt:SetAttribute("Shop", shop)
        prompt.Parent = holder

        local fx = Instance.new("Folder")
        fx.Name = "Fx"
        fx.Parent = model
        for _, spot in spots.Fx do
            SHOP_FX[spot.Kind](marker(spot.Kind, Vector3.new(1, 1, 1), frame * CFrame.new(spot.Position), fx))
        end
        model.Parent = folder
    end
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- The Hatching Sanctum (tools/blender/world/hub_celestial.py), where eggs carried home are hatched
-- (PetService): FloatingIslands.<island>.HatchingAltar, placed by GameConfig.HatchingAltar, with
-- "Prompt" (its prompt, attribute Hatchery, opens the hatching window), "Cradle" (where PetService
-- lays an egg, on the pool's surface) and "Motes" (golden motes over the pool, and its light).
-- Spots in the sanctum's frame, as authored (hub_celestial CRADLE_TOP, FLOOR).
-- Since the hub's rebuild (2026-11-12) it is the Hatching Sanctum (hub_celestial.py): the egg rests in the lapis well of the cradle.
WorldBuilder.Altar = {
    Pieces = { "HB_HatchSanctum", "HB_HatchGlass", "HB_HatchCrystal", "HB_HatchRunes" },
    Cradle = Vector3.new(0, 4.1, 0),
    Prompt = Vector3.new(0, 3.4, 6.0),
    Motes = Vector3.new(0, 4.5, 0),
}

function WorldBuilder.buildAltar(island)
    local config = GameConfig.HatchingAltar
    assert(island == config.Island, "the Hatching Altar stands on " .. config.Island)
    local folder = WorldBuilder.islandFolder(island)
    local old = folder:FindFirstChild("HatchingAltar")
    if old then
        old:Destroy()
    end
    local frame = islandFrame(island) * CFrame.new(config.Centre) * CFrame.Angles(0, config.Yaw, 0)
    local model = Instance.new("Model")
    model.Name = "HatchingAltar"
    for _, piece in WorldBuilder.Altar.Pieces do
        placeTemplate(island, piece, frame, model)
    end
    marker("Cradle", Vector3.new(1, 0.2, 1), frame * CFrame.new(WorldBuilder.Altar.Cradle), model)
    local holder = marker("Prompt", Vector3.new(1, 1, 1), frame * CFrame.new(WorldBuilder.Altar.Prompt), model)
    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Hatch"
    prompt.ObjectText = "Hatching Sanctum"
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = 12 * (config.Scale or 1) -- (reached from the edge of the altar's floor, as it grew)
    prompt.RequiresLineOfSight = false
    prompt:SetAttribute("Hatchery", true)
    prompt.Parent = holder
    local motes = marker("Motes", Vector3.new(4.4, 0.2, 4.4), frame * CFrame.new(WorldBuilder.Altar.Motes), model)
    addEmitterPreset(motes, "GoldenMotes")
    addLight(motes, Color3.fromRGB(255, 170, 60), 18, 1.1)
    -- (scaled about its base, on the ground: at its authored size, beside the shops it read as a small fountain)
    model.WorldPivot = frame
    if config.Scale and config.Scale ~= 1 then
        model:ScaleTo(config.Scale)
    end
    model.Parent = folder
    WorldBuilder.applyCollision(model)
    return model
end

-- ---------- the Blossom Sanctuary (the owner's directive, 2026-11-16; tools/blender/world/blossom_layout.py, blossom_assets.py) ----------
-- The Qi Spring's +50% moved here (GameConfig.TrainingStation): QiService reads the Training Ground's outline from
-- Placements.BlossomSanctuary itself, so nothing in the place has to stay in step with it but its sign and kerb.

local SANCTUARY_STONE = { Material = Enum.Material.Limestone, Color = Color3.fromRGB(222, 212, 192) }
-- each cap piece's smallest half-width as modelled (pieces.json), so a stone's Radius scales it to cover its rock all round
local CAP_RADIUS = { BS_SteppingStoneA = 4.8, BS_SteppingStoneB = 4.14, BS_SteppingStoneC = 2.87 }

-- A billboard sign in plain words over an invisible part.
local function signPost(name, parent, at, title, line, color)
    local post = marker(name, Vector3.new(1, 1, 1), CFrame.new(at), parent)
    local sign = Instance.new("BillboardGui")
    sign.Name = "Sign"
    sign.Size = UDim2.fromOffset(250, 58)
    sign.MaxDistance = 90
    sign.LightInfluence = 0
    sign.Parent = post
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.TextColor3 = color
    label.TextStrokeTransparency = 0.45
    label.Text = title .. "\n" .. line
    label.Parent = sign
    return post
end

-- A floating rock of terrain (no draw calls of its own, exact collision): a flat top at `top` (world Y) of radius r, tapering to a
-- point `depth` below it, its outline and underside a little uneven. Written column by column with the same occupancy rule as the
-- islands (a voxel's surface renders from its centre: measured), so the top is where it is asked to be; Studio's FillBall and
-- FillCylinder round to the voxel grid and left rock up to 5 studs over a stone's cap. `grass`: a grass top over Ground (the
-- platforms); a stone's rock stops 1.2 under its cap's top (the cap is 1.4-1.6 thick, so they overlap). `erase`: clears the same columns instead.
local function floatingRock(centre, top, r, depth, grass, seed, erase)
    local terrain = workspace.Terrain
    local reach = r + VOXEL
    local x0 = math.floor((centre.X - reach) / VOXEL) * VOXEL
    local z0 = math.floor((centre.Z - reach) / VOXEL) * VOXEL
    local n = math.ceil((centre.X + reach - x0) / VOXEL)
    local m = math.ceil((centre.Z + reach - z0) / VOXEL)
    local y0 = math.floor((top - depth - VOXEL) / VOXEL) * VOXEL
    local layers = math.ceil((top + 2 * VOXEL - y0) / VOXEL)
    local region = Region3.new(Vector3.new(x0, y0, z0), Vector3.new(x0 + n * VOXEL, y0 + layers * VOXEL, z0 + m * VOXEL))
    local mats, occs = terrain:ReadVoxels(region, VOXEL)
    local surfaceTop = if grass then top else top - 1.2
    for i = 1, n do
        for k = 1, m do
            local x, z = x0 + (i - 0.5) * VOXEL, z0 + (k - 0.5) * VOXEL
            local dx, dz = x - centre.X, z - centre.Z
            local angle = math.atan2(dz, dx)
            local edge = r * (0.92 + 0.08 * math.noise(math.cos(angle) * 1.3 + seed, math.sin(angle) * 1.3, seed * 0.37))
            local d = math.sqrt(dx * dx + dz * dz)
            if d <= (if erase then r + 2 else edge) then
                local t = d / edge
                local hang = 2.5 + (depth - 2.5) * (1 - t) ^ 1.25 * (0.85 + 0.3 * math.noise(x * 0.11, z * 0.11, seed))
                local bottom = top - hang
                for j = 1, layers do
                    local yv = y0 + (j - 1) * VOXEL
                    if erase then
                        mats[i][j][k] = Enum.Material.Air
                        occs[i][j][k] = 0
                    else
                        local solid = math.min(math.clamp((surfaceTop - yv - VOXEL / 2) / VOXEL, 0, 1), math.clamp((yv + VOXEL - bottom) / VOXEL, 0, 1))
                        if solid > 0 then
                            local below = surfaceTop - (yv + VOXEL / 2)
                            mats[i][j][k] = if grass and below <= VOXEL then Enum.Material.Grass elseif grass and below < 8 then Enum.Material.Ground else Enum.Material.Rock
                            occs[i][j][k] = solid
                        elseif yv + VOXEL / 2 > bottom then
                            mats[i][j][k] = Enum.Material.Air
                            occs[i][j][k] = 0
                        end
                    end
                end
            end
        end
    end
    terrain:WriteVoxels(region, VOXEL, mats, occs)
end

-- Erases what floatingRock laid for a piece built last time (its extent is kept on it as attributes).
local function eraseRock(part)
    local r, depth, top, centre = part:GetAttribute("RockRadius"), part:GetAttribute("RockDepth"), part:GetAttribute("RockTop"), part:GetAttribute("RockCentre")
    if r and depth and top and centre then
        floatingRock(centre, top, r, depth, false, 0, true)
    end
end

local function zonePart(name, size, cframe, parent)
    local zone = marker(name, size, cframe, parent)
    zone.CanQuery = true -- WorldService finds it with an overlap query
    return zone
end

-- The climb from the hub's south-east avenue to the island (Placements.BlossomSanctuary.Approach): every stone is a rock pillar of
-- terrain under a carved cap (BS_SteppingStone*, or a plain limestone disc until the kit is stored), the two platforms floating
-- islets of terrain with a tree and a seat; a pair of the hub's crystal lamps marks where the avenue now leads (the lamps'
-- rule: a pair where an avenue reaches its place). Zones: every piece has one ("Route"), the hub's verge, both platforms and the
-- island's landing a "Check" with the place a fall returns to (WorldService). Also places the garden court's tree on the hub.
function WorldBuilder.buildApproach(island)
    local placements = placementsFor(island)
    local approach = placements.Approach
    local frame = islandFrame(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("Approach")
    if old then
        for _, part in old:GetDescendants() do
            if part:IsA("BasePart") then
                eraseRock(part)
            end
        end
        old:Destroy()
    end
    local folder = Instance.new("Folder")
    folder.Name = "Approach"
    local zones = Instance.new("Folder")
    zones.Name = "Zones"
    zones.Parent = folder
    local towardIsland = (frame.Position - Vector3.new(0, frame.Position.Y, 0)) * Vector3.new(1, 0, 1)
    local outward = towardIsland.Unit

    local function check(name, at, size, returnTo)
        local zone = zonePart("Check", size, CFrame.new(at + Vector3.new(0, size.Y / 2 - 1, 0)), zones)
        zone:SetAttribute("Name", name)
        zone:SetAttribute("ReturnTo", returnTo)
        return zone
    end

    for index, stone in approach.Stones do
        local top = frame:PointToWorldSpace(stone.Position)
        local yaw = (index * 1.618) % (2 * math.pi)
        local at = CFrame.new(top) * CFrame.Angles(0, yaw, 0)
        local cap
        if hasTemplate(island, stone.Piece) then
            cap = placeTemplate(island, stone.Piece, at, folder, stone.Radius / CAP_RADIUS[stone.Piece])
        else
            cap = Instance.new("Part")
            cap.Shape = Enum.PartType.Cylinder
            cap.Size = Vector3.new(1.6, stone.Radius * 2, stone.Radius * 2)
            cap.CFrame = at * CFrame.new(0, -0.8, 0) * CFrame.Angles(0, 0, math.pi / 2)
            cap.Anchored = true
            cap.CanTouch = false
            cap.TopSurface, cap.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
            cap.Material, cap.Color = SANCTUARY_STONE.Material, SANCTUARY_STONE.Color
            cap.Parent = folder
        end
        cap.Name = (if stone.Leap then "LeapStone_" else "Stone_") .. index
        cap:SetAttribute("RockCentre", top)
        cap:SetAttribute("RockTop", top.Y)
        cap:SetAttribute("RockRadius", stone.Radius)
        cap:SetAttribute("RockDepth", 16)
        floatingRock(top, top.Y, stone.Radius, 16, false, index)
        zonePart("Route", Vector3.new(stone.Radius * 2 + 2, 9, stone.Radius * 2 + 2), CFrame.new(top + Vector3.new(0, 3.5, 0)), zones)
    end

    for index, platform in approach.Platforms do
        local top = frame:PointToWorldSpace(platform.Position)
        local holder = marker(platform.Name, Vector3.new(1, 1, 1), CFrame.new(top), folder)
        holder:SetAttribute("RockCentre", top)
        holder:SetAttribute("RockTop", top.Y)
        -- (terrain rounds a rim off over its last couple of studs: 2 more keep the walkable top at Radius)
        holder:SetAttribute("RockRadius", platform.Radius + 2)
        holder:SetAttribute("RockDepth", platform.Depth)
        floatingRock(top, top.Y, platform.Radius + 2, platform.Depth, true, 10 + index)
        local facing = CFrame.lookAt(top, top + outward)
        check(platform.Name, top, Vector3.new(platform.Radius * 2, 10, platform.Radius * 2), facing + Vector3.new(0, 0.2, 0))
        zonePart("Route", Vector3.new(platform.Radius * 2 + 2, 9, platform.Radius * 2 + 2), CFrame.new(top + Vector3.new(0, 3.5, 0)), zones)
        for _, dress in approach.Dressing do
            if dress.Platform == platform.Name and hasTemplate(island, dress.Piece) then
                local piece = placeTemplate(island, dress.Piece, CFrame.new(top) * frame.Rotation * CFrame.new(dress.Position)
                    * CFrame.Angles(0, dress.Yaw, 0), folder, dress.Scale)
                piece.Name = dress.Piece .. "_" .. platform.Name
            end
        end
    end

    -- the island's end: its landing (the island's checkpoint), facing into the island
    local landing = frame * CFrame.new(placements.Checkpoint.Position) * CFrame.Angles(0, placements.Checkpoint.Yaw, 0)
    check("Arrival", landing.Position, Vector3.new(24, 10, 24), landing + Vector3.new(0, 0.2, 0))

    -- the hub's end: where the south-east avenue's line meets the verge past the Ring Road (world space: the hub is at the origin)
    local hubStart = frame:PointToWorldSpace(approach.HubStart.Position)
    local bearing = Vector3.new(hubStart.X, 0, hubStart.Z).Unit
    local side = Vector3.new(-bearing.Z, 0, bearing.X)
    local hubY = WorldBuilder.islandFrame("Yggdrasil").Position.Y
    local verge = Vector3.new(0, hubY, 0) + bearing * 241.5
    check("HubStart", verge, Vector3.new(18, 10, 18), CFrame.lookAt(verge, verge + bearing) + Vector3.new(0, 0.25, 0))
    local lamps = 0
    if hasTemplate("Yggdrasil", "HB_CrystalLamp") then
        for k, s in { -1, 1 } do
            local at = Vector3.new(0, hubY, 0) + bearing * 239.5 + side * s * 8.2
            local lampFrame = CFrame.lookAt(at, Vector3.new(0, hubY, 0)) * CFrame.Angles(0, math.pi, 0)
            local lamp = placeTemplate("Yggdrasil", "HB_CrystalLamp", lampFrame, folder)
            lamp.Name = "HB_CrystalLamp_Sanctuary" .. k
            local crystal = if k == 1 then "HB_CrystalLampLight" else "HB_CrystalLampGlow"
            local glow = placeTemplate("Yggdrasil", crystal, lampFrame, folder)
            local light = WorldBuilder.Lights[crystal]
            if light then
                addLight(glow, glow.Color, light.Range, light.Brightness)
            end
            lamps += 1
        end
    end
    signPost("HubSign", folder, verge + Vector3.new(0, 9, 0), "Blossom Sanctuary", "Training: +" .. GameConfig.TrainingStation.QiBonusPercent .. "% Qi",
        Color3.fromRGB(255, 214, 230))

    folder.Parent = model
    WorldBuilder.applyCollision(folder)
    return #approach.Stones, #approach.Platforms, lamps
end

-- A fallback koi until the kit is stored: a body and a tail fin from Roblox's own shapes (no upload), in the variant's colours.
local function fallbackKoi(name, colour, patch)
    local fish = Instance.new("Model")
    fish.Name = name
    local body = Instance.new("Part")
    body.Name = "Body"
    body.Size = Vector3.new(0.9, 0.7, 3)
    body.Color = colour
    body.Material = Enum.Material.SmoothPlastic
    local mesh = Instance.new("SpecialMesh")
    mesh.MeshType = Enum.MeshType.Sphere
    mesh.Parent = body
    local tail = Instance.new("WedgePart")
    tail.Name = "Tail"
    tail.Size = Vector3.new(0.12, 0.8, 0.9)
    tail.Color = patch
    tail.Material = Enum.Material.SmoothPlastic
    tail.Transparency = 0.2
    for _, part in { body, tail } do
        part.Anchored = true
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.CastShadow = false
        part.Parent = fish
    end
    body.CFrame = CFrame.new()
    tail.CFrame = CFrame.new(0, 0, -1.75)
    tail:SetAttribute("Hinge", Vector3.new(0, 0, -1.3))
    return fish
end

local KOI = {
    { Variant = "Kohaku", Fallback = { Color3.fromRGB(246, 243, 236), Color3.fromRGB(226, 82, 40) } },
    { Variant = "Showa", Fallback = { Color3.fromRGB(32, 30, 32), Color3.fromRGB(226, 82, 40) } },
    { Variant = "Ogon", Fallback = { Color3.fromRGB(240, 182, 72), Color3.fromRGB(250, 220, 160) } },
}
local KOI_PER_LOOP = { 3, 2, 2 }
local KOI_HINGE = Vector3.new(0, 0.03, -0.85) -- pieces.json: where each tail joins its body

-- The island's own pieces besides its kit: the Training Ground's sign, the checkpoint, and the pond's koi (each a model whose
-- parts the client swims round Placements' loops: SanctuaryLife), their ripple template and the pond's sound spot.
function WorldBuilder.buildSanctuary(island)
    local placements = placementsFor(island)
    local frame = islandFrame(island)
    local model = WorldBuilder.islandFolder(island)
    for _, name in { "TrainingGround", "Pond", "Checkpoint" } do
        local old = model:FindFirstChild(name)
        if old then
            old:Destroy()
        end
    end
    local station = GameConfig.TrainingStation
    local ground = Instance.new("Folder")
    ground.Name = "TrainingGround"
    local rules = placements.TrainingGround
    signPost("Sign", ground, frame:PointToWorldSpace(rules.Sign), "Training Ground", "Cultivate here: +" .. station.QiBonusPercent .. "% Qi",
        Color3.fromRGB(255, 214, 230))
    ground.Parent = model

    local checkpoint = placements.Checkpoint
    marker("Checkpoint", Vector3.new(4, 1, 4), frame * CFrame.new(checkpoint.Position) * CFrame.Angles(0, checkpoint.Yaw, 0), model)

    local pond = Instance.new("Model")
    pond.Name = "Pond"
    pond.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- the koi arrive with the pond, whole
    local centre = marker("PondCentre", Vector3.new(1, 1, 1), frame * CFrame.new(placements.Pond.Centre), pond)
    pond.PrimaryPart = centre
    local koiFolder = Instance.new("Folder")
    koiFolder.Name = "Koi"
    koiFolder.Parent = pond
    local count = 0
    for loopIndex, loop in placements.Pond.Koi do
        for n = 1, KOI_PER_LOOP[loopIndex] or 1 do
            count += 1
            local kind = KOI[(count - 1) % #KOI + 1]
            local name = "BS_Koi" .. kind.Variant
            local fish
            if hasTemplate(island, name) and hasTemplate(island, name .. "Tail") then
                fish = Instance.new("Model")
                fish.Name = name
                for _, source in templates(island, name) do
                    local part = source:Clone()
                    part.Name = "Body_" .. (select(2, splitName(source.Name)) or "Part")
                    part.CFrame = source.CFrame
                    applyLook(part, source.Name)
                    part.Parent = fish
                end
                for _, source in templates(island, name .. "Tail") do
                    local part = source:Clone()
                    part.Name = "Tail_" .. (select(2, splitName(source.Name)) or "Part")
                    part.CFrame = source.CFrame
                    part:SetAttribute("Hinge", KOI_HINGE)
                    applyLook(part, source.Name)
                    part.Parent = fish
                end
            else
                fish = fallbackKoi(name, kind.Fallback[1], kind.Fallback[2])
            end
            for _, part in fish:GetDescendants() do
                if part:IsA("BasePart") then
                    part:SetAttribute("Rest", part.CFrame) -- its place in the fish's own frame (the fish's origin at the world's)
                    part.Anchored = true
                    part.CanCollide = false
                    part.CanQuery = false
                    part.CanTouch = false
                    part.CastShadow = false
                end
            end
            fish:SetAttribute("Loop", loopIndex)
            fish:SetAttribute("Phase", (n - 1) / (KOI_PER_LOOP[loopIndex] or 1) + loopIndex * 0.13)
            -- parked at its loop's first point until the client swims it
            local start = frame:PointToWorldSpace(loop[1])
            for _, part in fish:GetDescendants() do
                if part:IsA("BasePart") then
                    part.CFrame = CFrame.new(start) * part:GetAttribute("Rest")
                end
            end
            fish.Parent = koiFolder
        end
    end
    -- the swimming loops, in world space, for the client (Placements live in ServerStorage)
    local loops = Instance.new("Folder")
    loops.Name = "Loops"
    loops.Parent = pond
    for loopIndex, loop in placements.Pond.Koi do
        local points = Instance.new("Configuration")
        points.Name = "Loop" .. loopIndex
        for k, point in loop do
            points:SetAttribute("P" .. k, frame:PointToWorldSpace(point))
        end
        points:SetAttribute("Count", #loop)
        points.Parent = loops
    end
    pond:SetAttribute("Water", frame.Position.Y + placements.Pond.Water)
    model:SetAttribute("Centre", frame.Position)
    model:SetAttribute("Reach", placements.Reach)
    if hasTemplate(island, "BS_Ripple") then
        local ripple = placeTemplate(island, "BS_Ripple", CFrame.new(centre.Position - Vector3.new(0, 30, 0)), pond)
        ripple.Name = "RippleTemplate"
        ripple.Transparency = 1
    end
    pond.Parent = model
    return count
end

-- Seamless vertical streaks (assets/world/StartingIsland/waterfall_streaks.png).
WorldBuilder.WaterfallTexture = "rbxassetid://84166602047979"

-- Looks for a liquid pouring off an island's edge.
WorldBuilder.Falls = {
    Water = { Name = "Waterfall", Color = Color3.fromRGB(205, 240, 250), LightEmission = 0.25, Mist = Color3.fromRGB(225, 245, 255),
        Spray = Color3.fromRGB(230, 250, 255), SprayEmission = 0.3 },
    Lava = { Name = "Lavafall", Color = Color3.fromRGB(255, 130, 40), LightEmission = 1, Mist = Color3.fromRGB(90, 60, 55),
        Spray = Color3.fromRGB(255, 170, 60), SprayEmission = 1 },
}

-- A liquid pouring off `lip`: a short arc, then a long fall fading into the sky with a wider, fainter
-- sheen scrolling at another speed, and mist drifting off it.
-- A fall: a few beams of water over a lip, a mist, a spray at the lip. `opts` (all optional; the default is the 52-stud fall off an island's edge):
--   Drop      how far the water falls. Under 40 it falls almost straight down the face (a cliff's fall); otherwise it leaves the island in an arc
--   Scale     width of every water beam as a multiple of the default (2.4 studs at the lip)
--   Curtains  how many curtains hang side by side across the lip (each as wide as one Scale'd fall, so the whole lip is about 2.4 x Scale x Curtains studs)
--   Splash    true: a splash and a foam mist where it lands (the fall's own bottom)
function WorldBuilder.buildWaterfall(parent, lip, from, look, opts)
    opts = opts or {}
    local scale = opts.Scale or 1
    local curtains = math.max(1, opts.Curtains or 1)
    local drop = opts.Drop or 52
    local short = drop < 40
    local out = Vector3.new(lip.X - from.X, 0, lip.Z - from.Z).Unit
    local side = Vector3.new(-out.Z, 0, out.X) -- horizontal, along the lip
    local holder = marker(look.Name, Vector3.new(1, 1, 1), CFrame.new(lip), parent)
    local function attach(name, offset)
        local a = Instance.new("Attachment")
        a.Name = name
        a.Parent = holder -- parent first: WorldPosition on an unparented attachment is taken as local
        a.WorldPosition = lip + offset
        return a
    end
    -- where the water bends over the lip and where it ends (a short fall hugs the face; the default leaves in an arc)
    local bendOut, bendDown = if short then 1.2 else 3.2, if short then math.min(2, drop * 0.2) else 5
    local bottomOut = if short then 1.8 else 5.5
    local mistOut, mistDown = if short then 2.0 else 4.5, if short then drop * 0.85 else 16

    local function beam(name, a0, a1, w0, w1, transparency, speed, length)
        local b = Instance.new("Beam")
        b.Name = name
        b.Attachment0, b.Attachment1 = a0, a1
        b.Width0, b.Width1 = w0 * scale, w1 * scale
        b.FaceCamera = true
        b.Texture = WorldBuilder.WaterfallTexture
        b.TextureMode = Enum.TextureMode.Wrap
        b.TextureLength = length
        b.TextureSpeed = speed
        b.Transparency = transparency
        b.Color = ColorSequence.new(look.Color)
        b.LightEmission = look.LightEmission
        b.LightInfluence = 0.7
        b.Segments = 12
        b.Parent = holder
        return b
    end
    local bottom
    for c = 1, curtains do
        local across = side * ((c - (curtains + 1) / 2) * 2.4 * scale) -- each curtain's own place along the lip (they touch, so together they read as one wide fall)
        local suffix = if curtains > 1 then tostring(c) else ""
        local top = attach("Lip" .. suffix, across + out * 0.4)
        local bend = attach("Bend" .. suffix, across + out * bendOut + Vector3.new(0, -bendDown, 0))
        local foot = attach("Bottom" .. suffix, across + out * bottomOut + Vector3.new(0, -drop, 0))
        bottom = bottom or foot
        local speed = 1 + 0.25 * ((c - 1) % 3) -- (a different pace in each curtain, so a wide fall doesn't read as one stamped strip)
        beam("LipCore" .. suffix, top, bend, 2.4, 2.6, NumberSequence.new(0.05, 0.1), 1.6 * speed, 4)
        beam("FallCore" .. suffix, bend, foot, 2.6, if short then 3.4 else 4.2, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.45, 0.3), NumberSequenceKeypoint.new(1, 1) }), 1.6 * speed, 6)
        beam("FallSheen" .. suffix, bend, foot, 3.6, if short then 4.8 else 6.5, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.5, 0.7), NumberSequenceKeypoint.new(1, 1) }), 2.3 * speed, 9)
    end
    local bend = holder:FindFirstChild("Bend") or holder:FindFirstChild("Bend" .. math.ceil(curtains / 2))

    local mistAt = attach("Mist", out * mistOut + Vector3.new(0, -mistDown, 0))
    local mist = Instance.new("ParticleEmitter")
    mist.Name = "Mist"
    mist.Texture = "rbxasset://textures/particles/smoke_main.dds"
    mist.Color = ColorSequence.new(look.Mist)
    mist.LightInfluence = 0.6
    mist.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 2 * math.sqrt(scale)), NumberSequenceKeypoint.new(1, 7 * math.sqrt(scale)) })
    mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.82), NumberSequenceKeypoint.new(1, 1) })
    mist.Lifetime = NumberRange.new(3, 5)
    mist.Speed = NumberRange.new(1, 2.5)
    mist.SpreadAngle = Vector2.new(60, 60)
    mist.EmissionDirection = Enum.NormalId.Bottom
    mist.Rotation = NumberRange.new(0, 360)
    mist.RotSpeed = NumberRange.new(-15, 15)
    mist.Rate = math.min(12, 5 * math.sqrt(scale) * math.sqrt(curtains))
    mist.Parent = mistAt

    local spray = Instance.new("ParticleEmitter")
    spray.Name = "LipSpray"
    spray.Color = ColorSequence.new(look.Spray)
    spray.LightEmission = look.SprayEmission
    spray.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18), NumberSequenceKeypoint.new(1, 0) })
    spray.Transparency = NumberSequence.new(0.2, 1)
    spray.Lifetime = NumberRange.new(0.5, 0.9)
    spray.Speed = NumberRange.new(2, 4)
    spray.SpreadAngle = Vector2.new(35, 35)
    spray.Acceleration = Vector3.new(0, -20, 0)
    spray.Rate = math.min(30, 14 * math.sqrt(scale * curtains))
    spray.Parent = bend

    if opts.Splash and bottom then
        -- where it lands: spray thrown up and out of the pool, and a low foam that spreads over the water (a beam's own end hides in the mist otherwise)
        local splash = Instance.new("ParticleEmitter")
        splash.Name = "Splash"
        splash.Color = ColorSequence.new(look.Spray)
        splash.LightEmission = look.SprayEmission
        splash.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.4, 0.9), NumberSequenceKeypoint.new(1, 0) })
        splash.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
        splash.Lifetime = NumberRange.new(0.6, 1.1)
        splash.Speed = NumberRange.new(5, 11)
        splash.SpreadAngle = Vector2.new(50, 50)
        splash.EmissionDirection = Enum.NormalId.Top
        splash.Acceleration = Vector3.new(0, -26, 0)
        splash.Rate = math.min(28, 10 * math.sqrt(scale * curtains))
        splash.Parent = bottom
        local foam = Instance.new("ParticleEmitter")
        foam.Name = "Foam"
        foam.Texture = "rbxasset://textures/particles/smoke_main.dds"
        foam.Color = ColorSequence.new(look.Mist)
        foam.LightInfluence = 0.5
        foam.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 3 * math.sqrt(scale)), NumberSequenceKeypoint.new(1, 8 * math.sqrt(scale)) })
        foam.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.75), NumberSequenceKeypoint.new(1, 1) })
        foam.Lifetime = NumberRange.new(2.5, 4)
        foam.Speed = NumberRange.new(1, 3)
        foam.SpreadAngle = Vector2.new(85, 85)
        foam.EmissionDirection = Enum.NormalId.Top
        foam.Rotation = NumberRange.new(0, 360)
        foam.RotSpeed = NumberRange.new(-20, 20)
        foam.Rate = math.min(10, 4 * math.sqrt(scale * curtains))
        foam.Parent = bottom
    end
    return holder
end

-- The lava river pouring off the island's edge (Placements.<island>.Lavafall).
function WorldBuilder.buildLavafall(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("Lavafall")
    if old then
        old:Destroy()
    end
    local holder = WorldBuilder.buildWaterfall(model, islandPoint(island, placements.Lavafall.Lip), islandPoint(island, placements.Lavafall.From),
        WorldBuilder.Falls.Lava)
    addLight(holder, Color3.fromRGB(255, 110, 30), 24, 1.4)
    return holder
end

WorldBuilder.Relics = {
    IslandRoot = { Color = Color3.fromRGB(255, 165, 40) },
    GroveHeart = { Color = Color3.fromRGB(40, 230, 120) },
    JadeSeed = { Color = Color3.fromRGB(150, 255, 60) },
    WhisperingSpring = { Color = Color3.fromRGB(40, 220, 210) },
    CalderaCrown = { Color = Color3.fromRGB(255, 70, 20) },
    EmberHeart = { Color = Color3.fromRGB(255, 150, 30), Lift = 1.6 }, -- (it rose out of the forge hearth, sunk in its coals)
    AshenSigil = { Color = Color3.fromRGB(255, 200, 120) },
    MoonMirror = { Color = Color3.fromRGB(150, 175, 255) },
    StarWell = { Color = Color3.fromRGB(255, 225, 120) },
    OriginAltar = { Color = Color3.fromRGB(185, 60, 255) },
    VoidShard = { Color = Color3.fromRGB(120, 60, 255) },
}

-- The Star Well's glowing surface just under its lip, with starlight rising off it
-- (Placements.<island>.StarWell). It is sealed by design: smoothing caps a one-voxel terrain shaft.
function WorldBuilder.buildStarWell(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("StarSurface")
    if old then
        old:Destroy()
    end
    local well = placements.StarWell
    local surface = Instance.new("Part")
    surface.Name = "StarSurface"
    surface.Shape = Enum.PartType.Cylinder
    surface.Size = Vector3.new(0.4, (well.Radius + 0.3) * 2, (well.Radius + 0.3) * 2)
    surface.CFrame = CFrame.new(islandPoint(island, well.Mouth - Vector3.new(0, 0.45, 0))) * CFrame.Angles(0, 0, math.pi / 2)
    surface.Material = Enum.Material.Glass
    surface.Color = Color3.fromRGB(18, 22, 64)
    surface.Transparency = 0.25
    surface.Reflectance = 0.35
    surface.Anchored = true
    surface.CanTouch = false
    surface.CastShadow = false
    surface.Parent = model
    local depthGlow = surface:Clone()
    depthGlow.Name = "Depth"
    depthGlow.Material = Enum.Material.Neon
    depthGlow.Color = Color3.fromRGB(50, 70, 210)
    depthGlow.Transparency = 0.55
    depthGlow.Reflectance = 0
    depthGlow.CanCollide = false
    depthGlow.CanQuery = false
    depthGlow.Size = surface.Size * Vector3.new(1, 0.92, 0.92)
    depthGlow.CFrame = surface.CFrame - Vector3.new(0, 1.2, 0)
    depthGlow.Parent = surface

    local stars = Instance.new("ParticleEmitter")
    stars.Name = "Starlight"
    stars.Texture = "rbxasset://textures/particles/sparkles_main.dds"
    stars.EmissionDirection = Enum.NormalId.Right -- the cylinder's axis points up
    stars.Shape = Enum.ParticleEmitterShape.Disc
    stars.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    stars.Color = ColorSequence.new(Color3.fromRGB(255, 235, 170), Color3.fromRGB(130, 160, 255))
    stars.LightEmission = 1
    stars.LightInfluence = 0
    stars.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.45), NumberSequenceKeypoint.new(1, 0) })
    stars.Transparency = NumberSequence.new(0.1, 1)
    stars.Lifetime = NumberRange.new(2.5, 4)
    stars.Speed = NumberRange.new(2, 4)
    stars.SpreadAngle = Vector2.new(10, 10)
    stars.Rotation = NumberRange.new(0, 360)
    stars.RotSpeed = NumberRange.new(-60, 60)
    stars.Rate = 14
    stars.Parent = surface
    addLight(surface, Color3.fromRGB(150, 170, 255), 18, 1.2)
    return surface
end

-- Where WorldService returns a player who falls from this island (Placements.<island>.Checkpoint).
function WorldBuilder.buildCheckpoint(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("Checkpoint")
    if old then
        old:Destroy()
    end
    return marker("Checkpoint", Vector3.new(4, 1, 4), CFrame.new(islandPoint(island, placements.Checkpoint)), model)
end

-- Builds every relic listed in Placements.<island>.Relics.
function WorldBuilder.buildRelics(island)
    local placements = placementsFor(island)
    local count = 0
    for relicId, position in placements.Relics or {} do
        WorldBuilder.buildRelic(island, relicId, position)
        count += 1
    end
    return count
end

-- Replaces ServerStorage.RelicMeshes with the relics of an import of SpiritRelics.fbx (tools/blender/relics/spirit_relics.py): one
-- template per relic, its pieces placed round its anchor (Relic_<Id>_Anchor, the point the relic floats at). Pieces keep their names:
-- Relic_<Id>_Body (painted), Relic_<Id>_Core (its glowing heart: the part that dims when found) and Relic_<Id>_Glow_<hex>.
function WorldBuilder.storeRelics(model)
    local folder = ServerStorage:FindFirstChild("RelicMeshes")
    if folder then
        folder:Destroy()
    end
    folder = Instance.new("Folder")
    folder.Name = "RelicMeshes"
    local stored = {}
    for _, relic in GameConfig.Relics do
        local prefix = "Relic_" .. relic.Id .. "_"
        local anchor = model:FindFirstChild(prefix .. "Anchor", true)
        if anchor then
            local template = Instance.new("Model")
            template.Name = relic.Id
            local offset = CFrame.new(-anchor.Position)
            for _, part in model:GetDescendants() do
                if part:IsA("BasePart") and part ~= anchor and string.sub(part.Name, 1, #prefix) == prefix then
                    local piece = part:Clone()
                    for _, child in piece:GetChildren() do
                        if not child:IsA("SurfaceAppearance") then
                            child:Destroy()
                        end
                    end
                    piece.CFrame = offset * part.CFrame
                    piece.Anchored = true
                    piece.Parent = template
                end
            end
            template.Parent = folder
            table.insert(stored, relic.Id)
        end
    end
    folder.Parent = ServerStorage
    model:Destroy()
    return stored
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
    local point = islandPoint(island, localPosition) + Vector3.new(0, look.Lift or 0, 0) -- (Lift: studs the modelled relic floats higher than the old cube)
    local meshes = ServerStorage:FindFirstChild("RelicMeshes")
    local template = meshes and meshes:FindFirstChild(relicId)
    local crystal
    if template then
        -- the modelled relic, floating at the point (its anchor), turned to face where players come from (look.Yaw, degrees)
        local frame = CFrame.new(point) * CFrame.Angles(0, math.rad(look.Yaw or 0), 0)
        for _, piece in template:GetChildren() do
            local part = piece:Clone()
            part.CFrame = frame * piece.CFrame
            part.Anchored = true
            part.CanCollide = false
            part.CanTouch = false
            part.CanQuery = false
            local hex = string.match(part.Name, "_Glow_(%x%x%x%x%x%x)$")
            if part.Name == "Relic_" .. relicId .. "_Core" then
                part.Name = "RelicCrystal" -- (RelicController and DiscoveryService find the relic's heart by this name)
                part.Material = Enum.Material.Neon
                part.Color = look.Color
                crystal = part
            elseif hex then
                part.Material = Enum.Material.Neon
                part.Color = Color3.fromHex(hex)
                part:SetAttribute("RelicGlow", true)
            end
            part.Parent = model
        end
    end
    if not crystal then -- no model stored for it: the old glowing cube
        crystal = Instance.new("Part")
        crystal.Name = "RelicCrystal"
        crystal.Size = Vector3.new(1.6, 1.6, 1.6)
        crystal.CFrame = CFrame.new(point) * CFrame.Angles(0, math.rad(45), math.rad(45))
        crystal.Material = Enum.Material.Neon
        crystal.Color = look.Color
        crystal.Anchored = true
        crystal.CanCollide = false
        crystal.CanTouch = false
        crystal.Parent = model
    end
    addLight(crystal, look.Color, 16, 1.5)
    addSparkles(crystal, look.Color, 6).Name = "RelicSparkles"

    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Collect"
    prompt.ObjectText = relicConfig.DisplayName
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 1
    prompt.MaxActivationDistance = relicConfig.Reach or 12
    prompt.RequiresLineOfSight = false
    prompt.Parent = crystal

    model.PrimaryPart = crystal
    model:SetAttribute("RelicId", relicId)
    model:SetAttribute("RelicPoint", point)
    model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
    CollectionService:AddTag(model, GameConfig.RelicTag)
    model.Parent = folder
    return model
end

-- What CrossingBuilder (Murim Crossing's court, gate, banners and people) borrows from here, so that nothing is made twice.
WorldBuilder.placeTemplate = placeTemplate
WorldBuilder.hasTemplate = hasTemplate
WorldBuilder.marker = marker
WorldBuilder.addLight = addLight
WorldBuilder.dressPiece = dressPiece -- (a hub person's modelled face pieces, for the representatives)
WorldBuilder.npcData = npcData

return WorldBuilder

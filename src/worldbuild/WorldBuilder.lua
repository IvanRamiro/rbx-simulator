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
--   Yggdrasil (the hub): WB.buildWaystones, WB.buildSpawn, WB.buildSpawnSlots, WB.buildLeaderboard,
--   WB.buildShops, WB.buildQiSpring, WB.buildAltar, WB.buildRootColliders
--   every other island: WB.buildCheckpoint(island); Ember Peak also WB.buildLavafall, Moonlit Isle
--   WB.buildStarWell
--   terrain colours (once, after any terrain build): WB.applyMaterialColors()
--
-- Bridges (assets/world/Bridges): WB.storeBridgeKit(<import>, theme), then WB.buildBridges().
--
-- Eggs (assets/eggs/<EggId>.fbx): WB.storeEgg(<import>, eggId), then WB.buildEggStands(island).
-- Collision fidelity applies asynchronously; confirm with WB.checkCollision in a later call.
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
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
}

-- An island's terrain data, its grids turned by its quarter turns (Turns, layout.py) about its
-- centre: the generator writes them unturned. Quarter turns map cells onto cells exactly.
local function terrainData(island)
    local data = require(ServerStorage.WorldBuild.Terrain:FindFirstChild(island):Clone())
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
    { Prefix = "SI_Waystone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_LotusStone", Fidelity = Enum.CollisionFidelity.Hull },
    { Prefix = "SI_MossRock", Fidelity = Enum.CollisionFidelity.Hull },
    -- Yggdrasil: the Hatching Altar's dais must be walkable, under its arching roots
    { Prefix = "YG_AltarRoots", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_Altar", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
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
    { Prefix = "YG_Stele", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_Blacksmith", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_BuySell", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
    { Prefix = "YG_Market", Fidelity = Enum.CollisionFidelity.PreciseConvexDecomposition },
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
    YG_SpawnDaisGlow = table.clone(GLOW),
    YG_SteleGlow = table.clone(GLOW),
    YG_BlacksmithGlow = table.clone(GLOW),
    YG_BuySellStones = table.clone(GLOW),
    YG_BuySellLanterns = table.clone(GLOW),
    YG_MarketCoins = table.clone(GLOW),
    YG_MarketLanterns = table.clone(GLOW),
    YG_AltarPool = table.clone(GLOW),
    YG_AltarGemYggdrasil = table.clone(GLOW),
    YG_AltarGemJade = table.clone(GLOW),
    YG_AltarGemEmber = table.clone(GLOW),
    YG_AltarGemMoonlit = table.clone(GLOW),
    YG_AltarGemOrigin = table.clone(GLOW),
}
-- the Lion Court's flagstones lie on level terrain: decoration underfoot, so nothing catches on them
WorldBuilder.Appearance.BI_CourtPaving = { CanCollide = false, CastShadow = false }
-- The outer islands' arena floors (tools/blender/world/island_upgrades.py): decoration on level ground, like the Lion Court's
WorldBuilder.Appearance.JG_ArenaFloor = { CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.EP_ArenaFloor = { CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.MI_ArenaFloor = { CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.OA_ArenaFloor = { CanCollide = false, CastShadow = false }
-- and the paved ground of the hub and the Beginner Isle
for _, name in { "YG_Roads", "YG_Bridgeheads", "YG_PlotEdges", "YG_CompassRing", "BI_CourtApron", "BI_Roads", "BI_YardFloor" } do
    WorldBuilder.Appearance[name] = { CanCollide = false, CastShadow = false }
end
WorldBuilder.Appearance.EP_ArenaGlow = { Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 78, 14), CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.EP_PylonFire = { Material = Enum.Material.Neon, Color = Color3.fromRGB(255, 120, 20), Transparency = 0.35, CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.OA_ArenaGlow = { Material = Enum.Material.Neon, Color = Color3.fromRGB(115, 40, 255), CanCollide = false, CastShadow = false }
WorldBuilder.Appearance.SI_QiCompassGlow.Color = Color3.fromRGB(40, 210, 235)
WorldBuilder.Appearance.SI_LanternLight.Color = Color3.fromRGB(255, 150, 60)
WorldBuilder.Appearance.SI_SpringWater.Color = Color3.fromRGB(40, 165, 180)
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
WorldBuilder.Appearance.YG_TrunkVeins.Color = Color3.fromRGB(40, 210, 235) -- the Qi Spring's and the compass's Qi
WorldBuilder.Appearance.YG_SeedLanterns.Color = Color3.fromRGB(255, 170, 40)
WorldBuilder.Appearance.YG_BlacksmithGlow.Color = Color3.fromRGB(255, 105, 20)
WorldBuilder.Appearance.YG_BuySellStones.Color = Color3.fromRGB(30, 215, 170) -- the Spirit Stones' jade
WorldBuilder.Appearance.YG_BuySellLanterns.Color = Color3.fromRGB(235, 60, 30)
WorldBuilder.Appearance.YG_MarketCoins.Color = Color3.fromRGB(255, 170, 40)
WorldBuilder.Appearance.YG_MarketLanterns.Color = Color3.fromRGB(235, 60, 30)
-- the Hatching Altar's pool of golden Qi, and its seals' gems in each island's glow (the waystones')
-- a deep amber, a little clear: Neon blooms a paler gold to a flat lemon disc, and the jade heart
-- showing through reads as liquid in the lotus
WorldBuilder.Appearance.YG_AltarPool.Color = Color3.fromRGB(255, 110, 0)
WorldBuilder.Appearance.YG_AltarPool.Transparency = 0.3
WorldBuilder.Appearance.YG_AltarGemYggdrasil.Color = Color3.fromRGB(40, 210, 235)
WorldBuilder.Appearance.YG_AltarGemJade.Color = Color3.fromRGB(40, 215, 110)
WorldBuilder.Appearance.YG_AltarGemEmber.Color = Color3.fromRGB(255, 105, 25)
WorldBuilder.Appearance.YG_AltarGemMoonlit.Color = Color3.fromRGB(120, 100, 255)
WorldBuilder.Appearance.YG_AltarGemOrigin.Color = Color3.fromRGB(175, 45, 255)

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

-- A piece's look from WorldBuilder.Appearance (keyed by its template's name).
local function applyLook(part, name)
    local look = WorldBuilder.Appearance[name or part.Name]
    if look then
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

-- Places a template so its authored origin lands on `frame`, optionally scaled about that origin. Its look
-- comes from WorldBuilder.Appearance as it is now, not as it was when the template was stored.
local function placeTemplate(island, name, frame, parent, scale)
    local source = template(island, name)
    local part = source:Clone()
    scale = scale or 1
    part.Size = source.Size * scale
    part.CFrame = frame * (source.CFrame.Rotation + source.CFrame.Position * scale)
    applyLook(part, name)
    part.Parent = parent
    return part
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
            local folder = ServerStorage.WorldKit[where.Island]
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
        WorldBuilder.applyCollision(ServerStorage.WorldKit[where.Island])
    end
    return stored
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
    for name, list in placements.Kit do
        for index, entry in list do
            local frame = centre * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
            if WorldBuilder.ClearOfBridges[name] and onBridgeEnd(ends, frame.Position) then
                continue
            end
            local part = placeTemplate(island, name, frame, folder, entry.Scale)
            part.Name = name .. "_" .. index
            local light = WorldBuilder.Lights[name]
            if light then
                addLight(part, part.Color, light.Range, light.Brightness)
            end
            for _, preset in WorldBuilder.Emitters[name] or {} do
                addEmitterPreset(part, preset)
            end
            placed += 1
        end
    end
    WorldBuilder.applyCollision(folder)
    return placed
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

-- ---------- route waystones ----------

-- Where each waystone points: the destination and its glow. The rank it names is its bridge's
-- (Placements/Bridges.lua), the same one the bridge's Qi barrier checks, so the two can't differ.
WorldBuilder.Waystones = {
    JadeRoute = { Island = "JadeGrove", Title = "Jade Grove", Color = Color3.fromRGB(40, 215, 110) },
    EmberRoute = { Island = "EmberPeak", Title = "Ember Peak", Color = Color3.fromRGB(255, 105, 25) },
    MoonlitRoute = { Island = "MoonlitIsle", Title = "Moonlit Isle", Color = Color3.fromRGB(120, 100, 255) },
    BeginnerRoute = { Island = "BeginnerIsle", Title = "Beginner Isle", Subtitle = "The Stone Lion waits\nOpen to all", Color = Color3.fromRGB(255, 170, 60) },
    OriginRoute = { Island = "OriginAbyss", Title = "Origin Abyss", Color = Color3.fromRGB(175, 45, 255) },
    RootPath = { Title = "Root of the Island", Subtitle = "Climb down the great root", Color = Color3.fromRGB(255, 170, 40) },
}

local function rankLine(rankId)
    local rankName
    for _, rank in GameConfig.Ranks do
        if rank.Id == rankId then
            rankName = rank.Name
        end
    end
    assert(rankName, "no rank " .. tostring(rankId))
    return string.format("Bridge opens at\n%s", rankName)
end

local function inscribe(panel, title, subtitle, color)
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
        label.Name = if index == 1 then "Title" else "Subtitle"
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

function WorldBuilder.buildWaystones(island)
    local placements = placementsFor(island)
    local folder = WorldBuilder.islandFolder(island, "Waystones")
    folder:ClearAllChildren()
    local bridges = require(ServerStorage.WorldBuild.Placements.Bridges:Clone()).Bridges
    for _, entry in placements.Waystones do
        local info = WorldBuilder.Waystones[entry.Route]
        assert(info, "no waystone info for " .. entry.Route)
        local bridge = bridges[entry.Route]
        local frame = standFrame(island, entry)
        local model = Instance.new("Model")
        model.Name = "Waystone_" .. entry.Route
        model:SetAttribute("Route", entry.Route)
        placeTemplate(island, "SI_Waystone", frame, model).Name = "Stele"
        local glow = placeTemplate(island, "SI_WaystoneGlow", frame, model)
        glow.Name = "Glow"
        glow.Color = info.Color
        addLight(glow, info.Color, 10, 0.8)

        local panelSize = placements.WaystonePanel.Size
        local panel = marker("Inscription", Vector3.new(panelSize.X, panelSize.Y, 0.05),
            frame * CFrame.new(placements.WaystonePanel.Centre), model)
        inscribe(panel, info.Title, info.Subtitle or rankLine(bridge and bridge.RankId), info.Color)
        model.Parent = folder
    end
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- ---------- bridges ----------
-- The bridges from Yggdrasil to the other five islands (Placements/Bridges.lua). Each is a Model
-- in FloatingIslands.Bridges: one straight span, a deck along its nodes in pieces of up to Segment
-- studs, low rails, and at its start a gate whose Qi barrier (tagged
-- GameConfig.BridgeBarrierTag) stops everyone below its RankId (BridgeBarriers.client lets qualified
-- players through; WorldService returns the rest). Zone parts past the gate tell the server who is
-- on the bridge. The deck and rails are the collision, a plain blockout until the themed kit dresses
-- them.
WorldBuilder.BridgeThemes = {
    Jade = { Deck = Color3.fromRGB(150, 110, 70), DeckMaterial = Enum.Material.WoodPlanks, Rail = Color3.fromRGB(80, 160, 110), Glow = Color3.fromRGB(40, 215, 110) },
    Ember = { Deck = Color3.fromRGB(55, 48, 46), DeckMaterial = Enum.Material.Basalt, Rail = Color3.fromRGB(35, 30, 30), Glow = Color3.fromRGB(255, 105, 25) },
    Moon = { Deck = Color3.fromRGB(225, 225, 235), DeckMaterial = Enum.Material.Marble, Rail = Color3.fromRGB(215, 185, 110), Glow = Color3.fromRGB(120, 100, 255) },
    Lion = { Deck = Color3.fromRGB(176, 164, 142), DeckMaterial = Enum.Material.Slate, Rail = Color3.fromRGB(150, 40, 30), Glow = Color3.fromRGB(255, 170, 60) },
    Origin = { Deck = Color3.fromRGB(60, 58, 70), DeckMaterial = Enum.Material.Slate, Rail = Color3.fromRGB(40, 38, 50), Glow = Color3.fromRGB(175, 45, 255) },
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

-- Dress a built bridge with its theme's kit, if the kit is stored: a deck section on every
-- piece of deck, supports hanging under it, the gate. The blockout
-- stays as the invisible collision. Returns the number of pieces placed.
local function dressBridge(model, theme)
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
    local barrier = gate and gate:FindFirstChild("QiBarrier")
    if barrier then
        local base = barrier.CFrame * CFrame.new(0, -barrier.Size.Y / 2, 0)
        if placeKitPiece(theme, "Gate", base, dressing) then
            count += 1
            for _, part in gate:GetChildren() do
                if part.Name == "Pillar" or part.Name == "Lintel" then
                    part.Transparency = 1
                end
            end
        end
    end
    -- the blockout becomes invisible collision under the kit, unless a deck section is bare: then the
    -- whole deck and its rails stay as they are
    if count > 0 and not bareDeck then
        for _, c in model:GetChildren() do
            if c.Name == "Deck" or c.Name == "Rail" then
                c.Transparency = 1
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
        local info = WorldBuilder.Waystones[route]
        local width = data.DeckWidth
        local model = Instance.new("Model")
        model.Name = route
        model:SetAttribute("Route", route)
        model:SetAttribute("RankId", bridge.RankId)
        model:SetAttribute("Destination", info.Title)
        model:SetAttribute("Island", info.Island) -- the island it leads to, closed below RankId too
        local zones = Instance.new("Folder")
        zones.Name = "Zones"
        zones.Parent = model
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
                deckPiece(model, theme, width, a:Lerp(b, (k - 1) / pieces), a:Lerp(b, k / pieces), run + d0 >= zoneFrom and zones or nil)
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
        local barrier = bridgePart("QiBarrier", Vector3.new(width, BRIDGE.GateHeight, 0.5), frame * CFrame.new(0, BRIDGE.GateHeight / 2, 0), gate, theme.Glow, Enum.Material.ForceField)
        barrier.Transparency = 0.2
        barrier.CastShadow = false
        barrier:SetAttribute("RankId", bridge.RankId)
        barrier:SetAttribute("Route", route)
        CollectionService:AddTag(barrier, GameConfig.BridgeBarrierTag)
        local light = Instance.new("PointLight")
        light.Color, light.Range, light.Brightness = theme.Glow, 12, 0.6
        light.Parent = barrier
        gate.Parent = model
        model:SetAttribute("ReturnTo", base - dir * 3 + Vector3.new(0, 3, 0))
        model:SetAttribute("KitPieces", dressBridge(model, bridge.Theme))
        model.Parent = folder
    end
    return #folder:GetChildren()
end

-- ---------- spawn, Qi Spring, relic ----------

function WorldBuilder.buildSpawn(island)
    local placements = placementsFor(island)
    local model = WorldBuilder.islandFolder(island)
    local old = model:FindFirstChild("IslandSpawn")
    if old then
        old:Destroy()
    end
    return spawnPoint("IslandSpawn", CFrame.new(islandPoint(island, placements.Spawn + Vector3.new(0, 0.5, 0))), model)
end

-- ---------- spawn slots and plots (Yggdrasil) ----------

-- One slot per player (Placements.<island>.SpawnSlots), each a Model "Slot<n>" in
-- FloatingIslands.<island>.SpawnSlots: its dais, the dais's ring ("Ring"), a SpawnLocation ("Spawn")
-- facing the island's centre and the inscription on its name stone ("Plaque"). WorldService gives
-- each player a slot, lights its ring and cuts their name into the stone.
function WorldBuilder.buildSpawnSlots(island)
    local placements = placementsFor(island)
    local folder = WorldBuilder.islandFolder(island, "SpawnSlots")
    folder:ClearAllChildren()
    local centre = islandFrame(island).Position
    for index, entry in placements.SpawnSlots do
        local frame = standFrame(island, entry)
        local model = Instance.new("Model")
        model.Name = "Slot" .. index
        model:SetAttribute("Slot", index)
        placeTemplate(island, "YG_SpawnDais", frame, model).Name = "Dais"
        placeTemplate(island, "YG_SpawnDaisGlow", frame, model).Name = "Ring"

        local top = frame.Position + Vector3.new(0, placements.SlotTop + 0.5, 0)
        spawnPoint("Spawn", CFrame.lookAt(top, Vector3.new(centre.X, top.Y, centre.Z)), model)

        local plaqueSize = placements.SlotPanel.Size
        local plaque = marker("Plaque", Vector3.new(plaqueSize.X, plaqueSize.Y, 0.05),
            frame * CFrame.new(placements.SlotPanel.Centre), model)
        inscribe(plaque, "", "", Color3.new(1, 1, 1)) -- WorldService writes the owner
        model.Parent = folder
    end
    WorldBuilder.applyCollision(folder)
    return #folder:GetChildren()
end

-- What will stand on each plot, named on its notice board. Built names the building that stands
-- there now (buildLeaderboard, buildShops), and that plot is left unmarked.
WorldBuilder.Plots = {
    Leaderboard = { Title = "Leaderboard", Subtitle = "The greatest cultivators, carved here soon", Built = "Ascension Stele" },
    Blacksmith = { Title = "Blacksmith", Subtitle = "Swords and spears for every realm", Built = "Dragon-Kiln Forge" },
    Marketplace = { Title = "Marketplace", Subtitle = "Spirit eggs for Spirit Stones", Built = "Coin-Tree Market" },
    BuySell = { Title = "Buy & Sell", Subtitle = "Sell pets and weapons for Spirit Stones", Built = "Jade Scale" },
}
-- ---------- the Ascension Stele (the leaderboard) ----------
WorldBuilder.SteleRows = 10
WorldBuilder.SteleGlow = Color3.fromRGB(205, 120, 20) -- deep amber: a paler gold blooms into a loud frame round the names
local STELE_INK = { Color3.fromRGB(255, 205, 90), Color3.fromRGB(225, 230, 240), Color3.fromRGB(230, 150, 90) } -- the top three
local STELE_TEXT = Color3.fromRGB(236, 226, 200)

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

-- The Ascension Stele on the Leaderboard plot (FloatingIslands.<island>.Leaderboard): the stele and
-- its glow, the title plaque ("Title") and the board ("Board"), whose SurfaceGui holds a heading and
-- rows "Row1".."Row<SteleRows>", each with Place, Cultivator, Rank and Qi labels. LeaderboardService
-- writes the names; the builder leaves the rows empty.
function WorldBuilder.buildLeaderboard(island)
    local placements = placementsFor(island)
    local plot = placements.Plots.Leaderboard
    local folder = WorldBuilder.islandFolder(island, "Leaderboard")
    folder:ClearAllChildren()
    local frame = islandFrame(island) * CFrame.new(plot.Centre) * CFrame.Angles(0, plot.Yaw, 0)
    placeTemplate(island, "YG_Stele", frame, folder).Name = "Stele"
    local glow = placeTemplate(island, "YG_SteleGlow", frame, folder)
    glow.Name = "Glow"
    glow.Color = WorldBuilder.SteleGlow
    addLight(glow, WorldBuilder.SteleGlow, 16, 0.7)

    local _, titleGui = textPanel("Title", placements.SteleTitle.Size, frame * CFrame.new(placements.SteleTitle.Centre), folder, 60)
    steleLabel("Text", titleGui, UDim2.fromScale(0.96, 0.9), UDim2.fromScale(0.02, 0.05), Enum.TextXAlignment.Center,
        Color3.fromRGB(240, 222, 170)).Text = "Ascension Stele"

    local _, gui = textPanel("Board", placements.SteleBoard.Size, frame * CFrame.new(placements.SteleBoard.Centre), folder, 40)
    local heading = steleLabel("Heading", gui, UDim2.fromScale(0.9, 0.1), UDim2.fromScale(0.05, 0.02), Enum.TextXAlignment.Center, STELE_INK[1])
    heading.Text = "The most Qi under Heaven"
    local rowHeight = 0.84 / WorldBuilder.SteleRows
    for index = 1, WorldBuilder.SteleRows do
        local row = Instance.new("Frame")
        row.Name = "Row" .. index
        row.Size = UDim2.fromScale(0.94, rowHeight * 0.92)
        row.Position = UDim2.fromScale(0.03, 0.14 + (index - 1) * rowHeight)
        row.BackgroundColor3 = Color3.new(1, 1, 1)
        row.BackgroundTransparency = if index % 2 == 0 then 0.94 else 1
        row.BorderSizePixel = 0
        row.Parent = gui
        local ink = STELE_INK[index] or STELE_TEXT
        steleLabel("Place", row, UDim2.fromScale(0.08, 1), UDim2.fromScale(0, 0), Enum.TextXAlignment.Center, ink).Text = tostring(index)
        steleLabel("Cultivator", row, UDim2.fromScale(0.44, 1), UDim2.fromScale(0.1, 0), Enum.TextXAlignment.Left, ink)
        steleLabel("Rank", row, UDim2.fromScale(0.28, 0.8), UDim2.fromScale(0.55, 0.1), Enum.TextXAlignment.Left, STELE_TEXT)
        steleLabel("Qi", row, UDim2.fromScale(0.16, 1), UDim2.fromScale(0.84, 0), Enum.TextXAlignment.Right, ink)
    end
    WorldBuilder.applyCollision(folder)
    return folder
end

-- ---------- the shops (Yggdrasil) ----------
-- Each shop's building (tools/blender/world/ygg_shops.py): its plot, the kit pieces it is made of
-- and what its prompt says. ShopService opens the shop named by the prompt's "Shop" attribute.
WorldBuilder.Shops = {
    Blacksmith = { Plot = "Blacksmith", Pieces = { "YG_Blacksmith", "YG_BlacksmithGlow" }, Action = "Browse" },
    BuySell = { Plot = "BuySell", Pieces = { "YG_BuySell", "YG_BuySellStones", "YG_BuySellLanterns" }, Action = "Trade" },
    Marketplace = { Plot = "Marketplace", Pieces = { "YG_Market", "YG_MarketCoins", "YG_MarketLanterns" }, Action = "Browse" },
}
WorldBuilder.ForgeLight = Color3.fromRGB(255, 120, 40)
WorldBuilder.LanternLight = Color3.fromRGB(255, 130, 70) -- warm: a red light tints the paving pink

-- What goes on each of a shop's effect points (Placements.<island>.Shops.<Shop>.Fx).
local SHOP_FX = {
    -- flames licking up inside the dragon's jaws (kept short so they stay under its upper jaw) and
    -- sparks spat out of its mouth toward the anvil (a part's Back face is its +Z, the shop's front)
    Forge = function(part)
        part.Size = Vector3.new(3.6, 0.6, 2)
        addEmitterPreset(part, "Flames")
        local flames = part:FindFirstChild("Flames")
        flames.Speed = NumberRange.new(1.2, 2)
        flames.Lifetime = NumberRange.new(0.4, 0.7)
        flames.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.3), NumberSequenceKeypoint.new(1, 0.1) })
        addEmitterPreset(part, "EmberSparks")
        part:FindFirstChild("EmberSparks").EmissionDirection = Enum.NormalId.Back
        addLight(part, WorldBuilder.ForgeLight, 16, 0.9) -- any brighter floods the pale dragon orange
    end,
    Smoke = function(part)
        part.Size = Vector3.new(2.4, 0.4, 2.4)
        addEmitterPreset(part, "Smoke")
    end,
    Stones = function(part)
        addLight(part, WorldBuilder.Appearance.YG_BuySellStones.Color, 14, 0.9)
    end,
    Lantern = function(part)
        addLight(part, WorldBuilder.LanternLight, 12, 0.5)
    end,
    Coins = function(part)
        addLight(part, WorldBuilder.Appearance.YG_MarketCoins.Color, 14, 0.7)
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

-- The Hatching Altar (tools/blender/world/ygg_altar.py), where eggs carried home are hatched
-- (PetService): FloatingIslands.<island>.HatchingAltar, placed by GameConfig.HatchingAltar, with
-- "Prompt" (its prompt, attribute Hatchery, opens the hatching window), "Cradle" (where PetService
-- lays an egg, on the pool's surface) and "Motes" (golden motes over the pool, and its light).
-- Spots in the altar's frame, as authored (ygg_altar.CRADLE, PROMPT, FX).
WorldBuilder.Altar = {
    Pieces = { "YG_Altar", "YG_AltarRoots", "YG_AltarPool", "YG_AltarGemYggdrasil", "YG_AltarGemJade", "YG_AltarGemEmber",
        "YG_AltarGemMoonlit", "YG_AltarGemOrigin" },
    Cradle = Vector3.new(0, 4.15, 0),
    Prompt = Vector3.new(0, 3.2, 3.2),
    Motes = Vector3.new(0, 4.45, 0),
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
    prompt.ObjectText = "Hatching Altar"
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt:SetAttribute("Hatchery", true)
    prompt.Parent = holder
    local motes = marker("Motes", Vector3.new(4.4, 0.2, 4.4), frame * CFrame.new(WorldBuilder.Altar.Motes), model)
    addEmitterPreset(motes, "GoldenMotes")
    addLight(motes, Color3.fromRGB(255, 170, 60), 18, 1.1)
    model.Parent = folder
    WorldBuilder.applyCollision(model)
    return model
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
    local centre = islandPoint(island, placements.SpringCentre)
    local water = marker("SpringWater", Vector3.new(2, 0.2, 2), CFrame.new(centre), station)
    addLight(water, glow, 22, 0.9)

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

    WorldBuilder.buildWaterfall(station, islandPoint(island, placements.SpillEnd), centre, WorldBuilder.Falls.Water)
    station.Parent = model
    return station
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
function WorldBuilder.buildWaterfall(parent, lip, from, look)
    local out = Vector3.new(lip.X - from.X, 0, lip.Z - from.Z).Unit
    local holder = marker(look.Name, Vector3.new(1, 1, 1), CFrame.new(lip), parent)
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
        b.Color = ColorSequence.new(look.Color)
        b.LightEmission = look.LightEmission
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
    mist.Color = ColorSequence.new(look.Mist)
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
    spray.Color = ColorSequence.new(look.Spray)
    spray.LightEmission = look.SprayEmission
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
    EmberHeart = { Color = Color3.fromRGB(255, 150, 30) },
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
    crystal.CFrame = CFrame.new(islandPoint(island, localPosition)) * CFrame.Angles(0, math.rad(45), math.rad(45))
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

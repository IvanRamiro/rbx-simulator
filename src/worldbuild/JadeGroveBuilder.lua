-- Build-time only: run from Studio (Edit mode) to assemble Jade Grove's expanded ground and its own asset library (2026-11-22, phase A: written and linted, NOT yet run:
-- the owner imports the FBX files first). Require a clone so Studio's module cache never serves an old copy:
--
--   local JB = require(game.ServerStorage.WorldBuild.JadeGroveBuilder:Clone())
--   -- once per FBX file, File > Import 3D in Edit mode, one at a time, into Workspace, nothing renamed, in this order (assets/world/JadeGrove/Library):
--   --   JadeGrove_Trees, JadeGrove_Bamboo, JadeGrove_Rocks, JadeGrove_Plants, JadeGrove_Structures, JadeGrove_Bridges, JadeGrove_Cliffs
--   JB.storeKit(workspace.<the import's model>)   -- moves its meshes into ServerStorage.WorldAssets.JadeGroveAssets as templates (WorldBuilder.storeKit, anchor JL_Anchor)
--   JB.buildTerrain()                             -- the expanded ground: only the columns Terrain/JadeGrove.lua gives a height, one by one (Ember Peak's corner in its square is never rewritten)
--   JB.build()                                    -- Workspace.FloatingIslands.JadeGrove.{Terrain, Buildings, Vegetation, Rocks, Props, Paths}; removes the old dress; idempotent
--   JB.check()                                    -- a report: parts, colliders, lights, what is missing, what old is left
--
-- What it makes, all from Placements/JadeGroveLibrary.lua (island-local studs):
--   <folder>/<Piece>_<n>   a Model per placement holding the piece's MeshParts (one per material), each with its Roblox material and colour from Looks (no texture), never colliding
--   <folder>/Colliders     invisible Plastic boxes and cylinders (one material: one batch): trunks, boulders, steps, floors, walls, bridge decks and rails, the guardian tree's shelves and decks
--   Props/Lights           at most eight PointLights (small markers); glow is a Neon part on the piece, never a light
--   Buildings/Falls        the waterfalls (WorldBuilder.buildWaterfall; the short ones shortened to their drop); Terrain/Water the stream, the pools (Glass parts)
--   Paths/Spots            marked places (the hidden ones are not signposted anywhere in the world: these markers are for the next phases only)
-- It REPLACES the first foundation's Jade dress (replace means delete): the old tree, bamboo, fern, mushroom, log, outcrop, ruin pillar, standing stone, hollow stone and
-- lantern copies and templates, the Elder Jade Tree's pieces and the old underside. The four templates Murim Crossing's first-foundation dress still borrows are kept until
-- that track stops using them (Placements.Remove.Borrowed). The arena floor, glade floor, hollow rim and water, egg pedestals, hermitage, grove gate, relics and
-- checkpoint (Placements/JadeGrove.lua) stay exactly as they are.
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local H = require(WorldBuild:WaitForChild("Placements"):WaitForChild("JadeGroveLibrary"):Clone())

local JadeGroveBuilder = {}

local ISLAND = H.Island
local KIT = H.Kit
local VOXEL = 4
local SHELL = 22 -- studs of terrain under the centre line (the gorge reaches 10.5 down); the old shell was 14
local MAX_LIGHTS = 8

function JadeGroveBuilder.storeKit(model)
    return WorldBuilder.storeKit(KIT, model, "JL_Anchor")
end

-- ---------------------------------------------------------------------------------------------------------------------------------
-- the terrain
-- ---------------------------------------------------------------------------------------------------------------------------------
-- A grid array written as a run-length string: values joined by commas, "~N" for N entries of `off` (false for heights, 0 for material indices).
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

local function terrainData()
    local data = require(WorldBuild:WaitForChild("Terrain"):WaitForChild(ISLAND):Clone())
    if type(data.Heights) == "string" then
        data = table.clone(data)
        data.Heights = expand(data.Heights, false)
        data.MaterialIndex = expand(data.MaterialIndex, 0)
    end
    assert((data.Turns or 0) == 0, "Jade Grove's grid is written unturned")
    return data
end

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

-- The ground of Terrain/JadeGrove.lua, written column by column in strips (so Studio stays responsive): a column is written only where the data has a height, so the
-- rest of the grid's square (Ember Peak's corner, which the old data's square also overlapped) is read and left exactly as it is. A voxel's surface renders from its
-- centre (occupancy 0) to the next one up (1): the same rule as WorldBuilder.buildTerrain. Surface material on the top two voxels, Sandstone kept through, Mud under.
function JadeGroveBuilder.buildTerrain()
    local data = terrainData()
    local materials = {}
    for index, name in data.Materials do
        materials[index] = Enum.Material[name]
    end
    local sub = Enum.Material.Mud
    local highest = -math.huge
    for _, h in data.Heights do
        if h then
            highest = math.max(highest, h)
        end
    end
    local bottomY = data.Centre.Y - SHELL
    local minY = math.floor(bottomY / VOXEL) * VOXEL
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
            if owned then
                break
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
                        local surface = materials[data.MaterialIndex[index]]
                        local keep = data.Materials[data.MaterialIndex[index]] == "Sandstone"
                        for k = 1, layers do
                            local y0 = minY + (k - 1) * VOXEL
                            local material, occupancy = Enum.Material.Air, 0
                            if y0 + VOXEL > bottomY then
                                local solid = math.clamp((top - y0 - VOXEL / 2) / VOXEL, 0, 1)
                                if solid > 0 then
                                    -- (the top two voxels, or all of a Sandstone column: a top just over a voxel's boundary leaves the one under it showing)
                                    material = if keep or y0 + VOXEL >= top - VOXEL then surface else sub
                                    occupancy = solid
                                    filled += 1
                                end
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

-- ---------------------------------------------------------------------------------------------------------------------------------
-- the old dress (replace means delete)
-- ---------------------------------------------------------------------------------------------------------------------------------
local function baseOf(name)
    return string.match(name, "^(.-)_%d+$") or name
end

-- The first foundation's dress: every name in Placements/JadeGrove.lua's Kit except the pieces whose functions stay (Remove.Keep).
local function oldDress()
    local kit = require(WorldBuild:WaitForChild("Placements"):WaitForChild("JadeGrove"):Clone()).Kit
    local keep = {}
    for _, name in H.Remove.Keep do
        keep[name] = true
    end
    local set = {}
    for name in kit do
        if not keep[name] then
            set[name] = true
        end
    end
    return set
end

-- Deletes the old copies, the old island pieces and the old templates; returns the counts. The kit folder keeps what Remove.Borrowed names.
function JadeGroveBuilder.removeOld()
    local root = WorldBuilder.islandFolder(ISLAND)
    local old = oldDress()
    local islandPieces = {}
    for _, name in H.Remove.IslandPieces do
        islandPieces[name] = true
    end
    local keep = {}
    for _, name in H.Remove.Borrowed do
        keep[name] = true
    end
    local counts = { Placed = 0, IslandPieces = 0, Templates = 0, KeptBorrowed = 0, Stale = 0 }
    local kit = root:FindFirstChild("Kit")
    for _, d in (kit and kit:GetChildren() or {}) do
        if old[baseOf(d.Name)] then
            d:Destroy()
            counts.Placed += 1
        end
    end
    for _, d in root:GetDescendants() do
        if islandPieces[d.Name] then
            d:Destroy()
            counts.IslandPieces += 1
        end
    end
    local folder = WorldBuilder.kitFolder(KIT)
    for _, d in (folder and folder:GetChildren() or {}) do
        local base = WorldBuilder.splitName(d.Name)
        if old[base] then
            if keep[base] then
                counts.KeptBorrowed += 1
            else
                d:Destroy()
                counts.Templates += 1
            end
        end
    end
    -- the polish pass (2026-11-23) merged small accent materials into each piece's main one: the meshes the new FBX files no longer hold stay in the kit when it is
    -- re-imported (WorldBuilder.storeKit replaces same-named parts only), and would be placed as extra parts: destroy them (never one the borrowed list or a placement names)
    local placed = {}
    for name in H.Place do
        placed[name] = true
    end
    for _, name in H.Remove.StaleMeshes or {} do
        local template = folder and folder:FindFirstChild(name)
        local base = WorldBuilder.splitName(name)
        if template and not keep[base] and not placed[name] then
            template:Destroy()
            counts.Stale += 1
        end
    end
    return counts
end

-- ---------------------------------------------------------------------------------------------------------------------------------
-- placing
-- ---------------------------------------------------------------------------------------------------------------------------------
local function applyLook(part, suffix)
    local look = H.Looks[suffix]
    if not look then
        return
    end
    part.Material = Enum.Material[look.Material]
    part.Color = Color3.fromRGB(look.Color[1], look.Color[2], look.Color[3])
    part.Transparency = look.Transparency or 0
    part.Reflectance = look.Reflectance or 0
    part.CastShadow = look.CastShadow ~= false
end

local function quiet(part)
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.Massless = true
    if part:IsA("MeshPart") then -- (the water's plain Parts have no CollisionFidelity)
        part.CollisionFidelity = Enum.CollisionFidelity.Box
    end
end

local function folderOf(root, name)
    local f = root:FindFirstChild(name)
    if not f then
        f = Instance.new("Folder")
        f.Name = name
        f.Parent = root
    end
    return f
end

-- Every instance this builder made carries the attribute JadeLibrary: a second run removes exactly those.
local function clearBuilt(root)
    for _, name in H.Folders do
        local f = root:FindFirstChild(name)
        if f then
            for _, child in f:GetChildren() do
                if child:GetAttribute("JadeLibrary") then
                    child:Destroy()
                end
            end
        end
    end
end

local function mark(instance)
    instance:SetAttribute("JadeLibrary", true)
    return instance
end

local function placePiece(parent, name, index, entry, frame)
    local holder = mark(Instance.new("Model"))
    holder.Name = string.format("%s_%d", name, index)
    holder.Parent = parent
    local at = frame * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
    WorldBuilder.placeTemplate(KIT, name, at, holder, entry.Scale)
    for _, part in holder:GetChildren() do
        if part:IsA("MeshPart") then
            local _, suffix = WorldBuilder.splitName(part.Name)
            if suffix then
                applyLook(part, suffix)
            end
            quiet(part)
        end
    end
    return holder
end

local function buildPieces(root, frame)
    local placed, missing = 0, {}
    local names = {}
    for name in H.Place do
        table.insert(names, name)
    end
    table.sort(names)
    for _, name in names do
        if not WorldBuilder.hasTemplate(KIT, name) then
            table.insert(missing, name)
            continue
        end
        local folder = folderOf(root, H.Folder[name])
        for index, entry in H.Place[name] do
            placePiece(folder, name, index, entry, frame)
            placed += 1
        end
    end
    return placed, missing
end

local function buildColliders(root, frame)
    local boxes = {}
    for _, f in H.Folders do
        boxes[f] = mark(Instance.new("Folder"))
        boxes[f].Name = "Colliders"
        boxes[f].Parent = folderOf(root, f)
    end
    local n = 0
    for _, c in H.Colliders do
        local p = Instance.new("Part")
        p.Name = "Collider"
        p.Anchored = true
        p.Size = c.Size
        local cf = frame * CFrame.new(c.Position) * CFrame.Angles(0, c.Yaw, 0)
        if c.Shape == "Cylinder" then
            p.Shape = Enum.PartType.Cylinder
            cf = cf * CFrame.Angles(0, 0, math.pi / 2) -- (a Roblox cylinder's axis is its X: Size is height, diameter, diameter)
        end
        p.CFrame = cf
        p.Material = Enum.Material.Plastic
        p.Transparency = 1
        p.CanCollide = true
        p.CanQuery = true
        p.CanTouch = false
        p.CastShadow = false
        p.TopSurface = Enum.SurfaceType.Smooth
        p.BottomSurface = Enum.SurfaceType.Smooth
        p.Parent = boxes[c.Folder]
        n += 1
    end
    return n
end

local function buildLights(root, frame)
    assert(#H.Lights <= MAX_LIGHTS, "Jade Grove may have at most " .. MAX_LIGHTS .. " PointLights")
    local folder = mark(Instance.new("Folder"))
    folder.Name = "Lights"
    folder.Parent = folderOf(root, "Props")
    local color = Color3.fromRGB(H.LightColor[1], H.LightColor[2], H.LightColor[3])
    for _, l in H.Lights do
        local m = WorldBuilder.marker(l.Name, Vector3.new(0.4, 0.4, 0.4), frame * CFrame.new(l.Position), folder)
        m.Material = Enum.Material.Plastic
        WorldBuilder.addLight(m, color, l.Range, l.Brightness)
    end
    return #H.Lights
end

local function buildFalls(root, frame)
    local folder = mark(Instance.new("Folder"))
    folder.Name = "Falls"
    folder.Parent = folderOf(root, "Buildings")
    for _, f in H.Falls do
        local lip = frame:PointToWorldSpace(f.Lip)
        local from = frame:PointToWorldSpace(f.From)
        -- (Drop: how far it falls; Scale, Curtains and Splash are optional: a wide fall is several curtains side by side, see WorldBuilder.buildWaterfall)
        local holder = WorldBuilder.buildWaterfall(folder, lip, from, WorldBuilder.Falls.Water, { Drop = f.Drop, Scale = f.Scale, Curtains = f.Curtains, Splash = f.Splash })
        holder.Name = f.Name
    end
    return #H.Falls
end

local function waterPart(parent, name, size, cframe)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.Size = size
    p.CFrame = cframe
    local look = H.Looks.Water
    p.Material = Enum.Material[look.Material]
    p.Color = Color3.fromRGB(look.Color[1], look.Color[2], look.Color[3])
    p.Transparency = look.Transparency or 0
    p.CastShadow = false
    quiet(p)
    p.Parent = parent
    return p
end

local WATER_TOLERANCE = 1.0 -- studs a merged stream piece may stray from the path it replaces

-- Douglas-Peucker: the points of a polyline that matter to within `tolerance` (the ends always stay)
local function simplify(points, tolerance)
    if #points <= 2 then
        return points
    end
    local first, last = points[1], points[#points]
    local line = last - first
    local worst, at = 0, nil
    for i = 2, #points - 1 do
        local offset = points[i] - first
        local distance = if line.Magnitude < 1e-6 then offset.Magnitude else offset:Cross(line).Magnitude / line.Magnitude
        if distance > worst then
            worst, at = distance, i
        end
    end
    if worst <= tolerance or not at then
        return { first, last }
    end
    local left = simplify({ table.unpack(points, 1, at) }, tolerance)
    local right = simplify({ table.unpack(points, at, #points) }, tolerance)
    table.remove(left)
    for _, p in right do
        table.insert(left, p)
    end
    return left
end

local function buildWater(root, frame)
    local folder = mark(Instance.new("Folder"))
    folder.Name = "Water"
    folder.Parent = folderOf(root, "Terrain")
    local n = 0
    for _, s in H.Water.Streams do
        -- (every water part is a draw call, and the transparent ones are sorted one by one: 64 of them cost 53 draw calls from the hub and 108 at the pond, measured
        -- 2026-11-23. A stream's tiny straight pieces are merged wherever the path is straight to within a stud (Douglas-Peucker), the first and last points kept)
        local points = simplify(s.Points, WATER_TOLERANCE)
        for i = 1, #points - 1 do
            local a, b = frame:PointToWorldSpace(points[i]), frame:PointToWorldSpace(points[i + 1])
            local len = (b - a).Magnitude
            if len > 0.1 then
                waterPart(folder, s.Name, Vector3.new(s.Width, 0.3, len + 0.5), CFrame.lookAt((a + b) / 2, b))
                n += 1
            end
        end
    end
    for _, d in H.Water.Discs do
        waterPart(folder, d.Name, Vector3.new(0.3, d.Radius * 2, d.Radius * 2), CFrame.new(frame:PointToWorldSpace(d.Position)) * CFrame.Angles(0, 0, math.pi / 2)).Shape = Enum.PartType.Cylinder
        n += 1
    end
    return n
end

local function buildSpots(root, frame)
    local folder = mark(Instance.new("Folder"))
    folder.Name = "Spots"
    folder.Parent = folderOf(root, "Paths")
    for name, s in H.Spots do
        local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), frame * CFrame.new(s.Position), folder)
        m.Material = Enum.Material.Plastic
        m:SetAttribute("Note", s.Note)
        CollectionService:AddTag(m, "JadeSpot")
    end
    for name, b in H.Bridges do
        local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), frame * CFrame.new((b.A + b.B) / 2), folder)
        m.Material = Enum.Material.Plastic
        m:SetAttribute("Level", b.Level)
        m:SetAttribute("Span", b.Span)
        CollectionService:AddTag(m, "JadeBridge")
    end
end

function JadeGroveBuilder.build()
    if not WorldBuilder.hasTemplate(KIT, "JG_Tree_Aspire_A1") then
        return { Skipped = "the library's kit is not stored yet (import the seven FBX files and run storeKit on each): nothing built, nothing removed" }
    end
    local root = WorldBuilder.islandFolder(ISLAND)
    local frame = WorldBuilder.islandFrame(ISLAND)
    for _, name in H.Folders do
        folderOf(root, name)
    end
    clearBuilt(root)
    local removed = JadeGroveBuilder.removeOld()
    local placed, missing = buildPieces(root, frame)
    local colliders = buildColliders(root, frame)
    local lights = buildLights(root, frame)
    local falls = buildFalls(root, frame)
    local water = buildWater(root, frame)
    buildSpots(root, frame)
    if #missing > 0 then
        warn("JadeGroveBuilder: not in the kit yet (import and store these FBX files first), left out: " .. table.concat(missing, ", "))
    end
    return { Placed = placed, Missing = missing, Colliders = colliders, Lights = lights, Falls = falls, WaterParts = water, Removed = removed }
end

function JadeGroveBuilder.check()
    local root = WorldBuilder.islandFolder(ISLAND)
    local meshes, collides, lights, boxes = 0, 0, 0, 0
    local perFolder = {}
    for _, name in H.Folders do
        local f = root:FindFirstChild(name)
        local count = 0
        if f then
            for _, d in f:GetDescendants() do
                if d:IsA("MeshPart") then
                    meshes += 1
                    count += 1
                    if d.CanCollide or d.CanQuery or d.CanTouch then
                        collides += 1
                    end
                elseif d:IsA("PointLight") then
                    lights += 1
                elseif d.Name == "Collider" and d:IsA("Part") then
                    boxes += 1
                end
            end
        end
        perFolder[name] = count
    end
    local old = {}
    local oldNames = oldDress()
    local kit = root:FindFirstChild("Kit")
    local leftPlaced = 0
    for _, d in (kit and kit:GetChildren() or {}) do
        if oldNames[baseOf(d.Name)] then
            leftPlaced += 1
        end
    end
    for _, n in H.Remove.IslandPieces do
        if root:FindFirstChild(n, true) then
            table.insert(old, n)
        end
    end
    local missing = {}
    for name in H.Place do
        if not WorldBuilder.hasTemplate(KIT, name) then
            table.insert(missing, name)
        end
    end
    local borrowed = {}
    local folder = WorldBuilder.kitFolder(KIT)
    for _, n in H.Remove.Borrowed do
        if folder and folder:FindFirstChild(n) then
            table.insert(borrowed, n)
        end
    end
    return string.format(
        "%d MeshParts (%d that collide or answer queries: must be 0), %d collision parts, %d PointLights (at most %d); folders %s; old copies left in Kit: %d (must be 0), old island pieces left: %s; "
            .. "templates missing: %d; templates kept because Murim Crossing's dress still borrows them: %s",
        meshes, collides, boxes, lights, MAX_LIGHTS, game:GetService("HttpService"):JSONEncode(perFolder), leftPlaced, table.concat(old, ","), #missing, table.concat(borrowed, ", "))
end

return JadeGroveBuilder

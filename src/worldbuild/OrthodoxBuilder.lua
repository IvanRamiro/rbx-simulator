-- Build-time only: run from Studio (Edit mode) to assemble Dawnspire Hall, the Orthodox faction's headquarters, on its pad in Murim Crossing (2026-11-22,
-- phase A: written and linted, NOT yet run: the owner imports the FBX files first). Require a clone so Studio's module cache never serves an old copy:
--
--   local OB = require(game.ServerStorage.WorldBuild.OrthodoxBuilder:Clone())
--   -- once per import (File > Import 3D, Edit mode, one file at a time, into Workspace, nothing renamed): Orthodox_Structure, Orthodox_Roofs,
--   -- Orthodox_Modules, Orthodox_Props. Each import is a Model in Workspace; then
--   OB.storeKit(workspace.Orthodox_Structure)   -- moves its meshes into ServerStorage.WorldKit.MurimCrossing as templates (WorldBuilder.storeKit)
--   OB.build()                                  -- Workspace.FloatingIslands.MurimCrossing.OrthodoxPad.Hall (replaces what it built before)
--   OB.check()                                  -- a report: parts, lights, colliders, what is missing
--
-- What it makes, all from Placements/MurimOrthodox.lua (the model script's numbers, in the pad's frame):
--   Hall/Kit          every MeshPart of the hall (one Model per placement), its material and colour from the placements' Looks (no texture), never colliding
--   Hall/Colliders    invisible Plastic boxes: the floors, steps, walls, columns, rails, the rock mounds (one material: one batch)
--   Hall/Spots        markers: VaultSpot (tag FactionVaultSpot), MasterSpot (tag FactionMasterSpot), the court's centre, the door, the inner court
--   Hall/Falls        four waterfalls (WorldBuilder.buildWaterfall), Hall/Trees the Blossom Sanctuary's trees (WorldKit.BlossomSanctuary, reused)
--   Hall/Lights       the lanterns marked Light carry a PointLight each (four in the whole hall)
-- It also removes what the first foundation built on this stair's top that the hall replaces (Stairs.Gate_Orthodox, Stairs.Flags_Orthodox) and the first
-- foundation's blossom trees standing inside the hall's footprint (it places the rest again, as CrossingBuilder.buildDress does). It never touches the other
-- two factions' parts.
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local P = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimCrossing"):Clone())
local H = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimOrthodox"):Clone())

local OrthodoxBuilder = {}

local ISLAND = "MurimCrossing"
local BLOSSOM = { "BS_TreeElder", "BS_TreeWeeping", "BS_TreeLeaning", "BS_TreeTwin", "BS_TreeYoung", "BS_TreeGnarled" }

local function folder(parent, name)
    local f = Instance.new("Folder")
    f.Name = name
    f.Parent = parent
    return f
end

-- The pad's frame in the world: its centre lifted by FloorLift, turned by the pad's FrontYaw (a model's front, -Z, faces the plaza).
local function padFrame()
    local pad = P.Pads[H.Pad]
    return WorldBuilder.islandFrame(ISLAND) * CFrame.new(pad.Centre + Vector3.new(0, H.FloorLift, 0)) * CFrame.Angles(0, pad.FrontYaw, 0)
end

-- Moves an import's meshes into ServerStorage.WorldKit.MurimCrossing (templates, each relative to the import's anchor cube OH_Anchor).
function OrthodoxBuilder.storeKit(model)
    return WorldBuilder.storeKit(ISLAND, model, "OH_Anchor")
end

local function applyLook(part, suffix)
    local look = H.Looks[suffix]
    if not look then
        return
    end
    part.Material = Enum.Material[look.Material]
    part.Color = Color3.fromRGB(look.Color[1], look.Color[2], look.Color[3])
    part.Transparency = look.Transparency or 0
    part.CastShadow = look.CastShadow ~= false
    part.Reflectance = 0
end

-- One placement of a kit piece: a Model holding its material parts, none of them colliding.
local function placePiece(parent, name, index, entry, frame)
    local holder = Instance.new("Model")
    holder.Name = string.format("%s_%d", name, index)
    holder.Parent = parent
    local at = frame * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
    WorldBuilder.placeTemplate(ISLAND, name, at, holder, entry.Scale)
    for _, part in holder:GetChildren() do
        if part:IsA("MeshPart") then
            local _, suffix = WorldBuilder.splitName(part.Name)
            if suffix then
                applyLook(part, suffix)
            end
            part.Anchored = true
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
            part.Massless = true
            part.CollisionFidelity = Enum.CollisionFidelity.Box
        end
    end
    return holder
end

local function buildKit(hall, frame)
    local kit = folder(hall, "Kit")
    local placed, missing, lights = 0, {}, 0
    local names = {}
    for name in H.Kit do
        table.insert(names, name)
    end
    table.sort(names)
    for _, name in names do
        if not WorldBuilder.hasTemplate(ISLAND, name) then
            table.insert(missing, name)
            continue
        end
        for index, entry in H.Kit[name] do
            local holder = placePiece(kit, name, index, entry, frame)
            placed += 1
            if entry.Light then
                local glow = holder:FindFirstChild(name .. "__AzureGlow")
                if glow then
                    WorldBuilder.addLight(glow, Color3.fromRGB(H.Lights.Color[1], H.Lights.Color[2], H.Lights.Color[3]), H.Lights.Range, H.Lights.Brightness)
                    lights += 1
                end
            end
        end
    end
    return placed, missing, lights
end

local function buildColliders(hall, frame)
    local boxes = folder(hall, "Colliders")
    for _, c in H.Colliders do
        local p = Instance.new("Part")
        p.Name = c.Name
        p.Anchored = true
        p.Size = c.Size
        p.CFrame = frame * CFrame.new(c.Position)
        p.Material = Enum.Material.Plastic
        p.Transparency = 1
        p.CanCollide = true
        p.CanQuery = true
        p.CanTouch = false
        p.CastShadow = false
        p.TopSurface = Enum.SurfaceType.Smooth
        p.BottomSurface = Enum.SurfaceType.Smooth
        p.Parent = boxes
    end
    return #H.Colliders
end

local function buildSpots(hall, frame)
    local spots = folder(hall, "Spots")
    for name, s in H.Spots do
        local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), frame * CFrame.new(s.Position) * CFrame.Angles(0, s.Yaw, 0), spots)
        m.Material = Enum.Material.Plastic
        m:SetAttribute("Faction", H.Pad)
        m:SetAttribute("Role", name)
        if name == "VaultSpot" then
            CollectionService:AddTag(m, "FactionVaultSpot")
        elseif name == "MasterSpot" then
            CollectionService:AddTag(m, "FactionMasterSpot")
        end
    end
end

local function buildFalls(hall, frame)
    local falls = folder(hall, "Falls")
    for _, f in H.Falls do
        WorldBuilder.buildWaterfall(falls, frame:PointToWorldSpace(f.Lip), frame:PointToWorldSpace(f.From), WorldBuilder.Falls.Water)
    end
    return #H.Falls
end

local function buildTrees(hall, frame)
    local trees = folder(hall, "Trees")
    local placed = 0
    for _, t in H.Trees do
        local name = BLOSSOM[(placed % #BLOSSOM) + 1]
        if WorldBuilder.hasTemplate("BlossomSanctuary", name) then
            WorldBuilder.placeTemplate("BlossomSanctuary", name, frame * CFrame.new(t.Position) * CFrame.Angles(0, t.Yaw, 0), trees, t.Scale)
            placed += 1
        end
    end
    return placed
end

-- A name plaque over the hall's front, in Latin letters.
local function buildSign(hall, frame)
    local post = WorldBuilder.marker("Sign", Vector3.new(1, 1, 1), frame * CFrame.new(0, 24.5, -19.2), hall)
    post.Material = Enum.Material.Plastic
    local gui = Instance.new("BillboardGui")
    gui.Name = "Sign"
    gui.Size = UDim2.fromOffset(300, 54)
    gui.MaxDistance = 260
    gui.LightInfluence = 0
    gui.Parent = post
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.FontFace = Font.new("rbxasset://fonts/families/Merriweather.json", Enum.FontWeight.Bold)
    label.TextSize = 30
    label.TextColor3 = Color3.fromRGB(244, 246, 250)
    label.TextStrokeTransparency = 0.4
    label.Text = "DAWNSPIRE HALL"
    label.Parent = gui
end

-- What the first foundation built here and this hall replaces: the old gate and flags on the stair's top, and the blossom trees inside the footprint
-- (the others are placed again exactly as CrossingBuilder.buildDress placed them: the same list, names and scale rule).
local function removeSuperseded(root, frame)
    local stairs = root:FindFirstChild("Stairs")
    local removed = 0
    if stairs then
        for _, name in H.Remove.Stairs do
            local old = stairs:FindFirstChild(name, true) -- (the gate stands in Stairs_Orthodox, one folder down)
            if old then
                old:Destroy()
                removed += 1
            end
        end
    end
    local dress = root:FindFirstChild("Dress")
    local blossom = dress and dress:FindFirstChild("Blossom")
    local trees = 0
    if blossom and WorldBuilder.hasTemplate("BlossomSanctuary", BLOSSOM[1]) then
        blossom:ClearAllChildren()
        local island = WorldBuilder.islandFrame(ISLAND)
        for index, entry in P.Dress.TreesO do
            local local_ = frame:PointToObjectSpace(island:PointToWorldSpace(entry[1]))
            if math.abs(local_.X) < H.Footprint.XHalf and local_.Z > H.Footprint.ZFrom and local_.Z < H.Footprint.ZTo then
                continue
            end
            local name = BLOSSOM[(index - 1) % #BLOSSOM + 1]
            local scale = 1.1 + (1.5 - 1.1) * (((index * 37) % 10) / 9)
            WorldBuilder.placeTemplate("BlossomSanctuary", name, island * CFrame.new(entry[1] - Vector3.new(0, 0.4, 0)) * CFrame.Angles(0, entry[2], 0), blossom, scale)
            trees += 1
        end
    end
    return removed, trees
end

-- Terrain Grass grows blades over a stud tall through any floor laid on it (measured 2026-11-16): under the hall's footprint every Grass voxel becomes
-- Pavement (level, bladeless), its occupancy untouched (each column is read and written back alone, so a neighbour is never rewritten and a second
-- run changes nothing). Returns how many voxels changed.
function OrthodoxBuilder.paveGround(frame)
    frame = frame or padFrame()
    local terrain = workspace.Terrain
    -- the hall's footprint, and the top of the stair that climbs to it (a strip along the pad's front, 22 studs either side of its axis)
    local rects = { { H.Footprint.XHalf, H.Footprint.ZFrom, H.Footprint.ZTo }, { 22, -112, H.Footprint.ZFrom } }
    local y0 = math.floor((frame.Position.Y - 16) / 4) * 4
    local layers = 8 -- 32 studs of ground and what lies just under it
    local changed = 0
    for _, rect in rects do
        local half, zFrom, zTo = rect[1], rect[2], rect[3]
        local minX, maxX, minZ, maxZ = math.huge, -math.huge, math.huge, -math.huge
        for _, c in { Vector3.new(-half, 0, zFrom), Vector3.new(half, 0, zFrom), Vector3.new(-half, 0, zTo), Vector3.new(half, 0, zTo) } do
            local w = frame:PointToWorldSpace(c)
            minX, maxX, minZ, maxZ = math.min(minX, w.X), math.max(maxX, w.X), math.min(minZ, w.Z), math.max(maxZ, w.Z)
        end
        for gx = math.floor(minX / 4) * 4, math.ceil(maxX / 4) * 4 - 4, 4 do
            for gz = math.floor(minZ / 4) * 4, math.ceil(maxZ / 4) * 4 - 4, 4 do
                local lp = frame:PointToObjectSpace(Vector3.new(gx + 2, frame.Position.Y, gz + 2))
                if math.abs(lp.X) <= half and lp.Z >= zFrom and lp.Z <= zTo then
                    local region = Region3.new(Vector3.new(gx, y0, gz), Vector3.new(gx + 4, y0 + layers * 4, gz + 4))
                    local mats, occ = terrain:ReadVoxels(region, 4)
                    local dirty = false
                    for k = 1, layers do
                        if mats[1][k][1] == Enum.Material.Grass and occ[1][k][1] > 0 then
                            mats[1][k][1] = Enum.Material.Pavement
                            dirty = true
                            changed += 1
                        end
                    end
                    if dirty then
                        terrain:WriteVoxels(region, 4, mats, occ)
                    end
                end
            end
        end
    end
    return changed
end

function OrthodoxBuilder.build()
    if not WorldBuilder.hasTemplate(ISLAND, "Orthodox_HallBody") then
        return { Skipped = "the hall's kit is not stored yet (import the four FBX files and run storeKit on each): nothing built, the first foundation is untouched" }
    end
    local root = WorldBuilder.islandFolder(ISLAND)
    local pad = root:FindFirstChild(H.Pad .. "Pad") or folder(root, H.Pad .. "Pad")
    local old = pad:FindFirstChild("Hall")
    if old then
        old:Destroy()
    end
    local frame = padFrame()
    local removed, replanted = removeSuperseded(root, frame)
    local paved = OrthodoxBuilder.paveGround(frame)
    local hall = folder(pad, "Hall")
    local placed, missing, lights = buildKit(hall, frame)
    local boxes = buildColliders(hall, frame)
    buildSpots(hall, frame)
    local falls = buildFalls(hall, frame)
    local trees = buildTrees(hall, frame)
    buildSign(hall, frame)
    if #missing > 0 then
        warn("OrthodoxBuilder: not in the kit yet (import and store these FBX files first), left out: " .. table.concat(missing, ", "))
    end
    return { Placed = placed, Missing = missing, Lights = lights, Colliders = boxes, Falls = falls, Trees = trees, FirstFoundationParts = removed, TreesReplaced = replanted, GrassPaved = paved }
end

function OrthodoxBuilder.check()
    local root = WorldBuilder.islandFolder(ISLAND)
    local pad = root:FindFirstChild(H.Pad .. "Pad")
    local hall = pad and pad:FindFirstChild("Hall")
    if not hall then
        return "no Hall under " .. H.Pad .. "Pad: run build() first"
    end
    local meshes, lights, colliders, collides = 0, 0, 0, 0
    local trees = hall:FindFirstChild("Trees")
    for _, d in hall:GetDescendants() do
        if d:IsA("MeshPart") and not (trees and d:IsDescendantOf(trees)) then
            meshes += 1
            if d.CanCollide or d.CanQuery or d.CanTouch then
                collides += 1
            end
        elseif d:IsA("PointLight") then
            lights += 1
        end
    end
    local boxes = hall:FindFirstChild("Colliders")
    colliders = boxes and #boxes:GetChildren() or 0
    return string.format("%d MeshParts apart from the trees (%d that collide or answer queries: must be 0), %d PointLights (at most 4 in the hall), %d collision boxes", meshes, collides, lights, colliders)
end

return OrthodoxBuilder

-- Build-time only: run from Studio (Edit mode) to assemble Dawnspire's territory, the Orthodox side's extension of Murim Crossing (2026-11-22, phase A: written,
-- linted and compiled, NOT yet run: the owner imports the FBX files first). The hall itself is OrthodoxBuilder's; this builds the terraces' buildings, courts,
-- bridges, stairs, props and the faction's OWN cherry trees, plants and rocks on the ground murim_layout.py now writes (WorldBuilder.buildTerrain("MurimCrossing")).
-- Require a clone so Studio's module cache never serves an old copy:
--
--   local DB = require(game.ServerStorage.WorldBuild.DawnspireBuilder:Clone())
--   -- once per import (File > Import 3D, Edit mode, one file at a time, into Workspace, nothing renamed): Dawnspire_Buildings, Dawnspire_Courts, Dawnspire_Props,
--   -- Dawnspire_Trees, Dawnspire_Plants, Dawnspire_Rocks. Each import is a Model in Workspace; then
--   DB.storeKit(workspace.Dawnspire_Buildings)   -- moves its meshes into ServerStorage.WorldAssets.MurimAssets.DawnspireAssets as templates (WorldBuilder.storeKit)
--   DB.build()                                   -- Workspace.FloatingIslands.MurimCrossing.OrthodoxPad.Territory (replaces what it built before)
--   DB.check()                                   -- a report: parts, lights, colliders, zones, what is missing
--
-- What it makes, all from Placements/MurimDawnspire.lua (dawnspire.py's numbers, in the pad's frame):
--   Territory/Buildings   the Master's house and wings, the training yard's gate and tower, the tea pavilion and corridors, the exhibition hall, the garden's
--                         round pavilion, the walls with their moon gate and round windows, the carved screens, the stage, the pond
--   Territory/Paths       the floors, the stairs, the two arched bridges and their landings, the causeway, the rails, the stepping stones and ground cover
--   Territory/Props       lanterns, incense burners, benches, tea tables, weapon racks, training posts, plum-blossom posts, stone weights, the display bays and the
--                         Regent's plinth with its glass-like case
--   Territory/Vegetation  Dawnspire's own cherry trees (Dawnspire_Trees), clipped hedges, peony beds, lotus basins, iris, dwarf pines
--   Territory/Rocks       the scholar's rocks
--   Territory/Colliders   invisible Plastic boxes (one material, one batch): floors, steps, walls, columns, bridges, trunks, rocks
--   Territory/Spots       markers: MasterSpot, RegentDisplay, ExhibitDoor, the NPC places (Npc*), the garden and the yard; tags are set (see buildSpots)
--   Territory/Falls       three waterfalls (WorldBuilder.buildWaterfall); Territory/Lights six PointLights and four warm fills (2026-11-23); the Regent's static clone when ServerStorage.Weapons has it
--   Approach/Zones        Route and Check zones over every new terrace, stair and bridge, so nobody who falls from them is lost (WorldService reads them at start)
-- It also deletes what the first foundation borrowed on the Orthodox side (Dress.Blossom, the two Orthodox waterfalls, OrthodoxPad.Hall.Trees): replace means delete.
-- Every instance it makes is nested under Territory except the zones; build() can be run again (it removes Territory first).
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local P = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimCrossing"):Clone())
local H = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimDawnspire"):Clone())

local DawnspireBuilder = {}

local ISLAND = "MurimCrossing"
local KIT = "Dawnspire" -- its templates: ServerStorage.WorldAssets.MurimAssets.DawnspireAssets (WorldBuilder.kitFolder)
local ROUTE_DEPTH = 100 -- as CrossingBuilder: a route zone reaches this far under its ground, so a falling player never counts as having left the route

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

-- Moves an import's meshes into ServerStorage.WorldAssets.MurimAssets.DawnspireAssets (templates, each relative to the import's anchor cube DS_Anchor).
function DawnspireBuilder.storeKit(model)
    return WorldBuilder.storeKit(KIT, model, "DS_Anchor")
end

local function applyLook(part, looks, suffix)
    local look = looks[suffix]
    if not look then
        return
    end
    part.Material = Enum.Material[look.Material]
    part.Color = Color3.fromRGB(look.Color[1], look.Color[2], look.Color[3])
    part.Transparency = look.Transparency or 0
    part.CastShadow = look.CastShadow ~= false
    part.Reflectance = 0
end

local function looksFor(pieceName)
    return if string.find(pieceName, "^Dawnspire_Trees") or string.find(pieceName, "^Dawnspire_Plants") or string.find(pieceName, "^Dawnspire_Rocks") then H.Looks.Veg else H.Looks.Arch
end

-- One placement of a kit piece: a Model holding its material parts, none of them colliding.
local function placePiece(parent, name, index, entry, frame)
    local holder = Instance.new("Model")
    holder.Name = string.format("%s_%d", string.gsub(name, "^Dawnspire_", ""), index)
    holder.Parent = parent
    local at = frame * CFrame.new(entry.Position) * CFrame.Angles(0, entry.Yaw, 0)
    WorldBuilder.placeTemplate(KIT, name, at, holder, entry.Scale)
    local looks = looksFor(name)
    for _, part in holder:GetChildren() do
        if part:IsA("MeshPart") then
            local _, suffix = WorldBuilder.splitName(part.Name)
            if suffix then
                applyLook(part, looks, suffix)
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

local function buildKit(territory, frame)
    local folders = {}
    for _, name in H.Folders do
        folders[name] = folder(territory, name)
    end
    local placed, missing = 0, {}
    local names = {}
    for name in H.Kit do
        table.insert(names, name)
    end
    table.sort(names)
    for _, name in names do
        if not WorldBuilder.hasTemplate(KIT, name) then
            table.insert(missing, name)
            continue
        end
        for index, entry in H.Kit[name] do
            placePiece(folders[entry.Folder], name, index, entry, frame)
            placed += 1
        end
    end
    for index, v in H.Vegetation do
        if not WorldBuilder.hasTemplate(KIT, v.Piece) then
            if not table.find(missing, v.Piece) then
                table.insert(missing, v.Piece)
            end
            continue
        end
        placePiece(folders[v.Folder], v.Piece, index, { Position = v.Position, Yaw = v.Yaw, Scale = v.Scale }, frame)
        placed += 1
    end
    return placed, missing
end

local function buildColliders(territory, frame)
    local boxes = folder(territory, "Colliders")
    for _, c in H.Colliders do
        local p = Instance.new("Part")
        p.Name = c.Name
        p.Anchored = true
        p.Size = c.Size
        p.CFrame = frame * CFrame.new(c.Position) * CFrame.Angles(0, c.Yaw or 0, 0)
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

-- Markers (invisible, nothing touches them). Tags the faction and NPC code can find: DawnspireNpcSpot on every Npc* place, DawnspireRegentSpot on RegentDisplay,
-- DawnspireMasterHome on MasterSpot (not FactionMasterSpot: that one is the hall's dais).
local function buildSpots(territory, frame)
    local spots = folder(territory, "Spots")
    for name, s in H.Spots do
        local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), frame * CFrame.new(s.Position) * CFrame.Angles(0, s.Yaw, 0), spots)
        m.Material = Enum.Material.Plastic
        m:SetAttribute("Faction", H.Pad)
        m:SetAttribute("Role", name)
        if string.find(name, "^Npc") then
            CollectionService:AddTag(m, "DawnspireNpcSpot")
        elseif name == "RegentDisplay" then
            CollectionService:AddTag(m, "DawnspireRegentSpot")
        elseif name == "MasterSpot" then
            CollectionService:AddTag(m, "DawnspireMasterHome")
        end
    end
end

-- Warm fill for the rooms the sky does not reach (the 2026-11-23 polish: the exhibition hall, the Master's house and the tea pavilion read cold and over-blue under the
-- bluish ambient light). Each sits above a marker of the placements (H.Spots, in the pad's frame): a place, an offset, and `Between` (the middle of two markers).
local FILL = { Color = Color3.fromRGB(255, 214, 160), Range = 15, Brightness = 0.8 }
local FILL_LIGHTS = {
    { Name = "FillExhibitBack", Spot = "RegentDisplay", Offset = Vector3.new(0, 5, 0) },
    { Name = "FillExhibitMid", Between = { "ExhibitDoor", "RegentDisplay" }, Offset = Vector3.new(0, 5.5, 0) },
    { Name = "FillHouse", Spot = "MasterSpot", Offset = Vector3.new(0, 5, 0) },
    { Name = "FillTea", Spot = "TeaTable1", Offset = Vector3.new(0, 5, 0) },
}

local function buildLights(territory, frame)
    local lights = folder(territory, "Lights")
    for index, l in H.Lights do
        local m = WorldBuilder.marker("Light" .. index, Vector3.new(0.4, 0.4, 0.4), frame * CFrame.new(l.Position), lights)
        m.Material = Enum.Material.Plastic
        WorldBuilder.addLight(m, Color3.fromRGB(l.Color[1], l.Color[2], l.Color[3]), l.Range, l.Brightness)
    end
    for _, l in FILL_LIGHTS do
        local at = if l.Between then (H.Spots[l.Between[1]].Position + H.Spots[l.Between[2]].Position) / 2 else H.Spots[l.Spot].Position
        local m = WorldBuilder.marker(l.Name, Vector3.new(0.4, 0.4, 0.4), frame * CFrame.new(at + l.Offset), lights)
        m.Material = Enum.Material.Plastic
        WorldBuilder.addLight(m, FILL.Color, FILL.Range, FILL.Brightness)
    end
    return #H.Lights + #FILL_LIGHTS
end

local function buildFalls(territory, frame)
    local falls = folder(territory, "Falls")
    for _, f in H.Falls do
        WorldBuilder.buildWaterfall(falls, frame:PointToWorldSpace(f.Lip), frame:PointToWorldSpace(f.From), WorldBuilder.Falls.Water)
    end
    return #H.Falls
end

-- The exclusive weapon on its plinth: a static clone of ServerStorage.Weapons.SecretOrthodox lying along the marker's x axis (its point toward +x, its flat up),
-- centred on RegentDisplay. Skipped (returns false) when the weapon is not stored. Anchored, non-colliding, no scripts or effects: just the model and its maps.
local function buildRegent(territory, frame)
    local weapons = ServerStorage:FindFirstChild("Weapons")
    local source = weapons and weapons:FindFirstChild("SecretOrthodox")
    if not source then
        return false
    end
    local copy = source:Clone()
    local model = Instance.new("Model")
    model.Name = "RegentDisplay"
    for _, d in copy:GetDescendants() do
        if d:IsA("LuaSourceContainer") or d:IsA("ParticleEmitter") or d:IsA("Trail") or d:IsA("Beam") or d:IsA("Light") or d:IsA("Highlight") then
            d:Destroy()
        end
    end
    if copy:IsA("Model") then
        copy.Parent = model
    else -- a Tool: its parts become the model's
        for _, child in copy:GetChildren() do
            child.Parent = model
        end
        copy:Destroy()
    end
    for _, d in model:GetDescendants() do
        if d:IsA("BasePart") then
            d.Anchored = true
            d.CanCollide = false
            d.CanQuery = false
            d.CanTouch = false
            d.Massless = true
        end
    end
    local spot = H.Spots.RegentDisplay
    local target = frame * CFrame.new(spot.Position) * CFrame.Angles(0, -math.pi / 2, 0)
    model.Parent = territory
    local handle = model:FindFirstChild("Handle", true)
    if handle and not model.PrimaryPart then
        model.PrimaryPart = handle
    end
    model:PivotTo(target)
    local box = model:GetBoundingBox()
    model:PivotTo(model:GetPivot() + (target.Position - box.Position)) -- centre it on the marker
    return true
end

-- What the first foundation made on the Orthodox side and this territory replaces.
local function removeSuperseded(root, frame)
    local removed = 0
    local dress = root:FindFirstChild("Dress")
    for _, name in H.Remove.Dress do
        local old = dress and dress:FindFirstChild(name)
        if old then
            old:Destroy()
            removed += 1
        end
    end
    local pad = root:FindFirstChild(H.Pad .. "Pad")
    local hall = pad and pad:FindFirstChild("Hall")
    for _, name in H.Remove.Hall do
        local old = hall and hall:FindFirstChild(name)
        if old then
            old:Destroy()
            removed += 1
        end
    end
    local falls = dress and dress:FindFirstChild("Waterfalls")
    for _, holder in falls and falls:GetChildren() or {} do -- the falls on the Orthodox mesas, by where they are (the pad frame's box over the territory)
        local lp = frame:PointToObjectSpace(holder.Position)
        if lp.X > -60 and lp.X < 140 and lp.Z > -80 and lp.Z < 200 then
            holder:Destroy()
            removed += 1
        end
    end
    return removed
end

-- Route and Check zones, as CrossingBuilder.buildApproach makes them (WorldService reads Approach.Zones once when the server starts).
local function buildZones(root, frame)
    local approach = root:FindFirstChild("Approach") or folder(root, "Approach")
    local zones = approach:FindFirstChild("Zones") or folder(approach, "Zones")
    for _, old in zones:GetChildren() do
        if old:GetAttribute("Dawnspire") then
            old:Destroy()
        end
    end
    local function zone(name, size, cframe, returnTo)
        local z = WorldBuilder.marker(name, size, cframe, zones)
        z.Material = Enum.Material.Plastic
        z.CanQuery = true -- WorldService finds it with an overlap query
        z:SetAttribute("Dawnspire", true)
        if returnTo then
            z:SetAttribute("ReturnTo", returnTo)
        end
        return z
    end
    for _, r in H.Zones.Routes do
        local height = 8 + ROUTE_DEPTH + r.High
        zone("Route", Vector3.new(r.Size.X, height, r.Size.Y), frame * CFrame.new(r.Centre + Vector3.new(0, -ROUTE_DEPTH + height / 2, 0)))
    end
    for _, c in H.Zones.Checks do
        local z = zone("Check", Vector3.new(c.Size.X, 10, c.Size.Y), frame * CFrame.new(c.Centre + Vector3.new(0, 4, 0)), frame * CFrame.new(c.ReturnTo))
        z:SetAttribute("Name", "Dawnspire " .. c.Name)
    end
    return #H.Zones.Routes + #H.Zones.Checks
end

function DawnspireBuilder.build()
    local missingBase = not WorldBuilder.hasTemplate(KIT, "Dawnspire_Buildings_House")
    if missingBase then
        return { Skipped = "the territory's kit is not stored yet (import the six FBX files and run storeKit on each): nothing built, the first foundation is untouched" }
    end
    local root = WorldBuilder.islandFolder(ISLAND)
    local pad = root:FindFirstChild(H.Pad .. "Pad") or folder(root, H.Pad .. "Pad")
    local old = pad:FindFirstChild("Territory")
    if old then
        old:Destroy()
    end
    local frame = padFrame()
    local removed = removeSuperseded(root, frame)
    local territory = folder(pad, "Territory")
    -- where the territory is and how far its air reaches (DawnspireLife.client reads these: petals drift only inside it)
    local sum = Vector3.zero
    local count = 0
    for _, spot in H.Spots do
        sum += frame:PointToWorldSpace(spot.Position)
        count += 1
    end
    territory:SetAttribute("Centre", sum / math.max(1, count))
    territory:SetAttribute("Radius", 150)
    local placed, missing = buildKit(territory, frame)
    local boxes = buildColliders(territory, frame)
    buildSpots(territory, frame)
    local lights = buildLights(territory, frame)
    local falls = buildFalls(territory, frame)
    local regent = buildRegent(territory, frame)
    local zones = buildZones(root, frame)
    if #missing > 0 then
        warn("DawnspireBuilder: not in the kit yet (import and store these FBX files first), left out: " .. table.concat(missing, ", "))
    end
    return { Placed = placed, Missing = missing, Colliders = boxes, Lights = lights, Falls = falls, Regent = regent, Zones = zones, FirstFoundationParts = removed }
end

function DawnspireBuilder.check()
    local root = WorldBuilder.islandFolder(ISLAND)
    local pad = root:FindFirstChild(H.Pad .. "Pad")
    local territory = pad and pad:FindFirstChild("Territory")
    if not territory then
        return "no Territory under " .. H.Pad .. "Pad: run build() first"
    end
    local meshes, lights, collides, foreign = 0, 0, 0, 0
    local owned = {}
    local kitFolder = WorldBuilder.kitFolder(KIT)
    for _, t in kitFolder and kitFolder:GetChildren() or {} do
        if t:IsA("MeshPart") then
            owned[t.MeshId] = true
        end
    end
    for _, d in territory:GetDescendants() do
        if d:IsA("MeshPart") then
            meshes += 1
            if d.CanCollide or d.CanQuery or d.CanTouch then
                collides += 1
            end
            if not owned[d.MeshId] then
                foreign += 1
            end
        elseif d:IsA("PointLight") then
            lights += 1
        end
    end
    local boxes = territory:FindFirstChild("Colliders")
    local zones = 0
    local approach = root:FindFirstChild("Approach")
    for _, z in approach and approach:FindFirstChild("Zones") and approach.Zones:GetChildren() or {} do
        if z:GetAttribute("Dawnspire") then
            zones += 1
        end
    end
    local blossom = root:FindFirstChild("Dress") and root.Dress:FindFirstChild("Blossom")
    local hallTrees = pad:FindFirstChild("Hall") and pad.Hall:FindFirstChild("Trees")
    return string.format("%d MeshParts (%d that collide or answer queries: must be 0; %d whose mesh is not one of Dawnspire's own templates: must be 0), %d PointLights (at most 10: the first 6 and the 4 warm fills), "
        .. "%d collision boxes, %d zones, borrowed Blossom trees left: %d (must be 0)", meshes, collides, foreign, lights, boxes and #boxes:GetChildren() or 0, zones,
        (blossom and #blossom:GetChildren() or 0) + (hallTrees and #hallTrees:GetChildren() or 0))
end

return DawnspireBuilder

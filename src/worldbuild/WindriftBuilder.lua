-- Build-time only: run from Studio (Edit mode) to assemble Windrift Hold, the Unorthodox territory on Murim Crossing's centre pad (2026-11-23, phase A: written, linted and
-- compiled, NOT yet run: the owner imports the FBX files first). The ground is murim_layout.py's (WorldBuilder.buildTerrain("MurimCrossing"): the pad, a gorge cut through it,
-- the Eyrie and Perch ledges, the Drip ledge, the Eyrie's stair); this builds what stands on it: the headquarters, the Elder's house, the weapon gallery, the hall over the
-- waterfall, the training grounds, the gathering place, the bridges, the stairs, the walls, the props and the faction's OWN trees, plants and rocks.
-- Require a clone so Studio's module cache never serves an old copy:
--
--   local WB = require(game.ServerStorage.WorldBuild.WindriftBuilder:Clone())
--   -- once per import (File > Import 3D, Edit mode, one file at a time, into Workspace, nothing renamed): Windrift_Buildings, Windrift_Courts, Windrift_Props,
--   -- Windrift_Trees, Windrift_Plants, Windrift_Rocks. Each import is a Model in Workspace; then
--   WB.storeKit(workspace.Windrift_Buildings)    -- moves its meshes into ServerStorage.WorldAssets.MurimAssets.WindriftAssets as templates (WorldBuilder.storeKit)
--   WB.build()                                   -- Workspace.FloatingIslands.MurimCrossing.UnorthodoxPad.Territory (replaces what it built before)
--   WB.check()                                   -- a report: parts, lights, colliders, zones, what is missing
--
-- What it makes, all from Placements/MurimWindrift.lua (windrift.py's numbers, in the pad's frame):
--   Territory/Buildings   the Long Hold (headquarters), the Eyrie (the Elder's house), the Gallery of Blades, the Rain Hall over the gorge, the Perch pavilion, the Drip
--                         Shrine, the Hearth Yard (the gathering place), the stone ring, the log yard, the wire course, the swing frame, the Moss Court's rubble walls and gate
--   Territory/Paths       the two suspension bridges (the Great Span and the Gorge Bridge), the Eyrie's stair and landing, the Cleft Stair, the rim rails, the path slabs
--   Territory/Props       benches, lantern posts, banner poles, weapon racks, the saber's cradle, a waymarker, three bamboo scaffolds
--   Territory/Vegetation  Windrift's own trees (the Gale Cedar, Banner Pine, Cliff Juniper, Bronzeleaf, Split Snag and the Giant Cedar), grass, shrubs and flowers
--   Territory/Rocks       slate slabs, vein boulders, strata stacks, fins, crags, the wind gate, scree
--   Territory/Colliders   invisible Plastic boxes (one material, one batch): floors, steps, walls, posts, bridge decks, trunks, rocks
--   Territory/Spots       markers: SaberDisplay, ElderSpot, the NPC places (Npc*), the doors, the ledges; tags are set (see buildSpots)
--   Territory/Falls       the Great Falls (WorldBuilder.buildWaterfall with its Drop, Scale and Curtains); Territory/Lights the PointLights (at most 8);
--                         the Crosscurrent Saber's static clone on the cradle when ServerStorage.Weapons has it
--   Approach/Zones        Route and Check zones over every ledge, stair and bridge, so nobody who falls from them is lost (WorldService reads them at start)
-- It also deletes what the first foundation borrowed on the Unorthodox side (Dress.Forest, the old mesa fall): replace means delete.
-- Every instance it makes is nested under Territory except the zones; build() can be run again (it removes Territory first).
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local P = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimCrossing"):Clone())
local H = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimWindrift"):Clone())

local WindriftBuilder = {}

local ISLAND = "MurimCrossing"
local KIT = "Windrift" -- its templates: ServerStorage.WorldAssets.MurimAssets.WindriftAssets (WorldBuilder.kitFolder)
local ROUTE_DEPTH = 100 -- as CrossingBuilder: a route zone reaches this far under its ground, so a falling player never counts as having left the route
local MAX_LIGHTS = 8

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

-- Moves an import's meshes into ServerStorage.WorldAssets.MurimAssets.WindriftAssets (templates, each relative to the import's anchor cube WR_Anchor).
function WindriftBuilder.storeKit(model)
    return WorldBuilder.storeKit(KIT, model, "WR_Anchor")
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
    return if string.find(pieceName, "^Windrift_Trees") or string.find(pieceName, "^Windrift_Plants") or string.find(pieceName, "^Windrift_Rocks") then H.Looks.Veg else H.Looks.Arch
end

-- One placement of a kit piece: a Model holding its material parts, none of them colliding (except a Walkable path slab, a flat box).
local function placePiece(parent, name, index, entry, frame)
    local holder = Instance.new("Model")
    holder.Name = string.format("%s_%d", string.gsub(name, "^Windrift_", ""), index)
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
            part.CanCollide = entry.Walkable == true
            part.CanQuery = entry.Walkable == true
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
        placePiece(folders[v.Folder], v.Piece, index, { Position = v.Position, Yaw = v.Yaw, Scale = v.Scale, Walkable = v.Walkable }, frame)
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

-- Markers (invisible, nothing touches them). Tags the faction and NPC code can find: WindriftNpcSpot on every Npc* place, WindriftSaberSpot on SaberDisplay,
-- WindriftElderHome on ElderSpot.
local function buildSpots(territory, frame)
    local spots = folder(territory, "Spots")
    for name, s in H.Spots do
        local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), frame * CFrame.new(s.Position) * CFrame.Angles(0, s.Yaw, 0), spots)
        m.Material = Enum.Material.Plastic
        m:SetAttribute("Faction", H.Pad)
        m:SetAttribute("Role", name)
        if string.find(name, "^Npc") then
            CollectionService:AddTag(m, "WindriftNpcSpot")
        elseif name == "SaberDisplay" then
            CollectionService:AddTag(m, "WindriftSaberSpot")
        elseif name == "ElderSpot" then
            CollectionService:AddTag(m, "WindriftElderHome")
        end
    end
end

local function buildLights(territory, frame)
    local lights = folder(territory, "Lights")
    for index, l in H.Lights do
        local m = WorldBuilder.marker("Light" .. index, Vector3.new(0.4, 0.4, 0.4), frame * CFrame.new(l.Position), lights)
        m.Material = Enum.Material.Plastic
        WorldBuilder.addLight(m, Color3.fromRGB(l.Color[1], l.Color[2], l.Color[3]), l.Range, l.Brightness)
    end
    return #H.Lights
end

local function buildFalls(territory, frame)
    local falls = folder(territory, "Falls")
    for _, f in H.Falls do
        WorldBuilder.buildWaterfall(falls, frame:PointToWorldSpace(f.Lip), frame:PointToWorldSpace(f.From), WorldBuilder.Falls.Water,
            { Drop = f.Drop, Scale = f.Scale, Curtains = f.Curtains, Splash = f.Splash })
    end
    return #H.Falls
end

-- The exclusive weapon on its cradle: a static clone of ServerStorage.Weapons.SecretUnorthodox lying along the marker's x axis, centred on SaberDisplay. Skipped (returns
-- false) when the weapon is not stored. Anchored, non-colliding, no scripts or effects: just the model and its maps. Check its orientation (blade along x, flat up) in Studio.
local function buildSaber(territory, frame)
    local weapons = ServerStorage:FindFirstChild("Weapons")
    local source = weapons and weapons:FindFirstChild("SecretUnorthodox")
    if not source then
        return false
    end
    local copy = source:Clone()
    local model = Instance.new("Model")
    model.Name = "SaberDisplay"
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
    local spot = H.Spots.SaberDisplay
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

-- What the first foundation made on the Unorthodox side and this territory replaces: the Jade Grove's trees (Dress.Forest) and the old fall off the middle mesa
-- (Dress.Waterfalls: the holder whose place lies in the pad frame's box behind the pad).
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
    local falls = dress and dress:FindFirstChild("Waterfalls")
    if H.Remove.Waterfalls then
        for _, holder in falls and falls:GetChildren() or {} do
            local lp = frame:PointToObjectSpace(holder.Position)
            if lp.X > -40 and lp.X < 40 and lp.Z > 50 and lp.Z < 110 then
                holder:Destroy()
                removed += 1
            end
        end
    end
    return removed
end

-- Route and Check zones, as CrossingBuilder.buildApproach makes them (WorldService reads Approach.Zones once when the server starts).
local function buildZones(root, frame)
    local approach = root:FindFirstChild("Approach") or folder(root, "Approach")
    local zones = approach:FindFirstChild("Zones") or folder(approach, "Zones")
    for _, old in zones:GetChildren() do
        if old:GetAttribute("Windrift") then
            old:Destroy()
        end
    end
    local function zone(name, size, cframe, returnTo)
        local z = WorldBuilder.marker(name, size, cframe, zones)
        z.Material = Enum.Material.Plastic
        z.CanQuery = true -- WorldService finds it with an overlap query
        z:SetAttribute("Windrift", true)
        if returnTo then
            z:SetAttribute("ReturnTo", returnTo)
        end
        return z
    end
    for _, r in H.Zones.Routes do
        local height = 8 + ROUTE_DEPTH + r.High
        zone("Route", Vector3.new(r.Size.X, height, r.Size.Y), frame * CFrame.new(r.Centre + Vector3.new(0, -ROUTE_DEPTH + height / 2, 0)) * CFrame.Angles(0, r.Yaw, 0))
    end
    for _, c in H.Zones.Checks do
        local z = zone("Check", Vector3.new(c.Size.X, 10, c.Size.Y), frame * CFrame.new(c.Centre + Vector3.new(0, 4, 0)), frame * CFrame.new(c.ReturnTo))
        z:SetAttribute("Name", "Windrift " .. c.Name)
    end
    return #H.Zones.Routes + #H.Zones.Checks
end

function WindriftBuilder.build()
    local missingBase = not WorldBuilder.hasTemplate(KIT, "Windrift_Buildings_Hq")
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
    -- where the territory is and how far its air reaches (a later ambient script reads these)
    territory:SetAttribute("Centre", frame.Position)
    territory:SetAttribute("Radius", 100)
    local placed, missing = buildKit(territory, frame)
    local boxes = buildColliders(territory, frame)
    buildSpots(territory, frame)
    local lights = buildLights(territory, frame)
    local falls = buildFalls(territory, frame)
    local saber = buildSaber(territory, frame)
    local zones = buildZones(root, frame)
    if #missing > 0 then
        warn("WindriftBuilder: not in the kit yet (import and store these FBX files first), left out: " .. table.concat(missing, ", "))
    end
    return { Placed = placed, Missing = missing, Colliders = boxes, Lights = lights, Falls = falls, Saber = saber, Zones = zones, FirstFoundationParts = removed }
end

function WindriftBuilder.check()
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
            local walkable = d.CanCollide and d.Parent and d.Parent.Parent and d.Parent.Parent.Name == "Paths"
            if (d.CanCollide or d.CanQuery or d.CanTouch) and not walkable then
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
        if z:GetAttribute("Windrift") then
            zones += 1
        end
    end
    local forest = root:FindFirstChild("Dress") and root.Dress:FindFirstChild("Forest")
    return string.format("%d MeshParts (the budget is 450; %d that collide or answer queries outside the Paths folder's walkable slabs: must be 0; %d whose mesh is not one of Windrift's own templates: must be 0), "
        .. "%d PointLights (at most %d), %d collision boxes, %d zones, borrowed Jade trees left: %d (must be 0)", meshes, collides, foreign, lights, MAX_LIGHTS,
        boxes and #boxes:GetChildren() or 0, zones, forest and #forest:GetChildren() or 0)
end

return WindriftBuilder

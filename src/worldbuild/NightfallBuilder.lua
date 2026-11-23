-- Build-time only: run from Studio (Edit mode) to assemble Nightfall Citadel, the Demonic territory on Murim Crossing's right-hand pad (2026-11-23, phase A: written, linted and
-- compiled, NOT yet run: the owner imports the FBX files first). The ground is murim_layout.py's (WorldBuilder.buildTerrain("MurimCrossing"): the pad, the Upper Ward terrace
-- behind it, the fissure, the bridgehead and the Residence ledge); this builds what stands on it: the curtain wall and gatehouse, the arena, the training grounds, the Ember Court,
-- the Great Stair and the Postern, the Black Keep, the Armory with the Nightfall Talon's plinth, the chain bridge over the fissure and the Lord's tower, the props, the faction's
-- OWN trees, plants and rocks, a few lights and a very small set of effects.
-- Require a clone so Studio's module cache never serves an old copy:
--
--   local NB = require(game.ServerStorage.WorldBuild.NightfallBuilder:Clone())
--   -- once per import (File > Import 3D, Edit mode, one file at a time, into Workspace, nothing renamed): Nightfall_Buildings, Nightfall_Courts, Nightfall_Props,
--   -- Nightfall_Trees, Nightfall_Plants, Nightfall_Rocks. Each import is a Model in Workspace; then
--   NB.storeKit(workspace.Nightfall_Buildings)   -- moves its meshes into ServerStorage.WorldAssets.MurimAssets.NightfallAssets as templates (WorldBuilder.storeKit)
--   NB.build()                                   -- Workspace.FloatingIslands.MurimCrossing.DemonicPad.Territory (replaces what it built before)
--   NB.check()                                   -- a report: parts, lights, emitters, colliders, zones, what is missing
--
-- What it makes, all from Placements/MurimNightfall.lua (nightfall.py's numbers, in the pad's frame):
--   Territory/Buildings   the gatehouse, the bastions, the arena, the chain ring, the rack shed, the Ember Court, the Black Keep, the Armory, the Residence, the Upper Ward's gate
--   Territory/Paths       the Great Stair (two flights and a landing), the Postern, the bridgehead's stair, the chain bridge, the curtain wall, the parapets, the path slabs
--   Territory/Props       braziers, banner poles, the stake row, the Talon's plinth, and the Effects model (the particle emitters)
--   Territory/Vegetation  Nightfall's own trees (Ashthorn, Ironpine, Shardtree, Cinderstump and the Giant Blackthorn), thorns, lilies, ash grass
--   Territory/Rocks       basalt columns, pike rows, obsidian shards, obelisks, ember cones, fangs, crags and scatter
--   Territory/Colliders   invisible Plastic boxes (one material, one batch): floors, steps, walls, pylons, trunks, rocks
--   Territory/Spots       markers: TalonDisplay (tag NightfallTalonSpot), Vault (NightfallVault), LordSpot (NightfallLordHome), Npc1..10 (NightfallNpcSpot), ArenaCentre and
--                         ArenaDummy1..8 (NightfallArenaDummy), TrainingRing, GateCourt, HqDoor, HqInside and the stairs' and bridge's ends
--   Territory/Lights      the PointLights (at most 8); the Nightfall Talon's static clone on its plinth when ServerStorage.Weapons has it
--   Approach/Zones        Route and Check zones over every stair, ledge and bridge, so nobody who falls from them is lost (WorldService reads them at start)
-- It also deletes what the first foundation borrowed on the Demonic side (Dress.Basalt, the Ember Peak's basalt): replace means delete. Build() takes `Effects = false` (a table
-- argument { Effects = false }) to leave the particle emitters out. Every instance it makes is nested under Territory except the zones; build() can be run again.
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local P = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimCrossing"):Clone())
local H = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimNightfall"):Clone())

local NightfallBuilder = {}

local ISLAND = "MurimCrossing"
local KIT = "Nightfall" -- its templates: ServerStorage.WorldAssets.MurimAssets.NightfallAssets (WorldBuilder.kitFolder)
local ROUTE_DEPTH = 100 -- as CrossingBuilder: a route zone reaches this far under its ground, so a falling player never counts as having left the route
local MAX_LIGHTS = 8
local MAX_EMITTERS = 12
local MAX_RATE = 6

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

-- Moves an import's meshes into ServerStorage.WorldAssets.MurimAssets.NightfallAssets (templates, each relative to the import's anchor cube NF_Anchor).
function NightfallBuilder.storeKit(model)
    return WorldBuilder.storeKit(KIT, model, "NF_Anchor")
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
    return if string.find(pieceName, "^Nightfall_Trees") or string.find(pieceName, "^Nightfall_Plants") or string.find(pieceName, "^Nightfall_Rocks") then H.Looks.Veg else H.Looks.Arch
end

-- One placement of a kit piece: a Model holding its material parts, none of them colliding (except a Walkable path slab, a flat box).
local function placePiece(parent, name, index, entry, frame)
    local holder = Instance.new("Model")
    holder.Name = string.format("%s_%d", string.gsub(name, "^Nightfall_", ""), index)
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
    return placed, missing, folders
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

-- Markers (invisible, nothing touches them). Tags the faction, NPC and trial code can find: NightfallNpcSpot on every Npc* place, NightfallTalonSpot on TalonDisplay,
-- NightfallVault on Vault, NightfallLordHome on LordSpot, NightfallArenaDummy on every ArenaDummy* place.
local function buildSpots(territory, frame)
    local spots = folder(territory, "Spots")
    for name, s in H.Spots do
        local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), frame * CFrame.new(s.Position) * CFrame.Angles(0, s.Yaw, 0), spots)
        m.Material = Enum.Material.Plastic
        m:SetAttribute("Faction", H.Pad)
        m:SetAttribute("Role", name)
        if string.find(name, "^Npc") then
            CollectionService:AddTag(m, "NightfallNpcSpot")
        elseif string.find(name, "^ArenaDummy") then
            CollectionService:AddTag(m, "NightfallArenaDummy")
        elseif name == "TalonDisplay" then
            CollectionService:AddTag(m, "NightfallTalonSpot")
        elseif name == "Vault" then
            CollectionService:AddTag(m, "NightfallVault")
        elseif name == "LordSpot" then
            CollectionService:AddTag(m, "NightfallLordHome")
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

-- The small effects set: at most MAX_EMITTERS ParticleEmitters, each Rate at most MAX_RATE, on invisible parts, no scripts, textures the engine itself ships (the ones the world's own
-- fires and motes use). Flame: a brazier's fire; Embers: sparks rising from the keep's spire and from the fissure; Ash: a slow drift of grey flakes over the lower ward.
local function buildEffects(parent, frame)
    local model = Instance.new("Model")
    model.Name = "Effects"
    model.Parent = parent
    local count = 0
    for index, e in H.Effects do
        if count >= MAX_EMITTERS then
            break
        end
        local part = WorldBuilder.marker("Effect" .. index, if e.Kind == "Ash" then Vector3.new(70, 2, 70) else Vector3.new(1, 1, 1), frame * CFrame.new(e.Position), model)
        part.Material = Enum.Material.Plastic
        local emitter = Instance.new("ParticleEmitter")
        emitter.Name = e.Kind
        emitter.Rate = math.min(e.Rate, MAX_RATE)
        emitter.LightInfluence = 0
        emitter.EmissionDirection = Enum.NormalId.Top
        if e.Kind == "Flame" then
            emitter.Texture = "rbxasset://textures/particles/fire_main.dds"
            emitter.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 190, 100)), ColorSequenceKeypoint.new(0.45, Color3.fromRGB(255, 70, 40)),
                ColorSequenceKeypoint.new(1, Color3.fromRGB(110, 10, 20)) })
            emitter.LightEmission = 1
            emitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.3), NumberSequenceKeypoint.new(1, 0.2) })
            emitter.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
            emitter.Lifetime = NumberRange.new(0.7, 1.1)
            emitter.Speed = NumberRange.new(2.5, 4)
            emitter.SpreadAngle = Vector2.new(8, 8)
            emitter.Rotation = NumberRange.new(-20, 20)
        elseif e.Kind == "Embers" then
            emitter.Texture = "rbxasset://textures/particles/sparkles_main.dds"
            emitter.Color = ColorSequence.new(Color3.fromRGB(255, 170, 80), Color3.fromRGB(230, 40, 30))
            emitter.LightEmission = 1
            emitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.25, 0.5), NumberSequenceKeypoint.new(1, 0) })
            emitter.Transparency = NumberSequence.new(0.1, 1)
            emitter.Lifetime = NumberRange.new(3, 5)
            emitter.Speed = NumberRange.new(2, 4)
            emitter.SpreadAngle = Vector2.new(35, 35)
            emitter.Acceleration = Vector3.new(0, 1.2, 0)
            emitter.Drag = 0.5
            emitter.Rotation = NumberRange.new(0, 360)
        else -- Ash
            emitter.Texture = "rbxasset://textures/particles/smoke_main.dds"
            emitter.Color = ColorSequence.new(Color3.fromRGB(120, 116, 120), Color3.fromRGB(70, 66, 70))
            emitter.LightEmission = 0
            emitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1.1) })
            emitter.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.55), NumberSequenceKeypoint.new(1, 1) })
            emitter.Lifetime = NumberRange.new(9, 12)
            emitter.Speed = NumberRange.new(0.4, 1)
            emitter.SpreadAngle = Vector2.new(60, 60)
            emitter.Acceleration = Vector3.new(0.5, -0.3, 0.2)
            emitter.Shape = Enum.ParticleEmitterShape.Box
            emitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
            emitter.Rotation = NumberRange.new(0, 360)
        end
        emitter.Parent = part
        count += 1
    end
    return count
end

-- The exclusive weapon on its plinth: a static clone of ServerStorage.Weapons.SecretDemonic (the Nightfall Talon) lying along the marker's x axis, centred on TalonDisplay. Skipped
-- (returns false) when the weapon is not stored. Anchored, non-colliding, no scripts or effects: just the model and its maps. Check its orientation (blade along x, flat up) in Studio.
local function buildTalon(territory, frame)
    local weapons = ServerStorage:FindFirstChild("Weapons")
    local source = weapons and weapons:FindFirstChild("SecretDemonic")
    if not source then
        return false
    end
    local copy = source:Clone()
    local model = Instance.new("Model")
    model.Name = "TalonDisplay"
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
    local spot = H.Spots.TalonDisplay
    local target = frame * CFrame.new(spot.Position) * CFrame.Angles(0, spot.Yaw - math.pi / 2, 0)
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

-- What the first foundation made on the Demonic side and this territory replaces: the Ember Peak's basalt clusters and shards (Dress.Basalt).
local function removeSuperseded(root)
    local removed = 0
    local dress = root:FindFirstChild("Dress")
    for _, name in H.Remove.Dress do
        local old = dress and dress:FindFirstChild(name)
        if old then
            old:Destroy()
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
        if old:GetAttribute("Nightfall") then
            old:Destroy()
        end
    end
    local function zone(name, size, cframe, returnTo)
        local z = WorldBuilder.marker(name, size, cframe, zones)
        z.Material = Enum.Material.Plastic
        z.CanQuery = true -- WorldService finds it with an overlap query
        z:SetAttribute("Nightfall", true)
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
        z:SetAttribute("Name", "Nightfall " .. c.Name)
    end
    return #H.Zones.Routes + #H.Zones.Checks
end

function NightfallBuilder.build(options)
    local withEffects = not (options and options.Effects == false)
    local missingBase = not WorldBuilder.hasTemplate(KIT, "Nightfall_Buildings_Keep")
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
    local removed = removeSuperseded(root)
    local territory = folder(pad, "Territory")
    -- where the territory is and how far its air reaches (a later ambient script reads these)
    territory:SetAttribute("Centre", frame.Position)
    territory:SetAttribute("Radius", 100)
    local placed, missing, folders = buildKit(territory, frame)
    local boxes = buildColliders(territory, frame)
    buildSpots(territory, frame)
    local lights = buildLights(territory, frame)
    local effects = if withEffects then buildEffects(folders.Props, frame) else 0
    local talon = buildTalon(territory, frame)
    local zones = buildZones(root, frame)
    if #missing > 0 then
        warn("NightfallBuilder: not in the kit yet (import and store these FBX files first), left out: " .. table.concat(missing, ", "))
    end
    return { Placed = placed, Missing = missing, Colliders = boxes, Lights = lights, Emitters = effects, Talon = talon, Zones = zones, FirstFoundationParts = removed }
end

function NightfallBuilder.check()
    local root = WorldBuilder.islandFolder(ISLAND)
    local pad = root:FindFirstChild(H.Pad .. "Pad")
    local territory = pad and pad:FindFirstChild("Territory")
    if not territory then
        return "no Territory under " .. H.Pad .. "Pad: run build() first"
    end
    local meshes, lights, collides, foreign, emitters, fastest = 0, 0, 0, 0, 0, 0
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
        elseif d:IsA("ParticleEmitter") then
            emitters += 1
            fastest = math.max(fastest, d.Rate)
        end
    end
    local boxes = territory:FindFirstChild("Colliders")
    local zones = 0
    local approach = root:FindFirstChild("Approach")
    for _, z in approach and approach:FindFirstChild("Zones") and approach.Zones:GetChildren() or {} do
        if z:GetAttribute("Nightfall") then
            zones += 1
        end
    end
    local basalt = root:FindFirstChild("Dress") and root.Dress:FindFirstChild("Basalt")
    return string.format("%d MeshParts (the budget is 450; %d that collide or answer queries outside the Paths folder's walkable slabs: must be 0; %d whose mesh is not one of Nightfall's own templates: must be 0), "
        .. "%d PointLights (at most %d), %d ParticleEmitters (at most %d, the fastest Rate %d, at most %d), %d collision boxes, %d zones, borrowed Ember Peak basalt left: %d (must be 0)", meshes, collides, foreign,
        lights, MAX_LIGHTS, emitters, MAX_EMITTERS, fastest, MAX_RATE, boxes and #boxes:GetChildren() or 0, zones, basalt and #basalt:GetChildren() or 0)
end

return NightfallBuilder

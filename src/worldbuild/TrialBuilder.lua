-- Build-time only: run from Studio (Edit mode) to put the three faction trials' places in the world (2026-11-23). The rules are shared/TrialRules and the clocks are
-- server/Factions/TrialService; this builds what they read. It stands on the markers the earlier builds already made, so it needs no placements file:
--   Orthodox (Dawnspire)    a Trial Stone at the stair's foot, five gates up the Orthodox stairway (the foundation's OrthodoxPad TrialGate1..5, in order), each a gate mesh with two
--                           invisible collision boxes for its pillars and a tall invisible zone (tag TrialGateZone, Index) the server tests the player against; the vault's prompt in the hall
--   Unorthodox (Windrift)   a Trial Stone by the Hold's gate, six tokens hidden at the foundation's UnorthodoxPad TrialToken1..6 (models tagged TrialToken, Index, a prompt), the vault's
--                           prompt at the Gallery's cradle (Spots.SaberDisplay)
--   Demonic (Nightfall)     a Trial Stone outside the arena's front gate, the dummy the arena stands on its eight places (ServerStorage.TrialDummy, a model the server clones), the vault's
--                           prompt at the Armory's vault door (Spots.Vault)
-- Everything is under Workspace.FloatingIslands.MurimCrossing.Trials (CrossingBuilder.build() calls this last, because it clears the island first); build() replaces what it made.
-- The meshes come from the Trial kit (assets/world/MurimCrossing/Trial/Trial_Props.fbx: TrialGate, TrialToken, TrialDummy; ServerStorage.WorldAssets.MurimAssets.TrialAssets);
-- where a piece is not stored yet a plain stand-in of parts is built so the trials still run (it is named "StandIn" in the report). Require a clone so Studio's module cache never
-- serves an old copy:
--
--   local TB = require(game.ServerStorage.WorldBuild.TrialBuilder:Clone())
--   TB.storeKit(workspace.Trial_Props)    -- once per import (File > Import 3D, Edit mode, into Workspace, nothing renamed)
--   TB.build()
--   TB.check()
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())

local TrialBuilder = {}

local ISLAND = "MurimCrossing"
local KIT = "Trial"
local SPOT_LIFT = 0.4 -- a marked place stands this far over its floor

-- the tags and attributes the server and the client read (shared/FactionRules)
local TAGS = { Post = "FactionTrialPost", Gate = "TrialGateZone", Token = "TrialToken", Vault = "FactionVault" }

-- the gate mesh (Trial_Props_TrialGate, measured: pieces.json): its size in studs, the opening a body passes through (16.5 clear from the ground to 12), the shafts of its two pillars (13.1 high,
-- solid), and the zone the server tests the player against: the gate's own width, so a body must go through the gate and not round it, tall enough for a flyer
local GATE = { Width = 24.6, Height = 17.4, Depth = 3.4, Opening = 16.5, PillarHeight = 13.1, ZoneSize = Vector3.new(24.6, 46, 12) }

-- the looks of the Trial kit's pieces by material suffix (assets/world/MurimCrossing/Trial/pieces.json "looks"): the gate's are Dawnspire's, the dummy's Nightfall's, the token's Windrift's
local LOOKS = {
    Trial_Props_TrialGate = {
        Marble = { Material = "Marble", Color = { 238, 236, 232 } },
        Gold = { Material = "Metal", Color = { 255, 172, 48 } },
        Azure = { Material = "SmoothPlastic", Color = { 38, 104, 204 } },
    },
    Trial_Props_TrialToken = {
        Stone = { Material = "Slate", Color = { 62, 82, 74 } },
        Timber = { Material = "Wood", Color = { 88, 66, 46 } },
        Copper = { Material = "Metal", Color = { 196, 108, 58 } },
        Glow = { Material = "Neon", Color = { 60, 212, 178 }, CastShadow = false },
    },
    Trial_Props_TrialDummy = {
        Iron = { Material = "Metal", Color = { 78, 76, 92 } },
        Crimson = { Material = "Fabric", Color = { 158, 24, 36 }, CastShadow = false },
        Timber = { Material = "Wood", Color = { 52, 40, 36 } },
    },
}

local FACTION = { -- colours of each faction's stone (the stand-ins use them too)
    Orthodox = { Stele = Color3.fromRGB(236, 238, 244), Base = Color3.fromRGB(120, 124, 134), Band = Color3.fromRGB(96, 168, 255), SteleMaterial = Enum.Material.Marble, BaseMaterial = Enum.Material.Granite },
    Unorthodox = { Stele = Color3.fromRGB(122, 94, 64), Base = Color3.fromRGB(150, 98, 54), Band = Color3.fromRGB(70, 200, 150), SteleMaterial = Enum.Material.Wood, BaseMaterial = Enum.Material.Metal },
    Demonic = { Stele = Color3.fromRGB(26, 24, 30), Base = Color3.fromRGB(44, 42, 50), Band = Color3.fromRGB(226, 52, 48), SteleMaterial = Enum.Material.Basalt, BaseMaterial = Enum.Material.Metal },
}

local function folder(parent, name)
    local f = Instance.new("Folder")
    f.Name = name
    f.Parent = parent
    return f
end

local function island()
    return WorldBuilder.islandFolder(ISLAND)
end

function TrialBuilder.storeKit(model)
    return WorldBuilder.storeKit(KIT, model, "TR_Anchor")
end

-- places a kit piece (every material part of it) at `frame` inside `parent`, with its look, anchored and touching nothing
local function placeKitPiece(parent, name, frame)
    WorldBuilder.placeTemplate(KIT, name, frame, parent)
    for _, part in parent:GetChildren() do
        if part:IsA("MeshPart") then
            local _, suffix = WorldBuilder.splitName(part.Name)
            local look = suffix and LOOKS[name] and LOOKS[name][suffix]
            if look then
                part.Material = Enum.Material[look.Material]
                part.Color = Color3.fromRGB(look.Color[1], look.Color[2], look.Color[3])
                part.CastShadow = look.CastShadow ~= false
                part.Reflectance = 0
            end
            part.Anchored = true
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
            part.Massless = true
            part.CollisionFidelity = Enum.CollisionFidelity.Box
        end
    end
end

-- ---------- the ground ----------
-- the top of the ground under a point, over the invisible zones and boxes the world keeps (a ray that meets one of those isn't a floor)
local function groundAt(position, lift)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    local skip = {}
    local origin = position + Vector3.new(0, lift or 10, 0)
    for _ = 1, 16 do
        params.FilterDescendantsInstances = skip
        local hit = workspace:Raycast(origin, Vector3.new(0, -70, 0), params)
        if not hit then
            return nil
        end
        if hit.Instance:IsA("BasePart") and not hit.Instance:IsA("Terrain") and hit.Instance.Transparency >= 0.99 then
            table.insert(skip, hit.Instance)
        else
            return hit.Position.Y
        end
    end
    return nil
end

local function spotsOf(root, padName, name)
    local pad = root:FindFirstChild(padName)
    local territory = pad and pad:FindFirstChild("Territory")
    local spot = territory and territory:FindFirstChild("Spots") and territory.Spots:FindFirstChild(name)
    return spot
end

local function box(parent, name, size, cframe)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size
    part.CFrame = cframe
    part.Anchored = true
    part.CanCollide = true
    part.CanTouch = false
    part.Transparency = 1
    part.Material = Enum.Material.Plastic
    part.CastShadow = false
    part.Parent = parent
    return part
end

local function prompt(parent, props)
    local p = Instance.new("ProximityPrompt")
    p.ActionText = props.Action
    p.ObjectText = props.Object
    p.KeyboardKeyCode = Enum.KeyCode.F
    p.HoldDuration = props.Hold or 0
    p.MaxActivationDistance = props.Distance or 12
    p.RequiresLineOfSight = false
    for key, value in props.Attributes or {} do
        p:SetAttribute(key, value)
    end
    p.Parent = parent
    return p
end

-- ---------- the Trial Stones ----------
local TRIALS = require(game:GetService("ReplicatedStorage"):WaitForChild("GameConfig")).Faction.Factions

-- a plain stone: a round foot, a stele with a band of the faction's colour round it, and the prompt that begins the trial
local function buildStone(parent, factionId, at)
    local look = FACTION[factionId]
    local info = TRIALS[factionId]
    local model = Instance.new("Model")
    model.Name = "TrialStone"
    model:SetAttribute("Faction", factionId)
    local base = Instance.new("Part")
    base.Name = "Foot"
    base.Shape = Enum.PartType.Cylinder
    base.Size = Vector3.new(1.2, 4.6, 4.6)
    base.CFrame = at * CFrame.new(0, 0.6, 0) * CFrame.Angles(0, 0, math.rad(90))
    base.Color = look.Base
    base.Material = look.BaseMaterial
    local stele = Instance.new("Part")
    stele.Name = "Stele"
    stele.Size = Vector3.new(2.4, 5.6, 1.1)
    stele.CFrame = at * CFrame.new(0, 1.2 + 2.8, 0)
    stele.Color = look.Stele
    stele.Material = look.SteleMaterial
    local band = Instance.new("Part")
    band.Name = "Band"
    band.Size = Vector3.new(2.6, 0.4, 1.3)
    band.CFrame = at * CFrame.new(0, 1.2 + 3.9, 0)
    band.Color = look.Band
    band.Material = Enum.Material.Neon
    band.CanCollide = false
    local cap = Instance.new("Part")
    cap.Name = "Cap"
    cap.Size = Vector3.new(2.9, 0.5, 1.5)
    cap.CFrame = at * CFrame.new(0, 1.2 + 5.85, 0)
    cap.Color = look.Base
    cap.Material = look.BaseMaterial
    for _, part in { base, stele, band, cap } do
        part.Anchored = true
        part.CanTouch = false
        part.Massless = true
        part.Parent = model
    end
    model.PrimaryPart = stele
    prompt(stele, { Action = "Begin the trial", Object = info.Trial.Name, Hold = 0.6, Distance = 10, Attributes = { FactionTrialStart = true, Faction = factionId } })
    CollectionService:AddTag(model, TAGS.Post)
    model.Parent = parent
    return model
end

-- ---------- the vaults ----------
local function buildVault(parent, factionId, position)
    local info = TRIALS[factionId]
    local part = Instance.new("Part")
    part.Name = "Vault_" .. factionId
    part.Size = Vector3.new(4, 6, 4)
    part.CFrame = CFrame.new(position + Vector3.new(0, 3 - SPOT_LIFT, 0))
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.Transparency = 1
    part:SetAttribute("Faction", factionId)
    prompt(part, { Action = "Open the vault", Object = info.Weapon.Name, Hold = 0.6, Distance = 12, Attributes = { FactionVault = true, Faction = factionId } })
    CollectionService:AddTag(part, TAGS.Vault)
    part.Parent = parent
    return part
end

-- ---------- the Orthodox gates ----------
local function standInGate(parent, frame)
    local model = Instance.new("Model")
    model.Name = "StandInGate"
    local function piece(name, size, offset, color, material)
        local part = Instance.new("Part")
        part.Name = name
        part.Size = size
        part.CFrame = frame * CFrame.new(offset)
        part.Anchored = true
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.Color = color
        part.Material = material
        part.Parent = model
    end
    local side = GATE.Opening / 2 + (GATE.Width - GATE.Opening) / 4
    local pillarWidth = (GATE.Width - GATE.Opening) / 2
    for _, sign in { -1, 1 } do
        piece("Pillar", Vector3.new(pillarWidth, GATE.Height - 2.5, GATE.Depth), Vector3.new(sign * side, (GATE.Height - 2.5) / 2, 0), Color3.fromRGB(236, 238, 244), Enum.Material.Marble)
    end
    piece("Lintel", Vector3.new(GATE.Width, 2.5, GATE.Depth + 0.6), Vector3.new(0, GATE.Height - 1.25, 0), Color3.fromRGB(96, 168, 255), Enum.Material.SmoothPlastic)
    model.Parent = parent
    return model
end

local function buildGates(trials, markers)
    local gates = folder(trials, "Gates")
    local placed, standIns = 0, 0
    local points = {}
    for index, marker in markers do
        local position = marker.Position
        local y = groundAt(position) or position.Y
        points[index] = Vector3.new(position.X, y, position.Z)
    end
    for index, point in points do
        local ahead = points[index + 1] or (point + (point - points[index - 1]))
        local flat = Vector3.new(ahead.X - point.X, 0, ahead.Z - point.Z).Unit
        local frame = CFrame.lookAt(point, point + flat)
        local holder = folder(gates, "Gate" .. index)
        if WorldBuilder.hasTemplate(KIT, "Trial_Props_TrialGate") then
            local model = Instance.new("Model")
            model.Name = "Gate"
            model.Parent = holder
            placeKitPiece(model, "Trial_Props_TrialGate", frame)
        else
            standInGate(holder, frame)
            standIns += 1
        end
        -- the pillars are solid (two invisible boxes, one beside each side of the opening); the opening stays clear
        local pillarWidth = (GATE.Width - GATE.Opening) / 2
        local side = GATE.Opening / 2 + pillarWidth / 2
        for _, sign in { -1, 1 } do
            box(holder, "Pillar", Vector3.new(pillarWidth, GATE.PillarHeight, GATE.Depth), frame * CFrame.new(sign * side, GATE.PillarHeight / 2, 0))
        end
        -- the zone the server tests the player against: tall, so a flyer passes through it too
        local zone = Instance.new("Part")
        zone.Name = "Zone"
        zone.Size = GATE.ZoneSize
        zone.CFrame = frame * CFrame.new(0, GATE.ZoneSize.Y / 2 - 2, 0)
        zone.Anchored = true
        zone.CanCollide = false
        zone.CanQuery = false
        zone.CanTouch = false
        zone.Transparency = 1
        zone:SetAttribute("Faction", "Orthodox")
        zone:SetAttribute("Index", index)
        zone:SetAttribute("BadgeHeight", GATE.Height + 4) -- where the client hangs the gate's number: just over its top (studs over the ground)
        CollectionService:AddTag(zone, TAGS.Gate)
        zone.Parent = holder
        placed += 1
    end
    return placed, standIns, points
end

-- ---------- the Windrift tokens ----------
local function standInToken(model, base)
    local function piece(name, shape, size, cframe, color, material)
        local part = Instance.new("Part")
        part.Name = name
        part.Shape = shape
        part.Size = size
        part.CFrame = cframe
        part.Anchored = true
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.Color = color
        part.Material = material
        part.Parent = model
    end
    piece("Stone", Enum.PartType.Block, Vector3.new(3, 0.7, 3), base * CFrame.new(0, 0.35, 0), Color3.fromRGB(96, 98, 92), Enum.Material.Slate)
    piece("Stand", Enum.PartType.Block, Vector3.new(0.5, 1.6, 0.4), base * CFrame.new(0, 1.5, 0), Color3.fromRGB(122, 94, 64), Enum.Material.Wood)
    piece("Disc", Enum.PartType.Cylinder, Vector3.new(0.25, 1.6, 1.6), base * CFrame.new(0, 2.3, 0) * CFrame.Angles(0, 0, math.rad(90)) * CFrame.Angles(math.rad(90), 0, 0), Color3.fromRGB(150, 98, 54), Enum.Material.Metal)
    piece("Inlay", Enum.PartType.Cylinder, Vector3.new(0.3, 1.0, 1.0), base * CFrame.new(0, 2.3, 0) * CFrame.Angles(0, 0, math.rad(90)) * CFrame.Angles(math.rad(90), 0, 0), Color3.fromRGB(70, 200, 150), Enum.Material.Neon)
end

local function buildTokens(trials, markers)
    local tokens = folder(trials, "Tokens")
    local placed, standIns = 0, 0
    for index, marker in markers do
        local position = marker.Position
        local y = groundAt(position) or position.Y
        local base = CFrame.new(position.X, y, position.Z)
        local model = Instance.new("Model")
        model.Name = "Token" .. index
        model:SetAttribute("Faction", "Unorthodox")
        model:SetAttribute("Index", index)
        local root = Instance.new("Part")
        root.Name = "Root"
        root.Size = Vector3.new(2, 2, 2)
        root.CFrame = base * CFrame.new(0, 1.95, 0) -- (the disc's middle)
        root.Anchored = true
        root.CanCollide = false
        root.CanQuery = false
        root.CanTouch = false
        root.Transparency = 1
        root.Parent = model
        model.PrimaryPart = root
        model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- (its prompt arrives with it)
        if WorldBuilder.hasTemplate(KIT, "Trial_Props_TrialToken") then
            placeKitPiece(model, "Trial_Props_TrialToken", base)
        else
            standInToken(model, base)
            standIns += 1
        end
        -- a few sparks of its own colour, so it is found by the eye (a small, slow emitter: no script)
        local sparks = Instance.new("ParticleEmitter")
        sparks.Name = "Glint"
        sparks.Texture = "rbxassetid://243664672"
        sparks.Rate = 3
        sparks.Lifetime = NumberRange.new(1.6, 2.4)
        sparks.Speed = NumberRange.new(0.4, 1)
        sparks.SpreadAngle = Vector2.new(180, 180)
        sparks.LightEmission = 1
        sparks.LightInfluence = 0
        sparks.Color = ColorSequence.new(Color3.fromRGB(70, 200, 150), Color3.fromRGB(240, 170, 90))
        sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.7), NumberSequenceKeypoint.new(1, 0) })
        sparks.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.35), NumberSequenceKeypoint.new(1, 1) })
        sparks.Parent = root
        prompt(root, { Action = "Take the token", Object = "Windrift Token", Hold = 0.4, Distance = 8, Attributes = { TrialToken = true, Faction = "Unorthodox", Index = index } })
        CollectionService:AddTag(model, TAGS.Token)
        model.Parent = tokens
        placed += 1
    end
    return placed, standIns
end

-- ---------- the arena's dummy ----------
-- ServerStorage.TrialDummy: what TrialService clones for each dummy of a wave. Its PrimaryPart "Root" is an invisible part at the dummy's foot (Combat measures a strike from the
-- PrimaryPart's centre, and a body stands about 3 studs over the floor, well inside its reach), so a place's marker puts the foot on the floor. Nothing in it collides.
local function buildDummyTemplate()
    local old = ServerStorage:FindFirstChild("TrialDummy")
    if old then
        old:Destroy()
    end
    local model = Instance.new("Model")
    model.Name = "TrialDummy"
    local standIn = false
    local foot = CFrame.new(0, 0, 0)
    if WorldBuilder.hasTemplate(KIT, "Trial_Props_TrialDummy") then
        placeKitPiece(model, "Trial_Props_TrialDummy", foot)
    else
        standIn = true
        local function piece(name, size, offset, color, material)
            local part = Instance.new("Part")
            part.Name = name
            part.Size = size
            part.CFrame = foot * CFrame.new(offset)
            part.Color = color
            part.Material = material
            part.Parent = model
        end
        piece("Base", Vector3.new(3.6, 0.8, 3.6), Vector3.new(0, 0.4, 0), Color3.fromRGB(44, 42, 50), Enum.Material.Metal)
        piece("Post", Vector3.new(0.9, 5.4, 0.9), Vector3.new(0, 3.1, 0), Color3.fromRGB(70, 54, 40), Enum.Material.Wood)
        piece("Torso", Vector3.new(2.2, 2.4, 1.6), Vector3.new(0, 3.8, 0), Color3.fromRGB(150, 36, 36), Enum.Material.Fabric)
        piece("Arms", Vector3.new(4, 0.6, 0.6), Vector3.new(0, 4.4, 0), Color3.fromRGB(70, 54, 40), Enum.Material.Wood)
        piece("Helm", Vector3.new(1.4, 1.2, 1.4), Vector3.new(0, 5.8, 0), Color3.fromRGB(34, 32, 40), Enum.Material.Metal)
    end
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") then
            part.Anchored = true
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
            part.Massless = true
        end
    end
    local root = Instance.new("Part")
    root.Name = "Root"
    root.Size = Vector3.new(1, 1, 1)
    root.CFrame = foot
    root.Anchored = true
    root.CanCollide = false
    root.CanQuery = false
    root.CanTouch = false
    root.Transparency = 1
    root:SetAttribute("KeepInvisible", true)
    root.Parent = model
    model.PrimaryPart = root
    model.Parent = ServerStorage
    return standIn
end

-- ---------- the whole ----------
local function stoneFrame(from, towards, back, side)
    local flat = Vector3.new(towards.X - from.X, 0, towards.Z - from.Z).Unit
    local right = flat:Cross(Vector3.yAxis)
    local at = from - flat * back + right * side
    local y = groundAt(at) or from.Y
    return CFrame.lookAt(Vector3.new(at.X, y, at.Z), Vector3.new(at.X, y, at.Z) + flat)
end

function TrialBuilder.build()
    local root = island()
    local old = root:FindFirstChild("Trials")
    if old then
        old:Destroy()
    end
    local trials = folder(root, "Trials")
    local report = { StandIns = {} }

    -- Orthodox
    local ortho = root:FindFirstChild("OrthodoxPad")
    local markers = {}
    for index = 1, 5 do
        markers[index] = ortho and ortho:FindFirstChild("TrialGate" .. index)
    end
    if #markers == 5 then
        local f = folder(trials, "Orthodox")
        local placed, standIns, points = buildGates(f, markers)
        report.Gates = placed
        if standIns > 0 then
            table.insert(report.StandIns, "gates x" .. standIns)
        end
        buildStone(f, "Orthodox", stoneFrame(points[1], points[2], 9, 11))
        local vault = ortho:FindFirstChild("Hall") and ortho.Hall:FindFirstChild("Spots") and ortho.Hall.Spots:FindFirstChild("VaultSpot")
        report.OrthodoxVault = if vault then buildVault(f, "Orthodox", vault.Position) ~= nil else false
    end

    -- Unorthodox
    local unortho = root:FindFirstChild("UnorthodoxPad")
    local tokenMarkers = {}
    for index = 1, 6 do
        tokenMarkers[index] = unortho and unortho:FindFirstChild("TrialToken" .. index)
    end
    if #tokenMarkers == 6 then
        local f = folder(trials, "Unorthodox")
        local placed, standIns = buildTokens(f, tokenMarkers)
        report.Tokens = placed
        if standIns > 0 then
            table.insert(report.StandIns, "tokens x" .. standIns)
        end
        local gate = unortho:FindFirstChild("Gate")
        local centre = unortho:FindFirstChild("Centre")
        if gate and centre then
            buildStone(f, "Unorthodox", stoneFrame(gate.Position, centre.Position, 0, 9))
        end
        local cradle = spotsOf(root, "UnorthodoxPad", "SaberDisplay")
        report.UnorthodoxVault = if cradle then buildVault(f, "Unorthodox", cradle.Position) ~= nil else false
    end

    -- Demonic
    local demonic = root:FindFirstChild("DemonicPad")
    local arena = spotsOf(root, "DemonicPad", "ArenaCentre")
    local court = spotsOf(root, "DemonicPad", "GateCourt")
    local armory = spotsOf(root, "DemonicPad", "Vault")
    if demonic and arena and court then
        local f = folder(trials, "Demonic")
        -- outside the arena's front gate (the side the gate court is on), to one side of its way in
        local flat = Vector3.new(court.Position.X - arena.Position.X, 0, court.Position.Z - arena.Position.Z).Unit
        local right = flat:Cross(Vector3.yAxis)
        local at = arena.Position + flat * 19 + right * 6
        local y = groundAt(at) or arena.Position.Y - SPOT_LIFT
        buildStone(f, "Demonic", CFrame.lookAt(Vector3.new(at.X, y, at.Z), Vector3.new(arena.Position.X, y, arena.Position.Z)))
        if armory then
            report.DemonicVault = buildVault(f, "Demonic", armory.Position) ~= nil
        end
        if buildDummyTemplate() then
            table.insert(report.StandIns, "dummy")
        end
        report.Dummy = ServerStorage:FindFirstChild("TrialDummy") ~= nil
    end
    return report
end

function TrialBuilder.check()
    local root = island()
    local trials = root:FindFirstChild("Trials")
    if not trials then
        return "no Trials folder: run TrialBuilder.build()"
    end
    local count = { [TAGS.Post] = 0, [TAGS.Gate] = 0, [TAGS.Token] = 0, [TAGS.Vault] = 0 }
    for tag in count do
        for _, instance in CollectionService:GetTagged(tag) do
            if instance:IsDescendantOf(trials) then
                count[tag] += 1
            end
        end
    end
    local parts = 0
    for _, d in trials:GetDescendants() do
        if d:IsA("BasePart") then
            parts += 1
        end
    end
    local dummy = ServerStorage:FindFirstChild("TrialDummy")
    return string.format("%d Trial Stones (3 wanted), %d gate zones (5), %d tokens (6), %d vault prompts (3), %d parts, dummy template %s, %d arena places",
        count[TAGS.Post], count[TAGS.Gate], count[TAGS.Token], count[TAGS.Vault], parts, if dummy then "stored" else "MISSING",
        #CollectionService:GetTagged("NightfallArenaDummy"))
end

return TrialBuilder

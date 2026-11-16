-- Build-time only: run from Studio (edit mode) to (re)build the Beast Pastures on Yggdrasil (the owner, 2026-11-15: one pen per player,
-- its size upgradable). Require a clone so Studio's module cache never serves an old copy:
--
--   local PB = require(game.ServerStorage.WorldBuild.PastureBuilder:Clone())
--   PB.build()        -- Workspace.FloatingIslands.Yggdrasil.BeastPastures, from Placements/Pastures.lua (replaces any built before)
--   PB.check()        -- each site's ground: how far it is from level, and what stands in its way (a report; changes nothing)
--   PB.clearGround()  -- gives back the grass under every site's ring and yard (before moving a site; build() lays it again)
--   PB.layGround()    -- lays only the ground (each site's yard, then its ring and lane), leaving the built pastures as they are
--
-- What stands at every level is built here, in the hub's celestial look: a ring of pale paving round the pasture's whole ground (terrain
-- Pavement, flush, so no grass grows through it and it reads as one place from afar), a lawn with no grass blades inside the ring
-- (LeafyGrass: the pen's wooden deck, PenFence, lies on it, and Grass's blades grew up through the deck), the pen's gate (two marble
-- posts with gold caps and crystals, at the middle of the front fence's line, which stays put at every level: shared/PenLayout)
-- holding the PenPrompt that opens the pen picker, and before it the owner's board (marble posts, a gold-framed navy board PenService
-- writes the holder's name and level on) holding the UpgradePrompt. PenController shows both prompts only to the pasture's holder. The fence itself grows with the
-- level, so each client builds it (PenFence) from the pasture's replicated Level.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"):Clone())
-- (from ServerStorage, not script.Parent: this module runs as a clone, which has no parent)
local Sites = require(game:GetService("ServerStorage"):WaitForChild("WorldBuild"):WaitForChild("Placements"):WaitForChild("Pastures"):Clone())

local PastureBuilder = {}

local HUB_CENTRE = Vector3.new(0, 200, 0) -- Yggdrasil's island frame (no turns): island-local + this = world

local MARBLE = Color3.fromRGB(232, 234, 244)
local GOLD = Color3.fromRGB(226, 176, 70)       -- the hub's GoldFlat (WorldBuilder.MaterialLooks): Metal mirrored the sky olive
local CRYSTAL = Color3.fromRGB(96, 214, 255)    -- the hub's crystal blue, on Neon
local BOARD = Color3.fromRGB(24, 25, 68)        -- the interface's navy, for the name board's face

local groundAt -- (below: the terrain's height at a point)
local spawnPad -- (below: a pasture's holder's spawn)

local function part(name, size, cframe, parent, look)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.Size = size
    p.CFrame = cframe
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Material = look.Material or Enum.Material.Marble
    p.Color = look.Color or MARBLE
    p.CanCollide = look.CanCollide ~= false
    p.CanTouch = false
    p.CastShadow = look.CastShadow ~= false
    p.Parent = parent
    return p
end

local MARBLE_LOOK = { Material = Enum.Material.Marble, Color = MARBLE }
local GOLD_LOOK = { Material = Enum.Material.SmoothPlastic, Color = GOLD, CastShadow = false }
local CRYSTAL_LOOK = { Material = Enum.Material.Neon, Color = CRYSTAL, CanCollide = false, CastShadow = false }

local function surfaceText(board, pixels)
    for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
        local gui = Instance.new("SurfaceGui")
        gui.Face = face
        gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
        gui.PixelsPerStud = pixels
        gui.LightInfluence = 0.2
        gui.MaxDistance = 160
        gui.Parent = board
        local name = Instance.new("TextLabel")
        name.Name = "OwnerName"
        name.BackgroundTransparency = 1
        name.Position = UDim2.fromScale(0.04, 0.06)
        name.Size = UDim2.fromScale(0.92, 0.56)
        name.Font = Enum.Font.Garamond
        name.TextScaled = true
        name.TextColor3 = Color3.fromRGB(255, 226, 150)
        name.Text = "Beast Pasture"
        name.Parent = gui
        local line = Instance.new("TextLabel")
        line.Name = "Area"
        line.BackgroundTransparency = 1
        line.Position = UDim2.fromScale(0.08, 0.64)
        line.Size = UDim2.fromScale(0.84, 0.28)
        line.Font = Enum.Font.GothamBold
        line.TextScaled = true
        line.TextColor3 = Color3.fromRGB(172, 170, 204)
        line.Text = ""
        line.Parent = gui
    end
end

local function prompt(holder, name, action, object)
    local p = Instance.new("ProximityPrompt")
    p.Name = name
    p.ActionText = action
    p.ObjectText = object
    p.KeyboardKeyCode = Enum.KeyCode.F -- (E is cultivating)
    p.HoldDuration = 0
    p.MaxActivationDistance = 11
    p.RequiresLineOfSight = false
    p.Enabled = false -- (PenController turns it on for the pasture's holder)
    p.Parent = holder
    return p
end

-- the gate (its posts at the gap's two ends, on the front fence's line) and the owner's board before it
local BOARD_SIDE = 9.5 -- studs left of the gate (its centre) the owner's board stands

local function buildGateAndBoard(pasture, frame, area)
    local gate = frame * CFrame.new(0, 0, PenLayout.Front)
    gate = gate.Rotation + Vector3.new(gate.X, groundAt(gate.Position), gate.Z)
    for _, side in { -1, 1 } do
        local at = gate * CFrame.new(side * (PenLayout.Gate / 2 + 0.6), 0, 0)
        part("GatePost", Vector3.new(1.2, 6.4, 1.2), at * CFrame.new(0, 1.2, 0), pasture, MARBLE_LOOK)
        part("GateCap", Vector3.new(1.4, 0.3, 1.4), at * CFrame.new(0, 4.55, 0), pasture, GOLD_LOOK)
        part("GateCrystal", Vector3.new(0.7, 1.3, 0.7), at * CFrame.new(0, 5.35, 0) * CFrame.Angles(0, math.rad(45), 0), pasture, CRYSTAL_LOOK)
    end
    part("GateBeam", Vector3.new(PenLayout.Gate + 2.4, 0.4, 0.5), gate * CFrame.new(0, 4.95, 0), pasture, GOLD_LOOK)
    local penHolder = part("PenPromptHolder", Vector3.new(1, 1, 1), gate * CFrame.new(0, 2.5, 0), pasture,
        { Material = Enum.Material.SmoothPlastic, CanCollide = false, CastShadow = false })
    penHolder.Transparency = 1
    penHolder.CanQuery = false
    prompt(penHolder, "PenPrompt", "Your pen", "Beast pen")

    -- (the hub's redesign, 2026-11-15: the holder spawns 10 studs before the gate, the default camera right behind them, so the board
    -- stands to the left of the gate, where neither their body nor their name tag hides it; raised over their head it sat right
    -- behind the name tag)
    local board = frame * CFrame.new(-BOARD_SIDE, 0, PenLayout.Board) * CFrame.Angles(0, math.rad(-12), 0)   -- (turned toward the spawn)
    board = board.Rotation + Vector3.new(board.X, groundAt(board.Position), board.Z)
    for _, side in { -1, 1 } do
        part("BoardLeg", Vector3.new(0.9, 7.4, 0.9), board * CFrame.new(side * 5.2, 1.7, 0), pasture, MARBLE_LOOK)
    end
    part("BoardFrame", Vector3.new(11, 3.2, 0.5), board * CFrame.new(0, 5.4, 0), pasture, GOLD_LOOK)
    local face = part("Board", Vector3.new(10.4, 2.7, 0.6), board * CFrame.new(0, 5.4, 0), pasture,
        { Material = Enum.Material.SmoothPlastic, Color = BOARD, CastShadow = false })
    surfaceText(face, 40)
    face:FindFirstChild("Area", true).Text = string.upper(area)
    local upgradeHolder = part("UpgradePromptHolder", Vector3.new(1, 1, 1), board * CFrame.new(0, 2.4, 0), pasture,
        { Material = Enum.Material.SmoothPlastic, CanCollide = false, CastShadow = false })
    upgradeHolder.Transparency = 1
    upgradeHolder.CanQuery = false
    prompt(upgradeHolder, "UpgradePrompt", "Upgrade pen", "Beast pen")
end

-- the ring and the lane, in the terrain: a strip of `material` laid flush with the ground (filled from below up to its surface)
local GROUND_RING = Enum.Material.Pavement -- (the hub's paving tone; Limestone read as snow)
-- the yard inside the ring, under the pen at every level: a ground with no grass blades, since Grass's blades (Terrain.Decoration)
-- grow up through any part laid on it, and the pen's deck is a part (the owner, 2026-11-16: "add a wooden floor in every pen")
local GROUND_YARD = Enum.Material.LeafyGrass
local function yardStrips()
    local ring = PenLayout.Ring
    return { { CFrame.new(), Vector3.new(ring.Width - ring.Band, 0, ring.Depth - ring.Band) } }
end
local function groundStrips()
    local ring = PenLayout.Ring
    local w, d, band = ring.Width, ring.Depth, ring.Band
    return {
        { CFrame.new(0, 0, -d / 2), Vector3.new(w + band, 0, band) },
        { CFrame.new(0, 0, d / 2), Vector3.new(w + band, 0, band) },
        { CFrame.new(-w / 2, 0, 0), Vector3.new(band, 0, d) },
        { CFrame.new(w / 2, 0, 0), Vector3.new(band, 0, d) },
        -- the path from the ring's front to the gate
        { CFrame.new(0, 0, (PenLayout.Front - d / 2) / 2), Vector3.new(PenLayout.Gate, 0, PenLayout.Front + d / 2) },
    }
end

-- Sets the surface material of every terrain column under the strips (its top two solid voxels), leaving every voxel's occupancy as it
-- was: the ground never moves, however often this runs. (A FillBlock flush with the surface raised it 2 to 4 studs, and more each run:
-- seen in Studio, 2026-11-15, and repaired column by column from the untouched grass beside each.)
local function layGround(frame, material, strips)
    local terrain = workspace.Terrain
    local done = {}
    for _, strip in strips or groundStrips() do
        local size = strip[2]
        for a = -size.X / 2, size.X / 2, 2 do
            for b = -size.Z / 2, size.Z / 2, 2 do
                local p = frame * (strip[1] * Vector3.new(a, 0, b))
                local cx, cz = math.floor(p.X / 4), math.floor(p.Z / 4)
                local key = cx .. "," .. cz
                if not done[key] then
                    done[key] = true
                    local region = Region3.new(Vector3.new(cx * 4, p.Y - 16, cz * 4), Vector3.new(cx * 4 + 4, p.Y + 16, cz * 4 + 4))
                        :ExpandToGrid(4)
                    local materials, occupancy = terrain:ReadVoxels(region, 4)
                    local top = 0
                    for y = 1, occupancy.Size.Y do
                        if occupancy[1][y][1] > 0 then
                            top = y
                        end
                    end
                    if top > 0 then
                        local m, o = {}, {}
                        for y = 1, occupancy.Size.Y do
                            local mat = materials[1][y][1]
                            if occupancy[1][y][1] > 0 and y >= top - 1 and mat ~= Enum.Material.Rock then -- (a rock outcrop keeps its rock)
                                mat = material
                            end
                            m[y] = { mat }
                            o[y] = { occupancy[1][y][1] }
                        end
                        terrain:WriteVoxels(region, 4, { m }, { o })
                    end
                end
            end
        end
    end
end

-- the ground's height at a pasture's centre (terrain only), or the hub's ground height
function groundAt(position)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Include
    params.FilterDescendantsInstances = { workspace.Terrain }
    local hit = workspace:Raycast(position + Vector3.new(0, 40, 0), Vector3.new(0, -80, 0), params)
    return if hit then hit.Position.Y else position.Y
end

-- every spot must hold the largest pen and its paving ring (shared/PenLayout)
for index, site in Sites do
    local ring = PenLayout.Ring
    assert(site.Footprint and site.Footprint.X >= ring.Width + ring.Band and site.Footprint.Y >= ring.Depth + ring.Band
        and -PenLayout.Board <= site.Footprint.Y / 2,
        "Placements/Pastures[" .. index .. "]: its Footprint is too small for the largest pen")
end

function PastureBuilder.frameOf(site)
    local centre = HUB_CENTRE + site.Centre
    centre = Vector3.new(centre.X, groundAt(centre), centre.Z)
    return CFrame.new(centre) * CFrame.Angles(0, site.Yaw, 0)
end

-- Its holder's spawn (the hub's redesign, 2026-11-15): an invisible SpawnLocation on the spawn pad (the kit's HB_SpawnPad, top 0.45 over
-- the ground), turned to face the pen, so the character arrives looking at its pen. WorldService makes it the holder's RespawnLocation.
-- Every player always has a RespawnLocation of their own, so the game never picks one of these for anyone else.
local PAD_TOP = 0.45
function spawnPad(pasture, frame, spawn)
    local at = frame * CFrame.new(spawn) * CFrame.Angles(0, math.pi, 0)   -- (the spot's +Z, away from the tree, is toward its pen)
    local ground = groundAt(at.Position)
    local point = Instance.new("SpawnLocation")
    point.Name = "Spawn"
    point.Size = Vector3.new(6, 1, 6)
    point.CFrame = CFrame.new(at.X, ground + PAD_TOP - 0.5, at.Z) * at.Rotation
    point.Transparency = 1
    point.Anchored = true
    point.CanCollide = false
    point.CanQuery = false
    point.CanTouch = false
    point.Neutral = true
    point.AllowTeamChangeOnTouch = false
    point.Duration = 0
    for _, child in point:GetChildren() do
        child:Destroy() -- the default decal
    end
    point.Parent = pasture
    return point
end

function PastureBuilder.build()
    local hub = workspace:WaitForChild("FloatingIslands"):WaitForChild("Yggdrasil")
    local old = hub:FindFirstChild("BeastPastures")
    if old then
        old:Destroy()
    end
    local folder = Instance.new("Folder")
    folder.Name = "BeastPastures"
    for index, site in Sites do
        local frame = PastureBuilder.frameOf(site)
        local pasture = Instance.new("Model")
        pasture.Name = "Pasture" .. index
        pasture:SetAttribute("Index", index)
        pasture:SetAttribute("Frame", frame)
        pasture:SetAttribute("Area", site.Area)
        layGround(frame, GROUND_YARD, yardStrips()) -- (the yard first: the ring then takes back the cells they share)
        layGround(frame, GROUND_RING)
        buildGateAndBoard(pasture, frame, site.Area)
        if site.Spawn then
            spawnPad(pasture, frame, site.Spawn)
        end
        pasture.Parent = folder
        task.wait()
    end
    folder.Parent = hub
    return folder
end

function PastureBuilder.clearGround()
    for _, site in Sites do
        local frame = PastureBuilder.frameOf(site)
        layGround(frame, Enum.Material.Grass, yardStrips())
        layGround(frame, Enum.Material.Grass)
    end
end

function PastureBuilder.layGround()
    for _, site in Sites do
        local frame = PastureBuilder.frameOf(site)
        layGround(frame, GROUND_YARD, yardStrips())
        layGround(frame, GROUND_RING)
        task.wait()
    end
end

-- For each site: the ground's spread under its footprint (a 4-stud grid of terrain rays) and anything in the world (not terrain, not
-- the pastures) whose box overlaps its footprint up to 12 studs over the ground.
function PastureBuilder.check()
    local lines = {}
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Include
    params.FilterDescendantsInstances = { workspace.Terrain }
    local overlap = OverlapParams.new()
    local pastures = workspace.FloatingIslands.Yggdrasil:FindFirstChild("BeastPastures")
    overlap.FilterDescendantsInstances = { workspace.Terrain, pastures }
    overlap.FilterType = Enum.RaycastFilterType.Exclude
    for index, site in Sites do
        local frame = PastureBuilder.frameOf(site)
        local lo, hi, misses = math.huge, -math.huge, 0
        for x = -PenLayout.Ring.Width / 2 - 2, PenLayout.Ring.Width / 2 + 2, 4 do
            for z = -PenLayout.Ring.Depth / 2 - 2, PenLayout.Ring.Depth / 2 + 2, 4 do
                local p = frame * Vector3.new(x, 0, z)
                local hit = workspace:Raycast(p + Vector3.new(0, 40, 0), Vector3.new(0, -80, 0), params)
                if hit then
                    lo, hi = math.min(lo, hit.Position.Y), math.max(hi, hit.Position.Y)
                else
                    misses += 1
                end
            end
        end
        local blockers = {}
        for _, p in workspace:GetPartBoundsInBox(frame * CFrame.new(0, 6.5, 0), Vector3.new(PenLayout.Ring.Width + 8, 12, PenLayout.Ring.Depth + 8), overlap) do
            local top = p:FindFirstAncestorOfClass("Model") or p
            blockers[top:GetFullName()] = true
        end
        local names = {}
        for name in blockers do
            table.insert(names, name)
        end
        table.insert(lines, string.format("%d %s: ground %.2f..%.2f (centre %.2f), %d misses; overlaps: %s", index, site.Area, lo, hi,
            frame.Position.Y, misses, table.concat(names, ", ")))
    end
    return table.concat(lines, "\n")
end

return PastureBuilder

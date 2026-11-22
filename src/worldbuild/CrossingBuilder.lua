-- Build-time only: run from Studio (Edit mode) to build Murim Crossing's standing parts (the owner's faction map, 2026-11-22; phase M1, the
-- foundation). Its ground is terrain (WorldBuilder.buildTerrain("MurimCrossing"), written by tools/blender/world/murim_layout.py) and its
-- bridge WorldBuilder.buildBridges("MurimRoute"); this builds what stands on them, from Placements/MurimCrossing.lua. Require a clone so
-- Studio's module cache never serves an old copy:
--
--   local CB = require(game.ServerStorage.WorldBuild.CrossingBuilder:Clone())
--   CB.build()    -- Workspace.FloatingIslands.MurimCrossing (replaces what was built before; never touches the terrain beyond the hub apron's
--                 cobblestone: the columns under the bridge's hub end, which the hub's grass would grow through)
--   CB.check()    -- a report on the ground: how level the plaza, the landings and the pads' flat discs are, and their materials
--
-- What it makes (plain parts, Roblox materials and kits already in the place: no upload, no import):
--   Plaza          the oath stone (a dais, a stele with its world board on both faces and a tiled roof) and the three banner poles
--   Gate           the island's own entrance, a plain Korean post-and-lintel gate with a tiled roof across the end of the bridge
--   Stairs         each headquarters' stairway (solid steps, walls, a gate at the top with its name, flags on the first landing)
--   Npcs           the three representatives, on the plaza in front of their stairs (R15, plainly dressed; tagged FactionRep + HubNpc, a "Talk"
--                  prompt each)
--   <Faction>Pad   empty markers for each headquarters (centre, gate, main hall, vault, trial points): nothing is built on the pads yet
--   Approach       the route zones and checks WorldService uses to bring back a player who falls (bridge, spur, plaza, stairs, pads, hidden paths)
--   Checkpoint     where a fall from the island lands (the plaza, facing the oath stone)
--   Dress          forest trees (the Jade Grove's) on the Unorthodox side, basalt and shards (the Ember Peak's) on the Demonic, one waterfall
--                  (WorldBuilder.buildWaterfall) and the blood moon (the Orthodox side's own trees and falls are Dawnspire's: DawnspireBuilder)
--   HubApron       the hub's end of the bridge: a marble apron (cobblestone under it, so no grass grows through) and a pair of crystal lamps
-- No Chinese forms anywhere (no paifang, red lacquer or lanterns, dragon or ridge beasts, lettering): Korean hanok and gate forms, plain
-- timber and stone, Japanese-style paper lanterns, and shapes of its own.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"):Clone())
-- (shared/FactionRules.RepTag: not required here, because a clone of FactionRules would still require the live GameConfig, which Studio's
-- Edit session may have cached from before a change, and fail to load)
local REP_TAG = "FactionRep"
-- (from ServerStorage, not script.Parent: this module runs as a clone, which has no parent)
local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local P = require(WorldBuild:WaitForChild("Placements"):WaitForChild("MurimCrossing"):Clone())
local BridgePlacements = require(WorldBuild.Placements:WaitForChild("Bridges"):Clone())

local CrossingBuilder = {}

local ISLAND = "MurimCrossing"
local ROUTE = "MurimRoute"
local VOXEL = 4

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

-- ---------- looks ----------
local STONE = { Material = Enum.Material.Granite, Color = rgb(200, 202, 210), Solid = true }
local STONE_DARK = { Material = Enum.Material.Granite, Color = rgb(132, 134, 144), Solid = true }
local TILE = { Material = Enum.Material.Slate, Color = rgb(70, 80, 102) }             -- grey-blue roof tile
local TILE_DARK = { Material = Enum.Material.Slate, Color = rgb(52, 60, 80) }
local TIMBER = { Material = Enum.Material.Wood, Color = rgb(112, 86, 62) }          -- raw cedar, not painted (and not red)
local TIMBER_DARK = { Material = Enum.Material.Wood, Color = rgb(78, 60, 46) }
local BOARD = { Material = Enum.Material.Slate, Color = rgb(34, 36, 46) }
local PAPER = { Material = Enum.Material.SmoothPlastic, Color = rgb(238, 222, 176) }

-- each faction's own colours (GameConfig.Faction has the interface's; these are the cloth, stone and wood's)
local ORTHODOX = { Cloth = rgb(244, 246, 250), Blue = rgb(36, 78, 186), Gold = rgb(226, 176, 70), Stone = rgb(232, 234, 240) } -- white, blue and gold
local UNORTHODOX = { Jade = rgb(26, 88, 72), Copper = rgb(190, 112, 56), Linen = rgb(224, 210, 178), Wood = rgb(96, 82, 60) } -- dark jade, copper and linen
local DEMONIC = { Black = rgb(24, 22, 28), Crimson = rgb(176, 28, 40), Iron = rgb(46, 44, 54), Ember = rgb(255, 92, 40) }

local function cloth(colour)
    return { Material = Enum.Material.Fabric, Color = colour, Shadow = false }
end

local function plastic(colour)
    return { Material = Enum.Material.SmoothPlastic, Color = colour }
end

-- ---------- a few helpers ----------
local frame -- the island's frame (centre and turn), set by build()

local function at(position, yaw)
    return frame * CFrame.new(position) * CFrame.Angles(0, yaw or 0, 0)
end

local function folder(parent, name, class)
    local f = Instance.new(class or "Folder")
    f.Name = name
    f.Parent = parent
    return f
end

-- A part. look: Material, Color, Solid (collides and answers queries; decoration does neither), Shadow = false, Shape (a Part's),
-- Wedge (a WedgePart), Transparency.
local function part(parent, name, size, cframe, look)
    local p = Instance.new(if look.Wedge then "WedgePart" else "Part")
    p.Name = name
    p.Anchored = true
    p.Size = size
    p.CFrame = cframe
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Material = look.Material or Enum.Material.SmoothPlastic
    p.Color = look.Color or Color3.new(1, 1, 1)
    p.CanCollide = look.Solid == true
    p.CanQuery = look.Solid == true
    p.CanTouch = false
    p.CastShadow = look.Shadow ~= false
    if look.Transparency then
        p.Transparency = look.Transparency
    end
    if look.Shape and p:IsA("Part") then
        p.Shape = look.Shape
    end
    p.Parent = parent
    return p
end

-- A vertical cylinder standing on `base` (the centre of its bottom).
local function column(parent, name, diameter, height, base, look)
    local l = table.clone(look)
    l.Shape = Enum.PartType.Cylinder
    return part(parent, name, Vector3.new(height, diameter, diameter), base * CFrame.new(0, height / 2, 0) * CFrame.Angles(0, 0, math.pi / 2), l)
end

-- A box standing on `base` (the centre of its bottom).
local function block(parent, name, size, base, look)
    return part(parent, name, size, base * CFrame.new(0, size.Y / 2, 0), look)
end

local function ball(parent, name, diameter, cframe, look)
    local l = table.clone(look)
    l.Shape = Enum.PartType.Ball
    return part(parent, name, Vector3.new(diameter, diameter, diameter), cframe, l)
end

local function model(parent, name)
    local m = Instance.new("Model")
    m.Name = name
    m.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- (a whole assembly arrives together, board and all)
    m.Parent = parent
    return m
end

local function marker(parent, name, cframe, attributes)
    local m = WorldBuilder.marker(name, Vector3.new(1, 1, 1), cframe, parent)
    m.Material = Enum.Material.Plastic -- (an invisible part still costs a batch per material)
    for key, value in attributes or {} do
        m:SetAttribute(key, value)
    end
    return m
end

local function hex(c)
    return string.format("#%02X%02X%02X", math.floor(c.R * 255 + 0.5), math.floor(c.G * 255 + 0.5), math.floor(c.B * 255 + 0.5))
end

-- ---------- the world board (what the Court is, in plain words) ----------
local FAMILY = "rbxasset://fonts/families/"
local HEAD_FONT = Font.new(FAMILY .. "Merriweather.json", Enum.FontWeight.Bold)
local BODY_FONT = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.SemiBold)
local BOARD_PPS = 48

local function factionWord(id)
    local info = GameConfig.Faction.Factions[id]
    return '<font color="' .. hex(info.Color) .. '"><b>' .. info.Short .. "</b></font>"
end

local BOARD_BODY = table.concat({
    "Three factions share this island.",
    factionWord("Orthodox") .. ", " .. factionWord("Unorthodox") .. " and " .. factionWord("Demonic") .. '. All three are <font color="#FFE7A6"><b>equally strong</b></font>.',
    "Anyone can walk in, look around and talk to each leader.",
    "To join one, you need <b>" .. GameConfig.Faction.JoinRealm .. "</b>.",
    'Joining is <font color="#FFB27A"><b>for good</b></font>. You can never switch.',
}, "\n\n")

-- A SurfaceGui on `panel`'s Front face: a heading and one rich-text body (every label costs a draw call: two per face).
local function boardGui(panel, heading, body)
    local gui = Instance.new("SurfaceGui")
    gui.Name = "Board"
    gui.Face = Enum.NormalId.Front
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = BOARD_PPS
    gui.LightInfluence = 0.25
    gui.Brightness = 1
    gui.MaxDistance = 90
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = panel
    local width, height = panel.Size.X * BOARD_PPS, panel.Size.Y * BOARD_PPS
    local title = Instance.new("TextLabel")
    title.Name = "Heading"
    title.BackgroundTransparency = 1
    title.Position = UDim2.fromOffset(18, 16)
    title.Size = UDim2.fromOffset(width - 36, 50)
    title.FontFace = HEAD_FONT
    title.TextSize = 38
    title.TextColor3 = rgb(244, 214, 138)
    title.TextXAlignment = Enum.TextXAlignment.Center
    title.Text = heading
    title.Parent = gui
    local text = Instance.new("TextLabel")
    text.Name = "Body"
    text.BackgroundTransparency = 1
    text.Position = UDim2.fromOffset(26, 84)
    text.Size = UDim2.fromOffset(width - 52, height - 104)
    text.FontFace = BODY_FONT
    text.RichText = true
    text.TextWrapped = true
    text.TextSize = 29
    text.LineHeight = 1.08
    text.TextColor3 = rgb(236, 232, 220)
    text.TextXAlignment = Enum.TextXAlignment.Left
    text.TextYAlignment = Enum.TextYAlignment.Top
    text.Text = body
    text.Parent = gui
    return gui
end

-- ---------- the Plaza ----------
local function buildOathStone(court)
    local stone = model(court, "OathStone")
    local base = at(P.Plaza.OathStone, P.Plaza.OathYaw)
    -- a three-step round dais
    for index, spec in { { 9.2, 0.6 }, { 7.8, 1.2 }, { 6.4, 1.8 } } do
        column(stone, "DaisStep" .. index, spec[1] * 2, spec[2], base, STONE)
    end
    local top = base * CFrame.new(0, 1.8, 0)
    block(stone, "Plinth", Vector3.new(12.4, 1.4, 5.6), top, STONE_DARK)
    -- the stele: a tall slab, its front toward the bridge's gate; its board on both faces, a cream border behind a slate panel
    local slab = block(stone, "Stele", Vector3.new(11, 21, 3.2), top * CFrame.new(0, 1.4, 0), STONE)
    for index, side in { 1, -1 } do
        local face = top * CFrame.new(0, 1.4 + 10.2, -side * 1.62) * CFrame.Angles(0, if side == 1 then 0 else math.pi, 0)
        part(stone, "BoardBorder" .. index, Vector3.new(9.0, 13.2, 0.16), face * CFrame.new(0, 0, 0.02), plastic(rgb(206, 190, 142)))
        local panel = part(stone, "Board" .. index, Vector3.new(8.4, 12.6, 0.3), face * CFrame.new(0, 0, -0.1), BOARD)
        boardGui(panel, "COURT OF BANNERS", BOARD_BODY)
    end
    -- the roof: two tiled slabs and a ridge, like a hanok's cap on a stele
    local ridge = top * CFrame.new(0, 1.4 + 21.0 + 1.25, 0)
    for _, side in { -1, 1 } do
        part(stone, "RoofSlab", Vector3.new(14.6, 0.9, 4.6), ridge * CFrame.new(0, -0.35, side * 1.95) * CFrame.Angles(side * math.rad(18), 0, 0), TILE)
    end
    part(stone, "RoofRidge", Vector3.new(15.0, 0.9, 1.2), ridge * CFrame.new(0, 0.55, 0), TILE_DARK)
    part(stone, "RoofBeam", Vector3.new(12.6, 0.9, 3.4), ridge * CFrame.new(0, -1.15, 0), TIMBER_DARK)
    slab.Name = "Stele"
    -- one warm light so it reads at night
    local lamp = marker(stone, "StoneLight", top * CFrame.new(0, 12, -3.4), nil)
    WorldBuilder.addLight(lamp, rgb(255, 218, 150), 26, 0.55)
    return stone
end

local function buildBanner(plaza, faction)
    local spot = P.Banners[faction]
    local f = at(spot.Position, spot.Yaw) -- front (-Z) toward the bridge: the cloth shows its face to whoever arrives (it reads from both sides)
    local m = model(plaza, "Banner_" .. faction)
    local height, crossY = 38, 34.5
    column(m, "Pole", 1.0, height, f, { Material = Enum.Material.Wood, Color = rgb(74, 58, 46), Solid = true })
    column(m, "PoleFoot", 2.2, 1.2, f, STONE_DARK)
    part(m, "Crossbar", Vector3.new(10, 0.6, 0.6), f * CFrame.new(0, crossY, 0), { Material = Enum.Material.Wood, Color = rgb(74, 58, 46) })
    if faction == "Orthodox" then
        -- ordered: a blue cloth with white borders and bands, gold at its head and foot and on its finial
        part(m, "Cloth", Vector3.new(8, 21, 0.25), f * CFrame.new(0, crossY - 11, 0), cloth(ORTHODOX.Blue))
        for _, x in { -3.6, 3.6 } do
            part(m, "Border", Vector3.new(0.8, 21, 0.3), f * CFrame.new(x, crossY - 11, 0), cloth(ORTHODOX.Cloth))
        end
        part(m, "Band", Vector3.new(8, 2.4, 0.3), f * CFrame.new(0, crossY - 6, 0), cloth(ORTHODOX.Cloth))
        part(m, "GoldTop", Vector3.new(8.4, 0.7, 0.34), f * CFrame.new(0, crossY - 0.6, 0), plastic(ORTHODOX.Gold))
        part(m, "GoldFoot", Vector3.new(8.4, 0.7, 0.34), f * CFrame.new(0, crossY - 21.4, 0), plastic(ORTHODOX.Gold))
        ball(m, "Finial", 1.6, f * CFrame.new(0, height + 0.8, 0), plastic(ORTHODOX.Gold))
    elseif faction == "Unorthodox" then
        -- patched: a dark jade cloth with a copper and a linen patch, ragged tails of different lengths, a copper ring
        part(m, "Cloth", Vector3.new(8, 15, 0.25), f * CFrame.new(0, crossY - 8, 0), cloth(UNORTHODOX.Jade))
        for index, spec in { { -2.6, 5.0, 17 }, { 0.2, 4.0, 21 }, { 2.9, 3.0, 14.5 } } do
            part(m, "Tail" .. index, Vector3.new(2.5, spec[2] + 3, 0.25), f * CFrame.new(spec[1], crossY - spec[3] - spec[2] / 2 - 0.5, 0), cloth(UNORTHODOX.Jade))
        end
        part(m, "PatchCopper", Vector3.new(3.4, 3.4, 0.32), f * CFrame.new(-1.6, crossY - 4.2, 0), cloth(UNORTHODOX.Copper))
        part(m, "PatchLinen", Vector3.new(2.6, 4.4, 0.32), f * CFrame.new(1.9, crossY - 10, 0), cloth(UNORTHODOX.Linen))
        part(m, "Stitch", Vector3.new(8, 0.35, 0.34), f * CFrame.new(0, crossY - 14.4, 0), cloth(UNORTHODOX.Copper))
        column(m, "Ring", 2.2, 0.5, f * CFrame.new(0, height, 0) * CFrame.Angles(math.pi / 2, 0, 0), plastic(UNORTHODOX.Copper))
    else
        -- fierce: black cloth, a crimson spear-stripe, a split tail, a black fang
        part(m, "Cloth", Vector3.new(8, 19, 0.25), f * CFrame.new(0, crossY - 10, 0), cloth(DEMONIC.Black))
        part(m, "Stripe", Vector3.new(2.4, 19, 0.32), f * CFrame.new(0, crossY - 10, 0), cloth(DEMONIC.Crimson))
        for _, x in { -2.6, 2.6 } do
            part(m, "Tail", Vector3.new(2.6, 5.5, 0.25), f * CFrame.new(x, crossY - 21.7, 0), cloth(DEMONIC.Black))
        end
        part(m, "TailTip", Vector3.new(2.4, 2.6, 0.32), f * CFrame.new(0, crossY - 22.2, 0), cloth(DEMONIC.Crimson))
        part(m, "FangBase", Vector3.new(1.2, 2.6, 1.2), f * CFrame.new(0, height + 1.3, 0), plastic(DEMONIC.Iron))
        part(m, "Fang", Vector3.new(0.5, 3.6, 0.9), f * CFrame.new(0, height + 4.4, 0), { Wedge = true, Material = Enum.Material.SmoothPlastic, Color = DEMONIC.Iron })
    end
    return m
end

local function buildPlaza(root)
    local plaza = folder(root, "Plaza")
    buildOathStone(plaza)
    for _, faction in P.Order do
        buildBanner(plaza, faction)
    end
end

-- ---------- the island's own gate: a Korean post-and-lintel gate, plain timber, a tiled roof, nothing red ----------
local function buildGate(root)
    local gate = model(root, "Gate")
    local f = at(P.Gate.Position, P.Gate.Yaw)
    local half = 23 -- the posts stand either side of the bridge's 40-stud deck
    for _, x in { -half, half } do
        block(gate, "Plinth", Vector3.new(3.8, 1.6, 3.8), f * CFrame.new(x, 0, 0), STONE_DARK)
        column(gate, "Post", 2.4, 14.2, f * CFrame.new(x, 1.6, 0), TIMBER)
    end
    for _, post in gate:GetChildren() do
        if post.Name == "Post" then
            post.CanCollide, post.CanQuery = true, true
        end
    end
    part(gate, "Lintel", Vector3.new(2 * half + 5.6, 1.3, 2.3), f * CFrame.new(0, 14.9, 0), TIMBER)
    part(gate, "TieBeam", Vector3.new(2 * half, 0.9, 1.7), f * CFrame.new(0, 10.6, 0), TIMBER_DARK)
    part(gate, "Frieze", Vector3.new(2 * half, 3.3, 0.7), f * CFrame.new(0, 12.65, 0), TIMBER_DARK) -- (the board the plaques hang on)
    -- the roof: two slabs meeting at a ridge, a ridge cap, and a beam under it (so the sky doesn't show through the eaves)
    local roof = f * CFrame.new(0, 17.5, 0)
    for _, side in { -1, 1 } do
        part(gate, "RoofSlab", Vector3.new(2 * half + 9, 1.0, 6.4), roof * CFrame.new(0, 0.3, side * 2.9) * CFrame.Angles(side * math.rad(17), 0, 0), TILE)
    end
    part(gate, "RoofRidge", Vector3.new(2 * half + 9.6, 1.0, 1.4), roof * CFrame.new(0, 1.55, 0), TILE_DARK)
    part(gate, "RoofBeam", Vector3.new(2 * half + 3, 1.0, 3.4), roof * CFrame.new(0, -0.9, 0), TIMBER_DARK)
    for _, side in { -1, 1 } do
        -- the plaque: the island's name, on each face
        local face = f * CFrame.new(0, 12.7, side * 0.5) * CFrame.Angles(0, if side == 1 then math.pi else 0, 0)
        local panel = part(gate, "Plaque", Vector3.new(15, 2.6, 0.3), face, BOARD)
        local gui = Instance.new("SurfaceGui")
        gui.Name = "PlaqueText"
        gui.Face = Enum.NormalId.Front
        gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
        gui.PixelsPerStud = 50
        gui.LightInfluence = 0.25
        gui.MaxDistance = 140
        gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
        gui.Parent = panel
        local label = Instance.new("TextLabel")
        label.BackgroundTransparency = 1
        label.Size = UDim2.fromScale(1, 1)
        label.FontFace = HEAD_FONT
        label.TextScaled = true
        label.TextColor3 = rgb(244, 214, 138)
        label.Text = "MURIM CROSSING"
        label.Parent = gui
        local pad = Instance.new("UIPadding")
        pad.PaddingTop, pad.PaddingBottom = UDim.new(0.14, 0), UDim.new(0.14, 0)
        pad.Parent = label
    end
    return gate
end

-- ---------- each stairway, its gate at the top and its flags ----------
-- (a gate's frame: its front (-Z) faces down the stairs, +Z runs up them, X across; k widens the gate for the 32-stud stairway)
local function orthodoxGate(m, f, k)
    local h = 8.4 * k
    for _, x in { -h, h } do
        block(m, "Plinth", Vector3.new(3.6, 1.0, 3.6), f * CFrame.new(x, 0, 0), { Material = Enum.Material.Marble, Color = ORTHODOX.Stone, Solid = true })
        block(m, "Pillar", Vector3.new(2.2, 12, 2.2), f * CFrame.new(x, 1, 0), { Material = Enum.Material.Marble, Color = ORTHODOX.Stone, Solid = true })
        block(m, "Cap", Vector3.new(2.9, 0.7, 2.9), f * CFrame.new(x, 13, 0), plastic(ORTHODOX.Gold))
        -- a norigae tassel: a gold knot and a blue ribbon, hanging at each end of the band
        ball(m, "Knot", 0.8, f * CFrame.new(x * 0.7, 9.9, -1.1), plastic(ORTHODOX.Gold))
        part(m, "Ribbon", Vector3.new(0.5, 3.4, 0.16), f * CFrame.new(x * 0.7, 8.0, -1.1), cloth(ORTHODOX.Blue))
    end
    part(m, "Lintel", Vector3.new(2 * h + 4.6, 1.2, 1.9), f * CFrame.new(0, 12.6, 0), { Material = Enum.Material.Marble, Color = ORTHODOX.Stone })
    part(m, "Band", Vector3.new(2 * h + 1.0, 0.6, 2.05), f * CFrame.new(0, 11.4, 0), plastic(ORTHODOX.Blue))
    part(m, "GoldLine", Vector3.new(2 * h + 4.8, 0.3, 2.1), f * CFrame.new(0, 13.3, 0), plastic(ORTHODOX.Gold))
end

local function unorthodoxGate(m, f, k)
    local wood = { Material = Enum.Material.Wood, Color = UNORTHODOX.Wood }
    -- two posts of different height, each leaning a little, a crossbeam lashed between them at a slant
    local left = f * CFrame.new(-9.0 * k, 0, 0) * CFrame.Angles(0, 0, math.rad(2.5))
    local right = f * CFrame.new(9.0 * k, 0, 0.4) * CFrame.Angles(0, 0, math.rad(-3.5))
    local lp = column(m, "PostLeft", 1.6, 11.2, left, wood)
    local rp = column(m, "PostRight", 1.4, 8.8, right, wood)
    lp.CanCollide, lp.CanQuery, rp.CanCollide, rp.CanQuery = true, true, true, true
    column(m, "BandLeft", 1.95, 0.5, left * CFrame.new(0, 4.0, 0), plastic(UNORTHODOX.Copper))
    column(m, "BandRight", 1.75, 0.5, right * CFrame.new(0, 3.2, 0), plastic(UNORTHODOX.Copper))
    local span = 8.8 * k
    local from, to = f * Vector3.new(-span, 9.4, 0), f * Vector3.new(span, 7.6, 0.3)
    local beam = part(m, "Crossbeam", Vector3.new((to - from).Magnitude + 1.6, 0.95, 0.95), CFrame.lookAt((from + to) / 2, to) * CFrame.Angles(0, math.pi / 2, 0), wood)
    beam.Shape = Enum.PartType.Cylinder
    local function beamY(x)
        return 9.4 + (7.6 - 9.4) * ((x + span) / (2 * span))
    end
    -- cloth scraps hung from it
    local scraps = { { -0.75, 3.2, UNORTHODOX.Jade }, { -0.4, 4.6, UNORTHODOX.Linen }, { -0.02, 2.6, UNORTHODOX.Copper }, { 0.34, 3.8, UNORTHODOX.Jade }, { 0.7, 2.4, UNORTHODOX.Linen } }
    for index, s in scraps do
        local x = s[1] * span
        part(m, "Scrap" .. index, Vector3.new(1.5 + (index % 3) * 0.35, s[2], 0.18), f * CFrame.new(x, beamY(x) - 0.5 - s[2] / 2, 0.15), cloth(s[3]))
    end
    -- two paper lanterns, each on a cord from the beam, each with a warm light (they mark the road in)
    for index, spec in { { -0.52, 6.2 }, { 0.48, 4.4 } } do
        local x = spec[1] * span
        local y = beamY(x)
        part(m, "Cord" .. index, Vector3.new(0.14, y - spec[2] - 1.0, 0.14), f * CFrame.new(x, (y + spec[2] + 1.0) / 2, -0.5), plastic(UNORTHODOX.Wood))
        local lantern = column(m, "Lantern" .. index, 2.0, 2.4, f * CFrame.new(x, spec[2] - 1.2, -0.5), PAPER)
        WorldBuilder.addLight(lantern, rgb(190, 255, 200), 20, 0.5)
        for _, dy in { -1.2, 1.0 } do -- (a dark wooden cap and foot: it reads as a lantern, not a drum)
            column(m, "LanternCap" .. index, 2.2, 0.2, f * CFrame.new(x, spec[2] + dy, -0.5), TIMBER_DARK)
        end
    end
end

-- a lit crimson brazier standing on `base` (the middle of its foot): a basalt stand, an iron bowl, a flame and one light
local function brazier(m, base)
    column(m, "BrazierStand", 1.5, 2.2, base, { Material = Enum.Material.Basalt, Color = rgb(36, 34, 42), Solid = true })
    local bowl = column(m, "BrazierBowl", 3.2, 1.0, base * CFrame.new(0, 2.2, 0), { Material = Enum.Material.Metal, Color = DEMONIC.Iron, Solid = true })
    local fire = Instance.new("Fire")
    fire.Size, fire.Heat = 5.5, 6
    fire.Color, fire.SecondaryColor = rgb(255, 70, 46), rgb(255, 160, 50)
    fire.Parent = bowl
    WorldBuilder.addLight(bowl, rgb(255, 60, 40), 22, 0.9)
end

local function demonicGate(m, f, k)
    local h = 8.2 * k
    -- two black fangs, stepped to a point and leaning toward each other, on basalt feet
    for _, side in { -1, 1 } do
        local foot = f * CFrame.new(side * h, 0, 0)
        block(m, "Foot", Vector3.new(4.4, 1.6, 4.4), foot, { Material = Enum.Material.Basalt, Color = rgb(34, 32, 40), Solid = true })
        local lean = foot * CFrame.new(0, 1.6, 0) * CFrame.Angles(0, 0, side * math.rad(6)) -- (its tip toward the gate's middle)
        local steps = { { 2.8, 6.0 }, { 2.0, 5.0 }, { 1.3, 4.0 }, { 0.7, 3.0 } }
        local y = 0
        for index, s in steps do
            block(m, "Fang" .. index, Vector3.new(s[1], s[2], s[1]), lean * CFrame.new(0, y, 0), { Material = Enum.Material.Basalt, Color = DEMONIC.Iron, Solid = index == 1 })
            y += s[2] - 0.2
        end
        part(m, "Fangtip", Vector3.new(0.5, 2.4, 0.5), lean * CFrame.new(0, y + 1.0, 0), { Material = Enum.Material.Basalt, Color = DEMONIC.Iron })
        -- a brazier at its foot, lit crimson
        brazier(m, f * CFrame.new(side * h, 0, -4.4))
    end
    -- a crimson cloth slung between the fangs, sagging in the middle
    local w = h * 0.68
    part(m, "SlungLeft", Vector3.new(w, 2.2, 0.22), f * CFrame.new(-h * 0.68, 14.0, 0) * CFrame.Angles(0, 0, math.rad(-9)), cloth(DEMONIC.Crimson))
    part(m, "SlungMiddle", Vector3.new(h * 0.7, 2.2, 0.22), f * CFrame.new(0, 13.2, 0), cloth(DEMONIC.Crimson))
    part(m, "SlungRight", Vector3.new(w, 2.2, 0.22), f * CFrame.new(h * 0.68, 14.0, 0) * CFrame.Angles(0, 0, math.rad(9)), cloth(DEMONIC.Crimson))
end

-- a pair of flags on poles, one each side
local function flags(m, f, faction, half)
    for index, side in { -1, 1 } do
        local base = f * CFrame.new(side * half, 0, 0)
        if faction == "Orthodox" then
            column(m, "FlagPole", 0.6, 15, base, { Material = Enum.Material.Metal, Color = ORTHODOX.Gold, Solid = true })
            part(m, "Flag", Vector3.new(3.6, 8.5, 0.2), base * CFrame.new(side * -1.9, 10.5, 0), cloth(ORTHODOX.Blue))
            part(m, "FlagEdge", Vector3.new(3.6, 0.8, 0.26), base * CFrame.new(side * -1.9, 14.4, 0), cloth(ORTHODOX.Cloth))
            part(m, "FlagEdge", Vector3.new(3.6, 0.8, 0.26), base * CFrame.new(side * -1.9, 6.6, 0), cloth(ORTHODOX.Cloth))
            ball(m, "Finial", 1.0, base * CFrame.new(0, 15.4, 0), plastic(ORTHODOX.Gold))
        elseif faction == "Unorthodox" then
            local h = if index == 1 then 13.5 else 11.2
            column(m, "FlagPole", 0.7, h, base * CFrame.Angles(0, 0, math.rad(side * 3)), { Material = Enum.Material.Wood, Color = UNORTHODOX.Wood, Solid = true })
            part(m, "Pennant", Vector3.new(4.2, 2.6, 0.18), base * CFrame.new(side * -2.3, h - 2.2, 0), cloth(if index == 1 then UNORTHODOX.Jade else UNORTHODOX.Copper))
            part(m, "Pennant", Vector3.new(2.6, 1.7, 0.18), base * CFrame.new(side * -1.7, h - 4.4, 0), cloth(UNORTHODOX.Linen))
        else
            column(m, "FlagPole", 0.6, 15, base, { Material = Enum.Material.Metal, Color = DEMONIC.Iron, Solid = true })
            part(m, "Flag", Vector3.new(3.4, 9.5, 0.2), base * CFrame.new(side * -1.8, 9.6, 0), cloth(DEMONIC.Black))
            part(m, "FlagStripe", Vector3.new(1.1, 9.5, 0.26), base * CFrame.new(side * -1.8, 9.6, 0), cloth(DEMONIC.Crimson))
            part(m, "Spike", Vector3.new(0.4, 2.6, 0.9), base * CFrame.new(0, 16.3, 0), { Wedge = true, Material = Enum.Material.Metal, Color = DEMONIC.Iron })
        end
    end
end

-- what each stairway is built of
local STAIR_LOOK = {
    Orthodox = { Step = { Material = Enum.Material.Marble, Color = rgb(234, 236, 242), Solid = true },
        Wall = { Material = Enum.Material.Marble, Color = rgb(226, 228, 236), Solid = true }, Cap = plastic(ORTHODOX.Gold) },
    Unorthodox = { Step = { Material = Enum.Material.Slate, Color = rgb(58, 80, 72), Solid = true },
        Wall = { Material = Enum.Material.Wood, Color = rgb(64, 58, 44), Solid = true }, Cap = plastic(UNORTHODOX.Copper) },
    Demonic = { Step = { Material = Enum.Material.Basalt, Color = rgb(42, 40, 48), Solid = true },
        Wall = { Material = Enum.Material.Basalt, Color = rgb(30, 28, 34), Solid = true }, Cap = { Material = Enum.Material.Neon, Color = rgb(196, 20, 30), Shadow = false } },
}

local function buildStairs(root)
    local stairs = folder(root, "Stairs")
    for _, faction in P.Order do
        local st, pad = P.Stairs[faction], P.Pads[faction]
        local look = STAIR_LOOK[faction]
        local m = model(stairs, "Stairs_" .. faction)
        local side = Vector3.new(st.Axis.Z, 0, -st.Axis.X) -- across the axis: to the climber's right
        local function localPoint(s, u, h)
            return st.Axis * s + side * u + Vector3.new(0, h, 0)
        end
        for _, tier in st.Tiers do
            local kind, s0, s1, h0, h1 = tier[1], tier[2], tier[3], tier[4], tier[5]
            if kind == "flight" then
                local n = math.floor((h1 - h0) / P.StepRise + 0.5)
                local tread = (s1 - s0) / n
                for i = 0, n - 1 do
                    local top = h0 + (i + 1) * P.StepRise
                    part(m, "Step", Vector3.new(st.Width, 4.0, tread + 0.02), at(localPoint(s0 + (i + 0.5) * tread, 0, top - 2.0), st.Yaw), look.Step)
                end
                -- a wall along each side that follows the slope, a cap on it (a rail you can see from the plaza)
                for _, u in { -(st.Width / 2 + 0.7), st.Width / 2 + 0.7 } do
                    local a = at(localPoint(s0, u, h0 + 0.2 + 1.0), 0).Position
                    local b = at(localPoint(s1, u, h1 + 1.0), 0).Position
                    local mid = CFrame.lookAt((a + b) / 2, b)
                    part(m, "Wall", Vector3.new(1.4, 2.2, (b - a).Magnitude + 0.4), mid, look.Wall)
                    part(m, "WallCap", Vector3.new(1.8, 0.35, (b - a).Magnitude + 0.5), mid * CFrame.new(0, 1.25, 0), look.Cap)
                end
            end
        end
        -- its gate at the top, facing down the stairs
        local gate = model(m, "Gate_" .. faction)
        local f = at(pad.Gate.Position, pad.FrontYaw)
        if faction == "Orthodox" then
            orthodoxGate(gate, f, 1.5)
        elseif faction == "Unorthodox" then
            unorthodoxGate(gate, f, 1.4)
        else
            demonicGate(gate, f, 1.45)
        end
        -- its headquarters' name over the gate, in plain words
        local info = GameConfig.Faction.Factions[faction]
        local post = marker(gate, "Sign", f * CFrame.new(0, 19, 0), nil)
        local sign = Instance.new("BillboardGui")
        sign.Name = "Sign"
        sign.Size = UDim2.fromOffset(300, 68)
        sign.MaxDistance = 220
        sign.LightInfluence = 0
        sign.Parent = post
        local label = Instance.new("TextLabel")
        label.Size = UDim2.fromScale(1, 1)
        label.BackgroundTransparency = 1
        label.FontFace = HEAD_FONT
        label.RichText = true
        label.TextSize = 32
        label.TextColor3 = rgb(240, 236, 224)
        label.TextStrokeTransparency = 0.4
        label.Text = '<font color="' .. hex(info.Color) .. '">' .. info.Hq .. "</font>\n" .. '<font size="18">' .. info.DisplayName .. "</font>"
        label.Parent = sign
        -- a pair of flags on the first landing
        local landing
        for _, tier in st.Tiers do
            if tier[1] == "landing" then
                landing = landing or tier
            end
        end
        if landing then
            local flagModel = model(stairs, "Flags_" .. faction)
            local s = (landing[2] + landing[3]) / 2
            local lf = at(localPoint(s, 0, landing[4]), pad.FrontYaw)
            flags(flagModel, lf, faction, st.LandingWidth / 2 - 4)
            if faction == "Demonic" then -- the ominous red light: two braziers where the flight breaks
                for _, side_ in { -1, 1 } do
                    brazier(flagModel, lf * CFrame.new(side_ * 13, 0, 0))
                end
            end
        end
    end
end

-- ---------- the representatives ----------
local REPS = {
    Orthodox = { Rig = "MasterHwaRin", Head = rgb(246, 214, 184), Coat = rgb(236, 240, 248), Legs = rgb(30, 56, 140), Accent = ORTHODOX.Gold, Hair = rgb(30, 28, 34) },
    Unorthodox = { Rig = "ElderKangDal", Head = rgb(214, 168, 130), Coat = rgb(30, 96, 80), Legs = rgb(50, 56, 48), Accent = UNORTHODOX.Copper, Hair = rgb(214, 214, 214) },
    Demonic = { Rig = "LordMuYeong", Head = rgb(232, 196, 170), Coat = rgb(30, 26, 34), Legs = rgb(22, 20, 26), Accent = DEMONIC.Crimson, Hair = rgb(16, 14, 18) },
}

-- Something worn: welded to a body part (the way the hub people's kit is), light and unable to collide.
local function wear(rig, bodyName, name, size, offset, look)
    local body = rig:FindFirstChild(bodyName)
    assert(body, "R15 body part " .. bodyName .. " is missing")
    local p = part(rig, name, size, body.CFrame * offset, look)
    p.Anchored = false
    p.Massless = true
    p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = body
    weld.Part1 = p
    weld.Parent = p
    return p
end

-- The faces the hub's people already have (assets/npcs/HubNpcs.fbx, stored in WorldAssets.NpcAssets): each representative wears the eyes, brows
-- and mouth of one of them (the hub's kit is reused, not remade; their hair, beards and robes are plain parts for now). Where the kit
-- isn't stored, the stock face stays.
local FACES = {
    Orthodox = { Owner = "Curator", Pieces = { "Brows", "EyeWhites", "EyeShine", "Pupils", "Mouth", "Lashes", "Blush" } },
    Unorthodox = { Owner = "Forgemaster", Pieces = { "Brows", "EyeWhites", "EyeShine", "Pupils", "Nose" } },
    Demonic = { Owner = "Appraiser", Pieces = { "Brows", "EyeWhites", "EyeShine", "Pupils", "Mouth", "Nose" } },
}

local function wearFace(rig, spec, hairColour)
    local kit = WorldBuilder.kitFolder("HubNpcs")
    if not kit then
        return 0
    end
    local data = WorldBuilder.npcData()
    local wanted = {}
    for _, piece in spec.Pieces do
        wanted[spec.Owner .. "_" .. piece] = true
    end
    local count = 0
    for _, template in kit:GetChildren() do
        local base = WorldBuilder.splitName(template.Name)
        if template:IsA("MeshPart") and wanted[base] then
            local bodyPart = rig:FindFirstChild(data.Pieces[base] or "")
            if bodyPart then
                -- (the kit's pieces are authored in the person's root frame, which for every one of them is the same R15 body)
                WorldBuilder.dressPiece(template, data, spec.Owner, rig.HumanoidRootPart.CFrame, rig, bodyPart)
                count += 1
            end
        end
    end
    if count > 0 then
        rig.Head.TextureID = "" -- the stock face: this one wears the modelled face
        for _, piece in rig:GetChildren() do
            if piece:IsA("MeshPart") and string.find(piece.Name, "_Brows__", 1, true) then
                piece.Color = hairColour -- (the borrowed brows take this person's own hair colour)
            end
        end
    end
    return count
end

local function buildRep(parent, faction)
    local info = GameConfig.Faction.Factions[faction]
    local look = REPS[faction]
    local spot = P.Reps[faction]
    local description = Instance.new("HumanoidDescription")
    description.HeadColor = look.Head
    description.TorsoColor, description.LeftArmColor, description.RightArmColor = look.Coat, look.Coat, look.Coat
    description.LeftLegColor, description.RightLegColor = look.Legs, look.Legs
    local rig = Players:CreateHumanoidModelFromDescription(description, Enum.HumanoidRigType.R15)
    rig.Name = look.Rig
    rig:PivotTo(at(spot.Position + Vector3.new(0, 3, 0), spot.Yaw))
    rig.HumanoidRootPart.Anchored = true
    -- plain dress, for now: a long coat skirt, a sash and plain hair (the faction robes come later)
    -- (the R15 head shows about 1 stud across, the torso 1.9)
    wear(rig, "LowerTorso", "Skirt", Vector3.new(2.3, 2.8, 1.3), CFrame.new(0, -1.25, 0), cloth(look.Coat))
    wear(rig, "LowerTorso", "Sash", Vector3.new(2.1, 0.45, 1.1), CFrame.new(0, 0.05, 0), cloth(look.Accent))
    wear(rig, "Head", "Hair", Vector3.new(1.06, 0.44, 1.06), CFrame.new(0, 0.48, 0.03), plastic(look.Hair))
    if faction == "Orthodox" then
        wear(rig, "Head", "Topknot", Vector3.new(0.48, 0.48, 0.48), CFrame.new(0, 0.86, 0.03), { Shape = Enum.PartType.Ball, Material = Enum.Material.SmoothPlastic, Color = look.Hair })
    elseif faction == "Unorthodox" then
        wear(rig, "Head", "Beard", Vector3.new(0.78, 0.62, 0.26), CFrame.new(0, -0.44, -0.5), plastic(rgb(226, 226, 226)))
    else
        wear(rig, "Head", "LongHair", Vector3.new(1.08, 2.6, 0.24), CFrame.new(0, -0.85, 0.52), plastic(look.Hair))
        wear(rig, "UpperTorso", "Cape", Vector3.new(2.1, 3.0, 0.15), CFrame.new(0, -0.7, 0.58), cloth(rgb(18, 16, 22)))
        wear(rig, "UpperTorso", "CapeHem", Vector3.new(2.1, 0.4, 0.18), CFrame.new(0, -2.1, 0.58), cloth(DEMONIC.Crimson))
    end
    wearFace(rig, FACES[faction], look.Hair)
    for _, descendant in rig:GetDescendants() do
        if descendant:IsA("BasePart") then
            descendant.CanTouch = false
        end
    end
    local humanoid = rig:FindFirstChildOfClass("Humanoid")
    humanoid.DisplayName = info.Master
    humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
    humanoid.NameDisplayDistance = 45
    humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
    rig.PrimaryPart = rig.HumanoidRootPart
    rig.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
    rig:SetAttribute("Faction", faction)
    CollectionService:AddTag(rig, REP_TAG)
    CollectionService:AddTag(rig, "HubNpc") -- (NpcService plays the standard idle)
    -- the dialog's prompt: F, as every other prompt (E is cultivation)
    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Talk"
    prompt.ObjectText = info.Master
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt:SetAttribute("FactionTalk", true)
    prompt:SetAttribute("Faction", faction)
    prompt.Parent = rig.HumanoidRootPart
    rig.Parent = parent
    return rig
end

local function buildReps(root)
    local npcs = folder(root, "Npcs")
    for _, faction in P.Order do
        buildRep(npcs, faction)
    end
end

-- ---------- the pads: empty, with their markers ----------
local function buildPads(root)
    for _, faction in P.Order do
        local pad = P.Pads[faction]
        local f = folder(root, faction .. "Pad")
        f:SetAttribute("Faction", faction)
        f:SetAttribute("FlatRadius", pad.FlatRadius)
        f:SetAttribute("EdgeRadius", pad.EdgeRadius)
        f:SetAttribute("Front", pad.Front)
        f:SetAttribute("Hq", GameConfig.Faction.Factions[faction].Hq)
        marker(f, "Centre", at(pad.Centre, pad.FrontYaw), { Faction = faction, Role = "Centre" })
        for _, key in { "Gate", "MainHall", "Vault", "Checkpoint" } do
            marker(f, key, at(pad[key].Position, pad[key].Yaw), { Faction = faction, Role = key })
        end
        for index, point in pad.TrialGates or {} do
            marker(f, "TrialGate" .. index, at(point, pad.Gate.Yaw), { Faction = faction, Role = "TrialGate", Order = index })
        end
        for index, point in pad.TrialTokenSpots or {} do
            marker(f, "TrialToken" .. index, at(point, 0), { Faction = faction, Role = "TrialToken", Order = index })
        end
        if pad.TrialArena then
            marker(f, "TrialArena", at(pad.TrialArena, pad.FrontYaw), { Faction = faction, Role = "TrialArena" })
        end
        for index, point in pad.TrialWaves or {} do
            marker(f, "TrialWave" .. index, at(point, 0), { Faction = faction, Role = "TrialWave", Order = index })
        end
    end
end

-- ---------- the Unorthodox side's rope and timber bridges ----------
local ROPE = { Material = Enum.Material.Fabric, Color = rgb(150, 124, 86), Shadow = false }

local function buildRopeBridges(root)
    local bridges = folder(root, "RopeBridges")
    for index, br in P.RopeBridges do
        local m = model(bridges, "RopeBridge" .. index)
        local aw, bw = at(br.From, 0).Position, at(br.To, 0).Position
        local length = (bw - aw).Magnitude
        local dir = (bw - aw).Unit
        local side = dir:Cross(Vector3.yAxis).Unit
        local count = math.max(4, math.floor(length / 2))
        local function sagAt(t)
            return -2.4 * 4 * t * (1 - t)
        end
        for i = 0, count - 1 do
            local t = (i + 0.5) / count
            local pos = aw:Lerp(bw, t) + Vector3.new(0, sagAt(t) - 0.25, 0)
            part(m, "Plank", Vector3.new(5.2, 0.4, length / count * 0.82), CFrame.lookAt(pos, pos + dir), { Material = Enum.Material.WoodPlanks, Color = rgb(112, 92, 66), Solid = true })
        end
        for _, u in { -2.5, 2.5 } do -- a rope each side, hung from posts, a little over a stud above the planks
            local previous
            for i = 0, 6 do
                local t = i / 6
                local point = aw:Lerp(bw, t) + side * u + Vector3.new(0, sagAt(t) + 3.0, 0)
                if previous then
                    local len = (point - previous).Magnitude
                    local rope = part(m, "Rope", Vector3.new(len, 0.35, 0.35), CFrame.lookAt((point + previous) / 2, point) * CFrame.Angles(0, math.pi / 2, 0), ROPE)
                    rope.Shape = Enum.PartType.Cylinder
                end
                previous = point
            end
            for _, end_ in { aw, bw } do -- (a post at each end of each rope)
                local base = CFrame.new(end_ + side * u + Vector3.new(0, -0.6, 0))
                column(m, "Post", 0.9, 4.6, base, { Material = Enum.Material.Wood, Color = rgb(70, 58, 44), Solid = true })
            end
        end
    end
end

-- ---------- where a fall returns to ----------
local ROUTE_DEPTH = 100 -- the zones reach this far under the ground: a falling player brushes the cliffs under the island on the way down, and must still count as
                        -- "on the route" (a player who last stood outside every zone is only returned by the 110-stud rule, which lets them fall twice as far)

local function zone(zones, name, size, cframe, returnTo)
    local z = WorldBuilder.marker(name, size, cframe, zones)
    z.Material = Enum.Material.Plastic
    z.CanQuery = true -- WorldService finds it with an overlap query
    if returnTo then
        z:SetAttribute("ReturnTo", returnTo)
    end
    return z
end

local function buildApproach(root)
    local approach = folder(root, "Approach")
    local zones = folder(approach, "Zones")
    -- a Route zone over ground: `cframe` is at the ground's level (the box runs ROUTE_DEPTH under it and 8 over), `low`/`high` stretch it for a slope
    local function route(size, cframe, low, high)
        low, high = low or 0, high or 0
        local height = 8 + ROUTE_DEPTH + (high - low)
        return zone(zones, "Route", Vector3.new(size.X, height, size.Z), cframe + Vector3.new(0, low - ROUTE_DEPTH + height / 2, 0))
    end
    local function check(label, size, cframe, returnTo)
        local z = zone(zones, "Check", size, cframe + Vector3.new(0, 4, 0), returnTo)
        z:SetAttribute("Name", label)
        return z
    end
    -- the bridge: one long box over its whole span (it arches about 6 studs), a check at its hub end
    local nodes = BridgePlacements.Bridges[ROUTE].Nodes
    local from, to = nodes[1].Position, nodes[#nodes].Position
    local run = (to - from) * Vector3.new(1, 0, 1)
    local along = run.Unit
    local centre = (from + to) / 2 + Vector3.new(0, 7, 0)
    zone(zones, "Route", Vector3.new(BridgePlacements.DeckWidth + 4, 16, run.Magnitude + 4), CFrame.lookAt(centre, centre + along))
    local hubSpot = from - along * 5
    check("HubStart", Vector3.new(24, 10, 20), CFrame.lookAt(hubSpot, hubSpot + along), CFrame.lookAt(hubSpot - along * 3, hubSpot + along) + Vector3.new(0, 0.2, 0))
    -- the island's gate, the plaza
    local gate = P.Gate.Position
    route(Vector3.new(P.Spur.Half * 2 + 6, 0, P.Spur.ToZ - P.Spur.FromZ + 8), at(Vector3.new(0, 0, (P.Spur.FromZ + P.Spur.ToZ) / 2), 0))
    check("Gate", Vector3.new(30, 10, 24), at(Vector3.new(0, 0, gate.Z + 8), 0), at(Vector3.new(0, 0, gate.Z + 8), math.pi) + Vector3.new(0, 0.2, 0))
    local R = P.Plaza.Radius
    for _, turn in { 0, math.pi / 3, 2 * math.pi / 3 } do
        route(Vector3.new(2 * R, 0, 2 * R / math.cos(math.pi / 6)), at(Vector3.zero, turn))
    end
    check("Plaza", Vector3.new(70, 10, 70), at(Vector3.zero, 0), at(P.Checkpoint.Position, P.Checkpoint.Yaw) + Vector3.new(0, 0.2, 0))
    -- each stairway (a box per tier, as high as the tier is), its pad and its gate's check
    for _, faction in P.Order do
        local st, pad = P.Stairs[faction], P.Pads[faction]
        for _, tier in st.Tiers do
            local kind, s0, s1, h0, h1 = tier[1], tier[2], tier[3], tier[4], tier[5]
            local mid = st.Axis * ((s0 + s1) / 2)
            local width = (if kind == "flight" then st.Width else st.LandingWidth) + 8
            route(Vector3.new(width, 0, s1 - s0), at(Vector3.new(mid.X, h0, mid.Z), st.Yaw), 0, h1 - h0)
        end
        route(Vector3.new(pad.EdgeRadius * 2, 0, pad.EdgeRadius * 2), at(pad.Centre, 0))
        route(Vector3.new(pad.EdgeRadius * 2, 0, pad.EdgeRadius * 2), at(pad.Centre, math.pi / 4))
        local back = at(pad.Gate.Position, pad.Gate.Yaw) + Vector3.new(0, 0.2, 0)
        check(faction .. "Pad", Vector3.new(30, 10, 30), at(pad.Gate.Position, pad.Gate.Yaw), back)
    end
    -- the Unorthodox side's hidden paths and lookouts: a box along each stretch of path and on each nook, and a check at the first landing's far end
    local paths = P.Paths
    for _, knots in paths do
        for index = 1, #knots - 1 do
            local a, b = knots[index], knots[index + 1]
            local mid = (a + b) / 2
            local len = (Vector3.new(b.X, 0, b.Z) - Vector3.new(a.X, 0, a.Z)).Magnitude
            local yaw = math.atan2(-(b.X - a.X), -(b.Z - a.Z))
            route(Vector3.new(12, 0, len + 4), at(Vector3.new(mid.X, math.min(a.Y, b.Y), mid.Z), yaw), 0, math.abs(b.Y - a.Y))
        end
    end
    for _, nook in P.Nooks do
        route(Vector3.new(20, 0, 20), at(nook, 0))
    end
    for _, br in P.RopeBridges do
        local mid = (br.From + br.To) / 2
        local len = (Vector3.new(br.To.X, 0, br.To.Z) - Vector3.new(br.From.X, 0, br.From.Z)).Magnitude
        local yaw = math.atan2(-(br.To.X - br.From.X), -(br.To.Z - br.From.Z))
        route(Vector3.new(10, 0, len + 6), at(Vector3.new(mid.X, math.min(br.From.Y, br.To.Y) - 3, mid.Z), yaw), 0, math.abs(br.To.Y - br.From.Y) + 6)
    end
    do
        local landing = P.Stairs.Unorthodox
        for _, tier in landing.Tiers do
            if tier[1] == "landing" and tier[4] == 24 then
                local spot = landing.Axis * ((tier[2] + tier[3]) / 2)
                local back = at(Vector3.new(spot.X, tier[4], spot.Z), landing.Yaw) + Vector3.new(0, 0.2, 0)
                check("UnorthodoxLanding", Vector3.new(24, 10, 24), at(Vector3.new(spot.X, tier[4], spot.Z), 0), back)
            end
        end
    end
    -- the place a fall from anywhere on the island lands (the 110-stud rule returns here)
    local spot = marker(root, "Checkpoint", at(P.Checkpoint.Position, P.Checkpoint.Yaw), nil)
    spot.Size = Vector3.new(4, 1, 4)
    return #zones:GetChildren()
end

-- ---------- the mountains' dressing: trees, rocks, waterfalls, the moon ----------
-- Reused for now (the Unorthodox and Demonic territories get their own libraries later): the Jade Grove's trees on the Unorthodox side, the Ember
-- Peak's basalt clusters and shards on the Demonic, the place's own waterfall (WorldBuilder.buildWaterfall). The Orthodox side's borrowed Blossom Sanctuary
-- trees are gone (2026-11-22): Dawnspire plants its own (DawnspireBuilder). A piece whose kit isn't stored is left out (the build still runs).
local JADE = { "JG_AncientTreeA", "JG_AncientTreeB", "JG_BambooClump", "JG_AncientTreeB", "JG_AncientTreeA", "JG_Fern", "JG_BambooClump" }
local EMBER = { "EP_BasaltClusterA", "EP_BasaltClusterB", "EP_ObsidianShard", "EP_BasaltStep", "EP_PetrifiedTreeA", "EP_ObsidianShard", "EP_PetrifiedTreeB", "EP_BasaltClusterA" }

local function place(parent, kit, names, list, scaleFrom, scaleTo, sink)
    local placed = 0
    for index, entry in list do
        local name = names[(index - 1) % #names + 1]
        if WorldBuilder.hasTemplate(kit, name) then
            local scale = scaleFrom + (scaleTo - scaleFrom) * (((index * 37) % 10) / 9)
            WorldBuilder.placeTemplate(kit, name, at(entry[1] - Vector3.new(0, sink, 0), entry[2]), parent, scale)
            placed += 1
        end
    end
    return placed
end

local function buildDress(root)
    local dress = folder(root, "Dress")
    local counts = {}
    counts.Jade = place(folder(dress, "Forest"), "JadeGrove", JADE, P.Dress.TreesU, 0.9, 1.35, 0.3)
    counts.Ember = place(folder(dress, "Basalt"), "EmberPeak", EMBER, P.Dress.RocksD, 1.8, 3.0, 0.5)
    -- waterfalls: where a mesa's rim faces the plaza
    local falls = folder(dress, "Waterfalls")
    for index, fall in P.Falls do
        WorldBuilder.buildWaterfall(falls, at(fall.Lip, 0).Position, at(fall.From, 0).Position, WorldBuilder.Falls.Water)
        counts.Falls = (counts.Falls or 0) + 1
    end
    -- the blood moon: a big Neon ball far behind the Demonic mountains, tied to the island (a part in its model: it lights nothing, and it
    -- touches neither the sky nor Lighting for anyone)
    local moon = P.Moon
    ball(dress, "BloodMoon", moon.Radius * 2, at(moon.Position, 0), { Material = Enum.Material.Neon, Color = rgb(112, 4, 12), Shadow = false })
    counts.Moon = 1
    return counts
end

-- ---------- the hub's end of the bridge ----------
-- Where cobblestone should lie under the apron (the hub's grass would grow through it): the columns of a rectangle (world X/Z) turned to
-- face `along`, from `back` studs behind `from` to `front` ahead of it, `half` studs each side. Only Grass and Ground become Cobblestone,
-- with every occupancy kept as it is (it reads each voxel and writes it back: running it again changes nothing).
local function paintCobble(from, along, back, front, half)
    local terrain = workspace.Terrain
    local side = Vector3.new(-along.Z, 0, along.X)
    local corners = {}
    for _, a in { -back, front } do
        for _, s in { -half, half } do
            table.insert(corners, from + along * a + side * s)
        end
    end
    local minX, minZ, maxX, maxZ = math.huge, math.huge, -math.huge, -math.huge
    for _, c in corners do
        minX, maxX, minZ, maxZ = math.min(minX, c.X), math.max(maxX, c.X), math.min(minZ, c.Z), math.max(maxZ, c.Z)
    end
    local x0, z0 = math.floor(minX / VOXEL) * VOXEL, math.floor(minZ / VOXEL) * VOXEL
    local n, m = math.ceil((maxX - x0) / VOXEL), math.ceil((maxZ - z0) / VOXEL)
    local y0 = from.Y - 24
    local layers = 8
    local region = Region3.new(Vector3.new(x0, y0, z0), Vector3.new(x0 + n * VOXEL, y0 + layers * VOXEL, z0 + m * VOXEL))
    local mats, occs = terrain:ReadVoxels(region, VOXEL)
    local changed = 0
    for i = 1, n do
        for k = 1, m do
            local p = Vector3.new(x0 + (i - 0.5) * VOXEL - from.X, 0, z0 + (k - 0.5) * VOXEL - from.Z)
            local a, s = p:Dot(along), p:Dot(side)
            if a >= -back and a <= front and math.abs(s) <= half then
                for j = 1, layers do
                    local material = mats[i][j][k]
                    if occs[i][j][k] > 0 and (material == Enum.Material.Grass or material == Enum.Material.Ground) then
                        mats[i][j][k] = Enum.Material.Cobblestone
                        changed += 1
                    end
                end
            end
        end
    end
    terrain:WriteVoxels(region, VOXEL, mats, occs)
    return changed
end

local function buildHubApron(root)
    local apron = folder(root, "HubApron")
    local nodes = BridgePlacements.Bridges[ROUTE].Nodes
    local from = nodes[1].Position
    local along = ((nodes[2].Position - from) * Vector3.new(1, 0, 1)).Unit
    local width = BridgePlacements.DeckWidth
    -- marble from the Ring Road's edge to the deck's start (the abutment lies in it), with a gold line down each edge
    local lengthBack, lengthFront = 12, 1.5
    local mid = from - along * ((lengthBack - lengthFront) / 2)
    local slab = CFrame.lookAt(mid + Vector3.new(0, 0.15, 0), mid + Vector3.new(0, 0.15, 0) + along)
    part(apron, "Paving", Vector3.new(width, 0.6, lengthBack + lengthFront), slab * CFrame.new(0, -0.15, 0), { Material = Enum.Material.Marble, Color = rgb(238, 236, 232), Solid = true })
    for _, s in { -1, 1 } do
        part(apron, "GoldLine", Vector3.new(0.7, 0.62, lengthBack + lengthFront), slab * CFrame.new(s * (width / 2 - 0.55), -0.15, 0), { Material = Enum.Material.SmoothPlastic, Color = rgb(226, 176, 70), Solid = true })
    end
    local changed = paintCobble(from, along, lengthBack + 3, lengthFront + 1, width / 2 + 1)
    -- a pair of the hub's crystal lamps where the bridge's apron meets the Ring Road (the hub's rule: a pair at each bridge)
    local lamps = 0
    if WorldBuilder.hasTemplate("Yggdrasil", "HB_CrystalLamp") then
        local side = Vector3.new(-along.Z, 0, along.X)
        for k, s in { -1, 1 } do
            local pos = from - along * 7 + side * s * (width / 2 + 3.5)
            local lampFrame = CFrame.lookAt(pos, Vector3.new(0, from.Y, 0)) * CFrame.Angles(0, math.pi, 0)
            local lamp = WorldBuilder.placeTemplate("Yggdrasil", "HB_CrystalLamp", lampFrame, apron)
            lamp.Name = "HB_CrystalLamp_Crossing" .. k
            local crystal = if k == 1 then "HB_CrystalLampLight" else "HB_CrystalLampGlow"
            local glow = WorldBuilder.placeTemplate("Yggdrasil", crystal, lampFrame, apron)
            local light = WorldBuilder.Lights[crystal]
            if light then
                WorldBuilder.addLight(glow, glow.Color, light.Range, light.Brightness)
            end
            lamps += 1
        end
    end
    return changed, lamps
end

-- ---------- a report on the ground (changes nothing) ----------
-- Rays down over the plaza, each stairway's landings and each pad's flat disc: how far the terrain's top is from where it should be, and
-- which materials it is. A pad must be level out to its FlatRadius (its Height over the plaza), the plaza to 62, a landing across.
function CrossingBuilder.check()
    frame = WorldBuilder.islandFrame(ISLAND)
    local ground = frame.Position.Y
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { WorldBuilder.islandFolder(ISLAND) }
    local report = {}
    local function sample(label, points, level)
        local worst, misses, seen = 0, 0, {}
        for _, point in points do
            local world = frame:PointToWorldSpace(Vector3.new(point.X, 0, point.Z))
            local hit = workspace:Raycast(Vector3.new(world.X, ground + 160, world.Z), Vector3.new(0, -260, 0), params)
            if hit and hit.Instance:IsA("Terrain") then
                worst = math.max(worst, math.abs(hit.Position.Y - ground - (level or point.Y)))
                seen[hit.Material.Name] = (seen[hit.Material.Name] or 0) + 1
            else
                misses += 1
            end
        end
        local names = {}
        for name, count in seen do
            table.insert(names, name .. "=" .. count)
        end
        table.sort(names)
        table.insert(report, string.format("%-26s %4d points, %d with no ground, worst %.2f off level; %s", label, #points, misses, worst, table.concat(names, " ")))
    end
    local function disc(centre, radius, step)
        local points = {}
        for x = -radius, radius, step do
            for z = -radius, radius, step do
                if x * x + z * z <= radius * radius then
                    table.insert(points, Vector3.new(centre.X + x, centre.Y, centre.Z + z))
                end
            end
        end
        return points
    end
    sample("Plaza (r 62)", disc(Vector3.zero, 62, 4), 0)
    for _, faction in P.Order do
        local st, pad = P.Stairs[faction], P.Pads[faction]
        sample(faction .. " pad (flat disc)", disc(pad.Centre, pad.FlatRadius - 2, 6), pad.Height)
        for _, tier in st.Tiers do
            if tier[1] == "landing" then
                local mid = st.Axis * ((tier[2] + tier[3]) / 2)
                sample(faction .. " landing at " .. tier[4], { Vector3.new(mid.X, tier[4], mid.Z), Vector3.new(mid.X + st.Axis.Z * 10, tier[4], mid.Z - st.Axis.X * 10), Vector3.new(mid.X - st.Axis.Z * 10, tier[4], mid.Z + st.Axis.X * 10) }, tier[4])
            end
        end
    end
    return table.concat(report, "\n")
end

-- ---------- everything ----------
function CrossingBuilder.build()
    frame = WorldBuilder.islandFrame(ISLAND)
    local root = WorldBuilder.islandFolder(ISLAND)
    root:ClearAllChildren()
    root:SetAttribute("Centre", frame.Position)
    root:SetAttribute("Reach", P.Reach)
    buildPlaza(root)
    buildGate(root)
    buildStairs(root)
    buildRopeBridges(root)
    buildReps(root)
    buildPads(root)
    local zones = buildApproach(root)
    local dress = buildDress(root)
    local cobbled, lamps = buildHubApron(root)
    -- the Orthodox headquarters (OrthodoxBuilder): rebuilt here too, because the build above clears the island's folder (it does nothing until its kit is stored)
    local okHall, hall = pcall(function()
        return require(WorldBuild:WaitForChild("OrthodoxBuilder"):Clone()).build()
    end)
    -- Dawnspire's territory (DawnspireBuilder): rebuilt here too, for the same reason (it does nothing until its kit is stored)
    local okTerritory, territory = pcall(function()
        return require(WorldBuild:WaitForChild("DawnspireBuilder"):Clone()).build()
    end)
    WorldBuilder.applyCollision(root)
    local parts = 0
    for _, d in root:GetDescendants() do
        if d:IsA("BasePart") then
            parts += 1
        end
    end
    return { Parts = parts, Zones = zones, ApronVoxels = cobbled, Lamps = lamps, Forest = dress.Jade, Basalt = dress.Ember, Falls = dress.Falls,
        Hall = if okHall then hall else tostring(hall), Territory = if okTerritory then territory else tostring(territory) }
end

return CrossingBuilder

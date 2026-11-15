-- Build-time only: the Spin Wheel in the hub (GameConfig.SpinWheel; the owner, 2026-11-16: "Place it to where my character
-- standing"). Run from Studio (edit mode) to (re)build FloatingIslands.<island>.SpinWheel at its placement
-- (Placements/<island>.lua SpinWheel: Centre on the ground, Yaw turning the wheel's front, local +Z, toward the World Tree):
--
--   local SW = require(game.ServerStorage.WorldBuild.SpinWheelBuilder:Clone())
--   SW.build("Yggdrasil")
--
-- The hub's celestial look (white marble, gold, pale crystal), as Studio parts: a marble plinth and two pillars holding a
-- 12-stud wheel, a lintel with the words SPIN THE WHEEL, a gold pointer at the top and a crystal on each pillar. Only the
-- stand collides. What the game reads (SpinService, client/Rewards/SpinController):
--   SpinWheel (Model)
--     Rotor (Model)   every turning piece: the gold back disc, the segments' wedges ("Seg<i>"), the gold dividers and pegs,
--                     the hub, and the Face part whose SurfaceGui holds each segment's icon and words ("Seg<i>": Icon, Mark, Words)
--     Axle            invisible: the wheel turns about its Z axis (clockwise as seen from the front); the Rotor rests unturned
--     Pointer         the gold pointer (the ticks sound from it)
--     Prompt          the ProximityPrompt "Spin" (SpinService opens the spin window from it)
--     Sign, Info      the lintel's words and the plinth's line of plain words
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")

local WorldBuilder = require(ServerStorage.WorldBuild.WorldBuilder:Clone())
local GameConfig = require(ReplicatedStorage.GameConfig:Clone())
local UiTheme = require(StarterPlayer.StarterPlayerScripts.UI.UiTheme:Clone())

local SpinWheelBuilder = {}

local LOOKS = WorldBuilder.MaterialLooks
local GOLD = LOOKS.Gold
local MARBLE = LOOKS.Marble

-- measures (studs, the wheel's own frame: origin on the ground at the plinth's middle, +Z its front, +X the right as seen from it)
SpinWheelBuilder.Radius = 6          -- the coloured face (the gold rim reaches RIM)
SpinWheelBuilder.Rim = 6.4
SpinWheelBuilder.AxleHeight = 8.4
SpinWheelBuilder.PillarX = 7.4
SpinWheelBuilder.PillarTop = 15.6
SpinWheelBuilder.SliceDegrees = 15   -- each segment's face is drawn as triangles this wide (a 24-sided disc)
local R, RIM, H = SpinWheelBuilder.Radius, SpinWheelBuilder.Rim, SpinWheelBuilder.AxleHeight
local FACE_Z = 0.12 -- the segments' front face

local function part(name, size, cframe, parent, look, shape)
    local p = Instance.new("Part")
    p.Name = name
    p.Shape = shape or Enum.PartType.Block
    p.Size = size
    p.CFrame = cframe
    p.Anchored = true
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    for property, value in look or {} do
        p[property] = value
    end
    p.Parent = parent
    return p
end

local function quiet(p)
    p.CanCollide = false
    p.CanQuery = false
    p.CanTouch = false
    return p
end

-- A flat triangle (a, b, c in world space) of `thickness`, from two WedgeParts.
local function triangle(name, a, b, c, thickness, parent, look)
    local ab, ac, bc = b - a, c - a, c - b
    local abd, acd, bcd = ab:Dot(ab), ac:Dot(ac), bc:Dot(bc)
    if abd > acd and abd > bcd then
        c, a = a, c
    elseif acd > bcd and acd > abd then
        a, b = b, a
    end
    ab, ac, bc = b - a, c - a, c - b
    local right = ac:Cross(ab).Unit
    local up = bc:Cross(right).Unit
    local back = bc.Unit
    local height = math.abs(ab:Dot(up))
    local pieces = {}
    for i, spec in { { (a + b) / 2, right, back, math.abs(ab:Dot(back)) }, { (a + c) / 2, -right, -back, math.abs(ac:Dot(back)) } } do
        local w = Instance.new("WedgePart")
        w.Name = name
        w.Size = Vector3.new(thickness, height, spec[4])
        w.CFrame = CFrame.fromMatrix(spec[1], spec[2], up, spec[3])
        w.Anchored = true
        w.TopSurface = Enum.SurfaceType.Smooth
        w.BottomSurface = Enum.SurfaceType.Smooth
        for property, value in look do
            w[property] = value
        end
        quiet(w)
        w.Parent = parent
        pieces[i] = w
    end
    return pieces
end

local function bold(label, size, color)
    label.BackgroundTransparency = 1
    label.FontFace = UiTheme.Fonts.Heavy
    label.TextScaled = true
    label.TextColor3 = color or Color3.new(1, 1, 1)
    local stroke = Instance.new("UIStroke")
    stroke.Color = UiTheme.Colors.Outline
    stroke.Thickness = size
    stroke.Parent = label
    local limit = Instance.new("UITextSizeConstraint")
    limit.MaxTextSize = 200
    limit.Parent = label
    return label
end

-- An invisible part carrying a SurfaceGui on its +Z face.
local function panel(name, size, cframe, parent, pixelsPerStud)
    local p = quiet(part(name, Vector3.new(size.X, size.Y, 0.05), cframe, parent, { Transparency = 1 }))
    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Back
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = pixelsPerStud
    gui.LightInfluence = 0.15
    gui.MaxDistance = 220
    gui.Parent = p
    return p, gui
end

local function crystal(name, at, size, parent)
    local gem = quiet(part(name, Vector3.new(size, size * 1.6, size), at * CFrame.Angles(0, math.rad(45), 0), parent, LOOKS.Crystal))
    local core = quiet(part(name .. "Core", Vector3.new(size * 0.45, size * 1.1, size * 0.45), at * CFrame.Angles(0, math.rad(45), 0), parent,
        { Material = Enum.Material.Neon, Color = Color3.fromRGB(190, 225, 255), CastShadow = false }))
    return gem, core
end

-- the stand: plinth, step, pillars, lintel (these collide)
local function buildStand(frame, model)
    local stand = Instance.new("Model")
    stand.Name = "Stand"
    stand.Parent = model
    part("Plinth", Vector3.new(18, 1.2, 8), frame * CFrame.new(0, 0.3, 0), stand, MARBLE)
    quiet(part("PlinthTrim", Vector3.new(18.2, 0.16, 8.2), frame * CFrame.new(0, 0.84, 0), stand, GOLD))
    part("Step", Vector3.new(16, 0.6, 5.2), frame * CFrame.new(0, 1.2, -0.6), stand, MARBLE)
    quiet(part("StepTrim", Vector3.new(16.2, 0.14, 5.4), frame * CFrame.new(0, 1.47, -0.6), stand, LOOKS.GoldFlat))
    for _, side in { -1, 1 } do
        local x = side * SpinWheelBuilder.PillarX
        local name = if side < 0 then "Left" else "Right"
        part(name .. "Base", Vector3.new(2.6, 0.7, 2.6), frame * CFrame.new(x, 1.85, -0.6), stand, MARBLE)
        quiet(part(name .. "BaseTrim", Vector3.new(2.75, 0.16, 2.75), frame * CFrame.new(x, 2.22, -0.6), stand, GOLD))
        local height = SpinWheelBuilder.PillarTop - 2.2
        part(name .. "Pillar", Vector3.new(height, 1.6, 1.6), frame * CFrame.new(x, 2.2 + height / 2, -0.6) * CFrame.Angles(0, 0, math.rad(90)),
            stand, MARBLE, Enum.PartType.Cylinder)
        for _, y in { 4.2, SpinWheelBuilder.PillarTop - 0.5 } do
            quiet(part(name .. "Ring", Vector3.new(0.3, 1.78, 1.78), frame * CFrame.new(x, y, -0.6) * CFrame.Angles(0, 0, math.rad(90)), stand,
                GOLD, Enum.PartType.Cylinder))
        end
        -- the arm from the pillar to the hub, behind the wheel
        quiet(part(name .. "Arm", Vector3.new(SpinWheelBuilder.PillarX - 0.6, 0.7, 0.7), frame * CFrame.new(x / 2 + side * 0.3, H, -0.75),
            stand, GOLD))
        crystal(name .. "Crystal", frame * CFrame.new(x, SpinWheelBuilder.PillarTop + 3.35, -0.6), 1.1, stand)
    end
    -- the lintel over the pillars, its front carrying the words
    local lintelY = SpinWheelBuilder.PillarTop + 1.3
    part("Lintel", Vector3.new(SpinWheelBuilder.PillarX * 2 + 2.8, 2.6, 1.6), frame * CFrame.new(0, lintelY, -0.6), stand, MARBLE)
    quiet(part("LintelTrimTop", Vector3.new(SpinWheelBuilder.PillarX * 2 + 3, 0.2, 1.75), frame * CFrame.new(0, lintelY + 1.3, -0.6), stand, GOLD))
    quiet(part("LintelTrimFoot", Vector3.new(SpinWheelBuilder.PillarX * 2 + 3, 0.2, 1.75), frame * CFrame.new(0, lintelY - 1.3, -0.6), stand, GOLD))
    crystal("LintelCrystal", frame * CFrame.new(0, lintelY + 2.25, -0.6), 0.9, stand)
    local _, sign = panel("Sign", Vector2.new(SpinWheelBuilder.PillarX * 2 + 2.2, 2.1), frame * CFrame.new(0, lintelY, 0.23), model, 60)
    local words = bold(Instance.new("TextLabel"), 4, UiTheme.Colors.Highlight)
    words.Name = "Words"
    words.Size = UDim2.fromScale(0.96, 0.84)
    words.Position = UDim2.fromScale(0.02, 0.08)
    words.Text = "SPIN THE WHEEL"
    words.Parent = sign
    -- the plinth's line of plain words
    local _, info = panel("Info", Vector2.new(15, 0.7), frame * CFrame.new(0, 0.4, 4.03), model, 60)
    local line = bold(Instance.new("TextLabel"), 2.5, Color3.new(1, 1, 1))
    line.Name = "Words"
    line.Size = UDim2.fromScale(1, 0.9)
    line.Position = UDim2.fromScale(0, 0.05)
    line.Text = GameConfig.SpinWheel.DailySpins .. " FREE SPINS EVERY DAY"
    line.Parent = info
    return stand
end

-- the turning wheel: a 24-sided disc of eight coloured segments on a gold disc, gold dividers and pegs, a crystal hub
local function buildRotor(frame, model)
    local rotor = Instance.new("Model")
    rotor.Name = "Rotor"
    rotor.Parent = model
    local axle = frame * CFrame.new(0, H, 0)
    -- a point on the face at `degrees` clockwise from the top (as seen from the front) and `radius` out, `z` forward
    local function at(degrees, radius, z)
        local a = math.rad(degrees)
        return axle:PointToWorldSpace(Vector3.new(math.sin(a) * radius, math.cos(a) * radius, z))
    end
    quiet(part("BackDisc", Vector3.new(0.5, RIM * 2, RIM * 2), axle * CFrame.new(0, 0, -0.2) * CFrame.Angles(0, math.rad(90), 0), rotor,
        GOLD, Enum.PartType.Cylinder))
    local segments = GameConfig.SpinWheel.Segments
    local step = 360 / #segments
    local slices = math.max(1, math.round(step / SpinWheelBuilder.SliceDegrees))
    for index, segment in segments do
        local centre = (index - 1) * step
        local from = centre - step / 2
        for s = 0, slices - 1 do
            local a1 = from + s * step / slices
            local a2 = a1 + step / slices
            triangle("Seg" .. index, at(0, 0, 0), at(a1, R, 0), at(a2, R, 0), FACE_Z * 2, rotor,
                { Material = Enum.Material.SmoothPlastic, Color = segment.Color, CastShadow = false })
        end
        -- the divider on the segment's leading edge, and its peg at the rim
        local edge = from
        quiet(part("Divider", Vector3.new(0.16, R - 0.6, 0.12), CFrame.lookAt(at(edge, (R + 0.6) / 2, FACE_Z + 0.06), at(edge, (R + 0.6) / 2, FACE_Z + 1),
            (at(edge, R, 0) - at(edge, 0, 0)).Unit), rotor, GOLD))
        quiet(part("Peg", Vector3.new(0.7, 0.42, 0.42), CFrame.new(at(edge, R + 0.12, FACE_Z + 0.2)) * axle.Rotation * CFrame.Angles(0, math.rad(90), 0),
            rotor, GOLD, Enum.PartType.Cylinder))
    end
    -- the hub: a gold boss and a crystal in it
    quiet(part("Hub", Vector3.new(0.5, 2.4, 2.4), axle * CFrame.new(0, 0, FACE_Z + 0.2) * CFrame.Angles(0, math.rad(90), 0), rotor, GOLD,
        Enum.PartType.Cylinder))
    local gem = quiet(part("HubGem", Vector3.new(1.2, 1.2, 1.2), axle * CFrame.new(0, 0, FACE_Z + 0.55), rotor, LOOKS.Crystal, Enum.PartType.Ball))
    gem.Transparency = 0.2
    local core = quiet(part("HubCore", Vector3.new(0.6, 0.6, 0.6), axle * CFrame.new(0, 0, FACE_Z + 0.55), rotor,
        { Material = Enum.Material.Neon, Color = Color3.fromRGB(200, 232, 255), CastShadow = false }, Enum.PartType.Ball))
    local light = Instance.new("PointLight")
    light.Color = Color3.fromRGB(220, 236, 255)
    light.Range = 12
    light.Brightness = 0.6
    light.Shadows = false
    light.Parent = core

    -- each segment's icon, mark and words, on one face over the wedges (SpinController fills in the player's own amounts)
    local size = R * 2
    local face, gui = panel("Face", Vector2.new(size, size), axle * CFrame.new(0, 0, FACE_Z + 0.03), rotor, 50)
    face.Parent = rotor
    local px = size * 50
    for index, segment in segments do
        local degrees = (index - 1) * step
        local a = math.rad(degrees)
        local holder = Instance.new("Frame")
        holder.Name = "Seg" .. index
        holder.BackgroundTransparency = 1
        holder.Size = UDim2.fromScale(1, 1)
        holder.Parent = gui
        local function place(object, radius, w, h)
            object.AnchorPoint = Vector2.new(0.5, 0.5)
            object.Size = UDim2.fromOffset(w, h)
            object.Position = UDim2.fromOffset(px / 2 + math.sin(a) * radius * 50, px / 2 - math.cos(a) * radius * 50)
            object.Rotation = degrees
            object.Parent = holder
        end
        local icon = Instance.new("ImageLabel")
        icon.Name = "Icon"
        icon.BackgroundTransparency = 1
        icon.ScaleType = Enum.ScaleType.Fit
        icon.Image = if segment.Kind == "Stones" then UiTheme.Icons.Stones
            elseif segment.Kind == "Qi" then UiTheme.Icons.Qi
            elseif segment.Kind == "Jackpot" then UiTheme.EggIcons.ExclusiveEgg
            elseif segment.Kind == "Egg" then UiTheme.EggIcons.BeginnerQiEgg
            else ""
        place(icon, R * 0.5, 100, 100)
        local mark = bold(Instance.new("TextLabel"), 4, UiTheme.Colors.Highlight) -- the "+1" spin's mark, where it has no picture
        mark.Name = "Mark"
        mark.Text = if segment.Kind == "Spin" then "+1" else ""
        mark.Visible = segment.Kind == "Spin"
        place(mark, R * 0.5, 100, 76)
        local words = bold(Instance.new("TextLabel"), 3, if segment.Kind == "Jackpot" then UiTheme.Colors.Highlight else Color3.new(1, 1, 1))
        words.Name = "Words"
        words.Text = if segment.Kind == "Stones" then "STONES" elseif segment.Kind == "Qi" then segment.Minutes .. " MIN QI"
            elseif segment.Kind == "Egg" then "EGG" elseif segment.Kind == "Spin" then "EXTRA SPIN" else "JACKPOT"
        place(words, R * 0.8, 150, 40)
    end
    return rotor
end

-- the gold pointer at the top, over the rim, pointing down into the wheel
local function buildPointer(frame, model)
    local top = H + RIM
    local z = FACE_Z + 0.45
    local pieces = triangle("Pointer", frame:PointToWorldSpace(Vector3.new(-0.75, top + 0.9, z)), frame:PointToWorldSpace(Vector3.new(0.75, top + 0.9, z)),
        frame:PointToWorldSpace(Vector3.new(0, top - 0.85, z)), 0.4, model, GOLD)
    pieces[1].Name = "PointerLeft"
    pieces[2].Name = "PointerRight"
    local knob = quiet(part("Pointer", Vector3.new(0.6, 0.9, 0.9), frame * CFrame.new(0, top + 0.9, z) * CFrame.Angles(0, math.rad(90), 0), model, GOLD,
        Enum.PartType.Cylinder))
    local gem = quiet(part("PointerGem", Vector3.new(0.5, 0.5, 0.5), frame * CFrame.new(0, top + 0.9, z + 0.35), model,
        { Material = Enum.Material.Neon, Color = Color3.fromRGB(200, 232, 255), CastShadow = false }, Enum.PartType.Ball))
    return knob, gem
end

function SpinWheelBuilder.build(island)
    island = island or "Yggdrasil"
    local placements = require(ServerStorage.WorldBuild.Placements:FindFirstChild(island):Clone())
    local spot = assert(placements.SpinWheel, "Placements." .. island .. " has no SpinWheel")
    local root = WorldBuilder.islandFolder(island)
    local old = root:FindFirstChild("SpinWheel")
    if old then
        old:Destroy()
    end
    local model = Instance.new("Model")
    model.Name = "SpinWheel"
    local frame = WorldBuilder.islandFrame(island) * CFrame.new(spot.Centre) * CFrame.Angles(0, spot.Yaw, 0)
    buildStand(frame, model)
    buildRotor(frame, model)
    buildPointer(frame, model)
    quiet(part("Axle", Vector3.new(0.4, 0.4, 0.4), frame * CFrame.new(0, H, 0), model, { Transparency = 1 }))
    local promptPart = quiet(part("Prompt", Vector3.new(1, 1, 1), frame * CFrame.new(0, 2.6, 5), model, { Transparency = 1 }))
    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Spin"
    prompt.ObjectText = "Spin the Wheel"
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt.Parent = promptPart
    model.PrimaryPart = model:FindFirstChild("Axle")
    model.ModelStreamingMode = Enum.ModelStreamingMode.Persistent -- every client has it: the HUD points to it, and it turns for all
    model.Parent = root
    return model
end

return SpinWheelBuilder

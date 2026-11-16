-- A beast pen's fence at a level, built on each client (PenController) because it grows with the owner's upgrades: white marble posts
-- and kerb with two gold rails, in the hub's celestial look (the same pieces as the pasture's gate, which PastureBuilder builds once:
-- the front fence leaves the gate's opening at its middle). Each post stands on the ground under it, so a pen on a slope never floats.
-- Inside it, a wooden deck fills the pen at every level (the owner, 2026-11-16: "add a wooden floor in every pen"): honey-oak boards
-- running from the gate to the back, each line of boards in two lengths with its joint staggered from its neighbours', over a dark
-- bed that shows in the narrow gaps between them; their edges tuck under the kerb, and a marble sill closes the gate's opening. The
-- deck is flat, DECK_RISE over the highest ground under it, so no ground pokes through it. The pasture's ground under it is terrain
-- with no grass blades (PastureBuilder lays it: a grass blade grows up through any part laid on Grass).
--   PenFence.build(frame, level)        a Model of the fence and its deck (not parented), for a pasture's frame and a pen level; its
--                                       "DeckTop" attribute is the deck's top (world Y), where the pen's beasts stand
--   PenFence.grow(model, seconds)       lays the deck's boards (a wave across the pen) and raises its posts and rails out of the
--                                       ground, one after another round the pen
--   PenFence.sink(model, seconds)       lowers the fence back in, then destroys it (its deck goes at once: the new one takes its place)
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"))

local PenFence = {}

local MARBLE = Color3.fromRGB(232, 234, 244)
local KERB = Color3.fromRGB(206, 210, 228)
local GOLD = Color3.fromRGB(226, 176, 70)
local POST_EVERY = 8

-- the deck: light honey oak beside the white marble and gold (the hub has no wood of its own: a warm, light tone keeps it in the
-- city's palette), each board's tone a touch off its neighbours'
local BOARD = Color3.fromRGB(205, 160, 108)
local BOARD_TONES = { 1, 0.93, 0.97, 0.89, 0.99, 0.91, 0.95 } -- (darkened from BOARD by 1 minus this)
local BED = Color3.fromRGB(78, 54, 38)   -- what shows in the gaps between boards
local BOARD_PITCH = 1.75  -- studs from one board's middle to the next (the pen's width is shared out evenly: about this)
local BOARD_GAP = 0.14    -- the gap between two boards
local BOARD_THICK = 0.45
local DECK_RISE = 0.3     -- the deck's top over the highest ground under it (the kerb's top is 0.5 over its own ground)
local GAP_DEPTH = 0.1     -- how far under the boards' top the bed is
local JOINTS = { 0.62, 0.3, 0.78, 0.45, 0.2, 0.55, 0.85, 0.38 } -- where each line of boards is joined, along its length
local JOINT_GAP = 0.08
local DECK_DROP = 0.5     -- how far under its place a board starts when the deck is laid

local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Include
ray.FilterDescendantsInstances = { workspace.Terrain }

local function groundAt(position, fallback)
    local hit = workspace:Raycast(position + Vector3.new(0, 20, 0), Vector3.new(0, -40, 0), ray)
    return if hit then hit.Position.Y else fallback
end

local function piece(model, name, size, cframe, color, material, collide)
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.Size = size
    p.CFrame = cframe
    p.Color = color
    p.Material = material
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.CanCollide = collide
    p.CanTouch = false
    p.CanQuery = collide
    p.CastShadow = name == "Post"
    p:SetAttribute("Home", cframe)
    p.Parent = model
    return p
end

-- the fence's corners and the gate's ends, in order round the pen, in the pasture's frame (on the ground, Y 0)
local function outline(level)
    local entry = PenLayout.level(level)
    local x = entry.Width / 2 + PenLayout.Fence / 2
    local front = PenLayout.Front
    local back = front + PenLayout.Fence + entry.Depth
    local g = PenLayout.Gate / 2 + 1.2 -- (the gate's posts, PastureBuilder's, stand at the gap's ends)
    -- from the gate's right post, round the back, to its left post
    return { Vector3.new(g, 0, front), Vector3.new(x, 0, front), Vector3.new(x, 0, back), Vector3.new(-x, 0, back),
        Vector3.new(-x, 0, front), Vector3.new(-g, 0, front) }
end

-- the deck inside the fence at a level, its boards first in the model (they are laid first when it grows)
local function buildDeck(model, frame, level)
    local entry = PenLayout.level(level)
    local width, depth = entry.Width, entry.Depth
    local front = PenLayout.Front + PenLayout.Fence / 2 -- the fence's inner line: the deck's edges tuck 0.15 under the kerb
    -- flat at DECK_RISE over the highest ground under it, its bed reaching down past the lowest
    local high, low = -math.huge, math.huge
    for x = -width / 2, width / 2 + 0.01, width / 4 do
        for z = 0, depth + 0.01, depth / 6 do
            local at = frame * Vector3.new(x, 0, front + z)
            local y = groundAt(at, frame.Y)
            high, low = math.max(high, y), math.min(low, y)
        end
    end
    local top = high + DECK_RISE
    model:SetAttribute("DeckTop", top)
    local lines = math.round(width / BOARD_PITCH / 2) * 2 + 1 -- (odd: a board, not a gap, runs up the middle from the gate)
    local pitch = width / lines
    local yaw = frame.Rotation
    local function board(x, z0, z1, tone)
        local length = z1 - z0
        local at = frame * Vector3.new(x, 0, front + (z0 + z1) / 2)
        local p = piece(model, "DeckBoard", Vector3.new(pitch - BOARD_GAP, BOARD_THICK, length),
            CFrame.new(at.X, top - BOARD_THICK / 2, at.Z) * yaw, BOARD:Lerp(Color3.new(), 1 - tone), Enum.Material.Wood, true)
        p:SetAttribute("Deck", true)
        return p
    end
    for i = 1, lines do
        local x = -width / 2 + pitch * (i - 0.5)
        local tone = BOARD_TONES[(i - 1) % #BOARD_TONES + 1]
        if depth < 24 then -- a short pen: one board a line
            board(x, 0, depth, tone)
        else -- two, the joint staggered from the next line's
            local joint = depth * JOINTS[(i - 1) % #JOINTS + 1]
            board(x, 0, joint - JOINT_GAP / 2, tone)
            board(x, joint + JOINT_GAP / 2, depth, BOARD_TONES[(i + 2) % #BOARD_TONES + 1])
        end
    end
    -- the bed under the gaps: inset from the boards' ends and sides so no face of it lies on one of theirs
    local bottom = low - 0.6
    local bedTop = top - GAP_DEPTH
    local centre = frame * Vector3.new(0, 0, front + depth / 2)
    -- (solid: a character whose middle was over a gap felt for the floor through it, found the ground and walked inside the deck,
    -- seen in Studio; a beast's foot over a gap rests on it too)
    local bed = piece(model, "DeckBed", Vector3.new(width - 0.3, bedTop - bottom, depth - 0.3),
        CFrame.new(centre.X, (bedTop + bottom) / 2, centre.Z) * yaw, BED, Enum.Material.Wood, true)
    bed:SetAttribute("Deck", true)
    -- the gate's sill: the kerb carried across the opening, a little proud of the deck
    local sill = frame * Vector3.new(0, 0, PenLayout.Front)
    local sillTop = top + 0.12
    local sillPart = piece(model, "DeckSill", Vector3.new(PenLayout.Gate, sillTop - bottom, 1.3),
        CFrame.new(sill.X, (sillTop + bottom) / 2, sill.Z) * yaw, KERB, Enum.Material.Marble, true)
    sillPart:SetAttribute("Deck", true)
end

function PenFence.build(frame, level)
    local model = Instance.new("Model")
    model.Name = "PenFence"
    model:SetAttribute("Frame", frame)
    buildDeck(model, frame, level)
    local h = PenLayout.FenceHeight
    local corners = outline(level)
    -- the posts: every corner, and between them about every POST_EVERY studs; each on its own ground
    local posts = {}
    for i = 1, #corners - 1 do
        local a, b = corners[i], corners[i + 1]
        local count = math.max(1, math.ceil((b - a).Magnitude / POST_EVERY))
        for k = if i == 1 then 0 else 1, count do
            local at = frame * (a + (b - a) * (k / count))
            table.insert(posts, Vector3.new(at.X, groundAt(at, frame.Y), at.Z))
        end
    end
    for i, at in posts do
        piece(model, "Post", Vector3.new(0.9, h + 2, 0.9), CFrame.new(at + Vector3.new(0, h / 2 - 1, 0)), MARBLE, Enum.Material.Marble, true)
        piece(model, "PostCap", Vector3.new(1.1, 0.24, 1.1), CFrame.new(at + Vector3.new(0, h + 0.12, 0)), GOLD, Enum.Material.SmoothPlastic, false)
        local nextPost = posts[i + 1]
        if nextPost then
            local mid = (at + nextPost) / 2
            local span = (nextPost - at).Magnitude
            local turn = CFrame.lookAt(mid, nextPost)
            piece(model, "Kerb", Vector3.new(1.3, 2.5, span + 0.9), turn * CFrame.new(0, -0.75, 0), KERB, Enum.Material.Marble, true)
            for _, y in { 1.3, 2.6 } do
                piece(model, "Rail", Vector3.new(0.28, 0.32, span), turn * CFrame.new(0, y, 0), GOLD, Enum.Material.SmoothPlastic, true)
            end
        end
    end
    return model
end

-- (each piece of the fence rises from DEPTH studs down, its turn coming round the pen; the deck's boards rise DECK_DROP, in a wave
-- from one side of the pen to the other, before the fence)
local DEPTH = 4.5
function PenFence.grow(model, seconds)
    local fence, deck = {}, {}
    for _, p in model:GetChildren() do
        table.insert(if p:GetAttribute("Deck") then deck else fence, p)
    end
    local frame = model:GetAttribute("Frame")
    local half = PenLayout.Levels[PenLayout.Max].Width / 2
    for _, p in deck do
        local home = p:GetAttribute("Home")
        p.CFrame = home - Vector3.new(0, DECK_DROP, 0)
        local along = (frame:PointToObjectSpace(home.Position).X + half) / (2 * half) -- (0 at the pen's left, 1 at its right)
        task.delay(math.clamp(along, 0, 1) * seconds * 0.35, function()
            if p.Parent then
                TweenService:Create(p, TweenInfo.new(seconds * 0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = home }):Play()
            end
        end)
    end
    local count = #fence
    for i, p in fence do
        local home = p:GetAttribute("Home")
        p.CFrame = home - Vector3.new(0, DEPTH, 0)
        local delay = (i / math.max(count, 1)) * seconds * 0.6
        task.delay(delay, function()
            if p.Parent then
                TweenService:Create(p, TweenInfo.new(seconds * 0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = home }):Play()
            end
        end)
    end
end

function PenFence.sink(model, seconds)
    for _, p in model:GetChildren() do
        if p:GetAttribute("Deck") then
            p:Destroy() -- (the new, bigger deck is laid where it was: two decks would fight on one plane)
        elseif p:IsA("BasePart") then
            p.CanCollide = false
            TweenService:Create(p, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
                { CFrame = p.CFrame - Vector3.new(0, DEPTH, 0) }):Play()
        end
    end
    task.delay(seconds + 0.05, function()
        model:Destroy()
    end)
end

return PenFence

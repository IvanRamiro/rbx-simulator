-- A beast pen's fence at a level, built on each client (PenController) because it grows with the owner's upgrades: white marble posts
-- and kerb with two gold rails, in the hub's celestial look (the same pieces as the pasture's gate, which PastureBuilder builds once:
-- the front fence leaves the gate's opening at its middle). Each post stands on the ground under it, so a pen on a slope never floats.
--   PenFence.build(frame, level)        a Model of the fence (not parented), for a pasture's frame and a pen level
--   PenFence.grow(model, seconds)       raises its posts and rails out of the ground, one after another round the pen
--   PenFence.sink(model, seconds)       lowers them back in, then destroys it
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"))

local PenFence = {}

local MARBLE = Color3.fromRGB(232, 234, 244)
local KERB = Color3.fromRGB(206, 210, 228)
local GOLD = Color3.fromRGB(226, 176, 70)
local POST_EVERY = 8

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

function PenFence.build(frame, level)
    local model = Instance.new("Model")
    model.Name = "PenFence"
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

-- (each piece rises from DEPTH studs down, its turn coming round the pen)
local DEPTH = 4.5
function PenFence.grow(model, seconds)
    local parts = model:GetChildren()
    local count = #parts
    for i, p in parts do
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
        if p:IsA("BasePart") then
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

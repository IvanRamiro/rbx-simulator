-- The Qi barriers across the start of each island bridge (tagged GameConfig.BridgeBarrierTag, with
-- the RankId that opens them). A barrier is solid until this player reaches its rank, and shows a
-- plain wall of transparent light in its gate's own colour, with what it needs (the owner: "just
-- match the color of entrance with their realm level"; the part was built with its theme's Glow).
-- From then on it lets them through (collision off for this player only) and the wall is gone: one
-- player can see a sealed gate where another walks straight through. WorldService still returns
-- anyone below the rank who gets onto the bridge some other way.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))

local player = Players.LocalPlayer
local WALL_TRANSPARENCY = 0.68
local LABEL_DISTANCE = 90 -- studs: the wall's words show only close to it
-- each gate's opening, in studs from the deck: the wall reaches its lintel (the barrier's collision
-- stays as built)
local WALL_HEIGHT = { JadeRoute = 16.2, EmberRoute = 14.6, MoonlitRoute = 15.4, OriginRoute = 16.4 }

local barriers = {} -- [part] = { Index = required rank index, Wall = its Beam, Label, Light = its PointLight }

local function playerIndex()
    local leaderstats = player:FindFirstChild("leaderstats")
    local rank = leaderstats and leaderstats:FindFirstChild("Rank")
    return rank and Ranks.getIndex(rank.Value) or 0
end

-- a textureless Beam between the gate's two sides: with its attachments unturned it stands upright.
-- The barrier stands on the deck, so a taller wall grows upward.
local function buildWall(part)
    local half = part.Size.X / 2
    local height = WALL_HEIGHT[part:GetAttribute("Route")] or part.Size.Y
    local up = (height - part.Size.Y) / 2
    local a0 = Instance.new("Attachment")
    a0.Name = "QiWallLeft"
    a0.CFrame = CFrame.new(-half, up, 0)
    a0.Parent = part
    local a1 = Instance.new("Attachment")
    a1.Name = "QiWallRight"
    a1.CFrame = CFrame.new(half, up, 0)
    a1.Parent = part
    local beam = Instance.new("Beam")
    beam.Name = "QiWall"
    beam.Attachment0, beam.Attachment1 = a0, a1
    beam.Width0, beam.Width1 = height, height
    beam.Segments = 1
    beam.FaceCamera = false
    beam.Color = ColorSequence.new(part.Color)
    beam.Transparency = NumberSequence.new(WALL_TRANSPARENCY)
    beam.LightEmission = 0.3
    beam.LightInfluence = 0
    beam.Parent = part
    return beam
end

local function buildLabel(part, rank)
    local label = Instance.new("BillboardGui")
    label.Name = "QiWallLabel"
    label.Adornee = part
    label.MaxDistance = LABEL_DISTANCE
    label.LightInfluence = 0
    label.Size = UDim2.fromOffset(320, 52)
    label.StudsOffset = Vector3.new(0, -part.Size.Y / 2 + 7, 0)
    local text = Instance.new("TextLabel")
    text.BackgroundTransparency = 1
    text.Size = UDim2.fromScale(1, 1)
    text.FontFace = UiTheme.Fonts.Title
    text.TextScaled = true
    text.TextColor3 = UiTheme.Colors.Text
    text.Text = "Sealed\nReach " .. rank.Name .. " to pass"
    local stroke = Instance.new("UIStroke")
    stroke.Color = Color3.fromRGB(10, 14, 28)
    stroke.Thickness = 2
    stroke.Parent = text
    text.Parent = label
    label.Parent = part
    return label
end

local function refresh(part, entry)
    local open = playerIndex() >= entry.Index
    part.CanCollide = not open
    part.Transparency = 1 -- the wall is the Beam: the part itself is only the collision
    entry.Wall.Enabled = not open
    entry.Label.Enabled = not open
    if entry.Light then
        entry.Light.Enabled = not open
    end
end

local function refreshAll()
    for part, entry in barriers do
        refresh(part, entry)
    end
end

local function add(part)
    local rank = Ranks.getRankById(part:GetAttribute("RankId"))
    if not (rank and part:IsA("BasePart")) or barriers[part] then
        return
    end
    local entry = { Index = Ranks.getIndex(rank.Name), Wall = buildWall(part), Label = buildLabel(part, rank), Light = part:FindFirstChildOfClass("PointLight") }
    barriers[part] = entry
    refresh(part, entry)
end

CollectionService:GetInstanceAddedSignal(GameConfig.BridgeBarrierTag):Connect(add)
CollectionService:GetInstanceRemovedSignal(GameConfig.BridgeBarrierTag):Connect(function(part)
    barriers[part] = nil
end)
for _, part in CollectionService:GetTagged(GameConfig.BridgeBarrierTag) do
    add(part)
end

local leaderstats = player:WaitForChild("leaderstats")
local rank = leaderstats:WaitForChild("Rank")
rank.Changed:Connect(refreshAll)
refreshAll()

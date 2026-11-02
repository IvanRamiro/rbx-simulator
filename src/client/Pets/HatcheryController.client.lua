-- The Hatching Altar's window (Yggdrasil; PetService hatches): its prompt (attribute Hatchery) opens
-- a list of the eggs this player has carried home (player attributes "Egg_<EggId>", EggInventory),
-- each with its count and a Hatch button; an egg the player's rank can't hatch yet says which rank
-- it needs. One egg is hatched per press (HatchEggEvent); the window stays open to hatch the next,
-- and closes when the player walks away. The hatch itself plays on the altar (HatchCeremony, from
-- PetController's result).
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudScale"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "HatcheryHud"
local PANEL_COLOR = Color3.fromRGB(20, 20, 30)
local ROW_COLOR = Color3.fromRGB(40, 40, 55)
local TITLE_COLOR = Color3.fromRGB(240, 200, 110)
local HATCH_COLOR = Color3.fromRGB(70, 160, 110)
local DISABLED_COLOR = Color3.fromRGB(80, 80, 88)
local WALK_AWAY = 18
local PRESS_GAP = GameConfig.HatchingAltar.Stage -- the server stages one egg at a time: a press sooner is ignored

local old = playerGui:FindFirstChild(HUD_NAME)
if old then
    old:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false
hud.DisplayOrder = 10

local function corner(parent, radius)
    local c = Instance.new("UICorner")
    c.CornerRadius = UDim.new(0, radius)
    c.Parent = parent
end

local function label(parent, text, size, position, color, alignment)
    local l = Instance.new("TextLabel")
    l.Size = size
    l.Position = position
    l.BackgroundTransparency = 1
    l.Font = Enum.Font.GothamBold
    l.TextScaled = true
    l.TextColor3 = color or Color3.new(1, 1, 1)
    l.TextXAlignment = alignment or Enum.TextXAlignment.Left
    l.Text = text
    l.Parent = parent
    return l
end

local function button(parent, text, size, position, color, onClick)
    local b = Instance.new("TextButton")
    b.Size = size
    b.Position = position
    b.BackgroundColor3 = if onClick then color else DISABLED_COLOR
    b.AutoButtonColor = onClick ~= nil
    b.Font = Enum.Font.GothamBold
    b.TextScaled = true
    b.TextColor3 = Color3.new(1, 1, 1)
    b.Text = text
    b.Parent = parent
    corner(b, 6)
    local padding = Instance.new("UIPadding")
    padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 6), UDim.new(0, 6)
    padding.PaddingTop, padding.PaddingBottom = UDim.new(0, 3), UDim.new(0, 3)
    padding.Parent = b
    if onClick then
        b.Activated:Connect(onClick)
    end
    return b
end

local window = Instance.new("Frame")
window.Name = "HatcheryWindow"
-- at the screen's right edge, so the cradle (mid-screen behind the player) stays in sight
window.AnchorPoint = Vector2.new(1, 0.5)
window.Position = UDim2.new(1, -20, 0.5, 0)
window.Size = UDim2.fromOffset(440, 360)
window.BackgroundColor3 = PANEL_COLOR
window.BackgroundTransparency = 0.08
window.Visible = false
window.Parent = hud
corner(window, 12)
applyHudScale(window)

label(window, "Hatching Altar", UDim2.new(1, -70, 0, 30), UDim2.fromOffset(16, 10), TITLE_COLOR)
local hint = label(window, "", UDim2.new(1, -32, 0, 18), UDim2.fromOffset(16, 42), Color3.fromRGB(190, 190, 205))

local list = Instance.new("ScrollingFrame")
list.Position = UDim2.fromOffset(12, 68)
list.Size = UDim2.new(1, -24, 1, -80)
list.BackgroundTransparency = 1
list.BorderSizePixel = 0
list.ScrollBarThickness = 6
list.CanvasSize = UDim2.new()
list.AutomaticCanvasSize = Enum.AutomaticSize.Y
list.Parent = window
local layout = Instance.new("UIListLayout")
layout.Padding = UDim.new(0, 6)
layout.SortOrder = Enum.SortOrder.LayoutOrder
layout.Parent = list

hud.Parent = playerGui

local openedAt = nil
local lastPress = 0

local function close()
    window.Visible = false
    openedAt = nil
end
button(window, "X", UDim2.fromOffset(32, 32), UDim2.new(1, -44, 0, 10), Color3.fromRGB(150, 60, 60), close)

-- The eggs this player holds, in the order of GameConfig.Eggs' rank requirements.
local function heldEggs()
    local eggs = {}
    for eggId, egg in GameConfig.Eggs do
        local count = player:GetAttribute("Egg_" .. eggId)
        if typeof(count) == "number" and count > 0 then
            table.insert(eggs, { id = eggId, egg = egg, count = count, order = Ranks.getIndex(Ranks.getRankById(egg.RequiredRank).Name) or 0 })
        end
    end
    table.sort(eggs, function(a, b)
        return if a.order == b.order then a.id < b.id else a.order < b.order
    end)
    return eggs
end

local function render()
    for _, child in list:GetChildren() do
        if child:IsA("Frame") then
            child:Destroy()
        end
    end
    local eggs = heldEggs()
    hint.Text = if #eggs == 0 then "No eggs yet: take one from a guardian's stands and carry it home."
        else "Lay an egg in the cradle to hatch it."
    local rankName = Ranks.getPlayerRankName(player)
    for index, entry in eggs do
        local row = Instance.new("Frame")
        row.LayoutOrder = index
        row.Size = UDim2.new(1, -8, 0, 48)
        row.BackgroundColor3 = ROW_COLOR
        row.Parent = list
        corner(row, 8)
        label(row, entry.egg.DisplayName, UDim2.new(1, -150, 0, 22), UDim2.fromOffset(10, 4))
        local required = Ranks.getRankById(entry.egg.RequiredRank)
        local open = rankName ~= "" and Ranks.isAtLeast(rankName, entry.egg.RequiredRank)
        label(row, if open then "x" .. entry.count else "x" .. entry.count .. "  ·  needs " .. required.Name,
            UDim2.new(1, -150, 0, 16), UDim2.fromOffset(10, 27), if open then Color3.fromRGB(180, 230, 200) else Color3.fromRGB(255, 160, 140))
        button(row, "Hatch", UDim2.fromOffset(110, 34), UDim2.new(1, -120, 0, 7), HATCH_COLOR, if open then function()
            local now = os.clock()
            if now - lastPress < PRESS_GAP then
                return
            end
            lastPress = now
            RemoteEvents.HatchEggEvent:FireServer(entry.id)
        end else nil)
    end
end

ProximityPromptService.PromptTriggered:Connect(function(prompt, who)
    if who ~= player or not prompt:GetAttribute("Hatchery") then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    openedAt = root and root.Position
    if not window.Visible then
        Sfx.play("Open")
    end
    window.Visible = true
    render()
end)

-- the list follows the egg inventory, and the player's rank (which eggs they can hatch), while the
-- window is open
player.AttributeChanged:Connect(function(name)
    if window.Visible and string.sub(name, 1, 4) == "Egg_" then
        render()
    end
end)
task.spawn(function()
    local leaderstats = player:WaitForChild("leaderstats", 60)
    local rank = leaderstats and leaderstats:WaitForChild("Rank", 60)
    if rank then
        rank.Changed:Connect(function()
            if window.Visible then
                render()
            end
        end)
    end
end)

-- walking away closes the window
RunService.Heartbeat:Connect(function()
    if not window.Visible then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root or not openedAt or (root.Position - openedAt).Magnitude > WALK_AWAY then
        close()
    end
end)

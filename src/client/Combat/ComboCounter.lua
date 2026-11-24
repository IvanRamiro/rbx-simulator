-- The combo counter (the owner, 2026-11-24: "combo counters"): the count of consecutive landed hits, shown at the right of the screen, with the tier's
-- word under it (shared/FormRules.Counter: Nice, Great, Amazing, Legendary). The server counts (CombatService, FormRules.countHit) and tells the
-- striker with every strike; this only shows it. The count pops on each hit, a finisher pops it harder, and it fades once the window has lapsed.
-- For show only: it gives no damage. With Reduced Effects it doesn't pop.
--
--   ComboCounter.set(hits, finisher)   the server's count after this strike (0: none), and whether this strike was the chain's finisher
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local FormRules = require(ReplicatedStorage:WaitForChild("FormRules"))
local UI = script.Parent.Parent:WaitForChild("UI")
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

local ComboCounter = {}

local player = Players.LocalPlayer
local C = UiTheme.Colors
local TIER_COLORS = {
    Nice = Color3.fromRGB(255, 255, 255), Great = Color3.fromRGB(150, 226, 255), Amazing = Color3.fromRGB(255, 216, 92),
    Legendary = Color3.fromRGB(255, 120, 96),
}
local FADE = 0.35 -- seconds to fade out once the window has lapsed

local gui = Instance.new("ScreenGui")
gui.Name = "ComboCounter"
gui.ResetOnSpawn = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.DisplayOrder = 4
gui.Parent = player:WaitForChild("PlayerGui")

local holder = Instance.new("Frame")
holder.Name = "Holder"
holder.BackgroundTransparency = 1
holder.AnchorPoint = Vector2.new(1, 0.5)
holder.Position = UDim2.new(1, -28, 0.42, 0)
holder.Size = UDim2.fromOffset(190, 100)
holder.Visible = false
holder.Parent = gui
local scale = Instance.new("UIScale")
scale.Parent = holder

local count = UiKit.label({
    Name = "Count", Font = "Title", TextSize = 56, TextColor3 = C.Text, TextXAlignment = Enum.TextXAlignment.Right,
    AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 0), Size = UDim2.fromOffset(190, 58), Parent = holder,
})
UiKit.outline(count, 3)
local word = UiKit.label({
    Name = "Hits", Font = "Heavy", TextSize = 16, TextColor3 = C.Muted, Text = "HITS", TextXAlignment = Enum.TextXAlignment.Right,
    AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 56), Size = UDim2.fromOffset(190, 18), Parent = holder,
})
UiKit.outline(word, 2)
local tierLabel = UiKit.label({
    Name = "Tier", Font = "Heavy", TextSize = 20, TextColor3 = C.Text, TextXAlignment = Enum.TextXAlignment.Right,
    AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 74), Size = UDim2.fromOffset(190, 24), Parent = holder,
})
UiKit.outline(tierLabel, 2)

local lastHit = -math.huge
local shown = 0

local function setAlpha(alpha)
    count.TextTransparency, word.TextTransparency, tierLabel.TextTransparency = alpha, alpha, alpha
end

function ComboCounter.set(hits, finisher)
    if typeof(hits) ~= "number" or hits < 2 then -- one hit is no combo yet; nothing shows for a miss that lapsed it
        if hits == 0 then
            holder.Visible = false
            shown = 0
        end
        return
    end
    local now = os.clock()
    local grew = hits > shown
    shown = hits
    lastHit = now
    setAlpha(0)
    holder.Visible = true
    local tier = FormRules.tierOf(hits)
    count.Text = tostring(hits)
    tierLabel.Text = if tier then string.upper(tier) else ""
    local color = if tier then TIER_COLORS[tier] else C.Text
    count.TextColor3 = color
    tierLabel.TextColor3 = color
    if grew and player:GetAttribute("SettingReducedEffects") ~= true then
        scale.Scale = if finisher then 1.5 else 1.25
        TweenService:Create(scale, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
    end
end

-- it lapses with the window: a hit's count is shown for that long after, then fades
RunService.Heartbeat:Connect(function()
    if not holder.Visible then
        return
    end
    local idle = os.clock() - lastHit
    if idle > FormRules.Counter.WINDOW then
        local alpha = math.clamp((idle - FormRules.Counter.WINDOW) / FADE, 0, 1)
        setAlpha(alpha)
        if alpha >= 1 then
            holder.Visible = false
            shown = 0
        end
    end
end)

return ComboCounter

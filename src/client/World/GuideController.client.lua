-- Seren the Guide, on the spawn plaza (WorldBuilder.buildHubNpcs: her prompt carries the Guide attribute). Talking to her opens
-- a short walk through the game, a page at a time: what to do first and where everything in the hub is.
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local player = Players.LocalPlayer
local bonus = GameConfig.TrainingStation.QiBonusPercent

local PAGES = {
    "Welcome to Yggdrasil, %s! I'm Seren. The World Tree keeps every cultivator who comes home to it. Let me show you around.",
    "Press E, or the Cultivate button, to meditate and gather Qi. The more Qi you gather, the higher your rank, and the brighter your aura.",
    "You woke beside your own pen: put beasts in it to watch them roam. Down the south-west avenue is the Qi Spring: cultivate inside its runes for " .. bonus .. "% more Qi.",
    "The bridges lead to the outer islands. Weaken a guardian, take an egg from its stands and carry it home across the bridge.",
    "Hatch your eggs at the Hatching Sanctum, up the north avenue. Across the tree to the north-east is the Market Square: Brann at the Blacksmith forges weapons, Lyra at the Marketplace sells eggs, and Corvin at Buy & Sell trades your spares for Spirit Stones.",
    "And keep an eye on the dais beside the World Tree, on its north side: every hour, for ten minutes, the Wandering Merchant sets out his wares there. Good luck, cultivator!",
}

local window = Hud.window({
    Name = "GuideWindow", Title = "SEREN, GUIDE", Size = Vector2.new(500, 276), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body

-- what she says, on a card; under it the page's dots and NEXT
local FOOT = UiTheme.Height.Button
local speech = UiKit.card({ Name = "Speech", Size = UDim2.new(1, 0, 1, -(FOOT + UiTheme.Space.M)), Parent = body })
local text = UiKit.label({
    Name = "Line", Font = "Strong", TextSize = 16, TextWrapped = true, TextYAlignment = Enum.TextYAlignment.Top,
    Position = UDim2.fromOffset(UiTheme.Pad.Card + 2, UiTheme.Pad.Card), Size = UDim2.new(1, -(UiTheme.Pad.Card + 2) * 2, 1, -UiTheme.Pad.Card * 2),
    Parent = speech,
})
local pageLabel = Instance.new("Frame") -- a dot for each page, the one showing in gold
pageLabel.Name = "Page"
pageLabel.BackgroundTransparency = 1
pageLabel.AnchorPoint = Vector2.new(0, 0.5)
pageLabel.Position = UDim2.new(0, 4, 1, -FOOT / 2)
pageLabel.Size = UDim2.new(0.5, 0, 0, 12)
pageLabel.Parent = body
UiKit.list(pageLabel, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center })
local dots = {}
for index = 1, #PAGES do
    local dot = Instance.new("Frame")
    dot.Name = "Dot" .. index
    dot.BorderSizePixel = 0
    dot.Size = UDim2.fromOffset(10, 10)
    dot.LayoutOrder = index
    dot.Parent = pageLabel
    UiKit.corner(dot, 5)
    dots[index] = dot
end
local nextButton = UiKit.button({
    Name = "Next", Text = "NEXT", Tone = "Go", AnchorPoint = Vector2.new(1, 1),
    Position = UDim2.fromScale(1, 1), Size = UDim2.fromOffset(160, FOOT), Parent = body,
})

local page = 1

local function show()
    -- (only the first page carries a name: formatting every page broke on page 3's "% more Qi", release audit 2026-11-12)
    text.Text = if page == 1 then string.format(PAGES[1], player.DisplayName) else PAGES[page]
    for index, dot in dots do
        dot.BackgroundColor3 = if index == page then C.Highlight else C.EdgeDim
        dot.Size = if index == page then UDim2.fromOffset(22, 10) else UDim2.fromOffset(10, 10)
    end
    nextButton.Text = if page < #PAGES then "NEXT" else "THANK YOU"
end

nextButton.Activated:Connect(function()
    Sfx.play("Click")
    if page < #PAGES then
        page += 1
        show()
    else
        window.close()
    end
end)

ProximityPromptService.PromptTriggered:Connect(function(prompt, who)
    if who ~= player or not prompt:GetAttribute("Guide") then
        return
    end
    page = 1
    show()
    window.open()
end)

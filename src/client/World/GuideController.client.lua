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
    "East of the tree is the Qi Spring. Cultivate inside its ring of runes and you gather " .. bonus .. "% more Qi.",
    "The bridges lead to the outer islands. Weaken a guardian, take an egg from its stands and carry it home across the bridge.",
    "Hatch your eggs at the Hatching Sanctum. Brann at the Blacksmith forges weapons, Lyra at the Marketplace sells eggs, and Corvin at Buy & Sell trades your spares for Spirit Stones.",
    "And keep an eye on the north lawn: every hour, for ten minutes, the Wandering Merchant camps there with rare deals. Good luck, cultivator!",
}

local window = Hud.window({
    Name = "GuideWindow", Title = "SEREN, GUIDE", Size = Vector2.new(460, 230), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body

local text = UiKit.label({
    Name = "Line", TextSize = 16, TextWrapped = true, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(0, 6),
    Size = UDim2.new(1, 0, 1, -66), Parent = body,
})
local pageLabel = UiKit.label({
    Name = "Page", Font = "Strong", TextSize = 12, TextColor3 = C.AccentBright, AnchorPoint = Vector2.new(0, 1),
    Position = UDim2.new(0, 0, 1, -14), Size = UDim2.new(0.4, 0, 0, 18), Parent = body,
})
local nextButton = UiKit.button({
    Name = "Next", Font = "Strong", TextSize = 14, Text = "NEXT", Tone = "Accent", AnchorPoint = Vector2.new(1, 1),
    Position = UDim2.new(1, 0, 1, -4), Size = UDim2.fromOffset(150, 44), Parent = body,
})

local page = 1

local function show()
    -- (only the first page carries a name: formatting every page broke on page 3's "% more Qi", release audit 2026-11-12)
    text.Text = if page == 1 then string.format(PAGES[1], player.DisplayName) else PAGES[page]
    pageLabel.Text = page .. " / " .. #PAGES
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

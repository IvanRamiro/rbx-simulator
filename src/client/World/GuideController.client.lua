-- Seren the Guide, on the spawn plaza (WorldBuilder.buildHubNpcs: her prompt carries the Guide attribute). Talking to her opens
-- a short walk through the game, a page at a time: what to do first and where everything in the hub is.
-- She is also where a new player begins (the owner, 2026-11-23: "the tutorial must be shown when the player talked to the NPC, don't show the quest if the players aren't talking
-- to the NPC, but you can guide them to talk with the NPC"): until they have talked to her (their GuideMet setting, set by the server: World/GuideService) there is no quest and no
-- tutorial, only a card at the top ("Talk to Seren"), a marker over her and the gold arrow (Quests/GuideArrow) to lead them to her. The first time, her walk has one more page, the
-- one that sends them off to their first quest, and when it closes the tutorial card and the quest panel arrive (TutorialController, QuestController).
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local WorldMarkers = require(UI:WaitForChild("WorldMarkers"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local player = Players.LocalPlayer
local bonus = GameConfig.TrainingStation.QiBonusPercent

local PAGES = {
    "Welcome to Yggdrasil, %s! I'm Seren. This island, around the great World Tree, is your home. Let me show you around.",
    "Press E to cultivate and gather Qi. On a phone, tap the lotus button. The more Qi you gather, the higher your rank, and the brighter your aura.",
    "You start next to your own pen. Put pets in it and watch them walk around. At the end of the south-east road, jump across the stepping stones to the Blossom Sanctuary: cultivate on its Training Ground for " .. bonus .. "% more Qi.",
    "The bridges lead to the other islands. Hit a guardian until it is weak, take an egg from its stands and carry it home across the bridge.",
    "Hatch your eggs at the Hatching Sanctum, up the north road. The shops are to the north-east: Brann at the Blacksmith makes weapons, Lyra runs the Auction House, where players bid on each other's pets and weapons, and Corvin at Buy & Sell buys your extra pets and weapons.",
    "One more thing: every hour, for ten minutes, the Wandering Merchant visits the platform on the north side of the World Tree. He sells special deals. Good luck, cultivator!",
}

-- the first time only: the page that hands the player over to their first quest
local FIRST_PAGE = "Your first quest is ready. Press E to cultivate and gather Qi (on a phone, tap the lotus button). Your quest is at the top right, and a gold arrow will always point to where to go next. Off you go!"

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
for index = 1, #PAGES + 1 do
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
local count = #PAGES -- the pages in this telling: one more the first time

local function show()
    -- (only the first page carries a name: formatting every page broke on page 3's "% more Qi", release audit 2026-11-12)
    text.Text = if page == 1 then string.format(PAGES[1], player.DisplayName) elseif page > #PAGES then FIRST_PAGE else PAGES[page]
    for index, dot in dots do
        dot.Visible = index <= count
        dot.BackgroundColor3 = if index == page then C.Highlight else C.EdgeDim
        dot.Size = if index == page then UDim2.fromOffset(22, 10) else UDim2.fromOffset(10, 10)
    end
    nextButton.Text = if page < count then "NEXT" elseif count > #PAGES then "BEGIN" else "THANK YOU"
end

nextButton.Activated:Connect(function()
    Sfx.play("Click")
    if page < count then
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
    -- (read before the server's answer to this very trigger flips it: the first meeting has the extra page)
    count = if player:GetAttribute("SettingGuideMet") == false then #PAGES + 1 else #PAGES
    page = 1
    show()
    window.open()
end)

-- ---------- leading a new player to her ----------
-- a card at the top centre (Hud.Banner), a marker over her in the world, both only until the player has talked to her
local compact = Hud.isCompact()
local call = UiKit.panel({
    Name = "GuideCall", Brackets = false, Size = UDim2.fromOffset(if compact then 290 else 340, 70), LayoutOrder = -13, Visible = false, Parent = Hud.Banner,
})
UiKit.boldLabel({ Name = "Word", TextSize = 13, Text = "WELCOME, CULTIVATOR", TextColor3 = C.Edge, Position = UDim2.fromOffset(14, 7), Size = UDim2.new(1, -28, 0, 18), Parent = call })
UiKit.boldLabel({
    Name = "Line", Font = "Title", TextSize = 16, Text = "Talk to Seren, the Guide", TextColor3 = C.Highlight, Position = UDim2.fromOffset(14, 25),
    Size = UDim2.new(1, -28, 0, 22), Parent = call,
})
local callHint = UiKit.label({
    Name = "Hint", Font = "Strong", TextSize = 12, TextColor3 = C.Text, Position = UDim2.fromOffset(14, 47), Size = UDim2.new(1, -28, 0, 16),
    TextTruncate = Enum.TextTruncate.AtEnd, Parent = call,
})
local marker = WorldMarkers.new(C.Highlight, true)

local seren = nil -- her root part, once she has loaded
local function findSeren()
    if seren and seren.Parent then
        return seren
    end
    for _, model in CollectionService:GetTagged("HubNpc") do
        if model.Name == "Guide" then
            local root = model:FindFirstChild("HumanoidRootPart")
            if root and root:IsA("BasePart") then
                seren = root
                return root
            end
        end
    end
    return nil
end

local nextCheck = 0
RunService.RenderStepped:Connect(function()
    local now = os.clock()
    if now < nextCheck then
        return
    end
    nextCheck = now + 0.15
    local waiting = player:GetAttribute("SettingGuideMet") == false
    local rootPart = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local her = if waiting then findSeren() else nil
    local windowOpen = not Hud.Dock.Visible
    call.Visible = waiting and not windowOpen and player:GetAttribute("FactionTrial") ~= "Running" -- (a faction trial's banner has the top to itself)
    if not (waiting and rootPart and her) or windowOpen then
        marker.world = nil
        return
    end
    local distance = (her.Position - rootPart.Position).Magnitude
    callHint.Text = if distance > 14 then "Follow the gold arrow  ·  " .. math.floor(distance) .. " studs"
        else (if UiKit.usingTouch() then "Tap TALK beside her to begin." else "Press F beside her to begin.")
    marker.world = if distance > 14 then her.Position + Vector3.new(0, 6, 0) else nil
    marker.label.Text = "SEREN, GUIDE  " .. math.floor(distance) .. " studs"
end)

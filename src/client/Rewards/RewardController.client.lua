-- The rewards window (the Rewards button on the HUD's rail): the seven days of the login streak with
-- today's to claim, a code box, and the group reward when GameConfig.Rewards.Group has a GroupId. The
-- server decides everything (server/Rewards/RewardService); the "DailyReady", "DailyDay" and
-- "GroupClaimed" attributes carry the state here, and the button shows a dot while a claim waits.
-- Also announces offline Qi on joining.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local RewardRules = require(ReplicatedStorage:WaitForChild("RewardRules"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local DAYS = #GameConfig.Rewards.Daily
local GROUP = GameConfig.Rewards.Group
local hasGroup = GROUP.GroupId > 0

local toggleButton, setBadge = Hud.topButton("RewardsButton", UiTheme.Icons.Rewards, 1)
-- the body, top down: the seven days, CLAIM, the code row, the group's row (UiTheme's measures)
local DAY_HEIGHT = 96
local GAP = UiTheme.Space.M
local CLAIM_Y = DAY_HEIGHT + GAP
local CODE_Y = CLAIM_Y + UiTheme.Height.ButtonLarge + GAP
local GROUP_Y = CODE_Y + UiTheme.Height.Field + GAP
local BODY = (if hasGroup then GROUP_Y + UiTheme.Height.Button else CODE_Y + UiTheme.Height.Field)
local window = Hud.window({
    Name = "RewardsWindow", Title = "DAILY REWARDS", Size = Vector2.new(480, BODY + UiTheme.Height.TitleBar + UiTheme.Space.M + UiTheme.Pad.Window),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body
local message = Toast.new("RewardMessage", C.Highlight, 5)

-- the seven days
local cards = {}
local CARD_GAP = UiTheme.Space.S - 2
for day = 1, DAYS do
    local share = 1 / DAYS
    -- a square tile per day (the bold look): its day, the stone's picture, the number, and any Qi it adds
    local card = UiKit.card({
        Name = "Day" .. day, Position = UDim2.new((day - 1) * share, CARD_GAP / 2, 0, 0),
        Size = UDim2.new(share, -CARD_GAP, 0, DAY_HEIGHT), Parent = body,
    })
    local word = UiKit.label({ Name = "Word", Font = "Heavy", TextSize = 11, TextColor3 = C.Muted, Text = "DAY " .. day,
        Position = UDim2.fromOffset(0, 7), Size = UDim2.new(1, 0, 0, 14), TextXAlignment = Enum.TextXAlignment.Center, Parent = card })
    local stone = Instance.new("ImageLabel")
    stone.Name = "Stone"
    stone.BackgroundTransparency = 1
    stone.Image = UiTheme.Icons.Stones
    stone.AnchorPoint = Vector2.new(0.5, 0)
    stone.Position = UDim2.new(0.5, 0, 0, 24)
    stone.Size = UDim2.fromOffset(24, 24)
    stone.Parent = card
    local amount = UiKit.boldLabel({ Name = "Amount", TextSize = 16, TextColor3 = C.Text,
        Position = UDim2.fromOffset(0, 50), Size = UDim2.new(1, 0, 0, 18), TextXAlignment = Enum.TextXAlignment.Center, Parent = card })
    local extra = UiKit.label({ Name = "Extra", Font = "Heavy", TextSize = 10, TextColor3 = C.Sky,
        Position = UDim2.fromOffset(0, 71), Size = UDim2.new(1, 0, 0, 14), TextXAlignment = Enum.TextXAlignment.Center, Parent = card })
    cards[day] = { card = card, word = word, amount = amount, extra = extra, stone = stone }
end

local claim = UiKit.button({ Name = "Claim", Tone = "Go", TextSize = UiTheme.Text.ButtonLarge, Text = "CLAIM",
    Position = UDim2.fromOffset(0, CLAIM_Y), Size = UDim2.new(1, 0, 0, UiTheme.Height.ButtonLarge), Parent = body })
claim.Activated:Connect(function()
    if claim.Active then
        RemoteEvents.RewardEvent:FireServer("ClaimDaily")
    end
end)

-- the code box
local REDEEM = 120
local codeBox = UiKit.textbox({ Name = "CodeBox", PlaceholderText = "Enter a code", Text = "",
    Position = UDim2.fromOffset(0, CODE_Y), Size = UDim2.new(1, -(REDEEM + UiTheme.Space.S), 0, UiTheme.Height.Field), Parent = body })
local redeem = UiKit.button({ Name = "Redeem", Tone = "Accent", Text = "REDEEM",
    AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, CODE_Y), Size = UDim2.fromOffset(REDEEM, UiTheme.Height.Field), Parent = body })
local function submitCode()
    if codeBox.Text ~= "" then
        RemoteEvents.RewardEvent:FireServer("Redeem", codeBox.Text)
    end
end
redeem.Activated:Connect(submitCode)
codeBox.FocusLost:Connect(function(enterPressed)
    if enterPressed then
        submitCode()
    end
end)

-- the group reward
local groupButton
if hasGroup then
    groupButton = UiKit.button({ Name = "Group", Tone = "Accent", TextSize = 13,
        Position = UDim2.fromOffset(0, GROUP_Y), Size = UDim2.new(1, 0, 0, UiTheme.Height.Button), Parent = body })
    groupButton.Activated:Connect(function()
        if groupButton.Active then
            RemoteEvents.RewardEvent:FireServer("ClaimGroup")
        end
    end)
end

local function render()
    local isReady = player:GetAttribute("DailyReady") == true
    local current = player:GetAttribute("DailyDay") or 1
    local realm = Shop.playerRealmIndex(player)
    for day, c in cards do
        local stones, minutes = RewardRules.daily(day, realm, player)
        c.amount.Text = NumberFormat.compact(stones)
        c.extra.Text = if minutes > 0 then "+" .. minutes .. "m Qi" else "" -- ("+2 MIN QI" didn't fit a day card)
        local claimed = day < current or (day == current and not isReady)
        local isNext = day == current and isReady
        c.word.TextColor3 = if isNext then C.Highlight elseif claimed then C.Buy:Lerp(C.Text, 0.3) else C.Muted
        c.amount.TextColor3 = if claimed then C.Muted else C.Text
        c.word.Text = if claimed then "DONE" else "DAY " .. day
        c.stone.ImageTransparency = if claimed then 0.55 else 0
        -- today's card is lit gold, fill and edge; the days taken fall back
        c.card.BackgroundColor3 = if isNext then C.Raised:Lerp(C.Highlight, 0.22) else C.Raised
        c.card.BackgroundTransparency = if claimed then 0.45 else 0.12
        local edge = c.card:FindFirstChildOfClass("UIStroke")
        edge.Color = if isNext then C.Highlight else C.EdgeDim
        edge.Transparency = if isNext then 0 else 0.3
        edge:SetAttribute("Keep", isNext)
    end
    claim.Active = isReady
    claim.AutoButtonColor = false
    claim:SetAttribute("Tone", if isReady then "Go" else "Quiet")
    claim.Text = if isReady then "CLAIM DAY " .. current else "COME BACK TOMORROW"
    setBadge(if isReady then "!" else nil, "Highlight")
    if groupButton then
        local done = player:GetAttribute("GroupClaimed") == true
        groupButton.Active = not done
        groupButton.Text = if done then "GROUP REWARD CLAIMED"
            else "JOIN OUR GROUP, THEN CLAIM  +" .. NumberFormat.compact(GROUP.Stones) .. " STONES"
    end
end

for _, name in { "DailyReady", "DailyDay", "GroupClaimed", "Pass_VIP" } do
    player:GetAttributeChangedSignal(name):Connect(render)
end
task.spawn(function()
    player:WaitForChild("leaderstats"):WaitForChild("Rank").Changed:Connect(render)
    render()
end)
render()

window.link(toggleButton)
toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        render()
        window.open()
    end
end)

RemoteEvents.RewardEvent.OnClientEvent:Connect(function(kind, a, b, c)
    if kind == "Offline" and typeof(a) == "number" and typeof(b) == "number" then
        local hours = b / 3600
        local away = if hours >= 1 then string.format("%.1f hours", hours) else math.floor(b / 60) .. " minutes"
        Sfx.play("RewardClaim")
        message:show("Your Qi kept flowing for " .. away .. " while you were away: +" .. NumberFormat.compact(a) .. " Qi.", "Reward")
    elseif kind == "Daily" and typeof(a) == "number" then
        Sfx.play("RewardClaim")
        local qi = if typeof(b) == "number" and b > 0 then "  +" .. NumberFormat.compact(b) .. " Qi" else ""
        message:show("Day " .. tostring(c) .. " claimed: +" .. NumberFormat.compact(a) .. " Spirit Stones" .. qi, "Reward")
    elseif (kind == "Code" or kind == "Group") and typeof(b) == "string" then
        Sfx.play(if a then "RewardClaim" else "Error")
        message:show(b, if a then "Reward" else "Error")
        if kind == "Code" and a then
            codeBox.Text = ""
        end
    end
end)

-- The QUEST tracker (the HUD's top right): the current quest (GameConfig.Quests, at the
-- player's "QuestStep" attribute, which the server moves on), its goal, a bar for one with a
-- count (the "QuestProgress" attribute), its reward, and SKIP (asks once more). A finished
-- quest is announced with its reward (QuestEvent "Complete"); after the last, the tracker goes.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local QUESTS = GameConfig.Quests
local CONFIRM_SECONDS = 3

-- ---------- the tracker ----------
local panel = UiKit.panel({ Name = "QuestTracker", AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.fromOffset(270, 0), Visible = false, Parent = Hud.Quest })
local inner = Instance.new("Frame")
inner.Name = "Inner"
inner.BackgroundTransparency = 1
inner.AutomaticSize = Enum.AutomaticSize.Y
inner.Size = UDim2.new(1, 0, 0, 0)
inner.Parent = panel
UiKit.padding(inner, 14, 10)
UiKit.list(inner, { Padding = UDim.new(0, 5) })

local header = UiKit.header(inner, "QUEST", { TextSize = 13, LayoutOrder = 1 })
local count = UiKit.label({
    Name = "Count", Font = "Strong", TextSize = 11, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0.5),
    Position = UDim2.fromScale(1, 0.5), Size = UDim2.fromOffset(40, 14), TextXAlignment = Enum.TextXAlignment.Right,
    Parent = header,
})
local title = UiKit.label({
    Name = "Title", Font = "Title", TextSize = 15, TextColor3 = C.Highlight, AutomaticSize = Enum.AutomaticSize.Y,
    Size = UDim2.new(1, 0, 0, 0), TextWrapped = true, LayoutOrder = 2, Parent = inner,
})
local body = UiKit.label({
    Name = "Text", TextSize = 12, TextColor3 = C.Text, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0),
    TextWrapped = true, LayoutOrder = 3, Parent = inner,
})
local bar = UiKit.bar({ Name = "Progress", Size = UDim2.new(1, 0, 0, 5), LayoutOrder = 4, Parent = inner })

local footer = Instance.new("Frame")
footer.Name = "Footer"
footer.BackgroundTransparency = 1
footer.Size = UDim2.new(1, 0, 0, 22)
footer.LayoutOrder = 5
footer.Parent = inner
local reward = UiKit.label({
    Name = "Reward", Font = "Strong", TextSize = 11, TextColor3 = C.AccentBright, Size = UDim2.new(1, -70, 1, 0),
    Parent = footer,
})
local skip = UiKit.button({
    Name = "Skip", Font = "Strong", TextSize = 10, Text = "SKIP", Tone = "Quiet", AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.fromScale(1, 0), Size = UDim2.fromOffset(62, 22), Parent = footer,
})

local message = Toast.new("QuestMessage", C.Highlight, 4)

local function render()
    local step = player:GetAttribute("QuestStep")
    local quest = typeof(step) == "number" and QUESTS[step]
    panel.Visible = if quest then true else false
    if not quest then
        return
    end
    count.Text = step .. " / " .. #QUESTS
    title.Text = quest.Title
    body.Text = quest.Text
    reward.Text = "REWARD  " .. NumberFormat.compact(quest.Reward) .. " Spirit Stones"
    -- a bar only where there is a count to fill (Qi, a rank's Qi)
    bar.Visible = quest.Kind == "Qi" or quest.Kind == "Rank"
end

local function renderProgress()
    local share = player:GetAttribute("QuestProgress")
    UiKit.setBar(bar, if typeof(share) == "number" then share else 0)
end

player:GetAttributeChangedSignal("QuestStep"):Connect(render)
player:GetAttributeChangedSignal("QuestProgress"):Connect(renderProgress)
render()
renderProgress()

-- skipping them all asks once more
local armedUntil = 0
skip.Activated:Connect(function()
    if os.clock() < armedUntil then
        RemoteEvents.QuestEvent:FireServer("Skip")
        return
    end
    armedUntil = os.clock() + CONFIRM_SECONDS
    skip.Text = "SURE?"
    task.delay(CONFIRM_SECONDS, function()
        if os.clock() >= armedUntil then
            skip.Text = "SKIP"
        end
    end)
end)

RemoteEvents.QuestEvent.OnClientEvent:Connect(function(kind, step, stones)
    if kind ~= "Complete" or typeof(step) ~= "number" or not QUESTS[step] then
        return
    end
    Sfx.play("Attune")
    local paid = if typeof(stones) == "number" and stones > 0 then "  +" .. NumberFormat.compact(stones) .. " Spirit Stones" else ""
    if step == #QUESTS then
        message:show("Quest complete: " .. QUESTS[step].Title .. "." .. paid .. "\nThe path is yours now, cultivator.", C.Highlight)
    else
        message:show("Quest complete: " .. QUESTS[step].Title .. "." .. paid, C.Highlight)
    end
end)

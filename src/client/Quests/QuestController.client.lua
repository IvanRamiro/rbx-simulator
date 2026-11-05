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
local UiFx = require(UI:WaitForChild("UiFx"))
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
local rewardIcon = Instance.new("ImageLabel")
rewardIcon.Name = "RewardIcon"
rewardIcon.BackgroundTransparency = 1
rewardIcon.Image = UiTheme.Icons.Stones
rewardIcon.AnchorPoint = Vector2.new(0, 0.5)
rewardIcon.Position = UDim2.fromScale(0, 0.5)
rewardIcon.Size = UDim2.fromOffset(18, 18)
rewardIcon.Parent = footer
local reward = UiKit.label({
    Name = "Reward", Font = "Strong", TextSize = 12, TextColor3 = C.AccentBright, Position = UDim2.fromOffset(23, 0),
    Size = UDim2.new(1, -93, 1, 0), Parent = footer,
})
local skip = UiKit.button({
    Name = "Skip", Font = "Strong", TextSize = 11, Text = "Skip", Tone = "Quiet", AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.fromScale(1, 0), Size = UDim2.fromOffset(62, 22), Parent = footer,
})

local message = Toast.new("QuestMessage", C.Highlight, 4)

-- The Quests button on the rail shows or hides it, and the choice is saved.
local questButton = Hud.railButton("QuestButton", UiTheme.Icons.Quest, "Quests", 4)
local function questAllowed()
    local chosen = player:GetAttribute("SettingShowQuest")
    if chosen == nil then
        chosen = GameConfig.Settings.ShowQuest
    end
    questButton:SetAttribute("Tone", if chosen then "Accent" else "Quiet")
    return chosen == true
end

local lastStep = nil
local function render()
    local step = player:GetAttribute("QuestStep")
    local quest = typeof(step) == "number" and QUESTS[step]
    panel.Visible = quest ~= nil and questAllowed()
    if not quest then
        return
    end
    count.Text = step .. " / " .. #QUESTS
    title.Text = quest.Title
    body.Text = quest.Text
    if lastStep and lastStep ~= step and panel.Visible then -- a new quest writes itself on
        UiFx.flash(panel, C.Highlight)
        UiFx.typeIn(title, 0.25)
        UiFx.typeIn(body, 0.55)
    end
    lastStep = step
    reward.Text = NumberFormat.compact(quest.Reward) .. " Spirit Stones"
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

questButton.Activated:Connect(function()
    local shown = not questAllowed()
    player:SetAttribute("SettingShowQuest", shown)
    RemoteEvents.SettingsEvent:FireServer("ShowQuest", shown)
end)
player:GetAttributeChangedSignal("SettingShowQuest"):Connect(render)
questAllowed()

-- The guardian board, a page of the Rewards window (GameConfig.Bounty; the server counts and pays: server/Guardians/ConquestService): the guardian marked for
-- today with what its first conquest pays, then every guardian's ladder (its conquests, how far to the next tier, what the tier pays, the title at the end).
-- It draws what BountyEvent tells it ("State") and shows a notice for a "Conquered"; nothing here is asked for or decided.
--
--   BountyPage.new(parent)   builds the page in `parent` (a Frame) and returns it: { Frame, render() }
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local BountyRules = require(ReplicatedStorage:WaitForChild("BountyRules"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local TitleRules = require(ReplicatedStorage:WaitForChild("TitleRules"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local BountyPage = {}

local TODAY_H = 78
local ROW = 70

local function timeLeft(seconds)
    if seconds >= 3600 then
        return string.format("%dh %dm", seconds // 3600, (seconds % 3600) // 60)
    end
    return string.format("%dm", math.max(1, seconds // 60))
end

function BountyPage.new(parent)
    local message = Toast.new("BountyMessage", C.Highlight, 5)
    local scroll = UiKit.scroll({ Name = "BountyPage", Size = UDim2.fromScale(1, 1), Visible = false, Parent = parent })
    local state = nil

    local order = 0
    local function nextOrder()
        order += 1
        return order
    end

    -- today's bounty
    local header = Instance.new("Frame")
    header.Name = "TodayHeader"
    header.BackgroundTransparency = 1
    header.Size = UDim2.new(1, -4, 0, 22)
    header.LayoutOrder = nextOrder()
    header.Parent = scroll
    UiKit.label({ Name = "Title", Font = "Heavy", TextSize = UiTheme.Text.Heading + 2, TextColor3 = C.Highlight, Text = "TODAY'S BOUNTY",
        Size = UDim2.new(0.6, 0, 1, 0), Parent = header })
    local clock = UiKit.label({ Name = "Clock", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 0),
        Size = UDim2.new(0.4, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Right, Parent = header })
    local today = UiKit.card({ Name = "Today", Size = UDim2.new(1, -4, 0, TODAY_H), LayoutOrder = nextOrder(), Parent = scroll })
    local todayName = UiKit.boldLabel({ Name = "Name", TextSize = 17, Position = UDim2.fromOffset(12, 8), Size = UDim2.new(1, -110, 0, 22),
        TextTruncate = Enum.TextTruncate.AtEnd, Parent = today })
    local todayText = UiKit.label({ Name = "Text", TextSize = 13, TextColor3 = C.Muted, Position = UDim2.fromOffset(12, 32), Size = UDim2.new(1, -110, 0, 38),
        TextWrapped = true, TextYAlignment = Enum.TextYAlignment.Top, Parent = today })
    local todayTag = UiKit.label({ Name = "Tag", Font = "Heavy", TextSize = 14, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -12, 0.5, 0),
        Size = UDim2.fromOffset(90, 24), TextXAlignment = Enum.TextXAlignment.Right, Parent = today })

    local ladderHeader = Instance.new("Frame")
    ladderHeader.Name = "LadderHeader"
    ladderHeader.BackgroundTransparency = 1
    ladderHeader.Size = UDim2.new(1, -4, 0, 22)
    ladderHeader.LayoutOrder = nextOrder()
    ladderHeader.Parent = scroll
    UiKit.label({ Name = "Title", Font = "Heavy", TextSize = UiTheme.Text.Heading + 2, TextColor3 = C.Highlight, Text = "CONQUESTS",
        Size = UDim2.new(1, 0, 1, 0), Parent = ladderHeader })

    local rows = {}
    for _, id in GameConfig.Bounty.Order do
        local config = GameConfig.Guardians[id]
        local card = UiKit.card({ Name = id, Size = UDim2.new(1, -4, 0, ROW), LayoutOrder = nextOrder(), Parent = scroll })
        local name = UiKit.boldLabel({ Name = "Name", TextSize = 14, Position = UDim2.fromOffset(12, 7), Size = UDim2.new(1, -120, 0, 20),
            TextTruncate = Enum.TextTruncate.AtEnd, Text = config.DisplayName, Parent = card })
        local count = UiKit.label({ Name = "Count", Font = "Heavy", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0),
            Position = UDim2.new(1, -12, 0, 9), Size = UDim2.fromOffset(100, 18), TextXAlignment = Enum.TextXAlignment.Right, Parent = card })
        local bar = UiKit.bar({ Name = "Progress", Position = UDim2.fromOffset(12, 32), Size = UDim2.new(1, -24, 0, 10), Parent = card })
        local note = UiKit.label({ Name = "Note", TextSize = 12, TextColor3 = C.Muted, Position = UDim2.fromOffset(12, 46), Size = UDim2.new(1, -24, 0, 18),
            TextTruncate = Enum.TextTruncate.AtEnd, Parent = card })
        rows[id] = { card = card, count = count, bar = bar, note = note, name = name, title = config.DisplayName }
    end

    local function render()
        local realm = Shop.playerRealmIndex(player)
        local day = GoalRules.dayKey()
        local marked = BountyRules.marked(day)
        local fresh = state ~= nil and state.Day == day
        local dayPaid = fresh and state.DayPaid == true
        local counts = if state then state.Counts else {}
        local paid = if state then state.Paid else {}
        local config = GameConfig.Guardians[marked]
        clock.Text = "resets in " .. timeLeft(GoalRules.secondsLeft("Daily"))
        todayName.Text = if config then config.DisplayName else marked
        todayText.Text = if dayPaid then "The bounty is taken. A new guardian is marked tomorrow."
            else string.format("Bring it down once today: +%s Spirit Stones.", NumberFormat.compact(BountyRules.dailyStones(realm)))
        todayName.TextColor3 = if dayPaid then C.Muted else C.Text
        todayTag.Text = if dayPaid then "TAKEN" else "OPEN"
        todayTag.TextColor3 = if dayPaid then C.Buy else Color3.fromRGB(255, 200, 70)
        for _, id in GameConfig.Bounty.Order do
            local row = rows[id]
            local n = counts[id] or 0
            local reached = BountyRules.reached(n)
            local tiers = BountyRules.tiers
            local nextIndex, nextTier = BountyRules.nextTier(n)
            row.name.Text = if id == marked then row.title .. "  -  BOUNTY TODAY" else row.title
            row.name.TextColor3 = if id == marked then Color3.fromRGB(255, 200, 70) else C.Text
            row.count.Text = string.format("%d conquest%s", n, if n == 1 then "" else "s")
            if nextTier then
                local from = if reached > 0 then tiers[reached].Conquests else 0
                UiKit.setBar(row.bar, (n - from) / (nextTier.Conquests - from), true)
                UiKit.setBarColor(row.bar, C.Accent)
                row.note.Text = string.format("%d more for +%s stones (tier %d of %d)", nextTier.Conquests - n,
                    NumberFormat.compact(BountyRules.tierStones(nextIndex, realm)), nextIndex, #tiers)
                row.note.TextColor3 = C.Muted
            else
                UiKit.setBar(row.bar, 1, true)
                UiKit.setBarColor(row.bar, C.Highlight)
                local titleId = TitleRules.ConquestTitleIds[id]
                local title = titleId and TitleRules.ById[titleId]
                row.note.Text = if title then "Every tier done: the " .. title.Text .. " title is yours." else "Every tier done."
                row.note.TextColor3 = C.Highlight
            end
            if (paid[id] or 0) < reached then
                row.note.Text = "Paying..." -- (the server pays a tier the moment it is reached; this is only the moment between)
            end
        end
    end

    RemoteEvents.BountyEvent.OnClientEvent:Connect(function(kind, a, b, c, d, e)
        if kind == "State" and typeof(a) == "table" then
            state = a
            render()
        elseif kind == "Conquered" and typeof(a) == "string" then
            local config = GameConfig.Guardians[a]
            local parts = {}
            if typeof(c) == "number" and c > 0 then
                table.insert(parts, "bounty +" .. NumberFormat.compact(c))
            end
            if typeof(d) == "number" and d > 0 then
                table.insert(parts, "tier +" .. NumberFormat.compact(d))
            end
            Sfx.play(if #parts > 0 then "RewardClaim" else "Notify")
            message:show(string.format("Conquest! %s brought down %s time%s.%s", if config then config.DisplayName else a, tostring(b),
                if b == 1 then "" else "s", if #parts > 0 then " Spirit Stones: " .. table.concat(parts, ", ") .. "." else ""), "Reward")
        end
    end)

    task.spawn(function()
        while true do
            task.wait(30)
            if scroll.Visible then
                render()
            end
        end
    end)
    RemoteEvents.BountyEvent:FireServer("Get")
    render()

    return { Frame = scroll, render = render }
end

return BountyPage

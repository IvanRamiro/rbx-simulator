-- The goals page of the Rewards window (the owner, 2026-11-24: "daily or weekly goals beyond the quest chain"): today's three goals and this week's three, each
-- with its progress bar and a CLAIM, and what finishing all three pays. The server counts and pays (server/Rewards/GoalService); this only draws what GoalEvent
-- tells it ("State") and asks to claim. Which goals a player has is shared/GoalRules.pick from their id and the period, so nothing but the progress is sent.
--
--   GoalsPage.new(parent)   builds the page in `parent` (a Frame) and returns it: { Frame, render() }
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local GoalsPage = {}

local ROW = 66
local BONUS_ROW = 44
local SCOPES = { { Scope = "Daily", Title = "TODAY" }, { Scope = "Weekly", Title = "THIS WEEK" } }

local function timeLeft(seconds)
    if seconds >= 86400 then
        return string.format("%dd %dh", seconds // 86400, (seconds % 86400) // 3600)
    elseif seconds >= 3600 then
        return string.format("%dh %dm", seconds // 3600, (seconds % 3600) // 60)
    end
    return string.format("%dm", math.max(1, seconds // 60))
end

function GoalsPage.new(parent)
    local message = Toast.new("GoalMessage", C.Highlight, 5)
    local scroll = UiKit.scroll({ Name = "GoalsPage", Size = UDim2.fromScale(1, 1), Visible = false, Parent = parent })

    local state = nil -- the server's last State
    local rows = {}   -- [scope] = { header, time, goals = { { card, text, bar, count, button, goal } }, bonus = { card, text, tag } }

    local function sectionHeader(title, order)
        local holder = Instance.new("Frame")
        holder.Name = title .. "Header"
        holder.BackgroundTransparency = 1
        holder.Size = UDim2.new(1, -4, 0, 22)
        holder.LayoutOrder = order
        holder.Parent = scroll
        UiKit.label({ Name = "Title", Font = "Heavy", TextSize = UiTheme.Text.Heading + 2, TextColor3 = C.Highlight, Text = title,
            Size = UDim2.new(0.5, 0, 1, 0), Parent = holder })
        local clock = UiKit.label({ Name = "Clock", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 0),
            Size = UDim2.new(0.5, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Right, Parent = holder })
        return clock
    end

    local order = 0
    for _, spec in SCOPES do
        order += 1
        local entry = { goals = {} }
        entry.clock = sectionHeader(spec.Title, order)
        for slot = 1, GameConfig.Goals[spec.Scope].Count do
            order += 1
            local card = UiKit.card({ Name = spec.Scope .. slot, Size = UDim2.new(1, -4, 0, ROW), LayoutOrder = order, Parent = scroll })
            local text = UiKit.boldLabel({ Name = "Text", TextSize = 14, Position = UDim2.fromOffset(12, 8), Size = UDim2.new(1, -124, 0, 20),
                TextTruncate = Enum.TextTruncate.AtEnd, Parent = card })
            local bar = UiKit.bar({ Name = "Progress", Position = UDim2.fromOffset(12, 38), Size = UDim2.new(1, -184, 0, 10), Parent = card })
            local count = UiKit.label({ Name = "Count", Font = "Heavy", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(0, 0),
                Position = UDim2.new(1, -164, 0, 32), Size = UDim2.fromOffset(46, 22), TextXAlignment = Enum.TextXAlignment.Left, Parent = card })
            local button = UiKit.button({ Name = "Claim", Tone = "Go", TextSize = 13, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -8, 0.5, 0),
                Size = UDim2.fromOffset(104, UiTheme.Height.Button), Parent = card })
            table.insert(entry.goals, { card = card, text = text, bar = bar, count = count, button = button })
        end
        order += 1
        local bonus = UiKit.card({ Name = spec.Scope .. "Bonus", Size = UDim2.new(1, -4, 0, BONUS_ROW), LayoutOrder = order, Parent = scroll })
        local bonusText = UiKit.label({ Name = "Text", Font = "Strong", TextSize = 13, Position = UDim2.fromOffset(12, 0), Size = UDim2.new(1, -110, 1, 0),
            TextTruncate = Enum.TextTruncate.AtEnd, Parent = bonus })
        local tag = UiKit.label({ Name = "Tag", Font = "Heavy", TextSize = 12, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 0),
            Size = UDim2.fromOffset(88, BONUS_ROW), TextXAlignment = Enum.TextXAlignment.Right, Parent = bonus })
        entry.bonus = { card = bonus, text = bonusText, tag = tag }
        rows[spec.Scope] = entry
        order += 1
        local gap = Instance.new("Frame") -- (a little air between the two sections)
        gap.Name = "Gap"
        gap.BackgroundTransparency = 1
        gap.Size = UDim2.new(1, 0, 0, 4)
        gap.LayoutOrder = order
        gap.Parent = scroll
    end

    local lastAsked = {}
    local function render()
        local realm = Shop.playerRealmIndex(player)
        for _, spec in SCOPES do
            local scope, entry = spec.Scope, rows[spec.Scope]
            local key = if scope == "Weekly" then GoalRules.weekKey() else GoalRules.dayKey()
            -- progress counts only for the period the server's state is for (a new day not yet told is empty)
            local fresh = state ~= nil and (if scope == "Weekly" then state.Week else state.Day) == key
            local progress = if fresh then (if scope == "Weekly" then state.WeekProgress else state.DayProgress) else {}
            local claimed = if fresh then (if scope == "Weekly" then state.WeekClaimed else state.DayClaimed) else {}
            local bonusPaid = fresh and (if scope == "Weekly" then state.WeekBonus else state.DayBonus) == true
            local picks = GoalRules.pick(scope, player.UserId, key)
            local stones = GoalRules.stones(scope, realm)
            local allDone = #picks > 0
            entry.clock.Text = "resets in " .. timeLeft(GoalRules.secondsLeft(scope))
            for slot, row in entry.goals do
                local goal = picks[slot]
                row.card.Visible = goal ~= nil
                if goal then
                    local have = progress[goal.Id] or 0
                    local done = have >= goal.Target
                    local isClaimed = claimed[goal.Id] == true
                    allDone = allDone and isClaimed
                    row.text.Text = GoalRules.label(goal)
                    row.text.TextColor3 = if isClaimed then C.Muted else C.Text
                    UiKit.setBar(row.bar, have / goal.Target, true)
                    UiKit.setBarColor(row.bar, if done then C.Highlight else C.Accent)
                    row.count.Text = string.format("%d / %d", have // goal.Unit, goal.Target // goal.Unit)
                    row.button:SetAttribute("GoalId", goal.Id)
                    row.button.Active = done and not isClaimed
                    row.button:SetAttribute("Tone", if done and not isClaimed then "Go" else "Quiet")
                    row.button.Text = if isClaimed then "DONE" elseif done then "CLAIM +" .. NumberFormat.compact(stones) else "+" .. NumberFormat.compact(stones)
                    row.card.BackgroundTransparency = if isClaimed then 0.5 else 0.15
                end
            end
            local bonusStones, minutes = GoalRules.bonus(scope, realm)
            entry.bonus.text.Text = string.format("All %d done: +%s stones%s", #picks, NumberFormat.compact(bonusStones),
                if minutes > 0 then string.format(" and %d minutes of 2x Qi", minutes) else "")
            entry.bonus.text.TextColor3 = if bonusPaid then C.Muted else if allDone then C.Highlight else C.Text
            entry.bonus.tag.Text = if bonusPaid then "TAKEN" elseif allDone then "..." else ""
            entry.bonus.tag.TextColor3 = if bonusPaid then C.Buy else C.Muted
        end
    end

    for _, entry in rows do
        for slot, row in entry.goals do
            row.button.Activated:Connect(function()
                if not row.button.Active then
                    return
                end
                local scope = if entry == rows.Weekly then "Weekly" else "Daily"
                local id = row.button:GetAttribute("GoalId")
                if typeof(id) ~= "string" or os.clock() - (lastAsked[id] or 0) < 0.8 then
                    return
                end
                lastAsked[id] = os.clock()
                row.button.Active = false -- (until the server's word comes back)
                RemoteEvents.GoalEvent:FireServer("Claim", scope, id)
            end)
        end
    end

    RemoteEvents.GoalEvent.OnClientEvent:Connect(function(kind, a, b, c, d, e)
        if kind == "State" and typeof(a) == "table" then
            state = a
            render()
        elseif kind == "Claimed" and typeof(b) == "string" and typeof(c) == "number" then
            Sfx.play("RewardClaim")
            local extra = ""
            if typeof(d) == "number" and d > 0 then
                extra = "  Bonus: +" .. NumberFormat.compact(d) .. " stones"
                    .. (if typeof(e) == "number" and e > 0 then " and " .. e .. " minutes of 2x Qi" else "")
            end
            message:show("Goal done: +" .. NumberFormat.compact(c) .. " Spirit Stones." .. extra, "Reward")
        end
    end)

    -- the clocks tick over (and a new day is told by the server within a minute)
    task.spawn(function()
        while true do
            task.wait(30)
            if scroll.Visible then
                render()
            end
        end
    end)
    RemoteEvents.GoalEvent:FireServer("Get")
    render()

    return { Frame = scroll, render = render }
end

return GoalsPage

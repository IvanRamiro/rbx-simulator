-- The faction page of the Rewards window, for a member (GameConfig.Renown; the server counts and pays: server/Factions/StandingService): their rank and the renown to the next,
-- the daily cache, this week's rivalry between the three factions, and last week's result with the Victory share to take. It draws what StandingEvent tells it ("State") and
-- asks to claim ("Cache", "Victory"); nothing is decided here.
--
--   FactionPage.new(parent)   builds the page in `parent` (a Frame) and returns it: { Frame, render() }
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local StandingRules = require(ReplicatedStorage:WaitForChild("StandingRules"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local CONFIG = GameConfig.Renown

local FactionPage = {}

local function timeLeft(seconds)
    if seconds >= 86400 then
        return string.format("%dd %dh", seconds // 86400, (seconds % 86400) // 3600)
    elseif seconds >= 3600 then
        return string.format("%dh %dm", seconds // 3600, (seconds % 3600) // 60)
    end
    return string.format("%dm", math.max(1, seconds // 60))
end

function FactionPage.new(parent)
    local message = Toast.new("FactionStandingMessage", C.Highlight, 5)
    local scroll = UiKit.scroll({ Name = "FactionPage", Size = UDim2.fromScale(1, 1), Visible = false, Parent = parent })
    local state = nil
    local order = 0
    local function nextOrder()
        order += 1
        return order
    end
    local function header(text, withClock)
        local holder = Instance.new("Frame")
        holder.Name = text .. "Header"
        holder.BackgroundTransparency = 1
        holder.Size = UDim2.new(1, -4, 0, 22)
        holder.LayoutOrder = nextOrder()
        holder.Parent = scroll
        local title = UiKit.label({ Name = "Title", Font = "Heavy", TextSize = UiTheme.Text.Heading + 2, TextColor3 = C.Highlight, Text = text,
            Size = UDim2.new(0.6, 0, 1, 0), Parent = holder })
        local clock = if withClock then UiKit.label({ Name = "Clock", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0),
            Position = UDim2.new(1, 0, 0, 0), Size = UDim2.new(0.4, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Right, Parent = holder }) else nil
        return title, clock
    end

    -- rank
    local rankTitle = header("RANK")
    local rankCard = UiKit.card({ Name = "Rank", Size = UDim2.new(1, -4, 0, 78), LayoutOrder = nextOrder(), Parent = scroll })
    local rankName = UiKit.boldLabel({ Name = "Name", TextSize = 17, Position = UDim2.fromOffset(12, 8), Size = UDim2.new(1, -24, 0, 22), TextTruncate = Enum.TextTruncate.AtEnd, Parent = rankCard })
    local rankBar = UiKit.bar({ Name = "Progress", Position = UDim2.fromOffset(12, 36), Size = UDim2.new(1, -24, 0, 10), Parent = rankCard })
    local rankNote = UiKit.label({ Name = "Note", TextSize = 12, TextColor3 = C.Muted, Position = UDim2.fromOffset(12, 52), Size = UDim2.new(1, -24, 0, 30),
        TextWrapped = true, TextYAlignment = Enum.TextYAlignment.Top, Parent = rankCard })

    -- the daily cache
    header("DAILY CACHE")
    local cacheCard = UiKit.card({ Name = "Cache", Size = UDim2.new(1, -4, 0, 62), LayoutOrder = nextOrder(), Parent = scroll })
    local cacheText = UiKit.label({ Name = "Text", Font = "Strong", TextSize = 13, Position = UDim2.fromOffset(12, 0), Size = UDim2.new(1, -140, 1, 0),
        TextWrapped = true, Parent = cacheCard })
    local cacheButton = UiKit.button({ Name = "Claim", Tone = "Go", TextSize = 13, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -8, 0.5, 0),
        Size = UDim2.fromOffset(116, UiTheme.Height.Button), Parent = cacheCard })

    -- the week's rivalry
    local _, weekClock = header("THIS WEEK", true)
    local rows = {}
    for _, id in GameConfig.Faction.Order do
        local info = GameConfig.Faction.Factions[id]
        local card = UiKit.card({ Name = id, Size = UDim2.new(1, -4, 0, 52), LayoutOrder = nextOrder(), Parent = scroll })
        local name = UiKit.boldLabel({ Name = "Name", TextSize = 14, Position = UDim2.fromOffset(12, 6), Size = UDim2.new(0.6, 0, 0, 18), Text = info.Short, TextColor3 = info.Color, Parent = card })
        local score = UiKit.label({ Name = "Score", Font = "Heavy", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 8),
            Size = UDim2.new(0.4, 0, 0, 16), TextXAlignment = Enum.TextXAlignment.Right, Parent = card })
        local bar = UiKit.bar({ Name = "Share", Position = UDim2.fromOffset(12, 30), Size = UDim2.new(1, -24, 0, 12), Parent = card })
        UiKit.setBarColor(bar, info.Color)
        rows[id] = { card = card, score = score, bar = bar, name = name, info = info }
    end
    local weekNote = UiKit.label({ Name = "WeekNote", TextSize = 12, TextColor3 = C.Muted, Size = UDim2.new(1, -4, 0, 64), TextWrapped = true,
        TextYAlignment = Enum.TextYAlignment.Top, LayoutOrder = nextOrder(), Parent = scroll })

    -- last week
    header("LAST WEEK")
    local lastCard = UiKit.card({ Name = "Last", Size = UDim2.new(1, -4, 0, 70), LayoutOrder = nextOrder(), Parent = scroll })
    local lastText = UiKit.label({ Name = "Text", Font = "Strong", TextSize = 13, Position = UDim2.fromOffset(12, 0), Size = UDim2.new(1, -140, 1, 0),
        TextWrapped = true, Parent = lastCard })
    local lastButton = UiKit.button({ Name = "Victory", Tone = "Go", TextSize = 13, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -8, 0.5, 0),
        Size = UDim2.fromOffset(116, UiTheme.Height.Button), Parent = lastCard })

    local function render()
        local faction = player:GetAttribute("Faction")
        local info = typeof(faction) == "string" and GameConfig.Faction.Factions[faction] or nil
        if not (info and state) then
            rankName.Text = if info then "Reading your standing..." else "Join a faction to earn renown."
            return
        end
        local realm = Shop.playerRealmIndex(player)
        local rank = StandingRules.rankOf(state.Renown)
        rankTitle.Text = string.upper(info.Short) .. " RANK"
        rankName.Text = string.format("%s  -  rank %d of %d  -  %s renown", StandingRules.rankName(faction, rank) or "?", rank, StandingRules.ranks, NumberFormat.compact(state.Renown))
        rankName.TextColor3 = info.Color
        local nextRank, need = StandingRules.nextRank(state.Renown)
        if nextRank then
            local from = CONFIG.Thresholds[rank]
            UiKit.setBar(rankBar, (state.Renown - from) / (need - from), true)
            UiKit.setBarColor(rankBar, info.Color)
            local stones = StandingRules.rankStones(nextRank, realm)
            rankNote.Text = string.format("%s more renown for %s: +%s Spirit Stones and the %s %s title.",
                NumberFormat.compact(need - state.Renown), StandingRules.rankName(faction, nextRank) or "?", NumberFormat.compact(stones), info.Short, StandingRules.rankName(faction, nextRank) or "")
        else
            UiKit.setBar(rankBar, 1, true)
            UiKit.setBarColor(rankBar, C.Highlight)
            rankNote.Text = "The highest rank. Renown still counts for your faction's week."
        end
        -- the cache
        local cache = StandingRules.cacheStones(rank, realm)
        cacheText.Text = if state.CacheReady then string.format("The faction's daily cache: +%s Spirit Stones (a higher rank, a bigger cache).", NumberFormat.compact(cache))
            else "Taken today. The cache fills again tomorrow."
        cacheButton.Active = state.CacheReady
        cacheButton:SetAttribute("Tone", if state.CacheReady then "Go" else "Quiet")
        cacheButton.Text = if state.CacheReady then "CLAIM +" .. NumberFormat.compact(cache) else "TAKEN"
        -- the week
        weekClock.Text = "resets in " .. timeLeft(GoalRules.secondsLeft("Weekly"))
        local top = 0
        for id in rows do
            top = math.max(top, StandingRules.score(state.Totals[id]))
        end
        for id, row in rows do
            local entry = state.Totals[id] or { Renown = 0, Members = 0 }
            local score = StandingRules.score(entry)
            UiKit.setBar(row.bar, if top > 0 then score / top else 0, true)
            row.score.Text = string.format("%s per member  -  %d earning", NumberFormat.compact(math.floor(score)), entry.Members)
            row.name.Text = row.info.Short .. (if id == faction then "  (yours)" else "")
        end
        weekNote.Text = string.format("Renown comes from goals you finish, guardians you conquer and eggs you carry home. You earned %s this week (%s needed to share in a victory). A faction's score is its renown per member who earned any, so a bigger crowd does not win by size.",
            NumberFormat.compact(state.WeekRenown), tostring(CONFIG.War.MinRenown))
        -- last week
        local last = state.Last
        local winnerInfo = last.Winner and GameConfig.Faction.Factions[last.Winner]
        local canTake = last.Ready and last.Winner == faction and last.Mine >= CONFIG.War.MinRenown and not last.Claimed
        if not last.Ready then
            lastText.Text = "Last week's result is not in yet."
        elseif not winnerInfo then
            lastText.Text = "Last week had no winner."
        elseif last.Winner ~= faction then
            lastText.Text = string.format("Last week the %s won. Earn renown this week to win the next.", winnerInfo.DisplayName)
        elseif last.Mine < CONFIG.War.MinRenown then
            lastText.Text = string.format("Your faction won last week, but you earned %d renown and %d were needed to share in it.", last.Mine, CONFIG.War.MinRenown)
        elseif last.Claimed then
            lastText.Text = "Your faction won last week and you have taken your share."
        else
            lastText.Text = string.format("Your faction won last week! Your share: +%s Spirit Stones and %d minutes of 2x Qi.", NumberFormat.compact(StandingRules.warStones(realm)), CONFIG.War.BoostMinutes)
        end
        lastButton.Active = canTake
        lastButton:SetAttribute("Tone", if canTake then "Go" else "Quiet")
        lastButton.Text = if canTake then "TAKE SHARE" elseif last.Claimed then "TAKEN" else "-"
    end

    cacheButton.Activated:Connect(function()
        if cacheButton.Active then
            cacheButton.Active = false
            RemoteEvents.StandingEvent:FireServer("Cache")
        end
    end)
    lastButton.Activated:Connect(function()
        if lastButton.Active then
            lastButton.Active = false
            RemoteEvents.StandingEvent:FireServer("Victory")
        end
    end)

    RemoteEvents.StandingEvent.OnClientEvent:Connect(function(kind, a, b, c)
        if kind == "State" and typeof(a) == "table" then
            state = a
            render()
        elseif kind == "Paid" and typeof(a) == "string" and typeof(b) == "number" then
            Sfx.play("RewardClaim")
            if a == "Cache" then
                message:show("Faction cache: +" .. NumberFormat.compact(b) .. " Spirit Stones.", "Reward")
            elseif a == "Victory" then
                message:show("Your faction won the week! +" .. NumberFormat.compact(b) .. " Spirit Stones" .. (if typeof(c) == "number" and c > 0 then " and " .. c .. " minutes of 2x Qi." else "."), "Reward")
            elseif a == "Rank" then
                message:show("New faction rank! +" .. NumberFormat.compact(b) .. " Spirit Stones.", "Reward")
            end
        end
    end)
    player:GetAttributeChangedSignal("Faction"):Connect(function()
        RemoteEvents.StandingEvent:FireServer("Get")
        render()
    end)
    task.spawn(function()
        while true do
            task.wait(30)
            if scroll.Visible then
                render()
            end
        end
    end)
    RemoteEvents.StandingEvent:FireServer("Get")
    render()

    return { Frame = scroll, render = render }
end

return FactionPage

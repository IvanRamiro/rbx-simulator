-- The Murim factions' window (GameConfig.Faction, shared/FactionRules; the server decides everything: server/Factions). Anyone may talk to
-- a faction's representative and read about it, a page at a time: who they are, how they fight, what a member gets. The last page is the
-- decision. A pledge is for good, so it says so first (on every page, and again on the decision page), and it takes two separate
-- confirmations, each with a wait before its button wakes (ConfirmDialog), before the request goes out.
-- The prompt on a representative (a ProximityPrompt with the FactionTalk attribute and its Faction) opens the window; the prompt on a
-- faction's vault (FactionVault) asks the server for the faction's secret weapon once the trial is passed.
-- The server's answers: "Joined" (the ceremony), "Taken" (the weapon), "Refused" (why, in plain words).
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local FactionRules = require(ReplicatedStorage:WaitForChild("FactionRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local client = script.Parent.Parent
local UI = client:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local ConfirmDialog = require(UI:WaitForChild("ConfirmDialog"))
local Sfx = require(client:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local C = UiTheme.Colors
local Event = RemoteEvents.FactionEvent
local config = GameConfig.Faction
local FOOT = UiTheme.Height.Button
local GAP = UiTheme.Space.M
local BANNER = 66

local message = Toast.new("FactionMessage", C.Highlight, 6)
local DANGER_HEX = C.Danger:ToHex()

local window = Hud.window({
    Name = "FactionWindow", Title = "FACTION", Size = Vector2.new(560, 372), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body

-- the faction's name and its master, in its own colour
local banner = UiKit.card({ Name = "Banner", Size = UDim2.new(1, 0, 0, BANNER), Parent = body })
UiKit.boldCard(banner, C.Edge)
local hqLabel = UiKit.boldLabel({
    Name = "Hq", TextSize = 22, TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromOffset(UiTheme.Pad.Card + 2, 6),
    Size = UDim2.new(1, -(UiTheme.Pad.Card + 2) * 2, 0, 28), Parent = banner,
})
local masterLabel = UiKit.label({
    Name = "Master", Font = "Strong", TextSize = 14, TextColor3 = C.Text, TextXAlignment = Enum.TextXAlignment.Left,
    Position = UDim2.fromOffset(UiTheme.Pad.Card + 2, 36), Size = UDim2.new(1, -(UiTheme.Pad.Card + 2) * 2, 0, 22), Parent = banner,
})

-- what they say, a page at a time
local speech = UiKit.card({
    Name = "Speech", Position = UDim2.fromOffset(0, BANNER + GAP), Size = UDim2.new(1, 0, 1, -(BANNER + GAP + FOOT + GAP)), Parent = body,
})
local pageTitle = UiKit.label({
    Name = "PageTitle", Font = "Heavy", TextSize = 14, TextColor3 = C.Highlight, TextXAlignment = Enum.TextXAlignment.Left,
    Position = UDim2.fromOffset(UiTheme.Pad.Card + 2, UiTheme.Pad.Card), Size = UDim2.new(1, -(UiTheme.Pad.Card + 2) * 2, 0, 20), Parent = speech,
})
local pageText = UiKit.label({
    Name = "PageText", Font = "Strong", TextSize = 15, TextWrapped = true, RichText = true, TextYAlignment = Enum.TextYAlignment.Top,
    Position = UDim2.fromOffset(UiTheme.Pad.Card + 2, UiTheme.Pad.Card + 24),
    Size = UDim2.new(1, -(UiTheme.Pad.Card + 2) * 2, 1, -(UiTheme.Pad.Card * 2 + 24 + 22)), Parent = speech,
})
-- on every page, so nobody reaches the decision without having been told
UiKit.label({
    Name = "Forever", Font = "Heavy", TextSize = 12, TextColor3 = C.Danger, TextXAlignment = Enum.TextXAlignment.Left,
    AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, UiTheme.Pad.Card + 2, 1, -UiTheme.Pad.Card + 2),
    Size = UDim2.new(1, -(UiTheme.Pad.Card + 2) * 2, 0, 16), Text = "Joining a faction is for good.", Parent = speech,
})

local dotRow = Instance.new("Frame")
dotRow.Name = "Dots"
dotRow.BackgroundTransparency = 1
dotRow.AnchorPoint = Vector2.new(0, 1)
dotRow.Position = UDim2.new(0, 4, 1, -FOOT / 2 + 6)
dotRow.Size = UDim2.new(0.3, 0, 0, 12)
dotRow.Parent = body
UiKit.list(dotRow, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center })
local dots = {}
for index = 1, #config.Factions.Orthodox.Pages + 1 do
    local dot = Instance.new("Frame")
    dot.Name = "Dot" .. index
    dot.BorderSizePixel = 0
    dot.Size = UDim2.fromOffset(10, 10)
    dot.LayoutOrder = index
    dot.Parent = dotRow
    UiKit.corner(dot, 5)
    dots[index] = dot
end

local backButton = UiKit.button({
    Name = "Back", Text = "BACK", Tone = "Quiet", AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -170, 1, 0),
    Size = UDim2.fromOffset(110, FOOT), Parent = body,
})
local nextButton = UiKit.button({
    Name = "Next", Text = "NEXT", Tone = "Go", AnchorPoint = Vector2.new(1, 1), Position = UDim2.fromScale(1, 1),
    Size = UDim2.fromOffset(160, FOOT), Parent = body,
})

local viewing = nil -- the faction's id being read
local page = 1
local busy = false

-- (state, text): what the decision page can offer this player now
local function standing(factionId)
    local own = FactionRules.of(player)
    local info = config.Factions[factionId]
    if own then
        local ownInfo = config.Factions[own]
        if own == factionId then
            return "Member", "You belong to the " .. ownInfo.DisplayName .. ". Welcome home."
        end
        return "Member", "You belong to the " .. ownInfo.DisplayName .. ". A faction is for good, so you can't join the " .. info.DisplayName .. "."
    end
    if not FactionRules.ready(player) then
        return "Loading", "Checking your record. One moment..."
    end
    if not FactionRules.canJoin(Ranks.getPlayerRankName(player)) then
        return "Locked", "Reach the " .. config.JoinRealm .. " realm to join a faction. You can still look around and read."
    end
    return "Open", "Ready to join? Think hard. " .. "<font color=\"#" .. DANGER_HEX .. "\">" .. config.Forever .. "</font>"
end

local function render()
    if not viewing then
        return
    end
    local info = config.Factions[viewing]
    local pages = #info.Pages + 1
    page = math.clamp(page, 1, pages)
    hqLabel.Text = string.upper(info.DisplayName) .. "  -  " .. info.Hq
    hqLabel.TextColor3 = info.Color
    masterLabel.Text = info.Master .. ": \"" .. info.Motto .. "\""
    banner:FindFirstChildOfClass("UIStroke").Color = info.Color
    local canJoin = false
    if page <= #info.Pages then
        pageTitle.Text = info.Pages[page].Title
        pageText.Text = info.Pages[page].Text
    else
        local state, text = standing(viewing)
        pageTitle.Text = if state == "Member" then "YOUR FACTION" else "JOIN?"
        pageText.Text = (if state == "Open" or state == "Locked" then config.Equal .. "\n\n" else "") .. text
        canJoin = state == "Open"
    end
    for index, dot in dots do
        dot.Visible = index <= pages
        dot.BackgroundColor3 = if index == page then info.Color else C.EdgeDim
        dot.Size = if index == page then UDim2.fromOffset(22, 10) else UDim2.fromOffset(10, 10)
    end
    backButton.Visible = page > 1
    if page < pages then
        nextButton.Visible = true
        nextButton.Text = "NEXT"
        nextButton:SetAttribute("Tone", "Go")
    else
        nextButton.Visible = canJoin and not busy
        nextButton.Text = "JOIN"
        nextButton:SetAttribute("Tone", "Danger")
    end
end

local function open(factionId)
    if not config.Factions[factionId] then
        return
    end
    viewing, page = factionId, 1
    render()
    window.open()
end

backButton.Activated:Connect(function()
    Sfx.play("Click")
    page -= 1
    render()
end)

-- two confirmations, each waking its button only after a wait: then the request
local function pledge(factionId)
    local info = config.Factions[factionId]
    ConfirmDialog.show({
        Title = "JOIN FOR GOOD?",
        Text = "Join the " .. info.DisplayName .. "?\n\n" .. config.Forever .. "\nThere is no way back.",
        ConfirmText = "I UNDERSTAND", CancelText = "NOT YET", ConfirmTone = "Danger", Seconds = 3,
        OnConfirm = function()
            ConfirmDialog.show({
                Title = "LAST CHANCE",
                Text = "You will be " .. info.Short .. " for the rest of your time in this game. Are you sure?",
                ConfirmText = "JOIN FOREVER", CancelText = "NO, GO BACK", ConfirmTone = "Danger", Seconds = 4,
                OnConfirm = function()
                    if busy or FactionRules.of(player) then
                        return
                    end
                    busy = true
                    render()
                    Event:FireServer("Join", factionId)
                    task.delay(15, function() -- (no answer: the button wakes again)
                        if busy then
                            busy = false
                            render()
                        end
                    end)
                end,
            })
        end,
    })
end

nextButton.Activated:Connect(function()
    Sfx.play("Click")
    local info = viewing and config.Factions[viewing]
    if not info then
        return
    end
    if page <= #info.Pages then
        page += 1
        render()
    elseif standing(viewing) == "Open" and not busy then
        pledge(viewing)
    end
end)

-- ---------- the ceremony ----------
local function ceremony(factionId)
    local info = config.Factions[factionId]
    local gui = Instance.new("ScreenGui")
    gui.Name = "FactionCeremony"
    gui.ResetOnSpawn = false
    gui.IgnoreGuiInset = true
    gui.DisplayOrder = 60
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = playerGui

    local flash = Instance.new("Frame")
    flash.Name = "Flash"
    flash.BackgroundColor3 = info.Deep
    flash.BackgroundTransparency = 1
    flash.BorderSizePixel = 0
    flash.Size = UDim2.fromScale(1, 1)
    flash.Parent = gui

    local column = Instance.new("Frame")
    column.Name = "Column"
    column.BackgroundTransparency = 1
    column.AnchorPoint = Vector2.new(0.5, 0.5)
    column.Position = UDim2.fromScale(0.5, 0.42)
    column.Size = UDim2.fromScale(0.8, 0.3)
    column.Parent = gui
    local constraint = Instance.new("UISizeConstraint")
    constraint.MaxSize = Vector2.new(760, 220)
    constraint.Parent = column

    local function line(text, y, height, color, big)
        local label = (if big then UiKit.boldLabel else UiKit.label)({
            Text = text, Font = "Heavy", TextScaled = true, TextColor3 = color, TextTransparency = 1,
            TextXAlignment = Enum.TextXAlignment.Center, Position = UDim2.fromScale(0, y), Size = UDim2.fromScale(1, height), Parent = column,
        })
        local limit = Instance.new("UITextSizeConstraint")
        limit.MaxTextSize = if big then 54 else 22
        limit.Parent = label
        return label
    end
    local small = line("YOU HAVE JOINED THE", 0, 0.2, C.Text, false)
    local big = line(string.upper(info.DisplayName), 0.22, 0.42, info.Color, true)
    local motto = line(info.Motto, 0.7, 0.2, C.Text, false)

    local inTime, hold, outTime = 0.7, 3.2, 1.4
    TweenService:Create(flash, TweenInfo.new(inTime), { BackgroundTransparency = 0.4 }):Play()
    for _, label in { small, big, motto } do
        TweenService:Create(label, TweenInfo.new(inTime), { TextTransparency = 0 }):Play()
        local outline = label:FindFirstChildOfClass("UIStroke")
        if outline then
            outline.Transparency = 1
            TweenService:Create(outline, TweenInfo.new(inTime), { Transparency = 0 }):Play()
        end
    end
    Sfx.play("RewardClaim")
    task.delay(inTime + hold, function()
        TweenService:Create(flash, TweenInfo.new(outTime), { BackgroundTransparency = 1 }):Play()
        for _, label in { small, big, motto } do
            TweenService:Create(label, TweenInfo.new(outTime), { TextTransparency = 1 }):Play()
            local outline = label:FindFirstChildOfClass("UIStroke")
            if outline then
                TweenService:Create(outline, TweenInfo.new(outTime), { Transparency = 1 }):Play()
            end
        end
        task.delay(outTime + 0.1, function()
            gui:Destroy()
        end)
    end)
end

-- ---------- the server's answers ----------
Event.OnClientEvent:Connect(function(kind, argument)
    if kind == "Joined" and config.Factions[argument] then
        busy = false
        if window.isOpen() then
            window.close()
        end
        ceremony(argument)
    elseif kind == "Refused" and typeof(argument) == "string" then
        busy = false
        render()
        message:show(argument, "Warning")
    elseif kind == "Taken" and typeof(argument) == "string" then
        local owner = FactionRules.weaponFaction(argument)
        local info = owner and config.Factions[owner]
        Sfx.play("RewardClaim")
        message:show("You took the " .. (if info then info.Weapon.Name else "weapon") .. ". It is in your weapons.", "Reward")
    end
end)

-- ---------- the prompts ----------
ProximityPromptService.PromptTriggered:Connect(function(prompt, who)
    if who ~= player then
        return
    end
    local factionId = prompt:GetAttribute("Faction")
    if prompt:GetAttribute("FactionTalk") then
        open(factionId)
    elseif prompt:GetAttribute("FactionVault") and config.Factions[factionId] then
        if FactionRules.of(player) ~= factionId then
            message:show("This vault belongs to the " .. config.Factions[factionId].DisplayName .. ".", "Warning")
            return
        end
        Event:FireServer("Take")
    end
end)

-- the window stays true while it is open (the pledge or the rank may change under it)
task.spawn(function()
    while true do
        task.wait(0.5)
        if window.isOpen() then
            render()
        end
    end
end)

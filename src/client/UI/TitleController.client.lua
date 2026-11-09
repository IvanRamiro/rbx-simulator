-- Titles (the owner, November 9, 2026): a nameplate over every player, the title they wear over their name, in the
-- title's own colour (a light running across the grandest); and the Titles window (the Titles button on the HUD's rail):
-- every title by section, earned or locked with how to earn it, to choose which to wear: one of them, Auto (Developer,
-- else Beta Tester, else the highest realm's) or none. A new title is announced and badged on the button.
-- The server (server/Titles) decides what is earned; the "Title" attribute on each player is what they show.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local TitleRules = require(ReplicatedStorage:WaitForChild("TitleRules"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local Toast = require(script.Parent:WaitForChild("Toast"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local C = UiTheme.Colors

local PLATE_DISTANCE = 90 -- studs past which a nameplate isn't drawn
local ROW = 54

-- ---------- a title, drawn ----------
-- Every title's text is white under a gradient of its colour; a shimmer is a band of light running across it.
local shimmers = setmetatable({}, { __mode = "k" }) -- [UIGradient] = true

local function styleTitle(label, entry)
    label.TextColor3 = Color3.new(1, 1, 1)
    local gradient = label:FindFirstChild("TitleColor") or Instance.new("UIGradient")
    gradient.Name = "TitleColor"
    if entry.Shimmer then
        gradient.Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, entry.Color), ColorSequenceKeypoint.new(0.4, entry.Color),
            ColorSequenceKeypoint.new(0.5, entry.Shimmer), ColorSequenceKeypoint.new(0.6, entry.Color), ColorSequenceKeypoint.new(1, entry.Color),
        })
        shimmers[gradient] = true
    else
        gradient.Color = ColorSequence.new(entry.Color)
        gradient.Offset = Vector2.zero
        shimmers[gradient] = nil
    end
    gradient.Parent = label
end

RunService.Heartbeat:Connect(function()
    local x = (os.clock() * 0.45) % 2.4 - 1.2 -- the band crosses, then rests off the edge a moment
    for gradient in shimmers do
        gradient.Offset = Vector2.new(x, 0)
    end
end)

-- ---------- nameplates ----------
local plates = {} -- [Player] = { gui, title, name }

local function renderPlate(owner)
    local plate = plates[owner]
    if not plate then
        return
    end
    local entry = TitleRules.ById[owner:GetAttribute("Title") or ""]
    plate.title.Visible = entry ~= nil
    if entry then
        plate.title.Text = entry.Text
        styleTitle(plate.title, entry)
    end
    plate.name.Text = owner.DisplayName
end

local function removePlate(owner)
    local plate = plates[owner]
    if plate then
        plate.gui:Destroy()
        plates[owner] = nil
    end
end

local function buildPlate(owner, character)
    removePlate(owner)
    local head = character:WaitForChild("Head", 10)
    local humanoid = character:WaitForChild("Humanoid", 10)
    if not (head and humanoid) or owner.Character ~= character then
        return
    end
    humanoid.NameDisplayDistance = 0 -- the nameplate replaces Roblox's own name (its health bar stays)
    local gui = Instance.new("BillboardGui")
    gui.Name = "Nameplate_" .. owner.UserId
    gui.Adornee = head
    gui.Size = UDim2.new(7, 0, 1.5, 0) -- in studs: it shrinks with distance, as the head does
    gui.StudsOffsetWorldSpace = Vector3.new(0, 2.3, 0)
    gui.MaxDistance = PLATE_DISTANCE
    gui.LightInfluence = 0
    gui.ResetOnSpawn = false
    local title = UiKit.label({
        Name = "Title", Font = "Title", TextScaled = true, Size = UDim2.fromScale(1, 0.46), TextXAlignment = Enum.TextXAlignment.Center,
        Parent = gui,
    })
    local titleEdge = Instance.new("UIStroke")
    titleEdge.Color = Color3.fromRGB(10, 10, 30)
    titleEdge.Thickness = 1.5
    titleEdge.Parent = title
    local name = UiKit.label({
        Name = "PlayerName", Font = "Strong", TextScaled = true, Position = UDim2.fromScale(0, 0.5), Size = UDim2.fromScale(1, 0.42),
        TextXAlignment = Enum.TextXAlignment.Center, Parent = gui,
    })
    local nameEdge = Instance.new("UIStroke")
    nameEdge.Color = Color3.fromRGB(10, 10, 30)
    nameEdge.Thickness = 1.2
    nameEdge.Parent = name
    gui.Parent = playerGui
    plates[owner] = { gui = gui, title = title, name = name }
    renderPlate(owner)
end

local function watch(owner)
    owner.CharacterAdded:Connect(function(character)
        buildPlate(owner, character)
    end)
    owner:GetAttributeChangedSignal("Title"):Connect(function()
        renderPlate(owner)
    end)
    if owner.Character then
        task.spawn(buildPlate, owner, owner.Character)
    end
end

Players.PlayerAdded:Connect(watch)
for _, owner in Players:GetPlayers() do
    watch(owner)
end
Players.PlayerRemoving:Connect(removePlate)

-- ---------- the Titles window ----------
local toggleButton, setBadge = Hud.railButton("TitlesButton", UiTheme.Icons.Titles, "Titles", 5)
local window = Hud.window({
    Name = "TitlesWindow", Title = "TITLES", Size = Vector2.new(400, 470), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body
local book = { Earned = {}, Worn = "Auto", Showing = nil }
local earnedSet = {}
local unseen = 0

-- the top: what they show now, and Auto and Hide
UiKit.label({ Name = "ShowingWord", Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = "SHOWING",
    Size = UDim2.new(1, -150, 0, 14), Parent = body })
local showing = UiKit.label({ Name = "Showing", Font = "Title", TextSize = 18, Position = UDim2.fromOffset(0, 15),
    Size = UDim2.new(1, -150, 0, 24), TextTruncate = Enum.TextTruncate.AtEnd, Parent = body })
local autoButton = UiKit.button({ Name = "Auto", Font = "Strong", Text = "AUTO", TextSize = 12, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, -74, 0, 6), Size = UDim2.fromOffset(66, 28), Parent = body })
local hideButton = UiKit.button({ Name = "Hide", Font = "Strong", Text = "HIDE", TextSize = 12, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, 6), Size = UDim2.fromOffset(66, 28), Parent = body })
local count = UiKit.label({ Name = "Count", TextSize = 11, TextColor3 = C.Muted, Position = UDim2.fromOffset(0, 42),
    Size = UDim2.new(1, 0, 0, 14), Parent = body })
local list = UiKit.scroll({ Name = "List", Position = UDim2.fromOffset(0, 62), Size = UDim2.new(1, 0, 1, -62), Parent = body })

local rows = {} -- [id] = { button, title, how, card }
local render

local function wear(choice)
    Sfx.play("Click")
    book.Worn = choice
    RemoteEvents.TitleEvent:FireServer("Wear", choice)
end
autoButton.Activated:Connect(function()
    wear("Auto")
end)
hideButton.Activated:Connect(function()
    wear("None")
end)

local order = 0
for _, group in TitleRules.Groups do
    order += 1
    local header = Instance.new("Frame")
    header.Name = group.Id .. "Header"
    header.BackgroundTransparency = 1
    header.Size = UDim2.new(1, 0, 0, 22)
    header.LayoutOrder = order
    header.Parent = list
    UiKit.header(header, group.Name, { TextSize = 12 })
    for _, entry in TitleRules.List do
        if entry.Group ~= group.Id then
            continue
        end
        order += 1
        local card = UiKit.card({ Name = entry.Id, Size = UDim2.new(1, 0, 0, ROW), LayoutOrder = order, Stripe = entry.Color, Parent = list })
        local title = UiKit.label({ Name = "Text", Font = "Title", TextSize = 16, Text = entry.Text, Position = UDim2.fromOffset(12, 7),
            Size = UDim2.new(1, -112, 0, 20), TextTruncate = Enum.TextTruncate.AtEnd, Parent = card })
        local how = UiKit.label({ Name = "How", TextSize = 11, TextColor3 = C.Muted, Text = entry.How, TextWrapped = true,
            TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(12, 28), Size = UDim2.new(1, -112, 0, 24), Parent = card })
        local button = UiKit.button({ Name = "Wear", Font = "Strong", TextSize = 11, AnchorPoint = Vector2.new(1, 0.5),
            Position = UDim2.new(1, -8, 0.5, 0), Size = UDim2.fromOffset(86, 28), Parent = card })
        button.Activated:Connect(function()
            if earnedSet[entry.Id] and book.Worn ~= entry.Id then
                wear(entry.Id)
                render()
            end
        end)
        rows[entry.Id] = { button = button, title = title, how = how, card = card }
    end
end

render = function()
    local earnedCount = 0
    for _, entry in TitleRules.List do
        local row = rows[entry.Id]
        local has = earnedSet[entry.Id] == true
        earnedCount += if has then 1 else 0
        local wearing = book.Worn == entry.Id
        if has then
            styleTitle(row.title, entry)
        else
            local gradient = row.title:FindFirstChild("TitleColor")
            if gradient then
                shimmers[gradient] = nil
                gradient:Destroy()
            end
            row.title.TextColor3 = C.Muted
        end
        row.card.BackgroundTransparency = if has then 0.35 else 0.6
        row.button.Text = if wearing then "WEARING" elseif has then "WEAR" else "LOCKED"
        row.button:SetAttribute("Tone", if wearing then "Accent" else "Quiet")
        row.button.AutoButtonColor = false
        row.button.Active = has and not wearing
        row.button.TextTransparency = if has then 0 else 0.45
    end
    -- the Developer row only for those who have it: nobody else can earn it
    rows.Developer.card.Visible = earnedSet.Developer == true
    local total = #TitleRules.List - (if earnedSet.Developer then 0 else 1)
    count.Text = string.format("%d of %d earned", earnedCount, total)
    local shown = TitleRules.ById[player:GetAttribute("Title") or ""]
    if shown then
        showing.Text = shown.Text
        styleTitle(showing, shown)
    else
        local gradient = showing:FindFirstChild("TitleColor")
        if gradient then
            shimmers[gradient] = nil
            gradient:Destroy()
        end
        showing.TextColor3 = C.Muted
        showing.Text = "No title"
    end
    autoButton:SetAttribute("Tone", if book.Worn == "Auto" then "Accent" else "Quiet")
    hideButton:SetAttribute("Tone", if book.Worn == "None" then "Accent" else "Quiet")
end

player:GetAttributeChangedSignal("Title"):Connect(render)

local notice = Toast.new("TitleMessage", C.Highlight, 4)
RemoteEvents.TitleEvent.OnClientEvent:Connect(function(kind, data)
    if kind == "State" then
        book = data
        earnedSet = {}
        for _, id in data.Earned do
            earnedSet[id] = true
        end
        render()
    elseif kind == "EarnedOnJoin" then -- the ones they qualified for, found as they joined: one notice for them all
        if not window.isOpen() then
            unseen += data
            setBadge(tostring(unseen), "Highlight")
        end
        notice:show(if data == 1 then "NEW TITLE: open Titles to wear it" else data .. " NEW TITLES: open Titles to wear them", C.Highlight)
        Sfx.play("Attune")
    elseif kind == "Earned" then
        local entry = TitleRules.ById[data]
        if entry then
            if not window.isOpen() then
                unseen += 1
                setBadge(tostring(unseen), "Highlight")
            end
            notice:show("NEW TITLE: " .. entry.Text, entry.Color)
            Sfx.play("Attune")
        end
    end
end)

toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        unseen = 0
        setBadge(nil)
        render()
        window.open()
    end
end)

render()
RemoteEvents.TitleEvent:FireServer("Get")

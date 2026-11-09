-- Titles (the owner, November 9, 2026): a nameplate over every player, the title they wear over their name, in the
-- title's own lettering and colour, a sheen of light sweeping across it; and the Titles window (the Titles button on the
-- HUD's rail): every title by section, earned or locked with how to earn it, to choose which to wear: one of them, Auto
-- (Developer, else Content Creator, else Beta Tester, else the highest realm's) or none. A new title is announced and
-- badged on the button. The server (server/Titles) decides what is earned; the "Title" attribute on each player is what
-- they show.
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
-- Every title in its own lettering (TitleRules' Font) and colour, and now and then a sheen sweeps across it: a slanted band
-- of light with a white-hot core, as off polished metal, lighting the letters and their outline together (in the letters
-- alone, a narrow band was hardly seen: the owner). A grander title (its Shimmer) sweeps more often, its band tinted its own
-- colour. Each title keeps its own moment, so a crowd of nameplates never flashes at once.
local SHEEN = { -- band half-width (along the text), seconds between sweeps, seconds a sweep takes
    Plain = { Width = 0.2, Period = 3.4, Sweep = 1.0 },
    Grand = { Width = 0.26, Period = 2.3, Sweep = 1.1 },
}
local EDGE = Color3.fromRGB(14, 12, 34) -- the outline's colour, away from the sheen
local WHITE = Color3.new(1, 1, 1)
local WEIGHTS = {
    [100] = Enum.FontWeight.Thin, [200] = Enum.FontWeight.ExtraLight, [300] = Enum.FontWeight.Light, [400] = Enum.FontWeight.Regular,
    [500] = Enum.FontWeight.Medium, [600] = Enum.FontWeight.SemiBold, [700] = Enum.FontWeight.Bold, [800] = Enum.FontWeight.ExtraBold,
    [900] = Enum.FontWeight.Heavy,
}
-- [UIGradient] = { Period, Sweep, Phase }. A plain table, cleared as each gradient leaves the game: weak keys dropped them
-- (an Instance's Lua handle is collected while the Instance lives on) and every sheen froze where it was.
local shimmers = {}

local function fontOf(entry)
    local f = entry.Font
    return Font.new("rbxasset://fonts/families/" .. f[1] .. ".json", WEIGHTS[f[2]] or Enum.FontWeight.Regular,
        if f[3] == "Italic" then Enum.FontStyle.Italic else Enum.FontStyle.Normal)
end

-- a band across a base colour, at the middle of a gradient (its Offset carries it across): a halo of its own colour, then
-- a white-hot core (tinted toward its own colour, the band read as hardly more than a change of shade: the owner)
local function band(base, halo, w)
    return ColorSequence.new({
        ColorSequenceKeypoint.new(0, base), ColorSequenceKeypoint.new(0.5 - w, base),
        ColorSequenceKeypoint.new(0.5 - w * 0.55, halo), ColorSequenceKeypoint.new(0.5 - w * 0.18, WHITE),
        ColorSequenceKeypoint.new(0.5 + w * 0.18, WHITE), ColorSequenceKeypoint.new(0.5 + w * 0.55, halo),
        ColorSequenceKeypoint.new(0.5 + w, base), ColorSequenceKeypoint.new(1, base),
    })
end

local function gradientIn(parent, name)
    local gradient = parent:FindFirstChild(name) or Instance.new("UIGradient")
    gradient.Name = name
    gradient.Rotation = 18 -- slanted, as a glint is
    gradient.Parent = parent
    return gradient
end

local function edgeOf(label)
    local edge = label:FindFirstChild("TitleEdge")
    if not edge then
        edge = Instance.new("UIStroke")
        edge.Name = "TitleEdge"
        edge.Thickness = label:GetAttribute("EdgeThickness") or 1
        edge.Parent = label
    end
    return edge
end

local function styleTitle(label, entry)
    label.FontFace = fontOf(entry)
    label.TextColor3 = WHITE
    local kind = if entry.Shimmer then SHEEN.Grand else SHEEN.Plain
    local halo = if entry.Shimmer then entry.Shimmer else entry.Color:Lerp(WHITE, 0.55)
    local letters = gradientIn(label, "TitleColor")
    letters.Color = band(entry.Color, halo, kind.Width)
    local edge = edgeOf(label)
    edge.Color = WHITE
    edge.Transparency = 0
    local glow = gradientIn(edge, "TitleGlow")
    glow.Color = band(EDGE, halo, kind.Width * 1.1)
    local old = shimmers[letters]
    local phase = if old then old.Phase else math.random() * kind.Period
    shimmers[letters] = { Period = kind.Period, Sweep = kind.Sweep, Phase = phase }
    shimmers[glow] = { Period = kind.Period, Sweep = kind.Sweep, Phase = phase }
end

-- a title not earned, or no title: plain, in this colour
local function plainTitle(label, color, entry)
    if entry then
        label.FontFace = fontOf(entry)
    end
    local letters = label:FindFirstChild("TitleColor")
    if letters then
        shimmers[letters] = nil
        letters:Destroy()
    end
    local edge = edgeOf(label)
    local glow = edge:FindFirstChild("TitleGlow")
    if glow then
        shimmers[glow] = nil
        glow:Destroy()
    end
    edge.Color = EDGE
    edge.Transparency = 0.4
    label.TextColor3 = color
end

RunService.Heartbeat:Connect(function()
    local now = os.clock()
    for gradient, sheen in shimmers do
        if not gradient:IsDescendantOf(game) then
            shimmers[gradient] = nil -- its nameplate went with its character
            continue
        end
        local t = (now + sheen.Phase) % sheen.Period
        -- across from beyond its left edge to beyond its right, then resting out of sight until the next
        local x = if t < sheen.Sweep then -1 + 2 * (t / sheen.Sweep) else 1
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
    gui.Size = UDim2.new(8, 0, 1.7, 0) -- in studs: it shrinks with distance, as the head does
    gui.StudsOffsetWorldSpace = Vector3.new(0, 2.3, 0)
    gui.MaxDistance = PLATE_DISTANCE
    gui.LightInfluence = 0
    gui.ResetOnSpawn = false
    local title = UiKit.label({
        Name = "Title", Font = "Title", TextScaled = true, Size = UDim2.fromScale(1, 0.5), TextXAlignment = Enum.TextXAlignment.Center,
        Parent = gui,
    })
    title:SetAttribute("EdgeThickness", 2)
    local name = UiKit.label({
        Name = "PlayerName", Font = "Strong", TextScaled = true, Position = UDim2.fromScale(0, 0.54), Size = UDim2.fromScale(1, 0.4),
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
local showing = UiKit.label({ Name = "Showing", Font = "Title", TextSize = 20, Position = UDim2.fromOffset(0, 15),
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
        local title = UiKit.label({ Name = "Text", Font = "Title", TextSize = 18, Text = entry.Text, Position = UDim2.fromOffset(12, 5),
            Size = UDim2.new(1, -112, 0, 22), TextTruncate = Enum.TextTruncate.AtEnd, Parent = card })
        title.FontFace = fontOf(entry)
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
            plainTitle(row.title, C.Muted, entry)
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
        plainTitle(showing, C.Muted)
        showing.FontFace = UiTheme.Fonts.Title
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

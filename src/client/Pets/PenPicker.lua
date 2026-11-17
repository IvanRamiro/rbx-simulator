-- The pen window: the player's one beast pen (PenService). At the top, its level and how many beasts it holds, and the upgrade: the
-- next level's room and price in Spirit Stones, with a green UPGRADE button (the server checks the level, the price and the stones,
-- and is the only place that spends). Below, the beasts in the pen (REMOVE), then every other pet (ADD; an equipped one must be
-- unequipped first; PEN FULL when there is no room). Opened at the pen's gate or board (PenController), or from the Pets window's PEN
-- button, anywhere.
--   PenPicker.open(upgrade)       opens it (upgrade: true, opened at the board's UPGRADE PEN prompt: the upgrade card is lit)
--   PenPicker.setSnapshot(s)      the inventory as PetController last received it (PetInventory.getSnapshot: Pets, Pen, PenLevel)
--   PenPicker.showPasture()       a marker on the way to the player's pasture, for a while
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Toast = require(UI:WaitForChild("Toast"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local WorldMarkers = require(UI:WaitForChild("WorldMarkers"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local PenPicker = {}

local RARITY_ORDER = { Divine = 8, Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }
local ROW_H = 64
local BUTTON = UiTheme.Height.Button
local CARD_H = 104
local LIST_MIN = 140 -- the list's least height beside the card (a heading and about two rows)

local snapshot = nil
local window -- (made on first open)
local message = Toast.new("PenMessage", Color3.new(1, 1, 1), 3)

-- ---------- the way to the pasture ----------
local marker, markerUntil = nil, 0
local function pastureConfig()
    local index = player:GetAttribute("PastureIndex")
    local folder = ReplicatedStorage:FindFirstChild("BeastPastures")
    return if typeof(index) == "number" and index > 0 and folder then folder:FindFirstChild(tostring(index)) else nil
end

function PenPicker.showPasture()
    local config = pastureConfig()
    local frame = config and config:GetAttribute("Frame")
    if typeof(frame) ~= "CFrame" then
        message:show("All the pens in this server are taken. Your pen is saved, and it will show up when one is free.", "Info")
        return
    end
    if not marker then
        marker = WorldMarkers.new(C.Highlight, true)
    end
    marker.world = frame.Position + Vector3.new(0, 8, 0)
    marker.label.Text = "YOUR PEN"
    markerUntil = os.clock() + 25
end
RunService.Heartbeat:Connect(function()
    if not marker or not marker.world then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if (root and (root.Position - marker.world).Magnitude < 45) or os.clock() > markerUntil then
        marker.world = nil
    end
end)

-- ---------- the window ----------
local levelLabel, card, list
local cardParts = {}
local portraitPool = {} -- ["PetId#size"] = { frames }

local function portrait(petId, size, parent)
    local key = petId .. "#" .. size
    local spare = portraitPool[key]
    local frame = (spare and table.remove(spare)) or Portraits.pet(petId, size)
    frame:SetAttribute("PoolKey", key)
    frame.Parent = parent
    return frame
end
local function keepPortraits(root)
    for _, frame in root:GetDescendants() do
        local key = frame:IsA("ViewportFrame") and frame:GetAttribute("PoolKey")
        if key then
            frame.Parent = nil
            portraitPool[key] = portraitPool[key] or {}
            table.insert(portraitPool[key], frame)
        end
    end
end

local function penLevel()
    return if snapshot and typeof(snapshot.PenLevel) == "number" then snapshot.PenLevel else 1
end

local function ask(action, argument)
    RemoteEvents.PenEvent:FireServer(action, argument)
end

local render -- (below)

local function build()
    window = Hud.window({ Name = "PenWindow", Title = "BEAST PEN", Size = Vector2.new(600, 580), AnchorPoint = Vector2.new(0.5, 0.5),
        Position = UDim2.fromScale(0.5, 0.5) })
    local body = window.Body
    local pill
    pill, levelLabel = UiKit.pill(UiTheme.Icons.Pets, "", { Name = "Level", Position = UDim2.fromOffset(0, 7), Size = UDim2.fromOffset(0, 30), Parent = body })
    local _ = pill
    local show = UiKit.button({ Name = "ShowMe", Text = "SHOW ME", TextSize = 13, Tone = "Quiet", AnchorPoint = Vector2.new(1, 0),
        Position = UDim2.fromScale(1, 0), Size = UDim2.fromOffset(120, UiTheme.Height.ButtonSmall), Parent = body })
    show.Activated:Connect(function()
        PenPicker.showPasture()
        window.close()
    end)
    -- the upgrade card
    local TOP = UiTheme.Height.ButtonSmall + UiTheme.Space.S
    card = UiKit.boldCard(UiKit.card({ Name = "Upgrade", Position = UDim2.fromOffset(0, TOP), Size = UDim2.new(1, 0, 0, CARD_H), Parent = body }), C.Edge)
    cardParts.title = UiKit.boldLabel({ Name = "Title", TextSize = 16, Text = "UPGRADE PEN", TextColor3 = C.Highlight,
        Position = UDim2.fromOffset(16, 12), Size = UDim2.new(1, -220, 0, 20), Parent = card })
    cardParts.from = UiKit.label({ Name = "Change", Font = "Heavy", TextSize = 15, Text = "", RichText = true, TextColor3 = C.Text,
        Position = UDim2.fromOffset(16, 40), Size = UDim2.new(1, -220, 0, 20), Parent = card })
    cardParts.note = UiKit.label({ Name = "Note", Font = "Strong", TextSize = 12, Text = "", TextColor3 = C.Muted, TextWrapped = true,
        Position = UDim2.fromOffset(16, 64), Size = UDim2.new(1, -220, 0, 30), Parent = card })
    local priceFrame
    priceFrame, cardParts.price = UiKit.pill(UiTheme.Icons.Stones, "", { Name = "Price", AnchorPoint = Vector2.new(1, 0),
        Position = UDim2.new(1, -16, 0, 10), Size = UDim2.fromOffset(0, 30), Parent = card })
    cardParts.priceFrame = priceFrame
    cardParts.buy = UiKit.button({ Name = "Buy", Text = "UPGRADE", TextSize = 15, Tone = "Go", AnchorPoint = Vector2.new(1, 1),
        Position = UDim2.new(1, -16, 1, -10), Size = UDim2.fromOffset(170, BUTTON), Parent = card })
    cardParts.buy.Activated:Connect(function()
        local level = penLevel()
        if level < PenLayout.Max then
            ask("Upgrade", level)
        end
    end)
    local LIST_TOP = TOP + CARD_H + UiTheme.Space.M
    list = UiKit.scroll({ Name = "Pets", Position = UDim2.fromOffset(0, LIST_TOP), Size = UDim2.new(1, 0, 1, -LIST_TOP), Parent = body })
    -- on a short screen (a phone held sideways) the window is too short for the card and a list under it: the list had 8 px
    -- and no beast could be added. There the card goes into the list, first, and scrolls with the beasts.
    local function fitList()
        local bodyHeight = window.Frame.Size.Y.Offset + body.Size.Y.Offset
        local inList = bodyHeight - LIST_TOP < LIST_MIN
        card.Parent = if inList then list else body
        card.LayoutOrder = 0
        card.Position = if inList then UDim2.new() else UDim2.fromOffset(0, TOP)
        list.Position = UDim2.fromOffset(0, if inList then TOP else LIST_TOP)
        list.Size = UDim2.new(1, 0, 1, -(if inList then TOP else LIST_TOP))
    end
    window.Frame:GetPropertyChangedSignal("Size"):Connect(fitList)
    fitList()
    player:GetAttributeChangedSignal("SpiritStones"):Connect(function()
        render()
    end)
end

local function heading(text, order)
    local label = UiKit.label({ Name = "Heading", Font = "Heavy", TextSize = UiTheme.Text.Heading, Text = text, TextColor3 = C.Muted,
        Size = UDim2.new(1, 0, 0, 20), LayoutOrder = order, Parent = list })
    return label
end

local function petRow(pet, order, inPen, full)
    local definition = GameConfig.Pets[pet.PetId]
    local row = UiKit.card({ Name = "Pet", LayoutOrder = order, Size = UDim2.new(1, 0, 0, ROW_H), Parent = list })
    local picture = portrait(pet.PetId, 52, row)
    picture.Position = UDim2.fromOffset(6, 6)
    UiKit.boldLabel({ Name = "PetName", TextSize = 14, Text = definition.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
        TextColor3 = C.Text, Position = UDim2.fromOffset(68, 10), Size = UDim2.new(1, -(68 + 150), 0, 18), Parent = row })
    local tags = Instance.new("Frame")
    tags.Name = "Tags"
    tags.BackgroundTransparency = 1
    tags.Position = UDim2.fromOffset(68, 34)
    tags.Size = UDim2.new(1, -(68 + 150), 0, 18)
    tags.Parent = row
    UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
    local function tag(text, color, n)
        local t = UiKit.tag(text, color)
        t.LayoutOrder = n
        t.Parent = tags
    end
    tag(definition.Rarity, GameConfig.PetRarityColors[definition.Rarity] or C.Text, 1)
    local size = PetRules.size(pet)
    if size ~= "Normal" then
        tag(size, PetRules.sizeInfo(size).Color, 2)
    end
    if PetRules.level(pet) > 1 then
        tag("Lv " .. PetRules.level(pet), C.AccentBright, 3)
    end
    local text, tone, active, action
    if inPen then
        text, tone, active, action = "REMOVE", "Quiet", true, "Remove"
    elseif pet.Equipped then
        text, tone, active = "EQUIPPED", "Quiet", false
    elseif full then
        text, tone, active = "PEN FULL", "Quiet", false
    else
        text, tone, active, action = "ADD", "Go", true, "Add"
    end
    local b = UiKit.button({ Name = "Action", Text = text, TextSize = 13, Tone = tone, Active = active, AnchorPoint = Vector2.new(1, 0.5),
        Position = UDim2.new(1, -8, 0.5, 0), Size = UDim2.fromOffset(136, BUTTON), Parent = row })
    if active then
        b.Activated:Connect(function()
            ask(action, pet.InstanceId)
        end)
    end
end

local lightUpgrade = false
function render()
    if not (window and window.isOpen()) then
        return
    end
    keepPortraits(list)
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") and child ~= card then
            child:Destroy()
        end
    end
    local level = penLevel()
    local capacity = PenLayout.capacity(level)
    local penIds = snapshot and snapshot.Pen or {}
    local count = #penIds
    local area = player:GetAttribute("PastureArea")
    local held = (player:GetAttribute("PastureIndex") or 0) > 0
    levelLabel.Text = "LEVEL " .. level .. "  ·  " .. count .. " / " .. capacity .. " BEASTS"
        .. (if held and typeof(area) == "string" then "  ·  " .. string.upper(area) else "")
    -- the upgrade card
    if level >= PenLayout.Max then
        cardParts.title.Text = "YOUR PEN IS AS BIG AS IT GETS"
        cardParts.from.Text = "Level " .. level .. ":  room for " .. capacity .. " beasts"
        cardParts.note.Text = "Every beast you own can be shown off here, ten at a time."
        cardParts.priceFrame.Visible = false
        cardParts.buy.Visible = false
    else
        local nextCap = PenLayout.capacity(level + 1)
        local price = Shop.penPrice(level + 1) or 0
        local stones = player:GetAttribute("SpiritStones") or 0
        local afford = stones >= price
        cardParts.title.Text = "UPGRADE PEN"
        cardParts.from.Text = string.format('Level %d  →  <font color="#%s">Level %d</font>     %d  →  <font color="#%s">%d beasts</font>',
            level, C.Highlight:ToHex(), level + 1, capacity, C.Highlight:ToHex(), nextCap)
        cardParts.note.Text = if afford then "A bigger pen, with room for one more beast." else
            "You need " .. NumberFormat.compact(price - stones) .. " more Spirit Stones."
        cardParts.priceFrame.Visible = true
        cardParts.price.Text = NumberFormat.compact(price)
        cardParts.price.TextColor3 = if afford then C.Text else C.Danger
        cardParts.buy.Visible = true
        cardParts.buy.Active = afford
        cardParts.buy:SetAttribute("Tone", if afford then "Go" else "Quiet")
    end
    -- the pets: those in the pen (in its order), then the rest (free ones first, the rarest and biggest first)
    local byId = {}
    for _, pet in if snapshot then snapshot.Pets else {} do
        byId[pet.InstanceId] = pet
    end
    local order = 0
    local function nextOrder()
        order += 1
        return order
    end
    heading("IN YOUR PEN  (" .. count .. " / " .. capacity .. ")", nextOrder())
    if count == 0 then
        UiKit.label({ Name = "Empty", Font = "Strong", TextSize = 13, Text = "Your pen is empty. Add a beast below and it will walk around there for everyone to see.",
            TextWrapped = true, TextColor3 = C.Muted, Size = UDim2.new(1, 0, 0, 36), LayoutOrder = nextOrder(), Parent = list })
    end
    for _, instanceId in penIds do
        local pet = byId[instanceId]
        if pet and GameConfig.Pets[pet.PetId] then
            petRow(pet, nextOrder(), true, false)
        end
    end
    heading("ADD A BEAST", nextOrder())
    local others = {}
    for _, pet in if snapshot then snapshot.Pets else {} do
        if not pet.InPen and GameConfig.Pets[pet.PetId] then
            table.insert(others, pet)
        end
    end
    table.sort(others, function(a, b)
        if (a.Equipped == true) ~= (b.Equipped == true) then
            return b.Equipped == true
        end
        local da, db = GameConfig.Pets[a.PetId], GameConfig.Pets[b.PetId]
        local ra, rb = RARITY_ORDER[da.Rarity] or 0, RARITY_ORDER[db.Rarity] or 0
        if ra ~= rb then
            return ra > rb
        end
        local sa, sb = PetRules.sizeInfo(a).Order, PetRules.sizeInfo(b).Order
        if sa ~= sb then
            return sa > sb
        end
        return da.DisplayName < db.DisplayName
    end)
    for _, pet in others do
        petRow(pet, nextOrder(), false, count >= capacity)
    end
    if lightUpgrade and level < PenLayout.Max then
        lightUpgrade = false
        UiFx.sweep(card, C.Highlight, 0.6)
    end
end

local shownOnce = false
function PenPicker.open(upgrade)
    if not window then
        build()
    end
    lightUpgrade = upgrade == true
    window.open()
    render()
    if not shownOnce then -- the first time: where the pasture is
        shownOnce = true
        local config = pastureConfig()
        local frame = config and config:GetAttribute("Frame")
        local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        if typeof(frame) == "CFrame" and root and (root.Position - frame.Position).Magnitude > 60 then
            PenPicker.showPasture()
        end
    end
end

function PenPicker.isOpen()
    return window ~= nil and window.isOpen()
end

function PenPicker.setSnapshot(s)
    snapshot = s
    render()
end

RemoteEvents.PenEvent.OnClientEvent:Connect(function(kind, ok, text, what)
    if kind ~= "Result" then
        return
    end
    if ok then
        -- an upgrade pays (the pen's growing has its own sound, heard by anyone near: PenController); a beast let in or out
        Sfx.play(if what == "Upgraded" then "Purchase" elseif what == "Remove" then "PetDismiss" else "PenPlace")
        message:show(tostring(text), if what == "Upgraded" then "Reward" else "Success")
        if what == "Upgraded" and card then
            UiFx.pop(card, 1.04, 0.3)
            UiFx.sweep(card, C.Highlight, 0.6)
        end
    else
        Sfx.play("Error")
        message:show(tostring(text), "Warning")
    end
end)

player:GetAttributeChangedSignal("PastureIndex"):Connect(function()
    render()
end)

return PenPicker

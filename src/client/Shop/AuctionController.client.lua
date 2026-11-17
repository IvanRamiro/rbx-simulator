-- The Auction House's window (server/Auction/AuctionService; rules: shared/AuctionRules, GameConfig.AuctionHouse). The Market's
-- prompt opens it (AuctionEvent "Open"). Three tabs:
--   BROWSE       every server's listings: by type and rarity, sorted by ending soon, price, rarity or newest, a page at a time;
--                a listing opens its page: the item, the seller, the top bid, how many bids, the time left, the last bids, and
--                a bid (quick raises, asked once more in a ConfirmDialog)
--   SELL         the player's pets and weapons (why one can't go up, if it can't), a starting bid, a duration, the fee shown
--   MY AUCTIONS  what they sell and what they bid on, with each one's status; mail waiting for room, and CLAIM
-- Mail (outbid, won, sold, back to you) shows as notifications wherever the player is. Everything is asked of the server, which
-- checks it all; the window closes when the player walks away.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local AuctionRules = require(ReplicatedStorage:WaitForChild("AuctionRules"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local ConfirmDialog = require(UI:WaitForChild("ConfirmDialog"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Toast = require(UI:WaitForChild("Toast"))
local Portraits = require(UI:WaitForChild("Portraits"))
local MutationLook = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("MutationLook"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local Event = RemoteEvents.AuctionEvent
local CONFIG = AuctionRules.Config

local WALK_AWAY = 30 -- studs (the prompt opens within 12; the server acts within CONFIG.Reach)
local TAB = UiTheme.Height.Tab
local GAP = UiTheme.Space.M
local BUTTON = UiTheme.Height.Button
local CARD = 80

local message = Toast.new("AuctionMessage", C.Highlight, 5)

local SORTS = { { "Ending", "ENDING SOON" }, { "Low", "LOWEST PRICE" }, { "High", "HIGHEST PRICE" }, { "Rare", "RAREST" }, { "New", "NEWEST" } }
local RARITY_CHOICES = { "All" }
for _, rarity in AuctionRules.Rarities do
    table.insert(RARITY_CHOICES, rarity)
end

local current = {
    open = false, tab = "Browse", openedAt = nil, state = nil,
    kind = "All", rarity = "All", sort = 1, page = 1, browse = nil,
    detailId = nil, detail = nil, bidAmount = nil,
    sellable = nil, selling = nil, sellStart = nil, sellHours = CONFIG.Hours[2] or CONFIG.Hours[1],
    mine = nil, waitingRender = false,
}
local render

-- ---------- small helpers ----------
local function serverNow()
    return workspace:GetServerTimeNow()
end

local function timeLeft(ends)
    local left = math.floor(ends - serverNow())
    if left <= 0 then
        return "Ended", true
    end
    local h, m, s = left // 3600, left % 3600 // 60, left % 60
    if h > 0 then
        return string.format("%dh %02dm", h, m), false
    end
    return string.format("%dm %02ds", m, s), left < 60
end

local function stones(n)
    return NumberFormat.compact(n or 0)
end

-- what to call an item from its summary ({ K, P, W, N, ... }) or a sellable entry ({ Kind, PetId, WeaponId, Name })
local function nameOf(entry)
    local kind = entry.K or entry.Kind
    if kind == "Pet" then
        local petId = entry.P or entry.PetId
        return if GameConfig.Pets[petId] then PetRules.displayName(petId, entry.M or entry.Mutation) else "Pet"
    end
    local name = entry.N or entry.Name
    if typeof(name) == "string" and name ~= "" then
        return name
    end
    local weapon = Shop.weapon(entry.W or entry.WeaponId)
    return weapon and weapon.Name or "Weapon"
end

local function colourOf(entry)
    local kind = entry.K or entry.Kind
    if kind == "Pet" then
        return GameConfig.PetRarityColors[entry.R or entry.Rarity] or C.Text
    end
    local element = Shop.element(entry.E or entry.Element)
    return if element then element.Color:Lerp(Color3.new(1, 1, 1), 0.2) else C.AccentBright
end

-- the line under the name: a pet's rarity, size, mutation and level; a weapon's realm and element
local function detailOf(entry)
    local kind = entry.K or entry.Kind
    if kind == "Pet" then
        local size = PetRules.size(entry.S or entry.Size)
        local level = PetRules.level({ Level = entry.Lv or entry.Level })
        local mutation = PetRules.mutation(entry.M or entry.Mutation)
        return (entry.R or entry.Rarity or "") .. (if size ~= "Normal" then "  ·  " .. size else "")
            .. (if mutation then "  ·  " .. mutation else "") .. (if level > 1 then "  ·  Level " .. level else "")
    end
    local weapon = Shop.weapon(entry.W or entry.WeaponId)
    local element = Shop.element(entry.E or entry.Element)
    return (weapon and (weapon.Kind .. "  ·  " .. weapon.Realm) or "Weapon") .. (if element then "  ·  " .. element.DisplayName else "")
end

local function portrait(entry, size)
    local kind = entry.K or entry.Kind
    if kind == "Pet" then
        local frame = Portraits.pet(entry.P or entry.PetId, size)
        MutationLook.portrait(frame, entry.M or entry.Mutation) -- (tinted, with its glints)
        return frame
    end
    local element = Shop.element(entry.E or entry.Element)
    return Portraits.weapon(entry.W or entry.WeaponId, element and element.Color, size)
end

local function ask(...)
    Event:FireServer(...)
end

-- ---------- the window ----------
local window = Hud.window({
    Name = "AuctionWindow", Title = "AUCTION HOUSE", Size = Vector2.new(720, 540), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5), OnClose = function()
        current.open = false
    end,
})
local body = window.Body

local _, balance = UiKit.pill(UiTheme.Icons.Stones, "", {
    Name = "Balance", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0, TAB / 2), Parent = body,
})

local tabs = Instance.new("Frame")
tabs.Name = "Tabs"
tabs.BackgroundTransparency = 1
tabs.Size = UDim2.new(1, -140, 0, TAB)
tabs.Parent = body
UiKit.list(tabs, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
local tabButtons = {}
for index, entry in { { "Browse", "BROWSE" }, { "Sell", "SELL" }, { "Mine", "MY AUCTIONS" } } do
    local tab = UiKit.tab({
        Name = entry[1], Text = entry[2], TextSize = 13, LayoutOrder = index,
        Size = UDim2.new(1 / 3, -UiTheme.Space.S * 2 / 3, 1, 0), Parent = tabs,
    })
    tab.Activated:Connect(function()
        if current.tab == entry[1] then
            return
        end
        Sfx.play("Tab")
        current.tab = entry[1]
        current.detailId, current.detail, current.selling = nil, nil, nil
        if entry[1] == "Browse" then
            ask("Browse", { Kind = current.kind, Rarity = current.rarity, Sort = SORTS[current.sort][1], Page = current.page })
        elseif entry[1] == "Sell" then
            ask("Sellable")
        else
            ask("Mine")
        end
        render()
    end)
    tabButtons[entry[1]] = tab
end

local list = UiKit.scroll({ Name = "List", Position = UDim2.fromOffset(0, TAB + GAP), Size = UDim2.new(1, 0, 1, -(TAB + GAP)), Parent = body })

-- the labels that count down: each holds its listing's end
local timers = {}

local focused = nil -- a TextBox being typed in: the window waits to redraw until it lets go

local function renderSoon()
    if focused then
        current.waitingRender = true
    else
        render()
    end
end

local function clear()
    table.clear(timers)
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
end

local order = 0
local function nextOrder()
    order += 1
    return order
end

local function card(height, stripe)
    return UiKit.card({ LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, height), Stripe = stripe, Parent = list })
end

local function heading(text)
    UiKit.header(list, text, { LayoutOrder = nextOrder() })
end

local function button(parent, text, tone, size, position, onClick)
    local b = UiKit.button({
        TextSize = 13, Text = text, Tone = tone, Active = onClick ~= nil, Size = size, Position = position, Parent = parent,
    })
    if onClick then
        b.Activated:Connect(onClick)
    end
    return b
end

local function row(height)
    local frame = Instance.new("Frame")
    frame.BackgroundTransparency = 1
    frame.LayoutOrder = nextOrder()
    frame.Size = UDim2.new(1, 0, 0, height)
    frame.Parent = list
    return frame
end

-- a price: the stone's picture and the number, heavy
local function priceTag(parent, value, props)
    local tag = Instance.new("Frame")
    tag.Name = "Price"
    tag.BackgroundTransparency = 1
    tag.Size = props.Size or UDim2.fromOffset(120, 22)
    tag.Position = props.Position or UDim2.new()
    tag.AnchorPoint = props.AnchorPoint or Vector2.new()
    tag.Parent = parent
    UiKit.list(tag, { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = props.Align or Enum.HorizontalAlignment.Right,
        VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 4) })
    local stone = Instance.new("ImageLabel")
    stone.BackgroundTransparency = 1
    stone.Image = UiTheme.Icons.Stones
    stone.Size = UDim2.fromOffset(props.Icon or 18, props.Icon or 18)
    stone.Parent = tag
    UiKit.boldLabel({
        TextSize = props.TextSize or 15, Text = stones(value), TextColor3 = props.Color or C.AccentBright,
        AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 20), LayoutOrder = 2, Parent = tag,
    })
    return tag
end

-- a box for a number of stones: digits only
local function numberBox(parent, value, props, onChange)
    local box = UiKit.textbox({
        Name = "Amount", Text = tostring(value or ""), PlaceholderText = props.Placeholder or "Spirit Stones",
        Size = props.Size, Position = props.Position, TextXAlignment = Enum.TextXAlignment.Center, Parent = parent,
    })
    box.FontFace = UiTheme.Fonts.Number
    box.TextSize = 16
    box:GetPropertyChangedSignal("Text"):Connect(function()
        local digits = string.gsub(box.Text, "%D", "")
        if #digits > 13 then
            digits = string.sub(digits, 1, 13)
        end
        if digits ~= box.Text then
            box.Text = digits
        end
        onChange(tonumber(digits))
    end)
    box.Focused:Connect(function()
        focused = box
    end)
    box.FocusLost:Connect(function()
        if focused == box then
            focused = nil
        end
        if current.waitingRender then
            current.waitingRender = false
            task.defer(render)
        end
    end)
    return box
end

local function chip(parent, text, on, size, onClick)
    local b = UiKit.button({ TextSize = 12, Text = text, Tone = if on then "Highlight" else "Tile", Size = size, Parent = parent })
    b.Activated:Connect(function()
        Sfx.play("Click")
        onClick()
    end)
    return b
end

local function notice(text, tone)
    local box = card(0)
    box.AutomaticSize = Enum.AutomaticSize.Y
    UiKit.padding(box, UiTheme.Pad.Card, 10)
    UiKit.label({
        Font = "Strong", TextSize = 13, TextWrapped = true, Text = text, TextColor3 = if tone == "Danger" then C.Danger else C.Muted,
        AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0), Parent = box,
    })
end

local function canTrade()
    return current.state ~= nil and current.state.Can == true
end

-- ---------- BROWSE ----------
local function listingCard(entry)
    local colour = colourOf(entry)
    local box = UiKit.boldCard(card(CARD), colour)
    local art = portrait(entry, 60)
    art.Position = UDim2.fromOffset(10, 10)
    art.Parent = box
    UiKit.boldLabel({
        TextSize = 14, Text = nameOf(entry), TextColor3 = colour, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(80, 9), Size = UDim2.new(0.5, -80, 0, 18), Parent = box,
    })
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = detailOf(entry), TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(80, 30), Size = UDim2.new(0.5, -80, 0, 14), Parent = box,
    })
    local mine = entry.Su == player.UserId
    local top = entry.Hb == player.UserId
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = if mine then C.Sky elseif top then C.BuyBright else C.Muted,
        Text = if mine then "Your listing" elseif top then "Your bid is on top" else "Seller: " .. tostring(entry.Sn or "?"),
        TextTruncate = Enum.TextTruncate.AtEnd, Position = UDim2.fromOffset(80, 48), Size = UDim2.new(0.5, -80, 0, 14), Parent = box,
    })
    priceTag(box, entry.Pr, { Position = UDim2.new(0.72, -UiTheme.Space.M, 0, 14), AnchorPoint = Vector2.new(1, 0),
        Size = UDim2.new(0.22, 0, 0, 22) })
    local bids = entry.B or 0
    local when = UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.Muted, TextXAlignment = Enum.TextXAlignment.Right,
        Text = "", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(0.72, -UiTheme.Space.M, 0, 42),
        Size = UDim2.new(0.3, 0, 0, 14), Parent = box,
    })
    timers[when] = { ends = entry.End, prefix = (if bids == 0 then "No bids" elseif bids == 1 then "1 bid" else bids .. " bids") .. "  ·  " }
    button(box, if mine then "VIEW" else "BID", if mine then "Quiet" else "Buy", UDim2.new(0.28, -12, 0, BUTTON),
        UDim2.new(0.72, 0, 0.5, -BUTTON / 2), function()
            Sfx.play("Click")
            current.detailId, current.detail, current.bidAmount = entry.Id, nil, nil
            ask("Detail", entry.Id)
            render()
        end)
end

local function renderFilters()
    local filters = row(BUTTON)
    UiKit.list(filters, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S),
        VerticalAlignment = Enum.VerticalAlignment.Center })
    local function refetch()
        current.page = 1
        ask("Browse", { Kind = current.kind, Rarity = current.rarity, Sort = SORTS[current.sort][1], Page = current.page })
        render()
    end
    for index, entry in { { "All", "ALL" }, { "Pet", "PETS" }, { "Weapon", "WEAPONS" } } do
        local b = chip(filters, entry[2], current.kind == entry[1], UDim2.new(0.13, 0, 1, 0), function()
            current.kind = entry[1]
            if entry[1] == "Weapon" then
                current.rarity = "All"
            end
            refetch()
        end)
        b.LayoutOrder = index
    end
    local rarity = chip(filters, if current.rarity == "All" then "ANY RARITY" else string.upper(current.rarity),
        current.rarity ~= "All", UDim2.new(0.25, 0, 1, 0), function()
            local at = table.find(RARITY_CHOICES, current.rarity) or 1
            current.rarity = RARITY_CHOICES[at % #RARITY_CHOICES + 1]
            if current.rarity ~= "All" and current.kind == "Weapon" then
                current.kind = "Pet"
            end
            refetch()
        end)
    rarity.LayoutOrder = 4
    if current.rarity ~= "All" then
        rarity.TextColor3 = Color3.fromRGB(48, 28, 6)
    end
    local sort = chip(filters, SORTS[current.sort][2], false, UDim2.new(0.3, 0, 1, 0), function()
        current.sort = current.sort % #SORTS + 1
        refetch()
    end)
    sort.LayoutOrder = 5
end

local function renderBrowse()
    if not canTrade() and current.state then
        notice(current.state.Why or "You can look, but not trade yet.", "Danger")
    end
    renderFilters()
    local data = current.browse
    if not data then
        notice("Looking for auctions...")
        return
    end
    if data.Ok == false then
        notice("The Auction House is busy. The list may be out of date: it will try again in a moment.", "Danger")
    end
    if #data.Items == 0 then
        UiKit.empty(list, if current.kind == "All" and current.rarity == "All"
            then "Nothing for sale right now.\nBe the first: put a pet or a weapon up in the SELL tab."
            else "Nothing like that for sale right now.\nTry another type or rarity.").LayoutOrder = nextOrder()
        return
    end
    for _, entry in data.Items do
        listingCard(entry)
    end
    local pager = row(BUTTON)
    local function go(page)
        Sfx.play("Click")
        current.page = page
        ask("Browse", { Kind = current.kind, Rarity = current.rarity, Sort = SORTS[current.sort][1], Page = page })
    end
    button(pager, "PREVIOUS", "Quiet", UDim2.new(0.3, 0, 1, 0), UDim2.new(), if data.Page > 1 then function()
        go(data.Page - 1)
    end else nil)
    UiKit.boldLabel({
        TextSize = 13, Text = "Page " .. data.Page .. " of " .. data.Pages .. "  ·  " .. data.Total .. " for sale",
        TextXAlignment = Enum.TextXAlignment.Center, Position = UDim2.fromScale(0.3, 0), Size = UDim2.new(0.4, 0, 1, 0), Parent = pager,
    })
    button(pager, "NEXT", "Quiet", UDim2.new(0.3, 0, 1, 0), UDim2.fromScale(0.7, 0), if data.Page < data.Pages then function()
        go(data.Page + 1)
    end else nil)
end

-- ---------- one listing's page ----------
local function placeBid(entry, amount)
    ConfirmDialog.show({
        Title = "PLACE A BID", Picture = portrait(entry, 72), ConfirmText = "BID " .. stones(amount), Seconds = 1,
        Text = "Bid " .. NumberFormat.compact(amount) .. " Spirit Stones on the " .. nameOf(entry) .. "? The stones are held now. "
            .. "If someone bids more, you get them all back.",
        OnConfirm = function()
            ask("Bid", entry.Id, amount)
        end,
    })
end

local function renderDetail()
    local back = row(BUTTON)
    button(back, "BACK TO THE LIST", "Quiet", UDim2.new(0.4, 0, 1, 0), UDim2.new(), function()
        Sfx.play("Click")
        current.detailId, current.detail = nil, nil
        render()
    end)
    local entry = current.detail
    if not entry then
        notice("Opening the listing...")
        return
    end
    if entry.Gone then
        notice("This auction is gone.", "Danger")
        return
    end
    local colour = colourOf(entry)
    local top = UiKit.boldCard(card(132), colour)
    local art = portrait(entry, 112)
    art.Position = UDim2.fromOffset(10, 10)
    art.Parent = top
    UiKit.boldLabel({
        TextSize = 18, Text = nameOf(entry), TextColor3 = colour, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(134, 12), Size = UDim2.new(1, -146, 0, 22), Parent = top,
    })
    local lines = { detailOf(entry), "Seller: " .. tostring(entry.Sn or "?") }
    if entry.Paid then
        table.insert(lines, "Came from Robux: some regions can't trade it")
    end
    for i, text in lines do
        UiKit.label({
            Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Text = text, TextTruncate = Enum.TextTruncate.AtEnd,
            Position = UDim2.fromOffset(134, 22 + i * 20), Size = UDim2.new(1, -146, 0, 16), Parent = top,
        })
    end
    local status = UiKit.boldLabel({
        TextSize = 13, Text = "", TextColor3 = C.AccentBright, Position = UDim2.fromOffset(134, 104), Size = UDim2.new(1, -146, 0, 18),
        Parent = top,
    })

    local stats = card(76)
    local bids = entry.B or 0
    UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = if bids > 0 then "TOP BID" else "STARTING BID",
        Position = UDim2.fromOffset(14, 10), Size = UDim2.new(0.33, -14, 0, 14), Parent = stats })
    priceTag(stats, entry.Pr, { Position = UDim2.fromOffset(14, 30), Size = UDim2.new(0.33, -14, 0, 28), TextSize = 20, Icon = 22,
        Align = Enum.HorizontalAlignment.Left })
    UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = "BIDS", Position = UDim2.fromScale(0.36, 0),
        Size = UDim2.new(0.25, 0, 0, 24), TextYAlignment = Enum.TextYAlignment.Bottom, Parent = stats })
    UiKit.boldLabel({ TextSize = 20, Text = tostring(bids), Position = UDim2.new(0.36, 0, 0, 30), Size = UDim2.new(0.25, 0, 0, 28), Parent = stats })
    UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = "TIME LEFT", Position = UDim2.fromScale(0.64, 0),
        Size = UDim2.new(0.36, -14, 0, 24), TextYAlignment = Enum.TextYAlignment.Bottom, Parent = stats })
    local left = UiKit.boldLabel({ TextSize = 20, Text = "", Position = UDim2.new(0.64, 0, 0, 30), Size = UDim2.new(0.36, -14, 0, 28), Parent = stats })
    timers[left] = { ends = entry.End, prefix = "" }

    local active = entry.State == "Active" and entry.End > serverNow()
    if entry.Mine then
        status.Text = if active then "This is your listing." else "Your auction has ended."
    elseif entry.Top then
        status.Text, status.TextColor3 = "Your bid is on top!", C.BuyBright
    elseif not active then
        status.Text = if entry.Result and entry.Result.Winner == player.UserId then "You won this auction!" else "This auction has ended."
    end

    if entry.Last and #entry.Last > 0 then
        heading("Last bids")
        for _, bid in entry.Last do
            local line = card(34)
            UiKit.label({ Font = "Strong", TextSize = 12, Text = tostring(bid.Name), TextTruncate = Enum.TextTruncate.AtEnd,
                Position = UDim2.fromOffset(14, 0), Size = UDim2.new(0.6, -14, 1, 0), Parent = line })
            priceTag(line, bid.Amount, { Position = UDim2.new(1, -14, 0.5, 0), AnchorPoint = Vector2.new(1, 0.5), Size = UDim2.new(0.4, 0, 0, 22),
                TextSize = 13, Icon = 16 })
        end
    end

    if not active or entry.Mine or entry.Top then
        if entry.Mine and active and bids == 0 then
            local foot = row(BUTTON)
            button(foot, "CANCEL THIS AUCTION", "Danger", UDim2.new(0.5, 0, 1, 0), UDim2.new(), function()
                ConfirmDialog.show({
                    Title = "CANCEL THE AUCTION", Picture = portrait(entry, 72), ConfirmText = "CANCEL IT", Seconds = 1,
                    Text = "Take the " .. nameOf(entry) .. " back? The listing fee is not given back.",
                    OnConfirm = function()
                        ask("Cancel", entry.Id)
                    end,
                })
            end)
        end
        return
    end
    if not canTrade() or entry.CanBid == false then
        notice(if not canTrade() then (current.state and current.state.Why) or "You can't bid yet." else entry.WhyNot or "You can't bid on this.", "Danger")
        return
    end
    heading("Your bid")
    local least = entry.MinBid or entry.Pr
    current.bidAmount = math.max(current.bidAmount or least, least)
    local controls = card(BUTTON * 2 + 30)
    local box
    local function setAmount(n)
        current.bidAmount = math.clamp(math.floor(n), least, entry.Cap or math.huge)
        if box then
            box.Text = tostring(current.bidAmount)
        end
    end
    box = numberBox(controls, current.bidAmount, { Size = UDim2.new(0.4, -14, 0, BUTTON), Position = UDim2.fromOffset(12, 10) },
        function(n)
            current.bidAmount = n
        end)
    local quick = Instance.new("Frame")
    quick.BackgroundTransparency = 1
    quick.Position = UDim2.new(0.4, 6, 0, 10)
    quick.Size = UDim2.new(0.6, -18, 0, BUTTON)
    quick.Parent = controls
    UiKit.list(quick, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
    local raises = { { "LOWEST", function()
        return least
    end }, { "+10%", function()
        return math.max(least, math.ceil(entry.Pr * 1.1))
    end }, { "+25%", function()
        return math.max(least, math.ceil(entry.Pr * 1.25))
    end } }
    for index, raise in raises do
        local b = chip(quick, raise[1], false, UDim2.new(1 / 3, -UiTheme.Space.S * 2 / 3, 1, 0), function()
            setAmount(raise[2]())
        end)
        b.LayoutOrder = index
    end
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.Muted, TextWrapped = true,
        Text = "Lowest bid now: " .. stones(least) .. ". Highest allowed: " .. stones(entry.Cap) .. ". A bid in the last minute adds a minute.",
        Position = UDim2.fromOffset(12, BUTTON + 14), Size = UDim2.new(1, -24, 0, 26), Parent = controls,
    })
    local have = player:GetAttribute("SpiritStones") or 0
    local bidButton = button(controls, "", "Buy", UDim2.new(1, -24, 0, BUTTON), UDim2.new(0, 12, 1, -(BUTTON + 6)), function()
        local amount = current.bidAmount
        if not amount or amount < least then
            Sfx.play("Error")
            message:show("The lowest bid now is " .. stones(least) .. " Spirit Stones.", "Error")
            return
        end
        if amount > have then
            Sfx.play("Error")
            message:show("You need " .. stones(amount) .. " Spirit Stones.", "Error")
            return
        end
        placeBid(entry, amount)
    end)
    bidButton.Text = "PLACE BID"
    controls.Size = UDim2.new(1, 0, 0, BUTTON * 2 + 52)
end

-- ---------- SELL ----------
local function sellRow(item)
    local colour = colourOf(item)
    local box = card(72, colour)
    local art = portrait(item, 52)
    art.Position = UDim2.fromOffset(14, 10)
    art.Parent = box
    UiKit.boldLabel({ TextSize = 14, Text = nameOf(item), TextColor3 = colour, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(76, 10), Size = UDim2.new(0.6, -76, 0, 18), Parent = box })
    UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = detailOf(item), TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(76, 31), Size = UDim2.new(0.6, -76, 0, 14), Parent = box })
    UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = if item.Why then C.Danger else C.Muted, TextTruncate = Enum.TextTruncate.AtEnd,
        Text = item.Why or ("Buy & Sell pays " .. stones(item.Value) .. ". Start from " .. stones(item.Low) .. "."),
        Position = UDim2.fromOffset(76, 48), Size = UDim2.new(0.6, -76, 0, 14), Parent = box })
    local blocked = item.Why or not canTrade() or (current.sellable and current.sellable.Full)
    button(box, if blocked then (if item.Why then "NOT NOW" elseif not canTrade() then "LOCKED" else "FULL") else "SELL", if blocked then "Quiet" else "Go",
        UDim2.new(0.3, -12, 0, BUTTON), UDim2.new(0.7, 0, 0.5, -BUTTON / 2), if blocked then nil else function()
            Sfx.play("Click")
            current.selling = item
            current.sellStart = item.Low
            render()
        end)
end

local function renderSellForm(item)
    local back = row(BUTTON)
    button(back, "CHOOSE ANOTHER", "Quiet", UDim2.new(0.4, 0, 1, 0), UDim2.new(), function()
        Sfx.play("Click")
        current.selling = nil
        render()
    end)
    local colour = colourOf(item)
    local top = UiKit.boldCard(card(108), colour)
    local art = portrait(item, 88)
    art.Position = UDim2.fromOffset(10, 10)
    art.Parent = top
    UiKit.boldLabel({ TextSize = 17, Text = nameOf(item), TextColor3 = colour, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(110, 12), Size = UDim2.new(1, -122, 0, 22), Parent = top })
    UiKit.label({ Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Text = detailOf(item), TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(110, 40), Size = UDim2.new(1, -122, 0, 16), Parent = top })
    UiKit.label({ Font = "Strong", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true,
        Text = "Buy & Sell pays " .. stones(item.Value) .. " for it. The starting bid can be " .. stones(item.Low) .. " to " .. stones(item.High) .. ".",
        Position = UDim2.fromOffset(110, 60), Size = UDim2.new(1, -122, 0, 36), Parent = top })

    heading("Starting bid")
    local start = card(BUTTON + 20)
    local box
    box = numberBox(start, current.sellStart, { Size = UDim2.new(0.4, -14, 0, BUTTON), Position = UDim2.fromOffset(12, 10) }, function(n)
        current.sellStart = n
        if current.feeLabel then
            local fee = AuctionRules.listingFee(math.max(1, n or item.Low))
            current.feeLabel.Text = "Listing fee: " .. stones(fee) .. " Spirit Stones (kept even if it doesn't sell). When it sells, "
                .. math.floor(CONFIG.SaleTax * 100 + 0.5) .. "% of the price is kept as a fee."
        end
    end)
    local quick = Instance.new("Frame")
    quick.BackgroundTransparency = 1
    quick.Position = UDim2.new(0.4, 6, 0, 10)
    quick.Size = UDim2.new(0.6, -18, 0, BUTTON)
    quick.Parent = start
    UiKit.list(quick, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
    for index, pick in { { "LOWEST", item.Low }, { "x2", item.Low * 2 }, { "x5", item.Low * 5 } } do
        local b = chip(quick, pick[1], false, UDim2.new(1 / 3, -UiTheme.Space.S * 2 / 3, 1, 0), function()
            current.sellStart = math.clamp(pick[2], item.Low, item.High)
            box.Text = tostring(current.sellStart)
        end)
        b.LayoutOrder = index
    end

    heading("How long")
    local hours = row(BUTTON)
    UiKit.list(hours, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
    for index, h in CONFIG.Hours do
        local b = chip(hours, h .. (if h == 1 then " HOUR" else " HOURS"), current.sellHours == h,
            UDim2.new(1 / #CONFIG.Hours, -UiTheme.Space.S * (#CONFIG.Hours - 1) / #CONFIG.Hours, 1, 0), function()
                current.sellHours = h
                render()
            end)
        b.LayoutOrder = index
    end

    local foot = card(BUTTON + 58)
    current.feeLabel = UiKit.label({ Font = "Strong", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true, Text = "",
        TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(12, 10), Size = UDim2.new(1, -24, 0, 34), Parent = foot })
    local fee = AuctionRules.listingFee(math.max(1, current.sellStart or item.Low))
    current.feeLabel.Text = "Listing fee: " .. stones(fee) .. " Spirit Stones (kept even if it doesn't sell). When it sells, "
        .. math.floor(CONFIG.SaleTax * 100 + 0.5) .. "% of the price is kept as a fee."
    button(foot, "PUT IT UP FOR AUCTION", "Buy", UDim2.new(1, -24, 0, BUTTON), UDim2.new(0, 12, 1, -(BUTTON + 8)), function()
        local startBid = current.sellStart
        if not startBid or startBid < item.Low or startBid > item.High then
            Sfx.play("Error")
            message:show("The starting bid must be from " .. stones(item.Low) .. " to " .. stones(item.High) .. " Spirit Stones.", "Error")
            return
        end
        local cost = AuctionRules.listingFee(startBid)
        ConfirmDialog.show({
            Title = "PUT IT UP FOR AUCTION", Picture = portrait(item, 72), ConfirmText = "LIST FOR " .. stones(cost), Seconds = 1,
            Text = "Auction the " .. nameOf(item) .. " for " .. current.sellHours .. (if current.sellHours == 1 then " hour" else " hours")
                .. ", starting at " .. stones(startBid) .. " Spirit Stones? It leaves your inventory now. The listing fee is "
                .. stones(cost) .. ".",
            OnConfirm = function()
                ask("List", { Kind = item.Kind, InstanceId = item.InstanceId, StartBid = startBid, Hours = current.sellHours })
            end,
        })
    end)
end

local function renderSell()
    if not canTrade() and current.state then
        notice(current.state.Why or "You can't sell yet.", "Danger")
    end
    if current.selling then
        renderSellForm(current.selling)
        return
    end
    local data = current.sellable
    if not data then
        notice("Looking at your pets and weapons...")
        return
    end
    if data.Full then
        notice("You have " .. CONFIG.MaxListings .. " items for sale already: wait for one to end, or cancel one with no bids.")
    end
    local pets, weapons = {}, {}
    for _, item in data.Items do
        table.insert(if item.Kind == "Pet" then pets else weapons, item)
    end
    local function sorted(items)
        table.sort(items, function(a, b)
            if (a.Why == nil) ~= (b.Why == nil) then
                return a.Why == nil
            end
            return (a.Value or 0) > (b.Value or 0)
        end)
        return items
    end
    heading("Your pets")
    if #pets == 0 then
        UiKit.empty(list, "No pets.").LayoutOrder = nextOrder()
    end
    for _, item in sorted(pets) do
        sellRow(item)
    end
    heading("Your weapons")
    if #weapons == 0 then
        UiKit.empty(list, "No weapons yet.\nBuy one at the Blacksmith.").LayoutOrder = nextOrder()
    end
    for _, item in sorted(weapons) do
        sellRow(item)
    end
end

-- ---------- MY AUCTIONS ----------
local STATUS_COLOURS = { Winning = C.BuyBright, Outbid = C.Danger, Won = C.Highlight, Sold = C.Highlight, Lost = C.Muted }

local function mineCard(entry, selling)
    local colour = colourOf(entry)
    local box = card(CARD, colour)
    local art = portrait(entry, 56)
    art.Position = UDim2.fromOffset(14, 12)
    art.Parent = box
    UiKit.boldLabel({ TextSize = 14, Text = nameOf(entry), TextColor3 = colour, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(80, 9), Size = UDim2.new(0.5, -80, 0, 18), Parent = box })
    UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = detailOf(entry), TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(80, 30), Size = UDim2.new(0.5, -80, 0, 14), Parent = box })
    local status = entry.Status or ""
    if status == "Sold" and entry.Result then
        status = "Sold for " .. stones(entry.Result.Price) .. " to " .. tostring(entry.Result.WinnerName or "?")
    elseif status == "Won" and entry.Result then
        status = "Won for " .. stones(entry.Result.Price)
    end
    UiKit.boldLabel({ TextSize = 12, Text = status, TextColor3 = STATUS_COLOURS[entry.Status] or C.AccentBright, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(80, 50), Size = UDim2.new(0.5, -80, 0, 16), Parent = box })
    if entry.Pr then
        priceTag(box, entry.Pr, { Position = UDim2.new(0.72, -UiTheme.Space.M, 0, 14), AnchorPoint = Vector2.new(1, 0),
            Size = UDim2.new(0.22, 0, 0, 22) })
    end
    if entry.End and entry.State ~= "Sold" and entry.State ~= "Unsold" and entry.State ~= "Cancelled" then
        local when = UiKit.label({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, TextXAlignment = Enum.TextXAlignment.Right, Text = "",
            AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(0.72, -UiTheme.Space.M, 0, 42), Size = UDim2.new(0.3, 0, 0, 14), Parent = box })
        timers[when] = { ends = entry.End, prefix = "" }
    end
    if entry.Id then
        local canCancel = selling and entry.Status == "No bids yet"
        button(box, if canCancel then "CANCEL" else "VIEW", if canCancel then "Danger" else "Quiet", UDim2.new(0.28, -12, 0, BUTTON),
            UDim2.new(0.72, 0, 0.5, -BUTTON / 2), function()
                Sfx.play("Click")
                if canCancel then
                    ConfirmDialog.show({
                        Title = "CANCEL THE AUCTION", Picture = portrait(entry, 72), ConfirmText = "CANCEL IT", Seconds = 1,
                        Text = "Take the " .. nameOf(entry) .. " back? The listing fee is not given back.",
                        OnConfirm = function()
                            ask("Cancel", entry.Id)
                        end,
                    })
                    return
                end
                current.tab = "Browse"
                current.detailId, current.detail, current.bidAmount = entry.Id, nil, nil
                ask("Detail", entry.Id)
                render()
            end)
    end
end

local function renderMine()
    local data = current.mine
    if not data then
        notice("Looking up your auctions...")
        return
    end
    if (data.Waiting or 0) > 0 then
        local box = card(BUTTON + 24, C.Highlight)
        UiKit.label({ Font = "Strong", TextSize = 12, TextWrapped = true, TextColor3 = C.AccentBright,
            Text = data.Waiting .. (if data.Waiting == 1 then " item is" else " items are") .. " waiting for you. Make room in your pets or weapons, then claim.",
            Position = UDim2.fromOffset(14, 0), Size = UDim2.new(0.68, -14, 1, 0), Parent = box })
        button(box, "CLAIM", "Go", UDim2.new(0.28, -12, 0, BUTTON), UDim2.new(0.72, 0, 0.5, -BUTTON / 2), function()
            Sfx.play("Click")
            ask("Claim")
        end)
    end
    heading("Selling (" .. #data.Selling .. ")")
    if #data.Selling == 0 then
        UiKit.empty(list, "You aren't selling anything.\nPut a pet or a weapon up in the SELL tab.").LayoutOrder = nextOrder()
    end
    for _, entry in data.Selling do
        mineCard(entry, true)
    end
    heading("Bidding (" .. #data.Bidding .. ")")
    if #data.Bidding == 0 then
        UiKit.empty(list, "You haven't bid on anything.\nFind something you like in the BROWSE tab.").LayoutOrder = nextOrder()
    end
    for _, entry in data.Bidding do
        mineCard(entry, false)
    end
end

local lastView, lastSignature = nil, nil

-- what the open view shows, as one string: a poll that brings nothing new doesn't redraw (a redraw rebuilt every portrait)
local function signature()
    local data = if current.tab == "Browse" and current.detailId then current.detail
        elseif current.tab == "Browse" then current.browse elseif current.tab == "Sell" then current.sellable else current.mine
    local ok, text = pcall(HttpService.JSONEncode, HttpService, { data, current.kind, current.rarity, current.sort, current.page,
        current.selling and current.selling.InstanceId, current.sellHours, current.state and current.state.Can })
    return if ok then text else tostring(os.clock())
end

function render(force)
    if not current.open then
        return
    end
    local view = current.tab .. "|" .. tostring(current.detailId) .. "|" .. tostring(current.selling and current.selling.InstanceId)
    local sig = signature()
    if not force and view == lastView and sig == lastSignature then
        return
    end
    -- the same view redrawn with new data keeps where the player had scrolled to
    local keep = if view == lastView then list.CanvasPosition else Vector2.zero
    lastView, lastSignature = view, sig
    clear()
    order = 0
    balance.Text = stones(player:GetAttribute("SpiritStones") or 0)
    for name, tab in tabButtons do
        UiKit.selectTab(tab, current.tab == name)
    end
    current.feeLabel = nil
    if current.tab == "Browse" and current.detailId then
        renderDetail()
    elseif current.tab == "Browse" then
        renderBrowse()
    elseif current.tab == "Sell" then
        renderSell()
    else
        renderMine()
    end
    if keep ~= Vector2.zero then
        task.defer(function()
            list.CanvasPosition = keep
        end)
    end
end

-- ---------- what the server sends ----------
local function mailText(mail)
    local name = mail.Name
    if not name or name == "" then
        name = nameOf({ K = mail.Kind, P = mail.PetId, W = mail.WeaponId })
    end
    if mail.Why == "Outbid" then
        return "Someone bid more for the " .. name .. ". Your " .. stones(mail.Stones) .. " Spirit Stones are back.", "Warning"
    elseif mail.Why == "Won" then
        return "You won the " .. name .. (if mail.Price then " for " .. stones(mail.Price) .. " Spirit Stones" else "") .. "!", "Reward"
    elseif mail.Why == "Sold" then
        return "Your " .. name .. " sold for " .. stones(mail.Price) .. "! You get " .. stones(mail.Stones) .. " Spirit Stones after the fee.", "Reward"
    elseif mail.Reason == "Unsold" then
        return "Nobody bid on your " .. name .. ". It's back with you.", "Info"
    end
    return "Your " .. name .. " is back with you.", "Info"
end

Event.OnClientEvent:Connect(function(kind, ...)
    if kind == "Open" then
        local state = ...
        current.state = state
        local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        current.openedAt = root and root.Position
        current.open = true
        current.tab, current.detailId, current.detail, current.selling = "Browse", nil, nil, nil
        window.open()
        render(true)
    elseif kind == "Browse" then
        current.browse = ...
        if current.open and current.tab == "Browse" and not current.detailId then
            renderSoon()
        end
    elseif kind == "Detail" then
        local detail = ...
        if detail and detail.Id == current.detailId then
            current.detail = detail
            if current.open and current.tab == "Browse" then
                renderSoon()
            end
        end
    elseif kind == "Sellable" then
        current.sellable = ...
        if current.open and current.tab == "Sell" then
            renderSoon()
        end
    elseif kind == "Mine" then
        current.mine = ...
        if current.open and current.tab == "Mine" then
            renderSoon()
        end
    elseif kind == "Result" then
        local ok, text, extra = ...
        Sfx.play(if ok then "Purchase" else "Error")
        message:show(text, if ok then "Success" else "Error")
        extra = extra or {}
        if ok and extra.Action == "List" then
            current.selling = nil
            current.tab = "Mine"
        elseif extra.Action == "Bid" and current.detailId == extra.ListingId then
            current.bidAmount = nil
            ask("Detail", extra.ListingId)
        elseif ok and extra.Action == "Cancel" then
            current.detailId, current.detail = nil, nil
            current.tab = "Mine"
        end
        if current.open and current.tab == "Browse" and not current.detailId then
            ask("Browse", { Kind = current.kind, Rarity = current.rarity, Sort = SORTS[current.sort][1], Page = current.page })
        end
        if current.open then
            renderSoon()
        end
    elseif kind == "Mail" then
        local mails = ...
        for _, mail in mails do
            local text, tone = mailText(mail)
            message:show(text, tone)
        end
        Sfx.play("RewardClaim")
    elseif kind == "Busy" then
        local text = ...
        message:show(text, "Warning")
    end
end)

player:GetAttributeChangedSignal("SpiritStones"):Connect(function()
    if current.open then
        balance.Text = stones(player:GetAttribute("SpiritStones") or 0)
    end
end)

-- the clocks, the walk away, and a fresh look every few seconds while it's open
local lastTick, lastPoll = 0, 0
RunService.Heartbeat:Connect(function()
    if not current.open then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root or not current.openedAt or (root.Position - current.openedAt).Magnitude > WALK_AWAY then
        window.close()
        return
    end
    local now = os.clock()
    if now - lastTick >= 0.5 then
        lastTick = now
        for label, timer in timers do
            if label.Parent then
                local text, urgent = timeLeft(timer.ends)
                label.Text = timer.prefix .. text
                label.TextColor3 = if urgent then C.Danger else (if timer.prefix == "" then C.AccentBright else C.Muted)
            else
                timers[label] = nil
            end
        end
    end
    if now - lastPoll >= 10 then
        lastPoll = now
        if current.tab == "Browse" and current.detailId then
            ask("Detail", current.detailId)
        elseif current.tab == "Browse" then
            ask("Browse", { Kind = current.kind, Rarity = current.rarity, Sort = SORTS[current.sort][1], Page = current.page })
        elseif current.tab == "Mine" then
            ask("Mine")
        end
    end
end)


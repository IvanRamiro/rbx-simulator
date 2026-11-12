-- The Wandering Merchant's window and his line on the HUD (MerchantService; GameConfig.WanderingMerchant). His prompt
-- opens the window (MerchantEvent "Open"): one card per deal of this visit, what it costs, and a Buy button (it asks once
-- more, a purchase can't be undone), "SOLD OUT" once bought, or why it's locked; the player's Spirit Stones and how long
-- he stays. It closes when he leaves or the player walks away. While he is in the hub a slim line under the currencies
-- (Hud.Banner) counts down to his leaving. His arrival and his last minute are notifications (MerchantEvent "Announce").
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Toast = require(UI:WaitForChild("Toast"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local MerchantEvent = RemoteEvents.MerchantEvent

-- as the shops (ShopController): his prompt opens within 12 studs and he sells within 45, so walking 30 away closes it first
local WALK_AWAY = 30
local CONFIRM_SECONDS = 3
local CARD_HEIGHT = 70

local message = Toast.new("MerchantMessage", C.Highlight, 5)

local function serverNow()
    return workspace:GetServerTimeNow()
end

local function clock(seconds)
    seconds = math.max(0, math.floor(seconds))
    return string.format("%d:%02d", seconds // 60, seconds % 60)
end

local function isHere()
    return workspace:GetAttribute("MerchantOpen") == true
end

local function secondsLeft()
    local leaves = workspace:GetAttribute("MerchantLeavesAt")
    return if typeof(leaves) == "number" then leaves - serverNow() else 0
end

-- ---------- the HUD line ----------
local line = UiKit.panel({
    Name = "MerchantLine", Brackets = false, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 26),
    LayoutOrder = 20, Visible = false, Parent = Hud.Banner,
})
UiKit.padding(line, 10, 0)
local lineText = UiKit.label({
    Name = "Text", Font = "Strong", TextSize = 13, TextColor3 = C.AccentBright, AutomaticSize = Enum.AutomaticSize.X,
    Size = UDim2.fromScale(0, 1), Parent = line,
})

-- ---------- the window ----------
local current = { state = nil, openedAt = nil }
local render

local window = Hud.window({
    -- short enough to clear the dock below and fit a phone in landscape (HudScale shrinks it, its list scrolls)
    Name = "MerchantWindow", Title = "WANDERING MERCHANT", Size = Vector2.new(560, 380), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5), OnClose = function()
        current.state = nil
    end,
})
local body = window.Body

local countdown = UiKit.label({
    Name = "Countdown", Font = "Strong", TextSize = 13, TextColor3 = C.Highlight, Position = UDim2.fromOffset(0, 4),
    Size = UDim2.new(0.5, 0, 0, 18), Parent = body,
})
local balance = UiKit.label({
    Name = "Balance", Font = "Strong", TextSize = 13, TextColor3 = C.AccentBright, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, 4), Size = UDim2.new(0.5, 0, 0, 18), TextXAlignment = Enum.TextXAlignment.Right, Parent = body,
})
local list = UiKit.scroll({ Name = "List", Position = UDim2.fromOffset(0, 28), Size = UDim2.new(1, 0, 1, -28), Parent = body })

local function stones()
    local attribute = player:GetAttribute("SpiritStones")
    return if typeof(attribute) == "number" then attribute elseif current.state then current.state.Stones else 0
end

local function rarestOf(eggId)
    local egg = GameConfig.Eggs[eggId]
    local best, weight = nil, math.huge
    for _, entry in egg and egg.Pool or {} do
        if entry.HatchChance < weight then
            best, weight = GameConfig.Pets[entry.PetId], entry.HatchChance
        end
    end
    return best
end

local function picture(deal)
    if deal.Kind == "Pet" then
        return Portraits.pet(deal.ItemId, 52)
    end
    return UiKit.icon(UiTheme.EggIcons[deal.ItemId] or UiTheme.Icons.Hatch, 52)
end

local function detailOf(deal)
    if deal.Kind == "Pet" then
        local pet = GameConfig.Pets[deal.ItemId]
        local color = GameConfig.PetRarityColors[deal.Rarity] or C.Text
        return string.format('<font color="#%s">%s</font>  ·  +%d%% Qi', color:ToHex(), deal.Rarity or "", pet and pet.QiBonus or 0)
    end
    local off = if deal.FullPrice and deal.FullPrice > 0 then math.floor((1 - deal.Price / deal.FullPrice) * 100 + 0.5) else 0
    local rarest = rarestOf(deal.ItemId)
    local up = if rarest then string.format('  ·  up to <font color="#%s">%s</font>',
        (GameConfig.PetRarityColors[rarest.Rarity] or C.Text):ToHex(), rarest.DisplayName) else ""
    return deal.Count .. (if deal.Count == 1 then " egg" else " eggs") .. "  ·  " .. off .. "% off" .. up
end

local function dealCard(order, deal)
    local rarityColor = deal.Rarity and GameConfig.PetRarityColors[deal.Rarity]
    local card = UiKit.card({ LayoutOrder = order, Size = UDim2.new(1, 0, 0, CARD_HEIGHT), Stripe = rarityColor or C.Accent, Parent = list })
    local art = picture(deal)
    art.Position = UDim2.fromOffset(10, 9)
    art.Parent = card
    UiKit.label({
        Font = "Title", TextSize = 14, Text = if deal.Kind == "Egg" and deal.Count > 1 then deal.Name .. "  x" .. deal.Count else deal.Name,
        TextColor3 = rarityColor or C.Text, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(72, 7), Size = UDim2.new(0.5, -72, 0, 18), Parent = card,
    })
    UiKit.label({
        TextSize = 11, RichText = true, TextColor3 = C.Muted, Text = detailOf(deal), TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(72, 27), Size = UDim2.new(0.5, -72, 0, 14), Parent = card,
    })
    UiKit.label({
        TextSize = 11, TextColor3 = if deal.Locked then C.Danger else C.Muted, TextTruncate = Enum.TextTruncate.AtEnd,
        Text = if deal.Bought then "Bought this visit"
            elseif deal.Locked then deal.Locked
            elseif deal.FullPrice then "Marketplace: " .. NumberFormat.compact(deal.FullPrice) .. " Stones"
            else "Sold to you directly, no hatching",
        Position = UDim2.fromOffset(72, 44), Size = UDim2.new(0.5, -72, 0, 14), Parent = card,
    })
    local affordable = stones() >= deal.Price
    UiKit.label({
        Font = "Strong", TextSize = 13, Text = NumberFormat.compact(deal.Price) .. " Stones",
        TextColor3 = if affordable and not deal.Bought then C.AccentBright else C.Muted,
        Position = UDim2.new(0.5, 0, 0, 26), Size = UDim2.new(0.2, -6, 0, 18), TextXAlignment = Enum.TextXAlignment.Right, Parent = card,
    })
    local why = if deal.Bought then "SOLD OUT" elseif deal.Locked then "LOCKED" elseif not affordable then "TOO DEAR" else nil
    local buy = UiKit.button({
        Font = "Strong", TextSize = 13, Text = why or "BUY", Tone = if why then "Quiet" else "Accent", Active = why == nil,
        -- tall enough for a thumb on a phone (the shops' buttons: 34 and up)
        Size = UDim2.new(0.3, -10, 0, 40), Position = UDim2.new(0.7, 0, 0.5, -20), Parent = card,
    })
    if why then
        return
    end
    local armedUntil = 0
    buy.Activated:Connect(function()
        if os.clock() < armedUntil then
            armedUntil = 0
            MerchantEvent:FireServer("Buy", deal.Id)
            return
        end
        armedUntil = os.clock() + CONFIRM_SECONDS
        buy.Text = "SURE?"
        task.delay(CONFIRM_SECONDS, function()
            if buy.Parent and os.clock() >= armedUntil then
                buy.Text = "BUY"
            end
        end)
    end)
end

local function updateCountdown()
    countdown.Text = "Leaves in " .. clock(secondsLeft())
    balance.Text = NumberFormat.compact(stones()) .. " Spirit Stones"
end

function render()
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
    local state = current.state
    if not state then
        return
    end
    updateCountdown()
    if #state.Deals == 0 then
        UiKit.empty(list, "Nothing for sale.\nHe brings new wares every visit.").LayoutOrder = 1
    end
    for index, deal in state.Deals do
        dealCard(index, deal)
    end
end

player:GetAttributeChangedSignal("SpiritStones"):Connect(function()
    if current.state then
        render() -- what they can afford changed
    end
end)

MerchantEvent.OnClientEvent:Connect(function(kind, ...)
    if kind == "Open" then
        local state = ...
        local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        window.open()
        current.state = state
        current.openedAt = root and root.Position
        render()
    elseif kind == "Result" then
        local ok, text, state = ...
        Sfx.play(if ok then "Purchase" else "Error")
        message:show(text, if ok then "Success" else "Error")
        if state and current.state then
            current.state = state
            render()
        end
    elseif kind == "Announce" then
        local text = ...
        if typeof(text) == "string" then
            message:show(text, "Info")
        end
    end
end)

-- ---------- every moment: the countdowns, and closing ----------
local function updateLine()
    local here = isHere()
    line.Visible = here
    if here then
        lineText.Text = (if Hud.isCompact() then "Merchant" else "Wandering Merchant") .. "  ·  leaves in " .. clock(secondsLeft())
    end
end
workspace:GetAttributeChangedSignal("MerchantOpen"):Connect(function()
    updateLine()
    if not isHere() then
        window.close()
    end
end)
workspace:GetAttributeChangedSignal("MerchantLeavesAt"):Connect(updateLine)
Hud.CompactChanged:Connect(updateLine)
updateLine()

local nextTick = 0
RunService.Heartbeat:Connect(function()
    local now = os.clock()
    if now >= nextTick then
        nextTick = now + 0.25
        updateLine()
        if current.state then
            updateCountdown()
        end
    end
    if not current.state then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not isHere() or not root or not current.openedAt or (root.Position - current.openedAt).Magnitude > WALK_AWAY then
        window.close()
    end
end)

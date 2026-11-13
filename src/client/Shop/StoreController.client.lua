-- The Shop (the first button on the HUD's rail, named so players can read it; the owner, November 10, 2026): the game passes (GameConfig.GamePasses), each
-- with its picture, what it does, and its live Robux price, and the Exclusive Egg, locked until its beast is made. A pass not on
-- sale yet (no GamePassId) says "Coming soon"; one the player owns says so. Buying is Roblox's own prompt; the server counts
-- the purchase (server/Shop/GamePassService) and sets the "Pass_<Id>" attribute, and this window and every other follow it.
-- Its look is "Cultivation Bold" (the owner, 2026-11-13: the top Roblox shops' patterns in our colours): two tabs (GAME PASSES,
-- EXCLUSIVE EGG), cards with heavy outlined words, and each price on a big green Robux button, the old price struck above it.
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local ROBUX = utf8.char(0xE002) -- Roblox's Robux sign, in its own fonts
local CARD_HEIGHT = 168
local TABS_HEIGHT = 40
local GAP = 8
local EGG = GameConfig.ExclusiveEgg

local toggleButton = Hud.railButton("StoreButton", UiTheme.Icons.Store, "Shop", 0)
-- on a phone the rail is a row of bare icons: the Shop keeps its name under its gift box, so players can always find it
local caption = UiKit.label({
    Name = "Caption", Font = "Strong", TextSize = 9, Text = "SHOP", TextColor3 = C.Highlight, TextXAlignment = Enum.TextXAlignment.Center,
    AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, 1), Size = UDim2.new(1, 0, 0, 11), ZIndex = 4, Parent = toggleButton,
})
local captionEdge = Instance.new("UIStroke")
captionEdge.Color = Color3.fromRGB(14, 12, 34)
captionEdge.Thickness = 1.5
captionEdge.Parent = caption
local function showCaption()
    caption.Visible = Hud.isCompact()
end
Hud.CompactChanged:Connect(showCaption)
showCaption()
local window = Hud.window({
    Name = "StoreWindow", Title = "SHOP", Size = Vector2.new(640, 470),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local message = Toast.new("StoreMessage", C.Highlight, 5)
-- the tabs, across the top of the window's body; each shows its own page under them
local tabBar = Instance.new("Frame")
tabBar.Name = "Tabs"
tabBar.BackgroundTransparency = 1
tabBar.Size = UDim2.new(1, 0, 0, TABS_HEIGHT - 6)
tabBar.Parent = window.Body
UiKit.list(tabBar, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8) })
local function page(name)
    local frame = UiKit.scroll({ Name = name, Position = UDim2.fromOffset(0, TABS_HEIGHT), Size = UDim2.new(1, 0, 1, -TABS_HEIGHT),
        Parent = window.Body })
    return frame
end
local list = page("List")
local eggPage = page("EggPage")
eggPage.Visible = false
local tabs = {}
local function showTab(name)
    local oddsView = window.Body:FindFirstChild("Odds") -- (built below) a tab press closes the odds
    if oddsView then
        oddsView.Visible = false
    end
    for tabName, tab in tabs do
        tab.button:SetAttribute("Tone", if tabName == name then "Highlight" else "Tile")
        tab.page.Visible = tabName == name
    end
end
local function tab(name, text, pageFrame, order)
    local button = UiKit.button({ Name = name .. "Tab", Font = "Heavy", TextSize = 14, Text = text, Tone = "Tile",
        Size = UDim2.fromOffset(170, TABS_HEIGHT - 6), LayoutOrder = order, Parent = tabBar })
    button:SetAttribute("EdgeThickness", 2)
    tabs[name] = { button = button, page = pageFrame }
    button.Activated:Connect(function()
        Sfx.play("Click")
        showTab(name)
    end)
end

local render -- (below)
local prices = {} -- [GamePassId] = its live price in Robux, once Roblox has said
local cards = {}

-- Roblox's paid random items policy covers a luck boost: its effect is shown in numbers before purchase (the ODDS panel), and
-- where paid random items are restricted (PolicyService) the pass can't be bought: its button says so instead.
local luckRestricted = false
task.spawn(function()
    local ok, info = pcall(PolicyService.GetPolicyInfoForPlayerAsync, PolicyService, player)
    luckRestricted = ok and typeof(info) == "table" and info.ArePaidRandomItemsRestricted == true
    if luckRestricted then
        render()
    end
end)

-- ---------- the luck pass's odds: every egg's chances by rarity, without and with it ----------
local odds = Instance.new("Frame")
odds.Name = "Odds"
odds.BackgroundTransparency = 1
odds.Position = UDim2.fromOffset(0, TABS_HEIGHT)
odds.Size = UDim2.new(1, 0, 1, -TABS_HEIGHT)
odds.Visible = false
odds.Parent = window.Body
local oddsBack = UiKit.button({ Name = "Back", Font = "Strong", TextSize = 12, Text = "< BACK", Tone = "Quiet",
    Size = UDim2.fromOffset(84, 28), Parent = odds })
local oddsTitle = UiKit.label({ Name = "Title", Font = "Strong", TextSize = 13, TextColor3 = C.AccentBright, Text = "",
    Position = UDim2.fromOffset(96, 0), Size = UDim2.new(1, -96, 0, 28), TextTruncate = Enum.TextTruncate.AtEnd, Parent = odds })
local oddsList = UiKit.scroll({ Name = "List", Position = UDim2.fromOffset(0, 36), Size = UDim2.new(1, 0, 1, -36), Parent = odds })
local oddsBuilt = false

local function buildOdds(pass)
    oddsTitle.Text = string.upper(pass.Name) .. ": EACH EGG'S CHANCES, WITHOUT  >  WITH IT"
    if oddsBuilt then
        return
    end
    oddsBuilt = true
    local eggs = {}
    for id, egg in GameConfig.Eggs do
        if egg.Exclusive then
            continue -- (takes no luck: its odds are on its own card)
        end
        local rank = Ranks.getRankById(egg.RequiredRank)
        table.insert(eggs, { id = id, egg = egg, order = rank and Ranks.getIndex(rank.Name) or 0 })
    end
    table.sort(eggs, function(a, b)
        if a.order ~= b.order then
            return a.order < b.order
        end
        return a.id < b.id
    end)
    for order, entry in eggs do
        local lucky = PassRules.luckyPool(entry.egg.Pool, pass.Luck)
        local byRarity, rarities = {}, {}
        for i, item in entry.egg.Pool do
            local pet = GameConfig.Pets[item.PetId]
            local rarity = pet and pet.Rarity or "Common"
            if not byRarity[rarity] then
                byRarity[rarity] = { base = 0, lucky = 0 }
                table.insert(rarities, rarity)
            end
            byRarity[rarity].base += item.HatchChance
            byRarity[rarity].lucky += lucky[i].HatchChance
        end
        table.sort(rarities, function(a, b)
            return (PassRules.RarityOrder[a] or 0) < (PassRules.RarityOrder[b] or 0)
        end)
        local card = UiKit.card({ Name = entry.id, Size = UDim2.new(1, 0, 0, 30 + 18 * #rarities), LayoutOrder = order, Parent = oddsList })
        UiKit.label({ Font = "Title", TextSize = 14, Text = entry.egg.DisplayName, Position = UDim2.fromOffset(12, 6),
            Size = UDim2.new(1, -24, 0, 18), Parent = card })
        for k, rarity in rarities do
            local row = byRarity[rarity]
            local boosted = row.lucky > row.base + 1e-6
            UiKit.label({ Font = "Strong", TextSize = 12, Text = rarity, TextColor3 = GameConfig.PetRarityColors[rarity] or C.Text,
                Position = UDim2.fromOffset(20, 10 + 18 * k), Size = UDim2.new(0.45, -20, 0, 16), Parent = card })
            UiKit.label({ Font = "Strong", TextSize = 12,
                Text = string.format("%.3g%%  >  %.3g%%", row.base, row.lucky),
                TextColor3 = if boosted then C.Highlight else C.Muted, TextXAlignment = Enum.TextXAlignment.Right,
                AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -14, 0, 10 + 18 * k), Size = UDim2.new(0.55, -14, 0, 16), Parent = card })
        end
    end
end

local function showOdds(pass)
    buildOdds(pass)
    list.Visible = false
    odds.Visible = true
end
oddsBack.Activated:Connect(function()
    odds.Visible = false
    list.Visible = true
end)

-- words in the heavy face with a dark outline (the bold look)
local function bold(props)
    props.Font = props.Font or "Heavy"
    local label = UiKit.label(props)
    UiKit.outline(label, props.TextSize >= 18 and 2 or 1.5)
    return label
end

-- one pass: its picture, its name and headline, what it does, the old price struck through, and its big price button
local function passCard(pass, parent, slot)
    local card = UiKit.card({
        Name = pass.Id, Position = UDim2.new(slot * 0.5, if slot == 0 then 0 else GAP / 2, 0, 0),
        Size = UDim2.new(0.5, -GAP / 2, 1, 0), Parent = parent,
    })
    card.BackgroundTransparency = 0.1
    local edge = card:FindFirstChildOfClass("UIStroke")
    edge.Thickness = 2
    card:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 10)
    local picture = Instance.new("ImageLabel")
    picture.Name = "Picture"
    picture.BackgroundTransparency = 1
    picture.Image = pass.Icon
    picture.Position = UDim2.fromOffset(8, 8)
    picture.Size = UDim2.fromOffset(84, 84)
    picture.Parent = card
    bold({
        Name = "PassName", Text = string.upper(pass.Name), TextSize = 17, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(100, 10), Size = UDim2.new(1, -108, 0, 22), Parent = card,
    })
    bold({
        Name = "Headline", Text = pass.Headline or "", TextSize = 20, TextColor3 = C.Highlight,
        Position = UDim2.fromOffset(100, 34), Size = UDim2.new(1, -108, 0, 24), Parent = card,
    })
    UiKit.label({
        Name = "What", Font = "Strong", TextSize = 12, Text = pass.Text, TextColor3 = C.Muted, TextWrapped = true,
        TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(100, 60), Size = UDim2.new(1, -108, 0, 44), Parent = card,
    })
    -- the price it had before the cut, struck through, just over the button (shown by render only while the live price is lower)
    local was = bold({
        Name = "WasPrice", Text = "", RichText = true, TextSize = 14, TextColor3 = C.Danger,
        TextXAlignment = Enum.TextXAlignment.Right, AnchorPoint = Vector2.new(1, 1),
        Position = UDim2.new(1, -12, 1, -56), Size = UDim2.new(1, -24, 0, 16), Visible = false, Parent = card,
    })
    local button = UiKit.button({
        Name = "Buy", Font = "Heavy", TextSize = 20, Text = "", AnchorPoint = Vector2.new(0, 1),
        Position = UDim2.new(0, 10, 1, -10), Size = UDim2.new(1, if pass.Luck then -94 else -20, 0, 42), Parent = card,
    })
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 10)
    button:SetAttribute("EdgeThickness", 2)
    -- the words on their own label, so they can carry an outline (the button's own stroke is its border)
    local price = bold({
        Name = "Price", Text = "", TextSize = 20, TextColor3 = Color3.new(1, 1, 1), TextXAlignment = Enum.TextXAlignment.Center,
        Size = UDim2.fromScale(1, 1), ZIndex = button.ZIndex + 1, Parent = button,
    })
    button.Activated:Connect(function()
        if pass.Luck and luckRestricted and not PassRules.owns(player, pass.Id) then
            Sfx.play("Error")
            message:show(pass.Name .. " isn't available in your region: luck boosts follow Roblox's rules on paid random items.", "Warning")
        elseif button.Active and (pass.GamePassId or 0) > 0 and not PassRules.owns(player, pass.Id) then
            Sfx.play("Click")
            MarketplaceService:PromptGamePassPurchase(player, pass.GamePassId)
        end
    end)
    if pass.Luck then -- its effect, in numbers, before anyone buys it: beside its Buy button (in the top corner it covered the
        -- description's first line, seen in Play 2026-11-12)
        local oddsButton = UiKit.button({ Name = "Odds", Font = "Heavy", TextSize = 13, Text = "ODDS", Tone = "Accent",
            AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -10, 1, -10), Size = UDim2.fromOffset(76, 42), Parent = card })
        oddsButton:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 10)
        oddsButton.Activated:Connect(function()
            Sfx.play("Click")
            showOdds(pass)
        end)
    end
    cards[pass.Id] = { pass = pass, button = button, price = price, was = was }
end

for row = 0, math.ceil(#PassRules.List / 2) - 1 do
    local frame = Instance.new("Frame")
    frame.Name = "Row" .. row + 1
    frame.BackgroundTransparency = 1
    frame.Size = UDim2.new(1, 0, 0, CARD_HEIGHT)
    frame.LayoutOrder = 2 + row
    frame.Parent = list
    for slot = 0, 1 do
        local pass = PassRules.List[row * 2 + slot + 1]
        if pass then
            passCard(pass, frame, slot)
        end
    end
end

-- the Exclusive Egg (the owner, 2026-11-13): bought with Robux, one egg each time (ProductService gives it), hatched at the Hatching
-- Altar. Its three beasts and their chances are on the card, beside the price, before anyone buys; where paid random items are
-- restricted (PolicyService) it can't be bought. Before its product exists (ProductId 0) it stays locked.
local EGG_POOL = GameConfig.Eggs[EGG.EggId or ""]
local eggCard = UiKit.card({ Name = "ExclusiveEgg", Size = UDim2.new(1, 0, 0, 330), LayoutOrder = 1, Parent = eggPage })
eggCard.BackgroundTransparency = 0.1
eggCard:FindFirstChildOfClass("UIStroke").Thickness = 2
eggCard:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 10)
local eggPicture = Instance.new("ImageLabel")
eggPicture.Name = "Picture"
eggPicture.BackgroundTransparency = 1
eggPicture.Image = EGG.Icon
eggPicture.AnchorPoint = Vector2.new(0, 0.5)
eggPicture.Position = UDim2.new(0, 16, 0.5, 0)
eggPicture.Size = UDim2.fromOffset(210, 210)
eggPicture.Parent = eggCard
local EGG_TEXT_X = 240
bold({ Name = "EggName", Text = string.upper(EGG.Name), TextSize = 26, Position = UDim2.fromOffset(EGG_TEXT_X, 24),
    Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 32), Parent = eggCard })
local eggHeadline = bold({ Name = "Headline", Text = "COMING SOON!", TextSize = 20, TextColor3 = C.Highlight, Position = UDim2.fromOffset(EGG_TEXT_X, 60),
    Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 24), Parent = eggCard })
-- its beasts, rarest last, each with its chance
local oddsRows = Instance.new("Frame")
oddsRows.Name = "Odds"
oddsRows.BackgroundTransparency = 1
oddsRows.Position = UDim2.fromOffset(EGG_TEXT_X, 94)
oddsRows.Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 96)
oddsRows.Parent = eggCard
UiKit.list(oddsRows, { FillDirection = Enum.FillDirection.Vertical, Padding = UDim.new(0, 4) })
for order, entry in if EGG_POOL then EGG_POOL.Pool else {} do
    local pet = GameConfig.Pets[entry.PetId]
    local row = Instance.new("Frame")
    row.Name = entry.PetId
    row.BackgroundTransparency = 1
    row.Size = UDim2.new(1, 0, 0, 26)
    row.LayoutOrder = order
    row.Parent = oddsRows
    local tag = UiKit.tag(pet.Rarity, GameConfig.PetRarityColors[pet.Rarity])
    tag.AnchorPoint = Vector2.new(0, 0.5)
    tag.Position = UDim2.fromScale(0, 0.5)
    tag.Parent = row
    bold({ Name = "PetName", Text = pet.DisplayName, TextSize = 16, Position = UDim2.fromOffset(88, 0), Size = UDim2.new(1, -150, 1, 0),
        TextTruncate = Enum.TextTruncate.AtEnd, Parent = row })
    bold({ Name = "Chance", Text = entry.HatchChance .. "%", TextSize = 16, TextColor3 = GameConfig.PetRarityColors[pet.Rarity],
        TextXAlignment = Enum.TextXAlignment.Right, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0),
        Size = UDim2.new(0, 60, 1, 0), Parent = row })
end
UiKit.label({ Name = "What", Font = "Strong", TextSize = 12, Text = "Hatch it at the Hatching Altar. Luck doesn't change these chances.",
    TextColor3 = C.Muted, TextWrapped = true, Position = UDim2.fromOffset(EGG_TEXT_X, 196), Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 30),
    Parent = eggCard })
local eggBuy = UiKit.button({ Name = "Buy", Font = "Heavy", TextSize = 16, Text = "", Tone = "Quiet",
    AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, EGG_TEXT_X, 1, -20), Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 48), Parent = eggCard })
eggBuy:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 10)
eggBuy:SetAttribute("EdgeThickness", 2)
eggBuy.Active = false
local eggPrice = bold({ Name = "Price", Text = "LOCKED", TextSize = 18, TextColor3 = Color3.new(1, 1, 1), TextXAlignment = Enum.TextXAlignment.Center,
    Size = UDim2.fromScale(1, 1), ZIndex = eggBuy.ZIndex + 1, Parent = eggBuy })
local padlock = Instance.new("ImageLabel")
padlock.Name = "Lock"
padlock.BackgroundTransparency = 1
padlock.Image = UiTheme.Icons.Lock
padlock.AnchorPoint = Vector2.new(1, 1)
padlock.Position = UDim2.new(0, 222, 1, -48)
padlock.Size = UDim2.fromOffset(52, 52)
padlock.Parent = eggCard
local eggLivePrice = nil -- the product's price on Roblox, once asked

local function eggOnSale()
    return (EGG.ProductId or 0) > 0 and EGG_POOL ~= nil
end

local function renderEgg()
    local onSale = eggOnSale()
    local tone, text
    if not onSale then
        tone, text = "Quiet", "LOCKED"
    elseif luckRestricted then
        tone, text = "Quiet", "NOT AVAILABLE HERE"
    else
        tone, text = "Buy", ROBUX .. " " .. tostring(eggLivePrice or EGG.Price)
    end
    eggBuy.Active = tone == "Buy"
    eggBuy:SetAttribute("Tone", tone)
    eggPrice.Text = text
    eggPrice.TextSize = if tone == "Buy" then 22 else 16
    eggPrice.TextColor3 = if tone == "Buy" then Color3.new(1, 1, 1) else C.Muted
    eggHeadline.Text = if onSale then "3 EXCLUSIVE BEASTS!" else "COMING SOON!"
    padlock.Visible = not onSale
end

eggBuy.Activated:Connect(function()
    if not eggBuy.Active then
        return
    end
    if (player:GetAttribute("Egg_" .. EGG.EggId) or 0) >= 99 then
        Sfx.play("Error")
        message:show("You're holding as many Exclusive Eggs as you can. Hatch some at the Hatching Altar first.", "Warning")
        return
    end
    Sfx.play("Click")
    MarketplaceService:PromptProductPurchase(player, EGG.ProductId)
end)

-- an egg arrived (ProductService): say where it hatches
local heldEggs = player:GetAttribute("Egg_" .. (EGG.EggId or "")) or 0
player:GetAttributeChangedSignal("Egg_" .. (EGG.EggId or "")):Connect(function()
    local now = player:GetAttribute("Egg_" .. EGG.EggId) or 0
    if now > heldEggs then
        Sfx.play("RareReveal")
        message:show("An Exclusive Egg is yours! Hatch it at the Hatching Altar. Thank you for supporting the game!", "Reward")
    end
    heldEggs = now
end)

function render()
    for _, entry in cards do
        local pass, button = entry.pass, entry.button
        local onSale = (pass.GamePassId or 0) > 0
        local owned = PassRules.owns(player, pass.Id)
        local livePrice = prices[pass.GamePassId] or pass.Price
        local tone, text
        if owned then
            tone, text = "Active", "OWNED"
        elseif pass.Luck and luckRestricted then
            tone, text = "Quiet", "NOT AVAILABLE HERE"
        elseif not onSale then
            tone, text = "Quiet", "COMING SOON"
        else
            tone, text = "Buy", ROBUX .. " " .. tostring(livePrice)
        end
        button.Active = onSale and not owned
        button:SetAttribute("Tone", tone)
        entry.price.Text = text
        entry.price.TextSize = if tone == "Buy" then 22 else 15
        local cut = tone == "Buy" and pass.WasPrice and livePrice < pass.WasPrice
        entry.was.Visible = cut == true
        entry.was.Text = if cut then "<s>" .. ROBUX .. " " .. pass.WasPrice .. "</s>" else ""
    end
    renderEgg()
end

-- each pass's live price, once (a price changed on Roblox shows here without a new release)
local function fetchPrices()
    if eggOnSale() and not eggLivePrice then
        task.spawn(function()
            local ok, info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, EGG.ProductId, Enum.InfoType.Product)
            if ok and info and typeof(info.PriceInRobux) == "number" then
                eggLivePrice = info.PriceInRobux
                render()
            end
        end)
    end
    for _, pass in PassRules.List do
        local id = pass.GamePassId or 0
        if id > 0 and not prices[id] then
            task.spawn(function()
                local ok, info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, id, Enum.InfoType.GamePass)
                if ok and info and typeof(info.PriceInRobux) == "number" then
                    prices[id] = info.PriceInRobux
                    render()
                end
            end)
        end
    end
end

for _, pass in PassRules.List do
    player:GetAttributeChangedSignal("Pass_" .. pass.Id):Connect(function()
        render()
        if PassRules.owns(player, pass.Id) and player:GetAttribute("PassesChecked") then -- bought just now, not found on joining
            Sfx.play("RareReveal")
            message:show(pass.Name .. " is yours. Thank you for supporting the game!", "Reward")
        end
    end)
end
tab("Passes", "GAME PASSES", list, 1)
tab("Egg", "EXCLUSIVE EGG", eggPage, 2)
showTab("Passes")
render()

window.link(toggleButton)
toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        fetchPrices()
        render()
        window.open()
    end
end)

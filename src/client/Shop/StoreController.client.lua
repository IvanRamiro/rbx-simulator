-- The Shop (the first button on the HUD's rail, named so players can read it; the owner, November 10, 2026): the game passes (GameConfig.GamePasses), each
-- with its picture, what it does, and its live Robux price, and the Exclusive Egg, locked until its beast is made. A pass not on
-- sale yet (no GamePassId) says "Coming soon"; one the player owns says so. Buying is Roblox's own prompt; the server counts
-- the purchase (server/Shop/GamePassService) and sets the "Pass_<Id>" attribute, and this window and every other follow it.
-- Its look is "Cultivation Bold" (the owner, 2026-11-13: the top Roblox shops' patterns in our colours): three tabs (QI BOOSTS, GAME
-- PASSES, EXCLUSIVE EGG), cards with heavy outlined words, and each price on a big green Robux button, the old price struck above it.
-- QI BOOSTS (the owner, 2026-11-15) sells the Qi multiplier tiers (passes with a QiTier): only the highest one owned counts, so a
-- tier under one already owned says INCLUDED and can't be bought.
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
local CARD_HEIGHT = 172
local TAB = UiTheme.Height.Tab
local TABS_HEIGHT = TAB + UiTheme.Space.M -- the tabs, and the gap under them
local GAP = UiTheme.Space.S
local EGG = GameConfig.ExclusiveEgg

-- on a phone the rail is a row of bare icons: the Shop keeps its name under its gift box, so players can always find it
local toggleButton = Hud.railButton("StoreButton", UiTheme.Icons.Store, "Shop", 0, { KeepWord = true })
local window = Hud.window({
    Name = "StoreWindow", Title = "SHOP", Size = Vector2.new(660, 500),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local message = Toast.new("StoreMessage", C.Highlight, 5)
-- the tabs, across the top of the window's body; each shows its own page under them
local tabBar = Instance.new("Frame")
tabBar.Name = "Tabs"
tabBar.BackgroundTransparency = 1
tabBar.Size = UDim2.new(1, 0, 0, TAB)
tabBar.Parent = window.Body
UiKit.list(tabBar, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
local function page(name)
    local frame = UiKit.scroll({ Name = name, Position = UDim2.fromOffset(0, TABS_HEIGHT), Size = UDim2.new(1, 0, 1, -TABS_HEIGHT),
        Parent = window.Body })
    return frame
end
local qiPage = page("QiPage")
local list = page("List")
list.Visible = false
local eggPage = page("EggPage")
eggPage.Visible = false
local tabs = {}
local function showTab(name)
    local oddsView = window.Body:FindFirstChild("Odds") -- (built below) a tab press closes the odds
    if oddsView then
        oddsView.Visible = false
    end
    for tabName, tab in tabs do
        UiKit.selectTab(tab.button, tabName == name)
        tab.page.Visible = tabName == name
    end
end
local function tab(name, text, pageFrame, order)
    local share = UiTheme.Space.S * 2 / 3 -- three tabs share the bar's width (fixed widths ran past a phone's window)
    local button = UiKit.tab({ Name = name .. "Tab", Text = text, Size = UDim2.new(1 / 3, -share, 0, TAB), LayoutOrder = order, Parent = tabBar })
    tabs[name] = { button = button, page = pageFrame }
    button.Activated:Connect(function()
        Sfx.play("Tab")
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
local SMALL = UiTheme.Height.ButtonSmall
local oddsBack = UiKit.button({ Name = "Back", TextSize = 13, Text = "< BACK", Tone = "Quiet",
    Size = UDim2.fromOffset(96, SMALL), Parent = odds })
local oddsTitle = UiKit.boldLabel({ Name = "Title", TextSize = 13, TextColor3 = C.AccentBright, Text = "",
    Position = UDim2.fromOffset(96 + UiTheme.Space.M, 0), Size = UDim2.new(1, -(96 + UiTheme.Space.M), 0, SMALL),
    TextTruncate = Enum.TextTruncate.AtEnd, Parent = odds })
local oddsList = UiKit.scroll({ Name = "List", Position = UDim2.fromOffset(0, SMALL + UiTheme.Space.M),
    Size = UDim2.new(1, 0, 1, -(SMALL + UiTheme.Space.M)), Parent = odds })
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
        local card = UiKit.card({ Name = entry.id, Size = UDim2.new(1, 0, 0, 36 + 18 * #rarities), LayoutOrder = order, Parent = oddsList })
        UiKit.boldLabel({ TextSize = 14, Text = entry.egg.DisplayName, Position = UDim2.fromOffset(12, 8),
            Size = UDim2.new(1, -24, 0, 18), Parent = card })
        for k, rarity in rarities do
            local row = byRarity[rarity]
            local boosted = row.lucky > row.base + 1e-6
            UiKit.label({ Font = "Strong", TextSize = 12, Text = rarity, TextColor3 = GameConfig.PetRarityColors[rarity] or C.Text,
                Position = UDim2.fromOffset(20, 14 + 18 * k), Size = UDim2.new(0.45, -20, 0, 16), Parent = card })
            UiKit.label({ Font = "Strong", TextSize = 12,
                Text = string.format("%.3g%%  >  %.3g%%", row.base, row.lucky),
                TextColor3 = if boosted then C.Highlight else C.Muted, TextXAlignment = Enum.TextXAlignment.Right,
                AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -14, 0, 14 + 18 * k), Size = UDim2.new(0.55, -14, 0, 16), Parent = card })
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
    if pass.QiTier then -- the tier, big over its picture, so the four cards read at a glance
        bold({ Name = "Tier", Text = pass.QiTier .. "x", TextSize = 30, TextColor3 = C.Highlight, TextXAlignment = Enum.TextXAlignment.Center,
            AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, 4), Size = UDim2.new(1, 0, 0, 34), ZIndex = picture.ZIndex + 1,
            Parent = picture })
    end
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
        Position = UDim2.new(1, -12, 1, -64), Size = UDim2.new(1, -24, 0, 16), Visible = false, Parent = card,
    })
    local button = UiKit.button({
        Name = "Buy", TextSize = 20, Text = "", AnchorPoint = Vector2.new(0, 1),
        Position = UDim2.new(0, 12, 1, -12), Size = UDim2.new(1, if pass.Luck then -112 else -24, 0, UiTheme.Height.ButtonLarge - 4), Parent = card,
    })
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
            if pass.QiTier and pass.QiTier < PassRules.qiTier(player) then
                return -- (INCLUDED: a higher tier already counts)
            end
            MarketplaceService:PromptGamePassPurchase(player, pass.GamePassId)
        end
    end)
    if pass.Luck then -- its effect, in numbers, before anyone buys it: beside its Buy button (in the top corner it covered the
        -- description's first line, seen in Play 2026-11-12)
        local oddsButton = UiKit.button({ Name = "Odds", TextSize = 14, Text = "ODDS", Tone = "Accent",
            AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -12, 1, -12), Size = UDim2.fromOffset(84, UiTheme.Height.ButtonLarge - 4), Parent = card })
        oddsButton.Activated:Connect(function()
            Sfx.play("Click")
            showOdds(pass)
        end)
    end
    cards[pass.Id] = { pass = pass, button = button, price = price, was = was }
end

-- cards two to a row
local function cardRows(passes, parent, firstOrder)
    for row = 0, math.ceil(#passes / 2) - 1 do
        local frame = Instance.new("Frame")
        frame.Name = "Row" .. row + 1
        frame.BackgroundTransparency = 1
        frame.Size = UDim2.new(1, 0, 0, CARD_HEIGHT)
        frame.LayoutOrder = firstOrder + row
        frame.Parent = parent
        for slot = 0, 1 do
            local pass = passes[row * 2 + slot + 1]
            if pass then
                passCard(pass, frame, slot)
            end
        end
    end
end
local qiTiers, otherPasses = {}, {}
for _, pass in PassRules.List do
    table.insert(if pass.QiTier then qiTiers else otherPasses, pass)
end
table.sort(qiTiers, function(a, b)
    return a.QiTier < b.QiTier
end)
cardRows(otherPasses, list, 2)

-- QI BOOSTS: what the player's Qi is multiplied by now, the rule, then the tiers
local qiHeader = UiKit.card({ Name = "Current", Size = UDim2.new(1, 0, 0, 64), LayoutOrder = 1, Parent = qiPage })
qiHeader.BackgroundTransparency = 0.1
qiHeader:FindFirstChildOfClass("UIStroke").Thickness = 2
local qiIcon = Instance.new("ImageLabel")
qiIcon.Name = "Icon"
qiIcon.BackgroundTransparency = 1
qiIcon.Image = UiTheme.Icons.Qi
qiIcon.AnchorPoint = Vector2.new(0, 0.5)
qiIcon.Position = UDim2.new(0, 12, 0.5, 0)
qiIcon.Size = UDim2.fromOffset(40, 40)
qiIcon.Parent = qiHeader
local qiNow = bold({ Name = "Now", Text = "", TextSize = 18, Position = UDim2.fromOffset(62, 8), Size = UDim2.new(1, -74, 0, 24), Parent = qiHeader })
UiKit.label({ Name = "Rule", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true,
    Text = "Only your highest Qi boost counts, on everything that gives Qi. VIP's +10% adds on top.",
    Position = UDim2.fromOffset(62, 32), Size = UDim2.new(1, -74, 0, 28), Parent = qiHeader })
cardRows(qiTiers, qiPage, 2)

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
local eggName = bold({ Name = "EggName", Text = string.upper(EGG.Name), TextSize = 26, Position = UDim2.fromOffset(EGG_TEXT_X, 24),
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
local eggWhat = UiKit.label({ Name = "What", Font = "Strong", TextSize = 12, Text = "Hatch it at the Hatching Altar. Luck doesn't change these chances.",
    TextColor3 = C.Muted, TextWrapped = true, Position = UDim2.fromOffset(EGG_TEXT_X, 196), Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 30),
    Parent = eggCard })
local eggBuy = UiKit.button({ Name = "Buy", TextSize = 16, Text = "", Tone = "Quiet",
    AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, EGG_TEXT_X, 1, -20), Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, UiTheme.Height.ButtonLarge), Parent = eggCard })
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

-- Two layouts. A tall window: the big picture left, everything else beside it. A phone's short window (its page is under 200
-- high): the card fits the page whole, so the price is seen without scrolling: a smaller picture over the Buy button on the
-- left, the name, headline and the three beasts' chances on the right.
local function layoutEgg()
    local scale = Hud.windowScale()
    local short = eggPage.AbsoluteSize.Y > 0 and eggPage.AbsoluteSize.Y / scale < 260
    if short then
        local LEFT, PICTURE = 156, 104
        local x = 12 + LEFT + 16
        eggCard.Size = UDim2.new(1, 0, 0, math.max(168, eggPage.AbsoluteSize.Y / scale - 8))
        eggPicture.AnchorPoint = Vector2.new(0.5, 0)
        eggPicture.Position = UDim2.fromOffset(12 + LEFT / 2, 6)
        eggPicture.Size = UDim2.fromOffset(PICTURE, PICTURE)
        padlock.AnchorPoint = Vector2.new(1, 1)
        padlock.Position = UDim2.fromOffset(12 + LEFT / 2 + PICTURE / 2, 6 + PICTURE)
        padlock.Size = UDim2.fromOffset(36, 36)
        eggName.TextSize = 20
        eggName.Position = UDim2.fromOffset(x, 12)
        eggName.Size = UDim2.new(1, -x - 16, 0, 24)
        eggHeadline.TextSize = 16
        eggHeadline.Position = UDim2.fromOffset(x, 38)
        eggHeadline.Size = UDim2.new(1, -x - 16, 0, 20)
        oddsRows.Position = UDim2.fromOffset(x, 66)
        oddsRows.Size = UDim2.new(1, -x - 16, 0, 90)
        eggWhat.Visible = false
        eggBuy.Position = UDim2.new(0, 12, 1, -12)
        eggBuy.Size = UDim2.fromOffset(LEFT, UiTheme.Height.Button)
    else
        eggCard.Size = UDim2.new(1, 0, 0, 330)
        eggPicture.AnchorPoint = Vector2.new(0, 0.5)
        eggPicture.Position = UDim2.new(0, 16, 0.5, 0)
        eggPicture.Size = UDim2.fromOffset(210, 210)
        padlock.AnchorPoint = Vector2.new(1, 1)
        padlock.Position = UDim2.new(0, 222, 1, -48)
        padlock.Size = UDim2.fromOffset(52, 52)
        eggName.TextSize = 26
        eggName.Position = UDim2.fromOffset(EGG_TEXT_X, 24)
        eggName.Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 32)
        eggHeadline.TextSize = 20
        eggHeadline.Position = UDim2.fromOffset(EGG_TEXT_X, 60)
        eggHeadline.Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 24)
        oddsRows.Position = UDim2.fromOffset(EGG_TEXT_X, 94)
        oddsRows.Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, 96)
        eggWhat.Visible = true
        eggBuy.Position = UDim2.new(0, EGG_TEXT_X, 1, -20)
        eggBuy.Size = UDim2.new(1, -EGG_TEXT_X - 16, 0, UiTheme.Height.ButtonLarge)
    end
end
eggPage:GetPropertyChangedSignal("AbsoluteSize"):Connect(layoutEgg)
layoutEgg()
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
        Sfx.play("PremiumPurchase")
        message:show("An Exclusive Egg is yours! Hatch it at the Hatching Altar. Thank you for supporting the game!", "Reward")
    end
    heldEggs = now
end)

function render()
    local tier = PassRules.qiTier(player)
    local multiplier = PassRules.qiMultiplier(player)
    qiNow.Text = if tier > 1 then string.format("YOUR QI BOOST: %dx  (QI x%s)", tier, string.format("%.3g", multiplier))
        else "NO QI BOOST YET" .. (if multiplier > 1 then string.format("  (QI x%.3g)", multiplier) else "")
    for _, entry in cards do
        local pass, button = entry.pass, entry.button
        local onSale = (pass.GamePassId or 0) > 0
        local owned = PassRules.owns(player, pass.Id)
        local included = pass.QiTier ~= nil and not owned and pass.QiTier < tier -- a higher tier already covers it
        local livePrice = prices[pass.GamePassId] or pass.Price
        local tone, text
        if owned then
            tone, text = "Active", "OWNED"
        elseif included then
            tone, text = "Quiet", "INCLUDED"
        elseif pass.Luck and luckRestricted then
            tone, text = "Quiet", "NOT AVAILABLE HERE"
        elseif not onSale then
            tone, text = "Quiet", "COMING SOON"
        else
            tone, text = "Buy", ROBUX .. " " .. tostring(livePrice)
        end
        button.Active = onSale and not owned and not included
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
            Sfx.play("PremiumPurchase")
            message:show(pass.Name .. " is yours. Thank you for supporting the game!", "Reward")
        end
    end)
end
tab("Qi", "QI BOOSTS", qiPage, 1)
tab("Passes", "GAME PASSES", list, 2)
tab("Egg", "EXCLUSIVE EGG", eggPage, 3)
showTab("Qi")
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

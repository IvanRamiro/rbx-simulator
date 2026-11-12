-- The Shop (the first button on the HUD's rail, named so players can read it; the owner, November 10, 2026): the game passes (GameConfig.GamePasses), each
-- with its picture, what it does, and its live Robux price, and the Exclusive Egg, locked until its beast is made. A pass not on
-- sale yet (no GamePassId) says "Coming soon"; one the player owns says so. Buying is Roblox's own prompt; the server counts
-- the purchase (server/Shop/GamePassService) and sets the "Pass_<Id>" attribute, and this window and every other follow it.
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
local CARD_HEIGHT = 128
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
    Name = "StoreWindow", Title = "SHOP", Size = Vector2.new(560, 470),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local message = Toast.new("StoreMessage", C.Highlight, 5)
local list = UiKit.scroll({ Name = "List", Size = UDim2.fromScale(1, 1), Parent = window.Body })

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
odds.Size = UDim2.fromScale(1, 1)
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

-- one pass: its picture, name, what it does, and its button
local function passCard(pass, parent, slot)
    local card = UiKit.card({
        Name = pass.Id, Position = UDim2.new(slot * 0.5, if slot == 0 then 0 else GAP / 2, 0, 0),
        Size = UDim2.new(0.5, -GAP / 2, 1, 0), Stripe = C.Accent, Parent = parent,
    })
    local picture = Instance.new("ImageLabel")
    picture.Name = "Picture"
    picture.BackgroundTransparency = 1
    picture.Image = pass.Icon
    picture.Position = UDim2.fromOffset(10, 10)
    picture.Size = UDim2.fromOffset(64, 64)
    picture.Parent = card
    UiKit.label({
        Name = "PassName", Font = "Title", TextSize = 15, Text = pass.Name, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(84, 10), Size = UDim2.new(1, -92, 0, 20), Parent = card,
    })
    UiKit.label({
        Name = "What", Font = "Body", TextSize = 12, Text = pass.Text, TextColor3 = C.Muted, TextWrapped = true,
        TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(84, 32), Size = UDim2.new(1, -92, 0, 48), Parent = card,
    })
    local button = UiKit.button({
        Name = "Buy", Font = "Strong", TextSize = 14, Text = "", AnchorPoint = Vector2.new(0, 1),
        Position = UDim2.new(0, 10, 1, -10), Size = UDim2.new(1, if pass.Luck then -86 else -20, 0, 34), Parent = card,
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
        local oddsButton = UiKit.button({ Name = "Odds", Font = "Strong", TextSize = 12, Text = "ODDS", Tone = "Accent",
            AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -10, 1, -10), Size = UDim2.fromOffset(70, 34), Parent = card })
        oddsButton.Activated:Connect(function()
            Sfx.play("Click")
            showOdds(pass)
        end)
    end
    cards[pass.Id] = { pass = pass, button = button }
end

local function sectionHeader(text, order)
    UiKit.header(list, text, { TextSize = 13, LayoutOrder = order })
end

sectionHeader("GAME PASSES", 1)
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

-- the Exclusive Egg: locked, until its beast is made
sectionHeader("EXCLUSIVE EGG", 50)
local eggCard = UiKit.card({ Name = "ExclusiveEgg", Size = UDim2.new(1, 0, 0, 92), LayoutOrder = 51, Stripe = C.Highlight, Parent = list })
local eggPicture = Instance.new("ImageLabel")
eggPicture.Name = "Picture"
eggPicture.BackgroundTransparency = 1
eggPicture.Image = EGG.Icon
eggPicture.Position = UDim2.fromOffset(10, 8)
eggPicture.Size = UDim2.fromOffset(76, 76)
eggPicture.Parent = eggCard
UiKit.label({ Name = "EggName", Font = "Title", TextSize = 16, Text = EGG.Name, Position = UDim2.fromOffset(96, 14),
    Size = UDim2.new(1, -250, 0, 20), Parent = eggCard })
UiKit.label({ Name = "What", Font = "Body", TextSize = 12, Text = EGG.Text, TextColor3 = C.Muted, TextWrapped = true,
    TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(96, 38), Size = UDim2.new(1, -250, 0, 40), Parent = eggCard })
local soon = UiKit.button({ Name = "Soon", Font = "Strong", TextSize = 13, Text = "COMING SOON", Tone = "Quiet",
    AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -12, 0.5, 0), Size = UDim2.fromOffset(136, 36), Parent = eggCard })
soon.Active = false
local padlock = Instance.new("ImageLabel")
padlock.Name = "Lock"
padlock.BackgroundTransparency = 1
padlock.Image = UiTheme.Icons.Lock
padlock.AnchorPoint = Vector2.new(1, 1)
padlock.Position = UDim2.new(0, 88, 0, 86)
padlock.Size = UDim2.fromOffset(26, 26)
padlock.Parent = eggCard

function render()
    for _, entry in cards do
        local pass, button = entry.pass, entry.button
        local onSale = (pass.GamePassId or 0) > 0
        local owned = PassRules.owns(player, pass.Id)
        local tone, text
        if owned then
            tone, text = "Active", "OWNED"
        elseif pass.Luck and luckRestricted then
            tone, text = "Quiet", "NOT AVAILABLE HERE"
        elseif not onSale then
            tone, text = "Quiet", "COMING SOON"
        else
            tone, text = "Primary", ROBUX .. " " .. tostring(prices[pass.GamePassId] or pass.Price)
        end
        button.Active = onSale and not owned
        button:SetAttribute("Tone", tone)
        button.Text = text
    end
end

-- each pass's live price, once (a price changed on Roblox shows here without a new release)
local function fetchPrices()
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

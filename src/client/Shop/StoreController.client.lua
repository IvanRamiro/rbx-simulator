-- The Store (the gift box in the HUD's top row; the owner, November 10, 2026): the game passes (GameConfig.GamePasses), each
-- with its picture, what it does, and its live Robux price, and the Exclusive Egg, locked until its beast is made. A pass not on
-- sale yet (no GamePassId) says "Coming soon"; one the player owns says so. Buying is Roblox's own prompt; the server counts
-- the purchase (server/Shop/GamePassService) and sets the "Pass_<Id>" attribute, and this window and every other follow it.
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
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

local toggleButton = Hud.topButton("StoreButton", UiTheme.Icons.Store, 2)
local window = Hud.window({
    Name = "StoreWindow", Title = "STORE", Size = Vector2.new(560, 470),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local message = Toast.new("StoreMessage", C.Highlight, 5)
local list = UiKit.scroll({ Name = "List", Size = UDim2.fromScale(1, 1), Parent = window.Body })

local prices = {} -- [GamePassId] = its live price in Robux, once Roblox has said
local cards = {}

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
        Position = UDim2.new(0, 10, 1, -10), Size = UDim2.new(1, -20, 0, 34), Parent = card,
    })
    button.Activated:Connect(function()
        if button.Active and (pass.GamePassId or 0) > 0 and not PassRules.owns(player, pass.Id) then
            Sfx.play("Click")
            MarketplaceService:PromptGamePassPurchase(player, pass.GamePassId)
        end
    end)
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

local function render()
    for _, entry in cards do
        local pass, button = entry.pass, entry.button
        local onSale = (pass.GamePassId or 0) > 0
        local owned = PassRules.owns(player, pass.Id)
        local tone, text
        if owned then
            tone, text = "Active", "OWNED"
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
            message:show(pass.Name .. " is yours. Thank you for supporting the game!", C.Highlight)
        end
    end)
end
render()

toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        fetchPrices()
        render()
        window.open()
    end
end)

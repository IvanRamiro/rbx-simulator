-- The Spirit Stones counter, and the shop window the Blacksmith's anvil and Buy & Sell's Jade Scale
-- open (ShopService sends ShopEvent "Open"). The Blacksmith has two tabs: Weapons lists a sword and
-- a spear for every realm (buy those of your realm or below, equip any you own); Forge gives an
-- owned weapon an unlocked element and a name (GameConfig.Forge). Buy & Sell lists your pets and
-- weapons with what each fetches. Every request goes to the server, which answers with the
-- result and fresh contents; the window closes when the player walks away.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local applyHudScale = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudScale"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "ShopHud"
local PANEL_COLOR = Color3.fromRGB(20, 20, 30)
local ROW_COLOR = Color3.fromRGB(40, 40, 55)
local CARD_COLOR = Color3.fromRGB(52, 48, 58)
local STONE_COLOR = Color3.fromRGB(110, 230, 200)
local FORGE_COLOR = Color3.fromRGB(220, 140, 60)
local BUY_COLOR = Color3.fromRGB(70, 160, 110)
local SELL_COLOR = Color3.fromRGB(190, 120, 50)
local EQUIP_COLOR = Color3.fromRGB(70, 110, 180)
local DISABLED_COLOR = Color3.fromRGB(80, 80, 88)
local RARITY_COLOR = {
    Common = Color3.fromRGB(200, 200, 200), Uncommon = Color3.fromRGB(120, 220, 120), Rare = Color3.fromRGB(90, 160, 255),
    Epic = Color3.fromRGB(190, 110, 255), Legendary = Color3.fromRGB(255, 190, 60), Mythical = Color3.fromRGB(255, 90, 120),
    Secret = Color3.fromRGB(240, 240, 255),
}
local WALK_AWAY = 60 -- studs from where the window was opened

local old = playerGui:FindFirstChild(HUD_NAME)
if old then
    old:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false
hud.DisplayOrder = 10 -- over the other HUD panels

local function corner(parent, radius)
    local c = Instance.new("UICorner")
    c.CornerRadius = UDim.new(0, radius)
    c.Parent = parent
end

local function label(parent, text, size, position, color, alignment)
    local l = Instance.new("TextLabel")
    l.Size = size
    l.Position = position
    l.BackgroundTransparency = 1
    l.Font = Enum.Font.GothamBold
    l.TextScaled = true
    l.TextColor3 = color or Color3.new(1, 1, 1)
    l.TextXAlignment = alignment or Enum.TextXAlignment.Left
    l.Text = text
    l.Parent = parent
    return l
end

local function button(parent, text, size, position, color, onClick)
    local b = Instance.new("TextButton")
    b.Size = size
    b.Position = position
    b.BackgroundColor3 = if onClick then color else DISABLED_COLOR
    b.AutoButtonColor = onClick ~= nil
    b.Font = Enum.Font.GothamBold
    b.TextScaled = true
    b.TextColor3 = Color3.new(1, 1, 1)
    b.Text = text
    b.Parent = parent
    corner(b, 6)
    local padding = Instance.new("UIPadding")
    padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 6), UDim.new(0, 6)
    padding.PaddingTop, padding.PaddingBottom = UDim.new(0, 3), UDim.new(0, 3)
    padding.Parent = b
    if onClick then
        b.Activated:Connect(onClick)
    end
    return b
end

-- ---------- the Spirit Stones counter ----------
local counter = label(hud, "", UDim2.fromOffset(150, 30), UDim2.fromOffset(174, 64), STONE_COLOR, Enum.TextXAlignment.Center)
counter.Name = "StoneCounter"
counter.BackgroundColor3 = PANEL_COLOR
counter.BackgroundTransparency = 0.25
corner(counter, 8)
local counterPadding = Instance.new("UIPadding")
counterPadding.PaddingTop, counterPadding.PaddingBottom = UDim.new(0, 4), UDim.new(0, 4)
counterPadding.Parent = counter
applyHudScale(counter)

local function updateCounter()
    local stones = player:GetAttribute("SpiritStones")
    counter.Visible = stones ~= nil
    counter.Text = "Stones " .. NumberFormat.compact(stones or 0)
end
player:GetAttributeChangedSignal("SpiritStones"):Connect(updateCounter)
updateCounter()

-- ---------- the window ----------
local window = Instance.new("Frame")
window.Name = "ShopWindow"
window.AnchorPoint = Vector2.new(0.5, 0.5)
window.Position = UDim2.fromScale(0.5, 0.5)
window.Size = UDim2.fromOffset(560, 420)
window.BackgroundColor3 = PANEL_COLOR
window.BackgroundTransparency = 0.08
window.Visible = false
window.Parent = hud
corner(window, 12)
applyHudScale(window)

local title = label(window, "", UDim2.new(1, -150, 0, 30), UDim2.fromOffset(16, 10), FORGE_COLOR)
local LIST_TOP, TABS_TOP, FORGE_TOP, FORGE_HEIGHT = 50, 46, 78, 100
local balance = label(window, "", UDim2.fromOffset(110, 22), UDim2.new(1, -170, 0, 14), STONE_COLOR, Enum.TextXAlignment.Right)

local list = Instance.new("ScrollingFrame")
list.Position = UDim2.fromOffset(12, 50) -- render() moves it below the Blacksmith's tabs
list.Size = UDim2.new(1, -24, 1, -62)
list.BackgroundTransparency = 1
list.BorderSizePixel = 0
list.ScrollBarThickness = 6
list.CanvasSize = UDim2.new()
list.AutomaticCanvasSize = Enum.AutomaticSize.Y
list.Parent = window
local layout = Instance.new("UIListLayout")
layout.Padding = UDim.new(0, 6)
layout.SortOrder = Enum.SortOrder.LayoutOrder
layout.Parent = list

local message = Toast.new(hud, "ShopMessage", 120, Color3.new(1, 1, 1), 3)
hud.Parent = playerGui

local current = { shop = nil, contents = nil, openedAt = nil, tab = "Weapons", element = nil }
local render

local function close()
    window.Visible = false
    current.shop = nil
end
button(window, "X", UDim2.fromOffset(32, 32), UDim2.new(1, -44, 0, 10), Color3.fromRGB(150, 60, 60), close)

local function ask(action, id, extra)
    RemoteEvents.ShopEvent:FireServer(action, id, extra)
end

-- ---------- the Blacksmith's tabs and the forge's controls (kept out of the list, so typing survives a redraw) ----------
local tabs = Instance.new("Frame")
tabs.Position = UDim2.fromOffset(12, TABS_TOP)
tabs.Size = UDim2.new(1, -24, 0, 26)
tabs.BackgroundTransparency = 1
tabs.Visible = false
tabs.Parent = window
local tabButtons = {}
for index, name in { "Weapons", "Forge" } do
    tabButtons[name] = button(tabs, name, UDim2.fromOffset(120, 26), UDim2.fromOffset((index - 1) * 128, 0), EQUIP_COLOR, function()
        current.tab = name
        render()
    end)
end

local forgePanel = Instance.new("Frame")
forgePanel.Position = UDim2.fromOffset(12, FORGE_TOP)
forgePanel.Size = UDim2.new(1, -24, 0, FORGE_HEIGHT)
forgePanel.BackgroundTransparency = 1
forgePanel.Visible = false
forgePanel.Parent = window
local chips = Instance.new("Frame")
chips.Size = UDim2.new(1, 0, 0, 34)
chips.BackgroundTransparency = 1
chips.Parent = forgePanel
local nameBox = Instance.new("TextBox")
nameBox.Position = UDim2.fromOffset(0, 42)
nameBox.Size = UDim2.new(0.6, 0, 0, 28)
nameBox.BackgroundColor3 = CARD_COLOR
nameBox.ClearTextOnFocus = false
nameBox.Font = Enum.Font.GothamBold
nameBox.TextScaled = true
nameBox.TextColor3 = Color3.new(1, 1, 1)
nameBox.PlaceholderColor3 = Color3.fromRGB(150, 150, 160)
nameBox.PlaceholderText = ("Name your weapon (%d to %d letters)"):format(GameConfig.Forge.NameLength.Min, GameConfig.Forge.NameLength.Max)
nameBox.Text = ""
nameBox.Parent = forgePanel
corner(nameBox, 6)
local namePadding = Instance.new("UIPadding")
namePadding.PaddingLeft, namePadding.PaddingRight = UDim.new(0, 8), UDim.new(0, 8)
namePadding.PaddingTop, namePadding.PaddingBottom = UDim.new(0, 4), UDim.new(0, 4)
namePadding.Parent = nameBox
nameBox:GetPropertyChangedSignal("Text"):Connect(function()
    local max = GameConfig.Forge.NameLength.Max
    if (utf8.len(nameBox.Text) or 0) > max then
        nameBox.Text = string.sub(nameBox.Text, 1, utf8.offset(nameBox.Text, max + 1) - 1)
    end
end)
local forgeHint = label(forgePanel, "", UDim2.new(1, 0, 0, 16), UDim2.fromOffset(0, 78), Color3.fromRGB(190, 190, 200))

local function row(order, height)
    local r = Instance.new("Frame")
    r.LayoutOrder = order
    r.Size = UDim2.new(1, -8, 0, height)
    r.BackgroundColor3 = ROW_COLOR
    r.Parent = list
    corner(r, 8)
    return r
end

local function heading(order, text)
    local h = label(list, text, UDim2.new(1, -8, 0, 24), UDim2.new(), FORGE_COLOR)
    h.LayoutOrder = order
    return h
end

-- the weapon's owned instance (the equipped one first), or nil
local function owned(contents, weaponId)
    local found
    for _, weapon in contents.Weapons.Weapons do
        if weapon.WeaponId == weaponId then
            if weapon.InstanceId == contents.Weapons.Equipped then
                return weapon
            end
            found = found or weapon
        end
    end
    return found
end

-- one weapon's card in a realm's row: name, damage, and buy / equip / equipped / locked
local function weaponCard(parent, x, weapon, contents, realmIndex)
    local card = Instance.new("Frame")
    card.Position = UDim2.new(x, 4, 0, 26)
    card.Size = UDim2.new(0.5, -8, 1, -30)
    card.BackgroundColor3 = CARD_COLOR
    card.Parent = parent
    corner(card, 6)
    local mine = owned(contents, weapon.Id)
    local element = mine and Shop.element(mine.Element)
    label(card, if mine and mine.Name then mine.Name else weapon.Name, UDim2.new(1, -10, 0, 18), UDim2.fromOffset(6, 4),
        element and element.Color)
    local kind = GameConfig.WeaponKinds[weapon.Kind]
    label(card, string.format("%s  ·  %d damage  ·  %d reach", weapon.Kind, math.floor(weapon.Damage + 0.5), kind.Range),
        UDim2.new(1, -10, 0, 14), UDim2.fromOffset(6, 24), Color3.fromRGB(190, 190, 200))
    local size, position = UDim2.new(1, -12, 0, 24), UDim2.new(0, 6, 1, -30)
    if mine and mine.InstanceId == contents.Weapons.Equipped then
        button(card, "Wielding", size, position, EQUIP_COLOR, nil)
    elseif mine then
        button(card, "Wield", size, position, EQUIP_COLOR, function()
            ask("Equip", mine.InstanceId)
        end)
    elseif weapon.Tier > realmIndex then
        button(card, "Needs " .. weapon.Realm, size, position, DISABLED_COLOR, nil)
    elseif contents.Stones < weapon.Price then
        button(card, NumberFormat.compact(weapon.Price) .. " Stones", size, position, DISABLED_COLOR, nil)
    else
        button(card, "Buy · " .. NumberFormat.compact(weapon.Price) .. " Stones", size, position, BUY_COLOR, function()
            ask("Buy", weapon.Id)
        end)
    end
end

local function renderForge(contents)
    local unlocked = {}
    for _, element in contents.Elements or {} do
        unlocked[element] = true
    end
    if current.element and not unlocked[current.element] then
        current.element = nil
    end
    for _, child in chips:GetChildren() do
        child:Destroy()
    end
    local order = GameConfig.Forge.Order
    for index, name in order do
        local info = GameConfig.Forge.Elements[name]
        local chip = button(chips, info.DisplayName, UDim2.new(1 / #order, -6, 1, 0), UDim2.new((index - 1) / #order, 0, 0, 0),
            if unlocked[name] then info.Color else DISABLED_COLOR, function()
                if unlocked[name] then
                    current.element = name
                    render()
                else
                    message:show("Find " .. info.Source .. " to forge with " .. info.DisplayName .. ".", Color3.new(1, 1, 1))
                end
            end)
        if current.element == name then
            local stroke = Instance.new("UIStroke")
            stroke.Thickness = 2
            stroke.Color = Color3.new(1, 1, 1)
            stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
            stroke.Parent = chip
        end
    end
    local chosen = current.element and GameConfig.Forge.Elements[current.element]
    forgeHint.Text = if chosen
        then chosen.DisplayName .. ": its glow, trail and strike, and " .. math.floor(GameConfig.Forge.DamageBonus * 100 + 0.5) .. "% more damage."
        elseif next(unlocked) then "Choose an element, name your weapon, then forge it."
        else "Attune relics, or secure a guardian's egg, to unlock elements."

    for index, weapon in contents.Weapons.Weapons do
        local info = Shop.weapon(weapon.WeaponId)
        if info then
            local element = Shop.element(weapon.Element)
            local r = row(index, 44)
            label(r, weapon.Name or info.Name, UDim2.new(0.55, 0, 0, 20), UDim2.fromOffset(10, 4), element and element.Color)
            label(r, info.Name .. (if element then "  ·  " .. element.DisplayName else "  ·  unforged"), UDim2.new(0.55, 0, 0, 14),
                UDim2.fromOffset(10, 25), Color3.fromRGB(190, 190, 200))
            local price = Shop.forgePrice(info.Id)
            local size, position = UDim2.new(0.38, 0, 0, 30), UDim2.new(0.62, -6, 0, 7)
            if not chosen then
                button(r, "Choose an element", size, position, DISABLED_COLOR, nil)
            elseif contents.Stones < price then
                button(r, NumberFormat.compact(price) .. " Stones", size, position, DISABLED_COLOR, nil)
            else
                button(r, (if element then "Re-forge · " else "Forge · ") .. NumberFormat.compact(price) .. " Stones", size, position, FORGE_COLOR,
                    function()
                        ask("Forge", weapon.InstanceId, { Element = current.element, Name = nameBox.Text })
                    end)
            end
        end
    end
end

local function renderBlacksmith(contents)
    title.Text = "Blacksmith"
    for name, b in tabButtons do
        b.BackgroundColor3 = if current.tab == name then FORGE_COLOR else EQUIP_COLOR
    end
    if current.tab == "Forge" then
        renderForge(contents)
        return
    end
    local realmIndex = Shop.playerRealmIndex(player)
    local unarmed = contents.Weapons.Equipped == nil
    local palm = row(0, 36)
    label(palm, "Qi Palm: fight bare-handed", UDim2.new(0.6, 0, 0, 20), UDim2.fromOffset(10, 8))
    button(palm, if unarmed then "Using" else "Use", UDim2.fromOffset(110, 26), UDim2.new(1, -118, 0, 5), EQUIP_COLOR,
        if unarmed then nil else function()
            ask("Equip", nil)
        end)
    for tier, info in GameConfig.WeaponTiers do
        local r = row(tier, 112)
        label(r, info.Realm, UDim2.new(1, -16, 0, 20), UDim2.fromOffset(10, 4),
            if tier <= realmIndex then FORGE_COLOR else Color3.fromRGB(140, 140, 150))
        weaponCard(r, 0, Shop.weapon("Sword" .. tier), contents, realmIndex)
        weaponCard(r, 0.5, Shop.weapon("Spear" .. tier), contents, realmIndex)
    end
end

-- A sale can't be undone, so its button asks once more: "Sure?" for CONFIRM_SECONDS.
local CONFIRM_SECONDS = 3
local function sellRow(order, name, detail, detailColor, value, onSell, why)
    local r = row(order, 40)
    label(r, name, UDim2.new(0.42, 0, 0, 20), UDim2.fromOffset(10, 4))
    label(r, detail, UDim2.new(0.42, 0, 0, 14), UDim2.fromOffset(10, 23), detailColor)
    label(r, NumberFormat.compact(value) .. " Stones", UDim2.new(0.22, 0, 0, 20), UDim2.new(0.44, 0, 0, 10), STONE_COLOR, Enum.TextXAlignment.Right)
    local sell
    local armedUntil = 0
    sell = button(r, if onSell then "Sell" else why, UDim2.new(0.28, 0, 0, 28), UDim2.new(0.7, -6, 0, 6), SELL_COLOR, onSell and function()
        if os.clock() < armedUntil then
            onSell()
            return
        end
        armedUntil = os.clock() + CONFIRM_SECONDS
        sell.Text = "Sure?"
        task.delay(CONFIRM_SECONDS, function()
            if sell.Parent and os.clock() >= armedUntil then
                sell.Text = "Sell"
            end
        end)
    end)
end

local function renderBuySell(contents)
    title.Text = "Buy & Sell"
    local order = 0
    local function nextOrder()
        order += 1
        return order
    end
    heading(nextOrder(), "Pets")
    if #contents.Pets == 0 then
        heading(nextOrder(), "  No pets to sell.")
    end
    for _, pet in contents.Pets do
        local info = GameConfig.Pets[pet.PetId]
        if info then
            sellRow(nextOrder(), info.DisplayName .. (if pet.Equipped then " (following you)" else ""), info.Rarity,
                RARITY_COLOR[info.Rarity], Shop.petValue(pet.PetId), function()
                    ask("SellPet", pet.InstanceId)
                end)
        end
    end
    heading(nextOrder(), "Weapons")
    for _, weapon in contents.Weapons.Weapons do
        local info = Shop.weapon(weapon.WeaponId)
        if info then
            local wielded = weapon.InstanceId == contents.Weapons.Equipped
            local element = Shop.element(weapon.Element)
            sellRow(nextOrder(), weapon.Name or info.Name, info.Realm .. (if element then "  ·  " .. element.DisplayName else ""),
                if element then element.Color else Color3.fromRGB(190, 190, 200), Shop.weaponRefund(info.Id, weapon.Element),
                if wielded then nil else function()
                    ask("SellWeapon", weapon.InstanceId)
                end, "Wielding")
        end
    end
end

function render()
    for _, child in list:GetChildren() do
        if not child:IsA("UIListLayout") then
            child:Destroy()
        end
    end
    local contents = current.contents
    balance.Text = NumberFormat.compact(contents.Stones) .. " Stones"
    local blacksmith = current.shop == "Blacksmith"
    local forging = blacksmith and current.tab == "Forge"
    tabs.Visible = blacksmith
    forgePanel.Visible = forging
    local top = if forging then FORGE_TOP + FORGE_HEIGHT + 4 elseif blacksmith then TABS_TOP + 32 else LIST_TOP
    list.Position = UDim2.fromOffset(12, top)
    list.Size = UDim2.new(1, -24, 1, -top - 12)
    if blacksmith then
        renderBlacksmith(contents)
    else
        renderBuySell(contents)
    end
end

RemoteEvents.ShopEvent.OnClientEvent:Connect(function(kind, ...)
    if kind == "Open" then
        local shop, contents = ...
        local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        if shop ~= current.shop then
            current.tab = "Weapons"
        end
        current.shop, current.contents = shop, contents
        current.openedAt = root and root.Position
        if not window.Visible then
            Sfx.play("Open")
        end
        window.Visible = true
        render()
    elseif kind == "Result" then
        local ok, text, contents = ...
        Sfx.play(if ok then "Purchase" else "Error")
        message:show(text, if ok then STONE_COLOR else Color3.fromRGB(255, 150, 140))
        if contents then
            current.contents = contents
            if current.shop then
                render()
            end
        end
    end
end)

-- walking away closes the window
RunService.Heartbeat:Connect(function()
    if not current.shop then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root or not current.openedAt or (root.Position - current.openedAt).Magnitude > WALK_AWAY then
        close()
    end
end)

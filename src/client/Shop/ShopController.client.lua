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
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Toast = require(UI:WaitForChild("Toast"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local WALK_AWAY = 60 -- studs from where the window was opened

-- ---------- the Spirit Stones counter ----------
local stoneChip, counter = Hud.chip("StoneCounter", UiTheme.Icons.Stones, 1)

local function updateCounter()
    local stones = player:GetAttribute("SpiritStones")
    stoneChip.Visible = stones ~= nil
    counter.Text = NumberFormat.compact(stones or 0) .. " Spirit Stones"
end
player:GetAttributeChangedSignal("SpiritStones"):Connect(updateCounter)
updateCounter()

-- ---------- the window ----------
local current = { shop = nil, contents = nil, openedAt = nil, tab = "Weapons", element = nil }
local render

local window = Hud.window({
    -- centred, and short enough to clear the dock below (and fit a phone: HudScale shrinks it)
    Name = "ShopWindow", Title = "SHOP", Size = Vector2.new(580, 420), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5), OnClose = function()
        current.shop = nil
    end,
})
local body = window.Body

-- the player's stones, at the top right of the body
local balance = UiKit.label({
    Name = "Balance", Font = "Strong", TextSize = 13, TextColor3 = C.AccentBright, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, 4), Size = UDim2.fromOffset(200, 18), TextXAlignment = Enum.TextXAlignment.Right, Parent = body,
})
local TABS_HEIGHT, FORGE_HEIGHT = 32, 106

local list = UiKit.scroll({ Name = "List", Parent = body }) -- render() places it under what the shop shows above it

local message = Toast.new(nil, "ShopMessage", nil, Color3.new(1, 1, 1), 3)

local function ask(action, id, extra)
    RemoteEvents.ShopEvent:FireServer(action, id, extra)
end

-- a button; disabled (onClick nil) it still says why
local function button(parent, text, tone, size, position, onClick)
    local b = UiKit.button({
        Font = "Strong", TextSize = 12, Text = text, Tone = tone, Active = onClick ~= nil, Size = size, Position = position,
        Parent = parent,
    })
    if onClick then
        b.Activated:Connect(onClick)
    end
    return b
end

-- ---------- the Blacksmith's tabs and the forge's controls (kept out of the list, so typing survives a redraw) ----------
local tabs = Instance.new("Frame")
tabs.Name = "Tabs"
tabs.BackgroundTransparency = 1
tabs.Size = UDim2.new(1, -210, 0, 26)
tabs.Visible = false
tabs.Parent = body
UiKit.list(tabs, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6) })
local tabButtons = {}
for index, name in { "Weapons", "Forge" } do
    local tab = UiKit.button({
        Name = name, Font = "Strong", TextSize = 12, Text = string.upper(name), Tone = "Quiet", LayoutOrder = index,
        Size = UDim2.fromOffset(110, 26), Parent = tabs,
    })
    tab.Activated:Connect(function()
        current.tab = name
        render()
    end)
    tabButtons[name] = tab
end

local forgePanel = Instance.new("Frame")
forgePanel.Name = "Forge"
forgePanel.BackgroundTransparency = 1
forgePanel.Position = UDim2.fromOffset(0, TABS_HEIGHT)
forgePanel.Size = UDim2.new(1, 0, 0, FORGE_HEIGHT)
forgePanel.Visible = false
forgePanel.Parent = body
local elementRow = Instance.new("Frame")
elementRow.Name = "Elements"
elementRow.BackgroundTransparency = 1
elementRow.Size = UDim2.new(1, 0, 0, 30)
elementRow.Parent = forgePanel
local nameBox = UiKit.textbox({
    Name = "WeaponName", Position = UDim2.fromOffset(0, 40), Size = UDim2.new(0.6, 0, 0, 30), Text = "",
    PlaceholderText = ("Name your weapon (%d to %d letters)"):format(GameConfig.Forge.NameLength.Min, GameConfig.Forge.NameLength.Max),
    Parent = forgePanel,
})
nameBox:GetPropertyChangedSignal("Text"):Connect(function()
    local max = GameConfig.Forge.NameLength.Max
    if (utf8.len(nameBox.Text) or 0) > max then
        nameBox.Text = string.sub(nameBox.Text, 1, utf8.offset(nameBox.Text, max + 1) - 1)
    end
end)
local forgeHint = UiKit.label({
    Name = "Hint", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true, Position = UDim2.fromOffset(0, 76),
    Size = UDim2.new(1, 0, 0, 28), Parent = forgePanel,
})

local function card(order, height, stripe)
    return UiKit.card({ LayoutOrder = order, Size = UDim2.new(1, 0, 0, height), Stripe = stripe, Parent = list })
end

local function heading(order, text)
    local _, word = UiKit.header(list, string.upper(text), { TextSize = 11, Color = C.Muted, LayoutOrder = order })
    return word
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
    local mine = owned(contents, weapon.Id)
    local element = mine and Shop.element(mine.Element)
    local box = UiKit.card({
        Position = UDim2.new(x, if x == 0 then 0 else 4, 0, 24), Size = UDim2.new(0.5, -4, 1, -30),
        Stripe = element and element.Color, Parent = parent,
    })
    -- the weapon itself, so the player sees the design before buying
    local picture = Portraits.weapon(weapon.Id, element and element.Color, 70)
    picture.Position = UDim2.fromOffset(8, 7)
    picture.Parent = box
    UiKit.label({
        Font = "Title", TextSize = 14, Text = if mine and mine.Name then mine.Name else weapon.Name,
        TextColor3 = if element then element.Color else C.Text, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(86, 6), Size = UDim2.new(1, -94, 0, 18), Parent = box,
    })
    local kind = GameConfig.WeaponKinds[weapon.Kind]
    UiKit.label({
        TextSize = 11, TextColor3 = C.Muted, Text = string.format("%s  ·  %d dmg  ·  %d reach", weapon.Kind, math.floor(weapon.Damage + 0.5), kind.Range),
        Position = UDim2.fromOffset(86, 25), Size = UDim2.new(1, -94, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = box,
    })
    local size, position = UDim2.new(1, -94, 0, 26), UDim2.new(0, 86, 1, -33)
    if mine and mine.InstanceId == contents.Weapons.Equipped then
        button(box, "WIELDING", "Highlight", size, position, nil)
    elseif mine then
        button(box, "WIELD", "Accent", size, position, function()
            ask("Equip", mine.InstanceId)
        end)
    elseif weapon.Tier > realmIndex then
        button(box, "NEEDS " .. string.upper(weapon.Realm), "Quiet", size, position, nil)
    elseif contents.Stones < weapon.Price then
        button(box, NumberFormat.compact(weapon.Price) .. " STONES", "Quiet", size, position, nil)
    else
        button(box, "BUY  ·  " .. NumberFormat.compact(weapon.Price) .. " STONES", "Accent", size, position, function()
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
    for _, child in elementRow:GetChildren() do
        child:Destroy()
    end
    local order = GameConfig.Forge.Order
    for index, name in order do
        local info = GameConfig.Forge.Elements[name]
        local chosen = current.element == name
        local chip = UiKit.button({
            Font = "Strong", TextSize = 12, Text = string.upper(info.DisplayName), Tone = if chosen then "Highlight" else "Quiet",
            Position = UDim2.new((index - 1) / #order, 0, 0, 0), Size = UDim2.new(1 / #order, -6, 1, 0), Parent = elementRow,
        })
        -- each element in its own colour; a locked one dim
        chip.TextColor3 = if unlocked[name] then info.Color:Lerp(Color3.new(1, 1, 1), 0.35) else C.Muted
        chip.Activated:Connect(function()
            if unlocked[name] then
                current.element = name
                render()
            else
                message:show("Find " .. info.Source .. " to forge with " .. info.DisplayName .. ".", Color3.new(1, 1, 1))
            end
        end)
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
            local r = card(index, 56, element and element.Color)
            local picture = Portraits.weapon(info.Id, element and element.Color, 44)
            picture.Position = UDim2.fromOffset(10, 6)
            picture.Parent = r
            UiKit.label({
                Font = "Title", TextSize = 14, Text = weapon.Name or info.Name, TextColor3 = if element then element.Color else C.Text,
                TextTruncate = Enum.TextTruncate.AtEnd, Position = UDim2.fromOffset(62, 9), Size = UDim2.new(0.58, -62, 0, 18), Parent = r,
            })
            UiKit.label({
                TextSize = 11, TextColor3 = C.Muted, Text = info.Name .. (if element then "  ·  " .. element.DisplayName else "  ·  unforged"),
                Position = UDim2.fromOffset(62, 29), Size = UDim2.new(0.58, -62, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = r,
            })
            local price = Shop.forgePrice(info.Id)
            local size, position = UDim2.new(0.4, -8, 0, 30), UDim2.new(0.6, 0, 0, 13)
            if not chosen then
                button(r, "CHOOSE AN ELEMENT", "Quiet", size, position, nil)
            elseif contents.Stones < price then
                button(r, NumberFormat.compact(price) .. " STONES", "Quiet", size, position, nil)
            else
                button(r, (if element then "RE-FORGE  ·  " else "FORGE  ·  ") .. NumberFormat.compact(price), "Highlight", size, position,
                    function()
                        ask("Forge", weapon.InstanceId, { Element = current.element, Name = nameBox.Text })
                    end)
            end
        end
    end
end

local function renderBlacksmith(contents)
    window.setTitle("BLACKSMITH")
    for name, tab in tabButtons do
        tab:SetAttribute("Tone", if current.tab == name then "Accent" else "Quiet")
    end
    if current.tab == "Forge" then
        renderForge(contents)
        return
    end
    local realmIndex = Shop.playerRealmIndex(player)
    local unarmed = contents.Weapons.Equipped == nil
    local palm = card(0, 42)
    UiKit.label({
        Font = "Title", TextSize = 14, Text = "Qi Palm", Position = UDim2.fromOffset(12, 5), Size = UDim2.new(0.6, 0, 0, 18), Parent = palm,
    })
    UiKit.label({
        TextSize = 11, TextColor3 = C.Muted, Text = "Fight bare-handed", Position = UDim2.fromOffset(12, 22), Size = UDim2.new(0.6, 0, 0, 14), Parent = palm,
    })
    button(palm, if unarmed then "USING" else "USE", if unarmed then "Highlight" else "Accent", UDim2.fromOffset(110, 26),
        UDim2.new(1, -120, 0, 8), if unarmed then nil else function()
            ask("Equip", nil)
        end)
    for tier, info in GameConfig.WeaponTiers do
        local r = card(tier, 120)
        UiKit.label({
            Font = "Strong", TextSize = 12, Text = string.upper(info.Realm), TextColor3 = if tier <= realmIndex then C.Highlight else C.Muted,
            Position = UDim2.fromOffset(10, 5), Size = UDim2.new(1, -20, 0, 16), Parent = r,
        })
        local inner = Instance.new("Frame")
        inner.BackgroundTransparency = 1
        inner.Position = UDim2.fromOffset(8, 0)
        inner.Size = UDim2.new(1, -16, 1, 0)
        inner.Parent = r
        weaponCard(inner, 0, Shop.weapon("Sword" .. tier), contents, realmIndex)
        weaponCard(inner, 0.5, Shop.weapon("Spear" .. tier), contents, realmIndex)
    end
end

-- A sale can't be undone, so its button asks once more: "SURE?" for CONFIRM_SECONDS.
local CONFIRM_SECONDS = 3
local function sellRow(order, picture, name, detail, detailColor, value, onSell, why)
    local r = card(order, 56, detailColor)
    picture.Position = UDim2.fromOffset(10, 6)
    picture.Parent = r
    UiKit.label({
        Font = "Title", TextSize = 14, Text = name, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(62, 9), Size = UDim2.new(0.44, -62, 0, 18), Parent = r,
    })
    UiKit.label({
        Font = "Strong", TextSize = 11, Text = detail, TextColor3 = detailColor, Position = UDim2.fromOffset(62, 29),
        Size = UDim2.new(0.44, -62, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = r,
    })
    UiKit.label({
        Font = "Strong", TextSize = 13, Text = NumberFormat.compact(value) .. " Stones", TextColor3 = C.AccentBright,
        Position = UDim2.new(0.44, 0, 0, 19), Size = UDim2.new(0.24, 0, 0, 18), TextXAlignment = Enum.TextXAlignment.Right, Parent = r,
    })
    local sell
    local armedUntil = 0
    sell = button(r, if onSell then "SELL" else string.upper(why), if onSell then "Danger" else "Quiet", UDim2.new(0.28, -10, 0, 30),
        UDim2.new(0.72, 0, 0, 13), onSell and function()
            if os.clock() < armedUntil then
                onSell()
                return
            end
            armedUntil = os.clock() + CONFIRM_SECONDS
            sell.Text = "SURE?"
            task.delay(CONFIRM_SECONDS, function()
                if sell.Parent and os.clock() >= armedUntil then
                    sell.Text = "SELL"
                end
            end)
        end)
end

local function renderBuySell(contents)
    window.setTitle("BUY & SELL")
    local order = 0
    local function nextOrder()
        order += 1
        return order
    end
    heading(nextOrder(), "Pets")
    if #contents.Pets == 0 then
        UiKit.empty(list, "No pets to sell.").LayoutOrder = nextOrder()
    end
    for _, pet in contents.Pets do
        local info = GameConfig.Pets[pet.PetId]
        if info then
            sellRow(nextOrder(), Portraits.pet(pet.PetId, 44), info.DisplayName, info.Rarity .. (if pet.Equipped then "  ·  following you" else ""),
                GameConfig.PetRarityColors[info.Rarity] or C.Text, Shop.petValue(pet.PetId), function()
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
            sellRow(nextOrder(), Portraits.weapon(info.Id, element and element.Color, 44), weapon.Name or info.Name,
                info.Realm .. (if element then "  ·  " .. element.DisplayName else ""),
                if element then element.Color else C.Muted, Shop.weaponRefund(info.Id, weapon.Element),
                if wielded then nil else function()
                    ask("SellWeapon", weapon.InstanceId)
                end, "Wielding")
        end
    end
end

function render()
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
    local contents = current.contents
    balance.Text = NumberFormat.compact(contents.Stones) .. " Spirit Stones"
    local blacksmith = current.shop == "Blacksmith"
    local forging = blacksmith and current.tab == "Forge"
    tabs.Visible = blacksmith
    forgePanel.Visible = forging
    local top = if forging then TABS_HEIGHT + FORGE_HEIGHT + 4 elseif blacksmith then TABS_HEIGHT else 26
    list.Position = UDim2.fromOffset(0, top)
    list.Size = UDim2.new(1, 0, 1, -top)
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
        if not window.isOpen() then
            Sfx.play("Open")
        end
        window.open()
        current.shop, current.contents = shop, contents
        current.openedAt = root and root.Position
        render()
    elseif kind == "Result" then
        local ok, text, contents = ...
        Sfx.play(if ok then "Purchase" else "Error")
        message:show(text, if ok then C.AccentBright else Color3.fromRGB(255, 150, 140))
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
        window.close()
    end
end)

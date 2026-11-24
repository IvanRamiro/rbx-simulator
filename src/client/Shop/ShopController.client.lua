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

-- studs from where the window was opened. It opens within 12 of the shop's prompt, and the server sells only
-- within 45 of it (ShopService REACH): 12 + 30 keeps a margin, so the window closes before a purchase is refused
local WALK_AWAY = 30

-- ---------- the Spirit Stones counter ----------
local stoneChip, setStones = Hud.chip("StoneCounter", UiTheme.Icons.Stones, 1, { Caption = "Stones", Format = NumberFormat.compact, Color = Color3.fromRGB(120, 240, 255) })

local function updateCounter()
    local stones = player:GetAttribute("SpiritStones")
    stoneChip.Visible = stones ~= nil
    setStones(stones or 0)
end
player:GetAttributeChangedSignal("SpiritStones"):Connect(updateCounter)
updateCounter()

-- ---------- the window ----------
local current = { shop = nil, contents = nil, openedAt = nil, tab = "Weapons", element = nil }
local render

local window = Hud.window({
    -- centred, and short enough to clear the dock below (and fit a phone: HudScale shrinks it)
    Name = "ShopWindow", Title = "SHOP", Size = Vector2.new(620, 500), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5), OnClose = function()
        current.shop = nil
    end,
})
local body = window.Body

-- the player's stones, at the top right of the body: a pill with the stone's picture
local TAB = UiTheme.Height.Tab
local _, balance = UiKit.pill(UiTheme.Icons.Stones, "", {
    Name = "Balance", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0, TAB / 2), Parent = body,
})
local GAP = UiTheme.Space.M
-- a line at the top left, beside the balance, saying what this counter is for (not the Blacksmith's: its tabs are there)
local topNote = UiKit.label({
    Name = "Note", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, AnchorPoint = Vector2.new(0, 0.5),
    Position = UDim2.new(0, 2, 0, TAB / 2), Size = UDim2.new(1, -150, 0, 30), TextWrapped = true, Parent = body,
})
local TABS_HEIGHT, FORGE_HEIGHT = TAB + GAP, 40 + GAP + UiTheme.Height.Field + 6 + 30

local list = UiKit.scroll({ Name = "List", Parent = body }) -- render() places it under what the shop shows above it

local message = Toast.new("ShopMessage", Color3.new(1, 1, 1), 3)

local lastAsked = nil -- what the next Result answers: its sound (a purchase, a sale, a forging)
local function ask(action, id, extra)
    lastAsked = action
    RemoteEvents.ShopEvent:FireServer(action, id, extra)
end
local RESULT_SOUNDS = { Forge = "Forge", SellPet = "Sell", SellSpares = "Sell", SellWeapon = "Sell", Equip = "WeaponEquip" }

-- a button; disabled (onClick nil) it still says why
local function button(parent, text, tone, size, position, onClick)
    local b = UiKit.button({
        TextSize = 13, Text = text, Tone = tone, Active = onClick ~= nil, Size = size, Position = position,
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
tabs.Size = UDim2.new(1, -210, 0, TAB)
tabs.Visible = false
tabs.Parent = body
UiKit.list(tabs, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
local tabButtons = {}
for index, name in { "Weapons", "Forge" } do
    local tab = UiKit.tab({ Name = name, Text = string.upper(name), LayoutOrder = index, Size = UDim2.fromOffset(130, TAB), Parent = tabs })
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
elementRow.Size = UDim2.new(1, 0, 0, 40)
elementRow.Parent = forgePanel
UiKit.list(elementRow, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, UiTheme.Space.S) })
local nameBox = UiKit.textbox({
    Name = "WeaponName", Position = UDim2.fromOffset(0, 40 + GAP), Size = UDim2.new(1, 0, 0, UiTheme.Height.Field), Text = "",
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
    Name = "Hint", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true,
    Position = UDim2.fromOffset(0, 40 + GAP + UiTheme.Height.Field + 6), Size = UDim2.new(1, 0, 0, 30), Parent = forgePanel,
})

local priceTag -- (below)
local function card(order, height, stripe)
    return UiKit.card({ LayoutOrder = order, Size = UDim2.new(1, 0, 0, height), Stripe = stripe, Parent = list })
end

local function heading(order, text)
    local _, word = UiKit.header(list, text, { LayoutOrder = order })
    return word
end

-- one row's measures, shared by every list here
local ROW = 68
local ROW_BUTTON = UiTheme.Height.Button

-- a price, right-aligned in the column before a row's button: the stone's picture and the number, heavy
function priceTag(row, value, dim)
    local tag = Instance.new("Frame")
    tag.Name = "Price"
    tag.BackgroundTransparency = 1
    tag.AnchorPoint = Vector2.new(1, 0.5)
    tag.Position = UDim2.new(0.72, -UiTheme.Space.M, 0.5, 0)
    tag.Size = UDim2.new(0.26, 0, 0, 22)
    tag.Parent = row
    UiKit.list(tag, { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
        VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 4) })
    local stone = Instance.new("ImageLabel")
    stone.BackgroundTransparency = 1
    stone.Image = UiTheme.Icons.Stones
    stone.ImageTransparency = if dim then 0.5 else 0
    stone.Size = UDim2.fromOffset(18, 18)
    stone.Parent = tag
    UiKit.boldLabel({
        TextSize = 15, Text = NumberFormat.compact(value), TextColor3 = if dim then C.Muted else C.AccentBright,
        AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 20), LayoutOrder = 2, Parent = tag,
    })
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
    local box = UiKit.boldCard(UiKit.card({
        Position = UDim2.new(x, if x == 0 then 0 else UiTheme.Space.S / 2, 0, 30), Size = UDim2.new(0.5, -UiTheme.Space.S / 2, 1, -(30 + 8)),
        Parent = parent,
    }), element and element.Color)
    box.BackgroundColor3 = C.Panel
    -- the weapon itself, so the player sees the design before buying
    local picture = Portraits.weapon(weapon.Id, element and element.Color, 64)
    picture.Position = UDim2.fromOffset(10, 10)
    picture.Parent = box
    local name = UiKit.boldLabel({
        TextSize = 14, Text = if mine and mine.Name then mine.Name else weapon.Name,
        TextColor3 = if element then element.Color:Lerp(Color3.new(1, 1, 1), 0.2) else C.Text, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(84, 10), Size = UDim2.new(1, -94, 0, 18), Parent = box,
    })
    local _ = name
    local kind = GameConfig.WeaponKinds[weapon.Kind]
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.Muted,
        Text = string.format("%s  ·  %d dmg  ·  %d reach", weapon.Kind, math.floor(weapon.Damage + 0.5), kind.Range),
        Position = UDim2.fromOffset(84, 30), Size = UDim2.new(1, -94, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = box,
    })
    local size, position = UDim2.new(1, -94, 0, UiTheme.Height.ButtonSmall), UDim2.new(0, 84, 1, -(UiTheme.Height.ButtonSmall + 10))
    if mine and mine.InstanceId == contents.Weapons.Equipped then
        button(box, "EQUIPPED", "Active", size, position, nil) -- a state, not an action: not the gold of something to press
    elseif mine then
        button(box, "EQUIP", "Go", size, position, function()
            ask("Equip", mine.InstanceId)
        end)
    elseif weapon.Tier > realmIndex then
        button(box, "NEEDS THIS REALM", "Quiet", size, position, nil) -- (its realm heads the row; "NEEDS ETERNAL TRANSCENDENCE" didn't fit)
    elseif contents.Stones < weapon.Price then
        button(box, NumberFormat.compact(weapon.Price) .. " STONES", "Quiet", size, position, nil)
    else
        button(box, "BUY  " .. NumberFormat.compact(weapon.Price), "Buy", size, position, function()
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
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
    local order = GameConfig.Forge.Order
    for index, name in order do
        local info = GameConfig.Forge.Elements[name]
        local chosen = current.element == name
        local chip = UiKit.button({
            TextSize = 12, Text = string.upper(info.DisplayName), Tone = if chosen then "Highlight" else "Tile",
            LayoutOrder = index, Size = UDim2.new(1 / #order, -UiTheme.Space.S * (#order - 1) / #order, 1, 0), Parent = elementRow,
        })
        -- each element in its own colour (dark on the gold of the chosen one); a locked one dim
        chip.TextColor3 = if chosen then Color3.fromRGB(48, 28, 6) elseif unlocked[name] then info.Color:Lerp(Color3.new(1, 1, 1), 0.35) else C.Muted
        chip.Activated:Connect(function()
            if unlocked[name] then
                current.element = name
                render()
            else
                message:show("Find " .. info.Source .. " to forge with " .. info.DisplayName .. ".", "Info")
            end
        end)
    end
    local chosen = current.element and GameConfig.Forge.Elements[current.element]
    forgeHint.Text = if chosen
        then chosen.DisplayName .. ": a new glow, trail and hit effect, and " .. math.floor(GameConfig.Forge.DamageBonus * 100 + 0.5) .. "% more damage."
        elseif next(unlocked) then "Choose an element, name your weapon, then forge it."
        else "Collect relics, or bring a guardian's egg home, to unlock elements."

    for index, weapon in contents.Weapons.Weapons do
        local info = Shop.weapon(weapon.WeaponId)
        if info then
            local element = Shop.element(weapon.Element)
            local r = card(index, ROW, element and element.Color)
            local picture = Portraits.weapon(info.Id, element and element.Color, 48)
            picture.Position = UDim2.fromOffset(14, 8)
            picture.Parent = r
            UiKit.boldLabel({
                TextSize = 14, Text = weapon.Name or info.Name, TextColor3 = if element then element.Color:Lerp(Color3.new(1, 1, 1), 0.2) else C.Text,
                TextTruncate = Enum.TextTruncate.AtEnd, Position = UDim2.fromOffset(72, 12), Size = UDim2.new(0.58, -72, 0, 18), Parent = r,
            })
            UiKit.label({
                Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = info.Name .. (if element then "  ·  " .. element.DisplayName else "  ·  no element"),
                Position = UDim2.fromOffset(72, 33), Size = UDim2.new(0.58, -72, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = r,
            })
            local price = Shop.forgePrice(info.Id)
            local size, position = UDim2.new(0.4, -12, 0, ROW_BUTTON), UDim2.new(0.6, 0, 0.5, -ROW_BUTTON / 2)
            if not chosen then
                button(r, "CHOOSE AN ELEMENT", "Quiet", size, position, nil)
            elseif contents.Stones < price then
                button(r, NumberFormat.compact(price) .. " STONES", "Quiet", size, position, nil)
            else
                button(r, (if element then "RE-FORGE  " else "FORGE  ") .. NumberFormat.compact(price), "Buy", size, position,
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
        UiKit.selectTab(tab, current.tab == name)
    end
    if current.tab == "Forge" then
        renderForge(contents)
        return
    end
    local realmIndex = Shop.playerRealmIndex(player)
    local unarmed = contents.Weapons.Equipped == nil
    local palm = card(0, ROW)
    UiKit.boldLabel({
        TextSize = 14, Text = "Qi Palm", Position = UDim2.fromOffset(14, 12), Size = UDim2.new(0.6, 0, 0, 18), Parent = palm,
    })
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = "Fight with no weapon", Position = UDim2.fromOffset(14, 33),
        Size = UDim2.new(0.6, 0, 0, 14), Parent = palm,
    })
    button(palm, if unarmed then "USING" else "USE", if unarmed then "Active" else "Go", UDim2.fromOffset(120, ROW_BUTTON),
        UDim2.new(1, -132, 0.5, -ROW_BUTTON / 2), if unarmed then nil else function()
            ask("Equip", nil)
        end)
    for tier, info in GameConfig.WeaponTiers do
        local r = card(tier, 148)
        UiKit.header(r, info.Realm, {
            Color = if tier <= realmIndex then C.Highlight else C.Muted, Position = UDim2.fromOffset(12, 6), Size = UDim2.new(1, -24, 0, 22),
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
    local r = card(order, ROW, detailColor)
    picture.Position = UDim2.fromOffset(14, 8)
    picture.Parent = r
    UiKit.boldLabel({
        TextSize = 14, Text = name, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(72, 12), Size = UDim2.new(0.44, -72, 0, 18), Parent = r,
    })
    UiKit.label({
        Font = "Strong", TextSize = 11, Text = detail, TextColor3 = detailColor, Position = UDim2.fromOffset(72, 33),
        Size = UDim2.new(0.44, -72, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = r,
    })
    priceTag(r, value)
    local sell
    local armedUntil = 0
    sell = button(r, if onSell then "SELL" else string.upper(why), if onSell then "Danger" else "Quiet", UDim2.new(0.28, -12, 0, ROW_BUTTON),
        UDim2.new(0.72, 0, 0.5, -ROW_BUTTON / 2), onSell and function()
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

local function sellPet(pet, info)
    if info.Rarity ~= "Secret" and info.Rarity ~= "Divine" then
        ask("SellPet", pet.InstanceId)
        return
    end
    -- a Secret pet is the last thing anyone should lose to a quick tap: the server won't take one without this
    ConfirmDialog.show({
        Title = "SELL A " .. string.upper(info.Rarity) .. " PET", Picture = Portraits.pet(pet.PetId, 72), ConfirmText = "SELL FOREVER",
        Text = "This " .. info.DisplayName .. " is one of the rarest beasts in the world. Sell it for "
            .. NumberFormat.compact(Shop.petValue(pet.PetId, PetRules.worth(pet))) .. " Spirit Stones? It can't be undone.",
        OnConfirm = function()
            ask("SellPet", pet.InstanceId, { ConfirmSecret = true })
        end,
    })
end

local function renderBuySell(contents)
    window.setTitle("BUY & SELL")
    topNote.Text = "Sell your extra beasts and weapons for Spirit Stones."
    local order = 0
    local function nextOrder()
        order += 1
        return order
    end
    heading(nextOrder(), "Pets")
    if #contents.Pets == 0 then
        UiKit.empty(list, "No pets to sell.").LayoutOrder = nextOrder()
    end
    -- everything past the copy worth keeping, in one go (PetRules.spares: never a locked or equipped pet, nor anything Legendary or rarer)
    local spares = PetRules.spares(contents.Pets)
    if #spares > 0 then
        local total = 0
        for _, pet in spares do
            total += Shop.petValue(pet.PetId, PetRules.worth(pet))
        end
        sellRow(nextOrder(), UiKit.icon(UiTheme.Icons.Stones, 44), "Sell all spares", #spares .. (if #spares == 1 then " duplicate" else " duplicates"),
            C.AccentBright, total, function()
                ask("SellSpares")
            end)
    end
    for _, pet in contents.Pets do
        local info = GameConfig.Pets[pet.PetId]
        if info then
            local level = PetRules.level(pet)
            local mutation = PetRules.mutation(pet)
            local picture = Portraits.pet(pet.PetId, 44)
            MutationLook.portrait(picture, mutation)
            sellRow(nextOrder(), picture, PetRules.displayName(pet.PetId, mutation),
                info.Rarity .. (if PetRules.size(pet) ~= "Normal" then "  ·  " .. PetRules.size(pet) else "")
                    .. (if mutation then "  ·  " .. mutation else "") .. (if level > 1 then "  ·  Level " .. level else ""),
                GameConfig.PetRarityColors[info.Rarity] or C.Text, Shop.petValue(pet.PetId, PetRules.worth(pet)),
                if pet.Locked or pet.Equipped then nil else function()
                    sellPet(pet, info)
                end, if pet.Locked then "Locked" else "Equipped")
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
                end, "Equipped")
        end
    end
end

function render()
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") and child ~= forgePanel then
            child:Destroy()
        end
    end
    local contents = current.contents
    balance.Text = NumberFormat.compact(contents.Stones)
    local blacksmith = current.shop == "Blacksmith"
    local forging = blacksmith and current.tab == "Forge"
    tabs.Visible = blacksmith
    topNote.Visible = not blacksmith
    forgePanel.Visible = forging
    -- on a short window (a phone) the forge's controls scroll with its weapons, or the list under them had one row's room
    local short = body.AbsoluteSize.Y / Hud.windowScale() < 330
    forgePanel.Parent = if forging and short then list else body
    forgePanel.LayoutOrder = -100
    local top = if forging and not short then TABS_HEIGHT + FORGE_HEIGHT + GAP elseif blacksmith then TABS_HEIGHT else TAB / 2 + 15 + GAP
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
        window.open()
        current.shop, current.contents = shop, contents
        current.openedAt = root and root.Position
        render()
    elseif kind == "Result" then
        local ok, text, contents = ...
        Sfx.play(if ok then RESULT_SOUNDS[lastAsked] or "Purchase" else "Error")
        message:show(text, if ok then "Success" else "Error")
        if contents then
            current.contents = contents
            if current.shop then
                render()
            end
        end
    end
end)

-- Stones that arrive while the window is open (a quest reward, a relic) move its balance and what it can afford: it showed
-- the balance from when it opened (a new player's run, 2026-11-12: 250 in the window, 290 on the HUD after a quest paid out)
player:GetAttributeChangedSignal("SpiritStones"):Connect(function()
    local stones = player:GetAttribute("SpiritStones")
    if current.shop and current.contents and typeof(stones) == "number" and stones ~= current.contents.Stones then
        current.contents.Stones = stones
        render()
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

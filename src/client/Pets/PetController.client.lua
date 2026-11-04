-- The pets window (the Pets button on the HUD's rail) and the hatch results. Each pet is a card:
-- its portrait (the pet itself, in a ViewportFrame), name, rarity and Qi bonus, and its Equip and
-- Aura buttons. Equipped pets come first, then by rarity. The server owns the inventory
-- (PetInventoryUpdatedEvent sends it; Equip / Unequip / SetAura ask).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Toast = require(UI:WaitForChild("Toast"))
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Portraits = require(UI:WaitForChild("Portraits"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local HatchCeremony = require(script.Parent:WaitForChild("HatchCeremony"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local GRAND_REVEAL = { Legendary = true, Mythical = true, Secret = true } -- rarities revealed with the grander sound
local RARITY_ORDER = { Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }

local toggleButton, setPetBadge = Hud.railButton("PetsButton", UiTheme.Icons.Pets, "Pets", 1)

local window = Hud.window({
    Name = "PetsWindow", Title = "PETS", Size = Vector2.new(330, 400), AnchorPoint = Vector2.new(0, 0),
    Position = UDim2.fromOffset(UiTheme.Margin + 310 + 16, UiTheme.Margin), -- beside the left column (STATUS is 310 wide)
})
local body = window.Body

local equippedLabel = UiKit.label({
    Name = "Equipped", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Text = "",
    Size = UDim2.new(0.5, 0, 0, 16), Parent = body,
})
local bonusLabel = UiKit.label({
    Name = "Bonus", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Text = "", AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.fromScale(1, 0), Size = UDim2.new(0.5, 0, 0, 16), TextXAlignment = Enum.TextXAlignment.Right,
    Parent = body,
})
local petList = UiKit.scroll({ Name = "PetList", Position = UDim2.fromOffset(0, 24), Size = UDim2.new(1, 0, 1, -24), Parent = body })

local hatchMessage = Toast.new("HatchMessage", Color3.new(1, 1, 1), 3.5)

toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        Sfx.play("Open")
        window.open()
    end
end)

-- ---------- a pet's card ----------
local function createPetCard(pet, layoutOrder, equippedCount, auraPetInstanceId)
    local definition = GameConfig.Pets[pet.PetId]
    if not definition then
        return
    end
    local isAuraPet = pet.InstanceId == auraPetInstanceId
    local rarityColor = GameConfig.PetRarityColors[definition.Rarity] or C.Text

    local card = UiKit.card({ Name = "PetCard", LayoutOrder = layoutOrder, Size = UDim2.new(1, 0, 0, 76), Stripe = rarityColor, Parent = petList })
    local picture = Portraits.pet(pet.PetId, 58)
    picture.Position = UDim2.fromOffset(10, 9)
    picture.Parent = card
    UiKit.label({
        Name = "PetName", Font = "Title", TextSize = 15, Text = definition.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(78, 7), Size = UDim2.new(1, -86, 0, 18), Parent = card,
    })
    local tags = Instance.new("Frame")
    tags.Name = "Tags"
    tags.BackgroundTransparency = 1
    tags.Position = UDim2.fromOffset(78, 27)
    tags.Size = UDim2.new(1, -86, 0, 16)
    tags.Parent = card
    UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
    UiKit.tag(definition.Rarity, rarityColor).Parent = tags
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.AccentBright, Text = "+" .. definition.QiBonusPercent .. "% Qi",
        AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 16), LayoutOrder = 1, Parent = tags,
    })
    if isAuraPet then
        local aura = UiKit.tag("Aura", C.Highlight)
        aura.LayoutOrder = 2
        aura.Parent = tags
    end

    -- two buttons side by side, from the portrait's edge to the card's (78 px in, 8 px short, 4 apart)
    local function action(text, tone, x, onClick)
        local b = UiKit.button({
            Font = "Strong", TextSize = 11, Text = text, Tone = tone, Active = onClick ~= nil,
            Position = UDim2.new(x, if x == 0 then 78 else 37, 0, 49), Size = UDim2.new(0.5, -45, 0, 22),
            Parent = card,
        })
        if onClick then
            b.Activated:Connect(onClick)
        end
        return b
    end
    if pet.Equipped then
        action("UNEQUIP", "Quiet", 0, function()
            RemoteEvents.UnequipPetEvent:FireServer(pet.InstanceId)
        end)
    elseif equippedCount < GameConfig.MaxEquippedPets then
        action("EQUIP", "Accent", 0, function()
            RemoteEvents.EquipPetEvent:FireServer(pet.InstanceId)
        end)
    else
        action("SLOTS FULL", "Quiet", 0, nil)
    end
    if isAuraPet then
        action("AURA ON", "Highlight", 0.5, function()
            RemoteEvents.SetAuraPetEvent:FireServer(nil)
        end)
    else
        action("SET AURA", "Quiet", 0.5, if pet.Equipped then function()
            RemoteEvents.SetAuraPetEvent:FireServer(pet.InstanceId)
        end else nil)
    end
end

local function renderInventory(snapshot)
    for _, pet in if snapshot then snapshot.Pets else {} do
        PetPreload.soon(pet.PetId) -- ready before their portraits or their first walk
    end
    if not snapshot then
        return
    end
    for _, child in petList:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end

    local equippedCount = 0
    local bonusPercent = 0
    for _, pet in snapshot.Pets do
        local definition = GameConfig.Pets[pet.PetId]
        if pet.Equipped and definition then
            equippedCount += 1
            bonusPercent += definition.QiBonusPercent
        end
    end
    local equippedText = equippedCount .. "/" .. GameConfig.MaxEquippedPets
    setPetBadge(equippedText)
    equippedLabel.Text = "EQUIPPED  " .. equippedCount .. " / " .. GameConfig.MaxEquippedPets
    bonusLabel.Text = "QI BONUS  +" .. bonusPercent .. "%"

    if #snapshot.Pets == 0 then
        UiKit.empty(petList, "No pets yet.\nTake an egg from a guardian, carry it home, and hatch it at the Hatching Altar.")
        return
    end
    -- equipped first, then the rarest, then by name
    local pets = table.clone(snapshot.Pets)
    table.sort(pets, function(a, b)
        local da, db = GameConfig.Pets[a.PetId], GameConfig.Pets[b.PetId]
        if (a.Equipped == true) ~= (b.Equipped == true) then
            return a.Equipped == true
        end
        local ra, rb = da and RARITY_ORDER[da.Rarity] or 0, db and RARITY_ORDER[db.Rarity] or 0
        if ra ~= rb then
            return ra > rb
        end
        return (da and da.DisplayName or a.PetId) < (db and db.DisplayName or b.PetId)
    end)
    for index, pet in pets do
        createPetCard(pet, index, equippedCount, snapshot.AuraPetInstanceId)
    end
end

RemoteEvents.PetInventoryUpdatedEvent.OnClientEvent:Connect(renderInventory)

local function showMessage(text, color)
    hatchMessage:show(text, color)
end

local function onHatchResult(result)
    if typeof(result) ~= "table" then
        return
    end

    local egg = GameConfig.Eggs[result.EggId]
    local eggName = if egg then egg.DisplayName else "The egg"

    if result.Reason then
        Sfx.play("Error") -- refused: the egg is locked, guarded, or the bag is full
    end
    if result.Reason == "Locked" then
        showMessage(eggName .. " needs " .. tostring(result.RequiredRank) .. " to hatch.", Color3.new(1, 1, 1))
    elseif result.Reason == "TakeLocked" then
        showMessage(eggName .. " needs " .. tostring(result.RequiredRank) .. ": you can't carry it yet.", Color3.new(1, 1, 1))
    elseif result.Reason == "Guarded" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        local text = if result.Busy then "An egg is already being carried off. Wait for " .. who .. " to calm."
            else "Weaken " .. who .. " first: its eggs can be taken once it falters."
        showMessage(text, Color3.new(1, 1, 1))
    elseif result.Reason == "NoShare" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        showMessage("You haven't earned this egg: strike " .. who .. " yourself before you take one.", Color3.new(1, 1, 1))
    elseif result.Reason == "Retake" then
        showMessage("You just let an egg go back. You can take another in " .. tostring(result.Seconds) .. " s.", Color3.new(1, 1, 1))
    elseif result.Reason == "InventoryFull" then
        showMessage("Your pet inventory is full (" .. GameConfig.MaxOwnedPets .. " pets).", Color3.new(1, 1, 1))
    else
        local definition = GameConfig.Pets[result.PetId]
        -- the egg rises from the altar's cradle and breaks; the pet is named as it does
        local delay = if typeof(result.BreakAt) == "number" then math.max(0, result.BreakAt - workspace:GetServerTimeNow()) else 0
        HatchCeremony.play(result.Staged, delay, function()
            if definition then
                Sfx.play(if GRAND_REVEAL[definition.Rarity] then "RareReveal" else "HatchReveal")
                local rarityColor = GameConfig.PetRarityColors[definition.Rarity] or Color3.new(1, 1, 1)
                local article = if string.find(definition.DisplayName, "^[AEIOUaeiou]") then "an " else "a "
                local text = "You hatched " .. article .. definition.DisplayName .. "! ("
                    .. definition.Rarity .. ", " .. tostring(result.ChancePercent) .. "% chance)"
                showMessage(text, rarityColor)
            end
        end)
    end
end

RemoteEvents.EggHatchResultEvent.OnClientEvent:Connect(onHatchResult)

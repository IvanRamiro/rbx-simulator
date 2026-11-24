-- The pets window (the Pets button on the HUD's rail) and the hatch results. Each pet is a card:
-- its portrait (the pet itself, in a ViewportFrame), name, rarity, level and Qi bonus, its lock, and its Equip and
-- Aura buttons, and Fuse when a spare copy can go into it. Equipped pets come first, then by rarity. The server owns the
-- inventory (PetInventoryUpdatedEvent sends it; Equip / Unequip / TogglePetLock / FusePet ask).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Toast = require(UI:WaitForChild("Toast"))
local Hud = require(UI:WaitForChild("Hud"))
local ConfirmDialog = require(UI:WaitForChild("ConfirmDialog"))
local GiftUi = require(script.Parent:WaitForChild("GiftUi"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Portraits = require(UI:WaitForChild("Portraits"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local MutationLook = require(script.Parent:WaitForChild("MutationLook"))
local HatchCeremony = require(script.Parent:WaitForChild("HatchCeremony"))
local PenPicker = require(script.Parent:WaitForChild("PenPicker"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local RARITY_ORDER = { Divine = 8, Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }

local toggleButton, setPetBadge = Hud.railButton("PetsButton", UiTheme.Icons.Pets, "Pets", 1)

local onWindowClosed -- set below, with the pets it redraws

local window = Hud.window({
    Name = "PetsWindow", Title = "PETS", OnClose = function()
        onWindowClosed()
    end, Size = Vector2.new(600, 500), AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body

-- the top: how many are out of how many slots, and what they add, as two pills; between them, PEN (the beast pen: PenPicker)
local SUMMARY = UiTheme.Height.ButtonSmall
local PILL = 30
local equippedPill, equippedLabel = UiKit.pill(UiTheme.Icons.Pets, "", { Name = "Equipped", Position = UDim2.fromOffset(0, (SUMMARY - PILL) / 2),
    Size = UDim2.fromOffset(0, PILL), Parent = body })
local bonusPill, bonusLabel = UiKit.pill(UiTheme.Icons.Qi, "", {
    Name = "Bonus", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, (SUMMARY - PILL) / 2), Size = UDim2.fromOffset(0, PILL), Parent = body,
})
local pensButton = UiKit.button({ Name = "Pens", Text = "PEN", TextSize = 14, Tone = "Accent", AnchorPoint = Vector2.new(0.5, 0),
    Position = UDim2.fromScale(0.5, 0), Size = UDim2.fromOffset(110, SUMMARY), Parent = body })
pensButton.Activated:Connect(function()
    PenPicker.open()
end)
bonusLabel.TextColor3 = C.Highlight
local _, _ = equippedPill, bonusPill
local LIST_TOP = SUMMARY + UiTheme.Space.M
local petList = UiKit.scroll({ Name = "PetList", Position = UDim2.fromOffset(0, LIST_TOP), Size = UDim2.new(1, 0, 1, -LIST_TOP), Parent = body })
-- two cards to a row (square-cornered tiles of the bold look, the owner's "Cultivation Bold")
petList:FindFirstChildOfClass("UIListLayout"):Destroy()
local CARD_HEIGHT = 148
local petGrid = Instance.new("UIGridLayout")
petGrid.CellSize = UDim2.new(0.5, -UiTheme.Space.S / 2, 0, CARD_HEIGHT)
petGrid.CellPadding = UDim2.fromOffset(UiTheme.Space.S, UiTheme.Space.S)
petGrid.SortOrder = Enum.SortOrder.LayoutOrder
petGrid.Parent = petList

local hatchMessage = Toast.new("HatchMessage", Color3.new(1, 1, 1), 3.5)

window.link(toggleButton)
toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        window.open()
    end
end)

-- ---------- newly hatched pets ----------
-- Only a few cards fit in the window and the rest sort by rarity, so a new pet could land out of sight.
-- It goes to the top, marked New, until the window has been opened and closed.
local known = nil -- [InstanceId] = true: the pets seen so far (nil until the first inventory arrives)
local fresh = {}  -- [InstanceId] = true: new since the player last looked

-- ---------- a pet's card ----------
local CONFIRM_SECONDS = 3
local PORTRAIT = 72
local lastSnapshot = nil

-- Portraits kept from the last drawing, by pet: a redraw moves them to the new cards instead of building a ViewportFrame
-- and cloning a model per card (release audit, 2026-11-12: every equip, lock or hatch rebuilt up to 50 of them)
local portraitPool = {} -- [petId] = { frame, ... }

-- the portraits a drawing didn't reuse: pets no longer owned
local function clearPool()
    for petId, spare in portraitPool do
        for _, frame in spare do
            frame:Destroy()
        end
        portraitPool[petId] = nil
    end
end

local function takePortrait(petId)
    local spare = portraitPool[petId]
    local frame = spare and table.remove(spare)
    return frame or Portraits.pet(petId, PORTRAIT)
end

local function createPetCard(pet, layoutOrder, equippedCount)
    local definition = GameConfig.Pets[pet.PetId]
    if not definition then
        return
    end
    local rarityColor = GameConfig.PetRarityColors[definition.Rarity] or C.Text

    local level = PetRules.level(pet)
    local size = PetRules.size(pet)
    local sizeInfo = PetRules.sizeInfo(size)
    local big = sizeInfo.Order > PetRules.Sizes.Normal.Order
    local mutation = PetRules.mutation(pet)
    local mutationColor = mutation and PetRules.Mutations[mutation].Color
    local card = UiKit.boldCard(UiKit.card({ Name = "PetCard", LayoutOrder = layoutOrder, Parent = petList }), rarityColor)
    if big or mutation then
        -- a Large, Giant or Colossal pet: a faint light of its size's colour rising from the card's foot, and its portrait's well ringed
        -- in it; a mutated one's light and ring are its mutation's colour
        local glow = Instance.new("Frame")
        glow.Name = "SizeGlow"
        glow.BorderSizePixel = 0
        glow.BackgroundColor3 = mutationColor or sizeInfo.Color
        glow.Size = UDim2.fromScale(1, 1)
        glow.Parent = card -- (first in: the card's contents draw over it)
        UiKit.corner(glow, UiTheme.Radius.Card)
        local fade = Instance.new("UIGradient")
        fade.Rotation = -90
        local strength = if sizeInfo.Order >= PetRules.Sizes.Giant.Order or mutation then 0.72 else 0.84 -- (transparency at the foot)
        fade.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, strength), NumberSequenceKeypoint.new(0.55, 0.97),
            NumberSequenceKeypoint.new(1, 1) })
        fade.Parent = glow
    end
    card:SetAttribute("InstanceId", pet.InstanceId)
    local PAD = UiTheme.Pad.Card
    -- the portrait on a dark well, its rarity's colour round it
    local well = Instance.new("Frame")
    well.Name = "Well"
    well.BackgroundColor3 = C.Well
    well.BackgroundTransparency = 0.3
    well.BorderSizePixel = 0
    well.Position = UDim2.fromOffset(PAD, PAD)
    well.Size = UDim2.fromOffset(PORTRAIT, PORTRAIT)
    well.Parent = card
    UiKit.corner(well, UiTheme.Radius.Chip + 2)
    UiKit.stroke(well, mutationColor or (if big then sizeInfo.Color else rarityColor), if big or mutation then 0.15 else 0.55,
        if sizeInfo.Order >= PetRules.Sizes.Giant.Order or mutation then 2 else 1)
    local picture = takePortrait(pet.PetId)
    MutationLook.portrait(picture, mutation) -- (tinted, with its glints; a pooled portrait's old tint is cleared)
    picture.Name = "Portrait"
    picture:SetAttribute("PetId", pet.PetId)
    picture.Position = UDim2.fromOffset(PAD, PAD)
    picture.Parent = card
    local textLeft = PAD + PORTRAIT + UiTheme.Space.M
    local BUTTON = UiTheme.Height.Button
    local LOCK = BUTTON -- a square at the end of the buttons' row
    -- beside the portrait, top down: the name (a long one wraps to a second line), its tags, its Qi
    local info = Instance.new("Frame")
    info.Name = "Info"
    info.BackgroundTransparency = 1
    info.Position = UDim2.fromOffset(textLeft, PAD - 2)
    info.Size = UDim2.new(1, -(textLeft + PAD), 0, PORTRAIT + 4)
    info.Parent = card
    UiKit.list(info, { Padding = UDim.new(0, 4) })
    UiKit.boldLabel({
        Name = "PetName", TextSize = 15, Text = PetRules.displayName(pet.PetId, mutation), TextWrapped = true, AutomaticSize = Enum.AutomaticSize.Y,
        Size = UDim2.new(1, -38, 0, 0), LayoutOrder = 1, Parent = info, -- (room at the right of the name for the gift button)
    })
    -- the lock: gold while it's on, faint while it's off
    local lock = UiKit.button({
        Name = "Lock", Text = "", Tone = if pet.Locked then "Highlight" else "Quiet", AnchorPoint = Vector2.new(1, 1),
        Position = UDim2.new(1, -PAD, 1, -PAD + 2), Size = UDim2.fromOffset(LOCK, BUTTON), Parent = card,
    })
    local padlock = Instance.new("ImageLabel")
    padlock.BackgroundTransparency = 1
    padlock.Image = UiTheme.Icons.Lock
    padlock.ImageTransparency = if pet.Locked then 0 else 0.55
    padlock.AnchorPoint = Vector2.new(0.5, 0.5)
    padlock.Position = UDim2.fromScale(0.5, 0.5)
    padlock.Size = UDim2.fromOffset(20, 20)
    padlock.Parent = lock
    lock.Activated:Connect(function()
        RemoteEvents.TogglePetLockEvent:FireServer(pet.InstanceId)
    end)
    -- the gift button, top right: opens the list of players here to give this pet to (the server decides if it can be given: GiftService)
    local gift = UiKit.button({
        Name = "Gift", Text = "", Tone = "Quiet", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -PAD, 0, PAD - 2), Size = UDim2.fromOffset(34, 34), Parent = card,
    })
    local giftIcon = Instance.new("ImageLabel")
    giftIcon.Name = "GiftIcon"
    giftIcon.BackgroundTransparency = 1
    giftIcon.Image = UiTheme.Icons.Store -- (a gift box tied in gold)
    giftIcon.AnchorPoint = Vector2.new(0.5, 0.5)
    giftIcon.Position = UDim2.fromScale(0.5, 0.5)
    giftIcon.Size = UDim2.fromOffset(24, 24)
    giftIcon.Parent = gift
    gift.Activated:Connect(function()
        GiftUi.open(pet)
    end)
    local tags = Instance.new("Frame")
    tags.Name = "Tags"
    tags.BackgroundTransparency = 1
    tags.Size = UDim2.new(1, 0, 0, 18)
    tags.LayoutOrder = 2
    tags.Parent = info
    local tagRow = UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4),
        VerticalAlignment = Enum.VerticalAlignment.Center })
    if fresh[pet.InstanceId] then -- (on the portrait's corner: the tags row holds rarity, size and mutation, and must fit them all)
        local new = UiKit.tag("New", C.Highlight)
        new.Name = "NewTag"
        new.BackgroundTransparency = 0.25
        new.BackgroundColor3 = C.Well
        new.Position = UDim2.fromOffset(PAD - 4, PAD - 6)
        new.ZIndex = picture.ZIndex + 2
        new.Parent = card
    end
    local rarityTag = UiKit.tag(definition.Rarity, rarityColor)
    rarityTag.Parent = tags
    if size ~= "Normal" then -- (Normal is the usual: no pill)
        local sizeTag = UiKit.tag(size, sizeInfo.Color)
        sizeTag.Name = "SizeTag"
        sizeTag.LayoutOrder = 1
        sizeTag.Parent = tags
    end
    local mutationTag = MutationLook.badge(mutation)
    if mutationTag then
        mutationTag.LayoutOrder = 1
        mutationTag.Parent = tags
        -- a long rarity, size and mutation together (LEGENDARY COLOSSAL CELESTIAL) can't fit the row on a narrow card: the rarity's pill
        -- steps aside (the card's edge is the rarity's colour already), never the size or the mutation
        local function fit()
            if rarityTag.Parent and tags.AbsoluteSize.X > 0 then
                rarityTag.Visible = true
                if tagRow.AbsoluteContentSize.X > tags.AbsoluteSize.X + 1 then
                    rarityTag.Visible = false
                end
            end
        end
        tags:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
        task.defer(fit)
    end

    UiKit.boldLabel({
        Name = "Qi", TextSize = 15, TextColor3 = C.Highlight, RichText = true,
        -- (and, for one roaming in a pen, which: equipping it takes it out)
        -- (its level here, not in the tags: a Colossal Celestial's tags fill the row)
        Text = "+" .. PetRules.qiBonus(pet.PetId, level, size, mutation) .. "% Qi"
            .. (if level > 1 then '  <font color="#' .. C.AccentBright:ToHex() .. '">Lv ' .. level .. "</font>" else "")
            .. (if pet.InPen then '  <font color="#' .. C.Sky:ToHex() .. '">IN PEN</font>' else ""),
        Size = UDim2.new(1, 0, 0, 18), LayoutOrder = 3, Parent = info,
    })

    -- buttons side by side along the card's foot, under the portrait's level: one thumb's height (44)
    local material = PetRules.findMaterial(lastSnapshot.Pets, pet)
    local buttons = if material then 2 else 1 -- (SET AURA removed, the owner 2026-11-12: pets no longer colour the aura)
    local function action(text, tone, slot, onClick)
        local gap = UiTheme.Space.S
        local share = -(PAD * 2 + LOCK + gap + (buttons - 1) * gap) / buttons
        local b = UiKit.button({
            Name = if slot == 0 then "Main" else "Fuse", TextSize = 14, Text = text, Tone = tone, Active = onClick ~= nil,
            AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(slot / buttons, PAD + slot * (share + gap), 1, -PAD + 2),
            Size = UDim2.new(1 / buttons, share, 0, BUTTON), Parent = card,
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
    elseif equippedCount < PassRules.maxEquipped(Players.LocalPlayer) then
        action("EQUIP", "Go", 0, function()
            RemoteEvents.EquipPetEvent:FireServer(pet.InstanceId)
        end)
    else
        action("SLOTS FULL", "Quiet", 0, nil)
    end
    -- Fuse asks once more, naming the level it reaches; a Secret copy asks properly, with a wait
    if material then
        local reaches = level + PetRules.level(material)
        local fuse
        local armedUntil = 0
        fuse = action("FUSE", "Accent", 1, function()
            if definition.Rarity == "Secret" or definition.Rarity == "Divine" then
                ConfirmDialog.show({
                    Title = "FUSE A " .. string.upper(definition.Rarity) .. " PET", Picture = Portraits.pet(pet.PetId, 72), ConfirmText = "FUSE IT",
                    Text = "This uses up another " .. definition.DisplayName .. " to raise this one to Level " .. reaches .. ". You can't undo this.",
                    OnConfirm = function()
                        RemoteEvents.FusePetEvent:FireServer(pet.InstanceId, true)
                    end,
                })
            elseif os.clock() < armedUntil then
                RemoteEvents.FusePetEvent:FireServer(pet.InstanceId)
            else
                armedUntil = os.clock() + CONFIRM_SECONDS
                fuse.Text = "TO LV " .. reaches .. "?"
                task.delay(CONFIRM_SECONDS, function()
                    if fuse.Parent and os.clock() >= armedUntil then
                        fuse.Text = "FUSE"
                    end
                end)
            end
        end)
    end
end

local drawList -- (below)
local listDirty = false   -- the inventory changed while the window was closed
local scrollToTop = false -- a new pet arrived: the next drawing starts at the top, where it is

local function renderInventory(snapshot)
    for _, pet in if snapshot then snapshot.Pets else {} do
        PetPreload.soon(pet.PetId) -- ready before their portraits or their first walk
    end
    if not snapshot then
        return
    end
    lastSnapshot = snapshot
    PenPicker.setSnapshot(snapshot)
    local arrived = false
    for _, pet in snapshot.Pets do
        if known and not known[pet.InstanceId] then
            fresh[pet.InstanceId] = true
            arrived = true
        end
    end
    known = {}
    for _, pet in snapshot.Pets do
        known[pet.InstanceId] = true
    end
    scrollToTop = scrollToTop or arrived

    local equippedCount = 0
    local bonusPercent = 0
    for _, pet in snapshot.Pets do
        local definition = GameConfig.Pets[pet.PetId]
        if pet.Equipped and definition then
            equippedCount += 1
            bonusPercent += PetRules.qiBonus(pet.PetId, PetRules.level(pet), pet.Size, pet.Mutation)
        end
    end
    bonusPercent += snapshot.CodexQiPercent or 0
    local slots = PassRules.maxEquipped(Players.LocalPlayer) -- (the slots pass adds more)
    setPetBadge(equippedCount .. "/" .. slots)
    equippedLabel.Text = "EQUIPPED  " .. equippedCount .. " / " .. slots
    bonusLabel.Text = "QI BONUS  +" .. bonusPercent .. "%"

    -- the cards only while someone can see them: a closed window is drawn when it opens
    if window.isOpen() then
        drawList(snapshot, equippedCount)
    else
        listDirty = true
    end
end

function drawList(snapshot, equippedCount)
    listDirty = false
    for _, child in petList:GetChildren() do
        if child:IsA("GuiObject") then
            local portrait = child:FindFirstChild("Portrait")
            local petId = portrait and portrait:GetAttribute("PetId")
            if petId then
                portrait.Parent = nil
                portraitPool[petId] = portraitPool[petId] or {}
                table.insert(portraitPool[petId], portrait)
            end
            child:Destroy()
        end
    end
    if equippedCount == nil then
        equippedCount = 0
        for _, pet in snapshot.Pets do
            if pet.Equipped and GameConfig.Pets[pet.PetId] then
                equippedCount += 1
            end
        end
    end

    -- an empty list's message spans the window; cards sit two to a row
    petGrid.CellSize = if #snapshot.Pets == 0 then UDim2.new(1, 0, 0, 200) else UDim2.new(0.5, -UiTheme.Space.S / 2, 0, CARD_HEIGHT)
    if #snapshot.Pets == 0 then
        UiKit.empty(petList, "No pets yet.\nTake an egg from a guardian, carry it home, and hatch it at the Hatching Sanctum.")
        clearPool()
        return
    end
    -- new first, then equipped, then the rarest, then by name
    local pets = table.clone(snapshot.Pets)
    table.sort(pets, function(a, b)
        local da, db = GameConfig.Pets[a.PetId], GameConfig.Pets[b.PetId]
        if (fresh[a.InstanceId] == true) ~= (fresh[b.InstanceId] == true) then
            return fresh[a.InstanceId] == true
        end
        if (a.Equipped == true) ~= (b.Equipped == true) then
            return a.Equipped == true
        end
        local ra, rb = da and RARITY_ORDER[da.Rarity] or 0, db and RARITY_ORDER[db.Rarity] or 0
        if ra ~= rb then
            return ra > rb
        end
        if (da and da.DisplayName) ~= (db and db.DisplayName) then
            return (da and da.DisplayName or a.PetId) < (db and db.DisplayName or b.PetId)
        end
        -- (copies of one beast: the rarer mutation, then the bigger, first)
        local ma, mb = PetRules.mutationInfo(a).Order, PetRules.mutationInfo(b).Order
        if ma ~= mb then
            return ma > mb
        end
        return PetRules.sizeInfo(a).Order > PetRules.sizeInfo(b).Order
    end)
    for index, pet in pets do
        createPetCard(pet, index, equippedCount)
    end
    clearPool()
    if scrollToTop then
        scrollToTop = false
        petList.CanvasPosition = Vector2.zero
    end
end

window.Frame:GetPropertyChangedSignal("Visible"):Connect(function()
    if window.Frame.Visible and listDirty and lastSnapshot then
        drawList(lastSnapshot)
    end
end)

RemoteEvents.PetInventoryUpdatedEvent.OnClientEvent:Connect(renderInventory)
for _, pass in PassRules.List do
    if pass.ExtraSlots then -- bought in the Store: the limit and every Equip button change at once
        Players.LocalPlayer:GetAttributeChangedSignal("Pass_" .. pass.Id):Connect(function()
            if lastSnapshot then
                renderInventory(lastSnapshot)
            end
        end)
    end
end

-- a fusion's answer: the inventory has already redrawn, so the card it raised can be found and lit
RemoteEvents.PetActionResultEvent.OnClientEvent:Connect(function(ok, text, fused)
    if not ok then
        Sfx.play("Error")
        hatchMessage:show(tostring(text), "Error")
        return
    end
    local definition = fused and GameConfig.Pets[fused.PetId]
    local color = definition and GameConfig.PetRarityColors[definition.Rarity] or Color3.new(1, 1, 1)
    Sfx.play("PetFuse")
    hatchMessage:show(tostring(text), "Success", color)
    for _, card in petList:GetChildren() do
        if card:IsA("GuiObject") and fused and card:GetAttribute("InstanceId") == fused.InstanceId then
            UiFx.pop(card, 1.04, 0.3)
            UiFx.sweep(card, color, 0.5)
        end
    end
end)

-- once the player has looked, new pets take their usual places
function onWindowClosed()
    if next(fresh) then
        fresh = {}
        renderInventory(lastSnapshot)
    end
end


-- a refusal: something the player can do about it (a Warning), or simply can't right now (an Error)
local function showMessage(text, kind)
    hatchMessage:show(text, kind)
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
        showMessage(eggName .. " needs " .. tostring(result.RequiredRank) .. " to hatch.", "Warning")
    elseif result.Reason == "TakeLocked" then
        -- and which egg here is theirs: each island's three eggs need three ranks, and a newcomer can only carry the first
        local instead = GameConfig.Eggs[result.Instead or ""]
        local text = "You need to be " .. tostring(result.RequiredRank) .. " to carry the " .. eggName .. "."
        if instead and typeof(result.BackIn) == "number" and result.BackIn > 0 then
            text ..= " You can take the " .. instead.DisplayName .. ": it comes back to its stand in "
                .. string.format("%d:%02d", result.BackIn // 60, result.BackIn % 60) .. "."
        elseif instead then
            text ..= " You can take the " .. instead.DisplayName .. "."
        end
        showMessage(text, "Warning")
    elseif result.Reason == "Guarded" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        local text = if result.Busy then "Someone is already carrying an egg away. Wait for " .. who .. " to calm down."
            else "Hit " .. who .. " until it is weak. Then you can take its eggs."
        showMessage(text, "Warning")
    elseif result.Reason == "NoShare" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        showMessage("You haven't earned this egg yet. Hit " .. who .. " yourself before you take one.", "Warning")
    elseif result.Reason == "Retake" then
        showMessage("You just let an egg go back. You can take another in " .. tostring(result.Seconds) .. " s.", "Warning")
    elseif result.Reason == "NotAtAltar" then
        showMessage("Stand by the altar and try again: your egg is safe.", "Warning")
    elseif result.Reason == "HatchBusy" then
        showMessage("An egg is still hatching. Try again in a moment: your egg is safe.", "Warning")
    elseif result.Reason == "PurchaseSaving" then
        showMessage("Your purchase is being saved. Try again in a moment: your egg is safe.", "Warning")
    elseif result.Reason == "NoEgg" then
        showMessage("You don't have that egg any more.", "Error")
    elseif result.Reason == "InventoryFull" then
        showMessage("Your pet inventory is full (" .. GameConfig.MaxOwnedPets .. " pets). Fuse or sell your extra pets.", "Warning")
    else
        -- the hatch cinematic: the camera to the egg, the reel of its beasts, the crack and the reveal card (HatchCeremony)
        HatchCeremony.play(result)
    end
end

RemoteEvents.EggHatchResultEvent.OnClientEvent:Connect(onHatchResult)

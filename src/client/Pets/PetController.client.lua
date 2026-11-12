-- The pets window (the Pets button on the HUD's rail) and the hatch results. Each pet is a card:
-- its portrait (the pet itself, in a ViewportFrame), name, rarity, level and Qi bonus, its lock, and its Equip and
-- Aura buttons, and Fuse when a spare copy can go into it. Equipped pets come first, then by rarity. The server owns the
-- inventory (PetInventoryUpdatedEvent sends it; Equip / Unequip / SetAura / TogglePetLock / FusePet ask).
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
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Portraits = require(UI:WaitForChild("Portraits"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local HatchCeremony = require(script.Parent:WaitForChild("HatchCeremony"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local RARITY_ORDER = { Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }

local toggleButton, setPetBadge = Hud.railButton("PetsButton", UiTheme.Icons.Pets, "Pets", 1)

local onWindowClosed -- set below, with the pets it redraws

local window = Hud.window({
    Name = "PetsWindow", Title = "PETS", OnClose = function()
        onWindowClosed()
    end, Size = Vector2.new(372, 400), AnchorPoint = Vector2.new(0, 0),
    Position = UDim2.fromOffset(UiTheme.Margin + 270 + 16, UiTheme.Margin), -- beside the left column (the profile is 270 wide)
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
    return frame or Portraits.pet(petId, 58)
end

local function createPetCard(pet, layoutOrder, equippedCount, auraPetInstanceId)
    local definition = GameConfig.Pets[pet.PetId]
    if not definition then
        return
    end
    local isAuraPet = pet.InstanceId == auraPetInstanceId
    local rarityColor = GameConfig.PetRarityColors[definition.Rarity] or C.Text

    local level = PetRules.level(pet)
    local card = UiKit.card({ Name = "PetCard", LayoutOrder = layoutOrder, Size = UDim2.new(1, 0, 0, 90), Stripe = rarityColor, Parent = petList })
    card:SetAttribute("InstanceId", pet.InstanceId)
    local picture = takePortrait(pet.PetId)
    picture.Name = "Portrait"
    picture:SetAttribute("PetId", pet.PetId)
    picture.Position = UDim2.fromOffset(10, 9)
    picture.Parent = card
    UiKit.label({
        Name = "PetName", Font = "Title", TextSize = 15, Text = definition.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
        Position = UDim2.fromOffset(78, 7), Size = UDim2.new(1, -112, 0, 18), Parent = card,
    })
    -- the lock: gold while it's on, faint while it's off
    local lock = UiKit.button({
        Name = "Lock", Text = "", Tone = if pet.Locked then "Highlight" else "Quiet", AnchorPoint = Vector2.new(1, 0),
        Position = UDim2.new(1, -6, 0, 5), Size = UDim2.fromOffset(34, 34), Parent = card,
    })
    local padlock = Instance.new("ImageLabel")
    padlock.BackgroundTransparency = 1
    padlock.Image = UiTheme.Icons.Lock
    padlock.ImageTransparency = if pet.Locked then 0 else 0.6
    padlock.AnchorPoint = Vector2.new(0.5, 0.5)
    padlock.Position = UDim2.fromScale(0.5, 0.5)
    padlock.Size = UDim2.fromOffset(18, 18)
    padlock.Parent = lock
    lock.Activated:Connect(function()
        RemoteEvents.TogglePetLockEvent:FireServer(pet.InstanceId)
    end)
    local tags = Instance.new("Frame")
    tags.Name = "Tags"
    tags.BackgroundTransparency = 1
    tags.Position = UDim2.fromOffset(78, 27)
    tags.Size = UDim2.new(1, -86, 0, 16)
    tags.Parent = card
    UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
    if fresh[pet.InstanceId] then
        local new = UiKit.tag("New", C.Highlight)
        new.LayoutOrder = -1
        new.Parent = tags
    end
    UiKit.tag(definition.Rarity, rarityColor).Parent = tags
    if level > 1 then
        local levelTag = UiKit.tag("Lv " .. level, C.AccentBright)
        levelTag.LayoutOrder = 0
        levelTag.Parent = tags
    end
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.AccentBright, Text = "+" .. PetRules.qiBonus(pet.PetId, level) .. "% Qi",
        AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 16), LayoutOrder = 1, Parent = tags,
    })
    if isAuraPet then
        local aura = UiKit.tag("Aura", C.Highlight)
        aura.LayoutOrder = 2
        aura.Parent = tags
    end

    -- buttons side by side, from the portrait's edge to the card's (78 px in, 8 px short, 4 apart)
    local material = PetRules.findMaterial(lastSnapshot.Pets, pet)
    local buttons = if material then 3 else 2
    local function action(text, tone, slot, onClick)
        local share = -(86 + (buttons - 1) * 4) / buttons
        local b = UiKit.button({
            Font = "Strong", TextSize = 11, Text = text, Tone = tone, Active = onClick ~= nil,
            Position = UDim2.new(slot / buttons, 78 + slot * (share + 4), 0, 49), Size = UDim2.new(1 / buttons, share, 0, 34), -- (22 was too small to tap: UI audit 2026-11-11)
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
    elseif equippedCount < PassRules.maxEquipped(Players.LocalPlayer) then
        action("EQUIP", "Accent", 0, function()
            RemoteEvents.EquipPetEvent:FireServer(pet.InstanceId)
        end)
    else
        action("SLOTS FULL", "Quiet", 0, nil)
    end
    if isAuraPet then
        action("AURA ON", "Highlight", 1, function()
            RemoteEvents.SetAuraPetEvent:FireServer(nil)
        end)
    else
        action("SET AURA", "Quiet", 1, if pet.Equipped then function()
            RemoteEvents.SetAuraPetEvent:FireServer(pet.InstanceId)
        end else nil)
    end
    -- Fuse asks once more, naming the level it reaches; a Secret copy asks properly, with a wait
    if material then
        local reaches = level + PetRules.level(material)
        local fuse
        local armedUntil = 0
        fuse = action("FUSE", "Accent", 2, function()
            if definition.Rarity == "Secret" then
                ConfirmDialog.show({
                    Title = "FUSE A SECRET PET", Picture = Portraits.pet(pet.PetId, 72), ConfirmText = "FUSE IT",
                    Text = "This spends another " .. definition.DisplayName .. " to raise this one to Level " .. reaches .. ". It can't be undone.",
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
            bonusPercent += PetRules.qiBonus(pet.PetId, PetRules.level(pet))
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
        return (da and da.DisplayName or a.PetId) < (db and db.DisplayName or b.PetId)
    end)
    for index, pet in pets do
        createPetCard(pet, index, equippedCount, snapshot.AuraPetInstanceId)
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
    Sfx.play("RareReveal")
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
        showMessage(eggName .. " needs " .. tostring(result.RequiredRank) .. ": you can't carry it yet.", "Warning")
    elseif result.Reason == "Guarded" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        local text = if result.Busy then "An egg is already being carried off. Wait for " .. who .. " to calm."
            else "Weaken " .. who .. " first: its eggs can be taken once it falters."
        showMessage(text, "Warning")
    elseif result.Reason == "NoShare" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        showMessage("You haven't earned this egg: strike " .. who .. " yourself before you take one.", "Warning")
    elseif result.Reason == "Retake" then
        showMessage("You just let an egg go back. You can take another in " .. tostring(result.Seconds) .. " s.", "Warning")
    elseif result.Reason == "NotAtAltar" then
        showMessage("Stand by the altar and try again: your egg is safe.", "Warning")
    elseif result.Reason == "HatchBusy" then
        showMessage("An egg is still hatching. Try again in a moment: your egg is safe.", "Warning")
    elseif result.Reason == "NoEgg" then
        showMessage("You don't have that egg any more.", "Error")
    elseif result.Reason == "InventoryFull" then
        showMessage("Your pet inventory is full (" .. GameConfig.MaxOwnedPets .. " pets). Fuse or sell your spares.", "Warning")
    else
        -- the hatch cinematic: the camera to the egg, the reel of its beasts, the crack and the reveal card (HatchCeremony)
        HatchCeremony.play(result)
    end
end

RemoteEvents.EggHatchResultEvent.OnClientEvent:Connect(onHatchResult)

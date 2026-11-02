local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudScale"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local HatchCeremony = require(script.Parent:WaitForChild("HatchCeremony"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "PetHud"
local PANEL_COLOR = Color3.fromRGB(20, 20, 30)
local ROW_COLOR = Color3.fromRGB(40, 40, 55)
local EQUIP_COLOR = Color3.fromRGB(70, 160, 110)
local UNEQUIP_COLOR = Color3.fromRGB(170, 75, 75)
local SET_AURA_COLOR = Color3.fromRGB(70, 110, 180)
local AURA_COLOR = Color3.fromRGB(200, 155, 50)
local DISABLED_COLOR = Color3.fromRGB(90, 90, 90)

local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false

local root = Instance.new("Frame")
root.Name = "Root"
root.AnchorPoint = Vector2.new(0, 0.5)
root.Position = UDim2.new(0, 16, 0.5, 0)
root.Size = UDim2.fromOffset(260, 330)
root.BackgroundTransparency = 1
root.Parent = hud
applyHudScale(root)

local toggleButton = Instance.new("TextButton")
toggleButton.Name = "ToggleButton"
toggleButton.Size = UDim2.fromOffset(110, 40)
toggleButton.BackgroundColor3 = PANEL_COLOR
toggleButton.BackgroundTransparency = 0.25
toggleButton.Font = Enum.Font.GothamBold
toggleButton.TextScaled = true
toggleButton.TextColor3 = Color3.new(1, 1, 1)
toggleButton.Text = "Pets"
toggleButton.Parent = root

local toggleCorner = Instance.new("UICorner")
toggleCorner.CornerRadius = UDim.new(0, 10)
toggleCorner.Parent = toggleButton

local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.Position = UDim2.fromOffset(0, 48)
panel.Size = UDim2.new(1, 0, 1, -48)
panel.BackgroundColor3 = PANEL_COLOR
panel.BackgroundTransparency = 0.25
panel.Visible = false
panel.Parent = root

local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 12)
panelCorner.Parent = panel

local summaryLabel = Instance.new("TextLabel")
summaryLabel.Name = "SummaryLabel"
summaryLabel.Position = UDim2.fromOffset(10, 8)
summaryLabel.Size = UDim2.new(1, -20, 0, 22)
summaryLabel.BackgroundTransparency = 1
summaryLabel.Font = Enum.Font.GothamBold
summaryLabel.TextScaled = true
summaryLabel.TextColor3 = Color3.fromRGB(150, 230, 255)
summaryLabel.Text = "Loading pets..."
summaryLabel.Parent = panel

local petList = Instance.new("ScrollingFrame")
petList.Name = "PetList"
petList.Position = UDim2.fromOffset(8, 38)
petList.Size = UDim2.new(1, -16, 1, -46)
petList.BackgroundTransparency = 1
petList.BorderSizePixel = 0
petList.ScrollBarThickness = 6
petList.CanvasSize = UDim2.new()
petList.AutomaticCanvasSize = Enum.AutomaticSize.Y
petList.Parent = panel

local listLayout = Instance.new("UIListLayout")
listLayout.Padding = UDim.new(0, 6)
listLayout.SortOrder = Enum.SortOrder.LayoutOrder
listLayout.Parent = petList

local hatchMessage = Toast.new(hud, "HatchMessage", 12, Color3.new(1, 1, 1), 3.5)

hud.Parent = playerGui

toggleButton.Activated:Connect(function()
    panel.Visible = not panel.Visible
end)

local function createRowButton(row, position, text, color, onClick)
    local button = Instance.new("TextButton")
    button.Position = position
    button.Size = UDim2.new(0.5, -12, 0, 24)
    button.BackgroundColor3 = if onClick then color else DISABLED_COLOR
    button.AutoButtonColor = onClick ~= nil
    button.Font = Enum.Font.GothamBold
    button.TextScaled = true
    button.TextColor3 = Color3.new(1, 1, 1)
    button.Text = text
    button.Parent = row

    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 6)
    corner.Parent = button

    if onClick then
        button.Activated:Connect(onClick)
    end
end

local function createPetRow(pet, layoutOrder, equippedCount, auraPetInstanceId)
    local definition = GameConfig.Pets[pet.PetId]
    if not definition then
        return
    end

    local isAuraPet = pet.InstanceId == auraPetInstanceId

    local row = Instance.new("Frame")
    row.Name = "PetRow"
    row.LayoutOrder = layoutOrder
    row.Size = UDim2.new(1, -10, 0, 60)
    row.BackgroundColor3 = ROW_COLOR
    row.Parent = petList

    local rowCorner = Instance.new("UICorner")
    rowCorner.CornerRadius = UDim.new(0, 8)
    rowCorner.Parent = row

    local nameLabel = Instance.new("TextLabel")
    nameLabel.Position = UDim2.fromOffset(8, 4)
    nameLabel.Size = UDim2.new(0.68, -8, 0, 22)
    nameLabel.BackgroundTransparency = 1
    nameLabel.Font = Enum.Font.GothamBold
    nameLabel.TextScaled = true
    nameLabel.TextXAlignment = Enum.TextXAlignment.Left
    nameLabel.TextColor3 = if isAuraPet then AURA_COLOR else Color3.new(1, 1, 1)
    nameLabel.Text = definition.DisplayName .. "  +" .. definition.QiBonusPercent .. "% Qi"

    local rarityLabel = Instance.new("TextLabel")
    rarityLabel.AnchorPoint = Vector2.new(1, 0)
    rarityLabel.Position = UDim2.new(1, -8, 0, 6)
    rarityLabel.Size = UDim2.new(0.32, -8, 0, 18)
    rarityLabel.BackgroundTransparency = 1
    rarityLabel.Font = Enum.Font.GothamBold
    rarityLabel.TextScaled = true
    rarityLabel.TextXAlignment = Enum.TextXAlignment.Right
    rarityLabel.TextColor3 = GameConfig.PetRarityColors[definition.Rarity] or Color3.new(1, 1, 1)
    rarityLabel.Text = definition.Rarity
    rarityLabel.Parent = row
    nameLabel.Parent = row

    local leftPosition = UDim2.new(0, 8, 0, 30)
    if pet.Equipped then
        createRowButton(row, leftPosition, "Unequip", UNEQUIP_COLOR, function()
            RemoteEvents.UnequipPetEvent:FireServer(pet.InstanceId)
        end)
    elseif equippedCount < GameConfig.MaxEquippedPets then
        createRowButton(row, leftPosition, "Equip", EQUIP_COLOR, function()
            RemoteEvents.EquipPetEvent:FireServer(pet.InstanceId)
        end)
    else
        createRowButton(row, leftPosition, "Slots full", DISABLED_COLOR, nil)
    end

    local rightPosition = UDim2.new(0.5, 4, 0, 30)
    if isAuraPet then
        createRowButton(row, rightPosition, "Aura (on)", AURA_COLOR, function()
            RemoteEvents.SetAuraPetEvent:FireServer(nil)
        end)
    elseif pet.Equipped then
        createRowButton(row, rightPosition, "Set Aura", SET_AURA_COLOR, function()
            RemoteEvents.SetAuraPetEvent:FireServer(pet.InstanceId)
        end)
    else
        createRowButton(row, rightPosition, "Set Aura", DISABLED_COLOR, nil)
    end
end

local function renderInventory(snapshot)
    if not snapshot then
        return
    end

    for _, child in petList:GetChildren() do
        if child:IsA("Frame") then
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
    toggleButton.Text = "Pets " .. equippedText
    summaryLabel.Text = "Equipped " .. equippedText .. "  |  Qi bonus +" .. bonusPercent .. "%"

    for index, pet in snapshot.Pets do
        createPetRow(pet, index, equippedCount, snapshot.AuraPetInstanceId)
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

    if result.Reason == "Locked" then
        showMessage(eggName .. " needs " .. tostring(result.RequiredRank) .. " to hatch.", Color3.new(1, 1, 1))
    elseif result.Reason == "TakeLocked" then
        showMessage(eggName .. " needs " .. tostring(result.RequiredRank) .. ": you can't carry it yet.", Color3.new(1, 1, 1))
    elseif result.Reason == "Guarded" then
        local who = result.Called or ("the " .. tostring(result.Guardian))
        local text = if result.Busy then "An egg is already being carried off. Wait for " .. who .. " to calm."
            else "Weaken " .. who .. " first: its eggs can be taken once it falters."
        showMessage(text, Color3.new(1, 1, 1))
    elseif result.Reason == "InventoryFull" then
        showMessage("Your pet inventory is full (" .. GameConfig.MaxOwnedPets .. " pets).", Color3.new(1, 1, 1))
    else
        local definition = GameConfig.Pets[result.PetId]
        -- the egg rises from the altar's cradle and breaks; the pet is named as it does
        local delay = if typeof(result.BreakAt) == "number" then math.max(0, result.BreakAt - workspace:GetServerTimeNow()) else 0
        HatchCeremony.play(result.Staged, delay, function()
            if definition then
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

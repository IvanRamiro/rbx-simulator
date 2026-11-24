-- The beta gift's window (shared/BetaGift; the server decides everything: server/Rewards/BetaGiftService): "CHOOSE YOUR BETA GIFT",
-- the Exclusive Egg's three beasts side by side, each card with the beast turning, its name, its rarity in the rarity's colour, its
-- Qi bonus, a line about it and CHOOSE. CHOOSE asks once more (ConfirmDialog: "You can only choose once"), then the server gives it.
-- After that the window shows the beast as theirs, and once closed it is gone.
-- Players find it two ways while it waits (the player's "BetaGift" attribute is "Open"): a round gift button in the top row with a
-- gold "!", and the window opening by itself once after joining, when nothing else is on the screen (the tutorial's first step
-- done, the join's title notice gone, no other window open). It can be closed and opened again from the button until they choose.
-- Once chosen, the button and the window are gone for good: the attribute comes from the server's claim record, so a rejoin, a
-- respawn or another server never shows them again.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local BetaGift = require(ReplicatedStorage:WaitForChild("BetaGift"))
local PetLore = require(ReplicatedStorage:WaitForChild("PetLore"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local client = script.Parent.Parent
local UI = client:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local ConfirmDialog = require(UI:WaitForChild("ConfirmDialog"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Sfx = require(client:WaitForChild("Audio"):WaitForChild("Sfx"))
local HatchCeremony = require(client:WaitForChild("Pets"):WaitForChild("HatchCeremony"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local C = UiTheme.Colors
local Event = RemoteEvents.BetaGiftEvent
local ATTRIBUTE = "BetaGift"

local WIDTH, HEIGHT = 720, 440
local FRAME = UiTheme.Height.TitleBar + UiTheme.Space.M + UiTheme.Pad.Window -- the window's height round its body
local GAP = UiTheme.Space.M
local PAD = UiTheme.Space.S + 2 -- inside a card
local BUTTON = UiTheme.Height.Button
local TALL_CARD = 250 -- a card at least this tall stands its beast over its words; a shorter one (a phone's) puts it beside them

local message = Toast.new("BetaGiftMessage", C.Highlight, 6)

-- ---------- the round button ----------
local button, setBadge = Hud.topButton("BetaGiftButton", GameConfig.ExclusiveEgg.Icon, -1, "Egg")
button.Visible = false
setBadge("!", "Highlight")
-- a gold ring breathing round it while the gift waits (as the Spin's does while spins wait)
local glow = Instance.new("Frame")
glow.Name = "Glow"
glow.BackgroundTransparency = 1
glow.AnchorPoint = Vector2.new(0.5, 0.5)
glow.Position = UDim2.fromScale(0.5, 0.5)
glow.Size = UDim2.new(1, 8, 1, 8)
glow.Parent = button
UiKit.corner(glow, 999)
local ring = Instance.new("UIStroke")
ring.Color = C.Highlight
ring.Thickness = 2.5
ring.Transparency = 0.2
ring.Parent = glow
TweenService:Create(ring, TweenInfo.new(1.1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Transparency = 0.85 }):Play()

-- ---------- the window ----------
local window = Hud.window({
    Name = "BetaGiftWindow", Title = "CHOOSE YOUR BETA GIFT", Size = Vector2.new(WIDTH, HEIGHT),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body

local choosePage = Instance.new("Frame")
choosePage.Name = "Choose"
choosePage.BackgroundTransparency = 1
choosePage.Size = UDim2.fromScale(1, 1)
choosePage.Parent = body
local intro = UiKit.label({
    Name = "Intro", Font = "Strong", TextSize = 13, TextColor3 = C.Text, TextWrapped = true,
    TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.new(1, 0, 0, 36), Parent = choosePage,
})
local row = Instance.new("Frame")
row.Name = "Cards"
row.BackgroundTransparency = 1
row.Parent = choosePage

local cards = {}
local busy = false
local claimed = nil -- the beast they took, once the server has said

local function petName(petId)
    return GameConfig.Pets[petId].DisplayName
end

local function firstSentence(text)
    return string.match(text or "", "^(.-[%.!?])%s") or text or ""
end

local function setBusy(on)
    busy = on
    for _, card in cards do
        card.choose.Active = not on
        card.choose:SetAttribute("Tone", if on then "Quiet" else "Go")
        card.choose.Text = if on then "..." else "CHOOSE"
    end
end

local function ask(petId)
    if busy or claimed then
        return
    end
    local name = petName(petId)
    local picture = Portraits.pet(petId, 72)
    ConfirmDialog.show({
        Title = "YOUR BETA GIFT",
        Text = "Take the " .. name .. "? You can only choose once.",
        Picture = picture, ConfirmText = "TAKE IT", ConfirmTone = "Go", CancelText = "NOT YET", Seconds = 2,
        OnConfirm = function()
            if busy or claimed or player:GetAttribute(ATTRIBUTE) ~= "Open" then
                return
            end
            setBusy(true)
            Event:FireServer("Claim", petId)
            task.delay(20, function() -- (no answer: the cards wake again)
                if busy and not claimed then
                    setBusy(false)
                end
            end)
        end,
    })
end

-- the portraits turn only while the window is open (they were started at load and never stopped: four RenderStepped loops for
-- the whole session on every client, offered the gift or not; bug audit, 2026-11-24)
local spinFrames = {} -- the choice cards' portraits
local stopSpins = {}
local function stopSpinning()
    for _, stop in stopSpins do
        stop()
    end
    table.clear(stopSpins)
end

for order, petId in BetaGift.PetIds do
    local pet = GameConfig.Pets[petId]
    local color = GameConfig.PetRarityColors[pet.Rarity] or C.Edge
    local card = UiKit.card({ Name = petId, Parent = row })
    UiKit.boldCard(card, color)
    card.LayoutOrder = order
    local portrait = Portraits.pet(petId, 140)
    portrait.Name = "Portrait"
    portrait.Parent = card
    table.insert(spinFrames, portrait)
    local name = UiKit.boldLabel({ Name = "PetName", Text = pet.DisplayName, TextSize = 16, TextColor3 = C.Text,
        TextWrapped = true, Parent = card })
    -- its rarity in the rarity's colour and its Qi bonus: on one line, or two beside a phone's portrait (layout)
    local rarityWord = string.format('<font color="#%s">%s</font>', color:ToHex(), string.upper(pet.Rarity))
    local bonus = "+" .. pet.QiBonus .. "% Qi"
    local what = UiKit.label({ Name = "What", Font = "Heavy", TextSize = 12, RichText = true, TextColor3 = C.Sky,
        TextYAlignment = Enum.TextYAlignment.Top, Parent = card })
    local lore = UiKit.label({ Name = "Lore", Font = "Body", TextSize = 11, TextColor3 = C.Muted, TextWrapped = true,
        Text = firstSentence(PetLore[petId] and PetLore[petId].Lore), TextYAlignment = Enum.TextYAlignment.Top, Parent = card })
    local choose = UiKit.button({ Name = "Choose", Tone = "Go", Text = "CHOOSE", TextSize = UiTheme.Text.Button, Parent = card })
    choose.Activated:Connect(function()
        if choose.Active then
            ask(petId)
        end
    end)
    cards[order] = { card = card, portrait = portrait, name = name, what = what, lore = lore, choose = choose,
        oneLine = rarityWord .. "  ·  " .. bonus, twoLines = rarityWord .. "\n" .. bonus }
end

-- ---------- after choosing ----------
local donePage = Instance.new("Frame")
donePage.Name = "Done"
donePage.BackgroundTransparency = 1
donePage.Size = UDim2.fromScale(1, 1)
donePage.Visible = false
donePage.Parent = body
local doneHolder = Instance.new("Frame") -- where the chosen beast's portrait goes
doneHolder.Name = "Beast"
doneHolder.BackgroundTransparency = 1
doneHolder.Parent = donePage
local doneText = Instance.new("Frame")
doneText.Name = "Words"
doneText.BackgroundTransparency = 1
doneText.Parent = donePage
local doneTitle = UiKit.boldLabel({ Name = "Headline", TextSize = 22, TextColor3 = C.Highlight, TextWrapped = true,
    Size = UDim2.new(1, 0, 0, 56), Parent = doneText })
local doneLine = UiKit.label({ Name = "Line", Font = "Strong", TextSize = 14, TextColor3 = C.Text, TextWrapped = true,
    Text = "Thank you for testing the game! Find it in your Pets window.", Parent = doneText })
local okButton = UiKit.button({ Name = "Great", Tone = "Go", Text = "GREAT!", Parent = doneText })

-- ---------- the layout, for the window's size (a phone's window is shorter: Hud.window fits it to the screen) ----------
local function layout()
    local width = window.Frame.Size.X.Offset - UiTheme.Pad.Window * 2
    local height = window.Frame.Size.Y.Offset - FRAME
    local tight = height < 300
    intro.Text = if tight then "Thank you for testing! Pick one Exclusive beast, free. You can only choose once."
        else "Thank you for testing the game! Pick one Exclusive beast to keep, free.\nYou can only choose once."
    intro.TextSize = if tight then 12 else 13
    local introHeight = if tight then 18 else 36
    intro.Size = UDim2.new(1, 0, 0, introHeight)
    local rowTop = introHeight + (if tight then UiTheme.Space.XS + 2 else UiTheme.Space.S)
    row.Position = UDim2.fromOffset(0, rowTop)
    row.Size = UDim2.new(1, 0, 1, -rowTop)
    local cardWidth = math.floor((width - GAP * 2) / 3)
    local cardHeight = height - rowTop
    local tall = cardHeight >= TALL_CARD
    for order, c in cards do
        c.card.Position = UDim2.fromOffset((order - 1) * (cardWidth + GAP), 0)
        c.card.Size = UDim2.fromOffset(cardWidth, cardHeight)
        c.choose.AnchorPoint = Vector2.new(0.5, 1)
        c.choose.Position = UDim2.new(0.5, 0, 1, -PAD)
        c.choose.Size = UDim2.new(1, -PAD * 2, 0, BUTTON)
        if tall then
            -- the beast on top, its words under it, CHOOSE at the foot
            local words = 20 + 4 + 16 + 6 + 30 + 8 + BUTTON + PAD -- name, rarity, lore, CHOOSE
            local side = math.max(60, math.min(cardWidth - PAD * 2, cardHeight - PAD - words - 6))
            c.portrait.AnchorPoint = Vector2.new(0.5, 0)
            c.portrait.Position = UDim2.new(0.5, 0, 0, PAD)
            c.portrait.Size = UDim2.fromOffset(side, side)
            local y = PAD + side + 6
            c.name.TextXAlignment = Enum.TextXAlignment.Center
            c.name.TextWrapped = false
            c.name.TextSize = 16
            c.name.Position = UDim2.fromOffset(PAD, y)
            c.name.Size = UDim2.new(1, -PAD * 2, 0, 20)
            c.what.Text = c.oneLine
            c.what.TextXAlignment = Enum.TextXAlignment.Center
            c.what.Position = UDim2.fromOffset(PAD, y + 24)
            c.what.Size = UDim2.new(1, -PAD * 2, 0, 16)
            c.lore.Visible = true
            c.lore.TextXAlignment = Enum.TextXAlignment.Center
            c.lore.Position = UDim2.fromOffset(PAD, y + 46)
            c.lore.Size = UDim2.new(1, -PAD * 2, 0, 30)
        else
            -- the beast at the left, its name and rarity beside it, CHOOSE at the foot (no room for the line about it)
            local side = math.max(48, math.min(math.floor(cardWidth * 0.42), cardHeight - BUTTON - PAD * 2 - 6))
            c.portrait.AnchorPoint = Vector2.new(0, 0)
            c.portrait.Position = UDim2.fromOffset(PAD, PAD)
            c.portrait.Size = UDim2.fromOffset(side, side)
            local x = PAD + side + 8
            c.name.TextXAlignment = Enum.TextXAlignment.Left
            c.name.TextWrapped = true
            c.name.TextSize = 14
            c.name.Position = UDim2.fromOffset(x, PAD)
            c.name.Size = UDim2.new(1, -(x + PAD - 2), 0, 36)
            c.what.Text = c.twoLines
            c.what.TextXAlignment = Enum.TextXAlignment.Left
            c.what.Position = UDim2.fromOffset(x, PAD + 40)
            c.what.Size = UDim2.new(1, -(x + PAD - 2), 0, 34)
            c.lore.Visible = false
        end
    end
    -- after choosing: the beast at the left, the words and GREAT! beside it
    local side = math.floor(math.min(height, width * 0.42))
    doneHolder.Position = UDim2.fromOffset(0, math.floor((height - side) / 2))
    doneHolder.Size = UDim2.fromOffset(side, side)
    local textX = side + GAP + 4
    doneText.Position = UDim2.fromOffset(textX, 0)
    doneText.Size = UDim2.new(1, -textX, 1, 0)
    doneTitle.TextSize = if tight then 18 else 22
    local titleHeight = if tight then 44 else 56
    doneTitle.Size = UDim2.new(1, 0, 0, titleHeight)
    doneLine.TextSize = if tight then 13 else 14
    local lineHeight = if tight then 34 else 40
    local top = math.max(0, math.floor((height - (titleHeight + 6 + lineHeight + 12 + BUTTON)) / 2))
    doneTitle.Position = UDim2.fromOffset(0, top)
    doneLine.Position = UDim2.fromOffset(0, top + titleHeight + 6)
    doneLine.Size = UDim2.new(1, 0, 0, lineHeight)
    local buttonY = math.min(height - BUTTON, top + titleHeight + 6 + lineHeight + 12)
    okButton.AnchorPoint = Vector2.new(0, 0)
    okButton.Position = UDim2.fromOffset(0, buttonY)
    okButton.Size = UDim2.new(0, math.min(220, math.floor(width - textX)), 0, BUTTON)
end
window.Frame:GetPropertyChangedSignal("Size"):Connect(layout)
layout()

-- ---------- the state, from the server ----------
local finished = false -- they chose and closed the window: nothing of this shows again
local function gone()
    finished = true
    button.Visible = false
    if window.isOpen() then
        window.close()
    end
end

local function refresh()
    if finished then
        return
    end
    local open = player:GetAttribute(ATTRIBUTE) == "Open"
    if claimed then
        button.Visible = false
    elseif open then
        button.Visible = true
    else
        -- not offered (already taken, or the beta is over): the button and the window go
        button.Visible = false
        if window.isOpen() and not busy then
            window.close()
        end
    end
end
player:GetAttributeChangedSignal(ATTRIBUTE):Connect(refresh)
refresh()

local function startSpinning()
    stopSpinning()
    for _, frame in spinFrames do
        table.insert(stopSpins, Portraits.spin(frame))
    end
    for _, frame in doneHolder:GetChildren() do
        if frame:IsA("ViewportFrame") then
            table.insert(stopSpins, Portraits.spin(frame))
        end
    end
end

local function showDone(petId)
    claimed = petId
    setBusy(false)
    choosePage.Visible = false
    donePage.Visible = true
    window.setTitle("YOUR BETA GIFT")
    doneTitle.Text = string.upper("The " .. petName(petId) .. " is yours!")
    for _, child in doneHolder:GetChildren() do
        child:Destroy()
    end
    local portrait = Portraits.pet(petId, 200)
    portrait.Size = UDim2.fromScale(1, 1)
    local edge = portrait:FindFirstChildOfClass("UIStroke")
    if edge then
        edge.Color = GameConfig.PetRarityColors[GameConfig.Pets[petId].Rarity] or C.Edge
        edge.Transparency = 0.1
        edge.Thickness = 2
    end
    portrait.Parent = doneHolder
    if window.Frame.Visible then
        startSpinning()
    end
    layout()
    refresh()
end

local function closeForGood()
    if claimed then
        gone()
    end
end
okButton.Activated:Connect(function()
    window.close()
end)

window.link(button)
button.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        window.open()
    end
end)
-- (a closed window after choosing never comes back: Hud.window's own close button and the round button both lead here)
local seen = false -- it has been open this visit: it doesn't open by itself after that
window.Frame:GetPropertyChangedSignal("Visible"):Connect(function()
    if window.Frame.Visible then
        seen = true
        startSpinning()
    else
        stopSpinning()
        closeForGood()
    end
end)

Event.OnClientEvent:Connect(function(kind, a, b)
    if kind == "Claimed" and BetaGift.isChoice(a) then
        local rarity = GameConfig.Pets[a].Rarity
        Sfx.play(if rarity == "Mythical" or rarity == "Secret" or rarity == "Divine" then "HatchReveal" .. rarity else "RewardClaim")
        message:show(if b == true then "Your Beta gift arrived: the " .. petName(a) .. " is in your Pets window."
            else "The " .. petName(a) .. " is yours! Find it in your Pets window.", "Reward",
            GameConfig.PetRarityColors[rarity])
        showDone(a)
        if not window.isOpen() then
            window.open()
        end
    elseif kind == "Refused" and typeof(a) == "string" then
        setBusy(false)
        Sfx.play("Error")
        message:show(a, "Error")
        refresh() -- (refused because it is no longer offered: the window and the button go)
    end
end)

-- ---------- opening by itself, once after joining ----------
-- only when nothing else is asking for the player: the tutorial's first step done (they have sat down once, and had a moment to
-- read the next), no notice showing (the Beta Tester title's comes on joining), no window, dialog or hatch on the screen
local joinedAt = os.clock()
local satDownAt = if player:GetAttribute("IsCultivating") == true then os.clock() else nil
player:GetAttributeChangedSignal("IsCultivating"):Connect(function()
    if player:GetAttribute("IsCultivating") == true and not satDownAt then
        satDownAt = os.clock()
    end
end)
local function tutorialInTheWay()
    if player:GetAttribute("SettingGuideMet") ~= true then
        return true -- (a new player has yet to talk to Seren the Guide: the tutorial follows that, and the gift after it)
    end
    local card = Hud.Banner:FindFirstChild("Tutorial")
    if not card then
        return player:GetAttribute("SettingTutorialDone") == nil -- (not known yet: it may still come)
    end
    return not (satDownAt and os.clock() - satDownAt > 6)
end
local function anyWindowOpen()
    local windows = playerGui:FindFirstChild("HudWindows")
    for _, child in if windows then windows:GetChildren() else {} do
        if child:IsA("GuiObject") and child.Visible then
            return true
        end
    end
    local dialog = playerGui:FindFirstChild("ConfirmDialog")
    return dialog ~= nil and dialog.Enabled
end
task.spawn(function()
    local quietSince = nil
    while not finished and not claimed and not seen do
        task.wait(0.5)
        if player:GetAttribute(ATTRIBUTE) == "Open" and os.clock() - joinedAt > 8 then
            local clear = not tutorialInTheWay() and not Toast.showing() and not anyWindowOpen() and not HatchCeremony.isPlaying()
            quietSince = if clear then (quietSince or os.clock()) else nil
            if quietSince and os.clock() - quietSince > 1.5 then
                window.open()
                return
            end
        end
    end
end)

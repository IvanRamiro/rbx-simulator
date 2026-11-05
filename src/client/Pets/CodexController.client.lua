-- The Spirit Beast Codex (the Codex button on the HUD's rail): a page for each egg, in the order they unlock,
-- and a page of rewards. A beast the player has never owned is a black silhouette and "???"; its rarity and the eggs that
-- hatch it still show, so there is something to hunt. Once discovered an
-- entry stays, whatever happens to the pet. Each page draws only its own few portraits.
-- The server owns the book (server/Pets/Codex, CodexEvent "State"); CodexEvent "Claim" asks for a reward.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PetLore = require(ReplicatedStorage:WaitForChild("PetLore"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Toast = require(UI:WaitForChild("Toast"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local CodexState = require(script.Parent:WaitForChild("CodexState"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local SpecialPreview = require(script.Parent:WaitForChild("SpecialPreview"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local LOST_PAGE, REWARDS_PAGE = "Lost", "Rewards"
local NAV_WIDTH = 176

local toggleButton, setBadge = Hud.railButton("CodexButton", UiTheme.Icons.Codex, "Codex", 2)
local message = Toast.new("CodexMessage", Color3.new(1, 1, 1), 3.5)

local found, claimed, owned = CodexState.found, CodexState.claimed, CodexState.owned
local fresh = {}     -- [petId] = true: discovered since the player last looked
local page = REWARDS_PAGE
local detailPet = nil -- the beast whose entry is open, or nil for the page
local stopSpin = nil  -- stops the open entry's turntable
local render -- below

local window = Hud.window({
    Name = "CodexWindow", Title = "SPIRIT BEAST CODEX", Size = Vector2.new(690, 450), AnchorPoint = Vector2.new(1, 0.5),
    Position = UDim2.new(1, -16, 0.5, 0), OnClose = function()
        if stopSpin then
            stopSpin()
            stopSpin = nil
        end
        if next(fresh) then
            fresh = {}
        end
    end,
})
local body = window.Body

toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        render()
        window.open()
    end
end)

-- ---------- the left column: progress and the pages ----------
local side = Instance.new("Frame")
side.Name = "Side"
side.BackgroundTransparency = 1
side.Size = UDim2.new(0, NAV_WIDTH, 1, 0)
side.Parent = body

local countLabel = UiKit.label({
    Name = "Count", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Text = "", Size = UDim2.new(1, 0, 0, 16), Parent = side,
})
local bar = UiKit.bar({ Name = "Progress", Position = UDim2.fromOffset(0, 19), Size = UDim2.new(1, -6, 0, 8), Parent = side })
local bonusLabel = UiKit.label({
    Name = "Bonus", Font = "Strong", TextSize = 11, TextColor3 = C.AccentBright, Text = "", Position = UDim2.fromOffset(0, 31),
    Size = UDim2.new(1, 0, 0, 14), Parent = side,
})
local nav = UiKit.scroll({ Name = "Pages", Position = UDim2.fromOffset(0, 50), Size = UDim2.new(1, 0, 1, -50), Parent = side })

local content = Instance.new("Frame")
content.Name = "Content"
content.BackgroundTransparency = 1
content.Position = UDim2.fromOffset(NAV_WIDTH + 10, 0)
content.Size = UDim2.new(1, -(NAV_WIDTH + 10), 1, 0)
content.Parent = body

local function clear(frame)
    for _, child in frame:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
end

local function claimableCount()
    local n = 0
    for _, reward in CodexRules.Rewards do
        if not claimed[reward.Id] and CodexRules.isEarned(reward, found) then
            n += 1
        end
    end
    return n
end

local function lostBeasts()
    local list = {}
    for petId in found do
        if #CodexRules.eggsOf(petId) == 0 then
            table.insert(list, petId)
        end
    end
    table.sort(list)
    return list
end

local function navRow(order, image, name, detail, detailColor, selected, onClick)
    local row = UiKit.button({
        Name = "Page", Text = "", Tone = if selected then "Accent" else "Quiet", LayoutOrder = order, Size = UDim2.new(1, 0, 0, 40), Parent = nav,
    })
    local icon = UiKit.icon(image, 30)
    icon.AnchorPoint = Vector2.new(0, 0.5)
    icon.Position = UDim2.new(0, 5, 0.5, 0)
    icon.Parent = row
    UiKit.label({
        Font = "Strong", TextSize = 12, Text = name, TextTruncate = Enum.TextTruncate.AtEnd, Position = UDim2.fromOffset(40, 4),
        Size = UDim2.new(1, -44, 0, 16), Parent = row,
    })
    UiKit.label({
        Font = "Strong", TextSize = 11, Text = detail, TextColor3 = detailColor or C.Muted, Position = UDim2.fromOffset(40, 21),
        Size = UDim2.new(1, -44, 0, 14), Parent = row,
    })
    row.Activated:Connect(onClick)
    return row
end

local function openPage(id)
    page, detailPet = id, nil
    render()
end

local function renderNav()
    clear(nav)
    local total = CodexRules.count(found)
    countLabel.Text = "DISCOVERED  " .. total .. " / " .. CodexRules.Total
    UiKit.setBar(bar, total / CodexRules.Total)
    bonusLabel.Text = "CODEX QI BONUS  +" .. CodexRules.qiPercent(claimed) .. "%"

    local waiting = claimableCount()
    navRow(0, UiTheme.Icons.Rewards, "Rewards", if waiting > 0 then waiting .. " to claim" else "Collection goals",
        if waiting > 0 then C.Highlight else nil, page == REWARDS_PAGE, function()
            openPage(REWARDS_PAGE)
        end)
    for index, egg in CodexRules.Eggs do
        local reward = CodexRules.reward("Set:" .. egg.Id)
        local have, goal = CodexRules.progress(reward, found)
        local ready = have >= goal and not claimed[reward.Id]
        navRow(index, UiTheme.EggIcons[egg.Id], egg.DisplayName, if ready then "Claim its reward" else have .. " / " .. goal,
            if ready then C.Highlight elseif have >= goal then C.AccentBright else nil, page == egg.Id, function()
                openPage(egg.Id)
            end)
    end
    if #lostBeasts() > 0 then
        navRow(#CodexRules.Eggs + 1, UiTheme.Icons.Relics, "Lost Lineages", "No egg holds these", nil, page == LOST_PAGE, function()
            openPage(LOST_PAGE)
        end)
    end
end

-- ---------- a claim button ----------
local function claimButton(parent, reward, position, anchor)
    local earned = CodexRules.isEarned(reward, found)
    local text = if claimed[reward.Id] then "CLAIMED" elseif earned then "CLAIM" else "LOCKED"
    local button = UiKit.button({
        Name = "Claim", Font = "Strong", TextSize = 12, Text = text, Tone = if earned and not claimed[reward.Id] then "Primary" else "Quiet",
        Active = earned and not claimed[reward.Id], AnchorPoint = anchor, Position = position, Size = UDim2.fromOffset(84, 30), Parent = parent,
    })
    if earned and not claimed[reward.Id] then
        button.Activated:Connect(function()
            RemoteEvents.CodexEvent:FireServer("Claim", reward.Id)
        end)
    end
    return button
end

local function rewardText(reward)
    local stones = CodexRules.stones(reward, Shop.playerRealmIndex(Players.LocalPlayer))
    local text = NumberFormat.compact(stones) .. " Stones"
    if reward.QiPercent > 0 then
        text = "+" .. reward.QiPercent .. "% Qi forever  ·  " .. text
    end
    return text
end

-- ---------- the rewards page ----------
local function renderRewards()
    UiKit.label({
        Font = "Title", TextSize = 16, Text = "Collection Rewards", Size = UDim2.new(1, 0, 0, 20), Parent = content,
    })
    UiKit.label({
        TextSize = 12, TextColor3 = C.Muted, Text = "Every beast you discover stays in the Codex, even after you sell or fuse it.",
        Position = UDim2.fromOffset(0, 21), Size = UDim2.new(1, 0, 0, 16), TextTruncate = Enum.TextTruncate.AtEnd, Parent = content,
    })
    local list = UiKit.scroll({ Name = "Rewards", Position = UDim2.fromOffset(0, 42), Size = UDim2.new(1, 0, 1, -42), Parent = content })
    local function row(order, reward, title)
        local have, goal = CodexRules.progress(reward, found)
        local card = UiKit.card({
            Name = "Reward", LayoutOrder = order, Size = UDim2.new(1, 0, 0, 58),
            Stripe = if claimed[reward.Id] then C.EdgeDim elseif have >= goal then C.Highlight else C.Accent, Parent = list,
        })
        UiKit.label({
            Font = "Strong", TextSize = 13, Text = title, Position = UDim2.fromOffset(12, 6), Size = UDim2.new(1, -112, 0, 16),
            TextTruncate = Enum.TextTruncate.AtEnd, Parent = card,
        })
        UiKit.label({
            Font = "Strong", TextSize = 11, Text = rewardText(reward), TextColor3 = C.AccentBright, Position = UDim2.fromOffset(12, 23),
            Size = UDim2.new(1, -112, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = card,
        })
        local track = UiKit.bar({ Position = UDim2.fromOffset(12, 42), Size = UDim2.new(1, -160, 0, 7), Parent = card })
        UiKit.setBar(track, math.min(1, have / goal), true)
        UiKit.label({
            Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = math.min(have, goal) .. " / " .. goal, AnchorPoint = Vector2.new(1, 0),
            Position = UDim2.new(1, -100, 0, 38), Size = UDim2.fromOffset(44, 14), TextXAlignment = Enum.TextXAlignment.Right, Parent = card,
        })
        claimButton(card, reward, UDim2.new(1, -8, 0.5, 0), Vector2.new(1, 0.5))
    end
    -- what can be taken comes first, what's been taken last
    local function rank(reward)
        if claimed[reward.Id] then
            return 2
        end
        return if CodexRules.isEarned(reward, found) then 0 else 1
    end
    local rewards = {}
    for index, reward in CodexRules.Rewards do
        table.insert(rewards, { reward = reward, index = index })
    end
    table.sort(rewards, function(a, b)
        if rank(a.reward) ~= rank(b.reward) then
            return rank(a.reward) < rank(b.reward)
        end
        return a.index < b.index
    end)
    for order, entry in rewards do
        local reward = entry.reward
        local title = if reward.Kind == "Set" then "Complete the " .. GameConfig.Eggs[reward.EggId].DisplayName .. " page"
            elseif reward.Count == CodexRules.Total then "Discover every beast"
            else "Discover " .. reward.Count .. " beasts"
        row(order, reward, title)
    end
end

-- ---------- a page of beasts ----------
local function beastCard(parent, petId, order)
    local info = GameConfig.Pets[petId]
    local known = found[petId] == true
    local color = GameConfig.PetRarityColors[info.Rarity] or C.Text
    local card = UiKit.card({ Name = "Beast", LayoutOrder = order, Stripe = if known then color else nil, Parent = parent })
    local picture = if known then Portraits.pet(petId, 76) else Portraits.silhouette(petId, 76)
    picture.AnchorPoint = Vector2.new(0.5, 0)
    picture.Position = UDim2.new(0.5, 1, 0, 6)
    picture.Parent = card
    UiKit.label({
        Font = "Strong", TextSize = 11, Text = if known then info.DisplayName else "???", TextXAlignment = Enum.TextXAlignment.Center,
        TextWrapped = true, Position = UDim2.fromOffset(5, 84), Size = UDim2.new(1, -8, 0, 28), Parent = card,
    })
    local tag = UiKit.tag(info.Rarity, color)
    tag.AnchorPoint = Vector2.new(0.5, 1)
    tag.Position = UDim2.new(0.5, 1, 1, -5)
    tag.Parent = card
    if fresh[petId] then
        local new = UiKit.tag("New", C.Highlight)
        new.Position = UDim2.fromOffset(6, 5)
        new.Parent = card
    end
    local have = owned[petId]
    if have and have.Count > 0 then
        local count = UiKit.tag("x" .. have.Count, C.AccentBright)
        count.AnchorPoint = Vector2.new(1, 0)
        count.Position = UDim2.new(1, -4, 0, 5)
        count.Parent = card
    end
    local press = Instance.new("TextButton")
    press.Name = "Open"
    press.Text = ""
    press.BackgroundTransparency = 1
    press.Size = UDim2.fromScale(1, 1)
    press.ZIndex = 4
    press.Parent = card
    press.Activated:Connect(function()
        Sfx.play("Open")
        detailPet = petId
        render()
    end)
    PetPreload.soon(petId)
end

local function beastGrid(top, pets)
    local grid = UiKit.scroll({ Name = "Beasts", Position = UDim2.fromOffset(0, top), Size = UDim2.new(1, 0, 1, -top), Parent = content })
    grid:FindFirstChildOfClass("UIListLayout"):Destroy()
    local layout = Instance.new("UIGridLayout")
    layout.CellSize = UDim2.fromOffset(110, 138)
    layout.CellPadding = UDim2.fromOffset(6, 6)
    layout.SortOrder = Enum.SortOrder.LayoutOrder
    layout.Parent = grid
    for order, petId in pets do
        beastCard(grid, petId, order)
    end
end

local function renderEgg(egg)
    local rank = Ranks.getRankById(egg.RequiredRank)
    local reward = CodexRules.reward("Set:" .. egg.Id)
    local have, goal = CodexRules.progress(reward, found)
    local icon = UiKit.icon(UiTheme.EggIcons[egg.Id], 46)
    icon.Parent = content
    UiKit.label({
        Font = "Title", TextSize = 16, Text = egg.DisplayName, Position = UDim2.fromOffset(54, 0), Size = UDim2.new(1, -150, 0, 20),
        TextTruncate = Enum.TextTruncate.AtEnd, Parent = content,
    })
    UiKit.label({
        TextSize = 12, TextColor3 = C.Muted, Position = UDim2.fromOffset(54, 20), Size = UDim2.new(1, -150, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd,
        Text = (if egg.Guardian then "Guarded by the " .. egg.Guardian.DisplayName .. "  ·  " else "") .. "Needs " .. (if rank then rank.Name else "?"),
        Parent = content,
    })
    UiKit.label({
        Font = "Strong", TextSize = 11, TextColor3 = C.AccentBright, Position = UDim2.fromOffset(54, 35), Size = UDim2.new(1, -150, 0, 14),
        Text = have .. " / " .. goal .. " found  ·  Full page: " .. rewardText(reward), TextTruncate = Enum.TextTruncate.AtEnd, Parent = content,
    })
    claimButton(content, reward, UDim2.new(1, -8, 0, 8), Vector2.new(1, 0))
    -- commonest first: the way the egg gives them
    local pets = {}
    local pool = table.clone(egg.Pool)
    table.sort(pool, function(a, b)
        return a.HatchChance > b.HatchChance
    end)
    for _, entry in pool do
        table.insert(pets, entry.PetId)
    end
    beastGrid(56, pets)
end

local function renderLost()
    UiKit.label({ Font = "Title", TextSize = 16, Text = "Lost Lineages", Size = UDim2.new(1, 0, 0, 20), Parent = content })
    UiKit.label({
        TextSize = 12, TextColor3 = C.Muted, Text = "Beasts no egg holds any more. They don't count toward the Codex's goals.",
        Position = UDim2.fromOffset(0, 21), Size = UDim2.new(1, 0, 0, 16), Parent = content,
    })
    beastGrid(44, lostBeasts())
end

-- ---------- one beast's entry ----------
local function renderEntry(petId)
    local info = GameConfig.Pets[petId]
    local lore = PetLore[petId] or {}
    local known = found[petId] == true
    local color = GameConfig.PetRarityColors[info.Rarity] or C.Text

    local back = UiKit.button({
        Name = "Back", Font = "Strong", TextSize = 12, Text = "< BACK", Tone = "Quiet", Size = UDim2.fromOffset(70, 26), Parent = content,
    })
    back.Activated:Connect(function()
        detailPet = nil
        render()
    end)

    local picture = if known then Portraits.pet(petId, 170) else Portraits.silhouette(petId, 170)
    picture.Position = UDim2.fromOffset(0, 34)
    picture.Parent = content
    stopSpin = Portraits.spin(picture)

    local tags = Instance.new("Frame")
    tags.Name = "Tags"
    tags.BackgroundTransparency = 1
    tags.Position = UDim2.fromOffset(0, 210)
    tags.Size = UDim2.fromOffset(170, 16)
    tags.Parent = content
    UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
    UiKit.tag(info.Rarity, color).Parent = tags
    local have = owned[petId]
    if have and have.Count > 0 then
        UiKit.tag("Owned x" .. have.Count, C.AccentBright).Parent = tags
    end

    local text = UiKit.scroll({ Name = "Entry", Position = UDim2.fromOffset(180, 0), Size = UDim2.new(1, -180, 1, 0), Parent = content })
    local order = 0
    local function line(props)
        order += 1
        props.LayoutOrder = order
        props.Parent = text
        props.AutomaticSize = Enum.AutomaticSize.Y
        props.Size = UDim2.new(1, 0, 0, 0)
        props.TextWrapped = true
        return UiKit.label(props)
    end
    local function heading(words)
        return line({ Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = string.upper(words) })
    end

    line({ Font = "Title", TextSize = 20, Text = if known then info.DisplayName else "???", TextColor3 = if known then color else C.Muted })
    if known then
        line({ Font = "Strong", TextSize = 12, TextColor3 = C.AccentBright,
            Text = info.Theme .. "  ·  +" .. info.QiBonus .. "% Qi"
                .. (if have and have.Level > 1 then "  ·  Your best: Level " .. have.Level .. " (+" .. PetRules.qiBonus(petId, have.Level) .. "%)" else "") })
        line({ TextSize = 13, Text = lore.Lore or "" })
    else
        line({ TextSize = 13, TextColor3 = C.Muted, Text = "This page is blank. Hatch this beast to fill it in." })
    end

    heading("Hatches from")
    local eggs = CodexRules.eggsOf(petId)
    if #eggs == 0 then
        line({ TextSize = 13, TextColor3 = C.Muted, Text = "No egg holds this beast any more." })
    else
        for _, entry in eggs do
            order += 1
            local row = Instance.new("Frame")
            row.BackgroundTransparency = 1
            row.LayoutOrder = order
            row.Size = UDim2.new(1, 0, 0, 26)
            row.Parent = text
            UiKit.icon(UiTheme.EggIcons[entry.EggId], 24).Parent = row
            UiKit.label({
                Font = "Strong", TextSize = 12, Text = GameConfig.Eggs[entry.EggId].DisplayName, Position = UDim2.fromOffset(30, 5),
                Size = UDim2.new(1, -80, 0, 16), TextTruncate = Enum.TextTruncate.AtEnd, Parent = row,
            })
            UiKit.label({
                Font = "Strong", TextSize = 12, TextColor3 = C.AccentBright, Text = entry.Percent .. "%", AnchorPoint = Vector2.new(1, 0),
                Position = UDim2.new(1, 0, 0, 5), Size = UDim2.fromOffset(50, 16), TextXAlignment = Enum.TextXAlignment.Right, Parent = row,
            })
        end
    end

    if lore.Special then
        heading("Special")
        if known then
            line({ Font = "Strong", TextSize = 14, TextColor3 = C.Highlight, Text = lore.Special.Name })
            line({ TextSize = 13, Text = lore.Special.Text })
            order += 1
            local watch = UiKit.button({
                Name = "Watch", Font = "Strong", TextSize = 12, Text = "WATCH IT", Tone = "Accent", LayoutOrder = order,
                Size = UDim2.fromOffset(110, 30), Parent = text,
            })
            watch.Activated:Connect(function()
                window.close()
                local started = SpecialPreview.play(petId, function(ok)
                    if not ok then
                        message:show("That special can't be shown right now.", Color3.new(1, 1, 1))
                    end
                    render()
                    window.open()
                end)
                if started then
                    message:show(lore.Special.Name, color)
                else
                    window.open()
                end
            end)
        else
            line({ TextSize = 13, TextColor3 = C.Muted, Text = "Unknown until discovered." })
        end
    end
end

-- ---------- drawing ----------
function render()
    if stopSpin then
        stopSpin()
        stopSpin = nil
    end
    clear(content)
    renderNav()
    if detailPet then
        renderEntry(detailPet)
    elseif page == REWARDS_PAGE then
        renderRewards()
    elseif page == LOST_PAGE then
        renderLost()
    else
        for _, egg in CodexRules.Eggs do
            if egg.Id == page then
                renderEgg(egg)
            end
        end
    end
end

local function updateBadge()
    local waiting = claimableCount()
    setBadge(if waiting > 0 then tostring(waiting) else nil, "Highlight")
end

CodexState.Changed:Connect(function(discovered)
    found, claimed, owned = CodexState.found, CodexState.claimed, CodexState.owned
    for _, petId in discovered do
        fresh[petId] = true
    end
    updateBadge()
    if window.isOpen() then
        render()
    end
end)

RemoteEvents.CodexEvent.OnClientEvent:Connect(function(action, data)
    if action == "Claimed" and typeof(data) == "table" then
        Sfx.play("RareReveal")
        UiFx.flash(window.Frame, C.Highlight)
        local text = "Claimed " .. NumberFormat.compact(data.Stones) .. " Spirit Stones"
        if data.QiPercent > 0 then
            text ..= " and +" .. data.QiPercent .. "% Qi forever"
        end
        message:show(text .. "!", C.Highlight)
    end
end)

found, claimed, owned = CodexState.found, CodexState.claimed, CodexState.owned
updateBadge()
render()

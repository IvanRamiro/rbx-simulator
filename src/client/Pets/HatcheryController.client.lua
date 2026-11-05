-- The Hatching Altar's window (Yggdrasil; PetService hatches): its prompt (attribute Hatchery) opens
-- a list of the eggs this player has carried home (player attributes "Egg_<EggId>", EggInventory),
-- each with its count and a Hatch button; an egg the player's rank can't hatch yet says which rank
-- it needs. One egg is hatched per press (HatchEggEvent); the window stays open to hatch the next,
-- and closes when the player walks away. The hatch itself plays on the altar (HatchCeremony, from
-- PetController's result).
-- Each egg opens to show exactly what it can hatch: every pet's rarity and its HatchChance as configured, the rarest
-- last. A beast not yet in the player's Codex stays a silhouette named "???", marked New; the rest show their name, Qi and how many they hold.
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Portraits = require(UI:WaitForChild("Portraits"))
local CodexState = require(script.Parent:WaitForChild("CodexState"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local LEAVE_MARGIN = 4 -- studs past the prompt's range the window closes: inside the server's own limit (its range + 6)
local BREAK_MARGIN = 0.15 -- seconds after the egg breaks that Hatch wakes, so a press never reaches a server still busy
local NO_ANSWER = GameConfig.HatchingAltar.Stage + 3 -- seconds Hatch waits for an answer that never came
local RARITY_ORDER = { Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }
local CARD_HEIGHT, ROW_HEIGHT = 70, 40

local altarPart = nil
local leaveDistance = 0
local resting = false -- an egg is in the cradle, or the server hasn't answered: Hatch waits
local press = 0 -- the latest press: a timer from an older one does nothing

-- at the screen's right edge, so the cradle (mid-screen behind the player) stays in sight
local window = Hud.window({
    Name = "HatcheryWindow", Title = "HATCHING ALTAR", Size = Vector2.new(380, 420), AnchorPoint = Vector2.new(1, 0.5),
    Position = UDim2.new(1, -UiTheme.Margin, 0.5, 0), OnClose = function()
        altarPart = nil
    end,
})
local hint = UiKit.label({ Name = "Hint", TextSize = 12, TextColor3 = C.Muted, Size = UDim2.new(1, 0, 0, 16), Parent = window.Body })
local list = UiKit.scroll({ Name = "Eggs", Position = UDim2.fromOffset(0, 24), Size = UDim2.new(1, 0, 1, -24), Parent = window.Body })

-- The eggs this player holds, in the order of GameConfig.Eggs' rank requirements.
local function heldEggs()
    local eggs = {}
    for eggId, egg in GameConfig.Eggs do
        local count = player:GetAttribute("Egg_" .. eggId)
        if typeof(count) == "number" and count > 0 then
            table.insert(eggs, { id = eggId, egg = egg, count = count, order = Ranks.getIndex(Ranks.getRankById(egg.RequiredRank).Name) or 0 })
        end
    end
    table.sort(eggs, function(a, b)
        return if a.order == b.order then a.id < b.id else a.order < b.order
    end)
    return eggs
end

-- the rarest pet an egg can hatch
local function bestOf(egg)
    local best
    for _, entry in egg.Pool do
        local pet = GameConfig.Pets[entry.PetId]
        if pet and (not best or (RARITY_ORDER[pet.Rarity] or 0) > (RARITY_ORDER[best.Rarity] or 0)) then
            best = pet
        end
    end
    return best
end

local render
local openEgg = nil -- the egg whose chances are showing; the first one held, until the player picks another

-- A HatchChance as it's configured, with no rounding: 2.5%, 0.05%.
local function percentText(chance)
    return string.format("%g%%", chance)
end

-- One pet the egg can hatch: its picture, name and tags, and its chance at the right.
local function oddsRow(parent, entry, order)
    local pet = GameConfig.Pets[entry.PetId]
    if not pet then
        return
    end
    local known = CodexState.found[entry.PetId] == true
    local color = GameConfig.PetRarityColors[pet.Rarity] or C.Text
    local row = Instance.new("Frame")
    row.Name = "Odds"
    row.BackgroundTransparency = 1
    row.LayoutOrder = order
    row.Size = UDim2.new(1, 0, 0, ROW_HEIGHT - 4)
    row.Parent = parent
    local picture = if known then Portraits.pet(entry.PetId, 36) else Portraits.silhouette(entry.PetId, 36)
    picture.Parent = row
    UiKit.label({
        Name = "PetName", Font = "Strong", TextSize = 12, Text = if known then pet.DisplayName else "???", TextTruncate = Enum.TextTruncate.AtEnd,
        TextColor3 = if known then C.Text else C.Muted, Position = UDim2.fromOffset(44, 1), Size = UDim2.new(1, -112, 0, 16), Parent = row,
    })
    local tags = Instance.new("Frame")
    tags.BackgroundTransparency = 1
    tags.Position = UDim2.fromOffset(44, 19)
    tags.Size = UDim2.new(1, -112, 0, 16)
    tags.Parent = row
    UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
    UiKit.tag(pet.Rarity, color).Parent = tags
    if known then
        local qi = UiKit.label({
            Font = "Strong", TextSize = 11, TextColor3 = C.AccentBright, Text = "+" .. pet.QiBonus .. "% Qi",
            AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 16), LayoutOrder = 1, Parent = tags,
        })
        qi.LayoutOrder = 1
        local have = CodexState.owned[entry.PetId]
        if have and have.Count > 0 then
            local count = UiKit.tag("Owned x" .. have.Count, C.Accent)
            count.LayoutOrder = 2
            count.Parent = tags
        end
    else
        local new = UiKit.tag("New", C.Highlight)
        new.LayoutOrder = 1
        new.Parent = tags
    end
    UiKit.label({
        Name = "Chance", Font = "Title", TextSize = 15, Text = percentText(entry.HatchChance), TextColor3 = color, AnchorPoint = Vector2.new(1, 0.5),
        Position = UDim2.new(1, 0, 0.5, 0), Size = UDim2.fromOffset(66, 20), TextXAlignment = Enum.TextXAlignment.Right, Parent = row,
    })
end

-- Hatch wakes after `seconds`, unless a later press has taken over
local function wake(seconds)
    local this = press
    task.delay(seconds, function()
        if this == press and resting then
            resting = false
            if window.isOpen() then
                render()
            end
        end
    end)
end

local function hatch(eggId)
    if resting then
        return
    end
    resting = true
    press += 1
    wake(NO_ANSWER)
    RemoteEvents.HatchEggEvent:FireServer(eggId)
    render()
end

function render()
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
    local eggs = heldEggs()
    hint.Text = if #eggs == 0 then "" elseif resting then "The egg rests in the cradle..." else "Lay an egg in the cradle to hatch it. The odds below are exact."
    if #eggs == 0 then
        UiKit.empty(list, "No eggs yet.\nWeaken a guardian, take an egg from its stands, and carry it home.")
        return
    end
    -- the first egg opens by itself, so the odds are seen without looking for them; false: the player closed it
    if openEgg == nil then
        openEgg = eggs[1].id
    end
    local rankName = Ranks.getPlayerRankName(player)
    for index, entry in eggs do
        local open = rankName ~= "" and Ranks.isAtLeast(rankName, entry.egg.RequiredRank)
        local showing = openEgg == entry.id
        local height = CARD_HEIGHT + (if showing then #entry.egg.Pool * ROW_HEIGHT + 8 else 0)
        local card = UiKit.card({ Name = "EggCard", LayoutOrder = index, Size = UDim2.new(1, 0, 0, height), Parent = list })
        local icon = UiKit.icon(UiTheme.EggIcons[entry.id] or UiTheme.Icons.Hatch, 44, if open then "Accent" else "Danger")
        icon.Position = UDim2.fromOffset(12, 13)
        icon.Parent = card
        UiKit.label({
            Name = "EggName", Font = "Title", TextSize = 15, Text = entry.egg.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
            Position = UDim2.fromOffset(66, 9), Size = UDim2.new(1, -170, 0, 18), Parent = card,
        })
        local tags = Instance.new("Frame")
        tags.BackgroundTransparency = 1
        tags.Position = UDim2.fromOffset(66, 30)
        tags.Size = UDim2.new(1, -170, 0, 16)
        tags.Parent = card
        UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
        UiKit.tag("x" .. entry.count, C.Accent).Parent = tags
        if not open then
            local needs = UiKit.tag("Needs " .. Ranks.getRankById(entry.egg.RequiredRank).Name, C.Danger)
            needs.LayoutOrder = 1
            needs.Parent = tags
        end
        local best = bestOf(entry.egg)
        if best then
            UiKit.label({
                Name = "Best", TextSize = 11, TextColor3 = C.Muted, Position = UDim2.fromOffset(66, 49),
                Size = UDim2.new(1, -170, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, RichText = true,
                Text = "Up to: " .. string.format('<font color="#%s">%s</font>', (GameConfig.PetRarityColors[best.Rarity] or C.Text):ToHex(), best.DisplayName),
                Parent = card,
            })
        end
        local button = UiKit.button({
            Name = "Hatch", Font = "Strong", TextSize = 13, Tone = "Accent", Text = if open then "HATCH" else "LOCKED",
            Active = open and not resting, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -10, 0, 8),
            Size = UDim2.fromOffset(90, 30), Parent = card,
        })
        local chances = UiKit.button({
            Name = "Chances", Font = "Strong", TextSize = 11, Tone = "Quiet", Text = if showing then "HIDE ODDS" else "SEE ODDS",
            AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -10, 0, 42), Size = UDim2.fromOffset(90, 22), Parent = card,
        })
        chances.Activated:Connect(function()
            openEgg = if showing then false else entry.id
            render()
        end)
        if showing then
            local rows = Instance.new("Frame")
            rows.Name = "Odds"
            rows.BackgroundTransparency = 1
            rows.Position = UDim2.fromOffset(12, CARD_HEIGHT + 2)
            rows.Size = UDim2.new(1, -22, 0, #entry.egg.Pool * ROW_HEIGHT)
            rows.Parent = card
            UiKit.list(rows, { Padding = UDim.new(0, 4) })
            -- likeliest first, the way the chances read down to the rarest
            local pool = table.clone(entry.egg.Pool)
            table.sort(pool, function(a, b)
                return a.HatchChance > b.HatchChance
            end)
            for order, poolEntry in pool do
                oddsRow(rows, poolEntry, order)
            end
        end
        if open then
            button.Activated:Connect(function()
                if button.Active then
                    hatch(entry.id)
                end
            end)
        end
    end
end

ProximityPromptService.PromptTriggered:Connect(function(prompt, who)
    if who ~= player or not prompt:GetAttribute("Hatchery") then
        return
    end
    altarPart = prompt.Parent
    leaveDistance = prompt.MaxActivationDistance + LEAVE_MARGIN
    window.open()
    render()
end)

-- the server's answer ends the wait: at once when it refused, when the egg breaks when it didn't
RemoteEvents.EggHatchResultEvent.OnClientEvent:Connect(function(result)
    if typeof(result) ~= "table" or not resting then
        return
    end
    press += 1
    if result.Reason or typeof(result.BreakAt) ~= "number" then
        wake(0)
    else
        wake(math.max(0, result.BreakAt - workspace:GetServerTimeNow()) + BREAK_MARGIN)
    end
end)

-- the list follows the egg inventory, and the player's rank (which eggs they can hatch), while the
-- window is open
player.AttributeChanged:Connect(function(name)
    if window.isOpen() and string.sub(name, 1, 4) == "Egg_" then
        render()
    end
end)
task.spawn(function()
    local leaderstats = player:WaitForChild("leaderstats", 60)
    local rank = leaderstats and leaderstats:WaitForChild("Rank", 60)
    if rank then
        rank.Changed:Connect(function()
            if window.isOpen() then
                render()
            end
        end)
    end
end)

CodexState.Changed:Connect(function()
    if window.isOpen() then
        render()
    end
end)

-- walking away closes the window, before the server would refuse a press from there
RunService.Heartbeat:Connect(function()
    if not window.isOpen() then
        return
    end
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root or not altarPart or (root.Position - altarPart.Position).Magnitude > leaveDistance then
        window.close()
    end
end)

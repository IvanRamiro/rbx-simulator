-- The Hatching Altar's window (Yggdrasil; PetService hatches): its prompt (attribute Hatchery) opens
-- a list of the eggs this player has carried home (player attributes "Egg_<EggId>", EggInventory),
-- each with its count and a Hatch button; an egg the player's rank can't hatch yet says which rank
-- it needs. One egg is hatched per press (HatchEggEvent); the window stays open to hatch the next,
-- and closes when the player walks away. The hatch itself plays on the altar (HatchCeremony, from
-- PetController's result).
-- Each egg opens to show exactly what it can hatch: every pet's rarity and its HatchChance as configured (with the Luck pass,
-- the player's own lucky odds, marked so: PassRules.luckyPool, as the server rolls them), the rarest
-- last. A beast not yet in the player's Codex stays a silhouette named "???", marked New; the rest show their name, Qi and how many they hold.
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Toast = require(UI:WaitForChild("Toast"))
local CodexState = require(script.Parent:WaitForChild("CodexState"))
local HatchCeremony = require(script.Parent:WaitForChild("HatchCeremony"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local LEAVE_MARGIN = 4 -- studs past the prompt's range the window closes: inside the server's own limit (its range + 6)
local REVEAL_SPARE = 0.6 -- seconds past the cinematic's own length the window waits for it to say it's done (HatchCeremony.Finished)
local BREAK_MARGIN = 0.15 -- seconds after the egg breaks that Hatch wakes, so a press never reaches a server still busy
local NO_ANSWER = GameConfig.HatchingAltar.Stage + 3 -- seconds Hatch waits for an answer that never came
local RARITY_ORDER = { Divine = 8, Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }
local CARD_HEIGHT, ROW_HEIGHT = 112, 42
local ODDS_ROWS_SHOWN = 5 -- the most odds rows an egg card shows at once: more scroll inside the card (the owner, 2026-11-16)
local LUCK_TAG = 26 -- the Luck pass's "your odds" tag over the rows
local BUTTONS = 104 -- the egg card's right column
local TEXT_RIGHT = BUTTONS + 12 + 8

local altarPart = nil
local leaveDistance = 0
local resting = false -- an egg is in the cradle, or the server hasn't answered: Hatch waits
local press = 0 -- the latest press: a timer from an older one does nothing

-- at the screen's right edge, so the cradle (mid-screen behind the player) stays in sight
local window = Hud.window({
    Name = "HatcheryWindow", Title = "HATCHING SANCTUM", Size = Vector2.new(420, 500), Side = true, AnchorPoint = Vector2.new(1, 0.5),
    Position = UDim2.new(1, -UiTheme.Margin, 0.5, 0), OnClose = function()
        altarPart = nil
    end,
})
local hint = UiKit.label({ Name = "Hint", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true,
    Size = UDim2.new(1, 0, 0, 18), Parent = window.Body })
local list = UiKit.scroll({ Name = "Eggs", Position = UDim2.fromOffset(0, 26), Size = UDim2.new(1, 0, 1, -26), Parent = window.Body })

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
    local best, bestId
    for _, entry in egg.Pool do
        local pet = GameConfig.Pets[entry.PetId]
        if pet and (not best or (RARITY_ORDER[pet.Rarity] or 0) > (RARITY_ORDER[best.Rarity] or 0)) then
            bestId = entry.PetId
            best = pet
        end
    end
    return best, bestId
end

local render
local openEgg = nil -- the egg whose chances are showing; the first one held, until the player picks another

-- A HatchChance to three figures: 2.5%, 0.05%, and a lucky 17.1% (every configured one shows exactly as it's configured).
local function percentText(chance)
    return string.format("%.3g%%", chance)
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
    local picture = if known then Portraits.pet(entry.PetId, 38) else Portraits.silhouette(entry.PetId, 38)
    picture.Parent = row
    local nameLabel = UiKit.label({
        Name = "PetName", Font = "Heavy", TextSize = 13, Text = if known then pet.DisplayName else "???", TextTruncate = Enum.TextTruncate.AtEnd,
        TextColor3 = if known then C.Text else C.Muted, Position = UDim2.fromOffset(48, 0), Size = UDim2.new(1, -120, 0, 18), Parent = row,
    })
    UiKit.outline(nameLabel, 1)
    local tags = Instance.new("Frame")
    tags.BackgroundTransparency = 1
    tags.Position = UDim2.fromOffset(48, 20)
    tags.Size = UDim2.new(1, -120, 0, 18)
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
    UiKit.boldLabel({
        Name = "Chance", TextSize = 16, Text = percentText(entry.HatchChance), TextColor3 = color, AnchorPoint = Vector2.new(1, 0.5),
        Position = UDim2.new(1, -4, 0.5, 0), Size = UDim2.fromOffset(70, 20), TextXAlignment = Enum.TextXAlignment.Right, Parent = row,
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
    hint.Text = if #eggs == 0 then "" elseif resting then "Your egg is hatching..." else "Press HATCH to hatch an egg. The odds below are exact."
    if #eggs == 0 then
        UiKit.empty(list, "No eggs yet.\nHit a guardian until it is weak, take an egg from its stands, and carry it home.")
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
        -- the odds' own height: every row (and the luck tag), but never more than ODDS_ROWS_SHOWN rows: the rest scroll. The card
        -- is sized for exactly that, so the odds never spill over the next card (they did: the luck tag wasn't counted)
        local luck = PassRules.luck(Players.LocalPlayer)
        local oddsContent = #entry.egg.Pool * ROW_HEIGHT + (if luck > 1 then LUCK_TAG else 0) + 6 -- (+ the scroll's own padding)
        local oddsHeight = math.min(oddsContent, ODDS_ROWS_SHOWN * ROW_HEIGHT)
        local height = CARD_HEIGHT + (if showing then oddsHeight + 12 else 0)
        local card = UiKit.boldCard(UiKit.card({ Name = "EggCard", LayoutOrder = index, Size = UDim2.new(1, 0, 0, height), Parent = list }),
            if open then C.Edge else C.EdgeDim)
        local icon = UiKit.icon(UiTheme.EggIcons[entry.id] or UiTheme.Icons.Hatch, 56, if open then "Accent" else "Danger")
        icon.Position = UDim2.fromOffset(12, 12)
        icon.Parent = card
        UiKit.boldLabel({
            Name = "EggName", TextSize = UiTheme.Text.CardTitle, Text = entry.egg.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
            Position = UDim2.fromOffset(80, 12), Size = UDim2.new(1, -(80 + TEXT_RIGHT), 0, 20), Parent = card,
        })
        local tags = Instance.new("Frame")
        tags.BackgroundTransparency = 1
        tags.Position = UDim2.fromOffset(80, 36)
        tags.Size = UDim2.new(1, -(80 + TEXT_RIGHT), 0, 18)
        tags.Parent = card
        UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 4), VerticalAlignment = Enum.VerticalAlignment.Center })
        UiKit.tag("x" .. entry.count, C.Accent).Parent = tags
        if not open then
            local needs = UiKit.tag("Needs " .. Ranks.getRankById(entry.egg.RequiredRank).Name, C.Danger)
            needs.LayoutOrder = 1
            needs.Parent = tags
        end
        local best, bestId = bestOf(entry.egg)
        if best then
            UiKit.label({
                Name = "Best", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Position = UDim2.fromOffset(80, 58),
                Size = UDim2.new(1, -(80 + TEXT_RIGHT), 0, 16), TextTruncate = Enum.TextTruncate.AtEnd, RichText = true,
                Text = "Up to: " .. string.format('<font color="#%s">%s</font>', (GameConfig.PetRarityColors[best.Rarity] or C.Text):ToHex(),
                    if CodexState.found[bestId] then best.DisplayName else "???"), -- an undiscovered beast keeps its name
                Parent = card,
            })
        end
        -- the right column: HATCH (green, the action) over the odds toggle
        local button = UiKit.button({
            Name = "Hatch", TextSize = 15, Tone = "Go", Text = if open then "HATCH" else "LOCKED", Active = open and not resting,
            AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 12), Size = UDim2.fromOffset(BUTTONS, UiTheme.Height.Button),
            Parent = card,
        })
        local chances = UiKit.button({
            Name = "Chances", TextSize = 12, Tone = "Quiet", Text = if showing then "HIDE ODDS" else "SEE ODDS",
            AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 12 + UiTheme.Height.Button + UiTheme.Space.XS),
            Size = UDim2.fromOffset(BUTTONS, UiTheme.Height.ButtonSmall), Parent = card,
        })
        chances.Activated:Connect(function()
            openEgg = if showing then false else entry.id
            render()
        end)
        if showing then
            local rows = UiKit.scroll({
                Name = "Odds", Position = UDim2.fromOffset(12, CARD_HEIGHT), Size = UDim2.new(1, -22, 0, oddsHeight), Parent = card,
            })
            rows.ScrollingEnabled = oddsContent > oddsHeight
            rows.ScrollBarThickness = if oddsContent > oddsHeight then 4 else 0
            rows:FindFirstChildOfClass("UIListLayout").Padding = UDim.new(0, 4)
            if luck > 1 then -- the Luck pass: these are their own odds, and say so
                local lucky = UiKit.tag(luck .. "x luck: your odds", C.Highlight)
                lucky.LayoutOrder = 0
                lucky.Parent = rows
            end
            -- likeliest first, the way the chances read down to the rarest
            local pool = PassRules.luckyPool(entry.egg.Pool, luck)
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

local function withinReach()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return root ~= nil and altarPart ~= nil and (root.Position - altarPart.Position).Magnitude <= leaveDistance
end

-- the server's answer ends the wait: at once when it refused, when the egg breaks when it didn't
RemoteEvents.EggHatchResultEvent.OnClientEvent:Connect(function(result)
    if typeof(result) ~= "table" or not resting then
        return
    end
    press += 1
    if result.Reason or typeof(result.BreakAt) ~= "number" then
        wake(0)
    else
        local untilBroken = math.max(0, result.BreakAt - workspace:GetServerTimeNow()) + BREAK_MARGIN
        wake(untilBroken)
        -- the window steps aside so the egg can be seen breaking, and comes back if there are more to hatch
        if window.isOpen() then
            local part, reach = altarPart, leaveDistance -- closing forgets the altar
            window.close()
            local this = press
            -- it comes back as soon as the cinematic ends (a tap on the card ends it early: repeats stay quick), or, should that never
            -- be heard, once the cinematic's own length for this result has passed (a grand or Giant reveal stays longer)
            local back = false
            local ended
            local function comeBack()
                if back then
                    return
                end
                back = true
                if ended then
                    ended:Disconnect()
                end
                if this ~= press or window.isOpen() or #heldEggs() == 0 then
                    return
                end
                altarPart, leaveDistance = part, reach
                if withinReach() then
                    window.open()
                    render()
                else
                    altarPart = nil
                end
            end
            ended = HatchCeremony.Finished:Connect(function(breakAt)
                if breakAt == result.BreakAt then -- (this hatch's cinematic, not the one it cut short)
                    comeBack()
                end
            end)
            task.delay(untilBroken + HatchCeremony.afterBreak(result) + REVEAL_SPARE, comeBack)
        end
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

-- another player's hatch, heard by anyone near the Sanctum: their egg breaks in the cradle (PetService stages it, with who hatches
-- it, its rarity and when it breaks), quieter than the hatcher's own; a grand one carries further. The staged egg reaches every
-- player (it streams as Persistent), so the top rarities are told to the whole server as it breaks: a short notice in the rarity's
-- colour (the big pet games do the same: a rare pull is a public event)
local GRAND = { Legendary = true, Mythical = true, Secret = true, Divine = true }
local ANNOUNCED = { Mythical = true, Secret = true, Divine = true }
local news = Toast.new("HatchNews", nil, 5)
workspace.DescendantAdded:Connect(function(egg)
    if egg.Name ~= "HatchingEgg" or not egg:IsA("Model") or egg:GetAttribute("HatcherId") == player.UserId then
        return
    end
    local breakAt = egg:GetAttribute("BreakAt")
    if typeof(breakAt) ~= "number" then
        return
    end
    local at = egg:GetPivot().Position
    local rarity = egg:GetAttribute("Rarity")
    local untilBreak = math.max(0, breakAt - workspace:GetServerTimeNow())
    Sfx.after(untilBreak, if GRAND[rarity] then "HatchNearbyGrand" else "HatchNearby", at)
    local hatcher = Players:GetPlayerByUserId(egg:GetAttribute("HatcherId") or 0)
    if ANNOUNCED[rarity] and hatcher then
        task.delay(untilBreak, function()
            if hatcher.Parent then
                news:show(hatcher.DisplayName .. " just hatched a " .. string.upper(rarity) .. " beast!", "Info",
                    GameConfig.PetRarityColors[rarity])
            end
        end)
    end
end)

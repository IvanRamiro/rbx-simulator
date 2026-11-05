-- The Hatching Altar's window (Yggdrasil; PetService hatches): its prompt (attribute Hatchery) opens
-- a list of the eggs this player has carried home (player attributes "Egg_<EggId>", EggInventory),
-- each with its count and a Hatch button; an egg the player's rank can't hatch yet says which rank
-- it needs. One egg is hatched per press (HatchEggEvent); the window stays open to hatch the next,
-- and closes when the player walks away. The hatch itself plays on the altar (HatchCeremony, from
-- PetController's result).
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

local player = Players.LocalPlayer
local C = UiTheme.Colors

local LEAVE_MARGIN = 4 -- studs past the prompt's range the window closes: inside the server's own limit (its range + 6)
local BREAK_MARGIN = 0.15 -- seconds after the egg breaks that Hatch wakes, so a press never reaches a server still busy
local NO_ANSWER = GameConfig.HatchingAltar.Stage + 3 -- seconds Hatch waits for an answer that never came
local RARITY_ORDER = { Secret = 7, Mythical = 6, Legendary = 5, Epic = 4, Rare = 3, Uncommon = 2, Common = 1 }

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
    hint.Text = if #eggs == 0 then "" elseif resting then "The egg rests in the cradle..." else "Lay an egg in the cradle to hatch it."
    if #eggs == 0 then
        UiKit.empty(list, "No eggs yet.\nWeaken a guardian, take an egg from its stands, and carry it home.")
        return
    end
    local rankName = Ranks.getPlayerRankName(player)
    for index, entry in eggs do
        local open = rankName ~= "" and Ranks.isAtLeast(rankName, entry.egg.RequiredRank)
        local card = UiKit.card({ Name = "EggCard", LayoutOrder = index, Size = UDim2.new(1, 0, 0, 70), Parent = list })
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
            Active = open and not resting, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -10, 0.5, 0),
            Size = UDim2.fromOffset(90, 32), Parent = card,
        })
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

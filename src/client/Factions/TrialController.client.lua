-- The faction trials, as the player sees them (shared/TrialRules; server/Factions/TrialService decides every result and this only draws what the server says).
--   THE BANNER (top centre, Hud.Banner) while the player's "FactionTrial" attribute says "Running": the trial's name in its faction's colour, the time left (from
--   "FactionTrialEnds", the server's clock) and how far they have got ("FactionTrialText", with a bar). A trial of tokens also lists its clues, and strikes out the ones taken.
--   THE GATES of the Orthodox trial carry their number over them in the world; the one that is due next shines (the others sit quiet), so the order is never a guess.
--   THE TOKENS of the Unorthodox trial offer their prompt only while the player's trial runs and only if they have not taken that one (a prompt is a local thing: the server
--   checks every take itself), so nobody wanders into the hidden places and finds a button waiting.
--   THE ARENA'S DUMMIES (TrialDummy) carry a bar over their head of the blows they have left.
--   THE ENDING: the server's "TrialNote" (a token taken, a wave up, a gate skipped) is a notification; "TrialResult" is a big banner when the trial is passed and a notice when not.
--   THE VAULT: when the server says "Taken" (FactionController tells the player what they took), a burst of light stands at the vault they stand by.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local FactionRules = require(ReplicatedStorage:WaitForChild("FactionRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local client = script.Parent.Parent
local UI = client:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(client:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local C = UiTheme.Colors
local Event = RemoteEvents.FactionEvent
local config = GameConfig.Faction

local message = Toast.new("TrialMessage", C.Highlight, 5)
local GATE_DONE = Color3.fromRGB(111, 212, 154)

local function serverNow()
    return workspace:GetServerTimeNow()
end

local function running()
    return player:GetAttribute("FactionTrial") == "Running"
end

local function factionInfo()
    local id = FactionRules.of(player)
    return id, id and config.Factions[id]
end

local function formatTime(seconds)
    seconds = math.max(0, math.ceil(seconds))
    return string.format("%d:%02d", seconds // 60, seconds % 60)
end

-- ---------- the banner ----------
local compact = Hud.isCompact()
local banner = UiKit.panel({
    Name = "TrialBanner", Brackets = false, Size = UDim2.fromOffset(if compact then 290 else 340, 62), LayoutOrder = -12, Visible = false, Parent = Hud.Banner,
})
local bannerName = UiKit.boldLabel({
    Name = "Name", TextSize = 15, Position = UDim2.fromOffset(14, 6), Size = UDim2.new(1, -110, 0, 20), TextTruncate = Enum.TextTruncate.AtEnd, Parent = banner,
})
local bannerTime = UiKit.boldLabel({
    Name = "Time", TextSize = 20, TextXAlignment = Enum.TextXAlignment.Right, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -14, 0, 4),
    Size = UDim2.fromOffset(90, 24), Parent = banner,
})
local bannerText = UiKit.label({
    Name = "Progress", Font = "Strong", TextSize = 14, TextColor3 = C.Text, Position = UDim2.fromOffset(14, 28), Size = UDim2.new(1, -28, 0, 16), TextTruncate = Enum.TextTruncate.AtEnd, Parent = banner,
})
local timeBar = UiKit.bar({ Name = "TimeBar", AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 14, 1, -7), Size = UDim2.new(1, -28, 0, 6), Parent = banner })

local clues = UiKit.panel({
    Name = "TrialClues", Brackets = false, Size = UDim2.fromOffset(if compact then 290 else 340, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = -11,
    Visible = false, Parent = Hud.Banner,
})
UiKit.padding(clues, 12, 8)
UiKit.list(clues, { Padding = UDim.new(0, 2), SortOrder = Enum.SortOrder.LayoutOrder })
local clueRows = {}
do
    local trial = config.Factions.Unorthodox.Trial
    local heading = UiKit.label({
        Name = "Heading", Font = "Heavy", TextSize = 12, TextColor3 = C.Highlight, Text = "THE ELDER'S CLUES  -  FIND ANY " .. trial.Need,
        Size = UDim2.new(1, 0, 0, 16), LayoutOrder = 0, Parent = clues,
    })
    heading.TextTruncate = Enum.TextTruncate.AtEnd
    for index, clue in trial.Clues do
        clueRows[index] = UiKit.label({
            Name = "Clue" .. index, Font = "Strong", TextSize = if compact then 12 else 13, TextWrapped = true, RichText = true, AutomaticSize = Enum.AutomaticSize.Y,
            Size = UDim2.new(1, 0, 0, 0), LayoutOrder = index, Text = index .. ". " .. clue, Parent = clues,
        })
    end
end

local function takenSet()
    local set = {}
    local list = player:GetAttribute("FactionTrialTaken")
    if typeof(list) == "string" then
        for number in string.gmatch(list, "%d+") do
            set[tonumber(number)] = true
        end
    end
    return set
end

local function refreshClues()
    local id = FactionRules.of(player)
    clues.Visible = running() and id == "Unorthodox"
    if not clues.Visible then
        return
    end
    local taken = takenSet()
    for index, row in clueRows do
        local clue = config.Factions.Unorthodox.Trial.Clues[index]
        if taken[index] then
            row.Text = string.format('<font color="#%s"><s>%d. %s</s>  (found)</font>', GATE_DONE:ToHex(), index, clue)
        else
            row.Text = string.format("%d. %s", index, clue)
        end
    end
end

local function refreshBanner()
    local _, info = factionInfo()
    local show = running() and info ~= nil
    banner.Visible = show
    if not show then
        refreshClues()
        return
    end
    bannerName.Text = string.upper(info.Trial.Name)
    bannerName.TextColor3 = info.Color
    local text = player:GetAttribute("FactionTrialText")
    bannerText.Text = if typeof(text) == "string" then text else ""
    refreshClues()
end

local lastWhole = nil
RunService.Heartbeat:Connect(function()
    if not banner.Visible then
        lastWhole = nil
        return
    end
    local _, info = factionInfo()
    local ends = player:GetAttribute("FactionTrialEnds")
    if not info or typeof(ends) ~= "number" then
        return
    end
    local left = ends - serverNow()
    bannerTime.Text = formatTime(left)
    bannerTime.TextColor3 = if left <= 15 then C.Danger else C.Text
    local whole = math.max(0, math.ceil(left))
    if whole ~= lastWhole then
        lastWhole = whole
        UiKit.setBar(timeBar, math.clamp(left / info.Trial.Seconds, 0, 1), true)
        UiKit.setBarColor(timeBar, if left <= 15 then C.Danger else info.Color)
    end
end)

for _, name in { "FactionTrial", "FactionTrialText", "FactionTrialTaken", "Faction" } do
    player:GetAttributeChangedSignal(name):Connect(refreshBanner)
end
refreshBanner()

-- ---------- the gates' numbers ----------
local gateBadges = {} -- [zone] = { label, stroke }

local function paintGates()
    local id = FactionRules.of(player)
    local due = if running() and id == "Orthodox" then (player:GetAttribute("FactionTrialDone") or 0) + 1 else nil
    for zone, badge in gateBadges do
        local index = zone:GetAttribute("Index")
        local info = config.Factions.Orthodox
        local color, transparency
        if due == nil then
            color, transparency = C.Text, 0.35
        elseif index < due then
            color, transparency = GATE_DONE, 0.45
        elseif index == due then
            color, transparency = info.Color, 0
        else
            color, transparency = C.Muted, 0.35
        end
        badge.Label.TextColor3 = color
        badge.Label.TextTransparency = transparency
        badge.Stroke.Color = color
        badge.Stroke.Transparency = math.clamp(transparency + 0.1, 0, 1)
        badge.Frame.Size = if index == due then UDim2.fromScale(1, 1) else UDim2.fromScale(0.8, 0.8)
    end
end

local function addGate(zone)
    if gateBadges[zone] or not zone:IsA("BasePart") then
        return
    end
    local gui = Instance.new("BillboardGui")
    gui.Name = "GateNumber"
    gui.Adornee = zone
    gui.Size = UDim2.fromOffset(84, 84)
    -- (the zone's middle is 2 studs under half its height over the ground; the number hangs at the BadgeHeight the builder gives over the ground)
    gui.StudsOffsetWorldSpace = Vector3.new(0, (zone:GetAttribute("BadgeHeight") or 20) - (zone.Size.Y / 2 - 2), 0)
    gui.AlwaysOnTop = false
    gui.LightInfluence = 0
    gui.MaxDistance = 260
    gui.Parent = zone
    local frame = Instance.new("Frame")
    frame.Name = "Badge"
    frame.AnchorPoint = Vector2.new(0.5, 0.5)
    frame.Position = UDim2.fromScale(0.5, 0.5)
    frame.Size = UDim2.fromScale(0.8, 0.8)
    frame.BackgroundColor3 = C.Panel
    frame.BackgroundTransparency = 0.25
    frame.BorderSizePixel = 0
    frame.Parent = gui
    UiKit.corner(frame, 42)
    local edge = UiKit.stroke(frame, C.Text, 0.4, 3)
    local label = UiKit.boldLabel({
        Name = "Number", Font = "Heavy", TextScaled = true, TextXAlignment = Enum.TextXAlignment.Center, Text = tostring(zone:GetAttribute("Index")),
        Size = UDim2.fromScale(1, 1), Parent = frame,
    })
    local limit = Instance.new("UITextSizeConstraint")
    limit.MaxTextSize = 44
    limit.Parent = label
    gateBadges[zone] = { Label = label, Stroke = edge, Frame = frame }
    paintGates()
end

for _, zone in CollectionService:GetTagged(FactionRules.GateTag) do
    addGate(zone)
end
CollectionService:GetInstanceAddedSignal(FactionRules.GateTag):Connect(addGate)
CollectionService:GetInstanceRemovedSignal(FactionRules.GateTag):Connect(function(zone)
    gateBadges[zone] = nil
end)
for _, name in { "FactionTrial", "FactionTrialDone", "Faction" } do
    player:GetAttributeChangedSignal(name):Connect(paintGates)
end

-- ---------- the tokens' prompts ----------
local tokenPrompts = {} -- [token model] = its prompt

local function paintTokens()
    local id = FactionRules.of(player)
    local taken = takenSet()
    local on = running() and id == "Unorthodox"
    for token, prompt in tokenPrompts do
        prompt.Enabled = on and not taken[token:GetAttribute("Index")]
    end
end

local function addToken(token)
    if tokenPrompts[token] then
        return
    end
    local function found(prompt)
        tokenPrompts[token] = prompt
        paintTokens()
    end
    local prompt = token:FindFirstChildWhichIsA("ProximityPrompt", true)
    if prompt then
        found(prompt)
        return
    end
    -- (with streaming a token's parts can arrive after the model: wait for its prompt)
    local arrived
    arrived = token.DescendantAdded:Connect(function(descendant)
        if descendant:IsA("ProximityPrompt") then
            arrived:Disconnect()
            found(descendant)
        end
    end)
end

for _, token in CollectionService:GetTagged(FactionRules.TokenTag) do
    addToken(token)
end
CollectionService:GetInstanceAddedSignal(FactionRules.TokenTag):Connect(addToken)
CollectionService:GetInstanceRemovedSignal(FactionRules.TokenTag):Connect(function(token)
    tokenPrompts[token] = nil
end)
for _, name in { "FactionTrial", "FactionTrialTaken", "Faction" } do
    player:GetAttributeChangedSignal(name):Connect(paintTokens)
end

-- ---------- the dummies' bars ----------
local DUMMY_FILL = Color3.fromRGB(255, 96, 70)

local function addDummy(dummy)
    local root = dummy:IsA("Model") and (dummy.PrimaryPart or dummy:WaitForChild("Root", 5))
    if not root then
        return
    end
    local gui = Instance.new("BillboardGui")
    gui.Name = "DummyBar"
    gui.Adornee = root
    gui.Size = UDim2.fromOffset(110, 14)
    gui.StudsOffsetWorldSpace = Vector3.new(0, 4.6, 0)
    gui.AlwaysOnTop = false
    gui.LightInfluence = 0
    gui.MaxDistance = 120
    gui.Parent = root
    local bar = UiKit.bar({ Name = "Blows", Fill = DUMMY_FILL, Size = UDim2.fromScale(1, 1), Parent = gui })
    local function update(instant)
        local health, most = dummy:GetAttribute("Health"), dummy:GetAttribute("MaxHealth")
        if typeof(health) == "number" and typeof(most) == "number" and most > 0 then
            UiKit.setBar(bar, health / most, instant)
        end
    end
    update(true)
    dummy:GetAttributeChangedSignal("Health"):Connect(function()
        update(false)
    end)
end

for _, dummy in CollectionService:GetTagged(FactionRules.DummyTag) do
    task.spawn(addDummy, dummy)
end
CollectionService:GetInstanceAddedSignal(FactionRules.DummyTag):Connect(function(dummy)
    task.spawn(addDummy, dummy)
end)

-- ---------- the ending ----------
local function bigBanner(title, text, color)
    local gui = Instance.new("ScreenGui")
    gui.Name = "TrialResult"
    gui.ResetOnSpawn = false
    gui.IgnoreGuiInset = true
    gui.DisplayOrder = 58
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = playerGui
    local column = Instance.new("Frame")
    column.Name = "Column"
    column.BackgroundTransparency = 1
    column.AnchorPoint = Vector2.new(0.5, 0.5)
    column.Position = UDim2.fromScale(0.5, 0.36)
    column.Size = UDim2.fromScale(0.8, 0.22)
    column.Parent = gui
    local constraint = Instance.new("UISizeConstraint")
    constraint.MaxSize = Vector2.new(760, 170)
    constraint.Parent = column
    local function line(words, y, height, tint, maxSize)
        local label = UiKit.boldLabel({
            Text = words, Font = "Heavy", TextScaled = true, TextWrapped = true, TextColor3 = tint, TextTransparency = 1, TextXAlignment = Enum.TextXAlignment.Center,
            Position = UDim2.fromScale(0, y), Size = UDim2.fromScale(1, height), Parent = column,
        })
        local limit = Instance.new("UITextSizeConstraint")
        limit.MaxTextSize = maxSize
        limit.Parent = label
        return label
    end
    local big = line(title, 0, 0.5, color, 52)
    local small = line(text, 0.56, 0.44, C.Text, 20)
    local labels = { big, small }
    for _, label in labels do
        TweenService:Create(label, TweenInfo.new(0.5), { TextTransparency = 0 }):Play()
        local outline = label:FindFirstChildOfClass("UIStroke")
        if outline then
            outline.Transparency = 1
            TweenService:Create(outline, TweenInfo.new(0.5), { Transparency = 0 }):Play()
        end
    end
    task.delay(5, function()
        for _, label in labels do
            TweenService:Create(label, TweenInfo.new(1), { TextTransparency = 1 }):Play()
            local outline = label:FindFirstChildOfClass("UIStroke")
            if outline then
                TweenService:Create(outline, TweenInfo.new(1), { Transparency = 1 }):Play()
            end
        end
        task.delay(1.2, function()
            gui:Destroy()
        end)
    end)
end

-- a burst of light at the vault the player stands by
local function vaultBurst(color)
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root then
        return
    end
    local best, bestDistance = nil, 45
    for _, vault in CollectionService:GetTagged(FactionRules.VaultTag) do
        local part = vault:IsA("BasePart") and vault or (vault:IsA("Model") and vault.PrimaryPart)
        if part then
            local distance = (part.Position - root.Position).Magnitude
            if distance < bestDistance then
                best, bestDistance = part, distance
            end
        end
    end
    if not best then
        return
    end
    local emitter = Instance.new("ParticleEmitter")
    emitter.Texture = "rbxassetid://243664672"
    emitter.Rate = 0
    emitter.Lifetime = NumberRange.new(1, 1.8)
    emitter.Speed = NumberRange.new(8, 18)
    emitter.SpreadAngle = Vector2.new(180, 180)
    emitter.Acceleration = Vector3.new(0, 6, 0)
    emitter.Drag = 2
    emitter.LightEmission = 1
    emitter.LightInfluence = 0
    emitter.Color = ColorSequence.new(color)
    emitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.2, 1.4), NumberSequenceKeypoint.new(1, 0) })
    emitter.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.15, 0.1), NumberSequenceKeypoint.new(1, 1) })
    emitter.Parent = best
    emitter:Emit(46)
    task.delay(3, function()
        emitter:Destroy()
    end)
end

Event.OnClientEvent:Connect(function(kind, argument, text)
    if kind == "TrialStart" and config.Factions[argument] then
        Sfx.play("Click")
        message:show(config.Factions[argument].Trial.Name .. " begins. Go!", "Info", config.Factions[argument].Color)
    elseif kind == "TrialNote" and typeof(argument) == "string" then
        Sfx.play("Click")
        message:show(argument, "Info")
    elseif kind == "TrialResult" and typeof(text) == "string" then
        local _, info = factionInfo()
        if argument == "Passed" then
            Sfx.play("RewardClaim")
            bigBanner("TRIAL PASSED", text, if info then info.Color else C.Highlight)
        else
            message:show(text, "Warning")
        end
    elseif kind == "Taken" then
        local _, info = factionInfo()
        vaultBurst(if info then info.Color else C.Highlight)
    end
end)

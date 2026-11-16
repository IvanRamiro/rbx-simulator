-- The QUEST tracker (the HUD's top right): the current quest (GameConfig.Quests, at the
-- player's "QuestStep" attribute, which the server moves on), its goal, a bar for one with a
-- count (the "QuestProgress" attribute), its reward, and SKIP (asks once more). A finished
-- quest is announced with its reward (QuestEvent "Complete"); after the last, the tracker goes.
-- Its header folds it to the quest's title: it starts folded on a phone, opens for a moment when a new quest arrives, and stays as the player leaves it.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RunService = game:GetService("RunService")
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local WorldMarkers = require(UI:WaitForChild("WorldMarkers"))
local Toast = require(UI:WaitForChild("Toast"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local QUESTS = GameConfig.Quests
local CONFIRM_SECONDS = 3

-- ---------- the tracker ----------
local panel = UiKit.panel({ Name = "QuestTracker", Size = UDim2.fromOffset(270, 0), Visible = false, Parent = Hud.Quest })
local inner = Instance.new("Frame")
inner.Name = "Inner"
inner.BackgroundTransparency = 1
inner.AutomaticSize = Enum.AutomaticSize.Y
inner.Size = UDim2.new(1, 0, 0, 0)
inner.Parent = panel
UiKit.padding(inner, UiTheme.Pad.Card, UiTheme.Pad.Card) -- one inset all round, as the profile's (it was 14 across, 10 down)
UiKit.list(inner, { Padding = UDim.new(0, 6) })
-- as tall as what it holds: sized from that, not by the panel's own AutomaticSize, which also counted its corner ornaments'
-- overhang (its foot sat 3 lower than its top padding)
local function fitHeight()
    local drawn = panel.AbsoluteSize.X
    local ratio = if drawn > 0 then panel.Size.X.Offset / drawn else 1
    panel.Size = UDim2.fromOffset(panel.Size.X.Offset, math.ceil(inner.AbsoluteSize.Y * ratio))
end
inner:GetPropertyChangedSignal("AbsoluteSize"):Connect(fitHeight)

-- its header: the fold mark, QUEST in heavy gold, and how far along the quests are
local header = Instance.new("Frame")
header.Name = "Header"
header.BackgroundTransparency = 1
header.Size = UDim2.new(1, 0, 0, 22)
header.LayoutOrder = 1
header.Parent = inner
local questWord = UiKit.boldLabel({
    Name = "Word", TextSize = 13, Text = "QUEST", TextColor3 = C.Edge, Position = UDim2.fromOffset(22, 0),
    Size = UDim2.new(1, -70, 1, 0), Parent = header,
})
local _ = questWord
local count = UiKit.boldLabel({
    Name = "Count", TextSize = 11, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0.5),
    Position = UDim2.fromScale(1, 0.5), Size = UDim2.fromOffset(48, 14), TextXAlignment = Enum.TextXAlignment.Right,
    Parent = header,
})
local rule = Instance.new("Frame") -- a gold rule under the header
rule.Name = "Rule"
rule.BorderSizePixel = 0
rule.BackgroundColor3 = C.Edge
rule.AnchorPoint = Vector2.new(0, 1)
rule.Position = UDim2.new(0, 0, 1, 2)
rule.Size = UDim2.new(1, 0, 0, 1)
rule.Parent = header
local ruleFade = Instance.new("UIGradient")
ruleFade.Transparency = NumberSequence.new(0.3, 1)
ruleFade.Parent = rule
local title = UiKit.label({
    Name = "Title", Font = "Title", TextSize = 15, TextColor3 = C.Highlight, AutomaticSize = Enum.AutomaticSize.Y,
    Size = UDim2.new(1, 0, 0, 0), TextWrapped = true, LayoutOrder = 2, Parent = inner,
})
local body = UiKit.label({
    Name = "Text", Font = "Strong", TextSize = 12, TextColor3 = C.Text, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0),
    TextWrapped = true, LayoutOrder = 3, Parent = inner,
})
local bar = UiKit.bar({ Name = "Progress", Size = UDim2.new(1, 0, 0, 6), LayoutOrder = 4, Parent = inner })

-- the way to where a quest happens (its Way in GameConfig.Quests): an arrow that turns with the camera, what it points at, how far
local way = Instance.new("Frame")
way.Name = "Way"
way.BackgroundTransparency = 1
way.Size = UDim2.new(1, 0, 0, 20)
way.LayoutOrder = 4
way.Visible = false
way.Parent = inner
local wayArrow = UiKit.label({
    Name = "Arrow", Font = "Strong", TextSize = 20, Text = "^", TextColor3 = C.Highlight, TextXAlignment = Enum.TextXAlignment.Center,
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0, 9, 0.5, 2), Size = UDim2.fromOffset(18, 18), Parent = way,
})
local wayText = UiKit.label({
    Name = "Where", Font = "Strong", TextSize = 12, TextColor3 = C.Highlight, Position = UDim2.fromOffset(24, 0), Size = UDim2.new(1, -24, 1, 0),
    TextTruncate = Enum.TextTruncate.AtEnd, Parent = way,
})

local fold = Instance.new("TextButton") -- the whole header
fold.Name = "Fold"
fold.Text = ""
fold.BackgroundTransparency = 1
-- taller than the header it lies over (invisible): the header is a thin line, too thin to hit with a thumb (UI audit 2026-11-11);
-- on a phone 56 tall, 45 pixels at its scale
fold.AnchorPoint = Vector2.new(0, 0.5)
fold.Position = UDim2.fromScale(0, 0.5)
fold.Size = UDim2.new(1, 0, 1, 20)
fold.ZIndex = 3
fold.Parent = header
-- its mark starts on the panel's left edge, like the title and the text under it (centred in its box, the narrow "-" stood 5 in)
local foldMark = UiKit.boldLabel({
    Name = "FoldMark", TextSize = 16, TextColor3 = C.AccentBright, AnchorPoint = Vector2.new(0, 0.5), TextXAlignment = Enum.TextXAlignment.Left,
    Position = UDim2.fromScale(0, 0.5), Size = UDim2.fromOffset(16, 18), Parent = header,
})

local footer = Instance.new("Frame")
footer.Name = "Footer"
footer.BackgroundTransparency = 1
footer.Size = UDim2.new(1, 0, 0, UiTheme.Height.ButtonSmall)
footer.LayoutOrder = 5
footer.Parent = inner
local rewardIcon = Instance.new("ImageLabel")
rewardIcon.Name = "RewardIcon"
rewardIcon.BackgroundTransparency = 1
rewardIcon.Image = UiTheme.Icons.Stones
rewardIcon.AnchorPoint = Vector2.new(0, 0.5)
rewardIcon.Position = UDim2.fromScale(0, 0.5)
rewardIcon.Size = UDim2.fromOffset(18, 18)
rewardIcon.Parent = footer
local reward = UiKit.boldLabel({
    Name = "Reward", TextSize = 12, TextColor3 = C.AccentBright, Position = UDim2.fromOffset(24, 0),
    Size = UDim2.new(1, -(24 + 80), 1, 0), TextTruncate = Enum.TextTruncate.AtEnd, Parent = footer,
})
local SKIP = "SKIP" -- its label at rest (it asks "SURE?" when pressed once)
local skip = UiKit.button({
    Name = "Skip", TextSize = 12, Text = SKIP, Tone = "Quiet", AnchorPoint = Vector2.new(1, 0.5),
    Position = UDim2.fromScale(1, 0.5), Size = UDim2.new(0, 72, 1, 0), Parent = footer,
})

local message = Toast.new("QuestMessage", C.Highlight, 4)

-- The Quests button on the rail shows or hides it, and the choice is saved.
local questButton = Hud.railButton("QuestButton", UiTheme.Icons.Quest, "Quests", 4)
local function questAllowed()
    local chosen = player:GetAttribute("SettingShowQuest")
    if chosen == nil then
        chosen = GameConfig.Settings.ShowQuest
    end
    -- lit while its panel is on the screen, as a window's button is while the window is open: a window steps the panel
    -- aside (Hud.window), and two lit buttons would say two things are open
    questButton:SetAttribute("Tone", if chosen and Hud.Quest.Visible then "Accent" else "Tile")
    return chosen == true
end
Hud.Quest:GetPropertyChangedSignal("Visible"):Connect(questAllowed)

-- On a short screen the unfolded panel keeps above the touch buttons under it (Hud.rightColumnFloor): its words are cut to the
-- lines that fit there (a 667x375 phone: the panel reached the lotus button by 6 px, phone pass 2026-11-16)
local capping = false
local function capBody()
    if capping then
        return
    end
    capping = true
    body.AutomaticSize = Enum.AutomaticSize.Y
    body.Size = UDim2.new(1, 0, 0, 0)
    body.TextTruncate = Enum.TextTruncate.None
    task.defer(function() -- (once laid out at its full height)
        fitHeight()
        local over = panel.AbsolutePosition.Y + panel.AbsoluteSize.Y - Hud.rightColumnFloor()
        if over > 0 and body.Visible and panel.Visible and panel.AbsoluteSize.X > 0 then
            local unitsPerPixel = panel.Size.X.Offset / panel.AbsoluteSize.X
            body.AutomaticSize = Enum.AutomaticSize.None
            body.Size = UDim2.new(1, 0, 0, math.max(14, math.floor((body.AbsoluteSize.Y - over) * unitsPerPixel)))
            body.TextTruncate = Enum.TextTruncate.AtEnd
            fitHeight()
        end
        capping = false
    end)
end

local chosenFold = nil -- what the player chose: until then a phone starts folded
local peekUntil = 0    -- a new quest shows in full until this moment
local footerRef = footer
local questHasBar = false

local function applyFold()
    local folded = if chosenFold ~= nil then chosenFold else Hud.isCompact()
    if os.clock() < peekUntil then
        folded = false
    end
    if Hud.isCompact() and Hud.isFighting() then -- a phone's panel folds while a guardian is fought: the bar needs the room
        folded = true
    end
    body.Visible = not folded
    footerRef.Visible = not folded
    bar.Visible = questHasBar and not folded
    title.TextWrapped = not folded
    title.TextTruncate = if folded then Enum.TextTruncate.AtEnd else Enum.TextTruncate.None
    title.AutomaticSize = if folded then Enum.AutomaticSize.None else Enum.AutomaticSize.Y
    title.Size = if folded then UDim2.new(1, 0, 0, 18) else UDim2.new(1, 0, 0, 0)
    foldMark.Text = if folded then "+" else "-"
    local compact = Hud.isCompact()
    panel.Size = UDim2.fromOffset(Hud.rightColumnWidth(), panel.Size.Y.Offset) -- (the air leaps under it share this width)
    fitHeight()
    -- a thumb's 44 pixels on a phone, at its 0.8 scale
    footerRef.Size = UDim2.new(1, 0, 0, if compact then 56 else UiTheme.Height.ButtonSmall)
    fold.Size = UDim2.new(1, 0, 1, if compact then 34 else 20)
    capBody()
end

fold.Activated:Connect(function()
    local folded = if chosenFold ~= nil then chosenFold else Hud.isCompact()
    chosenFold = not folded
    peekUntil = 0
    applyFold()
end)
Hud.CompactChanged:Connect(applyFold)
Hud.FightChanged:Connect(applyFold)

local lastStep = nil
local function render()
    local step = player:GetAttribute("QuestStep")
    local quest = typeof(step) == "number" and QUESTS[step]
    panel.Visible = quest ~= nil and questAllowed()
    if not quest then
        return
    end
    count.Text = step .. " / " .. #QUESTS
    title.Text = quest.Title
    body.Text = quest.Text
    if lastStep and lastStep ~= step and panel.Visible then -- a new quest writes itself on
        peekUntil = os.clock() + 8
        task.delay(8.1, applyFold)
        UiFx.flash(panel, C.Highlight)
        UiFx.typeIn(title, 0.25)
        UiFx.typeIn(body, 0.55)
    end
    lastStep = step
    reward.Text = NumberFormat.compact(quest.Reward) .. " Spirit Stones"
    -- a bar only where there is a count to fill (Qi, a rank's Qi)
    questHasBar = quest.Kind == "Qi" or quest.Kind == "Rank"
    applyFold()
end

local function renderProgress()
    local share = player:GetAttribute("QuestProgress")
    UiKit.setBar(bar, if typeof(share) == "number" then share else 0)
end

-- It rests while the egg's own way home is showing, and within sight of the place.
-- The place is also marked in the world (WorldMarkers): its name and distance over it, or at the screen's edge with an
-- arrow when it's out of view (a new player's run, 2026-11-11: the only guide to the Stone Lion 609 studs away was the
-- small arrow in this panel). A Way gives the ground's x and z; its height is found once, by a ray down.
local WAY_NEAR, WAY_EVERY = 25, 0.15
local WAY_ABOVE = 9 -- studs over the ground the marker hangs
local WAY_MARKER_NEAR = 60 -- studs: closer, the place is in sight (and a guardian's own bar marks it), so the marker goes
local nextWay = 0
local wayMarker = WorldMarkers.new(UiTheme.Colors.Highlight, true)
local wayGround = {} -- [quest step] = the ground's height at its Way
local reachedWay = {} -- [quest step] = true once the player has been at its Way (its Then takes over)
local function groundAt(step, x, z)
    if wayGround[step] == nil then
        local params = RaycastParams.new()
        params.FilterType = Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances = { player.Character }
        local hit = workspace:Raycast(Vector3.new(x, 1500, z), Vector3.new(0, -3000, 0), params)
        wayGround[step] = if hit then hit.Position.Y else false
    end
    return wayGround[step] or nil
end
RunService.RenderStepped:Connect(function()
    local now = os.clock()
    if now < nextWay then
        return
    end
    nextWay = now + WAY_EVERY
    -- the place's marker goes with the panel: while a window steps the panel aside (or the player hid it) the marker lay
    -- over the window's edge (a new player's run, 2026-11-12)
    if not Hud.Quest.Visible then
        wayMarker.world = nil
        return
    end
    local step = player:GetAttribute("QuestStep")
    local quest = typeof(step) == "number" and QUESTS[step]
    local target = quest and quest.Way
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local camera = workspace.CurrentCamera
    local show = false
    if target and root and camera and player:GetAttribute("CarryingEgg") == nil then
        local to = Vector3.new(target[2] - root.Position.X, 0, target[3] - root.Position.Z)
        if to.Magnitude > WAY_NEAR then
            local away = camera.CFrame:VectorToObjectSpace(to)
            wayArrow.Rotation = math.deg(math.atan2(away.X, -away.Z))
            wayText.Text = target[1] .. "  ·  " .. NumberFormat.compact(math.floor(to.Magnitude)) .. " studs"
            show = true
        end
    end
    if way.Visible ~= show then
        way.Visible = show
    end
    local near = root and target and Vector3.new(target[2] - root.Position.X, 0, target[3] - root.Position.Z).Magnitude < WAY_MARKER_NEAR
    -- a Way with a Then (x, y, z): once the player has reached the Way, the marker points there instead (the great root's
    -- top, then the relic at its foot: without it the marker pointed back up the root at the player climbing down)
    if near and target and target.Then then
        reachedWay[step] = true
    end
    local after = target and target.Then and reachedWay[step] and target.Then
    if after and root then
        local to = Vector3.new(after[2], after[3], after[4]) - root.Position
        wayMarker.world = if to.Magnitude > WAY_NEAR then Vector3.new(after[2], after[3], after[4]) else nil
        wayMarker.label.Text = string.upper(after[1]) .. "  " .. NumberFormat.compact(math.floor(to.Magnitude)) .. " studs"
        return
    end
    local ground = show and not near and groundAt(step, target[2], target[3])
    wayMarker.world = if ground then Vector3.new(target[2], ground + WAY_ABOVE, target[3]) else nil
    if ground then
        local to = Vector3.new(target[2] - root.Position.X, 0, target[3] - root.Position.Z)
        wayMarker.label.Text = string.upper(target[1]) .. "  " .. NumberFormat.compact(math.floor(to.Magnitude)) .. " studs"
    end
end)

player:GetAttributeChangedSignal("QuestStep"):Connect(render)
player:GetAttributeChangedSignal("QuestProgress"):Connect(renderProgress)
render()
renderProgress()

-- skipping them all asks once more
local armedUntil = 0
skip.Activated:Connect(function()
    if os.clock() < armedUntil then
        RemoteEvents.QuestEvent:FireServer("Skip")
        return
    end
    armedUntil = os.clock() + CONFIRM_SECONDS
    skip.Text = "SURE?"
    task.delay(CONFIRM_SECONDS, function()
        if os.clock() >= armedUntil then
            skip.Text = SKIP
        end
    end)
end)

RemoteEvents.QuestEvent.OnClientEvent:Connect(function(kind, step, stones)
    if kind ~= "Complete" or typeof(step) ~= "number" or not QUESTS[step] then
        return
    end
    Sfx.play("QuestComplete")
    local paid = if typeof(stones) == "number" and stones > 0 then "  +" .. NumberFormat.compact(stones) .. " Spirit Stones" else ""
    if step == #QUESTS then
        message:show("Quest complete: " .. QUESTS[step].Title .. "." .. paid .. "\nYou finished every quest. Well done!", "Reward")
    else
        message:show("Quest complete: " .. QUESTS[step].Title .. "." .. paid, "Reward")
    end
end)

questButton.Activated:Connect(function()
    -- with a window open the panel is stepped aside, so the press means "show me my quest": close the window, never hide it
    -- (a new player's run, 2026-11-12: pressed over the Codex, it switched the quest off unseen, and it stayed off)
    local chosen = questAllowed()
    if Hud.closeWindows() and chosen then
        return
    end
    local shown = not chosen
    player:SetAttribute("SettingShowQuest", shown)
    RemoteEvents.SettingsEvent:FireServer("ShowQuest", shown)
end)
player:GetAttributeChangedSignal("SettingShowQuest"):Connect(render)
questAllowed()

-- The guardians on this client (the server decides everything, Guardian.lua):
--   - animates each guardian and plays its moves' effects from GuardianEvent, through its rig
--     (GuardianRigs/<GuardianId>; GuardianAnim drives it, GuardianFx gives the building blocks);
--   - knockback: a guardian's blow throws this player's character (the client owns it) off its
--     feet for a moment; nothing ever kills;
--   - the health bar of the guardian this player is fighting, with its state and weak mark, floating over the guardian
--     itself (the owner, 2026-11-11: "the boss Hp should be above on the boss, not in the player screen");
--   - each guardian's voice and blows (VOICES), and the egg's sounds;
--   - a thief is shown the way to the safe zone (home to Yggdrasil: its end of the island's bridge);
--     a dropped egg stands under a pillar of light,
--     and only its thief sees its prompt and countdown.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local GuardianAnim = require(script.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent:WaitForChild("GuardianFx"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local Hud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Hud"))
local UiKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiKit"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))
local UiFx = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiFx"))
local HudMetrics = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudMetrics"))

local player = Players.LocalPlayer

local LOW = require(script.Parent.Parent:WaitForChild("Quality")).Low
local ANIMATE_DISTANCE = if LOW then 150 else 400
local BAR_DISTANCE = 130

local GOLD = Color3.fromRGB(232, 200, 120) -- the in-world waypoint to the safe zone
local NAME_COLOR = Color3.fromRGB(236, 246, 255)
local STATE_LOOK = {
    Guardian = { Text = "GUARDIAN", Color = Color3.fromRGB(120, 214, 255) },
    Weakened = { Text = "WEAKENED · TAKE AN EGG", Color = Color3.fromRGB(255, 196, 70) },
    Enraged = { Text = "ENRAGED", Color = Color3.fromRGB(255, 96, 50) },
}
local FILL = { -- the HUD's blue while it guards; gold, pulsing, once weakened; red once enraged
    Calm = { Color3.fromRGB(120, 214, 255), Color3.fromRGB(26, 104, 196) },
    Weak = { Color3.fromRGB(255, 232, 130), Color3.fromRGB(224, 140, 20) },
    Rage = { Color3.fromRGB(255, 110, 120), Color3.fromRGB(176, 22, 44) },
}
local WEAK_GOLD = Color3.fromRGB(255, 200, 70)

-- Each guardian's sounds by action (SoundCatalog names). `Start` plays as the action arrives; `Hit`
-- when the move lands, its wind-up (the action's first value) plus `Lead` (negative: a roar swells
-- before its shockwave). "Land" plays where it lands.
local VOICES = {
    StoneLion = {
        Awaken = { Start = "LionAwaken" }, Weaken = { Start = "LionWeaken" },
        Slam = { Hit = "LionSlam" }, Roar = { Hit = "LionRoar", Lead = -0.5 },
        Pounce = { Hit = "GuardianLeap" }, Land = { Start = "LionLand" },
    },
    MantisSage = {
        Awaken = { Start = "MantisAwaken" }, Weaken = { Start = "MantisWeaken" },
        Scythe = { Hit = "MantisScythe", Lead = -0.1 }, BladeWave = { Hit = "MantisBladeWave", Lead = -0.2 },
        Leap = { Hit = "GuardianLeap" }, Land = { Start = "MantisLand" },
    },
    EmberXuanwu = {
        Awaken = { Start = "XuanwuAwaken" }, Weaken = { Start = "XuanwuWeaken" },
        SerpentLash = { Hit = "XuanwuLash", Lead = -0.15 }, Quake = { Hit = "XuanwuQuake" },
        Charge = { Hit = "GuardianLeap" }, Land = { Start = "XuanwuLand" },
    },
    Tiangou = {
        Awaken = { Start = "TiangouAwaken" }, Weaken = { Start = "TiangouWeaken" },
        Bite = { Hit = "TiangouBite" }, EclipseHowl = { Hit = "TiangouHowl", Lead = -0.8 },
        MoonLeap = { Hit = "GuardianLeap" }, Land = { Start = "TiangouLand" },
    },
    Pangu = {
        Awaken = { Start = "PanguAwaken" }, Weaken = { Start = "PanguWeaken" },
        AxeCleave = { Hit = "PanguCleave", Lead = -0.7 }, SkySplitter = { Hit = "PanguSplit", Lead = -0.2 },
        ChaosNova = { Hit = "PanguNova", Lead = -0.45 }, TitanLeap = { Hit = "GuardianLeap" },
        Land = { Start = "PanguLand" },
    },
}
local EGG_SOUNDS = { Steal = "EggSteal", Drop = "EggDrop", Recover = "EggSteal", Secure = "EggSecure", Return = "EggReturn" }

local function voice(model, action, ...)
    local cue = (VOICES[model:GetAttribute("GuardianId")] or {})[action]
    if not cue then
        return
    end
    local at = if action == "Land" then (...) else model.PrimaryPart
    if cue.Start then
        Sfx.play(cue.Start, at)
    end
    local windUp = ...
    if cue.Hit and typeof(windUp) == "number" then
        Sfx.after(math.max(0, windUp + (cue.Lead or 0)), cue.Hit, at)
    end
end

local anims = {} -- [model] = GuardianAnim
local updateAlert, takeSize -- below, with the guardian's bar

local function guardianModel(guardianId)
    for _, model in CollectionService:GetTagged(GameConfig.GuardianTag) do
        if model:GetAttribute("GuardianId") == guardianId then
            return model
        end
    end
    return nil
end

-- ---------- the HUD ----------
local message = Toast.new("GuardianMessage", Color3.new(1, 1, 1), 4)

-- the health bar of the guardian being fought, over the guardian itself: a screen panel placed each frame at the point
-- over its body (as DamageNumbers places its numbers), so nothing in the world can hide it and it reads the same at any
-- distance. (A BillboardGui drawn AlwaysOnTop didn't show in Studio, 2026-11-11; one that isn't would sink into the
-- guardian's body as the bar slides down it.)
local function smallBar() -- on a phone it shouldn't take the whole screen
    return Hud.isCompact()
end
local function barWidth()
    return if smallBar() then 300 else 360
end
local BAR_ABOVE = 3 -- studs over the top of the guardian's body
local BAR_GAP = 8 -- pixels between the bar and the HUD above it
-- The lowest bottom (viewport pixels) of the HUD's top pieces over the screen's columns x0 to x1: the profile, the
-- currencies, the notification and the egg panel, the QUEST panel. The bar keeps under them (a guardian is 30-45 studs
-- tall, so close by its head is up there, and the bar slides down the guardian until it's clear). Measured each frame,
-- not a fixed margin: on a short screen a fixed one put the bar in the middle of it (the owner, "the position of UI are off").
local GuiService = game:GetService("GuiService")
local function hudBottomOver(x0, x1)
    -- read each time: when this script starts the top bar may not be laid out yet, and its height reads 0
    local guiInset = GuiService:GetGuiInset()
    local lowest = guiInset.Y -- never into Roblox's own top bar (its menu and chat buttons)
    for _, piece in { Hud.Status:FindFirstChild("StatusWindow"), Hud.Currency, Hud.Banner, Hud.Notice, Hud.Quest } do
        if piece and piece.Visible and piece.AbsoluteSize.Y > 1 then
            local left = piece.AbsolutePosition.X
            if left < x1 and left + piece.AbsoluteSize.X > x0 then
                lowest = math.max(lowest, piece.AbsolutePosition.Y + piece.AbsoluteSize.Y + guiInset.Y)
            end
        end
    end
    return lowest
end
local barLayer = Instance.new("ScreenGui")
barLayer.Name = "GuardianBarLayer"
barLayer.ResetOnSpawn = false
barLayer.IgnoreGuiInset = true -- so the bar's place is the viewport's own pixel
barLayer.DisplayOrder = -1     -- under the HUD's panels
barLayer.Enabled = false
barLayer.Parent = player:WaitForChild("PlayerGui")
local bar = UiKit.panel({ Name = "GuardianBar", AnchorPoint = Vector2.new(0.5, 1), Size = UDim2.fromOffset(barWidth(), 72), Parent = barLayer })
local barScale = Instance.new("UIScale")
barScale.Parent = bar
local barHeights = {} -- [model] = studs from its PrimaryPart up to over its body, measured once
local barIcon = UiKit.icon(UiTheme.Icons.Guardian, 34, "Danger")
barIcon.Position = UDim2.fromOffset(14, 19)
barIcon.Parent = bar

local nameLabel = UiKit.label({
    Font = "Title", TextSize = 16, TextColor3 = NAME_COLOR, Position = UDim2.fromOffset(58, 9),
    Size = UDim2.new(0.6, -58, 0, 20), TextTruncate = Enum.TextTruncate.AtEnd, Parent = bar,
})

local stateLabel = UiKit.label({
    Font = "Strong", TextSize = 13, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -16, 0, 12),
    Size = UDim2.new(0.45, 0, 0, 16), TextXAlignment = Enum.TextXAlignment.Right, Parent = bar,
})

local barTrack = Instance.new("Frame")
barTrack.Position = UDim2.fromOffset(58, 34)
barTrack.Size = UDim2.new(1, -74, 0, 24)
barTrack.BackgroundColor3 = UiTheme.Colors.Well
barTrack.ClipsDescendants = true
barTrack.Parent = bar
UiKit.corner(barTrack, 2)
UiKit.stroke(barTrack, UiTheme.Colors.EdgeDim, 0.3)

-- the health just lost, catching up behind the bar
local trailFill = Instance.new("Frame")
trailFill.BorderSizePixel = 0
trailFill.BackgroundColor3 = Color3.fromRGB(236, 246, 255)
trailFill.Size = UDim2.fromScale(1, 1)
trailFill.Parent = barTrack

local fill = Instance.new("Frame")
fill.BorderSizePixel = 0
fill.BackgroundColor3 = Color3.new(1, 1, 1)
fill.Size = UDim2.fromScale(1, 1)
fill.Parent = barTrack
local fillGradient = Instance.new("UIGradient")
fillGradient.Rotation = 90
fillGradient.Parent = fill

-- where it weakens
local weakMark = Instance.new("Frame")
weakMark.BorderSizePixel = 0
weakMark.BackgroundColor3 = UiTheme.Colors.Highlight
weakMark.AnchorPoint = Vector2.new(0.5, 0)
weakMark.Size = UDim2.new(0, 3, 1, 0)
weakMark.ZIndex = 3
weakMark.Parent = barTrack

local healthText = Instance.new("TextLabel")
healthText.BackgroundTransparency = 1
healthText.Size = UDim2.fromScale(1, 1)
healthText.FontFace = UiTheme.Fonts.Strong
healthText.TextSize = 14
healthText.TextColor3 = Color3.new(1, 1, 1)
healthText.TextStrokeTransparency = 0.5
healthText.ZIndex = 4
healthText.Parent = barTrack

local function setFill(colours)
    fillGradient.Color = ColorSequence.new(colours[1], colours[2])
end
setFill(FILL.Calm)

local function formatNumber(n)
    local s = tostring(math.floor(n))
    return (s:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", ""))
end

HudMetrics.Changed:Connect(function()
    bar.Size = UDim2.fromOffset(barWidth(), 72)
    takeSize()
end)

-- ---------- weakened: impossible to miss ----------
-- The moment a guardian weakens the bar flashes gold and its edge keeps pulsing, and the guardian itself is outlined in gold through
-- anything in the way, so it can be found in the fight. One outline, on the one guardian the bar shows.
local outline = Instance.new("Highlight")
outline.Name = "WeakenedOutline"
outline.FillTransparency = 1
outline.OutlineColor = WEAK_GOLD
outline.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
outline.Enabled = false
outline.Parent = Workspace
local barEdge = bar:FindFirstChildOfClass("UIStroke")
local EDGE_COLOR, EDGE_THICK = barEdge.Color, barEdge.Thickness
local alertState = nil

function updateAlert(model, state)
    local weak = state == "Weakened"
    if state ~= alertState then
        if weak then
            UiFx.flash(bar, WEAK_GOLD)
            UiFx.sweep(bar, WEAK_GOLD, 0.8)
        elseif state == "Enraged" then
            UiFx.flash(bar, STATE_LOOK.Enraged.Color)
        end
        alertState = state
    end
    outline.Adornee = if weak then model else nil
    outline.Enabled = weak
    if weak then
        local pulse = 0.5 + 0.5 * math.sin(os.clock() * 5)
        outline.OutlineTransparency = 0.15 + 0.45 * pulse
        barEdge.Color = WEAK_GOLD
        barEdge.Thickness = 2 + 2 * pulse
    else
        barEdge.Color = EDGE_COLOR
        barEdge.Thickness = EDGE_THICK
    end
end

-- ---------- an egg this player can take ----------
-- While the server says they can (their CanTakeEgg attribute: they've earned a share of the fight, and nothing stops them), a panel under
-- the bar says so and points to the nearest stand, and each stand holding an egg their rank can carry is marked TAKE, seen through anything.
-- The marks stand above the eggs and touch nothing on them: eggs have only their Highlight and bloom.
local takePanel = UiKit.panel({ Name = "TakeEggPanel", Size = UDim2.fromOffset(if smallBar() then 300 else 340, 48), LayoutOrder = -1, Visible = false, Brackets = false, Parent = Hud.Banner })
function takeSize()
    takePanel.Size = UDim2.fromOffset(if smallBar() then 300 else 340, 48)
end
local takeEdge = takePanel:FindFirstChildOfClass("UIStroke")
takeEdge.Color = WEAK_GOLD
takeEdge.Thickness = 2
UiFx.attention(takePanel, WEAK_GOLD) -- (after the edge is set: it breathes from its rest thickness)
local takeArrow = UiKit.label({
    Name = "Arrow", Font = "Strong", TextSize = 34, Text = "^", TextColor3 = WEAK_GOLD, TextXAlignment = Enum.TextXAlignment.Center,
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(28, 24), Size = UDim2.fromOffset(30, 30), Parent = takePanel,
})
UiKit.label({
    Name = "Title", Font = "Title", TextSize = 16, Text = "TAKE AN EGG", TextColor3 = WEAK_GOLD, Position = UDim2.fromOffset(50, 5),
    Size = UDim2.new(1, -58, 0, 20), Parent = takePanel,
})
local takeHow = UiKit.label({
    Name = "How", Font = "Strong", TextSize = 12, Position = UDim2.fromOffset(50, 25), Size = UDim2.new(1, -58, 0, 16),
    TextTruncate = Enum.TextTruncate.AtEnd, Parent = takePanel,
})

local TAKE_MARK_ABOVE = Vector3.new(0, 7.5, 0)
local TAKE_REFRESH = 0.5
local takeMarks = {} -- [stand] = its mark, drawn on the screen over the stand
local TAKE_MARK_SLACK = 40 -- pixels it may sit below its proper place, over the egg's own height
local takeRefreshAt = 0
local takeStands = {}
local wasAbleToTake = false

local function clearTakeMarks()
    for _, mark in takeMarks do
        mark:Destroy()
    end
    table.clear(takeMarks)
end

local takeLayer = Instance.new("Frame") -- under everything else on the HUD: the marks are drawn on the screen, following the stands
takeLayer.Name = "TakeEggMarks"
takeLayer.BackgroundTransparency = 1
takeLayer.Size = UDim2.fromScale(1, 1)
takeLayer.ZIndex = -1
takeLayer.Parent = Hud.Banner.Parent

local function markStand(stand)
    local mark = Instance.new("Frame")
    mark.Name = "TakeEggMark"
    mark.BackgroundTransparency = 1
    mark.AnchorPoint = Vector2.new(0.5, 1)
    mark.Size = UDim2.fromOffset(84, 58)
    mark.Visible = false
    local word = UiKit.label({
        Name = "Word", Font = "Title", Text = "TAKE", TextSize = 22, TextColor3 = WEAK_GOLD, TextStrokeTransparency = 0.2,
        TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.new(1, 0, 0, 26), Parent = mark,
    })
    word.ZIndex = 1
    UiKit.label({
        Name = "Chevron", Font = "Strong", Text = "v", TextSize = 28, TextColor3 = WEAK_GOLD, TextStrokeTransparency = 0.2,
        TextXAlignment = Enum.TextXAlignment.Center, Position = UDim2.fromOffset(0, 24), Size = UDim2.new(1, 0, 0, 26), Parent = mark,
    })
    mark.Parent = takeLayer
    takeMarks[stand] = mark
end

-- Each frame, over its stand, above the egg; a stand out of view is left to the panel's arrow.
local function placeTakeMarks(camera, now)
    for _, entry in takeStands do
        local mark = takeMarks[entry.stand]
        if mark then
            local point, inFront = camera:WorldToScreenPoint(entry.pedestal.Position + TAKE_MARK_ABOVE)
            -- it never climbs behind the bars at the top of the screen: it stops just under them, and goes only once
            -- the egg itself is up there, when the panel has it
            local lowest = takePanel.AbsolutePosition.Y + takePanel.AbsoluteSize.Y + mark.AbsoluteSize.Y
            mark.Visible = inFront and point.Z > 0 and point.Y + TAKE_MARK_SLACK >= lowest
            mark.Position = UDim2.fromOffset(point.X, math.max(point.Y, lowest))
            mark.Chevron.Position = UDim2.fromOffset(0, 24 + 4 * math.sin(now * 5))
        end
    end
end

-- the stands holding an egg this player's rank can carry
local function findTakeStands(config)
    local stands = {}
    local islands = Workspace:FindFirstChild("FloatingIslands")
    local island = islands and islands:FindFirstChild(config.Island)
    local folder = island and island:FindFirstChild("EggStands")
    local rankName = Ranks.getPlayerRankName(player)
    for _, stand in if folder then folder:GetChildren() else {} do
        local egg = GameConfig.Eggs[stand:GetAttribute("EggId") or stand.Name]
        local pedestal = stand:FindFirstChild("Pedestal")
        local prompt = pedestal and pedestal:FindFirstChildWhichIsA("ProximityPrompt")
        if egg and prompt and prompt.Enabled and rankName ~= "" and Ranks.isAtLeast(rankName, egg.RequiredRank) then
            table.insert(stands, { stand = stand, pedestal = pedestal, prompt = prompt })
        end
    end
    return stands
end

local function updateTakeIndicator()
    local id = player:GetAttribute("CanTakeEgg")
    local config = id and GameConfig.Guardians[id]
    if not config or player:GetAttribute("CarryingEgg") then
        takePanel.Visible = false
        wasAbleToTake = false
        clearTakeMarks()
        return
    end
    local now = os.clock()
    if now >= takeRefreshAt then
        takeRefreshAt = now + TAKE_REFRESH
        takeStands = findTakeStands(config)
        local keep = {}
        for _, entry in takeStands do
            keep[entry.stand] = true
            if not takeMarks[entry.stand] then
                markStand(entry.stand)
            end
        end
        for stand, mark in takeMarks do
            if not keep[stand] then
                mark:Destroy()
                takeMarks[stand] = nil
            end
        end
    end
    if #takeStands == 0 then -- nothing here their rank can carry
        takePanel.Visible = false
        return
    end
    -- in the fight it waits while a notification is up: one thing at a time at the top of the screen
    takePanel.Visible = not Toast.showing()
    if not wasAbleToTake then
        wasAbleToTake = true
        Sfx.play("Attune")
        UiFx.flash(takePanel, WEAK_GOLD)
    end

    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local camera = Workspace.CurrentCamera
    if not (root and camera) then
        return
    end
    placeTakeMarks(camera, now)
    local nearest, nearestDistance = nil, math.huge
    for _, entry in takeStands do
        local distance = (entry.pedestal.Position - root.Position).Magnitude
        if distance < nearestDistance then
            nearest, nearestDistance = entry, distance
        end
    end
    local reach = nearest.prompt.MaxActivationDistance
    if nearestDistance <= reach then
        takeArrow.Text = "!"
        takeArrow.Rotation = 0
        takeHow.Text = if UserInputService.TouchEnabled then "Hold the Take button on the stand"
            else "Hold " .. nearest.prompt.KeyboardKeyCode.Name .. " at the stand"
    else
        takeArrow.Text = "^"
        local away = camera.CFrame:VectorToObjectSpace(nearest.pedestal.Position - root.Position)
        takeArrow.Rotation = math.deg(math.atan2(away.X, -away.Z))
        takeHow.Text = "Go to the stand: " .. math.floor(nearestDistance) .. " studs"
    end
end

local shownTrail = 1
local shownMargin = nil -- the bar's eased top limit, in viewport pixels
local function updateBar(dt)
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local best, bestDistance = nil, BAR_DISTANCE
    for model in anims do
        local state = model:GetAttribute("State")
        local body = model.PrimaryPart
        if body and STATE_LOOK[state] then
            local distance = if root then (body.Position - root.Position).Magnitude else math.huge
            if player:GetAttribute("CarryingGuardian") == model:GetAttribute("GuardianId") then
                distance = 0 -- a thief always sees their pursuer
            end
            if distance < bestDistance then
                best, bestDistance = model, distance
            end
        end
    end
    local camera = Workspace.CurrentCamera
    local placed = false
    if best and camera then
        local body = best.PrimaryPart
        if not barHeights[best] then
            local box, size = best:GetBoundingBox()
            barHeights[best] = box.Position.Y + size.Y / 2 - body.Position.Y
        end
        local scale = HudMetrics.scale()
        local function onScreen(h)
            local point = camera:WorldToViewportPoint(body.Position + Vector3.new(0, h, 0))
            return point
        end
        local height = barHeights[best] + BAR_ABOVE
        local point = onScreen(height)
        local half = barWidth() * scale / 2
        -- the bar hangs from the point: its bottom sits there, so the point must be a bar's height under the HUD above it
        local margin = hudBottomOver(point.X - half, point.X + half) + BAR_GAP * scale + 72 * scale
        -- eased: a notification coming or going moves the HUD's foot, and the bar glides to it instead of jumping
        shownMargin = if shownMargin then shownMargin + (margin - shownMargin) * (1 - math.exp(-dt * 12)) else margin
        margin = shownMargin
        if point.Z > 0 and point.Y < margin then
            local low, high = 0, height -- the highest point on the guardian that is still in view
            for _ = 1, 8 do
                local middle = (low + high) / 2
                if onScreen(middle).Y < margin then
                    high = middle
                else
                    low = middle
                end
            end
            point = onScreen(low)
        end
        if point.Z > 0 then
            placed = true
            barScale.Scale = scale
            bar.Position = UDim2.fromOffset(point.X, math.max(point.Y, margin))
        end
    end
    barLayer.Enabled = placed
    if not best then
        outline.Enabled = false
        alertState = nil
        return
    end
    local config = GameConfig.Guardians[best:GetAttribute("GuardianId")]
    local state = best:GetAttribute("State")
    local health, maxHealth = best:GetAttribute("Health") or 0, best:GetAttribute("MaxHealth") or 1
    local share = math.clamp(health / maxHealth, 0, 1)
    nameLabel.Text = config and config.DisplayName or best.Name
    local look = STATE_LOOK[state]
    stateLabel.Text = if smallBar() then string.split(look.Text, " ·")[1] else look.Text
    stateLabel.TextColor3 = look.Color
    setFill(if state == "Enraged" then FILL.Rage elseif state == "Weakened" then FILL.Weak else FILL.Calm)
    updateAlert(best, state, dt)
    fill.Size = UDim2.fromScale(share, 1)
    shownTrail = if share > shownTrail then share else shownTrail + (share - shownTrail) * (1 - math.exp(-dt * 3))
    trailFill.Size = UDim2.fromScale(shownTrail, 1)
    weakMark.Position = UDim2.fromScale(config and config.WeakenedAt or 0.4, 0)
    healthText.Text = formatNumber(health) .. " / " .. formatNumber(maxHealth)
end

-- ---------- knockback ----------
local knockToken = 0
local function knock(velocity, stagger)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and root) or humanoid.Health <= 0 then
        return
    end
    knockToken += 1
    local token = knockToken
    humanoid.PlatformStand = true
    root.AssemblyLinearVelocity = velocity
    local across = Vector3.new(velocity.Z, 0, -velocity.X)
    if across.Magnitude > 0.1 then
        root.AssemblyAngularVelocity = across.Unit * 6
    end
    GuardianFx.shake(root.Position, 2.5, 0.5)
    task.delay(stagger, function()
        if knockToken == token and humanoid.Parent and player:GetAttribute("IsFlying") ~= true then
            humanoid.PlatformStand = false
            humanoid:ChangeState(Enum.HumanoidStateType.GettingUp)
        end
    end)
end

-- ---------- the way to the safe zone, for a thief ----------
local waypoint = nil
local function updateWaypoint()
    local guardianId = player:GetAttribute("CarryingGuardian")
    local model = guardianId and guardianModel(guardianId)
    local centre = model and model:GetAttribute("SafeZone")
    if not centre then
        if waypoint then
            waypoint:Destroy()
            waypoint = nil
        end
        return
    end
    if waypoint then
        return
    end
    local anchor = Instance.new("Part")
    anchor.Name = "SafeZoneWaypoint"
    anchor.Anchored, anchor.CanCollide, anchor.CanQuery, anchor.CanTouch = true, false, false, false
    anchor.Transparency = 1
    anchor.Size = Vector3.new(0.4, 0.4, 0.4)
    anchor.CFrame = CFrame.new(centre + Vector3.new(0, 10, 0))
    local gui = Instance.new("BillboardGui")
    gui.AlwaysOnTop = true
    gui.Size = UDim2.fromOffset(170, 46)
    gui.LightInfluence = 0
    gui.Parent = anchor
    local label = Instance.new("TextLabel")
    label.Name = "Label"
    label.BackgroundTransparency = 1
    label.Size = UDim2.fromScale(1, 1)
    label.Font = Enum.Font.GothamBlack
    label.TextScaled = true
    label.TextColor3 = GOLD
    label.TextStrokeTransparency = 0.3
    label.Parent = gui
    local bottom, top = Instance.new("Attachment"), Instance.new("Attachment")
    bottom.Position = Vector3.new(0, -10, 0)
    top.Position = Vector3.new(0, 40, 0)
    bottom.Parent, top.Parent = anchor, anchor
    local beam = Instance.new("Beam")
    beam.Attachment0, beam.Attachment1 = bottom, top
    beam.Texture = "rbxassetid://135169457468310"
    beam.TextureMode = Enum.TextureMode.Stretch
    beam.FaceCamera = true
    beam.LightEmission = 1
    beam.LightInfluence = 0
    beam.Width0, beam.Width1 = 6, 2
    beam.Color = ColorSequence.new(Color3.fromRGB(255, 236, 170), Color3.fromRGB(255, 190, 60))
    beam.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(0.7, 0.65), NumberSequenceKeypoint.new(1, 1) })
    beam.Parent = anchor
    anchor.Parent = Workspace
    waypoint = anchor
end
player:GetAttributeChangedSignal("CarryingGuardian"):Connect(updateWaypoint)
updateWaypoint()

local function updateWaypointText()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not (waypoint and root) then
        return
    end
    local config = GameConfig.Guardians[player:GetAttribute("CarryingGuardian")]
    local distance = ((waypoint.Position - root.Position) * Vector3.new(1, 0, 1)).Magnitude
    waypoint.BillboardGui.Label.Text = string.upper(config.SafeZone.Name) .. "  " .. math.floor(distance) .. "m"
end

-- ---------- dropped eggs ----------
local eggsFolder = Workspace:WaitForChild("GuardianEggs")
local dropped = {} -- [eggModel] = { beacon, countdown }

local function watchEgg(egg)
    local function refresh()
        local isDropped = egg:GetAttribute("State") == "Dropped"
        local mine = egg:GetAttribute("OwnerUserId") == player.UserId
        local prompt = egg.PrimaryPart and egg.PrimaryPart:FindFirstChildOfClass("ProximityPrompt")
        if prompt and isDropped and not mine then
            prompt.Enabled = false -- only its thief may recover it (the server checks too)
        end
        local entry = dropped[egg]
        if isDropped and not entry then
            entry = { beacon = GuardianFx.beacon(egg) }
            if mine then
                local gui = Instance.new("BillboardGui")
                gui.AlwaysOnTop = true
                gui.Size = UDim2.fromOffset(150, 34)
                gui.StudsOffsetWorldSpace = Vector3.new(0, 3.5, 0)
                gui.Parent = egg.PrimaryPart
                local label = Instance.new("TextLabel")
                label.BackgroundTransparency = 1
                label.Size = UDim2.fromScale(1, 1)
                label.Font = Enum.Font.GothamBlack
                label.TextScaled = true
                label.TextColor3 = Color3.fromRGB(150, 210, 255)
                label.TextStrokeTransparency = 0.3
                label.Parent = gui
                entry.countdown = label
                entry.gui = gui
            end
            dropped[egg] = entry
        elseif not isDropped and entry then
            if entry.beacon then
                entry.beacon:Destroy()
            end
            if entry.gui then
                entry.gui:Destroy()
            end
            dropped[egg] = nil
        end
    end
    egg:GetAttributeChangedSignal("State"):Connect(refresh)
    egg:GetAttributeChangedSignal("OwnerUserId"):Connect(refresh)
    task.spawn(function()
        local body = egg.PrimaryPart or egg:WaitForChild("Egg", 5)
        local prompt = body and body:WaitForChild("ProximityPrompt", 5)
        if prompt then
            prompt:GetPropertyChangedSignal("Enabled"):Connect(refresh)
        end
        refresh()
    end)
    egg.AncestryChanged:Connect(function()
        if not egg:IsDescendantOf(Workspace) and dropped[egg] then
            if dropped[egg].beacon then
                dropped[egg].beacon:Destroy()
            end
            if dropped[egg].gui then
                dropped[egg].gui:Destroy()
            end
            dropped[egg] = nil
        end
    end)
end
eggsFolder.ChildAdded:Connect(watchEgg)
for _, egg in eggsFolder:GetChildren() do
    watchEgg(egg)
end

local function updateCountdowns()
    local now = Workspace:GetServerTimeNow()
    for egg, entry in dropped do
        if entry.countdown then
            local left = math.max(0, math.ceil((egg:GetAttribute("DropUntil") or now) - now))
            entry.countdown.Text = "RECOVER · " .. left .. "s"
        end
    end
end

-- ---------- the guardians ----------
local rigsFolder = script.Parent:WaitForChild("GuardianRigs")
local rigs = {} -- [model] = its rig (GuardianRigs/<GuardianId>)

local function track(model)
    if anims[model] or not model:IsDescendantOf(Workspace) then
        return
    end
    -- a model built with a skeleton names its own rig (GuardianBuilder.storeSkinned)
    local rigModule = rigsFolder:FindFirstChild(model:GetAttribute("Rig") or model:GetAttribute("GuardianId") or "")
    if not rigModule then
        warn("GuardianController: no rig for " .. model.Name)
        return
    end
    local rig = require(rigModule)
    rigs[model] = rig
    task.spawn(function()
        local anim = GuardianAnim.new(model, rig)
        if anim and model:IsDescendantOf(Workspace) then
            anims[model] = anim
        end
    end)
end
CollectionService:GetInstanceAddedSignal(GameConfig.GuardianTag):Connect(track)
CollectionService:GetInstanceRemovedSignal(GameConfig.GuardianTag):Connect(function(model)
    anims[model] = nil
    rigs[model] = nil
end)
for _, model in CollectionService:GetTagged(GameConfig.GuardianTag) do
    track(model)
end

local function isNear(model, distance)
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return root ~= nil and model.PrimaryPart ~= nil and (model.PrimaryPart.Position - root.Position).Magnitude <= distance
end

local EGG_ACTIONS = { Steal = true, Drop = true, Recover = true, Secure = true, Return = true }

RemoteEvents.GuardianEvent.OnClientEvent:Connect(function(model, action, ...)
    if action == "Knock" then
        Sfx.play("Knockback")
        knock(...)
        return
    end
    if action == "Secured" then
        local eggId, stones, element, qi = ...
        local egg = GameConfig.Eggs[eggId]
        local reward = if typeof(stones) == "number" and stones > 0 then " +" .. stones .. " Spirit Stones." else ""
        if typeof(qi) == "number" and qi > 0 then
            reward ..= " +" .. NumberFormat.compact(qi) .. " Qi."
        end
        local info = typeof(element) == "string" and GameConfig.Forge.Elements[element]
        local relic = if info then " Its relic unlocks " .. info.DisplayName .. " at the Blacksmith's forge." else ""
        message:show((egg and egg.DisplayName or "The egg") .. " secured! Hatch it at the Hatching Altar." .. reward .. relic, "Reward")
        return
    elseif action == "BagFull" then
        Sfx.play("Error")
        message:show("You can't hold any more of that egg: hatch some first.", "Warning")
        return
    end
    if not (typeof(model) == "Instance" and model.Parent) then
        return
    end
    local rig = rigs[model]
    local config = GameConfig.Guardians[model:GetAttribute("GuardianId")]
    local style = rig and rig.Style
    if not EGG_ACTIONS[action] then
        local anim = anims[model]
        if anim then
            anim:play(action, ...)
        end
        local fx = rig and rig.Fx[action]
        if fx then
            fx(model, ...)
        end
        voice(model, action, ...)
    elseif EGG_SOUNDS[action] then
        local egg = eggsFolder:FindFirstChild(model.Name .. "_Egg")
        local at = if typeof((...)) == "Vector3" then (...) else egg and egg.PrimaryPart
        Sfx.play(EGG_SOUNDS[action], at or model.PrimaryPart)
    end
    if action == "Awaken" then
        if isNear(model, BAR_DISTANCE) then
            message:show((config.Called or "The " .. config.DisplayName) .. " awakens!", "Info")
        end
    elseif action == "Weaken" then
        if isNear(model, BAR_DISTANCE) then
            message:show((config.Called or "The " .. config.DisplayName) .. " " .. config.WeakenedHint, "Info")
        end
    elseif action == "Steal" and style then
        GuardianFx.steal((...), style)
        if player:GetAttribute("CarryingGuardian") == model:GetAttribute("GuardianId") then
            local goal = "Carry it home to " .. config.SafeZone.Name .. "!"
            message:show("You took the egg! " .. goal, "Success")
        end
    elseif action == "Drop" and style then
        GuardianFx.drop((...), style)
        local egg = eggsFolder:FindFirstChild(model.Name .. "_Egg")
        if egg and egg:GetAttribute("OwnerUserId") == player.UserId then
            message:show("You dropped the egg! Recover it within " .. config.DropTime .. "s.", "Warning")
        end
    elseif action == "Secure" then
        GuardianFx.secure((...))
    elseif action == "Return" and style then
        local position = ...
        if position then
            GuardianFx.steal(position, style)
        end
    end
end)

RunService.RenderStepped:Connect(function(dt)
    local camera = Workspace.CurrentCamera
    for model, anim in anims do
        if not model.Parent then
            anims[model] = nil
            rigs[model] = nil
        elseif camera and model.PrimaryPart and (not anim.lastUpdate or (model.PrimaryPart.Position - camera.CFrame.Position).Magnitude <= ANIMATE_DISTANCE) then
            -- the first update comes at any distance: a skinned guardian that never had one stands in its bind pose
            -- on a phone a guardian at rest updates every other frame, with the time it missed
            local state = model:GetAttribute("State")
            local atRest = state == nil or state == "Dormant" or state == "Resting"
            anim.waited = (anim.waited or 0) + dt
            anim.odd = not anim.odd
            if not (LOW and atRest and anim.odd) then
                anim:update(anim.waited)
                anim.waited = 0
            end
        end
    end
    updateBar(dt)
    updateTakeIndicator()
    updateWaypointText()
    updateCountdowns()
end)

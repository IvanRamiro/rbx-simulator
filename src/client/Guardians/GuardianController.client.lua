-- The guardians on this client (the server decides everything, Guardian.lua):
--   - animates each guardian and plays its moves' effects from GuardianEvent, through its rig
--     (GuardianRigs/<GuardianId>; GuardianAnim drives it, GuardianFx gives the building blocks);
--   - knockback: a guardian's blow throws this player's character (the client owns it) off its
--     feet for a moment; nothing ever kills;
--   - each guardian's health bar over its head and its cooldown sign over its lair, in the world (GuardianBars), and a gold
--     outline through anything in the way round the weakened guardian nearest this player;
--   - each guardian's voice and blows (VOICES), and the egg's sounds;
--   - a thief is shown the way to the safe zone (home to Yggdrasil: its end of the island's bridge);
--     a dropped egg stands under a pillar of light,
--     and only its thief sees its prompt and countdown.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local GuardianAnim = require(script.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent:WaitForChild("GuardianFx"))
local GuardianBars = require(script.Parent:WaitForChild("GuardianBars"))
local GuardianReact = require(script.Parent:WaitForChild("GuardianReact"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local Hud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Hud"))
local UiKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiKit"))
local UiFx = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiFx"))
local HudMetrics = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudMetrics"))
local WorldMarkers = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("WorldMarkers"))

local player = Players.LocalPlayer

local LOW = require(script.Parent.Parent:WaitForChild("Quality")).Low
local ANIMATE_DISTANCE = if LOW then 150 else 400
local NEAR_DISTANCE = 130 -- studs: its wake and weak messages, and the weakened outline, are for players this near

local GOLD = Color3.fromRGB(232, 200, 120) -- the in-world waypoint to the safe zone
local WEAK_GOLD = Color3.fromRGB(255, 200, 70)

-- Each guardian's sounds by action (SoundCatalog names). `Start` plays as the action arrives; `Hit`
-- when the move lands, its wind-up (the action's first value) plus `Lead` (negative: a roar swells
-- before its shockwave). "Land" plays where it lands.
local VOICES = {
    StoneLion = {
        Awaken = { Start = "LionAwaken" }, Weaken = { Start = "LionWeaken" },
        Slam = { Start = "LionReady", Hit = "LionSlam" }, Roar = { Hit = "LionRoar", Lead = -0.5 },
        Pounce = { Hit = "GuardianLeap" }, Land = { Start = "LionLand" },
    },
    MantisSage = {
        Awaken = { Start = "MantisAwaken" }, Weaken = { Start = "MantisWeaken" },
        Scythe = { Start = "MantisReady", Hit = "MantisScythe", Lead = -0.1 }, BladeWave = { Hit = "MantisBladeWave", Lead = -0.2 },
        Leap = { Hit = "GuardianLeap" }, Land = { Start = "MantisLand" },
    },
    EmberXuanwu = {
        Awaken = { Start = "XuanwuAwaken" }, Weaken = { Start = "XuanwuWeaken" },
        SerpentLash = { Start = "XuanwuReady", Hit = "XuanwuLash", Lead = -0.15 }, Quake = { Start = "QuakeGather", Hit = "XuanwuQuake" },
        Charge = { Hit = "GuardianLeap" }, Land = { Start = "XuanwuLand" },
    },
    Tiangou = {
        Awaken = { Start = "TiangouAwaken" }, Weaken = { Start = "TiangouWeaken" },
        Bite = { Start = "TiangouReady", Hit = "TiangouBite" }, EclipseHowl = { Hit = "TiangouHowl", Lead = -0.8 },
        MoonLeap = { Hit = "GuardianLeap" }, Land = { Start = "TiangouLand" },
    },
    Pangu = {
        Awaken = { Start = "PanguAwaken" }, Weaken = { Start = "PanguWeaken" },
        AxeCleave = { Start = "PanguReady", Hit = "PanguCleave", Lead = -0.7 }, SkySplitter = { Start = "PanguReady", Hit = "PanguSplit", Lead = -0.2 },
        ChaosNova = { Hit = "PanguNova", Lead = -0.45 }, TitanLeap = { Hit = "GuardianLeap" },
        Land = { Start = "PanguLand" },
    },
}
local EGG_SOUNDS = { Steal = "EggSteal", Drop = "EggDrop", Recover = "EggRecover", Secure = "EggSecureWorld", Return = "EggReturn" }
-- each guardian's cry a beat after its egg is taken, from the guardian (SoundCatalog)
local ALERTS = { StoneLion = "LionGrowl", MantisSage = "BladeRing", EmberXuanwu = "SerpentHiss", Tiangou = "TiangouAlert", Pangu = "PanguAlert" }
local ALERT_DELAY = 0.25
local securedAt = -math.huge -- when this player last secured an egg: their own stinger plays, not the world's

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

-- The ground an attack will hit, drawn while it winds up (GuardianFx): a sweep's wedge, a wave's reach. A leap marks its own landing (Rig.Fx).
local function markGround(model, config, action, windUp)
    local spec = config and config.Attacks and config.Attacks[action]
    if not spec or typeof(windUp) ~= "number" then
        return
    end
    if spec.Kind == "Sweep" then
        GuardianFx.cone(model, spec.Range, spec.Arc, windUp)
    elseif spec.Kind == "Wave" then
        local arc = spec.Arc or 180
        if arc >= 180 then
            GuardianFx.ring(model, spec.Radius, windUp)
        else
            GuardianFx.cone(model, spec.Radius, arc, windUp)
        end
    end
end

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

-- ---------- weakened: impossible to miss ----------
-- The weakened guardian nearest this player is outlined in gold through anything in the way, so it can be found in the fight
-- (its bar flashes and pulses gold too: GuardianBars). One outline.
local outline = Instance.new("Highlight")
outline.Name = "WeakenedOutline"
outline.FillTransparency = 1
outline.OutlineColor = WEAK_GOLD
outline.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
outline.Enabled = false
outline.Parent = Workspace

local function updateOutline()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local best, bestDistance = nil, NEAR_DISTANCE
    for model in anims do
        local body = model.PrimaryPart
        if root and body and model:GetAttribute("State") == "Weakened" then
            local distance = (body.Position - root.Position).Magnitude
            if distance < bestDistance then
                best, bestDistance = model, distance
            end
        end
    end
    outline.Adornee = best
    outline.Enabled = best ~= nil
    if best then
        outline.OutlineTransparency = 0.15 + 0.45 * (0.5 + 0.5 * math.sin(os.clock() * 5))
    end
end

-- ---------- an egg this player can take ----------
-- While the server says they can (their CanTakeEgg attribute: they've earned a share of the fight, and nothing stops them), a panel at
-- the top of the screen says so and points to the nearest stand, and each stand holding an egg their rank can carry is marked TAKE, seen through anything.
-- The marks stand above the eggs and touch nothing on them: eggs have only their Highlight and bloom.
local takePanel = UiKit.panel({ Name = "TakeEggPanel", Size = UDim2.fromOffset(if Hud.isCompact() then 300 else 340, 48), LayoutOrder = -1, Visible = false, Brackets = false, Parent = Hud.Banner })
HudMetrics.Changed:Connect(function()
    takePanel.Size = UDim2.fromOffset(if Hud.isCompact() then 300 else 340, 48)
end)
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
local INFO_MARK_ABOVE = Vector3.new(0, 5.5, 0) -- a NEEDS or BACK IN word: just over the egg's top (it has no chevron)
local TAKE_REFRESH = 0.5
local takeMarks = {} -- [stand] = its mark, drawn on the screen over the stand
local TAKE_MARK_SLACK = 40 -- pixels it may sit below its proper place, over the egg's own height
local TAKE_MARK_GAP = 6 -- pixels it keeps from a guardian's bar or sign
local takeRefreshAt = 0
local takeStands = {}
local markStands = {} -- every stand with a mark: the TAKE ones (takeStands) and the others near the player
local wasAbleToTake = false

local takeLayer = Instance.new("Frame") -- under everything else on the HUD: the marks are drawn on the screen, following the stands
takeLayer.Name = "TakeEggMarks"
takeLayer.BackgroundTransparency = 1
takeLayer.Size = UDim2.fromScale(1, 1)
takeLayer.ZIndex = -1
takeLayer.Parent = Hud.Banner.Parent

-- A stand's mark: TAKE in gold with a bobbing chevron over an egg this player can take now; or, near the stands, a quieter word
-- over the others: what an egg their rank can't carry yet needs ("NEEDS QI ADEPT"), and when their own egg is back on an emptied
-- stand ("BACK IN 2:31"). Each island's three eggs need three ranks (GameConfig.Eggs), so a newcomer can carry only the first: all
-- three looked alike, and holding F on the other two seemed broken (beta, 2026-11-17).
local INFO_GREY = Color3.fromRGB(205, 214, 230)
local function markStand(stand, kind)
    local mark = Instance.new("Frame")
    mark.Name = "TakeEggMark"
    mark.BackgroundTransparency = 1
    mark.AnchorPoint = Vector2.new(0.5, 1)
    mark.Size = if kind == "take" then UDim2.fromOffset(84, 58) else UDim2.fromOffset(160, 26)
    mark.Visible = false
    mark:SetAttribute("Kind", kind)
    local word = UiKit.label({ -- (the heavy face of every mark over the world: WorldMarkers)
        Name = "Word", Font = "Heavy", Text = "TAKE", TextSize = if kind == "take" then 22 else 16,
        TextColor3 = if kind == "take" then WEAK_GOLD else INFO_GREY, TextStrokeTransparency = 0.2,
        TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.new(1, 0, 0, 26), Parent = mark,
    })
    word.ZIndex = 1
    if kind == "take" then
        UiKit.label({
            Name = "Chevron", Font = "Heavy", Text = "v", TextSize = 28, TextColor3 = WEAK_GOLD, TextStrokeTransparency = 0.2,
            TextXAlignment = Enum.TextXAlignment.Center, Position = UDim2.fromOffset(0, 24), Size = UDim2.new(1, 0, 0, 26), Parent = mark,
        })
    end
    mark.Parent = takeLayer
    takeMarks[stand] = mark
end

-- Each frame, over its stand, above the egg; a stand out of view is left to the panel's arrow.
local function placeTakeMarks(camera, now)
    local topFoot = 0
    for _, piece in { Hud.Banner, Hud.Notice } do
        if piece.Visible and piece.AbsoluteSize.Y > 1 then
            topFoot = math.max(topFoot, piece.AbsolutePosition.Y + piece.AbsoluteSize.Y)
        end
    end
    local boxes = GuardianBars.screenBoxes(camera)
    local placed = {} -- the words shown so far, { left, right, top, bottom }: a quieter word that would cross one waits
    for _, entry in markStands do
        local mark = takeMarks[entry.stand]
        if mark then
            local point, inFront = camera:WorldToScreenPoint(entry.pedestal.Position + (if entry.kind == "take" then TAKE_MARK_ABOVE else INFO_MARK_ABOVE))
            local size = mark.AbsoluteSize
            -- it never climbs behind the panels at the top of the screen (the Banner's: this panel, the tutorial, the Merchant's
            -- line; and a notification under them): it stops just under them
            local highest = topFoot + size.Y
            local y = math.max(point.Y, highest)
            local fits = point.Y + TAKE_MARK_SLACK >= y
            -- nor over a guardian's bar or sign in the world (marks are drawn over the world): where they'd cross, it hangs just
            -- under it, or else just over it, where the bar hides the egg's own place
            for _, box in boxes do
                local barX, barY, barW, barH = box[1], box[2], box[3], box[4]
                if point.X + size.X / 2 > barX and point.X - size.X / 2 < barX + barW
                    and y > barY - TAKE_MARK_GAP and y - size.Y < barY + barH + TAKE_MARK_GAP then
                    local under, over = barY + barH + TAKE_MARK_GAP + size.Y, barY - TAKE_MARK_GAP
                    if point.Y + TAKE_MARK_SLACK >= under then
                        y, fits = under, true
                    else
                        y, fits = over, over >= highest and point.Y > over
                    end
                end
            end
            -- and it goes once it would be more than a little under its proper place (the egg itself is up there, when
            -- the panel has it)
            local visible = inFront and point.Z > 0 and fits and not entry.blocked
            local half = math.max(mark.Word.TextBounds.X, size.X * 0.5) / 2 + 4
            local box = { point.X - half, point.X + half, y - size.Y, y }
            if visible and entry.kind ~= "take" then
                for _, other in placed do
                    if box[1] < other[2] and box[2] > other[1] and box[3] < other[4] and box[4] > other[3] then
                        visible = false
                        break
                    end
                end
            end
            if visible then
                table.insert(placed, box)
            end
            mark.Visible = visible
            mark.Position = UDim2.fromOffset(point.X, y)
            local chevron = mark:FindFirstChild("Chevron")
            if chevron then
                chevron.Position = UDim2.fromOffset(0, 24 + 4 * math.sin(now * 5))
            end
            if entry.backAt then
                local left = math.max(0, math.ceil(entry.backAt - Workspace:GetServerTimeNow()))
                mark.Word.Text = string.format("BACK IN %d:%02d", left // 60, left % 60)
            end
        end
    end
end

local function canCarry(rankName, eggId)
    local egg = GameConfig.Eggs[eggId or ""]
    return egg ~= nil and rankName ~= "" and Ranks.isAtLeast(rankName, egg.RequiredRank)
end

local function eachStand(fn)
    local islands = Workspace:FindFirstChild("FloatingIslands")
    for _, island in if islands then islands:GetChildren() else {} do
        local folder = island:FindFirstChild("EggStands")
        for _, stand in if folder then folder:GetChildren() else {} do
            local pedestal = stand:FindFirstChild("Pedestal")
            local prompt = pedestal and pedestal:FindFirstChildWhichIsA("ProximityPrompt")
            if prompt then
                fn(stand, pedestal, prompt)
            end
        end
    end
end

-- A stand's prompt as this player sees it: "Take" (hold) on an egg their rank can carry; on one it can't, what it needs
-- ("Needs Qi Adept") and a tap, which brings the server's answer naming the egg here they can take (PetController). The server
-- still decides (Guardian:takeFromStand); this only says it before the player tries.
local function stylePrompt(stand, prompt, rankName)
    local eggId = stand:GetAttribute("EggId")
    local locked = eggId ~= nil and not canCarry(rankName, eggId)
    local action = if locked then "Needs " .. Ranks.getRankById(GameConfig.Eggs[eggId].RequiredRank).Name else "Take"
    if prompt.ActionText ~= action then
        prompt.ActionText = action
    end
    local hold = if locked then 0 else 0.5 -- (EggStands' hold)
    if prompt.HoldDuration ~= hold then
        prompt.HoldDuration = hold
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

local INFO_RANGE = 60 -- studs from a stand within which its NEEDS or BACK IN word shows

-- the stands near the player with a word for them: an egg their rank can't carry yet, or their own egg's stand standing empty
local function findInfoStands(root, rankName, taking)
    local found = {}
    if not root or player:GetAttribute("CarryingEgg") then
        return found
    end
    eachStand(function(stand, pedestal)
        if taking[stand] or (pedestal.Position - root.Position).Magnitude > INFO_RANGE then
            return
        end
        local eggId = stand:GetAttribute("EggId")
        local backAt = stand:GetAttribute("EggBackAt")
        if eggId and not canCarry(rankName, eggId) then
            local needs = Ranks.getRankById(GameConfig.Eggs[eggId].RequiredRank).Name
            table.insert(found, { stand = stand, pedestal = pedestal, kind = "locked", text = "NEEDS " .. string.upper(needs) })
        elseif not eggId and typeof(backAt) == "number" and canCarry(rankName, stand.Name) then
            table.insert(found, { stand = stand, pedestal = pedestal, kind = "back", text = "", backAt = backAt })
        end
    end)
    -- a word only over an egg in sight: drawn on the screen, the word of a stand behind the guardian sat over the next stand's egg
    local camera = Workspace.CurrentCamera
    if camera then
        local params = RaycastParams.new()
        params.FilterType = Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances = { player.Character }
        for _, entry in found do
            local from = camera.CFrame.Position
            local to = entry.pedestal.Position + INFO_MARK_ABOVE * 0.6
            local hit = Workspace:Raycast(from, to - from, params)
            entry.blocked = hit ~= nil and not hit.Instance:IsDescendantOf(entry.stand)
        end
    end
    -- the nearest first: where two words would cross, the nearer stand's shows
    table.sort(found, function(a, b)
        return (a.pedestal.Position - root.Position).Magnitude < (b.pedestal.Position - root.Position).Magnitude
    end)
    return found
end

local function refreshMarks(entries)
    local keep = {}
    for _, entry in entries do
        keep[entry.stand] = true
        local mark = takeMarks[entry.stand]
        if mark and mark:GetAttribute("Kind") ~= entry.kind then
            mark:Destroy()
            mark = nil
        end
        if not mark then
            markStand(entry.stand, entry.kind)
        end
        if entry.kind == "locked" then
            takeMarks[entry.stand].Word.Text = entry.text
        end
    end
    for stand, mark in takeMarks do
        if not keep[stand] then
            mark:Destroy()
            takeMarks[stand] = nil
        end
    end
end

-- Which of the island's eggs this player can carry, and when it is back on its stand ("" when none of them is theirs yet).
local function ownEggNews(config)
    local rankName = Ranks.getPlayerRankName(player)
    local soonest, soonestAt = nil, math.huge
    local islands = Workspace:FindFirstChild("FloatingIslands")
    local island = islands and islands:FindFirstChild(config.Island)
    local folder = island and island:FindFirstChild("EggStands")
    for _, eggId in config.Eggs do
        local stand = folder and folder:FindFirstChild(eggId)
        local backAt = stand and stand:GetAttribute("EggBackAt")
        if canCarry(rankName, eggId) and typeof(backAt) == "number" and backAt < soonestAt then
            soonest, soonestAt = eggId, backAt
        end
    end
    if not soonest then
        return ""
    end
    local left = math.max(1, math.ceil(soonestAt - Workspace:GetServerTimeNow()))
    return "The " .. GameConfig.Eggs[soonest].DisplayName .. " is back on its stand in " .. string.format("%d:%02d", left // 60, left % 60) .. "."
end

local function updateTakeIndicator()
    local id = player:GetAttribute("CanTakeEgg")
    local config = id and GameConfig.Guardians[id]
    local carrying = player:GetAttribute("CarryingEgg") ~= nil
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local camera = Workspace.CurrentCamera
    local now = os.clock()
    if now >= takeRefreshAt then
        takeRefreshAt = now + TAKE_REFRESH
        local rankName = Ranks.getPlayerRankName(player)
        eachStand(function(stand, _, prompt)
            stylePrompt(stand, prompt, rankName)
        end)
        takeStands = if config and not carrying then findTakeStands(config) else {}
        local taking = {}
        markStands = {}
        for _, entry in takeStands do
            entry.kind = "take"
            taking[entry.stand] = true
            table.insert(markStands, entry)
        end
        for _, entry in findInfoStands(root, rankName, taking) do
            table.insert(markStands, entry)
        end
        refreshMarks(markStands)
    end
    if camera then
        placeTakeMarks(camera, now)
    end
    if not config or carrying then
        takePanel.Visible = false
        wasAbleToTake = false
        return
    end
    if #takeStands == 0 then -- nothing here their rank can carry
        takePanel.Visible = false
        return
    end
    -- in the fight it waits while a notification is up: one thing at a time at the top of the screen
    takePanel.Visible = not Toast.showing()
    if not wasAbleToTake then
        wasAbleToTake = true
        Sfx.play("TakeReady")
        UiFx.flash(takePanel, WEAK_GOLD)
    end

    if not (root and camera) then
        return
    end
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
        takeHow.Text = if UiKit.usingTouch() then "Hold the Take button on the stand"
            else "Hold " .. nearest.prompt.KeyboardKeyCode.Name .. " at the stand"
    else
        takeArrow.Text = "^"
        local away = camera.CFrame:VectorToObjectSpace(nearest.pedestal.Position - root.Position)
        takeArrow.Rotation = math.deg(math.atan2(away.X, -away.Z))
        takeHow.Text = "Go to the stand: " .. math.floor(nearestDistance) .. " studs"
    end
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
local waypointMarker = nil -- its label on the screen (placeMarkers)
local function updateWaypoint()
    local guardianId = player:GetAttribute("CarryingGuardian")
    local model = guardianId and guardianModel(guardianId)
    local centre = model and model:GetAttribute("SafeZone")
    if not centre then
        if waypoint then
            waypoint:Destroy()
            waypoint = nil
        end
        WorldMarkers.drop(waypointMarker)
        waypointMarker = nil
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
    waypointMarker = WorldMarkers.new(GOLD, true)
    waypointMarker.world = anchor.Position
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
    if not (waypoint and waypointMarker and root) then
        return
    end
    local config = GameConfig.Guardians[player:GetAttribute("CarryingGuardian")]
    local distance = ((waypoint.Position - root.Position) * Vector3.new(1, 0, 1)).Magnitude
    waypointMarker.label.Text = string.upper(config.SafeZone.Name) .. "  " .. math.floor(distance) .. " studs"
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
            if mine then -- its thief is shown where it lies, at the screen's edge if it's out of view
                entry.marker = WorldMarkers.new(Color3.fromRGB(150, 210, 255), true)
                entry.countdown = entry.marker.label
            end
            dropped[egg] = entry
        elseif not isDropped and entry then
            if entry.beacon then
                entry.beacon:Destroy()
            end
            WorldMarkers.drop(entry.marker)
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
            WorldMarkers.drop(dropped[egg].marker)
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
            entry.countdown.Text = "PICK UP · " .. left .. "s"
            local body = egg.PrimaryPart
            entry.marker.world = body and body.Position + Vector3.new(0, 3.5, 0)
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
    GuardianBars.add(model)
    task.spawn(function()
        local anim = GuardianAnim.new(model, rig)
        if anim and model:IsDescendantOf(Workspace) then
            anims[model] = anim
            GuardianReact.bind(model, anim, rig) -- (it shows the blows the player lands: CombatFx)
        end
    end)
end
CollectionService:GetInstanceAddedSignal(GameConfig.GuardianTag):Connect(track)
CollectionService:GetInstanceRemovedSignal(GameConfig.GuardianTag):Connect(function(model)
    GuardianReact.unbind(model)
    anims[model] = nil
    rigs[model] = nil
    GuardianBars.remove(model)
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
        -- the reward stinger, flat, with the gold flash and this toast (the "Secure" every client gets follows: skipped here)
        securedAt = os.clock()
        Sfx.play("EggSecure")
        local egg = GameConfig.Eggs[eggId]
        local reward = if typeof(stones) == "number" and stones > 0 then " +" .. stones .. " Spirit Stones." else ""
        if typeof(qi) == "number" and qi > 0 then
            reward ..= " +" .. NumberFormat.compact(qi) .. " Qi."
        end
        local info = typeof(element) == "string" and GameConfig.Forge.Elements[element]
        local relic = if info then " Its relic unlocks " .. info.DisplayName .. " at the Blacksmith's forge." else ""
        message:show((egg and egg.DisplayName or "The egg") .. " is home safe! Hatch it at the Hatching Sanctum." .. reward .. relic, "Reward")
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
        markGround(model, config, action, ...)
    elseif EGG_SOUNDS[action] and not (action == "Secure" and os.clock() - securedAt < 1.5) then
        local egg = eggsFolder:FindFirstChild(model.Name .. "_Egg")
        local at = if typeof((...)) == "Vector3" then (...) else egg and egg.PrimaryPart
        Sfx.play(EGG_SOUNDS[action], at or model.PrimaryPart)
        if action == "Steal" then
            local alert = ALERTS[model:GetAttribute("GuardianId")]
            if alert and model.PrimaryPart then
                Sfx.after(ALERT_DELAY, alert, model.PrimaryPart)
            end
            if player:GetAttribute("CarryingGuardian") == model:GetAttribute("GuardianId") then
                Sfx.play("StealSting") -- the thief alone: it has seen you
            end
        end
    end
    if action == "Steal" then
        -- it has seen the egg taken: its rage move (the state is Enraged already, and the poses are blending)
        local anim = anims[model]
        if anim then
            anim:play("Enrage")
        end
        local fx = rig and rig.Fx.Enrage
        if fx then
            fx(model)
        end
    end
    if action == "Awaken" then
        if isNear(model, NEAR_DISTANCE) then
            message:show((config.Called or "The " .. config.DisplayName) .. " wakes up!", "Info")
        end
    elseif action == "Weaken" then
        if isNear(model, NEAR_DISTANCE) then
            local who = config.Called or "The " .. config.DisplayName
            -- told to take an egg only when one on its stands is theirs to carry: else which egg is theirs, and when it's back
            if #findTakeStands(config) > 0 or player:GetAttribute("CarryingEgg") then
                message:show(who .. " " .. config.WeakenedHint, "Info")
            else
                message:show(who .. " is weak, but no egg on its stands is for your rank right now. " .. ownEggNews(config), "Info")
            end
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
            message:show("You dropped the egg! Pick it up within " .. config.DropTime .. "s.", "Warning")
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
    GuardianBars.update(dt)
    updateOutline()
    updateTakeIndicator()
    updateWaypointText()
    updateCountdowns()
end)

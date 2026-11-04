-- The guardians on this client (the server decides everything, Guardian.lua):
--   - animates each guardian and plays its moves' effects from GuardianEvent, through its rig
--     (GuardianRigs/<GuardianId>; GuardianAnim drives it, GuardianFx gives the building blocks);
--   - knockback: a guardian's blow throws this player's character (the client owns it) off its
--     feet for a moment; nothing ever kills;
--   - the health bar of the guardian this player is fighting, with its state and weak mark;
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
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local GuardianAnim = require(script.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent:WaitForChild("GuardianFx"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local Hud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Hud"))
local UiKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiKit"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))

local player = Players.LocalPlayer

local ANIMATE_DISTANCE = 400
local BAR_DISTANCE = 130

local GOLD = Color3.fromRGB(232, 200, 120) -- the in-world waypoint to the safe zone
local NAME_COLOR = Color3.fromRGB(236, 246, 255)
local STATE_LOOK = {
    Guardian = { Text = "GUARDIAN", Color = Color3.fromRGB(120, 214, 255) },
    Weakened = { Text = "WEAKENED · TAKE AN EGG", Color = Color3.fromRGB(255, 196, 70) },
    Enraged = { Text = "ENRAGED", Color = Color3.fromRGB(255, 96, 50) },
}
local FILL = { -- the System's blue while it guards; red once enraged
    Calm = { Color3.fromRGB(120, 214, 255), Color3.fromRGB(26, 104, 196) },
    Rage = { Color3.fromRGB(255, 110, 120), Color3.fromRGB(176, 22, 44) },
}

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

local function guardianModel(guardianId)
    for _, model in CollectionService:GetTagged(GameConfig.GuardianTag) do
        if model:GetAttribute("GuardianId") == guardianId then
            return model
        end
    end
    return nil
end

-- ---------- the HUD ----------
local message = Toast.new(nil, "GuardianMessage", nil, Color3.new(1, 1, 1), 4)

-- the health bar of the guardian being fought: first in the HUD's top-centre stack, so the
-- messages (Toast) fall in below it instead of under it
local bar = UiKit.panel({ Name = "GuardianBar", Size = UDim2.fromOffset(460, 66), LayoutOrder = 0, Visible = false, Parent = Hud.Banner })
local barIcon = UiKit.icon(UiTheme.Icons.Guardian, 34, "Danger")
barIcon.Position = UDim2.fromOffset(14, 16)
barIcon.Parent = bar

local nameLabel = UiKit.label({
    Font = "Title", TextSize = 16, TextColor3 = NAME_COLOR, Position = UDim2.fromOffset(58, 9),
    Size = UDim2.new(0.6, -58, 0, 20), TextTruncate = Enum.TextTruncate.AtEnd, Parent = bar,
})

local stateLabel = UiKit.label({
    Font = "Strong", TextSize = 12, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -16, 0, 12),
    Size = UDim2.new(0.45, 0, 0, 16), TextXAlignment = Enum.TextXAlignment.Right, Parent = bar,
})

local barTrack = Instance.new("Frame")
barTrack.Position = UDim2.fromOffset(58, 34)
barTrack.Size = UDim2.new(1, -74, 0, 18)
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
weakMark.Size = UDim2.new(0, 2, 1, 0)
weakMark.ZIndex = 3
weakMark.Parent = barTrack

local healthText = Instance.new("TextLabel")
healthText.BackgroundTransparency = 1
healthText.Size = UDim2.fromScale(1, 1)
healthText.FontFace = UiTheme.Fonts.Strong
healthText.TextSize = 12
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

local shownTrail = 1
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
    bar.Visible = best ~= nil
    if not best then
        return
    end
    local config = GameConfig.Guardians[best:GetAttribute("GuardianId")]
    local state = best:GetAttribute("State")
    local health, maxHealth = best:GetAttribute("Health") or 0, best:GetAttribute("MaxHealth") or 1
    local share = math.clamp(health / maxHealth, 0, 1)
    nameLabel.Text = config and config.DisplayName or best.Name
    local look = STATE_LOOK[state]
    stateLabel.Text = look.Text
    stateLabel.TextColor3 = look.Color
    setFill(if state == "Enraged" then FILL.Rage else FILL.Calm)
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
        if knockToken == token and humanoid.Parent then
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
            entry.beacon:Destroy()
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
            dropped[egg].beacon:Destroy()
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
    local rigModule = rigsFolder:FindFirstChild(model:GetAttribute("GuardianId") or "")
    if not rigModule then
        warn("GuardianController: no rig for " .. model.Name)
        return
    end
    local rig = require(rigModule)
    rigs[model] = rig
    task.spawn(function()
        local anim = GuardianAnim.new(model, rig)
        if model:IsDescendantOf(Workspace) then
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
        message:show((egg and egg.DisplayName or "The egg") .. " secured! Hatch it at the Hatching Altar." .. reward .. relic, Color3.fromRGB(255, 214, 110))
        return
    elseif action == "BagFull" then
        Sfx.play("Error")
        message:show("You can't hold any more of that egg: hatch some first.", Color3.new(1, 1, 1))
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
            message:show((config.Called or "The " .. config.DisplayName) .. " awakens!", Color3.fromRGB(150, 210, 255))
        end
    elseif action == "Weaken" then
        if isNear(model, BAR_DISTANCE) then
            message:show((config.Called or "The " .. config.DisplayName) .. " " .. config.WeakenedHint, Color3.fromRGB(255, 214, 110))
        end
    elseif action == "Steal" and style then
        GuardianFx.steal((...), style)
        if player:GetAttribute("CarryingGuardian") == model:GetAttribute("GuardianId") then
            local goal = if config.SafeZone.Island then "Carry it home to " .. config.SafeZone.Name .. "!" else "Reach the " .. config.SafeZone.Name .. "!"
            message:show("You took the egg! " .. goal, Color3.fromRGB(255, 214, 110))
        end
    elseif action == "Drop" and style then
        GuardianFx.drop((...), style)
        local egg = eggsFolder:FindFirstChild(model.Name .. "_Egg")
        if egg and egg:GetAttribute("OwnerUserId") == player.UserId then
            message:show("You dropped the egg! Recover it within " .. config.DropTime .. "s.", Color3.new(1, 1, 1))
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
        elseif camera and model.PrimaryPart and (model.PrimaryPart.Position - camera.CFrame.Position).Magnitude <= ANIMATE_DISTANCE then
            anim:update(dt)
        end
    end
    updateBar(dt)
    updateWaypointText()
    updateCountdowns()
end)

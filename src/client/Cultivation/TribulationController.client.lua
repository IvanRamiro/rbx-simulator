-- The Heavenly Tribulation, drawn (the server runs it: server/Cultivation/Tribulation). For anyone's tribulation in sight:
-- a storm of dark cloud gathering over them, lightning flickering inside it; a ring of light on the ground where each bolt
-- will fall, filling as it comes; the bolt, a flash, a scorch and sparks. For one's own: a panel at the top (the realm,
-- the bolts left, the lives left), the world darkening under the storm, and a white flash and a shake when a bolt hits
-- (neither with Reduced Effects); then what came of it.
local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local ui = script.Parent.Parent:WaitForChild("UI")
local Hud = require(ui:WaitForChild("Hud"))
local Toast = require(ui:WaitForChild("Toast"))
local UiKit = require(ui:WaitForChild("UiKit"))
local UiTheme = require(ui:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local SIGHT = if Quality.Low then 160 else 320 -- studs from the camera past which another's tribulation isn't drawn (nearer on a phone)
local CLOUD = "rbxassetid://16867371255" -- a billowy cloud that swells and thins (Smoke and Cloud Texture Library, 4x4)
local STORM_DARK, STORM_LIT = Color3.fromRGB(34, 30, 52), Color3.fromRGB(86, 74, 120)
local RING = Color3.fromRGB(196, 168, 255)
local BOLT_CORE, BOLT_GLOW = Color3.fromRGB(250, 248, 255), Color3.fromRGB(150, 120, 255)

local function reduced()
    return player:GetAttribute("SettingReducedEffects") == true
end

local realmNames = {}
for _, rank in GameConfig.Ranks do
    if not table.find(realmNames, rank.Realm) then
        table.insert(realmNames, rank.Realm)
    end
end

local storms = {} -- [Player] = { folder, cloud, light, stopSound, rings = { [id] = parts }, cloudHeight }

local function rootOf(owner)
    local character = owner.Character
    return character and character:FindFirstChild("HumanoidRootPart")
end

local function inSight(position)
    local camera = Workspace.CurrentCamera
    return camera ~= nil and (camera.CFrame.Position - position).Magnitude <= SIGHT
end

local function part(props, parent)
    local p = Instance.new("Part")
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Material = Enum.Material.Neon
    for key, value in props do
        p[key] = value
    end
    p.Parent = parent
    return p
end

-- a flat disc lying on the ground (a cylinder stood on its end)
local function disc(position, diameter, color, transparency, parent)
    return part({
        Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.12, diameter, diameter), Color = color, Transparency = transparency,
        CFrame = CFrame.new(position) * CFrame.Angles(0, 0, math.pi / 2),
    }, parent)
end

-- ---------- the storm ----------
local function startStorm(owner, data)
    local root = rootOf(owner)
    if not root or (owner ~= player and not inSight(root.Position)) then -- (another's, far off: not drawn at all)
        return
    end
    local folder = Instance.new("Folder")
    folder.Name = "Tribulation_" .. owner.UserId
    folder.Parent = Workspace
    local cloud = part({ Name = "Storm", Transparency = 1, Size = Vector3.new(1, 1, 1), CFrame = CFrame.new(root.Position) }, folder)
    local billow = Instance.new("ParticleEmitter")
    billow.Name = "Cloud"
    billow.Texture = CLOUD
    billow.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    billow.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    billow.Shape = Enum.ParticleEmitterShape.Disc
    billow.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    billow.Rate = if reduced() or Quality.Low then 10 else 22 -- (thinner on a phone)
    billow.Lifetime = NumberRange.new(3.5, 5)
    billow.Speed = NumberRange.new(0.5, 2)
    billow.SpreadAngle = Vector2.new(180, 10)
    billow.RotSpeed = NumberRange.new(-12, 12)
    billow.Rotation = NumberRange.new(0, 360)
    billow.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 14), NumberSequenceKeypoint.new(1, 30) })
    billow.Color = ColorSequence.new(STORM_DARK, STORM_LIT)
    billow.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.15), NumberSequenceKeypoint.new(0.8, 0.3), NumberSequenceKeypoint.new(1, 1) })
    billow.LightEmission = 0
    billow.LightInfluence = 0.4
    billow.Parent = cloud
    -- the disc of cloud spreads wide over them (the emitter's Disc shape is scaled by its part)
    cloud.Size = Vector3.new(46, 2, 46)
    local light = Instance.new("PointLight")
    light.Color = BOLT_GLOW
    light.Range = 60
    light.Brightness = 0
    light.Shadows = false
    light.Parent = cloud
    local stopSound = Sfx.loop("TribulationStorm", cloud)
    Sfx.play("TribulationGather", cloud)
    storms[owner] = { folder = folder, cloud = cloud, billow = billow, light = light, stopSound = stopSound, rings = {}, cloudHeight = data.CloudHeight or 55 }
end

local function endStorm(owner)
    local storm = storms[owner]
    if not storm then
        return
    end
    storms[owner] = nil
    storm.billow.Enabled = false
    if storm.stopSound then
        storm.stopSound()
    end
    for _, ring in storm.rings do
        for _, p in ring do
            p:Destroy()
        end
    end
    TweenService:Create(storm.light, TweenInfo.new(1), { Brightness = 0 }):Play()
    Debris:AddItem(storm.folder, 5.5)
end

-- the storm follows them; lightning flickers inside it
RunService.Heartbeat:Connect(function()
    for owner, storm in storms do
        local root = rootOf(owner)
        if root then
            storm.cloud.CFrame = CFrame.new(root.Position + Vector3.new(0, storm.cloudHeight, 0))
        end
        if math.random() < 0.04 then
            storm.light.Brightness = 3 + math.random() * 3
            TweenService:Create(storm.light, TweenInfo.new(0.25), { Brightness = 0 }):Play()
        end
    end
end)

-- ---------- rings and bolts ----------
local function showWarn(owner, data)
    local storm = storms[owner]
    if not storm or not inSight(data.Position) then
        return
    end
    local at = data.Position + Vector3.new(0, 0.08, 0)
    local d = data.Radius * 2
    local edge = disc(at, d, RING, 0.55, storm.folder)
    local fill = disc(at + Vector3.new(0, 0.02, 0), 0.4, RING, 0.35, storm.folder)
    local beam = part({ Size = Vector3.new(0.35, storm.cloudHeight, 0.35), Color = RING, Transparency = 0.85,
        CFrame = CFrame.new(at + Vector3.new(0, storm.cloudHeight / 2, 0)) }, storm.folder)
    -- the ring fills as its bolt comes: when it's full, it falls
    TweenService:Create(fill, TweenInfo.new(data.Delay, Enum.EasingStyle.Linear), { Size = Vector3.new(0.12, d, d) }):Play()
    TweenService:Create(beam, TweenInfo.new(data.Delay, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 0.45 }):Play()
    storm.rings[data.Id] = { edge, fill, beam }
    Sfx.play("TribulationArc", at)
end

local function bolt(from, to, width, color, transparency, folder)
    local segments = 9
    local last = from
    local parts = {}
    for k = 1, segments do
        local f = k / segments
        local at = from:Lerp(to, f)
        if k < segments then
            at += Vector3.new((math.random() - 0.5) * 5, 0, (math.random() - 0.5) * 5) * (1 - f * 0.6)
        end
        local length = (at - last).Magnitude
        table.insert(parts, part({ Size = Vector3.new(width, width, length), Color = color, Transparency = transparency,
            CFrame = CFrame.lookAt((last + at) / 2, at) }, folder))
        last = at
    end
    return parts
end

local function screenFlash()
    if reduced() then
        return
    end
    local gui = Instance.new("ScreenGui")
    gui.Name = "TribulationFlash"
    gui.IgnoreGuiInset = true
    gui.DisplayOrder = 50
    local flash = Instance.new("Frame")
    flash.BackgroundColor3 = Color3.new(1, 1, 1)
    flash.BackgroundTransparency = 0.25
    flash.BorderSizePixel = 0
    flash.Size = UDim2.fromScale(1, 1)
    flash.Parent = gui
    gui.Parent = player:WaitForChild("PlayerGui")
    TweenService:Create(flash, TweenInfo.new(0.45), { BackgroundTransparency = 1 }):Play()
    Debris:AddItem(gui, 0.5)
    -- a shake
    local camera = Workspace.CurrentCamera
    local start = os.clock()
    local name = "TribulationShake"
    RunService:BindToRenderStep(name, Enum.RenderPriority.Camera.Value + 1, function()
        local t = os.clock() - start
        if t > 0.35 or not camera then
            RunService:UnbindFromRenderStep(name)
            return
        end
        local k = 0.5 * (1 - t / 0.35)
        camera.CFrame *= CFrame.new((math.random() - 0.5) * k, (math.random() - 0.5) * k, 0)
    end)
end

local panel -- the local player's own panel, while their tribulation lasts

local function strike(owner, data)
    local storm = storms[owner]
    if not storm then
        return
    end
    local ring = storm.rings[data.Id]
    storm.rings[data.Id] = nil
    if ring then
        for _, p in ring do
            p:Destroy()
        end
    end
    if owner == player and panel then
        panel.setLives(data.Lives)
    end
    if owner == player and data.Hit then
        screenFlash()
        Sfx.play("Knockback")
    end
    if not inSight(data.Position) then
        return
    end
    local ground = data.Position
    local sky = ground + Vector3.new((math.random() - 0.5) * 6, storm.cloudHeight, (math.random() - 0.5) * 6)
    local parts = bolt(sky, ground, 0.35, BOLT_CORE, 0, storm.folder)
    for _, p in bolt(sky, ground, 1.3, BOLT_GLOW, 0.55, storm.folder) do
        table.insert(parts, p)
    end
    for _, p in parts do
        TweenService:Create(p, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.12), { Transparency = 1 }):Play()
        Debris:AddItem(p, 0.5)
    end
    local flash = part({ Shape = Enum.PartType.Ball, Size = Vector3.one * 3, Color = BOLT_CORE, Transparency = 0.1, CFrame = CFrame.new(ground + Vector3.new(0, 1, 0)) }, storm.folder)
    TweenService:Create(flash, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 14, Transparency = 1 }):Play()
    Debris:AddItem(flash, 0.4)
    local glow = Instance.new("PointLight")
    glow.Color = BOLT_GLOW
    glow.Range = 40
    glow.Brightness = 6
    glow.Shadows = false
    glow.Parent = flash
    storm.light.Brightness = 8
    TweenService:Create(storm.light, TweenInfo.new(0.4), { Brightness = 0 }):Play()
    -- a scorch where it fell, fading
    local scorch = disc(ground + Vector3.new(0, 0.05, 0), 5, Color3.fromRGB(24, 20, 30), 0.25, Workspace)
    scorch.Material = Enum.Material.SmoothPlastic
    TweenService:Create(scorch, TweenInfo.new(3, Enum.EasingStyle.Linear, Enum.EasingDirection.In, 0, false, 1), { Transparency = 1 }):Play()
    Debris:AddItem(scorch, 4.2)
    if not reduced() and not Quality.Low then
        local holder = part({ Transparency = 1, Size = Vector3.one * 0.2, CFrame = CFrame.lookAt(ground + Vector3.new(0, 0.5, 0), ground + Vector3.new(0, 5, 0)) }, Workspace)
        local sparks = Instance.new("ParticleEmitter")
        sparks.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        sparks.Enabled = false
        sparks.Lifetime = NumberRange.new(0.3, 0.7)
        sparks.Speed = NumberRange.new(10, 26)
        sparks.SpreadAngle = Vector2.new(75, 75)
        sparks.Acceleration = Vector3.new(0, -40, 0)
        sparks.Size = NumberSequence.new(0.5, 0)
        sparks.Color = ColorSequence.new(BOLT_CORE, BOLT_GLOW)
        sparks.LightEmission = 1
        sparks.Parent = holder
        sparks:Emit(22)
        Debris:AddItem(holder, 1)
    end
    Sfx.play("TribulationStrike", ground)
end

-- ---------- one's own panel ----------
local function makePanel(data)
    local frame = UiKit.panel({ Name = "TribulationPanel", Size = UDim2.fromOffset(340, 78), LayoutOrder = -10, Parent = Hud.Banner })
    local inner = UiKit.content(frame, 12, 8)
    UiKit.label({ Name = "Heading", Font = "Header", TextSize = 15, TextColor3 = C.Highlight, Text = "HEAVENLY TRIBULATION",
        Size = UDim2.new(1, -90, 0, 18), Parent = inner })
    UiKit.label({ Name = "Realm", Font = "Strong", TextSize = 12, TextColor3 = C.Text, Text = "Into the " .. (realmNames[data.Realm] or "next realm"),
        Position = UDim2.fromOffset(0, 20), Size = UDim2.new(1, -90, 0, 16), Parent = inner })
    local left = UiKit.label({ Name = "Left", TextSize = 11, TextColor3 = C.Muted, Position = UDim2.fromOffset(0, 38), Size = UDim2.new(1, -90, 0, 14),
        Text = "Keep out of the rings of light", Parent = inner })
    local pips = {}
    for k = 1, data.Lives do
        local pip = Instance.new("Frame")
        pip.Name = "Life" .. k
        pip.AnchorPoint = Vector2.new(1, 0.5)
        pip.Position = UDim2.new(1, -6 - (data.Lives - k) * 26, 0, 22)
        pip.Size = UDim2.fromOffset(15, 15)
        pip.Rotation = 45
        pip.BackgroundColor3 = C.Highlight
        pip.BorderSizePixel = 0
        pip.Parent = inner
        UiKit.corner(pip, 2)
        pips[k] = pip
    end
    return {
        frame = frame,
        setLeft = function(n)
            left.Text = if n > 0 then n .. " bolts to come: keep out of the rings" else "The last bolt falls"
        end,
        setLives = function(n)
            for k, pip in pips do
                local alive = k <= n
                pip.BackgroundColor3 = if alive then C.Highlight else C.DangerDeep
                pip.BackgroundTransparency = if alive then 0 else 0.3
            end
        end,
    }
end

local notice = Toast.new("TribulationMessage", C.Highlight, 5)
local grade = nil

RemoteEvents.TribulationEvent.OnClientEvent:Connect(function(kind, owner, data)
    if typeof(owner) ~= "Instance" or not owner:IsA("Player") then
        return
    end
    if kind == "Start" then
        startStorm(owner, data)
        if owner == player then
            if panel then
                panel.frame:Destroy()
            end
            panel = makePanel(data)
            notice:show("THE HEAVENS TEST YOU: survive the lightning", C.Highlight)
            if not reduced() then
                grade = Instance.new("ColorCorrectionEffect")
                grade.Name = "TribulationDark"
                grade.Parent = Lighting
                TweenService:Create(grade, TweenInfo.new(2), { Brightness = -0.08, Saturation = -0.3, TintColor = Color3.fromRGB(214, 206, 240) }):Play()
            end
        end
    elseif kind == "Warn" then
        showWarn(owner, data)
        if owner == player and panel then
            panel.setLeft(data.Left)
        end
    elseif kind == "Strike" then
        strike(owner, data)
    elseif kind == "End" then
        endStorm(owner)
        if owner == player then
            if panel then
                panel.frame:Destroy()
                panel = nil
            end
            if grade then
                local g = grade
                grade = nil
                TweenService:Create(g, TweenInfo.new(1.5), { Brightness = 0, Saturation = 0, TintColor = Color3.new(1, 1, 1) }):Play()
                Debris:AddItem(g, 1.6)
            end
            if data.Passed then
                notice:show("TRIBULATION SURVIVED: the realm is yours", C.Highlight)
            elseif not data.Cancelled then
                notice:show("THE HEAVENS STRUCK YOU DOWN: gather yourself and try again in a minute", C.Danger)
                Sfx.play("Error")
            end
        end
    end
end)

Players.PlayerRemoving:Connect(endStorm)

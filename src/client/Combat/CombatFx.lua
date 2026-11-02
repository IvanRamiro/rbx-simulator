-- Strike effects and poses (client-only, cosmetic: the server decides every hit, CombatService).
--
--   Palm   a Qi Palm: the right palm thrusts forward and a great hand of Qi (the QiPalm print)
--          flies from it, swelling and fading as it travels, with a ripple and wind streaks.
--   Sword  the flying sword darts out from over the right shoulder and sweeps an arc in front,
--          drawing a sheet of sword light behind it, with a crescent of light at the arc's height;
--          the hand directs it with a sword gesture.
--   hit    where a strike lands: a burst of light, a shockwave and scattering sparks.
--
-- Colours follow the striker's realm (QinggongFx.palette). Other players' strikes arrive through
-- CombatEvent and are skipped beyond MAX_DISTANCE.
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local AuraKit = require(script.Parent.Parent:WaitForChild("Auras"):WaitForChild("AuraKit"))
local QinggongFx = require(script.Parent.Parent:WaitForChild("Qinggong"):WaitForChild("QinggongFx"))

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local CombatFx = {}

local TEXTURES = {
    Palm = "rbxassetid://99797307127325",     -- QiPalm (tools/blender/vfx/combat_textures.py)
    Slash = "rbxassetid://77516609955713",    -- QiSlash
    Glow = "rbxassetid://135169457468310",
    Shockwave = "rbxassetid://130173906719836",
    Streak = "rbxassetid://115312010132075",
}
local MAX_DISTANCE = 250
local POSE_TIME = { Palm = 0.3, Sword = 0.38, Spear = 0.42 }
local SWORD_TIME = 0.3
local SPEAR_TIME = 0.36

local fxFolder = Instance.new("Folder")
fxFolder.Name = "CombatFx"
fxFolder.Parent = Workspace

local strikes = {} -- [player] = { weapon, until }

local function rootOf(player)
    local character = player.Character
    return character and character:FindFirstChild("HumanoidRootPart")
end

local function host(cframe, size, life)
    local part = Instance.new("Part")
    part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
    part.Transparency = 1
    part.Size = size
    part.CFrame = cframe
    part.Parent = fxFolder
    Debris:AddItem(part, life)
    return part
end

local function emitter(parent, properties)
    local e = Instance.new("ParticleEmitter")
    e.Rate = 0
    e.LightInfluence = 0
    e.LightEmission = 1
    for k, v in properties do
        e[k] = v
    end
    e.Parent = parent
    return e
end

local function flat(face, image, color, transparency)
    local gui = Instance.new("SurfaceGui")
    gui.Face = face
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = 30
    gui.LightInfluence = 0
    gui.Brightness = 2.2
    gui.AlwaysOnTop = false
    local label = Instance.new("ImageLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.Image = image
    label.ImageColor3 = color
    label.ImageTransparency = transparency
    label.Parent = gui
    return gui, label
end

-- ---------- the Qi Palm ----------
local function palm(p, root)
    local look = root.CFrame.LookVector
    local start = root.Position + look * 2 + Vector3.new(0, 0.6, 0)
    local frame = CFrame.lookAt(start, start + look)
    local plate = host(frame, Vector3.new(2.6, 2.6, 0.05), 0.7)
    local labels = {}
    -- a deeper tone than the palette's Main: the pale realm colours read as a faint ghost here
    local tone = p.Main:Lerp(p.Deep, 0.45)
    for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
        local gui, label = flat(face, TEXTURES.Palm, tone, 0)
        gui.Brightness = 3
        gui.Parent = plate
        table.insert(labels, label)
    end
    TweenService:Create(plate, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        { Size = Vector3.new(8, 8, 0.05), CFrame = frame + look * 7 }):Play()
    for _, label in labels do
        TweenService:Create(label, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.15), { ImageTransparency = 1 }):Play()
    end
    local burst = host(frame, Vector3.new(0.4, 0.4, 0.4), 0.8)
    emitter(burst, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.22),
        Size = numberSequence({ { 0, 1.2 }, { 1, 4 } }), Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
    }):Emit(1)
    emitter(burst, {
        Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(30, 44), SpreadAngle = Vector2.new(14, 14), Lifetime = NumberRange.new(0.14, 0.2),
        Size = numberSequence({ { 0, 1.5 }, { 1, 0.4 } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.2,
    }):Emit(8)
end

-- ---------- the sword strike ----------
-- the sword's glow: the same realm colour as the sword ridden in flight (FlightService), not the
-- effect palette, whose pale violet Neon turns pink
local function swordGlow(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and GameConfig.SwordFlight.RealmGlow[rank.Realm] or GameConfig.SwordFlight.DefaultGlow
end

local swordSource = nil
local function swordModel(player)
    swordSource = swordSource or (ReplicatedStorage:FindFirstChild("Weapons") and ReplicatedStorage.Weapons:FindFirstChild("FlyingSword"))
    if not swordSource then
        return nil
    end
    local model = Instance.new("Model")
    local parts = {}
    for _, piece in swordSource:GetChildren() do
        local part = piece:Clone()
        part.Anchored = true
        if piece:GetAttribute("Glow") then
            part.Color = swordGlow(player)
            part.Transparency = if part.Name == "Edge" then 0.3 else 0
        end
        part.Parent = model
        parts[part] = piece:GetAttribute("Offset")
    end
    model.Parent = fxFolder
    return model, parts
end

local function sword(player, p, root)
    local model, parts = swordModel(player)
    if not model then
        return
    end
    local body = model:FindFirstChild("Body")
    local hiltA, tipA = Instance.new("Attachment"), Instance.new("Attachment")
    local bodyOffset = parts[body]
    hiltA.Position = bodyOffset:PointToObjectSpace(Vector3.new(0, 0, 1.2))
    tipA.Position = bodyOffset:PointToObjectSpace(Vector3.new(0, 0, -4.3))
    hiltA.Parent, tipA.Parent = body, body
    local trail = Instance.new("Trail")
    trail.Attachment0, trail.Attachment1 = hiltA, tipA
    trail.Lifetime = 0.22
    trail.FaceCamera = false
    trail.LightEmission = 0.8
    trail.LightInfluence = 0
    trail.Texture = TEXTURES.Glow
    trail.TextureMode = Enum.TextureMode.Stretch
    trail.Color = colorSequence({ { 0, p.Core }, { 1, p.Main } })
    trail.Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } })
    trail.Parent = body

    -- the path: from over the right shoulder, across the front, ending low on the left
    local start = os.clock()
    local function at(t)
        local frame = root.CFrame
        local a = math.rad(-75 + 180 * t)
        local reach = 4.5 + 3 * math.sin(math.pi * t)
        local local_ = Vector3.new(math.cos(a) * reach * -1, 2.4 - 1.8 * t, -math.abs(math.sin(a)) * reach - 1.5 * t)
        return frame:PointToWorldSpace(local_)
    end
    local connection
    connection = RunService.RenderStepped:Connect(function()
        local t = math.clamp((os.clock() - start) / SWORD_TIME, 0, 1)
        local position = at(t)
        local ahead = at(math.min(1, t + 0.04))
        local direction = ahead - position
        if direction.Magnitude < 1e-3 then
            direction = root.CFrame.LookVector
        end
        local origin = CFrame.lookAt(position, position + direction) * CFrame.Angles(0, 0, math.rad(90))
        for part, offset in parts do
            part.CFrame = origin * offset
        end
        if t >= 1 then
            connection:Disconnect()
            trail.Enabled = false
            Debris:AddItem(model, 0.3)
        end
    end)
    local front = root.CFrame * CFrame.new(0, 0.8, -5)
    local holder = host(front, Vector3.new(0.4, 0.4, 0.4), 0.8)
    emitter(holder, {
        Texture = TEXTURES.Slash, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.24), Rotation = NumberRange.new(-12, 12),
        Size = numberSequence({ { 0, 5 }, { 1, 9 } }), Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
    }):Emit(1)
end

-- ---------- the spear thrust ----------
-- A spear of Qi light in the realm's colour (until each tier's spear is modelled): drawn back at the
-- right hip, driven straight ahead, held a beat and gone, a lance of streaks running on to the
-- spear's reach (GameConfig.WeaponKinds.Spear.Range).
local function spear(player, p, root)
    local glow = swordGlow(player)
    local function piece(size, color, transparency)
        local part = Instance.new("Part")
        part.Size = size
        part.Color = color
        part.Material = Enum.Material.Neon
        part.Transparency = transparency
        part.Anchored = true
        part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = false, false, false, false
        part.Parent = fxFolder
        return part
    end
    local shaft = piece(Vector3.new(0.2, 0.2, 7), glow, 0.25)
    local head = piece(Vector3.new(0.55, 0.55, 1.5), p.Core, 0)
    local tail, tip = Instance.new("Attachment"), Instance.new("Attachment")
    tail.Position, tip.Position = Vector3.new(0, 0, 3.5), Vector3.new(0, 0, -3.5)
    tail.Parent, tip.Parent = shaft, shaft
    local trail = Instance.new("Trail")
    trail.Attachment0, trail.Attachment1 = tail, tip
    trail.Lifetime = 0.12
    trail.FaceCamera = true
    trail.LightEmission = 0.8
    trail.LightInfluence = 0
    trail.Texture = TEXTURES.Glow
    trail.Color = colorSequence({ { 0, p.Core }, { 1, glow } })
    trail.Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } })
    trail.Parent = shaft

    local start = os.clock()
    local struck = false
    local connection
    connection = RunService.RenderStepped:Connect(function()
        local t = math.clamp((os.clock() - start) / SPEAR_TIME, 0, 1)
        -- drawn back, then driven forward fast and eased out, held, then fading
        local drive = math.clamp((t - 0.15) / 0.25, 0, 1)
        local reach = -1.5 + 6.5 * (1 - (1 - drive) ^ 3)
        local frame = root.CFrame * CFrame.new(0.9, 0.5, -1 - reach)
        shaft.CFrame = frame
        head.CFrame = frame * CFrame.new(0, 0, -4.2) * CFrame.Angles(0, 0, math.rad(45))
        local fade = math.clamp((t - 0.7) / 0.3, 0, 1)
        shaft.Transparency = 0.25 + 0.75 * fade
        head.Transparency = fade
        if drive >= 1 and not struck then
            struck = true
            local holder = host(head.CFrame, Vector3.new(0.4, 0.4, 0.4), 0.6)
            emitter(holder, {
                Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
                Speed = NumberRange.new(55, 70), SpreadAngle = Vector2.new(3, 3), Lifetime = NumberRange.new(0.16, 0.22), Drag = 2,
                Size = numberSequence({ { 0, 1.6 }, { 1, 0.3 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
                Color = colorSequence({ { 0, p.Core }, { 1, glow } }), Brightness = 2.4,
            }):Emit(6)
            emitter(holder, {
                Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.16),
                Size = numberSequence({ { 0, 1 }, { 1, 3.2 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
                Color = colorSequence({ { 0, p.Core }, { 1, glow } }), Brightness = 2,
            }):Emit(1)
        end
        if t >= 1 then
            connection:Disconnect()
            shaft:Destroy()
            head:Destroy()
        end
    end)
end

-- ---------- where a strike lands ----------
function CombatFx.hit(player, position)
    local p = QinggongFx.palette(player)
    local holder = host(CFrame.new(position), Vector3.new(0.4, 0.4, 0.4), 1)
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.18), ZOffset = 1,
        Size = numberSequence({ { 0, 2.5 }, { 1, 5 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Accent }, { 1, p.Main } }), Brightness = 2.5,
    }):Emit(1)
    emitter(holder, {
        Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.3), ZOffset = 0.8,
        Size = numberSequence({ { 0, 1 }, { 1, 7 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
    }):Emit(1)
    emitter(holder, {
        Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, SpreadAngle = Vector2.new(180, 180),
        Speed = NumberRange.new(20, 34), Drag = 4, Lifetime = NumberRange.new(0.2, 0.32),
        Size = numberSequence({ { 0, 1.1 }, { 1, 0.2 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.4,
    }):Emit(10)
end

-- ---------- entry points ----------
function CombatFx.play(player, weapon)
    local root = rootOf(player)
    if not root then
        return
    end
    strikes[player] = { weapon = weapon, untilTime = os.clock() + (POSE_TIME[weapon] or 0.3) }
    local camera = Workspace.CurrentCamera
    if player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE) then
        return
    end
    local p = QinggongFx.palette(player)
    if weapon == "Sword" then
        sword(player, p, root)
    elseif weapon == "Spear" then
        spear(player, p, root)
    else
        palm(p, root)
    end
end

-- The strike pose a player is in ("Palm", "Sword", "Spear") or nil; PoseController reads it.
function CombatFx.pose(player)
    local strike = strikes[player]
    if strike and os.clock() < strike.untilTime then
        return strike.weapon
    end
    return nil
end

Players.PlayerRemoving:Connect(function(player)
    strikes[player] = nil
end)

return CombatFx

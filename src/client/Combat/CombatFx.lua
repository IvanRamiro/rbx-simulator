-- Strike effects and poses (client-only, cosmetic: the server decides every hit, CombatService).
--
--   Palm   a Qi Palm: the right palm thrusts forward and a great hand of Qi (the QiPalm print)
--          flies from it, swelling and fading as it travels, with a ripple and wind streaks.
--   Sword  the striker's sword (their realm sword, or else the flying sword) darts out from over
--          the right shoulder and sweeps an arc in front, drawing a sheet of sword light behind it,
--          with a crescent of light at the arc's height; the hand directs it with a sword gesture.
--   Spear  the striker's spear (or a spear of Qi light) driven straight ahead from the right hip.
--   hit    where a strike lands: a burst of light, a shockwave and scattering sparks.
--
-- A forged weapon (the striker's "WeaponElement", GameConfig.Forge) glows, trails and slashes in its
-- element's colours and bursts with its element where it strikes: Fire rising embers and a lick of
-- flame, Frost flying ice shards and cold mist, Wood tumbling leaves, Earth thrown rock and a ring
-- of dust, Wind whipping streaks and a gust ring, Void dark smoke with sparks of violet.
--
-- Otherwise colours follow the striker's realm (QinggongFx.palette). Other players' strikes arrive through
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
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local CombatFx = {}

local TEXTURES = {
    Palm = "rbxassetid://99797307127325",     -- QiPalm (tools/blender/vfx/combat_textures.py)
    Slash = "rbxassetid://77516609955713",    -- QiSlash
    Glow = "rbxassetid://135169457468310",
    Shockwave = "rbxassetid://130173906719836",
    Streak = "rbxassetid://115312010132075",
    Fire = "rbxasset://textures/particles/fire_main.dds",
    Smoke = "rbxasset://textures/particles/smoke_main.dds",
}
local MAX_DISTANCE = 250
local POSE_TIME = { Palm = 0.3, Sword = 0.38, Spear = 0.42 }
local SWORD_TIME = 0.3
local SPEAR_TIME = 0.36
local SWING = { Palm = "PalmStrike", Sword = "SwordSwing", Spear = "SpearThrust" } -- each strike's sound (SoundCatalog)

local fxFolder = Instance.new("Folder")
fxFolder.Name = "CombatFx"
fxFolder.Parent = Workspace

local strikes = {} -- [player] = { weapon, untilTime }

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

-- ---------- the weapons ----------
-- the flying sword's glow: the same realm colour as the sword ridden in flight (FlightService), not
-- the effect palette, whose pale violet Neon turns pink
local function swordGlow(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and GameConfig.SwordFlight.RealmGlow[rank.Realm] or GameConfig.SwordFlight.DefaultGlow
end

-- What a strike of `kind` shows: the striker's own weapon (their "WeaponId", a realm weapon in
-- ReplicatedStorage.Weapons) when it is of that kind; otherwise, for a sword, the flying sword
-- (second result true: its glow takes the striker's realm colour). Nil: no model (the spear of light).
local function weaponSource(player, kind)
    local folder = ReplicatedStorage:FindFirstChild("Weapons")
    if not folder then
        return nil, false
    end
    local own = folder:FindFirstChild(player:GetAttribute("WeaponId") or "")
    if own and own:GetAttribute("Kind") == kind then
        return own, false
    end
    if kind == "Sword" then
        return folder:FindFirstChild("FlyingSword"), true
    end
    return nil, false
end

-- The striker's forged element for a realm weapon: its name and GameConfig.Forge.Elements entry, or nil.
local function elementOf(player, source, flying)
    local name = not flying and source and player:GetAttribute("WeaponElement")
    local info = typeof(name) == "string" and GameConfig.Forge.Elements[name]
    if info then
        return name, info
    end
    return nil, nil
end

-- The palette a strike draws with: the element's colours over the realm's.
local function strikePalette(p, element)
    if not element then
        return p
    end
    local q = table.clone(p)
    q.Core, q.Main = element.Core, element.Color
    return q
end

-- A copy of a stored weapon in the effects folder: the model and { [part] = its Offset from the
-- weapon's origin }. Glow pieces take `tint` (the realm's for the flying sword, a forged element's).
local function weaponModel(source, tint, flying)
    local model = Instance.new("Model")
    local parts = {}
    for _, piece in source:GetChildren() do
        local part = piece:Clone()
        part.Anchored = true
        if tint and piece:GetAttribute("Glow") then
            part.Color = tint
            part.Transparency = if flying and part.Name == "Edge" then 0.3 else 0
        end
        part.Parent = model
        parts[part] = piece:GetAttribute("Offset")
    end
    model.Parent = fxFolder
    return model, parts
end

-- Two attachments on `part` (whose Offset from the weapon's origin is `offset`) at weapon-space
-- points a and b, joined by a glowing trail.
local function weaponTrail(part, offset, a, b, p, glow, lifetime, faceCamera, transparency)
    local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
    a0.Position, a1.Position = offset:PointToObjectSpace(a), offset:PointToObjectSpace(b)
    a0.Parent, a1.Parent = part, part
    local trail = Instance.new("Trail")
    trail.Attachment0, trail.Attachment1 = a0, a1
    trail.Lifetime = lifetime
    trail.FaceCamera = faceCamera
    trail.LightEmission = 0.8
    trail.LightInfluence = 0
    trail.Texture = TEXTURES.Glow
    trail.TextureMode = Enum.TextureMode.Stretch
    trail.Color = colorSequence({ { 0, p.Core }, { 1, glow } })
    trail.Transparency = numberSequence({ { 0, transparency }, { 1, 1 } })
    trail.Parent = part
    return trail
end

-- ---------- the elements' bursts ----------
local function sequenceOf(element)
    return colorSequence({ { 0, element.Core }, { 1, element.Color } })
end

local ELEMENT_BURSTS = {
    Fire = function(holder, e)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(6, 12), SpreadAngle = Vector2.new(60, 60), Acceleration = Vector3.new(0, 14, 0),
            Drag = 2, Lifetime = NumberRange.new(0.5, 0.8), Size = numberSequence({ { 0, 0.35 }, { 1, 0 } }),
            Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }), Color = sequenceOf(e), Brightness = 3,
        }):Emit(14)
        emitter(holder, {
            Texture = TEXTURES.Fire, Speed = NumberRange.new(2, 4), Lifetime = NumberRange.new(0.3, 0.4), Rotation = NumberRange.new(-30, 30),
            Size = numberSequence({ { 0, 1.8 }, { 1, 0.4 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }), Color = sequenceOf(e),
            Brightness = 2,
        }):Emit(4)
    end,
    Frost = function(holder, e)
        emitter(holder, {
            Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, Speed = NumberRange.new(18, 28),
            SpreadAngle = Vector2.new(180, 180), Drag = 5, Acceleration = Vector3.new(0, -12, 0), Lifetime = NumberRange.new(0.4, 0.6),
            Size = numberSequence({ { 0, 0.9 }, { 1, 0.1 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }), Color = sequenceOf(e),
            Brightness = 2.4,
        }):Emit(12)
        emitter(holder, {
            Texture = TEXTURES.Smoke, Speed = NumberRange.new(1, 2), Lifetime = NumberRange.new(0.8), LightEmission = 0.3,
            Size = numberSequence({ { 0, 2 }, { 1, 5 } }), Transparency = numberSequence({ { 0, 0.6 }, { 1, 1 } }),
            Color = ColorSequence.new(e.Core),
        }):Emit(3)
    end,
    Wood = function(holder, e)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(6, 10), SpreadAngle = Vector2.new(120, 120), Acceleration = Vector3.new(0, -6, 0),
            Drag = 1.5, Lifetime = NumberRange.new(0.8, 1.1), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-180, 180),
            Squash = numberSequence({ { 0, 0.6 }, { 1, 0.6 } }), Size = numberSequence({ { 0, 0.4 }, { 1, 0.25 } }),
            Transparency = numberSequence({ { 0, 0 }, { 0.8, 0.2 }, { 1, 1 } }), Color = sequenceOf(e), LightEmission = 0.6, Brightness = 1.6,
        }):Emit(12)
    end,
    Earth = function(holder, e)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(10, 16), SpreadAngle = Vector2.new(50, 50), Acceleration = Vector3.new(0, -40, 0),
            Lifetime = NumberRange.new(0.5, 0.7), Size = numberSequence({ { 0, 0.45 }, { 1, 0.25 } }), LightEmission = 0.2,
            Transparency = numberSequence({ { 0, 0 }, { 1, 0.6 } }), Color = ColorSequence.new(e.Color, Color3.fromRGB(90, 60, 30)), Brightness = 1.2,
        }):Emit(12)
        emitter(holder, {
            Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.35), Size = numberSequence({ { 0, 1 }, { 1, 6 } }),
            Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }), Color = sequenceOf(e), Brightness = 1.5,
        }):Emit(1)
    end,
    Wind = function(holder, e)
        emitter(holder, {
            Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, Speed = NumberRange.new(20, 30),
            SpreadAngle = Vector2.new(180, 30), Drag = 4, Lifetime = NumberRange.new(0.3, 0.4), Size = numberSequence({ { 0, 1.4 }, { 1, 0.2 } }),
            Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }), Color = sequenceOf(e), Brightness = 2,
        }):Emit(10)
        emitter(holder, {
            Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.3), Size = numberSequence({ { 0, 1 }, { 1, 8 } }),
            Transparency = numberSequence({ { 0, 0.4 }, { 1, 1 } }), Color = ColorSequence.new(e.Core), Brightness = 1.5,
        }):Emit(1)
    end,
    Void = function(holder, e)
        emitter(holder, {
            Texture = TEXTURES.Smoke, Speed = NumberRange.new(2, 4), Lifetime = NumberRange.new(0.6), LightEmission = 0,
            Size = numberSequence({ { 0, 1 }, { 1, 3.5 } }), Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }),
            Color = ColorSequence.new(Color3.fromRGB(20, 4, 40), e.Color:Lerp(Color3.new(), 0.6)),
        }):Emit(4)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(10, 14), SpreadAngle = Vector2.new(180, 180), Drag = 6,
            Lifetime = NumberRange.new(0.35, 0.5), Size = numberSequence({ { 0, 0.3 }, { 1, 0 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
            Color = sequenceOf(e), Brightness = 2.6,
        }):Emit(10)
    end,
}

local function elementBurst(name, cframe)
    local burst = ELEMENT_BURSTS[name]
    if burst then
        burst(host(cframe, Vector3.new(0.4, 0.4, 0.4), 1.4), GameConfig.Forge.Elements[name])
    end
end

-- ---------- the sword strike ----------
local function sword(player, p, root)
    local source, flying = weaponSource(player, "Sword")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, flying)
    p = strikePalette(p, element)
    local model, parts = weaponModel(source, if flying then swordGlow(player) else element and element.Color, flying)
    local body = model:FindFirstChild("Body")
    -- the flying sword rides the arc by its origin; a realm sword by its blade's middle
    local hilt = source:GetAttribute("Hilt") or Vector3.new(0, 0, 1.2)
    local tip = source:GetAttribute("Tip") or Vector3.new(0, 0, -4.3)
    local centre = if flying then Vector3.zero else (hilt + tip) / 2
    local trail = weaponTrail(body, parts[body], hilt, tip, p, p.Main, 0.22, false, 0.2)

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
        local origin = CFrame.lookAt(position, position + direction) * CFrame.Angles(0, 0, math.rad(90)) * CFrame.new(-centre)
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
    if elementName then
        elementBurst(elementName, front)
    end
end

-- ---------- the spear thrust ----------
-- The striker's spear (or, with none modelled, a spear of Qi light in the realm's colour): drawn
-- back at the right hip, driven straight ahead, held a beat and gone, a lance of streaks running on
-- to the spear's reach (GameConfig.WeaponKinds.Spear.Range). Positions are from the spear's grip.
local function lightSpear(glow, p)
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
    return { [shaft] = CFrame.new(0, 0, -1.2), [head] = CFrame.new(0, 0, -5.4) * CFrame.Angles(0, 0, math.rad(45)) }, shaft,
        Vector3.new(0, 0, 2.3), Vector3.new(0, 0, -6.2)
end

local function spear(player, p, root)
    local source = weaponSource(player, "Spear")
    local elementName, element = elementOf(player, source, false)
    p = strikePalette(p, element)
    local glow = if element then element.Color else swordGlow(player)
    local model, parts, anchor, tail, tip
    if source then
        model, parts = weaponModel(source, element and element.Color, false)
        anchor = model:FindFirstChild("Body")
        tip = source:GetAttribute("Tip")
        tail = source:GetAttribute("Hilt") + Vector3.new(0, 0, 3.5)
    else
        parts, anchor, tail, tip = lightSpear(glow, p)
    end
    local base = {}
    for part in parts do
        base[part] = part.Transparency
    end
    weaponTrail(anchor, parts[anchor], tail, tip, p, glow, 0.12, true, 0.3)

    local start = os.clock()
    local struck = false
    local connection
    connection = RunService.RenderStepped:Connect(function()
        local t = math.clamp((os.clock() - start) / SPEAR_TIME, 0, 1)
        -- drawn back, then driven forward fast and eased out, held, then fading
        local drive = math.clamp((t - 0.15) / 0.25, 0, 1)
        local reach = -1.5 + 6.5 * (1 - (1 - drive) ^ 3)
        local grip = root.CFrame * CFrame.new(0.9, 0.5, 0.2 - reach)
        local fade = math.clamp((t - 0.7) / 0.3, 0, 1)
        for part, offset in parts do
            part.CFrame = grip * offset
            part.Transparency = base[part] + (1 - base[part]) * fade
        end
        if drive >= 1 and not struck then
            struck = true
            local holder = host(grip * CFrame.new(tip), Vector3.new(0.4, 0.4, 0.4), 0.6)
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
            if elementName then
                elementBurst(elementName, grip * CFrame.new(tip))
            end
        end
        if t >= 1 then
            connection:Disconnect()
            if model then
                model:Destroy()
            else
                for part in parts do
                    part:Destroy()
                end
            end
        end
    end)
end

-- ---------- where a strike lands ----------
function CombatFx.hit(player, position)
    Sfx.play("QiImpact", position)
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
    Sfx.play(SWING[weapon] or "PalmStrike", root)
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

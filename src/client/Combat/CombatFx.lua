-- Strike effects and poses (client-only, cosmetic: the server decides every hit, CombatService).
--
--   Palm   a Qi Palm: the right palm thrusts forward and a great hand of Qi (the QiPalm print)
--          flies from it, swelling and fading as it travels, with a ripple and wind streaks.
--   Sword  the striker's sword (their realm sword, or else the flying sword) in their right hand: the
--          arm rises over the shoulder and cuts down across the body, the blade drawing a sheet of
--          light through the cut, with a crescent of light where it passes.
--   Spear  the striker's spear in both hands: drawn back, then driven straight ahead, a lance of
--          streaks running on to its reach.
--   hit    where a strike lands: a burst of light, a shockwave and scattering sparks.
--
-- The Qi skills (CombatFx.skill, GameConfig.Combat.Skills), in the striker's colours, an element's if
-- their weapon is forged:
--   SurgingPalm   a great hand of Qi flies far ahead, swelling, with a wake of streaks.
--   CrescentWave  a wide crescent of sword light flies far ahead, a gust behind it.
--   QiNova        a ring of Qi races out across the ground from the caster, who flares with light.
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
local WIND_UP = { Sword = 0.09, Spear = 0.1 } -- seconds before the blow lands
local WIND_UP_POSE = { Sword = "SwordRise", Spear = "SpearDraw" }
local BLOW_POSE = { Sword = "SwordCut", Spear = "Spear" }
local HOLD_TIME = 5      -- seconds a weapon stays in the hand after the last strike
-- a weapon's turn in the fist, from the hand's grip attachment (whose -Z runs down the forearm): a
-- sword's blade rises out of the fist; a spear's shaft runs along the forearm
local GRIP_TURN = { Sword = CFrame.Angles(math.rad(80), 0, 0), Spear = CFrame.identity }
local POSE_TIME = { Palm = 0.3, Sword = 0.42, Spear = 0.42, Nova = 0.5 }
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
-- ---------- the weapon in the hand ----------
-- A sword or spear is welded to the striker's right hand, so it moves exactly as the arm does, and
-- stays there HOLD_TIME after the last strike, in that kind's ready stance (PoseController's SwordReady,
-- SpearReady), put away sooner if they meditate, fly or die. The strike itself is the arm's motion:
-- a short wind-up (SwordRise, SpearDraw), then the blow (SwordCut, Spear). CombatFx.pose picks by time.
local held = {} -- [player] = { kind, model, trail, hand, source, untilTime }
local holdWatch = nil

local function putAway(player)
    local entry = held[player]
    if entry then
        held[player] = nil
        entry.model:Destroy()
    end
end

local function watchHeld()
    if holdWatch then
        return
    end
    holdWatch = RunService.Heartbeat:Connect(function()
        local now = os.clock()
        for player, entry in held do
            if now > entry.untilTime or not entry.hand:IsDescendantOf(Workspace)
                or player:GetAttribute("IsCultivating") == true or player:GetAttribute("IsFlying") == true then
                putAway(player)
            end
        end
        if next(held) == nil then
            holdWatch:Disconnect()
            holdWatch = nil
        end
    end)
end

-- the weapon in this player's hand, drawing it if it isn't there. spec: the trail's two weapon-space
-- points, its lifetime, whether it faces the camera, and its transparency
local function hold(player, kind, source, flying, tint, spec, p)
    local character = player.Character
    local hand = character and (character:FindFirstChild("RightHand") or character:FindFirstChild("Right Arm"))
    local gripPoint = hand and hand:FindFirstChild("RightGripAttachment")
    if not gripPoint then
        return nil
    end
    local entry = held[player]
    if entry and entry.source == source and entry.hand == hand then
        entry.untilTime = os.clock() + HOLD_TIME
        return entry
    end
    putAway(player)
    local model, parts = weaponModel(source, tint, flying)
    -- a weapon's origin is its grip (its Hilt attribute is where the blade starts): in the fist,
    -- turned for its kind (GRIP_TURN)
    local origin = gripPoint.CFrame * GRIP_TURN[kind]
    for part, offset in parts do
        part.Anchored = false
        part.Massless = true
        part.CanCollide, part.CanTouch, part.CanQuery = false, false, false
        local weld = Instance.new("Weld")
        weld.Part0, weld.Part1 = hand, part
        weld.C0 = origin * offset
        weld.Parent = part
    end
    local body = model:FindFirstChild("Body")
    local trail = weaponTrail(body, parts[body], spec.from, spec.to, p, spec.glow or p.Main, spec.life, spec.faceCamera, spec.transparency)
    trail.Enabled = false
    entry = { kind = kind, model = model, trail = trail, hand = hand, source = source, untilTime = os.clock() + HOLD_TIME }
    held[player] = entry
    watchHeld()
    return entry
end

-- the blow lands after the wind-up: the trail draws through it, and `effect` plays
local function afterWindUp(player, entry, windUp, duration, root, effect)
    task.delay(windUp, function()
        if entry and held[player] == entry then
            entry.trail.Enabled = true
            task.delay(duration, function()
                if entry.trail.Parent then
                    entry.trail.Enabled = false
                end
            end)
        end
        if root.Parent then
            effect()
        end
    end)
end

local function sword(player, p, root)
    local source, flying = weaponSource(player, "Sword")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, flying)
    p = strikePalette(p, element)
    local entry = hold(player, "Sword", source, flying, if flying then swordGlow(player) else element and element.Color, {
        from = source:GetAttribute("Hilt") or Vector3.new(0, 0, 1.2), to = source:GetAttribute("Tip") or Vector3.new(0, 0, -4.3),
        life = 0.22, faceCamera = false, transparency = 0.2,
    }, p)
    afterWindUp(player, entry, WIND_UP.Sword, SWORD_TIME, root, function()
        -- a crescent of light where the blade passes
        local front = root.CFrame * CFrame.new(0, 0.8, -5)
        local holder = host(front, Vector3.new(0.4, 0.4, 0.4), 0.8)
        emitter(holder, {
            Texture = TEXTURES.Slash, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.24), Rotation = NumberRange.new(-30, -10),
            Size = numberSequence({ { 0, 5 }, { 1, 9 } }), Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }),
            Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
        }):Emit(1)
        if elementName then
            elementBurst(elementName, front)
        end
    end)
end

local function spear(player, p, root)
    local source = weaponSource(player, "Spear")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, false)
    p = strikePalette(p, element)
    local glow = if element then element.Color else swordGlow(player)
    local entry = hold(player, "Spear", source, false, element and element.Color, {
        from = source:GetAttribute("Hilt") + Vector3.new(0, 0, 3.5), to = source:GetAttribute("Tip"),
        glow = glow, life = 0.12, faceCamera = true, transparency = 0.3,
    }, p)
    afterWindUp(player, entry, WIND_UP.Spear, SPEAR_TIME, root, function()
        -- a lance of streaks running on to the spear's reach
        local tip = root.CFrame * CFrame.new(0.4, 0.5, -7)
        local holder = host(tip, Vector3.new(0.4, 0.4, 0.4), 0.6)
        emitter(holder, {
            Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
            Speed = NumberRange.new(55, 70), SpreadAngle = Vector2.new(3, 3), Lifetime = NumberRange.new(0.16, 0.22),
            Size = numberSequence({ { 0, 1.6 }, { 1, 0.3 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
            Color = colorSequence({ { 0, p.Core }, { 1, glow } }), Brightness = 2.4,
        }):Emit(6)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.16),
            Size = numberSequence({ { 0, 1 }, { 1, 3.2 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
            Color = colorSequence({ { 0, p.Core }, { 1, glow } }), Brightness = 2,
        }):Emit(1)
        if elementName then
            elementBurst(elementName, tip)
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

-- ---------- the Qi skills ----------
-- a flat plate of light flying ahead of the caster, swelling and fading
local function flyingPlate(frame, look, image, tone, fromSize, toSize, distance, time)
    local plate = host(frame, fromSize, time + 0.2)
    for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
        local gui, label = flat(face, image, tone, 0)
        gui.Brightness = 3
        gui.Parent = plate
        TweenService:Create(label, TweenInfo.new(time * 0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, time * 0.5),
            { ImageTransparency = 1 }):Play()
    end
    TweenService:Create(plate, TweenInfo.new(time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        { Size = toSize, CFrame = frame + look * distance }):Play()
end

-- a burst of light and a wake of streaks at the caster's hand
local function castBurst(frame, p, streaks)
    local burst = host(frame, Vector3.new(0.4, 0.4, 0.4), 0.8)
    emitter(burst, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.25),
        Size = numberSequence({ { 0, 2 }, { 1, 6 } }), Transparency = numberSequence({ { 0, 0.25 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
    }):Emit(1)
    emitter(burst, {
        Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(40, 60), SpreadAngle = Vector2.new(12, 12), Lifetime = NumberRange.new(0.2, 0.3),
        Size = numberSequence({ { 0, 2 }, { 1, 0.4 } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.2,
    }):Emit(streaks)
end

local function surgingPalm(p, root)
    local look = root.CFrame.LookVector
    local start = root.Position + look * 2 + Vector3.new(0, 0.8, 0)
    local frame = CFrame.lookAt(start, start + look)
    flyingPlate(frame, look, TEXTURES.Palm, p.Main:Lerp(p.Deep, 0.45), Vector3.new(4, 4, 0.05), Vector3.new(16, 16, 0.05), 32, 0.55)
    castBurst(frame, p, 14)
end

local function crescentWave(p, root, player)
    -- with a sword in hand the wave leaves its swing
    local own = ReplicatedStorage:FindFirstChild("Weapons")
    own = own and own:FindFirstChild(player:GetAttribute("WeaponId") or "")
    if own and own:GetAttribute("Kind") == "Sword" then
        sword(player, p, root)
    end
    local look = root.CFrame.LookVector
    local start = root.Position + look * 2 + Vector3.new(0, 0.8, 0)
    local frame = CFrame.lookAt(start, start + look)
    flyingPlate(frame, look, TEXTURES.Slash, p.Main:Lerp(p.Deep, 0.3), Vector3.new(8, 4, 0.05), Vector3.new(22, 8, 0.05), 46, 0.6)
    castBurst(frame, p, 18)
end

local function qiNova(p, root)
    -- the ring lies flat on the ground under the caster
    local base = CFrame.new(root.Position - Vector3.new(0, 2.6, 0))
    local plate = host(base, Vector3.new(4, 0.05, 4), 0.8)
    local gui, label = flat(Enum.NormalId.Top, TEXTURES.Shockwave, p.Main, 0)
    gui.Brightness = 3
    gui.Parent = plate
    TweenService:Create(plate, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(58, 0.05, 58) }):Play()
    TweenService:Create(label, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.25), { ImageTransparency = 1 }):Play()
    local burst = host(root.CFrame, Vector3.new(0.4, 0.4, 0.4), 1)
    emitter(burst, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.32),
        Size = numberSequence({ { 0, 4 }, { 1, 12 } }), Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
    }):Emit(1)
    emitter(burst, {
        Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, SpreadAngle = Vector2.new(180, 20),
        EmissionDirection = Enum.NormalId.Front, Speed = NumberRange.new(44, 64), Drag = 3, Lifetime = NumberRange.new(0.25, 0.4),
        Size = numberSequence({ { 0, 2.2 }, { 1, 0.3 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.4,
    }):Emit(26)
end

local SKILLS = {
    SurgingPalm = { pose = "Palm", sound = "SkillPalm", play = surgingPalm },
    CrescentWave = { pose = "Sword", sound = "SkillWave", play = crescentWave },
    QiNova = { pose = "Nova", sound = "SkillNova", play = qiNova },
}

function CombatFx.skill(player, skillId)
    local skill = SKILLS[skillId]
    local root = rootOf(player)
    if not (skill and root) then
        return
    end
    strikes[player] = { weapon = skill.pose, started = os.clock(), untilTime = os.clock() + (POSE_TIME[skill.pose] or 0.3) + 0.1 }
    local camera = Workspace.CurrentCamera
    if player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE) then
        return
    end
    Sfx.play(skill.sound, root)
    local element = GameConfig.Forge.Elements[player:GetAttribute("WeaponElement") or ""]
    skill.play(strikePalette(QinggongFx.palette(player), element), root, player)
end

-- ---------- entry points ----------
function CombatFx.play(player, weapon)
    local root = rootOf(player)
    if not root then
        return
    end
    strikes[player] = { weapon = weapon, started = os.clock(), untilTime = os.clock() + (POSE_TIME[weapon] or 0.3) }
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

-- The pose a player is in, or nil; PoseController reads it. During a strike: "Palm", "SwordRise" then
-- "SwordCut", "SpearDraw" then "Spear", or "Nova". With a weapon out after it: "SwordReady", "SpearReady".
function CombatFx.pose(player)
    local strike = strikes[player]
    if strike and os.clock() < strike.untilTime then
        local windUp = WIND_UP[strike.weapon]
        if windUp then
            return if os.clock() - strike.started < windUp then WIND_UP_POSE[strike.weapon] else BLOW_POSE[strike.weapon]
        end
        return strike.weapon
    end
    local entry = held[player]
    return entry and entry.kind .. "Ready"
end

Players.PlayerRemoving:Connect(function(player)
    strikes[player] = nil
    putAway(player)
end)

return CombatFx

-- Strike effects and poses (client-only, cosmetic: the server decides every hit, CombatService).
--
--   Palm   a Qi Palm: the right palm thrusts forward and a great hand of Qi (the QiPalm print)
--          flies from it, swelling and fading as it travels, with a ripple and wind streaks.
--   Sword  the striker's sword (their realm sword, or else the flying sword) in their right hand, in
--          a combo of three slashes, each with its own line (SLASHES): a diagonal cut down across the
--          body, a backhand rising the other way, and an overhead finisher. The arm's motion is
--          PoseController's (SLASH_KEYS); here the blade draws a sheet of light through the swing and
--          a crescent of light sweeps out along the slash's plane.
--   Spear  the striker's spear in both hands, in a combo of two: a thrust, drawn back then driven
--          straight ahead with a lance of streaks running on to its reach; then a slash, the whole body
--          turning to sweep the shaft across the front (PoseController's SPEAR_SLASH_KEYS) with a wide
--          crescent of light along the tip's path.
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
local GuardianFx = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("GuardianFx"))

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local CombatFx = {}

-- slows the slashes for reviewing them: 1 is real time
CombatFx.TimeScale = 1

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
local WIND_UP = { Sword = 0.1, Spear = 0.1 } -- seconds before the blow lands
local SLASH_SWING = 0.14 -- seconds the blade draws its light
-- each slash of the combo. Its crescent lies on the arc the blade's tip really draws, measured from
-- the swing in root space (PoseController's SLASH_KEYS: re-measure if those change): the circle's
-- Centre and Radius, the way its plane faces (Face) and the way the arc bulges (Bulge). Then how much
-- it swells and how far it carries ahead; the finisher is the biggest, and shakes the striker's camera.
-- The first's radius reaches past the tip (3.26), or the body hides its low arc from the player's camera
local SLASHES = {
    { Centre = Vector3.new(-1.38, 1.95, -3.9), Radius = 4.4, Face = Vector3.new(0.56, -0.27, 0.78), Bulge = Vector3.new(0.51, -0.63, -0.58),
        Grow = 1.35, Travel = 3, Pitch = 1.05 },
    { Centre = Vector3.new(2.02, -0.45, -2.25), Radius = 4.59, Face = Vector3.new(-0.54, 0.5, 0.68), Bulge = Vector3.new(0.11, 0.84, -0.53),
        Grow = 1.35, Travel = 3, Pitch = 1.2 },
    { Centre = Vector3.new(-0.92, -1.1, -0.73), Radius = 5.31, Face = Vector3.new(0.83, 0.51, 0.23), Bulge = Vector3.new(0.21, 0.09, -0.97),
        Grow = 1.5, Travel = 4.5, Pitch = 0.82, Finisher = true },
}
-- the spear's slash, on the same terms: a wide flat arc round the striker
local SPEAR_SLASH = { Centre = Vector3.new(0, -0.7, 0), Radius = 6.8, Face = Vector3.new(0, 0.95, 0.31), Bulge = Vector3.new(0, 0.31, -0.95),
    Grow = 1.25, Travel = 2.5 }
local SPEAR_SWING = 0.2 -- seconds the spear's slash draws its light
-- the QiSlash texture's circle, as shares of the plate's half-width (tools/blender/vfx/combat_textures.py)
local CRESCENT_RADIUS, CRESCENT_DROP = 0.92, 0.3
local HOLD_TIME = 5      -- seconds a weapon stays in the hand after the last strike
local SPEAR_LOW_TIME = 1.4 -- seconds a spear stays in its low stance after a thrust
-- a weapon's turn in the fist, from the hand's grip attachment (whose -Z runs down the forearm): a
-- sword's blade rises out of the fist; a spear's shaft runs along the forearm
local GRIP_TURN = { Sword = CFrame.Angles(math.rad(80), 0, 0), Spear = CFrame.identity }
local POSE_TIME = { Palm = 0.3, Sword = 0.46, Spear = 0.42, SpearSlash = 0.5 }
local SPEAR_TIME = 0.36
local SWING = { Palm = "PalmStrike" } -- a strike's sound at once (SoundCatalog; a weapon's plays with its blow)

local fxFolder = Instance.new("Folder")
fxFolder.Name = "CombatFx"
fxFolder.Parent = Workspace

local COMBO_STEPS = { Sword = #SLASHES, Spear = 2 } -- how many strikes each weapon's combo has
local strikes = {} -- [player] = { weapon, started, untilTime, step (its place in the weapon's combo) }
local combos = {}  -- [player] = { weapon, step, at }: their last strike in a combo

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
-- SpearReady), put away sooner if they meditate or die, or once a strike made in flight is over. The
-- strike itself is the arm's motion (PoseController): a sword's SLASH_KEYS; a spear's SpearDraw, then Spear.
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
            local striking = strikes[player] ~= nil and now < strikes[player].untilTime
            local stale = now > entry.untilTime or player:GetAttribute("IsFlying") == true
            local humanoid = entry.hand.Parent and entry.hand.Parent:FindFirstChildOfClass("Humanoid")
            if not entry.hand:IsDescendantOf(Workspace) or not humanoid or humanoid.Health <= 0
                or player:GetAttribute("IsCultivating") == true or (stale and not striking) then
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

-- a crescent of light on the arc the blade draws, swelling and carrying ahead as it fades
local function slashCrescent(slash, p, root)
    local half = slash.Radius / CRESCENT_RADIUS
    local across = -slash.Bulge.Unit -- a Top face's gui has its top towards the part's -X, a Bottom's +X
    local along = across:Cross(slash.Face.Unit).Unit
    local frame = root.CFrame * CFrame.fromMatrix(slash.Centre + slash.Bulge.Unit * CRESCENT_DROP * half, across, along:Cross(across), along)
    local size = Vector3.new(half * 2, 0.05, half * 2)
    local scale = CombatFx.TimeScale
    local plate = host(frame, size, 0.5 / scale)
    for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
        local gui, label = flat(face, TEXTURES.Slash, p.Main:Lerp(p.Core, 0.25), 0.05)
        gui.Brightness = 2.6
        label.Rotation = if face == Enum.NormalId.Bottom then 180 else 0
        gui.Parent = plate
        TweenService:Create(label, TweenInfo.new(0.16 / scale, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.08 / scale),
            { ImageTransparency = 1 }):Play()
    end
    TweenService:Create(plate, TweenInfo.new(0.24 / scale, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        { Size = size * Vector3.new(slash.Grow, 1, slash.Grow), CFrame = frame + root.CFrame.LookVector * slash.Travel }):Play()
end

local function sword(player, p, root, step)
    local source, flying = weaponSource(player, "Sword")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, flying)
    p = strikePalette(p, element)
    local slash = SLASHES[step]
    local entry = hold(player, "Sword", source, flying, if flying then swordGlow(player) else element and element.Color, {
        from = source:GetAttribute("Hilt") or Vector3.new(0, 0, 1.2), to = source:GetAttribute("Tip") or Vector3.new(0, 0, -4.3),
        life = 0.22, faceCamera = false, transparency = 0.2,
    }, p)
    afterWindUp(player, entry, WIND_UP.Sword / CombatFx.TimeScale, SLASH_SWING / CombatFx.TimeScale, root, function()
        Sfx.play("SwordSwing", root, slash.Pitch)
        slashCrescent(slash, p, root)
        if slash.Finisher and player == Players.LocalPlayer then
            GuardianFx.shake(root.Position, 0.7, 0.2)
        end
        if elementName then
            elementBurst(elementName, root.CFrame * CFrame.new(slash.Centre + slash.Bulge.Unit * slash.Radius))
        end
    end)
end

local function spear(player, p, root, step)
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
    local scale = CombatFx.TimeScale
    if step == 2 then
        afterWindUp(player, entry, WIND_UP.Spear / scale, SPEAR_SWING / scale, root, function()
            Sfx.play("SwordSwing", root, 0.72)
            slashCrescent(SPEAR_SLASH, p, root)
            if elementName then
                elementBurst(elementName, root.CFrame * CFrame.new(SPEAR_SLASH.Centre + SPEAR_SLASH.Bulge.Unit * SPEAR_SLASH.Radius))
            end
        end)
        return
    end
    Sfx.play("SpearThrust", root)
    afterWindUp(player, entry, WIND_UP.Spear / scale, SPEAR_TIME / scale, root, function()
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

-- ---------- entry points ----------
function CombatFx.play(player, weapon)
    local root = rootOf(player)
    if not root then
        return
    end
    local now = os.clock()
    local strike = { weapon = weapon, started = now }
    local steps = COMBO_STEPS[weapon]
    if steps then
        local last = combos[player]
        local continuing = last and last.weapon == weapon and now - last.at < GameConfig.WeaponKinds[weapon].ComboWindow / CombatFx.TimeScale
        strike.step = if continuing then last.step % steps + 1 else 1
        combos[player] = { weapon = weapon, step = strike.step, at = now }
    end
    local poseTime = if weapon == "Spear" and strike.step == 2 then POSE_TIME.SpearSlash else POSE_TIME[weapon] or 0.3
    strike.untilTime = now + poseTime / CombatFx.TimeScale
    strikes[player] = strike
    local camera = Workspace.CurrentCamera
    if player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE) then
        return
    end
    if SWING[weapon] then
        Sfx.play(SWING[weapon], root)
    end
    local p = QinggongFx.palette(player)
    if weapon == "Sword" then
        sword(player, p, root, strike.step)
    elseif weapon == "Spear" then
        spear(player, p, root, strike.step)
    else
        palm(p, root)
    end
end

-- The pose a player is in, or nil; PoseController reads it. During a strike: "Palm", "Slash" or
-- "SpearSlash" (ask CombatFx.slash where in it they are), or "SpearDraw" then "Spear". With a weapon out after it:
-- "SwordReady"; a spear stays low a moment ("SpearLow"), then rises to its guard ("SpearReady").
function CombatFx.pose(player)
    local strike = strikes[player]
    if strike and os.clock() < strike.untilTime then
        if strike.weapon == "Sword" then
            return "Slash"
        elseif strike.weapon == "Spear" then
            if strike.step == 2 then
                return "SpearSlash"
            end
            return if (os.clock() - strike.started) * CombatFx.TimeScale < WIND_UP.Spear then "SpearDraw" else "Spear"
        end
        return strike.weapon
    end
    local entry = held[player]
    if entry and entry.kind == "Spear" and strike and os.clock() - strike.untilTime < SPEAR_LOW_TIME then
        return "SpearLow"
    end
    return entry and entry.kind .. "Ready"
end

-- Which strike of the combo a player is in, and how far through it in real-time seconds.
function CombatFx.slash(player)
    local strike = strikes[player]
    if strike and strike.step then
        return strike.step, (os.clock() - strike.started) * CombatFx.TimeScale
    end
    return 1, 0
end

Players.PlayerRemoving:Connect(function(player)
    strikes[player] = nil
    combos[player] = nil
    putAway(player)
end)

return CombatFx

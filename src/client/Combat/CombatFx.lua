-- Strike effects and poses (client-only, cosmetic: the server decides every hit, CombatService).
--
--   Palm   bare hands: a punch, right then left (WeaponClips), and a great hand of Qi (the QiPalm print)
--          flies from it, swelling and fading as it travels, with a ripple and wind streaks.
--   Sword  the striker's sword (their realm sword, or else the flying sword) in their right hand, in
--          a combo of three slashes, each with its own line (SLASHES): a diagonal cut down across the
--          body, a backhand rising the other way, and an overhead finisher. The body's motion is a
--          clip keyed in Blender (WeaponClips, played by PoseController); here the blade draws a sheet of light through the swing and
--          a crescent of light sweeps out along the slash's plane.
--   Spear  the striker's spear in both hands, in a combo of two, also clips: a thrust, coiled then
--          lunging with a real step, holding its reach, a lance of streaks running on from its tip; then
--          a slash, one wide sweep right to left round the body, with a crescent on the tip's true path.
--   hit    where a strike lands, by the kind of blow: a cut (a sword, a spear's slash) leaves a line of light
--          along the blade's path and throws sparks the way it travelled; a pierce (a spear's thrust) punches a
--          ring and drives a narrow jet of sparks on through; a blunt blow (bare hands) bursts in a ring with
--          sparks all round and a puff of dust. The struck target flashes; the striker's pose holds for an
--          instant (hit-stop) and their own camera kicks; their own strikes show their damage (DamageNumbers).
--          A critical strike (the server's roll) is bigger, gold, crossed with a flare of light and rung.
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
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local DamageNumbers = require(script.Parent:WaitForChild("DamageNumbers"))

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
    Spike = "rbxassetid://89522570963572",    -- QiSpike, a sharp shard (shared with QinggongFx): the sparks a blow throws
    Fire = "rbxasset://textures/particles/fire_main.dds",
    Smoke = "rbxasset://textures/particles/smoke_main.dds",
}
local MAX_DISTANCE = 250
-- each slash of the combo. Its crescent lies on the arc the blade's tip really draws, measured from
-- the swing in root space (fitted by weapon_moves.py when the clips are baked): the circle's
-- Centre and Radius, the way its plane faces (Face) and the way the arc bulges (Bulge). Then how much
-- it swells and how far it carries ahead; the finisher is the biggest, and shakes the striker's camera.
local WeaponClips = require(script.Parent.Parent:WaitForChild("Character"):WaitForChild("WeaponClips"))
-- each strike's timing and the arc its weapon truly draws come from its clip (tools/blender/animation)
local function fromClip(name, slash)
    local clip = WeaponClips.Clips[name]
    slash.Clip = clip
    slash.Centre, slash.Radius, slash.Face, slash.Bulge = clip.Crescent.Centre, clip.Crescent.Radius, clip.Crescent.Face, clip.Crescent.Bulge
    return slash
end
local SLASHES = {
    fromClip("SwordA", { Grow = 1.35, Travel = 3, Pitch = 1.05 }),
    fromClip("SwordB", { Grow = 1.35, Travel = 3, Pitch = 1.2 }),
    fromClip("SwordC", { Grow = 1.5, Travel = 4.5, Pitch = 0.82, Finisher = true }),
}
-- the spear's slash, on the same terms: one wide flat arc round the striker, right to left
local SPEAR_SLASH = fromClip("SpearSlash", { Grow = 1.25, Travel = 2.5 })
local SPEAR_THRUST = WeaponClips.Clips.SpearThrust
-- the QiSlash texture's circle, as shares of the plate's half-width (tools/blender/vfx/combat_textures.py)
local CRESCENT_RADIUS, CRESCENT_DROP = 0.92, 0.3
local HOLD_TIME = 5      -- seconds a weapon stays in the hand after the last strike
local SPEAR_LOW_TIME = 1.4 -- seconds a spear stays in its low stance after a thrust
-- a weapon's turn in the fist, from the hand's grip attachment (whose -Z runs down the forearm): a
-- sword's blade rises out of the fist; a spear's shaft runs along the forearm
local GRIP_TURN = { Sword = CFrame.Angles(math.rad(80), 0, 0), Spear = CFrame.identity }
local PUNCHES = { WeaponClips.Clips.PunchRight, WeaponClips.Clips.PunchLeft } -- bare hands: right, then left
local PUNCH_WINDOW = 1.1 -- seconds in which the next punch uses the other hand
local SWING = { Palm = "PalmStrike" } -- a strike's sound at once (SoundCatalog; a weapon's plays with its blow)
-- where a strike lands (landHit), by the kind of blow
local HIT_SOUND = { Cut = "BladeHit", Pierce = "SpearHit", Blunt = "PalmHit" }
-- the farthest from the striker a blow shows, in studs: about where the weapon and its light reach. The server's point is
-- on the target's near side by its HitRadius, which for a big guardian close by is deep inside its body
local HIT_REACH = { Cut = 8, Pierce = 10, Blunt = 6 }
local HIT_DEPTH = 3 -- studs toward the camera a blow's light is drawn (ZOffset), so a guardian's skin just in front can't hide it
local CRIT_GOLD = Color3.fromRGB(255, 205, 80)
local EDGE_SHARE = 0.16 -- the outer share of a blade that draws the bright edge of its trail
-- seconds the striker's pose holds as a blow lands: longer for a combo's finisher and a critical strike
local HIT_STOP = { Normal = 0.045, Finisher = 0.07, Critical = 0.09 }
-- the camera's kick for the striker's own blow: degrees, seconds (GuardianFx.shake)
local HIT_SHAKE = { Normal = { 0.3, 0.12 }, Finisher = { 0.5, 0.16 }, Critical = { 0.95, 0.22 } }
-- a crescent draws on along the blade's path: a UIGradient's transparency, slid across the plate. One
-- shows from the image's left, the other from its right
local WIPE_FROM_LEFT = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.35, 0),
    NumberSequenceKeypoint.new(0.65, 1), NumberSequenceKeypoint.new(1, 1) })
local WIPE_FROM_RIGHT = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.35, 1),
    NumberSequenceKeypoint.new(0.65, 0), NumberSequenceKeypoint.new(1, 0) })

local fxFolder = Instance.new("Folder")
fxFolder.Name = "CombatFx"
fxFolder.Parent = Workspace

local COMBO_STEPS = { Sword = #SLASHES, Spear = 2 } -- how many strikes each weapon's combo has
local strikes = {} -- [player] = { weapon, started, untilTime, step (its place in the weapon's combo), palette (what it draws with),
                   -- holdAt, holdUntil (a hit-stop: its clip holds at holdAt seconds until then) }
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

local emitter = GuardianFx.emitter

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

-- The bright edge of a weapon's trail: a thin line the tip draws, sharpening to a point as it fades (the
-- soft sheet behind it is weaponTrail's). No texture: a narrow ribbon reads as a drawn line.
local function edgeTrail(part, offset, a, b, p, glow)
    local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
    a0.Position, a1.Position = offset:PointToObjectSpace(a), offset:PointToObjectSpace(b)
    a0.Parent, a1.Parent = part, part
    local trail = Instance.new("Trail")
    trail.Name = "EdgeTrail"
    trail.Attachment0, trail.Attachment1 = a0, a1
    trail.Lifetime = 0.26
    trail.FaceCamera = true
    trail.LightEmission = 1
    trail.LightInfluence = 0
    trail.Brightness = 3
    trail.Color = colorSequence({ { 0, p.Core }, { 1, glow } })
    trail.Transparency = numberSequence({ { 0, 0 }, { 0.6, 0.35 }, { 1, 1 } })
    trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0 } })
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

-- ---------- the weapon in the hand ----------
-- A sword or spear is welded to the striker's right hand, so it moves exactly as the arm does, and
-- stays there HOLD_TIME after the last strike, in that kind's ready stance (PoseController's SwordReady,
-- SpearReady), put away sooner if they meditate, die, change weapon or strike with the palm, or once a
-- strike made in flight is over. The strike itself is the arm's motion (PoseController): a sword's
-- a clip in WeaponClips.
local held = {} -- [player] = { kind, model, trail, hand, source, weaponId, untilTime }
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
                or player:GetAttribute("IsCultivating") == true or player:GetAttribute("WeaponId") ~= entry.weaponId
                or player:GetAttribute("CarryingEgg") ~= nil
                or (stale and not striking) then
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
    local edge = edgeTrail(body, parts[body], spec.from:Lerp(spec.to, 1 - EDGE_SHARE), spec.to, p, spec.glow or p.Main)
    edge.Enabled = false
    entry = { kind = kind, model = model, trail = trail, edge = edge, hand = hand, source = source, weaponId = player:GetAttribute("WeaponId"),
        untilTime = os.clock() + HOLD_TIME }
    held[player] = entry
    watchHeld()
    return entry
end

-- the blow lands after the wind-up: the trail draws through it (to swingEnds, which a hit-stop puts back), and `effect` plays
local function afterWindUp(player, entry, windUp, duration, root, effect)
    task.delay(windUp, function()
        if entry and held[player] == entry then
            local swing = {}
            entry.swing, entry.swingEnds = swing, os.clock() + duration
            entry.trail.Enabled, entry.edge.Enabled = true, true
            task.spawn(function()
                while entry.swing == swing and os.clock() < entry.swingEnds do
                    task.wait()
                end
                if entry.swing == swing and entry.trail.Parent then -- (a newer swing keeps drawing)
                    entry.trail.Enabled, entry.edge.Enabled = false, false
                end
            end)
        end
        if root.Parent then
            effect()
        end
    end)
end

-- a crescent of light on the arc the blade draws: it draws on along the blade's own path, the way the tip
-- travels, then swells and carries ahead as it fades. echo: a paler one after it, for a finisher's weight
local function slashCrescent(slash, p, root, echo)
    local half = slash.Radius / CRESCENT_RADIUS
    local across = -slash.Bulge.Unit -- a Top face's gui has its top towards the part's -X, a Bottom's +X
    local along = across:Cross(slash.Face.Unit).Unit
    local frame = root.CFrame * CFrame.fromMatrix(slash.Centre + slash.Bulge.Unit * CRESCENT_DROP * half, across, along:Cross(across), along)
    local size = Vector3.new(half * 2, 0.05, half * 2)
    local scale = CombatFx.TimeScale
    local plate = host(frame, size, 0.5 / scale)
    local swing = (slash.Clip.SwingEnd - slash.Clip.SwingStart) / scale
    for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
        local gui, label = flat(face, TEXTURES.Slash, if echo then p.Core else p.Main:Lerp(p.Core, 0.25), if echo then 0.55 else 0.05)
        gui.Brightness = 2.6
        label.Rotation = if face == Enum.NormalId.Bottom then 180 else 0
        -- the tip travels along the plate's +Z (`along`): across the image from its left on the top face, and (the label
        -- turned half round) from its right on the bottom (seen in Play in slow motion from over the plate: the other way
        -- round, the light ran ahead of the blade)
        local fromLeft = face == Enum.NormalId.Top
        local wipe = Instance.new("UIGradient")
        wipe.Transparency = if fromLeft then WIPE_FROM_LEFT else WIPE_FROM_RIGHT
        wipe.Offset = Vector2.new(if fromLeft then -1 else 1, 0)
        wipe.Parent = label
        gui.Parent = plate
        TweenService:Create(wipe, TweenInfo.new(swing, Enum.EasingStyle.Sine, Enum.EasingDirection.Out),
            { Offset = Vector2.new(if fromLeft then 1 else -1, 0) }):Play()
        TweenService:Create(label, TweenInfo.new(0.16 / scale, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.08 / scale),
            { ImageTransparency = 1 }):Play()
    end
    local grow, travel = slash.Grow * (if echo then 1.2 else 1), slash.Travel * (if echo then 1.35 else 1)
    TweenService:Create(plate, TweenInfo.new(0.24 / scale, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        { Size = size * Vector3.new(grow, 1, grow), CFrame = frame + root.CFrame.LookVector * travel }):Play()
end

local function sword(player, p, root, step, strike)
    local source, flying = weaponSource(player, "Sword")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, flying)
    p = strikePalette(p, element)
    strike.palette = p
    local slash = SLASHES[step]
    local entry = hold(player, "Sword", source, flying, if flying then swordGlow(player) else element and element.Color, {
        from = source:GetAttribute("Hilt") or Vector3.new(0, 0, 1.2), to = source:GetAttribute("Tip") or Vector3.new(0, 0, -4.3),
        life = 0.22, faceCamera = false, transparency = 0.2,
    }, p)
    local clip, scale = slash.Clip, CombatFx.TimeScale
    if entry then -- the finisher's light hangs in the air longer
        entry.trail.Lifetime, entry.edge.Lifetime = if slash.Finisher then 0.32 else 0.22, if slash.Finisher then 0.36 else 0.26
    end
    afterWindUp(player, entry, clip.SwingStart / scale, (clip.SwingEnd - clip.SwingStart) / scale, root, function()
        Sfx.play("SwordSwing", root, slash.Pitch)
        slashCrescent(slash, p, root)
        if slash.Finisher then
            task.delay(0.06 / scale, function()
                if root.Parent then
                    slashCrescent(slash, p, root, true)
                end
            end)
            if player == Players.LocalPlayer then
                GuardianFx.shake(root.Position, 0.7, 0.2)
            end
        end
        if elementName then
            elementBurst(elementName, root.CFrame * CFrame.new(slash.Centre + slash.Bulge.Unit * slash.Radius))
        end
    end)
end

local function spear(player, p, root, step, strike)
    local source = weaponSource(player, "Spear")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, false)
    p = strikePalette(p, element)
    strike.palette = p
    local glow = if element then element.Color else swordGlow(player)
    local entry = hold(player, "Spear", source, false, element and element.Color, {
        from = source:GetAttribute("Hilt") + Vector3.new(0, 0, 3.5), to = source:GetAttribute("Tip"),
        glow = glow, life = 0.2, faceCamera = true, transparency = 0.3,
    }, p)
    local scale = CombatFx.TimeScale
    if step == 2 then
        local clip = SPEAR_SLASH.Clip
        afterWindUp(player, entry, clip.SwingStart / scale, (clip.SwingEnd - clip.SwingStart) / scale, root, function()
            Sfx.play("SpearSwing", root)
            slashCrescent(SPEAR_SLASH, p, root)
            if elementName then
                elementBurst(elementName, root.CFrame * CFrame.new(SPEAR_SLASH.Centre + SPEAR_SLASH.Bulge.Unit * SPEAR_SLASH.Radius))
            end
        end)
        return
    end
    afterWindUp(player, entry, SPEAR_THRUST.SwingStart / scale, (SPEAR_THRUST.SwingEnd - SPEAR_THRUST.SwingStart) / scale, root, function()
        Sfx.play("SpearThrust", root)
        -- a lance of streaks running on from the spear's tip at full reach
        local tip = root.CFrame * CFrame.new(0, -0.3, -7.9)
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
-- The kind of blow a strike is: "Cut" (a sword, a spear's slash), "Pierce" (a spear's thrust) or "Blunt" (bare hands).
local function blowOf(strike)
    if strike and strike.weapon == "Sword" then
        return "Cut", SLASHES[strike.step]
    elseif strike and strike.weapon == "Spear" then
        if strike.step == 2 then
            return "Cut", SPEAR_SLASH
        end
        return "Pierce", nil
    end
    return "Blunt", nil
end

-- The way a blow travels as it lands: a cut along its blade's path (the tip goes round its arc's Face, so at
-- the arc's middle it moves along Face x Bulge), a thrust and a punch straight ahead.
local function blowDirection(root, slash)
    if not root then
        return Vector3.yAxis
    end
    if slash then
        return root.CFrame:VectorToWorldSpace(slash.Face.Unit:Cross(slash.Bulge.Unit)).Unit
    end
    return root.CFrame.LookVector
end

-- The struck target flashes: one Highlight, moved to whichever was struck last.
local hitFlash, flashCount = nil, 0
local function flashTarget(target, color, critical)
    if not target or not target:IsDescendantOf(Workspace) then
        return
    end
    if not hitFlash then
        hitFlash = Instance.new("Highlight")
        hitFlash.Name = "HitFlash"
        hitFlash.OutlineTransparency = 1
        hitFlash.DepthMode = Enum.HighlightDepthMode.Occluded
        hitFlash.Parent = fxFolder
    end
    flashCount += 1
    local mine = flashCount
    hitFlash.Adornee = target
    hitFlash.FillColor = color
    hitFlash.FillTransparency = if critical then 0.3 else 0.55
    hitFlash.Enabled = true
    local fade = TweenService:Create(hitFlash, TweenInfo.new((if critical then 0.24 else 0.15) / CombatFx.TimeScale, Enum.EasingStyle.Quad,
        Enum.EasingDirection.Out), { FillTransparency = 1 })
    fade.Completed:Once(function()
        if flashCount == mine then -- (a newer flash cancels this one, and keeps the Highlight)
            hitFlash.Enabled = false
            hitFlash.Adornee = nil
        end
    end)
    fade:Play()
end

-- The striker's pose holds for `seconds` as their blow lands: the clip stops where it is, then goes on.
local function hitStop(player, strike, seconds)
    if not strike or strikes[player] ~= strike then
        return
    end
    seconds /= CombatFx.TimeScale
    local now = os.clock()
    strike.holdAt = (now - strike.started) * CombatFx.TimeScale
    strike.holdUntil = now + seconds
    strike.started += seconds
    strike.untilTime += seconds
    local entry = held[player]
    if entry and entry.swingEnds then
        entry.swingEnds += seconds -- the trail draws on through the rest of the swing
    end
end

-- strike: the striker's strike as the server's answer came (nil if they had none: the blunt burst).
local function landHit(player, position, info, strike)
    local blow, slash = blowOf(strike)
    local critical = info.critical == true
    Sfx.play(HIT_SOUND[blow], position, if blow == "Cut" and strike.weapon == "Spear" then 0.8 else nil)
    if critical then
        Sfx.play("CritHit", position)
    end
    local mine = player == Players.LocalPlayer
    local camera = Workspace.CurrentCamera
    if not mine and (not camera or (camera.CFrame.Position - position).Magnitude > MAX_DISTANCE) then
        return
    end
    local root = rootOf(player)
    local p = (strike and strike.palette) or QinggongFx.palette(player)
    local finisher = slash ~= nil and slash.Finisher == true
    local grade = if critical then "Critical" elseif finisher then "Finisher" else "Normal"
    -- thinner for another player's blow on a phone, and with reduced effects
    local thin = (Quality.Low and not mine) or Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
    local power = if critical then 1.5 else 1
    local hot = if critical then CRIT_GOLD else p.Core
    local direction = blowDirection(root, slash)
    if root then
        local from = root.Position + Vector3.new(0, 0.5, 0)
        local to = position - from
        if to.Magnitude > HIT_REACH[blow] then
            position = from + to.Unit * HIT_REACH[blow]
        end
    end
    local holder = host(CFrame.lookAt(position, position + direction), Vector3.new(0.4, 0.4, 0.4), 1)

    -- where it landed: a flash of light
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.14), ZOffset = HIT_DEPTH + 1,
        Size = numberSequence({ { 0, 2.2 * power }, { 1, 4.4 * power } }), Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }),
        Color = colorSequence({ { 0, hot }, { 1, p.Main } }), Brightness = if critical then 1.8 else 2.5,
    }):Emit(1)

    -- how hard and which way: sparks thrown along the blow, falling as they go
    -- (a thrust goes into its target, away from whoever is watching it: its sparks spray back off the point)
    local sparks = if blow == "Cut" then { Count = 9, Spread = 26, Speed = NumberRange.new(26, 44), Fall = -34, Way = Enum.NormalId.Front }
        elseif blow == "Pierce" then { Count = 9, Spread = 52, Speed = NumberRange.new(24, 40), Fall = -20, Way = Enum.NormalId.Back }
        else { Count = 10, Spread = 180, Speed = NumberRange.new(14, 24), Fall = -26, Way = Enum.NormalId.Front }
    emitter(holder, {
        Texture = TEXTURES.Spike, Orientation = Enum.ParticleOrientation.VelocityParallel, EmissionDirection = sparks.Way,
        SpreadAngle = Vector2.new(sparks.Spread, sparks.Spread), Speed = sparks.Speed, Drag = 5, Acceleration = Vector3.new(0, sparks.Fall, 0),
        Lifetime = NumberRange.new(0.18, 0.34), Size = numberSequence({ { 0, 0.9 * power }, { 1, 0.15 } }),
        Transparency = numberSequence({ { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } }), Color = colorSequence({ { 0, hot }, { 1, p.Main } }), Brightness = 2.6,
        ZOffset = HIT_DEPTH,
    }):Emit(math.ceil(sparks.Count * power * (if thin then 0.6 else 1)))

    -- what kind of blow
    if blow == "Cut" then
        -- the cut itself: a line of light through the point, along the blade's path
        emitter(holder, {
            Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, EmissionDirection = Enum.NormalId.Front,
            SpreadAngle = Vector2.new(0, 0), Speed = NumberRange.new(3), Lifetime = NumberRange.new(0.2), ZOffset = HIT_DEPTH + 1.2,
            Size = numberSequence({ { 0, 5 * power }, { 1, 8.5 * power } }), Transparency = numberSequence({ { 0, 0 }, { 0.5, 0.1 }, { 1, 1 } }),
            Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 1, hot } }), Brightness = 3,
        }):Emit(1)
    else
        -- a ring punched out round the point: small and quick for a pierce, broad for a blunt blow
        local reach = if blow == "Pierce" then 5.5 else 7.5
        emitter(holder, {
            Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(if blow == "Pierce" then 0.22 else 0.3), ZOffset = HIT_DEPTH + 0.8,
            Size = numberSequence({ { 0, 0.9 }, { 1, reach * power } }), Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }),
            Color = colorSequence({ { 0, hot }, { 1, p.Main } }), Brightness = 2,
        }):Emit(1)
        if blow == "Pierce" then
            -- the lance driving in: a line of light that starts short of the point and runs on through it
            local behind = Instance.new("Attachment")
            behind.Position = Vector3.new(0, 0, 3.5) -- (the holder faces the way the blow travels: +Z is back toward the striker)
            behind.Parent = holder
            emitter(behind, {
                Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, EmissionDirection = Enum.NormalId.Front,
                SpreadAngle = Vector2.new(0, 0), Speed = NumberRange.new(42), Lifetime = NumberRange.new(0.13), ZOffset = HIT_DEPTH + 1,
                Size = numberSequence({ { 0, 3.5 * power }, { 1, 6.5 * power } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
                Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 1, hot } }), Brightness = 3,
            }):Emit(1)
        elseif not thin then
            -- dust knocked off it
            emitter(holder, {
                Texture = TEXTURES.Smoke, LightEmission = 0.2, Speed = NumberRange.new(2, 4), SpreadAngle = Vector2.new(180, 180), Drag = 3,
                Lifetime = NumberRange.new(0.4, 0.55), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40),
                Size = numberSequence({ { 0, 1.2 }, { 1, 3.4 } }), Transparency = numberSequence({ { 0, 0.6 }, { 1, 1 } }),
                Color = ColorSequence.new(p.Main:Lerp(Color3.fromRGB(150, 150, 160), 0.6)),
            }):Emit(3)
        end
    end

    -- a critical strike: a cross of light through the point, and a second ring of gold
    if critical then
        for _, turn in { 45, -45 } do
            emitter(holder, {
                Texture = TEXTURES.Streak, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.24), ZOffset = HIT_DEPTH + 1.4,
                Rotation = NumberRange.new(turn), Size = numberSequence({ { 0, 5 }, { 0.3, 8.5 }, { 1, 9.5 } }), Squash = NumberSequence.new(-1),
                Transparency = numberSequence({ { 0, 0 }, { 0.4, 0.15 }, { 1, 1 } }),
                Color = colorSequence({ { 0, CRIT_GOLD:Lerp(Color3.new(1, 1, 1), 0.5) }, { 1, CRIT_GOLD } }), Brightness = 2.4, LightEmission = 0.7,
            }):Emit(1)
        end
        emitter(holder, {
            Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.34), ZOffset = HIT_DEPTH + 0.6,
            Size = numberSequence({ { 0, 1.5 }, { 1, 11 } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
            Color = ColorSequence.new(CRIT_GOLD), Brightness = 2.2, LightEmission = 0.6, -- (fully additive, gold washed to white in Play)
        }):Emit(1)
    end

    if not (Quality.Low and not mine) then
        flashTarget(info.target, hot:Lerp(Color3.new(1, 1, 1), 0.5), critical)
    end
    hitStop(player, strike, HIT_STOP[grade])
    if mine then
        GuardianFx.shake(position, HIT_SHAKE[grade][1], HIT_SHAKE[grade][2])
        if info.damage then
            DamageNumbers.show(position + Vector3.new(0, 1.5, 0), info.damage, critical, p.Main)
        end
    end
end

-- The server answers at once, but the blow lands part way through the strike's clip: the impact waits for it.
-- info: what the server said it did: { damage, critical, target }.
function CombatFx.hit(player, position, info)
    info = info or {}
    local strike = strikes[player]
    local wait = strike and strike.hitAt and (strike.hitAt - (os.clock() - strike.started) * CombatFx.TimeScale) / CombatFx.TimeScale or 0
    if wait > 0.01 then
        task.delay(wait, landHit, player, position, info, strike)
    else
        landHit(player, position, info, strike)
    end
end

-- ---------- entry points ----------
-- step: which strike of the combo it is, when the server says (another player's spear); else counted here
function CombatFx.play(player, weapon, step)
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
        strike.step = step or if continuing then last.step % steps + 1 else 1
        combos[player] = { weapon = weapon, step = strike.step, at = now }
    else
        local last = combos[player]
        strike.step = if last and last.weapon == weapon and now - last.at < PUNCH_WINDOW / CombatFx.TimeScale then last.step % 2 + 1 else 1
        combos[player] = { weapon = weapon, step = strike.step, at = now }
        putAway(player) -- a palm strike is bare-handed
    end
    local clip = if weapon == "Sword" then SLASHES[strike.step].Clip
        elseif weapon == "Spear" then (if strike.step == 2 then SPEAR_SLASH.Clip else SPEAR_THRUST)
        else PUNCHES[strike.step]
    strike.hitAt = clip.Hit
    strike.untilTime = now + clip.Length / CombatFx.TimeScale
    strikes[player] = strike
    local camera = Workspace.CurrentCamera
    if player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE) then
        return
    end
    if SWING[weapon] then
        Sfx.play(SWING[weapon], root)
    end
    local p = QinggongFx.palette(player)
    strike.palette = p
    if weapon == "Sword" then
        sword(player, p, root, strike.step, strike)
    elseif weapon == "Spear" then
        spear(player, p, root, strike.step, strike)
    else
        -- the Qi print flies as the fist lands
        task.delay(clip.Hit / CombatFx.TimeScale, function()
            if root.Parent then
                palm(p, root)
            end
        end)
    end
end

-- The server's count of a spear's combo (it decides the slash's reach): the next strike follows on from it.
function CombatFx.syncCombo(player, weapon, step)
    local combo = combos[player]
    if combo and combo.weapon == weapon then
        combo.step = step
    end
end

-- The pose a player is in, or nil; PoseController reads it. During a strike: "Palm", "Slash" or
-- "SpearSlash" or "SpearThrust" (ask CombatFx.slash where in it they are). With a weapon out after it:
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
            return "SpearThrust"
        end
        return strike.weapon
    end
    local entry = held[player]
    if entry and entry.kind == "Spear" and strike and os.clock() - strike.untilTime < SPEAR_LOW_TIME then
        return "SpearLow"
    end
    return entry and entry.kind .. "Ready"
end

-- Which strike of the combo a player is in, and how far through it in real-time seconds (held still through a hit-stop).
function CombatFx.slash(player)
    local strike = strikes[player]
    if strike and strike.step then
        if strike.holdUntil and os.clock() < strike.holdUntil then
            return strike.step, strike.holdAt
        end
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

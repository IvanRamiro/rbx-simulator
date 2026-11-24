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
--          Combat feel (2026-11-18): the impact is drawn on the guardian's skin (a ray from the striker), layered in time (flash and sparks,
--          then the ring, then chips of the guardian's own material and a faint scorch) in the weapon's realm or forged colours, and
--          scaled a little by the weapon's tier; the guardian flinches (GuardianReact); each blow has its own hit-stop and camera kick
--          (BLOWS); heavy blows (a finisher, a thrust, a critical strike) add a low thump and a shove of the body. The blow's real-time shape
--          (RETIME) lengthens a heavy wind-up and keeps the server's cooldown. The striker's own blow is shown at its blow frame even
--          before the server's answer arrives (a predicted impact; the answer then adds the number and a critical's flare).
--
-- A forged weapon (the striker's "WeaponElement", GameConfig.Forge) glows, trails and slashes in its
-- element's colours and bursts with its element where it strikes: Fire rising embers and a lick of
-- flame, Frost flying ice shards and cold mist, Wood tumbling leaves, Earth thrown rock and a ring
-- of dust, Wind whipping streaks and a gust ring, Void dark smoke with sparks of violet.
--
-- Every realm weapon wears its own aura on the steel of its blade or spearhead (WeaponAura, WeaponAuraStyles): at full strength
-- while it is drawn, quiet while it rides on the back, flaring as a blow lands, tinted by a forged element, thinned and then
-- switched off with distance (tend) and on a phone.
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
local FormRules = require(ReplicatedStorage:WaitForChild("FormRules"))
local AuraKit = require(script.Parent.Parent:WaitForChild("Auras"):WaitForChild("AuraKit"))
local QinggongFx = require(script.Parent.Parent:WaitForChild("Qinggong"):WaitForChild("QinggongFx"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("GuardianFx"))
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local DamageNumbers = require(script.Parent:WaitForChild("DamageNumbers"))
local WeaponAura = require(script.Parent:WaitForChild("WeaponAura"))
local WeaponAuraStyles = require(script.Parent:WaitForChild("WeaponAuraStyles"))
local GuardianReact = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("GuardianReact"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local CollectionService = game:GetService("CollectionService")

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
-- The real-time shape of each blow, in seconds: to the swing's start (the wind-up), the swing, and what is left of the clip. The clips are
-- keyed for it (2026-11-18: the spear's thrust, the sword's finisher and the punches were keyed again in Blender, tools/blender/animation, with a
-- longer wind-up and the blow at the frame the weapon connects), so by default these are the clip's own numbers. RETIME can still stretch or
-- squeeze a part of a clip for the eye (played faster or slower through that part, the blow frame moving with it): never the cooldown, the server's.
local RETIME = {} -- [clip name] = { Wind, Swing, Tail } in seconds
local function timingOf(name, clip)
    local timing = { Clip = clip }
    if clip.SwingStart then
        local swing = clip.SwingEnd - clip.SwingStart
        local re = RETIME[name]
        timing.ClipWind, timing.ClipSwing, timing.ClipTail = clip.SwingStart, swing, clip.Length - clip.SwingEnd
        timing.Wind, timing.Swing, timing.Tail = if re then re.Wind else clip.SwingStart, if re then re.Swing else swing,
            if re then re.Tail else timing.ClipTail
        timing.Hit = timing.Wind + (clip.Hit - clip.SwingStart) / swing * timing.Swing
    else -- (a punch has no swing marks: played as it is)
        timing.Wind, timing.Swing, timing.Tail, timing.Hit = 0, 0, clip.Length, clip.Hit
    end
    timing.Length = timing.Wind + timing.Swing + timing.Tail
    return timing
end
-- the clip's own time (seconds into it) at `real` seconds into the blow as played
local function clipTime(timing, real)
    if not timing.ClipWind then
        return real
    end
    if real <= timing.Wind then
        return timing.ClipWind * real / timing.Wind
    elseif real <= timing.Wind + timing.Swing then
        return timing.ClipWind + timing.ClipSwing * (real - timing.Wind) / timing.Swing
    end
    return math.min(timing.ClipWind + timing.ClipSwing + timing.ClipTail * (real - timing.Wind - timing.Swing) / timing.Tail,
        timing.Clip.Length)
end

local function fromClip(name, slash)
    local clip = WeaponClips.Clips[name]
    slash.Clip = clip
    slash.Timing = timingOf(name, clip)
    slash.Name = name
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
local THRUST_TIMING = timingOf("SpearThrust", SPEAR_THRUST)
-- the QiSlash texture's circle, as shares of the plate's half-width (tools/blender/vfx/combat_textures.py)
local CRESCENT_RADIUS, CRESCENT_DROP = 0.92, 0.3
local HOLD_TIME = 5      -- seconds a weapon stays in the hand after the last strike
local SPEAR_LOW_TIME = 1.4 -- seconds a spear stays in its low stance after a thrust
-- a weapon's turn in the fist, from the hand's grip attachment (whose -Z runs down the forearm): a
-- sword's blade rises out of the fist; a spear's shaft runs along the forearm
local GRIP_TURN = { Sword = CFrame.Angles(math.rad(80), 0, 0), Spear = CFrame.identity }
local PUNCHES = { WeaponClips.Clips.PunchRight, WeaponClips.Clips.PunchLeft } -- bare hands: right, then left
local PUNCH_TIMINGS = { timingOf("PunchRight", PUNCHES[1]), timingOf("PunchLeft", PUNCHES[2]) }
local SWING = { Palm = "PalmStrike" } -- a strike's sound at once (SoundCatalog; a weapon's plays with its blow)
-- where a strike lands (landHit), by the kind of blow
local HIT_SOUND = { Cut = "BladeHit", Pierce = "SpearHit", Blunt = "PalmHit" }
-- the farthest from the striker a blow shows, in studs: about where the weapon and its light reach. The server's point is
-- on the target's near side by its HitRadius, which for a big guardian close by is deep inside its body
local HIT_REACH = { Cut = 8, Pierce = 10, Blunt = 6 }
-- the farthest a blow may be drawn from the striker when it is put on the guardian's skin: the weapon's range (sword 12, spear 18 and its slash 13,
-- palm 9, from the skin) and a little over
local SKIN_REACH = { Cut = 15, Pierce = 21, Blunt = 12 }
local HIT_DEPTH = 3 -- studs toward the camera a blow's light is drawn (ZOffset), so a guardian's skin just in front can't hide it
local CRIT_GOLD = Color3.fromRGB(255, 205, 80)
local EDGE_SHARE = 0.16 -- the outer share of a blade that draws the bright edge of its trail
-- What each blow does as it lands, by blow (Stop: seconds the striker's pose holds; Shake: the camera's noise, degrees and seconds, and
-- Kick: its one knock along the way the blow travelled, in degrees). A critical strike takes CRIT_STOP and CRIT_SHAKE times the blow's own,
-- to a cap. Frames at 60 fps: a light blow holds 2 to 4, a heavy one 5 to 8 (the audit, "Combat Feel Audit 2026-11-18": over 20 reads
-- as a bug, and a fight is 75 blows or more). The camera is the player's own and off with Reduced Effects, as the hold is.
local BLOWS = {
    Palm = { Stop = 0.040, Shake = { 0.35, 0.12 }, Kick = 0.35 },        -- 2.4 f
    SwordA = { Stop = 0.055, Shake = { 0.40, 0.12 }, Kick = 0.45 },      -- 3.3 f
    SwordB = { Stop = 0.055, Shake = { 0.40, 0.12 }, Kick = 0.45 },
    SwordC = { Stop = 0.100, Shake = { 0.80, 0.18 }, Kick = 0.9, Punch = 2.0 },       -- 6 f: the finisher
    Thrust = { Stop = 0.090, Shake = { 0.60, 0.16 }, Kick = 0.75, Punch = 1.4 },      -- 5.4 f: the spear's heavy blow
    SpearSlash = { Stop = 0.065, Shake = { 0.45, 0.14 }, Kick = 0.5, Punch = 1.0 },   -- 3.9 f: the spear's finisher
}
-- Punch: how many degrees a blow narrows the player's own field of view as it lands (GuardianFx.punch): the camera leans in on a chain's
-- last blow, a thrust, a critical strike (CRIT_PUNCH at least, 1.5 times a heavy blow's own, to PUNCH_MAX). Held for PUNCH_TIME seconds.
local CRIT_PUNCH, PUNCH_MAX, PUNCH_TIME = 1.2, 3.2, 0.24
-- The hit's sound is pitched up a little at each step of a chain, so a combo climbs as it goes, and the finisher drops under it, heavier
-- (the sword's overhead, with its thump below it; the spear's slash was already pitched down). By weapon, then step.
local HIT_LADDER = { Sword = { 1, 1.07, 0.9 }, Spear = { 1, 0.8 }, Palm = { 1, 1.06 } }
local CRIT_STOP, CRIT_STOP_MAX = 1.4, 0.12
local CRIT_SHAKE, CRIT_SHAKE_MAX = 1.5, { 1.2, 0.24 }
local TIER_STEP = 0.02 -- a weapon of tier n shows (1 + TIER_STEP * (n - 1)) as big: 1.0 for the first realm, 1.22 for the twelfth
-- a crescent draws on along the blade's path: a UIGradient's transparency, slid across the plate. One
-- shows from the image's left, the other from its right
local WIPE_FROM_LEFT = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.35, 0),
    NumberSequenceKeypoint.new(0.65, 1), NumberSequenceKeypoint.new(1, 1) })
local WIPE_FROM_RIGHT = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.35, 1),
    NumberSequenceKeypoint.new(0.65, 0), NumberSequenceKeypoint.new(1, 0) })

local fxFolder = Instance.new("Folder")
fxFolder.Name = "CombatFx"
fxFolder.Parent = Workspace

-- COMBAT FORMS (shared/FormRules): a strike comes with its form's `info` ({ Form, Step, Finisher, Name, Reaction, Range, Arc, ... }). The chain, the
-- reach, the damage and the cooldown are the form's (the server decides them); what a strike LOOKS and FEELS like is this file's:
--   * the clips are the keyed ones, borrowed by weapon (clipStep): a sword's finisher plays the overhead and its other strikes the two cuts in turn; a
--     spear's finisher plays the slash and the rest the thrust; bare hands alternate the fists and the finisher is the left;
--   * each strike is retimed to its own cooldown (retimed): a quick form's strikes play fast, a heavy form's finisher slowly, so the blow still lands
--     when the clip says (a clip's timing is never the server's: the cooldown is);
--   * each form has its own look (FORM_LOOKS): a tint for the light a strike draws (not over a forged weapon's element), how hard its blows are held
--     in the air (Stop), shaken (Shake) and pitched (Pitch), and for a finisher a ring on the ground (Ring, studs);
--   * what the target does (Light, Heavy, Launch) picks the guardian's reaction grade and the blow's weight (landHit).
local FORM_LOOKS = {
    Crescent = { Stop = 1, Shake = 1, Pitch = 1 },
    Gale = { Tint = Color3.fromRGB(150, 235, 255), Stop = 0.7, Shake = 0.7, Pitch = 1.12, Ring = 10 },
    Mountain = { Tint = Color3.fromRGB(255, 170, 70), Stop = 1.5, Shake = 1.4, Pitch = 0.88, Ring = 14 },
    Lancer = { Stop = 1, Shake = 1, Pitch = 1 },
    Swallow = { Tint = Color3.fromRGB(130, 255, 200), Stop = 0.7, Shake = 0.7, Pitch = 1.15, Ring = 9 },
    Tiger = { Tint = Color3.fromRGB(255, 110, 60), Stop = 1.4, Shake = 1.3, Pitch = 0.9, Ring = 13 },
    Fist = { Stop = 1, Shake = 1, Pitch = 1, Ring = 8 },
}
local DEFAULT_LOOK = FORM_LOOKS.Crescent
local function lookOf(info)
    return (info and FORM_LOOKS[info.Form]) or DEFAULT_LOOK
end

local function clipStep(weapon, info)
    if weapon == "Sword" then
        return if info.Finisher then 3 else (info.Step - 1) % 2 + 1
    elseif weapon == "Spear" then
        return if info.Finisher then 2 else 1
    end
    return if info.Finisher then 2 else (info.Step - 1) % 2 + 1
end

-- the clip's timing played in the time this strike's cooldown allows: faster for a short step, slower for a long one, never past SPEED_MIN to SPEED_MAX
local SPEED_MIN, SPEED_MAX = 0.75, 1.8
local function retimed(timing, weapon, info)
    local base = if weapon == "Palm" then GameConfig.Combat.Palm.Cooldown else GameConfig.WeaponKinds[weapon].Cooldown
    local step = FormRules.Forms[info.Form].Chain[info.Step]
    local speed = math.clamp(timing.Length / (base * step.Cd * 0.92), SPEED_MIN, SPEED_MAX)
    local copy = table.clone(timing)
    copy.Wind, copy.Swing, copy.Tail, copy.Hit, copy.Length = timing.Wind / speed, timing.Swing / speed, timing.Tail / speed, timing.Hit / speed, timing.Length / speed
    return copy
end

-- the palette a strike draws with, leaned toward its form's tint (not over a forged weapon's own element)
local function formPalette(p, info, element)
    local look = lookOf(info)
    if element or not look.Tint then
        return p
    end
    local q = table.clone(p)
    q.Core, q.Main = p.Core:Lerp(look.Tint, 0.45), p.Main:Lerp(look.Tint, 0.7)
    if p.Deep then
        q.Deep = p.Deep:Lerp(look.Tint, 0.4)
    end
    return q
end

local strikes = {} -- [player] = { weapon, info, started, untilTime, step (the clip it plays), palette (what it draws with),
               -- holdAt, holdUntil (a hit-stop: its clip holds at holdAt seconds until then) }

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
-- A realm weapon without an element draws with its own realm's colours (WeaponAuraStyles: the same as its aura), not the wearer's.
local function strikePalette(p, element, tier)
    local style = not element and tier and WeaponAuraStyles.Tiers[tier]
    if not element and not style then
        return p
    end
    local q = table.clone(p)
    if element then
        q.Core, q.Main = element.Core, element.Color
    else
        q.Core, q.Main, q.Deep = style.Palette.Core, style.Palette.Main, style.Palette.Deep
    end
    return q
end

-- the tier (1 to 12) of the weapon a player wields, 1 with none
local function tierOf(player)
    local weapon = Shop.weapon(player:GetAttribute("WeaponId"))
    return if weapon then weapon.Tier else 1
end

-- A puff of dust at the feet as a heavy blow drives off the ground: the body behind it. Their own, and others' near enough to see.
local function footDust(player, root)
    local camera = Workspace.CurrentCamera
    local humanoid = root.Parent and root.Parent:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.FloorMaterial == Enum.Material.Air or Quality.Low and player ~= Players.LocalPlayer
        or player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > 80) then
        return
    end
    local ground = root.Position - Vector3.new(0, humanoid.HipHeight + root.Size.Y / 2 - 0.1, 0)
    GuardianFx.puff(CFrame.new(ground), { Debris = "Dust" }, 6, 9, Vector2.new(180, 10), 1.4, 0.5)
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
-- stays there HOLD_TIME after the last strike (or, drawn, until it is sheathed), in that kind's ready stance (PoseController's SwordReady,
-- SpearReady), put away sooner if they meditate, die, change weapon or strike with the palm, or once a
-- strike made in flight is over. The strike itself is the arm's motion (PoseController): a sword's
-- a clip in WeaponClips.
local held = {} -- [player] = { kind, model, trail, hand, source, weaponId, untilTime }
local holdWatch = nil

local function putAway(player)
    local entry = held[player]
    if entry then
        held[player] = nil
        if entry.aura then
            entry.aura:destroy()
        end
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
            local drawn = player:GetAttribute("WeaponDrawn") == true and entry.source.Name == player:GetAttribute("WeaponId")
            local sheathedNow = entry.drawn and not drawn -- put back while it was drawn: at once, not when the strike's hold runs out
            entry.drawn = drawn
            local stale = (now > entry.untilTime and not drawn) or sheathedNow or player:GetAttribute("IsFlying") == true
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
local function hold(player, kind, source, flying, tint, spec, p, element)
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
    if not flying then -- (the flying sword has no profile: it keeps its own glow)
        entry.aura = WeaponAura.attach(body, parts[body], source.Name, { mine = player == Players.LocalPlayer, mode = "drawn", element = element })
        if entry.aura then -- (at once, so a strike that draws the weapon flares it too; tend refines this by distance)
            entry.aura:setDetail(if player == Players.LocalPlayer then 2 else 1)
        end
    end
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
            if entry.aura then
                entry.aura:strike(duration + 0.2)
            end
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
    local swing = slash.Timing.Swing / scale
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

-- How a weapon of `kind` is held: its trail's two weapon-space points, lifetime, facing and transparency (glow: the
-- spear's trail colour; a sword's takes the palette's)
local function holdSpec(kind, source, glow)
    if kind == "Spear" then
        return { from = source:GetAttribute("Hilt") + Vector3.new(0, 0, 3.5), to = source:GetAttribute("Tip"),
            glow = glow, life = 0.2, faceCamera = true, transparency = 0.3 }
    end
    return { from = source:GetAttribute("Hilt") or Vector3.new(0, 0, 1.2), to = source:GetAttribute("Tip") or Vector3.new(0, 0, -4.3),
        life = 0.22, faceCamera = false, transparency = 0.2 }
end

local function sword(player, p, root, step, strike)
    local source, flying = weaponSource(player, "Sword")
    if not source then
        return
    end
    local elementName, element = elementOf(player, source, flying)
    local slash = SLASHES[step]
    p = formPalette(strikePalette(p, element, not flying and tierOf(player) or nil), strike.info, element)
    strike.palette = p
    local entry = hold(player, "Sword", source, flying, if flying then swordGlow(player) else element and element.Color,
        holdSpec("Sword", source), p, element)
    local timing, scale = strike.timing or slash.Timing, CombatFx.TimeScale
    if entry then -- the finisher's light hangs in the air longer
        entry.trail.Lifetime, entry.edge.Lifetime = if slash.Finisher then 0.32 else 0.22, if slash.Finisher then 0.36 else 0.26
        if entry.aura then -- the blade starts to gather light as the wind-up starts (the flare comes with the swing)
            entry.aura:charge(timing.Wind / scale)
        end
    end
    afterWindUp(player, entry, timing.Wind / scale, timing.Swing / scale, root, function()
        Sfx.play("SwordSwing", root, slash.Pitch)
        slashCrescent(slash, p, root)
        if slash.Finisher then
            footDust(player, root)
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
    p = formPalette(strikePalette(p, element, tierOf(player)), strike.info, element)
    strike.palette = p
    local glow = if element then element.Color else swordGlow(player) -- (the trail's: the same whoever draws the spear first)
    local lance = if element then element.Color else p.Main
    local entry = hold(player, "Spear", source, false, element and element.Color, holdSpec("Spear", source, glow), p, element)
    local scale = CombatFx.TimeScale
    local timing = strike.timing or (if step == 2 then SPEAR_SLASH.Timing else THRUST_TIMING)
    if entry and entry.aura then
        entry.aura:charge(timing.Wind / scale)
    end
    if step == 2 then
        afterWindUp(player, entry, timing.Wind / scale, timing.Swing / scale, root, function()
            Sfx.play("SpearSwing", root)
            slashCrescent(SPEAR_SLASH, p, root)
            if elementName then
                elementBurst(elementName, root.CFrame * CFrame.new(SPEAR_SLASH.Centre + SPEAR_SLASH.Bulge.Unit * SPEAR_SLASH.Radius))
            end
        end)
        return
    end
    afterWindUp(player, entry, timing.Wind / scale, timing.Swing / scale, root, function()
        Sfx.play("SpearThrust", root)
        footDust(player, root)
        -- a lance of streaks running on from the spear's tip at full reach
        local tip = root.CFrame * CFrame.new(0, -0.3, -7.9)
        local holder = host(tip, Vector3.new(0.4, 0.4, 0.4), 0.6)
        emitter(holder, {
            Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
            Speed = NumberRange.new(55, 70), SpreadAngle = Vector2.new(3, 3), Lifetime = NumberRange.new(0.16, 0.22),
            Size = numberSequence({ { 0, 1.6 }, { 1, 0.3 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
            Color = colorSequence({ { 0, p.Core }, { 1, lance } }), Brightness = 2.4,
        }):Emit(6)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.16),
            Size = numberSequence({ { 0, 1 }, { 1, 3.2 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
            Color = colorSequence({ { 0, p.Core }, { 1, lance } }), Brightness = 2,
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

-- The struck target flashes: one Highlight, moved to whichever was struck last. A hard, short flash (a tint that reads as one bright
-- frame or two, not a stun): 0.35 fading to clear in 0.10 s, a critical strike 0.2 in 0.16 s.
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
    hitFlash.FillTransparency = if critical then 0.2 else 0.35
    hitFlash.Enabled = true
    local fade = TweenService:Create(hitFlash, TweenInfo.new((if critical then 0.16 else 0.10) / CombatFx.TimeScale, Enum.EasingStyle.Quad,
        Enum.EasingDirection.Out), { FillTransparency = 1 })
    fade.Completed:Once(function()
        if flashCount == mine then -- (a newer flash cancels this one, and keeps the Highlight)
            hitFlash.Enabled = false
            hitFlash.Adornee = nil
        end
    end)
    fade:Play()
end

-- The striker's pose holds for `seconds` as their blow lands: the clip stops where it is, then goes on. Off with Reduced Effects.
local function hitStop(player, strike, seconds)
    if not strike or strikes[player] ~= strike or Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true then
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

-- Where a blow meets the guardian's body: a ray from the striker's chest through the point the server gave, against the boxes of the
-- target's solid parts (a guardian's parts are not CanQuery, so Raycast can't see them; a part's box is its mesh's bounding box, a skinned
-- guardian's being its pose at rest), the first one entered, a little off it toward the striker. Nil if it enters none within `reach`
-- (a ray starting inside the body does not): the caller keeps the old clamp. Cosmetic: the server's point and range are still the authority.
local bodyBoxes = setmetatable({}, { __mode = "k" }) -- [target] = its solid parts
local function boxesOf(target)
    local list = bodyBoxes[target]
    if not list then
        list = {}
        for _, part in target:GetDescendants() do
            local size = if part:IsA("BasePart") then part.Size else nil
            if size and part.Transparency < 0.5 and size.X * size.Y * size.Z > 40 and part.Name ~= "Eyes" then
                table.insert(list, part)
            end
        end
        bodyBoxes[target] = list
    end
    return list
end

local function skinPoint(from, position, target, reach)
    if not (target and target.Parent) then
        return nil
    end
    local aim = position - from
    if aim.Magnitude < 0.1 then
        return nil
    end
    local best = nil
    local dir = aim.Unit
    for _, part in boxesOf(target) do
        local frame = part.CFrame
        local o, d, half = frame:PointToObjectSpace(from), frame:VectorToObjectSpace(dir), part.Size / 2
        local tmin, tmax = 0, math.huge
        for _, axis in { "X", "Y", "Z" } do
            local oa, da, ha = o[axis], d[axis], half[axis]
            if math.abs(da) < 1e-6 then
                if math.abs(oa) > ha then
                    tmax = -1
                    break
                end
            else
                local t1, t2 = (-ha - oa) / da, (ha - oa) / da
                if t1 > t2 then
                    t1, t2 = t2, t1
                end
                tmin, tmax = math.max(tmin, t1), math.min(tmax, t2)
                if tmin > tmax then
                    break
                end
            end
        end
        if tmin > 0.05 and tmin <= tmax and (not best or tmin < best) then
            best = tmin
        end
    end
    if best and best <= reach then
        return from + dir * (best - 0.35)
    end
    return nil
end

-- Mirrors CombatService.findTarget: the nearest guardian in reach and arc, and where the blow meets it (nil, nil if none). Only to show
-- the blow's impact at its blow frame before the server's answer reaches us: the answer, never this, brings the number and a critical.
local function predictTarget(root, spec)
    local facing = root.CFrame.LookVector * Vector3.new(1, 0, 1)
    facing = if facing.Magnitude > 0 then facing.Unit else Vector3.new(0, 0, -1)
    local cosArc = math.cos(math.rad(spec.Arc))
    local best, bestDistance, bestPoint = nil, math.huge, nil
    for _, target in CollectionService:GetTagged(GameConfig.Combat.TargetTag) do
        local body = target:IsA("Model") and target.PrimaryPart
        if body and target:IsDescendantOf(Workspace) and target:GetAttribute("Invulnerable") ~= true then
            local radius = target:GetAttribute("HitRadius") or 2
            local offset = body.Position - root.Position
            local flat = offset * Vector3.new(1, 0, 1)
            local distance = math.max(0, flat.Magnitude - radius)
            local inFront = flat.Magnitude <= radius or (flat.Unit:Dot(facing) >= cosArc)
            if distance <= spec.Range and inFront and math.abs(offset.Y) <= radius + 4 and distance < bestDistance then
                best, bestDistance = target, distance
                local near = body.Position - (if flat.Magnitude > 0 then flat.Unit else facing) * math.min(radius, flat.Magnitude) * 0.9
                bestPoint = Vector3.new(near.X, root.Position.Y + 0.5, near.Z)
            end
        end
    end
    return best, bestPoint
end

-- the name a blow goes by in BLOWS
local SWORD_BLOWS = { "SwordA", "SwordB", "SwordC" }
local function nameOf(strike)
    if strike and strike.weapon == "Sword" then
        return SWORD_BLOWS[strike.step] or "SwordA"
    elseif strike and strike.weapon == "Spear" then
        return if strike.step == 2 then "SpearSlash" else "Thrust"
    end
    return "Palm"
end

-- the gold of a critical strike: a cross of light through the point, and a second ring of gold
local function criticalFlare(holder, power)
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
        Size = numberSequence({ { 0, 1.5 }, { 1, 11 * power } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = ColorSequence.new(CRIT_GOLD), Brightness = 2.2, LightEmission = 0.6, -- (fully additive, gold washed to white in Play)
    }):Emit(1)
end

-- whether the strike is the last blow of a weapon's chain (a nil strike, the blunt burst with no strike behind it, is not; nor is a fist's
-- second punch: bare hands have no heavy blow to end on)
local function finisherOf(strike)
    return strike ~= nil and strike.info ~= nil and strike.info.Finisher == true
end

-- how far a blow narrows the player's own view as it lands (GuardianFx.punch), in degrees: nothing for a chain's early blows
local function punchOf(strike, critical, size)
    local punch = if strike then (BLOWS[nameOf(strike)].Punch or 0) else 0
    if critical then
        punch = math.min(math.max(punch * CRIT_SHAKE, CRIT_PUNCH), PUNCH_MAX)
    end
    return punch * size
end

-- strike: the striker's strike as the server's answer came (nil if they had none: the blunt burst).
-- info: { damage, critical, target } from the server, or { target, predicted = true } for a blow shown before its answer.
local function landHit(player, position, info, strike)
    local blow, slash = blowOf(strike)
    local critical = info.critical == true
    -- what the form says the target does (Light, Heavy, Launch) is the weight of the blow: the guardian's reaction grade, the thump, the hold in the air;
    -- without a form's word (a blow shown before the server's answer, with none) the kind of blow decides as it always did
    local formLook = lookOf(strike and strike.info)
    local reaction = strike and strike.info and strike.info.Reaction
    local heavy = if reaction then critical or reaction ~= "Light" else critical or blow == "Pierce" or (slash ~= nil and slash.Finisher == true)
    local grade = if critical or reaction == "Launch" then "Critical" elseif heavy then "Heavy" else "Normal"
    local ladder = strike and HIT_LADDER[strike.weapon]
    Sfx.play(HIT_SOUND[blow], position, (ladder and ladder[strike.step] or 1) * formLook.Pitch)
    if heavy then
        Sfx.play("HeavyThump", position) -- (the weight under it)
    end
    if critical then
        Sfx.play("CritHit", position)
    end
    local mine = player == Players.LocalPlayer
    local camera = Workspace.CurrentCamera
    if not mine and (not camera or (camera.CFrame.Position - position).Magnitude > MAX_DISTANCE) then
        return
    end
    local root = rootOf(player)
    local tier = tierOf(player)
    local size = 1 + TIER_STEP * (tier - 1)
    local p = (strike and strike.palette) or QinggongFx.palette(player)
    local reduced = Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
    -- thinner for another player's blow on a phone, and with reduced effects
    local thin = (Quality.Low and not mine) or reduced
    local power = (if critical then 1.5 else 1) * size
    local hot = if critical then CRIT_GOLD else p.Core
    local direction = blowDirection(root, slash)
    -- on the guardian's skin, not in the air: a ray from the striker's chest; else the point the server gave, held within the weapon's reach
    if root then
        local from = root.Position + Vector3.new(0, 0.5, 0)
        local snapped = skinPoint(from, position, info.target, SKIN_REACH[blow])
        if snapped then
            position = snapped
        else
            local to = position - from
            if to.Magnitude > HIT_REACH[blow] then
                position = from + to.Unit * HIT_REACH[blow]
            end
        end
    end
    if strike then
        strike.impacted, strike.impactAt, strike.impactDirection = true, position, direction
    end
    local holder = host(CFrame.lookAt(position, position + direction), Vector3.new(0.4, 0.4, 0.4), 1)

    -- frame 0: a hard flash where it landed, and the sparks thrown along the blow, falling as they go
    -- (a thrust goes into its target, away from whoever is watching it: its sparks spray back off the point)
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.09), ZOffset = HIT_DEPTH + 1,
        Size = numberSequence({ { 0, 2.6 * power }, { 1, 4.8 * power } }), Transparency = numberSequence({ { 0, 0.05 }, { 1, 1 } }),
        Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 0.4, hot }, { 1, p.Main } }), Brightness = if critical then 1.8 else 2.5,
    }):Emit(1)
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
    if blow == "Cut" then
        -- the cut itself: a line of light through the point, along the blade's path
        emitter(holder, {
            Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, EmissionDirection = Enum.NormalId.Front,
            SpreadAngle = Vector2.new(0, 0), Speed = NumberRange.new(3), Lifetime = NumberRange.new(0.2), ZOffset = HIT_DEPTH + 1.2,
            Size = numberSequence({ { 0, 5 * power }, { 1, 8.5 * power } }), Transparency = numberSequence({ { 0, 0 }, { 0.5, 0.1 }, { 1, 1 } }),
            Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 1, hot } }), Brightness = 3,
        }):Emit(1)
    elseif blow == "Pierce" then
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
    end
    if critical and not info.predicted then
        criticalFlare(holder, size)
    end

    -- two frames on: the ring the blow punches out (small and quick for a pierce, broad for a blunt blow, a thin one for a heavy cut)
    -- four frames on: chips of what the guardian is made of (its own style: dust, leaves, cinders, frost, void), and for a heavy blow a
    -- faint scorch of light left on the skin
    local style = GuardianReact.style(info.target)
    task.delay(0.033 / CombatFx.TimeScale, function()
        if not holder.Parent then
            return
        end
        if blow ~= "Cut" or heavy then
            local reach = if blow == "Pierce" then 5.5 elseif blow == "Blunt" then 7.5 else 6
            emitter(holder, {
                Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(if blow == "Pierce" then 0.22 else 0.3), ZOffset = HIT_DEPTH + 0.8,
                Size = numberSequence({ { 0, 0.9 }, { 1, reach * power } }), Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }),
                Color = colorSequence({ { 0, hot }, { 1, p.Main } }), Brightness = 2,
            }):Emit(1)
        end
    end)
    task.delay(0.066 / CombatFx.TimeScale, function()
        if not holder.Parent or thin then
            return
        end
        if blow == "Blunt" or heavy then
            GuardianFx.puff(CFrame.new(position), style or { Debris = "Dust" }, if heavy then 5 else 3, 9, 70, 1.3, 0.55)
        end
        if heavy then
            emitter(holder, {
                Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.6), ZOffset = HIT_DEPTH,
                Size = numberSequence({ { 0, 3.2 * size }, { 1, 2.4 * size } }), Transparency = numberSequence({ { 0, 0.6 }, { 0.3, 0.7 }, { 1, 1 } }),
                Color = colorSequence({ { 0, hot }, { 1, p.Main } }), Brightness = 1.6,
            }):Emit(1)
        end
    end)

    if not (Quality.Low and not mine) then
        flashTarget(info.target, hot:Lerp(Color3.new(1, 1, 1), 0.5), critical)
    end
    if info.target then
        GuardianReact.hit(info.target, direction, grade) -- the guardian flinches
    end
    local spec = BLOWS[nameOf(strike)]
    local weight = if reaction == "Launch" then 1.25 elseif reaction == "Light" then 0.8 else 1 -- (a form's blows are held and shaken to its look and to its reaction)
    local stop = spec.Stop * formLook.Stop * weight
    local shake, shakeTime, kick = spec.Shake[1] * size * formLook.Shake * weight, spec.Shake[2], spec.Kick * size
    if critical then
        stop = math.min(stop * CRIT_STOP, CRIT_STOP_MAX)
        shake, shakeTime = math.min(shake * CRIT_SHAKE, CRIT_SHAKE_MAX[1]), math.min(shakeTime * CRIT_SHAKE, CRIT_SHAKE_MAX[2])
        kick = math.min(kick * CRIT_SHAKE, CRIT_SHAKE_MAX[1])
    end
    hitStop(player, strike, stop)
    if mine then
        GuardianFx.shake(position, shake, shakeTime)
        if camera then
            -- the camera is knocked along the way the blow travelled: a downward cut nods it down, a sideways one turns it with the blade, a
            -- thrust or a punch dips it a little
            local look = camera.CFrame:VectorToObjectSpace(direction)
            GuardianFx.kick(position, kick * (0.8 * look.Y + 0.35 * look.Z), -kick * 0.8 * look.X, shakeTime)
        end
        local punch = punchOf(strike, critical, size)
        if punch > 0 then
            GuardianFx.punch(punch, PUNCH_TIME)
        end
        if info.damage then
            DamageNumbers.show(position + Vector3.new(0, 1.5, 0), info.damage, critical, p.Main, finisherOf(strike))
        end
    end
end

-- The server's answer to a blow that was already shown (predicted): what only the server knows, its damage and a critical strike.
local function confirmHit(player, strike, info)
    local position = strike.impactAt
    local p = strike.palette or QinggongFx.palette(player)
    if info.critical == true then
        local holder = host(CFrame.lookAt(position, position + strike.impactDirection), Vector3.new(0.4, 0.4, 0.4), 1)
        criticalFlare(holder, 1 + TIER_STEP * (tierOf(player) - 1))
        Sfx.play("CritHit", position)
        if info.target then
            GuardianReact.hit(info.target, strike.impactDirection, "Critical")
        end
        GuardianFx.shake(position, 0.6, 0.18)
        if player == Players.LocalPlayer then
            GuardianFx.punch(punchOf(strike, true, 1 + TIER_STEP * (tierOf(player) - 1)), PUNCH_TIME) -- (the blow's own was drawn at its frame)
        end
    end
    if player == Players.LocalPlayer and info.damage then
        DamageNumbers.show(position + Vector3.new(0, 1.5, 0), info.damage, info.critical == true, p.Main, finisherOf(strike))
    end
end

-- The server answers at once, but the blow lands part way through the strike's clip: the impact waits for it. If the answer is later than
-- that (a slow connection, the palm's blow comes at 0.1 s), the impact was already shown from the client's own look at it (play), and the
-- answer adds the number and a critical's flare. info: what the server said it did: { damage, critical, target }.
function CombatFx.hit(player, position, info)
    info = info or {}
    local strike = strikes[player]
    if strike then
        strike.answered = true
    end
    if strike and strike.impacted then
        confirmHit(player, strike, info)
        return
    end
    local wait = strike and strike.hitAt and (strike.hitAt - (os.clock() - strike.started) * CombatFx.TimeScale) / CombatFx.TimeScale or 0
    if wait > 0.01 then
        task.delay(wait, landHit, player, position, info, strike)
    else
        landHit(player, position, info, strike)
    end
end

-- The server says a strike of theirs hit nothing: a blow that was to be shown from the client's own look at it is dropped.
function CombatFx.missed(player)
    local strike = strikes[player]
    if strike then
        strike.answered = true
    end
end

-- ---------- the step into a strike ----------
-- (the owner, 2026-11-23: "make combos flow naturally from one attack into another") A strike carries the striker forward as its blade
-- comes round, so a chain of them walks into the target instead of swinging on the spot: how far each one steps, in studs, by weapon and
-- step (a finisher and a thrust step furthest; a fist hardly). Only for the player's own character, which their client moves; the others see
-- it arrive. The step begins part way through the wind-up and is over as the blow lands, an eased slide (the character's own pose clips
-- already lean and turn the hips: this is the travel under them). It is a movement of the character, not a speed given to it: the pose
-- code takes a character with any speed over a few studs a second for a runner and drops the clip's legs (PoseController STANCE_MAX_SPEED),
-- and a speed given to a Humanoid is half taken back by its floor friction, more at a low frame rate (Play, 2026-11-23: 0.91 of 1.4 studs
-- at 56 fps, 0.68 at 15). It moves the same studs at any frame rate and MovementGuard sees a few studs in a third of a second. It never
-- steps a player who is running or airborne, stops short of a wall, a guardian and an edge, and ends at the blow.
local LUNGE = { Sword = { 1.6, 2.0, 2.8 }, Spear = { 3.0, 2.0 }, Palm = { 1.0, 1.0 } }
local LUNGE_RUNNING = 20      -- a player faster than this (studs a second) is already travelling: no step
local LUNGE_WALKING = 3       -- faster than this and they are walking: half the step (they are going that way already)
local LUNGE_CLEAR = 1.6       -- studs left between the end of a step and a wall or a guardian's skin (the character is about 1 wide)
local LUNGE_DROP = 6          -- a step that would end over a drop deeper than this is cut to nothing
local LUNGE_AIM = 0.8         -- a guardian this much ahead (cosine) of the facing shortens the step to stop at it
local LUNGE_STOP_SHORT = 4.5  -- studs from a guardian's centre at which the step stops

local function lungeParams(character)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { character, fxFolder }
    params.RespectCanCollide = true
    return params
end

-- how far (studs) a step of `reach` along `direction` from `root` can go
local function clearReach(root, character, direction, reach)
    local params = lungeParams(character)
    local origin = root.Position
    local wall = Workspace:Raycast(origin, direction * (reach + LUNGE_CLEAR), params)
    if wall then
        reach = math.max(0, math.min(reach, wall.Distance - LUNGE_CLEAR))
    end
    if reach <= 0 then
        return 0
    end
    local ground = Workspace:Raycast(origin + direction * reach, Vector3.new(0, -(LUNGE_DROP + 3.5), 0), params) -- (the root is about 3 above the feet)
    if not ground then
        return 0
    end
    return reach
end

local function lunge(player, root, strike, timing, target, point)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local reaches = LUNGE[strike.weapon]
    local reach = reaches and reaches[strike.step]
    if not reach or not humanoid or humanoid.Health <= 0 or humanoid.Sit or humanoid.FloorMaterial == Enum.Material.Air then
        return
    end
    local flat = Vector3.new(1, 0, 1)
    local speed = (root.AssemblyLinearVelocity * flat).Magnitude
    if speed > LUNGE_RUNNING then
        return
    elseif speed > LUNGE_WALKING then
        reach *= 0.5
    end
    local facing = root.CFrame.LookVector * flat
    if facing.Magnitude < 0.1 then
        return
    end
    local direction = facing.Unit
    if target and point then -- stop at a guardian ahead of them, not through it
        local to = (point - root.Position) * flat
        if to.Magnitude > 0.1 and to.Unit:Dot(direction) >= LUNGE_AIM then
            reach = math.min(reach, math.max(0, to.Magnitude - LUNGE_STOP_SHORT))
        end
    end
    reach = clearReach(root, character, direction, reach)
    if reach < 0.25 then
        return
    end
    local scale = CombatFx.TimeScale
    local begin = timing.Wind * 0.55 / scale
    local duration = math.max(0.12, (timing.Hit + 0.02 - timing.Wind * 0.55)) / scale
    task.delay(begin, function()
        if strikes[player] ~= strike then
            return
        end
        local started, done = os.clock(), 0 -- done: the share of the step already made
        local connection
        connection = RunService.Heartbeat:Connect(function()
            local share = math.min((os.clock() - started) / duration, 1)
            if strikes[player] ~= strike or strike.impacted or not root.Parent or humanoid.Health <= 0
                or humanoid.FloorMaterial == Enum.Material.Air or player:GetAttribute("IsFlying") == true then
                connection:Disconnect()
                return
            end
            local eased = (1 - math.cos(math.pi * share)) / 2 -- (slow, quick, slow: the studs covered by the half sine of speed)
            character:PivotTo(character:GetPivot() + direction * (reach * (eased - done)))
            done = eased
            if share >= 1 then
                connection:Disconnect()
            end
        end)
    end)
end

-- a ring of light spreading over the ground from a character's feet (a form's finisher, a change of form): a thin plate on the ground wearing the
-- shockwave texture, growing to `size` studs across while it fades
local function groundRing(root, color, size, life)
    local feet = root.Position - Vector3.new(0, 2.9, 0)
    local plate = host(CFrame.new(feet), Vector3.new(1, 0.05, 1), life + 0.1)
    local labels = {}
    for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
        local gui, label = flat(face, TEXTURES.Shockwave, color, 0.1)
        gui.Brightness = 2.6
        gui.Parent = plate
        table.insert(labels, label)
    end
    TweenService:Create(plate, TweenInfo.new(life, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(size, 0.05, size) }):Play()
    for _, label in labels do
        TweenService:Create(label, TweenInfo.new(life * 0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, life * 0.3), { ImageTransparency = 1 }):Play()
    end
end

-- ---------- entry points ----------
-- info: the form's strike (FormRules.plan for our own, the server's form and step for everyone else's). Nothing plays without one: the chain is the form's.
function CombatFx.play(player, weapon, info)
    local root = rootOf(player)
    if not (root and info) then
        return
    end
    local now = os.clock()
    local strike = { weapon = weapon, started = now, info = info, step = clipStep(weapon, info) }
    if weapon == "Palm" then
        putAway(player) -- a palm strike is bare-handed
    end
    local timing = retimed(if weapon == "Sword" then SLASHES[strike.step].Timing
        elseif weapon == "Spear" then (if strike.step == 2 then SPEAR_SLASH.Timing else THRUST_TIMING)
        else PUNCH_TIMINGS[strike.step], weapon, info)
    strike.timing = timing
    strike.hitAt = timing.Hit
    strike.untilTime = now + timing.Length / CombatFx.TimeScale
    strikes[player] = strike
    local camera = Workspace.CurrentCamera
    if player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE) then
        return
    end
    if SWING[weapon] then
        Sfx.play(SWING[weapon], root)
    end
    local p = formPalette(QinggongFx.palette(player), info, nil)
    strike.palette = p
    local ringSize = lookOf(info).Ring
    if info.Finisher and ringSize and Players.LocalPlayer:GetAttribute("SettingReducedEffects") ~= true then
        task.delay(timing.Hit / CombatFx.TimeScale, function() -- the finisher's blow lands a ring on the ground
            if root.Parent then
                groundRing(root, p.Main, ringSize, 0.55)
            end
        end)
    end
    if player == Players.LocalPlayer and player:GetAttribute("IsFlying") ~= true then
        -- the blow at its blow frame, from our own look at it, if the server's answer isn't here by then (see CombatFx.hit)
        local target, point = predictTarget(root, info) -- (the form's own reach and arc)
        lunge(player, root, strike, timing, target, point)
        if target then
            task.delay(timing.Hit / CombatFx.TimeScale, function()
                if not strike.answered and not strike.impacted then
                    landHit(player, point, { target = target, predicted = true }, strike)
                end
            end)
        end
    end
    if weapon == "Sword" then
        sword(player, p, root, strike.step, strike)
    elseif weapon == "Spear" then
        spear(player, p, root, strike.step, strike)
    else
        -- the Qi print flies as the fist lands
        task.delay(timing.Hit / CombatFx.TimeScale, function()
            if root.Parent then
                palm(p, root)
            end
        end)
    end
end

-- A player changes form (their "Form<Family>" attribute changed, the server having allowed it): a ring over the ground and a flash of light in the
-- form's colour, seen by everyone near. Off with Reduced Effects (the notice still says it).
function CombatFx.formChange(player, id)
    local root = rootOf(player)
    if not root or Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true then
        return
    end
    local camera = Workspace.CurrentCamera
    if player ~= Players.LocalPlayer and (not camera or (camera.CFrame.Position - root.Position).Magnitude > MAX_DISTANCE) then
        return
    end
    local look = FORM_LOOKS[id]
    local tint = (look and look.Tint) or QinggongFx.palette(player).Main
    groundRing(root, tint, 11, 0.7)
    local flash = host(root.CFrame, Vector3.new(0.4, 0.4, 0.4), 1)
    emitter(flash, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.55),
        Size = numberSequence({ { 0, 2.5 }, { 1, 10 } }), Transparency = numberSequence({ { 0, 0.25 }, { 1, 1 } }),
        Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 1, tint } }), Brightness = 2.2,
    }):Emit(1)
    Sfx.play("Notify", root.Position, 1.2)
end

-- ---------- drawn and sheathed (the owner, 2026-11-11: "add equip and unequip for weapons", a draw / sheathe toggle) ----------
-- A player's "WeaponDrawn" attribute (set by the server, CombatService) keeps their own weapon in the hand, in its ready
-- stance, until they sheathe it. Sheathed, it rests across the back. Both show on every player within MAX_DISTANCE.
local TEND_EVERY = 0.25 -- seconds between looks at who should hold or wear what
-- on the back, in the UpperTorso's space (its back is +Z): where the weapon's middle sits, and the way its point runs.
-- A sword (about 6 studs) hangs point down, the hilt over the right shoulder; a spear (about 10) rides head up over the
-- right shoulder, steep and high enough that its butt clears the ground
local SHEATH = {
    Sword = { Centre = Vector3.new(0.05, 0.05, 0.62), Point = Vector3.new(-0.55, -0.83, 0) },
    Spear = { Centre = Vector3.new(0, 1.3, 0.62), Point = Vector3.new(0.4, 0.92, 0) },
}
local sheathed = {} -- [player] = { model, source, element, torso }

-- the player's own weapon (their "WeaponId") and its kind, or nil for bare hands
local function ownWeapon(player)
    local folder = ReplicatedStorage:FindFirstChild("Weapons")
    local source = folder and folder:FindFirstChild(player:GetAttribute("WeaponId") or "")
    local kind = source and source:GetAttribute("Kind")
    if kind == "Sword" or kind == "Spear" then
        return source, kind
    end
    return nil, nil
end

local function unsheathe(player)
    local entry = sheathed[player]
    if entry then
        sheathed[player] = nil
        if entry.aura then
            entry.aura:destroy()
        end
        entry.model:Destroy()
    end
end

-- the weapon across the back, welded to the torso
local function sheathe(torso, source, kind, tint, element, mine)
    local model, parts = weaponModel(source, tint, false)
    local spec = SHEATH[kind]
    -- the weapon's length along its own Z (the point is -Z), from its parts: its Hilt and Tip mark the blade, not the whole
    local low, high = math.huge, -math.huge
    for part, offset in parts do
        local size = part.Size
        local half = 0.5 * (math.abs(offset.XVector.Z) * size.X + math.abs(offset.YVector.Z) * size.Y + math.abs(offset.ZVector.Z) * size.Z)
        low, high = math.min(low, offset.Position.Z - half), math.max(high, offset.Position.Z + half)
    end
    local middle = Vector3.new(0, 0, (low + high) / 2)
    local turn = CFrame.lookAt(Vector3.zero, spec.Point, Vector3.zAxis) -- the point (-Z) along spec.Point, flat to the back
    local origin = CFrame.new(spec.Centre - turn:VectorToWorldSpace(middle)) * turn
    for part, offset in parts do
        part.Anchored = false
        part.Massless = true
        part.CanCollide, part.CanTouch, part.CanQuery = false, false, false
        local weld = Instance.new("Weld")
        weld.Part0, weld.Part1 = torso, part
        weld.C0 = origin * offset
        weld.Parent = part
    end
    local body = model:FindFirstChild("Body")
    return model, body and WeaponAura.attach(body, parts[body], source.Name, { mine = mine, mode = "sheathed", element = element })
end

local function draw(player, source, kind)
    local _, element = elementOf(player, source, false)
    local p = strikePalette(QinggongFx.palette(player), element)
    local glow = if kind == "Spear" then (if element then element.Color else swordGlow(player)) else nil
    hold(player, kind, source, false, element and element.Color, holdSpec(kind, source, glow), p, element)
end

local function tend()
    local camera = Workspace.CurrentCamera
    for _, player in Players:GetPlayers() do
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        local torso = character and character:FindFirstChild("UpperTorso")
        local root = character and character:FindFirstChild("HumanoidRootPart")
        local source, kind = ownWeapon(player)
        local shown = source ~= nil and torso ~= nil and root ~= nil and humanoid ~= nil and humanoid.Health > 0
            and (player == Players.LocalPlayer or (camera ~= nil and (camera.CFrame.Position - root.Position).Magnitude <= MAX_DISTANCE))
        if shown and player:GetAttribute("WeaponDrawn") == true and not held[player] and player:GetAttribute("IsCultivating") ~= true
            and player:GetAttribute("CarryingEgg") == nil and player:GetAttribute("IsFlying") ~= true then
            draw(player, source, kind)
        end
        local element = player:GetAttribute("WeaponElement")
        local entry = sheathed[player]
        local wanted = shown and not held[player]
        if entry and not (wanted and entry.source == source and entry.element == element and entry.torso == torso) then
            unsheathe(player)
            entry = nil
        end
        if wanted and not entry then
            local info = typeof(element) == "string" and GameConfig.Forge.Elements[element]
            local model, aura = sheathe(torso, source, kind, info and info.Color, info or nil, player == Players.LocalPlayer)
            entry = { model = model, aura = aura, source = source, element = element, torso = torso }
            sheathed[player] = entry
        end
        -- the aura's strength by distance: your own at full; others' thinned, then off (a phone sooner), and thinner still with
        -- Reduced Effects
        local far = camera and root and (camera.CFrame.Position - root.Position).Magnitude or math.huge
        local mine = player == Players.LocalPlayer
        local near, mid = if Quality.Low then 35 else 55, if Quality.Low then 70 else 110
        local capped = Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
        local heldEntry = held[player]
        local detail = if mine then 2 elseif far <= near then 2 elseif far <= mid then 1 else 0
        if capped and not mine then
            detail = math.min(detail, 1)
        end
        if heldEntry and heldEntry.aura then
            heldEntry.aura:setDetail(if heldEntry.hand:IsDescendantOf(Workspace) then detail else 0)
        end
        if entry and entry.aura then
            entry.aura:setDetail(math.min(detail, 1) * (if far <= (if Quality.Low then 30 else 45) or mine then 1 else 0))
        end
    end
end

do
    local waited = 0
    RunService.Heartbeat:Connect(function(dt)
        waited += dt
        if waited >= TEND_EVERY then
            waited = 0
            tend()
        end
    end)
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
            return strike.step, clipTime(strike.timing, strike.holdAt)
        end
        return strike.step, clipTime(strike.timing, (os.clock() - strike.started) * CombatFx.TimeScale)
    end
    return 1, 0
end

Players.PlayerRemoving:Connect(function(player)
    strikes[player] = nil
    putAway(player)
    unsheathe(player)
end)

return CombatFx

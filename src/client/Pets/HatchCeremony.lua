-- The hatch cinematic, as the hatcher sees it (the owner, November 10, 2026: "a cinematic egg-hatching animation" with "a gacha-style
-- rolling animation"; plan approved: a horizontal reel, about 5 s). The server has already chosen the beast (PetService) and laid
-- the egg in the altar's cradle (a model everyone sees); this only shows it, in five beats:
--   1. letterbox bars close in, the HUD steps aside, the camera glides round to the egg;
--   2. the egg rises and shivers while a reel of the egg's beasts races past a gold marker, drawn at the egg's real odds (the
--      player's own lucky odds with the Luck pass: PassRules.luckyPool, as the server rolled), undiscovered beasts as silhouettes;
--   3. as it slows, the marker and the egg glow the winner's rarity colour: the rarity first, the beast second;
--   4. the egg cracks at the server's BreakAt, in a burst of the rarity's light;
--   5. a reveal card: the beast turning, its name, rarity, chance, its size, and NEW or Duplicate.
--
-- The rarity ladder (the owner, 2026-11-16: "Improve the egg hatching animation depending on rarity and the size of the pets";
-- after studying how the big pet games stage a hatch). Every step up adds something the one below doesn't have:
--   Common     quick and clean: a flash and sparks, a plain card. A duplicate's card goes sooner.
--   Uncommon   + a small ring of light on the ground, a few slow rays behind the beast, a ping on the chime.
--   Rare       + light leaks out of the egg before it breaks (a glow inside, streaks), rays out of the burst, a full shockwave,
--                the lens punches in; the reel lands a beat before the crack.
--   Epic       + shafts of light break out of the egg and turn while it trembles, a fountain of sparks, a small camera shake,
--                light running round the card's edge, a short harp.
--   Legendary  + the egg is held a breath (it lifts, trembles, the camera leans in), the screen's edges glow its colour, a
--                column of light shoots up, a screen flash, a banner, a band of light across the card, the reward stinger.
--   Mythical   + a different sequence: the reel drops away, the bars close tighter, the camera circles the egg, the burst plays in
--                slow motion, two rings, a second set of rays turning the other way, the banner says how rare it was.
--   Secret     + the world drains to darkness while the egg's light grows, a breath drawn in before it breaks, the angelic vocal.
--   Divine     + a pillar of light comes down from the sky onto the egg, a white-out flash, the beast in its own glow.
-- The size ladder (PetRules.Sizes, rolled by the server):
--   Small      a cute, light beat: the egg hops as it glows, the beast settles smaller and bounces twice, a pop and a ping.
--   Normal     nothing extra.
--   Large      the egg swells as it glows; the beast drops onto the card with a thud and a small shake, a gold LARGE stamp, a
--              gold ring and burst at the egg, the camera pulls back a little.
--   Giant      the egg strains, swelling and throbbing; the card holds a trembling beat, then the beast grows past the card, a
--              GIANT! stamp slams on, a gold shockwave and flash, a heavy shake, and the camera pulls well back to take it in.
-- A tap moves on a beat (during the reel it lands it; during the held breath it breaks the egg; on the card it closes it). The
-- player's Reduced Effects setting drops the shake, the flashes and most particles; a phone (Quality.Low) thins the particles.
--   HatchCeremony.play(result)   result: the server's EggHatchResultEvent (EggId, PetId, ChancePercent, Size, IsNew, Staged, BreakAt)
--   HatchCeremony.afterBreak(result)  seconds the cinematic runs past the egg's break for this result (the altar window's fallback)
--   HatchCeremony.Finished       fires (with the result's BreakAt) when a cinematic ends: the altar window comes back at once
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Client = script.Parent.Parent
local UI = Client:WaitForChild("UI")
local HudMetrics = require(UI:WaitForChild("HudMetrics"))
local Portraits = require(UI:WaitForChild("Portraits"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local applyHudScale = require(UI:WaitForChild("HudScale"))
local Sfx = require(Client:WaitForChild("Audio"):WaitForChild("Sfx"))
local LOW = require(Client:WaitForChild("Quality")).Low
local CodexState = require(script.Parent:WaitForChild("CodexState"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local finished = Instance.new("BindableEvent")
local HatchCeremony = { Finished = finished.Event }

-- ---------- tuning ----------
local INTRO = 0.6            -- seconds the camera takes to glide in
local CARD_W, CARD_H, GAP = 96, 116, 8
local STEP = CARD_W + GAP
local CARDS = 34             -- the reel's length
local WINNER = 29            -- where the winner sits on it
local RISE = 1.6             -- studs the egg lifts from the cradle
local HOLD_RISE = 0.7        -- and further while it's held before breaking
local CRACK_TO_CARD = 0.35   -- seconds from the crack to the reveal card
local OUTRO = 0.45
local CARD_HEIGHT = 330      -- the reveal card's height (before the HUD's scale)
local TEXTURES = {           -- (GuardianFx's and the character aura's)
    Glow = "rbxassetid://135169457468310",
    Streak = "rbxassetid://115312010132075",
    Ring = "rbxassetid://81927825399672",
    Spark = "rbxassetid://112814194154292",
}
local SWELL_PEAK = 2.17 -- seconds into HatchSwell its burst lands: it starts that long before the crack
-- The ladder, one row per rarity (the header has it in words). Rank gates what each step adds:
--   2 ground ring, card rays; 3 light leaks, burst rays, full ring, lens punch; 4 shafts of light, spark fountain, shake, card edge
--   light; 5 the held breath, screen edges, light column, flash, banner, card sweep; 6 the reel drops away, tighter bars, the camera
--   circles, slow motion, two rings, counter rays, the odds under the banner; 7 darkness, the drawn breath; 8 the sky pillar, white-out,
--   the beast's glow.
-- Hold: seconds the egg is held between the reel landing and the crack (taken from the reel: the crack stays on the server's time).
-- Reveal: seconds the card stays; Dup: for a beast already owned (a repeat gets out of the way). Shafts: shafts of light (rank 4+).
local TIERS = {
    Common = { Rank = 1, Hold = 0, Sparks = 14, Rays = 0, CardRays = 0, Reveal = 1.9, Dup = 1.3, Sound = "HatchReveal" },
    Uncommon = { Rank = 2, Hold = 0, Sparks = 20, Rays = 0, CardRays = 8, Reveal = 2, Dup = 1.5, Sound = "HatchRevealUncommon" },
    Rare = { Rank = 3, Hold = 0.2, Sparks = 28, Rays = 10, CardRays = 10, Reveal = 2.2, Dup = 1.8, Sound = "HatchRevealRare" },
    Epic = { Rank = 4, Hold = 0.35, Sparks = 34, Rays = 14, CardRays = 12, Shafts = 4, Shake = 0.2, Reveal = 2.4, Sound = "HatchRevealEpic" },
    Legendary = { Rank = 5, Hold = 0.6, Sparks = 42, Rays = 18, CardRays = 16, Shafts = 6, Shake = 0.35, Banner = "LEGENDARY!",
        Reveal = 2.8, Sound = "HatchRevealLegendary" },
    Mythical = { Rank = 6, Hold = 0.85, Sparks = 48, Rays = 22, CardRays = 16, Shafts = 8, Shake = 0.45, Banner = "MYTHICAL!",
        Reveal = 3.1, Sound = "HatchRevealMythical" },
    Secret = { Rank = 7, Hold = 1, Sparks = 54, Rays = 26, CardRays = 18, Shafts = 8, Shake = 0.55, Banner = "SECRET!",
        Reveal = 3.3, Sound = "HatchRevealSecret" },
    Divine = { Rank = 8, Hold = 1.2, Sparks = 60, Rays = 30, CardRays = 18, Shafts = 10, Shake = 0.6, Banner = "DIVINE!",
        Reveal = 3.5, Sound = "HatchRevealDivine" },
}
-- the size beats: Swell, how much the egg swells while it glows; Pull, how far the camera pulls back at the stamp (and Ease, how
-- slowly it comes back: a Giant's stays wide while it is shown)
local SIZE_BEATS = {
    Small = { Swell = 0, Pull = 0, Ease = 3 },
    Normal = { Swell = 0, Pull = 0, Ease = 3 },
    Large = { Swell = 0.1, Pull = 0.55, Ease = 2.2 },
    Giant = { Swell = 0.24, Pull = 1, Ease = 0.6 },
}

local active = nil -- the playing cinematic: { finish = function(instant) }
-- a finished cinematic still fading out: completes its restore (camera, HUD, screen) at once. A new cinematic calls it before
-- saving the camera, or it would save the old one's Scriptable camera and leave the player's view frozen when it ends.
local pendingRestore = nil

local function rarityColor(rarity)
    return GameConfig.PetRarityColors[rarity] or Color3.new(1, 1, 1)
end

local function reduced()
    return player:GetAttribute("SettingReducedEffects") == true
end

local function tween(object, seconds, goal, style, direction)
    local t = TweenService:Create(object, TweenInfo.new(seconds, style or Enum.EasingStyle.Quad, direction or Enum.EasingDirection.Out), goal)
    t:Play()
    return t
end

local function tierOf(rarity)
    return TIERS[rarity] or TIERS.Common
end

-- ---------- the light at the egg (world particles: they don't render inside a ViewportFrame) ----------
local function emitter(parent, props)
    local e = Instance.new("ParticleEmitter")
    e.Rate = 0
    e.LightEmission = 1
    e.LightInfluence = 0
    for k, v in props do
        e[k] = v
    end
    e.Parent = parent
    return e
end

local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end

-- an invisible anchored part to hang light on, gone after `life` seconds (and with the cinematic's folder, whichever is first)
local function holderAt(folder, at, life)
    local holder = Instance.new("Part")
    holder.Anchored, holder.CanCollide, holder.CanQuery, holder.CanTouch, holder.CastShadow = true, false, false, false, false
    holder.Transparency = 1
    holder.Size = Vector3.new(0.4, 0.4, 0.4)
    holder.CFrame = CFrame.new(at)
    holder.Parent = folder
    task.delay(life, function()
        holder:Destroy()
    end)
    return holder
end

-- The crack's burst, by rarity (TIERS). Returns its emitters (a slow-motion burst eases them back to full speed).
local function burst(folder, at, tier, color, cut)
    local rank = tier.Rank
    -- (the colour stays the rarity's: a paler core and a high brightness, stacked over a few layers, washed a Mythical to white in
    -- Play; the grand ones carry more layers, so each is a touch dimmer)
    local core = color:Lerp(Color3.new(1, 1, 1), 0.3)
    local dim = if rank >= 5 then 0.7 else 1
    local made = {}
    local function emit(parent, props, count)
        local e = emitter(parent, props)
        table.insert(made, { e, count })
        return e
    end
    local holder = holderAt(folder, at, 3.5)
    -- the flash of the egg breaking
    emit(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5),
        Size = seq({ { 0, 3 }, { 1, 9 + rank * 0.8 } }), Transparency = seq({ { 0, 0.25 }, { 1, 1 } }),
        Color = ColorSequence.new(core, color), Brightness = 2.2 * dim,
    }, 1)
    -- sparks thrown up and out, falling back
    emit(holder, {
        Texture = TEXTURES.Spark, Speed = NumberRange.new(6, 13), SpreadAngle = Vector2.new(60, 60), EmissionDirection = Enum.NormalId.Top,
        Lifetime = NumberRange.new(0.8, 1.4), Acceleration = Vector3.new(0, -12, 0), Drag = 1.2,
        Size = seq({ { 0, 0.55 }, { 1, 0 } }), Color = ColorSequence.new(core, color), Brightness = 2.4 * dim,
    }, math.floor(tier.Sparks * cut))
    -- rays of light bursting out all round (Rare up)
    if tier.Rays > 0 then
        emit(holder, {
            Texture = TEXTURES.Streak, Speed = NumberRange.new(26, 34), SpreadAngle = Vector2.new(180, 180),
            Orientation = Enum.ParticleOrientation.VelocityParallel, Lifetime = NumberRange.new(0.3, 0.45), Drag = 4,
            Size = seq({ { 0, 3.2 }, { 1, 0.6 } }), Transparency = seq({ { 0, 0.25 }, { 1, 1 } }),
            Color = ColorSequence.new(core, color), Brightness = 1.8 * dim,
        }, math.floor(tier.Rays * cut))
    end
    -- a fountain of sparks that rises and hangs (Epic up)
    if rank >= 4 then
        emit(holder, {
            Texture = TEXTURES.Spark, Speed = NumberRange.new(8, 16), SpreadAngle = Vector2.new(18, 18), EmissionDirection = Enum.NormalId.Top,
            Lifetime = NumberRange.new(1.4, 2.2), Acceleration = Vector3.new(0, -3, 0), Drag = 1.6,
            Size = seq({ { 0, 0.35 }, { 0.5, 0.45 }, { 1, 0 } }), Color = ColorSequence.new(core, color), Brightness = 1.8 * dim,
        }, math.floor((8 + rank * 3) * cut))
    end
    -- a column of light shooting straight up (Legendary up)
    if rank >= 5 then
        emit(holder, {
            Texture = TEXTURES.Streak, Speed = NumberRange.new(40, 55), SpreadAngle = Vector2.new(6, 6), EmissionDirection = Enum.NormalId.Top,
            Orientation = Enum.ParticleOrientation.VelocityParallel, Lifetime = NumberRange.new(0.45, 0.6), Drag = 2,
            Size = seq({ { 0, 3.5 }, { 1, 0.8 } }), Transparency = seq({ { 0, 0.2 }, { 1, 1 } }),
            Color = ColorSequence.new(core, color), Brightness = 1.8,
        }, math.max(3, math.floor((rank - 2) * 2 * cut)))
    end
    -- a shockwave flat across the ground (a particle rising almost not at all, laid flat by VelocityPerpendicular): small for an
    -- Uncommon, full from Rare, a second behind it from Mythical
    if rank >= 2 then
        local ground = holderAt(folder, at - Vector3.new(0, RISE + 0.4, 0), 3)
        local ring = emit(ground, {
            Texture = TEXTURES.Ring, Speed = NumberRange.new(0.01), EmissionDirection = Enum.NormalId.Top,
            Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Lifetime = NumberRange.new(0.7),
            Size = seq({ { 0, 1 }, { 1, if rank >= 3 then 16 else 8 } }), Transparency = seq({ { 0, 0.05 }, { 0.6, 0.4 }, { 1, 1 } }),
            Color = ColorSequence.new(core, color), Brightness = 2.4 * dim,
        }, 1)
        if rank >= 6 then
            task.delay(0.18, function()
                if ring.Parent then
                    ring.Lifetime = NumberRange.new(1.1)
                    ring:Emit(1)
                end
            end)
        end
    end
    local list = {}
    for _, pair in made do
        if pair[2] > 0 then
            pair[1]:Emit(pair[2])
        end
        table.insert(list, pair[1])
    end
    return list
end

-- the gold light of a big hatch round the egg: a flash, a shockwave across the ground and a few long rays (Neon-bright gold, no
-- sparkle: the stamp and the beast carry it). `power`: 1 for Giant, less for Large.
local function sizeBurst(folder, at, color, power, cut)
    local holder = holderAt(folder, at, 3)
    local core = color:Lerp(Color3.new(1, 1, 1), 0.4)
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.6),
        Size = seq({ { 0, 4 }, { 1, 9 + 9 * power } }), Transparency = seq({ { 0, 0.15 }, { 1, 1 } }),
        Color = ColorSequence.new(core, color), Brightness = 2.4,
    }):Emit(1)
    local ground = holderAt(folder, at - Vector3.new(0, RISE + 0.4, 0), 2.5)
    local ring = emitter(ground, {
        Texture = TEXTURES.Ring, Speed = NumberRange.new(0.01), EmissionDirection = Enum.NormalId.Top,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Lifetime = NumberRange.new(0.9),
        Size = seq({ { 0, 1.5 }, { 1, 14 + 16 * power } }), Transparency = seq({ { 0, 0 }, { 0.55, 0.35 }, { 1, 1 } }),
        Color = ColorSequence.new(core, color), Brightness = 2.6,
    })
    ring:Emit(1)
    if power >= 1 then -- a second, slower ring behind the first
        task.delay(0.16, function()
            if ring.Parent then
                ring.Lifetime = NumberRange.new(1.2)
                ring:Emit(1)
            end
        end)
    end
    emitter(holder, {
        Texture = TEXTURES.Streak, Speed = NumberRange.new(22, 30), SpreadAngle = Vector2.new(180, 25),
        EmissionDirection = Enum.NormalId.Top, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Lifetime = NumberRange.new(0.35, 0.55), Drag = 4,
        Size = seq({ { 0, 3.6 }, { 1, 0.6 } }), Transparency = seq({ { 0, 0.05 }, { 1, 1 } }),
        Color = ColorSequence.new(core, color), Brightness = 2.8,
    }):Emit(math.floor((6 + 10 * power) * cut))
end

-- a Small one's puff: a few soft pale sparkles popping out (no ring, no rays: it's a light beat)
local function smallPuff(folder, at, color, cut)
    local holder = holderAt(folder, at, 2)
    emitter(holder, {
        Texture = TEXTURES.Spark, Speed = NumberRange.new(3, 6), SpreadAngle = Vector2.new(180, 180),
        Lifetime = NumberRange.new(0.5, 0.8), Drag = 3, Acceleration = Vector3.new(0, 2, 0),
        Size = seq({ { 0, 0.3 }, { 0.4, 0.4 }, { 1, 0 } }), Color = ColorSequence.new(Color3.new(1, 1, 1), color), Brightness = 1.8,
    }):Emit(math.max(4, math.floor(12 * cut)))
end

-- seconds the card stays for a result (a beast already owned: a repeat goes sooner; a big one: longer)
local function revealHold(result)
    local definition = GameConfig.Pets[result.PetId]
    local tier = tierOf(definition and definition.Rarity)
    local base = if result.IsNew ~= true and tier.Dup then tier.Dup else tier.Reveal
    return base + PetRules.sizeInfo(result.Size).RevealHold
end

function HatchCeremony.afterBreak(result)
    return if typeof(result) == "table" then CRACK_TO_CARD + revealHold(result) + OUTRO else 0
end

-- ---------- the reel ----------
-- The cards, drawn from the egg's pool at its real odds (the player's own, with the Luck pass), the winner placed at WINNER.
local function reelItems(egg, winner)
    local pool = PassRules.luckyPool(egg.Pool, PassRules.luck(player))
    local total = 0
    for _, entry in pool do
        total += entry.HatchChance
    end
    local rng = Random.new()
    local items = {}
    for i = 1, CARDS do
        if i == WINNER then
            items[i] = winner
        else
            local roll = rng:NextNumber() * total
            local pick = pool[#pool].PetId
            for _, entry in pool do
                roll -= entry.HatchChance
                if roll <= 0 then
                    pick = entry.PetId
                    break
                end
            end
            items[i] = pick
        end
    end
    return items
end

-- ---------- one cinematic ----------
local function play(result)
    local definition = GameConfig.Pets[result.PetId]
    local egg = GameConfig.Eggs[result.EggId]
    if not (definition and egg) then
        return
    end
    local rarity = definition.Rarity
    local color = rarityColor(rarity)
    local size = PetRules.size(result.Size)
    local sizeInfo = PetRules.sizeInfo(size)
    local sizeBeat = SIZE_BEATS[size]
    local tier = tierOf(rarity)
    local rank = tier.Rank
    local calm = reduced()
    local cut = (if calm then 0.4 else 1) * (if LOW then 0.6 else 1)
    local winnerHidden = result.IsNew == true -- a new beast stays a silhouette on the reel until it's revealed
    for _, entry in egg.Pool do
        PetPreload.soon(entry.PetId)
    end

    local started = os.clock()
    player:SetAttribute("InHatchCinematic", true) -- (their own pets step out of the shot: PetCompanionController)
    local breakIn = if typeof(result.BreakAt) == "number" then math.max(1.2, result.BreakAt - Workspace:GetServerTimeNow()) else 3.6
    -- the held breath comes out of the reel's time, so the crack still lands when the server breaks the egg (everyone near hears it
    -- then, and the server takes the egg away 0.4 s after)
    local hold = math.min(tier.Hold, breakIn * 0.32)
    local crackIn = breakIn - 0.05
    local roll = crackIn - hold
    local connections, done = {}, false
    local landed, cracked, revealed = false, false, false
    local landedAt, crackedAt = nil, nil
    local fx = Instance.new("Folder")
    fx.Name = "HatchFx"
    fx.Parent = Workspace
    -- the build-up: the music steps back for the cinematic, and a shimmering swell rises to burst on the crack
    Sfx.duck(if rank >= 5 then 0.4 else 0.6, crackIn + 1.2)
    local swell, swellAt = nil, nil
    task.delay(math.max(0, crackIn - SWELL_PEAK), function()
        if not (done or cracked) then
            swell, swellAt = Sfx.play("HatchSwell"), os.clock()
        end
    end)
    local playerGui = player:WaitForChild("PlayerGui")

    -- the HUD steps aside (and comes back as it was)
    local hidden = {}
    for _, name in { "Hud", "HudTop", "TouchActions" } do -- (the touch buttons too: Strike and Dash stood over the bars on a phone)
        local gui = playerGui:FindFirstChild(name)
        if gui and gui.Enabled then
            gui.Enabled = false
            table.insert(hidden, gui)
        end
    end

    local gui = Instance.new("ScreenGui")
    gui.Name = "HatchCinema"
    gui.IgnoreGuiInset = true
    gui.ScreenInsets = Enum.ScreenInsets.None -- the bars run edge to edge: on a phone with a notch they stopped short of its sides
    gui.ResetOnSpawn = false
    gui.DisplayOrder = 30
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = playerGui

    -- letterbox bars
    local bars = {}
    for side = 0, 1 do
        local bar = Instance.new("Frame")
        bar.Name = "Bar"
        bar.BorderSizePixel = 0
        bar.BackgroundColor3 = Color3.new(0, 0, 0)
        bar.AnchorPoint = Vector2.new(0, side)
        bar.Position = UDim2.fromScale(0, side)
        bar.Size = UDim2.fromScale(1, 0)
        bar.ZIndex = 5
        bar.Parent = gui
        tween(bar, 0.4, { Size = UDim2.fromScale(1, 0.1) })
        table.insert(bars, bar)
    end

    -- the screen's edges, glowing the rarity's colour from the held breath on (Legendary up)
    local edges = {}
    if rank >= 5 then
        for side = 0, 1 do
            local edge = Instance.new("Frame")
            edge.Name = "Edge"
            edge.BorderSizePixel = 0
            edge.BackgroundColor3 = color
            edge.BackgroundTransparency = 1
            edge.AnchorPoint = Vector2.new(side, 0)
            edge.Position = UDim2.fromScale(side, 0)
            edge.Size = UDim2.fromScale(0.22, 1)
            edge.ZIndex = 4
            edge.Parent = gui
            local g = Instance.new("UIGradient")
            g.Transparency = if side == 0 then NumberSequence.new(0, 1) else NumberSequence.new(1, 0)
            g.Parent = edge
            table.insert(edges, edge)
        end
    end
    local edgeMost = if calm then 0.75 else 0.5 -- how far the edges' glow comes in (as transparency: lower is brighter)

    -- the world dims a little and loses some colour, so the egg and its light stand out
    local grade = Instance.new("ColorCorrectionEffect")
    grade.Name = "HatchCinemaGrade"
    grade.Parent = Lighting
    tween(grade, 0.5, { Saturation = -0.25, Brightness = -0.04, Contrast = 0.08 })

    -- the camera: round to the egg, a slow push in, a shake at the crack
    local camera = Workspace.CurrentCamera
    local saved = { Type = camera.CameraType, CFrame = camera.CFrame, FieldOfView = camera.FieldOfView }
    local model = result.Staged
    local eggBase = if model and model.PrimaryPart then model:GetPivot() else nil
    local eggScale = if model and model.PrimaryPart then model:GetScale() else 1
    local focus = if eggBase then eggBase.Position + Vector3.new(0, RISE * 0.7, 0) else nil
    local shakeUntil, shakeSize = 0, 0
    if focus then
        camera.CameraType = Enum.CameraType.Scriptable
    end
    -- the shot's side: looking back toward where the player's view was, but turned off the line through their own avatar (standing close
    -- to the altar, their head filled the frame, seen in Play, 2026-11-10; fading the avatar can't work, the camera's transparency
    -- controller resets it every frame): the first of these turns that keeps the shot's line 3.5 studs clear of their body and head
    local away
    if focus then
        local base = (saved.CFrame.Position - focus) * Vector3.new(1, 0, 1)
        base = if base.Magnitude > 0.1 then base.Unit else Vector3.new(0, 0, 1)
        away = base
        local character = player.Character
        local body = character and character:FindFirstChild("HumanoidRootPart")
        local head = character and character:FindFirstChild("Head")
        if body then
            local bestGap = -1
            for _, turn in { 0, 35, -35, 60, -60, 90, -90 } do
                local dir = CFrame.fromAxisAngle(Vector3.yAxis, math.rad(turn)):VectorToWorldSpace(base)
                local a = focus
                local ab = dir * 10 + Vector3.new(0, 2.6, 0) -- (out to the shot's widest point)
                local gap = math.huge
                for _, part in { body, head } do
                    if part then
                        local t = math.clamp((part.Position - a):Dot(ab) / ab:Dot(ab), 0, 1)
                        gap = math.min(gap, (a + ab * t - part.Position).Magnitude)
                    end
                end
                if gap > bestGap then
                    away, bestGap = dir, gap
                end
                if gap >= 3.5 then
                    break
                end
            end
        end
    end
    -- the camera circles a little round the egg while a Mythical or higher is held (turning the way that keeps it off the avatar)
    local orbitMost = if rank >= 6 then math.rad(if calm then 10 else 22) else 0
    local function shotAt(push, orbit)
        local distance = 10 - 2.6 * push
        local dir = if orbit ~= 0 then CFrame.fromAxisAngle(Vector3.yAxis, orbit):VectorToWorldSpace(away) else away
        return CFrame.lookAt(focus + dir * distance + Vector3.new(0, 2.6 - 0.6 * push, 0), focus)
    end

    -- the egg: rises, turns, shivers harder as the reel slows; glows its rarity's colour near the end
    local glow
    if model and model.PrimaryPart then
        glow = Instance.new("Highlight")
        glow.FillColor = Color3.fromRGB(255, 220, 140)
        glow.OutlineColor = Color3.fromRGB(255, 240, 200)
        glow.FillTransparency = 1
        glow.OutlineTransparency = 1
        glow.DepthMode = Enum.HighlightDepthMode.Occluded
        glow.Parent = model
        Sfx.after(roll * 0.6, "EggRumble", model.PrimaryPart)
    end

    -- the light inside the egg (Rare up): a core that follows the egg, with a glow, streaks leaking out, and from Epic shafts of
    -- light breaking through the shell, turning as it trembles (the core's own turn carries them: nothing per shaft each frame)
    local eggCore, eggLight, leak, shafts = nil, nil, nil, {}
    if rank >= 3 and focus then
        eggCore = holderAt(fx, focus, 30)
        eggLight = Instance.new("PointLight")
        eggLight.Color = color
        eggLight.Brightness = 0
        eggLight.Range = 8
        eggLight.Shadows = false
        eggLight.Parent = eggCore
        leak = emitter(eggCore, {
            Texture = TEXTURES.Streak, Speed = NumberRange.new(4, 8), SpreadAngle = Vector2.new(180, 180),
            Orientation = Enum.ParticleOrientation.VelocityParallel, Lifetime = NumberRange.new(0.22, 0.38), Drag = 3,
            Size = seq({ { 0, 0.9 }, { 1, 0.2 } }), Transparency = seq({ { 0, 0.2 }, { 1, 1 } }),
            Color = ColorSequence.new(color:Lerp(Color3.new(1, 1, 1), 0.5), color), Brightness = 2,
        })
        local count = math.floor((tier.Shafts or 0) * (if calm or LOW then 0.5 else 1))
        if count > 0 then
            local root = Instance.new("Attachment")
            root.Parent = eggCore
            local shaftFade = seq({ { 0, 0.15 }, { 0.7, 0.75 }, { 1, 1 } })
            for k = 1, count do
                local tip = Instance.new("Attachment")
                local tilt = math.rad(if k % 2 == 0 then 25 else -35) + math.rad((k * 37) % 30)
                tip.Position = CFrame.Angles(0, (k / count) * math.pi * 2, 0):VectorToWorldSpace(
                    CFrame.Angles(tilt, 0, 0):VectorToWorldSpace(Vector3.new(0, 0, -7)))
                tip.Parent = eggCore
                local shaft = Instance.new("Beam")
                shaft.Attachment0, shaft.Attachment1 = root, tip
                shaft.FaceCamera = true
                shaft.LightEmission = 1
                shaft.LightInfluence = 0
                shaft.Color = ColorSequence.new(color:Lerp(Color3.new(1, 1, 1), 0.3), color)
                shaft.Transparency = shaftFade
                shaft.Width0, shaft.Width1 = 0, 0
                shaft.Brightness = 0
                shaft.Segments = 1
                shaft.Parent = eggCore
                table.insert(shafts, shaft)
            end
        end
    end
    -- the pillar of light from the sky (Divine)
    local pillar
    if rank >= 8 and focus then
        local top = holderAt(fx, focus + Vector3.new(0, 140, 0), 30)
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Parent, a1.Parent = top, eggCore
        pillar = Instance.new("Beam")
        pillar.Attachment0, pillar.Attachment1 = a0, a1
        pillar.FaceCamera = true
        pillar.LightEmission = 1
        pillar.LightInfluence = 0
        pillar.Color = ColorSequence.new(Color3.new(1, 1, 1), color)
        pillar.Transparency = seq({ { 0, 1 }, { 0.25, 0.35 }, { 1, 0.1 } })
        pillar.Width0, pillar.Width1 = 0, 0
        pillar.Brightness = 0
        pillar.Segments = 1
        pillar.Parent = top
    end

    -- ---------- the reel ----------
    local reelWidth = 720
    local panel = UiKit.panel({ Name = "Reel", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 0.9, -14),
        Size = UDim2.fromOffset(reelWidth + 20, CARD_H + 20), Parent = gui })
    panel.ZIndex = 6
    applyHudScale(panel)
    local window = Instance.new("Frame")
    window.Name = "Window"
    window.BackgroundTransparency = 1
    window.ClipsDescendants = true
    window.Position = UDim2.fromOffset(10, 10)
    window.Size = UDim2.fromOffset(reelWidth, CARD_H)
    window.ZIndex = 7
    window.Parent = panel
    -- fades at both ends, over the cards
    for side = 0, 1 do
        local fade = Instance.new("Frame")
        fade.BorderSizePixel = 0
        fade.BackgroundColor3 = C.Panel
        fade.AnchorPoint = Vector2.new(side, 0)
        fade.Position = UDim2.fromScale(side, 0)
        fade.Size = UDim2.new(0, 110, 1, 0)
        fade.ZIndex = 20
        fade.Parent = window
        local g = Instance.new("UIGradient")
        g.Transparency = if side == 0 then NumberSequence.new(0, 1) else NumberSequence.new(1, 0)
        g.Parent = fade
    end
    -- the gold marker down the middle, and its pointers
    local marker = Instance.new("Frame")
    marker.Name = "Marker"
    marker.BorderSizePixel = 0
    marker.BackgroundColor3 = C.Highlight
    marker.AnchorPoint = Vector2.new(0.5, 0)
    marker.Position = UDim2.new(0.5, 0, 0, -4)
    marker.Size = UDim2.new(0, 3, 1, 8)
    marker.ZIndex = 21
    marker.Parent = window
    local pointers = {}
    for side = 0, 1 do
        local pointer = Instance.new("TextLabel")
        pointer.BackgroundTransparency = 1
        pointer.Text = if side == 0 then "▼" else "▲"
        pointer.TextColor3 = C.Highlight
        pointer.TextSize = 22
        pointer.FontFace = UiTheme.Fonts.Strong
        pointer.AnchorPoint = Vector2.new(0.5, side)
        pointer.Position = UDim2.new(0.5, 0, side, if side == 0 then -2 else 2)
        pointer.Size = UDim2.fromOffset(24, 22)
        pointer.ZIndex = 8
        pointer.Parent = panel
        table.insert(pointers, pointer)
    end

    local items = reelItems(egg, result.PetId)
    local portraits = {} -- [key] = { free portraits }
    local pull, pullAt = 0, 0 -- (the size reveal's camera pull-back: how far, and when; it eases back at the size's own pace)
    local function takePortrait(petId, silhouette)
        local key = petId .. (if silhouette then "#s" else "")
        local free = portraits[key]
        if free and #free > 0 then
            return table.remove(free), key
        end
        local frame = if silhouette then Portraits.silhouette(petId, CARD_W - 12) else Portraits.pet(petId, CARD_W - 12)
        if not silhouette then
            frame.BackgroundTransparency = 1 -- (a silhouette keeps its lit page: a black shape on the dark card couldn't be read)
        end
        return frame, key
    end
    local function givePortrait(frame, key)
        frame.Parent = nil
        portraits[key] = portraits[key] or {}
        table.insert(portraits[key], frame)
    end

    local slots = {}
    for s = 1, math.ceil(reelWidth / STEP) + 2 do
        local card = Instance.new("Frame")
        card.Name = "Card"
        card.BackgroundColor3 = C.Raised
        card.BorderSizePixel = 0
        card.Size = UDim2.fromOffset(CARD_W, CARD_H)
        card.ZIndex = 9
        card.Parent = window
        UiKit.corner(card)
        local edge = UiKit.stroke(card, C.EdgeDim, 0.1, 2)
        local band = Instance.new("Frame")
        band.Name = "Band"
        band.BorderSizePixel = 0
        band.AnchorPoint = Vector2.new(0, 1)
        band.Position = UDim2.fromScale(0, 1)
        band.Size = UDim2.new(1, 0, 0, 6)
        band.ZIndex = 11
        band.Parent = card
        local shine = Instance.new("UIGradient") -- the rarity's light rising from the card's foot
        shine.Rotation = -90
        shine.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.6, 1), NumberSequenceKeypoint.new(1, 1) })
        shine.Parent = card
        local scale = Instance.new("UIScale")
        scale.Parent = card
        slots[s] = { card = card, edge = edge, band = band, scale = scale, index = nil, portrait = nil, key = nil }
    end

    local function fill(slot, index)
        if slot.portrait then
            givePortrait(slot.portrait, slot.key)
            slot.portrait = nil
        end
        slot.index = index
        local petId = items[index]
        slot.card.Visible = petId ~= nil
        if not petId then
            return
        end
        local pet = GameConfig.Pets[petId]
        local rc = rarityColor(pet and pet.Rarity)
        local silhouette = not CodexState.found[petId] or (petId == result.PetId and winnerHidden)
        local frame, key = takePortrait(petId, silhouette)
        frame.AnchorPoint = Vector2.new(0.5, 0)
        frame.Position = UDim2.new(0.5, 0, 0, 6)
        frame.ZIndex = 10
        frame.Parent = slot.card
        slot.portrait, slot.key = frame, key
        slot.card.BackgroundColor3 = C.Raised:Lerp(rc, 0.18)
        slot.edge.Color = rc
        slot.band.BackgroundColor3 = rc
    end

    -- where the reel starts and stops: the third card under the marker at first; the winner at the end, a little off its middle
    local half = reelWidth / 2
    local startScroll = 2 * STEP + CARD_W / 2 - half
    local endScroll = (WINNER - 1) * STEP + CARD_W / 2 - half + (math.random() - 0.5) * CARD_W * 0.55
    local scroll = startScroll
    local lastCrossed, lastTick = nil, 0
    local function placeCards()
        local first = math.floor(scroll / STEP) + 1
        for s, slot in slots do
            local index = first + s - 1
            if slot.index ~= index then
                fill(slot, index)
            end
            slot.card.Position = UDim2.fromOffset((index - 1) * STEP - scroll, 0)
        end
        local crossed = math.floor((scroll + half) / STEP)
        if crossed ~= lastCrossed then
            lastCrossed = crossed
            local now = os.clock()
            if now - lastTick > 0.055 then -- (each card that passes the marker ticks; at full speed they blur into a rattle)
                lastTick = now
                Sfx.play("ReelTick", nil, 0.9 + 0.5 * math.clamp((now - started) / roll, 0, 1))
            end
        end
    end
    placeCards()

    -- the skip / continue layer: a tap anywhere moves on a beat
    local tapper = Instance.new("TextButton")
    tapper.Name = "Tap"
    tapper.BackgroundTransparency = 1
    tapper.Text = ""
    tapper.AutoButtonColor = false
    tapper.Size = UDim2.fromScale(1, 1)
    tapper.ZIndex = 50
    tapper.Parent = gui
    local hint = UiKit.label({ Name = "Hint", Font = "Strong", TextSize = 12, Text = if UiKit.usingTouch() then "TAP TO SKIP" else "CLICK TO SKIP", TextColor3 = C.Muted,
        AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.95), Size = UDim2.fromOffset(200, 16),
        TextXAlignment = Enum.TextXAlignment.Center, ZIndex = 6, Parent = gui })

    local reveal, finish, crack -- (defined below)
    local holdFor = hold -- the held breath as it plays (a tap during the reel shortens it)

    -- ---------- the reel lands ----------
    local function land(tapped)
        if landed or done then
            return
        end
        landed = true
        landedAt = os.clock()
        scroll = endScroll
        placeCards()
        marker.BackgroundColor3 = color
        for _, pointer in pointers do
            pointer.TextColor3 = color
        end
        -- the winning card leaps out of the reel; the rest dim
        for _, slot in slots do
            if slot.index == WINNER then
                slot.scale.Scale = 1.18
                tween(slot.scale, 0.3, { Scale = 1.08 }, Enum.EasingStyle.Back)
                slot.edge.Thickness = 3
            else
                tween(slot.card, 0.25, { BackgroundTransparency = 0.6 })
                if slot.portrait then
                    slot.portrait.ImageTransparency = 0.5
                end
            end
        end
        if tapped then
            holdFor = math.min(hold, if rank >= 5 then 0.3 else 0) -- impatient: a short breath for the grand ones, none below
        end
        if holdFor <= 0 then
            crack()
            return
        end
        -- the held breath: the egg's light grows (the shafts open, the edges glow, the pillar comes down)
        for _, shaft in shafts do
            tween(shaft, holdFor, { Width0 = 0.7, Width1 = 2.6, Brightness = 2 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
        end
        if pillar then
            tween(pillar, holdFor, { Width0 = 7, Width1 = 3, Brightness = 2.5 }, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
            Sfx.play("HatchPillar")
        end
        if rank >= 5 then
            Sfx.play("HatchCharge", nil, if rank >= 6 then 0.85 else 1)
        end
        if rank >= 6 then -- a different sequence: the reel's done its job, the bars close in, it's all the egg now
            task.delay(0.3, function() -- (after the winning card's leap)
                if not done then
                    tween(panel, 0.3, { Position = UDim2.new(0.5, 0, 1.4, 0) }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
                end
            end)
            for _, bar in bars do
                tween(bar, holdFor, { Size = UDim2.fromScale(1, if HudMetrics.class() == "Phone" then 0.11 else 0.14) })
            end
        end
        if rank >= 7 then -- a Secret and up: the world drains to darkness while the egg's light grows, and a breath is drawn in
            tween(grade, holdFor * 0.7, { Brightness = -0.55, Saturation = -1 })
            Sfx.after(math.max(0, holdFor - 0.75), "HatchHush")
        end
        task.delay(holdFor, crack)
    end

    -- ---------- the crack ----------
    function crack()
        if cracked or done then
            return
        end
        cracked = true
        crackedAt = os.clock()
        local at = if model and model.PrimaryPart then model:GetPivot().Position else (focus or Vector3.zero)
        if swell and os.clock() - swellAt < SWELL_PEAK - 0.15 then
            Sfx.fadeOut(swell, 0.15) -- skipped ahead: a swell that hasn't burst yet would burst late
        end
        Sfx.play("EggCrack", at, if rank >= 6 then 0.85 else 1)
        Sfx.play(tier.Sound)
        local made = burst(fx, at, tier, color, cut)
        if rank >= 6 then -- slow motion: the burst opens at a fifth of its speed and eases back to full
            for _, e in made do
                e.TimeScale = 0.2
                tween(e, 0.9, { TimeScale = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
            end
        end
        if model then
            for _, part in model:GetDescendants() do
                if part:IsA("BasePart") then
                    tween(part, 0.15, { Transparency = 1 })
                end
            end
        end
        if glow then
            glow:Destroy()
            glow = nil
        end
        -- the light inside lets go: the shafts flare and fade, the glow flares and dies
        if eggLight then
            eggLight.Brightness = 6
            eggLight.Range = 18
            tween(eggLight, 0.8, { Brightness = 0, Range = 8 })
        end
        if leak then
            leak.Rate = 0
        end
        for _, shaft in shafts do
            tween(shaft, 0.5, { Width0 = 0, Width1 = 3, Brightness = 0 })
        end
        if pillar then
            pillar.Width0, pillar.Width1 = 14, 8
            tween(pillar, 0.9, { Width0 = 0, Width1 = 0, Brightness = 0 })
        end
        for _, edge in edges do
            edge.BackgroundTransparency = if calm then 0.6 else 0.15
            tween(edge, 0.8, { BackgroundTransparency = 0.8 })
        end
        if rank >= 5 and not calm then
            local flash = Instance.new("Frame")
            flash.BorderSizePixel = 0
            flash.BackgroundColor3 = if rank >= 8 then Color3.new(1, 1, 1) else color:Lerp(Color3.new(1, 1, 1), 0.6)
            flash.BackgroundTransparency = if rank >= 8 then 0 else 0.15
            flash.Size = UDim2.fromScale(1, 1)
            flash.ZIndex = 40
            flash.Parent = gui
            if rank >= 8 then -- a white-out that turns the Divine's colour as it clears
                tween(flash, 0.35, { BackgroundColor3 = color:Lerp(Color3.new(1, 1, 1), 0.3), BackgroundTransparency = 0.3 })
                task.delay(0.35, function()
                    if flash.Parent then
                        tween(flash, 0.6, { BackgroundTransparency = 1 })
                    end
                end)
            else
                tween(flash, 0.45, { BackgroundTransparency = 1 })
            end
        end
        if tier.Shake and not calm then
            shakeUntil, shakeSize = os.clock() + tier.Shake, 0.35
        end
        grade.TintColor = color:Lerp(Color3.new(1, 1, 1), 0.55)
        grade.Brightness = 0.12
        tween(grade, 0.6, { TintColor = Color3.new(1, 1, 1), Brightness = -0.04, Saturation = -0.25 }) -- (back from a Secret's darkness too)
        task.delay(if rank >= 6 then CRACK_TO_CARD + 0.15 else CRACK_TO_CARD, function()
            if not done then
                reveal()
            end
        end)
    end

    -- ---------- the reveal card ----------
    local stopSpin
    function reveal()
        if revealed or done then
            return
        end
        revealed = true
        hint.Text = if UiKit.usingTouch() then "TAP TO CONTINUE" else "CLICK TO CONTINUE"
        tween(panel, 0.25, { Position = UDim2.new(0.5, 0, 1.4, 0) }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
        if rank >= 6 then
            for _, bar in bars do
                tween(bar, 0.4, { Size = UDim2.fromScale(1, 0.1) })
            end
        end
        -- (an object takes one UIScale: the HUD's goes on a holder, the card's pop on the card inside it)
        local cardHolder = Instance.new("Frame")
        cardHolder.Name = "RevealHolder"
        cardHolder.BackgroundTransparency = 1
        cardHolder.AnchorPoint = Vector2.new(0.5, 0.5)
        cardHolder.Position = UDim2.fromScale(0.5, 0.47)
        cardHolder.Size = UDim2.fromOffset(320, CARD_HEIGHT)
        cardHolder.ZIndex = 12
        cardHolder.Parent = gui
        applyHudScale(cardHolder)
        local card = UiKit.panel({ Name = "Reveal", Size = UDim2.fromOffset(320, CARD_HEIGHT), Parent = cardHolder })
        card.ZIndex = 12
        local cardEdge = card:FindFirstChildOfClass("UIStroke")
        if cardEdge and rank >= 2 then
            cardEdge.Color = color:Lerp(C.Edge, 0.35)
        end
        local pop = Instance.new("UIScale")
        pop.Scale = 0.55
        pop.Parent = card
        tween(pop, if rank >= 6 then 0.55 else 0.35, { Scale = 1 }, Enum.EasingStyle.Back)
        -- rays of the rarity's light turning slowly behind the beast (Uncommon up; more and wider up the ladder)
        local rays = Instance.new("Frame")
        rays.Name = "Rays"
        rays.BackgroundTransparency = 1
        rays.AnchorPoint = Vector2.new(0.5, 0.5)
        rays.Position = UDim2.new(0.5, 0, 0, 118)
        rays.Size = UDim2.fromOffset(300, 300)
        rays.ZIndex = 13
        rays.Parent = card
        local function rayFan(parent, count, width, rayColor)
            for k = 1, count do
                local ray = Instance.new("Frame")
                ray.BorderSizePixel = 0
                ray.BackgroundColor3 = rayColor
                ray.AnchorPoint = Vector2.new(0.5, 0.5)
                ray.Position = UDim2.fromScale(0.5, 0.5)
                ray.Size = UDim2.new(0, width, 1, 0)
                ray.Rotation = k * 180 / count
                ray.ZIndex = 13
                ray.Parent = parent
                local fade = Instance.new("UIGradient")
                fade.Rotation = 90
                fade.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.42, 0.45),
                    NumberSequenceKeypoint.new(0.5, 0.3), NumberSequenceKeypoint.new(0.58, 0.45), NumberSequenceKeypoint.new(1, 1) })
                fade.Parent = ray
            end
        end
        rayFan(rays, tier.CardRays, if rank >= 5 then 16 else 12, color)
        local counter -- a second, thinner fan turning the other way (Mythical up)
        if rank >= 6 then
            counter = rays:Clone()
            counter.Name = "Counter"
            counter:ClearAllChildren()
            counter.Size = UDim2.fromOffset(250, 250)
            counter.Parent = card
            rayFan(counter, 10, 6, color:Lerp(Color3.new(1, 1, 1), 0.5))
        end
        local bloom -- the beast's own glow (Divine)
        if rank >= 8 then
            bloom = Instance.new("ImageLabel")
            bloom.Name = "Bloom"
            bloom.BackgroundTransparency = 1
            bloom.Image = TEXTURES.Glow
            bloom.ImageColor3 = color
            bloom.ImageTransparency = 0.3
            bloom.AnchorPoint = Vector2.new(0.5, 0.5)
            bloom.Position = UDim2.new(0.5, 0, 0, 118)
            bloom.Size = UDim2.fromOffset(250, 250)
            bloom.ZIndex = 13
            bloom.Parent = card
        end
        local rayTurn = 18
        local spin = RunService.RenderStepped:Connect(function(dt)
            rays.Rotation += dt * rayTurn
            if counter then
                counter.Rotation -= dt * 26
            end
            if bloom then
                bloom.ImageTransparency = 0.3 + 0.15 * math.sin(os.clock() * 4)
            end
        end)
        table.insert(connections, spin)
        local portrait = Portraits.pet(result.PetId, 190)
        portrait.BackgroundTransparency = 1
        local frameEdge = portrait:FindFirstChildOfClass("UIStroke") -- (no box round the beast: it stands in its own light)
        if frameEdge then
            frameEdge:Destroy()
        end
        portrait.AnchorPoint = Vector2.new(0.5, 0.5)
        portrait.Position = UDim2.new(0.5, 0, 0, 118)
        portrait.ZIndex = 14
        portrait.Parent = card
        stopSpin = Portraits.spin(portrait)
        UiKit.label({ Name = "PetName", Font = "Title", TextSize = 24, Text = definition.DisplayName, TextColor3 = C.Text,
            TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 222),
            Size = UDim2.new(1, -20, 0, 28), TextScaled = true, ZIndex = 15, Parent = card })
        local tags = Instance.new("Frame")
        tags.BackgroundTransparency = 1
        tags.AnchorPoint = Vector2.new(0.5, 0)
        tags.Position = UDim2.new(0.5, 0, 0, 258)
        tags.Size = UDim2.new(1, -20, 0, 18)
        tags.ZIndex = 15
        tags.Parent = card
        UiKit.list(tags, { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center,
            VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 6) })
        local function tag(text, tagColor, order)
            local t = UiKit.tag(text, tagColor)
            t.LayoutOrder = order
            t.ZIndex = 16
            t.Parent = tags
            return t
        end
        tag(rarity, color, 1)
        tag(string.format("%.3g%% chance", tonumber(result.ChancePercent) or 0), C.AccentBright, 3)
        tag("+" .. tostring(PetRules.qiBonus(result.PetId, 1, size)) .. "% Qi", C.Sky, 4)
        UiKit.label({ Name = "Verdict", Font = "Strong", TextSize = 14, TextXAlignment = Enum.TextXAlignment.Center,
            Text = if result.IsNew then "NEW! Added to your Codex" else "You have this one: fuse it or sell it",
            TextColor3 = if result.IsNew then C.Highlight else C.Muted, AnchorPoint = Vector2.new(0.5, 0),
            Position = UDim2.new(0.5, 0, 0, 290), Size = UDim2.new(1, -20, 0, 20), ZIndex = 15, Parent = card })
        if rank >= 4 then
            UiFx.edgeLight(card, 4)
        end
        if rank >= 5 then
            task.delay(0.3, function()
                if card.Parent then
                    UiFx.sweep(card, color:Lerp(Color3.new(1, 1, 1), 0.4), 0.6)
                end
            end)
        end
        if tier.Banner then -- the grand rarities announce themselves, just over the card (on a phone, over the top bar)
            local scale = HudMetrics.scale()
            local view = HudMetrics.viewport()
            local cardTop = view.Y * 0.47 - CARD_HEIGHT / 2 * scale
            -- the odds line under it only where there's room above the card (a phone held sideways has none: it sat on the card's
            -- edge at 844 x 390; the card's own chance tag says it anyway)
            local withOdds = rank >= 6 and cardTop - 4 >= 78 * scale
            local bannerH = if withOdds then 78 else 60
            local holder = Instance.new("Frame")
            holder.Name = "Banner"
            holder.BackgroundTransparency = 1
            holder.AnchorPoint = Vector2.new(0.5, 1)
            holder.Position = UDim2.new(0.5, 0, 0, math.max(bannerH * scale + 2, cardTop - 4))
            holder.Size = UDim2.fromOffset(600, bannerH)
            holder.ZIndex = 30
            holder.Parent = gui
            applyHudScale(holder)
            local banner = UiKit.label({ Name = "Word", Font = "Title", TextSize = 46, Text = tier.Banner, TextColor3 = color,
                TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0),
                Size = UDim2.fromOffset(600, 56), ZIndex = 30, Parent = holder })
            local edge = Instance.new("UIStroke")
            edge.Color = Color3.fromRGB(14, 12, 34)
            edge.Thickness = 3
            edge.Parent = banner
            local grow = Instance.new("UIScale")
            grow.Scale = 2
            grow.Parent = banner
            tween(grow, if rank >= 6 then 0.55 else 0.4, { Scale = 1 }, Enum.EasingStyle.Back)
            if rank >= 7 then
                UiFx.typeIn(banner, 0.35)
            end
            if rank >= 8 then -- a band of white light running through the word
                local shine = Instance.new("UIGradient")
                shine.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)), ColorSequenceKeypoint.new(0.45, Color3.new(1, 1, 1)),
                    ColorSequenceKeypoint.new(0.5, color:Lerp(Color3.new(1, 1, 1), 0.85)), ColorSequenceKeypoint.new(0.55, Color3.new(1, 1, 1)),
                    ColorSequenceKeypoint.new(1, Color3.new(1, 1, 1)) })
                shine.Offset = Vector2.new(-1, 0)
                shine.Parent = banner
                tween(shine, 1.4, { Offset = Vector2.new(1, 0) }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
            end
            if withOdds then -- how rare it was, in plain words
                local odds = UiKit.label({ Name = "Odds", Font = "Strong", TextSize = 16, TextXAlignment = Enum.TextXAlignment.Center,
                    Text = string.format("Only a %.3g%% chance!", tonumber(result.ChancePercent) or 0), TextColor3 = C.AccentBright,
                    AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromScale(0.5, 1), Size = UDim2.fromOffset(400, 20),
                    ZIndex = 30, Parent = holder })
                UiKit.outline(odds, 1.5)
                odds.TextTransparency = 1
                task.delay(0.35, function()
                    if odds.Parent then
                        tween(odds, 0.3, { TextTransparency = 0 })
                    end
                end)
            end
        end

        -- ---------- the size reveal ----------
        local at = if model and model.PrimaryPart then model:GetPivot().Position else focus
        if size == "Small" then -- a little one: it settles smaller and bounces twice, with a pop and a ping
            tween(portrait, 0.4, { Size = UDim2.fromOffset(160, 160) })
            local smallTag = tag(size, sizeInfo.Color, 2)
            task.delay(0.25, function()
                if done then
                    return
                end
                UiFx.pop(smallTag, 1.5, 0.4)
                Sfx.play("SizeSmall")
                if at then
                    smallPuff(fx, at, sizeInfo.Color, cut)
                end
                for hop = 0, 1 do
                    local height = if hop == 0 then 16 else 8
                    task.delay(hop * 0.3, function()
                        if done then
                            return
                        end
                        tween(portrait, 0.13, { Position = UDim2.new(0.5, 0, 0, 118 - height) }, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
                        task.delay(0.13, function()
                            if not done then
                                tween(portrait, 0.15, { Position = UDim2.new(0.5, 0, 0, 118) }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
                            end
                        end)
                    end)
                end
            end)
        elseif size == "Large" or size == "Giant" then
            local giant = size == "Giant"
            local gold = sizeInfo.Color
            local wait = if giant then 0.75 else 0.3 -- the held beat before it shows how big it is
            local trembling = giant
            if giant then
                Sfx.play("EggRumble", nil, 1.15)
                local shake = RunService.RenderStepped:Connect(function()
                    if trembling then
                        local k = 2.5
                        portrait.Position = UDim2.new(0.5, (math.random() - 0.5) * k, 0, 118 + (math.random() - 0.5) * k)
                    end
                end)
                rayTurn = 108 -- the rays quicken
                table.insert(connections, shake)
            end
            task.delay(wait, function()
                if done then
                    return
                end
                trembling = false
                rayTurn = if giant then 30 else 18
                if giant then -- the beast grows to its full size, out past the card's edges (since 2026-11-17 a Giant is colossal in the world)
                    portrait.Position = UDim2.new(0.5, 0, 0, 118)
                    portrait.Size = UDim2.fromOffset(190, 190)
                    tween(portrait, 0.6, { Size = UDim2.fromOffset(330, 330), Position = UDim2.new(0.5, 0, 0, 108) }, Enum.EasingStyle.Back)
                else -- a heavy one drops onto the card and lands with a bounce
                    portrait.Position = UDim2.new(0.5, 0, 0, 118 - 70)
                    tween(portrait, 0.45, { Position = UDim2.new(0.5, 0, 0, 118), Size = UDim2.fromOffset(236, 236) }, Enum.EasingStyle.Bounce)
                end
                -- the rays and the card's edge turn gold
                for _, fan in { rays, counter } do
                    for _, ray in fan:GetChildren() do
                        if ray:IsA("Frame") then
                            tween(ray, 0.35, { BackgroundColor3 = gold:Lerp(color, if giant then 0.15 else 0.5) })
                        end
                    end
                end
                if cardEdge then
                    tween(cardEdge, 0.3, { Color = gold, Thickness = if giant then 4 else 3 })
                end
                -- the stamp, slammed onto the card's top corner (clear of a banner over the card)
                local stamp = UiKit.label({ Name = "SizeStamp", Font = "Title", TextSize = if giant then 40 else 28,
                    Text = if giant then "GIANT!" else "LARGE", TextColor3 = gold, TextXAlignment = Enum.TextXAlignment.Center,
                    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(1, if giant then -54 else -44, 0, if giant then 30 else 26),
                    Size = UDim2.fromOffset(if giant then 170 else 130, 50), Rotation = 12, ZIndex = 31, Parent = card })
                local stampEdge = Instance.new("UIStroke")
                stampEdge.Color = Color3.fromRGB(40, 22, 4)
                stampEdge.Thickness = if giant then 4 else 3
                stampEdge.Parent = stamp
                local slam = Instance.new("UIScale")
                slam.Scale = if giant then 2.6 else 1.8
                slam.Parent = stamp
                tween(slam, if giant then 0.32 else 0.25, { Scale = 1 }, Enum.EasingStyle.Back)
                tag(size, gold, 2)
                -- a ring of gold light running out from the beast across the card
                local ring = Instance.new("Frame")
                ring.Name = "SizeRing"
                ring.BackgroundTransparency = 1
                ring.AnchorPoint = Vector2.new(0.5, 0.5)
                ring.Position = UDim2.new(0.5, 0, 0, 118)
                ring.Size = UDim2.fromOffset(120, 120)
                ring.ZIndex = 13
                ring.Parent = card
                UiKit.corner(ring, 999)
                local ringEdge = UiKit.stroke(ring, gold, 0, if giant then 6 else 4)
                tween(ring, if giant then 0.8 else 0.5, { Size = UDim2.fromOffset(if giant then 720 else 380, if giant then 720 else 380) })
                tween(ringEdge, if giant then 0.7 else 0.5, { Transparency = 1, Thickness = 1 })
                Sfx.play(if giant then "SizeGiant" else "SizeLarge")
                Sfx.after(if giant then 0.05 else 0.3, "SizeLand") -- (a Large's thud on its landing bounce)
                -- in the world: gold light round the egg, a shake, and the camera pulls back to take it in
                if at then
                    sizeBurst(fx, at, gold, if giant then 1 else 0.45, cut)
                end
                pull, pullAt = sizeBeat.Pull * (if calm then 0.5 else 1), os.clock()
                if not calm then
                    shakeUntil, shakeSize = os.clock() + (if giant then 0.5 else 0.25), if giant then 0.45 else 0.2
                    if giant then
                        local flash = Instance.new("Frame")
                        flash.BorderSizePixel = 0
                        flash.BackgroundColor3 = gold:Lerp(Color3.new(1, 1, 1), 0.55)
                        flash.BackgroundTransparency = 0.35
                        flash.Size = UDim2.fromScale(1, 1)
                        flash.ZIndex = 11 -- (under the card: the card stays readable through it)
                        flash.Parent = gui
                        tween(flash, 0.5, { BackgroundTransparency = 1 })
                    end
                end
            end)
        end
        task.delay(revealHold(result), function()
            finish(false)
        end)
    end

    -- ---------- the end ----------
    function finish(instant)
        if done then
            return
        end
        done = true
        if active and active.token == started then
            active = nil
        end
        for _, connection in connections do
            connection:Disconnect()
        end
        if stopSpin then
            stopSpin()
        end
        if glow then
            glow:Destroy()
        end
        local seconds = if instant then 0 else OUTRO
        for _, bar in bars do
            tween(bar, math.max(seconds, 0.01), { Size = UDim2.fromScale(1, 0) })
        end
        tween(grade, math.max(seconds, 0.01), { Saturation = 0, Brightness = 0, Contrast = 0 })
        -- the reveal card folds away into a line of its rarity's light (the owner, 2026-11-16: "a collapse effect"); the rest goes
        local cardHolder = gui:FindFirstChild("RevealHolder")
        local revealCard = if seconds > 0 and cardHolder then cardHolder:FindFirstChild("Reveal") else nil
        for _, child in gui:GetChildren() do
            if child:IsA("GuiObject") and child.Name ~= "Bar" and not (revealCard and child == cardHolder) then
                child.Visible = false
            end
        end
        if revealCard then
            UiFx.collapse(revealCard, math.min(0.34, seconds), color)
        end
        local cameraTween = if focus and seconds > 0
            then tween(camera, seconds, { CFrame = saved.CFrame, FieldOfView = saved.FieldOfView })
            else nil
        local restored = false
        local function restore()
            if restored then
                return
            end
            restored = true
            if pendingRestore == restore then
                pendingRestore = nil
            end
            if focus then
                if cameraTween then
                    cameraTween:Cancel()
                end
                camera.CameraType = saved.Type
                camera.FieldOfView = saved.FieldOfView
            end
            for _, hud in hidden do
                hud.Enabled = true
            end
            player:SetAttribute("InHatchCinematic", nil)
            gui:Destroy()
            grade:Destroy()
            fx:Destroy()
            for _, list in portraits do
                for _, frame in list do
                    frame:Destroy()
                end
            end
            finished:Fire(result.BreakAt)
        end
        if seconds > 0 then
            pendingRestore = restore
            task.delay(seconds, restore)
        else
            restore() -- now, not deferred: a cinematic that starts next must see the camera and HUD as they were
        end
    end

    tapper.Activated:Connect(function()
        if os.clock() - started < 0.35 then
            return -- (the press that started the hatch)
        elseif not landed then
            land(true)
        elseif not cracked then
            crack() -- the held breath, cut short
        elseif revealed then
            finish(false)
        end
    end)

    -- ---------- each frame ----------
    local spinAngle, coreTurn, lastScale = 0, 0, 1
    local eggOutline, eggOutlineColor = nil, nil
    local eggSwell = sizeBeat.Swell
    table.insert(connections, RunService.RenderStepped:Connect(function(dt)
        local now = os.clock()
        local t = now - started
        local u = math.clamp(t / roll, 0, 1)
        local tell = math.clamp((u - 0.72) / 0.2, 0, 1)
        -- the held breath, 0 to 1 (it stays at 1 once the egg has broken)
        local h = if landedAt then (if holdFor > 0 then math.clamp((now - landedAt) / holdFor, 0, 1) else 1) else 0
        if not landed then
            -- fast, then a long slow settle (ease-out quint)
            scroll = startScroll + (endScroll - startScroll) * (1 - (1 - u) ^ 5)
            placeCards()
            -- the rarity first: the marker and the egg take the winner's colour as the reel slows
            marker.BackgroundColor3 = C.Highlight:Lerp(color, tell)
            for _, pointer in pointers do
                pointer.TextColor3 = C.Highlight:Lerp(color, tell)
            end
            if u >= 1 then
                land(false)
            end
        end
        -- the egg's own outline (EggGlow's, in the egg's colour, drawn over ours) takes the rarity's colour too, or the tell is hidden
        if not cracked and model and model.PrimaryPart then
            if not eggOutline then
                eggOutline = model.PrimaryPart:FindFirstChild("EggHighlight")
                eggOutlineColor = eggOutline and eggOutline.OutlineColor
            end
            if eggOutline then
                eggOutline.OutlineColor = eggOutlineColor:Lerp(color, tell)
                eggOutline.FillColor = eggOutlineColor:Lerp(color, tell)
            end
        end
        if glow then
            glow.FillColor = Color3.fromRGB(255, 220, 140):Lerp(color, tell)
            glow.OutlineColor = Color3.fromRGB(255, 240, 200):Lerp(color, tell)
            glow.FillTransparency = 1 - (0.6 * u * u + 0.25 * h)
            glow.OutlineTransparency = 1 - math.min(1, 0.85 * u + 0.15 * h)
        end
        -- the egg rising and turning, shivering harder near the end, and harder still while it's held; its turn slows to a stop as it
        -- is held, then it trembles in place
        if model and model.Parent and eggBase and not cracked then
            local lift = RISE * (1 - (1 - math.min(1, t / (roll * 0.6))) ^ 3) + HOLD_RISE * (1 - (1 - h) ^ 2)
            if size == "Small" then -- a little one hops as it glows
                lift += 0.35 * math.abs(math.sin(t * 11)) * tell * (1 - h)
            end
            local amp = (if u > 0.55 then 0.07 * (u - 0.55) / 0.45 else 0) + 0.11 * h * h
            local shiver = amp * math.sin(t * (58 + 24 * h))
            local turnRate = (1.2 + 6 * u * u) * (1 - h) + 0.2
            spinAngle += dt * turnRate
            if eggSwell > 0 then -- a big one swells as it glows, and throbs while it's held (straining)
                local s = 1 + eggSwell * tell + eggSwell * 0.35 * h * (0.5 + 0.5 * math.sin(t * 16))
                if math.abs(s - lastScale) > 0.004 then
                    lastScale = s
                    model:ScaleTo(eggScale * s)
                end
            end
            model:PivotTo(eggBase * CFrame.new(shiver, lift, amp * 0.6 * math.cos(t * 47)) * CFrame.Angles(0, spinAngle, 0))
        end
        -- the light inside it
        if eggCore and not cracked then
            coreTurn += dt * (0.5 + 2.5 * h)
            local at = if model and model.Parent and model.PrimaryPart then model:GetPivot().Position else focus
            eggCore.CFrame = CFrame.new(at) * CFrame.Angles(0, coreTurn, 0)
            local light = 0.6 * tell + 1.8 * h
            eggLight.Brightness = light * (0.85 + 0.15 * math.sin(t * 23))
            eggLight.Range = 8 + 6 * h
            leak.Rate = if light > 0.05 then (6 + 30 * h) * cut else 0
        end
        -- the screen's edges, coming in with the held breath
        if not cracked then
            for _, edge in edges do
                edge.BackgroundTransparency = 1 - (1 - edgeMost) * h
            end
        end
        -- the camera
        if focus then
            local intro = math.clamp(t / INTRO, 0, 1)
            intro = 1 - (1 - intro) ^ 3
            local held = if rank >= 5 then 0.45 * h else 0 -- leaning in while it's held
            local orbit = orbitMost * (1 - (1 - h) ^ 2)
            local shot = saved.CFrame:Lerp(shotAt(math.clamp(t / (roll + hold + 2), 0, 1) + held, orbit), intro)
            local back = pull * math.exp(-(now - pullAt) * sizeBeat.Ease)
            if back > 0.001 then -- the size reveal's pull-back: away from the egg and a little up, easing back in
                shot *= CFrame.new(0, 0.8 * back, 3.2 * back)
            end
            if now < shakeUntil then
                local k = (shakeUntil - now) / 0.5 * shakeSize
                shot *= CFrame.new((math.random() - 0.5) * k, (math.random() - 0.5) * k, 0)
            end
            camera.CFrame = shot
            -- the lens: narrows while a grand one is held, punches in at the crack (harder from Rare), widens with a big beast
            local fov = saved.FieldOfView
            if not cracked then
                fov -= (if rank >= 5 then 6 else 0) * h
            else
                local punch = (if rank >= 3 then 8 else 4) + (if rank >= 5 then 6 else 0)
                fov -= punch * math.exp(-(now - crackedAt) * 5)
            end
            camera.FieldOfView = fov + 8 * back
        end
    end))

    active = { token = started, finish = finish }
end

-- Plays the hatch cinematic for a successful hatch result (a new one ends any still showing).
local function endShowing()
    if active then
        active.finish(true)
    end
    if pendingRestore then
        pendingRestore()
    end
end

-- True while a hatch cinematic plays, or is about to (its staged egg may still be on the way): other notices
-- (a title earned by the new pet) wait until it ends, so they never give the result away (2-player test, 2026-11-16).
local requestedAt = nil
function HatchCeremony.isPlaying()
    return active ~= nil or (requestedAt ~= nil and os.clock() - requestedAt < 3)
end

function HatchCeremony.play(result)
    requestedAt = os.clock()
    endShowing()
    -- The staged egg rides in the result, but with streaming on it can land a moment after the remote that names it: on real hatches
    -- Staged arrived nil and the cinematic ran without its camera or its egg (seen in Play, 2026-11-10). Wait for it at the altar, briefly
    -- (the reel times itself to BreakAt, so the wait costs nothing).
    if result.Staged == nil and result.PetId then
        task.spawn(function()
            local islands = Workspace:FindFirstChild("FloatingIslands")
            local island = islands and islands:FindFirstChild(GameConfig.HatchingAltar.Island)
            local altar = island and island:FindFirstChild("HatchingAltar")
            result.Staged = altar and altar:WaitForChild("HatchingEgg", 1.5)
            endShowing()
            play(result)
        end)
        return
    end
    play(result)
end

return HatchCeremony

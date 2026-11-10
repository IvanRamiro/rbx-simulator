-- The hatch cinematic, as the hatcher sees it (the owner, November 10, 2026: "a cinematic egg-hatching animation" with "a gacha-style
-- rolling animation"; plan approved: a horizontal reel, about 5 s). The server has already chosen the beast (PetService) and laid
-- the egg in the altar's cradle (a model everyone sees); this only shows it, in five beats:
--   1. letterbox bars close in, the HUD steps aside, the camera glides round to the egg;
--   2. the egg rises and shivers while a reel of the egg's beasts races past a gold marker, drawn at the egg's real odds (the
--      player's own lucky odds with the Luck pass: PassRules.luckyPool, as the server rolled), undiscovered beasts as silhouettes;
--   3. as it slows, the marker and the egg glow the winner's rarity colour: the rarity first, the beast second;
--   4. it lands as the egg cracks (at the server's BreakAt), in a burst that grows with rarity: a flash and sparks; from Rare a
--      shockwave and rays of light; from Legendary a screen flash, a camera shake and a banner; for a Secret, a beat of darkness first;
--   5. a reveal card: the beast turning, its name, rarity, chance, and NEW or Duplicate.
-- A tap skips to the next beat. The player's Reduced Effects setting drops the shake, the flashes and most particles.
--   HatchCeremony.play(result)   result: the server's EggHatchResultEvent (EggId, PetId, ChancePercent, IsNew, Staged, BreakAt)
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Client = script.Parent.Parent
local UI = Client:WaitForChild("UI")
local Portraits = require(UI:WaitForChild("Portraits"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local applyHudScale = require(UI:WaitForChild("HudScale"))
local Sfx = require(Client:WaitForChild("Audio"):WaitForChild("Sfx"))
local CodexState = require(script.Parent:WaitForChild("CodexState"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local HatchCeremony = {}

-- ---------- tuning ----------
local INTRO = 0.6            -- seconds the camera takes to glide in
local CARD_W, CARD_H, GAP = 96, 116, 8
local STEP = CARD_W + GAP
local CARDS = 34             -- the reel's length
local WINNER = 29            -- where the winner sits on it
local RISE = 1.6             -- studs the egg lifts from the cradle
local REVEAL_HOLD = 2.2      -- seconds the reveal card stays (with its fade, done before the altar window comes back at 2.8)
local OUTRO = 0.45
local TEXTURES = {           -- (GuardianFx's and the character aura's)
    Glow = "rbxassetid://135169457468310",
    Streak = "rbxassetid://115312010132075",
    Ring = "rbxassetid://81927825399672",
    Spark = "rbxassetid://112814194154292",
}
-- each rarity's burst: rays and sparks out of the egg, a shockwave, the screen flash, the camera shake, the banner
local TIERS = {
    Common = { Sparks = 18, Rays = 0 },
    Uncommon = { Sparks = 24, Rays = 0 },
    Rare = { Sparks = 30, Rays = 10, Ring = true },
    Epic = { Sparks = 36, Rays = 14, Ring = true },
    Legendary = { Sparks = 44, Rays = 18, Ring = true, Flash = true, Shake = 0.35, Banner = "LEGENDARY!" },
    Mythical = { Sparks = 50, Rays = 22, Ring = true, Flash = true, Shake = 0.45, Banner = "MYTHICAL!" },
    Secret = { Sparks = 56, Rays = 26, Ring = true, Flash = true, Shake = 0.55, Banner = "SECRET!", Dark = true },
}

local active = nil -- the playing cinematic: { finish = function(instant) }

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

-- ---------- the burst at the egg (world particles: they don't render inside a ViewportFrame) ----------
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

local function burst(at, rarity, cut)
    local tier = TIERS[rarity] or TIERS.Common
    local color = rarityColor(rarity)
    local core = color:Lerp(Color3.new(1, 1, 1), 0.65)
    local holder = Instance.new("Part")
    holder.Anchored, holder.CanCollide, holder.CanQuery, holder.CanTouch, holder.CastShadow = true, false, false, false, false
    holder.Transparency = 1
    holder.Size = Vector3.new(0.4, 0.4, 0.4)
    holder.CFrame = CFrame.new(at)
    holder.Parent = Workspace
    task.delay(3, function()
        holder:Destroy()
    end)
    -- the flash of the egg breaking
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.5),
        Size = seq({ { 0, 3 }, { 1, 13 } }), Transparency = seq({ { 0, 0.25 }, { 1, 1 } }),
        Color = ColorSequence.new(Color3.new(1, 1, 1), color), Brightness = 2.2,
    }):Emit(1)
    -- sparks thrown up and out, falling back
    emitter(holder, {
        Texture = TEXTURES.Spark, Speed = NumberRange.new(6, 13), SpreadAngle = Vector2.new(60, 60), EmissionDirection = Enum.NormalId.Top,
        Lifetime = NumberRange.new(0.8, 1.4), Acceleration = Vector3.new(0, -12, 0), Drag = 1.2,
        Size = seq({ { 0, 0.55 }, { 1, 0 } }), Color = ColorSequence.new(core, color), Brightness = 2.4,
    }):Emit(math.floor(tier.Sparks * cut))
    -- rays of light bursting out all round
    if tier.Rays > 0 then
        emitter(holder, {
            Texture = TEXTURES.Streak, Speed = NumberRange.new(26, 34), SpreadAngle = Vector2.new(180, 180),
            Orientation = Enum.ParticleOrientation.VelocityParallel, Lifetime = NumberRange.new(0.3, 0.45), Drag = 4,
            Size = seq({ { 0, 3.2 }, { 1, 0.6 } }), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }),
            Color = ColorSequence.new(core, color), Brightness = 2.6,
        }):Emit(math.floor(tier.Rays * cut))
    end
    -- a shockwave flat across the ground (a particle rising almost not at all, laid flat by VelocityPerpendicular)
    if tier.Ring then
        local ground = holder:Clone()
        ground.CFrame = CFrame.new(at - Vector3.new(0, RISE + 0.4, 0))
        ground.Parent = Workspace
        task.delay(2, function()
            ground:Destroy()
        end)
        emitter(ground, {
            Texture = TEXTURES.Ring, Speed = NumberRange.new(0.01), EmissionDirection = Enum.NormalId.Top,
            Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Lifetime = NumberRange.new(0.7),
            Size = seq({ { 0, 1 }, { 1, 16 } }), Transparency = seq({ { 0, 0.05 }, { 0.6, 0.4 }, { 1, 1 } }),
            Color = ColorSequence.new(core, color), Brightness = 2.4,
        }):Emit(1)
    end
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
    local tier = TIERS[rarity] or TIERS.Common
    local calm = reduced()
    local cut = if calm then 0.4 else 1
    local winnerHidden = result.IsNew == true -- a new beast stays a silhouette on the reel until it's revealed
    for _, entry in egg.Pool do
        PetPreload.soon(entry.PetId)
    end

    local started = os.clock()
    local breakIn = if typeof(result.BreakAt) == "number" then math.max(1.2, result.BreakAt - Workspace:GetServerTimeNow()) else 3.6
    local roll = breakIn - 0.05
    local connections, done = {}, false
    local landed, revealed = false, false
    local playerGui = player:WaitForChild("PlayerGui")

    -- the HUD steps aside (and comes back as it was)
    local hidden = {}
    for _, name in { "Hud", "HudTop" } do
        local gui = playerGui:FindFirstChild(name)
        if gui and gui.Enabled then
            gui.Enabled = false
            table.insert(hidden, gui)
        end
    end

    local gui = Instance.new("ScreenGui")
    gui.Name = "HatchCinema"
    gui.IgnoreGuiInset = true
    gui.ResetOnSpawn = false
    gui.DisplayOrder = 30
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = playerGui

    -- letterbox bars
    local bars = {}
    for side = 0, 1 do
        local bar = Instance.new("Frame")
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
    local focus = if eggBase then eggBase.Position + Vector3.new(0, RISE * 0.7, 0) else nil
    local shakeUntil, shakeSize = 0, 0
    if focus then
        camera.CameraType = Enum.CameraType.Scriptable
    end
    local function shotAt(push)
        local away = (saved.CFrame.Position - focus) * Vector3.new(1, 0, 1)
        away = if away.Magnitude > 0.1 then away.Unit else Vector3.new(0, 0, 1)
        local distance = 10 - 2.6 * push
        return CFrame.lookAt(focus + away * distance + Vector3.new(0, 2.6 - 0.6 * push, 0), focus)
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
                Sfx.play("Click", nil, 0.9 + 0.5 * math.clamp((now - started) / roll, 0, 1))
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
    local hint = UiKit.label({ Name = "Hint", Font = "Strong", TextSize = 12, Text = "TAP TO SKIP", TextColor3 = C.Muted,
        AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.95), Size = UDim2.fromOffset(200, 16),
        TextXAlignment = Enum.TextXAlignment.Center, ZIndex = 6, Parent = gui })

    local reveal, finish -- (defined below)

    -- ---------- the crack ----------
    local function land()
        if landed or done then
            return
        end
        landed = true
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
        local at = if model and model.PrimaryPart then model:GetPivot().Position else (focus or Vector3.zero)
        local function crack()
            if done then
                return
            end
            Sfx.play("EggCrack", at)
            Sfx.play(if tier.Flash then "RareReveal" else "HatchReveal")
            burst(at, rarity, cut)
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
            if tier.Flash and not calm then
                local flash = Instance.new("Frame")
                flash.BorderSizePixel = 0
                flash.BackgroundColor3 = color:Lerp(Color3.new(1, 1, 1), 0.6)
                flash.BackgroundTransparency = 0.15
                flash.Size = UDim2.fromScale(1, 1)
                flash.ZIndex = 40
                flash.Parent = gui
                tween(flash, 0.45, { BackgroundTransparency = 1 })
            end
            if tier.Shake and not calm then
                shakeUntil, shakeSize = os.clock() + tier.Shake, 0.35
            end
            if focus then -- the lens punches in and settles
                camera.FieldOfView = saved.FieldOfView - 8
                tween(camera, 0.5, { FieldOfView = saved.FieldOfView }, Enum.EasingStyle.Back)
            end
            grade.TintColor = color:Lerp(Color3.new(1, 1, 1), 0.55)
            grade.Brightness = 0.12
            tween(grade, 0.6, { TintColor = Color3.new(1, 1, 1), Brightness = -0.04, Saturation = -0.25 }) -- (back from a Secret's dark beat too)
            task.delay(0.35, function()
                if not done then
                    reveal()
                end
            end)
        end
        if tier.Dark and not calm then -- a Secret: the world goes dark a beat before it breaks
            tween(grade, 0.2, { Brightness = -0.55, Saturation = -1 })
            task.delay(0.35, crack)
        else
            crack()
        end
    end

    -- ---------- the reveal card ----------
    local stopSpin
    function reveal()
        if revealed or done then
            return
        end
        revealed = true
        hint.Text = "TAP TO CONTINUE"
        tween(panel, 0.25, { Position = UDim2.new(0.5, 0, 1.4, 0) }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
        local card = UiKit.panel({ Name = "Reveal", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.47),
            Size = UDim2.fromOffset(320, 330), Parent = gui })
        card.ZIndex = 12
        applyHudScale(card)
        local pop = Instance.new("UIScale")
        pop.Scale = 0.55
        pop.Parent = card
        tween(pop, 0.35, { Scale = 1 }, Enum.EasingStyle.Back)
        -- rays of the rarity's light turning slowly behind the beast
        local rays = Instance.new("Frame")
        rays.Name = "Rays"
        rays.BackgroundTransparency = 1
        rays.AnchorPoint = Vector2.new(0.5, 0.5)
        rays.Position = UDim2.new(0.5, 0, 0, 118)
        rays.Size = UDim2.fromOffset(300, 300)
        rays.ZIndex = 13
        rays.Parent = card
        local rayCount = if tier.Flash then 16 else 10
        for k = 1, rayCount do
            local ray = Instance.new("Frame")
            ray.BorderSizePixel = 0
            ray.BackgroundColor3 = color
            ray.AnchorPoint = Vector2.new(0.5, 0.5)
            ray.Position = UDim2.fromScale(0.5, 0.5)
            ray.Size = UDim2.new(0, if tier.Flash then 16 else 12, 1, 0)
            ray.Rotation = k * 180 / rayCount
            ray.ZIndex = 13
            ray.Parent = rays
            local fade = Instance.new("UIGradient")
            fade.Rotation = 90
            fade.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.42, 0.45),
                NumberSequenceKeypoint.new(0.5, 0.3), NumberSequenceKeypoint.new(0.58, 0.45), NumberSequenceKeypoint.new(1, 1) })
            fade.Parent = ray
        end
        local spin = RunService.RenderStepped:Connect(function(dt)
            rays.Rotation += dt * 18
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
        end
        tag(rarity, color, 1)
        tag(string.format("%.3g%% chance", tonumber(result.ChancePercent) or 0), C.AccentBright, 2)
        tag("+" .. tostring(definition.QiBonus) .. "% Qi", C.Sky, 3)
        UiKit.label({ Name = "Verdict", Font = "Strong", TextSize = 14, TextXAlignment = Enum.TextXAlignment.Center,
            Text = if result.IsNew then "NEW! Added to your Codex" else "Duplicate: fuse it or sell it",
            TextColor3 = if result.IsNew then C.Highlight else C.Muted, AnchorPoint = Vector2.new(0.5, 0),
            Position = UDim2.new(0.5, 0, 0, 290), Size = UDim2.new(1, -20, 0, 20), ZIndex = 15, Parent = card })
        if tier.Banner then -- the grand rarities announce themselves
            local banner = UiKit.label({ Name = "Banner", Font = "Title", TextSize = 46, Text = tier.Banner, TextColor3 = color,
                TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.16),
                Size = UDim2.fromOffset(600, 60), ZIndex = 30, Parent = gui })
            local edge = Instance.new("UIStroke")
            edge.Color = Color3.fromRGB(14, 12, 34)
            edge.Thickness = 3
            edge.Parent = banner
            local grow = Instance.new("UIScale")
            grow.Scale = 2
            grow.Parent = banner
            applyHudScale(banner)
            tween(grow, 0.4, { Scale = 1 }, Enum.EasingStyle.Back)
        end
        task.delay(REVEAL_HOLD, function()
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
        for _, child in gui:GetChildren() do
            if child:IsA("GuiObject") and child.Name ~= "" and not table.find(bars, child) then
                child.Visible = false
            end
        end
        if focus then
            if seconds > 0 then
                tween(camera, seconds, { CFrame = saved.CFrame, FieldOfView = saved.FieldOfView })
            end
            task.delay(seconds, function()
                camera.CameraType = saved.Type
                camera.FieldOfView = saved.FieldOfView
            end)
        end
        task.delay(seconds, function()
            for _, hud in hidden do
                hud.Enabled = true
            end
            gui:Destroy()
            grade:Destroy()
            for _, list in portraits do
                for _, frame in list do
                    frame:Destroy()
                end
            end
        end)
    end

    tapper.Activated:Connect(function()
        if os.clock() - started < 0.35 then
            return -- (the press that started the hatch)
        elseif not landed then
            land()
        elseif revealed then
            finish(false)
        end
    end)

    -- ---------- each frame ----------
    table.insert(connections, RunService.RenderStepped:Connect(function()
        local t = os.clock() - started
        local u = math.clamp(t / roll, 0, 1)
        if not landed then
            -- fast, then a long slow settle (ease-out quint)
            scroll = startScroll + (endScroll - startScroll) * (1 - (1 - u) ^ 5)
            placeCards()
            -- the rarity first: the marker and the egg take the winner's colour as the reel slows
            local tell = math.clamp((u - 0.72) / 0.2, 0, 1)
            marker.BackgroundColor3 = C.Highlight:Lerp(color, tell)
            for _, pointer in pointers do
                pointer.TextColor3 = C.Highlight:Lerp(color, tell)
            end
            if glow then
                glow.FillColor = Color3.fromRGB(255, 220, 140):Lerp(color, tell)
                glow.OutlineColor = Color3.fromRGB(255, 240, 200):Lerp(color, tell)
                glow.FillTransparency = 1 - 0.6 * u * u
                glow.OutlineTransparency = 1 - 0.85 * u
            end
            if u >= 1 then
                land()
            end
        end
        -- the egg rising and turning, shivering harder near the end
        if model and model.Parent and eggBase and not landed then
            local lift = RISE * (1 - (1 - math.min(1, t / (roll * 0.6))) ^ 3)
            local shiver = if u > 0.55 then 0.07 * math.sin(t * 58) * (u - 0.55) / 0.45 else 0
            model:PivotTo(eggBase * CFrame.new(shiver, lift, 0) * CFrame.Angles(0, t * (1.2 + 6 * u * u), 0))
        end
        -- the camera
        if focus then
            local intro = math.clamp(t / INTRO, 0, 1)
            intro = 1 - (1 - intro) ^ 3
            local shot = saved.CFrame:Lerp(shotAt(math.clamp(t / (roll + 2), 0, 1)), intro)
            local now = os.clock()
            if now < shakeUntil then
                local k = (shakeUntil - now) / 0.5 * shakeSize
                shot *= CFrame.new((math.random() - 0.5) * k, (math.random() - 0.5) * k, 0)
            end
            camera.CFrame = shot
        end
    end))

    active = { token = started, finish = finish }
end

-- Plays the hatch cinematic for a successful hatch result (a new one ends any still showing).
function HatchCeremony.play(result)
    if active then
        active.finish(true)
    end
    play(result)
end

return HatchCeremony

-- Brings the egg auras to life. The auras themselves are built in the Workspace (particle
-- emitters, trails, beams, billboards, glowing image planes and lights; see
-- src/worldbuild/EggAuraVFX.lua) and tagged "EggAura"; this script only moves and times them from
-- their attributes, so an aura tuned by hand in Studio keeps working:
--   * attachments with an Orbit attribute circle the egg (their trails draw arcs of energy, their
--     beams sweep, their crystals drift);
--   * parts with a Spin attribute turn (formations and rings), their tilt precessing by Wobble
--     degrees every WobblePeriod seconds if set, and their images swell toward SwellScale as
--     the aura breathes and on the hatch burst, and draw in by GatherScale while a hatch gathers;
--   * parts with a Ripple attribute send rings running outward on the hatch;
--   * image labels with a Sway attribute rock to and fro;
--   * on a hatch, the aura gathers for Gather seconds (everything speeds up and draws in, emitters
--     with GatherRate pull energy in, the egg glows in the aura's Tint), then bursts: emitters
--     with HatchEmit fire, the rings fling outward and the egg flashes.
-- The aura breathes (model attributes Breath, a fraction, and BreathPeriod, in
-- seconds): its speed, glow and ring size swell and ease back in a slow rhythm. BreathShape
-- "Heartbeat" makes it beat instead: a double thump, then a rest.
-- Auras run at full rate near the camera, half rate further out, and switch off beyond that.
local CollectionService = game:GetService("CollectionService")
local ContentProvider = game:GetService("ContentProvider")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local EggAura = {}

local TAG = "EggAura"
local NEAR = 90   -- full emission rates within this distance of the camera
local FAR = 200   -- half rates out to here; switched off beyond
local TAU = 2 * math.pi
local RIPPLE_GAP = 0.22 -- seconds between ripples fired together

local auras = {} -- [model] = state, or false while the model has not streamed in complete

-- An instance with its attributes, kept current when they are changed (by hand, in Play).
local function watched(instance)
    local entry = { Instance = instance, A = instance:GetAttributes() }
    instance.AttributeChanged:Connect(function()
        entry.A = instance:GetAttributes()
    end)
    return entry
end

local function labelsOf(instance)
    local labels = {}
    for _, d in instance:GetDescendants() do
        if d:IsA("ImageLabel") then
            table.insert(labels, { Label = d, Size = d.Size })
        end
    end
    return labels
end

local function index(model)
    local root = model.PrimaryPart or model:FindFirstChild("Root")
    if not root then
        return false
    end
    local state = {
        model = model, root = root, eggId = model:GetAttribute("EggId"), tint = model:GetAttribute("Tint"),
        movers = {}, spinners = {}, ripples = {}, waves = {}, sways = {}, emitters = {}, trails = {}, lights = {}, guis = {},
        speed = 1, glow = 1, swell = 0, level = 2,
        gather = model:GetAttribute("Gather") or 1.2,
        breathPhase = math.random() * TAU,
    }
    state.modelAttrs = watched(model)
    for _, d in model:GetDescendants() do
        if d:IsA("Attachment") and d:GetAttribute("Orbit") then
            local m = watched(d)
            m.Angle = m.A.Phase or 0
            table.insert(state.movers, m)
        elseif d:IsA("BasePart") and d:GetAttribute("Ripple") then
            local r = watched(d)
            r.Templates = labelsOf(d)
            table.insert(state.ripples, r)
        elseif d:IsA("BasePart") and d:GetAttribute("Spin") then
            local s = watched(d)
            s.Base, s.Angle, s.Scale, s.Labels = d.CFrame, 0, 1, labelsOf(d)
            table.insert(state.spinners, s)
        elseif d:IsA("ImageLabel") and d:GetAttribute("Sway") then
            table.insert(state.sways, watched(d))
        elseif d:IsA("ParticleEmitter") then
            table.insert(state.emitters, { Emitter = d, Rate = d.Rate, Enabled = d.Enabled })
        elseif d:IsA("Trail") or d:IsA("Beam") then
            table.insert(state.trails, d)
        elseif d:IsA("Light") then
            table.insert(state.lights, { Light = d, Brightness = d.Brightness })
        elseif d:IsA("SurfaceGui") or d:IsA("BillboardGui") then
            table.insert(state.guis, { Gui = d, Brightness = d.Brightness })
        end
    end
    task.spawn(function()
        pcall(ContentProvider.PreloadAsync, ContentProvider, { model }) -- textures ready before it is seen
    end)
    return state
end

local function rateFactor(state)
    return state.level == 1 and 0.5 or 1
end

-- level: 2 full, 1 half rates, 0 off.
local function setLevel(state, level)
    if state.level == level then
        return
    end
    state.level = level
    local on = level > 0
    for _, e in state.emitters do
        e.Emitter.Enabled = on and e.Enabled
        if not state.hatching then
            e.Emitter.Rate = e.Rate * rateFactor(state)
        end
    end
    for _, t in state.trails do
        t.Enabled = on
    end
    for _, l in state.lights do
        l.Light.Enabled = on
    end
    for _, g in state.guis do
        g.Gui.Enabled = on
    end
end

-- Where an orbiting attachment is at `angle` degrees round its orbit (relative to the Root).
local function moverPosition(a, angle, now)
    local radius = a.Radius or 2.5
    local tilt = a.Tilt or Vector3.zero
    local r = math.rad(angle)
    local p = CFrame.Angles(math.rad(tilt.X), 0, math.rad(tilt.Z)):VectorToWorldSpace(Vector3.new(math.cos(r) * radius, 0, math.sin(r) * radius))
    local bob = (a.Bob or 0) * math.sin(now * TAU / (a.BobPeriod or 3) + math.rad(a.Phase or 0))
    return p + Vector3.new(0, (a.Height or 1.75) + bob, 0)
end

-- How big a spinning plane's image is: swell 0 is at rest, 1 fully swollen, -1 drawn in to gather.
local function swellScale(a, swell)
    if swell >= 0 then
        return 1 + swell * ((a.SwellScale or 1) - 1)
    end
    return 1 - swell * ((a.GatherScale or 1) - 1)
end

local function smooth(k)
    k = math.clamp(k, 0, 1)
    return k * k * (3 - 2 * k)
end

-- Eases speed, glow and swell toward the targets over `rise` seconds, then back to rest (1, 1, 0)
-- over `fall`.
local REST = { 1, 1, 0 }
local function surge(state, speed, glow, swell, rise, fall)
    state.surge = { From = { state.speed, state.glow, state.swell }, To = { speed, glow, swell }, Start = os.clock(), Rise = rise, Fall = fall }
end

local function updateSurge(state, now)
    local s = state.surge
    if not s then
        return
    end
    local t = now - s.Start
    local from, to, k
    if t < s.Rise then
        from, to, k = s.From, s.To, smooth(t / s.Rise)
    elseif t < s.Rise + s.Fall then
        from, to, k = s.To, REST, smooth((t - s.Rise) / s.Fall)
    else
        from, to, k, state.surge = REST, REST, 1, nil
    end
    state.speed = from[1] + (to[1] - from[1]) * k
    state.glow = from[2] + (to[2] - from[2]) * k
    state.swell = from[3] + (to[3] - from[3]) * k
end

-- A ring running outward: a copy of the ripple's hidden image, grown and faded by step().
local function startRipple(state, r)
    for _, t in r.Templates do
        local label = t.Label:Clone()
        label.Visible = true
        label.Size = UDim2.fromScale(0.15, 0.15)
        label.Parent = t.Label.Parent
        table.insert(state.waves, { Label = label, Start = os.clock(), Duration = r.A.Ripple or 1, Base = t.Label.ImageTransparency })
    end
end

local function emitAll(state, attribute)
    for _, e in state.emitters do
        local n = e.Emitter:GetAttribute(attribute)
        if n and n > 0 then
            e.Emitter:Emit(n)
        end
    end
    for _, r in state.ripples do
        for k = 1, r.A[attribute] or 0 do
            task.delay((k - 1) * RIPPLE_GAP, function()
                if state.model.Parent then
                    startRipple(state, r)
                end
            end)
        end
    end
end

-- The breath at time `now`, from -1 to 1: a smooth swell, or with BreathShape "Heartbeat" a
-- double thump (lub-dub) and a rest.
local function breathAt(ma, now, phase)
    local t = now / (ma.BreathPeriod or 4) + phase / TAU
    if ma.BreathShape == "Heartbeat" then
        local p = t % 1
        local beat = math.exp(-((p - 0.08) / 0.05) ^ 2) + 0.65 * math.exp(-((p - 0.26) / 0.05) ^ 2)
        return beat * 2 - 0.5
    end
    return math.sin(t * TAU)
end

local function step(state, dt, now)
    updateSurge(state, now)
    local ma = state.modelAttrs.A
    local breath = (ma.Breath or 0) * breathAt(ma, now, state.breathPhase)
    local speed = state.speed * (1 + breath)
    local glow = state.glow * (1 + breath * 0.6)
    local swell = state.swell + breath * 2
    for _, m in state.movers do
        m.Angle += (m.A.Orbit or 0) * dt * speed
        m.Instance.Position = moverPosition(m.A, m.Angle, now)
    end
    for _, s in state.spinners do
        s.Angle += (s.A.Spin or 0) * dt * speed
        local base = s.Base
        local wobble = s.A.Wobble
        if wobble then -- the plane's tilt precesses, like a spinning top
            s.Precess = (s.Precess or math.rad(s.A.Phase or 0)) + dt * speed * TAU / (s.A.WobblePeriod or 6)
            base *= CFrame.Angles(math.rad(wobble) * math.sin(s.Precess), 0, math.rad(wobble) * math.cos(s.Precess))
        end
        s.Instance.CFrame = base * CFrame.Angles(0, math.rad(s.Angle), 0)
        local scale = swellScale(s.A, swell)
        if math.abs(scale - s.Scale) > 1e-3 then
            s.Scale = scale
            for _, l in s.Labels do
                l.Label.Size = UDim2.fromScale(l.Size.X.Scale * scale, l.Size.Y.Scale * scale)
            end
        end
    end
    for _, w in state.sways do
        local a = w.A
        w.Instance.Rotation = (a.Sway or 0) * math.sin(now * TAU / (a.SwayPeriod or 3) + math.rad(a.Phase or 0))
    end
    for k = #state.waves, 1, -1 do
        local w = state.waves[k]
        local t = (now - w.Start) / w.Duration
        if t >= 1 or not w.Label.Parent then
            w.Label:Destroy()
            table.remove(state.waves, k)
        else
            local grow = 0.15 + 0.85 * (1 - (1 - t) ^ 2)
            w.Label.Size = UDim2.fromScale(grow, grow)
            w.Label.ImageTransparency = w.Base + (1 - w.Base) * t ^ 1.5
        end
    end
    for _, l in state.lights do
        l.Light.Brightness = l.Brightness * glow
    end
    for _, g in state.guis do
        g.Gui.Brightness = g.Brightness * glow
    end
end

local function track(model)
    if not auras[model] then
        auras[model] = index(model)
    end
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(track)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(function(model)
    auras[model] = nil
end)
for _, model in CollectionService:GetTagged(TAG) do
    track(model)
end

RunService.RenderStepped:Connect(function(dt)
    local camera = Workspace.CurrentCamera
    if not camera then
        return
    end
    local eye = camera.CFrame.Position
    local now = os.clock()
    for model, state in auras do
        if not state then
            track(model) -- not streamed in yet: look again
            continue
        end
        if not model.Parent then
            auras[model] = nil
            continue
        end
        local distance = (state.root.Position - eye).Magnitude
        setLevel(state, distance < NEAR and 2 or distance < FAR and 1 or 0)
        if state.level == 0 then
            continue
        end
        step(state, dt, now)
    end
end)

-- The egg on the aura's stand (FloatingIslands.<Island>.EggStands.<EggId>.Egg), if streamed in.
local function eggOf(state)
    local island = state.model.Parent and state.model.Parent.Parent
    local stands = island and island:FindFirstChild("EggStands")
    local stand = stands and stands:FindFirstChild(state.eggId)
    return stand and stand:FindFirstChild("Egg")
end

-- The egg brightens in the aura's tint while the hatch gathers, flashes on the burst, then fades.
local function brighten(state)
    local egg = eggOf(state)
    if not egg then
        return nil
    end
    local highlight = Instance.new("Highlight")
    highlight.Adornee = egg
    highlight.DepthMode = Enum.HighlightDepthMode.Occluded
    highlight.FillColor = state.tint or Color3.new(1, 1, 1)
    highlight.OutlineColor = Color3.new(1, 1, 1)
    highlight.FillTransparency = 1
    highlight.OutlineTransparency = 1
    highlight.Parent = state.model
    TweenService:Create(highlight, TweenInfo.new(state.gather, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
        { FillTransparency = 0.45, OutlineTransparency = 0.3 }):Play()
    return highlight
end

local function flash(highlight)
    if not highlight or not highlight.Parent then
        return
    end
    highlight.FillColor = highlight.FillColor:Lerp(Color3.new(1, 1, 1), 0.6)
    highlight.FillTransparency = 0.05
    highlight.OutlineTransparency = 0
    local fade = TweenService:Create(highlight, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        { FillTransparency = 1, OutlineTransparency = 1 })
    fade.Completed:Connect(function()
        highlight:Destroy()
    end)
    fade:Play()
end

-- Plays the hatch at the aura of this egg nearest the player: it gathers, then bursts.
function EggAura.hatch(eggId)
    local character = Players.LocalPlayer.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root then
        return
    end
    local best, bestDistance = nil, 60
    for _, state in auras do
        if state and state.eggId == eggId then
            local d = (state.root.Position - root.Position).Magnitude
            if d < bestDistance then
                best, bestDistance = state, d
            end
        end
    end
    if not best or best.hatching then
        return
    end
    local state = best
    state.hatching = true
    surge(state, 6, 2.6, -1, state.gather, 2)
    for _, e in state.emitters do
        local rate = e.Emitter:GetAttribute("GatherRate")
        if rate then
            e.Emitter.Rate = rate
        end
    end
    local highlight = brighten(state)
    task.delay(state.gather, function()
        for _, e in state.emitters do
            if e.Emitter:GetAttribute("GatherRate") then
                e.Emitter.Rate = e.Rate * rateFactor(state)
            end
        end
        if state.model.Parent then
            emitAll(state, "HatchEmit")
            surge(state, 2.5, 3.2, 2, 0.12, 1.6)
        end
        flash(highlight)
        task.delay(1.8, function()
            state.hatching = false
        end)
    end)
end

return EggAura

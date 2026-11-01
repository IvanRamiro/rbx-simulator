-- Brings the egg auras to life. The auras are built in the Workspace (src/worldbuild/EggAuraVFX.lua)
-- and tagged "EggAura"; this script only moves and times them from their attributes, so an aura
-- tuned by hand in Studio keeps working:
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
-- "Heartbeat" makes it beat instead: a double thump, then a rest. The rhythm runs faster as the
-- aura speeds up, so a heart races while a hatch gathers. On the beat (0 to 1, the breath's peak):
--   * beams with BeatWidth swell their width and brightness by that fraction;
--   * orbiting attachments with BeatReach are flung that many studs further out, and with
--     GatherPull drawn in by that fraction while a hatch gathers (and flung out on the burst);
--   * emitters and ripples with BeatEmit fire that many on each first thump;
--   * a model with BeatHighlight throbs a Highlight on its egg in its Tint;
--   * a model with BeatScreen (studs) pulses the player's screen, ColorCorrection and Bloom, in
--     its Tint when the camera is within that distance, and flashes it white-hot on the burst.
-- Parts with an Orbit attribute (rocks) orbit like attachments, carrying their child parts (their
-- glowing cores), and tumble by Tumble (Vector3, degrees per second). A mover with AvoidAngle
-- (degrees round its orbit) pulls in to AvoidRadius studs as it passes that way, past a
-- neighbouring egg, however far a pulse or a hatch throws it.
-- An aura with PulseInterval (seconds, give or take PulseJitter) sends an energy pulse through
-- itself, each piece answering PulseDelay seconds after it starts, so nothing pulses at once:
--   * the aura speeds up by PulseSpeed and glows brighter by PulseGlow (fractions);
--   * orbiting pieces are thrown PulseReach studs outward and ease back;
--   * beams with PulseWidth and spinning planes with PulseSwell swell by that much;
--   * emitters and ripples with PulseEmit fire that many;
--   * with PulseEggGlow (a colour), the egg's own glowing parts heat toward it (and while a hatch
--     gathers and bursts).
-- Emitters with FlickerRate (a NumberRange) flicker like flames: every FlickerPeriod seconds
-- (default 0.15) their rate jumps to a random value in that range, and with FlickerSpeedMin and
-- FlickerSpeedMax (NumberRanges) their speed's low and high ends jump too.
-- The hatch's burst sends a pulse too. Settings, all model attributes, all optional: Intensity
-- (glow), Density (emission rates), OrbitSpeed, LightIntensity, and Visible (false hides it).
-- An aura with CyclePeriod (seconds) runs a cycle through it, a fraction from 0 to 1 that wraps
-- round; every curve below is a NumberSequence or ColorSequence over that fraction:
--   * emitters with CycleRate scale their rate by it, and with CycleEmit fire that many as the
--     cycle passes CycleAt;
--   * lights with CycleBrightness scale by it and take their colour from CycleColor;
--   * attachments with SweepTo move from SweepFrom (via SweepVia) to SweepTo as SweepCurve rises
--     from 0 to 1 (a trail between one and a still attachment sweeps open like a wing);
--   * the model's CycleEggGlow (0 cold, 1 the egg's own glow, 2 hot) cools the egg's glowing parts
--     toward CycleEggCold and heats them toward CycleEggHot; CycleHighlight (colour),
--     CycleOutline and CycleFill (transparencies) drive a Highlight on the egg;
--   * with CycleScreen (studs) the player's screen flashes by CycleScreenFlash as the cycle passes
--     CycleRebirth, and a hatch's burst jumps the cycle to CycleRebirth.
-- Auras run at full rate near the camera, half rate further out, and switch off beyond that, or
-- when their egg's stand is gone.
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

-- An instance with its attributes, kept current when they are changed (by hand, in Play). The
-- connection goes into `connections` (the aura's), so releasing the aura drops it.
local function watched(instance, connections)
    local entry = { Instance = instance, A = instance:GetAttributes() }
    table.insert(connections, instance.AttributeChanged:Connect(function()
        entry.A = instance:GetAttributes()
    end))
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
        connections = {}, movers = {}, spinners = {}, ripples = {}, waves = {}, sways = {}, emitters = {}, trails = {}, lights = {}, guis = {}, flickers = {}, sweepers = {},
        speed = 1, glow = 1, swell = 0, level = 2,
        gather = model:GetAttribute("Gather") or 1.2,
        breathT = math.random(), beat = 0, swellBeams = {}, screenFlash = 0, distance = math.huge,
        cycleT = math.random(),
    }
    state.modelAttrs = watched(model, state.connections)
    for _, d in model:GetDescendants() do
        if (d:IsA("Attachment") or d:IsA("BasePart")) and d:GetAttribute("Orbit") then
            local m = watched(d, state.connections)
            m.Angle = m.A.Phase or 0
            if d:IsA("BasePart") then
                m.Base, m.Rot, m.Followers = d.CFrame, root.CFrame:ToObjectSpace(d.CFrame).Rotation, {}
                for _, c in d:GetDescendants() do
                    if c:IsA("BasePart") then
                        table.insert(m.Followers, { Part = c, Offset = d.CFrame:ToObjectSpace(c.CFrame), Base = c.CFrame })
                    end
                end
            end
            table.insert(state.movers, m)
        elseif d:IsA("Attachment") and d:GetAttribute("SweepTo") then
            table.insert(state.sweepers, watched(d, state.connections))
        elseif d:IsA("BasePart") and d:GetAttribute("Ripple") then
            local r = watched(d, state.connections)
            r.Templates = labelsOf(d)
            table.insert(state.ripples, r)
        elseif d:IsA("BasePart") and d:GetAttribute("Spin") then
            local s = watched(d, state.connections)
            s.Base, s.Angle, s.Scale, s.Labels = d.CFrame, 0, 1, labelsOf(d)
            table.insert(state.spinners, s)
        elseif d:IsA("ImageLabel") and d:GetAttribute("Sway") then
            table.insert(state.sways, watched(d, state.connections))
        elseif d:IsA("ParticleEmitter") then
            table.insert(state.emitters, { Emitter = d, Rate = d.Rate, Enabled = d.Enabled, Speed = d.Speed,
                CycleRate = d:GetAttribute("CycleRate"), CycleEmit = d:GetAttribute("CycleEmit"), CycleAt = d:GetAttribute("CycleAt") })
            if d:GetAttribute("FlickerRate") or d:GetAttribute("FlickerSpeedMin") then
                local f = watched(d, state.connections)
                f.Next = 0
                table.insert(state.flickers, f)
            end
        elseif d:IsA("Trail") or d:IsA("Beam") then
            table.insert(state.trails, d)
            if d:IsA("Beam") and (d:GetAttribute("BeatWidth") or d:GetAttribute("PulseWidth")) then
                table.insert(state.swellBeams, { Beam = d, W0 = d.Width0, W1 = d.Width1, B = d.Brightness, K = d:GetAttribute("BeatWidth") or 0,
                    P = d:GetAttribute("PulseWidth") or 0, Delay = d:GetAttribute("PulseDelay") or 0 })
            end
        elseif d:IsA("Light") then
            table.insert(state.lights, { Light = d, Brightness = d.Brightness, Color = d.Color,
                CycleBrightness = d:GetAttribute("CycleBrightness"), CycleColor = d:GetAttribute("CycleColor") })
        elseif d:IsA("SurfaceGui") or d:IsA("BillboardGui") then
            table.insert(state.guis, { Gui = d, Brightness = d.Brightness })
        end
    end
    task.spawn(function()
        pcall(ContentProvider.PreloadAsync, ContentProvider, { model })
    end)
    return state
end

local function rateFactor(state)
    return (state.level == 1 and 0.5 or 1) * (state.modelAttrs.A.Density or 1)
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
    if state.beatHighlight then
        state.beatHighlight.Enabled = on
    end
    if state.cycleHighlight then
        state.cycleHighlight.Enabled = on
    end
end

-- Where an orbiting attachment is at `angle` degrees round its orbit (relative to the Root).
local function moverPosition(a, angle, now, radius)
    radius = radius or a.Radius or 2.5
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

-- The rhythm `t` cycles in: the beat from 0 to 1 (a smooth swell, or with BreathShape "Heartbeat"
-- a double thump, lub-dub, then a rest), and the breath from -1 to 1.
local function beatAt(ma, t)
    local p = t % 1
    if ma.BreathShape == "Heartbeat" then
        local beat = math.exp(-((p - 0.08) / 0.05) ^ 2) + 0.65 * math.exp(-((p - 0.26) / 0.05) ^ 2)
        return beat, beat * 2 - 0.5
    end
    local b = math.sin(p * TAU)
    return (b + 1) / 2, b
end

-- The egg on the aura's stand (FloatingIslands.<Island>.EggStands.<EggId>.Egg), if streamed in.
local function eggOf(state)
    local island = state.model.Parent and state.model.Parent.Parent
    local stands = island and island:FindFirstChild("EggStands")
    local stand = stands and stands:FindFirstChild(state.eggId)
    return stand and stand:FindFirstChild("Egg")
end

local THUMB = 0.08 -- where in the cycle the first thump peaks

-- The energy pulse at `delay` seconds after the last one began, 0 to 1: a sharp rise, then a slow
-- ease back.
local PULSE_RISE, PULSE_FALL = 0.18, 1.5
local function pulseAt(state, now, delay)
    local start = state.pulseStart
    if not start then
        return 0
    end
    local t = now - start - (delay or 0)
    if t <= 0 then
        return 0
    elseif t < PULSE_RISE then
        return smooth(t / PULSE_RISE)
    end
    return 1 - smooth((t - PULSE_RISE) / PULSE_FALL)
end

local function firePulse(state, now)
    state.pulseStart = now
    for _, e in state.emitters do
        local emitter = e.Emitter
        local n = emitter:GetAttribute("PulseEmit")
        if n and n > 0 then
            task.delay(emitter:GetAttribute("PulseDelay") or 0, function()
                if state.model.Parent and state.level > 0 then
                    emitter:Emit(n)
                end
            end)
        end
    end
    for _, r in state.ripples do
        for k = 1, r.A.PulseEmit or 0 do
            task.delay((r.A.PulseDelay or 0) + (k - 1) * RIPPLE_GAP, function()
                if state.model.Parent and state.level > 0 then
                    startRipple(state, r)
                end
            end)
        end
    end
end

-- The egg's own glowing parts (its stand's "<EggId>_Glow_<hex>" pieces), with their colours as built.
local function eggGlowParts(state)
    if not state.eggGlow then
        local egg = eggOf(state)
        if not egg then
            return nil
        end
        state.eggGlow = {}
        for _, d in egg.Parent:GetDescendants() do
            if d:IsA("BasePart") and d.Name:find("_Glow_") then
                table.insert(state.eggGlow, { Part = d, Color = d.Color })
            end
        end
    end
    return state.eggGlow
end

-- The egg's glowing parts heated toward `hot`.
local function heatEgg(state, hot, heat)
    if not eggGlowParts(state) then
        return
    end
    if math.abs(heat - (state.eggHeat or 0)) < 0.005 then
        return
    end
    state.eggHeat = heat
    for _, g in state.eggGlow do
        g.Part.Color = g.Color:Lerp(hot, heat)
    end
end

-- A NumberSequence or ColorSequence read at `t` (0 to 1), straight between its keypoints.
local function evalSeq(seq, t)
    local k = seq.Keypoints
    for i = 1, #k - 1 do
        local a, b = k[i], k[i + 1]
        if t <= b.Time then
            local f = (b.Time > a.Time) and (t - a.Time) / (b.Time - a.Time) or 0
            if typeof(a.Value) == "Color3" then
                return a.Value:Lerp(b.Value, f)
            end
            return a.Value + (b.Value - a.Value) * f
        end
    end
    return k[#k].Value
end

-- Whether the cycle passed `at` going from `before` to `after` (wrapping round at 1).
local function passed(before, after, at)
    if after >= before then
        return before < at and at <= after
    end
    return at > before or at <= after
end

local function quadratic(a, b, c, t)
    return a:Lerp(b, t):Lerp(b:Lerp(c, t), t)
end

local function stepCycle(state, dt, ma)
    local before = state.cycleT % 1
    state.cycleT += dt / ma.CyclePeriod
    local t = state.cycleT % 1
    for _, e in state.emitters do
        if e.CycleRate and not state.hatching then
            e.Emitter.Rate = e.Rate * rateFactor(state) * evalSeq(e.CycleRate, t)
        end
        if e.CycleEmit and passed(before, t, e.CycleAt or 0) then
            e.Emitter:Emit(e.CycleEmit)
        end
    end
    if ma.CycleScreen and passed(before, t, ma.CycleRebirth or 0) then
        state.screenFlash = math.max(state.screenFlash, ma.CycleScreenFlash or 0.5)
    end
    for _, s in state.sweepers do
        local a = s.A
        local k = a.SweepCurve and evalSeq(a.SweepCurve, t) or 0
        s.Instance.Position = quadratic(a.SweepFrom, a.SweepVia or (a.SweepFrom + a.SweepTo) / 2, a.SweepTo, math.clamp(k, 0, 1))
    end
    local glow = ma.CycleEggGlow and eggGlowParts(state)
    if glow then
        local g = evalSeq(ma.CycleEggGlow, t)
        if math.abs(g - (state.eggCycle or -1)) > 0.004 then
            state.eggCycle = g
            local cold, hot = ma.CycleEggCold or Color3.new(0, 0, 0), ma.CycleEggHot or Color3.new(1, 1, 1)
            for _, p in glow do
                p.Part.Color = g < 1 and p.Color:Lerp(cold, 1 - g) or p.Color:Lerp(hot, math.min(g - 1, 1))
            end
        end
    end
    if ma.CycleHighlight then
        local h = state.cycleHighlight
        if not h then
            local egg = eggOf(state)
            if egg then
                h = Instance.new("Highlight")
                h.Name = "Cycle"
                h.Adornee = egg
                h.DepthMode = Enum.HighlightDepthMode.Occluded
                h.Parent = state.model
                state.cycleHighlight = h
            end
        end
        if h then
            local c = evalSeq(ma.CycleHighlight, t)
            h.OutlineColor, h.FillColor = c, c
            h.OutlineTransparency = ma.CycleOutline and evalSeq(ma.CycleOutline, t) or 1
            h.FillTransparency = ma.CycleFill and evalSeq(ma.CycleFill, t) or 1
        end
    end
    return t
end

local function step(state, dt, now)
    updateSurge(state, now)
    local ma = state.modelAttrs.A
    if ma.Density ~= state.density then
        state.density = ma.Density
        if not state.hatching then
            for _, e in state.emitters do
                e.Emitter.Rate = e.Rate * rateFactor(state)
            end
        end
    end
    local interval = ma.PulseInterval
    if interval and not state.hatching then
        state.nextPulse = state.nextPulse or now + interval * math.random()
        if now >= state.nextPulse then
            firePulse(state, now)
            state.nextPulse = now + interval + (ma.PulseJitter or 0) * (math.random() * 2 - 1)
        end
    end
    local pulse = pulseAt(state, now, 0)
    local cycle = ma.CyclePeriod and stepCycle(state, dt, ma)
    if not state.hatching then
        for _, f in state.flickers do
            if now >= f.Next then
                local a = f.A
                f.Next = now + (a.FlickerPeriod or 0.15)
                local rate, lo, hi = a.FlickerRate, a.FlickerSpeedMin, a.FlickerSpeedMax
                if rate then
                    f.Instance.Rate = (rate.Min + math.random() * (rate.Max - rate.Min)) * rateFactor(state)
                end
                if lo and hi then
                    f.Instance.Speed = NumberRange.new(lo.Min + math.random() * (lo.Max - lo.Min), hi.Min + math.random() * (hi.Max - hi.Min))
                end
            end
        end
    end
    local before = state.breathT % 1
    state.breathT += dt * state.speed / (ma.BreathPeriod or 4)
    local after = state.breathT % 1
    if (before < THUMB and after >= THUMB) or (after < before and after >= THUMB) then
        emitAll(state, "BeatEmit")
    end
    local beat, b = beatAt(ma, state.breathT)
    state.beat = beat
    local breath = (ma.Breath or 0) * b
    local speed = state.speed * (1 + breath) * (1 + (ma.PulseSpeed or 0) * pulse) * (ma.OrbitSpeed or 1)
    local glow = state.glow * (1 + breath * 0.6) * (1 + (ma.PulseGlow or 0) * pulse) * (ma.Intensity or 1)
    local swell = state.swell + breath * 2
    for _, m in state.movers do
        local a = m.A
        m.Angle += (a.Orbit or 0) * dt * speed
        local radius = (a.Radius or 2.5) + (a.BeatReach or 0) * (beat + math.max(state.swell, 0) * 1.5)
            + (a.PulseReach or 0) * pulseAt(state, now, a.PulseDelay)
        if state.swell < 0 then
            radius *= 1 + state.swell * (a.GatherPull or 0)
        end
        local avoid = a.AvoidAngle
        if avoid then
            local w = math.max(0, math.cos(math.rad(m.Angle - avoid))) ^ 2
            radius += (math.min(radius, a.AvoidRadius or radius) - radius) * w
        end
        local p = moverPosition(a, m.Angle, now, radius)
        if m.Rot then
            local tumble = a.Tumble
            if tumble then
                local k = math.rad(1) * dt * speed
                m.Rot *= CFrame.Angles(tumble.X * k, tumble.Y * k, tumble.Z * k)
            end
            local cf = state.root.CFrame * CFrame.new(p) * m.Rot
            m.Instance.CFrame = cf
            for _, f in m.Followers do
                f.Part.CFrame = cf * f.Offset
            end
        else
            m.Instance.Position = p
        end
    end
    local beamGlow = state.glow * (ma.Intensity or 1)
    for _, a in state.swellBeams do
        local k = 1 + a.K * (beat + math.max(state.swell, 0)) + a.P * pulseAt(state, now, a.Delay)
        a.Beam.Width0, a.Beam.Width1 = a.W0 * k, a.W1 * k
        a.Beam.Brightness = a.B * k * beamGlow
    end
    if ma.PulseEggGlow then
        heatEgg(state, ma.PulseEggGlow, math.max(pulse, math.clamp(state.glow - 1, 0, 1)))
    end
    if ma.BeatHighlight then
        local h = state.beatHighlight
        if not h then
            local egg = eggOf(state)
            if egg then
                h = Instance.new("Highlight")
                h.Name = "Heartbeat"
                h.Adornee = egg
                h.DepthMode = Enum.HighlightDepthMode.Occluded
                h.FillColor = state.tint or Color3.new(1, 1, 1)
                h.OutlineColor = (state.tint or Color3.new(1, 1, 1)):Lerp(Color3.new(1, 1, 1), 0.4)
                h.Parent = state.model
                state.beatHighlight = h
            end
        end
        if h then
            h.Enabled = not state.hatching and state.level > 0
            -- a stronger fill paints over the egg's baked facets
            h.FillTransparency = 1 - 0.15 * beat
            h.OutlineTransparency = 1 - 0.85 * beat
        end
    end
    state.screenFlash = math.max(0, state.screenFlash - dt * 1.4)
    for _, s in state.spinners do
        s.Angle += (s.A.Spin or 0) * dt * speed
        local base = s.Base
        local wobble = s.A.Wobble
        if wobble then
            s.Precess = (s.Precess or math.rad(s.A.Phase or 0)) + dt * speed * TAU / (s.A.WobblePeriod or 6)
            base *= CFrame.Angles(math.rad(wobble) * math.sin(s.Precess), 0, math.rad(wobble) * math.cos(s.Precess))
        end
        s.Instance.CFrame = base * CFrame.Angles(0, math.rad(s.Angle), 0)
        local scale = swellScale(s.A, swell + (s.A.PulseSwell or 0) * pulseAt(state, now, s.A.PulseDelay))
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
    local lightGlow = glow * (ma.LightIntensity or 1)
    for _, l in state.lights do
        l.Light.Brightness = l.Brightness * lightGlow * (cycle and l.CycleBrightness and evalSeq(l.CycleBrightness, cycle) or 1)
        if cycle and l.CycleColor then
            l.Light.Color = evalSeq(l.CycleColor, cycle)
        end
    end
    for _, g in state.guis do
        g.Gui.Brightness = g.Brightness * glow
    end
end

-- Hands an aura back as it was built when it stops being tracked (its tag removed, to tune it in
-- Studio), so tagging it again indexes the authored values, not ones the runtime had changed:
-- emitters, trails and guis switched off by distance, beams swollen mid-beat, scaled brightness.
local function release(state)
    for _, connection in state.connections do
        connection:Disconnect()
    end
    for _, e in state.emitters do
        e.Emitter.Enabled, e.Emitter.Rate, e.Emitter.Speed = e.Enabled, e.Rate, e.Speed
    end
    for _, t in state.trails do
        t.Enabled = true
    end
    for _, l in state.lights do
        l.Light.Enabled = true
    end
    for _, g in state.guis do
        g.Gui.Enabled = true
    end
    for _, a in state.swellBeams do
        a.Beam.Width0, a.Beam.Width1, a.Beam.Brightness = a.W0, a.W1, a.B
    end
    for _, m in state.movers do
        if m.Base then
            m.Instance.CFrame = m.Base
            for _, f in m.Followers do
                f.Part.CFrame = f.Base
            end
        end
    end
    for _, g in state.eggGlow or {} do
        g.Part.Color = g.Color
    end
    for _, l in state.lights do
        l.Light.Brightness, l.Light.Color = l.Brightness, l.Color
    end
    for _, s in state.sweepers do
        if s.A.SweepFrom then
            s.Instance.Position = s.A.SweepFrom
        end
    end
    for _, g in state.guis do
        g.Gui.Brightness = g.Brightness
    end
    for _, s in state.spinners do
        s.Instance.CFrame = s.Base
        for _, l in s.Labels do
            l.Label.Size = l.Size
        end
    end
    for _, w in state.sways do
        w.Instance.Rotation = 0
    end
    for _, w in state.waves do
        w.Label:Destroy()
    end
    if state.beatHighlight then
        state.beatHighlight:Destroy()
    end
    if state.cycleHighlight then
        state.cycleHighlight:Destroy()
    end
end

local function track(model)
    if not auras[model] then
        auras[model] = index(model)
    end
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(track)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(function(model)
    if auras[model] then
        release(auras[model])
    end
    auras[model] = nil
end)
for _, model in CollectionService:GetTagged(TAG) do
    track(model)
end

-- The heartbeat on the player's screen (client-only effects, made when first needed).
local screen
local function screenEffects()
    if not screen then
        local Lighting = game:GetService("Lighting")
        local cc = Instance.new("ColorCorrectionEffect")
        cc.Name = "EggAuraHeartbeat"
        cc.Enabled = false
        cc.Parent = Lighting
        local bloom = Instance.new("BloomEffect")
        bloom.Name = "EggAuraHeartbeatBloom"
        bloom.Size = 30
        bloom.Threshold = 0.95
        bloom.Enabled = false
        bloom.Parent = Lighting
        screen = { cc = cc, bloom = bloom }
    end
    return screen
end

local function updateScreen()
    local weight, flash, tint = 0, 0, nil
    for _, state in auras do
        local A = state and state.modelAttrs.A
        local radius = state and state.level > 0 and (A.BeatScreen or A.CycleScreen)
        if radius then
            local near = math.clamp(1 - state.distance / radius, 0, 1)
            local w = A.BeatScreen and smooth(near) * (0.2 + 0.8 * state.beat) or 0 -- a cycle only flashes
            if w + state.screenFlash > weight + flash then
                weight, flash, tint = w, state.screenFlash * smooth(near), state.tint
            end
        end
    end
    if weight + flash <= 0.002 then
        if screen then
            screen.cc.Enabled, screen.bloom.Enabled = false, false
        end
        return
    end
    local fx = screenEffects()
    local white = Color3.new(1, 1, 1)
    fx.cc.Enabled, fx.bloom.Enabled = true, true
    fx.cc.TintColor = white:Lerp(tint or white, 0.22 * weight * (1 - flash))
    fx.cc.Brightness = 0.03 * weight + 0.35 * flash
    fx.cc.Contrast = 0.12 * weight
    fx.cc.Saturation = 0.18 * weight - 0.3 * flash
    fx.bloom.Intensity = 0.7 * weight + 1.5 * flash
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
        state.distance = distance
        if now >= (state.eggCheck or 0) then
            state.eggCheck = now + 1
            local egg = eggOf(state)
            state.hasEgg = egg ~= nil
            if egg and egg ~= state.egg then
                -- a stand that streamed out and back in is new instances: forget the old ones
                state.egg = egg
                state.eggGlow, state.eggHeat, state.eggCycle = nil, nil, nil
                if state.beatHighlight then
                    state.beatHighlight.Adornee = egg
                end
                if state.cycleHighlight then
                    state.cycleHighlight.Adornee = egg
                end
            end
        end
        local shown = state.hasEgg and state.modelAttrs.A.Visible ~= false
        setLevel(state, not shown and 0 or distance < NEAR and 2 or distance < FAR and 1 or 0)
        if state.level == 0 then
            continue
        end
        step(state, dt, now)
    end
    updateScreen()
end)

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
            if state.modelAttrs.A.PulseInterval then
                firePulse(state, os.clock())
            end
            surge(state, 2.5, 3.2, 2, 0.12, 1.6)
            local ma = state.modelAttrs.A
            if ma.CyclePeriod and ma.CycleRebirth then
                state.cycleT = math.floor(state.cycleT) + ma.CycleRebirth - 0.002
            end
            if ma.BeatScreen or ma.CycleScreen then
                state.screenFlash = 1
            end
        end
        flash(highlight)
        task.delay(1.8, function()
            state.hatching = false
        end)
    end)
end

return EggAura

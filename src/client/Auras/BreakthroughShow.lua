-- The player's own breakthrough: BreakthroughFx draws the world and keeps the clock; this adds what only the one breaking through
-- sees and hears, in the same beats (BreakthroughStyles.Grades[grade].Own):
--   camera    never taken over: the player's own camera keeps running and an offset is laid over it each frame, so they can look
--             round and move at any time. It leans in and narrows through the gather and the held breath, punches at the break,
--             then pulls back and slowly orbits while the title card stands, and eases home in the settle.
--   screen    the world dims and loses colour as it gathers, the edges glow the realm's colour, a flash at the break (a dip into
--             black first for the Void), a bloom and a short blur, letterbox bars and a title card (BreakthroughCard)
--   HUD       Hud, HudTop and TouchActions step aside from a Milestone up, as in the hatch cinematic, and come back as the card leaves
--   sound     a drawn breath, a humming swell rising in pitch, silence in the held breath, the break (grade by grade), the realm's
--             beats; the music ducks, and notices wait their turn (Sfx.hold, Toast.hold)
--   skip      a Milestone or more can be skipped by a tap or a click anywhere (the hatch cinematic's pattern); the sequence jumps to
--             its settle and the title is said once in a notice instead
-- Reduced Effects: no shake, no blur or bloom, a gentle fade instead of the flash, smaller camera moves, no orbit. The phone tier thins
-- the particles (BreakthroughFx) and drops the bloom and the blur.
--
--   BreakthroughShow.play(spec) -> show
--     spec: Player, Character, Root, Info (BreakthroughStyles.describe), Container (a Folder in the workspace), Calm, Low,
--           OnBreak() at the break (the new aura is shown), OnSettle() as the card leaves, OnDone() when everything is over and removed
--   BreakthroughShow.skip(show), BreakthroughShow.stop(show)  (stop: at once, nothing left behind)
--   BreakthroughShow.baseFov()  the field of view the running show started from, or nil
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Client = script.Parent.Parent
local Card = require(script.Parent:WaitForChild("BreakthroughCard"))
local Fx = require(script.Parent:WaitForChild("BreakthroughFx"))
local Sfx = require(Client:WaitForChild("Audio"):WaitForChild("Sfx"))
local Toast = require(Client:WaitForChild("UI"):WaitForChild("Toast"))
local UiKit = require(Client:WaitForChild("UI"):WaitForChild("UiKit"))
local UiTheme = require(Client:WaitForChild("UI"):WaitForChild("UiTheme"))

local Show = {}

local player = Players.LocalPlayer
local C = UiTheme.Colors
local RENDER_NAME = "BreakthroughShow"
local RENDER_PRE = "BreakthroughShowPre"
local HUD_GUIS = { "Hud", "HudTop", "HudNotice", "HudWindows", "TouchActions" } -- (as the hatch cinematic puts away the HUD; the notices wait: Toast.hold)
local FOLLOW = 7 -- how quickly the slow camera and grade channels follow their targets (1 / second)

local function clamp01(x)
    return math.clamp(x, 0, 1)
end

local function smooth(x)
    x = clamp01(x)
    return x * x * (3 - 2 * x)
end

local function ramp(t, a, b)
    return clamp01((t - a) / (b - a))
end

local function outCubic(x)
    return 1 - (1 - clamp01(x)) ^ 3
end

local function follow(current, target, dt, rate)
    return current + (target - current) * (1 - math.exp(-dt * (rate or FOLLOW)))
end

local active = nil -- the one running: a second never overlaps it (AuraController waits for OnDone)

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.IgnoreWater = true

-- ---------- the pieces ----------
local function makeGui(S)
    local grade, theme = S.grade, S.theme
    local playerGui = player:WaitForChild("PlayerGui")
    local gui = Instance.new("ScreenGui")
    gui.Name = "BreakthroughShow"
    gui.IgnoreGuiInset = true
    gui.ScreenInsets = Enum.ScreenInsets.None
    gui.ResetOnSpawn = false
    gui.DisplayOrder = 28
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = playerGui
    S.gui = gui

    -- the screen's edges, in the realm's colour, closing in as it gathers
    S.edges = {}
    for side = 0, 1 do
        local edge = Instance.new("Frame")
        edge.Name = "Edge"
        edge.BorderSizePixel = 0
        edge.BackgroundColor3 = theme.Deep:Lerp(theme.Main, 0.4)
        edge.BackgroundTransparency = 1
        edge.AnchorPoint = Vector2.new(side, 0)
        edge.Position = UDim2.fromScale(side, 0)
        edge.Size = UDim2.fromScale(0.24, 1)
        edge.ZIndex = 3
        edge.Parent = gui
        local fade = Instance.new("UIGradient")
        fade.Transparency = if side == 0 then NumberSequence.new(0, 1) else NumberSequence.new(1, 0)
        fade.Parent = edge
        table.insert(S.edges, edge)
    end

    -- letterbox bars (a Milestone and up)
    S.bars = {}
    if grade.Bars > 0 then
        for side = 0, 1 do
            local bar = Instance.new("Frame")
            bar.Name = "Bar"
            bar.BorderSizePixel = 0
            bar.BackgroundColor3 = Color3.new(0, 0, 0)
            bar.AnchorPoint = Vector2.new(0, side)
            bar.Position = UDim2.fromScale(0, side)
            bar.Size = UDim2.fromScale(1, 0)
            bar.ZIndex = 6
            bar.Parent = gui
            table.insert(S.bars, bar)
        end
    end

    -- the flash (above everything but the tap layer)
    local flash = Instance.new("Frame")
    flash.Name = "Flash"
    flash.BorderSizePixel = 0
    flash.BackgroundColor3 = theme.Hot:Lerp(Color3.new(1, 1, 1), 0.7)
    flash.BackgroundTransparency = 1
    flash.Size = UDim2.fromScale(1, 1)
    flash.ZIndex = 5 -- (under the bars: they stay black)
    flash.Parent = gui
    S.flashFrame = flash

    if grade.Tap then
        local tapper = Instance.new("TextButton")
        tapper.Name = "Tap"
        tapper.BackgroundTransparency = 1
        tapper.Text = ""
        tapper.AutoButtonColor = false
        tapper.Size = UDim2.fromScale(1, 1)
        tapper.ZIndex = 50
        tapper.Parent = gui
        S.hint = UiKit.label({
            Name = "Hint", Font = "Strong", TextSize = 12, Text = if UiKit.usingTouch() then "TAP TO SKIP" else "CLICK TO SKIP", TextColor3 = C.Muted,
            AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.955), Size = UDim2.fromOffset(200, 16),
            TextXAlignment = Enum.TextXAlignment.Center, TextTransparency = 1, ZIndex = 7, Parent = gui,
        })
        tapper.Activated:Connect(function()
            if os.clock() - S.started >= 0.6 then
                Show.skip(S)
            end
        end)
    end
end

local function makeLighting(S)
    local grade = S.grade
    local grading = Instance.new("ColorCorrectionEffect")
    grading.Name = "BreakthroughGrade"
    grading.Parent = Lighting
    S.grading = grading
    if not S.calm and not S.low and grade.Name ~= "Step" then
        local bloom = Instance.new("BloomEffect")
        bloom.Name = "BreakthroughBloom"
        bloom.Intensity = 0
        bloom.Size = 30
        bloom.Threshold = 0.7
        bloom.Parent = Lighting
        S.bloom = bloom
        local blur = Instance.new("BlurEffect")
        blur.Name = "BreakthroughBlur"
        blur.Size = 0
        blur.Parent = Lighting
        S.blur = blur
    end
end

local function hideHud(S)
    S.hidden = {}
    if not S.grade.Hud then
        return
    end
    local playerGui = player:WaitForChild("PlayerGui")
    for _, name in HUD_GUIS do
        local gui = playerGui:FindFirstChild(name)
        if gui and gui.Enabled then
            gui.Enabled = false
            table.insert(S.hidden, gui)
        end
    end
end

local function showHud(S)
    for _, gui in S.hidden do
        if gui.Parent then
            gui.Enabled = true
        end
    end
    S.hidden = {}
end

-- ---------- the sound, beat by beat ----------
local BREAK_SOUND = { Step = "BtBreakStep", Milestone = "BtBreakMilestone", Realm = "BtBreakRealm", Apex = "BtBreakApex" }

local function startSound(S)
    local fx = S.fx
    local grade = S.grade
    local B, H = fx.B, fx.H
    Sfx.hold(fx.beats.End + 0.3)
    if grade.Name == "Step" then
        Sfx.duck(0.5, B + 1.5)
    else
        Sfx.duck(0.28, fx.beats.End)
        Sfx.play("BtBreath")
    end
    S.sounds = {
        -- the humming swell: begins as the gather does, rises in pitch and level into the held breath
        { time = if grade.Name == "Step" then 0 else 0.3 * B, fn = function()
            local swell = Sfx.play("BtRise")
            if swell then
                S.swell = swell
                swell.PlaybackSpeed = 0.7
                TweenService:Create(swell, TweenInfo.new(math.max(0.5, B - H - 0.3 * B), Enum.EasingStyle.Quad, Enum.EasingDirection.In), { PlaybackSpeed = 1.55 }):Play()
            end
        end },
    }
    if H > 0 then
        table.insert(S.sounds, { time = B - H, fn = function()
            if S.swell then
                Sfx.fadeOut(S.swell, 0.12)
                S.swell = nil
            end
            Sfx.duck(0.03, H + 0.3) -- near silence
        end })
    elseif grade.Name == "Step" then
        table.insert(S.sounds, { time = B - 0.05, fn = function()
            if S.swell then
                Sfx.fadeOut(S.swell, 0.08)
                S.swell = nil
            end
        end })
    end
    table.insert(S.sounds, { time = B, fn = function()
        if S.swell then
            Sfx.fadeOut(S.swell, 0.08)
            S.swell = nil
        end
        Sfx.play(BREAK_SOUND[grade.Name] or "BtBreakStep")
    end })
end

-- ---------- the camera ----------
-- Roblox's own camera script derives each frame's view from the last frame's look direction, so a turn laid over the camera would
-- be turned again every frame. Before it runs, the view is put back to what the script made last time (its position it recomputes).
local function restoreCamera(S)
    local camera = Workspace.CurrentCamera
    if camera and S.baseRotation and camera.CameraType ~= Enum.CameraType.Scriptable then
        camera.CFrame = CFrame.new(camera.CFrame.Position) * S.baseRotation
    end
end

local function stepCamera(S, dt)
    local camera = Workspace.CurrentCamera
    local fx = S.fx
    if not camera or fx.finished then
        return
    end
    local grade = S.grade
    local t, B, H = fx.t, fx.B, fx.H
    local calm = S.calm
    local mild = if calm then 0.4 else 1
    -- the clock after the break runs slow while the particles do (the hit-pause), so the camera's move is slow too
    if fx.broke then
        S.after += dt * math.max(fx.pace, 0.12)
    end
    local after = S.after
    local gather = smooth(ramp(t, 0.08 * B, B - H))
    local hold = if H > 0 then ramp(t, B - H, B) else 0
    local settle = 1 - smooth(ramp(t, fx.settle0, fx.beats.End))

    local push, yaw, pitch, fov
    if not fx.broke then
        push = grade.Dolly * (0.5 * gather + 0.4 * hold)
        yaw = 0
        pitch = 3 * gather
        fov = -grade.Fov * (0.35 * gather + 0.45 * hold)
    else
        push = -grade.Dolly * 1.1 * outCubic(ramp(after, 0.05, 1.1)) * settle
        yaw = grade.Orbit * smooth(ramp(after, 0.1, 4.2)) * settle * (if calm then 0 else 1)
        pitch = 4 * (1 - ramp(after, 0, 2.4)) * settle
        fov = grade.Fov * 0.5 * smooth(ramp(after, 0.05, 0.9)) * settle
    end
    S.push = follow(S.push, push * mild, dt)
    S.yaw = follow(S.yaw, yaw, dt, 4)
    S.pitch = follow(S.pitch, pitch * mild, dt)
    S.fov = follow(S.fov, fov * mild, dt)

    -- impulses: the break's punch in, the beats' small kicks, and the shake
    S.punch *= math.exp(-dt * 7)
    S.shakeAmp *= math.exp(-dt * 5)
    local tremor = if calm then 0 else grade.Shake * 0.07 * gather * gather * (1 + 1.6 * hold)
    local shake = S.shakeAmp + tremor

    -- the shot
    if camera.CameraType == Enum.CameraType.Scriptable then
        return -- (someone else holds the camera: the hatch)
    end
    local cf = camera.CFrame
    S.baseRotation = cf.Rotation
    local focus = fx.chest + Vector3.new(0, 0.6, 0)
    local toCam = cf.Position - focus
    local third = toCam.Magnitude > 2.4
    local rot = CFrame.Angles(0, if third then math.rad(S.yaw) else 0, 0)
    local newCf = CFrame.new(focus + rot:VectorToWorldSpace(toCam)) * (rot * cf.Rotation)
    if third then
        local move = math.clamp(S.push, -grade.Dolly * 1.3, toCam.Magnitude - 2.2) -- closer for positive, never past the head
        local wanted = newCf * Vector3.new(0, 0, -move)
        -- a pull-back stops short of a wall behind the camera
        if move < 0 then
            params.FilterDescendantsInstances = { S.character, S.container }
            local back = wanted - focus
            local hit = Workspace:Raycast(focus, back + back.Unit * 0.6, params)
            if hit then
                wanted = focus + back.Unit * math.max(2.4, (hit.Position - focus).Magnitude - 0.6)
            end
        end
        newCf = CFrame.new(wanted) * newCf.Rotation
    end
    newCf *= CFrame.Angles(math.rad(S.pitch), 0, 0)
    if shake > 0.001 then
        local clock = os.clock()
        newCf *= CFrame.new(
            (math.noise(clock * 31, 0.3) * 2) * shake,
            (math.noise(clock * 29, 7.1) * 2) * shake,
            0
        ) * CFrame.Angles(0, 0, math.rad(math.noise(clock * 23, 3.7) * 2 * shake * 0.8))
    end
    camera.CFrame = newCf
    camera.FieldOfView = S.baseFov + S.fov - S.punch * grade.Fov * mild
end

-- ---------- the screen ----------
local function stepScreen(S, dt)
    local fx = S.fx
    local grade, theme = S.grade, S.theme
    local t, B, H = fx.t, fx.B, fx.H
    local gather = smooth(ramp(t, 0.06 * B, B - H))
    local after = S.after
    local settle = 1 - smooth(ramp(t, fx.settle0, fx.beats.End))

    -- the break: a flash that falls away (a dip into black first in the Void)
    S.flash *= math.exp(-dt * S.flashRate)
    local flashAmount = S.flash
    if S.dip > 0 then
        S.dip = math.max(0, S.dip - dt / 0.14)
        S.flashFrame.BackgroundColor3 = Color3.new(0, 0, 0)
        S.flashFrame.BackgroundTransparency = 1 - 0.95 * S.dip
        if S.dip == 0 then
            S.flashFrame.BackgroundColor3 = theme.Hot:Lerp(Color3.new(1, 1, 1), 0.7)
            S.flash = 1
        end
    else
        S.flashFrame.BackgroundTransparency = 1 - math.min(1, flashAmount) * S.flashPeak
    end

    local vivid = if fx.broke then (1 - smooth(ramp(after, 0.2, 3.5))) * settle else 0
    local dimTarget = if fx.broke then 0 else gather * (1 - 0.35 * (if H > 0 then ramp(t, B - H, B) else 0))
    S.dimNow = follow(S.dimNow, dimTarget, dt, 6)
    local dim = S.dimNow * grade.Dim * (if S.calm then 0.5 else 1)
    local grading = S.grading
    grading.Brightness = -dim * 1.1 + 0.12 * flashAmount * (if S.calm then 0.3 else 1)
    grading.Saturation = -dim * 2.6 + 0.2 * vivid
    grading.Contrast = dim * 0.8 + 0.08 * vivid
    grading.TintColor = Color3.new(1, 1, 1):Lerp(theme.Main:Lerp(Color3.new(1, 1, 1), 0.55), clamp01(dim * 3))
    if S.bloom then
        S.bloom.Intensity = 0.25 * gather * (1 - (if fx.broke then 1 else 0)) + 1.0 * grade.Flash * flashAmount * flashAmount + 0.2 * vivid
        S.blur.Size = 12 * grade.Flash * flashAmount * flashAmount
    end
    -- the edges
    local edge = clamp01(S.dimNow * 0.55 + 0.45 * flashAmount) * (1 - (if fx.broke then 0 else 0))
    for _, frame in S.edges do
        frame.BackgroundTransparency = 1 - 0.5 * edge * (if S.calm then 0.6 else 1)
    end
end

local function bars(S, open, seconds)
    for _, bar in S.bars do
        TweenService:Create(bar, TweenInfo.new(seconds, Enum.EasingStyle.Cubic, Enum.EasingDirection.Out), {
            Size = UDim2.fromScale(1, if open then S.grade.Bars else 0),
        }):Play()
    end
end

-- ---------- the timeline's own beats ----------
local function step(S, dt)
    local fx = S.fx
    if fx.finished then
        return
    end
    local t = fx.t
    for _, event in S.sounds do
        if not event.done and t >= event.time then
            event.done = true
            if not S.skipped then
                event.fn()
            end
        end
    end
    -- the card in and out; the HUD and bars with it
    local beats = fx.beats
    if not S.cardShown and t >= beats.Card and not S.skipped then
        S.cardShown = true
        S.card = Card.new(S.gui, S.info)
        S.card.show()
        if S.hint then
            TweenService:Create(S.hint, TweenInfo.new(0.5), { TextTransparency = 0.25 }):Play()
        end
    end
    if not S.cardGone and t >= beats.Out then
        S.cardGone = true
        if S.card then
            S.card.hide(0.55)
        end
        showHud(S)
        bars(S, false, 0.7)
        if S.hint then
            S.hint.Visible = false
        end
        if S.spec.OnSettle then
            S.spec.OnSettle()
        end
    end
    stepCamera(S, dt)
    stepScreen(S, dt)
end

local function cleanUp(S)
    if S.cleaned then
        return
    end
    S.cleaned = true
    if active == S then
        active = nil
    end
    RunService:UnbindFromRenderStep(RENDER_NAME)
    RunService:UnbindFromRenderStep(RENDER_PRE)
    if S.swell then
        Sfx.fadeOut(S.swell, 0.1)
    end
    showHud(S)
    local camera = Workspace.CurrentCamera
    if camera and camera.CameraType ~= Enum.CameraType.Scriptable then
        camera.FieldOfView = S.baseFov
    end
    for _, effect in { S.grading, S.bloom, S.blur } do
        effect:Destroy()
    end
    if S.card then
        S.card.destroy()
    end
    S.gui:Destroy()
end

-- The field of view the running show started from (nil when none runs): a hatch that takes the camera mid-show saves this, not
-- the show's shifted value, or it put the shift back for the session (bug audit, 2026-11-24)
function Show.baseFov()
    return active and active.baseFov or nil
end

-- ---------- starting ----------
function Show.play(spec)
    if active then
        Show.stop(active)
    end
    local info = spec.Info
    local grade, theme = info.Grade, info.Theme
    local camera = Workspace.CurrentCamera
    local S = {
        spec = spec, info = info, grade = grade, theme = theme, character = spec.Character, container = spec.Container,
        calm = spec.Calm == true, low = spec.Low == true, started = os.clock(),
        baseFov = camera and camera.FieldOfView or 70, after = 0,
        push = 0, yaw = 0, pitch = 0, fov = 0, punch = 0, shakeAmp = 0, dimNow = 0, flash = 0, dip = 0,
        flashPeak = 0.62 * grade.Flash, flashRate = if grade.Name == "Step" then 4.5 else 2.3,
        hidden = {}, sounds = {}, skipped = false,
    }
    if S.calm then
        S.flashPeak *= 0.3
    end
    active = S

    makeGui(S)
    makeLighting(S)
    hideHud(S)
    if grade.Hud then
        Toast.hold(grade.Own.End + 0.4)
    end
    if #S.bars > 0 then
        bars(S, true, 0.9)
    end

    S.fx = Fx.start({
        Parent = spec.Container, Character = spec.Character, Root = spec.Root, Info = info, Own = true, Calm = S.calm, Low = S.low,
        OnBreak = function()
            if spec.OnBreak then
                spec.OnBreak()
            end
        end,
        OnImpact = function()
            S.flash = 1
            if theme.Realm == 9 and not S.calm then
                S.dip = 1 -- the Void swallows the light, then the shock
                S.flash = 0
            end
            S.punch = 0.7
            S.shakeAmp = if S.calm then 0 else grade.Shake
            S.after = 0
        end,
        OnBeat = function(kind, power)
            S.punch = math.max(S.punch, 0.12 * power)
            if not S.calm then
                S.shakeAmp = math.max(S.shakeAmp, 0.06 * power * grade.Shake * 2)
            end
            if kind == "core" then
                Sfx.play("BtBeat", nil, 0.85 + 0.5 * power)
            elseif kind == "bolt" then
                Sfx.play("BtBeat", nil, 1.5 + 0.4 * power)
                S.flash = math.max(S.flash, 0.18 * power)
            end
        end,
        OnDone = function(instant)
            cleanUp(S)
            if spec.OnDone then
                spec.OnDone(instant)
            end
        end,
    })
    startSound(S)
    RunService:BindToRenderStep(RENDER_PRE, Enum.RenderPriority.Camera.Value - 1, function()
        restoreCamera(S)
    end)
    RunService:BindToRenderStep(RENDER_NAME, Enum.RenderPriority.Camera.Value + 2, function(dt)
        step(S, math.min(dt, 0.1) * Fx.TimeScale)
    end)
    return S
end

-- jump to the settle; the title is said in a notice instead of the card
function Show.skip(S)
    if S.skipped or S.cleaned then
        return
    end
    S.skipped = true
    if not S.cardShown then
        Toast.new("BreakthroughSkip", nil, 4):show(
            string.format("You reached %s. %s", S.info.RankName, S.info.Lines[1]), "Success")
    end
    if S.swell then
        Sfx.fadeOut(S.swell, 0.12)
        S.swell = nil
    end
    Fx.skip(S.fx)
end

function Show.stop(S)
    if S.cleaned then
        return
    end
    Fx.stop(S.fx)
    cleanUp(S)
end

return Show

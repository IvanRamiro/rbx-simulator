-- A 45-second cinematic tour of the game for a vertical (9:16) TikTok video (Studio only; never shipped).
--
-- Record with Studio's device emulator on a portrait phone (Test > Device): Roblox keeps the vertical field of view, so every shot is composed
-- for a tall frame (its centre). Run in the Client context during Play. Before it runs, open the Codex (its rail button) on a beast's entry
-- (opened by hand its turntable spins and the portrait has its colours; shown from a script it is a grey still): the tour hides it until the
-- Codex shot. The character is put at AURA_SPOT and cultivates from 9 s (its realm aura up for the aura shot).
--
--    0-12   the main hub: rising up the World Tree's trunk, over the canopy, curving down onto the shop street (Blacksmith, Marketplace, Buy & Sell)
--   12-14   the realm aura, a low push-in
--   14-26   the other islands: out past Jade Grove, then sweeping along Ember Peak, Moonlit Isle and Origin Abyss
--   26-34   the eggs: a slow, shallow-focus glide past Moonlit Isle's three eggs
--   34-40   the Codex: the world softly blurred behind the open entry
--   40-45   the finale: pulling back from the World Tree up into the sky
-- Between shots (never inside one) a short dip to black. At the end it restores the camera, HUD, nameplates and cursor.
--
-- PREVIEW: a number of seconds places the camera at that moment (for framing) and returns; nil plays the tour.
local PREVIEW = nil

-- (Kept in _G so a session can preview frames with _G.TikTokTour(seconds), then _G.tourRestore().)
function _G.TikTokTour(PREVIEW)
    if _G.tourRestore then
        _G.tourRestore()
        _G.tourRestore = nil
    end
    local Players = game:GetService("Players")
    local RunService = game:GetService("RunService")
    local Lighting = game:GetService("Lighting")
    local UserInputService = game:GetService("UserInputService")
    local ReplicatedStorage = game:GetService("ReplicatedStorage")

    local player = Players.LocalPlayer
    local character = player.Character or player.CharacterAdded:Wait()
    local camera = workspace.CurrentCamera
    local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

    local TOTAL = 45
    local LEAD = 2.5 -- seconds on the first frame before it moves (time to start recording)

    -- ---------- helpers ----------
    local function smooth(t)
        t = math.clamp(t, 0, 1)
        return t * t * (3 - 2 * t)
    end

    local function smoother(t) -- eases in and out more gently: a camera operator's move
        t = math.clamp(t, 0, 1)
        return t * t * t * (t * (6 * t - 15) + 10)
    end

    local function lerp(a, b, t)
        return a + (b - a) * t
    end

    -- a Catmull-Rom curve through points, at s (0..1) along it
    local function spline(points, s)
        local n = #points
        local x = math.clamp(s, 0, 1) * (n - 1)
        local i = math.min(math.floor(x), n - 2)
        local t = x - i
        local p0, p1, p2, p3 = points[math.max(i, 1)], points[i + 1], points[i + 2], points[math.min(i + 3, n)]
        local t2, t3 = t * t, t * t * t
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
    end

    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { character }
    local function groundAt(x, z)
        local hit = workspace:Raycast(Vector3.new(x, 500, z), Vector3.new(0, -600, 0), params)
        return if hit then hit.Position.Y else 202
    end

    -- ---------- where things are ----------
    local AURA_SPOT = Vector3.new(150, 0, 40) -- the east lawn, the World Tree behind it from the camera
    local auraY = groundAt(AURA_SPOT.X, AURA_SPOT.Z)
    local me = Vector3.new(AURA_SPOT.X, auraY + 3, AURA_SPOT.Z)
    local toTree = (Vector3.new(0, me.Y, 0) - me).Unit
    local ALTAR = Vector3.new(100, 206, -130)
    local EGGS = { Vector3.new(179.6, 207.2, -818.4), Vector3.new(199.8, 207.2, -820), Vector3.new(216.6, 207.2, -808.9) } -- Moonlit Isle's eggs

    -- ---------- the shots: each returns the camera CFrame, its field of view, and its look (blur, focus) at local time u (0..1) ----------
    local shots = {
        { length = 12, name = "hub", fn = function(u)
            -- up the trunk on its north-west side, out over the canopy, round and down to the Hatching Altar
            local s = smoother(u)
            -- (ending at the Hatching Altar, a pine stood in front of it and it was small in frame, seen in Play)
            local pos = spline({
                Vector3.new(-70, 207, 95), Vector3.new(-82, 250, 105), Vector3.new(-95, 315, 110), Vector3.new(-90, 420, 150),
                Vector3.new(-175, 400, 95), Vector3.new(-160, 310, 45), Vector3.new(-90, 245, 25), Vector3.new(-60, 228, 20),
            }, s)
            local look = spline({
                Vector3.new(0, 240, 0), Vector3.new(0, 275, 0), Vector3.new(0, 320, 0), Vector3.new(0, 370, 0),
                Vector3.new(-40, 330, 0), Vector3.new(-150, 230, -20), Vector3.new(-160, 215, -25), Vector3.new(-150, 212, -20),
            }, s)
            return CFrame.lookAt(pos, look), lerp(62, 50, s)
        end },
        { length = 2, name = "aura", fn = function(u)
            local s = smoother(u)
            local side = toTree:Cross(Vector3.yAxis)
            -- wide: the aura, the pets and the World Tree behind (at 12-17 studs the character filled the frame)
            local pos = me - toTree * lerp(26, 21, s) + side * lerp(7, 6, s) + Vector3.new(0, lerp(2.5, 3.2, s), 0)
            return CFrame.lookAt(pos, me + Vector3.new(0, 4.5, 0)), 50
        end },
        { length = 12, name = "islands", fn = function(u)
            local s = smoother(u)
            local pos = spline({
                Vector3.new(-170, 330, -170), Vector3.new(-290, 305, -360), Vector3.new(-270, 295, -560),
                Vector3.new(-60, 300, -600), Vector3.new(170, 310, -640), Vector3.new(360, 330, -690),
            }, s)
            local look = spline({
                Vector3.new(-394, 200, -457), Vector3.new(-394, 195, -470), Vector3.new(-132, 195, -697),
                Vector3.new(80, 200, -760), Vector3.new(300, 210, -820), Vector3.new(594, 240, -863),
            }, s)
            return CFrame.lookAt(pos, look), 60
        end },
        { length = 8, name = "eggs", fn = function(u)
            -- a slow glide past the three eggs at their height, the camera turning to keep the middle one
            local s = smoother(u)
            local centre = (EGGS[1] + EGGS[2] + EGGS[3]) / 3
            local pos = spline({
                centre + Vector3.new(-22, 2.2, 13), centre + Vector3.new(-9, 1.6, 15), centre + Vector3.new(6, 1.4, 15), centre + Vector3.new(19, 2, 10),
            }, s)
            local look = spline({ EGGS[1], EGGS[1], EGGS[2], EGGS[3], EGGS[3] }, s) -- each egg in turn in focus
            return CFrame.lookAt(pos, look), 36, { focus = (look - pos).Magnitude }
        end },
        { length = 6, name = "codex", fn = function(u)
            local s = smoother(u)
            local pos = lerp(Vector3.new(170, 250, 160), Vector3.new(150, 262, 190), s)
            return CFrame.lookAt(pos, Vector3.new(0, 300, 0)), 55, { blur = 16, codex = true }
        end },
        { length = 5, name = "finale", fn = function(u)
            local s = smoother(u)
            local pos = spline({ Vector3.new(90, 300, 150), Vector3.new(120, 400, 300), Vector3.new(60, 560, 470) }, s)
            local look = lerp(Vector3.new(0, 320, 0), Vector3.new(0, 250, -150), s)
            return CFrame.lookAt(pos, look), lerp(55, 68, s)
        end },
    }

    local function shotAt(t)
        local start = 0
        for index, shot in shots do
            if t < start + shot.length or index == #shots then
                local u = math.clamp((t - start) / shot.length, 0, 1)
                local cf, fov, look = shot.fn(u)
                -- a dip to black at each cut: out over the last 0.18 s of a shot, in over the first 0.18 s of the next
                local dip = 0
                if index > 1 then
                    dip = math.max(dip, 1 - smooth((t - start) / 0.18))
                end
                if index < #shots then
                    dip = math.max(dip, smooth((t - (start + shot.length - 0.18)) / 0.18))
                end
                return cf, fov, look or {}, dip
            end
            start += shot.length
        end
    end

    -- ---------- the stage ----------
    local hidden = {}
    local function hide(instance)
        if instance.Enabled then
            instance.Enabled = false
            table.insert(hidden, instance)
        end
    end
    local windows = player.PlayerGui:FindFirstChild("HudWindows")
    for _, g in player.PlayerGui:GetChildren() do
        if g:IsA("ScreenGui") then
            hide(g)
        end
    end
    for _, container in { player.PlayerGui, workspace } do
        for _, d in container:GetDescendants() do
            if d:IsA("BillboardGui") then
                hide(d)
            end
        end
    end

    local fade = Instance.new("ScreenGui")
    fade.Name = "TourFade"
    fade.IgnoreGuiInset = true
    fade.DisplayOrder = 1000
    local black = Instance.new("Frame")
    black.Size = UDim2.fromScale(1, 1)
    black.BackgroundColor3 = Color3.new(0, 0, 0)
    black.BackgroundTransparency = 1
    black.BorderSizePixel = 0
    black.Parent = fade
    fade.Parent = player.PlayerGui

    local grade = Instance.new("ColorCorrectionEffect")
    grade.Name = "TourGrade"
    grade.Contrast = 0.08
    grade.Saturation = 0.12
    grade.TintColor = Color3.fromRGB(255, 248, 238)
    grade.Parent = Lighting
    local blur = Instance.new("BlurEffect")
    blur.Name = "TourBlur"
    blur.Size = 0
    blur.Parent = Lighting
    local dof = Instance.new("DepthOfFieldEffect")
    dof.Name = "TourFocus"
    dof.Enabled = false
    dof.FarIntensity = 0.6
    dof.NearIntensity = 0.3
    dof.InFocusRadius = 6
    dof.Parent = Lighting
    local oldFov = camera.FieldOfView
    local mouseShown = UserInputService.MouseIconEnabled
    UserInputService.MouseIconEnabled = false

    local function apply(t)
        local cf, fov, look, dip = shotAt(t)
        camera.CameraType = Enum.CameraType.Scriptable
        camera.CFrame = cf
        camera.FieldOfView = fov
        black.BackgroundTransparency = 1 - dip
        blur.Size = look.blur or 0
        dof.Enabled = look.focus ~= nil
        if look.focus then
            dof.FocusDistance = look.focus
        end
        if windows then
            windows.Enabled = look.codex == true
        end
    end

    local function restore()
        RunService:UnbindFromRenderStep("TikTokTour")
        for _, instance in hidden do
            if instance.Parent then
                instance.Enabled = true
            end
        end
        if windows then
            windows.Enabled = true
        end
        fade:Destroy()
        grade:Destroy()
        blur:Destroy()
        dof:Destroy()
        camera.FieldOfView = oldFov
        camera.CameraType = Enum.CameraType.Custom
        UserInputService.MouseIconEnabled = mouseShown
    end

    if PREVIEW then
        character:PivotTo(CFrame.lookAt(me, me + toTree))
        RunService:BindToRenderStep("TikTokTour", Enum.RenderPriority.Camera.Value + 10, function()
            apply(PREVIEW) -- (held every frame: a run from the command bar hands the camera back when it ends)
        end)
        _G.tourRestore = restore -- (call it when done looking; a later preview calls it first)
        return
    end

    character:PivotTo(CFrame.lookAt(me, me + toTree))
    apply(0)
    task.wait(LEAD)
    local started = os.clock()
    local cultivating = false
    RunService:BindToRenderStep("TikTokTour", Enum.RenderPriority.Camera.Value + 10, function()
        local t = os.clock() - started
        if not cultivating and t > 9 then -- its realm aura up in time for the aura shot (12 s)
            cultivating = true
            RemoteEvents.CultivationEvent:FireServer(true)
        end
        apply(math.min(t, TOTAL))
    end)
    task.wait(TOTAL + 0.2)
    RemoteEvents.CultivationEvent:FireServer(false)
    restore()
    print("TikTok tour finished (" .. TOTAL .. " s)")
end

_G.TikTokTour(PREVIEW)

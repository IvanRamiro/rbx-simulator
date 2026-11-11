-- A 44-second camera tour of the game for recording a video (Studio only; never shipped).
--
-- How to use:
--   1. Press Play in Studio. Equip up to three pets if you want them in the shot.
--   2. Start your screen recorder.
--   3. In the command bar, switch the context to Client (the dropdown next to it), paste this
--      whole file and press Enter. A 3-second pause, then the tour plays and hands the camera back.
--
-- What it does: hides the HUD and nameplates, moves your character to an open spot by the tree and starts
-- meditating (so the realm aura and the pets show), then flies the camera through eight shots:
--    0-6     high orbit over Yggdrasil and its bridges
--    6-11    swoop down the World Tree to you
--   11-18    orbit you in your realm aura
--   18-23    low angle on the pets circling you
--   23-28.5  glide past the Hatching Altar to the shops
--   28.5-34.5 fly the Ember bridge toward Ember Peak
--   34.5-40  circle the Ember Xuanwu
--   40-44    pull up to all the floating islands
-- At the end it stops meditating and restores the camera, HUD and nameplates.
--
-- PREVIEW: set to a number of seconds to just place the camera at that moment (for checking
-- framing), or leave nil to play the whole tour.
local PREVIEW = nil

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()
local root = character:WaitForChild("HumanoidRootPart")
local camera = workspace.CurrentCamera
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local TOTAL = 44
local COURT = Vector3.new(75, 0, 130) -- an open spot north-east of the tree (a clear 20-stud orbit), where you meditate

-- ---------- helpers ----------
local function smooth(t)
    t = math.clamp(t, 0, 1)
    return t * t * (3 - 2 * t)
end

local function lerp(a, b, t)
    return a + (b - a) * t
end

local function bezier(a, b, c, t) -- a quadratic curve from a to c, bent toward b
    return lerp(lerp(a, b, t), lerp(b, c, t), t)
end

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.FilterDescendantsInstances = { character }
local function groundAt(x, z)
    local hit = workspace:Raycast(Vector3.new(x, 400, z), Vector3.new(0, -500, 0), params)
    return if hit then hit.Position.Y else 202
end

local function guardianCentre()
    local folder = workspace:FindFirstChild("Guardians")
    local model = folder and folder:FindFirstChild("EmberXuanwu")
    if model then
        local cf, size = model:GetBoundingBox()
        return cf.Position, math.max(size.X, size.Z)
    end
    return Vector3.new(-132, 210, -700), 30 -- Ember Peak, if the guardian isn't out
end

-- ---------- the shots: each returns the camera at local time u (0..1) ----------
local TREE = Vector3.new(0, 255, 0)
local courtY = groundAt(COURT.X, COURT.Z)
local me = Vector3.new(COURT.X, courtY + 3, COURT.Z)
local facing = (Vector3.new(0, me.Y, 0) - me).Unit -- you face the tree; the swoop lands behind you, the tree ahead
local gPos, gSize = guardianCentre()

local shots = {
    { length = 6, fn = function(u) -- high orbit
        local a = math.rad(lerp(35, 115, smooth(u)))
        local r, h = lerp(320, 270, u), lerp(340, 300, u)
        return CFrame.lookAt(Vector3.new(math.cos(a) * r, h, math.sin(a) * r), TREE + Vector3.new(0, lerp(10, 0, u), 0))
    end },
    { length = 5, fn = function(u) -- swoop down the tree to you
        local a = math.rad(115)
        local from = Vector3.new(math.cos(a) * 270, 300, math.sin(a) * 270)
        local to = me - facing * 22 + Vector3.new(0, 6, 0)
        local s = smooth(u)
        local pos = bezier(from, Vector3.new(-20, 270, 235), to, s) -- round the north side, clear of the trunk
        return CFrame.lookAt(pos, lerp(TREE, me + Vector3.new(0, 3, 0), smooth((u - 0.3) / 0.7)))
    end },
    { length = 7, fn = function(u) -- orbit you in your aura
        local base = math.atan2(-facing.Z, -facing.X)
        local a = base + math.rad(lerp(0, 300, smooth(u)))
        local r, h = lerp(22, 18, u), lerp(6, 4.5, u)
        local centre = root.Position -- the high realms' poses float the body ~2 studs over the root
        return CFrame.lookAt(centre + Vector3.new(math.cos(a) * r, h, math.sin(a) * r), centre + Vector3.new(0, 3, 0))
    end },
    { length = 5, fn = function(u) -- low angle on the pets
        local base = math.atan2(-facing.Z, -facing.X) + math.rad(300)
        local a = base + math.rad(lerp(0, -70, smooth(u)))
        local centre = root.Position
        return CFrame.lookAt(centre + Vector3.new(math.cos(a) * 14, 1.2, math.sin(a) * 14), centre + Vector3.new(0, 3, 0))
    end },
    { length = 5.5, fn = function(u) -- the Hatching Altar, then the shops
        local s = smooth(u)
        local pos = bezier(Vector3.new(135, 214, -165), Vector3.new(10, 232, -175), Vector3.new(-95, 220, -75), s)
        local look = lerp(Vector3.new(101, 206, -130), Vector3.new(-140, 212, -85), smooth((u - 0.25) / 0.6))
        return CFrame.lookAt(pos, look)
    end },
    { length = 6, fn = function(u) -- the Ember bridge
        local s = smooth(u)
        local pos = lerp(Vector3.new(-12, 222, -225), Vector3.new(-95, 228, -560), s)
        return CFrame.lookAt(pos, lerp(Vector3.new(-60, 205, -420), Vector3.new(-132, 200, -690), s))
    end },
    { length = 5.5, fn = function(u) -- circle the Ember Xuanwu
        local a = math.rad(lerp(60, 160, smooth(u)))
        local r = gSize * 1.15 + 14
        return CFrame.lookAt(gPos + Vector3.new(math.cos(a) * r, gSize * 0.35 + 6, math.sin(a) * r), gPos + Vector3.new(0, gSize * 0.15, 0))
    end },
    { length = 4, fn = function(u) -- pull up to all the islands
        local a = math.rad(160)
        local r = gSize * 1.15 + 14
        local from = gPos + Vector3.new(math.cos(a) * r, gSize * 0.35 + 6, math.sin(a) * r)
        local s = smooth(u)
        local pos = lerp(from, Vector3.new(-20, 560, 40), s)
        return CFrame.lookAt(pos, lerp(gPos, Vector3.new(60, 200, -420), s))
    end },
}

local function frameAt(t)
    local start = 0
    for _, shot in shots do
        if t < start + shot.length or shot == shots[#shots] then
            return shot.fn(math.clamp((t - start) / shot.length, 0, 1))
        end
        start += shot.length
    end
end

-- ---------- set the stage ----------
local hidden = {}
local function hideUi()
    for _, g in player.PlayerGui:GetChildren() do
        if g:IsA("ScreenGui") and g.Enabled then
            g.Enabled = false
            table.insert(hidden, g)
        end
    end
    for _, container in { player.PlayerGui, workspace } do -- nameplates live in both
        for _, d in container:GetDescendants() do
            if d:IsA("BillboardGui") and d.Enabled then
                d.Enabled = false
                table.insert(hidden, d)
            end
        end
    end
end
local function restoreUi()
    for _, g in hidden do
        if g.Parent then
            g.Enabled = true
        end
    end
end

camera.CameraType = Enum.CameraType.Scriptable
if PREVIEW then
    camera.CFrame = frameAt(PREVIEW)
    return
end

hideUi()
character:PivotTo(CFrame.lookAt(me, me + facing))
camera.CFrame = frameAt(0)
task.wait(3)

local started = os.clock()
local cultivating = false
RunService:BindToRenderStep("TrailerTour", Enum.RenderPriority.Camera.Value + 10, function()
    local t = os.clock() - started
    if not cultivating and t > 3 then -- in time for the aura to build before the swoop reaches you
        cultivating = true
        RemoteEvents.CultivationEvent:FireServer(true)
    end
    camera.CameraType = Enum.CameraType.Scriptable
    camera.CFrame = frameAt(math.min(t, TOTAL))
end)
task.wait(TOTAL + 0.5)
RunService:UnbindFromRenderStep("TrailerTour")
RemoteEvents.CultivationEvent:FireServer(false)
camera.CameraType = Enum.CameraType.Custom
restoreUi()
print("Trailer tour finished (" .. TOTAL .. " s)")

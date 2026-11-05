-- What the HUD knows about the screen, so each piece can change its layout for a screen's size instead of the whole
-- interface only shrinking:
--   HudMetrics.class()      "Phone" (a short screen, under 500 px on its shorter side), "Tablet" (under 800) or "Desktop"
--   HudMetrics.viewport()   the screen's size
--   HudMetrics.scale()      the scale for a piece: never below 0.8, growing on big screens so the HUD keeps its share of them
--   HudMetrics.Changed      fires when the screen's size changes
--   HudMetrics.keepReadable(gui)  no text under gui is ever drawn smaller than MIN_DRAWN_TEXT, however the scale shrinks it
-- In Studio, the player's HudTestViewport attribute (a Vector2) stands in for the screen, to check a layout at another size.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local PHONE_BELOW, TABLET_BELOW = 500, 800 -- px on the screen's shorter side
local SMALL_REFERENCE = 600  -- the shorter side at which the scale is 1
local LARGE_REFERENCE = 800  -- past this the HUD grows with the screen ...
local MIN_SCALE, MAX_SCALE = 0.8, 1.6 -- ... up to here
local MIN_DRAWN_TEXT = 10    -- px on the screen

local changed = Instance.new("BindableEvent")
local HudMetrics = { Changed = changed.Event }

local player = Players.LocalPlayer
local IN_STUDIO = RunService:IsStudio()

function HudMetrics.viewport()
    if IN_STUDIO then
        local test = player:GetAttribute("HudTestViewport")
        if typeof(test) == "Vector2" then
            return test
        end
    end
    local camera = workspace.CurrentCamera
    return if camera then camera.ViewportSize else Vector2.new(1280, 720)
end

function HudMetrics.class()
    local view = HudMetrics.viewport()
    local short = math.min(view.X, view.Y)
    return if short < PHONE_BELOW then "Phone" elseif short < TABLET_BELOW then "Tablet" else "Desktop"
end

function HudMetrics.scale()
    local view = HudMetrics.viewport()
    local short = math.min(view.X, view.Y)
    local scale = if short > LARGE_REFERENCE then short / LARGE_REFERENCE else short / SMALL_REFERENCE
    return math.clamp(scale, MIN_SCALE, MAX_SCALE)
end

-- ---------- readable text ----------
local function floorFor(scale)
    return math.ceil(MIN_DRAWN_TEXT / scale)
end

local authored = setmetatable({}, { __mode = "k" }) -- [label] = the TextSize its script asked for
local applying = false

local function fitText(label)
    local wanted = authored[label]
    if wanted and not label.TextScaled then
        applying = true
        label.TextSize = math.max(wanted, floorFor(HudMetrics.scale()))
        applying = false
    end
end

local function track(item)
    if not (item:IsA("TextLabel") or item:IsA("TextButton") or item:IsA("TextBox")) or authored[item] then
        return
    end
    authored[item] = item.TextSize
    fitText(item)
    item:GetPropertyChangedSignal("TextSize"):Connect(function()
        if not applying then -- its script chose a new size
            authored[item] = item.TextSize
            fitText(item)
        end
    end)
end

local watchedGuis = {}
function HudMetrics.keepReadable(gui)
    table.insert(watchedGuis, gui)
    for _, item in gui:GetDescendants() do
        track(item)
    end
    gui.DescendantAdded:Connect(track)
end

-- ---------- following the screen ----------
local function refresh()
    for label in authored do
        if label.Parent then
            fitText(label)
        end
    end
    changed:Fire()
end

local viewportChanged
local function watchCamera()
    if viewportChanged then
        viewportChanged:Disconnect()
    end
    local camera = workspace.CurrentCamera
    viewportChanged = camera and camera:GetPropertyChangedSignal("ViewportSize"):Connect(refresh)
    refresh()
end
workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(watchCamera)
player:GetAttributeChangedSignal("HudTestViewport"):Connect(refresh)
watchCamera()

return HudMetrics

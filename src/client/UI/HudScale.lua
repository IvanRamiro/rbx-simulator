-- Scales a HUD element with the screen: full size from 600 px on the shorter side, never below
-- 80% (smaller made a phone's text unreadable: 11 px became 7). fitHeight (optional): never so
-- tall that the element's height doesn't fit the screen under the top bar, with a margin (a window
-- on a phone). Follows the current camera, which Roblox may replace.
local GuiService = game:GetService("GuiService")

local REFERENCE_SIZE = 600
local MIN_SCALE = 0.8
local FIT_MARGIN = 24

local function applyHudScale(guiObject, fitHeight)
    local uiScale = Instance.new("UIScale")
    uiScale.Parent = guiObject

    local function updateScale()
        local camera = workspace.CurrentCamera
        if camera then
            local view = camera.ViewportSize
            local scale = math.clamp(math.min(view.X, view.Y) / REFERENCE_SIZE, MIN_SCALE, 1)
            if fitHeight then
                local room = view.Y - GuiService:GetGuiInset().Y - FIT_MARGIN
                scale = math.min(scale, room / fitHeight)
            end
            uiScale.Scale = scale
        end
    end

    local viewportChanged
    local function watchCamera()
        if viewportChanged then
            viewportChanged:Disconnect()
        end
        local camera = workspace.CurrentCamera
        viewportChanged = camera and camera:GetPropertyChangedSignal("ViewportSize"):Connect(updateScale)
        updateScale()
    end

    workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(watchCamera)
    watchCamera()
end

return applyHudScale

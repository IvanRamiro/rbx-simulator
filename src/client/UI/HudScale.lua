-- Scales a HUD element with the screen: full size from 600 px on the shorter side, never
-- below 60%. Follows the current camera, which Roblox may replace.
local REFERENCE_SIZE = 600
local MIN_SCALE = 0.6

local function applyHudScale(guiObject)
    local uiScale = Instance.new("UIScale")
    uiScale.Parent = guiObject

    local function updateScale()
        local camera = workspace.CurrentCamera
        if camera then
            local shorterSide = math.min(camera.ViewportSize.X, camera.ViewportSize.Y)
            uiScale.Scale = math.clamp(shorterSide / REFERENCE_SIZE, MIN_SCALE, 1)
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


-- Shrinks a HUD panel on small screens (like phones) so panels don't overlap.
-- Panels are full size when the screen's shorter side is at least REFERENCE_SIZE pixels.

local REFERENCE_SIZE = 600
local MIN_SCALE = 0.6

local function applyHudScale(guiObject)
    local camera = workspace.CurrentCamera

    local uiScale = Instance.new("UIScale")
    uiScale.Parent = guiObject

    local function updateScale()
        local shorterSide = math.min(camera.ViewportSize.X, camera.ViewportSize.Y)
        uiScale.Scale = math.clamp(shorterSide / REFERENCE_SIZE, MIN_SCALE, 1)
    end

    camera:GetPropertyChangedSignal("ViewportSize"):Connect(updateScale)
    updateScale()
end

return applyHudScale

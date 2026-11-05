-- Scales a HUD element with the screen (HudMetrics.scale).
local HudMetrics = require(script.Parent:WaitForChild("HudMetrics"))

local function applyHudScale(guiObject)
    local uiScale = Instance.new("UIScale")
    uiScale.Parent = guiObject

    local function updateScale()
        uiScale.Scale = HudMetrics.scale()
    end
    HudMetrics.Changed:Connect(updateScale)
    updateScale()
end

return applyHudScale

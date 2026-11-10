-- Scales a HUD element with the screen (HudMetrics.scale). The link lasts as long as the element: it's dropped when the
-- element is destroyed, so short-lived UI (the hatch cinematic's cards and banners) leaves nothing connected behind.
local HudMetrics = require(script.Parent:WaitForChild("HudMetrics"))

local function applyHudScale(guiObject)
    local uiScale = Instance.new("UIScale")
    uiScale.Parent = guiObject

    local function updateScale()
        uiScale.Scale = HudMetrics.scale()
    end
    local connection = HudMetrics.Changed:Connect(updateScale)
    guiObject.Destroying:Once(function()
        connection:Disconnect()
    end)
    updateScale()
end

return applyHudScale

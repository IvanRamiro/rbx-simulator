-- A message banner across the top of the HUD. It hides itself after a few seconds, and a newer
-- message replaces the one showing.
local applyHudScale = require(script.Parent:WaitForChild("HudScale"))

local Toast = {}
Toast.__index = Toast

function Toast.new(parent, name, top, textColor, seconds)
    local label = Instance.new("TextLabel")
    label.Name = name
    label.AnchorPoint = Vector2.new(0.5, 0)
    label.Position = UDim2.new(0.5, 0, 0, top)
    label.Size = UDim2.fromOffset(380, 44)
    label.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
    label.BackgroundTransparency = 0.25
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.TextColor3 = textColor
    label.Visible = false
    label.Parent = parent
    applyHudScale(label)

    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 10)
    corner.Parent = label

    local padding = Instance.new("UIPadding")
    padding.PaddingLeft = UDim.new(0, 10)
    padding.PaddingRight = UDim.new(0, 10)
    padding.PaddingTop = UDim.new(0, 6)
    padding.PaddingBottom = UDim.new(0, 6)
    padding.Parent = label

    return setmetatable({ label = label, seconds = seconds, shown = 0 }, Toast)
end

function Toast:show(text, color)
    self.shown += 1
    local this = self.shown
    self.label.Text = text
    if color then
        self.label.TextColor3 = color
    end
    self.label.Visible = true

    task.delay(self.seconds, function()
        if self.shown == this then
            self.label.Visible = false
        end
    end)
end

return Toast

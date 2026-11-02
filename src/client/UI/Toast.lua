-- A message banner at the top of the screen (the HUD's Banner region, where every Toast stacks,
-- so two never overlap). It fades in, hides itself after a few seconds, and a newer message
-- replaces the one showing. Toast.new(_, name, _, textColor, seconds): the first and third
-- arguments (a parent and a height) are kept for the callers but no longer used.
local TweenService = game:GetService("TweenService")

local Hud = require(script.Parent:WaitForChild("Hud"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local Toast = {}
Toast.__index = Toast

local FADE = TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local created = 0

function Toast.new(_, name, _, textColor, seconds)
    created += 1
    local label = UiKit.label({
        Name = name, Font = "Strong", TextSize = 17, TextColor3 = textColor, TextWrapped = true,
        TextXAlignment = Enum.TextXAlignment.Center, BackgroundTransparency = UiTheme.PanelTransparency,
        BackgroundColor3 = UiTheme.Colors.Ink, AutomaticSize = Enum.AutomaticSize.XY, Size = UDim2.new(),
        LayoutOrder = created, Visible = false, Parent = Hud.Banner,
    })
    local limit = Instance.new("UISizeConstraint")
    limit.MaxSize = Vector2.new(520, math.huge)
    limit.Parent = label
    UiKit.corner(label)
    local edge = UiKit.stroke(label, UiTheme.Colors.Gold, 0.4)
    UiKit.padding(label, 18, 9)
    return setmetatable({ label = label, edge = edge, seconds = seconds, shown = 0 }, Toast)
end

function Toast:show(text, color)
    self.shown += 1
    local this = self.shown
    local label = self.label
    label.Text = text
    if color then
        label.TextColor3 = color
    end
    if not label.Visible then
        label.TextTransparency, label.BackgroundTransparency, self.edge.Transparency = 1, 1, 1
        label.Visible = true
    end
    TweenService:Create(label, FADE, { TextTransparency = 0, BackgroundTransparency = UiTheme.PanelTransparency }):Play()
    TweenService:Create(self.edge, FADE, { Transparency = 0.4 }):Play()

    task.delay(self.seconds, function()
        if self.shown ~= this then
            return
        end
        TweenService:Create(label, FADE, { TextTransparency = 1, BackgroundTransparency = 1 }):Play()
        TweenService:Create(self.edge, FADE, { Transparency = 1 }):Play()
        task.delay(FADE.Time, function()
            if self.shown == this then
                label.Visible = false
            end
        end)
    end)
end

return Toast

-- A System notification at the top of the screen: a small window headed [ NOTIFICATION ] with
-- the message under it, in the HUD's Banner region where every Toast stacks (two never overlap).
-- It fades in, hides itself after a few seconds, and a newer message replaces the one showing.
-- Toast.new(name, textColor, seconds), then :show(text, color).
local TweenService = game:GetService("TweenService")

local Hud = require(script.Parent:WaitForChild("Hud"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local Toast = {}
Toast.__index = Toast

local FADE = TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local WIDTH = if Hud.isCompact() then 262 else 420 -- fits between the STATUS and QUEST windows
local created = 0

function Toast.new(name, textColor, seconds)
    created += 1
    -- a CanvasGroup fades the whole window at once; its padding keeps the glow and ticks inside it
    local group = Instance.new("CanvasGroup")
    group.Name = name
    group.BackgroundTransparency = 1
    group.AutomaticSize = Enum.AutomaticSize.Y
    group.Size = UDim2.fromOffset(WIDTH + 6, 0)
    group.LayoutOrder = created
    group.Visible = false
    group.Parent = Hud.Banner
    UiKit.padding(group, 3, 3)

    local window = UiKit.panel({ Name = "Window", AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0), Parent = group })
    local inner = Instance.new("Frame")
    inner.Name = "Inner"
    inner.BackgroundTransparency = 1
    inner.AutomaticSize = Enum.AutomaticSize.Y
    inner.Size = UDim2.new(1, 0, 0, 0)
    inner.Parent = window
    UiKit.padding(inner, 16, 9)
    UiKit.list(inner, { Padding = UDim.new(0, 5), HorizontalAlignment = Enum.HorizontalAlignment.Center })
    UiKit.header(inner, "NOTIFICATION", { TextSize = 11, Color = UiTheme.Colors.Muted, LayoutOrder = 1 })
    local label = UiKit.label({
        Name = "Message", Font = "Strong", TextSize = 16, TextColor3 = textColor, TextWrapped = true,
        TextXAlignment = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.Y,
        Size = UDim2.new(1, 0, 0, 0), LayoutOrder = 2, Parent = inner,
    })
    return setmetatable({ group = group, label = label, seconds = seconds, shown = 0 }, Toast)
end

function Toast:show(text, color)
    self.shown += 1
    local this = self.shown
    local group = self.group
    self.label.Text = text
    if color then
        self.label.TextColor3 = color
    end
    if not group.Visible then
        group.GroupTransparency = 1
        group.Visible = true
    end
    TweenService:Create(group, FADE, { GroupTransparency = 0 }):Play()

    task.delay(self.seconds, function()
        if self.shown ~= this then
            return
        end
        TweenService:Create(group, FADE, { GroupTransparency = 1 }):Play()
        task.delay(FADE.Time, function()
            if self.shown == this then
                group.Visible = false
            end
        end)
    end)
end

return Toast

-- A notification at the top of the screen: a small window headed NOTIFICATION with
-- the message under it, in the HUD's Banner region where every Toast stacks (two never overlap).
-- It fades in, hides itself after a few seconds, and a newer message replaces the one showing.
-- Toast.new(name, textColor, seconds), then :show(text, color).
-- Toast.setSingle(on): while on (a guardian fight, GuardianController), only one notification shows at a time: a new one
-- puts away any other (the owner, 2026-11-11: "don't make 2 notification at once when fighting a boss").
-- Toast.showing(): whether any notification is on the screen.
local TweenService = game:GetService("TweenService")

local Hud = require(script.Parent:WaitForChild("Hud"))
local UiFx = require(script.Parent:WaitForChild("UiFx"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local Toast = {}
Toast.__index = Toast

local FADE = TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local function width() -- fits between the profile and the QUEST panel
    return if Hud.isCompact() then 334 else 420
end
local created = 0
local all = {} -- every Toast, to keep to one at a time while single
local single = false

function Toast.new(name, textColor, seconds)
    created += 1
    -- a CanvasGroup fades the whole window at once; its padding keeps the glow and ticks inside it
    local group = Instance.new("CanvasGroup")
    group.Name = name
    group.BackgroundTransparency = 1
    group.AutomaticSize = Enum.AutomaticSize.Y
    group.Size = UDim2.fromOffset(width() + 6, 0)
    Hud.CompactChanged:Connect(function()
        group.Size = UDim2.fromOffset(width() + 6, 0)
    end)
    group.LayoutOrder = created
    group.Visible = false
    group.Parent = Hud.Banner
    UiKit.padding(group, 3, 3)

    local window = UiKit.panel({ Name = "Window", Brackets = false, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0), Parent = group })
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
    local toast = setmetatable({ group = group, label = label, seconds = seconds, shown = 0, at = 0 }, Toast)
    table.insert(all, toast)
    return toast
end

-- fades this one out now
function Toast:hide()
    self.shown += 1
    local this = self.shown
    local group = self.group
    if not group.Visible then
        return
    end
    TweenService:Create(group, FADE, { GroupTransparency = 1 }):Play()
    task.delay(FADE.Time, function()
        if self.shown == this then
            group.Visible = false
        end
    end)
end

function Toast.showing()
    for _, toast in all do
        if toast.group.Visible and toast.group.GroupTransparency < 1 then
            return true
        end
    end
    return false
end

-- one at a time from now on (on), or as many as there are (off); turning it on keeps only the newest showing
function Toast.setSingle(on)
    if on == single then
        return
    end
    single = on
    if on then
        local newest = nil
        for _, toast in all do
            if toast.group.Visible and (not newest or toast.at > newest.at) then
                newest = toast
            end
        end
        for _, toast in all do
            if toast ~= newest and toast.group.Visible then
                toast:hide()
            end
        end
    end
end

function Toast:show(text, color)
    if single then
        for _, other in all do
            if other ~= self and other.group.Visible then
                other:hide()
            end
        end
    end
    self.at = os.clock()
    self.shown += 1
    local this = self.shown
    local group = self.group
    self.label.Text = text
    UiFx.typeIn(self.label, 0.22)
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

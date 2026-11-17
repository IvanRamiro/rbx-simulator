-- The last question before something that can't be undone: a dimmed screen, a panel, and a button that only
-- wakes after a few seconds, so nothing is lost to a quick tap or a double click.
--   ConfirmDialog.show({ Title, Text, Picture, ConfirmText, Seconds, OnConfirm })
-- Picture (optional) is a GuiObject of up to 72 px, such as a portrait. Only one shows at a time.
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")

local UI = script.Parent
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local HudMetrics = require(UI:WaitForChild("HudMetrics"))
local Sfx = require(UI.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local PANEL_SIZE = Vector2.new(400, 244)
local PAD = UiTheme.Pad.Window
local TOP = UiTheme.Height.TitleBar + UiTheme.Space.M

local gui = Instance.new("ScreenGui")
gui.Name = "ConfirmDialog"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 40
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Enabled = false
gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

local shade = Instance.new("TextButton") -- takes every click behind the panel
shade.Name = "Shade"
shade.Text = ""
shade.AutoButtonColor = false
shade.BackgroundColor3 = Color3.new(0, 0, 0)
shade.BackgroundTransparency = 0.45
shade.BorderSizePixel = 0
shade.Size = UDim2.fromScale(1, 1)
shade.Parent = gui

local panel = UiKit.panel({
    Name = "Panel", Size = UDim2.fromOffset(PANEL_SIZE.X, PANEL_SIZE.Y), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5), ZIndex = 2, Parent = gui,
})
panel.BackgroundTransparency = 0
panel:FindFirstChildOfClass("UIGradient").Transparency = NumberSequence.new(0)
panel:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Window)
panel.Active = true
-- at a window's scale (HudMetrics.windowScale: never under 1 on a phone, where its buttons must stay a thumb's size)
local panelScale = Instance.new("UIScale")
panelScale.Parent = panel
local function rescale()
    panelScale.Scale = HudMetrics.windowScale()
    -- in the middle of the room under Roblox's top bar: centred on the whole screen, a phone held sideways put its title
    -- band under the top bar, beside Roblox's own buttons
    panel.Position = UDim2.new(0.5, 0, 0.5, GuiService:GetGuiInset().Y / 2)
end
HudMetrics.Changed:Connect(rescale)
rescale()
-- the same frame as every window: its title band, and padding all round (Hud.window)
local title, closeButton = UiKit.titleBar(panel, "CONFIRM")
local inner = Instance.new("Frame")
inner.Name = "Body"
inner.BackgroundTransparency = 1
inner.Position = UDim2.fromOffset(PAD, TOP)
inner.Size = UDim2.new(1, -PAD * 2, 1, -(TOP + PAD))
inner.Parent = panel

local pictureSlot = Instance.new("Frame")
pictureSlot.Name = "Picture"
pictureSlot.BackgroundTransparency = 1
pictureSlot.Size = UDim2.fromOffset(72, 72)
pictureSlot.Parent = inner

local message = UiKit.label({
    Name = "Message", TextSize = 14, TextWrapped = true, TextColor3 = C.Text, TextYAlignment = Enum.TextYAlignment.Top,
    Position = UDim2.fromOffset(84, 0), Size = UDim2.new(1, -84, 1, -(UiTheme.Height.Button + UiTheme.Space.M)), Parent = inner,
})

local cancelButton = UiKit.button({
    Name = "Cancel", Text = "KEEP IT", Tone = "Quiet", AnchorPoint = Vector2.new(0, 1),
    Position = UDim2.fromScale(0, 1), Size = UDim2.new(0.5, -UiTheme.Space.S / 2, 0, UiTheme.Height.Button), Parent = inner,
})
local confirmButton = UiKit.button({
    Name = "Confirm", Text = "", Tone = "Danger", AnchorPoint = Vector2.new(1, 1),
    Position = UDim2.fromScale(1, 1), Size = UDim2.new(0.5, -UiTheme.Space.S / 2, 0, UiTheme.Height.Button), Parent = inner,
})

local showing = 0 -- which dialog is the latest
local readyAt, onConfirm, confirmText = 0, nil, ""

local function hide()
    showing += 1
    gui.Enabled = false
    onConfirm = nil
    for _, child in pictureSlot:GetChildren() do
        child:Destroy()
    end
end

cancelButton.Activated:Connect(hide)
closeButton.Activated:Connect(hide)
confirmButton.Activated:Connect(function()
    if os.clock() < readyAt or not onConfirm then
        return
    end
    local run = onConfirm
    hide()
    run()
end)

local ConfirmDialog = {}

function ConfirmDialog.show(props)
    hide()
    rescale() -- (the top bar's height is known by now)
    showing += 1
    local this = showing
    local seconds = props.Seconds or 3
    title.Text = props.Title or "CONFIRM"
    message.Text = props.Text or ""
    confirmText = props.ConfirmText or "CONFIRM"
    onConfirm = props.OnConfirm
    readyAt = os.clock() + seconds
    if props.Picture then
        props.Picture.Position = UDim2.fromOffset(0, 0)
        props.Picture.Parent = pictureSlot
        message.Position = UDim2.fromOffset(84, 0)
        message.Size = UDim2.new(1, -84, 1, -(UiTheme.Height.Button + UiTheme.Space.M))
    else
        message.Position = UDim2.fromOffset(0, 0)
        message.Size = UDim2.new(1, 0, 1, -(UiTheme.Height.Button + UiTheme.Space.M))
    end
    gui.Enabled = true
    Sfx.play("Open")
    task.spawn(function()
        for left = math.ceil(seconds), 1, -1 do
            if showing ~= this then
                return
            end
            confirmButton.Text = "WAIT " .. left
            task.wait(1)
        end
        if showing == this then
            confirmButton.Text = confirmText
        end
    end)
end

return ConfirmDialog

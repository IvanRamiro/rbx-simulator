-- The last question before something that can't be undone: a dimmed screen, a panel, and a button that only
-- wakes after a few seconds, so nothing is lost to a quick tap or a double click.
--   ConfirmDialog.show({ Title, Text, Picture, ConfirmText, Seconds, OnConfirm })
-- Picture (optional) is a GuiObject of up to 72 px, such as a portrait. Only one shows at a time.
local Players = game:GetService("Players")

local UI = script.Parent
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local applyHudScale = require(UI:WaitForChild("HudScale"))
local Sfx = require(UI.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local C = UiTheme.Colors
local PANEL_SIZE = Vector2.new(360, 208)

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
panel.BackgroundTransparency = 0.03
panel:FindFirstChildOfClass("UIGradient").Transparency = NumberSequence.new(0)
panel.Active = true
applyHudScale(panel, PANEL_SIZE.Y)
local inner = UiKit.content(panel, 14, 10)
local _, title = UiKit.header(inner, "CONFIRM", { TextSize = 14 })

local pictureSlot = Instance.new("Frame")
pictureSlot.Name = "Picture"
pictureSlot.BackgroundTransparency = 1
pictureSlot.Position = UDim2.fromOffset(0, 38)
pictureSlot.Size = UDim2.fromOffset(72, 72)
pictureSlot.Parent = inner

local message = UiKit.label({
    Name = "Message", TextSize = 14, TextWrapped = true, TextColor3 = C.Text, TextYAlignment = Enum.TextYAlignment.Top,
    Position = UDim2.fromOffset(84, 38), Size = UDim2.new(1, -84, 0, 92), Parent = inner,
})

local cancelButton = UiKit.button({
    Name = "Cancel", Font = "Strong", TextSize = 13, Text = "KEEP IT", Tone = "Accent", AnchorPoint = Vector2.new(0, 1),
    Position = UDim2.fromScale(0, 1), Size = UDim2.new(0.5, -4, 0, 36), Parent = inner,
})
local confirmButton = UiKit.button({
    Name = "Confirm", Font = "Strong", TextSize = 13, Text = "", Tone = "Danger", AnchorPoint = Vector2.new(1, 1),
    Position = UDim2.fromScale(1, 1), Size = UDim2.new(0.5, -4, 0, 36), Parent = inner,
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
        message.Position = UDim2.fromOffset(84, 38)
        message.Size = UDim2.new(1, -84, 0, 92)
    else
        message.Position = UDim2.fromOffset(0, 38)
        message.Size = UDim2.new(1, 0, 0, 92)
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

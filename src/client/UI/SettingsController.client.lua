-- The settings window (the Settings button on the HUD's rail): music and sound volume, and Reduced
-- Effects, which hides other players' auras and turns off screen flashes and camera shake, for
-- weaker devices and for anyone sensitive to flashing. Saved by the server (server/Data/Settings);
-- the "SettingMusic", "SettingSound" and "SettingReducedEffects" attributes carry them back.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local STEP = 0.1

local toggleButton = Hud.railButton("SettingsButton", UiTheme.Icons.Settings, "Settings", 6)
local isDeveloper = table.find(GameConfig.Titles.DeveloperUserIds, player.UserId) ~= nil
local window = Hud.window({
    Name = "SettingsWindow", Title = "SETTINGS", Size = Vector2.new(420, if isDeveloper then 460 else 376), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5),
})
-- the rows, one card each, in a list that scrolls on a short screen
local body = UiKit.scroll({ Name = "Rows", Size = UDim2.fromScale(1, 1), Parent = window.Body })
local PAD = UiTheme.Pad.Card
local BUTTON = UiTheme.Height.Button

local function read(key)
    local value = player:GetAttribute("Setting" .. key)
    if value == nil then
        return GameConfig.Settings[key]
    end
    return value
end

local function rowCard(name, height, order)
    return UiKit.card({ Name = name, Size = UDim2.new(1, 0, 0, height), LayoutOrder = order, Parent = body })
end

local function rowName(card, text)
    return UiKit.boldLabel({ Name = "Label", TextSize = 14, Text = text, Position = UDim2.fromOffset(PAD, PAD),
        Size = UDim2.new(1, -PAD * 2, 0, 18), Parent = card })
end

-- a volume row: its name and percent, a bar, and - and + buttons a thumb's size
local volumeRows = {}
local function volumeRow(key, word, order)
    local card = rowCard(key .. "Row", PAD + 18 + UiTheme.Space.S + BUTTON + PAD, order)
    rowName(card, word)
    local percent = UiKit.boldLabel({ Name = key .. "Percent", TextSize = 14, TextColor3 = C.Highlight,
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -PAD, 0, PAD), Size = UDim2.fromOffset(60, 18),
        TextXAlignment = Enum.TextXAlignment.Right, Parent = card })
    local y = PAD + 18 + UiTheme.Space.S
    local less = UiKit.button({ Name = key .. "Less", Text = "-", TextSize = 20, Tone = "Quiet",
        Position = UDim2.fromOffset(PAD, y), Size = UDim2.fromOffset(BUTTON, BUTTON), Parent = card })
    local more = UiKit.button({ Name = key .. "More", Text = "+", TextSize = 20, Tone = "Quiet",
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -PAD, 0, y), Size = UDim2.fromOffset(BUTTON, BUTTON), Parent = card })
    -- the - and + drawn as bars, so they read at the same weight as everything else (a "-" glyph is a speck)
    for button, bars in { [less] = { 0 }, [more] = { 0, 90 } } do
        button.Text = ""
        for _, turn in bars do
            local bar = Instance.new("Frame")
            bar.Name = "Mark"
            bar.BorderSizePixel = 0
            bar.BackgroundColor3 = C.Text
            bar.AnchorPoint = Vector2.new(0.5, 0.5)
            bar.Position = UDim2.fromScale(0.5, 0.5)
            bar.Size = UDim2.fromOffset(16, 3)
            bar.Rotation = turn
            bar.Parent = button
            UiKit.corner(bar, 2)
        end
        button:GetPropertyChangedSignal("Active"):Connect(function()
            for _, mark in button:GetChildren() do
                if mark.Name == "Mark" then
                    mark.BackgroundTransparency = if button.Active then 0 else 0.6
                end
            end
        end)
    end
    local inset = PAD + BUTTON + UiTheme.Space.M
    local bar = UiKit.bar({ Name = key .. "Bar", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, inset, 0, y + BUTTON / 2),
        Size = UDim2.new(1, -inset * 2, 0, 12), Parent = card })
    bar:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
    bar.Fill:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
    local function render(value)
        percent.Text = math.round(value * 100) .. "%"
        UiKit.setBar(bar, value)
        Sfx.setVolume(key, value)
        less.Active = value > 0 -- at an end, its button has nothing to do and shows it
        more.Active = value < 1
    end
    local function change(delta)
        local value = math.round(math.clamp(read(key) + delta, 0, 1) * 10) / 10
        player:SetAttribute("Setting" .. key, value) -- at once here; the server saves it and sends it back
        RemoteEvents.SettingsEvent:FireServer(key, value)
    end
    less.Activated:Connect(function()
        change(-STEP)
    end)
    more.Activated:Connect(function()
        change(STEP)
    end)
    player:GetAttributeChangedSignal("Setting" .. key):Connect(function()
        render(read(key))
    end)
    volumeRows[key] = render
end
volumeRow("Music", "MUSIC", 1)
volumeRow("Sound", "SOUND", 2)
for key, render in volumeRows do
    render(read(key))
end

-- an on/off row: its name, what it does, and its switch at the right
local SWITCH = 92
local function switchRow(name, word, help, order)
    local card = rowCard(name .. "Row", PAD + 18 + 4 + 30 + PAD, order)
    local label = rowName(card, word)
    label.Size = UDim2.new(1, -(PAD * 2 + SWITCH + UiTheme.Space.S), 0, 18)
    UiKit.label({ Name = name .. "Help", Font = "Strong", TextSize = 11, TextColor3 = C.Muted, TextWrapped = true,
        TextYAlignment = Enum.TextYAlignment.Top, Text = help, Position = UDim2.fromOffset(PAD, PAD + 22),
        Size = UDim2.new(1, -(PAD * 2 + SWITCH + UiTheme.Space.S), 0, 30), Parent = card })
    return UiKit.button({ Name = name, TextSize = 14, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -PAD, 0.5, 0),
        Size = UDim2.fromOffset(SWITCH, BUTTON), Parent = card })
end

-- reduced effects, on or off
local reduced = switchRow("Reduced", "REDUCED EFFECTS", "Hides other players' auras, and turns off screen flashes and camera shake.", 3)
local function renderReduced()
    local on = read("ReducedEffects")
    reduced.Text = if on then "ON" else "OFF"
    reduced:SetAttribute("Tone", if on then "Active" else "Quiet") -- on reads as running, not as something to press
end
reduced.Activated:Connect(function()
    local on = not read("ReducedEffects")
    player:SetAttribute("SettingReducedEffects", on)
    RemoteEvents.SettingsEvent:FireServer("ReducedEffects", on)
end)
player:GetAttributeChangedSignal("SettingReducedEffects"):Connect(renderReduced)
renderReduced()

-- for developers: the performance readout (client/Performance/PerfProbe), to read a device's frame rate and memory live;
-- not saved
if isDeveloper then
    local perf = switchRow("PerfReadout", "PERFORMANCE READOUT", "Frame rate and memory at the top left. Developers only; not saved.", 4)
    local function renderPerf()
        local on = player:GetAttribute("PerfReadout") == true
        perf.Text = if on then "ON" else "OFF"
        perf:SetAttribute("Tone", if on then "Active" else "Quiet") -- on reads as running, not as something to press
    end
    perf.Activated:Connect(function()
        player:SetAttribute("PerfReadout", player:GetAttribute("PerfReadout") ~= true)
        renderPerf()
    end)
    renderPerf()
end

window.link(toggleButton)
toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        window.open()
    end
end)

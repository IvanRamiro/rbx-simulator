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
local ROW = 58

local toggleButton = Hud.railButton("SettingsButton", UiTheme.Icons.Settings, "Settings", 6)
local isDeveloper = table.find(GameConfig.Titles.DeveloperUserIds, player.UserId) ~= nil
local window = Hud.window({
    Name = "SettingsWindow", Title = "SETTINGS", Size = Vector2.new(340, if isDeveloper then 300 else 250), AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5),
})
local body = window.Body

local function read(key)
    local value = player:GetAttribute("Setting" .. key)
    if value == nil then
        return GameConfig.Settings[key]
    end
    return value
end

-- a volume row: its name and percent, a bar, and - and + buttons (easy to hit on a phone)
local volumeRows = {}
local function volumeRow(key, word, order)
    local y = (order - 1) * ROW
    UiKit.label({ Name = key .. "Label", Font = "Strong", TextSize = 13, TextColor3 = C.Text, Text = word,
        Position = UDim2.fromOffset(0, y), Size = UDim2.new(0.6, 0, 0, 18), Parent = body })
    local percent = UiKit.label({ Name = key .. "Percent", Font = "Strong", TextSize = 12, TextColor3 = C.Muted,
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, y), Size = UDim2.new(0.4, 0, 0, 18),
        TextXAlignment = Enum.TextXAlignment.Right, Parent = body })
    local less = UiKit.button({ Name = key .. "Less", Font = "Strong", Text = "-", TextSize = 18, Tone = "Quiet",
        Position = UDim2.fromOffset(0, y + 20), Size = UDim2.fromOffset(32, 28), Parent = body })
    local more = UiKit.button({ Name = key .. "More", Font = "Strong", Text = "+", TextSize = 18, Tone = "Quiet",
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, y + 20), Size = UDim2.fromOffset(32, 28), Parent = body })
    local bar = UiKit.bar({ Name = key .. "Bar", Position = UDim2.fromOffset(40, y + 29), Size = UDim2.new(1, -80, 0, 10), Parent = body })
    local function render(value)
        percent.Text = math.round(value * 100) .. "%"
        UiKit.setBar(bar, value)
        Sfx.setVolume(key, value)
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

-- reduced effects, on or off
local y = 2 * ROW
UiKit.label({ Name = "ReducedLabel", Font = "Strong", TextSize = 13, TextColor3 = C.Text, Text = "REDUCED EFFECTS",
    Position = UDim2.fromOffset(0, y + 4), Size = UDim2.new(1, -70, 0, 18), Parent = body })
local reduced = UiKit.button({ Name = "Reduced", Font = "Strong", TextSize = 12, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, y), Size = UDim2.fromOffset(62, 28), Parent = body })
UiKit.label({ Name = "ReducedHelp", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true,
    Text = "Hides other players' auras, and turns off screen flashes and camera shake.",
    Position = UDim2.fromOffset(0, y + 34), Size = UDim2.new(1, 0, 0, 34), Parent = body })
local function renderReduced()
    local on = read("ReducedEffects")
    reduced.Text = if on then "ON" else "OFF"
    reduced:SetAttribute("Tone", if on then "Accent" else "Quiet")
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
    local devY = y + 76
    UiKit.label({ Name = "PerfLabel", Font = "Strong", TextSize = 13, TextColor3 = C.Text, Text = "PERFORMANCE READOUT",
        Position = UDim2.fromOffset(0, devY + 4), Size = UDim2.new(1, -70, 0, 18), Parent = body })
    local perf = UiKit.button({ Name = "PerfReadout", Font = "Strong", TextSize = 12, AnchorPoint = Vector2.new(1, 0),
        Position = UDim2.new(1, 0, 0, devY), Size = UDim2.fromOffset(62, 28), Parent = body })
    local function renderPerf()
        local on = player:GetAttribute("PerfReadout") == true
        perf.Text = if on then "ON" else "OFF"
        perf:SetAttribute("Tone", if on then "Accent" else "Quiet")
    end
    perf.Activated:Connect(function()
        player:SetAttribute("PerfReadout", player:GetAttribute("PerfReadout") ~= true)
        renderPerf()
    end)
    renderPerf()
end

toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        window.open()
    end
end)

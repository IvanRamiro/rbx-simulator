-- Damage numbers: what the local player's own strikes did, shown where they landed (CombatFx.hit; the
-- server decides the damage and whether it was critical, CombatService). A number pops, rises and
-- fades in under a second; a critical one is bigger, gold and tilted, with a "!".
--
--   DamageNumbers.show(position, amount, critical, tint)
--       position  where the strike landed, in the world
--       amount    the damage, a whole number (NumberFormat.compact shortens the big ones)
--       critical  true for a critical strike
--       tint      the striker's colour (their realm's, or their forged element's): the number's outline
--
-- Labels in one ScreenGui, placed each frame from the world position (not BillboardGuis: their size and
-- motion on screen are set here in pixels, the same at any distance). Nothing runs while none is shown.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local HudMetrics = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudMetrics"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))

local DamageNumbers = {}

local MAX_LIVE = 10 -- the most on screen at once: the oldest goes first
local LOOK = {
    Normal = { Size = 28, Life = 0.75, Rise = 46, Pop = 1.35, Color = Color3.fromRGB(255, 255, 255) },
    Critical = { Size = 40, Life = 1.0, Rise = 64, Pop = 1.75, Color = Color3.fromRGB(255, 216, 92), Stroke = Color3.fromRGB(120, 46, 10) },
}
local POP_TIME, SETTLE_TIME = 0.08, 0.2 -- seconds: up to its biggest, then back to its size
local FADE_FROM = 0.55                  -- the share of its life after which it fades

local gui = nil
local live = {}
local connection = nil
local side = 1 -- each number drifts to the other side of the last, so two in a row don't cover each other

local function screen()
    if gui and gui.Parent then
        return gui
    end
    gui = Instance.new("ScreenGui")
    gui.Name = "DamageNumbers"
    gui.ResetOnSpawn = false
    gui.IgnoreGuiInset = true -- so a label's place is the viewport's own pixel
    gui.DisplayOrder = -1     -- under the whole HUD: a number rising to the top of the screen passes behind its panels
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
    return gui
end

local function remove(index)
    live[index].label:Destroy()
    table.remove(live, index)
end

local function update()
    local camera = Workspace.CurrentCamera
    local now = os.clock()
    local hud = HudMetrics.scale()
    for index = #live, 1, -1 do
        local n = live[index]
        local age = now - n.born
        local t = age / n.look.Life
        if t >= 1 or not camera then
            remove(index)
            continue
        end
        local point = camera:WorldToViewportPoint(n.world)
        n.label.Visible = point.Z > 0
        local out = 1 - (1 - t) ^ 2 -- fast at first, easing to rest
        n.label.Position = UDim2.fromOffset(point.X + n.drift * out * hud, point.Y - n.look.Rise * out * hud)
        local pop = if age < POP_TIME then 0.5 + (n.look.Pop - 0.5) * (age / POP_TIME)
            elseif age < SETTLE_TIME then n.look.Pop + (1 - n.look.Pop) * ((age - POP_TIME) / (SETTLE_TIME - POP_TIME))
            else 1
        n.scale.Scale = pop * hud
        n.label.Rotation = n.tilt * math.max(0, 1 - age / SETTLE_TIME)
        local fade = math.clamp((t - FADE_FROM) / (1 - FADE_FROM), 0, 1)
        n.label.TextTransparency = fade
        n.stroke.Transparency = fade
    end
    if #live == 0 and connection then
        connection:Disconnect()
        connection = nil
    end
end

function DamageNumbers.show(position, amount, critical, tint)
    local look = if critical then LOOK.Critical else LOOK.Normal
    local label = Instance.new("TextLabel")
    label.Name = if critical then "Critical" else "Damage"
    label.AnchorPoint = Vector2.new(0.5, 0.5)
    label.AutomaticSize = Enum.AutomaticSize.XY
    label.BackgroundTransparency = 1
    label.Interactable = false
    label.FontFace = UiTheme.Fonts.Number
    label.TextSize = look.Size
    label.TextColor3 = look.Color
    label.Text = NumberFormat.compact(amount) .. (if critical then "!" else "")
    label.Visible = false
    local stroke = Instance.new("UIStroke")
    stroke.Thickness = if critical then 3 else 2
    stroke.Color = look.Stroke or (tint or Color3.new(0, 0, 0)):Lerp(Color3.new(0, 0, 0), 0.7)
    stroke.Parent = label
    local scale = Instance.new("UIScale")
    scale.Scale = 0.5
    scale.Parent = label
    label.Parent = screen()
    side = -side
    table.insert(live, {
        label = label, stroke = stroke, scale = scale, look = look, world = position, born = os.clock(),
        drift = side * (14 + 16 * math.random()), tilt = if critical then side * -7 else 0,
    })
    while #live > MAX_LIVE do
        remove(1)
    end
    if not connection then
        connection = RunService.RenderStepped:Connect(update)
    end
    update()
end

return DamageNumbers

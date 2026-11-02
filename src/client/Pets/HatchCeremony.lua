-- A hatch at the Hatching Altar, as the hatcher sees it: the server lays the egg in the altar's
-- cradle (PetService, a model everyone sees); here it rises from the cradle, turning, its glow
-- swelling, then breaks open in a burst of gold light (GuardianFx.secure) and vanishes. `delay` is
-- when it breaks (the server takes the egg away just after).
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local GuardianFx = require(script.Parent.Parent:WaitForChild("Guardians"):WaitForChild("GuardianFx"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local HatchCeremony = {}

local RISE = 1.6 -- studs the egg lifts from the cradle
local SHIVER = 0.7 -- the share of the rise after which the egg shivers (and rattles)

function HatchCeremony.play(model, delay, onBreak)
    if not (model and model.PrimaryPart) then
        if onBreak then
            onBreak()
        end
        return
    end
    local start = model:GetPivot()
    local began = os.clock()
    local highlight = Instance.new("Highlight")
    highlight.FillColor = Color3.fromRGB(255, 220, 140)
    highlight.OutlineColor = Color3.fromRGB(255, 240, 200)
    highlight.FillTransparency = 1
    highlight.OutlineTransparency = 1
    highlight.DepthMode = Enum.HighlightDepthMode.Occluded
    highlight.Parent = model
    local connection
    connection = RunService.RenderStepped:Connect(function()
        local t = os.clock() - began
        if t >= delay or not model.Parent then
            connection:Disconnect()
            return
        end
        local u = t / delay
        local lift = RISE * (1 - (1 - u) ^ 3)
        local shiver = if u > SHIVER then 0.06 * math.sin(t * 60) * (u - SHIVER) / (1 - SHIVER) else 0
        model:PivotTo(start * CFrame.new(shiver, lift, 0) * CFrame.Angles(0, t * (1.2 + 5 * u * u), 0))
        highlight.FillTransparency = 1 - 0.65 * u * u
        highlight.OutlineTransparency = 1 - 0.8 * u
    end)
    Sfx.after(delay * SHIVER, "EggRumble", model.PrimaryPart)
    task.delay(delay, function()
        if model.Parent then
            local at = model:GetPivot().Position
            Sfx.play("EggCrack", at)
            GuardianFx.secure(at)
            GuardianFx.flash(CFrame.new(at), { Qi = Color3.fromRGB(255, 190, 70), QiCore = Color3.fromRGB(255, 250, 230) }, 12)
            for _, part in model:GetDescendants() do
                if part:IsA("BasePart") then
                    TweenService:Create(part, TweenInfo.new(0.15), { Transparency = 1 }):Play()
                end
            end
            highlight:Destroy()
        end
        if onBreak then
            onBreak()
        end
    end)
end

return HatchCeremony

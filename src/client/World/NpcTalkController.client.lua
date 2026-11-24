-- The territories' people talk (TerritoryNpcBuilder, Placements/TerritoryNpcs; the owner approved them 2026-11-24): each person tagged "TerritoryNpc" carries two lines in its
-- Line1 and Line2 attributes. A Talk prompt (F, as every other prompt; E is cultivation) on the person shows the first line in a speech bubble over their head, the next press the
-- second, then the first again. Nothing is asked of the server and nothing is saved: they are only talk (no line mentions a trial, a weapon, a rank, an egg or any route, and
-- none gives a hint or a reward). The prompt is made here, on this client, so a person streaming in or out takes it with them.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

local UI = script.Parent.Parent:WaitForChild("UI")
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

local TAG = "TerritoryNpc"
local SHOW_FOR = 5.5      -- seconds a line stays up
local TALK_RANGE = 10     -- studs
local BUBBLE_W = 250      -- pixels, at scale 1

local player = Players.LocalPlayer
local C = UiTheme.Colors

local wired = setmetatable({}, { __mode = "k" })

local function say(model, text)
    local head = model:FindFirstChild("Head")
    if not head then
        return
    end
    local old = head:FindFirstChild("TalkBubble")
    if old then
        old:Destroy()
    end
    local gui = Instance.new("BillboardGui")
    gui.Name = "TalkBubble"
    gui.Adornee = head
    gui.AlwaysOnTop = false
    gui.LightInfluence = 0
    gui.MaxDistance = 40
    gui.Size = UDim2.fromOffset(BUBBLE_W, 74)
    gui.StudsOffsetWorldSpace = Vector3.new(0, 2.3, 0)
    gui.ClipsDescendants = false
    gui.Parent = head
    local panel = UiKit.panel({ Name = "Panel", Size = UDim2.fromScale(1, 1), Brackets = false, Parent = gui })
    UiKit.label({
        Name = "Line", Font = "Strong", TextSize = 16, Text = text, TextColor3 = C.Text, Position = UDim2.fromOffset(12, 6), Size = UDim2.new(1, -24, 1, -12),
        TextWrapped = true, TextXAlignment = Enum.TextXAlignment.Center, TextYAlignment = Enum.TextYAlignment.Center, Parent = panel,
    })
    task.delay(SHOW_FOR, function()
        if gui.Parent then
            gui:Destroy()
        end
    end)
end

local function wire(model)
    if wired[model] or not model:IsA("Model") then
        return
    end
    local root = model:FindFirstChild("HumanoidRootPart")
    local line1, line2 = model:GetAttribute("Line1"), model:GetAttribute("Line2")
    if not root or typeof(line1) ~= "string" then
        return
    end
    wired[model] = true
    local prompt = Instance.new("ProximityPrompt")
    prompt.Name = "TalkPrompt"
    prompt.ActionText = "Talk"
    prompt.ObjectText = string.match(model:FindFirstChildOfClass("Humanoid") and model:FindFirstChildOfClass("Humanoid").DisplayName or model.Name, "^[^,]+") or model.Name
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = TALK_RANGE
    prompt.RequiresLineOfSight = false
    prompt.Parent = root
    local next = 1
    prompt.Triggered:Connect(function(who)
        if who ~= player or player:GetAttribute("IsCultivating") == true then
            return
        end
        local text = if next == 1 or typeof(line2) ~= "string" then line1 else line2
        next = if next == 1 and typeof(line2) == "string" then 2 else 1
        say(model, text)
    end)
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(function(model)
    task.defer(wire, model)
    -- (a person that streams in has its root a moment after the model)
    model.ChildAdded:Connect(function()
        task.defer(wire, model)
    end)
end)
for _, model in CollectionService:GetTagged(TAG) do
    task.spawn(wire, model)
end

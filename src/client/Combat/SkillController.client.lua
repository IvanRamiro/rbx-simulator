-- The Qi skills (GameConfig.Combat.Skills): a row of buttons over the dock, each with its key and its
-- cooldown draining. A skill shows once its rank is near: those unlocked, and the next to come,
-- dimmed. Keys (and gamepad buttons) or a tap cast them; the effects play here at once (CombatFx) and
-- the server resolves the hit (SkillEvent, CombatService), relaying it for everyone's effects.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local CombatFx = require(script.Parent:WaitForChild("CombatFx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local SKILLS = GameConfig.Combat.Skills
local SLOT = 56

local message = Toast.new(nil, "SkillMessage", nil, C.Highlight, 4)

local row = Instance.new("Frame")
row.Name = "SkillRow"
row.BackgroundTransparency = 1
row.AutomaticSize = Enum.AutomaticSize.XY
row.Size = UDim2.new()
row.LayoutOrder = 5
row.Parent = Hud.Dock
UiKit.list(row, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8) })

local function unlocked(skill)
    return Ranks.isAtLeast(Ranks.getPlayerRankName(player), skill.RankId)
end

local slots = {}
local cooling = nil

local function cast(slot)
    local skill = slot.skill
    if not unlocked(skill) then
        Sfx.play("Error")
        message:show(skill.Name .. " unlocks at " .. Ranks.getRankById(skill.RankId).Name .. ".", Color3.new(1, 1, 1))
        return
    end
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true or os.clock() < slot.readyAt then
        return
    end
    slot.readyAt = os.clock() + skill.Cooldown
    CombatFx.skill(player, skill.Id)
    RemoteEvents.SkillEvent:FireServer(skill.Id)
    if not cooling then
        cooling = RunService.RenderStepped:Connect(function()
            local any = false
            for _, s in slots do
                local left = s.readyAt - os.clock()
                if left > 0 then
                    any = true
                    s.shade.Size = UDim2.fromScale(1, left / s.skill.Cooldown)
                    s.count.Text = tostring(math.ceil(left))
                elseif s.shade.Visible then
                    s.shade.Visible, s.count.Text = false, ""
                end
                if left > 0 and not s.shade.Visible then
                    s.shade.Visible = true
                end
            end
            if not any then
                cooling:Disconnect()
                cooling = nil
            end
        end)
    end
end

for order, skill in SKILLS do
    local button = UiKit.button({ Name = skill.Id, Text = "", Size = UDim2.fromOffset(SLOT, SLOT), LayoutOrder = order, Tone = "Quiet", Parent = row })
    local icon = UiKit.icon(UiTheme.Icons[skill.Icon], 34)
    icon.AnchorPoint = Vector2.new(0.5, 0.5)
    icon.Position = UDim2.fromScale(0.5, 0.5)
    icon.Parent = button
    local shade = Instance.new("Frame")
    shade.Name = "Cooldown"
    shade.AnchorPoint = Vector2.new(0, 1)
    shade.Position = UDim2.fromScale(0, 1)
    shade.BackgroundColor3 = Color3.new(0, 0, 0)
    shade.BackgroundTransparency = 0.35
    shade.BorderSizePixel = 0
    shade.Visible = false
    shade.ZIndex = 3
    shade.Parent = button
    local count = UiKit.label({ Name = "Count", Font = "Title", TextSize = 20, TextColor3 = C.Text, Text = "", Size = UDim2.fromScale(1, 1),
        TextXAlignment = Enum.TextXAlignment.Center, ZIndex = 4, Parent = button })
    local key = UiKit.keycap(skill.Key)
    key.AnchorPoint = Vector2.new(1, 1)
    key.Position = UDim2.new(1, -2, 1, -2)
    key.ZIndex = 5
    key.Parent = button
    local slot = { skill = skill, button = button, icon = icon, shade = shade, count = count, readyAt = 0 }
    slots[order] = slot
    button.Activated:Connect(function()
        cast(slot)
    end)
end

-- the unlocked skills and the next to come; a skill unlocked in play is announced
local seen = {}
local function render(announce)
    local nextShown = false
    for _, slot in slots do
        local open = unlocked(slot.skill)
        slot.button.Visible = open or not nextShown
        if not open then
            nextShown = true
        end
        slot.icon.Image.ImageTransparency = if open then 0 else 0.65
        if open and not seen[slot.skill.Id] then
            seen[slot.skill.Id] = true
            if announce then
                Sfx.play("Attune")
                message:show("New skill: " .. slot.skill.Name .. ". " .. slot.skill.Hint, C.Highlight)
            end
        end
    end
end

task.spawn(function()
    local rank = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    render(false)
    rank.Changed:Connect(function()
        render(true)
    end)
end)
render(false)

UserInputService.InputBegan:Connect(function(input, gameProcessed)
    if gameProcessed then
        return
    end
    for _, slot in slots do
        if input.KeyCode == Enum.KeyCode[slot.skill.Key] or input.KeyCode == Enum.KeyCode[slot.skill.Gamepad] then
            cast(slot)
        end
    end
end)

RemoteEvents.SkillEvent.OnClientEvent:Connect(function(source, skillId, position)
    if typeof(source) ~= "Instance" or not source:IsA("Player") then
        return
    end
    if source ~= player then
        CombatFx.skill(source, skillId)
    end
    if typeof(position) == "Vector3" then
        CombatFx.hit(source, position)
    end
end)

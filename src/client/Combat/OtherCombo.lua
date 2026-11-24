-- Other players' combo counters (the owner's improvement list, item 8, 2026-11-24: "show combo counters to other players; right now you only see your own"). The
-- server already tells every client each strike's count (CombatEvent carries `hits` to all clients), so this is a small plate that rides over a striker's nameplate while
-- their combo is up: the count and the tier's word (shared/FormRules.tierOf), in the same colours as your own counter, popping as it grows and fading once the window lapses.
-- It shows from 3 hits (a pair of hits is no combo), within the nameplates' distance, and doesn't pop with Reduced Effects. Your own counter is ComboCounter.
--
--   OtherCombo.set(player, hits, finisher)   the count after this player's strike (0 or none: it goes)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local FormRules = require(ReplicatedStorage:WaitForChild("FormRules"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))
local UI = script.Parent.Parent:WaitForChild("UI")
local UiKit = require(UI:WaitForChild("UiKit"))

local OtherCombo = {}

local localPlayer = Players.LocalPlayer
local MIN_HITS = 3
local DISTANCE = if Quality.Low then 55 else 90 -- studs, as the nameplates
local FADE = 0.35
local TIER_COLORS = {
    Nice = Color3.fromRGB(255, 255, 255), Great = Color3.fromRGB(150, 226, 255), Amazing = Color3.fromRGB(255, 216, 92),
    Legendary = Color3.fromRGB(255, 120, 96),
}

local plates = {} -- [player] = { gui, count, tier, scale, lastHit, shown }

local function remove(player)
    local plate = plates[player]
    if plate then
        plates[player] = nil
        plate.gui:Destroy()
    end
end

local function build(player, character)
    local head = character and character:FindFirstChild("Head")
    if not head then
        return nil
    end
    local gui = Instance.new("BillboardGui")
    gui.Name = "ComboPlate_" .. tostring(if typeof(player) == "Instance" then player.UserId else player)
    gui.Adornee = head
    gui.Size = UDim2.new(7, 0, 2.2, 0)
    gui.StudsOffsetWorldSpace = Vector3.new(0, 5, 0) -- over the nameplate (2.3 up, 1.7 tall)
    gui.MaxDistance = DISTANCE
    gui.LightInfluence = 0
    gui.ResetOnSpawn = false
    gui.AlwaysOnTop = false
    local holder = Instance.new("Frame")
    holder.Name = "Holder"
    holder.BackgroundTransparency = 1
    holder.AnchorPoint = Vector2.new(0.5, 0.5)
    holder.Position = UDim2.fromScale(0.5, 0.5)
    holder.Size = UDim2.fromScale(1, 1)
    holder.Parent = gui
    local scale = Instance.new("UIScale")
    scale.Parent = holder
    local count = UiKit.label({
        Name = "Count", Font = "Title", TextScaled = true, TextXAlignment = Enum.TextXAlignment.Center,
        Size = UDim2.fromScale(1, 0.6), Parent = holder,
    })
    UiKit.outline(count, 2)
    local tier = UiKit.label({
        Name = "Tier", Font = "Heavy", TextScaled = true, TextXAlignment = Enum.TextXAlignment.Center,
        Position = UDim2.fromScale(0, 0.6), Size = UDim2.fromScale(1, 0.4), Parent = holder,
    })
    UiKit.outline(tier, 1.5)
    gui.Parent = localPlayer:WaitForChild("PlayerGui")
    local plate = { gui = gui, count = count, tier = tier, scale = scale, lastHit = os.clock(), shown = 0 }
    plates[player] = plate
    return plate
end

-- (setFor is `set` for any owner and body: the plate is keyed by the owner, drawn over the body's head. `set` is the game's call; the tests use setFor)
function OtherCombo.setFor(player, character, hits, finisher)
    if player == localPlayer or player == nil then
        return
    end
    if typeof(hits) ~= "number" or hits < MIN_HITS then
        if hits == 0 then
            remove(player)
        end
        return
    end
    local plate = plates[player]
    if plate and plate.gui.Adornee ~= (character and character:FindFirstChild("Head")) then
        remove(player) -- a new body: a new plate
        plate = nil
    end
    plate = plate or build(player, character)
    if not plate then
        return
    end
    local grew = hits > plate.shown
    plate.shown = hits
    plate.lastHit = os.clock()
    local name = FormRules.tierOf(hits)
    local color = if name then TIER_COLORS[name] else TIER_COLORS.Nice
    plate.count.Text = hits .. " HITS"
    plate.tier.Text = if name then string.upper(name) else ""
    plate.count.TextColor3, plate.tier.TextColor3 = color, color
    plate.count.TextTransparency, plate.tier.TextTransparency = 0, 0
    plate.gui.Enabled = true
    if grew and localPlayer:GetAttribute("SettingReducedEffects") ~= true then
        plate.scale.Scale = if finisher then 1.4 else 1.2
        TweenService:Create(plate.scale, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
    end
end

function OtherCombo.set(player, hits, finisher)
    if typeof(player) == "Instance" and player:IsA("Player") then
        OtherCombo.setFor(player, player.Character, hits, finisher)
    end
end

-- each plate lapses with the combat window, then fades and goes
RunService.Heartbeat:Connect(function()
    for player, plate in plates do
        local idle = os.clock() - plate.lastHit
        if (typeof(player) == "Instance" and not player.Parent) or not plate.gui.Adornee or not plate.gui.Adornee:IsDescendantOf(workspace) then
            remove(player)
        elseif idle > FormRules.Counter.WINDOW then
            local alpha = math.clamp((idle - FormRules.Counter.WINDOW) / FADE, 0, 1)
            plate.count.TextTransparency, plate.tier.TextTransparency = alpha, alpha
            if alpha >= 1 then
                remove(player)
            end
        end
    end
end)

Players.PlayerRemoving:Connect(remove)

return OtherCombo

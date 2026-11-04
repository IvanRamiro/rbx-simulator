-- What makes an egg stand out, and all it has: a Highlight in its own colour on each egg near the
-- camera, and a BloomEffect that rises as you come up to one. No aura, no smoke, nothing that hides the
-- egg (the owner, November 4, 2026). Eggs are the parts tagged GameConfig.EggGlowTag: on stands, carried,
-- dropped or hatching, the server tags them all.
--
-- A client can only draw so many Highlights at once (Roblox caps it at 31, and auras use them too), so
-- only the nearest few are on. The fill is faint so it doesn't paint over the egg's baked detail; the
-- outline does the work.
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local LOW = require(script.Parent.Parent:WaitForChild("Quality")).Low

local TAG = GameConfig.EggGlowTag
local HIGHLIGHT_RANGE = if LOW then 90 else 140
local MAX_HIGHLIGHTS = if LOW then 4 else 8
local OUTLINE_TRANSPARENCY = 0.2
local FILL_TRANSPARENCY = 0.9

-- The bloom: comes in between BLOOM_FAR and BLOOM_NEAR studs from the nearest egg.
local BLOOM_FAR, BLOOM_NEAR = 70, 25
local BLOOM_INTENSITY = 0.3 -- it lights the whole screen, not only the egg: at 0.75 it washed out the grass
local BLOOM_FADE = 3 -- how fast it follows, per second

local player = Players.LocalPlayer
local eggs = {} -- [part] = Highlight or false

local function highlightFor(part)
    local highlight = eggs[part]
    if highlight then
        return highlight
    end
    local color = GameConfig.EggGlow[part:GetAttribute("EggId")] or Color3.new(1, 1, 1)
    highlight = Instance.new("Highlight")
    highlight.Name = "EggHighlight"
    highlight.Adornee = part
    highlight.DepthMode = Enum.HighlightDepthMode.Occluded
    highlight.FillColor = color
    highlight.FillTransparency = FILL_TRANSPARENCY
    highlight.OutlineColor = color
    highlight.OutlineTransparency = OUTLINE_TRANSPARENCY
    highlight.Parent = part
    eggs[part] = highlight
    return highlight
end

local function added(part)
    if part:IsA("BasePart") and eggs[part] == nil then
        eggs[part] = false
    end
end

local function removed(part)
    local highlight = eggs[part]
    if highlight then
        highlight:Destroy()
    end
    eggs[part] = nil
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(added)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(removed)
for _, part in CollectionService:GetTagged(TAG) do
    added(part)
end

local bloom = Instance.new("BloomEffect")
bloom.Name = "EggBloom"
bloom.Size = 18
bloom.Threshold = 0.97 -- only what really shines: Neon and white-hot highlights, not a sunlit field
bloom.Intensity = 0
bloom.Enabled = false
bloom.Parent = Lighting

local bloomTarget = 0

-- Four times a second: which eggs are near enough to be lit, and how near the nearest is.
task.spawn(function()
    while true do
        local camera = workspace.CurrentCamera
        if camera then
            local eye = camera.CFrame.Position
            local list = {}
            for part in eggs do
                if part:IsDescendantOf(workspace) then
                    table.insert(list, { Part = part, Distance = (part.Position - eye).Magnitude })
                end
            end
            table.sort(list, function(a, b)
                return a.Distance < b.Distance
            end)
            for i, entry in list do
                local on = i <= MAX_HIGHLIGHTS and entry.Distance <= HIGHLIGHT_RANGE
                if on then
                    highlightFor(entry.Part).Enabled = true
                elseif eggs[entry.Part] then
                    eggs[entry.Part].Enabled = false
                end
            end
            local nearest = list[1] and list[1].Distance or math.huge
            bloomTarget = BLOOM_INTENSITY * math.clamp((BLOOM_FAR - nearest) / (BLOOM_FAR - BLOOM_NEAR), 0, 1)
            if player:GetAttribute("SettingReducedEffects") == true then
                bloomTarget = 0
            end
        end
        task.wait(0.25)
    end
end)

RunService.RenderStepped:Connect(function(dt)
    local difference = bloomTarget - bloom.Intensity
    if math.abs(difference) > 0.002 then
        bloom.Intensity += difference * math.min(1, dt * BLOOM_FADE)
    elseif bloom.Intensity ~= bloomTarget then
        bloom.Intensity = bloomTarget
    end
    bloom.Enabled = bloom.Intensity > 0.005
end)

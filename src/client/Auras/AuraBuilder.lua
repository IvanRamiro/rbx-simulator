local TweenService = game:GetService("TweenService")

local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

-- Pet auras: an equipped pet of a cultivating player shows its element's aura, for the pets that
-- have one (ELEMENTS below; the rest show none). The player's own aura is CharacterAura.
local AuraBuilder = {}

local PET_AMOUNT = 0.6 -- pet auras are a lighter version of the element's full aura

AuraBuilder.REMOVE_DELAY = 3

local FADE_IN = TweenInfo.new(1.2, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
local FADE_OUT = TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.In)
local TRAIL_START_DELAY = 0.2
local FULL_TURN = 2 * math.pi

local function addFade(aura, instance, property, visibleValue, hiddenValue)
    instance[property] = hiddenValue
    table.insert(aura.fades, { Instance = instance, Property = property, Visible = visibleValue, Hidden = hiddenValue })
end

local function measureBody(model, rootPart)
    local rootCFrame = rootPart.CFrame
    local low, high = AuraKit.bodyBounds(model, rootPart)
    local boxSize = high - low
    local feetY = low.Y
    local head = model:FindFirstChild("Head")
    local headTopY = if head and head:IsA("BasePart")
        then rootCFrame:PointToObjectSpace(head.Position).Y + head.Size.Y / 2
        else feetY + boxSize.Y
    local height = math.clamp(headTopY - feetY, 2, 12)
    return { FeetY = feetY, Height = height, Reach = math.max(boxSize.X, boxSize.Z) / 2 }
end

-- (empty for now: the Aqua Wisp's droplets and the Golden Kirin's leaves went with their old designs, 2026-11-09; the new Aqua Wisp's
-- aura comes once the new pet is done)
local ELEMENTS = {}

function AuraBuilder.build(player, character, rootPart, petId, rankId)
    local style = AuraStyles.Auras[petId]
    if not style or not ELEMENTS[petId] then
        return nil
    end

    local model = Instance.new("Folder")
    model.Name = player.Name .. "_Aura"

    local body = measureBody(character, rootPart)
    local aura = {
        player = player,
        rootPart = rootPart,
        model = model,
        style = style,
        body = body,
        amount = PET_AMOUNT,
        orbitRadius = math.max(style.OrbitRadius * body.Height, body.Reach + 0.8),
        boost = AuraStyles.getBoost(rankId),
        fades = {},
        loops = {},
        trails = {},
        phase = math.random() * FULL_TURN,
        hiding = false,
        destroyed = false,
    }

    local fader = Instance.new("NumberValue")
    fader.Name = "Fader"
    fader.Parent = model
    aura.fader = fader
    addFade(aura, fader, "Value", 1, 0)

    local width = math.max(body.Height * 0.8, body.Reach * 2)
    aura.volume = AuraKit.newPart(aura, "Volume", Vector3.new(width, body.Height * 0.9, width))

    local element = ELEMENTS[petId]
    element.Build(aura, style)
    aura.animate = element.Animate
    return aura
end

local function playFades(aura, toVisible)
    local tweenInfo = if toVisible then FADE_IN else FADE_OUT
    for _, fade in aura.fades do
        TweenService:Create(fade.Instance, tweenInfo, { [fade.Property] = if toVisible then fade.Visible else fade.Hidden }):Play()
    end
end

function AuraBuilder.show(aura)
    playFades(aura, true)
    task.delay(TRAIL_START_DELAY, function()
        if aura.destroyed or aura.hiding then
            return
        end
        for _, trail in aura.trails do
            trail.Enabled = true
        end
    end)
end

function AuraBuilder.hide(aura)
    aura.hiding = true
    playFades(aura, false)
    for _, trail in aura.trails do
        trail.Enabled = false
    end
end

function AuraBuilder.destroy(aura)
    aura.destroyed = true
    for _, tween in aura.loops do
        tween:Cancel()
    end
    table.clear(aura.loops)
    aura.model:Destroy()
end

function AuraBuilder.update(aura, now, parts, cframes)
    local body = aura.body
    local rootCFrame = aura.rootPart.CFrame
    aura.animate(aura, now, rootCFrame, parts, cframes)

    table.insert(parts, aura.volume)
    table.insert(cframes, rootCFrame * CFrame.new(0, body.FeetY + body.Height * 0.5, 0))

    aura.light.Brightness = aura.lightBrightness * aura.fader.Value * (0.85 + 0.15 * math.sin(now * 1.6))
end

return AuraBuilder

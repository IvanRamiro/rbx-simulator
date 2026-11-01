local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

local VerdantGaleAura = {}

local STYLE = AuraStyles.VerdantGale
local numberSequence = AuraKit.numberSequence
local newPart = AuraKit.newPart
local addEmitter = AuraKit.addEmitter
local BEAM_FADE = { { 0, 1 }, { 0.1, 0.15 }, { 0.8, 0.3 }, { 1, 1 } }

local FLAT_DEFAULTS = { Rotation = NumberRange.new(-180, 180) }

local function flatEmitter(aura, parent, rate, properties)
    return AuraKit.flatEmitter(aura, parent, rate, properties, FLAT_DEFAULTS)
end

local function buildGround(aura)
    local s = aura.k
    local c = STYLE.Colors
    aura.ground = newPart(aura, "Ground", Vector3.one * 0.2)
    aura.swirl = flatEmitter(aura, aura.ground, 8, {
        Texture = STYLE.Textures.Swirl,
        Color = ColorSequence.new(c.Lime, c.Deep),
        LightEmission = 0.6,
        Brightness = 4,
        Size = numberSequence({ { 0, 4 * s }, { 0.5, 6.2 * s }, { 1, 7 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0 }, { 0.75, 0 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1.6),
        RotSpeed = NumberRange.new(-260, -200),
        ZOffset = 0.5,
    })
    aura.slash = flatEmitter(aura, aura.ground, 10, {
        Texture = STYLE.Textures.Slash,
        Color = ColorSequence.new(c.Pale, c.Lime),
        LightEmission = 1,
        Brightness = 4,
        Size = numberSequence({ { 0, 2.5 * s }, { 0.5, 5 * s }, { 1, 5.8 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0 }, { 0.7, 0.1 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1.2),
        RotSpeed = NumberRange.new(-380, -300),
        ZOffset = 1,
    })

    aura.riser = newPart(aura, "Risers", Vector3.new(7 * s, 0.2, 7 * s))
    aura.wind = addEmitter(aura, aura.riser, 55, {
        Texture = STYLE.Textures.Streak,
        Shape = Enum.ParticleEmitterShape.Disc,
        ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top,
        Orientation = Enum.ParticleOrientation.VelocityParallel,
        Color = ColorSequence.new(Color3.new(1, 1, 1), c.Pale),
        LightEmission = 1,
        Brightness = 3,
        Size = numberSequence({ { 0, 0.15 * s }, { 0.5, 0.25 * s }, { 1, 0.1 * s } }),
        Squash = numberSequence({ { 0, -1 }, { 0.5, -3 }, { 1, -4 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0 }, { 0.8, 0.3 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1.2, 1.8),
        Speed = NumberRange.new(2.5 * s, 4 * s),
        SpreadAngle = Vector2.new(5, 5),
        Acceleration = Vector3.new(0, 3 * s, 0),
        ZOffset = 1,
    })
end

local function buildBody(aura)
    local s = aura.k
    local c = STYLE.Colors
    aura.volume = newPart(aura, "Body", Vector3.one * 0.2)
    addEmitter(aura, aura.volume, 22, {
        Texture = STYLE.Textures.Fog,
        Color = ColorSequence.new(c.Lime, c.Deep),
        LightEmission = 1,
        Brightness = 1.5,
        Size = numberSequence({ { 0, 2.5 * s }, { 1, 5 * s } }),
        Transparency = numberSequence({ { 0, 0.55 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1.5, 2.2),
        Speed = NumberRange.new(0.5 * s, 1.5 * s),
        SpreadAngle = Vector2.new(70, 70),
        EmissionDirection = Enum.NormalId.Top,
        Acceleration = Vector3.new(0, 1.5 * s, 0),
        Rotation = NumberRange.new(-180, 180),
        RotSpeed = NumberRange.new(-30, 30),
        Drag = 1,
        ZOffset = -1,
    })

    aura.beamBottom = AuraKit.attachment(aura.volume)
    aura.beamTop = AuraKit.attachment(aura.volume)
    local beam = AuraKit.beam(aura.volume, aura.beamBottom, aura.beamTop, {
        Texture = STYLE.Textures.Wisp,
        TextureLength = 7 * s,
        TextureSpeed = 1.2,
        LightEmission = 1,
        Brightness = 3,
        Color = ColorSequence.new(c.White, c.Pale),
        Width0 = 4.5 * s,
        Width1 = 3 * s,
        CurveSize0 = 1.5 * s,
        CurveSize1 = -1.5 * s,
        Segments = 16,
        ZOffset = 0.5,
    })
    aura.beamFade = AuraKit.fader(beam, BEAM_FADE)

    AuraKit.glow(aura, c.Lime, c.Pale, 14 * s)
end

local function onSurge(aura, strength)
    aura.swirl:Emit(math.round(3 * strength))
    aura.slash:Emit(math.round(3 * strength))
    aura.wind:Emit(math.round(30 * strength * aura.detail))
end

function VerdantGaleAura.build(player, character, rootPart, _petId, rankId)
    local aura = AuraKit.newAura(player, character, rootPart, rankId, nil, STYLE)
    aura.onSurge = onSurge
    buildGround(aura)
    buildBody(aura)
    return aura
end

VerdantGaleAura.show = AuraKit.show
VerdantGaleAura.hide = AuraKit.hide
VerdantGaleAura.pulse = function(aura)
    AuraKit.surge(aura, 1)
end
VerdantGaleAura.destroy = AuraKit.destroy

function VerdantGaleAura.update(aura, now, parts, cframes)
    local s = aura.k
    local frame = AuraKit.step(aura, now)
    local floor, seat = frame.floor, frame.seat

    local function place(part, cframe)
        table.insert(parts, part)
        table.insert(cframes, cframe)
    end

    place(aura.ground, CFrame.new(floor + Vector3.new(0, 0.1, 0)))
    place(aura.riser, CFrame.new(floor + Vector3.new(0, 0.1, 0)))
    local center = seat + Vector3.new(0, 2 * s, 0)
    place(aura.volume, CFrame.new(center))

    local head = aura.character:FindFirstChild("Head")
    local top = if head and head:IsA("BasePart") then head.Position.Y + 3 * s else center.Y + 5 * s
    aura.beamBottom.Position = Vector3.new(0, floor.Y - center.Y, 0)
    aura.beamTop.Position = Vector3.new(0, top - center.Y, 0)
    AuraKit.fadeBeam(aura.beamFade, frame.fade * math.min(1, frame.charge * 1.5))

    AuraKit.finishGlow(aura, frame, 4, 0.05, 0.3)
end

return VerdantGaleAura

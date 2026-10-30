local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

local EmberCrucibleAura = {}

local STYLE = AuraStyles.EmberCrucible
local SET = "EmberCrucible"
local TAU = AuraKit.TAU
local numberSequence = AuraKit.numberSequence
local smoothstep = AuraKit.smoothstep
local approach = AuraKit.approach
local newPart = AuraKit.newPart
local meshPart = AuraKit.meshPart
local addEmitter = AuraKit.addEmitter
local showPart = AuraKit.showPart
local MESHES = { "BeadShell", "WyrmHead", "WyrmGlow", "HaloRing" }
local RING_FADE = { { 0, 0.05 }, { 1, 0.05 } }
local CORONA_FADE = { { 0, 0.1 }, { 0.6, 0.35 }, { 1, 1 } }
local VORTEX_FADE = { { 0, 1 }, { 0.12, 0.1 }, { 0.7, 0.35 }, { 1, 1 } }

local function template(name)
    return AuraKit.template(SET, name)
end

local function fit(name, length)
    local mesh = template(name)
    return length / math.max(mesh.Size.X, mesh.Size.Y, mesh.Size.Z)
end

local function colors(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, ColorSequenceKeypoint.new(point[1], point[2]))
    end
    return ColorSequence.new(keypoints)
end

local function fireEmitter(aura, parent, rate, properties, minStage)
    local preset = {
        Texture = STYLE.Textures.Fire,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8,
        FlipbookMode = Enum.ParticleFlipbookMode.Loop,
        FlipbookFramerate = NumberRange.new(28, 36),
        FlipbookStartRandom = true,
        LightEmission = 0.55,
        Brightness = 1.8,
        Rotation = NumberRange.new(-8, 8),
    }
    for property, value in properties do
        preset[property] = value
    end
    return addEmitter(aura, parent, rate, preset, minStage)
end

local function energyEmitter(aura, parent, rate, properties, minStage)
    local preset = {
        Texture = STYLE.Textures.EnergyFlame,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8,
        FlipbookMode = Enum.ParticleFlipbookMode.Loop,
        FlipbookFramerate = NumberRange.new(30, 40),
        FlipbookStartRandom = true,
        LightEmission = 1,
        Brightness = 1.8,
        Rotation = NumberRange.new(-8, 8),
        EmissionDirection = Enum.NormalId.Top,
    }
    for property, value in properties do
        preset[property] = value
    end
    return addEmitter(aura, parent, rate, preset, minStage)
end

local function flatEmitter(aura, parent, rate, properties)
    local preset = {
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
        EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.01),
        LockedToPart = true,
        Rotation = NumberRange.new(0, 360),
        LightEmission = 1,
    }
    for property, value in properties do
        preset[property] = value
    end
    return addEmitter(aura, parent, rate, preset)
end

local function buildGround(aura)
    local s = aura.k
    local c = STYLE.Colors
    local ring = STYLE.Ground
    aura.ground = newPart(aura, "Ground", Vector3.new(1, 0.2, 1))
    flatEmitter(aura, aura.ground, 2.4, {
        Texture = STYLE.Textures.Fog, Lifetime = NumberRange.new(5), RotSpeed = ring.FogSpin,
        Size = NumberSequence.new(ring.Size * s), Transparency = numberSequence({ { 0, 1 }, { 0.3, 0.45 }, { 0.7, 0.55 }, { 1, 1 } }),
        Color = colors({ { 0, c.Main }, { 1, c.Deep } }), LightEmission = 0.6, Brightness = 1.4,
    })
    flatEmitter(aura, aura.ground, 2, {
        Texture = STYLE.Textures.Fog, Lifetime = NumberRange.new(4), RotSpeed = ring.FogCounterSpin,
        Size = NumberSequence.new(ring.Size * s), Transparency = numberSequence({ { 0, 1 }, { 0.3, 0.35 }, { 0.7, 0.5 }, { 1, 1 } }),
        Color = colors({ { 0, c.Deep }, { 1, c.Ember } }), LightEmission = 0.7, Brightness = 1.6, ZOffset = 0.1,
    })
    flatEmitter(aura, aura.ground, 2.8, {
        Texture = STYLE.Textures.Slash, Lifetime = NumberRange.new(2.5), RotSpeed = NumberRange.new(ring.SlashSpin[1]),
        Size = NumberSequence.new(ring.Size * s), Transparency = numberSequence({ { 0, 1 }, { 0.15, 0 }, { 0.6, 0.2 }, { 1, 1 } }),
        Color = colors({ { 0, c.Core }, { 0.5, c.Gold }, { 1, c.Main } }), Brightness = 3, ZOffset = 0.2,
    })
    flatEmitter(aura, aura.ground, 2, {
        Texture = STYLE.Textures.Slash, Lifetime = NumberRange.new(3), RotSpeed = NumberRange.new(ring.SlashSpin[2]),
        Size = NumberSequence.new(ring.Size * s), Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.15 }, { 0.7, 0.35 }, { 1, 1 } }),
        Color = colors({ { 0, c.Main }, { 1, c.Deep } }), Brightness = 2.4, ZOffset = 0.2,
    })
    flatEmitter(aura, aura.ground, 4, {
        Texture = STYLE.Textures.Slash, Lifetime = NumberRange.new(1.4), RotSpeed = NumberRange.new(ring.SlashSpin[3]),
        Size = NumberSequence.new(ring.Size * s), Transparency = numberSequence({ { 0, 1 }, { 0.15, 0 }, { 1, 1 } }),
        Color = colors({ { 0, c.Core }, { 1, c.Gold } }), Brightness = 3.5, ZOffset = 0.25,
    })

    local spread = AuraKit.attachment(aura.ground)
    spread.CFrame = CFrame.Angles(0, 0, math.rad(90))
    addEmitter(aura, spread, 12, {
        Texture = STYLE.Textures.Fog, EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(999, 0),
        Speed = NumberRange.new(4 * s, 7 * s), Drag = 1.2, Lifetime = NumberRange.new(3, 4),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-80, 80),
        Size = numberSequence({ { 0, 2.5 * s }, { 1, 5.5 * s } }), Transparency = numberSequence({ { 0, 1 }, { 0.25, 0.82 }, { 1, 1 } }),
        Color = colors({ { 0, c.Main }, { 1, c.Ember } }), LightEmission = 0.4, Acceleration = Vector3.new(0, 0.4 * s, 0),
    })

    aura.debrisZone = newPart(aura, "DebrisZone", Vector3.new(9 * s, 0.4 * s, 9 * s))
    addEmitter(aura, aura.debrisZone, 18, {
        Texture = STYLE.Textures.Debris, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        FlipbookFramerate = NumberRange.new(0.001), FlipbookStartRandom = true,
        Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(12, 12),
        Speed = NumberRange.new(1.5 * s, 3 * s), Drag = 0.8, Acceleration = Vector3.new(0, 0.8 * s, 0),
        Lifetime = NumberRange.new(2.5, 3.5), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-80, 80),
        Size = numberSequence({ { 0, 0 }, { 0.12, 0.75 * s }, { 0.85, 0.65 * s }, { 1, 0 } }), Transparency = numberSequence({ { 0, 0 }, { 0.8, 0 }, { 1, 1 } }),
        Color = ColorSequence.new(STYLE.Colors.Debris), LightEmission = 0.15, LightInfluence = 0.3,
    })

    aura.sparkleZone = newPart(aura, "SparkleZone", Vector3.new(10 * s, 4 * s, 10 * s))
    addEmitter(aura, aura.sparkleZone, 60, {
        Texture = STYLE.Textures.Sparkle, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(2 * s), SpreadAngle = Vector2.new(360, 360), Acceleration = Vector3.new(0, 0.5 * s, 0),
        Lifetime = NumberRange.new(1.5), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40),
        Size = numberSequence({ { 0, 0 }, { 0.1, 0.9 * s }, { 0.2, 0 }, { 0.3, 0.8 * s }, { 0.4, 0 }, { 0.55, 0.9 * s }, { 0.65, 0 }, { 0.8, 0.7 * s }, { 1, 0 } }),
        Transparency = NumberSequence.new(0, 1),
        Color = colors({ { 0, c.Gold }, { 1, c.Core } }), LightEmission = 1, Brightness = 3,
    })
    addEmitter(aura, aura.sparkleZone, 28, {
        Texture = STYLE.Textures.Sparkle, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(1 * s, 2.5 * s), SpreadAngle = Vector2.new(15, 15),
        Lifetime = NumberRange.new(2, 3), Drag = 0.5, Acceleration = Vector3.new(0, 1 * s, 0),
        Size = numberSequence({ { 0, 0 }, { 0.2, 0.3 * s }, { 1, 0 } }),
        Color = colors({ { 0, c.Main }, { 1, c.Deep } }), LightEmission = 1, Brightness = 2.5,
    })
end

local function buildVortex(aura)
    local s = aura.k
    local c = STYLE.Colors
    aura.vortex = newPart(aura, "BeamVortex", Vector3.one * 0.2)
    aura.vortexBeams = {}
    local rings = {
        { Settings = STYLE.Vortex.Outer, Stage = 1, Color = colors({ { 0, c.Core }, { 0.45, c.Main }, { 1, c.Deep } }) },
        { Settings = STYLE.Vortex.Inner, Stage = 2, Color = colors({ { 0, c.Core }, { 1, c.Gold } }) },
    }
    for ringIndex, ring in rings do
        local settings = ring.Settings
        for index = 1, settings.Count do
            local angle = (index - 1) / settings.Count * TAU + (ringIndex - 1) * 0.3
            local outward = Vector3.new(math.cos(angle), 0, math.sin(angle))
            local tangent = Vector3.new(-math.sin(angle), 0, math.cos(angle)) * math.sign(settings.Twist)
            local base = AuraKit.attachment(aura.vortex)
            base.Position = outward * settings.Base * s + Vector3.new(0, 0.1 * s, 0)
            base.Axis = (Vector3.yAxis * 0.7 + tangent).Unit
            local twist = angle + settings.Twist
            local tip = AuraKit.attachment(aura.vortex)
            tip.Position = Vector3.new(math.cos(twist) * settings.Top * s, (settings.Height + (index % 3) * 0.9) * s, math.sin(twist) * settings.Top * s)
            tip.Axis = Vector3.yAxis
            local beam = AuraKit.beam(aura.vortex, base, tip, {
                Texture = STYLE.Textures.Energy,
                TextureLength = 3.2 * s,
                TextureSpeed = settings.Flow,
                LightEmission = 1,
                Brightness = 2.6,
                Color = ring.Color,
                Segments = 18,
                CurveSize0 = settings.Curve * s,
                CurveSize1 = settings.Curve * 0.5 * s,
                Width0 = settings.Width * s,
                Width1 = settings.Width * 0.15 * s,
            })
            table.insert(aura.vortexBeams, { Fade = AuraKit.fader(beam, VORTEX_FADE), Stage = ring.Stage })
        end
    end
end

local function buildOrbiters(aura)
    local s = aura.k
    local c = STYLE.Colors
    aura.orbiters = {}
    for index, spec in STYLE.Orbiters do
        local point = newPart(aura, "Orbiter" .. index, Vector3.one * 0.2)
        local trail = AuraKit.trail(point, 0.3 * s, STYLE.Textures.TrailWisp, 1.5, colors({ { 0, c.Core }, { 0.35, c.Gold }, { 1, c.Deep } }), 2.8)
        trail.Transparency = numberSequence({ { 0, 0 }, { 0.6, 0.35 }, { 1, 1 } })
        trail.WidthScale = numberSequence({ { 0, 1 }, { 1, 0.2 } })
        addEmitter(aura, point, 18, {
            Texture = STYLE.Textures.Sparkle, LightEmission = 1, Brightness = 3,
            Lifetime = NumberRange.new(0.25, 0.4), Speed = NumberRange.new(0),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90),
            Size = numberSequence({ { 0, 0.9 * s }, { 1, 0 } }), Color = colors({ { 0, c.Core }, { 1, c.Gold } }),
            LockedToPart = true,
        }, 2)
        table.insert(aura.orbiters, { Part = point, Trail = trail, Spec = spec })
    end
end

local function buildBody(aura)
    local s = aura.k
    local c = STYLE.Colors
    aura.volume = newPart(aura, "AuraBody", Vector3.new(2.6 * s, 4.6 * s, 2.6 * s))
    energyEmitter(aura, aura.volume, 38, {
        Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(0.5, 0.8), Speed = NumberRange.new(3 * s, 5 * s), SpreadAngle = Vector2.new(8, 8),
        Acceleration = Vector3.new(0, 5 * s, 0),
        Size = numberSequence({ { 0, 0.6 * s }, { 0.3, 2.4 * s }, { 1, 0.8 * s } }), Transparency = numberSequence({ { 0, 1 }, { 0.12, 0.35 }, { 0.7, 0.55 }, { 1, 1 } }),
        Color = colors({ { 0, c.Core }, { 0.35, c.Main }, { 1, c.Deep } }), ZOffset = -0.6,
    })
    energyEmitter(aura, aura.volume, 16, {
        Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Lifetime = NumberRange.new(0.4, 0.6), Speed = NumberRange.new(2 * s, 3.5 * s), SpreadAngle = Vector2.new(6, 6),
        Acceleration = Vector3.new(0, 4 * s, 0),
        Size = numberSequence({ { 0, 0.4 * s }, { 0.3, 1.5 * s }, { 1, 0.5 * s } }), Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.5 }, { 1, 1 } }),
        Color = colors({ { 0, c.Core }, { 1, c.Gold } }), Brightness = 2, ZOffset = -0.2,
    })
    addEmitter(aura, aura.volume, 20, {
        Texture = STYLE.Textures.Sparkle, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(8 * s, 14 * s), SpreadAngle = Vector2.new(6, 6), Drag = 1.5,
        Lifetime = NumberRange.new(0.5, 0.8),
        Size = numberSequence({ { 0, 0.5 * s }, { 1, 0 } }), Squash = numberSequence({ { 0, -1.6 }, { 1, -0.6 } }),
        Color = colors({ { 0, c.Core }, { 1, c.Main } }), LightEmission = 1, Brightness = 3,
    })
    local chest = AuraKit.attachment(aura.volume)
    chest.Position = Vector3.new(0, 0.3 * s, 0)
    addEmitter(aura, chest, 3, {
        Texture = STYLE.Textures.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(1.4, 1.8), LockedToPart = true,
        Size = numberSequence({ { 0, 6 * s }, { 0.5, 7.5 * s }, { 1, 6 * s } }), Transparency = numberSequence({ { 0, 1 }, { 0.3, 0.72 }, { 0.7, 0.75 }, { 1, 1 } }),
        Color = colors({ { 0, c.Main }, { 1, c.Deep } }), LightEmission = 1, Brightness = 1.5, ZOffset = -2,
    })

    aura.feet = newPart(aura, "AuraFeet", Vector3.one * 0.2)
    for index = 1, 8 do
        local angle = (index - 0.5) / 8 * TAU
        local spot = AuraKit.attachment(aura.feet)
        spot.Position = Vector3.new(math.cos(angle), 0, math.sin(angle)) * 1.8 * s
        energyEmitter(aura, spot, 6, {
            Lifetime = NumberRange.new(0.5, 0.75), Speed = NumberRange.new(3 * s, 5 * s), SpreadAngle = Vector2.new(10, 10),
            Acceleration = Vector3.new(0, 5 * s, 0),
            Size = numberSequence({ { 0, 0.4 * s }, { 0.35, 2.8 * s }, { 1, 0.8 * s } }), Transparency = numberSequence({ { 0, 1 }, { 0.12, 0.1 }, { 0.7, 0.4 }, { 1, 1 } }),
            Color = colors({ { 0, c.Main }, { 1, c.Deep } }),
        })
    end

    aura.burst = addEmitter(aura, aura.volume, 0, {
        Texture = STYLE.Textures.Sparkle,
        Color = colors({ { 0, c.Core }, { 1, c.Main } }),
        LightEmission = 1,
        Brightness = 4,
        Size = numberSequence({ { 0, 0.9 * s }, { 1, 0 } }),
        Lifetime = NumberRange.new(0.5, 0.9),
        Speed = NumberRange.new(16 * s, 26 * s),
        SpreadAngle = Vector2.new(70, 70),
        Acceleration = Vector3.new(0, -12 * s, 0),
        Drag = 1.5,
        EmissionDirection = Enum.NormalId.Top,
    })
    aura.blast = fireEmitter(aura, aura.volume, 0, {
        FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        LightEmission = 0.7,
        Brightness = 2.4,
        Size = numberSequence({ { 0, 0.4 * s }, { 0.3, 3 * s }, { 1, 4 * s } }),
        Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
        Lifetime = NumberRange.new(0.5, 0.8),
        Speed = NumberRange.new(8 * s, 14 * s),
        SpreadAngle = Vector2.new(180, 30),
        Drag = 3,
        Rotation = NumberRange.new(0, 360),
    })
    AuraKit.glow(aura, c.Main, c.Core, 20 * s)
end

local function buildWyrm(aura)
    local s = aura.k
    local head, glow = template("WyrmHead"), template("WyrmGlow")
    local headScale = STYLE.Wyrm.Head * s / math.max(head.Size.X, head.Size.Y, head.Size.Z)
    aura.wyrmHead = meshPart(aura, "WyrmHead", headScale, "Rock")
    aura.wyrmGlow = meshPart(aura, "WyrmGlow", headScale, "Eye")
    local offset = head.CFrame:ToObjectSpace(glow.CFrame)
    aura.wyrmGlowOffset = offset.Rotation + offset.Position * headScale
    aura.wyrmHeadSize = aura.wyrmHead.Size

    local shell = template("BeadShell")
    aura.beads = {}
    for index = 1, STYLE.Wyrm.Beads do
        local diameter = STYLE.Wyrm.Bead * s * (1 - 0.045 * (index - 1))
        local part = meshPart(aura, "BeadShell", diameter / shell.Size.X, "Rock")
        local core = newPart(aura, "BeadCore" .. index, Vector3.one * diameter * 0.72, Enum.PartType.Ball)
        AuraKit.dress(core, STYLE.Materials.Core)
        core.Transparency = 1
        table.insert(aura.beads, { Part = part, Core = core, Size = part.Size, CoreSize = core.Size, Phase = index * 0.9 })
    end
    local tail = aura.beads[#aura.beads]
    aura.wyrmTrail = AuraKit.trail(tail.Part, 0.25 * s, STYLE.Textures.Trail, 0.7, ColorSequence.new(STYLE.Colors.Main, STYLE.Colors.Deep), 3)
    aura.wyrmU = 0
end

local function buildHalo(aura)
    local s = aura.k
    local settings = STYLE.Halo
    local scale = fit("HaloRing", settings.Diameter * s)
    aura.halo = meshPart(aura, "HaloRing", scale, "Rock")
    aura.haloGlow = meshPart(aura, "HaloRing", scale * 1.04, "HaloGlow")
    aura.haloSize = { aura.halo.Size, aura.haloGlow.Size }
    aura.haloRadius = settings.Diameter * s / 2 / 1.29

    aura.haloAnchor = newPart(aura, "HaloAnchor", Vector3.one * 0.2)
    aura.ringPoints = {}
    for index = 1, settings.RingPoints do
        table.insert(aura.ringPoints, { Attachment = AuraKit.attachment(aura.haloAnchor), Angle = (index - 1) / settings.RingPoints * TAU })
    end
    aura.ringBeams = {}
    local quarter = #aura.ringPoints / 4
    for arc = 0, 3 do
        local from = aura.ringPoints[arc * quarter + 1].Attachment
        local to = aura.ringPoints[((arc + 1) % 4) * quarter + 1].Attachment
        local flow = AuraKit.beam(aura.haloAnchor, from, to, {
            Texture = STYLE.Textures.Flow,
            TextureLength = 3.2 * s,
            TextureSpeed = 1.1,
            LightEmission = 0.65,
            Brightness = 2.2,
            Segments = 24,
        })
        local core = AuraKit.beam(aura.haloAnchor, from, to, {
            Texture = STYLE.Textures.Rise,
            TextureLength = 3 * s,
            TextureSpeed = -2.2,
            LightEmission = 0.8,
            Brightness = 3,
            Color = ColorSequence.new(STYLE.Colors.Core),
            Segments = 24,
            ZOffset = 0.4,
        })
        table.insert(aura.ringBeams, { Flow = flow, Core = core, FlowFade = AuraKit.fader(flow, RING_FADE), CoreFade = AuraKit.fader(core, RING_FADE) })
    end

    aura.corona = {}
    for index = 1, settings.Corona do
        local point = aura.ringPoints[math.floor((index - 1) * #aura.ringPoints / settings.Corona) + 1]
        local tip = AuraKit.attachment(aura.haloAnchor)
        local beam = AuraKit.beam(aura.haloAnchor, point.Attachment, tip, {
            Texture = STYLE.Textures.Rise,
            TextureLength = 2.2 * s,
            TextureSpeed = aura.random:NextNumber(1.5, 2.2),
            LightEmission = 0.6,
            Brightness = 2.4,
            Segments = 8,
        })
        table.insert(aura.corona, { Beam = beam, Point = point, Tip = tip, Phase = index * 2.7, Reach = aura.random:NextNumber(1.4, 2.6) * s, Fade = AuraKit.fader(beam, CORONA_FADE) })
    end

    for index = 1, #aura.ringPoints, 2 do
        fireEmitter(aura, aura.ringPoints[index].Attachment, 6, {
            Size = numberSequence({ { 0, 1.1 * s }, { 0.4, 2.6 * s }, { 1, 0.8 * s } }),
            Transparency = numberSequence({ { 0, 1 }, { 0.1, 0.1 }, { 0.7, 0.4 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.5, 0.8),
            Speed = NumberRange.new(2 * s, 4 * s),
            SpreadAngle = Vector2.new(20, 20),
            Acceleration = Vector3.new(0, 4 * s, 0),
            EmissionDirection = Enum.NormalId.Top,
        }, 3)
        addEmitter(aura, aura.ringPoints[index].Attachment, 3, {
            Texture = STYLE.Textures.Ember,
            Color = ColorSequence.new(STYLE.Colors.Core, STYLE.Colors.Deep),
            LightEmission = 1,
            Brightness = 4,
            Size = numberSequence({ { 0, 0.3 * s }, { 1, 0 } }),
            Lifetime = NumberRange.new(0.8, 1.4),
            Speed = NumberRange.new(3 * s, 6 * s),
            SpreadAngle = Vector2.new(35, 35),
            Acceleration = Vector3.new(0, 2 * s, 0),
            EmissionDirection = Enum.NormalId.Top,
        }, 3)
    end
end

local function onSurge(aura, strength)
    aura.burst:Emit(math.round(30 * strength * aura.detail))
    aura.blast:Emit(math.round(14 * strength * aura.detail))
end

local function onStage(aura, stage)
    if stage == 2 then
        aura.wyrmTrail.Enabled = true
        for _, orbiter in aura.orbiters do
            orbiter.Trail.Enabled = true
        end
    end
end

local function onHide(aura)
    aura.wyrmTrail.Enabled = false
    for _, orbiter in aura.orbiters do
        orbiter.Trail.Enabled = false
    end
    if aura.stage > 0 then
        aura.blast:Emit(math.round(10 * aura.detail))
    end
end

function EmberCrucibleAura.build(player, character, rootPart, _petId, rankId)
    if not AuraKit.hasTemplates(SET, MESHES) then
        return nil
    end
    local aura = AuraKit.newAura(player, character, rootPart, rankId, SET, STYLE)
    aura.rise = 0
    aura.wyrmLevel = 0
    aura.crownLevel = 0
    aura.onSurge = onSurge
    aura.onStage = onStage
    aura.onHide = onHide

    buildGround(aura)
    buildVortex(aura)
    buildBody(aura)
    buildOrbiters(aura)
    buildWyrm(aura)
    buildHalo(aura)
    return aura
end

EmberCrucibleAura.show = AuraKit.show
EmberCrucibleAura.hide = AuraKit.hide
EmberCrucibleAura.pulse = function(aura)
    AuraKit.surge(aura, 1)
end
EmberCrucibleAura.destroy = AuraKit.destroy

local function wyrmPoint(aura, seat, u, level)
    local s = aura.k
    local radius = STYLE.Wyrm.Radius * s * (0.55 + 0.45 * level)
    local height = (2.8 + 1.6 * math.sin(u * 0.43)) * s * level - (1 - level) * 3 * s
    return seat + Vector3.new(math.cos(u) * radius, height + 0.25 * s * math.sin(u * 2.1), math.sin(u) * radius)
end

function EmberCrucibleAura.update(aura, now, parts, cframes)
    local s = aura.k
    local frame = AuraKit.step(aura, now)
    local deltaTime, fade, live, surge, spin = frame.deltaTime, frame.fade, frame.live, frame.surge, frame.spin
    local seat, floor = frame.seat, frame.floor
    local flicker = 0.85 + 0.15 * math.noise(now * 4.3, 0.5) + 0.1 * math.sin(now * 11)

    aura.rise = approach(aura.rise, if live and aura.stage > 0 then 1 else 0, if live then 2.4 else 3, deltaTime)
    aura.wyrmLevel = approach(aura.wyrmLevel, if live and aura.stage >= 2 then 1 else 0, 1.4, deltaTime)
    aura.crownLevel = approach(aura.crownLevel, if live and aura.stage >= 3 then 1 else 0, 1.5, deltaTime)

    local function place(part, cframe)
        table.insert(parts, part)
        table.insert(cframes, cframe)
    end

    place(aura.ground, CFrame.new(floor + Vector3.new(0, 0.1 * s, 0)))
    place(aura.debrisZone, CFrame.new(floor + Vector3.new(0, 0.2 * s, 0)))
    place(aura.sparkleZone, CFrame.new(floor + Vector3.new(0, 2 * s, 0)))
    place(aura.volume, CFrame.new(seat + Vector3.new(0, 2.2 * s, 0)))
    place(aura.feet, CFrame.new(seat + Vector3.new(0, 0.4 * s, 0)))

    place(aura.vortex, CFrame.new(floor) * CFrame.Angles(0, now * STYLE.Vortex.Spin, 0))
    local beamAmount = { fade * aura.rise, fade * aura.wyrmLevel }
    for _, entry in aura.vortexBeams do
        AuraKit.fadeBeam(entry.Fade, beamAmount[entry.Stage])
    end

    for _, orbiter in aura.orbiters do
        local spec = orbiter.Spec
        local angle = now * spec.Speed + spec.Phase
        local radius = spec.Radius * s * (1 + 0.12 * math.sin(now * 1.7 + spec.Phase)) * (0.4 + 0.6 * aura.wyrmLevel)
        local height = (spec.Height + spec.Rise * math.sin(now * 1.3 + spec.Phase)) * s
        place(orbiter.Part, CFrame.new(floor + Vector3.new(math.cos(angle) * radius, height, math.sin(angle) * radius)))
    end

    local level = aura.wyrmLevel
    aura.wyrmU += deltaTime * (0.75 + 0.25 * aura.power + 1.2 * surge)
    local u = aura.wyrmU
    local gap = STYLE.Wyrm.Gap * s / (STYLE.Wyrm.Radius * s * (0.55 + 0.45 * level))
    local headAt = wyrmPoint(aura, seat, u, level)
    local headCF = CFrame.lookAt(headAt, wyrmPoint(aura, seat, u + 0.05, level)) * CFrame.Angles(0.15 * math.sin(now * 3), 0, 0)
    local present = fade * math.min(1, level * 1.5)
    aura.wyrmHead.Size = aura.wyrmHeadSize
    place(aura.wyrmHead, headCF)
    place(aura.wyrmGlow, headCF * aura.wyrmGlowOffset)
    showPart(aura.wyrmHead, 0, present)
    showPart(aura.wyrmGlow, 0, present)
    for index, bead in aura.beads do
        local at = wyrmPoint(aura, seat, u - index * gap, level)
        local pulse = 0.5 + 0.5 * math.sin(now * 5 - index * 0.6)
        local cframe = CFrame.new(at) * CFrame.Angles(now * 0.8 + bead.Phase, now * 0.5, bead.Phase)
        place(bead.Part, cframe)
        place(bead.Core, cframe)
        bead.Core.Size = bead.CoreSize * (0.92 + 0.12 * pulse + 0.15 * surge)
        bead.Core.Color = STYLE.Materials.Core.Color:Lerp(STYLE.Colors.Core, 0.45 * pulse)
        showPart(bead.Part, 0, present)
        showPart(bead.Core, 0, present)
    end

    local head = aura.character:FindFirstChild("Head")
    local headPosition = if head and head:IsA("BasePart") then head.Position else seat + Vector3.new(0, 3 * s, 0)
    local grow = 0.15 + 0.85 * smoothstep(0, 1, aura.crownLevel) + 0.12 * surge
    local haloCF = CFrame.new(headPosition) * frame.facing * CFrame.new(0, STYLE.Halo.Lift * s, STYLE.Halo.Back * s)
    local turn = CFrame.Angles(0, 0, spin * 0.3)
    local crown = fade * aura.crownLevel
    aura.halo.Size = aura.haloSize[1] * grow
    aura.haloGlow.Size = aura.haloSize[2] * grow
    place(aura.halo, haloCF * turn)
    place(aura.haloGlow, haloCF * turn)
    place(aura.haloAnchor, haloCF * turn)
    showPart(aura.halo, 0, crown)
    showPart(aura.haloGlow, STYLE.Materials.HaloGlow.Transparency, crown * (0.8 + 0.2 * flicker))
    local ringRadius = aura.haloRadius * grow
    for _, point in aura.ringPoints do
        point.Attachment.CFrame = CFrame.new(math.cos(point.Angle) * ringRadius, math.sin(point.Angle) * ringRadius, 0)
            * CFrame.Angles(0, 0, point.Angle - math.pi / 2)
    end
    local bend = -0.5523 * ringRadius
    for _, ring in aura.ringBeams do
        local width = (1.5 + 0.25 * flicker) * s * grow
        ring.Flow.Width0, ring.Flow.Width1 = width, width
        ring.Core.Width0, ring.Core.Width1 = 0.45 * s * grow, 0.45 * s * grow
        ring.Flow.CurveSize0, ring.Flow.CurveSize1 = bend, bend
        ring.Core.CurveSize0, ring.Core.CurveSize1 = bend, bend
        AuraKit.fadeBeam(ring.FlowFade, crown)
        AuraKit.fadeBeam(ring.CoreFade, crown)
    end
    for _, flare in aura.corona do
        local lick = (0.7 + 0.45 * math.noise(now * 2.4, flare.Phase) + 0.5 * surge) * grow
        local angle = flare.Point.Angle + 0.25 * math.noise(now * 1.3, flare.Phase, 2)
        local reach = ringRadius + flare.Reach * math.max(lick, 0.05)
        flare.Tip.Position = Vector3.new(math.cos(angle) * reach, math.sin(angle) * reach, 0)
        flare.Beam.Width0 = 0.75 * s * grow
        flare.Beam.Width1 = 0.1 * s
        AuraKit.fadeBeam(flare.Fade, crown)
    end

    AuraKit.finishGlow(aura, frame, 1.6 * flicker, 0.06, 0.35)
end

return EmberCrucibleAura

-- Qinggong leap VFX: the cultivator rides a current of Qi rather than simply jumping.
--
--   Takeoff  (a jump from the ground): a Qi formation blooms over a turning vortex as the feet
--            leave the ground, with wind streaks rising and auspicious clouds puffing out round it.
--   Leap     (each air leap): the foot steps on the void. A small formation and a ripple ring
--            open where it pushes off, clouds burst from the step and linger (each leap leaves
--            a stepping-stone of cloud in the sky), streaks shoot downward and the step flashes.
--   Ascend   (after each leap): curved energy trails from the feet, a silk ribbon of Qi from the
--            shoulders, and a current of Qi spiralling round the body as it rises. The legs stride
--            as if climbing steps in the air, alternating with each leap (see pose).
--   Glide    (holding jump while falling): riding the clouds. A stream of cloud pours from under
--            the feet and wind lines rush past the body.
--   Land     (touching down after any of the above, or a hard fall): a starburst, a formation
--            flash, shockwave rings, sharp Qi spikes, rolling cloud and glittering Qi mist, all
--            scaled by impact.
--
-- Every cloud is line-drawn auspicious cloud riding on a bank of soft fog (the fog, vortex,
-- starburst and glitter textures come from the PDS' Particles & Models Kit).
--
-- The colour style follows the cultivator's realm (azure, jade, gold, violet). Effects play
-- here at once for the local player; other players' arrive through QinggongFxEvent (the
-- server relays them) and are skipped beyond MAX_DISTANCE from the camera. Everything is
-- client-side and cosmetic: it never affects movement. PoseController reads pose(player).
local ContentProvider = game:GetService("ContentProvider")
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local QinggongFx = {}

local TEXTURES = {
    Formation = "rbxassetid://86025672711867",
    Shockwave = "rbxassetid://130173906719836",
    Clouds = "rbxassetid://138514806240957", -- 2x2 flipbook of four auspicious clouds
    Spike = "rbxassetid://89522570963572",
    Streak = "rbxassetid://115312010132075",
    Ribbon = "rbxassetid://99893839045856",
    Glow = "rbxassetid://135169457468310", -- shared with the auras
    -- from the PDS' Particles & Models Kit
    Fog = "rbxassetid://14050223758",        -- a soft billowing puff: the body behind each cloud
    GlitterFog = "rbxassetid://14049414463", -- Qi mist shot through with glints
    Vortex = "rbxassetid://14050094484",     -- a spiral that turns under the formations
    Flare = "rbxassetid://14054628491",      -- a starburst for the moment of impact
}

-- Core is the near-white heart of the light, Main the body of the effect, Deep its fading edge,
-- Accent the warm glint at the brightest moments (the step flash and the landing).
local PALETTES = {
    Azure = { Core = Color3.fromRGB(225, 244, 255), Main = Color3.fromRGB(90, 176, 255), Deep = Color3.fromRGB(40, 82, 235), Accent = Color3.fromRGB(255, 228, 160) },
    Jade = { Core = Color3.fromRGB(222, 255, 240), Main = Color3.fromRGB(56, 226, 178), Deep = Color3.fromRGB(16, 128, 120), Accent = Color3.fromRGB(255, 236, 170) },
    Gold = { Core = Color3.fromRGB(255, 249, 222), Main = Color3.fromRGB(255, 198, 76), Deep = Color3.fromRGB(222, 118, 30), Accent = Color3.fromRGB(255, 255, 235) },
    Violet = { Core = Color3.fromRGB(242, 226, 255), Main = Color3.fromRGB(172, 108, 255), Deep = Color3.fromRGB(92, 40, 214), Accent = Color3.fromRGB(255, 205, 250) },
}
local REALM_PALETTE = {
    ["Qi Awakening"] = "Azure",
    ["Qi Foundation"] = "Azure",
    ["Spirit Core"] = "Jade",
    ["Spirit Soul"] = "Jade",
    ["Ascendant Realm"] = "Gold",
    ["Immortal Realm"] = "Gold",
} -- Divine Realm and above: Violet

local MAX_DISTANCE = 250        -- other players' effects beyond this distance from the camera are skipped
local OTHERS_DETAIL = 0.6       -- other players' effects use this share of the particles
local LEAP_POSE_TIME = 0.55     -- how long the leap poses hold after a takeoff or an air leap
local STEP_TIME = 0.2           -- the first part of it: the stepping stride, before the knees tuck
local ASCEND_TIME = 0.6         -- how long the trails, ribbon and spiral run after an air leap
local GROUND_LIFT = 0.35        -- flat ground effects float this far up, clear of terrain grass

local fxFolder = Instance.new("Folder")
fxFolder.Name = "QinggongFx"
fxFolder.Parent = Workspace

task.spawn(function()
    local images = {}
    for _, id in TEXTURES do
        local decal = Instance.new("Decal")
        decal.Texture = id
        table.insert(images, decal)
    end
    ContentProvider:PreloadAsync(images)
end)

-- ---------- helpers ----------
local function paletteFor(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return PALETTES[rank and REALM_PALETTE[rank.Realm] or (rank and "Violet" or "Azure")]
end

local function rootOf(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if humanoid and root and humanoid.Health > 0 then
        return character, humanoid, root
    end
    return nil
end

local function feetOffset(humanoid, root)
    return humanoid.HipHeight + root.Size.Y / 2
end

-- The ground under a character (or nil when there is none within reach).
local function groundBelow(character, root, reach)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { character, fxFolder }
    local hit = Workspace:Raycast(root.Position, Vector3.new(0, -reach, 0), params)
    return hit and hit.Position
end

local function inRange(root)
    local camera = Workspace.CurrentCamera
    return camera ~= nil and (camera.CFrame.Position - root.Position).Magnitude <= MAX_DISTANCE
end

local function emitter(parent, properties)
    local e = Instance.new("ParticleEmitter")
    e.Rate = 0
    e.LightInfluence = 0
    e.LightEmission = 1
    for property, value in properties do
        e[property] = value
    end
    e.Parent = parent
    return e
end

local function count(n, detail)
    return math.max(1, math.floor(n * detail + 0.5))
end

-- A short-lived invisible anchored part to hold a burst's emitters; it removes itself.
local function host(position, size, life)
    local part = Instance.new("Part")
    part.Name = "QinggongBurst"
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Transparency = 1
    part.Size = size
    part.CFrame = CFrame.new(position)
    part.Parent = fxFolder
    Debris:AddItem(part, life)
    return part
end

-- Particles that lie flat on the ground (VelocityPerpendicular with a token upward speed).
local FLAT = {
    Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
    EmissionDirection = Enum.NormalId.Top,
    Speed = NumberRange.new(0.01),
}
local function flat(parent, properties)
    local merged = table.clone(FLAT)
    for property, value in properties do
        merged[property] = value
    end
    return emitter(parent, merged)
end

local CLOUD = {
    Texture = TEXTURES.Clouds,
    FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2,
    FlipbookMode = Enum.ParticleFlipbookMode.Loop,
    FlipbookFramerate = NumberRange.new(0),
    FlipbookStartRandom = true,
    LightEmission = 0.55,
    Rotation = NumberRange.new(-12, 12),
    RotSpeed = NumberRange.new(-18, 18),
}
local function cloud(parent, properties)
    local merged = table.clone(CLOUD)
    for property, value in properties do
        merged[property] = value
    end
    return emitter(parent, merged)
end

local function scaled(sequence, k)
    local keypoints = {}
    for _, point in sequence.Keypoints do
        table.insert(keypoints, NumberSequenceKeypoint.new(point.Time, point.Value * k, point.Envelope * k))
    end
    return NumberSequence.new(keypoints)
end

local function faded(sequence, amount)
    local keypoints = {}
    for _, point in sequence.Keypoints do
        table.insert(keypoints, NumberSequenceKeypoint.new(point.Time, point.Value + (1 - point.Value) * amount))
    end
    return NumberSequence.new(keypoints)
end

-- A burst of auspicious clouds with soft volume: the line-drawn clouds ride on a bank of fog
-- that moves the same way, a little larger and fainter, behind them.
local function puff(parent, properties, n, detail)
    cloud(parent, properties):Emit(count(n, detail))
    local body = table.clone(properties)
    body.Texture = TEXTURES.Fog
    body.Size = scaled(properties.Size, 1.45)
    body.Transparency = faded(properties.Transparency, 0.22)
    body.LightEmission = 0.35
    body.Brightness = (properties.Brightness or 1) * 0.8
    body.Rotation = NumberRange.new(0, 360)
    body.RotSpeed = NumberRange.new(-25, 25)
    body.ZOffset = -0.3
    emitter(parent, body):Emit(count(math.max(1, n * 0.6), detail))
end

local function flash(position, color, brightness, range)
    local holder = host(position, Vector3.new(0.2, 0.2, 0.2), 0.6)
    local light = Instance.new("PointLight")
    light.Color = color
    light.Brightness = brightness
    light.Range = range
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
end

-- ---------- bursts in the world ----------
local function takeoff(p, ground, detail)
    local centre = host(ground + Vector3.new(0, GROUND_LIFT, 0), Vector3.new(0.2, 0.2, 0.2), 1.2)
    flat(centre, {
        Texture = TEXTURES.Formation, Lifetime = NumberRange.new(0.6),
        Size = numberSequence({ { 0, 0.6 }, { 0.15, 5.2 }, { 1, 5.8 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.08, 0.12 }, { 0.55, 0.3 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 0.1, p.Main }, { 1, p.Deep } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(70, 90), Brightness = 2,
    }):Emit(1)
    flat(centre, {
        Texture = TEXTURES.Vortex, Lifetime = NumberRange.new(0.55), ZOffset = -0.1,
        Size = numberSequence({ { 0, 1 }, { 0.3, 4.6 }, { 1, 5.2 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.3 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 0.2, p.Main }, { 1, p.Deep } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-260, -220), Brightness = 1.6,
    }):Emit(1)
    flat(centre, {
        Texture = TEXTURES.Shockwave, Lifetime = NumberRange.new(0.35), ZOffset = 0.1,
        Size = numberSequence({ { 0, 1 }, { 0.3, 4.5 }, { 1, 6.5 } }),
        Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
    }):Emit(1)
    local ring = host(ground + Vector3.new(0, 0.3, 0), Vector3.new(3, 0.2, 3), 1.6)
    emitter(ring, {
        Texture = TEXTURES.Streak, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapePartial = 1, EmissionDirection = Enum.NormalId.Top, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(24, 34), SpreadAngle = Vector2.new(6, 6), Lifetime = NumberRange.new(0.16, 0.24),
        Size = numberSequence({ { 0, 1.4 }, { 1, 0.6 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.5,
    }):Emit(count(7, detail))
    puff(ring, {
        Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(6, 10), Drag = 4, Acceleration = Vector3.new(0, 1.2, 0), Lifetime = NumberRange.new(0.6, 0.9),
        Size = numberSequence({ { 0, 1.0 }, { 0.4, 2.1 }, { 1, 2.6 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.12, 0.25 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.5) }, { 0.4, p.Main }, { 1, p.Deep } }), Brightness = 1.6,
    }, 5, detail)
end

local function step(p, feet, power, detail)
    local s = 0.85 + 0.3 * power
    local centre = host(feet, Vector3.new(0.2, 0.2, 0.2), 1.0)
    flat(centre, {
        Texture = TEXTURES.Formation, Lifetime = NumberRange.new(0.45),
        Size = numberSequence({ { 0, 0.5 }, { 0.2, 4.2 * s }, { 1, 4.6 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.06, 0.08 }, { 0.5, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 0.1, p.Main }, { 1, p.Deep } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(150, 190), Brightness = 2.4,
    }):Emit(1)
    flat(centre, {
        Texture = TEXTURES.Vortex, Lifetime = NumberRange.new(0.4), ZOffset = -0.1,
        Size = numberSequence({ { 0, 0.8 }, { 0.3, 3.6 * s }, { 1, 4 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.12, 0.3 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 0.2, p.Main }, { 1, p.Deep } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-340, -300), Brightness = 1.6,
    }):Emit(1)
    flat(centre, {
        Texture = TEXTURES.Shockwave, Lifetime = NumberRange.new(0.32), ZOffset = 0.1,
        Size = numberSequence({ { 0, 1.5 }, { 0.3, 6.5 * s }, { 1, 9 * s } }),
        Transparency = numberSequence({ { 0, 0.05 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.4,
    }):Emit(1)
    emitter(centre, {
        Texture = TEXTURES.Glow, Lifetime = NumberRange.new(0.16), ZOffset = 0.3,
        Size = numberSequence({ { 0, 2.6 * s }, { 1, 0.4 } }), Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Accent }, { 1, p.Main } }), Speed = NumberRange.new(0), Brightness = 2,
    }):Emit(1)
    local ring = host(feet, Vector3.new(2.4, 0.2, 2.4), 1.8)
    puff(ring, {
        Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(9, 14), Drag = 3.5, Acceleration = Vector3.new(0, -1.5, 0), Lifetime = NumberRange.new(1.0, 1.4),
        Size = numberSequence({ { 0, 1.4 }, { 0.3, 2.8 * s }, { 1, 3.4 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.08, 0.2 }, { 0.7, 0.55 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.5) }, { 0.4, p.Main }, { 1, p.Deep } }), Brightness = 1.6,
    }, 7, detail)
    emitter(ring, {
        Texture = TEXTURES.Streak, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapePartial = 1, EmissionDirection = Enum.NormalId.Bottom, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(30, 42), SpreadAngle = Vector2.new(10, 10), Lifetime = NumberRange.new(0.18, 0.25),
        Size = numberSequence({ { 0, 1.9 }, { 1, 0.7 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.5,
    }):Emit(count(8, detail))
end

local function impact(p, ground, strength, detail, withLight)
    local s = 0.6 + 0.6 * strength
    local centre = host(ground + Vector3.new(0, GROUND_LIFT, 0), Vector3.new(0.2, 0.2, 0.2), 1.4)
    flat(centre, {
        Texture = TEXTURES.Formation, Lifetime = NumberRange.new(0.55),
        Size = numberSequence({ { 0, 1 }, { 0.12, 7 * s }, { 1, 7.8 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.05, 0.05 }, { 0.5, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Accent }, { 0.1, p.Main }, { 1, p.Deep } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-70, -50), Brightness = 2.4,
    }):Emit(1)
    local wave = flat(centre, {
        Texture = TEXTURES.Shockwave, Lifetime = NumberRange.new(0.45), ZOffset = 0.1,
        Size = numberSequence({ { 0, 1 }, { 0.25, 8 * s }, { 1, 12 * s } }),
        Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.6,
    })
    wave:Emit(1)
    task.delay(0.08, function()
        if wave.Parent then
            wave:Emit(1) -- a second, trailing ring
        end
    end)
    emitter(centre, {
        Texture = TEXTURES.Flare, Lifetime = NumberRange.new(0.24), ZOffset = 0.4,
        Size = numberSequence({ { 0, 2 * s }, { 0.25, 7 * s }, { 1, 8 * s } }), Transparency = numberSequence({ { 0, 0.05 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Accent }, { 0.4, p.Main }, { 1, p.Deep } }), Speed = NumberRange.new(0),
        Rotation = NumberRange.new(0, 360), Brightness = 2,
    }):Emit(1)
    local ring = host(ground + Vector3.new(0, 0.3, 0), Vector3.new(3.2, 0.2, 3.2), 1.8)
    emitter(ring, {
        Texture = TEXTURES.Spike, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapePartial = 1, EmissionDirection = Enum.NormalId.Top, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(18, 34), SpreadAngle = Vector2.new(24, 24), Acceleration = Vector3.new(0, -40, 0),
        Lifetime = NumberRange.new(0.22, 0.34), Size = numberSequence({ { 0, 3.2 * s }, { 0.6, 2.6 * s }, { 1, 0.6 } }),
        Transparency = numberSequence({ { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 0.5, p.Main }, { 1, p.Deep } }), Brightness = 3,
    }):Emit(count(8 + 12 * strength, detail))
    emitter(ring, {
        Texture = TEXTURES.Streak, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Orientation = Enum.ParticleOrientation.VelocityParallel, Speed = NumberRange.new(30, 45),
        Lifetime = NumberRange.new(0.14, 0.22), Size = numberSequence({ { 0, 2 }, { 1, 0.8 } }),
        Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }), Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.4,
    }):Emit(count(10, detail))
    puff(ring, {
        Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(10, 16), Drag = 4, Acceleration = Vector3.new(0, 1.5, 0), Lifetime = NumberRange.new(0.9, 1.2),
        Size = numberSequence({ { 0, 1.4 }, { 0.3, 3 * s }, { 1, 3.8 * s } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.1, 0.2 }, { 0.7, 0.5 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.5) }, { 0.4, p.Main }, { 1, p.Deep } }), Brightness = 1.6,
    }, 6 + 6 * strength, detail)
    -- glittering Qi mist rolling out low across the ground
    emitter(ring, {
        Texture = TEXTURES.GlitterFog, Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(7, 11), Drag = 3, Lifetime = NumberRange.new(0.8, 1.1), LightEmission = 0.7,
        Size = numberSequence({ { 0, 2 * s }, { 1, 5.5 * s } }), Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.45 }, { 1, 1 } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30),
        Color = colorSequence({ { 0, p.Core }, { 0.4, p.Main }, { 1, p.Deep } }), Brightness = 1.6,
    }):Emit(count(4 + 2 * strength, detail))
    if withLight then
        flash(ground + Vector3.new(0, 2, 0), p.Main, 2 * strength + 0.6, 18)
    end
end

-- ---------- what follows the body: trails, ribbon, spiral current, cloud stream ----------
local rigs = {} -- [character] = rig

local function trailBetween(parent, a0, a1, properties)
    local trail = Instance.new("Trail")
    trail.Attachment0 = a0
    trail.Attachment1 = a1
    trail.FaceCamera = true
    trail.LightInfluence = 0
    trail.LightEmission = 1
    trail.Enabled = false
    for property, value in properties do
        trail[property] = value
    end
    trail.Parent = parent
    return trail
end

local function attachment(parent, name, position)
    local a = Instance.new("Attachment")
    a.Name = name
    a.Position = position
    a.Parent = parent
    return a
end

local function buildRig(character, humanoid, root, p)
    local rig = { character = character, root = root, palette = p, trails = {}, ascendUntil = 0, gliding = false, angle = 0, active = false }
    -- energy trails from each foot (their width runs across the foot, so they stay full whether
    -- the body rises or glides forward)
    for _, side in { "Left", "Right" } do
        local foot = character:FindFirstChild(side .. "Foot")
        local base = if foot then Vector3.new(0, -0.1, 0) else Vector3.new(side == "Left" and -0.5 or 0.5, -feetOffset(humanoid, root) + 0.3, 0)
        local parent = foot or root
        local a0 = attachment(parent, "QinggongTrailA", base + Vector3.new(-0.3, 0, 0))
        local a1 = attachment(parent, "QinggongTrailB", base + Vector3.new(0.3, 0, 0))
        table.insert(rig.trails, trailBetween(parent, a0, a1, {
            Name = "QinggongFootTrail", Texture = TEXTURES.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.35,
            Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.2,
            Transparency = numberSequence({ { 0, 0.15 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.2 } }),
        }))
    end
    -- the silk ribbon across the shoulders, streaming behind the rise (only then: held through a
    -- glide it would hang over the body as a wide sheet)
    local torso = character:FindFirstChild("UpperTorso") or root
    local r0 = attachment(torso, "QinggongRibbonA", Vector3.new(-0.7, 0.2, 0.55))
    local r1 = attachment(torso, "QinggongRibbonB", Vector3.new(0.7, 0.2, 0.55))
    rig.ribbon = trailBetween(torso, r0, r1, {
        Name = "QinggongRibbon", Texture = TEXTURES.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.4,
        Color = colorSequence({ { 0, p.Core }, { 0.1, p.Main }, { 1, p.Deep } }), Brightness = 1.8,
        Transparency = numberSequence({ { 0, 0.5 }, { 0.5, 0.68 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.15 } }),
    })
    -- the spiral current: a short ribbon carried round the body while it rises
    rig.orbit0 = attachment(root, "QinggongOrbitA", Vector3.zero)
    rig.orbit1 = attachment(root, "QinggongOrbitB", Vector3.zero)
    rig.spiral = trailBetween(root, rig.orbit0, rig.orbit1, {
        Name = "QinggongSpiral", Texture = TEXTURES.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.45,
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
        Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.3 } }),
    })
    -- clouds shed from the feet: a light trail of them while rising, a full stream while gliding
    local feet = attachment(root, "QinggongFeet", Vector3.new(0, -feetOffset(humanoid, root), 0))
    rig.wisps = cloud(feet, {
        Speed = NumberRange.new(0.5, 1.5), Lifetime = NumberRange.new(0.6, 0.8),
        Size = numberSequence({ { 0, 0.6 }, { 0.3, 1.3 }, { 1, 1.6 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.5) }, { 1, p.Main } }), Brightness = 1.4,
    })
    -- the cloud it rides: a few large clouds held under the feet, carried along with the body
    -- (an attachment emits along its +Y: this one is turned over so the clouds spill downward and
    -- out beneath the feet rather than up into the body)
    local cradle = attachment(root, "QinggongCradle", Vector3.new(0, -feetOffset(humanoid, root) - 1.1, 0))
    cradle.Orientation = Vector3.new(180, 0, 0)
    rig.stream = cloud(cradle, {
        LockedToPart = true, Speed = NumberRange.new(0.6, 1.4), SpreadAngle = Vector2.new(75, 75),
        Lifetime = NumberRange.new(0.8, 1.1), Rotation = NumberRange.new(-8, 8), RotSpeed = NumberRange.new(-6, 6),
        Size = numberSequence({ { 0, 2.2 }, { 0.35, 3.8 }, { 1, 4.2 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.25, 0.3 }, { 0.75, 0.45 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.5) }, { 0.4, p.Main }, { 1, p.Deep } }), Brightness = 1.4,
    })
    rig.streamFog = emitter(cradle, {
        Texture = TEXTURES.Fog, LockedToPart = true, Speed = NumberRange.new(0.4, 1), SpreadAngle = Vector2.new(75, 75),
        Lifetime = NumberRange.new(1.0, 1.3), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-20, 20),
        Size = numberSequence({ { 0, 3 }, { 0.4, 5 }, { 1, 5.6 } }), LightEmission = 0.35, ZOffset = -0.3,
        Transparency = numberSequence({ { 0, 1 }, { 0.3, 0.55 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Main }, { 1, p.Deep } }), Brightness = 1.2,
    })
    -- and the wisps it sheds: small clouds that lag only a little behind before fading
    rig.shed = cloud(feet, {
        VelocityInheritance = 0.7, Speed = NumberRange.new(0.5, 1.5), SpreadAngle = Vector2.new(180, 180),
        Lifetime = NumberRange.new(0.5, 0.7),
        Size = numberSequence({ { 0, 0.8 }, { 0.3, 1.3 }, { 1, 1.5 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.55 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Main }, { 1, p.Deep } }), Brightness = 1.2,
    })
    -- wind lines rushing past while gliding (the root part's box spreads them round the body)
    rig.wind = emitter(root, {
        Name = "QinggongWind", Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Back, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(26, 36), SpreadAngle = Vector2.new(6, 6), Lifetime = NumberRange.new(0.18, 0.28),
        Size = numberSequence({ { 0, 2.6 }, { 1, 1.4 } }), Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.45 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 1.8,
    })
    rig.detail = 1
    rigs[character] = rig
    character.Destroying:Connect(function()
        rigs[character] = nil
    end)
    return rig
end

local function rigFor(player)
    local character, humanoid, root = rootOf(player)
    if not character then
        return nil
    end
    local p = paletteFor(player)
    local rig = rigs[character]
    if rig and rig.palette ~= p then
        -- the realm changed: rebuild in the new colours
        for _, child in character:GetDescendants() do
            if string.sub(child.Name, 1, 8) == "Qinggong" and (child:IsA("Trail") or child:IsA("Attachment") or child:IsA("ParticleEmitter")) then
                child:Destroy()
            end
        end
        rig = nil
    end
    rig = rig or buildRig(character, humanoid, root, p)
    rig.detail = if player == Players.LocalPlayer then 1 else OTHERS_DETAIL
    return rig, humanoid, root
end

local function setTrail(trail, on)
    if on and not trail.Enabled then
        trail:Clear()
    end
    trail.Enabled = on
end

local function updateRig(rig, deltaTime, now)
    local root = rig.root
    local visible = root.Parent ~= nil and inRange(root)
    local ascending = visible and now < rig.ascendUntil
    local gliding = visible and rig.gliding
    for _, trail in rig.trails do
        setTrail(trail, ascending or gliding)
    end
    setTrail(rig.ribbon, ascending)
    if ascending then
        -- about one turn round the body while rising, climbing from the feet to the head
        local t = 1 - (rig.ascendUntil - now) / ASCEND_TIME
        rig.angle += deltaTime * 11
        local y = -1.8 + 3.4 * t
        local offset = Vector3.new(math.cos(rig.angle), 0, math.sin(rig.angle)) * 2.3
        rig.orbit0.Position = offset + Vector3.new(0, y - 0.35, 0)
        rig.orbit1.Position = offset + Vector3.new(0, y + 0.35, 0)
    end
    setTrail(rig.spiral, ascending)
    rig.wisps.Rate = if ascending then 12 * rig.detail else 0
    rig.stream.Rate = if gliding then 5 * rig.detail else 0
    rig.streamFog.Rate = if gliding then 3 * rig.detail else 0
    rig.shed.Rate = if gliding then 6 * rig.detail else 0
    rig.wind.Rate = if gliding then 16 * rig.detail else 0
    rig.active = ascending or gliding
end

RunService.RenderStepped:Connect(function(deltaTime)
    local now = os.clock()
    for character, rig in rigs do
        if character.Parent == nil then
            rigs[character] = nil -- the character was removed (respawn or leaving) without being destroyed
        elseif rig.active or now < rig.ascendUntil or rig.gliding then
            updateRig(rig, deltaTime, now)
        end
    end
end)

-- ---------- pose state ----------
local states = setmetatable({}, { __mode = "k" }) -- [player] = { leapAt, leapUntil, side, gliding }

local function stateFor(player)
    local state = states[player]
    if not state then
        state = { leapAt = 0, leapUntil = 0, side = "Right", gliding = false }
        states[player] = state
    end
    return state
end

-- Each leap is a stride up through the air, and the legs alternate like climbing invisible
-- steps: the takeoff drives the right knee up, the first air leap the left, the second the
-- right, and so on.
local function startLeap(state, side)
    state.side = side
    state.leapAt = os.clock()
    state.leapUntil = state.leapAt + LEAP_POSE_TIME
end

-- The Qinggong pose a player should hold now: "Glide", "StepRight" / "StepLeft" (the stride, its
-- knee driving up), "TuckRight" / "TuckLeft" (both knees drawn up after it), or nil.
function QinggongFx.pose(player)
    local state = states[player]
    if not state then
        return nil
    end
    if state.gliding then
        return "Glide"
    end
    local now = os.clock()
    if now >= state.leapUntil then
        return nil
    end
    return (if now - state.leapAt < STEP_TIME then "Step" else "Tuck") .. state.side
end

-- ---------- entry point ----------
-- kind: "Takeoff" | "Leap" (value = the leap's number) | "Glide" (value 1 = start, 0 = stop) |
-- "Land" (value = impact strength, 0..1)
function QinggongFx.play(player, kind, value)
    local character, humanoid, root = rootOf(player)
    if not character then
        return
    end
    local state = stateFor(player)
    local isLocal = player == Players.LocalPlayer
    local visible = isLocal or inRange(root)
    local detail = if isLocal then 1 else OTHERS_DETAIL
    local p = paletteFor(player)

    if kind == "Leap" then
        startLeap(state, if (value or 1) % 2 == 1 then "Left" else "Right")
        if visible then
            local rig = rigFor(player)
            if rig then
                rig.ascendUntil = os.clock() + ASCEND_TIME
                rig.active = true
            end
            local leaps = math.max(1, player:GetAttribute("QinggongAirLeaps") or 1)
            step(p, root.Position - Vector3.new(0, feetOffset(humanoid, root), 0), math.clamp((value or 1) / leaps, 0, 1), detail)
        end
    elseif kind == "Glide" then
        state.gliding = value == 1
        local rig = visible and rigFor(player)
        if rig then
            rig.gliding = state.gliding
            rig.active = true
        end
    elseif kind == "Land" then
        state.gliding = false
        state.leapUntil = 0
        local rig = rigs[character]
        if rig then
            rig.gliding = false
            rig.ascendUntil = 0
            rig.active = true
        end
        if visible then
            local ground = groundBelow(character, root, feetOffset(humanoid, root) + 4)
            if ground then
                impact(p, ground, math.clamp(value or 0.3, 0, 1), detail, isLocal)
            end
        end
    elseif kind == "Takeoff" then
        startLeap(state, "Right")
        if visible then
            local ground = groundBelow(character, root, feetOffset(humanoid, root) + 2)
            if ground then
                takeoff(p, ground, detail)
            end
        end
    end
end

return QinggongFx

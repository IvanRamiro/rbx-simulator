-- Qinggong VFX, all client-side and cosmetic (they never affect movement):
--   Takeoff  (a jump from the ground) a Qi formation blooms over a turning vortex, with rising
--            wind streaks and clouds puffing out round it.
--   Leap     (each air leap) a small formation and ripple ring where the foot pushes off, clouds
--            that linger as a stepping-stone, streaks shooting down and a flash.
--   Ascend   (after each leap) energy trails from the feet, a silk ribbon from the shoulders and
--            a current of Qi spiralling round the body.
--   Glide    (holding jump while falling) a stream of cloud under the feet, wind lines past the body.
--   Dash     wind streaks back past the body, a lingering cloud and a faint ripple at the start.
--   Land     (after any of the above, or a hard fall) a starburst, formation flash, shockwave
--            rings, Qi spikes, rolling cloud and Qi mist, all scaled by impact.
--   Run      (running on the ground) a wind trail: two streaming bands of wispy wind streaks (the
--            owner's chosen texture) peel back from the shoulders, wind lines rush past the body and the stride kicks up a little wind-blown
--            dust, all stronger the faster the run (full at RUN_FULL_SPEED). Read from each
--            character's own movement, so other players' need no message.
--
-- Colours follow the cultivator's realm. Effects play here at once for the local player; other
-- players' arrive through QinggongFxEvent and are skipped beyond MAX_DISTANCE from the camera.
-- PoseController reads pose(player).
local ContentProvider = game:GetService("ContentProvider")
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local AuraKit = require(script.Parent.Parent:WaitForChild("Auras"):WaitForChild("AuraKit"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

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
    -- chosen by the owner for the running wind trail (2026-11-02): "Images/Trails15", by BloxenRBLX
    WindTrail = "rbxassetid://124753331461910",
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
local RUN_MIN_SPEED = 19        -- studs/s on the ground before the wind trail shows (above a walk, below the first run)
local RUN_FULL_SPEED = 64       -- the wind trail is at full strength from this speed

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

local function dashBurst(p, centre, direction, detail)
    local back = -direction
    local spot = host(centre, Vector3.new(0.6, 1.6, 0.6), 1.6)
    spot.CFrame = CFrame.lookAt(centre, centre + back)
    -- the emitter's Front face points back
    emitter(spot, {
        Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        Speed = NumberRange.new(28, 40), SpreadAngle = Vector2.new(8, 8), Lifetime = NumberRange.new(0.14, 0.22),
        Size = numberSequence({ { 0, 1.6 }, { 1, 0.5 } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.2,
    }):Emit(count(9, detail))
    puff(spot, {
        EmissionDirection = Enum.NormalId.Front, Speed = NumberRange.new(4, 8), SpreadAngle = Vector2.new(35, 35), Drag = 3,
        Lifetime = NumberRange.new(0.8, 1.2), Size = numberSequence({ { 0, 1 }, { 0.3, 2.2 }, { 1, 2.8 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.1, 0.35 }, { 0.7, 0.65 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.4) }, { 1, p.Main } }), Brightness = 1.4,
    }, 4, detail)
    emitter(spot, {
        Texture = TEXTURES.Shockwave, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.3), ZOffset = 0.2,
        Size = numberSequence({ { 0, 0.8 }, { 1, 4.2 } }), Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 1.8,
    }):Emit(1)
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
            wave:Emit(1)
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
    local rig = { root = root, palette = p, trails = {}, ascendUntil = 0, gliding = false, running = 0, shownRun = -1, angle = 0, active = false }
    -- their width runs across the foot, so they stay full whether the body rises or glides
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
    -- the ribbon trails only while rising: held through a glide it would hang as a wide sheet
    local torso = character:FindFirstChild("UpperTorso") or root
    local r0 = attachment(torso, "QinggongRibbonA", Vector3.new(-0.7, 0.2, 0.55))
    local r1 = attachment(torso, "QinggongRibbonB", Vector3.new(0.7, 0.2, 0.55))
    rig.ribbon = trailBetween(torso, r0, r1, {
        Name = "QinggongRibbon", Texture = TEXTURES.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.4,
        Color = colorSequence({ { 0, p.Core }, { 0.1, p.Main }, { 1, p.Deep } }), Brightness = 1.8,
        Transparency = numberSequence({ { 0, 0.5 }, { 0.5, 0.68 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.15 } }),
    })
    rig.orbit0 = attachment(root, "QinggongOrbitA", Vector3.zero)
    rig.orbit1 = attachment(root, "QinggongOrbitB", Vector3.zero)
    rig.spiral = trailBetween(root, rig.orbit0, rig.orbit1, {
        Name = "QinggongSpiral", Texture = TEXTURES.Ribbon, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.45,
        Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2,
        Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.3 } }),
    })
    local feet = attachment(root, "QinggongFeet", Vector3.new(0, -feetOffset(humanoid, root), 0))
    rig.wisps = cloud(feet, {
        Speed = NumberRange.new(0.5, 1.5), Lifetime = NumberRange.new(0.6, 0.8),
        Size = numberSequence({ { 0, 0.6 }, { 0.3, 1.3 }, { 1, 1.6 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.15, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Core:Lerp(p.Main, 0.5) }, { 1, p.Main } }), Brightness = 1.4,
    })
    -- an attachment emits along its +Y: turned over so the clouds spill down beneath the feet
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
    rig.shed = cloud(feet, {
        VelocityInheritance = 0.7, Speed = NumberRange.new(0.5, 1.5), SpreadAngle = Vector2.new(180, 180),
        Lifetime = NumberRange.new(0.5, 0.7),
        Size = numberSequence({ { 0, 0.8 }, { 0.3, 1.3 }, { 1, 1.5 } }),
        Transparency = numberSequence({ { 0, 1 }, { 0.2, 0.55 }, { 1, 1 } }),
        Color = colorSequence({ { 0, p.Main }, { 1, p.Deep } }), Brightness = 1.2,
    })
    -- the wind trail while running: a soft band of wind from each shoulder's back (standing upright,
    -- so it streams out flat behind the runner) and a bright wind line from each hand
    rig.runTrails = {}
    for _, side in { -1, 1 } do
        local w0 = attachment(torso, "QinggongRunA", Vector3.new(side * 1.0, 1.1, 0.45))
        local w1 = attachment(torso, "QinggongRunB", Vector3.new(side * 1.0, -1.2, 0.45))
        table.insert(rig.runTrails, trailBetween(torso, w0, w1, {
            Name = "QinggongRunTrail", Texture = TEXTURES.WindTrail, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.32,
            Color = colorSequence({ { 0, p.Core }, { 0.3, p.Core:Lerp(p.Main, 0.4) }, { 1, p.Main } }), Brightness = 1.8,
            Transparency = numberSequence({ { 0, 0.5 }, { 0.4, 0.65 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.3 } }),
        }))
        local hand = character:FindFirstChild(side < 0 and "LeftHand" or "RightHand")
        if hand then
            local h0 = attachment(hand, "QinggongRunA", Vector3.new(0, 0.12, 0))
            local h1 = attachment(hand, "QinggongRunB", Vector3.new(0, -0.12, 0))
            table.insert(rig.runTrails, trailBetween(hand, h0, h1, {
                Name = "QinggongRunTrail", Texture = TEXTURES.Streak, TextureMode = Enum.TextureMode.Stretch, Lifetime = 0.26,
                Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 2.4,
                Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }), WidthScale = numberSequence({ { 0, 1 }, { 1, 0.4 } }),
            }))
        end
    end
    rig.dust = emitter(feet, {
        Name = "QinggongRunDust", Texture = TEXTURES.Fog, VelocityInheritance = -0.15, Speed = NumberRange.new(1, 3),
        SpreadAngle = Vector2.new(70, 20), Lifetime = NumberRange.new(0.35, 0.55), Rotation = NumberRange.new(0, 360),
        RotSpeed = NumberRange.new(-40, 40), Size = numberSequence({ { 0, 0.6 }, { 1, 2.4 } }), LightEmission = 0.25,
        Transparency = numberSequence({ { 0, 0.7 }, { 1, 1 } }), Color = colorSequence({ { 0, p.Core }, { 1, p.Main } }), Brightness = 1,
    })
    -- the root part's box spreads the wind lines round the body
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
    -- the wind trail while running, scaled by how fast (rig.running, 0..1)
    local running = if visible and not gliding and not ascending then rig.running else 0
    for _, trail in rig.runTrails do
        setTrail(trail, running > 0)
    end
    if math.abs(running - rig.shownRun) > 0.05 then   -- denser the faster (only re-set when it changes)
        rig.shownRun = running
        local fade = numberSequence({ { 0, 0.75 - 0.4 * running }, { 0.4, 0.85 - 0.3 * running }, { 1, 1 } })
        for _, trail in rig.runTrails do
            trail.Transparency = fade
        end
    end
    rig.dust.Rate = running * 10 * rig.detail
    rig.wind.Rate = if gliding then 16 * rig.detail else running * 18 * rig.detail
    rig.active = ascending or gliding or running > 0
end

-- How strongly a character is running (0..1): on the ground, faster than RUN_MIN_SPEED.
local function runStrength(humanoid, root)
    if humanoid.FloorMaterial == Enum.Material.Air or humanoid:GetState() == Enum.HumanoidStateType.Seated then
        return 0
    end
    local speed = (root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)).Magnitude
    if speed < RUN_MIN_SPEED then
        return 0
    end
    return math.clamp((speed - RUN_MIN_SPEED) / (RUN_FULL_SPEED - RUN_MIN_SPEED), 0.15, 1)
end

RunService.RenderStepped:Connect(function(deltaTime)
    local now = os.clock()
    for _, player in Players:GetPlayers() do   -- who is running (rigs are built on demand)
        local character, humanoid, root = rootOf(player)
        local rig = character and rigs[character]
        local strength = if character and inRange(root) then runStrength(humanoid, root) else 0
        if strength > 0 and not rig then
            rig = rigFor(player)
        end
        if rig then
            rig.running = strength
        end
    end
    for character, rig in rigs do
        if character.Parent == nil then
            rigs[character] = nil -- the character was removed (respawn or leaving) without being destroyed
        elseif rig.active or now < rig.ascendUntil or rig.gliding or rig.running > 0 then
            updateRig(rig, deltaTime, now)
        end
    end
end)

-- ---------- pose state ----------
local states = setmetatable({}, { __mode = "k" }) -- [player] = { leapAt, leapUntil, side, gliding, stopWind }

local function stateFor(player)
    local state = states[player]
    if not state then
        state = { leapAt = 0, leapUntil = 0, side = "Right", gliding = false }
        states[player] = state
    end
    return state
end

-- The legs alternate like climbing steps: the takeoff drives the right knee up, then each
-- air leap the other.
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

-- The realm palette (Core, Main, Deep, Accent) a player's effects use: shared with CombatFx.
function QinggongFx.palette(player)
    return paletteFor(player)
end

-- the glide's wind, on while a visible player glides
local function glideWind(state, root, on)
    if on and state.windRoot ~= root then
        glideWind(state, nil, false) -- a loop left on a body that's gone (a respawn mid-glide)
    end
    if on and not state.stopWind then
        state.stopWind = Sfx.loop("GlideLoop", root)
        state.windRoot = root
    elseif not on and state.stopWind then
        state.stopWind()
        state.stopWind = nil
        state.windRoot = nil
    end
end

-- ---------- entry point ----------
-- kind: "Takeoff" | "Leap" (value = the leap's number) | "Glide" (value 1 = start, 0 = stop) |
-- "Land" (value = impact strength, 0..1) | "Dash"
function QinggongFx.play(player, kind, value)
    local state = stateFor(player)
    local character, humanoid, root = rootOf(player)
    if not character then
        -- dead or not loaded: still end a glide or leap, or the next character keeps its pose
        if kind == "Glide" and value ~= 1 or kind == "Land" then
            state.gliding = false
            state.leapUntil = 0
            glideWind(state, nil, false)
        end
        return
    end
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
            Sfx.play("Leap", root)
            local leaps = math.max(1, player:GetAttribute("QinggongAirLeaps") or 1)
            step(p, root.Position - Vector3.new(0, feetOffset(humanoid, root), 0), math.clamp((value or 1) / leaps, 0, 1), detail)
        end
    elseif kind == "Glide" then
        state.gliding = value == 1
        -- out of range, an existing rig still learns it, or its clouds stay on after a glide ends
        local rig = if visible then rigFor(player) else rigs[character]
        if rig then
            rig.gliding = state.gliding
            rig.active = true
        end
        glideWind(state, root, state.gliding and visible)
    elseif kind == "Land" then
        state.gliding = false
        state.leapUntil = 0
        local rig = rigs[character]
        if rig then
            rig.gliding = false
            rig.ascendUntil = 0
            rig.active = true
        end
        glideWind(state, nil, false)
        if visible then
            local ground = groundBelow(character, root, feetOffset(humanoid, root) + 4)
            if ground then
                impact(p, ground, math.clamp(value or 0.3, 0, 1), detail, isLocal)
                if (value or 0) >= 0.3 then
                    Sfx.play("Land", ground)
                end
            end
        end
    elseif kind == "Dash" then
        if visible then
            local direction = root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)
            if direction.Magnitude < 1 then
                direction = humanoid.MoveDirection
            end
            if direction.Magnitude < 0.05 then
                direction = root.CFrame.LookVector * Vector3.new(1, 0, 1)
            end
            dashBurst(p, root.Position, direction.Unit, detail)
            Sfx.play("Dash", root)
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

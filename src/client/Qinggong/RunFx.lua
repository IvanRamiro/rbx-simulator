-- The running effects: what follows a cultivator across the ground. Cosmetic only (it never writes to a humanoid, a root part or a
-- movement state), built from the character's own movement, so every client draws every runner without a message.
--
-- The effect is built from the stride, not from a line behind the body:
--   Foot-plant   a puff of dust kicked back (tinted by what the floor is), a ripple ring spreading on the ground, a glint, each time a
--                foot lands (read from the foot's height over the floor; a distance clock stands in if the animation is not
--                running), and the realm's own touch on every step (a ground mark, a flash on the chest, a bolt ...)
--   Wake         a soft veil of glowing wind left in the air behind the hips, and two curls that spiral off the shoulders and a swirl
--                at the heels (the emitters ride a circle round the body, so what they leave in the air curls and flutters)
--   Sprint       (at the runner's full speed) wind lines past the body, rings of compressed air thrown ahead that the runner passes
--                through, and afterimages of the body's pose that fade behind (the player's own screen only)
--   Realm        the colours are the aura's; each realm adds one signature (SIG) from the textures of its own aura piece
--
-- Strength is smoothed: a level (jog) that rises over about 0.2 s and falls over 0.3 s, and a sprint amount that follows how near the
-- runner is to their own top speed; neither pops on a start, a stop, a turn or a bump that flickers the floor read.
--
--   RunFx.step(deltaTime, busy)   called once a frame by QinggongFx; busy(character) is true while a leap or glide owns the body
--   RunFx.stats()                 Studio checks: how many rigs, emitters and ghost parts exist
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Auras = script.Parent.Parent:WaitForChild("Auras")
local Styles = require(Auras:WaitForChild("BreakthroughStyles"))
local AuraKit = require(Auras:WaitForChild("AuraKit"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))

local RunFx = {}

local ns = AuraKit.numberSequence
local cs = AuraKit.colorSequence

local T = Styles.Textures
local WIND_CURL = "rbxassetid://124753331461910" -- the swirl of wind the owner chose on 2026-11-02, now a particle that turns and fades

-- ---------- numbers ----------
local RUN_MIN = 19             -- studs/s on the ground before anything shows (above a walk, below the first rank's run)
local RUN_JOG_FULL = 25        -- the level is full from here (the first rank runs at 22: already most of the way)
local RUN_TOP = 76             -- the highest rank's run speed: the scale of "how fast" (pace 0..1 from RUN_MIN to here)
local SPRINT_FROM = 0.80       -- the sprint begins at this share of the humanoid's WalkSpeed and is whole by SPRINT_FULL
local SPRINT_FULL = 0.95
local AIR_GRACE = 0.12         -- seconds of "air" read before the run is let go (a bump or a stair flickers the floor read)
local UP_RATE, DOWN_RATE, AIR_DOWN_RATE = 5.5, 3.2, 9
local SPRINT_UP, SPRINT_DOWN = 3.2, 5
local PLANT_GAP = 0.085        -- fewest seconds between two foot-plants
local RING_SPACING = 3.4       -- fewest studs between two ground rings
local FOOT_DOWN, FOOT_UP = 0.34, 0.62 -- a foot is planted below this height over the floor and lifts above the other
local STRIDE_FALLBACK = 9      -- studs between steps when no foot is seen landing
local NEAR_OTHERS, FAR_OTHERS = 48, 90      -- others: all of the lighter version within, steps only beyond, nothing past
local NEAR_LOW, FAR_LOW = 34, 60           -- the same on the phone tier
local PARK_DESTROY = 14        -- seconds an idle rig of someone else is kept
local GHOSTS = 3
local GHOST_SPACING = 4.6     -- studs the runner must have covered since the last afterimage
local GHOST_LIFE = 0.3
local GHOST_ALPHA = 0.8      -- how see-through an afterimage is when it is left (1 = invisible): a faint echo, never a block
local GHOST_SIDE = 1.5        -- studs an echo stands to one side of the runner's path
local GHOST_CLEAR_COS, GHOST_HIDE_COS = 0.85, 0.97 -- seen from the camera: an echo within about 32 degrees of the runner starts to fade, within 14 it is gone
local GHOST_FROM_PACE = 0.4   -- afterimages belong to the fast ranks: from about 42 studs/s (the Dao Seeker's run)
local GHOST_IDLE = 6           -- seconds after the last sprint before the afterimage parts are destroyed

local GHOST_PARTS = {
    "Head", "UpperTorso", "LowerTorso",
    "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot",
}

local localPlayer = Players.LocalPlayer
-- In Studio only, two attributes on the local player (QARunAsOther, QARunLow) show the other-player and the phone versions of their own run
local inStudio = RunService:IsStudio()
local asOther, isLow = false, Quality.Low

-- ---------- what the floor is made of: dust and sparks ----------
local SURFACE_CLASS = {
    [Enum.Material.Grass] = "earth", [Enum.Material.LeafyGrass] = "earth", [Enum.Material.Ground] = "earth", [Enum.Material.Mud] = "earth",
    [Enum.Material.Sand] = "earth", [Enum.Material.Sandstone] = "earth", [Enum.Material.Salt] = "earth",
    [Enum.Material.Snow] = "soft", [Enum.Material.Ice] = "soft", [Enum.Material.Glacier] = "soft",
    [Enum.Material.Wood] = "wood", [Enum.Material.WoodPlanks] = "wood",
    [Enum.Material.Metal] = "metal", [Enum.Material.DiamondPlate] = "metal", [Enum.Material.CorrodedMetal] = "metal",
    [Enum.Material.Foil] = "metal", [Enum.Material.Neon] = "metal", [Enum.Material.Glass] = "metal", [Enum.Material.ForceField] = "metal",
}
-- tone: the dust's own colour; dust: how much of it; spark: how readily a step throws a glint
local SURFACE = {
    earth = { tone = Color3.fromRGB(150, 128, 96), dust = 1.2, spark = 0.15 },
    stone = { tone = Color3.fromRGB(206, 210, 222), dust = 0.6, spark = 0.7 },
    soft = { tone = Color3.fromRGB(236, 244, 255), dust = 1.0, spark = 0.35 },
    wood = { tone = Color3.fromRGB(196, 166, 126), dust = 0.55, spark = 0.1 },
    metal = { tone = Color3.fromRGB(214, 220, 232), dust = 0.12, spark = 1.0 },
}
local CLASSES = { "earth", "stone", "soft", "wood", "metal" }

-- ---------- the realm signatures ----------
-- One entry per realm (the aura's twelve). Each is told in the realm's own textures (the pieces its aura and its breakthrough use):
--   cont   one emitter running while the runner runs (rate scales with the level and the sprint); `at` says where it sits
--   burst  one emitter fired on a foot-plant, `at` the floor ("flat" lies on the ground, "kick" throws upward and back), the chest or
--          the heels; count(lv, sprint) is how many, lv the pace step 1..3
-- t is the realm's theme (Hot, Main, Deep ...), k its scale (0.8 at the first realm to 1.25 at the last).
local FLAT = {
    Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Speed = NumberRange.new(0.01), Rotation = NumberRange.new(0, 360),
}
local function merged(base, props)
    for key, value in props do
        base[key] = value
    end
    return base
end
local function ground(props)
    return merged(table.clone(FLAT), props)
end

local SIG = {}

-- 1 Qi Awakening, a calm breath: jade shells turn out on the ground, soft motes lift off the shoulders
SIG[1] = function(t, k)
    return {
        cont = { at = "shoulders", rate = 5, props = {
            Texture = T.Glow, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(1.5, 3), Acceleration = Vector3.new(0, 3, 0),
            SpreadAngle = Vector2.new(40, 40), Lifetime = NumberRange.new(0.7, 1.1), Brightness = 1.4,
            Size = ns({ { 0, 0.5 * k }, { 0.4, 0.95 * k }, { 1, 0.2 } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.35 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }),
        } },
        burst = { at = "flat", count = function() return 1 end, props = ground({
            Texture = T.Vortex, Lifetime = NumberRange.new(0.5), RotSpeed = NumberRange.new(-230, -170), ZOffset = -0.1,
            Size = ns({ { 0, 0.6 }, { 0.3, 3.0 * k }, { 1, 3.9 * k } }), Transparency = ns({ { 0, 1 }, { 0.12, 0.4 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }), Brightness = 1.4,
        }) },
    }
end

-- 2 Qi Foundation, Meridian Current: ribbons of current stream back off the shoulders and a second thin ring answers each step
SIG[2] = function(t, k)
    return {
        cont = { at = "shoulders", rate = 6, props = {
            Texture = T.Current, EmissionDirection = Enum.NormalId.Back, Orientation = Enum.ParticleOrientation.VelocityParallel,
            Speed = NumberRange.new(12, 18), Drag = 2.5, SpreadAngle = Vector2.new(10, 10), Lifetime = NumberRange.new(0.35, 0.55),
            Size = ns({ { 0, 2.4 * k }, { 0.5, 4.2 * k }, { 1, 2 * k } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.45 }, { 0.7, 0.7 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(190, 255, 245) }, { 1, t.Main } }), Brightness = 1.2,
        } },
        burst = { at = "flat", count = function() return 1 end, props = ground({
            Texture = T.Current, Lifetime = NumberRange.new(0.55), RotSpeed = NumberRange.new(120, 180), ZOffset = -0.1,
            Size = ns({ { 0, 1 }, { 0.3, 4.2 * k }, { 1, 5 * k } }), Transparency = ns({ { 0, 1 }, { 0.1, 0.5 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Deep } }), Brightness = 1.2,
        }) },
    }
end

-- 3 Spirit Core, Core Pulse: the golden core on the chest beats once with every step
SIG[3] = function(t, k)
    return {
        burst = { at = "chest", count = function() return 1 end, props = {
            Texture = T.CorePulse, Lifetime = NumberRange.new(0.3), LockedToPart = true, Rotation = NumberRange.new(0, 360),
            Size = ns({ { 0, 1.2 }, { 0.3, 3.4 * k }, { 1, 4.4 * k } }), Transparency = ns({ { 0, 1 }, { 0.08, 0.35 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(255, 240, 160) }, { 1, t.Main } }), Brightness = 1.6, ZOffset = 0.5,
        } },
        cont = { at = "shoulders", rate = 4, props = {
            Texture = T.Glow, EmissionDirection = Enum.NormalId.Back, Speed = NumberRange.new(2, 5), SpreadAngle = Vector2.new(30, 30),
            Lifetime = NumberRange.new(0.5, 0.8), Size = ns({ { 0, 0.6 * k }, { 1, 0.15 } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.2 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }), Brightness = 1.6,
        } },
    }
end

-- 4 Spirit Soul, Soul Flames: blue flames lick up from the heels, a small one is thrown up at every step
SIG[4] = function(t, k)
    local flame = {
        Texture = T.SoulFlame, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
        FlipbookFramerate = NumberRange.new(24, 30), Orientation = Enum.ParticleOrientation.FacingCameraWorldUp, LightEmission = 0.85,
        Rotation = NumberRange.new(-8, 8), Color = cs({ { 0, t.Hot }, { 0.4, t.Main }, { 1, t.Deep } }),
    }
    return {
        cont = { at = "heels", rate = 6, props = merged(table.clone(flame), {
            Lifetime = NumberRange.new(0.5, 0.8), Speed = NumberRange.new(1, 2.5), Acceleration = Vector3.new(0, 5, 0), SpreadAngle = Vector2.new(25, 25),
            Size = ns({ { 0, 1.4 * k }, { 0.5, 2.4 * k }, { 1, 1.2 * k } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.2 }, { 0.75, 0.4 }, { 1, 1 } }),
        }) },
        burst = { at = "kick", count = function(lv) return lv >= 2 and 2 or 1 end, props = merged(table.clone(flame), {
            Lifetime = NumberRange.new(0.45, 0.7), Speed = NumberRange.new(5, 9), Acceleration = Vector3.new(0, 7, 0), SpreadAngle = Vector2.new(35, 35), Drag = 2,
            Size = ns({ { 0, 1.8 * k }, { 0.4, 3 * k }, { 1, 1.2 * k } }), Transparency = ns({ { 0, 0.1 }, { 0.7, 0.4 }, { 1, 1 } }),
        }) },
    }
end

-- 5 Ascendant, Ascending Gale: wind streaks tear back off the shoulders and a gust of streaks fans out of each step
SIG[5] = function(t, k)
    return {
        cont = { at = "shoulders", rate = 12, props = {
            Texture = T.GaleStreak, EmissionDirection = Enum.NormalId.Back, Orientation = Enum.ParticleOrientation.VelocityParallel,
            Speed = NumberRange.new(24, 34), SpreadAngle = Vector2.new(7, 7), Lifetime = NumberRange.new(0.18, 0.3),
            Size = ns({ { 0, 3.2 * k }, { 1, 1.4 * k } }), Transparency = ns({ { 0, 1 }, { 0.2, 0.4 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }), Brightness = 1.8,
        } },
        burst = { at = "kick", count = function(lv) return 3 + lv end, props = {
            Texture = T.GaleStreak, Orientation = Enum.ParticleOrientation.VelocityParallel, Speed = NumberRange.new(16, 26), Drag = 3,
            SpreadAngle = Vector2.new(70, 14), Lifetime = NumberRange.new(0.14, 0.26),
            Size = ns({ { 0, 2.6 * k }, { 1, 0.8 } }), Transparency = ns({ { 0, 0.1 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }), Brightness = 2.2,
        } },
    }
end

-- 6 Immortal, Heaven's Light: a thin shaft of silver light stands up out of each step, motes of it fall back through the air
SIG[6] = function(t, k)
    return {
        burst = { at = "flat", count = function() return 1 end, props = {
            Texture = T.HeavenBeam, Orientation = Enum.ParticleOrientation.FacingCameraWorldUp, Speed = NumberRange.new(0.01),
            Lifetime = NumberRange.new(0.4), Size = ns({ { 0, 2 * k }, { 0.3, 5.5 * k }, { 1, 4.6 * k } }),
            Transparency = ns({ { 0, 1 }, { 0.1, 0.45 }, { 1, 1 } }), Color = cs({ { 0, t.Hot }, { 1, t.Main } }), Brightness = 1.1, ZOffset = 0.3,
        } },
        cont = { at = "shoulders", rate = 5, props = {
            Texture = T.Glow, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.5, 1.5), Acceleration = Vector3.new(0, -2.5, 0),
            SpreadAngle = Vector2.new(60, 60), Lifetime = NumberRange.new(0.8, 1.2), Brightness = 1.3,
            Size = ns({ { 0, 0.55 * k }, { 1, 0.15 } }), Transparency = ns({ { 0, 1 }, { 0.2, 0.3 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }),
        } },
    }
end

-- 7 Divine, Divine Lightning: a crack of crimson lightning flickers at the foot with each step, sparks fly up off the heels
SIG[7] = function(t, k)
    return {
        burst = { at = "kick", count = function(lv, sprint) return 1 + (sprint > 0.5 and 1 or 0) end, props = {
            Texture = T.Bolt, Rotation = NumberRange.new(-35, 35), Speed = NumberRange.new(0.5, 3), SpreadAngle = Vector2.new(40, 40),
            Lifetime = NumberRange.new(0.09, 0.16), Size = ns({ { 0, 2.4 * k }, { 0.3, 4 * k }, { 1, 3 * k } }),
            Transparency = ns({ { 0, 0 }, { 0.6, 0.1 }, { 1, 0.7 } }), Color = cs({ { 0, Color3.fromRGB(255, 190, 170) }, { 1, t.Main } }), Brightness = 2.4,
        } },
        cont = { at = "heels", rate = 9, props = {
            Texture = T.StarDust, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(4, 9), Acceleration = Vector3.new(0, -18, 0),
            SpreadAngle = Vector2.new(30, 30), Lifetime = NumberRange.new(0.3, 0.5), Brightness = 2,
            Size = ns({ { 0, 0.9 * k }, { 1, 0.2 } }), Transparency = ns({ { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(255, 200, 170) }, { 1, t.Main } }),
        } },
    }
end

-- 8 Cosmic, Star Drift: stars shed off the body and drift, twinkling; each step throws a few of them out of the floor
SIG[8] = function(t, k)
    local twinkle = ns({ { 0, 1 }, { 0.1, 0.1 }, { 0.3, 0.7 }, { 0.45, 0.05 }, { 0.65, 0.65 }, { 0.8, 0.15 }, { 1, 1 } })
    return {
        cont = { at = "shoulders", rate = 7, props = {
            Texture = T.Star, EmissionDirection = Enum.NormalId.Back, Speed = NumberRange.new(2, 6), SpreadAngle = Vector2.new(60, 60),
            Lifetime = NumberRange.new(0.9, 1.4), Rotation = NumberRange.new(0, 90), RotSpeed = NumberRange.new(-40, 40), Brightness = 1.8,
            Size = ns({ { 0, 0.9 * k }, { 0.5, 1.3 * k }, { 1, 0.5 * k } }), Transparency = twinkle,
            Color = cs({ { 0, Color3.fromRGB(240, 220, 255) }, { 1, t.Main } }),
        } },
        burst = { at = "kick", count = function(lv) return 1 + lv end, props = {
            Texture = T.StarDust, Speed = NumberRange.new(5, 12), SpreadAngle = Vector2.new(45, 45), Acceleration = Vector3.new(0, -6, 0), Drag = 1.5,
            Lifetime = NumberRange.new(0.5, 0.9), Rotation = NumberRange.new(0, 360), Brightness = 2,
            Size = ns({ { 0, 0.5 * k }, { 0.3, 1.1 * k }, { 1, 0.2 } }), Transparency = ns({ { 0, 0.1 }, { 0.6, 0.3 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.new(1, 1, 1) }, { 1, t.Main } }),
        } },
    }
end

-- 9 Void, Void Pull: black smoke is left behind (it does not glow, it darkens), chips of dark glass fly off each step
SIG[9] = function(t, k)
    return {
        cont = { at = "heels", rate = 11, props = {
            Texture = T.Fog, Speed = NumberRange.new(1, 3), SpreadAngle = Vector2.new(35, 35), Drag = 2, LightEmission = 0, LightInfluence = 0,
            Lifetime = NumberRange.new(0.6, 0.95), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30),
            Size = ns({ { 0, 2.0 * k }, { 1, 6 * k } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.18 }, { 0.6, 0.45 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(14, 18, 34) }, { 1, Color3.fromRGB(4, 6, 16) } }), Brightness = 1,
        } },
        burst = { at = "kick", count = function(lv) return 1 + lv end, props = {
            Texture = T.VoidShards, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2, FlipbookMode = Enum.ParticleFlipbookMode.Random,
            Speed = NumberRange.new(6, 13), SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, -22, 0), LightEmission = 0, LightInfluence = 0,
            Lifetime = NumberRange.new(0.35, 0.6), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-300, 300),
            Size = ns({ { 0, 0.9 * k }, { 0.3, 1.5 * k }, { 1, 0.4 } }), Transparency = ns({ { 0, 0.1 }, { 0.7, 0.2 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(26, 36, 70) }, { 1, Color3.fromRGB(6, 8, 20) } }),
        } },
    }
end

-- 10 Heavenly Dao, Radiant Rays: a rose sunburst opens on the floor at each step
SIG[10] = function(t, k)
    return {
        burst = { at = "flat", count = function() return 1 end, props = ground({
            Texture = T.RayBeam, Lifetime = NumberRange.new(0.45), RotSpeed = NumberRange.new(-60, 60), ZOffset = -0.1,
            Size = ns({ { 0, 1.2 }, { 0.3, 4.4 * k }, { 1, 5.2 * k } }), Transparency = ns({ { 0, 1 }, { 0.1, 0.5 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(255, 225, 240) }, { 1, t.Main } }), Brightness = 1.5,
        }) },
        cont = { at = "shoulders", rate = 5, props = {
            Texture = T.Glow, EmissionDirection = Enum.NormalId.Back, Speed = NumberRange.new(2, 5), SpreadAngle = Vector2.new(40, 40),
            Lifetime = NumberRange.new(0.6, 0.9), Size = ns({ { 0, 0.7 * k }, { 1, 0.15 } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.25 }, { 1, 1 } }),
            Color = cs({ { 0, t.Hot }, { 1, t.Main } }), Brightness = 1.6,
        } },
    }
end

-- 11 Primordial, Magma Rise: each step presses a glowing crack into the floor that cools to ember, chips of magma and dark heat-smoke
SIG[11] = function(t, k)
    return {
        burst = { at = "flat", count = function() return 1 end, props = ground({
            Texture = T.Streak, Lifetime = NumberRange.new(0.9, 1.2), ZOffset = -0.1,
            Size = ns({ { 0, 1.2 }, { 0.15, 5 * k }, { 1, 5.5 * k } }), Transparency = ns({ { 0, 1 }, { 0.08, 0.1 }, { 0.7, 0.4 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(255, 220, 90) }, { 0.35, Color3.fromRGB(255, 120, 25) }, { 1, Color3.fromRGB(150, 30, 5) } }), Brightness = 1.8,
        }) },
        burst2 = { at = "kick", count = function(lv) return lv end, props = {
            Texture = T.Magma, Speed = NumberRange.new(8, 15), SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, -40, 0),
            Lifetime = NumberRange.new(0.4, 0.7), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-220, 220), LightEmission = 0.6,
            Size = ns({ { 0, 0.55 * k }, { 0.2, 0.95 * k }, { 1, 0.5 * k } }), Transparency = ns({ { 0, 0.4 }, { 0.1, 0 }, { 0.85, 0 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(255, 200, 70) }, { 0.4, Color3.fromRGB(255, 110, 20) }, { 1, Color3.fromRGB(70, 10, 0) } }),
        } },
        cont = { at = "heels", rate = 5, props = {
            Texture = T.HeatSmoke, Speed = NumberRange.new(2, 4), Acceleration = Vector3.new(0, 2, 0), SpreadAngle = Vector2.new(30, 30), Drag = 1,
            LightEmission = 0, LightInfluence = 0.6, Lifetime = NumberRange.new(0.8, 1.2), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30),
            Size = ns({ { 0, 1.6 * k }, { 1, 5 * k } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.55 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.fromRGB(70, 40, 30) }, { 1, Color3.fromRGB(25, 15, 15) } }),
        } },
    }
end

-- 12 Eternal Transcendence, Eternal Orbits: three rings, gold then cyan then magenta, one inside the next, answer every step
SIG[12] = function(t, k)
    local function ring(color, small, big, life)
        return ground({
            Texture = T.Ring, Lifetime = NumberRange.new(life), RotSpeed = NumberRange.new(-80, 80),
            Size = ns({ { 0, small * 0.2 }, { 0.3, big * 0.8 }, { 1, big } }), Transparency = ns({ { 0, 0.15 }, { 0.5, 0.5 }, { 1, 1 } }),
            Color = cs({ { 0, Color3.new(1, 1, 1) }, { 0.3, color }, { 1, color } }), Brightness = 1.8, ZOffset = 0.3,
        })
    end
    return {
        burst = { at = "flat", count = function() return 1 end, props = ring(t.Cyan, 4, 6.6, 0.5) },
        burst2 = { at = "flat", count = function() return 1 end, props = ring(t.Magenta, 5, 9, 0.6) },
        cont = { at = "shoulders", rate = 8, props = {
            Texture = T.Glow, EmissionDirection = Enum.NormalId.Back, Speed = NumberRange.new(2, 6), SpreadAngle = Vector2.new(50, 50),
            Lifetime = NumberRange.new(0.6, 0.95), Size = ns({ { 0, 0.7 * k }, { 1, 0.15 } }), Transparency = ns({ { 0, 1 }, { 0.15, 0.2 }, { 1, 1 } }),
            Color = cs({ { 0, t.Gold }, { 0.5, t.Cyan }, { 1, t.Magenta } }), Brightness = 1.8,
        } },
    }
end

-- ---------- instances ----------
local ghostFolder -- every runner's afterimage parts (created with the first)

local function newAttachment(rig, parent, name, position, orientation)
    local a = Instance.new("Attachment")
    a.Name = name
    a.Position = position
    if orientation then
        a.Orientation = orientation
    end
    a.Parent = parent
    table.insert(rig.items, a)
    return a
end

local function newEmitter(rig, parent, name, properties)
    local e = Instance.new("ParticleEmitter")
    e.Name = name
    e.Rate = 0
    e.LightInfluence = 0
    e.LightEmission = 1
    e.Enabled = true
    for property, value in properties do
        e[property] = value
    end
    e.Parent = parent
    table.insert(rig.items, e)
    rig.emitters += 1
    return e
end

-- the realm's theme as the run uses it: the Immortal Realm's silver-white blooms to a white wash, so its light is a cool blue-white
local function themeOf(realm)
    local theme = Styles.theme(realm)
    if realm == 6 then
        theme.Hot = Color3.fromRGB(214, 230, 255)
        theme.Main = Color3.fromRGB(140, 182, 248)
        theme.Deep = Color3.fromRGB(80, 108, 196)
    end
    return theme
end

-- the realm number of a player (1 to 12), 1 until their rank has loaded
local function realmOf(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and Styles.realmNumber(rank.Realm) or 1
end

local function sizes(a, b, c, k)
    return { ns({ { 0, 0.5 * k }, { 1, a * k } }), ns({ { 0, 0.6 * k }, { 1, b * k } }), ns({ { 0, 0.7 * k }, { 1, c * k } }) }
end

local function ringSizes(a, b, c, k)
    local function one(size)
        return ns({ { 0, 0.5 }, { 0.25, size * 0.8 * k }, { 1, size * k } })
    end
    return { one(a), one(b), one(c) }
end

-- Everything one runner needs, built the first time they run and destroyed with their character (or after PARK_DESTROY seconds idle).
local function build(player, character, humanoid, root, realm)
    local theme = themeOf(realm)
    local k = theme.Scale
    local rig = {
        player = player, character = character, humanoid = humanoid, root = root, realm = realm, theme = theme,
        items = {}, emitters = 0, isLocal = player == localPlayer,
        lvl = 0, sprint = 0, airTime = 0, parked = true, parkedAt = os.clock(), lastPlant = 0, lastRing = 0, nextCompress = 0,
        sinceRing = RING_SPACING, stride = 0, side = 1, footDown = { false, false }, spin = math.random() * 6.28, rates = {},
        ghostNext = 1, ghostRetry = 0, ghostSince = 0, ghostClock = 0, ghostSide = 1, lastSprint = 0,
    }
    local torso = character:FindFirstChild("UpperTorso") or root
    rig.torso = torso
    rig.feet = humanoid.HipHeight + root.Size.Y / 2
    rig.footL = character:FindFirstChild("LeftFoot")
    rig.footR = character:FindFirstChild("RightFoot")
    local hot, main, deep = theme.Hot, theme.Main, theme.Deep
    local tint = cs({ { 0, hot:Lerp(main, 0.3) }, { 0.4, main }, { 1, deep } })
    local tintLight = cs({ { 0, hot }, { 1, main } })

    -- attachments
    local backAngle = Vector3.new(90, 0, 0)   -- an attachment emits along its +Y: turned to the character's back
    rig.flat = newAttachment(rig, root, "RunFlat", Vector3.new(0, -rig.feet + 0.12, 0))
    rig.kick = newAttachment(rig, root, "RunKick", Vector3.new(0, -rig.feet + 0.15, 0), Vector3.new(37, 0, 0)) -- up and back
    rig.backAtt = newAttachment(rig, torso, "RunBack", Vector3.new(0, -0.5, 0.75), backAngle)
    rig.heelAtt = newAttachment(rig, root, "RunHeel", Vector3.new(0, -rig.feet + 0.5, 0.6), backAngle)
    rig.helixA = newAttachment(rig, torso, "RunHelixA", Vector3.new(0, 0.5, 0.7), backAngle)
    rig.helixB = newAttachment(rig, torso, "RunHelixB", Vector3.new(0, 0.5, 0.7), backAngle)
    rig.chest = newAttachment(rig, torso, "RunChest", Vector3.new(0, 0.2, -0.7))
    rig.front = newAttachment(rig, root, "RunFront", Vector3.new(0, 0.1, -4), Vector3.new(-90, 0, 0)) -- emits ahead

    -- the foot-plant: dust, ring, glint
    rig.dustColor = {}
    for _, class in CLASSES do
        local tone = SURFACE[class].tone
        rig.dustColor[class] = cs({ { 0, tone:Lerp(hot, 0.3) }, { 0.5, tone:Lerp(main, 0.22) }, { 1, tone } })
    end
    rig.dustSizes = sizes(2.6, 3.4, 4.4, k)
    rig.ringSizes = ringSizes(3.2, 4.6, 6.2, k)
    rig.dust = newEmitter(rig, rig.kick, "RunDust", {
        Texture = T.Fog, Speed = NumberRange.new(3, 8), SpreadAngle = Vector2.new(35, 35), Drag = 3.5, Acceleration = Vector3.new(0, 2, 0),
        Lifetime = NumberRange.new(0.35, 0.6), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-60, 60),
        LightEmission = 0.12, LightInfluence = 0.7, Brightness = 1,
        Size = rig.dustSizes[1], Transparency = ns({ { 0, 0.55 }, { 0.35, 0.72 }, { 1, 1 } }), Color = rig.dustColor.stone,
    })
    rig.ring = newEmitter(rig, rig.flat, "RunRing", ground({
        Texture = T.Ring, Lifetime = NumberRange.new(0.4), Size = rig.ringSizes[1], ZOffset = 0.2,
        Transparency = ns({ { 0, 0.25 }, { 0.5, 0.62 }, { 1, 1 } }), Color = tint, Brightness = 1.5,
    }))
    rig.glint = newEmitter(rig, rig.kick, "RunGlint", {
        Texture = T.Star, Speed = NumberRange.new(7, 14), SpreadAngle = Vector2.new(30, 30), Acceleration = Vector3.new(0, -30, 0),
        Lifetime = NumberRange.new(0.28, 0.45), Rotation = NumberRange.new(0, 90), Brightness = 2,
        Size = ns({ { 0, 0.9 * k }, { 0.3, 1.0 * k }, { 1, 0.1 } }), Transparency = ns({ { 0, 0 }, { 0.7, 0.2 }, { 1, 1 } }), Color = tintLight,
    })

    -- the wake: a veil, two curls off the shoulders and a swirl at the heels
    rig.veil = newEmitter(rig, rig.backAtt, "RunVeil", {
        Texture = T.Fog, Speed = NumberRange.new(2, 5), SpreadAngle = Vector2.new(40, 40), Drag = 1.5,
        Lifetime = NumberRange.new(0.55, 0.85), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-25, 25), LightEmission = 0.55, ZOffset = -0.3,
        Size = ns({ { 0, 1.8 * k }, { 0.4, 4.0 * k }, { 1, 5.4 * k } }), Transparency = ns({ { 0, 1 }, { 0.12, 0.84 }, { 0.5, 0.92 }, { 1, 1 } }),
        Color = cs({ { 0, main }, { 1, deep } }), Brightness = 1,
    })
    local curl = {
        Texture = WIND_CURL, Speed = NumberRange.new(1, 3), SpreadAngle = Vector2.new(15, 15), Lifetime = NumberRange.new(0.45, 0.7),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-170, 170), LightEmission = 0.9,
        Size = ns({ { 0, 1.2 * k }, { 0.35, 2.8 * k }, { 1, 3.6 * k } }), Transparency = ns({ { 0, 1 }, { 0.12, 0.38 }, { 0.6, 0.62 }, { 1, 1 } }),
        Color = tint, Brightness = 1.25,
    }
    rig.curlA = newEmitter(rig, rig.helixA, "RunCurlA", curl)
    rig.curlB = newEmitter(rig, rig.helixB, "RunCurlB", curl)
    rig.swirl = newEmitter(rig, rig.heelAtt, "RunSwirl", {
        Texture = WIND_CURL, Speed = NumberRange.new(1, 3), SpreadAngle = Vector2.new(20, 20), Lifetime = NumberRange.new(0.35, 0.55),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-220, 220), LightEmission = 0.8,
        Size = ns({ { 0, 0.8 * k }, { 0.4, 1.8 * k }, { 1, 2.4 * k } }), Transparency = ns({ { 0, 1 }, { 0.12, 0.45 }, { 1, 1 } }),
        Color = cs({ { 0, main }, { 1, deep } }), Brightness = 1.3,
    })

    -- the sprint: wind lines past the body and rings of compressed air ahead
    rig.rush = newEmitter(rig, root, "RunRush", {
        Texture = T.Streak, EmissionDirection = Enum.NormalId.Back, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(30, 42), SpreadAngle = Vector2.new(5, 5), Lifetime = NumberRange.new(0.16, 0.26),
        Size = ns({ { 0, 3.6 }, { 1, 1.2 } }), Transparency = ns({ { 0, 1 }, { 0.2, 0.5 }, { 1, 1 } }), Color = tintLight, Brightness = 1.6,
    })
    rig.compress = newEmitter(rig, rig.front, "RunCompress", ground({
        Texture = T.Ring, Lifetime = NumberRange.new(0.5), Size = ns({ { 0, 2.5 * k }, { 1, 7.5 * k } }),
        Transparency = ns({ { 0, 0.85 }, { 0.3, 0.8 }, { 1, 1 } }), Color = tintLight, Brightness = 1.3, ZOffset = 0.1,
    }))

    -- the realm's signature
    local spec = SIG[realm](theme, k)
    local function place(at)
        if at == "flat" then return rig.flat end
        if at == "kick" then return rig.kick end
        if at == "chest" then return rig.chest end
        if at == "heels" then return rig.heelAtt end
        return torso
    end
    if spec.cont then
        rig.sigRate = spec.cont.rate
        rig.sig = newEmitter(rig, place(spec.cont.at), "RunSig", spec.cont.props)
    end
    if spec.burst then
        rig.sigBurst = newEmitter(rig, place(spec.burst.at), "RunSigBurst", spec.burst.props)
        rig.sigCount = spec.burst.count
    end
    if spec.burst2 then
        rig.sigBurst2 = newEmitter(rig, place(spec.burst2.at), "RunSigBurst2", spec.burst2.props)
        rig.sigCount2 = spec.burst2.count
    end
    return rig
end

local function destroyGhosts(rig)
    if rig.ghosts then
        for _, ghost in rig.ghosts do
            for _, part in ghost.parts do
                part:Destroy()
            end
        end
        rig.ghosts = nil
    end
    rig.ghostSources = nil
end

local function destroyRig(rig)
    for _, item in rig.items do
        item:Destroy()
    end
    table.clear(rig.items)
    destroyGhosts(rig)
end

-- ---------- afterimages (the player's own screen, at a sprint) ----------
local function buildGhosts(rig)
    local character = rig.character
    local sources, count = {}, 0
    for _, name in GHOST_PARTS do
        local part = character:FindFirstChild(name)
        if part and part:IsA("MeshPart") then
            count += 1
            sources[count] = part
        end
    end
    if count < 8 then
        return false
    end
    if not ghostFolder or not ghostFolder.Parent then
        ghostFolder = Instance.new("Folder")
        ghostFolder.Name = "RunFxGhosts"
        ghostFolder.Parent = Workspace
    end
    local theme = rig.theme
    local color = if theme.Dark then theme.Dark else theme.Hot:Lerp(theme.Main, 0.35)
    local ghosts = {}
    for index = 1, GHOSTS do
        local parts = {}
        for i, source in sources do
            local copy = source:Clone()
            copy:ClearAllChildren()
            copy.Name = "RunGhost"
            copy.Anchored = true
            copy.CanCollide = false
            copy.CanQuery = false
            copy.CanTouch = false
            copy.CastShadow = false
            copy.Massless = true
            copy.Material = if theme.Dark then Enum.Material.SmoothPlastic else Enum.Material.Neon
            copy.Color = color
            copy.Reflectance = 0
            copy.Transparency = 1
            copy.Parent = ghostFolder
            parts[i] = copy
        end
        ghosts[index] = { parts = parts, age = GHOST_LIFE, pos = Vector3.zero }
    end
    rig.ghosts = ghosts
    rig.ghostSources = sources
    return true
end

local function spawnGhost(rig)
    local ghost = rig.ghosts[rig.ghostNext]
    rig.ghostNext = rig.ghostNext % GHOSTS + 1
    ghost.age = 0
    local sources, parts = rig.ghostSources, ghost.parts
    local theme = rig.theme
    local tinted = theme.Gold ~= nil
    if tinted then -- the last realm's afterimages run gold, cyan, magenta
        rig.ghostClock = rig.ghostClock % 3 + 1
        local color = (if rig.ghostClock == 1 then theme.Gold elseif rig.ghostClock == 2 then theme.Cyan else theme.Magenta)
        for i = 1, #parts do
            parts[i].Color = color
        end
    end
    -- each echo stands a little to one side of the path (alternately), so from behind they show beside the runner, not over them
    rig.ghostSide = -rig.ghostSide
    local offset = rig.root.CFrame.RightVector * (GHOST_SIDE * rig.ghostSide)
    ghost.pos = rig.root.Position + offset
    for i = 1, #parts do
        parts[i].CFrame = sources[i].CFrame + offset
        parts[i].Transparency = GHOST_ALPHA
    end
end

-- An echo that stands between the camera and the runner, or close to the lens, fades out: it never hides the body it follows.
local function updateGhosts(rig, deltaTime, cameraPosition)
    local live = false
    local toRunner = if cameraPosition then rig.root.Position - cameraPosition else Vector3.zero
    local runnerDistance = toRunner.Magnitude
    for _, ghost in rig.ghosts do
        if ghost.age < GHOST_LIFE then
            ghost.age += deltaTime
            local u = math.min(ghost.age / GHOST_LIFE, 1)
            local alpha = 1 - (1 - GHOST_ALPHA) * (1 - u) ^ 1.6
            if cameraPosition and runnerDistance > 0.5 then
                local toGhost = ghost.pos - cameraPosition
                local ghostDistance = toGhost.Magnitude
                local hide = math.clamp((6 - ghostDistance) / 3, 0, 1) -- near the lens
                if ghostDistance < runnerDistance + 1 and ghostDistance > 0.5 then -- in front of the runner: how well it lines up with them
                    local cosine = toGhost:Dot(toRunner) / (ghostDistance * runnerDistance)
                    hide = math.max(hide, math.clamp((cosine - GHOST_CLEAR_COS) / (GHOST_HIDE_COS - GHOST_CLEAR_COS), 0, 1))
                end
                alpha += (1 - alpha) * hide
            end
            for _, part in ghost.parts do
                part.Transparency = alpha
            end
            live = true
        end
    end
    return live
end

-- ---------- stepping ----------
local function setRate(rig, key, emitter, rate)
    local last = rig.rates[key]
    if emitter and (last == nil or math.abs(last - rate) > 0.25 or (rate == 0 and last ~= 0)) then
        rig.rates[key] = rate
        emitter.Rate = rate
    end
end

local function park(rig, now)
    if not rig.parked then
        rig.parked = true
        rig.parkedAt = now
        rig.veil.Rate = 0
        rig.curlA.Rate = 0
        rig.curlB.Rate = 0
        rig.swirl.Rate = 0
        rig.rush.Rate = 0
        if rig.sig then
            rig.sig.Rate = 0
        end
        table.clear(rig.rates)
    end
end

-- a foot has landed
local function plant(rig, foot, now, tier, pace, sprint, cls)
    rig.lastPlant = now
    rig.stride = 0
    local root = rig.root
    local feet = rig.feet
    local x, z = 0, 0
    if foot then
        local lp = root.CFrame:PointToObjectSpace(foot.Position)
        x, z = lp.X, lp.Z
    end
    local lv = if pace < 0.25 then 1 elseif pace < 0.6 then 2 else 3
    local surface = SURFACE[cls]
    -- dust kicked back (tinted by the floor)
    local dustCount = math.floor(0.7 + surface.dust * (0.8 + pace))
    if dustCount > 0 then
        rig.kick.Position = Vector3.new(x, -feet + 0.15, z)
        rig.dust.Size = rig.dustSizes[lv]
        rig.dust.Color = rig.dustColor[cls]
        rig.dust:Emit(dustCount)
    end
    -- the ring on the ground, not more often than every few studs
    if rig.sinceRing >= RING_SPACING then
        rig.sinceRing = 0
        rig.flat.Position = Vector3.new(x, -feet + 0.12, z)
        rig.ring.Size = rig.ringSizes[lv]
        rig.ring:Emit(1)
    end
    if tier < 2 then
        return
    end
    -- a glint (always on sparkling floors, otherwise on a sprint)
    if surface.spark > 0.5 or sprint > 0.5 or math.random() < surface.spark then
        rig.glint:Emit(1 + (if sprint > 0.5 then 1 else 0))
    end
    -- the realm's touch
    if rig.sigBurst then
        local burst = rig.sigBurst
        local parent = burst.Parent
        if parent == rig.flat then
            parent.Position = Vector3.new(x, -feet + 0.12, z)
        elseif parent == rig.kick then
            parent.Position = Vector3.new(x, -feet + 0.15, z)
        end
        burst:Emit(rig.sigCount(lv, sprint))
        if rig.sigBurst2 then
            local parent2 = rig.sigBurst2.Parent
            if parent2 == rig.flat then
                parent2.Position = Vector3.new(x, -feet + 0.12, z)
            elseif parent2 == rig.kick then
                parent2.Position = Vector3.new(x, -feet + 0.15, z)
            end
            rig.sigBurst2:Emit(rig.sigCount2(lv, sprint))
        end
    end
end

local rigs = {}              -- [character] = rig
local playerList = {}        -- every player (kept by PlayerAdded/Removing, so the frame loop builds no table)

local function stepRig(rig, deltaTime, now, tier)
    local humanoid, root = rig.humanoid, rig.root
    local velocity = root.AssemblyLinearVelocity
    local speed = math.sqrt(velocity.X * velocity.X + velocity.Z * velocity.Z)
    local detail = if isLow then 0.55 else 1

    -- the target strength
    local air = humanoid.FloorMaterial == Enum.Material.Air
    rig.airTime = if air then rig.airTime + deltaTime else 0
    local grounded = rig.airTime < AIR_GRACE
    local busy = rig.busy
    local alive = humanoid.Health > 0
    local running = alive and grounded and not busy and speed >= RUN_MIN
    local ratio = speed / math.max(humanoid.WalkSpeed, 1)
    local sprintTarget = if running and speed >= RUN_MIN + 2 then math.clamp((ratio - SPRINT_FROM) / (SPRINT_FULL - SPRINT_FROM), 0, 1) else 0
    if tier < 2 then
        sprintTarget = 0
    end
    -- a jog is what the speed gives; a runner at their own top speed is at least at three quarters
    local target = if running then math.max(math.clamp((speed - RUN_MIN) / (RUN_JOG_FULL - RUN_MIN), 0.12, 1), 0.75 * sprintTarget) else 0
    local rate = if target > rig.lvl then UP_RATE elseif air and rig.airTime >= AIR_GRACE then AIR_DOWN_RATE else DOWN_RATE
    rig.lvl += (target - rig.lvl) * (1 - math.exp(-rate * deltaTime))
    local sprintRate = if sprintTarget > rig.sprint then SPRINT_UP else SPRINT_DOWN
    rig.sprint += (sprintTarget - rig.sprint) * (1 - math.exp(-sprintRate * deltaTime))
    local lvl, sprint = rig.lvl, rig.sprint
    if lvl < 0.01 and target == 0 then
        rig.lvl, rig.sprint = 0, 0
        park(rig, now)
        return
    end
    rig.parked = false
    local pace = math.clamp((speed - RUN_MIN) / (RUN_TOP - RUN_MIN), 0, 1)
    rig.sinceRing += speed * deltaTime
    rig.stride += speed * deltaTime

    -- the steps
    if running and lvl > 0.2 and now - rig.lastPlant >= PLANT_GAP then
        local ground = root.Position.Y - rig.feet
        local planted, stepped = nil, false
        for index = 1, 2 do
            local foot = if index == 1 then rig.footL else rig.footR
            if foot then
                local h = foot.Position.Y - foot.Size.Y * 0.5 - ground
                if rig.footDown[index] then
                    if h > FOOT_UP then
                        rig.footDown[index] = false
                    end
                elseif h < FOOT_DOWN then
                    rig.footDown[index] = true
                    if not stepped then
                        stepped, planted = true, foot
                    end
                end
            end
        end
        if not stepped and rig.stride >= STRIDE_FALLBACK and now - rig.lastPlant > 0.3 then -- no foot seen: a step every few studs
            stepped = true
            rig.side = -rig.side
            planted = if rig.side > 0 then rig.footL else rig.footR
        end
        if stepped then
            plant(rig, planted, now, tier, pace, sprint, SURFACE_CLASS[humanoid.FloorMaterial] or "stone")
        end
    end

    -- the wake (what a tier does not draw is let go: a runner who falls from a near tier to a far one, or a screen that goes to
    -- Reduced Effects, stops emitting in a moment)
    local full = tier >= 3
    local wake = tier >= 2
    local level = lvl * detail
    setRate(rig, "veil", rig.veil, if wake then (6 + 8 * sprint) * level else 0)
    local curl = (4 + 5 * sprint) * level
    rig.spin += deltaTime * (14 + 16 * pace)
    local radius = 0.7 + 0.45 * pace
    local c, s = math.cos(rig.spin), math.sin(rig.spin)
    setRate(rig, "curlA", rig.curlA, if wake then curl * (if full then 1 else 0.6) else 0)
    setRate(rig, "curlB", rig.curlB, if full then curl else 0)
    setRate(rig, "swirl", rig.swirl, if full then (4 + 3 * sprint) * level else 0)
    setRate(rig, "rush", rig.rush, if full and not isLow then 16 * sprint * sprint else 0)
    if wake then
        rig.helixA.Position = Vector3.new(c * radius, 0.5 + s * radius * 0.8, 0.7)
        if full then
            rig.helixB.Position = Vector3.new(-c * radius, 0.5 - s * radius * 0.8, 0.7)
            rig.heelAtt.Position = Vector3.new(c * 0.45, -rig.feet + 0.5 + math.abs(s) * 0.3, 0.6)
        end
    end
    if rig.sig then
        setRate(rig, "sig", rig.sig, if wake then rig.sigRate * level * (0.55 + 0.45 * sprint) else 0)
    end

    -- rings of compressed air thrown ahead, and afterimages
    if full and sprint > 0.55 then
        if now >= rig.nextCompress then
            rig.nextCompress = now + 0.62 - 0.22 * pace
            rig.front.Position = Vector3.new(0, 0.1, -(2.8 + speed * 0.1))
            rig.compress:Emit(1)
        end
        if rig.isLocal and not isLow and sprint > 0.45 and pace >= GHOST_FROM_PACE then
            rig.lastSprint = now
            if not rig.ghosts and now >= rig.ghostRetry then
                if not buildGhosts(rig) then
                    rig.ghostRetry = now + 2 -- a body without its limbs (still loading): look again in a moment
                end
            end
            rig.ghostSince += speed * deltaTime
            if rig.ghosts and rig.ghostSince >= GHOST_SPACING then
                rig.ghostSince = 0
                spawnGhost(rig)
            end
        end
    end
end

local function trim(rig, now)
    if rig.ghosts and now - rig.lastSprint > GHOST_IDLE then
        destroyGhosts(rig)
    end
end

function RunFx.step(deltaTime, busy)
    local now = os.clock()
    local camera = Workspace.CurrentCamera
    local cameraPosition = if camera then camera.CFrame.Position else nil
    local reduced = localPlayer ~= nil and localPlayer:GetAttribute("SettingReducedEffects") == true
    if inStudio and localPlayer then
        asOther = localPlayer:GetAttribute("QARunAsOther") == true
        isLow = Quality.Low or localPlayer:GetAttribute("QARunLow") == true
    end
    local near, far = if isLow then NEAR_LOW else NEAR_OTHERS, if isLow then FAR_LOW else FAR_OTHERS

    for index = 1, #playerList do
        local player = playerList[index]
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        local root = humanoid and humanoid.RootPart
        local rig = character and rigs[character]
        if not (humanoid and root and root.Parent) then
            continue
        end

        -- how much of the effect this runner gets on this screen
        local tier
        if player == localPlayer and not asOther then
            tier = if reduced then 1 else 3
        elseif cameraPosition == nil then
            tier = 0
        else
            local distance = (cameraPosition - root.Position).Magnitude
            tier = if distance <= near then 2 elseif distance <= far then 1 else 0
            if reduced and tier > 1 then
                tier = 1
            end
        end

        if not rig then
            -- a runner without a rig gets one only when they are really running
            if tier > 0 and humanoid.Health > 0 and humanoid.FloorMaterial ~= Enum.Material.Air then
                local v = root.AssemblyLinearVelocity
                if v.X * v.X + v.Z * v.Z >= RUN_MIN * RUN_MIN then
                    rig = build(player, character, humanoid, root, realmOf(player))
                    rig.nextRealmCheck = now + 1
                    rigs[character] = rig
                    character.Destroying:Connect(function()
                        local entry = rigs[character]
                        if entry then
                            destroyRig(entry)
                            rigs[character] = nil
                        end
                    end)
                end
            end
        end
        if rig then
            rig.isLocal = player == localPlayer and not asOther
            rig.busy = player:GetAttribute("IsFlying") == true or humanoid.Sit or busy(character)
            if tier == 0 then
                -- out of reach: let it go quietly
                if not rig.parked then
                    rig.lvl, rig.sprint = 0, 0
                    park(rig, now)
                end
            else
                if now >= rig.nextRealmCheck then
                    rig.nextRealmCheck = now + 1
                    local realm = realmOf(player)
                    if realm ~= rig.realm then -- the realm changed: rebuilt in its colours and its signature
                        destroyRig(rig)
                        rigs[character] = nil
                        rig = build(player, character, humanoid, root, realm)
                        rig.nextRealmCheck = now + 1
                        rigs[character] = rig
                    end
                end
                stepRig(rig, deltaTime, now, tier)
            end
            if rig.ghosts then
                if updateGhosts(rig, deltaTime, cameraPosition) == false then
                    trim(rig, now)
                end
            end
        end
    end

    -- characters that left without being destroyed, players who left, idle rigs of other players
    for character, rig in rigs do
        if character.Parent == nil or rig.player.Parent == nil then
            destroyRig(rig)
            rigs[character] = nil
        elseif not rig.isLocal and rig.parked and now - rig.parkedAt > PARK_DESTROY then
            destroyRig(rig)
            rigs[character] = nil
        end
    end
end

-- Studio checks
function RunFx.stats()
    local rigCount, emitters, ghostParts = 0, 0, 0
    for _, rig in rigs do
        rigCount += 1
        emitters += rig.emitters
        if rig.ghosts then
            ghostParts += GHOSTS * #rig.ghostSources
        end
    end
    return { rigs = rigCount, emitters = emitters, ghostParts = ghostParts }
end

for _, player in Players:GetPlayers() do
    table.insert(playerList, player)
end
Players.PlayerAdded:Connect(function(player)
    table.insert(playerList, player)
end)
Players.PlayerRemoving:Connect(function(player)
    local at = table.find(playerList, player)
    if at then
        table.remove(playerList, at)
    end
    local character = player.Character
    local rig = character and rigs[character]
    if rig then
        destroyRig(rig)
        rigs[character] = nil
    end
end)

return RunFx

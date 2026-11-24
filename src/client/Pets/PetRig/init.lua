-- Rigs and animates every pet: PetRig.build (a jointed model) and buildSkinned (one skin on bones), each pet's profile
-- (PetRig.Profiles: its bones, points, glow and special) and its animate function, played each frame by PetRig.update
-- (idles, walking, flight, cultivating and its special, the Blasts).
local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local PetRig = {}

-- (kept on the module, not as locals: the main chunk sits at Luau's 200-local limit)
PetRig.Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
PetRig.PetSounds = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("PetSounds"))
PetRig.LIGHT_REACH = 26 -- studs: the farthest a pet's light reaches, whatever its size (PetRig.update holds big pets' lights to it)
PetRig.VOICE_EVERY = { 9, 18 } -- seconds between a pet's calls while it idles in the world (PetSounds)
PetRig.Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality")) -- the phone tier: other players' pets drop their lights

local SPARKLE = "rbxasset://textures/particles/sparkles_main.dds"

-- Plays a tween once a delay has passed. A later step can't be queued with TweenInfo's DelayTime when an earlier tween on the same instance
-- changes the same property: playing the later one cancels the earlier at once, delay or not (measured in Studio, 2026-11-08). So it waits here.
local function tweenAfter(delay, instance, info, goal)
    task.delay(delay, function()
        if instance.Parent then
            TweenService:Create(instance, info, goal):Play()
        end
    end)
end

local function pose(motor, cframe)
    if motor then
        motor.Transform = cframe
    end
end

local function smoothstep(edge0, edge1, x)
    local t = math.clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
end

-- ---------- the pets' animations and effects live in the folders beside this file (split out of one 17,700-line file on 2026-11-24, code unchanged) ----------
-- K carries what the pieces share; each piece in Animators/ returns the animate functions (and any helper) it defines.
local K = { PetRig = PetRig, Debris = Debris, Lighting = Lighting, Players = Players, RunService = RunService, TweenService = TweenService, SPARKLE = SPARKLE, tweenAfter = tweenAfter, pose = pose, smoothstep = smoothstep }
local Animators = {}
for _, name in { "SunDragon", "Hellhound", "Sprite", "Golem", "Panda", "Deer", "Sphinx", "Cub", "CloudSheep", "JadeWyrmTurtle", "NebulaOwl", "CosmicJellyfish", "StarfallFox", "LanternWarden", "DreamMoth", "PrismArmadillo", "CrystalSnail", "AbyssAnomalocaris", "VoidscaleHydra", "TheNamelessOne", "EclipseCat", "Shadowcoil", "PearlDragon", "SnowLeopard", "CometStag", "SandPhantom", "SolarButterfly", "TimekeeperTortoise", "GravityImp", "GlacierPuff", "ObsidianGuardian", "WindSprite", "GalaxyManta", "StormhornKirin", "Lion", "Brute" } do
    for key, value in require(script:WaitForChild("Animators"):WaitForChild(name))(K) do
        K[key] = value
        Animators[key] = value
    end
end
local ANOMALO_GLOW = Animators.ANOMALO_GLOW
local CAT_LEADS = Animators.CAT_LEADS
local GUARD_BONES = Animators.GUARD_BONES
local GUARD_VIOLET = Animators.GUARD_VIOLET
local HYDRA_LIGHT = Animators.HYDRA_LIGHT
local IMP = Animators.IMP
local LEOPARD_BONES = Animators.LEOPARD_BONES
local NAMELESS_HALO = Animators.NAMELESS_HALO
local NAMELESS_SPARK = Animators.NAMELESS_SPARK
local PEARL_BONES = Animators.PEARL_BONES
local PEARL_GLOW = Animators.PEARL_GLOW
local SAND_BONES = Animators.SAND_BONES
local SHADOW_BONES = Animators.SHADOW_BONES
local SHADOW_EYESHINE = Animators.SHADOW_EYESHINE
local SHADOW_RIM = Animators.SHADOW_RIM
local STAG_BONES = Animators.STAG_BONES
local TORT = Animators.TORT
local dropToGround = Animators.dropToGround
local jellyBones = Animators.jellyBones

PetRig.Profiles = {
    SunscaleDragon = {
        Joints = {
            Body = "Root",
            Neck = "Body",
            Head = "Neck",
            WingL = "Body",
            WingR = "Body",
            WingL2 = "WingL",
            WingR2 = "WingR",
            LegFL = "Body",
            LegFR = "Body",
            LegBL = "Body",
            LegBR = "Body",
            Tail = "Body",
            Tail2 = "Tail",
        },
        GlowColors = {
            ffdd81 = Color3.fromRGB(255, 175, 40),
            ffeaa6 = Color3.fromRGB(255, 195, 70),
            ffbc3f = Color3.fromRGB(255, 145, 15),
            ffb338 = Color3.fromRGB(255, 120, 10),
            ff952c = Color3.fromRGB(255, 100, 10),
            f98127 = Color3.fromRGB(220, 60, 0),
        },
        Effects = {
            Motes = "Body",
            Light = "Body",
            Pulse = "Body",
            Burst = "Body",
            Sparks = { "Head_Crest", "Tail2_Sun" },
            Trail = { "WingL2_Tip", "WingR2_Tip" },
            Blast = "SolarCorona",
            NovaLight = 3,
        },
        Colors = {
            Gold = Color3.fromHex("FFC24A"),
            Amber = Color3.fromHex("6B2E12"),
            Orange = Color3.fromHex("FF8A2A"),
            Sun = Color3.fromHex("FFE9A6"),
            Ivory = Color3.fromHex("FFF4DC"),
        },
        Animate = Animators.animateSunDragon,
    },
}

PetRig.Profiles.DreadfangCerberus = {
    Joints = {
        Body = "Root",
        HeadC = "Body",
        HeadL = "Body",
        HeadR = "Body",
        JawC = "HeadC",
        JawL = "HeadL",
        JawR = "HeadR",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        Tail1 = "Body",
        Tail2 = "Tail1",
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "HeadC_Eye", "HeadL_Eye", "HeadR_Eye" },
        Trail = "Tail2_Tip",
        Blast = "HellBreath",
    },
    Colors = {
        Gold = Color3.fromRGB(40, 215, 255),
        Amber = Color3.fromRGB(20, 70, 160),
        Orange = Color3.fromRGB(30, 150, 255),
        Sun = Color3.fromRGB(190, 250, 255),
        Ivory = Color3.fromRGB(225, 250, 255),
    },
    Animate = Animators.animateHellhound,
}

PetRig.Profiles.MyceliumSprite = {
    Joints = {
        Body = "Root",
        Cap = "Body",
        ArmL = "Body",
        ArmR = "Body",
        Threads = "Body",
    },
    Effects = {
        Motes = "Cap",
        Light = "Body",
        Pulse = "Cap",
        Burst = "Body",
        Sparks = { "ArmL_Puff", "ArmR_Puff" },
        Trail = "Threads_Tip",
        Blast = "SporeBloom",
        NovaLight = 4,
    },
    Colors = {
        Gold = Color3.fromRGB(90, 245, 215),
        Amber = Color3.fromRGB(70, 60, 190),
        Orange = Color3.fromRGB(150, 110, 255),
        Sun = Color3.fromRGB(200, 255, 245),
        Ivory = Color3.fromRGB(230, 240, 255),
    },
    Animate = Animators.animateSprite,
}

PetRig.Profiles.MossGolem = {
    Joints = {
        Body = "Root",
        Head = "Body",
        ArmL = "Body",
        ArmR = "Body",
        ArmL2 = "ArmL",
        ArmR2 = "ArmR",
        LegL = "Body",
        LegR = "Body",
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "Body_Core" },
        Blast = "Groundbreaker",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(110, 255, 140),
        Amber = Color3.fromRGB(105, 102, 94),
        Orange = Color3.fromRGB(120, 200, 70),
        Sun = Color3.fromRGB(200, 255, 190),
        Ivory = Color3.fromRGB(225, 255, 220),
    },
    Animate = Animators.animateGolem,
}

PetRig.Profiles.JadeSpiritPanda = {
    Joints = {
        Body = "Root",
        Head = "Body",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
    },
    SeeThroughGlow = { ["89edbc"] = 0.3 },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "Head_Gem", "Body_Crystal" },
        Blast = "JadeLotus",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(60, 225, 130),
        Amber = Color3.fromRGB(20, 70, 45),
        Orange = Color3.fromRGB(80, 235, 205),
        Sun = Color3.fromRGB(195, 255, 220),
        Ivory = Color3.fromRGB(230, 250, 235),
    },
    Animate = Animators.animatePanda,
}

PetRig.Profiles.JadeAntlerDeer = {
    Joints = {
        Body = "Root",
        Neck = "Body",
        Head = "Neck",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        LegFL2 = "LegFL",
        LegFR2 = "LegFR",
        LegBL2 = "LegBL",
        LegBR2 = "LegBR",
    },
    SeeThroughGlow = { adedce = 0.4, ["89ffd3"] = 0.2 },
    GlowColors = {
        adedce = Color3.fromRGB(40, 200, 140),
        ["89ffd3"] = Color3.fromRGB(20, 225, 160),
        f3c461 = Color3.fromRGB(255, 160, 20),
        ["61f1d4"] = Color3.fromRGB(20, 210, 170),
    },
    Effects = {
        Motes = "Head",
        Light = "Head",
        Pulse = "Head",
        Burst = "Body",
        Sparks = { "LegFL2_Hoof", "LegFR2_Hoof", "LegBL2_Hoof", "LegBR2_Hoof" },
        Trail = "Body_Tail",
        Blast = "SacredGrove",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(45, 215, 130),
        Amber = Color3.fromRGB(25, 60, 35),
        Orange = Color3.fromRGB(90, 230, 200),
        Sun = Color3.fromRGB(200, 255, 225),
        Ivory = Color3.fromRGB(240, 240, 225),
    },
    Animate = Animators.animateDeer,
}

PetRig.Profiles.RuneSphinx = {
    Joints = {
        Body = "Root",
        Head = "Body",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        Tail = "Body",
        Tail2 = "Tail",
    },
    SeeThroughGlow = { ffad3f = 0.15 },
    GlowColors = {
        ffc555 = Color3.fromRGB(255, 140, 0),
        ffc461 = Color3.fromRGB(240, 120, 10),
        ffad3f = Color3.fromRGB(255, 95, 0),
        f98e27 = Color3.fromRGB(200, 55, 0),
        fff6cb = Color3.fromRGB(255, 200, 70),
    },
    Effects = {
        Motes = "Head",
        Light = "Body",
        Pulse = "Head",
        Burst = "Body",
        Sparks = { "LegFL_Paw", "LegFR_Paw", "LegBL_Paw", "LegBR_Paw" },
        Blast = "RuneSeal",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 196, 97),
        Amber = Color3.fromRGB(60, 45, 30),
        Orange = Color3.fromRGB(255, 160, 48),
        Sun = Color3.fromRGB(255, 240, 200),
        Ivory = Color3.fromRGB(255, 250, 235),
    },
    Animate = Animators.animateSphinx,
}

PetRig.Profiles.MagmaCub = {
    Joints = {
        Body = "Root",
        Head = "Body",
        ArmL = "Body",
        ArmR = "Body",
        LegL = "Body",
        LegR = "Body",
        Tail = "Body",
    },
    GlowColors = {
        ffce61 = Color3.fromRGB(255, 150, 20),
        ff9b30 = Color3.fromRGB(255, 85, 0),
        ffad27 = Color3.fromRGB(255, 110, 0),
        ffda61 = Color3.fromRGB(255, 175, 30),
        ed6119 = Color3.fromRGB(220, 50, 0),
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "ArmL_Paw", "ArmR_Paw", "Head_Vent" },
        Blast = "MagmaPop",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 140, 30),
        Amber = Color3.fromRGB(40, 30, 28),
        Orange = Color3.fromRGB(255, 80, 10),
        Sun = Color3.fromRGB(255, 200, 90),
        Ivory = Color3.fromRGB(255, 235, 200),
    },
    Animate = Animators.animateCub,
}

PetRig.Profiles.CloudSheep = {
    Skinned = true,
    SkinTint = Color3.fromRGB(255, 240, 216), -- the game's light pushes its slate face to royal blue: this brings it back (seen in Studio)
    Bones = {
        "Body", "Head", "WoolCap", "Tail", "WoolTop", "WoolBack", "WoolChest", "WoolL", "WoolR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR", "Smile", "Mouth",
        "LegFL1", "LegFL2", "HoofFL", "LegFR1", "LegFR2", "HoofFR", "LegBL1", "LegBL2", "HoofBL", "LegBR1", "LegBR2", "HoofBR",
    },
    Points = { "Tail" },
    GlowColors = {
        ["f0ead8"] = Color3.fromRGB(170, 165, 150), -- the catch-light in its eye
    },
    Effects = {
        Burst = "Body",
        Trail = "Tail",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "CloudBloom",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(190, 215, 240),
        Amber = Color3.fromRGB(150, 150, 190),
        Orange = Color3.fromRGB(185, 195, 235),
        Sun = Color3.fromRGB(240, 248, 255),
        Ivory = Color3.fromRGB(250, 250, 255),
    },
    Animate = Animators.animateCloudSheep,
}

PetRig.Profiles.JadeWyrmTurtle = {
    Skinned = true,
    Bones = {
        "Body", "Shell", "Neck1", "Neck2", "Neck3", "Neck4", "Head", "Jaw", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "FrillL", "FrillR",
        "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip",
        "LegFL1", "LegFL2", "FootFL", "LegFR1", "LegFR2", "FootFR", "LegBL1", "LegBL2", "FootBL", "LegBR1", "LegBR2", "FootBR",
        "Plum1", "Plum2", "PadA", "PadB", "PadC", "Pine1", "PineA", "PineB", "PineC",
    },
    Points = { "FootFR", "TailTip", "PadA", "PadB", "PadC" },
    GlowColors = {
        ["24c0a4"] = Color3.fromRGB(26, 170, 150), -- the spring
        ["f0ead8"] = Color3.fromRGB(170, 165, 150), -- the catch-light in its eye
    },
    Effects = {
        Pulse = "Spring",
        Burst = "Body",
        Trail = "TailTip",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "BetweenSteps",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(110, 225, 180),
        Amber = Color3.fromRGB(235, 190, 110),
        Orange = Color3.fromRGB(245, 170, 195),
        Sun = Color3.fromRGB(225, 250, 235),
        Ivory = Color3.fromRGB(250, 240, 225),
    },
    Animate = Animators.animateJadeWyrmTurtle,
}

PetRig.Profiles.NebulaOwl = {
    Skinned = true,
    Bones = {
        "Body", "Chest", "Head", "BeakLow", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "BrowL", "BrowR", "TuftL", "TuftR",
        "WingL1", "WingL2", "WingL3", "WingPL", "WingR1", "WingR2", "WingR3", "WingPR", "Tail", "TailL", "TailR", "LegL", "FootL", "LegR", "FootR",
    },
    Points = { "WingPL", "WingPR" },
    GlowColors = {
        ["d6b4ff"] = Color3.fromRGB(176, 122, 255), -- the new stars in its wings
        ["f0ead8"] = Color3.fromRGB(190, 182, 160), -- the catch-lights in its eyes
    },
    Effects = {
        Burst = "Body",
        Trail = { "WingPL", "WingPR" },
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "StarsNotYetBorn",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(176, 122, 255),
        Amber = Color3.fromRGB(240, 120, 200),
        Orange = Color3.fromRGB(120, 76, 230),
        Sun = Color3.fromRGB(235, 220, 255),
        Ivory = Color3.fromRGB(245, 240, 255),
    },
    Animate = Animators.animateNebulaOwl,
}

PetRig.Profiles.CosmicJellyfish = {
    Skinned = true,
    SeeThrough = { Glass = 0.5 }, -- its bell: the nebula shows through it, and the sky through the rest
    Bones = jellyBones(),
    Points = { "Apex" },
    GlowColors = {
        ["ffb04a"] = Color3.fromRGB(255, 118, 26), -- the four horseshoes (warm gold: paler goes to lemon as Neon)
    },
    Effects = {
        Burst = "Body",
        Blast = "RollingNebula",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(245, 120, 180),
        Amber = Color3.fromRGB(255, 170, 84),
        Orange = Color3.fromRGB(128, 84, 226),
        Sun = Color3.fromRGB(255, 225, 235),
        Ivory = Color3.fromRGB(250, 240, 248),
    },
    Animate = Animators.animateCosmicJellyfish,
}

PetRig.Profiles.StarfallFox = {
    Skinned = true,
    Bones = {
        "Body", "Hips", "Chest", "Neck", "Head", "Jaw", "Mouth", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR",
        "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip",
        "LegFL1", "LegFL2", "PawFL", "LegFR1", "LegFR2", "PawFR", "LegBL1", "LegBL2", "PawBL", "LegBR1", "LegBR2", "PawBR",
    },
    Points = { "TailTip", "Mouth", "PawFL", "PawFR" },
    GlowColors = {
        ["f6ecd6"] = Color3.fromRGB(190, 182, 160), -- the catch-lights in its eyes (full white blooms over the whole eye)
    },
    Effects = {
        Burst = "Body",
        Trail = "TailTip",
        TrailWidth = 0.05, -- flying, its white brush draws a comet's thin tail
        TrailTaper = true,
        Blast = "StarInItsTeeth",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(248, 192, 92),
        Amber = Color3.fromRGB(214, 120, 28),
        Orange = Color3.fromRGB(120, 140, 255),
        Sun = Color3.fromRGB(255, 240, 200),
        Ivory = Color3.fromRGB(245, 245, 255),
    },
    Animate = Animators.animateStarfallFox,
}

PetRig.Profiles.LanternWarden = {
    Skinned = true,
    Bones = {
        "Body", "Chest", "Neck", "Head", "Hat", "EyeL", "EyeR", "Crook1", "Crook2", "Crook3", "Chain1", "Chain2", "Lantern", "Flame",
        "MidF", "MidL", "MidB", "MidR", "LowF", "LowL", "LowB", "LowR",
        "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR", "LegL1", "LegL2", "LegL3", "FootL", "LegR1", "LegR2", "LegR3", "FootR",
    },
    Points = { "Flame" },
    GlowColors = {
        ["ffc070"] = Color3.fromRGB(255, 118, 26), -- the lantern's paper (paler goes to lemon as Neon)
        ["ffe6b0"] = Color3.fromRGB(190, 170, 130), -- the catch-lights behind its mask
    },
    Effects = {
        Burst = "Body",
        Trail = "Flame",
        TrailWidth = 0.06, -- flying, the lantern draws a thin line of light behind it
        TrailTaper = true,
        Blast = "TheLongWayRound",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 176, 70),
        Amber = Color3.fromRGB(255, 130, 50),
        Orange = Color3.fromRGB(214, 90, 30),
        Sun = Color3.fromRGB(255, 225, 160),
        Ivory = Color3.fromRGB(245, 235, 210),
    },
    Animate = Animators.animateLanternWarden,
}

PetRig.Profiles.DreamMoth = {
    Skinned = true,
    Bones = {
        "Body", "Abd1", "Abd2", "Abd3", "Head", "PupilL", "PupilR", "AntL1", "AntL2", "AntR1", "AntR2",
        "ForeL1", "ForeL2", "HindL1", "HindL2", "ForeR1", "ForeR2", "HindR1", "HindR2",
        "LegFL1", "LegFL2", "LegML1", "LegML2", "LegBL1", "LegBL2", "LegFR1", "LegFR2", "LegMR1", "LegMR2", "LegBR1", "LegBR2",
        "Tongue1", "Tongue2", "Tongue3", "Tongue4", "Tongue5", "Tongue6", "Tongue7", "Tongue8", "Tongue9", "Tongue10", "Tongue11", "Tongue12",
    },
    Points = { "Tongue12", "PupilL", "PupilR", "Abd3" },
    Effects = {
        Burst = "Body",
        Trail = "Abd3",
        TrailWidth = 0.04, -- flying, a faint thread of scale dust behind it
        TrailTaper = true,
        Blast = "AForgottenDream",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(236, 190, 255),
        Amber = Color3.fromRGB(255, 196, 228),
        Orange = Color3.fromRGB(196, 168, 255),
        Sun = Color3.fromRGB(255, 236, 250),
        Ivory = Color3.fromRGB(255, 250, 255),
    },
    Animate = Animators.animateDreamMoth,
}

PetRig.Profiles.PrismArmadillo = {
    Skinned = true,
    Bones = {
        "Body", "Front", "Neck", "Head", "Mid", "Back", "Pelvis", "Tail1", "Tail2", "Tail3", "EarL", "EarR", "CheekL", "CheekR",
        "LegFL1", "LegFL2", "PawFL", "LegFR1", "LegFR2", "PawFR", "LegBL1", "LegBL2", "PawBL", "LegBR1", "LegBR2", "PawBR",
    },
    Points = { "Body" },
    GlowColors = {
        ["ff7ab4"] = Color3.fromRGB(255, 160, 200), -- the crest prisms: their colours are set each frame, these are only where they start
        ["ffc864"] = Color3.fromRGB(255, 220, 150),
        ["8cf0a0"] = Color3.fromRGB(160, 240, 180),
        ["78c8ff"] = Color3.fromRGB(150, 210, 255),
        ["a08cff"] = Color3.fromRGB(180, 160, 255),
        ["f08cff"] = Color3.fromRGB(240, 160, 255),
    },
    Effects = {
        Burst = "Body",
        Blast = "EveryColour",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(200, 170, 255),
        Amber = Color3.fromRGB(255, 180, 220),
        Orange = Color3.fromRGB(150, 210, 255),
        Sun = Color3.fromRGB(245, 240, 255),
        Ivory = Color3.fromRGB(250, 248, 255),
    },
    Animate = Animators.animatePrismArmadillo,
}

PetRig.Profiles.CrystalSnail = {
    Skinned = true,
    Bones = {
        "Body", "Tail1", "Tail2", "TailTip", "Front", "Head", "Shell",
        "StalkL1", "StalkL2", "StalkL3", "StalkR1", "StalkR2", "StalkR3",
    },
    Points = { "TailTip", "Shell" },
    GlowColors = {
        ["8ff5dc"] = Color3.fromRGB(70, 225, 190), -- the glowing crystal in each cluster (set each frame; paler goes to white as Neon)
    },
    Effects = {
        Burst = "Body",
        Blast = "AHundredYears",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(110, 230, 200),
        Amber = Color3.fromRGB(150, 240, 220),
        Orange = Color3.fromRGB(60, 170, 160),
        Sun = Color3.fromRGB(210, 255, 240),
        Ivory = Color3.fromRGB(235, 255, 250),
    },
    Animate = Animators.animateCrystalSnail,
}

PetRig.Profiles.AbyssAnomalocaris = {
    Skinned = true,
    Bones = {
        "Body", "Seg2", "Seg1", "Head", "Seg4", "Seg5", "Seg6", "Seg7", "Seg8", "Seg9", "Tail",
        "FlapL1", "FlapL2", "FlapL3", "FlapL4", "FlapL5", "FlapL6", "FlapL7", "FlapL8", "FlapL9",
        "FlapR1", "FlapR2", "FlapR3", "FlapR4", "FlapR5", "FlapR6", "FlapR7", "FlapR8", "FlapR9",
        "FanL1", "FanL2", "FanL3", "FanR1", "FanR2", "FanR3",
        "ArmL1", "ArmL2", "ArmL3", "ArmL4", "ArmL5", "ArmL6", "ArmR1", "ArmR2", "ArmR3", "ArmR4", "ArmR5", "ArmR6",
        "StalkL", "StalkR", "EyeL", "EyeR",
    },
    Points = { "Head", "ArmL5", "ArmR5" },
    GlowColors = {
        ["e040b8"] = ANOMALO_GLOW, -- the thin line along every flap's and tail blade's outer edge (set each frame)
    },
    Effects = {
        Burst = "Body",
        Blast = "TheFirstHunt",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(225, 50, 175),
        Amber = Color3.fromRGB(255, 140, 220),
        Orange = Color3.fromRGB(196, 138, 66),
        Sun = Color3.fromRGB(255, 200, 240),
        Ivory = Color3.fromRGB(255, 235, 250),
    },
    Animate = Animators.animateAbyssAnomalocaris,
}

PetRig.Profiles.VoidscaleHydra = {
    Skinned = true,
    Bones = {
        "Body", "Chest", "Hips", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5",
        "UpperFL", "LowerFL", "FootFL", "UpperBL", "LowerBL", "FootBL", "UpperFR", "LowerFR", "FootFR", "UpperBR", "LowerBR", "FootBR",
        "NeckL1", "NeckL2", "NeckL3", "NeckL4", "NeckR1", "NeckR2", "NeckR3", "NeckR4", "NeckM1", "NeckM2", "ForkL1", "ForkL2", "ForkR1", "ForkR2",
        "HeadL", "HeadR", "HeadML", "HeadMR", "TongueL", "TongueR", "TongueML", "TongueMR",
    },
    Points = { "HeadL", "HeadR", "HeadML", "HeadMR" },
    GlowColors = {
        ["5aa0ff"] = HYDRA_LIGHT, -- the eye slits and the tongues (set each frame)
    },
    Effects = {
        Burst = "Body",
        Blast = "TheVoidBetween",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(70, 150, 255),
        Amber = Color3.fromRGB(150, 200, 255),
        Orange = Color3.fromRGB(40, 70, 190),
        Sun = Color3.fromRGB(200, 225, 255),
        Ivory = Color3.fromRGB(235, 242, 255),
    },
    Animate = Animators.animateVoidscaleHydra,
}

local function namelessBones()
    local bones = { "Hips", "Body", "Chest", "Neck", "Head", "Spark", "Halo" }
    for _, side in { "L", "R" } do
        for k = 1, 5 do
            table.insert(bones, "Arm" .. side .. k)
        end
        for k = 1, 3 do
            table.insert(bones, "Scarf" .. side .. k)
        end
    end
    for k = 0, 7 do
        for _, tag in { "a", "b", "c" } do
            table.insert(bones, "Hem" .. k .. tag)
        end
    end
    return bones
end

PetRig.Profiles.TheNamelessOne = {
    Skinned = true,
    Bones = namelessBones(),
    Points = { "Chest", "Spark", "ArmL5", "ArmR5" },
    GlowColors = {
        ["f4f0ff"] = NAMELESS_SPARK, -- the point of light in the hollow
        ["b89cff"] = NAMELESS_HALO, -- the broken halo and the tips that write (set each frame)
    },
    Effects = {
        Burst = "Body",
        Blast = "Unwritten",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(200, 170, 255),
        Amber = Color3.fromRGB(150, 120, 230),
        Orange = Color3.fromRGB(90, 60, 170),
        Sun = Color3.fromRGB(240, 235, 255),
        Ivory = Color3.fromRGB(250, 248, 255),
    },
    Animate = Animators.animateTheNamelessOne,
}

local function catBones()
    local bones = { "Body", "Hips", "Chest", "Neck", "Head", "Pendant", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR" }
    for k = 1, 6 do
        table.insert(bones, "Tail" .. k)
    end
    for key in CAT_LEADS do
        for k = 1, 3 do
            table.insert(bones, "Leg" .. key .. k)
        end
        table.insert(bones, "Paw" .. key)
    end
    return bones
end

PetRig.Profiles.EclipseCat = {
    Skinned = true,
    Bones = catBones(),
    Points = { "Head", "Tail6" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        ffd27a = Color3.fromRGB(255, 196, 90), -- the crescent on its forehead
        ffd27b = Color3.fromRGB(255, 188, 84), -- the thread of gold along its tail
        b07cff = Color3.fromRGB(176, 124, 255), -- the gem under its pendant
    },
    Effects = {
        Burst = "Body",
        Blast = "Totality",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 200, 100),
        Amber = Color3.fromRGB(196, 150, 255),
        Orange = Color3.fromRGB(118, 70, 220),
        Sun = Color3.fromRGB(255, 236, 190),
        Ivory = Color3.fromRGB(245, 238, 255),
    },
    Animate = Animators.animateEclipseCat,
}

local function shadowProfileBones()
    local bones = table.clone(SHADOW_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.Shadowcoil = {
    Skinned = true,
    Bones = shadowProfileBones(),
    Points = { "Tail7" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "FirstMove",
    },
    Colors = {
        Gold = SHADOW_EYESHINE,
        Amber = SHADOW_RIM,
        Orange = Color3.fromRGB(60, 46, 96),
        Sun = Color3.fromRGB(220, 255, 240),
        Ivory = Color3.fromRGB(236, 232, 248),
    },
    Animate = Animators.animateShadowcoil,
}

local function pearlProfileBones()
    local bones = table.clone(PEARL_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.CelestialPearlDragon = {
    Skinned = true,
    Bones = pearlProfileBones(),
    SkinTint = Color3.fromRGB(200, 198, 214), -- its near-white nacre blows out in daylight: toned down, the scale rows and plates read (seen in Play)
    Points = { "HandR", "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        fff4e2 = PEARL_GLOW, -- the pearl
    },
    Effects = {
        Blast = "HeavenCondensed",
        Pulse = "Pearl", -- (its light and motes ride on the hand: pearlGlow)
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 240, 214),
        Amber = Color3.fromRGB(224, 210, 255),
        Orange = Color3.fromRGB(196, 176, 255),
        Sun = Color3.fromRGB(255, 250, 240),
        Ivory = Color3.fromRGB(246, 238, 218),
    },
    Animate = Animators.animatePearlDragon,
}

local function leopardProfileBones()
    local bones = table.clone(LEOPARD_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.CelestialSnowLeopard = {
    Skinned = true,
    Bones = leopardProfileBones(),
    Points = { "Tail4", "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "WhereTheSkyBegins",
    },
    Colors = {
        Gold = Color3.fromRGB(196, 232, 255),
        Amber = Color3.fromRGB(140, 200, 255),
        Orange = Color3.fromRGB(70, 110, 200),
        Sun = Color3.fromRGB(240, 250, 255),
        Ivory = Color3.fromRGB(246, 247, 250),
    },
    Animate = Animators.animateSnowLeopard,
}

local function stagProfileBones()
    local bones = table.clone(STAG_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.CometStag = {
    Skinned = true,
    Bones = stagProfileBones(),
    SkinTint = Color3.fromRGB(180, 184, 210), -- its night-blue hide washed out pale in daylight; deeper, the antlers keep their gold (seen in Play)
    Points = { "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        eaf6ff = Color3.fromRGB(190, 228, 255), -- the comet's nucleus on its brow: a touch of blue, or Neon blooms it to plain white
    },
    Effects = {
        Blast = "OnceInALifetime",
        Pulse = "Nucleus", -- (its light, trail and antler dust ride on the head bone: stagGlow)
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 214, 140),
        Amber = Color3.fromRGB(110, 190, 255),
        Orange = Color3.fromRGB(56, 120, 250),
        Sun = Color3.fromRGB(234, 246, 255),
        Ivory = Color3.fromRGB(226, 232, 246),
    },
    Animate = Animators.animateCometStag,
}

local function sandProfileBones()
    local bones = table.clone(SAND_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.SandPhantom = {
    Skinned = true,
    Bones = sandProfileBones(),
    Points = { "Tail6", "EarL", "EarR", "Hips" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "Mirage",
    },
    Colors = {
        Gold = Color3.fromRGB(226, 182, 110),
        Amber = Color3.fromRGB(246, 226, 180),
        Orange = Color3.fromRGB(176, 124, 70),
        Sun = Color3.fromRGB(255, 240, 210),
        Ivory = Color3.fromRGB(248, 238, 214),
    },
    Animate = Animators.animateSandPhantom,
}

PetRig.Profiles.SolarButterfly = {
    Skinned = true,
    Bones = {
        "Body", "Head", "Abd1", "Abd2", "Abd3", "AntL1", "AntL2", "AntR1", "AntR2",
        "ForeL1", "ForeL2", "HindL1", "HindL2", "ForeR1", "ForeR2", "HindR1", "HindR2",
    },
    Points = { "HindL2", "HindR2", "Head", "Body" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        ff8a1e = Color3.fromRGB(255, 138, 30), -- the sun-disc eyespots on its hindwings (saturated: Neon keeps the hue)
    },
    Effects = {
        Blast = "Afterglow",
        Pulse = "Eyespots",
        Light = "Eyespots",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 196, 80),
        Amber = Color3.fromRGB(250, 146, 38),
        Orange = Color3.fromRGB(226, 72, 36),
        Sun = Color3.fromRGB(255, 226, 150),
        Ivory = Color3.fromRGB(255, 240, 210),
    },
    Animate = Animators.animateSolarButterfly,
}

PetRig.Profiles.ObsidianGuardian = {
    Skinned = true,
    Bones = GUARD_BONES,
    Points = { "Head", "Hips", "Chest" },
    GlowColors = {
        ["9a50ff"] = GUARD_VIOLET, -- the slits of light that are its eyes (saturated: Neon keeps the hue)
    },
    Effects = {
        Blast = "HonestGlass",
        Pulse = "Eyes",
        Light = "Eyes",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(176, 110, 255),
        Amber = Color3.fromRGB(150, 80, 240),
        Orange = Color3.fromRGB(90, 50, 160),
        Sun = Color3.fromRGB(226, 206, 255),
        Ivory = Color3.fromRGB(240, 232, 255),
    },
    Animate = Animators.animateObsidianGuardian,
}

PetRig.Profiles.GlacierPuff = {
    Skinned = true,
    Bones = {
        "Body", "Head", "Jaw", "EyeL", "EyeR", "Tail1", "Tail2", "FinL", "FinR", "Dorsal", "Anal",
        "Puff1", "Puff2", "Puff3", "Puff4", "Puff5", "Puff6", "Puff7", "Puff8",
        "Spike1", "Spike2", "Spike3", "Spike4", "Spike5", "Spike6", "Spike7", "Spike8",
    },
    Points = { "Body", "Jaw", "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "HoarfrostBloom",
        Pulse = "Glints",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(190, 230, 255),
        Amber = Color3.fromRGB(150, 210, 250),
        Orange = Color3.fromRGB(80, 150, 220),
        Sun = Color3.fromRGB(236, 248, 255),
        Ivory = Color3.fromRGB(246, 252, 255),
    },
    Animate = Animators.animateGlacierPuff,
}

PetRig.Profiles.TimekeeperTortoise = {
    Skinned = true,
    Bones = {
        "Body", "Neck1", "Neck2", "Head", "Jaw", "LidUL", "LidLL", "LidUR", "LidLR", "BrowL", "BrowR", "Tail",
        "LegFL1", "LegFL2", "FootFL", "LegFR1", "LegFR2", "FootFR", "LegBL1", "LegBL2", "FootBL", "LegBR1", "LegBR2", "FootBR",
    },
    Points = { "Body", "Head" },
    GlowColors = {
        ffcf6e = TORT.GOLD, -- the line of gold light along its gnomon's edge
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "StoppedHour",
        Pulse = "Edge",
        Light = "Edge",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 214, 130),
        Amber = Color3.fromRGB(230, 200, 120),
        Orange = Color3.fromRGB(176, 124, 58),
        Sun = Color3.fromRGB(255, 245, 210),
        Ivory = Color3.fromRGB(250, 244, 226),
    },
    Animate = Animators.animateTimekeeperTortoise,
}

-- The five rigged in Studio (2026-11-12; animateBrute, animateWinged, animateDreamEater). No standing light or motes: the owner removed the
-- pets' auras; their glow pieces stay as part of their designs, and the special keeps its burst.
PetRig.Profiles.HeavenbreakerApe = {
    Joints = { Body = "Root", Head = "Body", ArmL = "Body", ArmR = "Body", Legs = "Body" },
    Sole = 1.531, -- template units from its middle to its feet
    Effects = { Pulse = "Body", Burst = "Body", Blast = "HeavenQuake", NovaLight = 2 },
    Colors = { Gold = Color3.fromRGB(255, 215, 110), Amber = Color3.fromRGB(150, 110, 40), Orange = Color3.fromRGB(255, 180, 60),
        Sun = Color3.fromRGB(255, 245, 210), Ivory = Color3.fromRGB(235, 245, 255) },
    Animate = Animators.animateBrute,
}
PetRig.Profiles.WorldrootColossus = {
    Joints = { Body = "Root", ArmL = "Body", ArmR = "Body", Legs = "Body" },
    Sole = 1.868,
    Effects = { Pulse = "Body", Burst = "Body", Blast = "Rootwake", NovaLight = 2 },
    Colors = { Gold = Color3.fromRGB(120, 255, 140), Amber = Color3.fromRGB(70, 45, 25), Orange = Color3.fromRGB(60, 200, 90),
        Sun = Color3.fromRGB(210, 255, 200), Ivory = Color3.fromRGB(240, 255, 235) },
    Animate = Animators.animateBrute,
}
PetRig.Profiles.PrismaticPhoenix = {
    Joints = { Body = "Root", Head = "Body", WingL = "Body", WingR = "Body", Tail = "Body" },
    Effects = { Pulse = "Body", Burst = "Body", Blast = "PrismBloom", NovaLight = 2.5 },
    Colors = { Gold = Color3.fromRGB(255, 200, 120), Amber = Color3.fromRGB(200, 80, 160), Orange = Color3.fromRGB(255, 120, 200),
        Sun = Color3.fromRGB(255, 250, 230), Ivory = Color3.fromRGB(255, 255, 255) },
    Animate = Animators.animateWinged,
}
PetRig.Profiles.EternalClockworkDragon = {
    Joints = { Body = "Root", Head = "Body", WingL = "Body", WingR = "Body", Tail = "Body" },
    Effects = { Pulse = "Body", Burst = "Body", Blast = "Clockstrike", NovaLight = 2.5 },
    Colors = { Gold = Color3.fromRGB(255, 210, 90), Amber = Color3.fromRGB(120, 90, 30), Orange = Color3.fromRGB(90, 190, 255),
        Sun = Color3.fromRGB(255, 245, 205), Ivory = Color3.fromRGB(230, 245, 255) },
    Animate = Animators.animateWinged,
}
PetRig.Profiles.ThousandYearDreamEater = {
    Joints = { Body = "Root", Head = "Body", Fins = "Body" },
    Effects = { Pulse = "Body", Burst = "Body", Blast = "SwallowedDream", NovaLight = 2 },
    Colors = { Gold = Color3.fromRGB(150, 175, 255), Amber = Color3.fromRGB(40, 30, 110), Orange = Color3.fromRGB(255, 130, 230),
        Sun = Color3.fromRGB(235, 235, 255), Ivory = Color3.fromRGB(250, 245, 255) },
    Animate = Animators.animateDreamEater,
}

-- The Exclusive Egg's beasts (the owner, 2026-11-13), skinned rigs since 2026-11-22 (Blender, tools/blender/pets): the Dreadwing's wings are chains with
-- fanning feathers, its neck and tail chains, its legs hang and trail; Crysalith walks on four solved legs over a four-bone spine, its antlers ring on
-- springs, its tail drags (DreadwingMotion, CrysalithMotion). Their eclipse and frost appear only in the specials (Blasts.DevourStars, Blasts.EternalFrost).
do
    local DreadwingMotion = require(script.Parent:WaitForChild("DreadwingMotion"))
    local CrysalithMotion = require(script.Parent:WaitForChild("CrysalithMotion"))
    PetRig.Profiles.EclipseDreadwing = {
        Skinned = true,
        Bones = DreadwingMotion.BONES,
        Points = DreadwingMotion.POINTS,
        Effects = { Pulse = "Body", Burst = "Body", Sparks = { "Head" }, Blast = "DevourStars", NovaLight = 2 },
        Colors = { Gold = Color3.fromRGB(190, 150, 255), Amber = Color3.fromRGB(40, 20, 70), Orange = Color3.fromRGB(150, 90, 255),
            Sun = Color3.fromRGB(240, 230, 255), Ivory = Color3.fromRGB(250, 245, 255) },
        Animate = DreadwingMotion.animate,
    }
    PetRig.Profiles.Crysalith = {
        Skinned = true,
        Bones = CrysalithMotion.BONES,
        Points = CrysalithMotion.POINTS,
        Effects = {
            Pulse = "Antlers", Light = "Antlers", Motes = "Body", Burst = "Body",
            Sparks = { "AntlerL2", "AntlerR2" }, Blast = "EternalFrost", NovaLight = 3,
        },
        LightScale = 0.5,
        SeeThroughGlow = { ["5fe3ff"] = 0.7 }, -- the frozen light over its antlers
        Colors = { Gold = Color3.fromRGB(150, 235, 255), Amber = Color3.fromRGB(40, 90, 140), Orange = Color3.fromRGB(90, 200, 255),
            Sun = Color3.fromRGB(235, 252, 255), Ivory = Color3.fromRGB(250, 255, 255) },
        Animate = CrysalithMotion.animate,
    }
end

PetRig.Profiles.GravityImp = {
    Skinned = true,
    Bones = {
        "Core", "Planet", "Pivot", "Hips", "Chest", "Head", "EarL", "EarR", "BrowL", "BrowR", "LidUL", "LidLL", "LidUR", "LidLR",
        "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR", "LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR",
        "Tail1", "Tail2", "Tail3", "Tail4", "Pebble1", "Pebble2", "Pebble3",
    },
    Points = { "Core", "Head" },
    GlowColors = {
        d28cff = IMP.VIOLET, -- the veins of gravity in its moonlet's cracks
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "WhichWayIsDown",
        Pulse = "Veins",
        NovaLight = 2, -- (its light hangs on its Core bone: animateGravityImp)
    },
    Colors = {
        Gold = IMP.VIOLET,
        Amber = Color3.fromRGB(186, 156, 220),
        Orange = IMP.DEEP,
        Sun = Color3.fromRGB(240, 210, 255),
        Ivory = Color3.fromRGB(246, 240, 255),
    },
    Animate = Animators.animateGravityImp,
}

PetRig.Profiles.GoldenManeLion = {
    Joints = {
        Body = "Root",
        Head = "Body",
        Jaw = "Head",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        Tail = "Body",
        Tail2 = "Tail",
    },
    GlowColors = {
        ffce61 = Color3.fromRGB(255, 140, 10),
        ffce59 = Color3.fromRGB(255, 150, 20),
    },
    Effects = {
        Motes = "Head",
        Light = "Body",
        Pulse = "Head",
        Burst = "Head",
        Sparks = { "LegFL_Paw", "LegFR_Paw", "Head_Crown" },
        Trail = "Tail2_Tuft",
        Blast = "SovereignRoar",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 180, 50),
        Amber = Color3.fromRGB(120, 60, 20),
        Orange = Color3.fromRGB(255, 120, 20),
        Sun = Color3.fromRGB(255, 225, 140),
        Ivory = Color3.fromRGB(255, 240, 210),
    },
    Animate = Animators.animateLion,
}

PetRig.NOVA_TIME = 2.6
local NOVA_BURST_AT = 0.42
PetRig.NOVA_BURST = NOVA_BURST_AT

PetRig.Profiles.WindSprite = {
    Skinned = true,
    Bones = {
        "Body", "Head", "Crest1", "Crest2", "EarL", "EarR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "BrowL", "BrowR", "CheekL", "CheekR",
        "Smile", "Blow", "ArmL1", "ArmL2", "ArmR1", "ArmR2", "WingL", "WingR", "WingMidL", "WingMidR", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "Tail7", "TailTip", "Tassel",
    },
    Points = { "TailTip", "WingTipL", "WingTipR", "Blow" },
    SkinTint = Color3.fromRGB(238, 250, 228), -- its pale maps run a little hot under the game's light
    GlowColors = {
        ["1eebb4"] = Color3.fromRGB(30, 235, 180),
        ["ffffff"] = Color3.fromRGB(165, 190, 190), -- catch-lights: full white blooms over the whole eye
    },
    Effects = {
        Motes = "Body", -- no Light: a light inside a body this pale washes all its shading out
        Pulse = "Channels",
        Burst = "Body",
        Sparks = { "WingTipL", "WingTipR" },
        Trail = "TailTip",
        TrailWidth = 0.07, -- a thread of wind off the tail's tip, not a plank
        TrailTaper = true,
        Blast = "TuggingGale",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(60, 235, 190),
        Amber = Color3.fromRGB(240, 110, 90),
        Orange = Color3.fromRGB(25, 190, 170),
        Sun = Color3.fromRGB(170, 255, 230),
        Ivory = Color3.fromRGB(235, 255, 250),
    },
    Animate = Animators.animateWindSprite,
}

PetRig.Profiles.StormhornKirin = {
    Skinned = true,
    SkinTint = Color3.fromRGB(250, 230, 198), -- the game's light pushes its slate to a royal blue: this brings the storm back (seen in Studio)
    Bones = {
        "Body", "Hips", "Chest", "Neck1", "Neck2", "Head", "Jaw", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR", "FrillL", "FrillR",
        "ManeA1", "ManeA2", "ManeB1", "ManeB2", "ManeC1", "ManeC2", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip",
        "LegFL1", "LegFL2", "LegFL3", "HoofFL", "LegFR1", "LegFR2", "LegFR3", "HoofFR", "LegBL1", "LegBL2", "LegBL3", "HoofBL", "LegBR1", "LegBR2", "LegBR3", "HoofBR",
    },
    Points = { "HoofFL", "HoofFR", "HoofBL", "HoofBR", "TailTip", "HornTip" },
    GlowColors = {
        ["4fb4ff"] = Color3.fromRGB(30, 125, 255),
        ["2a9dff"] = Color3.fromRGB(20, 110, 255),
        ["a8e0ff"] = Color3.fromRGB(120, 200, 255),
        ["f0ead8"] = Color3.fromRGB(170, 165, 150), -- the catch-light in its eye
    },
    Effects = {
        Pulse = "Horn",
        Burst = "Body",
        Sparks = { "HoofFL", "HoofFR", "HoofBL", "HoofBR" },
        Trail = "TailTip",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "ThunderAnswers",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(90, 170, 255),
        Amber = Color3.fromRGB(255, 190, 90),
        Orange = Color3.fromRGB(60, 110, 240),
        Sun = Color3.fromRGB(190, 230, 255),
        Ivory = Color3.fromRGB(235, 245, 255),
    },
    Animate = Animators.animateStormhornKirin,
}

PetRig.Profiles.GalaxyManta = {
    Skinned = true,
    Bones = {
        "Body", "Head", "EyeL", "EyeR", "Smile", "Mouth", "SpiralInner", "SpiralMid", "SpiralOuter", "Orbit",
        "HornL1", "HornL2", "HornL3", "HornR1", "HornR2", "HornR3",
        "WingL1", "WingL2", "WingL3", "WingL4", "WingR1", "WingR2", "WingR3", "WingR4",
        "WingRearL1", "WingRearL2", "WingRearL3", "WingRearL4", "WingRearR1", "WingRearR2", "WingRearR3", "WingRearR4",
        "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "Tail7", "Tail8", "TailTip",
    },
    Points = { "TailTip", "WingL4", "WingR4", "SpiralInner" },
    GlowColors = {
        ["8a6bff"] = Color3.fromRGB(104, 62, 255),
        ["ffc878"] = Color3.fromRGB(255, 118, 26), -- Neon shifts hard here: 255,92,16 reads orange, 255,142,44 lemon (seen in Studio)
        ["e6e0ff"] = Color3.fromRGB(176, 160, 255),
        ["d8d0f0"] = Color3.fromRGB(170, 165, 200), -- the catch-light in its eye: full white blooms over so small an eye
    },
    Effects = {
        Motes = "Body",
        Pulse = "Ember",
        Burst = "Body",
        Sparks = { "WingL4", "WingR4" },
        Trail = "TailTip",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "TurningOfTheHeavens",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(140, 100, 255),
        Amber = Color3.fromRGB(255, 180, 90),
        Orange = Color3.fromRGB(216, 72, 178),
        Sun = Color3.fromRGB(255, 214, 140),
        Ivory = Color3.fromRGB(235, 232, 255),
    },
    Animate = Animators.animateGalaxyManta,
}

function PetRig.isRigged(petId, template)
    local profile = PetRig.Profiles[petId]
    if not profile then
        return false
    end
    if profile.Skinned then
        return template:FindFirstChildWhichIsA("Bone", true) ~= nil
    end
    for name in profile.Joints do
        if template:FindFirstChild(petId .. "_Pivot_" .. name, true) then
            return true
        end
    end
    return false
end

local function prepare(part)
    part.Anchored = false
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Massless = true
end

local function weld(part0, part1)
    local constraint = Instance.new("WeldConstraint")
    constraint.Part0 = part0
    constraint.Part1 = part1
    constraint.Parent = part1
end

local function emitter(parent, properties)
    local particles = Instance.new("ParticleEmitter")
    particles.LightInfluence = 0
    particles.LightEmission = 1
    for property, value in properties do
        particles[property] = value
    end
    particles.Parent = parent
    return particles
end

local function attachmentAt(part, position, name)
    local attachment = Instance.new("Attachment")
    attachment.Name = name
    attachment.CFrame = part.CFrame:Inverse() * CFrame.new(position)
    attachment.Parent = part
    return attachment
end

local function addEffects(rig)
    local profile = rig.profile
    local effects, colors, u = profile.Effects, profile.Colors, rig.unit

    local motes = rig.parts[effects.Motes]
    if motes then
        emitter(motes, {
            Name = "Motes",
            Texture = SPARKLE,
            Rate = 6,
            Lifetime = NumberRange.new(1.6, 2.6),
            Speed = NumberRange.new(0.3, 0.8),
            SpreadAngle = Vector2.new(180, 180),
            Acceleration = Vector3.new(0, 0.6 * u, 0),
            Size = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0),
                NumberSequenceKeypoint.new(0.3, 0.13 * u),
                NumberSequenceKeypoint.new(1, 0),
            }),
            Color = ColorSequence.new(colors.Gold, colors.Orange),
            Transparency = NumberSequence.new(0.2, 1),
        })
    end

    for _, pointName in effects.Sparks or {} do
        local attachment = rig.points[pointName]
        if attachment then
            emitter(attachment, {
                Name = "Sparks",
                Texture = SPARKLE,
                Rate = 5,
                Lifetime = NumberRange.new(0.3, 0.6),
                Speed = NumberRange.new(0.6, 1.6),
                SpreadAngle = Vector2.new(60, 60),
                Size = NumberSequence.new(0.09 * u, 0),
                Color = ColorSequence.new(colors.Sun, colors.Gold),
            })
        end
    end

    local lightPart = rig.parts[effects.Light]
    if lightPart then
        local light = Instance.new("PointLight")
        light.Name = "PulseLight"
        light.Color = colors.Gold
        light.Range = 5 * u
        light.Brightness = 1.4
        light.Shadows = false
        light.Parent = lightPart
        rig.light = light
    end

    local burstPart = rig.parts[effects.Burst]
    if burstPart then
        rig.burst = emitter(attachmentAt(burstPart, burstPart.Position, "Burst"), {
            Name = "BurstParticles",
            Texture = SPARKLE,
            Enabled = false,
            Lifetime = NumberRange.new(0.6, 1.2),
            Speed = NumberRange.new(8 * u, 16 * u),
            Drag = 4,
            SpreadAngle = Vector2.new(180, 180),
            Size = NumberSequence.new(0.35 * u, 0),
            Color = ColorSequence.new(colors.Sun, colors.Orange),
        })
    end

    local trailPoints = if type(effects.Trail) == "table" then effects.Trail else { effects.Trail }
    for _, pointName in trailPoints do
        local tip = rig.points[pointName]
        if not tip then
            continue
        end
        local upper = Instance.new("Attachment")
        upper.Name = "TrailTop"
        upper.CFrame = tip.CFrame * CFrame.new(0, (effects.TrailWidth or 0.25) * u, 0)
        upper.Parent = tip.Parent
        local trail = Instance.new("Trail")
        trail.Name = "FlightTrail"
        trail.Attachment0 = tip
        trail.Attachment1 = upper
        trail.Lifetime = 0.45
        trail.LightEmission = 1
        trail.LightInfluence = 0
        trail.FaceCamera = true
        trail.Color = ColorSequence.new(colors.Sun, colors.Orange)
        trail.Transparency = NumberSequence.new(0.35, 1)
        if effects.TrailTaper then
            trail.WidthScale = NumberSequence.new(1, 0)
        end
        trail.Enabled = false
        trail.Parent = tip.Parent
        table.insert(rig.trails, trail)
    end
end

function PetRig.build(model, rootPart, template, petId, place, unit)
    local profile = PetRig.Profiles[petId]
    local prefix = petId .. "_"
    local rig = {
        petId = petId,
        profile = profile,
        model = model,
        rootPart = rootPart,
        unit = unit,
        parts = {},
        motors = {},
        sides = {},
        points = {},
        pointPositions = {},
        pulseGlow = {},
        trails = {},
        deltaTime = 0,
        state = { walk = 0, fly = 0, time = math.random() * 10 },
    }

    local pivots, glows = {}, {}
    for _, piece in template:GetDescendants() do
        if not piece:IsA("BasePart") or string.sub(piece.Name, 1, #prefix) ~= prefix then
            continue
        end
        local name = string.sub(piece.Name, #prefix + 1)
        local cframe, size = place(piece)
        local pivot = string.match(name, "^Pivot_(.+)$")
        local point = string.match(name, "^Point_(.+)$")
        if pivot then
            pivots[pivot] = cframe.Position
            continue
        elseif point then
            rig.pointPositions[point] = cframe.Position
            continue
        end

        local part = piece:Clone()
        for _, child in part:GetChildren() do
            if not child:IsA("SurfaceAppearance") then
                child:Destroy()
            end
        end
        part.Name = name
        part.Size = size
        part.CFrame = cframe
        local owner, hex = string.match(name, "^(.+)_Glow_(%x%x%x%x%x%x)$")
        part.Transparency = (hex and profile.SeeThroughGlow and profile.SeeThroughGlow[string.lower(hex)]) or 0
        prepare(part)
        if hex then
            part.Color = (profile.GlowColors and profile.GlowColors[string.lower(hex)]) or Color3.fromHex(hex)
            part.Material = Enum.Material.Neon
            if part:IsA("MeshPart") then
                part.TextureID = ""
            end
            table.insert(glows, { part = part, owner = owner })
        else
            part.Material = Enum.Material.SmoothPlastic
            rig.parts[name] = part
        end
        part.Parent = model
    end

    for _, glow in glows do
        if not rig.parts[glow.owner] then
            rig.parts[glow.owner] = glow.part
            glow.carrier = true
        end
    end

    local function partFor(name)
        return if name == "Root" then rootPart else rig.parts[name]
    end
    for name, parentName in profile.Joints do
        local part, parent, pivot = rig.parts[name], partFor(parentName), pivots[name]
        if part and parent and pivot then
            local motor = Instance.new("Motor6D")
            motor.Name = name
            motor.Part0 = parent
            motor.Part1 = part
            motor.C0 = parent.CFrame:Inverse() * CFrame.new(pivot)
            motor.C1 = part.CFrame:Inverse() * CFrame.new(pivot)
            motor.Parent = part
            rig.motors[name] = motor
            rig.sides[name] = if pivot.X > 0.01 then 1 elseif pivot.X < -0.01 then -1 else 0
        else
            warn(string.format("PetRig: %s is missing the part, parent or pivot for %s", petId, tostring(name)))
        end
    end
    local pulseName = profile.Effects.Pulse
    for _, glow in glows do
        local owner = rig.parts[glow.owner]
        if not glow.carrier then
            weld(owner, glow.part)
        end
        if glow.owner == pulseName then
            table.insert(rig.pulseGlow, { part = glow.part, color = glow.part.Color })
        end
    end
    for name, position in rig.pointPositions do
        local ownerName, label = string.match(name, "^([^_]+)_(.+)$")
        local owner = ownerName and rig.parts[ownerName]
        if owner then
            rig.points[name] = attachmentAt(owner, position, label)
        end
    end

    local controller = Instance.new("AnimationController")
    controller.Parent = model
    Instance.new("Animator").Parent = controller

    addEffects(rig)
    return rig
end

-- A pet that is one skin on a skeleton. Its joints are Bones; rig.motors holds a stand-in for each, so animations pose it exactly as they
-- pose a jointed pet: a pose in the pet's axes, turned into the bone's own (a bone may rest at any angle): rest:Inverse() * pose * rest.
-- rig.unit keeps effects the size they are on other pets; rig.meters is studs per metre as built, what its own poses are written in.
function PetRig.buildSkinned(model, rootPart, template, petId, turn, scale, length)
    local profile = PetRig.Profiles[petId]
    local prefix = petId .. "_"
    local rig = {
        petId = petId,
        profile = profile,
        model = model,
        rootPart = rootPart,
        unit = length / 3,
        meters = scale,
        parts = {},
        motors = {},
        sides = {},
        points = {},
        pointPositions = {},
        pulseGlow = {},
        trails = {},
        deltaTime = 0,
        state = { walk = 0, fly = 0, time = math.random() * 10 },
    }

    local skin = template:Clone()
    skin.Name = "Skin"
    local box = skin:GetBoundingBox()
    local bones = {}
    for _, d in skin:GetDescendants() do
        if d:IsA("Bone") then
            bones[d.Name] = d
            d.CFrame = d.CFrame.Rotation + d.CFrame.Position * scale
        elseif d:IsA("BasePart") then
            local from = d.CFrame
            d.Size *= scale
            d.CFrame = turn * (from.Rotation + (from.Position - box.Position) * scale)
            prepare(d)
            local name = if string.sub(d.Name, 1, #prefix) == prefix then string.sub(d.Name, #prefix + 1) else d.Name
            local owner, hex = string.match(name, "^(.+)_Glow_(%x%x%x%x%x%x)$")
            if hex then
                d.Color = (profile.GlowColors and profile.GlowColors[string.lower(hex)]) or Color3.fromHex(hex)
                d.Material = Enum.Material.Neon
                if d:IsA("MeshPart") then
                    d.TextureID = ""
                end
                local seeThrough = profile.SeeThroughGlow and profile.SeeThroughGlow[string.lower(hex)]
                if seeThrough then
                    d.Transparency = seeThrough
                end
                rig.parts[owner] = d
                if owner == profile.Effects.Pulse then
                    table.insert(rig.pulseGlow, { part = d, color = d.Color })
                end
            elseif d.Name == "RootPart" then
                d.Transparency = 1 -- the importer's holder of the bones
            else
                d.Material = Enum.Material.SmoothPlastic
                rig.parts[name] = d
                if profile.SeeThrough and profile.SeeThrough[name] then
                    d.Transparency = profile.SeeThrough[name]
                end
                local look = d:FindFirstChildOfClass("SurfaceAppearance")
                if look and profile.SkinTint then
                    look.Color = profile.SkinTint
                end
            end
            -- a Weld, not a WeldConstraint: its offset is fixed now, so the root can be placed before the model is in the world
            local joint = Instance.new("Weld")
            joint.Part0 = rootPart
            joint.Part1 = d
            joint.C0 = rootPart.CFrame:ToObjectSpace(d.CFrame)
            joint.Parent = d
        end
    end
    -- Each mesh needs a Motor6D from the part that holds the bones, as the importer made them: without one the skin stays in its bind pose,
    -- whatever the bones do (seen in Studio, 2026-11-05).
    local holder = bones.Root and bones.Root.Parent
    for _, d in skin:GetChildren() do
        if d:IsA("MeshPart") and holder then
            local motor = Instance.new("Motor6D")
            motor.Name = d.Name .. "Motor6D"
            motor.Part0 = holder
            motor.Part1 = d
            motor.C0 = holder.CFrame:ToObjectSpace(d.CFrame)
            motor.Parent = d
        end
    end
    for _, child in skin:GetChildren() do
        child.Parent = model
    end
    skin:Destroy()

    local function worldOf(bone)
        local cframe = bone.CFrame
        local up = bone.Parent
        while up:IsA("Bone") do
            cframe = up.CFrame * cframe
            up = up.Parent
        end
        return up.CFrame * cframe
    end
    -- where every bone rests, in the pet's own frame (metres' worth of studs: its rotation is the model's, its place the bone's head): what a solved
    -- animation (PetMotion) measures its legs and spine from; and the ground-finder it shares
    rig.restCF = {}
    for name, bone in bones do
        rig.restCF[name] = worldOf(bone)
    end
    rig.dropToGround = dropToGround
    for _, name in profile.Bones do
        local bone = bones[name]
        if bone then
            local rest = worldOf(bone).Rotation
            local restInverse = rest:Inverse()
            rig.motors[name] = setmetatable({}, {
                __newindex = function(_, _, cframe)
                    bone.Transform = restInverse * cframe * rest
                end,
            })
        else
            warn("PetRig: " .. petId .. " has no bone " .. name)
            rig.motors[name] = {} -- poses of a missing bone land nowhere
        end
    end
    for _, name in profile.Points do
        rig.points[name] = bones[name]
    end

    addEffects(rig)
    return rig
end

K.emitter = emitter
local blastPieces = require(script:WaitForChild("Blasts"))(K)
local Blasts = blastPieces.Blasts
local blastWarned = blastPieces.blastWarned
local guardOwnerCharacter = blastPieces.guardOwnerCharacter
local leopardGroundAt = blastPieces.leopardGroundAt
local function burst(rig)
    local profile = rig.profile
    local folder = Instance.new("Folder")
    folder.Name = "PetSpecial"
    folder.Parent = rig.model.Parent or workspace

    local fx = {
        origin = (rig.parts[profile.Effects.Burst] or rig.rootPart).Position,
        facing = rig.rootPart.CFrame - rig.rootPart.Position,
        neon = function(size, cframe, color)
            local part = Instance.new("Part")
            part.Anchored = true
            part.CanCollide = false
            part.CanTouch = false
            part.CanQuery = false
            part.CastShadow = false
            part.Material = Enum.Material.Neon
            part.Color = color
            part.Size = size
            part.CFrame = cframe
            part.Parent = folder
            return part
        end,
    }
    Debris:AddItem(folder, 2) -- the longest blast (Sacred Grove's branches) has faded by 1.75 s. (Set first: a blast that throws
    -- must not leave its parts in the world, release audit 2026-11-12)
    local ok, err = pcall(Blasts[profile.Effects.Blast], rig, fx)
    if not ok and not blastWarned[rig.petId] then
        blastWarned[rig.petId] = true
        warn("PetRig: " .. tostring(rig.petId) .. "'s special failed: " .. tostring(err))
    end
    if PetRig.PetSounds.special(rig.petId) and rig.rootPart:IsDescendantOf(workspace) then -- (never from a portrait)
        PetRig.Sfx.play(PetRig.PetSounds.special(rig.petId), rig.rootPart)
    end
end

-- Pets' special moves (the Blasts below, and each animate function's special pose) are switched OFF for now (the owner,
-- 2026-11-16: "temporarily remove all special moves and abilities from every pet ... We may reintroduce special moves in
-- the future"). Everything stays in place: set this back to true to bring them all back (the cultivating and rank-up
-- specials, PetCompanionController, and the Codex's "WATCH IT", CodexController and SpecialPreview).
PetRig.SPECIALS_ENABLED = false

function PetRig.nova(rig)
    if not PetRig.SPECIALS_ENABLED then
        return
    end
    if rig.nova == nil then
        rig.nova = { start = rig.state.time, fired = false }
    end
end

function PetRig.update(rig, deltaTime, state)
    local s = rig.state
    s.time += deltaTime
    rig.deltaTime = deltaTime
    local blend = math.min(1, deltaTime * 5)
    local walkTarget = if state.flying then 0 else math.clamp(state.speed / (4 * rig.unit), 0, 1)
    s.walk += (walkTarget - s.walk) * blend
    s.fly += ((if state.flying then 1 else 0) - s.fly) * blend

    local nova = 0
    if rig.nova then
        local progress = (s.time - rig.nova.start) / PetRig.NOVA_TIME
        nova = smoothstep(0, 0.3, progress) * (1 - smoothstep(0.75, 1, progress))
        if not rig.nova.fired and progress >= NOVA_BURST_AT then
            rig.nova.fired = true
            burst(rig)
        end
        if progress >= 1 then
            rig.nova = nil
        end
    end

    rig.profile.Animate(rig, s, s.walk, s.fly, nova)

    -- on a phone, another player's pet gives up its point lights (a phone pays for every dynamic light; a pet makes some
    -- of its lights as it first animates, so they are looked for now and then)
    if PetRig.Quality.Low and rig.owner and rig.owner ~= Players.LocalPlayer and s.time >= (s.nextLightSweep or 0) then
        s.nextLightSweep = s.time + 2
        for _, d in rig.model:GetDescendants() do
            if d:IsA("PointLight") or d:IsA("SpotLight") then
                d.Enabled = false
            end
        end
    end

    -- a big pet's lights scale with it, but none reaches past PetRig.LIGHT_REACH (a Giant Dawn Phoenix's reached 50 studs and
    -- washed the ground round its owner in its colour); its lights made as it animates are caught here, now and then
    if (rig.model:GetAttribute("SizeScale") or 1) > 1 and s.time >= (s.nextReachSweep or 0) then
        s.nextReachSweep = s.time + 2
        for _, d in rig.model:GetDescendants() do
            if d:IsA("Light") and d.Range > PetRig.LIGHT_REACH then
                d.Range = PetRig.LIGHT_REACH
            end
        end
    end

    -- now and then, its voice (in the world only: never from a portrait; never over its special)
    local every = PetRig.VOICE_EVERY
    s.nextVoice = s.nextVoice or s.time + every[1] * math.random()
    if s.time >= s.nextVoice then
        s.nextVoice = s.time + every[1] + math.random() * (every[2] - every[1])
        local voice = PetRig.PetSounds.voice(rig.petId)
        if voice and not rig.nova and not rig.quiet and rig.rootPart:IsDescendantOf(workspace) then -- (rig.quiet: a pen's beast far off)
            PetRig.Sfx.play(voice, rig.rootPart)
        end
    end

    local pulse = 0.5 + 0.5 * math.sin(s.time * 2.2)
    if rig.light then
        rig.light.Brightness = (1.1 + 0.8 * pulse) * (rig.profile.LightScale or 1) + (rig.profile.Effects.NovaLight or 9) * nova
    end
    for _, glow in rig.pulseGlow do
        glow.part.Color = glow.color:Lerp(Color3.new(1, 1, 1), 0.2 * pulse + 0.7 * nova)
    end

    for _, trail in rig.trails do
        trail.Enabled = s.fly > 0.5
    end
end

K.Blasts = Blasts
K.guardOwnerCharacter = guardOwnerCharacter
K.leopardGroundAt = leopardGroundAt
for _, name in { "CrystalBeetle", "ThunderclawDrake", "FrostfangSerpent", "StormBumblebee", "GoldenKirin", "AquaWisp", "EmberWyrm", "LunarHopper", "VoltFox", "AstralWhale", "OriginSerpent", "AzureSkyDragon", "BonefireDragon", "EchoBat", "QiClockworkFinch", "NineTailMoonfox", "MoonfangTiger", "LotusElephant", "NinefoldSpiritSerpent", "SpiritCrane", "DawnPhoenix" } do
    require(script:WaitForChild("Pets"):WaitForChild(name))(K)
end

return PetRig

-- Realm6WingsConfig: every value behind the Realm 6 (Immortal) wings. The runtime (Realm6Wings) holds no look of its own.
--
-- The owner's brief (2026-11-10, a fresh start): "Massive feather wings: Feather-texture ParticleEmitters + carefully
-- designed Beams". The design doc's Realm 6 theme: layered halos and luminous energy wings, gold.
--
-- How it's built: each wing is an arm of three bones (Humerus, Forearm, Hand: invisible anchored parts moved every frame).
-- Every feather is one Beam lying in the wing's surface (FaceCamera off: a Beam lays its width along its attachments' Y
-- axis and bends along their X axis, measured in Studio 2026-11-10), its texture a feather painted from scratch
-- (tools/vfx/realm6_wing_textures.py). The coverts sit still on their bone; only the flight feathers move each frame (the
-- ripple). Two particle roles: light streaming off the outer primaries' tips, and now and then a feather drifting off.
--
-- Units: studs at character scale 1 (times Scale), degrees, seconds. A wing's own axes: u out along the wing, v up, n its
-- back (dorsal) side, which faces away from the character's front.
return {
    Scale = 0.85, -- of the wing as laid out below: about 19 studs tip to tip on a 5-stud character

    -- where the wings grow: the first of these parts the character has, and the offset from it (x right, y up, z behind)
    Mount = {
        Parts = { "UpperTorso", "Torso", "HumanoidRootPart" },
        -- z 0.78: behind the halos (Realm6Halos' rings sit 0.66-0.72 behind the head), so from in front they show over the roots
        Offset = { UpperTorso = { 0, 0.35, 0.78 }, Torso = { 0, 0.5, 0.78 }, HumanoidRootPart = { 0, 1.4, 0.78 } },
        ShoulderX = 0.3, -- each wing's root, out from the spine
    },

    -- the arm: bone lengths, and the joint angles (degrees in the wing's surface; Sweep swings a wing back about the vertical)
    Arm = { Humerus = 1.9, Forearm = 2.6, Hand = 1.5 },
    Pose = {
        Spread = { Shoulder = 55, Elbow = -25, Wrist = 15, Sweep = 16 },
        Folded = { Shoulder = -25, Elbow = -95, Wrist = -50, Sweep = 78 },
        FoldFan = 0.22, -- folded, each feather's angle off its bone shrinks to this share: the fan closes along the arm
    },

    -- the cupped surface: roots drift to the back side the farther out along the arm they are; flight tips curl back
    Cup = 0.45, -- studs at the wing's hand end (grows with the square of the distance out)

    -- the feathers, row by row. Bone: which bone they grow from; From/To: where along it (0 its start, 1 its end), first
    -- to last; Angle: off the bone's direction, first to last (negative: down and back toward the trailing edge);
    -- Length (first, last) or Lengths (each); Offset: toward the leading edge (kept tiny: a root ahead of the arm line
    -- shows its bare quill above the wing's edge, a comb of spikes); Layer: toward the back side (+) or the front
    -- (-); Width: the beam's width (the painted feather fills about two thirds of it); Twist: about its own shaft,
    -- first to last (the surface isn't flat from the side); Bend: the shaft's curve; Curl: the tip's lean to the back side,
    -- per stud of length. Flight rows move with the ripple; Emit names the particle roles on their tips.
    Rows = {
        {
            Name = "Primary", Bone = "Hand", Count = 10, From = 0.0, To = 1.0, Angle = { -112, -28 },
            Lengths = { 4.3, 4.5, 4.7, 4.9, 5.2, 5.5, 5.8, 6.1, 6.3, 6.0 },
            Offset = 0, Layer = 0, Width = 2.3, Twist = { 2, 14 }, Bend = 5, Curl = 0.05,
            Textures = { "PrimaryA", "PrimaryB" }, Look = "Flight", Flight = true,
            Emit = { TipLight = { 6, 7, 8, 9, 10 }, Shed = { 2, 4 } },
        },
        {
            Name = "Secondary", Bone = "Forearm", Count = 12, From = 1.0, To = 0.08, Angle = { -108, -120 },
            Length = { 4.1, 3.5 }, Offset = 0, Layer = 0.012, Width = 1.95, Twist = { 1, -2 }, Bend = 3, Curl = 0.04,
            Textures = { "Secondary" }, Look = "Flight", Flight = true,
            Emit = { Shed = { 2, 5, 8, 11 } },
        },
        {
            Name = "Tertial", Bone = "Humerus", Count = 3, From = 0.85, To = 0.3, Angle = { -152, -158 },
            Length = { 3.2, 2.4 }, Offset = 0, Layer = 0.024, Width = 1.85, Twist = { -2, -4 }, Bend = 2, Curl = 0.03,
            Textures = { "Secondary" }, Look = "Flight", Flight = true,
        },
        -- the coverts, over the flight feathers' bases on the back side
        {
            Name = "PrimaryCovert", Bone = "Hand", Count = 7, From = 0.05, To = 0.85, Angle = { -108, -30 },
            Length = { 1.7, 1.9 }, Offset = 0.02, Layer = 0.07, Width = 1.25, Twist = { 2, 8 }, Bend = 2, Curl = 0.03,
            Textures = { "Covert" }, Look = "Covert",
        },
        {
            Name = "GreaterCovert", Bone = "Forearm", Count = 11, From = 0.97, To = 0.06, Angle = { -105, -117 },
            Length = { 1.7, 1.5 }, Offset = 0.02, Layer = 0.07, Width = 1.3, Twist = { 0, 0 }, Bend = 2, Curl = 0.03,
            Textures = { "Covert" }, Look = "Covert",
        },
        {
            Name = "Scapular", Bone = "Humerus", Count = 5, From = 0.95, To = 0.15, Angle = { -146, -154 },
            Length = { 1.5, 1.2 }, Offset = 0.02, Layer = 0.09, Width = 1.25, Twist = { 0, 0 }, Bend = 2, Curl = 0.03,
            Textures = { "Covert" }, Look = "Covert",
        },
        {
            Name = "MedianCovert", Bone = "Forearm", Count = 8, From = 0.95, To = 0.05, Angle = { -98, -108 },
            Length = { 1.0, 0.95 }, Offset = 0.04, Layer = 0.12, Width = 1.0, Twist = { 0, 0 }, Bend = 1, Curl = 0.02,
            Textures = { "Covert" }, Look = "Covert",
        },
        {
            Name = "HumeralCovert", Bone = "Humerus", Count = 4, From = 0.9, To = 0.2, Angle = { -138, -146 },
            Length = { 0.95, 0.9 }, Offset = 0.04, Layer = 0.13, Width = 1.0, Twist = { 0, 0 }, Bend = 1, Curl = 0.02,
            Textures = { "Covert" }, Look = "Covert",
        },
        -- the under-wing coverts, on the front side (seen from in front of the character)
        {
            Name = "UnderCovert", Bone = "Forearm", Count = 9, From = 0.95, To = 0.05, Angle = { -108, -118 },
            Length = { 1.6, 1.5 }, Offset = 0.02, Layer = -0.07, Width = 1.3, Twist = { 0, 0 }, Bend = 2, Curl = -0.02,
            Textures = { "Covert" }, Look = "Covert", LowQuality = false,
        },
        {
            Name = "UnderHand", Bone = "Hand", Count = 5, From = 0.05, To = 0.7, Angle = { -108, -45 },
            Length = { 1.8, 1.8 }, Offset = 0.02, Layer = -0.07, Width = 1.25, Twist = { 0, 4 }, Bend = 2, Curl = -0.02,
            Textures = { "Covert" }, Look = "Covert", LowQuality = false,
        },
    },
    Jitter = { Length = 0.04, Angle = 1.5, Width = 0.06, Seed = 6 }, -- no two feathers alike (the same on every character)

    Textures = {
        PrimaryA = "rbxassetid://85123639778669",
        PrimaryB = "rbxassetid://107892795054714",
        Secondary = "rbxassetid://91220961182753",
        Covert = "rbxassetid://73618501060967",
        ShedFeather = "rbxassetid://137470230727726",
        LightPlume = "rbxassetid://90566324908199",
    },

    -- how the feather textures sit on their beams (set from Studio: which end the quill is at, which side each vane)
    QuillAtAttachment0 = false, -- seen in Play: the texture's bottom (the quill) lands at Attachment1
    FlipVane = false,

    -- the looks: colour from root to tip (Beam.Color runs Attachment0 -> Attachment1), light
    Looks = {
        Flight = {
            Color = { { 0, Color3.fromRGB(226, 160, 66) }, { 0.35, Color3.fromRGB(250, 226, 186) }, { 0.78, Color3.fromRGB(252, 240, 222) }, { 1, Color3.fromRGB(248, 200, 112) } },
            Transparency = 0.04, LightEmission = 0.05, LightInfluence = 0.75, Brightness = 1, Segments = 8,
        },
        Covert = {
            Color = { { 0, Color3.fromRGB(228, 164, 72) }, { 0.55, Color3.fromRGB(248, 222, 176) }, { 1, Color3.fromRGB(252, 234, 204) } },
            Transparency = 0.04, LightEmission = 0.03, LightInfluence = 0.75, Brightness = 1, Segments = 4,
        },
    },

    Unfold = { Time = 1.8, Overshoot = 1.15 }, -- opening (ease-out-back), on show
    Fade = { In = 0.8, Out = 0.9 }, -- seconds (In shorter than the unfold, so the folded wings are seen swinging out); destroy() folds and fades over Out
    Breath = { Period = 4.6, Shoulder = 5, Elbow = 4, Wrist = 3, Sweep = 4, Fan = 0.05 }, -- degrees, a slow beat out along the arm
    Ripple = { Degrees = 1.3, Speed = 2.2, Waves = 2.4 }, -- across the flight feathers, root to tip (Waves: radians across the arm)

    -- the two particle roles, fired by script (a Rate near 1 is dropped by automatic quality)
    Particles = {
        TipLight = {
            Interval = { 0.1, 0.18 }, -- per wing: one plume from a random outer primary's tip
            Texture = "LightPlume", Lifetime = { 1.1, 1.8 }, Speed = { 0.2, 0.5 }, Spread = 180, Acceleration = { 0, 0.35, 0 },
            Drag = 1.2, Rotation = { -30, 30 }, RotSpeed = { -20, 20 },
            Size = { { 0, 0.3 }, { 0.3, 0.8 }, { 1, 0.2 } }, Transparency = { { 0, 1 }, { 0.2, 0.55 }, { 1, 1 } },
            Color = { { 0, Color3.fromRGB(255, 196, 100) }, { 1, Color3.fromRGB(255, 226, 160) } },
            LightEmission = 0.5, LightInfluence = 0, Brightness = 0.7, ZOffset = 0.15,
        },
        Shed = {
            Interval = { 1.6, 3.2 }, -- per wing: now and then one feather loosens from a flight feather's tip
            Texture = "ShedFeather", Lifetime = { 4.5, 6.5 }, Speed = { 0.1, 0.3 }, Spread = 180, Acceleration = { 0, -0.7, 0 },
            Drag = 0.6, Rotation = { 0, 360 }, RotSpeed = { -45, 45 },
            Size = { { 0, 0.9 }, { 1, 0.9 } }, Transparency = { { 0, 1 }, { 0.08, 0.1 }, { 0.8, 0.2 }, { 1, 1 } },
            Color = { { 0, Color3.fromRGB(255, 240, 215) }, { 1, Color3.fromRGB(255, 240, 215) } },
            LightEmission = 0.1, LightInfluence = 0.8, Brightness = 1, ZOffset = 0,
        },
    },

    Performance = {
        CullDistance = 140, -- studs from the camera past which other players' wings hide and stop
        LowQualityCullDistance = 70,
        HalfRateDistance = 50, -- other players' flight feathers move every other frame past this
        LowQualityTipLight = 0.5, -- share of the tip light on a phone
    },
}

-- RealmAura: every player's realm aura, the owner's design (built and reviewed in the Studio test
-- range, AuraTestRange, kept in ServerStorage.DevStage; drag it to Workspace to use it. It runs this same module: a realm enhanced there is the realm
-- the game shows). Worn only while the player meditates (AuraController).
--
-- Each realm (1-12, AuraConfig's palettes) has its own layers; its sub-rank (1-5) moves it along one
-- continuous level, t = (realm - 1 + progress) / 11, progress = (sub - 1) / 5: Peak (0.8) sits just
-- short of the next realm's base, so a breakthrough never looks weaker. Every size, rate and speed
-- follows t (rates capped at 60 per emitter for mobile); the layers a realm adds are the visible jump.
--   Every realm: the owner's base aura (baseAura: the ground burst, smoke and slashes, the rising
--   wisp and sparkles, the body glow; bigger with the level) and body aura (bodyAura), in the realm's
--   own colours (AuraConfig's Palette, no two alike).
--   Realms 1-4: their own builds (realm1 .. realm4).
--   From Ascendant (5): the breathing outline and light; ribbon arcs (one at Ascendant, two from
--   Immortal).
--   Cosmic, Void and Eternal: a dark void core inside a bright rim (in place of the body glow).
--   From Heavenly Dao (10): a third ribbon; Heavenly Dao's streaks of law, Eternal's nebula.
--   Only particles, beams and trails (and the outline and light): no magic circles and no solid
--   pieces (the owner, 2026-11-11), so the only parts are invisible emitter hosts.
--
-- RealmAura.build(root, realm, sub) returns the aura's folder (ActiveAuraFX, under the root);
-- destroying it removes everything the aura made, on the root and the body parts too. The module
-- animates every aura itself, and switches off other players' auras farther than CULL_DISTANCE_LIVE from
-- the camera (Roblox draws at most 31 Highlights per client).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

local RealmAura = {}

local LOW = Quality.Low
local RATE_SCALE = if LOW then 0.5 else 1 -- every emitter's rate, on a phone
local CULL_DISTANCE_LIVE = if LOW then 60 else 120 -- studs from the camera
local CULL_CHECK = 0.25        -- seconds between distance checks
local CULLED_CLASSES = { "ParticleEmitter", "Beam", "Trail", "Highlight", "Light", "BillboardGui" }

local building = nil -- the record of the aura being built (bodyAura dresses parts that arrive later)

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local AuraConfig = require(ReplicatedStorage:WaitForChild("AuraConfig"))

local TEX = {
    Glow = "rbxassetid://135169457468310",
    SoftGlow = "rbxassetid://243664672",        -- a soft round glow (PDS kit): Realm 4's orb core and rim
    Swoosh = "rbxassetid://98818011129942",     -- the owner's pick: an 8x8 flipbook of a thin glowing stroke whipping a full circle
    Ring = "rbxassetid://130173906719836",
    LawStreak = "rbxassetid://75983337371298",
    Nebula = "rbxassetid://128568519603570",
    -- Realm 1, from the PDS' Particles & Models Kit (Workspace)
    Mote = "rbxassetid://16512006463",         -- one tiny core with a faint halo (Sparkles&Debris)
    QiThread = "rbxassetid://11829306338",     -- one soft waving thread (Beams)
    Wisp = "rbxassetid://7216854921",          -- a faint soft smoke wisp (Fogs)
    -- Realm 2, from the PDS kit
    Spark = "rbxassetid://16511998441",         -- a small dot with a faint cross flare (Sparkles&Debris)
    -- Realm 3, from the PDS kit (Rings)
    EnergyRing = "rbxassetid://12403112662",    -- a thin glowing ring with brighter arcs
    SwirlRing = "rbxassetid://6250126210",      -- a thin ring of wispy strokes
    -- our own (tools/vfx/mist_ribbon_textures.py)
    MistRibbon = "rbxassetid://106430686548190", -- smoke streaming along its length, no edge anywhere
    MistHaze = "rbxassetid://139629863109215",   -- a wider, fainter veil under it
    -- the owner's Realm 4 layout, textures from the PDS kit (Shines)
    SoulWisp = "rbxassetid://14590122278",       -- a small soft spiral wisp (Wisps)
    -- the owner's own body aura (built by the owner on the AuraWorkbench dummy, approved 2026-11-03)
    BodySmoke = "rbxassetid://17332831347",     -- an 8x8 flipbook of rolling smoke
    BodySpark = "rbxassetid://9997556038",      -- a small round spark
    BodyStar = "rbxassetid://12363796862",      -- a four-point star glint
    -- the owner's vortex ripple for Realm 4 (their picks, Creator Store)
    VortexRings = "rbxassetid://18281460865",   -- a 4x4 flipbook: a glinting ring forms and breaks up (realkilometers)
    VortexCloud = "rbxassetid://12683695494",   -- an 8x8 flipbook: a small rolling smoke cloud (Isathyst)
    -- Realm 4's smoke orbs (the owner's design): their star and lightning, smoke from the PDS kit (Fogs)
    OrbStar = "rbxassetid://84556863870846",      -- our own short cross flare (tools/vfx/soul_orb_textures.py)
    SmokePuff = "rbxassetid://80021798595720",    -- our own 4x4 flipbook: a puff billows, tears and dissolves
                                                  -- (inside 78% of each frame: a clear margin, so no cell edges show)
    ElectricRing = "rbxassetid://6900421398",     -- a crackling electric ring (PDS Rings)
    BoltBurst = "rbxassetid://7216850580",        -- a small burst of lightning (PDS Fogs)
    SmokeRipple = "rbxassetid://133636855384267", -- our own ripple of smoke strands, zero at its border (tools/vfx/soul_orb_textures.py;
                                                  -- the PDS ring 12878479033's faint border showed as a square at 19 studs)
    -- the owner's base aura, every realm (their picks on Workspace.AuraDummies.AuraDummy_1, 2026-11-11)
    BaseBurst = "rbxassetid://13455668887",       -- a 4x4 flipbook burst, lying flat on the ground
    BaseSmoke = "rbxassetid://113821949376919",   -- the ground smoke spreading out (light over dark)
    BaseSlash = "rbxassetid://127353288690632",   -- a slash turning on the ground
    BaseCrescent = "rbxassetid://13367229656",    -- a spiny crescent turning on the ground
    BaseWisp = "rbxassetid://12191903502",        -- the wisp rising from the feet (a Beam)
    BaseGlint = "rbxassetid://12386384198",       -- a thin upright glint (the rising sparkles)
}
local VOID_CORE = { [8] = true, [9] = true, [12] = true }
local MAX_RATE = if LOW then 30 else 60

local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end

local function lastColor(colors)
    return colors.Keypoints[#colors.Keypoints].Value
end

local function emitter(parent, props)
    local e = Instance.new("ParticleEmitter")
    for k, v in props do
        e[k] = v
    end
    e.Rate *= RATE_SCALE
    e.Parent = parent
    return e
end

local spinners = {}

-- The meditation poses move the body, not the root (PoseController sets the root joint's Transform):
-- from Ascendant on the body floats 1 to 2.5 studs up, upside down at Cosmic. What sits on the body
-- (the glow, the outline's light, the void core, the realm's unique piece) follows the hips'
-- shift from where it rests; what lies on the floor doesn't. lifted() marks a root attachment to
-- follow it, while an aura is being built.
local function lifted(attachment)
    if building then
        table.insert(building.lifted, { attachment, attachment.Position })
    end
end

-- the body's resting place in the root's space: the hips, which the pose's root joint moves (the
-- upper torso won't do: Cosmic's pose turns the body upside down round the hips and brings it back
-- down beside the root). Players' rigs join with AnimationConstraints, the test dummies with Motor6Ds
-- (R6: the root's RootJoint). nil when neither is there
local function restingBody(character)
    local lower = character:FindFirstChild("LowerTorso")
    local joint = lower and lower:FindFirstChild("Root")
    if not joint then
        lower = character:FindFirstChild("Torso")
        local hrp = character:FindFirstChild("HumanoidRootPart")
        joint = hrp and hrp:FindFirstChild("RootJoint")
    end
    if lower and joint and joint:IsA("Motor6D") then
        return lower, (joint.C0 * joint.C1:Inverse()).Position
    end
    if lower and joint and joint:IsA("AnimationConstraint") and joint.Attachment0 and joint.Attachment1 then
        return lower, (joint.Attachment0.CFrame * joint.Attachment1.CFrame:Inverse()).Position
    end
    return nil, nil
end

-- an invisible part for a ring-shaped emitter (from an attachment an emitter emits from a point). It
-- follows the root (a player may shift a few studs while cultivating, QiService.STILL_RADIUS);
-- grounded: the "ground" spinner moves it instead, on the floor under the feet.
local function host(fx, root, r, h, y, grounded)
    local part = Instance.new("Part")
    part.Name = "EmitterHost"
    part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch = true, false, false, false
    part.Transparency = 1
    part.Size = Vector3.new(r * 2, h, r * 2)
    part.CFrame = root.CFrame * CFrame.new(0, y, 0)
    part.Parent = fx
    if not grounded then
        table.insert(spinners, { kind = "follow", part = part, root = root, offset = CFrame.new(0, y, 0), speed = 0, angle = 0 })
    end
    return part
end


-- mist ribbons revolving round the body (the owner's brief: "smooth, no edge, not flat, mist or
-- smoke, long length"). Each is a Trail behind a point racing round its own tilted circle and
-- weaving up and down; the ribbons run opposite each other. Each has a mist core standing upright
-- and a wider, fainter haze lying flat across it: crossed, so from any angle one of them is broad
-- (never flat), thinning to the tail. Not FaceCamera: where a camera-facing trail runs straight at
-- the camera its width has no direction, and the pieces fan out into spikes.
local function mistRibbons(root, fx, main, count, speed, alpha)
    for i = 1, count do
        local layers = {}
        for _, L in { { tex = TEX.MistHaze, hw = 1, flat = true, head = math.min(0.95, alpha + 0.3), tail = math.min(0.97, alpha + 0.42) },
                      { tex = TEX.MistRibbon, hw = 0.65, flat = false, head = alpha, tail = alpha + 0.15 } } do
            local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
            a0.Name, a1.Name = "MistA", "MistB"
            a0.Parent, a1.Parent = root, root
            local trail = Instance.new("Trail")
            trail.Attachment0, trail.Attachment1 = a0, a1
            trail.Texture = L.tex
            trail.TextureMode = Enum.TextureMode.Stretch
            trail.Color = ColorSequence.new(main)
            trail.LightEmission = 0.35
            trail.LightInfluence = 0
            trail.FaceCamera = false
            trail.Lifetime = 1.6
            trail.MinLength = 0.05
            -- the head tapers in from a point and fades in, so no end is ever a straight cut
            trail.Transparency = seq({ { 0, 1 }, { 0.22, L.head }, { 0.6, L.tail }, { 1, 1 } })
            trail.WidthScale = seq({ { 0, 0.15 }, { 0.2, 1 }, { 1, 0.35 } })
            trail.Parent = fx
            table.insert(layers, { a0 = a0, a1 = a1, hw = L.hw, flat = L.flat })
        end
        table.insert(spinners, { kind = "mist", layers = layers, root = root, speed = speed, angle = (i - 1) * math.tau / count,
            tilt = if i % 2 == 1 then 0.35 else -0.35, radius = 2.8, clock = i * 1.7 })
    end
end

-- Realm 1, Qi Awakening: the first breath of Qi. Motes revolve round the body the full 360 degrees
-- on two rings turning opposite ways; a faint mist rises off the shoulders; from Qi Adept, arcs of
-- Qi circle the body; a faint outline, a fainter fill and a soft PointLight breathe together.
-- Nothing gathers on the body's middle (the owner's calls). Each sub-rank adds more.
-- every realm's body glow (the owner's must-haves): a faint outline round the whole body with a
-- fainter fill, and a soft PointLight on the body and the ground; all breathe together (4 s in,
-- 4 s out)
local function bodyGlow(root, fx, main, line, fill, glow, range)
    if LOW and building and not building.isLocal then
        return -- on a phone only your own aura has these: a Highlight is costly, and there's a limit of 31
    end
    local centre = Instance.new("Attachment")
    centre.Name = "AuraCentre"
    centre.Parent = root
    lifted(centre)
    local outline = Instance.new("Highlight")
    outline.Adornee = root.Parent
    outline.FillColor = main
    outline.OutlineColor = main
    outline.DepthMode = Enum.HighlightDepthMode.Occluded
    outline.Parent = fx
    local light = Instance.new("PointLight")
    light.Color = main
    light.Range = range
    light.Shadows = false
    light.Parent = centre
    table.insert(spinners, { kind = "outline", highlight = outline, light = light, root = root, speed = 0, angle = 0, clock = 0,
        line = line, fill = fill, glow = glow })
end

-- arcs of Qi circling the body (each end's axis is the circle's tangent, so the beam's curve
-- follows the circle)
local function qiArcs(root, tint, count, alpha, speedK)
    for i = 1, count do
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Name, a1.Name = "ThreadA", "ThreadB"
        a0.Parent, a1.Parent = root, root
        local span, radius = 1.9, 3
        local curve = 4 / 3 * math.tan(span / 4) * radius
        local beam = Instance.new("Beam")
        beam.Attachment0, beam.Attachment1 = a0, a1
        beam.Texture = TEX.QiThread
        beam.TextureMode = Enum.TextureMode.Stretch
        beam.TextureSpeed = 0.6
        beam.Color = tint
        beam.LightEmission = 1
        beam.Transparency = seq({ { 0, 1 }, { 0.3, alpha }, { 0.7, alpha }, { 1, 1 } })
        beam.Width0, beam.Width1 = 1.2, 1.2
        beam.CurveSize0, beam.CurveSize1 = curve, curve
        beam.Segments = 20
        beam.FaceCamera = true
        beam.Parent = root
        table.insert(spinners, { kind = "arc", a0 = a0, a1 = a1, root = root, speed = (0.7 + 0.2 * i) * speedK * (if i % 2 == 0 then -1 else 1),
            angle = i * math.tau / 3, span = span, radius = radius, height = ({ 0.8, -0.8, 1.9 })[i], tilt = ({ 0.2, -0.25, 0.35 })[i] })
    end
end

-- Realm 1, Qi Awakening: the first breath of Qi. Motes revolve round the body the full 360 degrees
-- on two rings turning opposite ways; a faint mist rises off the shoulders; from Qi Adept, arcs of
-- Qi circle the body. Nothing gathers on the body's middle, and nothing is too bright (the owner's
-- calls). Each sub-rank adds more.
local function realm1(root, fx, tint, p)
    local main = lastColor(tint)
    for i, ring in { { r = 2.7, rate = 12 + 10 * p, turn = 0.9 + 0.4 * p, y = -0.3 }, { r = 2.1, rate = 6 + 6 * p, turn = -(0.6 + 0.3 * p), y = 0.4 } } do
        local part = host(fx, root, ring.r, 5, ring.y)
        emitter(part, { Texture = TEX.Mote, Color = tint, LightEmission = 0.6, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0 }, { 0.2, 3.4 }, { 0.8, 2.8 }, { 1, 0 } }),
            Transparency = seq({ { 0, 1 }, { 0.2, 0.3 }, { 0.8, 0.45 }, { 1, 1 } }), Lifetime = NumberRange.new(3, 4),
            Rate = ring.rate, Speed = NumberRange.new(0), Acceleration = Vector3.new(0, 0.35, 0) })
        table.insert(spinners, { kind = "mesh", part = part, root = root, offset = Vector3.new(0, ring.y, 0), speed = ring.turn,
            angle = i * 1.3 })
    end
    qiArcs(root, tint, if p >= 0.8 then 3 elseif p >= 0.6 then 2 else 0, 0.35, 1)
    emitter(host(fx, root, 1.1, 0.3, 1.5), { Texture = TEX.Wisp, Color = ColorSequence.new(main:Lerp(Color3.new(1, 1, 1), 0.4)),
        LightEmission = 0.4, EmissionDirection = Enum.NormalId.Top, Size = seq({ { 0, 1.6 }, { 1, 3.2 } }),
        Transparency = seq({ { 0, 1 }, { 0.35, 0.2 - 0.1 * p }, { 1, 1 } }), Lifetime = NumberRange.new(2.2, 3),
        Rate = 1.2 + 0.8 * p, Speed = NumberRange.new(0.5, 0.9), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-12, 12) })
    bodyGlow(root, fx, main, 0.55 - 0.25 * p, 0.92 - 0.08 * p, 0.6 + 0.5 * p, 9 + 3 * p)
end

-- Realm 2, Qi Foundation: the foundation is laid, and Qi now circulates in steady orbits. Two
-- tilted rings of small energy sparks circle the body, turning opposite ways (the signature);
-- Realm 1's arcs keep turning, quicker. Every value starts a step above Realm 1's Peak. (Its rising
-- stars gave way to the base aura's sparkles, 2026-11-11.)
local function realm2(root, fx, tint, p)
    local main = lastColor(tint)
    for i, o in { { r = 2.7, y = 0.3, tilt = 0.35, turn = 2.2 }, { r = 2.4, y = -0.7, tilt = -0.45, turn = -1.8 } } do
        local ring = host(fx, root, o.r, 0.15, o.y)
        emitter(ring, { Texture = TEX.Spark, Color = tint, LightEmission = 0.4, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0 }, { 0.25, 1.6 + 0.4 * p }, { 1, 0 } }), Transparency = seq({ { 0, 1 }, { 0.25, 0.45 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.6), Rate = 18 + 10 * p, Speed = NumberRange.new(0) })
        table.insert(spinners, { kind = "orbit", part = ring, root = root, offset = Vector3.new(0, o.y, 0), tilt = o.tilt,
            speed = o.turn * (1 + 0.3 * p), angle = i * 1.7 })
    end
    qiArcs(root, tint, 3, 0.3 - 0.05 * p, 1.3 + 0.3 * p)
    bodyGlow(root, fx, main, 0.3 - 0.12 * p, 0.85 - 0.06 * p, 1.05 + 0.4 * p, 12 + 2 * p)
end
-- Realm 3, Spirit Core: the Qi condenses into a core, and its orbits close into rings. Rings swirl
-- round the body like a gyroscope, each at its own tilt, turning while the tilt swings round (a
-- third from sub-rank 4). Each ring is an invisible part: Realm 2's sparks ride its edge, and from
-- two of our own mist ribbons revolve round the body (they replaced the owner's borrowed crescent
-- flipbook at their request for our own asset). Every value starts a step above Realm 2's Peak (the
-- sparks are fewer: they ride the rings now, and the owner wants particles sparse). Its colour is
-- the realm's gold (the owner's set of 2026-11-11, which replaced the jade), and its rising stars
-- gave way to the base aura's sparkles.
local function realm3(root, fx, tint, p)
    local main = lastColor(tint)
    local rings = {
        { r = 2.9, y = 0.2, tilt = 0.5, turn = 0.5, spin = 1.6, tex = TEX.EnergyRing },
        { r = 3.2, y = -0.3, tilt = -0.62, turn = -0.4, spin = -1.2, tex = TEX.SwirlRing },
        { r = 2.6, y = 0.6, tilt = 0.25, turn = 0.7, spin = 2.1, tex = TEX.EnergyRing },
    }
    for i = 1, if p >= 0.6 then 3 else 2 do
        local o = rings[i]
        local ring = Instance.new("Part")
        ring.Name = "EnergyRing"
        ring.Anchored, ring.CanCollide, ring.CanQuery, ring.CanTouch = true, false, false, false
        ring.CastShadow = false
        ring.Transparency = 1
        ring.Size = Vector3.new(o.r * 2, 0.05, o.r * 2)
        ring.CFrame = root.CFrame * CFrame.new(0, o.y, 0)
        emitter(ring, { Texture = TEX.Spark, Color = tint, LightEmission = 0.4, LockedToPart = true,
            Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
            Size = seq({ { 0, 0 }, { 0.25, 2 + 0.3 * p }, { 1, 0 } }), Transparency = seq({ { 0, 1 }, { 0.25, 0.4 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.6), Rate = 14 + 8 * p, Speed = NumberRange.new(0) })
        ring.Parent = fx
        table.insert(spinners, { kind = "gyro", part = ring, root = root, offset = Vector3.new(0, o.y, 0), tilt = o.tilt,
            speed = o.turn * (1 + 0.3 * p), angle = i * 2.1, spin = 0, spinSpeed = o.spin * (1 + 0.3 * p) })
    end
    mistRibbons(root, fx, main, 2, 2.5 + 0.5 * p, 0.5 - 0.05 * p)
    bodyGlow(root, fx, main, 0.2 - 0.08 * p, 0.88 - 0.03 * p, 1.4 + 0.3 * p, 14 + 2 * p) -- gold fills strongly: kept light
end

-- The owner's own body aura (designed on workspace.AuraWorkbench, approved 2026-11-03: "now that's
-- perfect"), added over the whole body of every realm, on top of the realm's own layers (the owner:
-- "Apply that as default to all aura"): a smoke of the realm's colour over a black smoke, sparks of
-- both, a few star glints. The smoke follows the level (the owner: "Weaker qi fainter smoke, Higher
-- Qi bigger smoke"): faint and small at the first realm, exactly the approved look at Realm 4's
-- middle sub-rank (t = 0.31), denser and larger towards Eternal. Every body part emits (a Box volume emits through the part). An R6 part's
-- rate is split across its R15 pieces by height, so an R15 body is as dense as an R6 one (one rate
-- per piece made it 2.5x too much). The emitters sit on the body parts, outside fx, so they go when
-- fx goes.
local BODY_SHARE = {
    Head = 1, UpperTorso = 0.81, LowerTorso = 0.19,
    LeftUpperArm = 0.46, LeftLowerArm = 0.42, LeftHand = 0.12,
    RightUpperArm = 0.46, RightLowerArm = 0.42, RightHand = 0.12,
    LeftUpperLeg = 0.46, LeftLowerLeg = 0.44, LeftFoot = 0.10,
    RightUpperLeg = 0.46, RightLowerLeg = 0.44, RightFoot = 0.10,
    Torso = 1, ["Left Arm"] = 1, ["Right Arm"] = 1, ["Left Leg"] = 1, ["Right Leg"] = 1,
}

-- a at the first realm (t = 0), b at Realm 4's middle sub-rank (the approved look), c at t = 1
-- on a phone: the fewest parts that still surround the whole body, and a share of the rate
local LOW_BODY_PARTS = { Head = true, UpperTorso = true, LeftUpperArm = true, RightUpperArm = true, LeftUpperLeg = true, RightUpperLeg = true,
    Torso = true, ["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true }
local LOW_BODY_RATE = 0.4

local function byLevel(t, a, b, c)
    if t <= 0.31 then
        return a + (b - a) * t / 0.31
    end
    return b + (c - b) * math.min(1, (t - 0.31) / 0.69)
end

-- smoke: the coloured smoke's LightEmission and Brightness (default 1 and 3, the approved look).
-- The realms pass dummy 1's 0.4 and 2 (2026-11-11): against a bright sky,
-- smoke that only adds light washes to white.
local function bodyAura(root, fx, color, t, smokeLook)
    local glow = if typeof(color) == "ColorSequence" then color else ColorSequence.new(color)
    local black = ColorSequence.new(Color3.new(0, 0, 0))
    local spread = byLevel(t, 45, 60, 75)
    local smokeLight = smokeLook and smokeLook.LightEmission or 1
    local smokeBrightness = smokeLook and smokeLook.Brightness or 3
    local function smoke(c, light, peak, z)
        return { Texture = TEX.BodySmoke, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8,
            FlipbookFramerate = NumberRange.new(10, 40), FlipbookStartRandom = true, Color = c,
            LightEmission = if light > 0 then smokeLight else 0,
            Brightness = if light > 0 then smokeBrightness else 3, LightInfluence = 0, Size = seq({ { 0, byLevel(t, 0.9, 1.2, 1.8) }, { 1, byLevel(t, 2.4, 4, 6.5) } }),
            Transparency = seq({ { 0, peak + (1 - peak) * 0.97 }, { 0.2, peak }, { 1, 1 } }),
            Lifetime = NumberRange.new(byLevel(t, 0.5, 0.6, 0.8), byLevel(t, 0.9, 1.1, 1.4)),
            Speed = NumberRange.new(byLevel(t, 1, 1.5, 2.5), byLevel(t, 3, 4.5, 6.5)), SpreadAngle = Vector2.new(spread, spread), Drag = 2.5,
            Rotation = NumberRange.new(-360, 360), Orientation = Enum.ParticleOrientation.VelocityParallel, ZOffset = z }
    end
    local function spark(c, light)
        return { Texture = TEX.BodySpark, Color = c, LightEmission = light, Brightness = 3, LightInfluence = 0,
            Size = seq({ { 0, 0 }, { 0.05, 0.5 }, { 1, 0 } }), Transparency = NumberSequence.new(0),
            Lifetime = NumberRange.new(0.4, 0.9), Speed = NumberRange.new(2, 9), SpreadAngle = Vector2.new(90, 90), Drag = 2.5,
            Rotation = NumberRange.new(-360, 360), Orientation = Enum.ParticleOrientation.VelocityParallel }
    end
    local layers = {
        { "BodySmoke", 25, smoke(glow, 1, byLevel(t, 0.62, 0.3, 0.15), -1) },
        { "BodyShadow", 5, smoke(black, 0, byLevel(t, 0.78, 0.5, 0.4), -1.5) },          -- the dark core under the colour
        { "BodySpark", 12, spark(glow, 1) },
        { "BodyAsh", 12, spark(black, 0) },
        -- a glint that flashes three or four times in its short life
        { "BodyStar", 3, { Texture = TEX.BodyStar, Color = glow, LightEmission = 1, Brightness = 3, LightInfluence = 0,
            Size = seq({ { 0, 0 }, { 0.04, 0.3 }, { 0.099, 0.313 }, { 0.118, 2.2 }, { 0.131, 0.25 }, { 0.245, 0.188 }, { 0.263, 1.6 },
                { 0.284, 0.188 }, { 0.493, 0.125 }, { 0.508, 1.37 }, { 0.526, 0.063 }, { 0.705, 0.063 }, { 0.723, 1 }, { 0.739, 0.063 }, { 1, 0 } }),
            Transparency = NumberSequence.new(0), Lifetime = NumberRange.new(0.1, 0.5), Speed = NumberRange.new(0, 9),
            SpreadAngle = Vector2.new(360, 360), Drag = 2.5, Rotation = NumberRange.new(45), ZOffset = 1 } },
    }
    local made = {}
    local record = building                -- the aura being built: its culling also covers parts dressed later
    local function dress(part)
        local share = BODY_SHARE[part.Name]
        if not share or not part:IsA("BasePart") or part:FindFirstChild("BodySmoke") or (LOW and not LOW_BODY_PARTS[part.Name]) then
            return
        end
        for _, layer in layers do
            if LOW and layer[1] == "BodyAsh" then
                continue
            end
            local e = emitter(part, layer[3])
            e.Name = layer[1]
            e.Rate = math.floor(layer[2] * share * 10 + 0.5) / 10 * (if LOW then LOW_BODY_RATE else 1)
            table.insert(made, e)
            if record then
                table.insert(record.items, e)
                e.Enabled = not record.culled
            end
        end
    end
    local model = root.Parent
    for _, part in model:GetChildren() do
        dress(part)
    end
    -- with streaming on, a far body part can reach the client after the build, or stream out and
    -- come back as a new part: dress it when it arrives
    local arrived = model.ChildAdded:Connect(dress)
    local function undress()
        arrived:Disconnect()
        for _, e in made do
            e:Destroy()
        end
    end
    if record then
        table.insert(record.cleanups, undress)
    end
    fx.Destroying:Connect(undress)
    return undress
end

-- Realm 4, Spirit Soul: the owner's design (2026-11-03). Three spheres of black smoke revolve
-- round the character in a fixed triangle (a third of a circle apart on one tilted path, 4.2
-- studs out), rising and dipping together. The smoke is locked inside each sphere, so it holds
-- its shape. Its star stays still at the centre of the smoke, riding with the sphere; a crackling
-- electric ring (PDS) hugs the cloud's edge, with bursts flashing from the rim. Star and lightning
-- are on a billboard, so they draw over the smoke (the owner: "the lightning should be the edge
-- of the cloud, not the cloud overlapping it"). Spiral wisps rise round the body; nothing sits
-- on its middle. On the ground (its Soul Seal circle was removed, 2026-11-11): the owner's vortex ripple, a smoke
-- ripple and a rolling mist, all quickening while the player meditates.
local function realm4(root, fx, tint, p)
    local main = lastColor(tint)
    local black = ColorSequence.new(Color3.fromRGB(18, 10, 28))
    local GAP = math.tau / 3                           -- a triangle: a third of a circle apart
    local balls = {}
    for i = 1, 3 do
        -- a small invisible part that the spinner moves, its X axis along the path (the links' beams
        -- curve along it); everything on it rides with it
        local ball = Instance.new("Part")
        ball.Name = "SmokeOrb"
        ball.Anchored, ball.CanCollide, ball.CanQuery, ball.CanTouch = true, false, false, false
        ball.Transparency = 1
        ball.Size = Vector3.new(0.2, 0.2, 0.2)
        ball.CFrame = root.CFrame
        ball.Parent = fx
        local orb = Instance.new("Attachment")
        orb.Parent = ball
        -- the sphere holds its shape (the owner, 2026-11-11: "The dark sphere in tier 4 is breaking"):
        -- a solid soft dark core, and the rolling smoke round it fading out before its flipbook's
        -- tearing frames, so no shred ever leaves the ball
        emitter(orb, { Name = "OrbCore", Texture = TEX.SoftGlow, Color = black, LightEmission = 0, LightInfluence = 0,
            LockedToPart = true, ZOffset = -1.4, Size = NumberSequence.new(2.7 + 0.12 * p), Transparency = NumberSequence.new(0.02),
            Lifetime = NumberRange.new(0.8, 1), Rate = 8, Speed = NumberRange.new(0), Rotation = NumberRange.new(0, 360) })
        emitter(orb, { Name = "OrbSmoke", Texture = TEX.SmokePuff, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
            FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = black, LightEmission = 0, LightInfluence = 0, LockedToPart = true, ZOffset = -1.5,
            Size = NumberSequence.new(2.95 + 0.13 * p),
            Transparency = seq({ { 0, 0.6 }, { 0.1, 0.15 }, { 0.4, 0.2 }, { 0.6, 1 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1.2, 1.6), Rate = 12 + 2 * p, Speed = NumberRange.new(0), SpreadAngle = Vector2.new(0, 0),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40) })
        -- the star and the lightning: billboard images on the sphere (a billboard draws over the smoke,
        -- which hid them as particles, and still hides behind the body). The lightning plays its 16
        -- frames through a clipping window; the star turns slowly
        local gui = Instance.new("BillboardGui")
        gui.Name = "OrbCore"
        gui.Adornee = ball
        gui.Size = UDim2.fromScale(2.6 + 0.2 * p, 2.6 + 0.2 * p)
        gui.LightInfluence = 0
        gui.Brightness = 2.4
        gui.MaxDistance = 250
        -- no offset toward the camera: seen from an angle it slid the ring and star off the ball (the
        -- owner: "the particles are off"); the smoke is pushed back by its ZOffset, so they still draw over it
        gui.Parent = ball
        -- the glow is a rim behind the ball (drawn over it, it washed the black out)
        emitter(orb, { Name = "OrbGlow", Texture = TEX.SoftGlow, Color = tint, LightEmission = 1, LightInfluence = 0, LockedToPart = true, ZOffset = -2.2,
            Size = NumberSequence.new(4.2 + 0.25 * p), Transparency = seq({ { 0, 1 }, { 0.3, 0.6 }, { 0.7, 0.62 }, { 1, 1 } }),
            Lifetime = NumberRange.new(1, 1.4), Rate = 5, Speed = NumberRange.new(0), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-20, 20) })
        -- the lightning (the owner: "a ring or better lightning"): a crackling electric ring hugging the
        -- cloud's edge, a fainter one turning the other way, and bursts flashing out from the rim
        local function image(id, size, z)
            local img = Instance.new("ImageLabel")
            img.BackgroundTransparency = 1
            img.AnchorPoint = Vector2.new(0.5, 0.5)
            img.Position = UDim2.fromScale(0.5, 0.5)
            img.Size = UDim2.fromScale(size, size)
            img.Image = id
            img.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.55)
            img.ZIndex = z
            img.Parent = gui
            return img
        end
        local ringA = image(TEX.ElectricRing, 0.88, 1)
        local ringB = image(TEX.ElectricRing, 0.78, 1)
        ringB.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.2)
        local spark = image(TEX.BoltBurst, 0.42, 1)
        spark.Visible = false
        local star = Instance.new("ImageLabel")
        star.BackgroundTransparency = 1
        star.AnchorPoint = Vector2.new(0.5, 0.5)
        star.Position = UDim2.fromScale(0.5, 0.5)
        star.Size = UDim2.fromScale(1, 1)
        star.ZIndex = 3
        star.ImageTransparency = 0.5                  -- softer (the owner: "increase the light transparency of the star")

        star.Image = TEX.OrbStar
        star.ImageColor3 = main:Lerp(Color3.new(1, 1, 1), 0.85)
        star.ZIndex = 2
        star.Parent = gui
        table.insert(balls, orb)
        table.insert(spinners, { kind = "orb", ball = ball, ringA = ringA, ringB = ringB, spark = spark, boltClock = 0,
            sparkAt = math.random() * 0.5, star = star, root = root, speed = 1.4 + 0.3 * p,
            angle = -(i - 1) * GAP, tilt = 0.3, radius = 4.2, height = 0.4, clock = 0 })
    end
    -- two ground smokes rippling out past where the seal lay (9.6 studs across; the owner: "2 different type of smoke in the
    -- ground, bigger than the circle, like a ripple"):
    -- 1. the ripple: a wispy ring of smoke lying flat, expanding from 6 to ~19 studs as it fades
    local rippleHost = host(fx, root, 0.1, 0.1, -2.85, true)
    local ripple = emitter(rippleHost, { Name = "SmokeRipple", Texture = TEX.SmokeRipple,
        Color = ColorSequence.new(Color3.fromRGB(150, 95, 230)), LightEmission = 0.45, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        -- (the owner: "twice the size of the ground ring": it had reached 2.7 times)
        -- (the owner: "trim the smoke similar to the distance of vortex": out to 7.5, not 14.2)
        Size = seq({ { 0, 2 }, { 1, 7.5 } }), Transparency = seq({ { 0, 1 }, { 0.12, 0.3 }, { 0.6, 0.55 }, { 1, 1 } }),
        Lifetime = NumberRange.new(1.6, 1.9), Rate = 1.8 + 0.4 * p, Speed = NumberRange.new(0.01),  -- the owner: more, faster
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-12, 12) })
    -- 2. the rolling mist: billowy torn puffs born round the old seal's rim, lying flat just above the
    -- ground and swelling outward as they turn and fade. Flat, because a camera-facing puff this
    -- low dips into the floor, which cuts it with a hard straight line (Roblox has no soft particles)
    local mistHost = Instance.new("Part")
    mistHost.Name = "EmitterHost"
    mistHost.Anchored, mistHost.CanCollide, mistHost.CanQuery, mistHost.CanTouch = true, false, false, false
    mistHost.Transparency = 1
    mistHost.Size = Vector3.new(4.6, 0.1, 4.6)               -- trimmed to the vortex (it was 9.4)
    mistHost.CFrame = root.CFrame * CFrame.new(0, -2.88, 0)
    mistHost.Parent = fx
    local mist = emitter(mistHost, { Name = "GroundSmoke", Texture = TEX.SmokePuff,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        Color = ColorSequence.new(Color3.fromRGB(115, 75, 180)), LightEmission = 0.2, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume, ShapePartial = 0.6,
        Size = seq({ { 0, 2 }, { 1, 4.2 } }), Transparency = seq({ { 0, 1 }, { 0.15, 0.1 }, { 0.7, 0.35 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2.4, 3), Rate = 10 + 2 * p, Speed = NumberRange.new(0.02),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30) })
    -- 3. the owner's vortex ripple (their idea, built on the AuraWorkbench, 2026-11-03): glinting
    -- rings swirling out from the feet over a dark cloud. On the ripple host, so it follows the floor.
    -- The rings grow fast and slow down as they pass the old seal's rim, turn one way, and fade in and
    -- out (they had popped off); the cloud lies just under them, a dark ground for them
    local vortexAt = Instance.new("Attachment")
    vortexAt.Name = "Vortex"
    vortexAt.Parent = rippleHost
    local cloudAt = Instance.new("Attachment")
    cloudAt.Name = "VortexCloud"
    cloudAt.Position = Vector3.new(0, -0.13, 0)              -- 0.02 above the floor
    cloudAt.Parent = rippleHost
    local vortex = emitter(vortexAt, { Name = "VortexRings", Texture = TEX.VortexRings,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        -- Brightness 5 (the owner's 10 burned the thin rings white; 2 lost them on the old seal)
        Color = ColorSequence.new(main), LightEmission = 1, Brightness = 5, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.01), SpreadAngle = Vector2.new(0, 0),
        -- the owner's own timing, which reads as a ripple: each ring grows steadily from the centre
        -- and stays whole until its flipbook breaks it up (eased, faded rings read as loose arcs).
        -- Smaller and denser than their first (the owner: "it spread too wide, reduce it, increase
        -- the rate"): out to 7 studs, not 10
        Size = seq({ { 0, 0 }, { 1, 7 } }), Transparency = seq({ { 0, 0 }, { 0.85, 0 }, { 1, 1 } }),
        Lifetime = NumberRange.new(0.8, 3), Rate = 22 + 4 * p, Rotation = NumberRange.new(-360, 360), RotSpeed = NumberRange.new(5),
        ZOffset = 0.2 })
    emitter(cloudAt, { Name = "VortexCloud", Texture = TEX.VortexCloud,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        Color = ColorSequence.new(main:Lerp(Color3.new(0, 0, 0), 0.72)), LightEmission = 0, LightInfluence = 0,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top,
        Speed = NumberRange.new(0.01), SpreadAngle = Vector2.new(0, 0),
        Size = NumberSequence.new(12), Transparency = seq({ { 0, 1 }, { 0.15, 0.2 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2.5, 4), Rate = 2.5, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(10),
        ZOffset = -0.5 })
    -- the ground pieces (the mist, the ripples) follow the floor under the feet, so they sit
    -- on slopes and steps. (The ground wind that raced out across the floor was removed at the
    -- owner's word, 2026-11-03: "REMOVE THE GROUND WIND".)
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = { root.Parent, fx }
    table.insert(spinners, { kind = "ground", root = root, fx = fx, rayParams = rayParams,
        grounded = { { mistHost, 0.08, false }, { rippleHost, 0.15, false } },
        rayClock = 0, speed = 0, angle = 0 })
    -- the ground smoke follows meditation (the owner): calm as it starts, the ripple quickening and the
    -- mist rushing out while the player cultivates (the player's IsCultivating; a test dummy's own
    -- attribute), easing between the two
    table.insert(spinners, { kind = "meditate", root = root, model = root.Parent, ripple = ripple, mist = mist, vortex = vortex, k = -1,
        p = p, speed = 0, angle = 0 })
    -- the spiral wisps from the owner's first layout, rising round the body (from a ring, not the middle)
    emitter(host(fx, root, 2, 0.2, -1), { Name = "Wisps", Texture = TEX.SoulWisp, Color = tint, Rate = 12 + 6 * p,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, EmissionDirection = Enum.NormalId.Top,
        Lifetime = NumberRange.new(1, 1.8), Size = seq({ { 0, 0.5 }, { 1, 1.2 } }), Speed = NumberRange.new(3, 6), LightEmission = 0.6,
        Transparency = seq({ { 0, 0.3 }, { 1, 1 } }), SpreadAngle = Vector2.new(20, 20), Drag = 1.2,
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120) })
    bodyGlow(root, fx, main, 0.13 - 0.05 * p, 0.86 - 0.03 * p, 1.65 + 0.3 * p, 16 + 2 * p)
end

-- The owner's base aura, on every realm under the realm's own pieces (built by the owner on
-- Workspace.AuraDummies.AuraDummy_1, 2026-11-11: "apply that aura to all realms", "change the color
-- depending on realm, Don't repeat same color to aura", "The higher the realm, the bigger the
-- effects"). The dummy wore it in Ascendant's orange, so its values are Realm 5's base; sizes, reach
-- and rates follow the level from there.
--   On the ground: a burst, a smoke spreading out, a slash and a crescent turning; each but the
--   burst a light layer over a black copy of itself (the owner's pairs: the copy at ZOffset -0.001,
--   two thirds the rate, half as opaque; fully opaque black was "way too intense").
--   A wisp (Beam) rising from the feet past the head, narrowing to a point.
--   Sparkles rising from a ring round the feet to above the head.
--   A soft glow over the body, in front of it (behind, the body hides it); none round a void core.
-- The light layers run Hot to Main to Deep (the realm's Palette) at Brightness 4 scaled by its Glow:
-- the owner's pale orange at 10 burned to white, and the smoke kept Main to its edge (ending in Deep,
-- its outward spread disappeared).
local BASE_FLOOR = -2.95 -- the floor under the root

local function halfOpacity(points)
    local out = {}
    for _, point in points do
        table.insert(out, { point[1], 1 - (1 - point[2]) * 0.5 })
    end
    return seq(out)
end

local function baseAura(root, fx, palette, t, voidCore)
    local k = 0.6 + 1.1 * t                 -- size and reach: 0.6 at the first realm, 1 at Ascendant's base, 1.8 at Eternal's Peak
    local n = 0.7 + 0.8 * t                 -- the sparkles' rate: 0.7 to 1.55
    -- Every ground layer is born on one point, so all of them cover the centre: their count grows
    -- little (0.8 to 1.12) and they dim as they grow, or a high realm's core burns white (seen on
    -- Eternal at the sparkles' rate, 2026-11-11)
    local nGround = 0.8 + 0.3 * t
    local dim = 1 / (0.6 + 0.4 * k)
    local bright = palette.Glow or 1
    local hot, main, deep = palette.Hot, palette.Main, palette.Deep
    local fire = ColorSequence.new({ ColorSequenceKeypoint.new(0, hot), ColorSequenceKeypoint.new(0.4, main),
        ColorSequenceKeypoint.new(1, deep) })
    local black = ColorSequence.new(Color3.new(0, 0, 0))
    local function rate(base)
        return math.min(MAX_RATE, base * n)
    end
    local function groundRate(base)
        return math.min(MAX_RATE, base * nGround)
    end

    -- the ground layers: flat on the floor (VelocityPerpendicular, rising at a near-zero speed),
    -- spinning where they were born. Rates and brightness are given at Ascendant's base
    local ground = Instance.new("Attachment")
    ground.Name = "BaseGround"
    ground.Position = Vector3.new(0, BASE_FLOOR + 0.42, 0)
    ground.Parent = root
    local function layer(name, props, darkRate)
        props.Name = name
        props.LightEmission, props.LightInfluence = 1, 0
        props.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
        props.EmissionDirection = Enum.NormalId.Top
        props.Rotation = NumberRange.new(-360, 360)
        props.Rate = groundRate(props.Rate)
        props.Brightness *= bright * dim
        local points = props.Transparency
        props.Transparency = seq(points)
        emitter(ground, props)
        if darkRate then
            local dark = table.clone(props)
            dark.Name = name .. "Dark"
            dark.Color, dark.LightEmission = black, 0
            dark.Transparency = halfOpacity(points)
            dark.Rate = groundRate(darkRate)
            dark.ZOffset = -0.001
            emitter(ground, dark)
        end
    end
    layer("BaseBurst", { Texture = TEX.BaseBurst, Color = fire, Brightness = 4,
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        Size = seq({ { 0, 1 * k }, { 1, 10 * k } }), Transparency = { { 0, 0 }, { 1, 1 } },
        Lifetime = NumberRange.new(0.8, 1.8), Speed = NumberRange.new(0.001), SpreadAngle = Vector2.new(3, 3), Rate = 7 })
    layer("BaseSmoke", { Texture = TEX.BaseSmoke, Color = ColorSequence.new(hot, main), Brightness = 7,
        Size = seq({ { 0, 1 * k }, { 1, 10 * k } }), Transparency = { { 0, 0 }, { 1, 1 } },
        Lifetime = NumberRange.new(0.5, 1), Speed = NumberRange.new(0.001), SpreadAngle = Vector2.new(2, 2), Rate = 15 }, 10)
    layer("BaseSlash", { Texture = TEX.BaseSlash, Color = fire, Brightness = 4,
        Size = seq({ { 0, 5 * k }, { 1, 10 * k } }), Transparency = { { 0, 1 }, { 0.2, 0.4 }, { 1, 1 } },
        Lifetime = NumberRange.new(0.4, 1.2), Speed = NumberRange.new(0.001, 10 * k), SpreadAngle = Vector2.new(15, 15), Drag = 2.5,
        RotSpeed = NumberRange.new(-200, -100), Rate = 15 }, 10)
    layer("BaseCrescent", { Texture = TEX.BaseCrescent, Color = fire, Brightness = 4,
        Size = seq({ { 0, 5 * k }, { 1, 10 * k } }), Transparency = { { 0, 0.5 }, { 1, 1 } },
        Lifetime = NumberRange.new(0.5, 1), Speed = NumberRange.new(0.001, 5 * k), SpreadAngle = Vector2.new(12, 12),
        RotSpeed = NumberRange.new(-200, -100), Rate = 20 }, 13)

    -- the wisp: from just under the feet to well over the head, wide at the feet, narrowing to a point
    local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
    a0.Name, a1.Name = "BaseWispA", "BaseWispB"
    a0.Position = Vector3.new(0, BASE_FLOOR - 0.3, 0)
    a1.Position = Vector3.new(0, BASE_FLOOR - 0.3 + 10 * k, 0)
    a0.Parent, a1.Parent = root, root
    local wisp = Instance.new("Beam")
    wisp.Name = "BaseWisp"
    wisp.Attachment0, wisp.Attachment1 = a0, a1
    wisp.Texture = TEX.BaseWisp
    wisp.TextureMode = Enum.TextureMode.Stretch
    wisp.TextureSpeed = 1
    wisp.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, main), ColorSequenceKeypoint.new(0.5, main:Lerp(hot, 0.5)),
        ColorSequenceKeypoint.new(1, hot) })
    wisp.Brightness = 3 * bright
    wisp.LightEmission, wisp.LightInfluence = 1, 0
    wisp.Transparency = seq({ { 0, 0.5 }, { 0.394, 0.634 }, { 1, 1 } })
    wisp.Width0, wisp.Width1 = 8 * k, 0
    wisp.Segments = 10
    wisp.FaceCamera = true
    wisp.ZOffset = 1
    wisp.Parent = a0

    -- the sparkles: thin upright glints rising from a ring round the feet (a Disc host: from an
    -- attachment an emitter emits from one point), twinkling as they go, gone above the head
    local s = 0.7 + 0.3 * k
    emitter(host(fx, root, 2.5 * (0.85 + 0.15 * k), 0.2, BASE_FLOOR + 0.35), { Name = "BaseSparkles", Texture = TEX.BaseGlint,
        Color = ColorSequence.new(main:Lerp(hot, 0.5)), LightEmission = 0.6, Brightness = 4 * bright, LightInfluence = 0,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
        ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, ShapePartial = 0.45, EmissionDirection = Enum.NormalId.Top,
        Orientation = Enum.ParticleOrientation.FacingCameraWorldUp,
        Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.1, 0.55 * s, 0.08 * s),
            NumberSequenceKeypoint.new(0.35, 0.36 * s, 0.06 * s), NumberSequenceKeypoint.new(0.55, 0.6 * s, 0.08 * s),
            NumberSequenceKeypoint.new(0.8, 0.3 * s, 0.05 * s), NumberSequenceKeypoint.new(1, 0) }),
        Transparency = seq({ { 0, 1 }, { 0.08, 0 }, { 0.7, 0.15 }, { 1, 1 } }), Squash = seq({ { 0, -0.3 }, { 1, 0.3 } }),
        Lifetime = NumberRange.new(1.1, 1.3), Speed = NumberRange.new(6 * k, 7.5 * k), SpreadAngle = Vector2.new(6, 6),
        ZOffset = 1, Rate = rate(25) })

    -- the glow over the body
    if not voidCore then
        local centre = Instance.new("Attachment")
        centre.Name = "BaseGlow"
        centre.Position = Vector3.new(0, 0.5, 0)
        centre.Parent = root
        lifted(centre)
        local g = 0.75 + 0.25 * k
        emitter(centre, { Name = "BaseGlow", Texture = TEX.Glow, Color = ColorSequence.new(main), LightEmission = 0.5,
            Brightness = 1.2 * bright, LightInfluence = 0, Size = seq({ { 0, 5.5 * g }, { 1, 6.8 * g } }),
            Transparency = seq({ { 0, 1 }, { 0.3, 0.86 }, { 0.7, 0.86 }, { 1, 1 } }), Lifetime = NumberRange.new(1.2, 1.6),
            Speed = NumberRange.new(0), LockedToPart = true, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-15, 15),
            ZOffset = 0.5, Rate = 4 })
    end
end

local function buildRealm(root, tier, sub)
    tier = math.clamp(tier or 1, 1, 12)
    sub = math.clamp(sub or 1, 1, 5)
    local config = AuraConfig.Tiers[tier]
    local old = root:FindFirstChild("ActiveAuraFX")
    if old then RealmAura.destroy(old) end
    local fx = Instance.new("Folder")
    fx.Name = "ActiveAuraFX"
    fx.Parent = root

    local p = (sub - 1) / 5                   -- the sub-rank: 0 (Initiate) to 0.8 (Peak)
    local t = (tier - 1 + p) / 11             -- the level: 0 at the first realm, 1 at the last's base
    local function rate(base)
        return math.min(MAX_RATE, base)
    end
    local tint = config.Color
    local palette = config.Palette

    local core = Instance.new("Attachment")
    core.Name = "Core"
    core.Parent = root
    lifted(core)

    -- the owner's body aura, on every realm (its colour and scale by realm and level; Eternal's runs
    -- through its three hues)
    bodyAura(root, fx, if tier == 12 then tint else palette.Main, t, { LightEmission = 0.4, Brightness = 2 })
    -- the owner's base aura, on every realm (bigger with the level)
    baseAura(root, fx, palette, t, VOID_CORE[tier])

    -- the realm's own core: a dark void core inside a bright rim, or Realms 1 to 4's own layers; from
    -- Ascendant on, the base aura's glow and the breathing outline and light
    if VOID_CORE[tier] then
        emitter(core, { Texture = TEX.Glow, Color = ColorSequence.new(Color3.fromRGB(4, 2, 12)), LightEmission = 0,
            Size = seq({ { 0, 2.6 + 0.6 * t }, { 1, 3.2 + 0.8 * t } }), Transparency = seq({ { 0, 0.15 }, { 1, 1 } }),
            Lifetime = NumberRange.new(0.6, 0.9), Rate = rate(8), Speed = NumberRange.new(0), LockedToPart = true, ZOffset = 1 })
        if tier ~= 12 then emitter(core, { Texture = TEX.Ring, Color = tint, LightEmission = 1, Size = seq({ { 0, 4.5 + 1 * t }, { 1, 7 + 1.5 * t } }),
            Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Lifetime = NumberRange.new(0.7, 1), Rate = rate(6),
            Speed = NumberRange.new(0), LockedToPart = true, Rotation = NumberRange.new(0, 360), ZOffset = 0.5 }) end
    elseif tier == 1 then
        realm1(root, fx, tint, p)
    elseif tier == 2 then
        realm2(root, fx, tint, p)
    elseif tier == 3 then
        realm3(root, fx, tint, p)
    elseif tier == 4 then
        realm4(root, fx, tint, p)
    end
    if tier >= 5 then
        -- Realm 4's breathing outline and light, carried on and growing (a PointLight and a Highlight are
        -- the owner's must-haves)
        bodyGlow(root, fx, palette.Main, 0.1, 0.87, 2 * (palette.Glow or 1), 16 + 8 * t)
    end

    -- ribbon arcs orbiting the body: one at Ascendant, two from Immortal, three from Heavenly Dao
    local ribbons = if tier >= 10 then 3 elseif tier >= 6 then 2 elseif tier >= 5 then 1 else 0
    -- The ribbons (the owner, 2026-11-11, after the beam and trail tries: "98818011129942 I need a
    -- look something like this"): their pick is an 8x8 flipbook of one thin, sharp, glowing stroke
    -- whipping a full circle. Each swoosh is a particle lying round the body (VelocityPerpendicular,
    -- at a small random tilt), so the stroke circles the body like a ring in 3D and the body hides
    -- its back half; it plays its 64 frames once, whipping all the way round. Born at heights from
    -- the waist to the shoulders on a host that rides the body; a softer, wider copy behind each
    -- stroke is its glow. More of them, larger and quicker, the higher the realm.
    if ribbons > 0 then
        local glowK = palette.Glow or 1
        local swirlHost = Instance.new("Part")
        swirlHost.Name = "SwooshHost"
        swirlHost.Anchored, swirlHost.CanCollide, swirlHost.CanQuery, swirlHost.CanTouch, swirlHost.CastShadow = true, false, false, false, false
        swirlHost.Transparency = 1
        swirlHost.Size = Vector3.new(0.2, 2.4, 0.2)
        swirlHost.CFrame = root.CFrame * CFrame.new(0, 0.4, 0)
        swirlHost.Parent = fx
        table.insert(spinners, { kind = "follow", part = swirlHost, root = root, offset = CFrame.new(0, 0.4, 0), speed = 0, angle = 0, lifted = true })
        local size = 6.2 + 1.6 * t
        local life = NumberRange.new(1.1 - 0.3 * t, 1.3 - 0.3 * t)
        local swoosh = { Texture = TEX.Swoosh, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid8x8,
            FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
            EmissionDirection = Enum.NormalId.Top, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
            Speed = NumberRange.new(0.01), SpreadAngle = Vector2.new(22, 22), Rotation = NumberRange.new(0, 360),
            LockedToPart = true, LightInfluence = 0, Lifetime = life }
        local stroke = table.clone(swoosh)
        stroke.Name = "Swoosh"
        stroke.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, palette.Hot), ColorSequenceKeypoint.new(1, palette.Main) })
        stroke.LightEmission, stroke.Brightness = 1, 3 * glowK
        stroke.Size = NumberSequence.new(size)
        stroke.Transparency = seq({ { 0, 1 }, { 0.08, 0 }, { 0.85, 0 }, { 1, 1 } })
        stroke.Rate = 1.6 * ribbons
        stroke.ZOffset = 1
        emitter(swirlHost, stroke)
        local glow = table.clone(swoosh)
        glow.Name = "SwooshGlow"
        glow.Color = ColorSequence.new(palette.Main)
        glow.LightEmission, glow.Brightness = 1, 1.5 * glowK
        glow.Size = NumberSequence.new(size * 1.04)
        glow.Squash = NumberSequence.new(-0.25) -- a little wider: the soft halo round the stroke
        glow.Transparency = seq({ { 0, 1 }, { 0.08, 0.55 }, { 0.85, 0.55 }, { 1, 1 } })
        glow.Rate = 1.6 * ribbons
        glow.ZOffset = 0.9
        emitter(swirlHost, glow)
    end

    -- The magic circles and solid pieces (the sigils, Realm 4's seal, the signature meshes, the top
    -- realms' rigs) were removed at the owner's word, 2026-11-11: "Remove all the magic circle for all
    -- realms", "Remove the hard objects on the aura, just keep only the particle emitters and beams,
    -- trails". The top two realms keep their particles, a little stronger through the sub-ranks (not
    -- carried past a breakthrough): Heavenly Dao's streaks of law shooting into the sky, Eternal's
    -- nebula round the core.
    local grow = 1 + 0.3 * p
    if tier == 10 then
        emitter(host(fx, root, 3, 0.2, -2.9), { Texture = TEX.LawStreak, Color = ColorSequence.new(palette.Hot),
            LightEmission = 1, Orientation = Enum.ParticleOrientation.FacingCameraWorldUp, Shape = Enum.ParticleEmitterShape.Disc,
            ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, Size = seq({ { 0, 0.7 * grow }, { 1, 0.4 * grow } }),
            Transparency = seq({ { 0, 0.1 }, { 0.7, 0.3 }, { 1, 1 } }), Lifetime = NumberRange.new(0.6, 0.9),
            Rate = math.min(MAX_RATE, 14 * (1 + p)), Speed = NumberRange.new(45 * grow, 70 * grow), EmissionDirection = Enum.NormalId.Top })
    elseif tier == 12 then
        emitter(core, { Texture = TEX.Nebula, Color = tint, LightEmission = 0.6,
            Size = seq({ { 0, 5 * grow }, { 1, 7 * grow } }), Transparency = seq({ { 0, 1 }, { 0.3, 0.55 }, { 1, 1 } }),
            Lifetime = NumberRange.new(2, 3), Rate = 2.5, Speed = NumberRange.new(0), LockedToPart = true,
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-15, 15), ZOffset = 0.8 })
    end

    -- the realm's unique piece (the owner's call, 2026-11-11: "add each realm a unique particle
    -- emitter, trails or beam"), built by hand in Studio as instances, no code: a Model per realm in
    -- ReplicatedStorage.AuraMeshes.RealmUnique (Tier01 .. Tier12), its pivot where the root stood.
    -- Its invisible host parts ride on the body; one with a Ground attribute stays on the floor
    local library = ReplicatedStorage:FindFirstChild("AuraMeshes")
    library = library and library:FindFirstChild("RealmUnique")
    local template = library and library:FindFirstChild(string.format("Tier%02d", tier))
    local riders = {}
    -- (a test-range dummy already wearing its preview copy, a Model named Unique, keeps that one)
    if template and not (root.Parent and root.Parent:FindFirstChild("Unique")) then
        local copy = template:Clone()
        local pivot = copy:GetPivot()
        for _, inst in copy:GetDescendants() do
            if inst:IsA("BasePart") then
                inst.Anchored, inst.CanCollide, inst.CanQuery, inst.CanTouch = true, false, false, false
                table.insert(riders, { inst, pivot:ToObjectSpace(inst.CFrame), inst:GetAttribute("Ground") == true })
            elseif inst:IsA("ParticleEmitter") then
                inst.Rate *= RATE_SCALE
            elseif inst:IsA("BaseScript") then
                inst:Destroy() -- instances only, never code
            end
        end
        copy:PivotTo(root.CFrame)
        copy.Parent = fx
    end

    -- one step per aura moves everything that rides on the body (lifted attachments, the unique
    -- piece's parts) by the hips' shift from rest
    local torso, rest = restingBody(root.Parent)
    local attachments = building and building.lifted or {}
    if #attachments > 0 or #riders > 0 then
        table.insert(spinners, { kind = "lift", root = root, torso = torso, rest = rest, attachments = attachments,
            riders = riders, speed = 0, angle = 0 })
    end
    return fx
end

-- the auras alive now (and each folder's)
local records = {}
local recordOf = {}

-- removes everything an aura made, once. Run at once when an aura is replaced or removed: Destroying
-- handlers run deferred, too late for a rebuild in the same frame
local function cleanUp(record)
    if record.cleaned then
        return
    end
    record.cleaned = true
    for _, cleanup in record.cleanups do
        cleanup()
    end
end

function RealmAura.destroy(fx)
    local record = recordOf[fx]
    if record then
        cleanUp(record)
    end
    fx:Destroy()
end

local function cullable(inst)
    for _, class in CULLED_CLASSES do
        if inst:IsA(class) then
            return true
        end
    end
    return false
end

local function setCulled(record, culled)
    record.culled = culled
    for _, item in record.items do
        if item.Parent then
            if culled then
                record.saved[item] = item.Enabled
                item.Enabled = false
            else
                local was = record.saved[item]
                item.Enabled = if was == nil then true else was
                if item:IsA("Trail") then
                    item:Clear() -- placed this frame before it draws again, so it doesn't streak
                end
            end
        end
    end
    for _, part in record.fx:GetDescendants() do
        if part:IsA("BasePart") then
            part.LocalTransparencyModifier = if culled then 1 else 0
        end
    end
end

local function step(dt)
    local camera = workspace.CurrentCamera
    local eye = camera and camera.CFrame.Position
    for record in records do
        if not record.root:IsDescendantOf(workspace) then
            RealmAura.destroy(record.fx) -- the character went without being destroyed: its aura goes with it
            continue
        end
        record.cullClock -= dt
        if record.cullClock <= 0 and eye then
            record.cullClock = CULL_CHECK
            local far = not record.isLocal and (record.root.Position - eye).Magnitude > record.cullDistance
            if far ~= record.culled then
                setCulled(record, far)
            end
        end
    end
    for _, s in spinners do
        if s.record and s.record.culled then
            continue
        end
        s.angle += dt * s.speed
        if s.kind == "mesh" then        -- an emitter host turning round the body (Realm 1's mote rings)
            s.part.CFrame = s.root.CFrame * CFrame.Angles(0, s.angle, 0) * CFrame.new(s.offset)
        elseif s.kind == "orbit" then       -- a tilted ring turning round the body
            s.part.CFrame = s.root.CFrame * CFrame.new(s.offset) * CFrame.Angles(s.tilt, 0, 0) * CFrame.Angles(0, s.angle, 0)
        elseif s.kind == "mist" then        -- a mist ribbon's head racing round its tilted circle
            s.clock += dt
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            local pos = tiltCF * Vector3.new(math.cos(s.angle) * s.radius, (s.height or 0.3) + (s.weave or 0.6) * math.sin(s.clock * 1.3),
                math.sin(s.angle) * s.radius) + (s.record and s.record.shift or Vector3.zero)
            local up = tiltCF * Vector3.yAxis
            local out = tiltCF * Vector3.new(math.cos(s.angle), 0, math.sin(s.angle))
            for _, L in s.layers do
                local across = if L.flat then out else up
                L.a0.Position = pos + across * L.hw
                L.a1.Position = pos - across * L.hw
            end
        elseif s.kind == "orb" then         -- a smoke orb racing round its tilted circle, rising and dipping
            s.clock += dt
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            local pos = tiltCF * Vector3.new(math.cos(s.angle) * s.radius, s.height + 0.5 * math.sin(s.clock * 1.2), math.sin(s.angle) * s.radius)
            local tangent = tiltCF * Vector3.new(-math.sin(s.angle), 0, math.cos(s.angle))
            s.ball.CFrame = s.root.CFrame * CFrame.fromMatrix(pos, tangent, tiltCF * Vector3.yAxis)
            -- the electric rings: spinning, with a small jump and a flicker every few frames (crackle)
            s.boltClock += dt
            if s.boltClock >= 0.06 then
                s.boltClock = 0
                s.ringA.Rotation = (s.ringA.Rotation + 35 + math.random() * 50) % 360
                s.ringA.ImageTransparency = 0.05 + math.random() * 0.3
                local j = 0.86 + math.random() * 0.05
                s.ringA.Size = UDim2.fromScale(j, j)
                s.ringB.Rotation = (s.ringB.Rotation - 20 - math.random() * 40) % 360
                s.ringB.ImageTransparency = 0.45 + math.random() * 0.4
            end
            -- a burst flashes out from a random point on the rim for a moment
            s.sparkAt -= dt
            if s.sparkAt <= 0 then
                if s.spark.Visible then
                    s.spark.Visible = false
                    s.sparkAt = 0.25 + math.random() * 0.5
                else
                    local a = math.random() * math.pi * 2
                    s.spark.Position = UDim2.fromScale(0.5 + math.cos(a) * 0.42, 0.5 + math.sin(a) * 0.42)
                    s.spark.Rotation = math.deg(a) + 90
                    s.spark.Visible = true
                    s.sparkAt = 0.08 + math.random() * 0.06
                end
            end
        elseif s.kind == "meditate" then    -- Realm 4's ground smoke: idle or meditating
            local player = s.model and Players:GetPlayerFromCharacter(s.model)
            local on = if player then player:GetAttribute("IsCultivating") == true
                else s.model ~= nil and s.model:GetAttribute("IsCultivating") == true
            local target = if on then 1 else 0
            local k = if s.k < 0 then target else s.k + (target - s.k) * math.min(1, dt * 3)
            if math.abs(k - s.k) > 0.002 then
                s.k = k
                local function mix(a, b) return a + (b - a) * k end
                s.ripple.Rate = RATE_SCALE * mix(2 + 0.3 * s.p, 3.5 + 0.5 * s.p)                -- the owner: "faster loop ripple"
                s.ripple.Lifetime = NumberRange.new(mix(1.5, 0.9), mix(1.7, 1.1))
                s.mist.Rate = RATE_SCALE * mix(9 + 2 * s.p, 16 + 3 * s.p)                      -- denser (the owner)
                s.mist.Lifetime = NumberRange.new(mix(3.2, 1.9), mix(3.8, 2.3))   -- shorter: swells out faster
                local spin = mix(20, 55)
                s.mist.RotSpeed = NumberRange.new(-spin, spin)
                if s.vortex then                                              -- the owner's vortex quickens and spins up
                    s.vortex.Rate = RATE_SCALE * mix(22 + 4 * s.p, 30 + 5 * s.p)
                    s.vortex.Lifetime = NumberRange.new(mix(0.8, 0.6), mix(3, 2.2))
                    s.vortex.RotSpeed = NumberRange.new(mix(5, 12))
                end
            end
        elseif s.kind == "ground" then      -- Realm 4's ground pieces kept on the floor under the feet
            if s.fx.Parent then
                s.rayClock -= dt
                if s.rayClock <= 0 then                                      -- the floor under the feet, 10 times a second
                    s.rayClock = 0.1
                    local centre = s.root.Position
                    local hit = workspace:Raycast(centre, Vector3.new(0, -12, 0), s.rayParams)
                    local groundY = if hit then hit.Position.Y else centre.Y - 3
                    local _, yaw = s.root.CFrame:ToOrientation()
                    for _, g in s.grounded do
                        local cf = CFrame.new(centre.X, groundY + g[2], centre.Z)
                        g[1].CFrame = if g[3] then cf * CFrame.fromOrientation(0, yaw, 0) else cf
                    end
                end
            end
        elseif s.kind == "lift" then        -- what rides on the body, moved by the hips' shift from rest
            local shift = Vector3.zero
            if s.torso and s.rest and s.torso.Parent then
                shift = s.root.CFrame:PointToObjectSpace(s.torso.Position) - s.rest
            end
            if s.record then
                s.record.shift = shift -- the ribbons and mist ride on it too
            end
            for _, item in s.attachments do
                if item[1].Parent then
                    item[1].Position = item[2] + shift
                end
            end
            local base = s.root.CFrame
            local raised = base * CFrame.new(shift)
            for _, rider in s.riders do
                rider[1].CFrame = (if rider[3] then base else raised) * rider[2]
            end
        elseif s.kind == "gyro" then        -- a tilted ring: turning in its plane, its tilt swinging round
            s.spin += dt * s.spinSpeed
            s.part.CFrame = s.root.CFrame * CFrame.new(s.offset) * CFrame.Angles(0, s.angle, 0) * CFrame.Angles(s.tilt, 0, 0) * CFrame.Angles(0, s.spin, 0)
        elseif s.kind == "arc" then         -- a Qi thread circling the body: both ends on the circle
            local tiltCF = CFrame.Angles(s.tilt, 0, 0)
            for j, at in { s.a0, s.a1 } do
                local ang = s.angle + (j - 1) * s.span
                local pos = Vector3.new(math.cos(ang) * s.radius, s.height, math.sin(ang) * s.radius)
                local tangent = Vector3.new(-math.sin(ang), 0, math.cos(ang))
                at.CFrame = tiltCF * CFrame.fromMatrix(pos, tangent, Vector3.yAxis)
            end
        elseif s.kind == "outline" then     -- Realm 1's outline, breathing (4 s in, 4 s out)
            s.clock += dt
            local out = 0.5 + 0.5 * math.cos(s.clock * math.pi / 4)
            s.highlight.OutlineTransparency = s.line + 0.18 * out
            s.highlight.FillTransparency = s.fill + 0.04 * out
            s.light.Brightness = s.glow * (1 - 0.35 * out)
        elseif s.kind == "follow" then      -- an emitter host, keeping its place round the root (riding the body's lift if marked)
            local shift = if s.lifted and s.record and s.record.shift then s.record.shift else Vector3.zero
            s.part.CFrame = s.root.CFrame * CFrame.new(shift) * s.offset
        end
    end
end

local stepping = nil

-- builds the aura of a realm (1-12) and sub-rank (1-5) round a character's root (or a test dummy's).
-- options.isLocal: never culled (the local player's own aura); options.cullDistance overrides it
function RealmAura.build(root, realm, sub, options)
    options = options or {}
    local before = {}
    for _, child in root:GetChildren() do
        before[child] = true
    end
    local record = { root = root, items = {}, saved = {}, cleanups = {}, lifted = {}, culled = false, cullClock = 0,
        isLocal = options.isLocal == true, cullDistance = options.cullDistance or CULL_DISTANCE_LIVE }
    local first = #spinners + 1
    building = record
    local ok, fx = pcall(buildRealm, root, realm, sub)
    building = nil
    if not ok then
        warn("[RealmAura] build failed:", fx)
        local partial = root:FindFirstChild("ActiveAuraFX")
        if partial then
            partial:Destroy()
        end
        return nil
    end
    record.fx = fx

    -- what the build hung on the root itself (attachments, beams, trails) goes with the folder
    local onRoot = {}
    for _, child in root:GetChildren() do
        if not before[child] and child ~= fx then
            table.insert(onRoot, child)
        end
    end
    for i = first, #spinners do
        spinners[i].record = record
    end
    -- each effect once (listed twice, culling saved its switched-off state over its own and never
    -- switched it back on)
    local listed = {}
    local function list(inst)
        if cullable(inst) and not listed[inst] then
            listed[inst] = true
            table.insert(record.items, inst)
        end
    end
    for _, inst in fx:GetDescendants() do
        list(inst)
    end
    for _, inst in onRoot do
        list(inst)
        for _, inner in inst:GetDescendants() do
            list(inner)
        end
    end
    records[record] = true
    recordOf[fx] = record

    table.insert(record.cleanups, function()
        records[record] = nil
        recordOf[fx] = nil
        for i = #spinners, 1, -1 do
            if spinners[i].record == record then
                table.remove(spinners, i)
            end
        end
        for _, inst in onRoot do
            inst:Destroy()
        end
    end)
    fx.Destroying:Connect(function()
        cleanUp(record)
    end)

    if not stepping then
        stepping = RunService.RenderStepped:Connect(step)
    end
    return fx
end

return RealmAura

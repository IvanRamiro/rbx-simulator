local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))

local meshFolder = ReplicatedStorage:WaitForChild("PetMeshes", 10)
-- the folder, looked for again while it's missing (it can replicate after the 10 s wait on a slow join)
local function meshes()
    meshFolder = meshFolder or ReplicatedStorage:FindFirstChild("PetMeshes")
    return meshFolder
end

local PetModels = {}

-- [model] = its rig. A rig holds its model, so a weak key would never free it: each entry goes
-- when its model is destroyed (keep).
local rigs = {}
local function keep(model, rig)
    rigs[model] = rig
    model.Destroying:Once(function()
        rigs[model] = nil
    end)
end

function PetModels.getRig(model)
    return rigs[model]
end

PetModels.SIZE = 2

local function at(x, y, z, rx, ry, rz)
    return CFrame.new(x, y, z) * CFrame.Angles(math.rad(rx or 0), math.rad(ry or 0), math.rad(rz or 0))
end

local function mirrored(parts, make)
    table.insert(parts, make(-1))
    table.insert(parts, make(1))
end

local function nineTailMoonfox()
    local fur = Color3.fromRGB(245, 245, 255)
    local lilac = Color3.fromRGB(190, 160, 255)
    local violet = Color3.fromRGB(150, 110, 255)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(0.75, 0.7, 1.2), At = at(0, 0, 0.1), Color = fur },
        { Shape = "Prism", Size = Vector3.new(0.8, 0.7, 0.7), At = at(0, 0.45, -0.65), Color = fur },
        { Shape = "Wedge", Size = Vector3.new(0.4, 0.3, 0.45), At = at(0, 0.32, -1.18), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.12, 0.12, 0.05), At = at(0, 0.72, -1.01, 0, 0, 45), Color = lilac, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.12, 0.5, 0.35), At = at(0.25 * side, 0.92, -0.6, 0, 90 * side), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.15, 0.1, 0.06), At = at(0.2 * side, 0.52, -1.01), Color = violet, Neon = true }
    end)
    for tail = 1, 9 do
        local base = at(0, 0.15, 0.75, 25, 0, -60 + (tail - 1) * 15)
        table.insert(parts, { Shape = "Wedge", Size = Vector3.new(0.12, 0.85, 0.25), At = base * CFrame.new(0, 0.5, 0), Color = fur })
        table.insert(parts, { Shape = "Block", Size = Vector3.new(0.15, 0.15, 0.15), At = base * CFrame.new(0, 0.98, 0) * CFrame.Angles(0, 0, math.rad(45)), Color = lilac, Neon = true })
    end
    return { Scale = 1.2, Parts = parts }
end

PetModels.Pets = {
    AquaWisp = { Scale = 0.95, Parts = {} }, -- recreated (2026-11-09): only its imported model; its old droplet design removed (MESH_LOOKS was tuned with this scale)
    EmberWyrm = { Scale = 1.05, Parts = {} }, -- recreated (2026-11-09): only its imported model; its old lava-bead design removed (MESH_LOOKS was tuned with this scale)
    LunarHopper = { Scale = 1.0, Parts = {} }, -- recreated (2026-11-10): only its imported model; its old faceted-rabbit design removed (MESH_LOOKS was tuned with this scale)
    VoltFox = { Scale = 1.05, Parts = {} }, -- recreated (2026-11-10): only its imported model; its old yellow block-fox design removed (MESH_LOOKS was tuned with this scale)
    GoldenKirin = { Scale = 1.15, Parts = {} }, -- recreated (2026-11-09): only its imported model; its old design removed (MESH_LOOKS was tuned with this scale)
    NineTailMoonfox = nineTailMoonfox(),
    OriginSerpent = { Scale = 1.25, Parts = {} }, -- recreated (2026-11-10): only its imported model; its old block serpent removed (MESH_LOOKS was tuned with this scale)
    AstralWhale = { Scale = 1.25, Parts = {} }, -- recreated (2026-11-10): only its imported model; its old faceted block whale removed (MESH_LOOKS was tuned with this scale)
    MossGolem = { Scale = 0.9, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
    MyceliumSprite = { Scale = 0.9, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
    JadeSpiritPanda = { Scale = 1, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
    JadeAntlerDeer = { Scale = 1.05, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
    MagmaCub = { Scale = 0.95, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
    SunscaleDragon = { Scale = 1, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
    DawnPhoenix = { Scale = 1.15, Parts = {} }, -- its imported model; its old procedural design removed (MESH_LOOKS was tuned with this scale)
}

-- every other pet: its imported model at its rarity's scale; the few still without one (PetArchetypes.Specs) built from simple shapes
do
    local PetArchetypes = require(script.Parent:WaitForChild("PetArchetypes"))
    for petId, pet in GameConfig.Pets do
        if not PetModels.Pets[petId] then
            local spec = PetArchetypes.Specs[petId]
            PetModels.Pets[petId] = if spec then PetArchetypes.build(spec, pet.Rarity) else { Scale = PetArchetypes.scaleFor(pet.Rarity), Parts = {} }
        end
    end
end

local PART_SHAPES = {
    Block = Enum.PartType.Block,
    Wedge = Enum.PartType.Wedge,
}

local PRISM_TURNS = {
    X = CFrame.identity,
    Y = CFrame.Angles(0, 0, math.rad(90)),
    Z = CFrame.Angles(0, math.rad(90), 0),
}

local function prismPieces(size, axis)
    local length, height, depth
    if axis == "X" then
        length, height, depth = size.X, size.Y, size.Z
    elseif axis == "Y" then
        length, height, depth = size.Y, size.X, size.Z
    else
        length, height, depth = size.Z, size.Y, size.X
    end

    local turn = PRISM_TURNS[axis]
    local corner = math.min(height, depth) * 0.293
    local pieces = {
        { Shape = "Block", Size = Vector3.new(length, height - 2 * corner, depth), Offset = turn, Tone = 0 },
        { Shape = "Block", Size = Vector3.new(length, height, depth - 2 * corner), Offset = turn, Tone = 0 },
    }
    for index, signs in { { 1, 1 }, { -1, 1 }, { -1, -1 }, { 1, -1 } } do
        table.insert(pieces, {
            Shape = "Wedge",
            Tone = signs[1],
            Size = Vector3.new(length, corner, corner),
            Offset = turn
                * CFrame.new(0, signs[1] * (height / 2 - corner / 2), signs[2] * (depth / 2 - corner / 2))
                * CFrame.Angles(math.rad(90 * (index - 1)), 0, 0)
                * CFrame.Angles(0, math.pi, 0),
        })
    end
    return pieces
end

local function toneColor(color, tone)
    if tone > 0 then
        return color:Lerp(Color3.new(1, 1, 1), 0.22)
    elseif tone < 0 then
        return color:Lerp(Color3.new(0, 0, 0), 0.22)
    end
    return color
end

local function createPart(model, rootPart, shape, size, cframe, spec, tone)
    local part = Instance.new("Part")
    part.Shape = PART_SHAPES[shape]
    part.Size = size
    part.CFrame = cframe
    part.Color = if spec.Neon then spec.Color else toneColor(spec.Color, tone or 0)
    part.Material = if spec.Neon then Enum.Material.Neon elseif spec.Glass then Enum.Material.Glass else Enum.Material.SmoothPlastic
    part.Transparency = spec.Transparency or 0
    part.TopSurface = Enum.SurfaceType.Smooth
    part.BottomSurface = Enum.SurfaceType.Smooth
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Massless = true
    part.Anchored = false

    local weld = Instance.new("WeldConstraint")
    weld.Part0 = rootPart
    weld.Part1 = part
    weld.Parent = part

    part.Parent = model
end

local MESH_LOOKS = {
    MyceliumSprite = { Glow = Color3.fromRGB(90, 245, 215), Length = 2.6 },
    MossGolem = { Glow = Color3.fromRGB(110, 255, 140), Length = 3.4 },
    JadeSpiritPanda = { Glow = Color3.fromRGB(60, 225, 130), Length = 3.3 },
    JadeAntlerDeer = { Glow = Color3.fromRGB(60, 225, 140), Length = 4.2 },
    MagmaCub = { Glow = Color3.fromRGB(255, 120, 30), Length = 2.6 },
    AzureSkyDragon = { Glow = Color3.fromRGB(90, 215, 255), Length = 5.0 }, -- its box's longest side is its gliding wingspan (nose to tail 0.88 of it); in Play, 10.5 studs tip to tip and 9.3 nose to tail, as long as the Sunscale Dragon
    SpiritCrane = { Glow = Color3.fromRGB(40, 210, 200), Length = 4.2 },
    CloudSheep = { Glow = Color3.fromRGB(120, 215, 245), Length = 3.0 },
    WindSprite = { Glow = Color3.fromRGB(30, 235, 180), Length = 3.5 },
    GalaxyManta = { Glow = Color3.fromRGB(140, 100, 255), Length = 4.0 },
    AbyssAnomalocaris = { Glow = Color3.fromRGB(190, 36, 146), Length = 3.8 },
    VoidscaleHydra = { Glow = Color3.fromRGB(70, 150, 255), Length = 4.0 },
    TheNamelessOne = { Glow = Color3.fromRGB(200, 170, 255), Length = 3.6 },
    EclipseCat = { Glow = Color3.fromRGB(176, 124, 255), Length = 3.0 },
    Shadowcoil = { Glow = Color3.fromRGB(168, 255, 224), Length = 3.0 },
    CelestialPearlDragon = { Glow = Color3.fromRGB(224, 210, 255), Length = 4.6 },
    CelestialSnowLeopard = { Glow = Color3.fromRGB(196, 232, 255), Length = 4.2 },
    CometStag = { Glow = Color3.fromRGB(150, 210, 255), Length = 4.6 },
    SandPhantom = { Glow = Color3.fromRGB(240, 196, 120), Length = 4.0 }, -- its long tail is most of its length
    SolarButterfly = { Glow = Color3.fromRGB(255, 170, 70), Length = 3.8 }, -- its wingspan
    ObsidianGuardian = { Glow = Color3.fromRGB(176, 110, 255), Length = 3.8 }, -- its folded wings' peaks: its tallest part
    GlacierPuff = { Glow = Color3.fromRGB(170, 225, 255), Length = 2.6 }, -- its box runs from the origin below it (it floats) to its top: about 4 studs nose to tail
    GravityImp = { Glow = Color3.fromRGB(210, 140, 255), Length = 2.6 }, -- its box runs from the origin, just under its moonlet, to its cowlick (it is "a small creature": at 3.2 it stood taller than its owner)
    CrystalBeetle = { Glow = Color3.fromRGB(160, 245, 255), Length = 3.2 }, -- nose to tail (its longest): long and low, so at 2.6 it was knee-high and lost in tall grass
    ThunderclawDrake = { Glow = Color3.fromRGB(255, 235, 100), Length = 5.8 }, -- its box's longest side is its raised wingspan; nose to tail it is three quarters of that (at 5.2 its head came only to its owner's, lost in tall grass)
    FrostfangSerpent = { Glow = Color3.fromRGB(130, 210, 255), Length = 3.4 }, -- its box's longest side is its height, reared: about the Pearl Dragon's
    StormBumblebee = { Glow = Color3.fromRGB(255, 220, 80), Length = 3.2 }, -- feeler tips to tail (its longest), hovering: about the Crystal Beetle's
    TimekeeperTortoise = { Glow = Color3.fromRGB(255, 214, 130), Length = 4.4 }, -- head to tail
    StormhornKirin = { Glow = Color3.fromRGB(90, 170, 255), Length = 4.4 },
    JadeWyrmTurtle = { Glow = Color3.fromRGB(60, 220, 170), Length = 4.8 },
    NebulaOwl = { Glow = Color3.fromRGB(176, 122, 255), Length = 4.0 },
    CosmicJellyfish = { Glow = Color3.fromRGB(245, 120, 180), Length = 3.3 },
    StarfallFox = { Glow = Color3.fromRGB(150, 160, 255), Length = 3.6 },
    LanternWarden = { Glow = Color3.fromRGB(255, 176, 70), Length = 3.2 },
    DreamMoth = { Glow = Color3.fromRGB(230, 170, 255), Length = 3.2 },
    PrismArmadillo = { Glow = Color3.fromRGB(190, 150, 255), Length = 4.0 },
    CrystalSnail = { Glow = Color3.fromRGB(110, 230, 200), Length = 3.2 },
    GoldenManeLion = { Glow = Color3.fromRGB(255, 180, 60), Length = 4.4 },
    DawnPhoenix = { Glow = Color3.fromRGB(255, 170, 70), Length = 4.6 },
    AquaWisp = { Glow = Color3.fromRGB(60, 196, 232), Length = 1.8 }, -- crown to tail (its longest, upright): about 3.4 studs, a small starter beside its owner
    EmberWyrm = { Glow = Color3.fromRGB(255, 122, 30), Length = 2.4 }, -- nose to campfire (its longest): about 5 studs long and 1.5 tall, a small salamander at its owner's feet
    LunarHopper = { Glow = Color3.fromRGB(143, 188, 255), Length = 1.85 }, -- feet to ear crowns (its longest, sat up): about 3.7 studs, a little moon rabbit at its owner's feet; its old star sparkles removed
    VoltFox = { Glow = Color3.fromRGB(70, 190, 255), Length = 2.4 }, -- nose to the back of its cloud (its longest): about 5 studs, a fox kit at its owner's feet, its cloud over its back; its old sparks removed
    GoldenKirin = { Glow = Color3.fromRGB(255, 214, 120), Length = 2.4 }, -- nose to tail-silk (its longest), 5.5 studs; its halo's top about 4.8 studs up, under its owner's head (k is about 2.3 for it: 4.4 stood it 9 studs tall)
    AstralWhale = { Glow = Color3.fromRGB(255, 176, 48), Length = 3.6 }, -- rostrum to flukes (its longest): about 7 studs, a whale calf swimming beside its owner; its old star sparkles removed
    OriginSerpent = { Glow = Color3.fromRGB(30, 205, 255), Length = 3.0 }, -- tail root to antler tips (its tallest): about 7.5 studs, a floating helix taller than its owner; its old star sparkles removed
    SunscaleDragon = { Glow = Color3.fromRGB(255, 194, 74), Length = 4.6 },
    BonefireDragon = { Glow = Color3.fromRGB(61, 123, 255), Length = 4.6 }, -- nose to tail (its box's longest side); in Play about 10.6 studs, its raised wing bones half that high
    PrismaticPhoenix = { Effect = "Glitter", Glow = Color3.fromRGB(255, 175, 130), Length = 4.2 },
    RuneSphinx = { Glow = Color3.fromRGB(255, 190, 90), Length = 4.0 },
    WorldrootColossus = { Effect = "Glitter", Glow = Color3.fromRGB(90, 235, 120), Length = 3.6 },
    ThousandYearDreamEater = { Effect = "Stars", Glow = Color3.fromRGB(170, 120, 255), Length = 3.7 },
    EternalClockworkDragon = { Effect = "Sparks", Glow = Color3.fromRGB(255, 200, 90), Length = 4.3 },
    HeavenbreakerApe = { Effect = "Sparks", Glow = Color3.fromRGB(255, 215, 110), Length = 3.4 },
    DreadfangCerberus = { Glow = Color3.fromRGB(40, 200, 255), Length = 3.4 },
}

local TEXTURES = {
    Glow = "rbxasset://textures/particles/explosion01_implosion_main.dds",
    Sparkle = "rbxasset://textures/particles/sparkles_main.dds",
    Fire = "rbxasset://textures/particles/fire_main.dds",
    Sparks = "rbxasset://textures/particles/fire_sparks_main.dds",
}

local function emitter(parent, properties)
    local particles = Instance.new("ParticleEmitter")
    particles.LightInfluence = 0
    for property, value in properties do
        particles[property] = value
    end
    particles.Parent = parent
    return particles
end

local function sizeCurve(peak, k)
    return NumberSequence.new({
        NumberSequenceKeypoint.new(0, 0),
        NumberSequenceKeypoint.new(0.3, peak * k),
        NumberSequenceKeypoint.new(1, 0),
    })
end

local MESH_EFFECTS = {
    Bubbles = function(body, tail, glow, k)
        emitter(body, {
            Texture = TEXTURES.Glow, Color = ColorSequence.new(glow), LightEmission = 0.4, Brightness = 2,
            Size = sizeCurve(0.22, k), Transparency = NumberSequence.new(0.2), Rate = 5,
            Lifetime = NumberRange.new(1.2, 1.8), Speed = NumberRange.new(0.3, 0.8), SpreadAngle = Vector2.new(180, 180),
            Acceleration = Vector3.new(0, 1, 0),
        })
    end,
    TailFlame = function(body, tail, glow, k)
        emitter(tail, {
            Texture = TEXTURES.Fire, Brightness = 5, LightEmission = 0.4,
            Color = ColorSequence.new({
                ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 220, 120)),
                ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 120, 40)),
                ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 20)),
            }),
            Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7 * k), NumberSequenceKeypoint.new(1, 0.15 * k) }),
            Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) }),
            Rate = 18, Lifetime = NumberRange.new(0.35, 0.55), Speed = NumberRange.new(1, 2),
            SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 6, 0),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90),
        })
        emitter(body, {
            Texture = TEXTURES.Glow, Color = ColorSequence.new(glow), LightEmission = 0.5, Brightness = 2,
            Size = sizeCurve(0.12, k), Rate = 6, Lifetime = NumberRange.new(0.8, 1.3),
            Speed = NumberRange.new(0.5, 1.2), SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, 2.5, 0),
        })
    end,
    Stars = function(body, tail, glow, k)
        emitter(body, {
            Texture = TEXTURES.Sparkle, Color = ColorSequence.new(glow), LightEmission = 0.6, Brightness = 2,
            Size = sizeCurve(0.35, k), Rate = 6, Lifetime = NumberRange.new(0.5, 0.9),
            Speed = NumberRange.new(0.1, 0.4), SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 90),
        })
    end,
    Sparks = function(body, tail, glow, k)
        for _, source in { body, tail } do
            emitter(source, {
                Texture = TEXTURES.Sparks, Color = ColorSequence.new(glow), LightEmission = 0.6, Brightness = 2.5,
                Orientation = Enum.ParticleOrientation.VelocityParallel,
                Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * k), NumberSequenceKeypoint.new(1, 0.05 * k) }),
                Rate = 6, Lifetime = NumberRange.new(0.12, 0.25), Speed = NumberRange.new(4, 7),
                SpreadAngle = Vector2.new(180, 180), Drag = 6,
            })
        end
    end,
    Glitter = function(body, tail, glow, k)
        emitter(body, {
            Texture = TEXTURES.Sparkle, Color = ColorSequence.new(Color3.fromRGB(255, 225, 120), glow), LightEmission = 0.6,
            Brightness = 2, Size = sizeCurve(0.25, k), Rate = 7, Lifetime = NumberRange.new(0.6, 1),
            Speed = NumberRange.new(0.2, 0.5), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.6, 0),
        })
    end,
}

local function weldTo(rootPart, part)
    part.Anchored = false
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Massless = true
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = rootPart
    weld.Part1 = part
    weld.Parent = part
end

local dressUp

local function addImported(model, rootPart, template, design, petId)
    local look = MESH_LOOKS[petId] or {}
    local turn = template:GetAttribute("Turn") or CFrame.identity
    local boxCFrame, boxSize = template:GetBoundingBox()
    local longest = math.max(boxSize.X, boxSize.Y, boxSize.Z)
    local k = design.Scale * PetModels.SIZE
    local scale = (look.Length or longest) * k / longest

    if PetRig.isRigged(petId, template) then
        if PetRig.Profiles[petId].Skinned then
            keep(model, PetRig.buildSkinned(model, rootPart, template, petId, turn, scale, (look.Length or longest) * k))
            return
        end
        local function place(piece)
            local offset = CFrame.new(-boxCFrame.Position) * piece.CFrame
            return turn * (offset.Rotation + offset.Position * scale), piece.Size * scale
        end
        keep(model, PetRig.build(model, rootPart, template, petId, place, scale))
        return
    end

    local body
    for _, piece in template:GetDescendants() do
        if not piece:IsA("BasePart") then
            continue
        end
        local part = piece:Clone()
        local hex = string.match(piece.Name, "_Glow_(%x%x%x%x%x%x)$")
        for _, child in part:GetChildren() do
            if hex or not child:IsA("SurfaceAppearance") then
                child:Destroy()
            end
        end
        local offset = CFrame.new(-boxCFrame.Position) * piece.CFrame
        part.Size = piece.Size * scale
        part.CFrame = turn * (offset.Rotation + offset.Position * scale)
        if hex then
            part.Color = Color3.fromHex(hex)
            part.Material = Enum.Material.Neon
            if part:IsA("MeshPart") then
                part.TextureID = ""
            end
        else
            part.Material = Enum.Material.SmoothPlastic
            body = body or part
        end
        weldTo(rootPart, part)
        part.Parent = model
    end
    if body then
        dressUp(model, rootPart, body, boxSize * scale, look, k, turn)
    end
end

dressUp = function(model, rootPart, body, size, look, k, turn)
    local glow = look.Glow or Color3.new(1, 1, 1)
    local shell = body:Clone()
    shell.Name = "EnergyShell"
    shell:ClearAllChildren()
    shell.Material = Enum.Material.ForceField
    shell.Color = glow
    if shell:IsA("MeshPart") then
        shell.TextureID = ""
    end
    shell.Size = body.Size * 1.06
    weldTo(rootPart, shell)
    shell.Parent = model

    local light = Instance.new("PointLight")
    light.Color = glow
    light.Brightness = 1.2
    light.Range = 3 * k
    light.Parent = body

    local effect = MESH_EFFECTS[look.Effect]
    if effect then
        local tail = Instance.new("Attachment")
        tail.Name = "TailTip"
        tail.Position = (turn or CFrame.identity) * Vector3.new(0, size.Y * 0.25, size.Z * 0.45)
        tail.Parent = rootPart
        effect(body, tail, glow, k)
    end
end

local warnedMissing = {} -- [petId] = true once its missing model has been reported

function PetModels.build(petId)
    local design = PetModels.Pets[petId]
    if not design then
        return nil
    end

    local model = Instance.new("Model")
    model.Name = petId

    local rootPart = Instance.new("Part")
    rootPart.Name = "Root"
    rootPart.Size = Vector3.new(0.2, 0.2, 0.2)
    rootPart.Transparency = 1
    rootPart.Anchored = true
    rootPart.CanCollide = false
    rootPart.CanTouch = false
    rootPart.CanQuery = false
    rootPart.CFrame = CFrame.identity
    rootPart.Parent = model
    model.PrimaryPart = rootPart

    local imported = meshes() and meshFolder:FindFirstChild(petId, true)
    if imported and imported:IsA("Model") then
        addImported(model, rootPart, imported, design, petId)
        return model, rootPart
    end

    if #design.Parts == 0 and not warnedMissing[petId] then
        -- a pet whose only design is its imported model: without ReplicatedStorage.PetMeshes it would be an invisible root
        warnedMissing[petId] = true
        warn("PetModels: no imported model for " .. petId .. " in ReplicatedStorage.PetMeshes" .. (if meshFolder then "" else " (the folder is missing)"))
    end

    local scale = design.Scale * PetModels.SIZE
    for _, spec in design.Parts do
        local offset = spec.At - spec.At.Position + spec.At.Position * scale
        local size = spec.Size * scale

        if spec.Shape == "Prism" then
            for _, piece in prismPieces(size, spec.Axis or "Z") do
                createPart(model, rootPart, piece.Shape, piece.Size, offset * piece.Offset, spec, piece.Tone)
            end
        else
            createPart(model, rootPart, spec.Shape, size, offset, spec)
        end
    end

    return model, rootPart
end

for petId in GameConfig.Pets do
    assert(PetModels.Pets[petId], "PetModels has no model for pet " .. petId)
end

for petId, design in PetModels.Pets do
    for _, spec in design.Parts do
        assert(spec.Shape == "Prism" or PART_SHAPES[spec.Shape], "PetModels: " .. petId .. " uses an unknown Shape: " .. tostring(spec.Shape))
        assert(spec.Shape ~= "Prism" or PRISM_TURNS[spec.Axis or "Z"], "PetModels: " .. petId .. " has a prism with an unknown Axis")
    end
end

return PetModels

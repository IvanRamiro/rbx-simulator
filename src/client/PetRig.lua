-- Animated pets: a pet exported from Blender with --rig (tools/blender/export_pet.py)
-- arrives as separate parts plus tiny marker meshes:
--   <PetId>_<Part>                a rig part (palette textured)
--   <PetId>_<Part>_Glow_<hex>     that part's glowing pieces (Neon); a part may be glow only
--   <PetId>_Pivot_<Part>          where the part's joint sits
--   <PetId>_Point_<Owner>_<Name>  an effect attachment on the Owner part
-- PetRig.build joins the parts with Motor6Ds at the pivots and adds the pet's
-- effects. Each species moves in its own way: its profile's Animate poses the
-- joints every frame from code, so no uploaded animations are needed. The
-- model also gets an AnimationController with an Animator, so uploaded
-- keyframe animations can drive the same Motor6Ds later.
-- Purely visual and client-side, like the rest of the pets.

local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")

local PetRig = {}

local SPARKLE = "rbxasset://textures/particles/sparkles_main.dds"

local function pose(motor, cframe)
    if motor then
        motor.Transform = cframe
    end
end

local function smoothstep(edge0, edge1, x)
    local t = math.clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
end

-- Sunscale Dragon, the Solar Ouroboros: a legless dragon coiled around its own
-- small sun, ringed by a corona of ray-blades instead of wings.
local function animateOuroboros(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local axis = rig.axis

    -- The coil leans into its travel, bobs and slowly rocks; it rises for the Nova
    pose(m.Body, CFrame.new(0, (0.05 * math.sin(t * 1.3) + 0.25 * nova) * u, 0)
        * CFrame.Angles(-0.14 * moving - 0.3 * fly + 0.03 * math.sin(t * 0.9), 0, 0.05 * math.sin(t * 0.7)))

    -- The sun turns slowly inside the coil
    pose(m.Sun, CFrame.fromAxisAngle(axis, t * 0.8))

    -- The head looks about and rears back for the Nova
    pose(m.Head, CFrame.Angles(
        0.08 * math.sin(t * 1.1) - 0.1 * fly + 0.5 * nova,
        0.22 * math.sin(t * 0.6) * (1 - nova),
        0.06 * math.sin(t * 0.8)))

    -- The tail flicks
    pose(m.Tail, CFrame.Angles(0.1 * math.sin(t * 1.7), 0.3 * math.sin(t * 2.1), 0))

    -- The corona spins, faster when moving and fastest in the Nova
    s.spin = (s.spin or 0) + rig.deltaTime * (0.5 + 1.2 * moving + 1.6 * fly + 5 * nova)
    pose(m.Corona, CFrame.fromAxisAngle(axis, s.spin))

    -- Each ray breathes; they sweep back in flight and open forward like a sunflower in the Nova
    for index, ray in rig.rays do
        local angle = 0.08 * math.sin(t * 1.5 + index * 0.7) + 0.45 * fly - 0.95 * nova
        pose(ray.motor, CFrame.fromAxisAngle(ray.tangent, angle))
    end
end

-- Which parts each animated pet has, how they hang together, and how it moves.
--   Joints      part -> the part it hangs from ("Root" is the pet's root part)
--   Attached    parts welded to another part without a joint
--   SeeThrough  part or glow names -> transparency
--   Effects     which parts and points carry the shared effects
PetRig.Profiles = {
    SunscaleDragon = {
        Joints = {
            Body = "Root",
            Sun = "Body",
            Head = "Body",
            Tail = "Body",
            Corona = "Body",
        },
        -- Ray01..Ray12 hang from the corona (added below)
        RayPrefix = "Ray",
        RayParent = "Corona",
        Attached = {},
        SeeThrough = { Sun_Glow_ff8c24 = 0.45 },
        Effects = {
            Motes = "Sun",
            Light = "Sun",
            Pulse = "Sun",
            Burst = "Sun",
            Sparks = { "Head_Eye" },
            Trail = "Tail_Tip",
            Axis = "Corona_Axis",
        },
        Colors = {
            Gold = Color3.fromHex("FFD447"),
            Amber = Color3.fromHex("D97706"),
            Orange = Color3.fromHex("FF8C24"),
            Sun = Color3.fromHex("FFF700"),
            Ivory = Color3.fromHex("FFF1CC"),
        },
        Animate = animateOuroboros,
    },
}
for index = 1, 12 do
    PetRig.Profiles.SunscaleDragon.Joints[string.format("Ray%02d", index)] = "Corona"
end

PetRig.NOVA_TIME = 2.6 -- Seconds the special ability lasts
local NOVA_BURST_AT = 0.42 -- Fraction of the way through when the blast goes off

function PetRig.isRigged(petId, template)
    return PetRig.Profiles[petId] ~= nil and template:FindFirstChild(petId .. "_Pivot_Body", true) ~= nil
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

-- Shared effects, placed by the profile: drifting motes, sparks at points, a
-- pulsing light, a burst emitter for the special and a trail while flying.
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

    local tip = rig.points[effects.Trail]
    if tip then
        local upper = Instance.new("Attachment")
        upper.Name = "TrailTop"
        upper.CFrame = tip.CFrame * CFrame.new(0, 0.25 * u, 0)
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
        trail.Enabled = false
        trail.Parent = tip.Parent
        rig.trail = trail
    end
end

-- Builds the rigged pet into `model`. `place(piece)` gives each imported
-- piece's CFrame and size in pet space (the same placement unrigged pets use),
-- `unit` the studs per Blender unit. Returns the rig, which PetRig.update drives.
function PetRig.build(model, rootPart, template, petId, place, unit)
    local profile = PetRig.Profiles[petId]
    local prefix = petId .. "_"
    local rig = {
        profile = profile,
        model = model,
        rootPart = rootPart,
        unit = unit,
        parts = {},
        motors = {},
        points = {},
        pointPositions = {},
        pulseGlow = {},
        rays = {},
        deltaTime = 0,
        state = { walk = 0, fly = 0, time = math.random() * 10 },
    }

    -- Clone every piece into place, sorting out parts, glows and markers
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
        part.Transparency = profile.SeeThrough[name] or 0
        prepare(part)
        local owner, hex = string.match(name, "^(.+)_Glow_(%x%x%x%x%x%x)$")
        if hex then
            part.Color = Color3.fromHex(hex)
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

    -- A part made only of glow pieces (like a sun) is carried by its first piece
    for _, glow in glows do
        if not rig.parts[glow.owner] then
            rig.parts[glow.owner] = glow.part
            glow.carrier = true
        end
    end

    -- Joints at the pivots
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
        else
            warn(string.format("PetRig: %s is missing the part, parent or pivot for %s", petId, tostring(name)))
        end
    end
    for name, ownerName in profile.Attached do
        local part, owner = rig.parts[name], rig.parts[ownerName]
        if part and owner then
            weld(owner, part)
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

    -- The spin axis (from the centre pivot to the axis point) and each ray's hinge
    local axisPoint = profile.Effects.Axis and rig.pointPositions[profile.Effects.Axis]
    local center = profile.RayParent and pivots[profile.RayParent]
    if axisPoint and center then
        rig.axis = (axisPoint - center).Unit
        for name, motor in rig.motors do
            if profile.RayPrefix and string.sub(name, 1, #profile.RayPrefix) == profile.RayPrefix then
                local radial = (pivots[name] - center).Unit
                table.insert(rig.rays, { motor = motor, tangent = rig.axis:Cross(radial).Unit })
            end
        end
    else
        rig.axis = Vector3.new(0, 0, -1)
    end

    local controller = Instance.new("AnimationController")
    controller.Parent = model
    Instance.new("Animator").Parent = controller

    addEffects(rig)
    return rig
end

-- The special ability's blast: a ring of light racing outward, rays and sparks.
local function burst(rig)
    local profile = rig.profile
    local origin = (rig.parts[profile.Effects.Burst] or rig.rootPart).Position
    local colors = profile.Colors
    local u = rig.unit
    local facing = rig.rootPart.CFrame - rig.rootPart.Position

    local folder = Instance.new("Folder")
    folder.Name = "PetSpecial"
    folder.Parent = rig.model.Parent or workspace

    local function neon(size, cframe, color)
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
    end

    -- The expanding ring: segments flying outward in a flat circle
    local ringInfo = TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
    for index = 1, 20 do
        local angle = index / 20 * 2 * math.pi
        local direction = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local start = CFrame.lookAt(origin + direction * 0.8 * u, origin + direction * 2 * u)
        local segment = neon(Vector3.new(0.9 * u, 0.12 * u, 0.25 * u), start, colors.Gold)
        TweenService:Create(segment, ringInfo, {
            CFrame = start + direction * 9 * u,
            Size = Vector3.new(2.2 * u, 0.05 * u, 0.1 * u),
            Transparency = 1,
        }):Play()
    end

    -- Rays bursting out and up
    local rayInfo = TweenInfo.new(0.7, Enum.EasingStyle.Quint, Enum.EasingDirection.Out)
    for index = 1, 10 do
        local angle = index / 10 * 2 * math.pi
        local direction = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0.55, math.sin(angle))).Unit
        local base = CFrame.lookAt(origin, origin + direction)
        local ray = neon(Vector3.new(0.12 * u, 0.12 * u, 0.4 * u), base * CFrame.new(0, 0, -0.4 * u), colors.Sun)
        TweenService:Create(ray, rayInfo, {
            Size = Vector3.new(0.04 * u, 0.04 * u, 5 * u),
            CFrame = base * CFrame.new(0, 0, -2.8 * u),
            Transparency = 1,
        }):Play()
    end

    -- A flash of light and a spray of sparks
    local flash = neon(Vector3.one * 0.6 * u, CFrame.new(origin), colors.Ivory)
    flash.Shape = Enum.PartType.Ball
    TweenService:Create(flash, ringInfo, { Size = Vector3.one * 5 * u, Transparency = 1 }):Play()
    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 16 * u
    light.Brightness = 6
    light.Parent = flash
    TweenService:Create(light, ringInfo, { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(45)
    end

    Debris:AddItem(folder, 1.2)
end

-- Starts the pet's special ability (for Sunscale Dragon, the Solar Nova)
function PetRig.nova(rig)
    if rig.nova == nil then
        rig.nova = { start = rig.state.time, fired = false }
    end
end

-- Poses the rig for this frame. `state`: speed (studs/s the pet moves),
-- flying (its owner is flying).
function PetRig.update(rig, deltaTime, state)
    local s = rig.state
    s.time += deltaTime
    rig.deltaTime = deltaTime
    local blend = math.min(1, deltaTime * 5)
    local walkTarget = if state.flying then 0 else math.clamp(state.speed / (4 * rig.unit), 0, 1)
    s.walk += (walkTarget - s.walk) * blend
    s.fly += ((if state.flying then 1 else 0) - s.fly) * blend

    -- The special ability's envelope (0 when not playing)
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

    -- The glowing heart pulses, and blazes during the special
    local pulse = 0.5 + 0.5 * math.sin(s.time * 2.2)
    if rig.light then
        rig.light.Brightness = 1.1 + 0.8 * pulse + 9 * nova
    end
    for _, glow in rig.pulseGlow do
        glow.part.Color = glow.color:Lerp(Color3.new(1, 1, 1), 0.2 * pulse + 0.7 * nova)
    end

    if rig.trail then
        rig.trail.Enabled = s.fly > 0.5
    end
end

return PetRig

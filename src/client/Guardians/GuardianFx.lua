-- Guardian effects (client-only, cosmetic: the server decides every hit, Guardian.lua): building
-- blocks that each guardian's rig (GuardianRigs/<Id>) composes into its own moves, and the egg's
-- moments, shared by all.
--
-- A style: { Debris = "Dust" | "Leaves" | "Cinders" (dark volcanic ash) | "Frost" (pale frost mist) | "Void" (dark violet
-- chaos), Qi = Color3, QiCore = Color3 }.
--
--   shake(origin, strength, time)              the camera jolts, fading with distance from origin
--   kick(origin, pitch, yaw, time)             the camera is knocked once, by pitch degrees up and yaw degrees left (a blow landing:
--                                              a nod along the way it travelled), and settles back over `time`
--   puff(cframe, style, count, speed, spread, size, life)
--                                              debris thrown out from a point (spread: degrees from
--                                              its up axis, or a Vector2 for a low, wide fan), dust
--                                              billowing or leaves tumbling
--   shed(part, style, count)                   debris falling off a part's whole body
--   flash(cframe, style, size)                 a soft burst of Qi light
--   streaks(cframe, style, count, speed, spread)
--                                              Qi streaks shot out along the cframe's look
--   crescent(cframe, style, size)              a crescent of Qi light (a blade's cut) facing the camera
--   embers(cframe, count, speed, spread, life) glowing embers flung up from a point, falling back
--   wave(origin, facing, radius, speed, arc, style)
--                                              a wall of debris with Qi streaks rolling out along the
--                                              ground, all round (arc >= 180) or within arc degrees of
--                                              facing
--   telegraph(position, time, style)           debris stirring and embers rising where a leap lands
--   cone(model, range, arc, windUp)            the ground a sweep will hit, drawn while it winds up: a wedge of the guardian's reach and
--                                              half-angle (it turns with the guardian), filling in toward the blow, flashing as it lands
--   ring(model, radius, windUp)                the ground a wave that rolls all round will cross: a disc growing to its radius
--   steal / drop / secure (position, style)    the egg taken, dropped, secured
--   beacon(eggModel)                           a pillar of light over a dropped egg, until removed
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local AuraKit = require(script.Parent.Parent:WaitForChild("Auras"):WaitForChild("AuraKit"))

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local GuardianFx = {}

local TEXTURES = {
    Fog = "rbxassetid://14050223758",       -- a soft billowing puff
    Glow = "rbxassetid://135169457468310",
    Streak = "rbxassetid://115312010132075",
    Slash = "rbxassetid://77516609955713",  -- QiSlash (tools/blender/vfx/combat_textures.py)
    Leaf = "rbxassetid://126547188247220",  -- BambooLeaf (combat_textures.py)
}
local DUST = Color3.fromRGB(196, 190, 178)
local DUST_DARK = Color3.fromRGB(142, 136, 126)
local LEAF = Color3.fromRGB(96, 168, 70)
local LEAF_DARK = Color3.fromRGB(40, 104, 46)
local ASH = Color3.fromRGB(92, 82, 76)
local ASH_DARK = Color3.fromRGB(46, 40, 38)
local EMBER = Color3.fromRGB(255, 150, 30)
local FROST = Color3.fromRGB(214, 232, 255)
local FROST_DARK = Color3.fromRGB(150, 178, 225)
local VOID = Color3.fromRGB(70, 34, 110)
local VOID_DARK = Color3.fromRGB(22, 12, 38)
local RAGE = Color3.fromRGB(255, 80, 25)
local GOLD = Color3.fromRGB(255, 196, 70)
local MAX_DISTANCE = 300
local WAVE_SPACING = 7   -- studs between the wave's emitters along its front (at full radius)

local fxFolder = Instance.new("Folder")
fxFolder.Name = "GuardianFx"
fxFolder.Parent = Workspace

local function near(position)
    local camera = Workspace.CurrentCamera
    return camera ~= nil and (camera.CFrame.Position - position).Magnitude <= MAX_DISTANCE
end

local function host(cframe, life)
    local part = Instance.new("Part")
    part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
    part.Transparency = 1
    part.Size = Vector3.new(0.4, 0.4, 0.4)
    part.CFrame = cframe
    part.Parent = fxFolder
    Debris:AddItem(part, life)
    return part
end

local function emitter(parent, properties)
    local e = Instance.new("ParticleEmitter")
    e.Rate = 0
    e.LightInfluence = 0
    e.LightEmission = 1
    for k, v in properties do
        e[k] = v
    end
    e.Parent = parent
    return e
end
GuardianFx.emitter = emitter

local function debris(parent, style, properties)
    local base
    if style.Debris == "Leaves" then
        base = {
            Texture = TEXTURES.Leaf, LightEmission = 0, LightInfluence = 1,
            Color = colorSequence({ { 0, LEAF }, { 1, LEAF_DARK } }),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-220, 220),
            Drag = 2, Acceleration = Vector3.new(0, -6, 0),
        }
    else
        local light, dark = DUST, DUST_DARK
        if style.Debris == "Cinders" then
            light, dark = ASH, ASH_DARK
        elseif style.Debris == "Frost" then
            light, dark = FROST, FROST_DARK
        elseif style.Debris == "Void" then
            light, dark = VOID, VOID_DARK
        end
        base = {
            Texture = TEXTURES.Fog, LightEmission = 0, LightInfluence = 1,
            Color = colorSequence({ { 0, light }, { 1, dark } }),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-25, 25),
            Drag = 2.5,
        }
    end
    for k, v in properties do
        base[k] = v
    end
    return emitter(parent, base)
end

local function debrisSize(style, size)
    if style.Debris == "Leaves" then
        return numberSequence({ { 0, size * 0.35 }, { 1, size * 0.3 } })
    end
    return numberSequence({ { 0, size }, { 1, size * 2.2 } })
end

local function debrisFade(style)
    if style.Debris == "Leaves" then
        return numberSequence({ { 0, 0 }, { 0.75, 0.1 }, { 1, 1 } })
    end
    return numberSequence({ { 0, 0.35 }, { 1, 1 } })
end

-- ---------- the camera ----------
-- The shake turns the camera after the camera scripts have placed it. They read the camera's look
-- back the next frame, so each frame's turn is undone before they run, or the aim would drift.
local shaking = {}
local kicks = {}
local lastShake = nil
RunService:BindToRenderStep("GuardianShakeUndo", Enum.RenderPriority.Camera.Value - 1, function()
    local camera = Workspace.CurrentCamera
    if camera and lastShake then
        camera.CFrame *= lastShake:Inverse()
    end
    lastShake = nil
end)
RunService:BindToRenderStep("GuardianShake", Enum.RenderPriority.Camera.Value + 1, function()
    local camera = Workspace.CurrentCamera
    if not camera or (#shaking == 0 and #kicks == 0) then
        return
    end
    local now = os.clock()
    local amount = 0
    local pitch, yaw = 0, 0
    for i = #kicks, 1, -1 do
        local k = kicks[i]
        local t = now - k.start
        if t >= k.time then
            table.remove(kicks, i)
        else
            local c = math.min(t / 0.015, 1) * (1 - t / k.time) ^ 2
            pitch += k.pitch * c
            yaw += k.yaw * c
        end
    end
    for i = #shaking, 1, -1 do
        local s = shaking[i]
        local t = (now - s.start) / s.time
        if t >= 1 then
            table.remove(shaking, i)
        else
            amount += s.strength * (1 - t) ^ 2
        end
    end
    if amount > 0 or pitch ~= 0 or yaw ~= 0 then
        local a = math.rad(amount)
        lastShake = CFrame.Angles(a * math.noise(now * 18, 1) + math.rad(pitch), a * math.noise(now * 18, 2) + math.rad(yaw),
            a * 0.5 * math.noise(now * 18, 3))
        camera.CFrame *= lastShake
    end
end)

function GuardianFx.shake(origin, strength, time)
    local camera = Workspace.CurrentCamera
    if not camera or Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true then
        return
    end
    local distance = (camera.CFrame.Position - origin).Magnitude
    local falloff = math.clamp(1 - (distance - 20) / 90, 0, 1)
    if falloff > 0 then
        table.insert(shaking, { start = os.clock(), time = time, strength = strength * falloff })
    end
end

function GuardianFx.kick(origin, pitch, yaw, time)
    local camera = Workspace.CurrentCamera
    if not camera or Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true then
        return
    end
    local distance = (camera.CFrame.Position - origin).Magnitude
    local falloff = math.clamp(1 - (distance - 20) / 90, 0, 1)
    if falloff > 0 then
        if #kicks >= 6 then
            table.remove(kicks, 1)
        end
        table.insert(kicks, { start = os.clock(), time = time, pitch = pitch * falloff, yaw = yaw * falloff })
    end
end

-- ---------- building blocks ----------
function GuardianFx.puff(cframe, style, count, speed, spread, size, life)
    if not near(cframe.Position) then
        return
    end
    local holder = host(cframe, (life or 1) + 1)
    debris(holder, style, {
        Lifetime = NumberRange.new((life or 1) * 0.7, life or 1), Speed = NumberRange.new(speed * 0.65, speed),
        SpreadAngle = if typeof(spread) == "Vector2" then spread else Vector2.new(spread, spread), EmissionDirection = Enum.NormalId.Top,
        Size = debrisSize(style, size), Transparency = debrisFade(style),
    }):Emit(count)
end

function GuardianFx.shed(part, style, count)
    if not (part and near(part.Position)) then
        return
    end
    local e = debris(part, style, {
        Lifetime = NumberRange.new(1, 1.6), Speed = NumberRange.new(1, 4), SpreadAngle = Vector2.new(180, 180),
        Acceleration = Vector3.new(0, if style.Debris == "Leaves" then -5 else -9, 0),
        Size = debrisSize(style, 2.5), Transparency = numberSequence({ { 0, 0.5 }, { 0.3, 0.4 }, { 1, 1 } }),
    })
    task.delay(0.15, function()
        e:Emit(count)
    end)
    Debris:AddItem(e, 2)
end

function GuardianFx.flash(cframe, style, size)
    if not near(cframe.Position) then
        return
    end
    emitter(host(cframe, 1), {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.3),
        Size = numberSequence({ { 0, size * 0.4 }, { 1, size } }), Transparency = numberSequence({ { 0, 0.4 }, { 1, 1 } }),
        Color = colorSequence({ { 0, style.QiCore }, { 1, style.Qi } }), Brightness = 1.6,
    }):Emit(1)
end

function GuardianFx.streaks(cframe, style, count, speed, spread)
    if not near(cframe.Position) then
        return
    end
    emitter(host(cframe, 1), {
        Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
        Speed = NumberRange.new(speed * 0.7, speed), SpreadAngle = Vector2.new(spread, spread * 0.7), Lifetime = NumberRange.new(0.25, 0.4),
        Size = numberSequence({ { 0, 2.2 }, { 1, 0.5 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, style.QiCore }, { 1, style.Qi } }), Brightness = 2,
    }):Emit(count)
end

function GuardianFx.crescent(cframe, style, size)
    if not near(cframe.Position) then
        return
    end
    emitter(host(cframe, 1), {
        Texture = TEXTURES.Slash, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.28), Rotation = NumberRange.new(-20, 20),
        Size = numberSequence({ { 0, size * 0.6 }, { 1, size } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = colorSequence({ { 0, style.QiCore }, { 1, style.Qi } }), Brightness = 2.2,
    }):Emit(1)
end

function GuardianFx.embers(cframe, count, speed, spread, life)
    if not near(cframe.Position) then
        return
    end
    life = life or 1.4
    emitter(host(cframe, life + 0.5), {
        Texture = TEXTURES.Glow, EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(spread, spread),
        Speed = NumberRange.new(speed * 0.5, speed), Lifetime = NumberRange.new(life * 0.6, life), Drag = 0.6,
        Acceleration = Vector3.new(0, -speed * 0.9, 0),
        Size = numberSequence({ { 0, 0.7 }, { 0.7, 0.45 }, { 1, 0 } }), Transparency = numberSequence({ { 0, 0 }, { 0.8, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, EMBER }, { 1, RAGE } }), Brightness = 2.4,
    }):Emit(count)
end

function GuardianFx.wave(origin, facing, radius, speed, arc, style)
    if not near(origin) then
        return
    end
    local life = radius / speed
    local centre = host(CFrame.new(origin), life + 1.5)
    local half = math.rad(math.min(arc, 180))
    local count = math.max(5, math.floor(2 * half * radius / WAVE_SPACING))
    local base = math.atan2(facing.Z, facing.X)
    local points = {}
    for i = 1, count do
        local a = Instance.new("Attachment")
        a.Parent = centre
        local puff = debris(a, style, {
            Lifetime = NumberRange.new(0.5, 0.8), Speed = NumberRange.new(3, 7), SpreadAngle = Vector2.new(25, 25),
            EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, if style.Debris == "Leaves" then -3 else 2, 0),
            Size = debrisSize(style, 4), Transparency = debrisFade(style),
        })
        local streak = emitter(a, {
            Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
            Speed = NumberRange.new(speed * 0.9, speed * 1.1), SpreadAngle = Vector2.new(6, 4), Lifetime = NumberRange.new(0.25),
            Size = numberSequence({ { 0, 1.6 }, { 1, 0.4 } }), Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
            Color = colorSequence({ { 0, style.QiCore }, { 1, style.Qi } }), Brightness = 1.6,
        })
        local angle = if arc >= 180 then (i - 1) / count * 2 * math.pi else base - half + 2 * half * (i - 0.5) / count
        points[i] = { attachment = a, puff = puff, streak = streak, angle = angle }
    end
    local start = os.clock()
    local connection
    connection = RunService.Heartbeat:Connect(function()
        local r = (os.clock() - start) * speed
        if r > radius or not centre.Parent then
            connection:Disconnect()
            return
        end
        for i, point in points do
            local outward = Vector3.new(math.cos(point.angle), 0, math.sin(point.angle))
            local position = outward * r + Vector3.new(0, 0.6, 0)
            point.attachment.CFrame = CFrame.lookAt(position, position + outward)
            -- alternate points each frame: a steady wall, half the particles
            if (i + math.floor(r)) % 2 == 0 then
                point.puff:Emit(1)
                point.streak:Emit(1)
            end
        end
    end)
end

function GuardianFx.telegraph(position, time, style)
    if not near(position) then
        return
    end
    local holder = host(CFrame.new(position + Vector3.new(0, 0.3, 0)), time + 1)
    local stir = debris(holder, style, {
        Rate = if style.Debris == "Leaves" then 18 else 26, Lifetime = NumberRange.new(0.5, 0.8), Speed = NumberRange.new(4, 8),
        SpreadAngle = Vector2.new(90, 10), EmissionDirection = Enum.NormalId.Top,
        Size = debrisSize(style, 2), Transparency = numberSequence({ { 0, 0.55 }, { 1, 1 } }),
    })
    local embers = emitter(holder, {
        Texture = TEXTURES.Glow, Rate = 16, Lifetime = NumberRange.new(0.6, 0.9), Speed = NumberRange.new(3, 6),
        SpreadAngle = Vector2.new(60, 60), EmissionDirection = Enum.NormalId.Top,
        Size = numberSequence({ { 0, 0.9 }, { 1, 0 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, GOLD }, { 1, RAGE } }), Brightness = 2,
    })
    task.delay(time, function()
        stir.Enabled = false
        embers.Enabled = false
    end)
end

-- ---------- what an attack will hit ----------
local DANGER = Color3.fromRGB(255, 72, 36)
local GROUND_LIFT = 0.18

local function groundPiece(size, shape)
    local part = Instance.new("Part")
    part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
    part.Material = Enum.Material.Neon
    part.Color = DANGER
    part.Transparency = 1
    part.Size = size
    if shape then
        part.Shape = shape
    end
    return part
end

-- The ground under a guardian: its pivot is its ground (GuardianAnim), a little lifted so the light clears the turf.
local function groundOf(model)
    local pivot = model:GetPivot()
    return Vector3.new(pivot.X, pivot.Y + GROUND_LIFT, pivot.Z)
end

local function facingOf(model)
    local look = model:GetPivot().LookVector * Vector3.new(1, 0, 1)
    return if look.Magnitude > 1e-3 then look.Unit else Vector3.new(0, 0, -1)
end

-- One flat triangle (a, b, c) laid from two wedges, into `parent`. A triangle's longest side is split by the foot of its
-- opposite corner's height: each wedge is the right triangle on one side of that foot.
local function triangle(a, b, c, parent, thickness, color)
    local ab, ac, bc = b - a, c - a, c - b
    local abd, acd, bcd = ab:Dot(ab), ac:Dot(ac), bc:Dot(bc)
    if abd > acd and abd > bcd then
        c, a = a, c
    elseif acd > bcd and acd > abd then
        a, b = b, a
    end
    ab, ac, bc = b - a, c - a, c - b
    local right = ac:Cross(ab).Unit
    local up = bc:Cross(right).Unit
    local back = bc.Unit
    local height = math.abs(ab:Dot(up))
    local pieces = {}
    for i, spec in { { (a + b) / 2, ab, right, back }, { (a + c) / 2, ac, -right, -back } } do
        local wedge = Instance.new("WedgePart")
        wedge.Anchored, wedge.CanCollide, wedge.CanQuery, wedge.CanTouch, wedge.CastShadow = true, false, false, false, false
        wedge.Material = Enum.Material.Neon
        wedge.Color = color
        wedge.Transparency = 1
        wedge.Size = Vector3.new(thickness, math.max(height, 0.05), math.max(math.abs(spec[2]:Dot(back)), 0.05))
        wedge.CFrame = CFrame.fromMatrix(spec[1], spec[3], up, spec[4])
        wedge.Parent = parent
        pieces[i] = wedge
    end
    return pieces
end

-- Fades a ground marking in over the wind-up, flashes it at the blow and fades it out: `parts` are the marking's pieces.
local function fillAndFlash(parts, windUp, from, to)
    local TweenService = game:GetService("TweenService")
    for _, part in parts do
        part.Transparency = from
        TweenService:Create(part, TweenInfo.new(windUp, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = to }):Play()
        task.delay(windUp, function()
            if part.Parent then
                part.Transparency = 0.25
                TweenService:Create(part, TweenInfo.new(0.22, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 1 }):Play()
            end
        end)
    end
end

function GuardianFx.cone(model, range, arc, windUp)
    local root = model.PrimaryPart
    if not (root and near(root.Position)) then
        return
    end
    local holder = Instance.new("Model")
    holder.Name = "SweepWarning"
    local parts = {}
    -- the wedge in the guardian's frame: its apex at the origin, ahead along -Z, half-angle `arc` each way
    local slices = math.max(2, math.ceil(arc * 2 / 22))
    local apex = Vector3.zero
    for i = 1, slices do
        local a0 = math.rad(-arc + 2 * arc * (i - 1) / slices)
        local a1 = math.rad(-arc + 2 * arc * i / slices)
        local p0 = Vector3.new(math.sin(a0) * range, 0, -math.cos(a0) * range)
        local p1 = Vector3.new(math.sin(a1) * range, 0, -math.cos(a1) * range)
        for _, piece in triangle(apex, p0, p1, holder, 0.1, DANGER) do
            table.insert(parts, piece)
        end
    end
    local frame = CFrame.lookAt(groundOf(model), groundOf(model) + facingOf(model))
    holder:PivotTo(frame)
    holder.Parent = fxFolder
    fillAndFlash(parts, windUp, 0.9, 0.62)
    -- it turns with the guardian until the blow, where the server judges the sweep
    local connection
    connection = RunService.Heartbeat:Connect(function()
        if not (holder.Parent and model.Parent) then
            connection:Disconnect()
            return
        end
        local ground = groundOf(model)
        holder:PivotTo(CFrame.lookAt(ground, ground + facingOf(model)))
    end)
    task.delay(windUp, function()
        connection:Disconnect()
    end)
    Debris:AddItem(holder, windUp + 0.4)
end

function GuardianFx.ring(model, radius, windUp)
    local root = model.PrimaryPart
    if not (root and near(root.Position)) then
        return
    end
    local TweenService = game:GetService("TweenService")
    -- a Cylinder's axis is its X: laid on its side it is a flat disc
    local disc = groundPiece(Vector3.new(0.1, 4, 4), Enum.PartType.Cylinder)
    local ground = groundOf(model)
    disc.CFrame = CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2)
    disc.Parent = fxFolder
    disc.Transparency = 0.88
    TweenService:Create(disc, TweenInfo.new(windUp, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        { Size = Vector3.new(0.1, radius * 2, radius * 2), Transparency = 0.78 }):Play()
    task.delay(windUp, function()
        if disc.Parent then
            disc.Transparency = 0.4
            TweenService:Create(disc, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 1 }):Play()
        end
    end)
    Debris:AddItem(disc, windUp + 0.5)
end

-- ---------- the egg ----------
function GuardianFx.steal(position, style)
    GuardianFx.flash(CFrame.new(position), style, 12)
    if not near(position) then
        return
    end
    emitter(host(CFrame.new(position), 1.5), {
        Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, SpreadAngle = Vector2.new(180, 180),
        Speed = NumberRange.new(18, 30), Drag = 3, Lifetime = NumberRange.new(0.3, 0.45),
        Size = numberSequence({ { 0, 1.4 }, { 1, 0.2 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, style.QiCore }, { 1, style.Qi } }), Brightness = 2.2,
    }):Emit(16)
end

function GuardianFx.drop(position, style)
    GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.4, 0)), style, 14, 14, Vector2.new(180, 8), 2, 0.9)
end

function GuardianFx.secure(position)
    if not near(position) then
        return
    end
    local holder = host(CFrame.new(position), 3)
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.6),
        Size = numberSequence({ { 0, 4 }, { 1, 14 } }), Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
        Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 1, GOLD } }), Brightness = 2,
    }):Emit(1)
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(4, 9), SpreadAngle = Vector2.new(35, 35),
        EmissionDirection = Enum.NormalId.Top, Lifetime = NumberRange.new(1.2, 2), Acceleration = Vector3.new(0, 3, 0),
        Size = numberSequence({ { 0, 0.8 }, { 1, 0 } }), Transparency = numberSequence({ { 0, 0.1 }, { 1, 1 } }),
        Color = colorSequence({ { 0, Color3.new(1, 1, 1) }, { 1, GOLD } }), Brightness = 2.4,
    }):Emit(30)
end

-- A soft pillar of light standing over a dropped egg, seen from across the island. Returns the
-- beam's holder: destroy it when the egg is picked up.
function GuardianFx.beacon(eggModel)
    local body = eggModel.PrimaryPart
    if not body then
        return nil -- (not streamed in yet: no beacon, rather than an error)
    end
    local holder = Instance.new("Part")
    holder.Anchored, holder.CanCollide, holder.CanQuery, holder.CanTouch, holder.CastShadow = true, false, false, false, false
    holder.Transparency = 1
    holder.Size = Vector3.new(0.4, 0.4, 0.4)
    holder.CFrame = CFrame.new(body.Position)
    local bottom, top = Instance.new("Attachment"), Instance.new("Attachment")
    top.Position = Vector3.new(0, 46, 0)
    bottom.Parent, top.Parent = holder, holder
    local beam = Instance.new("Beam")
    beam.Attachment0, beam.Attachment1 = bottom, top
    beam.Texture = TEXTURES.Glow
    beam.TextureMode = Enum.TextureMode.Stretch
    beam.FaceCamera = true
    beam.LightEmission = 1
    beam.LightInfluence = 0
    beam.Width0, beam.Width1 = 3, 1.2
    beam.Color = colorSequence({ { 0, Color3.fromRGB(150, 210, 255) }, { 1, Color3.fromRGB(0, 110, 255) } })
    beam.Transparency = numberSequence({ { 0, 0.25 }, { 0.6, 0.6 }, { 1, 1 } })
    beam.Parent = holder
    holder.Parent = fxFolder
    return holder
end

return GuardianFx

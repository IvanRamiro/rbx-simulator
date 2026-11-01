-- Guardian effects (client-only, cosmetic: the server decides every hit, Guardian.lua). Stone dust
-- and the guardian's Qi, never flat rings: what moves along the ground is a rolling wall of dust.
--
--   awaken(model)                       dust shaken off the stone as it wakes
--   slam(model, windUp)                 the left paw hits the ground: a dust burst and a jolt
--   roar(model, windUp, radius, speed)  a blast of Qi from the jaws, then a wall of dust rolling
--                                       out along the ground to `radius` (jump it)
--   pounce(model, windUp, air, to)      dust stirring where it will land, until it does
--   land(position)                      a heavy landing: dust thrown out low, and a jolt
--   steal / drop / secure (position)    the egg taken (a flare of Qi), dropped (a thud of dust),
--                                       secured (gold light rising)
--   beacon(eggModel)                    a soft pillar of light over a dropped egg, until removed
--   shake(origin, strength, time)       the camera jolts, fading with distance from origin
local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local AuraKit = require(script.Parent:WaitForChild("AuraKit"))

local numberSequence = AuraKit.numberSequence
local colorSequence = AuraKit.colorSequence

local GuardianFx = {}

local TEXTURES = {
    Fog = "rbxassetid://14050223758",       -- a soft billowing puff
    Glow = "rbxassetid://135169457468310",
    Streak = "rbxassetid://115312010132075",
}
local DUST = Color3.fromRGB(196, 190, 178)
local DUST_DARK = Color3.fromRGB(142, 136, 126)
local QI = Color3.fromRGB(0, 110, 255)
local QI_CORE = Color3.fromRGB(150, 210, 255)
local RAGE = Color3.fromRGB(255, 80, 25)
local GOLD = Color3.fromRGB(255, 196, 70)
local MAX_DISTANCE = 300
local WAVE_POINTS = 18

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

-- billowing stone dust, lit by the sun
local function dust(parent, properties)
    local base = {
        Texture = TEXTURES.Fog, LightEmission = 0, LightInfluence = 1,
        Color = colorSequence({ { 0, DUST }, { 1, DUST_DARK } }),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-25, 25),
        Drag = 2.5,
    }
    for k, v in properties do
        base[k] = v
    end
    return emitter(parent, base)
end

-- ---------- the camera ----------
local shaking = {}
RunService:BindToRenderStep("GuardianShake", Enum.RenderPriority.Camera.Value + 1, function()
    local camera = Workspace.CurrentCamera
    if not camera or #shaking == 0 then
        return
    end
    local now = os.clock()
    local amount = 0
    for i = #shaking, 1, -1 do
        local s = shaking[i]
        local t = (now - s.start) / s.time
        if t >= 1 then
            table.remove(shaking, i)
        else
            amount += s.strength * (1 - t) ^ 2
        end
    end
    if amount > 0 then
        local a = math.rad(amount)
        camera.CFrame *= CFrame.Angles(a * math.noise(now * 18, 1), a * math.noise(now * 18, 2), a * 0.5 * math.noise(now * 18, 3))
    end
end)

function GuardianFx.shake(origin, strength, time)
    local camera = Workspace.CurrentCamera
    if not camera then
        return
    end
    local distance = (camera.CFrame.Position - origin).Magnitude
    local falloff = math.clamp(1 - (distance - 20) / 90, 0, 1)
    if falloff > 0 then
        table.insert(shaking, { start = os.clock(), time = time, strength = strength * falloff })
    end
end

-- ---------- the guardian ----------
function GuardianFx.awaken(model)
    local body = model:FindFirstChild("Body")
    if not (body and near(body.Position)) then
        return
    end
    -- dust shaken from the whole body, falling
    local e = dust(body, {
        Lifetime = NumberRange.new(1, 1.6), Speed = NumberRange.new(1, 4), SpreadAngle = Vector2.new(180, 180),
        Acceleration = Vector3.new(0, -9, 0), Size = numberSequence({ { 0, 2.5 }, { 1, 5 } }),
        Transparency = numberSequence({ { 0, 0.55 }, { 0.3, 0.45 }, { 1, 1 } }),
    })
    task.delay(0.15, function()
        e:Emit(30)
    end)
    Debris:AddItem(e, 2)
    GuardianFx.shake(body.Position, 1.2, 0.7)
end

-- where the left paw comes down: in front of the left shoulder (lion-local)
local SLAM_SPOT = CFrame.new(-4.6, 0.3, -17)

function GuardianFx.slam(model, windUp)
    task.delay(windUp, function()
        local root = model.PrimaryPart
        if not (root and model.Parent) then
            return
        end
        local at = model:GetPivot() * SLAM_SPOT
        if not near(at.Position) then
            return
        end
        local holder = host(at, 2)
        dust(holder, {
            Lifetime = NumberRange.new(0.6, 1), Speed = NumberRange.new(14, 22), SpreadAngle = Vector2.new(80, 8),
            EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, 3, 0),
            Size = numberSequence({ { 0, 3 }, { 1, 7 } }), Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
        }):Emit(22)
        emitter(holder, {
            Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.25),
            Size = numberSequence({ { 0, 4 }, { 1, 10 } }), Transparency = numberSequence({ { 0, 0.4 }, { 1, 1 } }),
            Color = colorSequence({ { 0, QI_CORE }, { 1, QI } }), Brightness = 1.6,
        }):Emit(1)
        GuardianFx.shake(at.Position, 1.6, 0.45)
    end)
end

-- the jaws (lion-local): a little ahead of the head
local MOUTH = CFrame.new(0, 21.5, -21)

function GuardianFx.roar(model, windUp, radius, speed)
    task.delay(windUp, function()
        if not model.Parent then
            return
        end
        local pivot = model:GetPivot()
        local origin = pivot.Position
        if not near(origin) then
            return
        end
        -- a blast of Qi from the jaws, thrown forward
        local mouth = host(pivot * MOUTH, 1.5)
        emitter(mouth, {
            Texture = TEXTURES.Glow, EmissionDirection = Enum.NormalId.Front, Speed = NumberRange.new(10, 16),
            SpreadAngle = Vector2.new(20, 20), Lifetime = NumberRange.new(0.5, 0.7), Drag = 3,
            Size = numberSequence({ { 0, 4 }, { 1, 14 } }), Transparency = numberSequence({ { 0, 0.55 }, { 1, 1 } }),
            Color = colorSequence({ { 0, QI_CORE }, { 1, QI } }), Brightness = 1.4,
        }):Emit(6)
        emitter(mouth, {
            Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
            Speed = NumberRange.new(40, 60), SpreadAngle = Vector2.new(35, 25), Lifetime = NumberRange.new(0.25, 0.4),
            Size = numberSequence({ { 0, 2.2 }, { 1, 0.5 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
            Color = colorSequence({ { 0, QI_CORE }, { 1, QI } }), Brightness = 2,
        }):Emit(14)
        GuardianFx.shake(origin, 2.2, 0.9)

        -- the wall of dust rolling out along the ground
        local life = radius / speed
        local centre = host(CFrame.new(origin), life + 1.5)
        local points = {}
        for i = 1, WAVE_POINTS do
            local a = Instance.new("Attachment")
            a.Parent = centre
            local puff = dust(a, {
                Lifetime = NumberRange.new(0.5, 0.8), Speed = NumberRange.new(3, 7), SpreadAngle = Vector2.new(25, 25),
                EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, 2, 0),
                Size = numberSequence({ { 0, 4 }, { 1, 8 } }), Transparency = numberSequence({ { 0, 0.4 }, { 1, 1 } }),
            })
            local streak = emitter(a, {
                Texture = TEXTURES.Streak, EmissionDirection = Enum.NormalId.Front, Orientation = Enum.ParticleOrientation.VelocityParallel,
                Speed = NumberRange.new(speed * 0.9, speed * 1.1), SpreadAngle = Vector2.new(6, 4), Lifetime = NumberRange.new(0.25),
                Size = numberSequence({ { 0, 1.6 }, { 1, 0.4 } }), Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
                Color = colorSequence({ { 0, QI_CORE }, { 1, QI } }), Brightness = 1.6,
            })
            points[i] = { attachment = a, puff = puff, streak = streak, angle = (i - 1) / WAVE_POINTS * 2 * math.pi }
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
    end)
end

function GuardianFx.pounce(model, windUp, air, to)
    if not near(to) then
        return
    end
    -- dust stirring and embers of rage where it will come down
    local holder = host(CFrame.new(to + Vector3.new(0, 0.3, 0)), windUp + air + 1)
    local stir = dust(holder, {
        Rate = 26, Lifetime = NumberRange.new(0.5, 0.8), Speed = NumberRange.new(4, 8), SpreadAngle = Vector2.new(90, 10),
        EmissionDirection = Enum.NormalId.Top, Size = numberSequence({ { 0, 2 }, { 1, 5 } }),
        Transparency = numberSequence({ { 0, 0.55 }, { 1, 1 } }),
    })
    local embers = emitter(holder, {
        Texture = TEXTURES.Glow, Rate = 16, Lifetime = NumberRange.new(0.6, 0.9), Speed = NumberRange.new(3, 6),
        SpreadAngle = Vector2.new(60, 60), EmissionDirection = Enum.NormalId.Top,
        Size = numberSequence({ { 0, 0.9 }, { 1, 0 } }), Transparency = numberSequence({ { 0, 0.2 }, { 1, 1 } }),
        Color = colorSequence({ { 0, GOLD }, { 1, RAGE } }), Brightness = 2,
    })
    task.delay(windUp + air, function()
        stir.Enabled = false
        embers.Enabled = false
    end)
end

function GuardianFx.land(position)
    if not near(position) then
        return
    end
    local holder = host(CFrame.new(position + Vector3.new(0, 0.5, 0)), 2.5)
    dust(holder, {
        Lifetime = NumberRange.new(0.8, 1.3), Speed = NumberRange.new(22, 34), SpreadAngle = Vector2.new(180, 6),
        EmissionDirection = Enum.NormalId.Top, Drag = 3.5, Acceleration = Vector3.new(0, 2, 0),
        Size = numberSequence({ { 0, 4 }, { 1, 10 } }), Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }),
    }):Emit(36)
    GuardianFx.shake(position, 3, 0.7)
end

-- ---------- the egg ----------
function GuardianFx.steal(position)
    if not near(position) then
        return
    end
    local holder = host(CFrame.new(position), 1.5)
    emitter(holder, {
        Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.4),
        Size = numberSequence({ { 0, 3 }, { 1, 12 } }), Transparency = numberSequence({ { 0, 0.3 }, { 1, 1 } }),
        Color = colorSequence({ { 0, QI_CORE }, { 1, QI } }), Brightness = 2.2,
    }):Emit(1)
    emitter(holder, {
        Texture = TEXTURES.Streak, Orientation = Enum.ParticleOrientation.VelocityParallel, SpreadAngle = Vector2.new(180, 180),
        Speed = NumberRange.new(18, 30), Drag = 3, Lifetime = NumberRange.new(0.3, 0.45),
        Size = numberSequence({ { 0, 1.4 }, { 1, 0.2 } }), Transparency = numberSequence({ { 0, 0 }, { 1, 1 } }),
        Color = colorSequence({ { 0, QI_CORE }, { 1, QI } }), Brightness = 2.2,
    }):Emit(16)
end

function GuardianFx.drop(position)
    if not near(position) then
        return
    end
    local holder = host(CFrame.new(position + Vector3.new(0, 0.4, 0)), 1.8)
    dust(holder, {
        Lifetime = NumberRange.new(0.6, 0.9), Speed = NumberRange.new(8, 14), SpreadAngle = Vector2.new(180, 8),
        EmissionDirection = Enum.NormalId.Top, Size = numberSequence({ { 0, 2 }, { 1, 5 } }),
        Transparency = numberSequence({ { 0, 0.35 }, { 1, 1 } }),
    }):Emit(14)
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
    beam.Color = colorSequence({ { 0, QI_CORE }, { 1, QI } })
    beam.Transparency = numberSequence({ { 0, 0.25 }, { 0.6, 0.6 }, { 1, 1 } })
    beam.Parent = holder
    holder.Parent = fxFolder
    return holder
end

return GuardianFx

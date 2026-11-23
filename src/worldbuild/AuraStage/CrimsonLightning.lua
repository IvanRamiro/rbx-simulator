-- CRIMSON LIGHTNING: a candidate replacement for Realm 7's (Divine) unique feature (the owner, 2026-11-23: "I want mine to stay consistent in the loop, like very visible like my base
-- aura ... I have a realm with red and black aura, so maybe you can replace the current unique feature to use that black and red lightning"). NOT in the game: dev-stage code
-- (ServerStorage.WorldBuild.AuraStage, copied into ServerStorage.DevStage.AuraCrimsonLightning), shown beside the current Realm 7 for comparison.
--
-- It is a LOOP, like the base aura: no cinematic events, nothing that comes and goes. About a dozen jagged bolts are alive round the body at every moment, each a black body with a
-- thin hot-red heart, and each re-forms in a new shape and direction a moment after it fades, so the body is always wrapped in a crackling corona that never settles into one look.
--   * corona: most bolts leave the chest in every direction, 6 to 12 studs long (sharp, forking now and then)
--   * floor: some run out along the ground from the feet
--   * high: some climb up past the head
--   * sparks thrown out in all directions, and a red light that flickers with the crackle
-- The current piece is a 6-stud sphere of bolts 1.2 studs long that live a tenth of a second: it is hard to see; these are 5 to 10 times longer and thicker and last a third of a second.
-- Cost (one aura, full quality): 14 bolts of two trails each (28 trails), 1 emitter, 1 light, about 17 invisible anchored parts. Reduced Effects: 5 bolts, no flicker. Phone (Low): 8 bolts.
--
--   local handle = CrimsonLightning.start(rootPart, { Reduced = false, Low = false, Speed = 1, Scale = 1, Thickness = 1 })
--   handle.destroy()
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local TEX = {
    SoftGlow = "rbxassetid://243664672",   -- a soft round glow (PDS kit): across a trail, a bright heart fading to nothing at the edges
    Spark = "rbxassetid://9997556038",     -- a small round spark (the base aura's BodySpark)
}
local BLACK = Color3.fromRGB(8, 0, 4)
local RED = Color3.fromRGB(235, 20, 40)
local HOT = Color3.fromRGB(255, 132, 108)

local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end
local function rand(a, b)
    return a + (b - a) * math.random()
end
local function direction(azimuth, elevation)
    local c = math.cos(elevation)
    return Vector3.new(math.cos(azimuth) * c, math.sin(elevation), math.sin(azimuth) * c)
end

-- a jagged path from an origin along a direction
local function boltPath(origin, dir, length, steps, jitter)
    local side = dir:Cross(Vector3.yAxis)
    if side.Magnitude < 0.1 then
        side = Vector3.xAxis
    end
    side = side.Unit
    local side2 = dir:Cross(side).Unit
    local pts = { origin }
    for k = 1, steps do
        local f = k / steps
        local p = origin + dir * (length * f)
        local j = jitter * length * (1 - 0.35 * f)
        if k < steps then
            p += side * ((math.random() - 0.5) * 2 * j) + side2 * ((math.random() - 0.5) * 2 * j)
        else
            p += side * ((math.random() - 0.5) * j)
        end
        table.insert(pts, p)
    end
    return pts
end

local CrimsonLightning = {}

function CrimsonLightning.start(root, options)
    options = options or {}
    local reduced = options.Reduced == true
    local low = options.Low == true
    local speed = options.Speed or 1
    local scale = options.Scale or 1
    local thick = options.Thickness or 1
    local BOLTS = if reduced then 5 elseif low then 8 else 14

    local folder = Instance.new("Folder")
    folder.Name = "CrimsonLightning"
    local function speck(name)
        local part = Instance.new("Part")
        part.Name = name
        part.Size = Vector3.new(0.2, 0.2, 0.2)
        part.Transparency = 1
        part.Anchored = true
        part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
        part.CastShadow = false
        part.CFrame = CFrame.new(root.Position)
        part.Parent = folder
        return part
    end
    local function attachment(name, parent, position)
        local a = Instance.new("Attachment")
        a.Name = name
        a.Position = position or Vector3.zero
        a.Parent = parent
        return a
    end

    local center = speck("Center")
    local chest = attachment("Chest", center, Vector3.new(0, 0.6, 0))
    -- sparks thrown out in all directions
    local sparks = Instance.new("ParticleEmitter")
    sparks.Name = "LightningSparks"
    sparks.Texture = TEX.Spark
    sparks.Color = ColorSequence.new(HOT, RED)
    sparks.LightEmission = 1
    sparks.LightInfluence = 0
    sparks.Size = seq({ { 0, 0.55 * thick }, { 1, 0 } })
    sparks.Transparency = seq({ { 0, 0 }, { 0.7, 0.3 }, { 1, 1 } })
    sparks.Lifetime = NumberRange.new(0.2, 0.4)
    sparks.Speed = NumberRange.new(10 * scale, 24 * scale)
    sparks.SpreadAngle = Vector2.new(180, 180)
    sparks.Drag = 2
    sparks.Rate = (if reduced then 10 elseif low then 18 else 30)
    sparks.Parent = chest

    local light = Instance.new("PointLight")
    light.Color = RED
    light.Range = 18 * scale
    light.Brightness = 1.2
    light.Shadows = false
    light.Parent = center

    -- the bolts: a head part walked along a jagged path, a black body trail and a red heart trail behind it
    local function makeBolt()
        local head = speck("BoltHead")
        local a0 = attachment("A0", head, Vector3.new(0, 0.5, 0))
        local a1 = attachment("A1", head, Vector3.new(0, -0.5, 0))
        local life = 0.26 / speed
        local body = Instance.new("Trail")
        body.Name = "Body"
        body.Attachment0, body.Attachment1 = a0, a1
        body.Color = ColorSequence.new(BLACK)
        body.LightEmission, body.LightInfluence = 0, 0
        body.Lifetime = life
        body.FaceCamera = true
        body.MinLength = 0.05
        body.Transparency = seq({ { 0, 0.0 }, { 0.65, 0.05 }, { 1, 1 } })
        body.WidthScale = seq({ { 0, 0.5 * thick }, { 1, 0.2 * thick } })
        body.Enabled = false
        body.Parent = head
        local heart = Instance.new("Trail")
        heart.Name = "Heart"
        heart.Attachment0, heart.Attachment1 = a0, a1
        heart.Color = ColorSequence.new(Color3.fromRGB(255, 205, 175), Color3.fromRGB(255, 70, 60))
        heart.Brightness = 2.5
        heart.LightEmission, heart.LightInfluence = 1, 0
        heart.Lifetime = life
        heart.FaceCamera = true
        heart.MinLength = 0.05
        heart.Transparency = seq({ { 0, 0 }, { 0.6, 0.1 }, { 1, 1 } })
        heart.WidthScale = seq({ { 0, 0.2 * thick }, { 1, 0.08 * thick } })
        heart.Enabled = false
        heart.Parent = head
        return { head = head, body = body, heart = heart, active = false, pts = nil, n = 0, t = 0, dur = 0.1, nextFire = math.random() * 0.4 }
    end
    local bolts = {}
    for _ = 1, BOLTS do
        table.insert(bolts, makeBolt())
    end

    folder.Parent = Workspace

    local clock = 0
    local groundY = root.Position.Y - 3
    local nextGround = 0
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = { folder, root.Parent }

    local function fire(bolt, pts, duration)
        bolt.pts, bolt.n, bolt.t, bolt.dur, bolt.active = pts, #pts, 0, duration, true
        bolt.head.CFrame = CFrame.new(pts[1])
        bolt.body.Enabled = true
        bolt.heart.Enabled = true
    end

    local function newBolt(bolt)
        local base = center.Position
        local kind = math.random()
        local pts
        if kind < 0.3 then -- the skin: short arcs that crawl over the body
            local at = base + Vector3.new(rand(-0.9, 0.9), rand(-1.6, 1.8), rand(-0.6, 0.6))
            local dir = direction(rand(0, math.pi * 2), rand(-0.9, 0.9))
            pts = boltPath(at, dir, rand(2.5, 5) * scale, 6, 0.22)
        elseif kind < 0.66 then -- the corona: out of the chest, every direction
            local dir = direction(rand(0, math.pi * 2), rand(-0.45, 1.2))
            pts = boltPath(base + Vector3.new(0, 0.6, 0) + dir * 1.1, dir, rand(7, 13) * scale, 9, 0.2)
        elseif kind < 0.84 then -- the floor: out along the ground from the feet
            local az = rand(0, math.pi * 2)
            local dir = direction(az, 0)
            local origin = Vector3.new(base.X, groundY + 0.35, base.Z) + dir * 1.2
            pts = boltPath(origin, dir, rand(7, 13) * scale, 8, 0.17)
            for i, p in pts do -- (the path is kept low, hugging the ground)
                pts[i] = Vector3.new(p.X, groundY + 0.35 + math.abs(p.Y - origin.Y) * 0.5, p.Z)
            end
        else -- high: up past the head
            local dir = direction(rand(0, math.pi * 2), rand(0.85, 1.45))
            pts = boltPath(base + Vector3.new(0, 1.5, 0) + dir * 1, dir, rand(8, 14) * scale, 9, 0.2)
        end
        fire(bolt, pts, rand(0.1, 0.15))
        -- now and then a fork leaves the bolt part of the way along
        if math.random() < 0.3 then
            for _, other in bolts do
                if not other.active and other ~= bolt then
                    local k = math.random(3, 4)
                    local bdir = (pts[#pts] - pts[k]).Unit
                    local turn = CFrame.Angles(0, rand(-0.9, 0.9), 0) * CFrame.Angles(rand(-0.4, 0.4), 0, 0)
                    bdir = (turn * CFrame.lookAt(Vector3.zero, bdir)).LookVector
                    fire(other, boltPath(pts[k], bdir, (pts[#pts] - pts[k]).Magnitude * rand(0.5, 0.8), 4, 0.12), rand(0.06, 0.09))
                    break
                end
            end
        end
    end

    local connection
    connection = RunService.RenderStepped:Connect(function(rawDt)
        if not root.Parent then
            return
        end
        local dt = rawDt * speed
        clock += dt
        center.CFrame = CFrame.new(root.Position)
        if clock >= nextGround then
            nextGround = clock + 0.6
            local hit = Workspace:Raycast(root.Position + Vector3.new(0, 2, 0), Vector3.new(0, -14, 0), rayParams)
            groundY = if hit then hit.Position.Y else root.Position.Y - 3
        end
        for _, b in bolts do
            if b.active then
                b.t += dt
                local idx = math.min(b.n, 1 + math.floor(b.t / b.dur * (b.n - 1) + 0.5))
                b.head.CFrame = CFrame.new(b.pts[idx])
                if b.t >= b.dur then
                    b.body.Enabled = false
                    b.heart.Enabled = false
                    b.active = false
                    b.nextFire = clock + rand(0.0, 0.1)
                end
            elseif clock >= b.nextFire then
                newBolt(b)
            end
        end
        if not reduced then
            light.Brightness = 1.2 + math.noise(clock * 18, 0.5) * 0.9
        end
    end)

    local handle = {}
    function handle.destroy()
        if connection then
            connection:Disconnect()
            connection = nil
        end
        folder:Destroy()
    end
    return handle
end

return CrimsonLightning

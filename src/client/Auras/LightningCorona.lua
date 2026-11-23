-- Realm 7's (Divine Realm) unique feature, 2026-11-23: a CORONA OF BLACK-AND-RED LIGHTNING (the owner: keep it a steady, very visible loop like the base aura, and replace the old
-- piece, a 6-stud sphere of bolts 1.2 studs long that lived a tenth of a second, with black and red lightning). It replaces RealmUnique.Tier07 for this realm only (the old model
-- stays in ReplicatedStorage: the breakthrough still reads its textures). Prototype and history: Claude Memory/Aura Crimson Lightning Prototype 2026-11-23.md.
--
-- A loop, not an event: about a dozen jagged bolts are alive round the body at every moment (nine are being drawn on average, each leaving a quarter second of fading trail), and each
-- re-forms in a new shape and direction a moment after it fades, so the crackle never settles into one look:
--   * skin     30%  short arcs (2.5 to 5 studs) crawling over the body
--   * corona   36%  7 to 13 studs, out of the chest in every direction, now and then forking
--   * floor    18%  running out along the ground from the feet
--   * high     16%  climbing past the head
-- Each bolt is two Trails on the same two attachments, a head part walked along a jagged path in 0.1 to 0.15 s: a hard-edged black body (normal blend) and a thin white-hot heart on
-- top (additive). Plus sparks thrown out in every direction, and a red light that flickers with the crackle.
-- It is driven by RealmAura's own loop (kind "corona"), so it follows the hips' shift of the meditation pose, is switched off with the rest of an aura beyond the cull distance, and is
-- destroyed with the aura's folder. Cost (the local player's own aura): 14 bolts = 28 trails, 1 emitter, 1 light, 15 invisible anchored parts; another player's: 8 bolts; a phone (Quality.Low):
-- 8 and 5.
local Workspace = game:GetService("Workspace")

local LightningCorona = {}

local TEX = {
    Spark = "rbxassetid://9997556038", -- a small round spark (the base aura's BodySpark)
}
local BLACK = Color3.fromRGB(8, 0, 4)
local RED = Color3.fromRGB(235, 20, 40)
local HOT = Color3.fromRGB(255, 132, 108)
local HEART_FROM, HEART_TO = Color3.fromRGB(255, 205, 175), Color3.fromRGB(255, 70, 60)

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

-- Builds the corona inside `fx` (the aura's folder). tuning: { low = Quality.Low, isLocal = the local player's own aura }. Returns the state RealmAura keeps for step().
function LightningCorona.build(fx, root, tuning)
    tuning = tuning or {}
    local bolts = if tuning.isLocal then (if tuning.low then 8 else 14) else (if tuning.low then 5 else 8)
    local state = { root = root, fx = fx, bolts = {}, clock = 0, groundY = root.Position.Y - 3, nextGround = 0 }

    local function speck(name)
        local part = Instance.new("Part")
        part.Name = name
        part.Size = Vector3.new(0.2, 0.2, 0.2)
        part.Transparency = 1
        part.Anchored = true
        part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
        part.CastShadow = false
        part.CFrame = CFrame.new(root.Position)
        part.Parent = fx
        return part
    end
    local function attachment(name, parent, position)
        local a = Instance.new("Attachment")
        a.Name = name
        a.Position = position or Vector3.zero
        a.Parent = parent
        return a
    end

    state.center = speck("LightningCenter")
    local chest = attachment("Chest", state.center, Vector3.new(0, 0.6, 0))
    local sparks = Instance.new("ParticleEmitter")
    sparks.Name = "LightningSparks"
    sparks.Texture = TEX.Spark
    sparks.Color = ColorSequence.new(HOT, RED)
    sparks.LightEmission = 1
    sparks.LightInfluence = 0
    sparks.Size = seq({ { 0, 0.55 }, { 1, 0 } })
    sparks.Transparency = seq({ { 0, 0 }, { 0.7, 0.3 }, { 1, 1 } })
    sparks.Lifetime = NumberRange.new(0.2, 0.4)
    sparks.Speed = NumberRange.new(10, 24)
    sparks.SpreadAngle = Vector2.new(180, 180)
    sparks.Drag = 2
    sparks.Rate = if tuning.low then 18 elseif tuning.isLocal then 30 else 20
    sparks.Parent = chest

    state.light = Instance.new("PointLight")
    state.light.Color = RED
    state.light.Range = 18
    state.light.Brightness = 1.2
    state.light.Shadows = false
    state.light.Parent = state.center

    for _ = 1, bolts do
        local head = speck("LightningBolt")
        local a0 = attachment("A0", head, Vector3.new(0, 0.5, 0))
        local a1 = attachment("A1", head, Vector3.new(0, -0.5, 0))
        local body = Instance.new("Trail")
        body.Name = "Body"
        body.Attachment0, body.Attachment1 = a0, a1
        body.Color = ColorSequence.new(BLACK)
        body.LightEmission, body.LightInfluence = 0, 0
        body.Lifetime = 0.26
        body.FaceCamera = true
        body.MinLength = 0.05
        body.Transparency = seq({ { 0, 0.0 }, { 0.65, 0.05 }, { 1, 1 } })
        body.WidthScale = seq({ { 0, 0.5 }, { 1, 0.2 } })
        body.Enabled = false
        body.Parent = head
        local heart = Instance.new("Trail")
        heart.Name = "Heart"
        heart.Attachment0, heart.Attachment1 = a0, a1
        heart.Color = ColorSequence.new(HEART_FROM, HEART_TO)
        heart.Brightness = 2.5
        heart.LightEmission, heart.LightInfluence = 1, 0
        heart.Lifetime = 0.26
        heart.FaceCamera = true
        heart.MinLength = 0.05
        heart.Transparency = seq({ { 0, 0 }, { 0.6, 0.1 }, { 1, 1 } })
        heart.WidthScale = seq({ { 0, 0.2 }, { 1, 0.08 } })
        heart.Enabled = false
        heart.Parent = head
        table.insert(state.bolts, { head = head, body = body, heart = heart, active = false, pts = nil, n = 0, t = 0, dur = 0.1, nextFire = math.random() * 0.4 })
    end

    state.rayParams = RaycastParams.new()
    state.rayParams.FilterType = Enum.RaycastFilterType.Exclude
    state.rayParams.FilterDescendantsInstances = { fx, root.Parent }
    return state
end

local function fire(bolt, pts, duration)
    bolt.pts, bolt.n, bolt.t, bolt.dur, bolt.active = pts, #pts, 0, duration, true
    bolt.head.CFrame = CFrame.new(pts[1])
    bolt.body.Enabled = true
    bolt.heart.Enabled = true
end

local function newBolt(state, bolt)
    local base = state.center.Position
    local groundY = state.groundY
    local kind = math.random()
    local pts
    if kind < 0.3 then -- the skin: short arcs that crawl over the body
        local at = base + Vector3.new(rand(-0.9, 0.9), rand(-1.6, 1.8), rand(-0.6, 0.6))
        pts = boltPath(at, direction(rand(0, math.pi * 2), rand(-0.9, 0.9)), rand(2.5, 5), 6, 0.22)
    elseif kind < 0.66 then -- the corona: out of the chest, every direction
        local dir = direction(rand(0, math.pi * 2), rand(-0.45, 1.2))
        pts = boltPath(base + Vector3.new(0, 0.6, 0) + dir * 1.1, dir, rand(7, 13), 9, 0.2)
    elseif kind < 0.84 then -- the floor: out along the ground from the feet
        local dir = direction(rand(0, math.pi * 2), 0)
        local origin = Vector3.new(base.X, groundY + 0.35, base.Z) + dir * 1.2
        pts = boltPath(origin, dir, rand(7, 13), 8, 0.17)
        for i, p in pts do -- (kept low, hugging the ground)
            pts[i] = Vector3.new(p.X, groundY + 0.35 + math.abs(p.Y - origin.Y) * 0.5, p.Z)
        end
    else -- high: up past the head
        local dir = direction(rand(0, math.pi * 2), rand(0.85, 1.45))
        pts = boltPath(base + Vector3.new(0, 1.5, 0) + dir * 1, dir, rand(8, 14), 9, 0.2)
    end
    fire(bolt, pts, rand(0.1, 0.15))
    -- now and then a fork leaves the bolt part of the way along
    if math.random() < 0.3 then
        for _, other in state.bolts do
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

-- One step of the loop (called by RealmAura's step with the aura's hips shift in the root's space). Not called while the aura is culled.
function LightningCorona.step(state, dt, shift)
    local root = state.root
    if not root.Parent or not state.center.Parent then
        return
    end
    state.clock += dt
    state.center.CFrame = CFrame.new(root.CFrame:PointToWorldSpace(shift or Vector3.zero))
    if state.clock >= state.nextGround then
        state.nextGround = state.clock + 0.6
        local hit = Workspace:Raycast(root.Position + Vector3.new(0, 2, 0), Vector3.new(0, -14, 0), state.rayParams)
        state.groundY = if hit then hit.Position.Y else root.Position.Y - 3
    end
    for _, b in state.bolts do
        if b.active then
            b.t += dt
            local idx = math.min(b.n, 1 + math.floor(b.t / b.dur * (b.n - 1) + 0.5))
            b.head.CFrame = CFrame.new(b.pts[idx])
            if b.t >= b.dur then
                b.body.Enabled = false
                b.heart.Enabled = false
                b.active = false
                b.nextFire = state.clock + rand(0.0, 0.1)
            end
        elseif state.clock >= b.nextFire then
            newBolt(state, b)
        end
    end
    state.light.Brightness = 1.2 + math.noise(state.clock * 18, 0.5) * 0.9
end

return LightningCorona

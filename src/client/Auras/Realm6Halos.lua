-- Realm6Halos: the Realm 6 (Immortal) celestial halos at runtime: three rings of curved, segmented Beams round the head, and
-- particle glints on them. Every value is in Realm6HalosConfig.
--
--   Crown      the halo behind the head: fine arcs with narrow gaps, turning slowly
--   Graduated  just outside and behind it: graduated arcs with wider gaps, turning the other way
--   Orbit      a tilted, beaded orbit round and above the head, spinning, its tilt slowly turning
--   glints     now and then a star glints at a joint of the crown or the graduated ring and rides it as it turns
--   show       the rings grow out one after another (ease-out-back) as they fade in; hide: they shrink and fade
--
-- Each ring's arcs hang on one anchored, non-colliding client-side part; turning a ring moves only that part (one
-- BulkMoveTo for all three). The arcs are rewritten only while a ring grows or shrinks. Nothing touches the character.
--
--   local handle = Realm6Halos.attach(character, { isLocal = true })
--     isLocal   the local player's own halos: never culled
--     clock     a function returning seconds (default os.clock); a review can hold it to look at one moment
--   handle.destroy()     -- shrinks and fades them, then removes them (at once if culled)
--   handle.destroyNow()  -- removes them at once
local RunService = game:GetService("RunService")

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local Config = require(script.Parent:WaitForChild("Realm6HalosConfig"))

local Realm6Halos = {}
Realm6Halos.Config = Config

local rad = math.rad

local function smooth(x)
    x = math.clamp(x, 0, 1)
    return x * x * (3 - 2 * x)
end

local function backOut(x, s)
    x = math.clamp(x, 0, 1) - 1
    return 1 + x * x * ((s + 1) * x + s)
end

local function numberSequence(points, scale)
    local keys = {}
    for _, k in points do
        table.insert(keys, NumberSequenceKeypoint.new(k[1], k[2] * (scale or 1)))
    end
    return NumberSequence.new(keys)
end

local function settle(part)
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Massless = true
    part.Transparency = 1
    part.Size = Vector3.new(0.1, 0.1, 0.1)
end

-- one arc's ends on a ring of radius r: X along the ring's tangent (the Bezier handles run along it), Y outward
local function arcEnds(a, b, r)
    local function frame(angle)
        local radial = Vector3.new(math.cos(angle), math.sin(angle), 0)
        local tangent = Vector3.new(-math.sin(angle), math.cos(angle), 0)
        return CFrame.fromMatrix(radial * r, tangent, radial)
    end
    return frame(a), frame(b), 4 / 3 * math.tan((b - a) / 4) * r
end

local warned = false

function Realm6Halos.attach(character, options)
    options = options or {}
    local C = Config
    local root = character:WaitForChild("HumanoidRootPart", 5)
    if not root then
        if not warned then
            warned = true
            warn("Realm6Halos: the character has no HumanoidRootPart")
        end
        return nil
    end
    local head = character:FindFirstChild("Head")
    local isLocal = options.isLocal == true
    local clock = options.clock or os.clock
    local low = Quality.Low
    local cullDistance = if low then C.Performance.LowQualityCullDistance else C.Performance.CullDistance
    local body = root.Size.Y / 2
    local k = C.Scale * body

    local folder = Instance.new("Folder")
    folder.Name = "Realm6Halos"
    folder.Parent = workspace

    local rings, parts, cframes = {}, {}, {}
    local glints = {}
    local G = C.Glints
    for _, spec in C.Rings do
        local host = Instance.new("Part")
        host.Name = spec.Name
        settle(host)
        host.Parent = folder
        table.insert(parts, host)
        table.insert(cframes, CFrame.identity)
        local ring = { spec = spec, host = host, arcs = {}, radius = -1, alpha = -1 }
        local step = 360 / spec.Segments
        for i = 1, spec.Segments do
            local a0 = Instance.new("Attachment")
            a0.Name = "Arc" .. i .. "Start"
            a0.Parent = host
            local a1 = Instance.new("Attachment")
            a1.Name = "Arc" .. i .. "End"
            a1.Parent = host
            local beam = Instance.new("Beam")
            beam.Name = "Arc" .. i
            beam.Texture = C.Textures[spec.Texture]
            beam.TextureMode = Enum.TextureMode.Stretch
            beam.TextureLength = 1
            beam.TextureSpeed = 0
            beam.FaceCamera = true
            beam.Segments = spec.BeamSegments
            beam.Width0 = spec.Width * k
            beam.Width1 = spec.Width * k
            beam.Color = ColorSequence.new(spec.Color)
            beam.LightEmission = spec.LightEmission
            beam.LightInfluence = 0
            beam.Brightness = spec.Brightness
            beam.ZOffset = spec.ZOffset
            beam.Transparency = NumberSequence.new(1)
            beam.Attachment0 = a0
            beam.Attachment1 = a1
            beam.Parent = host
            table.insert(ring.arcs, {
                a = rad((i - 1) * step + spec.Gap / 2),
                b = rad(i * step - spec.Gap / 2),
                start = a0,
                finish = a1,
                beam = beam,
            })
            if spec.Glints then
                local emitter = Instance.new("ParticleEmitter")
                emitter.Name = "Glint"
                emitter.Texture = C.Textures.Glint
                emitter.Rate = 0
                emitter.Speed = NumberRange.new(0)
                emitter.Lifetime = NumberRange.new(G.Lifetime[1], G.Lifetime[2])
                emitter.Rotation = NumberRange.new(G.Rotation[1], G.Rotation[2])
                emitter.RotSpeed = NumberRange.new(G.RotSpeed[1], G.RotSpeed[2])
                emitter.Size = numberSequence(G.Size, k)
                emitter.Transparency = numberSequence(G.Transparency)
                emitter.Color = ColorSequence.new(G.Color)
                emitter.LightEmission = G.LightEmission
                emitter.LightInfluence = G.LightInfluence
                emitter.Brightness = G.Brightness
                emitter.ZOffset = G.ZOffset
                emitter.LockedToPart = true
                emitter.Parent = a0
                table.insert(glints, emitter)
            end
        end
        table.insert(rings, ring)
    end

    local function shape(ring, radius, alpha)
        if math.abs(radius - ring.radius) > 1e-4 then
            ring.radius = radius
            for _, arc in ring.arcs do
                local s, e, handle = arcEnds(arc.a, arc.b, radius)
                arc.start.CFrame = s
                arc.finish.CFrame = e
                arc.beam.CurveSize0 = handle
                arc.beam.CurveSize1 = handle
            end
        end
        if math.abs(alpha - ring.alpha) > 0.004 or (alpha == 1 and ring.alpha ~= 1) or (alpha == 0 and ring.alpha ~= 0) then
            ring.alpha = alpha
            local transparency = NumberSequence.new(1 - alpha * (1 - ring.spec.Transparency))
            for _, arc in ring.arcs do
                arc.beam.Transparency = transparency
            end
        end
    end

    -- each frame ---------------------------------------------------------------------------------------------------
    local started = clock()
    local stopping = nil
    local hidden = false
    local connection
    local handle = {}
    local nextCull, nextGlint = 0, 0
    local random = Random.new()
    local glintShare = if low then C.Performance.LowQualityGlints else 1

    local function update()
        local now = clock()
        local t = now - started
        if not isLocal and now >= nextCull then
            nextCull = now + 0.25
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - root.Position).Magnitude > cullDistance then
                if stopping then
                    handle.destroyNow()
                    return
                end
                if not hidden then
                    hidden = true
                    folder.Parent = nil
                end
            elseif hidden then
                hidden = false
                folder.Parent = workspace
            end
        end
        if hidden then
            return
        end

        local leaving = if stopping then smooth((now - stopping) / C.Fade.Out) else 0
        local _, yaw = root.CFrame:ToEulerAnglesYXZ()
        local headAt = if head then head.Position else root.Position + Vector3.new(0, C.FallbackHead * body, 0)
        local bob = C.Bob.Amount * k * math.sin(t * C.Bob.Speed)
        local base = CFrame.new(headAt + Vector3.new(0, bob, 0)) * CFrame.Angles(0, yaw, 0)
        local open = 0
        for i, ring in rings do
            local spec = ring.spec
            local grow = (t - spec.Grow.Delay) / spec.Grow.Time
            local size = C.GrowFrom + (1 - C.GrowFrom) * backOut(grow, C.Overshoot)
            local alpha = smooth(grow * 1.4)
            if stopping then
                size *= 1 - (1 - C.Fade.ShrinkTo) * leaving
                alpha *= 1 - leaving
            end
            shape(ring, spec.Radius * k * math.max(size, 0.01), alpha)
            open = math.max(open, alpha)
            local centre = CFrame.new(spec.Centre[1] * k, spec.Centre[2] * k, spec.Centre[3] * k)
            if spec.Plane == "Tilted" then
                cframes[i] = base * centre * CFrame.Angles(0, t * spec.Precess, 0) * CFrame.Angles(rad(spec.Tilt), 0, 0)
                    * CFrame.Angles(0, 0, t * spec.Spin)
            else
                cframes[i] = base * centre * CFrame.Angles(0, 0, t * spec.Spin)
            end
        end
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)

        if not stopping and open > 0.9 and #glints > 0 and now >= nextGlint then
            nextGlint = now + random:NextNumber(G.Interval[1], G.Interval[2]) / glintShare
            glints[random:NextInteger(1, #glints)]:Emit(1)
        end

        if stopping and now - stopping >= C.Fade.Out then
            handle.destroyNow()
        end
    end

    connection = RunService.RenderStepped:Connect(update)
    update()

    function handle.destroyNow()
        if connection then
            connection:Disconnect()
            connection = nil
        end
        folder:Destroy()
    end

    function handle.destroy()
        if hidden then
            handle.destroyNow()
            return
        end
        if not stopping then
            stopping = clock()
        end
    end

    handle.folder = folder
    handle.beams = 0
    for _, ring in rings do
        handle.beams += #ring.arcs
    end
    return handle
end

return Realm6Halos

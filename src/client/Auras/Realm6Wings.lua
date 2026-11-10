-- Realm6Wings: the Realm 6 (Immortal) wings at runtime: massive feather wings built from Beams (one per feather) on an arm
-- of three invisible bones, plus feather-texture ParticleEmitters. Every value is in Realm6WingsConfig.
--
--   show      the wings swing out from behind the back and unfurl, the fan of feathers opening, a little past spread
--             and back (ease-out-back), as they fade in
--   idle      a slow beat travelling out along the arm (shoulder, then elbow, then wrist), the fan breathing with it,
--             and a ripple running across the flight feathers from the body to the tips
--   light     plumes of light stream off the outer primaries' tips; now and then a feather loosens and drifts down
--   hide      they fold back and fade
--
-- Each wing's bones are anchored, non-colliding client-side parts moved every frame (one BulkMoveTo); the coverts sit
-- still on them, and only the flight feathers' attachments are rewritten each frame. Nothing touches the character.
--
--   local handle = Realm6Wings.attach(character, { isLocal = true })
--     isLocal   the local player's own wings: never culled, always full rate
--     clock     a function returning seconds (default os.clock); a review can hold it to look at one moment
--   handle.destroy()     -- folds and fades them, then removes them (at once if culled)
--   handle.destroyNow()  -- removes them at once
local RunService = game:GetService("RunService")

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local Config = require(script.Parent:WaitForChild("Realm6WingsConfig"))

local Realm6Wings = {}
Realm6Wings.Config = Config

local rad = math.rad
local BONES = { "Humerus", "Forearm", "Hand" }
local FLIP = CFrame.Angles(0, math.pi, 0)

local function lerp(a, b, t)
    return a + (b - a) * t
end

local function smooth(x)
    x = math.clamp(x, 0, 1)
    return x * x * (3 - 2 * x)
end

-- ease-out-back: 0 -> 1 passing a little beyond 1 (by about (s - 1) / 6) before settling
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

local function colorSequence(points)
    local keys = {}
    for _, k in points do
        table.insert(keys, ColorSequenceKeypoint.new(k[1], k[2]))
    end
    return ColorSequence.new(keys)
end

local function reversed(points)
    local out = {}
    for i = #points, 1, -1 do
        table.insert(out, { 1 - points[i][1], points[i][2] })
    end
    return out
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

-- the feathers as laid out (the same on every character): one record per feather
local layout = nil
local function buildLayout()
    if layout then
        return layout
    end
    local J = Config.Jitter
    local random = Random.new(J.Seed)
    local arm = Config.Arm
    local start = { Humerus = 0, Forearm = arm.Humerus, Hand = arm.Humerus + arm.Forearm }
    local total = arm.Humerus + arm.Forearm + arm.Hand
    layout = {}
    for _, row in Config.Rows do
        for i = 1, row.Count do
            local f = if row.Count == 1 then 0 else (i - 1) / (row.Count - 1)
            local along = lerp(row.From, row.To, f)
            local length = if row.Lengths then row.Lengths[i] else lerp(row.Length[1], row.Length[2], f)
            local reach = (start[row.Bone] + along * arm[row.Bone]) / total -- 0 at the shoulder, 1 at the hand's end
            table.insert(layout, {
                row = row,
                index = i,
                bone = row.Bone,
                along = along * arm[row.Bone],
                angle = lerp(row.Angle[1], row.Angle[2], f) + random:NextNumber(-J.Angle, J.Angle),
                length = length * (1 + random:NextNumber(-J.Length, J.Length)),
                width = row.Width * (1 + random:NextNumber(-J.Width, J.Width)),
                offset = row.Offset,
                layer = row.Layer + Config.Cup * reach * reach,
                twist = lerp(row.Twist[1], row.Twist[2], f),
                bend = row.Bend,
                curl = row.Curl,
                texture = row.Textures[(i - 1) % #row.Textures + 1],
                flight = row.Flight == true,
                reach = reach,
            })
        end
    end
    return layout
end

-- a feather's two attachment frames in its bone's space: root and tip, X along the shaft (each tilted by the bend so the
-- beam arcs toward the leading edge, its tip trailing), Y across it (the beam's width), twisted about the shaft
local function featherFrames(entry, theta, side, k)
    local root = Vector3.new(entry.along, entry.offset, side * entry.layer) * k
    local bend = rad(entry.bend)
    local curl = side * entry.curl
    local planar = Vector3.new(math.cos(theta), math.sin(theta), 0)
    local tip = root + (planar + Vector3.new(0, 0, curl)) * (entry.length * k)
    local twist = rad(entry.twist) * side
    local function frame(position, angle)
        local x = Vector3.new(math.cos(angle), math.sin(angle), curl).Unit
        local y = Vector3.new(-x.Y, x.X, 0).Unit
        y = y * math.cos(twist) + x:Cross(y) * math.sin(twist)
        if Config.FlipVane then
            y = -y
        end
        return CFrame.fromMatrix(position, x, y)
    end
    return frame(root, theta + bend), frame(tip, theta - bend)
end

local warned = false

function Realm6Wings.attach(character, options)
    options = options or {}
    local C = Config
    local root = character:WaitForChild("HumanoidRootPart", 5)
    if not root then
        if not warned then
            warned = true
            warn("Realm6Wings: the character has no HumanoidRootPart")
        end
        return nil
    end
    local mountPart, mountOffset = root, C.Mount.Offset.HumanoidRootPart
    for _, name in C.Mount.Parts do
        local part = character:FindFirstChild(name)
        if part and part:IsA("BasePart") then
            mountPart, mountOffset = part, C.Mount.Offset[name]
            break
        end
    end
    local isLocal = options.isLocal == true
    local clock = options.clock or os.clock
    local low = Quality.Low
    local cullDistance = if low then C.Performance.LowQualityCullDistance else C.Performance.CullDistance
    local body = root.Size.Y / 2 -- the character's own scale (a scaled character's root is taller)
    local k = C.Scale * body -- the wings' scale
    local mount = CFrame.new(mountOffset[1] * body, mountOffset[2] * body, mountOffset[3] * body)
    local entries = buildLayout()

    local folder = Instance.new("Folder")
    folder.Name = "Realm6Wings"
    folder.Parent = workspace

    local wings = {}
    local parts, cframes = {}, {}
    local beams = {} -- { beam, base transparency }

    local function newEmitter(role, attachment)
        local spec = C.Particles[role]
        local emitter = Instance.new("ParticleEmitter")
        emitter.Name = role
        emitter.Texture = C.Textures[spec.Texture]
        emitter.Rate = 0
        emitter.Lifetime = NumberRange.new(spec.Lifetime[1], spec.Lifetime[2])
        emitter.Speed = NumberRange.new(spec.Speed[1] * k, spec.Speed[2] * k)
        emitter.SpreadAngle = Vector2.new(spec.Spread, spec.Spread)
        emitter.Acceleration = Vector3.new(spec.Acceleration[1], spec.Acceleration[2], spec.Acceleration[3]) * k
        emitter.Drag = spec.Drag
        emitter.Rotation = NumberRange.new(spec.Rotation[1], spec.Rotation[2])
        emitter.RotSpeed = NumberRange.new(spec.RotSpeed[1], spec.RotSpeed[2])
        emitter.Size = numberSequence(spec.Size, k)
        emitter.Transparency = numberSequence(spec.Transparency)
        emitter.Color = colorSequence(spec.Color)
        emitter.LightEmission = spec.LightEmission
        emitter.LightInfluence = spec.LightInfluence
        emitter.Brightness = spec.Brightness
        emitter.ZOffset = spec.ZOffset
        emitter.LockedToPart = false
        emitter.Parent = attachment
        return emitter
    end

    for _, side in { 1, -1 } do
        local wing = { side = side, bones = {}, flights = {}, coverts = {}, emitters = { TipLight = {}, Shed = {} } }
        for _, name in BONES do
            local bone = Instance.new("Part")
            bone.Name = (if side > 0 then "R" else "L") .. name
            settle(bone)
            bone.Parent = folder
            wing.bones[name] = bone
            table.insert(parts, bone)
            table.insert(cframes, CFrame.identity)
        end
        for _, entry in entries do
            local row = entry.row
            if row.LowQuality == false and low then
                continue
            end
            local bone = wing.bones[entry.bone]
            local a0 = Instance.new("Attachment")
            a0.Name = row.Name .. entry.index .. "Root"
            a0.Parent = bone
            local a1 = Instance.new("Attachment")
            a1.Name = row.Name .. entry.index .. "Tip"
            a1.Parent = bone
            local look = C.Looks[row.Look]
            local beam = Instance.new("Beam")
            beam.Name = row.Name .. entry.index
            beam.Texture = C.Textures[entry.texture]
            beam.TextureMode = Enum.TextureMode.Stretch
            beam.TextureLength = 1
            beam.TextureSpeed = 0
            beam.FaceCamera = false
            beam.Segments = look.Segments
            beam.Width0 = entry.width * k
            beam.Width1 = entry.width * k
            beam.CurveSize0 = entry.length * k / 3
            beam.CurveSize1 = entry.length * k / 3
            beam.LightEmission = look.LightEmission
            beam.LightInfluence = look.LightInfluence
            beam.Brightness = look.Brightness
            beam.Transparency = NumberSequence.new(1)
            if C.QuillAtAttachment0 then
                beam.Attachment0, beam.Attachment1 = a0, a1
                beam.Color = colorSequence(look.Color)
            else
                -- the tip first: a curve handle runs along +X from Attachment0 and along -X into Attachment1, and both
                -- attachments' X point root -> tip, so the handles turn negative (positive overshoots both ends: a spike
                -- past every root, seen in Play)
                beam.Attachment0, beam.Attachment1 = a1, a0
                beam.Color = colorSequence(reversed(look.Color))
                beam.CurveSize0, beam.CurveSize1 = -beam.CurveSize1, -beam.CurveSize0
            end
            beam.Parent = bone
            table.insert(beams, { beam, look.Transparency })
            local record = { entry = entry, root = a0, tip = a1 }
            if entry.flight then
                table.insert(wing.flights, record)
            else
                table.insert(wing.coverts, record)
            end
            if row.Emit then
                for role, indices in row.Emit do
                    if table.find(indices, entry.index) then
                        table.insert(wing.emitters[role], newEmitter(role, a1))
                    end
                end
            end
        end
        table.insert(wings, wing)
    end

    -- each frame ---------------------------------------------------------------------------------------------------
    local P, B, R = C.Pose, C.Breath, C.Ripple
    local arm = C.Arm
    local started = clock()
    local stopping, stopFold = nil, 1
    local hidden = false
    local connection
    local handle = {}
    local lastAlpha, lastCovertFold = -1, -1
    local frameCount = 0
    local nextCull = 0
    local nextEmit = { TipLight = { 0, 0 }, Shed = { 0, 0 } }
    local random = Random.new()
    local tipShare = if low then C.Performance.LowQualityTipLight else 1

    local function mix(key, fold)
        return lerp(P.Folded[key], P.Spread[key], fold)
    end

    -- a feather's angle off its bone, at this fold (the fan closes along the arm as it folds)
    local function fanned(angle, fold)
        return angle * lerp(P.FoldFan, 1, math.clamp(fold, 0, 1.2))
    end

    local function update()
        local now = clock()
        local t = now - started
        frameCount += 1
        local camera = workspace.CurrentCamera
        local distance = if camera then (camera.CFrame.Position - root.Position).Magnitude else 0
        if not isLocal and now >= nextCull then
            nextCull = now + 0.25
            if distance > cullDistance then
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

        -- fold (1 spread) and fade
        local fold, alpha
        if stopping then
            local e = smooth((now - stopping) / C.Fade.Out)
            fold = stopFold * (1 - e)
            alpha = (1 - e) * smooth(t / C.Fade.In)
        else
            fold = backOut(t / C.Unfold.Time, C.Unfold.Overshoot)
            alpha = smooth(t / C.Fade.In)
        end
        if math.abs(alpha - lastAlpha) > 0.004 or (alpha == 1 and lastAlpha ~= 1) then
            lastAlpha = alpha
            for _, item in beams do
                item[1].Transparency = NumberSequence.new(1 - alpha * (1 - item[2]))
            end
        end

        -- the beat: out along the arm, each joint a little after the last; it grows in as the wings open
        local beat = 2 * math.pi * t / B.Period
        local open = math.clamp(fold, 0, 1)
        local s1, s2, s3 = math.sin(beat) * open, math.sin(beat - 0.5) * open, math.sin(beat - 1.0) * open
        local fan = 1 + B.Fan * math.sin(beat - 0.8) * open
        local shoulder = rad(mix("Shoulder", fold) + B.Shoulder * s1)
        local elbow = rad(mix("Elbow", fold) + B.Elbow * s2)
        local wrist = rad(mix("Wrist", fold) + B.Wrist * s3)
        local sweep = rad(mix("Sweep", fold) - B.Sweep * s1)

        local basis = mountPart.CFrame * mount
        local i = 0
        for _, wing in wings do
            local side = wing.side
            local base = basis * CFrame.new(side * C.Mount.ShoulderX * body, 0, 0) * CFrame.Angles(0, -side * sweep, 0)
            if side < 0 then
                base = base * FLIP
            end
            local a1 = shoulder
            local a2 = a1 + elbow
            local a3 = a2 + wrist
            local elbowAt = Vector3.new(math.cos(a1), math.sin(a1), 0) * (arm.Humerus * k)
            local wristAt = elbowAt + Vector3.new(math.cos(a2), math.sin(a2), 0) * (arm.Forearm * k)
            i += 1
            cframes[i] = base * CFrame.Angles(0, 0, a1)
            i += 1
            cframes[i] = base * CFrame.new(elbowAt) * CFrame.Angles(0, 0, a2)
            i += 1
            cframes[i] = base * CFrame.new(wristAt) * CFrame.Angles(0, 0, a3)
        end
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)

        -- the flight feathers: the fan and the ripple, every frame (other players' far ones every other frame)
        local full = isLocal or distance < C.Performance.HalfRateDistance or frameCount % 2 == 0
        if full then
            for _, wing in wings do
                for _, record in wing.flights do
                    local entry = record.entry
                    local wave = rad(R.Degrees) * math.sin(R.Speed * t - R.Waves * entry.reach) * open
                    local theta = rad(fanned(entry.angle, fold) * fan) + wave
                    local a, b = featherFrames(entry, theta, wing.side, k)
                    record.root.CFrame = a
                    record.tip.CFrame = b
                end
            end
        end
        -- the coverts move only while the wing folds or opens
        if math.abs(fold - lastCovertFold) > 0.002 then
            lastCovertFold = fold
            for _, wing in wings do
                for _, record in wing.coverts do
                    local a, b = featherFrames(record.entry, rad(fanned(record.entry.angle, fold)), wing.side, k)
                    record.root.CFrame = a
                    record.tip.CFrame = b
                end
            end
        end

        -- the particles: one at a time, per wing, while open
        if not stopping and open > 0.85 then
            for w, wing in wings do
                for role, spec in C.Particles do
                    local list = wing.emitters[role]
                    if #list > 0 and now >= nextEmit[role][w] then
                        local gap = random:NextNumber(spec.Interval[1], spec.Interval[2])
                        if role == "TipLight" then
                            gap /= tipShare
                        end
                        nextEmit[role][w] = now + gap
                        list[random:NextInteger(1, #list)]:Emit(1)
                    end
                end
            end
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
            stopFold = backOut((stopping - started) / C.Unfold.Time, C.Unfold.Overshoot)
        end
    end

    handle.folder = folder
    handle.beams = #beams
    return handle
end

return Realm6Wings

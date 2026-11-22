-- The Nine-Tail Moonfox's animation (skinned on 61 bones; Mythical, the Exclusive Egg). She is a moon vixen: light, quick on her feet and graceful.
--
-- Her legs are solved, not played back: each of the four is a three-segment chain with a paw, and a footfall generator (PetMotion.foot) puts each paw down
-- on the ground and slides it back with the body, so it stays planted at any speed and at any size (a Giant's stride is long and slow), then
-- carries it forward on a curve that lands already moving at the ground's speed. Her gait follows her speed: a walk's lateral sequence, a trot's
-- diagonal pairs, then a bounding trot with a moment in the air. The body does what a body does over planted feet: it sinks as a leg stretches, bounces
-- twice a stride, twists a little through the spine, rolls into turns and leans with acceleration, rocking back and settling when she stops. Her head
-- stays level through all of it and leads her turns; her ears and her nine tails (three bones each) are springs: they lag, overshoot and settle, set
-- swinging by her turns and her stopping and starting, with one lazy wave running across the fan when she stands. Standing she breathes, shifts her
-- weight (the leg she rests lifts a paw), looks about with her head leading her neck and her body following, flicks an ear or a single tail now and
-- then. In the air she tucks her paws under her and her tails stream; she leaps off with a push and lands soft.
local PetMotion = require(script.Parent:WaitForChild("PetMotion"))
local PetQuad = require(script.Parent:WaitForChild("PetQuad"))

local Moonfox = {}

local sin, cos, abs, min, max, clamp = math.sin, math.cos, math.abs, math.min, math.max, math.clamp
local sm = PetMotion.smoothstep
local lerp = PetMotion.lerp
local spring = PetMotion.spring
local TAU = 2 * math.pi

local FAR = 90 -- studs from the camera past which nobody can see it move: its bones rest
local NEAR = 55 -- studs: past this her tails keep to a gentler spring
local SOLE = 0.7942 -- metres from the middle of its box (the RootPart's cube counted) down to its paws (nine_tail_moonfox_gen.py)
local TAILS = 9
local SEGS = { "A", "B", "C" }
local LEG_KEYS = { "BL", "FL", "BR", "FR" }

-- the bones the profile poses
local BONES = { "Hips", "Spine", "Chest", "Neck", "Head", "EarL", "EarR", "TailRoot" }
for _, key in LEG_KEYS do
    for k = 1, 3 do
        table.insert(BONES, "Leg" .. key .. k)
    end
    table.insert(BONES, "Paw" .. key)
end
local TAIL_NAMES = {} -- [k][j]
for k = 1, TAILS do
    TAIL_NAMES[k] = {}
    for j, seg in SEGS do
        TAIL_NAMES[k][j] = "Tail" .. k .. seg
        table.insert(BONES, TAIL_NAMES[k][j])
    end
end
Moonfox.BONES = BONES
Moonfox.POINTS = { "Head" }
for k = 1, TAILS do
    table.insert(Moonfox.POINTS, "Tail" .. k .. "_Tip") -- a bone at each tail's tip (no skin on it): where a special's lights would leave from
end

-- in the air: forelegs folded back under her chest, hind legs drawn up (checked in Blender: no tears; folded harder, the chest tore)
local FLY = {
    BL = { 0.6, -1.2, 0.5, 0.1 }, BR = { 0.6, -1.2, 0.5, 0.1 },
    FL = { 0.45, -1.35, 0.45, 0.45 }, FR = { 0.45, -1.35, 0.45, 0.45 },
}

-- a fox's gait: the defaults, with the longest stride held a little short so even a run keeps her joints inside what her skin takes
local GAIT = {
    v0 = 0.25, v1 = 3.2, cadence = { 0.95, 2.5 }, duty = { 0.68, 0.42 }, trotAt = { 0.8, 2.0 }, lift = { 0.1, 0.19 }, bounce = { 0.012, 0.05 }, stride = 0.85,
    dutyFrom = 0.5, dutyTo = 3.4, active = { 0.12, 0.45 },
}

-- tails: each tail's three segments swing a little more toward the tip; they are heavy, soft brushes, so a gentle, slightly underdamped spring
local SEG_W = { 0.55, 1.0, 1.45 } -- how much of her body's turn and acceleration each segment takes
local SEG_FREQ = { 7.5, 6.2, 5.2 } -- rad/s
local SEG_DAMP = { 0.62, 0.5, 0.42 }
local WW_NEAR, ZZ_NEAR, WW_FAR, ZZ_FAR = {}, {}, {}, {} -- the springs' constants, for near and for far (a touch slower)
for j = 1, 3 do
    WW_NEAR[j], ZZ_NEAR[j] = SEG_FREQ[j] ^ 2, 2 * SEG_DAMP[j] * SEG_FREQ[j]
    WW_FAR[j], ZZ_FAR[j] = (SEG_FREQ[j] * 0.85) ^ 2, 2 * SEG_DAMP[j] * SEG_FREQ[j] * 0.85
end

local function init(rig, s)
    local u = rig.meters
    s.u = u
    local legs = {}
    for _, key in LEG_KEYS do
        legs[key] = { "Leg" .. key .. "1", "Leg" .. key .. "2", "Leg" .. key .. "3", "Paw" .. key }
    end
    s.quad = PetQuad.new(rig, {
        spine = { "Hips", "Spine", "Chest" }, legs = legs, psiFront = 0.45, psiHind = 0.7, flickFront = -0.3, flickHind = 0.3, maxCrouch = 0.16,
        gait = GAIT,
        limit = { -- (checked on a fast trot in Studio: her fur skin takes these)
            front = { { -1.15, 1.15 }, { -1.6, 1.7 }, { -1.2, 1.2 } },
            hind = { { -1.1, 1.1 }, { -1.5, 1.5 }, { -1.6, 1.6 } },
        },
    })
    s.legMo = {}
    for _, key in LEG_KEYS do
        local names = legs[key]
        s.legMo[key] = { rig.motors[names[1]], rig.motors[names[2]], rig.motors[names[3]], rig.motors[names[4]], FLY[key] }
    end
    s.unload = { BL = 0, BR = 0, FL = 0, FR = 0 }
    s.lean, s.leanV, s.roll, s.rollV = 0, 0, 0, 0
    s.gYaw, s.gYawV, s.gPitch, s.gPitchV = 0, 0, 0, 0 -- where her head is looking
    s.nYaw, s.nYawV, s.cYaw, s.cYawV = 0, 0, 0, 0 -- her neck and chest, following it
    s.shift, s.shiftV, s.shiftWant = 0, 0, 0
    s.air, s.airV = 0, 0 -- a spring that is her height off the ground, in metres (a leap, a landing)
    s.earX1, s.earXV1, s.earY1, s.earYV1, s.earX2, s.earXV2, s.earY2, s.earYV2 = 0, 0, 0, 0, 0, 0, 0, 0
    s.tx, s.tv, s.ty, s.tyv = {}, {}, {}, {} -- tail segments: pitch (x) and yaw (y), angle and velocity, index (k - 1) * 3 + j
    for i = 1, TAILS * 3 do
        s.tx[i], s.tv[i], s.ty[i], s.tyv[i] = 0, 0, 0, 0
    end
    s.rng = Random.new(math.floor(s.time * 1000) % 100000 + 7)
    s.mo = {}
    for _, name in BONES do
        s.mo[name] = rig.motors[name]
    end
    s.nextGaze = s.time + 1
    s.nextEar = s.time + 2
    s.nextFlick = s.time + 4
    s.nextShift = s.time + 5
    s.gazeYaw, s.gazePitch = 0, 0
    s.wasFly = 0
    s.ready = true
end

function Moonfox.animate(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    local cameraAt = if camera then camera.CFrame.Position else rig.rootPart.Position + Vector3.new(0, 0, -20)
    local away = (cameraAt - rig.rootPart.Position).Magnitude
    if away > FAR then
        return
    end
    local dt, t = min(rig.deltaTime, 0.1), s.time
    if not s.ready then
        local ok, err = pcall(init, rig, s)
        if not ok then -- (a bone the importer dropped: it stays in its rest pose, and says so once)
            s.ready, s.failed = true, true
            warn("Moonfox: its rig is missing a bone: " .. tostring(err))
        end
    end
    if s.failed then
        return
    end
    local u = s.u
    local rng = s.rng
    local mo = s.mo
    PetMotion.track(rig, s, dt)
    local drop = rig.dropToGround(rig, s, t, u, fly, SOLE)
    local G = 1 - fly -- on the ground
    local special = math.sin(math.min(nova * 1.4, 1) * math.pi / 2) -- the special: 0 to 1 and back

    -- ---- her speed, in her own metres a second, and the gait it asks for ----
    local vm = s.vF / u
    local q = s.quad
    PetQuad.advance(q, dt, vm, G)
    local g = q.g
    local walking = g.active
    local phase = q.phase
    local speedN = sm(0.2, 3.2, abs(vm)) -- 0 standing .. 1 at a fast trot
    local accN = clamp(s.accF / u / 3, -1, 1)
    local turnN = clamp(s.yawRate / 1.6, -1, 1)
    local latN = clamp(s.accS / u / 5, -1, 1)

    -- ---- the body: lean with acceleration (it overshoots when she stops), roll into turns, breathe, shift her weight ----
    local leanWant = -0.05 * speedN - 0.05 * accN * G
    s.lean, s.leanV = spring(s.lean, s.leanV, leanWant, 6.5, 0.55, dt)
    local rollWant = 0.11 * latN * G + 0.03 * turnN * speedN
    s.roll, s.rollV = spring(s.roll, s.rollV, rollWant, 7, 0.6, dt)

    if t >= s.nextShift and walking < 0.05 and fly < 0.1 then
        s.nextShift = t + 4 + rng:NextNumber() * 6
        if s.shiftWant ~= 0 and rng:NextNumber() < 0.5 then
            s.shiftWant = 0
        else
            s.shiftWant = if rng:NextNumber() < 0.5 then -1 else 1
        end
    end
    s.shift, s.shiftV = spring(s.shift, s.shiftV, s.shiftWant * (1 - walking) * G, 3.2, 0.9, dt)

    local breath = sin(t * 1.3 + 0.4 * sin(t * 0.17)) -- (her breathing speeds and slows a little)
    local twist = sin(TAU * phase) -- the spine's wave through a stride
    local bounceWave = -cos(2 * TAU * (phase - g.duty / 2)) -- twice a stride: low as each pair takes her weight, high between (the quad's own bounce)
    local pitchWave = sin(2 * TAU * phase + 0.9)

    local gaitPitch = 0.028 * pitchWave * walking * (0.4 + 0.6 * g.trot)
    local aH = 0.5 * s.lean + 0.5 * gaitPitch
    local aS = 0.3 * s.lean + 0.3 * gaitPitch + 0.006 * breath
    local aC = 0.2 * s.lean + 0.2 * gaitPitch + 0.014 * breath
    local frontBase = aH + aS + aC

    -- ---- the legs: footfalls, then three-segment IK onto them ----
    local ang = q.ang
    ang[1], ang[2], ang[3] = aH, aS, aC
    local unload = s.unload -- the hind leg she rests while standing and shifting her weight lifts its paw a little
    unload.BL = max(0, -s.shift) * (1 - walking) * 0.014
    unload.BR = max(0, s.shift) * (1 - walking) * 0.014
    local crouch = PetQuad.solve(q, dt, vm, s.dFwd / u, s.air, 0.085 * (s.roll + 0.03 * s.shift), unload)
    local bounce = q.bounce

    -- ---- a leap and a landing: a push up as she leaves the ground, and a soft squash when she comes down ----
    if fly > 0.5 and s.wasFly <= 0.5 then
        s.airV = 0.9
    elseif fly < 0.5 and s.wasFly >= 0.5 then
        s.airV = -1.0
    end
    s.wasFly = fly
    s.air, s.airV = spring(s.air, s.airV, 0, 9, 0.35, dt)

    -- ---- her head: leads her neck, her neck leads her body; it stays level through her bounce ----
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((cameraAt - rig.rootPart.Position).Unit)
    if t >= s.nextGaze then
        s.nextGaze = t + 1.5 + rng:NextNumber() * 3.5
        s.atYou = rng:NextNumber() < 0.45
        s.gazeYaw, s.gazePitch = (rng:NextNumber() - 0.5) * 1.2, (rng:NextNumber() - 0.5) * 0.3
    end
    local calm = (1 - 0.65 * max(speedN, fly)) * (1 - special)
    local wantYaw = (if s.atYou then clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
    local wantPitch = (if s.atYou then clamp(toYou.Y * 0.5, -0.15, 0.3) else s.gazePitch) * calm
    wantYaw += 0.3 * turnN * speedN -- into a turn she looks where she is going
    s.gYaw, s.gYawV = spring(s.gYaw, s.gYawV, wantYaw, 11, 0.8, dt)
    s.gPitch, s.gPitchV = spring(s.gPitch, s.gPitchV, wantPitch, 11, 0.8, dt)
    s.nYaw, s.nYawV = spring(s.nYaw, s.nYawV, s.gYaw, 6, 0.9, dt) -- (the neck follows the head a beat late)
    s.cYaw, s.cYawV = spring(s.cYaw, s.cYawV, s.gYaw, 3, 1, dt) -- (and the chest after that)
    local headLevel = 0.55 * frontBase -- the body's pitch, taken out of her head
    local neckX = -0.06 * speedN - 0.5 * headLevel + 0.12 * s.gPitch - 0.01 * breath - 0.08 * fly
    local headX = 0.05 - 0.03 * (0.5 + 0.5 * bounceWave) * walking - 0.5 * headLevel + 0.25 * s.gPitch + 0.3 * special + 0.12 * fly
    local headRoll = 0.1 * s.gYaw + 0.5 * s.roll

    -- ---- her ears: springs; flattened by speed, turned by her gaze, flicked now and then ----
    if t >= s.nextEar then
        s.nextEar = t + 1.5 + rng:NextNumber() * 4.5
        if rng:NextNumber() < 0.5 then
            s.earXV1 -= 5
            s.earYV1 += 6
            if rng:NextNumber() < 0.25 then
                s.earXV2 -= 4
            end
        else
            s.earXV2 -= 5
            s.earYV2 -= 6
            if rng:NextNumber() < 0.25 then
                s.earXV1 -= 4
            end
        end
    end
    local earBack = 0.14 * speedN + 0.1 * fly
    s.earX1, s.earXV1 = spring(s.earX1, s.earXV1, -0.04 + earBack + 0.05 * sin(t * 0.8 + 1), 16, 0.35, dt)
    s.earX2, s.earXV2 = spring(s.earX2, s.earXV2, -0.04 + earBack + 0.05 * sin(t * 0.8 + 2), 16, 0.35, dt)
    s.earY1, s.earYV1 = spring(s.earY1, s.earYV1, 0.1 + 0.2 * s.gYaw + 0.1 * special, 16, 0.35, dt)
    s.earY2, s.earYV2 = spring(s.earY2, s.earYV2, -0.1 + 0.2 * s.gYaw - 0.1 * special, 16, 0.35, dt)

    -- ---- her tails ----
    local fan = 0.32 * special
    local streamUp = -(0.1 * speedN + 0.16 * fly + 0.1 * special) -- (they rise and stream back at speed)
    local dYaw = s.dYaw
    local still = 1 - 0.55 * speedN
    local tx, tv, ty, tyv = s.tx, s.tv, s.ty, s.tyv
    if t >= s.nextFlick then -- a flick now and then: one tail gets a quick kick
        s.nextFlick = t + 3 + rng:NextNumber() * 6
        local i0 = (rng:NextInteger(1, TAILS) - 1) * 3
        local side = if rng:NextNumber() < 0.5 then 1 else -1
        for j = 1, 3 do
            tyv[i0 + j] += side * (3.2 + 1.2 * j) * (1 - 0.6 * speedN)
        end
    end
    local near = away < NEAR
    local segs = if near then 3 else 1 -- (far off, only each tail's first segment is a spring; the others follow it)
    local still1 = 0.14 * still
    local gaitSway = 0.05 * walking
    local ph = phase * TAU
    local ww, zz = if near then WW_NEAR else WW_FAR, if near then ZZ_NEAR else ZZ_FAR
    local idleP = 0.1 * still
    local turnPush = dYaw * 0.55
    for k = 1, TAILS do
        local spread = ((TAILS + 1) / 2 - k) / ((TAILS - 1) / 2) -- 1 her left .. -1 her right
        local i0 = (k - 1) * 3
        local close = -0.08 * spread * speedN
        local slow = 0.8 * sin(t * 0.21 + k)
        local amp = 0.85 + 0.15 * sin(t * 0.37 + k * 1.9)
        for j = 1, segs do
            local i = i0 + j
            local w = SEG_W[j]
            -- the sway runs along the fan and down each tail; her stride, speed, turning and acceleration lean on it
            local yawWant = still1 * w * amp * sin(t * 1.1 - k * 0.3 - j * 0.65 + slow) + (if walking > 0.02 then gaitSway * w * sin(ph - j * 0.6 + k * 0.2) else 0)
                + close * (1 + 0.3 * j) - 0.1 * latN * w + (if j == 1 then fan * spread else 0)
            local pitchWant = idleP * w * sin(t * 0.9 - k * 0.22 - j * 0.7) + streamUp * (0.6 + 0.2 * j) - 0.06 * accN * w
            local vy = tyv[i] + (ww[j] * (yawWant - ty[i]) - zz[j] * tyv[i]) * dt
            local vp = tv[i] + (ww[j] * (pitchWant - tx[i]) - zz[j] * tv[i]) * dt
            if j > 1 then -- (each segment catches some of the one before it)
                vy += 0.8 * tyv[i - 1] * dt
                vp += 0.8 * tv[i - 1] * dt
            end
            tyv[i], tv[i] = vy, vp
            -- her turning pushes them the other way (a tail keeps its heading while she swings round it), more toward the tip
            ty[i] += vy * dt - turnPush * w
            tx[i] += vp * dt
        end
        if segs == 1 then
            ty[i0 + 2], tx[i0 + 2] = ty[i0 + 1] * 1.7, tx[i0 + 1] * 1.7
            ty[i0 + 3], tx[i0 + 3] = ty[i0 + 1] * 2.4, tx[i0 + 1] * 2.4
        end
    end

    -- ---- write it all ----
    local lifted = (-drop / u + bounce + s.air - crouch) * u + 0.03 * u * fly
    mo.Hips.Transform = CFrame.new(0, lifted, 0) * CFrame.Angles(aH + 0.06 * fly - 0.08 * special, 0.03 * twist * walking,
        s.roll * 0.6 + 0.02 * twist * walking * g.trot + 0.025 * s.shift)
    mo.Spine.Transform = CFrame.Angles(aS, -0.035 * twist * walking, 0.5 * s.roll)
    mo.Chest.Transform = CFrame.Angles(aC, -0.03 * twist * walking + 0.12 * s.cYaw * G, -0.03 * s.shift)
    mo.Neck.Transform = CFrame.Angles(neckX, 0.38 * s.nYaw, 0.3 * s.roll)
    mo.Head.Transform = CFrame.Angles(headX, 0.5 * (s.gYaw - 0.38 * s.nYaw), headRoll)
    mo.EarL.Transform = CFrame.Angles(s.earX1, s.earY1, 0.08 + 0.06 * special)
    mo.EarR.Transform = CFrame.Angles(s.earX2, s.earY2, -0.08 - 0.06 * special)
    mo.TailRoot.Transform = CFrame.Angles(0.02 * sin(t * 0.8) - 0.08 * speedN - 0.1 * special - 0.1 * fly + 0.15 * s.lean, 0.03 * twist * walking, 0)
    for i = 1, 4 do
        local key = LEG_KEYS[i]
        local leg, m = q.legs[key], s.legMo[key]
        local a = m[5]
        m[1].Transform = CFrame.Angles(lerp(leg.a1, a[1], fly), 0, 0)
        m[2].Transform = CFrame.Angles(lerp(leg.a2, a[2], fly), 0, 0)
        m[3].Transform = CFrame.Angles(lerp(leg.a3, a[3], fly), 0, 0)
        m[4].Transform = CFrame.Angles(lerp(leg.a4, a[4], fly), 0, 0)
    end
    for k = 1, TAILS do
        local names = TAIL_NAMES[k]
        local i0 = (k - 1) * 3
        for j = 1, 3 do
            mo[names[j]].Transform = CFrame.Angles(tx[i0 + j], ty[i0 + j], 0)
        end
    end
end

return Moonfox

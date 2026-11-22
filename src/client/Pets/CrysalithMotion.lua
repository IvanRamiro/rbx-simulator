-- Crysalith's animation, "The Eternal Frost" (Secret, the Exclusive Egg; skinned on 33 bones): a heavy frost-draconic guardian with a crown of crystal antlers.
-- Everything about her moves like weight. She walks in a plant-and-shift: each foot is solved onto the ground (PetQuad: it stays planted, whatever her
-- speed or size), the body sinks over a stretched leg, rolls and twists through four spine bones over each planted foot, and every footfall lands as a
-- thud that runs up through her: a dip of the body, a shiver through the antlers, a jolt along the tail. Standing she breathes deep and slow (her chest
-- and shoulders rise, her jaw loosens on the out-breath), shifts her weight rarely, turns her head slowly and deliberately with her neck following; her
-- antlers are two crystal chains on springs that ring after the head has stopped, with a slow hum of their own; her four-bone tail drags behind, set
-- swinging by her turns and stops. In the air her legs fold up under her and her antlers and tail stream; she lands with a heavy squash.
local PetMotion = require(script.Parent:WaitForChild("PetMotion"))
local PetQuad = require(script.Parent:WaitForChild("PetQuad"))

local Crysalith = {}

local sin, abs, min, max, clamp = math.sin, math.abs, math.min, math.max, math.clamp
local sm = PetMotion.smoothstep
local lerp = PetMotion.lerp
local spring = PetMotion.spring
local TAU = 2 * math.pi

local FAR = 90 -- studs from the camera past which nobody can see it move: its bones rest
local LEG_KEYS = { "BL", "FL", "BR", "FR" }

local BONES = { "Hips", "Spine1", "Spine2", "Chest", "Neck1", "Neck2", "Head", "Jaw", "AntlerL1", "AntlerL2", "AntlerR1", "AntlerR2", "Tail1", "Tail2", "Tail3", "Tail4" }
for _, key in LEG_KEYS do
    for k = 1, 3 do
        table.insert(BONES, "Leg" .. key .. k)
    end
    table.insert(BONES, "Foot" .. key)
end
Crysalith.BONES = BONES
Crysalith.POINTS = { "Head", "AntlerL2", "AntlerR2" }

-- a heavy walker: slow steps, long stances, mostly a walk
local GAIT = {
    v0 = 0.3, v1 = 3.6, cadence = { 0.8, 2.3 }, duty = { 0.76, 0.52 }, trotAt = { 1.4, 3.4 }, lift = { 0.07, 0.12 }, bounce = { 0.006, 0.02 }, stride = 0.65,
    dutyFrom = 0.6, dutyTo = 3.6, active = { 0.15, 0.5 },
}

-- in the air: forelegs and hind legs folded up (the safe lift poses checked in Blender: hip, middle, ankle, foot)
local FLY = {
    BL = { 0.5, -0.9, 0.9, 0.3 }, BR = { 0.5, -0.9, 0.9, 0.3 },
    FL = { 0.55, -1.0, 0.55, 0.25 }, FR = { 0.55, -1.0, 0.55, 0.25 },
}

local TAIL_W = { 0.5, 0.9, 1.2, 1.5 }
local TAIL_FREQ = { 4.6, 4.0, 3.5, 3.1 }
local TAIL_DAMP = { 0.7, 0.55, 0.5, 0.45 }
local TAIL_NAMES = { "Tail1", "Tail2", "Tail3", "Tail4" }
local ANT_NAMES = { "AntlerL1", "AntlerL2", "AntlerR1", "AntlerR2" } -- index 1, 2 left; 3, 4 right
local ANT_FREQ = { 4.2, 3.2, 4.2, 3.2 }
local ANT_DAMP = { 0.3, 0.22, 0.3, 0.22 }

local function init(rig, s)
    local u = rig.meters
    s.u = u
    local legs = {}
    for _, key in LEG_KEYS do
        legs[key] = { "Leg" .. key .. "1", "Leg" .. key .. "2", "Leg" .. key .. "3", "Foot" .. key }
    end
    s.quad = PetQuad.new(rig, {
        spine = { "Hips", "Spine1", "Spine2", "Chest" }, legs = legs, gait = GAIT, reachK = 0.9, maxCrouch = 0.2,
        limit = { -- (the Blender rig's safe turns, a little inside)
            front = { { -0.65, 0.7 }, { -1.3, 1.25 }, { -1.4, 1.4 } },
            hind = { { -0.8, 0.85 }, { -0.95, 0.55 }, { -1.4, 1.25 } },
        },
        psiFront = 0.4, psiHind = 0.6, flickFront = -0.25, flickHind = 0.25,
    })
    s.legMo = {}
    for _, key in LEG_KEYS do
        local names = legs[key]
        s.legMo[key] = { rig.motors[names[1]], rig.motors[names[2]], rig.motors[names[3]], rig.motors[names[4]], FLY[key] }
    end
    s.sole = -rig.restCF.Root.Position.Y / u -- metres from the middle of its box down to its hooves
    s.mo = {}
    for _, name in BONES do
        s.mo[name] = rig.motors[name]
    end
    s.lean, s.leanV, s.roll, s.rollV = 0, 0, 0, 0
    s.gYaw, s.gYawV, s.gPitch, s.gPitchV = 0, 0, 0, 0
    s.nYaw, s.nYawV, s.nPitch, s.nPitchV = 0, 0, 0, 0
    s.thud, s.thudV = 0, 0 -- the body's dip as a foot comes down, metres
    s.shift, s.shiftV, s.shiftWant = 0, 0, 0
    s.air, s.airV = 0, 0
    s.jaw, s.jawV = 0, 0
    s.ax, s.av, s.az, s.azv = { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 } -- antlers: pitch and roll, angle and velocity
    s.tx, s.tv, s.ty, s.tyv = { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 } -- tail: pitch and yaw
    s.rng = Random.new(math.floor(s.time * 1000) % 100000 + 11)
    s.nextGaze = s.time + 1.5
    s.nextShift = s.time + 6
    s.nextYawn = s.time + 12
    s.yawnAt = -10
    s.gazeYaw, s.gazePitch = 0, 0
    s.prevHeadYaw, s.prevHeadPitch = 0, 0
    s.wasFly = 0
    s.ready = true
end

function Crysalith.animate(rig, s, moving, fly, nova)
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
            warn("Crysalith: its rig is missing a bone: " .. tostring(err))
        end
    end
    if s.failed then
        return
    end
    local u = s.u
    local rng = s.rng
    local mo = s.mo
    PetMotion.track(rig, s, dt)
    local drop = rig.dropToGround(rig, s, t, u, fly, s.sole)
    local G = 1 - fly
    local special = math.sin(math.min(nova * 1.4, 1) * math.pi / 2)

    local vm = s.vF / u
    local q = s.quad
    PetQuad.advance(q, dt, vm, G)
    local g = q.g
    local walking = g.active
    local phase = q.phase
    local speedN = sm(0.3, 3.6, abs(vm))
    local accN = clamp(s.accF / u / 3, -1, 1)
    local turnN = clamp(s.yawRate / 1.4, -1, 1)
    local latN = clamp(s.accS / u / 5, -1, 1)

    -- ---- the body: a heavy lean that overshoots on a stop, a roll over each planted foot, a deep slow breath ----
    s.lean, s.leanV = spring(s.lean, s.leanV, -0.035 * speedN - 0.04 * accN * G, 5, 0.6, dt)
    local stepRoll = -0.05 * sin(TAU * (phase - 0.05)) * walking * (1 - 0.4 * g.trot)
    s.roll, s.rollV = spring(s.roll, s.rollV, 0.08 * latN * G + 0.02 * turnN * speedN + stepRoll, 9, 0.7, dt)
    if t >= s.nextShift and walking < 0.05 and fly < 0.1 then
        s.nextShift = t + 7 + rng:NextNumber() * 8
        if s.shiftWant ~= 0 and rng:NextNumber() < 0.5 then
            s.shiftWant = 0
        else
            s.shiftWant = if rng:NextNumber() < 0.5 then -1 else 1
        end
    end
    s.shift, s.shiftV = spring(s.shift, s.shiftV, s.shiftWant * (1 - walking) * G, 2.2, 0.95, dt)
    local breath = sin(t * 1.15 + 0.3 * sin(t * 0.11))
    local breathUp = 0.5 + 0.5 * breath
    local twist = sin(TAU * phase)
    local pitchWave = sin(2 * TAU * phase + 0.7)
    local gaitPitch = 0.02 * pitchWave * walking

    local ang = q.ang
    ang[1] = 0.35 * s.lean + 0.4 * gaitPitch
    ang[2] = 0.25 * s.lean + 0.3 * gaitPitch + 0.006 * breath
    ang[3] = 0.2 * s.lean + 0.2 * gaitPitch + 0.008 * breath
    ang[4] = 0.2 * s.lean + 0.1 * gaitPitch + 0.016 * breath
    local frontBase = ang[1] + ang[2] + ang[3] + ang[4]
    local unload = s.unloadT
    if not unload then
        unload = { BL = 0, BR = 0, FL = 0, FR = 0 }
        s.unloadT = unload
    end
    unload.BL = max(0, -s.shift) * (1 - walking) * 0.03
    unload.BR = max(0, s.shift) * (1 - walking) * 0.03
    unload.FL = max(0, -s.shift) * (1 - walking) * 0.012
    unload.FR = max(0, s.shift) * (1 - walking) * 0.012
    local crouch = PetQuad.solve(q, dt, vm, s.dFwd / u, s.air + s.thud, 0.14 * (s.roll + 0.03 * s.shift), unload)
    local bounce = q.bounce

    -- ---- footfalls: each one lands with a thud that runs up through her ----
    local kick = 0
    for i = 1, 4 do
        if q.touch[LEG_KEYS[i]] then
            kick += 1
        end
    end
    if kick > 0 and G > 0.5 then
        local weight = (0.25 + 0.5 * speedN) * kick
        s.thudV -= 0.45 * weight
        for a = 1, 4 do -- the antlers shiver, the tail jolts
            s.av[a] -= (2.4 + a * 0.2) * weight * (if a % 2 == 1 then 1 else 1.4)
            s.azv[a] += (if a <= 2 then 1 else -1) * 1.2 * weight
        end
        for j = 1, 4 do
            s.tv[j] -= 1.2 * TAIL_W[j] * weight
        end
    end
    s.thud, s.thudV = spring(s.thud, s.thudV, 0, 13, 0.4, dt)

    -- ---- a leap and a landing ----
    if fly > 0.5 and s.wasFly <= 0.5 then
        s.airV = 0.8
    elseif fly < 0.5 and s.wasFly >= 0.5 then
        s.airV = -1.6
        for a = 1, 4 do
            s.av[a] -= 4
        end
    end
    s.wasFly = fly
    s.air, s.airV = spring(s.air, s.airV, 0, 8, 0.3, dt)

    -- ---- her head: slow, deliberate, the neck following ----
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((cameraAt - rig.rootPart.Position).Unit)
    if t >= s.nextGaze then
        s.nextGaze = t + 3 + rng:NextNumber() * 5
        s.atYou = rng:NextNumber() < 0.4
        s.gazeYaw, s.gazePitch = (rng:NextNumber() - 0.5) * 1.1, (rng:NextNumber() - 0.5) * 0.25
    end
    local calm = (1 - 0.7 * max(speedN, fly)) * (1 - special)
    local wantYaw = (if s.atYou then clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw) * calm + 0.2 * turnN * speedN
    local wantPitch = (if s.atYou then clamp(toYou.Y * 0.4, -0.1, 0.25) else s.gazePitch) * calm
    s.gYaw, s.gYawV = spring(s.gYaw, s.gYawV, wantYaw, 5.5, 1.0, dt)
    s.gPitch, s.gPitchV = spring(s.gPitch, s.gPitchV, wantPitch, 5.5, 1.0, dt)
    s.nYaw, s.nYawV = spring(s.nYaw, s.nYawV, s.gYaw, 3.6, 1.0, dt)
    s.nPitch, s.nPitchV = spring(s.nPitch, s.nPitchV, s.gPitch, 3.6, 1.0, dt)
    local level = 0.6 * frontBase
    local neck1X = -0.5 * level - 0.03 * speedN + 0.4 * s.nPitch - 0.01 * breath - 0.1 * fly
    local neck2X = -0.3 * level + 0.4 * s.nPitch + 0.01 * breathUp - 0.05 * fly
    local headX = -0.2 * level + 0.35 * s.gPitch + 0.3 * special - 0.02 * breathUp + 0.08 * fly
    -- her jaw: loosens a little on the out-breath, and now and then she works it
    if t >= s.nextYawn and walking < 0.1 then
        s.nextYawn = t + 14 + rng:NextNumber() * 14
        s.yawnAt = t
    end
    local yawnT = (t - s.yawnAt) / 2.6
    local yawn = if yawnT >= 0 and yawnT < 1 then sin(math.pi * yawnT) ^ 2 else 0
    s.jaw, s.jawV = spring(s.jaw, s.jawV, -(0.03 + 0.05 * (1 - breathUp) * (1 - speedN) + 0.18 * yawn + 0.25 * special), 8, 0.8, dt)

    -- ---- her antlers: two chains of crystal on slow springs, a hum of their own, shaken by her head and her steps ----
    local headYaw = 0.6 * s.gYaw + 0.4 * s.nYaw
    local headPitch = headX + neck2X
    local dHY, dHP = PetMotion.wrap(headYaw - s.prevHeadYaw), headPitch - s.prevHeadPitch
    s.prevHeadYaw, s.prevHeadPitch = headYaw, headPitch
    local ax, av, az, azv = s.ax, s.av, s.az, s.azv
    for a = 1, 4 do
        local side = if a <= 2 then 1 else -1
        local hum = sin(t * (0.9 + 0.08 * a) + a * 1.7) * 0.03 + sin(t * 0.37 + a) * 0.02
        local w = if a % 2 == 1 then 1 else 1.5
        ax[a], av[a] = spring(ax[a], av[a], hum * (1 - 0.5 * speedN) - 0.02 * speedN, ANT_FREQ[a], ANT_DAMP[a], dt)
        az[a], azv[a] = spring(az[a], azv[a], side * 0.03 * sin(t * 0.8 + a * 0.9) * (1 - 0.5 * speedN) + side * 0.02 * speedN, ANT_FREQ[a], ANT_DAMP[a], dt)
        ax[a] -= dHP * 0.5 * w
        az[a] += side * dHY * 0.7 * w
    end

    -- ---- her tail: a heavy drag ----
    local tx, tv, ty, tyv = s.tx, s.tv, s.ty, s.tyv
    local lift = -(0.1 * speedN + 0.14 * fly)
    for j = 1, 4 do
        local w = TAIL_W[j]
        local wave = sin(t * 0.55 - j * 0.7 + 0.5 * sin(t * 0.13))
        local yawWant = 0.09 * w * wave * (1 - 0.6 * speedN) + 0.05 * w * sin(phase * TAU - j * 0.5) * walking - 0.1 * latN * w
        local pitchWant = lift * (0.5 + 0.2 * j) + 0.02 * w * sin(t * 0.4 + j) - 0.05 * accN * w
        ty[j], tyv[j] = spring(ty[j], tyv[j], yawWant, TAIL_FREQ[j], TAIL_DAMP[j], dt)
        tx[j], tv[j] = spring(tx[j], tv[j], pitchWant, TAIL_FREQ[j], TAIL_DAMP[j], dt)
        ty[j] -= s.dYaw * 0.6 * w
        if j > 1 then
            tyv[j] += 0.6 * tyv[j - 1] * dt
            tv[j] += 0.6 * tv[j - 1] * dt
        end
    end

    -- ---- write it all ----
    local lifted = (-drop / u + bounce + s.air + s.thud - crouch) * u + 0.04 * u * fly
    mo.Hips.Transform = CFrame.new(0, lifted, 0) * CFrame.Angles(ang[1] + 0.05 * fly - 0.06 * special, 0.05 * twist * walking, s.roll * 0.7 + 0.02 * s.shift)
    mo.Spine1.Transform = CFrame.Angles(ang[2], -0.02 * twist * walking, 0.3 * s.roll)
    mo.Spine2.Transform = CFrame.Angles(ang[3], -0.035 * twist * walking, -0.3 * s.roll - 0.015 * s.shift)
    mo.Chest.Transform = CFrame.Angles(ang[4], -0.04 * twist * walking + 0.1 * s.nYaw * G, -0.5 * s.roll)
    mo.Neck1.Transform = CFrame.Angles(neck1X, 0.3 * s.nYaw, 0.2 * s.roll)
    mo.Neck2.Transform = CFrame.Angles(neck2X, 0.4 * s.nYaw, 0.15 * s.roll)
    mo.Head.Transform = CFrame.Angles(headX, 0.5 * (s.gYaw - 0.7 * s.nYaw), 0.1 * s.gYaw + 0.4 * s.roll)
    mo.Jaw.Transform = CFrame.Angles(s.jaw, 0, 0)
    for a = 1, 4 do
        mo[ANT_NAMES[a]].Transform = CFrame.Angles(ax[a], 0, az[a])
    end
    for j = 1, 4 do
        mo[TAIL_NAMES[j]].Transform = CFrame.Angles(tx[j], ty[j], 0)
    end
    for i = 1, 4 do
        local key = LEG_KEYS[i]
        local leg, m = q.legs[key], s.legMo[key]
        local a = m[5]
        m[1].Transform = CFrame.Angles(lerp(leg.a1, a[1], fly), 0, 0)
        m[2].Transform = CFrame.Angles(lerp(leg.a2, a[2], fly), 0, 0)
        m[3].Transform = CFrame.Angles(lerp(leg.a3, a[3], fly), 0, 0)
        m[4].Transform = CFrame.Angles(lerp(leg.a4, a[4], fly), 0, 0)
    end
end

return Crysalith

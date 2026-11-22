-- The Eclipse Dreadwing's animation, "Devourer of Stars" (Divine, the Exclusive Egg; skinned on 45 bones): a raven-drake of blades that hovers by its owner.
-- Each wing is a chain: a shoulder, an elbow, a wrist, and below the wrist three groups of primary feathers and two of secondaries; the stroke runs out
-- along it with a lag at every joint, so the arm leads, the hand follows and the feathers trail and fan: a quick, powerful downstroke (about two fifths of
-- the beat) and a slower upstroke with the elbow and wrist folded in, as a big bird's wing goes. At rest it hovers on slow, heavy beats; moving, it leans in,
-- beats deeper and glides between bursts with its wings held wide and flickering; when its owner flies it beats hard; it flares its wings as it lands and
-- surges as it leaves the ground. Its body does what the wings ask of it: it rises on each downstroke and sinks on the recovery, pitches its chest up as the
-- wings come down, banks into turns; its neck bobs against it and its head holds steady, low and watchful, now and then sweeping slowly round, jaw working
-- in a hiss; its tail is the rudder (a four-bone spring that counter-swings turns and beats); its legs hang and trail, swinging on springs after the body.
local PetMotion = require(script.Parent:WaitForChild("PetMotion"))

local Dreadwing = {}

local sin, cos, abs, min, max, clamp = math.sin, math.cos, math.abs, math.min, math.max, math.clamp
local sm = PetMotion.smoothstep
local lerp = PetMotion.lerp
local spring = PetMotion.spring
local TAU = 2 * math.pi

local FAR = 90 -- studs from the camera past which nobody can see it move: its bones rest
local SIDES = { "L", "R" }
local LEG_KEYS = { "FL", "FR", "BL", "BR" }

local BONES = { "Hips", "Spine", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw", "Tail1", "Tail2", "Tail3", "Tail4" }
local WING_NAMES = {} -- [side] = { w1, w2, w3, p1, p2, p3, s1, s2 }
for _, side in SIDES do
    WING_NAMES[side] = { "Wing" .. side .. "1", "Wing" .. side .. "2", "Wing" .. side .. "3", "Prim" .. side .. "1", "Prim" .. side .. "2", "Prim" .. side .. "3",
        "Sec" .. side .. "1", "Sec" .. side .. "2" }
    for _, name in WING_NAMES[side] do
        table.insert(BONES, name)
    end
end
local LEG_NAMES = {}
for _, key in LEG_KEYS do
    LEG_NAMES[key] = { "Leg" .. key .. "1", "Leg" .. key .. "2", "Leg" .. key .. "3", "Foot" .. key }
    for _, name in LEG_NAMES[key] do
        table.insert(BONES, name)
    end
end
Dreadwing.BONES = BONES
Dreadwing.POINTS = { "Head" }

-- the stroke: its phase (0 the top, the downstroke first) warped so the downstroke takes this share of a beat
local DOWN = 0.4
local function stroke(ph)
    ph = ph % 1
    local psi = if ph < DOWN then 0.5 * ph / DOWN else 0.5 + 0.5 * (ph - DOWN) / (1 - DOWN)
    local flap = -cos(TAU * psi) -- -1 at the top, +1 at the bottom
    local flex = 0
    if ph >= DOWN then
        flex = sin(math.pi * (ph - DOWN) / (1 - DOWN)) ^ 0.8 -- the elbow and wrist fold in over the upstroke
    end
    return flap, flex
end

-- the segments' lag behind the shoulder (a share of a beat): elbow, wrist, the primaries, the secondaries
local LAG = { 0.07, 0.13, 0.17, 0.2, 0.23, 0.09, 0.11 }

-- the legs: hanging at rest, trailing when it goes. Four turns each (hip, middle, lower, foot), pitch; the safe ranges are in the Blender rig report.
local HANG = { FL = { 0.4, -0.35, 0.65, 0.3 }, FR = { 0.4, -0.35, 0.65, 0.3 }, BL = { -0.3, -0.2, 0.4, 0.3 }, BR = { -0.3, -0.2, 0.4, 0.3 } }
local TUCK = { FL = { 0.8, -0.5, 1.0, 0.4 }, FR = { 0.8, -0.5, 1.0, 0.4 }, BL = { -0.6, -0.35, 0.7, 0.4 }, BR = { -0.6, -0.35, 0.7, 0.4 } }

local TAIL_W = { 0.5, 0.9, 1.2, 1.5 }
local TAIL_FREQ = { 6, 5.2, 4.4, 3.8 }
local TAIL_DAMP = { 0.7, 0.55, 0.45, 0.4 }
local TAIL_NAMES = { "Tail1", "Tail2", "Tail3", "Tail4" }

local HOVER = 0.32 -- metres its feet hang above the ground when it hovers beside a walking owner

local function init(rig, s)
    local u = rig.meters
    s.u = u
    s.sole = -rig.restCF.Root.Position.Y / u + 0.04 -- metres from the middle of its box down to its talons
    s.mo = {}
    for _, name in BONES do
        s.mo[name] = rig.motors[name]
    end
    s.legMo = {}
    for _, key in LEG_KEYS do
        local n = LEG_NAMES[key]
        s.legMo[key] = { rig.motors[n[1]], rig.motors[n[2]], rig.motors[n[3]], rig.motors[n[4]] }
    end
    s.wingMo = {}
    for _, side in SIDES do
        local names, m = WING_NAMES[side], {}
        for i, name in names do
            m[i] = rig.motors[name]
        end
        s.wingMo[side] = m
    end
    s.beat = math.random() -- where it is in its stroke
    s.glide, s.glideV, s.glideWant = 0, 0, 0
    s.surge, s.surgeV = 0, 0 -- the push as it leaves the ground, the flare as it lands (spring: positive surge, negative flare)
    s.roll, s.rollV = 0, 0
    s.lean, s.leanV = 0, 0
    s.hover, s.hoverV = 0, 0 -- the height the body is lifted to hover
    s.lift, s.liftV = 0, 0
    s.gYaw, s.gYawV, s.gPitch, s.gPitchV = 0, 0, 0, 0
    s.nYaw, s.nYawV = 0, 0
    s.jaw, s.jawV = 0, 0
    s.legx, s.legv = table.create(16, 0), table.create(16, 0) -- leg springs: [(leg - 1) * 4 + joint]
    s.tx, s.tv, s.ty, s.tyv = { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 }
    s.rng = Random.new(math.floor(s.time * 1000) % 100000 + 13)
    s.nextGaze, s.nextGlide, s.nextHiss = s.time + 1.5, s.time + 3, s.time + 10
    s.hissAt = -10
    s.gazeYaw, s.gazePitch = 0, 0
    s.wasFly = 0
    s.lastLift = 0
    s.ready = true
end

function Dreadwing.animate(rig, s, moving, fly, nova)
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
            warn("Dreadwing: its rig is missing a bone: " .. tostring(err))
        end
    end
    if s.failed then
        return
    end
    local u = s.u
    local rng = s.rng
    local mo = s.mo
    PetMotion.track(rig, s, dt)
    rig.dropToGround(rig, s, t, u, fly, s.sole) -- (it finds the ground under it; s.ground)
    local G = 1 - fly
    local special = math.sin(math.min(nova * 1.4, 1) * math.pi / 2)

    local vm = s.vF / u
    local speedN = sm(0.3, 3.5, abs(vm)) -- 0 hovering .. 1 cruising at a run
    local accN = clamp(s.accF / u / 3, -1, 1)
    local turnN = clamp(s.yawRate / 1.4, -1, 1)
    local latN = clamp(s.accS / u / 5, -1, 1)
    local climb = clamp(s.vY / u / 2, -1, 1) -- (rising or sinking, a share of 2 m/s)
    local pace = max(speedN * 0.55, fly) -- how hard it is working

    -- ---- the wings' beat: slow and heavy at a hover, deeper and quicker on the move, hard in flight; a glide now and then once it is going ----
    if t >= s.nextGlide then
        local going = max(speedN, fly) > 0.45
        s.nextGlide = t + (if going then 1 + rng:NextNumber() * 2.2 else 2 + rng:NextNumber() * 3)
        s.glideWant = if going and s.glideWant == 0 and rng:NextNumber() < 0.55 then 1 else 0
    end
    s.glide, s.glideV = spring(s.glide, s.glideV, s.glideWant * (0.6 + 0.4 * fly), 7, 0.9, dt)
    local rate = lerp(1.15, 1.9, pace) * (1 + 0.25 * s.surge) * (1 - 0.7 * s.glide)
    s.beat = (s.beat + dt * rate) % 1
    local beat = s.beat
    local power = lerp(0.8, 1.05, pace) * (1 + 0.3 * clamp(s.surge, 0, 2)) -- how big the stroke is
    local open = 1 - 0.8 * s.glide -- a gliding wing is held out, almost still

    -- ---- landing and take-off ----
    if fly > 0.5 and s.wasFly <= 0.5 then
        s.surgeV = 6
    elseif fly < 0.5 and s.wasFly >= 0.5 then
        s.surgeV = -7
    end
    s.wasFly = fly
    s.surge, s.surgeV = spring(s.surge, s.surgeV, 0, 5, 0.45, dt)

    -- ---- body: rolls into a turn, leans into a run, rises on the downstroke and sinks on the recovery ----
    s.roll, s.rollV = spring(s.roll, s.rollV, 0.22 * latN + 0.05 * turnN * pace, 5, 0.7, dt)
    s.lean, s.leanV = spring(s.lean, s.leanV, -0.1 * speedN - 0.07 * accN - 0.1 * fly * speedN, 4.5, 0.65, dt)
    local flap0 = stroke(beat)
    local body = flap0 * open
    -- hovering: its feet are held just above the ground, whatever its owner's stride does to it; in the air it keeps to its owner's height
    local hoverWant = 0
    if s.ground then
        hoverWant = -(rig.rootPart.Position.Y - s.sole * u - s.ground - HOVER * u) / u
    end
    s.hover, s.hoverV = spring(s.hover, s.hoverV, hoverWant * G, 4, 0.9, dt)
    local bob = 0.055 * body * power * (1 - 0.5 * s.glide) + 0.012 * sin(t * 0.9)
    s.lift, s.liftV = spring(s.lift, s.liftV, bob, 14, 0.5, dt)
    local liftVel = (s.lift - s.lastLift) / dt
    s.lastLift = s.lift
    local bodyPitch = s.lean + 0.045 * body * power * open + 0.05 * climb
    local hipsX, spineX, chestX = 0.3 * bodyPitch, 0.3 * bodyPitch, 0.4 * bodyPitch

    -- ---- wings ----
    local f3, x3 = stroke(beat - LAG[2])
    local f2, x2 = stroke(beat - LAG[1])
    local fP1, _ = stroke(beat - LAG[3])
    local fP2, _ = stroke(beat - LAG[4])
    local fP3, _ = stroke(beat - LAG[5])
    local fS1, _ = stroke(beat - LAG[6])
    local fS2, _ = stroke(beat - LAG[7])
    local hold = 0.18 * special
    for i = 1, 2 do
        local side = SIDES[i]
        local sg = if i == 1 then 1 else -1 -- left: a turn down is positive roll; right: negative
        local m = s.wingMo[side]
        local bank = sg * 0.12 * turnN * pace -- the wing on the inside of a turn dips, the outside lifts
        local centre = lerp(0.2, 0.3, pace) - 0.34 * s.glide - 0.5 * clamp(-s.surge, 0, 1.2) + 0.12 * special -- (a flare lifts them)
        local amp = 0.7 * power * open
        local down = clamp(centre + amp * flap0 + hold, -0.7, 1.0)
        m[1].Transform = CFrame.Angles(-0.1 * flap0 * open - 0.02 * speedN, sg * (0.1 * flap0 * open - 0.08 * s.glide - 0.1 * pace), sg * down + sg * bank)
        m[2].Transform = CFrame.Angles(-0.55 * x2 * power * open, sg * (-0.08 * s.glide), sg * 0.18 * f2 * power * open)
        m[3].Transform = CFrame.Angles(-0.6 * x3 * power * open, sg * (0.1 + 0.25 * x3 * open - 0.12 * s.glide), sg * 0.22 * f3 * power * open)
        local spread = 0.12 + 0.1 * s.glide + 0.06 * (1 - x3) * open
        local flutter = 0.07 * s.glide * sin(t * 11 + i * 2.1)
        m[4].Transform = CFrame.Angles(0, sg * spread, sg * (0.22 * fP1 * power * open + flutter))
        m[5].Transform = CFrame.Angles(0, sg * spread * 1.4, sg * (0.3 * fP2 * power * open + flutter * 1.3))
        m[6].Transform = CFrame.Angles(0, sg * spread * 1.8, sg * (0.38 * fP3 * power * open + flutter * 1.6))
        m[7].Transform = CFrame.Angles(0, sg * 0.05, sg * 0.2 * fS1 * power * open)
        m[8].Transform = CFrame.Angles(0, sg * 0.08, sg * 0.26 * fS2 * power * open)
    end

    -- ---- the head: low and watchful, steady while the body works; now and then it turns slowly round, or hisses ----
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((cameraAt - rig.rootPart.Position).Unit)
    if t >= s.nextGaze then
        s.nextGaze = t + 2.5 + rng:NextNumber() * 4
        s.atYou = rng:NextNumber() < 0.4
        s.gazeYaw, s.gazePitch = (rng:NextNumber() - 0.5) * 1.3, (rng:NextNumber() - 0.5) * 0.3
    end
    local calm = (1 - 0.7 * pace) * (1 - special)
    local wantYaw = (if s.atYou then clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm + 0.25 * turnN * pace
    local wantPitch = (if s.atYou then clamp(toYou.Y * 0.4, -0.15, 0.25) else s.gazePitch) * calm
    s.gYaw, s.gYawV = spring(s.gYaw, s.gYawV, wantYaw, 9, 0.85, dt)
    s.gPitch, s.gPitchV = spring(s.gPitch, s.gPitchV, wantPitch, 9, 0.85, dt)
    s.nYaw, s.nYawV = spring(s.nYaw, s.nYawV, s.gYaw, 5, 0.9, dt)
    if t >= s.nextHiss and pace < 0.4 then
        s.nextHiss = t + 12 + rng:NextNumber() * 14
        s.hissAt = t
    end
    local hissT = (t - s.hissAt) / 1.1
    local hiss = if hissT >= 0 and hissT < 1 then sin(math.pi * hissT) ^ 2 else 0
    s.jaw, s.jawV = spring(s.jaw, s.jawV, -(0.02 + 0.04 * (0.5 + 0.5 * sin(t * 1.1)) + 0.4 * hiss + 0.3 * special), 10, 0.7, dt)
    local keep = hipsX + spineX + chestX -- the body's pitch, taken out of its neck and head
    local neck1X = -0.5 * keep + 0.03 * body * power - 0.03 * pace + 0.2 * s.gPitch
    local neck2X = -0.3 * keep + 0.03 * body * power + 0.25 * s.gPitch + 0.03 * hiss
    local neck3X = -0.2 * keep - 0.03 * body * power + 0.25 * s.gPitch - 0.04 + 0.1 * hiss + 0.25 * special
    local headX = -0.1 * keep + 0.25 * s.gPitch + 0.03 - 0.06 * hiss
    local headRoll = 0.5 * s.roll + 0.1 * s.gYaw

    -- ---- the tail, its rudder ----
    local tx, tv, ty, tyv = s.tx, s.tv, s.ty, s.tyv
    local fT = stroke(beat - 0.2)
    for j = 1, 4 do
        local w = TAIL_W[j]
        local yawWant = 0.07 * w * sin(t * 0.8 - j * 0.6) * (1 - 0.5 * pace) - 0.14 * latN * w
        local pitchWant = 0.1 * w * fT * power * open - 0.07 * pace * w - 0.1 * fly * w - 0.05 * accN * w + 0.1 * special * w
        ty[j], tyv[j] = spring(ty[j], tyv[j], yawWant, TAIL_FREQ[j], TAIL_DAMP[j], dt)
        tx[j], tv[j] = spring(tx[j], tv[j], pitchWant, TAIL_FREQ[j], TAIL_DAMP[j], dt)
        ty[j] -= s.dYaw * 0.7 * w
        if j > 1 then
            tyv[j] += 0.6 * tyv[j - 1] * dt
            tv[j] += 0.6 * tv[j - 1] * dt
        end
    end

    -- ---- the legs: hanging and trailing, swinging on springs after the body ----
    local tuck = clamp(0.25 + 0.55 * speedN + 0.5 * fly, 0, 1)
    local legx, legv = s.legx, s.legv
    for i = 1, 4 do
        local key = LEG_KEYS[i]
        local hang, tight = HANG[key], TUCK[key]
        local m = s.legMo[key]
        for j = 1, 4 do
            local k = (i - 1) * 4 + j
            local want = lerp(hang[j], tight[j], tuck)
            if j == 1 then
                want += -0.5 * liftVel * 0.4 - 0.15 * accN -- (the body's rise and its speed-up swing the legs back)
            end
            legx[k], legv[k] = spring(legx[k], legv[k], want, 6 - 0.4 * j, 0.4, dt)
        end
        m[1].Transform = CFrame.Angles(legx[(i - 1) * 4 + 1], 0, 0)
        m[2].Transform = CFrame.Angles(legx[(i - 1) * 4 + 2], 0, 0)
        m[3].Transform = CFrame.Angles(legx[(i - 1) * 4 + 3], 0, 0)
        m[4].Transform = CFrame.Angles(legx[(i - 1) * 4 + 4], 0, 0)
    end

    -- ---- write the body ----
    local lifted = (s.hover + s.lift + 0.04 * fly) * u
    mo.Hips.Transform = CFrame.new(0, lifted, 0) * CFrame.Angles(hipsX - 0.04 * special, 0.02 * turnN, s.roll)
    mo.Spine.Transform = CFrame.Angles(spineX, 0, 0.3 * s.roll)
    mo.Chest.Transform = CFrame.Angles(chestX + 0.05 * special, 0.1 * s.nYaw * G, -0.3 * s.roll)
    mo.Neck1.Transform = CFrame.Angles(neck1X, 0.25 * s.nYaw, 0.2 * s.roll)
    mo.Neck2.Transform = CFrame.Angles(neck2X, 0.3 * s.nYaw, 0.2 * s.roll)
    mo.Neck3.Transform = CFrame.Angles(neck3X, 0.3 * s.nYaw, 0.2 * s.roll)
    mo.Head.Transform = CFrame.Angles(headX, 0.45 * (s.gYaw - 0.8 * s.nYaw), headRoll)
    mo.Jaw.Transform = CFrame.Angles(s.jaw, 0, 0)
    for j = 1, 4 do
        mo[TAIL_NAMES[j]].Transform = CFrame.Angles(tx[j], ty[j], 0)
    end
end

return Dreadwing

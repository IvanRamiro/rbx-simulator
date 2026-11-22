-- A four-legged beast's feet: footfalls that stay planted on the ground, three-segment leg solving onto them, and the crouch a stretched leg asks for.
-- Used by the Nine-Tail Moonfox and Crysalith (PetMotion has the pieces; this is the whole leg system, once).
--
-- spec = {
--   spine = { "Hips", "Spine", "Chest" }  the body's bones from the hips forward (their pitch is the caller's; the forelegs hang from the last, the hind legs from
--                                         the first),
--   legs = { BL = { "LegBL1", "LegBL2", "LegBL3", "PawBL" }, FL = ..., BR = ..., FR = ... }  each leg's hip, middle joint, ankle and foot bones,
--   psiFront, psiHind  how much of a leg's swing its lower segment follows, flickFront, flickHind  which way it folds as the foot leaves the ground,
--   limit  { front = { {lo, hi} x3 }, hind = ... } the turns (upper, middle, lower) the skin can take, maxCrouch  the most the body may sink (metres),
--   gait  PetMotion's gait numbers (nil: a fox's), reachK  how far a leg may stretch, as a share of its length, before the body sinks (0.95; a heavy beast stands more bent),
-- }
local PetMotion = require(script.Parent:WaitForChild("PetMotion"))

local PetQuad = {}

local min, max, abs = math.min, math.max, math.abs
local KEYS = { "BL", "FL", "BR", "FR" }
PetQuad.KEYS = KEYS

function PetQuad.new(rig, spec)
    local rest, u = rig.restCF, rig.meters
    local ground = rest.Root.Position
    local function at(name)
        local p = rest[name].Position - ground
        return { p.Y / u, p.Z / u }
    end
    local function minus(a, b)
        return { a[1] - b[1], a[2] - b[2] }
    end
    local q = { spec = spec, u = u, legs = {}, g = { cadence = 1, duty = 0.6, trot = 0, active = 0, stride = 0, lift = 0, bounce = 0 } }
    q.phase, q.crouch, q.crouchV = 0, 0, 0
    q.touch = { BL = false, FL = false, BR = false, FR = false } -- (set on the pose a foot comes down)
    local spine = {}
    for i, name in spec.spine do
        spine[i] = at(name)
    end
    q.hip = spine[1]
    q.vSpine = {} -- from each spine bone to the next
    for i = 1, #spine - 1 do
        q.vSpine[i] = minus(spine[i + 1], spine[i])
    end
    q.n = #spine
    q.ang = table.create(q.n, 0) -- the caller's pitch for each spine bone, set before update
    local sum = 0
    for _, key in KEYS do
        local front = string.sub(key, 1, 1) == "F"
        local names = spec.legs[key]
        local pivot, mid, ankle, foot = at(names[1]), at(names[2]), at(names[3]), at(names[4])
        local leg = PetMotion.legFrom(pivot, mid, ankle, foot, spec.bend and spec.bend[key])
        leg.front = front
        leg.vP = if front then minus(pivot, spine[q.n]) else minus(pivot, spine[1])
        leg.foot = { z = 0, lifted = false, y = 0 }
        leg.psiFollow = if front then spec.psiFront else spec.psiHind
        leg.flick = if front then spec.flickFront else spec.flickHind
        leg.chord0 = math.atan2(foot[2] - pivot[2], foot[1] - pivot[1])
        leg.side = if string.sub(key, 2, 2) == "L" then -1 else 1
        leg.half = abs(rest[names[1]].Position.X) / u -- (half the width between its hips)
        leg.a1, leg.a2, leg.a3, leg.a4 = 0, 0, 0, 0
        q.legs[key] = leg
        sum += leg.l1 + leg.l2 + leg.l3
    end
    q.legLen = sum / 4
    return q
end

-- Step one: the gait for its speed (vm: its metres a second, signed, forward positive; G: how much it is on the ground, 1 standing .. 0 in the air) and
-- the stride's phase moved on. After this q.g (the gait numbers) and q.phase are the pose's, for the caller to build the body's own motion from.
function PetQuad.advance(q, dt, vm, G)
    local g = q.g
    PetMotion.gaitFor(g, abs(vm) * G, q.legLen, q.spec.gait)
    if g.active > 0.03 then
        q.phase = (q.phase + dt * g.cadence) % 1
    end
end

-- Step two, after the caller has set q.ang (the pitch of each spine bone): the legs. dzM: the metres it moved forward since the last pose, lift: metres its body is
-- moved up by something other than the gait (a leap, a landing), rollShift: metres one side's hips sit above the other's (a rolled body), unload: a table
-- { BL = metres, ... } a foot is lifted off the ground, or nil. Fills each leg's a1..a4 (their pitch turns), q.bounce (metres the gait lifts the body) and
-- q.touch (a foot came down this pose), and returns the metres the body is crouched by (the caller lowers the hips by it).
function PetQuad.solve(q, dt, vm, dzM, lift, rollShift, unload)
    local g = q.g
    local walking = g.active
    local phase = q.phase
    local bounceG = g.bounce * -math.cos(2 * 2 * math.pi * (phase - g.duty / 2)) * walking
    q.bounce = bounceG
    local ang, n = q.ang, q.n
    -- where the hips are and the spine's bones lie, in the ground's frame (not yet crouched)
    local py0, pz0 = q.hip[1] + bounceG + lift, q.hip[2]
    local cum = 0
    local fy, fz = py0, pz0
    for i = 1, n - 1 do
        cum += ang[i]
        local dy, dz = PetMotion.rot(cum, q.vSpine[i][1], q.vSpine[i][2])
        fy += dy
        fz += dz
    end
    local frontBase = cum + ang[n]
    local crouch = q.crouch
    local needCrouch = 0
    local reachK = q.spec.reachK or 0.95 -- how straight a leg may get before the body sinks
    for i = 1, 4 do
        local key = KEYS[i]
        local leg = q.legs[key]
        local phi = (phase + PetMotion.legPhase(key, g.trot)) % 1
        if walking < 0.03 then
            phi = 0
        end
        local f = leg.foot
        local wasLifted = f.lifted
        local z, y = PetMotion.foot(f, phi, g, vm, dzM, dt)
        q.touch[key] = wasLifted and not f.lifted
        if walking < 0.08 then
            f.z -= f.z * min(1, dt * 5)
        end
        local base, py, pz
        if leg.front then
            base = frontBase
            local ly, lz = PetMotion.rot(frontBase, leg.vP[1], leg.vP[2])
            py, pz = fy + ly, fz + lz
        else
            base = ang[1]
            local ly, lz = PetMotion.rot(ang[1], leg.vP[1], leg.vP[2])
            py, pz = py0 + ly, pz0 + lz
        end
        py += leg.side * rollShift - crouch
        local ty, tz = leg.footY + y + (if unload then unload[key] or 0 else 0), leg.footZ + z
        local chord = math.atan2(tz - pz, ty - py)
        local liftN = y / max(g.lift, 0.01)
        local dPsi = leg.psiFollow * PetMotion.wrap(chord - leg.chord0) + leg.flick * liftN * 0.5
        local a1, a2, a3, d, reach = PetMotion.leg3(leg, py, pz, base, ty, tz, dPsi)
        local over = d - reachK * reach
        if over > 0 then
            needCrouch = max(needCrouch, crouch + over * d / max(py - ty, 0.05))
        end
        local lim = q.spec.limit and (if leg.front then q.spec.limit.front else q.spec.limit.hind)
        if lim then -- (what the skin can take: the angles are held to the rig's checked range, the foot stays flat whatever)
            a1 = math.clamp(a1, lim[1][1], lim[1][2])
            a2 = math.clamp(a2, lim[2][1], lim[2][2])
            a3 = math.clamp(a3, lim[3][1], lim[3][2])
        end
        leg.a1, leg.a2, leg.a3 = a1, a2, a3
        leg.a4 = -(base + a1 + a2 + a3) - 0.5 * liftN -- (the foot stays flat on the ground while down, rolling heel to toe as it comes off)
    end
    q.crouch, q.crouchV = PetMotion.spring(q.crouch, q.crouchV, min(needCrouch, q.spec.maxCrouch or 0.3), 16, 0.9, dt)
    return q.crouch
end

return PetQuad

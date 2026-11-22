-- Shared tools for the exclusive beasts' animation (the Nine-Tail Moonfox, Crysalith, the Eclipse Dreadwing): motion signals read from the pet's own
-- root (speed, turn rate, acceleration), damped springs for follow-through, a smooth noise for irregular life, a planar three-segment leg solver
-- and a procedural footfall generator, so feet stay planted on the ground whatever the speed and size.
--
-- Everything here is allocation-free per frame (numbers in, numbers out; state lives in tables a pet makes once) and works in the pet's own
-- axes (x to its right, y up, z backward): a turn "pitch" is about x (positive lifts the nose, lowers the tail), "yaw" about y, "roll" about z.
local PetMotion = {}

local abs, sin, cos, sqrt, atan2, acos, min, ceil = math.abs, math.sin, math.cos, math.sqrt, math.atan2, math.acos, math.min, math.ceil
local TAU = 2 * math.pi

function PetMotion.smoothstep(edge0, edge1, x)
    local t = math.clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
end

function PetMotion.lerp(a, b, t)
    return a + (b - a) * t
end

-- an angle brought into (-pi, pi]
function PetMotion.wrap(a)
    return (a + math.pi) % TAU - math.pi
end

-- A smooth, never-repeating-looking value in [-1, 1] from the time and a seed (three sines that don't line up): the life under an idle
function PetMotion.noise(t, seed)
    return (sin(t * 0.9 + seed * 12.989) + 0.5 * sin(t * 2.31 + seed * 78.233 + 1.7) + 0.7 * sin(t * 0.43 + seed * 37.719 + 4.1)) / 2.2
end

-- One step of a damped spring: position x and velocity v toward `target`, natural frequency w (rad/s), damping ratio z (0.5 overshoots a little,
-- 1 doesn't). Sub-stepped, so it stays stable for any dt (a far pet poses every second or third frame). Returns the new x, v.
function PetMotion.spring(x, v, target, w, z, dt)
    local wd = w * dt
    if wd <= 0.45 then -- (the usual case: one step)
        v += (w * w * (target - x) - 2 * z * w * v) * dt
        return x + v * dt, v
    end
    local n = ceil(wd * 2.2)
    local h = dt / n
    local ww, zz = w * w, 2 * z * w
    for _ = 1, n do
        v += (ww * (target - x) - zz * v) * h
        x += v * h
    end
    return x, v
end

-- ---------- signals from the pet's own root ----------
-- Fills s.vF (forward speed, studs/s), s.vS (sideways), s.vY (vertical), s.speed (ground speed), s.yawRate (rad/s, positive turning left), s.dYaw (turned
-- this pose, radians), s.dFwd and s.dSide (studs moved this pose), s.accF (forward acceleration, studs/s^2), s.accS (sideways: speed x turn rate),
-- all lightly smoothed. Call once a pose, first.
function PetMotion.track(rig, s, dt)
    local cf = rig.rootPart.CFrame
    local pos = cf.Position
    local look = cf.LookVector
    local fx, fz = look.X, look.Z
    local flat = sqrt(fx * fx + fz * fz)
    if flat < 1e-3 then
        fx, fz, flat = s.trkFx or 0, s.trkFz or -1, 1
    end
    fx, fz = fx / flat, fz / flat
    local prev = s.trkPos
    if prev == nil or dt <= 1e-4 then
        s.trkPos, s.trkFx, s.trkFz = pos, fx, fz
        s.vF, s.vS, s.vY, s.speed, s.yawRate, s.dYaw, s.dFwd, s.dSide, s.accF, s.accS = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        return
    end
    local sx, sy, sz = pos.X - prev.X, pos.Y - prev.Y, pos.Z - prev.Z
    local lim = 25 * (rig.meters or 4)
    if sx * sx + sy * sy + sz * sz > lim * lim then -- (a teleport or a snap to its owner: nothing moved smoothly)
        s.trkPos, s.trkFx, s.trkFz = pos, fx, fz
        s.dYaw, s.dFwd, s.dSide = 0, 0, 0
        return
    end
    local dYaw = PetMotion.wrap(atan2(-fx, -fz) - atan2(-(s.trkFx or fx), -(s.trkFz or fz)))
    local dFwd = sx * fx + sz * fz
    local dSide = sx * -fz + sz * fx -- (right of its heading: a pet's x)
    s.trkPos, s.trkFx, s.trkFz = pos, fx, fz
    s.dYaw, s.dFwd, s.dSide = dYaw, dFwd, dSide
    local k = min(1, dt * 14)
    local vF0 = s.vF
    s.vF += (dFwd / dt - s.vF) * k
    s.vS += (dSide / dt - s.vS) * k
    s.vY += (sy / dt - s.vY) * k
    s.speed = sqrt(s.vF * s.vF + s.vS * s.vS)
    s.yawRate += (dYaw / dt - s.yawRate) * min(1, dt * 10)
    s.accF += ((s.vF - vF0) / dt - s.accF) * min(1, dt * 6)
    s.accS += (s.vF * s.yawRate - s.accS) * min(1, dt * 8)
end

-- ---------- a planar leg ----------
-- A leg of three segments (upper, middle, lower) and a foot, in the plane through the pet's length (y up, z backward; an angle is atan2(z, y)).
-- leg = { l1, l2, l3, th1, th2, th3 (the segments' angles at rest), bend (+1 or -1: which way the middle joint folds), px, py (rest ankle) }.
-- Built once from the rest bones by PetMotion.legFrom.
function PetMotion.legFrom(pivot, mid, ankle, foot, bend)
    -- each argument is { y, z } (metres, rest positions of the segments' heads: the hip, the middle joint, the ankle, the foot's head)
    local v1y, v1z = mid[1] - pivot[1], mid[2] - pivot[2]
    local v2y, v2z = ankle[1] - mid[1], ankle[2] - mid[2]
    local v3y, v3z = foot[1] - ankle[1], foot[2] - ankle[2]
    local leg = {
        l1 = sqrt(v1y * v1y + v1z * v1z),
        l2 = sqrt(v2y * v2y + v2z * v2z),
        l3 = sqrt(v3y * v3y + v3z * v3z),
        th1 = atan2(v1z, v1y),
        th2 = atan2(v2z, v2y),
        th3 = atan2(v3z, v3y),
        footY = foot[1],
        footZ = foot[2],
    }
    if bend then
        leg.bend = bend
    else
        local chord = atan2(ankle[2] - pivot[2], ankle[1] - pivot[1])
        leg.bend = if PetMotion.wrap(leg.th1 - chord) >= 0 then 1 else -1
    end
    return leg
end

-- The turns (pitch of each bone, relative to its parent) that put the foot's head at (ty, tz) with the pivot (hip) at (py, pz), the leg hanging from
-- a body turned `base` radians, the lower segment keeping its rest angle plus dPsi. Out of reach it stretches straight at the target.
-- Returns a1, a2, a3, then how far the ankle had to be (d) and the most it could reach (l1 + l2), so a body can crouch when a leg is stretched.
function PetMotion.leg3(leg, py, pz, base, ty, tz, dPsi)
    local th3 = leg.th3 + dPsi
    local wy, wz = ty - leg.l3 * cos(th3), tz - leg.l3 * sin(th3) -- the ankle
    local dy, dz = wy - py, wz - pz
    local d = sqrt(dy * dy + dz * dz)
    local l1, l2 = leg.l1, leg.l2
    local reach = math.clamp(d, abs(l1 - l2) + 0.002, l1 + l2 - 0.002)
    local cosA = math.clamp((l1 * l1 + reach * reach - l2 * l2) / (2 * l1 * reach), -1, 1)
    local t1 = atan2(dz, dy) + leg.bend * acos(cosA)
    local jy, jz = py + l1 * cos(t1), pz + l1 * sin(t1)
    local t2 = atan2(wz - jz, wy - jy)
    -- (a target nearer than the clamp: aim the leg at it anyway)
    local a1 = PetMotion.wrap(t1 - leg.th1 - base)
    local a2 = PetMotion.wrap(t2 - leg.th2 - (t1 - leg.th1))
    local a3 = PetMotion.wrap(th3 - leg.th3 - (t2 - leg.th2))
    return a1, a2, a3, d, l1 + l2
end

-- a planar rotation of (y, z) by theta (positive turns y toward z, as a pitch about x does)
function PetMotion.rot(theta, y, z)
    local c, s = cos(theta), sin(theta)
    return y * c - z * s, y * s + z * c
end

-- ---------- footfalls ----------
-- Gait numbers from the pet's speed in its own metres a second (vm): the stride rate, the share of each stride a foot is down (duty), how far the
-- diagonal pairs have moved from a walk's lateral sequence to a trot (0..1), how high a foot lifts and how far it travels while down. P tunes it per
-- beast: { v0, v1 (the speeds where it is clearly walking, and at its fastest), cadence = {slow, fast}, duty = {walk, trot}, trotAt = {from, to},
-- lift = {slow, fast} (as a share of its leg length), bounce = {slow, fast}, stride (the most a foot travels while down, as a share of its leg) }.
-- gait = { cadence, duty, trot, active, stride, lift, bounce }. The defaults are a fox's: a walk below about 1 m/s, a trot to about 3.
local DEFAULT_GAIT = {
    v0 = 0.25, v1 = 3.2, cadence = { 0.95, 2.5 }, duty = { 0.68, 0.42 }, trotAt = { 0.8, 2.0 }, lift = { 0.1, 0.19 }, bounce = { 0.012, 0.05 }, stride = 1.0,
    dutyFrom = 0.5, dutyTo = 3.4, active = { 0.12, 0.45 },
}
PetMotion.DEFAULT_GAIT = DEFAULT_GAIT
function PetMotion.gaitFor(g, vm, legLength, P)
    P = P or DEFAULT_GAIT
    local sm = PetMotion.smoothstep
    local lerp = PetMotion.lerp
    local top = sm(P.v0, P.v1, vm)
    g.cadence = lerp(P.cadence[1], P.cadence[2], top)
    g.duty = lerp(P.duty[1], P.duty[2], sm(P.dutyFrom, P.dutyTo, vm))
    g.trot = sm(P.trotAt[1], P.trotAt[2], vm)
    g.active = sm(P.active[1], P.active[2], vm) -- how much it is walking at all (0: standing, feet stay at rest)
    g.stride = min(vm * g.duty / g.cadence, P.stride * legLength) -- metres a foot travels while it is down
    g.lift = legLength * lerp(P.lift[1], P.lift[2], sm(0.4, 2.5, vm)) * g.active
    g.bounce = legLength * lerp(P.bounce[1], P.bounce[2], sm(0.5, 3.2, vm)) * g.active
end

-- the phase offsets (of a stride) for a leg key "BL", "FL", "BR", "FR": a walk's lateral sequence moving to a trot's diagonal pairs
function PetMotion.legPhase(key, trot)
    if key == "BL" then
        return 0
    elseif key == "BR" then
        return 0.5
    elseif key == "FL" then
        return PetMotion.lerp(0.25, 0.5, trot)
    end
    return PetMotion.lerp(0.75, 1.0, trot)
end

-- One foot's place along the ground (z, metres from its neutral place under the hip; backward positive) and height, at stride phase phi, as a planted foot
-- slides back with the body and a swinging foot carries forward on a curve that meets the ground already moving back at the body's speed
-- (a cubic Hermite, so it neither scuffs nor lands on tiptoe). `f` is the foot's own state table: { z, lifted, z0, zEnd, T, y } (z starts 0).
-- Returns z, y. vz is the body's speed in metres a second, dz the metres the body moved this pose (the planted foot slides back by it).
function PetMotion.foot(f, phi, g, vz, dz, dt)
    if phi < g.duty then
        if f.lifted then -- it just came down
            f.lifted = false
            f.z = f.zEnd
        end
        f.z += dz
        local lim = 0.5 * g.stride * 1.25 + 0.04 -- (a foot never trails past what it could reach)
        f.z = math.clamp(f.z, -lim, lim)
        f.y = 0
        return f.z, 0
    end
    local w = (phi - g.duty) / (1 - g.duty)
    if not f.lifted then -- it just left the ground: where it is now, where it will land
        f.lifted = true
        f.z0 = f.z
        f.zEnd = -0.5 * g.stride * (if vz < 0 then -1 else 1)
        f.T = (1 - g.duty) / g.cadence
    end
    local T = f.T
    local m = vz * T -- the body's speed over the whole swing: the tangent at both ends
    local w2, w3 = w * w, w * w * w
    local h00, h10, h01, h11 = 2 * w3 - 3 * w2 + 1, w3 - 2 * w2 + w, -2 * w3 + 3 * w2, w3 - w2
    local z = h00 * f.z0 + h10 * m + h01 * f.zEnd + h11 * m
    f.z = z
    local y = g.lift * sin(math.pi * w) ^ 0.8
    f.y = y
    return z, y
end

return PetMotion

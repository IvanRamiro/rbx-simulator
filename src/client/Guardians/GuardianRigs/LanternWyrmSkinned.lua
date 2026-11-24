-- The Abyssal Lantern Wyrm on a real skeleton (tools/blender/guardians/lantern_wyrm.py): a colossal limbless serpent-dragon of the deep dark, 72 bones,
-- about 76 studs long, a horned head with antlers and barbels, a mane-like frill along its neck, a stalk from the brow carrying a lantern of warm gold (the
-- lure that draws the eye), cold cyan ring-marks along its flanks. It holds no egg: no guardian does.
-- Its poses and every move were solved in Blender as curves (where the spine lies) and turned into bone turns; LanternWyrmClips.lua (written by the tool)
-- is that work as data, and this rig plays it through GuardianAnim's springs. What a clip cannot say it adds here:
--   the CHAIN: walking and running, the body lies on the path its root has taken (a recorded trail, each bone reading it back at its own distance along
--   the body, so a turn is followed and never sheared) carrying a bending wave fixed in the world, so every body point slides along its track and none
--   skates; the wave grows from nothing at the hips, so the neck and head stay steady and level;
--   the turn in place (the neck leads, the coils shuffle after it), the idle layers (the slow sway, the studying look, ripples of breath), springs with
--   drag on the barbels, the frill, the lantern's stalk and the tail's tip, the hit-pause on each blow, the glow (eyes, lantern, ring-marks, frill).
--   Dormant   asleep in a flat ring of coils, the head resting on them, the lantern dark, the frill flat, a very slow breath rippling along the body;
--   Guardian  awake, the neck raised in a slow S that sways almost imperceptibly, the head swinging to study you with one eye then the other, the lantern
--             bobbing a little ahead of the face like a lure; it does not fidget, it waits;
--   Weakened  worn out: the neck drooping, the head low, the lantern flickering, the frill folded, laboured ripples of breath;
--   Enraged   an egg was taken: the neck reared high, the frill flared wide, the lantern blazing, the whole body thrashing in waves;
--   Returning gliding home, the neck lowered, the frill half open.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))
local Clips = require(script.Parent:WaitForChild("LanternWyrmClips"))

local add, envelope, smooth = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth

local Rig = {}
Rig.Skinned = true
Rig.ExtraBones = { "Eyes" }
Rig.Joints = Clips.Joints
Clips.Poses.Resting = Clips.Poses.Dormant -- the server's Resting state (it sleeps again after an egg is secured) lies as Dormant does
Rig.Poses = Clips.Poses
Rig.Gallop = { 16, 24 } -- walking below the first, running past the second
Rig.LeapAction = "SerpentLeap"
-- the head turns to the target (the neck's upper bones lean in a little, the spine below them not at all)
Rig.Look = { Joint = "Head", Share = 0.55, Body = "Neck8", BodyShare = 0.25, Limit = 65 }

-- ---------- the springs ----------
-- the body follows its clips and its path closely (a lag would shear the chain); the neck whips, each bone a beat behind the one below it; the barbels, the
-- frill, the lantern's stalk and the tail's tip trail behind everything, with drag
local SPRING = {
    Hips = { Freq = 10, Damping = 0.7, Drag = 0 },
    Head = { Freq = 9, Damping = 0.55, Drag = 0.22 },
    Jaw = { Freq = 14, Damping = 0.6, Drag = 0 },
    Lure1 = { Freq = 5, Damping = 0.32, Drag = 0.45 },
    Lure2 = { Freq = 4.4, Damping = 0.28, Drag = 0.6 },
    Lure3 = { Freq = 3.9, Damping = 0.26, Drag = 0.72 },
}
for i = 1, 8 do
    SPRING["Neck" .. i] = { Freq = 10 - 0.35 * i, Damping = 0.62 - 0.015 * i, Drag = 0.02 * i }
end
for i = 1, 11 do
    SPRING["Body" .. i] = { Freq = 13, Damping = 0.78, Drag = 0 }
    SPRING["Tail" .. i] = { Freq = 12 - 0.45 * i, Damping = 0.72 - 0.02 * i, Drag = 0.012 * i }
end
for _, tag in { "Left", "Right" } do
    for i = 1, 10 do
        SPRING[tag .. "Frill" .. i] = { Freq = 7.5 - 0.15 * i, Damping = 0.36, Drag = 0.2 + 0.015 * i }
    end
    for i, spring in { { 3.4, 0.3, 0.4 }, { 3.0, 0.28, 0.55 }, { 2.7, 0.26, 0.7 }, { 2.4, 0.24, 0.8 } } do
        SPRING[tag .. "BarbelA" .. i] = { Freq = spring[1], Damping = spring[2], Drag = spring[3] }
    end
    for i, spring in { { 3.6, 0.3, 0.45 }, { 3.2, 0.28, 0.6 }, { 2.8, 0.26, 0.75 } } do
        SPRING[tag .. "BarbelB" .. i] = { Freq = spring[1], Damping = spring[2], Drag = spring[3] }
    end
end
Rig.Springs = SPRING

-- a blow taken (GuardianReact): the hips take it, the neck follows in a whip, the head last; the frill, the lantern and the tail's tip show it too
Rig.Hit = {
    Body = "Hips",
    Joints = {
        Neck1 = { 0.55, 0 }, Neck2 = { 0.6, 0.02 }, Neck3 = { 0.65, 0.04 }, Neck4 = { 0.7, 0.06 }, Neck5 = { 0.78, 0.08 }, Neck6 = { 0.85, 0.1 },
        Neck7 = { 0.9, 0.12 }, Neck8 = { 0.95, 0.14 }, Head = { 1, 0.16 }, Lure1 = { 0.8, 0.18 }, Lure2 = { 1, 0.22 }, Lure3 = { 1.2, 0.26 },
        LeftFrill3 = { 0.7, 0.1 }, RightFrill3 = { 0.7, 0.1 }, LeftFrill6 = { 0.7, 0.14 }, RightFrill6 = { 0.7, 0.14 },
        Body3 = { 0.4, 0.05 }, Body8 = { 0.5, 0.15 }, Tail5 = { 0.6, 0.25 }, Tail11 = { 0.9, 0.38 },
    },
    Scale = 0.8,
}
Rig.Style = { Debris = "Void", Qi = Color3.fromRGB(120, 90, 255), QiCore = Color3.fromRGB(215, 205, 255) }
local GOLD = { Debris = "Void", Qi = Color3.fromRGB(255, 170, 40), QiCore = Color3.fromRGB(255, 240, 200) }

-- ---------- the chain: a body that follows its leader (plain numbers, so it can be tested apart from the engine) ----------
-- CHAIN BEGIN
local Chain = {}
do
    local CH = Clips.Chain
    local TAU = 2 * math.pi
    local DEG = math.deg

    local function smooth01(x)
        x = math.clamp(x, 0, 1)
        return x * x * (3 - 2 * x)
    end

    -- the amplitude and the wavelength of the wave, from the ground speed (none at a standstill)
    function Chain.wave(speed)
        local g = smooth01((speed - 16) / 8)
        local k = smooth01(speed / 6)
        return (CH.amp_walk + (CH.amp_run - CH.amp_walk) * g) * k, CH.lam_walk + (CH.lam_run - CH.lam_walk) * g
    end

    -- the root's recorded path: points in the ground plane with the distance travelled at each, a point added when it has moved 0.3 studs
    local Trail = {}
    Trail.__index = Trail

    function Trail.new()
        return setmetatable({ x = {}, z = {}, s = {}, n = 0, nowX = 0, nowZ = 0, sNow = 0, backX = 0, backZ = 1 }, Trail)
    end

    function Trail:push(x, z)
        local n = self.n
        if n == 0 then
            self.n = 1
            self.x[1], self.z[1], self.s[1] = x, z, 0
        else
            local d = math.sqrt((x - self.x[n]) ^ 2 + (z - self.z[n]) ^ 2)
            if d >= 0.3 then
                self.n = n + 1
                self.x[n + 1], self.z[n + 1], self.s[n + 1] = x, z, self.s[n] + d
            end
        end
        self.nowX, self.nowZ = x, z
        n = self.n
        self.sNow = self.s[n] + math.sqrt((x - self.x[n]) ^ 2 + (z - self.z[n]) ^ 2)
        while self.n > 400 or (self.n > 2 and self.sNow - self.s[2] > 110) do
            table.remove(self.x, 1)
            table.remove(self.z, 1)
            table.remove(self.s, 1)
            self.n -= 1
        end
    end

    function Trail:point(i)
        if i > self.n then
            return self.nowX, self.nowZ, self.sNow
        end
        return self.x[i], self.z[i], self.s[i]
    end

    -- the direction of travel at stored point i (a central difference; the newest point looks on to the root)
    function Trail:tangent(i)
        local ax, az = self:point(math.max(i - 1, 1))
        local bx, bz = self:point(math.min(i + 1, self.n + 1))
        local dx, dz = bx - ax, bz - az
        local m = math.sqrt(dx * dx + dz * dz)
        if m < 1e-6 then
            return 0, -1
        end
        return dx / m, dz / m
    end

    -- (x, z, tx, tz, s) `behind` studs behind the root along its path; the tangent is blended between the points either side so the path bends smoothly;
    -- beyond the start the path carries straight back
    function Trail:at(behind)
        local target = self.sNow - behind
        local n = self.n
        if n < 2 or target <= self.s[1] then
            local tx, tz = -self.backX, -self.backZ
            if n > 1 then
                tx, tz = self:tangent(1)
            end
            return self.x[1] + tx * (target - self.s[1]), self.z[1] + tz * (target - self.s[1]), tx, tz, target
        end
        local lo, hi = 1, n
        if self.s[n] <= target then
            lo = n
        else
            while hi - lo > 1 do
                local mid = (lo + hi) // 2
                if self.s[mid] <= target then
                    lo = mid
                else
                    hi = mid
                end
            end
        end
        local i = lo
        local ax, az, sa = self:point(i)
        local bx, bz, sb = self:point(i + 1)
        local t1x, t1z = self:tangent(i)
        local t2x, t2z = self:tangent(i + 1)
        local u = math.clamp((target - sa) / math.max(sb - sa, 1e-9), 0, 1)
        local tx, tz = t1x + (t2x - t1x) * u, t1z + (t2z - t1z) * u
        local m = math.sqrt(tx * tx + tz * tz)
        if m > 1e-6 then
            tx, tz = tx / m, tz / m
        else
            tx, tz = t1x, t1z
        end
        if (bx - ax) ^ 2 + (bz - az) ^ 2 > 1e-18 then
            return ax + (bx - ax) * u, az + (bz - az) * u, tx, tz, target
        end
        return ax, az, tx, tz, target
    end

    Chain.Trail = Trail

    -- the joints of the trunk and the tail laid along the trail, the wave added, each joint exactly one bone's length (a chord) from the one before it, on
    -- the ground: {{x, y, z} ...} in the guardian's axes. toLocal(x, z) takes a world ground-plane point to the guardian's (x, z).
    function Chain.laid(trail, speed, toLocal)
        local amp, lam = Chain.wave(speed)
        local function track(b)
            local x, z, tx, tz, s = trail:at(b)
            local off = amp * smooth01(b / CH.ramp) * math.sin(TAU * s / lam)
            return x - tz * off, z + tx * off
        end
        local lens = CH.lengths
        local wx, wz = {}, {}
        wx[1], wz[1] = track(0)
        local b = 0
        for j, l in lens do
            local ax, az = wx[j], wz[j]
            local lo, hi = b, b + l * 1.8 + 2 * amp + 0.5
            for _ = 1, 24 do
                local mid = (lo + hi) / 2
                local qx, qz = track(mid)
                if (qx - ax) ^ 2 + (qz - az) ^ 2 < l * l then
                    lo = mid
                else
                    hi = mid
                end
            end
            b = (lo + hi) / 2
            wx[j + 1], wz[j + 1] = track(b)
        end
        local pts = {}
        for j = 1, #lens + 1 do
            local lx, lz = toLocal(wx[j], wz[j])
            pts[j] = { lx, CH.ground[j], lz }
        end
        return pts
    end

    -- small 3x3 rotations as rows of columns {{a1, b1, c1}, ...}: columns are the frame's axes
    local function cross(a, b)
        return { a[2] * b[3] - a[3] * b[2], a[3] * b[1] - a[1] * b[3], a[1] * b[2] - a[2] * b[1] }
    end
    local function dot(a, b)
        return a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    end
    local function unit(a)
        local m = math.sqrt(dot(a, a))
        if m < 1e-9 then
            return { 0, 0, 0 }
        end
        return { a[1] / m, a[2] / m, a[3] / m }
    end
    local function frameOf(a, b)
        a = unit(a)
        local k = dot(b, a)
        b = unit({ b[1] - a[1] * k, b[2] - a[2] * k, b[3] - a[3] * k })
        local c = cross(a, b)
        return { { a[1], b[1], c[1] }, { a[2], b[2], c[2] }, { a[3], b[3], c[3] } }
    end
    local function mul(A, B)
        local C = { {}, {}, {} }
        for i = 1, 3 do
            for j = 1, 3 do
                C[i][j] = A[i][1] * B[1][j] + A[i][2] * B[2][j] + A[i][3] * B[3][j]
            end
        end
        return C
    end
    local function transpose(A)
        return { { A[1][1], A[2][1], A[3][1] }, { A[1][2], A[2][2], A[3][2] }, { A[1][3], A[2][3], A[3][3] } }
    end
    -- R = Rx(pitch) Ry(yaw) Rz(roll), as CFrame.Angles: the turns, in degrees
    local function euler(R)
        local y = math.asin(math.clamp(R[1][3], -1, 1))
        local x = math.atan2(-R[2][3], R[3][3])
        local z = math.atan2(-R[1][2], R[1][1])
        return DEG(x), DEG(y), DEG(z)
    end

    local REST_INV = transpose(frameOf({ 0, 0, 1 }, { 0, 1, 0 }))
    local IDENTITY = { { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 } }

    -- the turns of the trunk's bones that lay them through the joints (the hips square to the guardian's axes): {{pitch, yaw, roll} ...}
    function Chain.turns(pts)
        local out = {}
        local pr = IDENTITY
        local up = { 0, 1, 0 }
        local prev = nil
        for i = 1, #pts - 1 do
            local d = unit({ pts[i + 1][1] - pts[i][1], pts[i + 1][2] - pts[i][2], pts[i + 1][3] - pts[i][3] })
            if prev then
                -- the face of the bone is carried along with no twist: up turned by the least turn that takes the last direction to this one
                local axis = cross(prev, d)
                local s = math.sqrt(dot(axis, axis))
                if s > 1e-9 then
                    local k = { axis[1] / s, axis[2] / s, axis[3] / s }
                    local c = dot(prev, d)
                    local kxu = cross(k, up)
                    local kd = dot(k, up) * (1 - c)
                    up = { up[1] * c + kxu[1] * s + k[1] * kd, up[2] * c + kxu[2] * s + k[2] * kd, up[3] * c + kxu[3] * s + k[3] * kd }
                end
            end
            local k = dot(up, d)
            up = { up[1] - d[1] * k, up[2] - d[2] * k, up[3] - d[3] * k }
            if dot(up, up) < 1e-8 then
                up = { 0, 0, 1 }
                k = dot(up, d)
                up = { up[1] - d[1] * k, up[2] - d[2] * k, up[3] - d[3] * k }
            end
            up = unit(up)
            local want = frameOf(d, up)
            local T = mul(transpose(pr), mul(want, REST_INV))
            local p, y, r = euler(T)
            out[i] = { p, y, r }
            pr = mul(want, REST_INV)
            prev = d
        end
        return out
    end
end
-- CHAIN END

local TRUNK = {}
for i = 1, 11 do
    table.insert(TRUNK, "Body" .. i)
end
for i = 1, 11 do
    table.insert(TRUNK, "Tail" .. i)
end
local NECK = { "Neck1", "Neck2", "Neck3", "Neck4", "Neck5", "Neck6", "Neck7", "Neck8" }

-- the root's path, recorded as it moves; a jump (a teleport) starts it again
local function record(anim)
    local root = anim.root
    local p = root.Position
    local trail = anim.trail
    if not trail then
        trail = Chain.Trail.new()
        local back = root.CFrame.LookVector
        trail.backX, trail.backZ = -back.X, -back.Z
        anim.trail = trail
    end
    if anim.trailAt ~= os.clock() then
        anim.trailAt = os.clock()
        if trail.n > 0 and (p.X - trail.nowX) ^ 2 + (p.Z - trail.nowZ) ^ 2 > 144 then
            trail = Chain.Trail.new()
            local back = root.CFrame.LookVector
            trail.backX, trail.backZ = -back.X, -back.Z
            anim.trail = trail
        end
        trail:push(p.X, p.Z)
    end
    return trail
end

-- a turn about the world's vertical, laid on a bone of the neck: the bones turn in their parent's frame, which leans with the neck, so it is a yaw of cos(alpha)
-- and a roll of -sin(alpha), alpha being how far the parent's long axis is raised (Clips.Alpha, in the awake pose)
local function turnAbout(pose, bone, degrees)
    local alpha = math.rad(Clips.Alpha[bone] or 0)
    local p = pose[bone]
    if p then
        p[2] += degrees * math.cos(alpha)
        p[3] -= degrees * math.sin(alpha)
    end
end

-- ---------- the gaits ----------
-- Walking and running: the trunk and tail are laid on the trail (the Chain), blended in by how fast it goes; the neck keeps its S, swaying with the wave a
-- little and never bobbing (a serpent's head stays level); the frill stays as the state has it.
function Rig.gait(anim, pose, dt)
    local trail = record(anim)
    local w = anim.moving * smooth((anim.speed - 2.5) / 5)
    if w > 0.001 then
        local cf = anim.root.CFrame
        local y = cf.Position.Y
        local pts = Chain.laid(trail, anim.speed, function(x, z)
            local q = cf:PointToObjectSpace(Vector3.new(x, y, z))
            return q.X, q.Z
        end)
        local turns = Chain.turns(pts)
        for i, bone in TRUNK do
            local p, e = pose[bone], turns[i]
            for k = 1, 3 do
                local gap = e[k] - p[k]
                p[k] += ((gap + 180) % 360 - 180) * w
            end
        end
        -- the head holds steady: the neck leans a few degrees with the wave's phase, the head turned back against it
        local amp, lam = Chain.wave(anim.speed)
        local phase = 2 * math.pi * trail.sNow / lam
        local sway = math.sin(phase) * (amp / 2.4) * w
        for i = 3, 8 do
            turnAbout(pose, NECK[i], 1.1 * sway)
        end
        turnAbout(pose, "Head", -2.4 * sway)
        add(pose, "Neck6", 1.2 * math.sin(2 * phase + 0.7) * w)
    end
    anim.phase = (anim.phase + dt * anim.stepSpeed / 24) % 1
end

-- ---------- its life ----------
-- Awake it holds the neck in a slow S that sways almost imperceptibly; it studies what it watches with the head tilted, one eye then the other, swinging
-- from one angle to the next and holding there while the body stays still; the lantern bobs ahead of the face; the body below it shifts in slow ripples as the
-- coils settle; now and then it half raises the frill, displeased. It does not fidget: it waits.
local GAZE_JOINTS = { { "Neck5", 0.12 }, { "Neck6", 0.18 }, { "Neck7", 0.22 }, { "Neck8", 0.22 }, { "Head", 0.34 } }

local function lay(pose, source, weight, only)
    for joint, values in source do
        local p = pose[joint]
        if p and (not only or only(joint)) then
            for k = 1, #values do
                local gap = values[k] - p[k]
                if k <= 3 then
                    gap = (gap + 180) % 360 - 180
                end
                p[k] += gap * weight
            end
        end
    end
end

local function gazeOf(anim, now, calm)
    anim.gazeAt = anim.gazeAt or now
    anim.gaze = anim.gaze or { 0, 0, 0 }
    anim.gazeNow = anim.gazeNow or { 0, 0, 0 }
    local dt = math.clamp(now - (anim.gazeSeen or now), 0, 0.2)
    anim.gazeSeen = now
    if calm then
        local keep = math.exp(-3 * dt)
        for i = 1, 3 do
            anim.gaze[i] *= keep
        end
        anim.gazeAt = now + 1
    elseif now >= anim.gazeAt then
        local last = anim.gaze
        -- a new angle: a turn of the whole neck's top, a nod, and the head's tilt, away from the last one
        anim.gaze = { -4 + 8 * math.random(), (if last[2] > 0 then -1 else 1) * (7 + 16 * math.random()), (if last[3] > 0 then -1 else 1) * (6 + 12 * math.random()) }
        anim.gazeAt = now + 2.6 + 3.6 * math.random()
    end
    -- the head swings to it, not snaps: eased
    for i = 1, 3 do
        anim.gazeNow[i] += (anim.gaze[i] - anim.gazeNow[i]) * (1 - math.exp(-dt * 2.2))
    end
    return anim.gazeNow
end

local function flourish(anim, now, state)
    -- a held flourish now and then, never while moving or in a move: { start, length }
    local idle = state == "Guardian" and anim.moving < 0.05 and next(anim.actions) == nil
    anim.nextFlourish = anim.nextFlourish or now + 9 + 8 * math.random()
    if idle and not anim.flourish and now >= anim.nextFlourish then
        anim.flourish = { now, 3.4 + 1.2 * math.random() }
        anim.nextFlourish = now + 16 + 18 * math.random()
    end
    local f = anim.flourish
    if not f then
        return 0
    end
    local t = now - f[1]
    if t > f[2] or not idle then
        anim.flourish = nil
        return 0
    end
    return envelope(t, 1.0, f[2], 1.1)
end

local TRUNK_PHASE = {}
for i, name in TRUNK do
    TRUNK_PHASE[name] = i
end

function Rig.life(anim, pose, state, now)
    record(anim)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 1.5 elseif asleep then 0.16 else 0.3
    local breath = math.sin(now * rate * 2 * math.pi)
    local idle = 1 - anim.moving
    -- a breath ripples along the whole length, from the head to the tail
    local ripple = if state == "Weakened" then 1.7 elseif asleep then 1.0 else 0.35
    for i, bone in TRUNK do
        add(pose, bone, ripple * 0.5 * math.sin(now * rate * 2 * math.pi - 0.42 * i), 0, 0)
    end
    for i, bone in NECK do
        add(pose, bone, 0.4 * ripple * math.sin(now * rate * 2 * math.pi + 0.4 - 0.3 * i))
    end
    add(pose, "Hips", 0, 0, 0, 0.12 * breath)
    -- the frill breathes a little and never lies quite still; the lantern's stalk bobs, the barbels drift
    for _, tag in { "Left", "Right" } do
        for k = 1, 10 do
            add(pose, tag .. "Frill" .. k, 0.8 * math.sin(now * 1.3 - 0.7 * k), 0.5 * math.sin(now * 0.9 + 0.4 * k), 0)
        end
    end
    add(pose, "Lure1", 2.5 * math.sin(now * 1.15), 1.5 * math.sin(now * 0.7))
    add(pose, "Lure2", 3.5 * math.sin(now * 1.15 - 0.6), 2 * math.sin(now * 0.7 - 0.5))
    add(pose, "Lure3", 4.5 * math.sin(now * 1.15 - 1.2), 2.5 * math.sin(now * 0.7 - 1.0))
    add(pose, "Tail9", 0, 1.2 * math.sin(now * 0.8), 0)
    add(pose, "Tail11", 0, 2.4 * math.sin(now * 0.8 - 0.6), 0)
    if asleep then
        return
    end
    -- the slow S sways, almost imperceptibly (about the vertical), the weight of the coils shifting under it
    local sway = (math.sin(now * 0.31) + 0.5 * math.sin(now * 0.53 + 1.1)) * idle
    for i = 2, 8 do
        turnAbout(pose, NECK[i], 0.9 * sway)
    end
    add(pose, "Body2", 0, 0.5 * math.sin(now * 0.23) * idle, 0)
    -- the studying look: a swing to a new angle (the neck's top turned, a nod, the head tilted), held; the barbels drift behind it
    local gaze = gazeOf(anim, now, state == "Weakened" or state == "Enraged")
    local share = (if state == "Enraged" then 0.35 else 1) * idle
    for _, pair in GAZE_JOINTS do
        local bone, f = pair[1], pair[2]
        turnAbout(pose, bone, gaze[2] * f * share)
        add(pose, bone, gaze[1] * f * share * 0.6)
    end
    add(pose, "Head", 0, 0, gaze[3] * share)
    -- a displeased half raising of the frill
    local f = flourish(anim, now, state)
    if f > 0 then
        lay(pose, Clips.Poses.Display, f * 0.9)
    end
    if state == "Weakened" then
        anim:tremor("Neck8", 0.5 * math.sin(now * 27), 0, 0.4 * math.sin(now * 21))
        anim:tremor("Tail11", 0, 2.5 * math.sin(now * 17), 0)
        add(pose, "Head", 1.8 * math.sin(now * 1.9))
    elseif state == "Enraged" then
        -- thrashing: waves of violent bending run down the whole length, the neck weaving, the frill rattling, the stalk whipping
        for i, bone in TRUNK do
            add(pose, bone, 0, 3.4 * math.sin(now * 4.6 - 0.5 * i), 1.2 * math.sin(now * 3.1 - 0.4 * i))
        end
        for i = 3, 8 do
            turnAbout(pose, NECK[i], 3.5 * math.sin(now * 1.7 + 0.2 * i))
        end
        for _, tag in { "Left", "Right" } do
            for k = 1, 10 do
                anim:tremor(tag .. "Frill" .. k, 1.6 * math.sin(now * (31 + k)), 1.2 * math.sin(now * (23 + k)), 0)
            end
        end
        anim:tremor("Lure3", 3 * math.sin(now * 13), 2 * math.sin(now * 9), 0)
    end
    -- turning on the spot: the neck leads, the coils shuffle after it; walking, the chain lays the body on its path and none of this applies
    if math.abs(anim.turnRate) > 4 and anim.speed < 6 then
        local lead = math.clamp(anim.turnRate * 0.16, -34, 34)
        for i = 2, 8 do
            turnAbout(pose, NECK[i], lead * (0.06 + 0.02 * i))
        end
    end
    -- the coils shuffle after it: the body keeps its place in the world while the root turns, and swings round after the neck
    local dt = math.clamp(now - (anim.lifeSeen or now), 0, 0.1)
    anim.lifeSeen = now
    anim.shuffleAt = anim.shuffleAt or anim.heading
    anim.shuffleAt += (anim.heading - anim.shuffleAt) * (1 - math.exp(-dt * 1.1))
    local shuffle = math.clamp(-(anim.heading - anim.shuffleAt), -70, 70) * (1 - smooth((anim.speed - 2) / 4))
    add(pose, "Body1", 0, shuffle * 0.9, 0)
end

-- ---------- the moves ----------
-- A move's tracks are keyframes [frame, values...]: the pose at clip time `clock` is read between them and laid over everything else by `weight`.
local function trackAt(track, frame)
    local n = #track
    if frame <= track[1][1] then
        return track[1], track[1], 0
    end
    if frame >= track[n][1] then
        return track[n], track[n], 0
    end
    local lo, hi = 1, n
    while hi - lo > 1 do
        local mid = (lo + hi) // 2
        if track[mid][1] <= frame then
            lo = mid
        else
            hi = mid
        end
    end
    local a, b = track[lo], track[hi]
    return a, b, (frame - a[1]) / (b[1] - a[1])
end

local function playMove(pose, name, clock, weight)
    local move = Clips.Moves[name]
    local frame = math.clamp(clock * Clips.Fps, 0, move.Length * Clips.Fps)
    for joint, track in move.Tracks do
        local p = pose[joint]
        if p then
            local a, b, u = trackAt(track, frame)
            for k = 2, #a do
                local value = a[k] + (b[k] - a[k]) * u
                local gap = value - p[k - 1]
                if k <= 4 then
                    gap = (gap + 180) % 360 - 180 -- the clip may have come round a whole turn: blended the short way
                end
                p[k - 1] += gap * weight
            end
        end
    end
end

local function blend(t, total)
    return math.min(smooth(t / 0.1), smooth((total - t) / 0.3))
end

local BARBELS = {}
for _, tag in { "Left", "Right" } do
    for i = 1, 4 do
        table.insert(BARBELS, tag .. "BarbelA" .. i)
    end
    for i = 1, 3 do
        table.insert(BARBELS, tag .. "BarbelB" .. i)
    end
end

-- what a blow leaves swinging: the barbels stream forward and then trail back, the frill's ribs ripple shut, the stalk whips, the tail's tip flicks on
local function followThrough(pose, after, strength)
    local k = GuardianAnim.damped(after, 2.6, 2.4) * strength
    for i, name in BARBELS do
        add(pose, name, -9 * k, 6 * k * (if i % 2 == 0 then 1 else -1), 0)
    end
    for _, tag in { "Left", "Right" } do
        for r = 1, 10 do
            add(pose, tag .. "Frill" .. r, 5 * k * (1 + 0.05 * r), 4 * k, 3 * k)
        end
    end
    add(pose, "Lure1", 9 * k)
    add(pose, "Lure2", 12 * k)
    add(pose, "Lure3", 15 * k)
    add(pose, "Tail9", 0, 8 * k)
    add(pose, "Tail11", 0, 14 * k)
end

-- each strike's wind-up comes from the server; its clip was made for this long, and scaled to fit
local STRIKES = { CoilLash = { 0.9, 2.45 }, LanternGaze = { 1.2, 2.45 }, VoidSurge = { 1.4, 2.6 } }
local BLOW_LEAD = 0.04 -- the springs carry a blow in this late: the clip runs this far ahead, so it lands with its effect
local HOLD = { CoilLash = 0.11, LanternGaze = 0.1, VoidSurge = 0.14 }

function Rig.actions(anim, pose, now)
    -- waking: the lantern ignites, the head lifts off the coils and shakes, the frill opens and shudders, the body uncoils one loop at a time
    local t = anim:action("Awaken", 3.0)
    if t then
        playMove(pose, "Awaken", t, smooth((3.0 - t) / 0.3))
        local shiver = envelope(t - 1.55, 0.1, 0.8, 0.2)
        for _, tag in { "Left", "Right" } do
            for k = 1, 10 do
                anim:tremor(tag .. "Frill" .. k, 2.5 * shiver * math.sin(t * (41 + 2 * k)), 3 * shiver * math.sin(t * (37 + k)), 0)
            end
        end
        anim:tremor("Head", 0, 1.6 * envelope(t - 1.2, 0.05, 0.6, 0.1) * math.sin(t * 25))
        for i, name in BARBELS do
            add(pose, name, 8 * envelope(t - 1.25, 0.1, 0.5, 0.3) * math.sin(t * 9 + i), 0, 0)
        end
    end

    -- faltering: the blow it cannot take: the neck whips back and collapses, the lantern gutters, the frill folds, the head sinks to the coils
    t = anim:action("Weaken", 1.9)
    if t then
        playMove(pose, "Weaken", t, math.min(smooth(t / 0.08), smooth((1.9 - t) / 0.2)))
        anim:contact("Weaken", 1.05, 0.09)
        followThrough(pose, t - 1.05, 0.9)
        anim:tremor("Neck5", 0, 0, 3 * envelope(t, 0.15, 0.9, 0.4) * math.sin(t * 9))
    end

    -- it has seen the egg taken: the neck rears up fast, the frill thrown wide, the mouth open in a hiss, the whole body thrashing; then it settles
    t = anim:action("Enrage", 1.4)
    if t then
        playMove(pose, "Enrage", t, math.min(smooth(t / 0.06), smooth((1.4 - t) / 0.25)))
        local rattle = envelope(t - 0.2, 0.05, 0.7, 0.2)
        for _, tag in { "Left", "Right" } do
            for k = 1, 10 do
                anim:tremor(tag .. "Frill" .. k, 2.2 * rattle * math.sin(t * (45 + k)), 1.8 * rattle * math.sin(t * (35 + k)), 0)
            end
        end
        anim:tremor("Head", 2.4 * rattle * math.sin(t * 40), 1.6 * rattle * math.sin(t * 31))
        anim:tremor("Jaw", -5 * rattle * math.abs(math.sin(t * 22)))
        followThrough(pose, t - 0.5, 0.4)
    end

    -- oldest first, so the newest move is laid over the last and a blow that starts during another's recovery is seen
    local order = {}
    for name in STRIKES do
        if anim.actions[name] then
            table.insert(order, name)
        end
    end
    table.sort(order, function(x, y)
        return anim.actions[x].start < anim.actions[y].start
    end)
    for _, name in order do
        local spec, action = STRIKES[name], anim.actions[name]
        if action then
            local w = action.args[1] or spec[1]
            local rate = spec[1] / w
            local total = spec[2] / rate
            t = anim:action(name, total)
            if t then
                playMove(pose, name, (t + BLOW_LEAD) * rate, blend(t, total))
                local gather = envelope(t - 0.3 * w, 0.1, 0.45 * w, 0.08)
                if name == "CoilLash" then
                    -- the drawn-back neck trembles like a spring held: the frill's ribs shake, the tension in the coils
                    for _, tag in { "Left", "Right" } do
                        for k = 1, 10 do
                            anim:tremor(tag .. "Frill" .. k, 1.6 * gather * math.sin(t * (47 + 2 * k)), 2 * gather * math.sin(t * (41 + k)), 0)
                        end
                    end
                    anim:tremor("Neck6", 0.5 * gather * math.sin(t * 43), 0, 0.5 * gather * math.sin(t * 37))
                elseif name == "LanternGaze" then
                    -- the lantern swings in its stalk's grip and the jaw works as the light gathers
                    local charge = envelope(t - 0.4 * w, 0.2, 0.55 * w, 0.1)
                    anim:tremor("Lure3", 2.5 * charge * math.sin(t * 19), 2 * charge * math.sin(t * 15))
                    anim:tremor("Jaw", -3 * charge * math.abs(math.sin(t * 17)))
                else
                    -- the breath gathered: the chest swells, the ring-marks pulse (glow), the coils beneath shake as they rise
                    local swell = envelope(t - 0.45 * w, 0.2, 0.45 * w, 0.1)
                    for i, bone in TRUNK do
                        anim:tremor(bone, 0.7 * swell * math.sin(t * 33 - i), 0.9 * swell * math.sin(t * 29 + i), 0)
                    end
                    anim:tremor("Neck3", 0.6 * swell * math.sin(t * 31), 0, 0)
                end
                -- the blow lands: the whole wyrm stops for an instant on it (the heavier, the longer), then what hangs off it whips on past the stop
                anim:contact(name, w, HOLD[name])
                local after = t - w
                if after > 0 then
                    local shake = envelope(after, 0.02, 0.4, 0.25)
                    anim:tremor("Neck1", 1.2 * shake * math.sin(t * 44), 0, 0.8 * shake * math.sin(t * 35))
                    followThrough(pose, after, if name == "VoidSurge" then 1.2 else 1.0)
                    if name == "VoidSurge" then
                        -- the slam runs outward through the coils from the middle to the tail tip
                        for i, bone in TRUNK do
                            local u = after - 0.018 * i
                            if u > 0 then
                                add(pose, bone, -3.2 * GuardianAnim.damped(u, 2.4, 3.6), 0, 0)
                            end
                        end
                    end
                end
            end
        end
    end

    -- the leap: its crouch and spring are the wind-up, the rest the time in the air, the body flying as a long undulating ribbon
    local leap = anim.actions.SerpentLeap
    if leap then
        local windUp, air = leap.args[1] or 0.8, leap.args[2] or 1.5
        t = anim:action("SerpentLeap", windUp + air + 0.1)
        if t then
            local clock = if t < windUp then t * (0.8 / windUp) else 0.8 + (t - windUp) * (1.5 / air)
            playMove(pose, "SerpentLeap", clock, math.min(smooth(t / 0.1), 1))
            if t < windUp then
                -- coiled and loaded: the frill's ribs quiver, the whole coil humming
                local load = envelope(t - 0.3 * windUp, 0.15, 0.55 * windUp, 0.08)
                for _, tag in { "Left", "Right" } do
                    for k = 1, 10 do
                        anim:tremor(tag .. "Frill" .. k, 1.4 * load * math.sin(t * (49 + k)), 1.8 * load * math.sin(t * (43 + k)), 0)
                    end
                end
            else
                -- in the air the barbels stream back and the stalk lies along its flight
                local fly = envelope(t - windUp, 0.1, air, 0.25)
                for i, name in BARBELS do
                    add(pose, name, 7 * fly, 3 * fly * math.sin(t * 17 + i), 0)
                end
                anim:tremor("Tail11", 0, 6 * fly * math.sin(t * 21))
            end
        end
    end

    -- landing: the head strikes down first, a stop on it, the body piling down behind it in loose coils, the frill flaring for balance
    t = anim:action("Land", 0.9)
    if t then
        playMove(pose, "Land", t, smooth((0.9 - t) / 0.25))
        anim:contact("Land", 0.1, 0.1)
        followThrough(pose, t - 0.1, 1.2)
        for i, bone in TRUNK do
            local u = t - 0.1 - 0.02 * i
            if u > 0 then
                add(pose, bone, -2.8 * GuardianAnim.damped(u, 2.6, 3.4), 0, 0)
            end
        end
    end
end

-- ---------- the eyes, the lantern, the ring-marks and the frill ----------
-- The eyes are lit awake and dark asleep; they slide back into their sockets to blink. The lantern is the tell: dark asleep, a flicker then steady when it
-- wakes, a slow bob awake, guttering weakened, blazing white enraged and swinging forward and flaring white before a gaze. The ring-marks along the flanks
-- glow faintly in four groups, brighter toward the head; they light one after another from the tail up before a gaze, pulse before a surge and ripple
-- when it wakes. The frill is a smoky membrane.
local EYE = Color3.fromRGB(255, 223, 128)
local EYE_HOT = Color3.fromRGB(255, 244, 205)
local LAMP = Color3.fromRGB(255, 178, 26)
local LAMP_HOT = Color3.fromRGB(255, 244, 214)
local LAMP_DARK = Color3.fromRGB(90, 52, 12)
local RING = Color3.fromRGB(58, 214, 255)
local RING_HOT = Color3.fromRGB(215, 250, 255)
local OPEN = { Guardian = 1, Weakened = 0.8, Enraged = 0.75, Returning = 0.95 }
local SOCKET_DEPTH = 0.2
local RING_BASE = { A = 0.72, B = 0.62, C = 0.5, D = 0.38 } -- Transparency: fainter toward the tail
local RING_ORDER = { "A", "B", "C", "D" } -- the tail's group first

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.lamp = model:FindFirstChild("Lantern")
    anim.frill = model:FindFirstChild("Frill")
    anim.rings = {}
    for _, g in RING_ORDER do
        anim.rings[g] = model:FindFirstChild("Rings" .. g)
    end
    if anim.lamp and anim.lamp:IsA("BasePart") then
        local light = Instance.new("PointLight")
        light.Name = "LanternLight"
        light.Color = LAMP
        light.Range = 18
        light.Brightness = 0
        light.Shadows = false
        light.Parent = anim.lamp
        anim.lampLight = light
    end
end

function Rig.glow(anim, state, now)
    local waking = anim:action("Awaken", 3.0)
    local asleep = (state == "Dormant" or state == "Resting") and not waking
    -- the eyes
    local amount = (OPEN[state] or 1) * anim:blink(now, asleep, 5.5, 0.34)
    if waking then
        amount *= smooth((waking - 1.0) / 0.5)
    end
    anim:poseBone("Eyes", CFrame.new(0, 0, SOCKET_DEPTH * (1 - math.clamp(amount, 0, 1))))
    if anim.iris then
        anim.iris.Transparency = if asleep or (waking and waking < 0.9) then 1 else 0
        anim.iris.Color = anim.iris.Color:Lerp(if state == "Enraged" then EYE_HOT else EYE, 0.25)
    end
    -- the lantern
    local bob = 0.5 + 0.5 * math.sin(now * 1.15)
    local glow = if asleep then 0 elseif state == "Weakened" then 0.25 + 0.4 * math.abs(math.sin(now * 5.1) * math.sin(now * 1.9)) elseif state == "Enraged" then 0.95
        else 0.62 + 0.18 * bob
    local hot = if state == "Enraged" then 0.8 else 0.0
    if waking then
        -- a flicker, then steady
        local flicker = if waking < 0.9 then 0 else smooth((waking - 0.9) / 0.15) * (0.55 + 0.45 * math.abs(math.sin(waking * 31) * math.sin(waking * 11)))
        glow = glow + (flicker - glow) * (1 - smooth((waking - 1.6) / 0.6))
        hot = math.max(hot, envelope(waking - 1.0, 0.05, 0.3, 0.3) * 0.5)
    end
    local rings = {}
    for i, g in RING_ORDER do
        rings[g] = RING_BASE[g]
        if asleep then
            rings[g] = 0.9
        elseif state == "Weakened" then
            rings[g] = 0.7 + 0.2 * math.sin(now * 3 - i)
        elseif state == "Enraged" then
            rings[g] = 0.16 + 0.1 * math.sin(now * 6 - 1.3 * i)
        else
            rings[g] += 0.07 * math.sin(now * 0.9 * 2 * math.pi * 0.3 - 0.9 * i) -- a faint pulse running toward the head
        end
    end
    local ringHot = { A = 0, B = 0, C = 0, D = 0 }
    if waking then
        -- a long ripple of light along the ring-marks, tail to head
        for i, g in RING_ORDER do
            local lit = envelope(waking - (1.7 + 0.3 * (i - 1)), 0.1, 0.5, 0.35)
            rings[g] = rings[g] + (0.05 - rings[g]) * lit
            ringHot[g] = lit
        end
    end
    for name, wind in { LanternGaze = 1.2, VoidSurge = 1.4, CoilLash = 0.9 } do
        local action = anim.actions[name]
        if action then
            local w = action.args[1] or wind
            local t = now - action.start
            if name == "LanternGaze" then
                -- the lantern swings forward and flares from gold to white; the ring-marks light one after another from the tail up to the head
                local flare = envelope(t - 0.25 * w, 0.4 * w, 1.0 * w, 0.5)
                glow = glow + (1 - glow) * flare
                hot = math.max(hot, flare)
                for i, g in RING_ORDER do
                    local start = 0.2 * w + (i - 1) * 0.18 * w
                    local lit = smooth((t - start) / (0.14 * w)) * (1 - smooth((t - w - 0.35) / 0.7))
                    rings[g] = rings[g] + (0.0 - rings[g]) * lit
                    ringHot[g] = math.max(ringHot[g], lit)
                end
            elseif name == "VoidSurge" then
                local pulse = envelope(t - 0.15 * w, 0.4 * w, 0.6 * w, 0.12)
                for i, g in RING_ORDER do
                    local p = pulse * (0.5 + 0.5 * math.sin(t * 15 - 1.2 * i))
                    rings[g] = rings[g] + (0.0 - rings[g]) * p
                    ringHot[g] = math.max(ringHot[g], p)
                end
                local after = envelope(t - w, 0.03, 0.4, 0.5)
                glow = glow + (1 - glow) * after
                hot = math.max(hot, after)
            else
                local blow = envelope(t - w, 0.04, 0.3, 0.4)
                glow = glow + (1 - glow) * blow
                hot = math.max(hot, blow)
            end
        end
    end
    local flash = anim:action("Enrage", 1.4)
    if flash then
        glow = 1
        hot = math.max(hot, envelope(flash, 0.05, 0.9, 0.4))
    end
    if anim.lamp then
        anim.lamp.Color = anim.lamp.Color:Lerp(LAMP_DARK:Lerp(LAMP:Lerp(LAMP_HOT, hot), math.clamp(glow * 1.3, 0, 1)), 0.35)
        anim.lamp.Transparency += ((if asleep then 0.35 else 0) - anim.lamp.Transparency) * 0.3
    end
    if anim.lampLight then
        anim.lampLight.Brightness += (glow * (1.2 + 2.2 * hot) - anim.lampLight.Brightness) * 0.3
        anim.lampLight.Color = LAMP:Lerp(LAMP_HOT, hot)
    end
    for g, part in anim.rings do
        part.Transparency += (rings[g] - part.Transparency) * 0.3
        part.Color = part.Color:Lerp(RING:Lerp(RING_HOT, ringHot[g]), 0.3)
    end
    -- the frill: a smoky membrane, a little clearer flared wide, murkier worn out
    if anim.frill then
        local open = (anim.weights.Enraged or 0) + 0.5 * (anim.weights.Returning or 0)
        local want = if state == "Weakened" then 0.5 + 0.1 * math.sin(now * 2.3) else 0.3 - 0.1 * math.clamp(open, 0, 1)
        anim.frill.Transparency += (want - anim.frill.Transparency) * 0.1
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local function anchor(name)
    local a = Clips.Anchors[name]
    return CFrame.new(a[1], a[2], a[3])
end
local LASH_HEAD, LASH_NECK = anchor("LashHead"), anchor("LashNeck")
local GAZE_LAMP, GAZE_MOUTH = anchor("GazeLamp"), anchor("GazeMouth")
local SURGE_HEAD, SURGE_COILS, SURGE_TOP = anchor("SurgeHead"), anchor("SurgeCoils"), anchor("SurgeTop")
local LAND_HEAD, CROWN, ENRAGE_MOUTH, COIL, LAMP_REST = anchor("LandHead"), anchor("Crown"), anchor("EnrageMouth"), anchor("Coil"), anchor("LampRest")

local function ground(cf)
    return CFrame.new(cf.X, 0.6, cf.Z)
end

Rig.Fx = {
    Awaken = function(model)
        task.delay(1.0, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.flash(p * LAMP_REST, GOLD, 9)
                GuardianFx.embers(p * CROWN, 12, 14, 70, 1.8)
            end
        end)
        task.delay(2.2, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.puff(p * ground(COIL), style, 20, 14, Vector2.new(180, 8), 4, 1.3)
                GuardianFx.flash(p * CROWN, style, 22)
                GuardianFx.shake(p.Position, 1.4, 0.8)
            end
        end)
    end,
    CoilLash = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * LASH_HEAD, style, 34)
            GuardianFx.crescent(pivot * LASH_NECK * CFrame.new(LASH_HEAD.X * 0.5, 0, LASH_HEAD.Z * 0.5), style, 22)
            GuardianFx.streaks(pivot * LASH_HEAD, style, 14, 60, 50)
            GuardianFx.puff(pivot * ground(LASH_HEAD), style, 16, 16, Vector2.new(80, 3), 3, 1.1)
            GuardianFx.shake(pivot.Position, 1.8, 0.45)
            GuardianFx.kick(pivot.Position, 0.8, 0, 0.3)
        end)
    end,
    -- the lantern's light: where the lantern and the mouth are at the release is GAZE_LAMP / GAZE_MOUTH (the guardian's own axes, off its pivot)
    LanternGaze = function(model, windUp, radius, speed, arc)
        task.delay(windUp * 0.55, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.flash(p * GAZE_LAMP, GOLD, 10)
            end
        end)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * GAZE_LAMP, GOLD, 30)
            GuardianFx.streaks(pivot * GAZE_MOUTH, GOLD, 18, 90, 6)
            GuardianFx.puff(pivot * ground(GAZE_MOUTH), GOLD, 20, 20, Vector2.new(60, 4), 3, 1.1)
            GuardianFx.shake(pivot.Position, 2.2, 0.6)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 15, GOLD)
        end)
    end,
    VoidSurge = function(model, windUp, radius, speed, arc)
        task.delay(windUp * 0.5, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.flash(p * SURGE_TOP, style, 24)
            end
        end)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            local at = (pivot * SURGE_COILS).Position
            GuardianFx.shockRing(Vector3.new(at.X, pivot.Y, at.Z), style, 14, 0.5)
            GuardianFx.puff(pivot * ground(SURGE_COILS), style, 34, 28, Vector2.new(180, 8), 5, 1.4)
            GuardianFx.puff(pivot * ground(SURGE_HEAD), style, 14, 16, Vector2.new(120, 6), 3, 1.0)
            GuardianFx.flash(pivot * ground(SURGE_COILS) * CFrame.new(0, 3, 0), style, 30)
            GuardianFx.shake(pivot.Position, 3, 0.9)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 360, style)
        end)
    end,
    SerpentLeap = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 28, 22, Vector2.new(180, 10), 4, 1.3)
            GuardianFx.shake(from, 1.6, 0.5)
        end)
    end,
    Land = function(model, position)
        GuardianFx.shockRing(position, style, 22, 0.55)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 44, 36, Vector2.new(180, 6), 5, 1.6)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 20)
        GuardianFx.shake(position, 3.4, 0.9)
    end,
    Weaken = function(model)
        task.delay(1.05, function()
            if model.Parent then
                local pivot = model:GetPivot()
                GuardianFx.shockRing(pivot.Position, style, 14, 0.5)
                GuardianFx.puff(pivot * ground(LAND_HEAD), style, 18, 18, Vector2.new(180, 6), 4, 1.2)
                GuardianFx.shake(pivot.Position, 1.8, 0.6)
            end
        end)
    end,
    Enrage = function(model)
        local pivot = model:GetPivot()
        GuardianFx.flash(pivot * ENRAGE_MOUTH, GOLD, 28)
        GuardianFx.embers(pivot * ENRAGE_MOUTH, 18, 18, 100, 1.6)
        task.delay(0.5, function()
            if model.Parent then
                local p = model:GetPivot()
                GuardianFx.shockRing(p.Position, style, 18, 0.55)
                GuardianFx.puff(p * ground(COIL), style, 24, 20, Vector2.new(180, 6), 4, 1.3)
                GuardianFx.shake(p.Position, 2.2, 0.7)
            end
        end)
    end,
}

return Rig

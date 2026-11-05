-- Tiangou the Moon-Eater on a real skeleton (tools/blender/guardians/tiangou_v2.py): one skin over 30 joints, posed by
-- GuardianAnim as a jointed guardian is. The gallop is the one the owner approved in Blender, the same numbers.
--   Dormant   asleep on its feet: head low, ears back, eyes shut, tail down, the corona burning low;
--   Guardian  alert, ears up, eyes on whoever comes, the tail waving;
--   Weakened  crouched low, head down, panting, the corona guttering;
--   Enraged   the hunting crouch: neck reaching, ears flat, lips drawn back, tail up, eyes narrowed and red.
-- A turn's signs: + swings a hanging limb's far end forward and up, lowers the tail (it points back), lays an ear back (it points up),
-- lifts the nose. It trots, diagonal legs together, and gallops as it speeds up: the spine gathers under it and throws open, all four feet
-- leave the ground twice a stride, the neck nods against the spine and the movement ripples down the tail.
local GuardianAnim = require(script.Parent.Parent:WaitForChild("GuardianAnim"))
local GuardianFx = require(script.Parent.Parent:WaitForChild("GuardianFx"))

local add, envelope, smooth, keyed = GuardianAnim.add, GuardianAnim.envelope, GuardianAnim.smooth, GuardianAnim.keyed

local Rig = {}
Rig.Skinned = true
Rig.ExtraBones = { "Eyes" }

local SIDES = { "Left", "Right" }
Rig.Joints = {
    "Hips", "Spine", "Chest", "Neck1", "Neck2", "Head", "Jaw", "LeftEar", "RightEar",
    "Tail1", "Tail2", "Tail3", "Tail4", "Tail5",
}
for _, side in SIDES do
    for _, part in { "FrontBlade", "FrontUpper", "FrontLower", "FrontPaw", "BackUpper", "BackLower", "BackMeta", "BackPaw" } do
        table.insert(Rig.Joints, side .. part)
    end
end

local function both(name, values)
    return { ["Left" .. name] = values, ["Right" .. name] = values }
end
local function merged(...)
    local out = {}
    for _, t in { ... } do
        for k, v in t do
            out[k] = v
        end
    end
    return out
end

local SLEEP = merged({ Neck1 = { -30 }, Neck2 = { -14 }, Head = { 14 }, Tail1 = { 34 }, Tail2 = { 20 }, Tail3 = { 12 }, Tail4 = { 6 } }, both("Ear", { 42 }))
Rig.Poses = {
    Dormant = SLEEP,
    Resting = SLEEP,
    Guardian = { Hips = { 0, 0, 0, -0.5 }, Neck1 = { 4 }, Tail1 = { -6 } },
    Weakened = merged({ Hips = { 3, 0, 0, -1.4 }, Spine = { -3 }, Chest = { -5 }, Neck1 = { -22 }, Neck2 = { -12 }, Head = { 8 }, Jaw = { -8 },
        Tail1 = { 40 }, Tail2 = { 24 }, Tail3 = { 14 }, Tail4 = { 8 } }, both("Ear", { 30 })),
    Enraged = merged({ Hips = { -2, 0, 0, -0.9 }, Chest = { -3 }, Neck1 = { -22 }, Neck2 = { -8 }, Head = { 22 }, Jaw = { -20 }, Tail1 = { -20 }, Tail2 = { -10 } }, both("Ear", { 50 })),
    Returning = { Hips = { 0, 0, 0, -0.6 }, Neck1 = { -6 }, Head = { 4 } },
}
Rig.Gallop = { 21, 25 } -- one gait or the other: halfway between the two (their legs lead differently) no foot is ever down, and they skate
Rig.LeapAction = "MoonLeap"
Rig.Look = { Joint = "Head", Share = 0.55, Body = "Neck2", BodyShare = 0.35, Limit = 50 }

local LIMB = { Freq = 14, Damping = 0.8, Drag = 0 }
Rig.Springs = {
    Hips = { Freq = 7, Damping = 0.6, Drag = 0 },
    Spine = { Freq = 7, Damping = 0.55, Drag = 0 },
    Chest = { Freq = 6.5, Damping = 0.55, Drag = 0 },
    Neck1 = { Freq = 5, Damping = 0.5, Drag = 0.15 },
    Neck2 = { Freq = 5.5, Damping = 0.5, Drag = 0.2 },
    Head = { Freq = 6, Damping = 0.5, Drag = 0.25 },
    Jaw = { Freq = 9, Damping = 0.45, Drag = 0 },
    LeftEar = { Freq = 5, Damping = 0.35, Drag = 0.3 },
    RightEar = { Freq = 5, Damping = 0.35, Drag = 0.3 },
    Tail1 = { Freq = 3.4, Damping = 0.34, Drag = 0.5 },
    Tail2 = { Freq = 3.0, Damping = 0.32, Drag = 0.65 },
    Tail3 = { Freq = 2.7, Damping = 0.3, Drag = 0.8 },
    Tail4 = { Freq = 2.4, Damping = 0.28, Drag = 0.9 },
    Tail5 = { Freq = 2.2, Damping = 0.26, Drag = 1 },
}
for _, side in SIDES do
    for _, part in { "FrontBlade", "FrontUpper", "FrontLower", "FrontPaw", "BackUpper", "BackLower", "BackMeta", "BackPaw" } do
        Rig.Springs[side .. part] = LIMB
    end
end
Rig.Lean = { Joint = "Hips", Accel = 0.12, Bank = 0.07, Max = 8 }
-- planted feet: a foreleg folds on a positive Lower turn, a hind leg on a negative one. What's kept on the ground is the wrist or
-- the hock, and what hangs below it stays level
Rig.Legs = {}
for _, side in SIDES do
    table.insert(Rig.Legs, { Name = side .. "Front", Upper = side .. "FrontUpper", Lower = side .. "FrontLower", Foot = side .. "FrontPaw",
        Flat = { side .. "FrontPaw" }, Axis = 1, Bend = 1, Lock = true })
    table.insert(Rig.Legs, { Name = side .. "Back", Upper = side .. "BackUpper", Lower = side .. "BackLower", Foot = side .. "BackMeta",
        Flat = { side .. "BackMeta", side .. "BackPaw" }, Axis = 1, Bend = -1, Lock = true })
end
Rig.Style = { Debris = "Frost", Qi = Color3.fromRGB(110, 190, 255), QiCore = Color3.fromRGB(235, 248, 255) }

-- ---------- the gait ----------
-- { phase, upper, lower, paw[, meta] } in degrees; each leg's phase 0 at its touchdown (tiangou_v2.py: GALLOP_FRONT, GALLOP_BACK)
local GALLOP_FRONT = { { 0, 30, 6, -28 }, { 0.12, 2, 2, -4 }, { 0.26, -34, 10, 24 }, { 0.42, -44, 56, -18 }, { 0.62, -8, 70, -30 }, { 0.84, 38, 30, -24 }, { 1, 30, 6, -28 } }
local GALLOP_BACK = { { 0, 34, -20, -6, 14 }, { 0.14, 6, -12, 2, 8 }, { 0.3, -34, 6, 22, -6 }, { 0.46, -42, -28, 8, 20 }, { 0.7, 6, -60, -14, 32 }, { 0.9, 40, -42, -16, 26 }, { 1, 34, -20, -6, 14 } }
local GALLOP_LEAD = { LeftBack = 0, RightBack = 0.09, LeftFront = 0.47, RightFront = 0.56 }
-- the height the body rides at through a gallop's stride, measured in Blender so the lowest paw meets the ground
local GALLOP_RIDE = { -1.89, -1.71, -1.4, -0.99, -0.6, -0.33, -0.26, -0.41, -0.78, -1.26, -1.65, -1.7, -1.36, -0.77, -0.21, 0.13, 0.18, -0.06, -0.51, -1.04, -1.5, -1.8, -1.93, -1.96 }
-- a trot: the same anatomy, lower and quicker, diagonal legs together
local TROT_FRONT = { { 0, 20, 4, -18 }, { 0.2, 4, 2, -3 }, { 0.42, -20, 6, 14 }, { 0.58, -22, 38, -12 }, { 0.8, 6, 44, -22 }, { 1, 20, 4, -18 } }
local TROT_BACK = { { 0, 20, -14, -4, 10 }, { 0.2, 4, -9, 2, 6 }, { 0.42, -20, 2, 12, -4 }, { 0.58, -22, -24, 6, 16 }, { 0.8, 8, -42, -8, 24 }, { 1, 20, -14, -4, 10 } }
local TROT_LEAD = { LeftFront = 0, RightBack = 0.02, RightFront = 0.5, LeftBack = 0.52 }
local TROT_STRIDE, GALLOP_STRIDE = 16, 44 -- studs a stride; 44 is what the approved gallop was made at, and it keeps a planted paw still at chase speed

-- a smooth closed curve through the keys: motion in arcs, no stop at each one
local function curve(keys, phase, column)
    phase %= 1
    local count = #keys - 1
    local i = 1
    while i < count and phase > keys[i + 1][1] do
        i += 1
    end
    local u = (phase - keys[i][1]) / math.max(keys[i + 1][1] - keys[i][1], 1e-6)
    local p1, p2 = keys[i][column] or 0, keys[i + 1][column] or 0
    local p0 = keys[(i - 2) % count + 1][column] or 0
    local p3 = keys[(i + 1) % count + 1][column] or 0
    return 0.5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (3 * p1 - p0 - 3 * p2 + p3) * u * u * u)
end

local function ride(phase)
    local at = (phase % 1) * #GALLOP_RIDE
    local i = math.floor(at)
    local a, b = GALLOP_RIDE[i % #GALLOP_RIDE + 1], GALLOP_RIDE[(i + 1) % #GALLOP_RIDE + 1]
    return a + (b - a) * (at - i)
end

-- a leg's stance is its keys' first part: planted then, free the rest of the stride
local function swing(phase, stance)
    phase %= 1
    return smooth((phase - stance) / 0.06) * (1 - smooth((phase - 0.95) / 0.05))
end

function Rig.gait(anim, pose, dt)
    local g = anim.gallop
    local moving = anim.moving
    local stride = TROT_STRIDE + (GALLOP_STRIDE - TROT_STRIDE) * g
    anim.phase = (anim.phase + dt * anim.stepSpeed / stride) % 1
    local phase = anim.phase
    local function blend(trot, gallop)
        return (trot + (gallop - trot) * g) * moving
    end
    for _, side in SIDES do
        local name = side .. "Front"
        local pt, pg = phase - TROT_LEAD[name], phase - GALLOP_LEAD[name]
        local upper = blend(curve(TROT_FRONT, pt, 2), curve(GALLOP_FRONT, pg, 2))
        add(pose, side .. "FrontUpper", upper)
        add(pose, side .. "FrontLower", blend(curve(TROT_FRONT, pt, 3), curve(GALLOP_FRONT, pg, 3)))
        add(pose, side .. "FrontPaw", blend(curve(TROT_FRONT, pt, 4), curve(GALLOP_FRONT, pg, 4)))
        add(pose, side .. "FrontBlade", 0.28 * upper)
        anim:lift(name, moving * (swing(pt, 0.42) * (1 - g) + swing(pg, 0.28) * g))
        name = side .. "Back"
        pt, pg = phase - TROT_LEAD[name], phase - GALLOP_LEAD[name]
        add(pose, side .. "BackUpper", blend(curve(TROT_BACK, pt, 2), curve(GALLOP_BACK, pg, 2)))
        add(pose, side .. "BackLower", blend(curve(TROT_BACK, pt, 3), curve(GALLOP_BACK, pg, 3)))
        add(pose, side .. "BackPaw", blend(curve(TROT_BACK, pt, 4), curve(GALLOP_BACK, pg, 4)))
        add(pose, side .. "BackMeta", blend(curve(TROT_BACK, pt, 5), curve(GALLOP_BACK, pg, 5)))
        anim:lift(name, moving * (swing(pt, 0.42) * (1 - g) + swing(pg, 0.3) * g))
    end
    local turn = 2 * math.pi
    local wave = math.cos(turn * (phase - 0.02)) -- 1: gathered, -1: stretched
    local sway = math.sin(turn * phase)
    local bounce = math.abs(math.sin(turn * phase))
    add(pose, "Hips", 7 * wave * g * moving, 1.5 * sway * g * moving, 1.2 * sway * (1 - g) * moving, blend(-0.45 + 0.35 * bounce, ride(phase)))
    add(pose, "Spine", -7 * wave * g * moving)
    add(pose, "Chest", -6 * wave * g * moving, -1.5 * sway * g * moving)
    -- the neck reaches forward, low and long, nodding against the spine; the head stays level, eyes on the prey
    add(pose, "Neck1", blend(-12 + 2 * bounce, -5 * wave - 30))
    add(pose, "Neck2", blend(-6, 4 * wave - 14))
    add(pose, "Head", blend(12, 6 * wave + 34))
    for i, lag in { 0.14, 0.24, 0.34, 0.44, 0.54 } do
        local size = 14 - 1.5 * i
        add(pose, "Tail" .. i, blend(-4 * bounce, (-16 + 2 * i) - size * math.cos(turn * (phase - lag))), blend(6 * math.sin(turn * (phase - lag)), 0))
    end
    local ears = blend(14, 46 - 6 * math.cos(turn * (phase - 0.2)))
    add(pose, "LeftEar", ears)
    add(pose, "RightEar", ears)
end

-- breathing that heaves the ribs over planted paws, a restless shift of weight, the tail's wave and flicks of the ears
function Rig.life(anim, pose, state, now)
    local asleep = state == "Dormant" or state == "Resting"
    local rate = if state == "Weakened" then 1.8 elseif asleep then 0.25 else 0.5
    local breath = math.sin(now * rate * 2 * math.pi)
    add(pose, "Chest", 1.3 * breath, 0, 0, 0.18 * breath)
    add(pose, "Spine", -0.7 * breath)
    add(pose, "Hips", 0, 0, 0, 0.12 * breath)
    add(pose, "Neck1", -1.2 * math.sin(now * rate * 2 * math.pi + 0.8))
    if not asleep then
        local idle = 1 - anim.moving
        add(pose, "Hips", 0, 1.5 * math.sin(now * 0.37) * idle, 1.2 * math.sin(now * 0.51) * idle)
        add(pose, "Chest", 0, -1.5 * math.sin(now * 0.37) * idle)
        add(pose, "Neck1", 2 * math.sin(now * 0.29) * idle, 3 * math.sin(now * 0.23) * idle)
        -- one ear turns on its own now and then: it's listening
        add(pose, "LeftEar", 8 * smooth((math.sin(now * 0.61) - 0.7) * 5) * idle)
        add(pose, "RightEar", 8 * smooth((math.sin(now * 0.43 + 1.7) - 0.7) * 5) * idle)
    end
    if state == "Weakened" then
        add(pose, "Jaw", -6 * (0.5 + 0.5 * breath))      -- panting
    end
    if asleep then
        return
    end
    local wag = if state == "Enraged" then 3.2 else 1.1
    local idleWag = 1 - anim.gallop * anim.moving
    for i = 1, 5 do
        add(pose, "Tail" .. i, 0, (5 + 1.6 * i) * math.sin(now * wag - 0.45 * i) * idleWag)
    end
end

local function legs(pose, front, back)
    for _, side in SIDES do
        add(pose, side .. "FrontUpper", front)
        add(pose, side .. "BackUpper", back)
    end
end

function Rig.actions(anim, pose, now)
    -- waking: the head comes up from sleep, the ears rise, it shakes off the sleep and howls once at the sky
    local t = anim:action("Awaken", 2.0)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.5, merged({ Hips = { 2, 0, 0, -0.4 }, Neck1 = { 26 }, Neck2 = { 12 }, Head = { -6 } }, both("Ear", { -34 })), "out" },
            { 0.85, merged({ Hips = { -5, 0, 0, -0.9 }, Chest = { 8 }, Neck1 = { 38 }, Neck2 = { 30 }, Head = { 16 }, Jaw = { -34 }, Tail1 = { -14 } }, both("Ear", { -10 })), "out" },
            { 1.4, merged({ Hips = { -4, 0, 0, -0.8 }, Chest = { 7 }, Neck1 = { 36 }, Neck2 = { 28 }, Head = { 14 }, Jaw = { -30 }, Tail1 = { -12 } }, both("Ear", { -6 })), "linear" },
            { 2.0, {} },
        })
    end

    -- faltering: it staggers, the weight lurching side to side through the whole spine, the forelegs buckling
    t = anim:action("Weaken", 1.9)
    if t then
        local w = envelope(t, 0.2, 1.9, 0.6)
        add(pose, "Hips", 2 * w, 0, 5 * math.sin(t * 7) * w, -1.2 * w)
        add(pose, "Spine", 0, 0, -3 * math.sin(t * 7 - 0.3) * w)
        add(pose, "Chest", -3 * w, 0, -3 * math.sin(t * 7 - 0.6) * w)
        add(pose, "Neck1", -10 * w, 0, -5 * math.sin(t * 7 - 0.9) * w)
    end

    -- the bite: it rears back, mouth opening, the whole spine coiled, then lunges over its planted paws and snaps shut
    local bite = anim.actions.Bite
    if bite then
        local w = bite.args[1] or 0.5
        t = anim:action("Bite", w + 0.7)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w - 0.1, merged({ Hips = { 3, 0, 0, -0.5, 1.4 }, Spine = { 3 }, Chest = { 4 }, Neck1 = { 16 }, Neck2 = { 8 }, Head = { 6 }, Jaw = { -38 }, Tail1 = { -10 } }, both("Ear", { 36 })) },
                { w + 0.02, merged({ Hips = { -4, 0, 0, -1.0, -2.8 }, Spine = { -3 }, Chest = { -5 }, Neck1 = { -28 }, Neck2 = { -10 }, Head = { 8 }, Jaw = { 4 }, Tail1 = { 8 } }, both("Ear", { 50 })), "in" },
                { w + 0.25, merged({ Hips = { -3, 0, 0, -0.8, -2.2 }, Spine = { -2 }, Chest = { -4 }, Neck1 = { -22 }, Neck2 = { -8 }, Head = { 6 }, Jaw = { 0 } }, both("Ear", { 40 })), "out" },
                { w + 0.7, {} },
            })
        end
    end

    -- the eclipse howl: it coils low, drawing breath; the chest rises; at the release it sits back and throws its head to the
    -- sky, jaws wide, ears flat, holds the cry quivering, and lets it fade
    local howl = anim.actions.EclipseHowl
    if howl then
        local w = howl.args[1] or 1.0
        t = anim:action("EclipseHowl", w + 1.3)
        if t then
            keyed(pose, t, {
                { 0, {} },
                { w * 0.3, merged({ Hips = { 3, 0, 0, -1.4 }, Chest = { -5 }, Neck1 = { -22 }, Neck2 = { -10 }, Head = { 4 }, Tail1 = { 16 }, Tail2 = { 8 } }, both("Ear", { 30 })), "out" },
                { w - 0.12, merged({ Hips = { -4, 0, 0, -0.9 }, Chest = { 6 }, Neck1 = { 16 }, Neck2 = { 10 }, Jaw = { -14 }, Tail1 = { -6 } }, both("Ear", { 10 })) },
                { w + 0.06, merged({ Hips = { -10, 0, 0, -1.4, 0.8 }, Spine = { 8 }, Chest = { 12 }, Neck1 = { 30 }, Neck2 = { 24 }, Head = { 16 }, Jaw = { -46 }, Tail1 = { -18 }, Tail2 = { -6 } }, both("Ear", { 34 })), "out" },
                { w + 0.7, merged({ Hips = { -9, 0, 0, -1.3, 0.7 }, Spine = { 7 }, Chest = { 11 }, Neck1 = { 28 }, Neck2 = { 22 }, Head = { 15 }, Jaw = { -42 }, Tail1 = { -16 } }, both("Ear", { 30 })), "linear" },
                { w + 1.3, {} },
            })
            local build = smooth((t - w * 0.45) / (w * 0.55)) * (if t < w then 1 else 0)
            anim:tremor("Chest", 0.6 * build * math.sin(t * 43), 0, 0.5 * build * math.sin(t * 37))
            local burst = envelope(t - w, 0.05, 0.7, 0.3)
            anim:tremor("Head", 3 * burst * math.sin(t * 40), 1.5 * burst * math.sin(t * 31))
        end
    end

    -- the moon leap: a deep crouch (its planted paws fold under it), the spine gathered, then thrown open and stretched flat
    -- through the air, tail streaming, and gathered again for the ground
    local leap = anim.actions.MoonLeap
    if leap then
        local windUp, air = leap.args[1] or 0.55, leap.args[2] or 1.4
        t = anim:action("MoonLeap", windUp + air + 0.1)
        if t then
            local crouch = envelope(t, windUp * 0.7, windUp + 0.12, 0.12)
            add(pose, "Hips", 6 * crouch, 0, 0, -2.6 * crouch)
            add(pose, "Spine", -5 * crouch)
            add(pose, "Chest", -5 * crouch)
            add(pose, "Neck1", -14 * crouch)
            add(pose, "Tail1", -14 * crouch)
            local u = (t - windUp) / air
            if u >= 0 and u <= 1 then
                local stretch = envelope(u, 0.12, 1, 0.22)
                add(pose, "Hips", (-8 + 18 * u) * stretch)
                add(pose, "Spine", (8 - 16 * u) * stretch)
                add(pose, "Chest", (8 - 14 * u) * stretch)
                legs(pose, 58 * stretch, -50 * stretch)
                for _, side in SIDES do
                    add(pose, side .. "FrontLower", 8 * stretch)
                    add(pose, side .. "BackLower", 16 * stretch)
                    add(pose, side .. "BackMeta", -10 * stretch)
                end
                add(pose, "Neck1", -22 * stretch)
                add(pose, "Neck2", -8 * stretch)
                add(pose, "Head", 24 * stretch)
                add(pose, "Jaw", -24 * stretch * u)
                add(pose, "LeftEar", 48 * stretch)
                add(pose, "RightEar", 48 * stretch)
                add(pose, "Tail1", -18 * stretch)
                add(pose, "Tail2", -10 * stretch)
            end
        end
    end

    -- landing: the shoulders take it, the spine folding, sinking deep over the paws, and it rebounds
    t = anim:action("Land", 0.7)
    if t then
        keyed(pose, t, {
            { 0, {} },
            { 0.08, merged({ Hips = { 8, 0, 0, -2.6 }, Spine = { -5 }, Chest = { -8 }, Neck1 = { -14 }, Tail1 = { 18 }, Tail2 = { 10 } }, both("Ear", { 20 })), "out" },
            { 0.3, { Hips = { -2, 0, 0, 0.1 }, Chest = { 2 }, Neck1 = { 4 } } },
            { 0.7, {} },
        })
    end
end

-- ---------- the eyes and the corona ----------
-- Asleep the eyes are hidden (the lid over them is the skin). A blink, or a narrowed glare, slides the eyes back into their sockets
-- on their bone: the skin's edge closes over them.
local EYE = Color3.fromRGB(255, 154, 0)
local RAGE = Color3.fromRGB(255, 60, 20)
local OPEN = { Guardian = 1, Weakened = 1, Enraged = 0.45, Returning = 0.85 }
local SOCKET_DEPTH = 0.3 -- studs back at fully shut

function Rig.setup(anim)
    local model = anim.model
    anim.iris = model:FindFirstChild("Eyes")
    anim.pupils = model:FindFirstChild("Pupils")
    anim.corona = model:FindFirstChild("Corona")
end

function Rig.glow(anim, state, now)
    local awaken = anim:action("Awaken", 2.0)
    local asleep = (state == "Dormant" or state == "Resting") and not awaken
    local amount = (OPEN[state] or 1) * anim:blink(now, asleep, 3, 0.26)
    if awaken then
        amount *= smooth((awaken - 0.3) / 0.5)
    end
    anim:poseBone("Eyes", CFrame.new(0, 0, SOCKET_DEPTH * (1 - math.clamp(amount, 0, 1))))
    local color = if state == "Enraged" then RAGE else EYE
    if state == "Weakened" then
        color = Color3.fromRGB(150, 80, 0):Lerp(EYE, 0.5 + 0.5 * math.sin(now * 12) * math.sin(now * 4.7))
    end
    for _, part in { anim.iris, anim.pupils } do
        if part then
            part.Transparency = if asleep then 1 else 0
        end
    end
    if anim.iris then
        anim.iris.Color = anim.iris.Color:Lerp(color, 0.25)
    end

    -- the corona: low asleep, guttering weakened, flickering in its rage, flaring as it howls
    local corona = anim.corona
    if corona then
        local fade = if asleep then 0.55 elseif state == "Weakened" then 0.25 + 0.25 * math.abs(math.sin(now * 6) * math.sin(now * 2.3))
            elseif state == "Enraged" then 0.12 * math.abs(math.sin(now * 17))
            else 0.05
        local howl = anim.actions.EclipseHowl
        if howl then
            fade *= 1 - envelope(now - howl.start - (howl.args[1] or 1), 0.05, 0.8, 0.5)
        end
        corona.Transparency += (fade - corona.Transparency) * 0.3
    end
end

-- ---------- its effects (GuardianController calls Rig.Fx[action](model, ...)) ----------
local style = Rig.Style
local ECLIPSE = CFrame.new(0, 27.5, -3.5)       -- the eclipse's centre (hound-local)
local MOUTH = CFrame.new(0, 21, -23)            -- before its jaws
local BITE = CFrame.new(0, 3, -24)              -- where the bite lands

Rig.Fx = {
    Awaken = function(model)
        local pivot = model:GetPivot()
        task.delay(0.7, function()
            if model.Parent then
                GuardianFx.flash(model:GetPivot() * ECLIPSE, style, 22)
                GuardianFx.streaks(model:GetPivot() * MOUTH * CFrame.Angles(math.rad(50), 0, 0), style, 10, 50, 25)
            end
        end)
        GuardianFx.shake(pivot.Position, 0.8, 0.6)
    end,
    Bite = function(model, windUp)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.crescent(pivot * MOUTH, style, 14)
            GuardianFx.puff(pivot * BITE, style, 14, 16, 70, 3, 1)
            GuardianFx.shake(pivot.Position, 1.2, 0.35)
        end)
    end,
    EclipseHowl = function(model, windUp, radius, speed, arc)
        task.delay(windUp, function()
            if not model.Parent then
                return
            end
            local pivot = model:GetPivot()
            GuardianFx.flash(pivot * ECLIPSE, style, 30)
            GuardianFx.streaks(pivot * ECLIPSE * CFrame.Angles(math.rad(90), 0, 0), style, 18, 45, 60)
            GuardianFx.shake(pivot.Position, 2, 0.9)
            GuardianFx.wave(pivot.Position, pivot.LookVector, radius, speed, arc or 180, style)
        end)
    end,
    MoonLeap = function(model, windUp, air, from, to)
        GuardianFx.telegraph(to, windUp + air, style)
        task.delay(windUp, function()
            GuardianFx.puff(CFrame.new(from + Vector3.new(0, 0.5, 0)), style, 22, 20, Vector2.new(180, 10), 3, 1.2)
        end)
    end,
    Land = function(model, position)
        GuardianFx.puff(CFrame.new(position + Vector3.new(0, 0.5, 0)), style, 34, 30, Vector2.new(180, 8), 4, 1.4)
        GuardianFx.flash(CFrame.new(position + Vector3.new(0, 2, 0)), style, 16)
        GuardianFx.shake(position, 2.6, 0.6)
    end,
}

return Rig

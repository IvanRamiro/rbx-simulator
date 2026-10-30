local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")

local PetRig = {}

local SPARKLE = "rbxasset://textures/particles/sparkles_main.dds"

local function pose(motor, cframe)
    if motor then
        motor.Transform = cframe
    end
end

local function smoothstep(edge0, edge1, x)
    local t = math.clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
end

local SUN_DRAGON_LEGS = { LegFL = 0, LegBR = 0.25, LegFR = math.pi, LegBL = math.pi + 0.25 }
local function animateSunDragon(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    s.stride = (s.stride or 0) + rig.deltaTime * (1.2 + 5.5 * moving)
    s.flap = (s.flap or 0) + rig.deltaTime * (1.1 + 5.5 * fly)
    local stride, beat = s.stride, math.sin(s.flap)
    local breathe = math.sin(t * 0.9)
    local flare = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)

    pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.03 * math.abs(math.sin(stride)) * moving + 0.07 * beat * fly + 0.12 * flare) * u, 0)
        * CFrame.Angles(0.02 * breathe + 0.22 * fly - 0.25 * flare, 0, 0.04 * math.sin(stride) * moving))
    local gaze = 0.3 * math.sin(t * 0.3) * (1 - fly) * (1 - flare)
    pose(m.Neck, CFrame.Angles(0.04 * math.sin(t * 0.7) - 0.18 * fly + 0.2 * flare, gaze * 0.5, 0))
    pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.85 + 1) - 0.1 * fly + 0.28 * flare, gaze * 0.6, 0.05 * math.sin(t * 0.5)))

    for _, side in { "L", "R" } do
        local sign = rig.sides["Wing" .. side] or 0
        local rest = 0.05 * breathe
        local stroke = (0.6 * beat - 0.05) * fly
        pose(m["Wing" .. side], CFrame.Angles(0, sign * (0.06 * breathe - 0.25 * flare), sign * (rest + stroke + 0.3 * flare)))
        pose(m["Wing" .. side .. "2"], CFrame.Angles(0, sign * 0.15 * math.max(0, -beat) * fly,
            sign * (0.04 * math.sin(t * 0.9 + 0.6) + 0.35 * math.max(0, beat) * fly + 0.25 * flare)))
    end

    for name, phase in SUN_DRAGON_LEGS do
        local front = string.sub(name, 4, 4) == "F"
        local swing = 0.35 * math.sin(stride + phase) * moving
        local tuck = (if front then 0.7 else -0.45) * fly
        pose(m[name], CFrame.Angles(swing + tuck + (if front then -0.35 else 0.2) * flare, 0, 0))
    end

    local sway = math.sin(t * 0.75)
    pose(m.Tail, CFrame.Angles(0.06 * math.sin(t * 0.6) - 0.2 * fly + 0.15 * flare, 0.22 * sway, 0))
    pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 0.6 - 0.7) - 0.15 * fly + 0.25 * flare, 0.32 * math.sin(t * 0.75 - 0.9), 0))
end

local WYRM_CHAIN = { "Head", "Heart", "Seg1", "Seg2", "Seg3", "Seg4", "Seg5", "Seg6" }
local function animateBeadWyrm(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    s.phase = (s.phase or 0) + rig.deltaTime * (2.2 + 3 * moving + 4 * fly)
    local rise = (0.035 + 0.05 * moving + 0.02 * fly) * u
    local sway = (0.035 + 0.06 * moving) * u
    for index, name in WYRM_CHAIN do
        local wave = s.phase - (index - 1) * 0.75
        local spread = (index - 1) * 0.07 * u * nova
        local offset = Vector3.new(sway * math.sin(wave * 0.8 + 1), rise * math.sin(wave), spread)
        local pitch = -0.28 * math.cos(wave) * (rise / u) * 10
        if name == "Head" then
            pitch += 0.06 * math.sin(t * 1.3) + 0.45 * nova
            pose(m.Head, CFrame.new(offset) * CFrame.Angles(pitch, 0.18 * math.sin(t * 0.7) * (1 - nova), 0))
        else
            pose(m[name], CFrame.new(offset) * CFrame.Angles(pitch, 0.12 * math.sin(wave * 0.8), 0))
        end
    end
    for name, side in rig.sides do
        if string.sub(name, 1, 4) == "Gill" then
            local k = tonumber(string.sub(name, -1)) or 1
            local flutter = 0.18 * math.sin(t * 7 + k * 1.3) + 0.1 * math.sin(t * 11 + k)
            pose(m[name], CFrame.Angles(0.1 * math.sin(t * 5 + k), side * (0.15 * flutter + 0.35 * nova), side * (flutter + 0.25 * fly)))
        end
    end
    pose(m.Tail, CFrame.Angles(0.15 * math.sin(t * 4), 0.35 * math.sin(t * 3.1), 0))
end

local function animateOssuary(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time

    pose(m.Ribs, CFrame.new(0, (0.06 * math.sin(t * 1.1) + 0.2 * nova) * u, 0)
        * CFrame.Angles(-0.1 * moving - 0.18 * fly + 0.04 * math.sin(t * 0.8), 0, 0.09 * math.sin(t * 0.9) * (1 - 0.5 * moving)))

    pose(m.Soul, CFrame.new(0.02 * u * math.sin(t * 9), (0.03 * math.sin(t * 6.3) + 0.35 * nova) * u, 0)
        * CFrame.Angles(0.06 * math.sin(t * 7.1), t * 1.5, 0.06 * math.sin(t * 8.3)))

    pose(m.Neck, CFrame.Angles(0.05 * math.sin(t * 0.9) - 0.08 * fly + 0.2 * nova, 0.1 * math.sin(t * 0.5), 0))
    pose(m.Skull, CFrame.Angles(
        0.08 * math.sin(t * 0.7) + 0.25 * nova,
        0.15 * math.sin(t * 0.45) * (1 - nova),
        0.18 * math.sin(t * 0.35) * (1 - nova)))

    local chatter = math.max(0, math.sin(t * 0.8)) ^ 8 * (0.5 + 0.5 * math.sin(t * 30))
    pose(m.Jaw, CFrame.Angles(-(0.14 * chatter + 0.6 * nova + 0.05 * fly), 0, 0))

    for _, name in { "WingL", "WingR" } do
        local side = rig.sides[name]
        local raise = 0.12 * math.sin(t * 1.3) * (1 - fly) - 0.25 * moving + (0.1 + 0.5 * math.sin(t * 3.2)) * fly + 0.5 * nova
        local sweep = -0.15 * moving + 0.3 * nova
        pose(m[name], CFrame.Angles(0, side * sweep, side * raise))
    end

    for index = 1, 5 do
        pose(m["Tail" .. index], CFrame.Angles(
            0.06 * math.sin(t * 1.2 - index * 0.7) + 0.08 * fly,
            0.18 * math.sin(t * 1.0 - index * 0.6) * (1 + moving),
            0))
    end

    local ghost = rig.parts.Ghost
    if ghost then
        ghost.Transparency = 1 - 0.62 * nova
    end
end

local HOUND_HEADS = { C = 0, L = 2.1, R = 4.2 }
local function animateHellhound(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    s.stride = (s.stride or 0) + rig.deltaTime * (7 * moving + 9 * fly)
    local stride = s.stride

    pose(m.Body, CFrame.new(0, (0.02 * math.sin(t * 1.8) + 0.04 * math.abs(math.sin(stride)) * moving + 0.06 * math.sin(stride) * fly) * u, 0)
        * CFrame.Angles(0.06 * math.sin(stride) * fly - 0.05 * moving + 0.08 * nova, 0, 0.03 * math.sin(stride * 0.5) * moving))

    for _, name in { "LegFL", "LegFR", "LegBL", "LegBR" } do
        local front = string.sub(name, 4, 4) == "F"
        local left = string.sub(name, 5, 5) == "L"
        local trot = 0.45 * math.sin(stride + (if front == left then 0 else math.pi)) * moving
        local gallop = (0.65 * math.sin(stride + (if front then 0 else math.pi) + (if left then 0.3 else 0)) + (if front then 0.25 else -0.25)) * fly
        pose(m[name], CFrame.Angles(trot + gallop, 0, 0))
    end

    for tag, phase in HOUND_HEADS do
        local side = rig.sides["Head" .. tag] or 0
        local sniff = 0.04 * math.sin(t * 9 + phase) * math.max(0, math.sin(t * 0.7 + phase)) ^ 4
        local snap = math.max(0, math.sin(t * 0.45 + phase)) ^ 14
        local yaw = (0.32 * math.sin(t * 0.55 + phase) + side * 0.08) * (1 - 0.5 * moving) * (1 - nova)
        local pitch = 0.08 * math.sin(t * 0.8 + phase) + sniff - 0.1 * fly + 0.6 * nova - 0.15 * snap
        pose(m["Head" .. tag], CFrame.new(0, 0, -0.08 * u * snap) * CFrame.Angles(pitch, yaw, 0.08 * math.sin(t * 0.6 + phase)))
        local growl = 0.05 * (0.5 + 0.5 * math.sin(t * 13 + phase)) * math.max(0, math.sin(t * 0.3 + phase))
        pose(m["Jaw" .. tag], CFrame.Angles(-(0.5 * snap + 0.7 * nova + growl + 0.08 * fly), 0, 0))
    end

    local wag = math.sin(t * (2.2 + 4 * moving + 4 * fly))
    pose(m.Tail1, CFrame.Angles(0.1 * math.sin(t * 1.1) - 0.15 * fly, (0.22 + 0.15 * moving) * wag, 0))
    pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 1.1 - 0.8), (0.3 + 0.2 * moving) * math.sin(t * (2.2 + 4 * moving + 4 * fly) - 0.9), 0))
end

local QILIN_LEGS = { LegFL = 0, LegFR = 0.35, LegBL = math.pi, LegBR = math.pi + 0.35 }
local function animateQilin(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (1.6 + 6.5 * pace)
    local stride = s.stride
    local reach = 0.18 + 0.4 * pace

    pose(m.Body, CFrame.new(0, (0.06 * math.sin(t * 1.3) + 0.07 * math.sin(stride) * pace) * u, 0)
        * CFrame.Angles(0.07 * math.sin(stride + 0.6) * pace - 0.42 * nova, 0, 0.04 * math.sin(t * 0.7)))

    for name, phase in QILIN_LEGS do
        local front = string.sub(name, 4, 4) == "F"
        local swing = math.sin(stride + phase)
        local fold = math.max(0, math.sin(stride + phase + 1.3))
        local rear = if front then 0.7 * nova else -0.25 * nova
        pose(m[name], CFrame.Angles(reach * swing + (if front then 0.12 else -0.12) * fly + rear, 0, 0))
        pose(m[name .. "2"], CFrame.Angles((if front then -1 else 1) * ((0.25 + 0.55 * pace) * fold + 0.5 * nova), 0, 0))
    end

    local look = 0.3 * math.sin(t * 0.4) * (1 - pace)
    pose(m.Neck, CFrame.Angles(0.05 * math.sin(t * 1.3 - 0.5) - 0.06 * math.sin(stride) * pace + 0.25 * nova, look * 0.5, 0))
    pose(m.Head, CFrame.Angles(0.06 * math.sin(t * 0.9) + 0.35 * nova, look * 0.6, 0.06 * math.sin(t * 0.5)))

    local sway = math.sin(t * (1.4 + 2 * pace))
    pose(m.Tail1, CFrame.Angles(0.12 * math.sin(t * 1.2) - 0.1 * pace + 0.3 * nova, 0.25 * sway, 0))
    pose(m.Tail2, CFrame.Angles(0.15 * math.sin(t * 1.2 - 0.9) + 0.2 * nova, 0.35 * math.sin(t * (1.4 + 2 * pace) - 1.1), 0))
end

local function animateSprite(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    local bloom = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)
    local drift = math.sin(t * 1.4)

    pose(m.Body, CFrame.new(0, (0.12 * drift + 0.25 * bloom) * u, 0)
        * CFrame.Angles(-0.18 * pace + 0.05 * math.sin(t * 0.9), 0.15 * math.sin(t * 0.4), 0.06 * math.sin(t * 0.7)))
    pose(m.Cap, CFrame.Angles(0.08 * math.sin(t * 1.4 + 0.6) + 0.12 * pace - 0.25 * bloom, t * 0.4 % (2 * math.pi), 0.08 * math.sin(t * 1.1)))
    for _, name in { "ArmL", "ArmR" } do
        local side = rig.sides[name] or 0
        local wave = math.sin(t * 1.8 + side)
        pose(m[name], CFrame.Angles(0.25 * wave * (1 - pace) - 0.3 * pace - 0.6 * bloom, 0, side * (0.15 * math.sin(t * 1.2 + side) - 0.7 * bloom)))
    end
    pose(m.Threads, CFrame.Angles(0.25 * math.sin(t * 2.1) + 0.45 * pace, 0.3 * math.sin(t * 1.3), 0.2 * math.sin(t * 1.7 + 1)))
end

local function animateGolem(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (1.2 + 4.5 * pace)
    local stride = s.stride
    local breathe = math.sin(t * 0.9)
    local slam = math.sin(math.min(nova * 1.4, 1) * math.pi / 2)

    pose(m.Body, CFrame.new(0, (0.025 * breathe + 0.06 * math.abs(math.sin(stride)) * pace - 0.12 * slam) * u, 0)
        * CFrame.Angles(0.04 * breathe - 0.08 * pace + 0.25 * slam, 0, 0.07 * math.sin(stride) * pace))
    pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.6) - 0.2 * slam, 0.18 * math.sin(t * 0.35) * (1 - pace), 0.04 * math.sin(t * 0.5)))

    for _, name in { "LegL", "LegR" } do
        local side = if name == "LegL" then 0 else math.pi
        pose(m[name], CFrame.Angles(0.32 * math.sin(stride + side) * pace - 0.15 * slam, 0, 0))
    end
    for _, name in { "ArmL", "ArmR" } do
        local side = if name == "ArmL" then math.pi else 0
        local heavy = name == "ArmR"
        local lift = (if heavy then 1.6 else 1.2) * slam
        pose(m[name], CFrame.Angles(0.3 * math.sin(stride + side) * pace + 0.05 * breathe - lift, 0, (if heavy then -0.05 else 0.05) * breathe))
        pose(m[name .. "2"], CFrame.Angles(-0.12 * math.max(0, math.sin(stride + side)) * pace - 0.25 * slam, 0, 0))
    end
end

local PANDA_LEGS = { LegFL = 0, LegBR = 0.3, LegFR = math.pi, LegBL = math.pi + 0.3 }
local function animatePanda(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (1 + 5 * pace)
    local stride = s.stride
    local breathe = math.sin(t * 1.1)
    s.lotus = if rig.nova then (s.lotus or 0) + rig.deltaTime else 0
    local rear = smoothstep(0, 0.75, s.lotus) * (1 - smoothstep(0.88, 1.06, s.lotus)) * math.min(1, nova * 3)
    local impact = smoothstep(0.95, 1.1, s.lotus) * (1 - smoothstep(1.2, 1.9, s.lotus))

    pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.04 * math.abs(math.sin(stride)) * pace + 0.32 * rear - 0.06 * impact) * u, 0)
        * CFrame.Angles(0.03 * breathe - 0.6 * rear + 0.14 * impact, 0, 0.06 * math.sin(stride) * pace))
    pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.7) + 0.04 * math.sin(stride * 2) * pace + 0.3 * rear - 0.12 * impact,
        0.25 * math.sin(t * 0.35) * (1 - pace) * (1 - rear), 0.05 * math.sin(t * 0.5) + 0.04 * math.sin(stride) * pace))

    for name, phase in PANDA_LEGS do
        local front = string.sub(name, 4, 4) == "F"
        local swing = 0.35 * math.sin(stride + phase) * pace
        local lift = if front then -0.75 * rear + 0.3 * impact else 0.6 * rear - 0.1 * impact
        pose(m[name], CFrame.Angles(swing + lift, 0, 0))
    end
end

local DEER_LEGS = { LegBL = 0, LegFL = math.pi / 2, LegBR = math.pi, LegFR = 3 * math.pi / 2 }
local function animateDeer(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (1.2 + 6 * pace)
    local stride = s.stride
    local breathe = math.sin(t * 1.2)
    s.grove = if rig.nova then (s.grove or 0) + rig.deltaTime else 0
    local rear = smoothstep(0, 0.7, s.grove) * (1 - smoothstep(0.9, 1.08, s.grove)) * math.min(1, nova * 3)
    local land = smoothstep(0.98, 1.1, s.grove) * (1 - smoothstep(1.2, 1.8, s.grove))

    pose(m.Body, CFrame.new(0, (0.015 * breathe + 0.04 * math.abs(math.sin(stride * 2)) * pace + 0.25 * rear - 0.05 * land) * u, 0)
        * CFrame.Angles(-0.5 * rear + 0.1 * land + 0.02 * math.sin(stride * 2) * pace, 0, 0.03 * math.sin(stride) * pace))
    local look = 0.35 * math.sin(t * 0.3) * (1 - pace) * (1 - rear)
    pose(m.Neck, CFrame.Angles(0.04 * math.sin(t * 0.8) - 0.05 * math.sin(stride * 2) * pace + 0.3 * rear - 0.1 * land, look * 0.45, 0))
    pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 1.1 + 1) + 0.2 * rear * math.sin(s.grove * 9) - 0.08 * land, look * 0.55, 0.05 * math.sin(t * 0.6)))

    for name, phase in DEER_LEGS do
        local front = string.sub(name, 4, 4) == "F"
        local swing = math.sin(stride + phase)
        local lift = math.max(0, math.sin(stride + phase + 1.2))
        local rearing = if front then 0.9 * rear - 0.25 * land else 0.45 * rear
        pose(m[name], CFrame.Angles((0.3 + 0.15 * fly) * swing * pace + rearing, 0, 0))
        pose(m[name .. "2"], CFrame.Angles((if front then -1 else 1) * (0.7 * lift * pace + (if front then 1.4 else 0.2) * rear), 0, 0))
    end
end

local function animatePhoenix(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    s.stride = (s.stride or 0) + rig.deltaTime * (1.5 + 5 * moving)
    s.flap = (s.flap or 0) + rig.deltaTime * (1.2 + 6 * fly)
    local breathe = math.sin(t * 1.0)
    local beat = math.sin(s.flap)
    local flare = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)

    pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.06 * math.sin(s.flap) * fly + 0.12 * flare) * u, 0)
        * CFrame.Angles(0.03 * breathe + 0.35 * fly - 0.12 * flare, 0, 0.04 * math.sin(s.stride) * moving))
    pose(m.Neck, CFrame.Angles(0.05 * math.sin(t * 0.7) - 0.25 * fly - 0.15 * flare, 0.12 * math.sin(t * 0.33) * (1 - fly), 0))
    pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.9 + 1) - 0.1 * fly - 0.2 * flare, 0.3 * math.sin(t * 0.4) * (1 - fly) * (1 - flare), 0.08 * math.sin(t * 0.55)))

    for _, side in { "L", "R" } do
        local sign = rig.sides["Wing" .. side] or 0
        local idle = 0.06 * math.sin(t * 1.1 + (if side == "L" then 0 else 0.4))
        local stroke = (0.55 * beat - 0.1) * fly
        pose(m["Wing" .. side], CFrame.Angles(0, sign * (0.08 * breathe * (1 - fly) - 0.2 * flare), sign * (idle + stroke + 0.35 * flare)))
        pose(m["Wing" .. side .. "2"], CFrame.Angles(0, sign * 0.12 * math.max(0, -beat) * fly, sign * (0.04 * math.sin(t * 1.1 + 0.6) + 0.3 * math.max(0, beat) * fly + 0.2 * flare)))
        local leg = m["Leg" .. side]
        if leg then
            local swing = 0.35 * math.sin(s.stride + (if side == "L" then 0 else math.pi)) * moving
            pose(leg, CFrame.Angles(swing + 0.9 * fly, 0, 0))
        end
    end

    pose(m.Tail, CFrame.Angles(0.06 * math.sin(t * 0.8) - 0.3 * fly + 0.2 * flare, 0.14 * math.sin(t * 0.6), 0.05 * math.sin(t * 1.3)))
end

local SPHINX_LEGS = { LegFL = 0, LegBR = 0.2, LegFR = math.pi, LegBL = math.pi + 0.2 }
local function animateSphinx(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (1 + 5.5 * pace)
    local stride = s.stride
    local breathe = math.sin(t * 0.9)
    local rise = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)

    pose(m.Body, CFrame.new(0, (0.015 * breathe + 0.03 * math.abs(math.sin(stride)) * pace + 0.1 * rise) * u, 0)
        * CFrame.Angles(0.02 * breathe - 0.22 * rise, 0, 0.05 * math.sin(stride) * pace))
    local gaze = 0.32 * math.sin(t * 0.25) * (1 - pace) * (1 - rise)
    pose(m.Head, CFrame.Angles(0.04 * math.sin(t * 0.6) + 0.12 * rise, gaze, 0.06 * math.sin(t * 0.35) * (1 - pace)))

    for name, phase in SPHINX_LEGS do
        local front = string.sub(name, 4, 4) == "F"
        local swing = 0.38 * math.sin(stride + phase) * pace
        pose(m[name], CFrame.Angles(swing + (if front then -0.3 * rise else 0.22 * rise), 0, 0))
    end

    local sway = math.sin(t * 0.8)
    pose(m.Tail, CFrame.Angles(0.08 * math.sin(t * 0.6) - 0.35 * rise, 0.25 * sway, 0))
    pose(m.Tail2, CFrame.Angles(0.12 * math.sin(t * 0.6 - 0.7) - 0.3 * rise, 0.35 * math.sin(t * 0.8 - 0.9), 0))
end

PetRig.Profiles = {
    SunscaleDragon = {
        Joints = {
            Body = "Root",
            Neck = "Body",
            Head = "Neck",
            WingL = "Body",
            WingR = "Body",
            WingL2 = "WingL",
            WingR2 = "WingR",
            LegFL = "Body",
            LegFR = "Body",
            LegBL = "Body",
            LegBR = "Body",
            Tail = "Body",
            Tail2 = "Tail",
        },
        Attached = {},
        SeeThrough = {},
        GlowColors = {
            ffdd81 = Color3.fromRGB(255, 175, 40),
            ffeaa6 = Color3.fromRGB(255, 195, 70),
            ffbc3f = Color3.fromRGB(255, 145, 15),
            ffb338 = Color3.fromRGB(255, 120, 10),
            ff952c = Color3.fromRGB(255, 100, 10),
            f98127 = Color3.fromRGB(220, 60, 0),
        },
        Effects = {
            Motes = "Body",
            Light = "Body",
            Pulse = "Body",
            Burst = "Body",
            Sparks = { "Head_Crest", "Tail2_Sun" },
            Trail = { "WingL2_Tip", "WingR2_Tip" },
            Blast = "SolarCorona",
            NovaLight = 3,
        },
        Colors = {
            Gold = Color3.fromHex("FFC24A"),
            Amber = Color3.fromHex("6B2E12"),
            Orange = Color3.fromHex("FF8A2A"),
            Sun = Color3.fromHex("FFE9A6"),
            Ivory = Color3.fromHex("FFF4DC"),
        },
        Animate = animateSunDragon,
    },
}

PetRig.Profiles.EmberWyrm = {
    Joints = {
        Head = "Root",
        Heart = "Root",
        Seg1 = "Root",
        Seg2 = "Root",
        Seg3 = "Root",
        Seg4 = "Root",
        Seg5 = "Root",
        Seg6 = "Root",
        Tail = "Seg6",
        GillL1 = "Head",
        GillL2 = "Head",
        GillL3 = "Head",
        GillR1 = "Head",
        GillR2 = "Head",
        GillR3 = "Head",
    },
    Attached = {},
    SeeThrough = {},
    Effects = {
        Motes = "Heart",
        Light = "Heart",
        Pulse = "Heart",
        Burst = "Heart",
        Sparks = { "GillL1_Tip", "GillR1_Tip" },
        Trail = "Tail_Tip",
        Blast = "Eruption",
    },
    Colors = {
        Gold = Color3.fromRGB(255, 120, 30),
        Amber = Color3.fromRGB(170, 30, 8),
        Orange = Color3.fromRGB(255, 70, 15),
        Sun = Color3.fromRGB(255, 180, 60),
        Ivory = Color3.fromRGB(255, 200, 140),
    },
    Animate = animateBeadWyrm,
}

PetRig.Profiles.BonefireDragon = {
    Joints = {
        Ribs = "Root",
        Soul = "Ribs",
        Ghost = "Ribs",
        Neck = "Ribs",
        Skull = "Neck",
        Jaw = "Skull",
        WingL = "Ribs",
        WingR = "Ribs",
        Tail1 = "Ribs",
        Tail2 = "Tail1",
        Tail3 = "Tail2",
        Tail4 = "Tail3",
        Tail5 = "Tail4",
    },
    Attached = {},
    SeeThrough = {},
    SeeThroughGlow = { ["95bcff"] = 1, ["61a0ff"] = 0.3 },
    Effects = {
        Motes = "Soul",
        Light = "Soul",
        Pulse = "Soul",
        Burst = "Soul",
        Sparks = { "Skull_EyeL", "Skull_EyeR" },
        Trail = "Tail5_Tip",
        Blast = "SoulLantern",
    },
    Colors = {
        Gold = Color3.fromRGB(120, 190, 255),
        Amber = Color3.fromRGB(40, 80, 220),
        Orange = Color3.fromRGB(70, 130, 255),
        Sun = Color3.fromRGB(210, 235, 255),
        Ivory = Color3.fromRGB(235, 245, 255),
    },
    Animate = animateOssuary,
}

PetRig.Profiles.DreadfangCerberus = {
    Joints = {
        Body = "Root",
        HeadC = "Body",
        HeadL = "Body",
        HeadR = "Body",
        JawC = "HeadC",
        JawL = "HeadL",
        JawR = "HeadR",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        Tail1 = "Body",
        Tail2 = "Tail1",
    },
    Attached = {},
    SeeThrough = {},
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "HeadC_Eye", "HeadL_Eye", "HeadR_Eye" },
        Trail = "Tail2_Tip",
        Blast = "HellBreath",
    },
    Colors = {
        Gold = Color3.fromRGB(40, 215, 255),
        Amber = Color3.fromRGB(20, 70, 160),
        Orange = Color3.fromRGB(30, 150, 255),
        Sun = Color3.fromRGB(190, 250, 255),
        Ivory = Color3.fromRGB(225, 250, 255),
    },
    Animate = animateHellhound,
}

PetRig.Profiles.GoldenKirin = {
    Joints = {
        Body = "Root",
        Neck = "Body",
        Head = "Neck",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        LegFL2 = "LegFL",
        LegFR2 = "LegFR",
        LegBL2 = "LegBL",
        LegBR2 = "LegBR",
        Tail1 = "Body",
        Tail2 = "Tail1",
    },
    Attached = {},
    SeeThrough = {},
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Head",
        Burst = "Body",
        Sparks = { "Head_EyeL", "Head_EyeR" },
        Trail = "Tail2_Tip",
        Blast = "AuspiciousClouds",
    },
    Colors = {
        Gold = Color3.fromRGB(70, 235, 195),
        Amber = Color3.fromRGB(70, 90, 230),
        Orange = Color3.fromRGB(255, 150, 60),
        Sun = Color3.fromRGB(255, 220, 140),
        Ivory = Color3.fromRGB(235, 255, 248),
    },
    Animate = animateQilin,
}

PetRig.Profiles.MyceliumSprite = {
    Joints = {
        Body = "Root",
        Cap = "Body",
        ArmL = "Body",
        ArmR = "Body",
        Threads = "Body",
    },
    Attached = {},
    SeeThrough = {},
    Effects = {
        Motes = "Cap",
        Light = "Body",
        Pulse = "Cap",
        Burst = "Body",
        Sparks = { "ArmL_Puff", "ArmR_Puff" },
        Trail = "Threads_Tip",
        Blast = "SporeBloom",
        NovaLight = 4,
    },
    Colors = {
        Gold = Color3.fromRGB(90, 245, 215),
        Amber = Color3.fromRGB(70, 60, 190),
        Orange = Color3.fromRGB(150, 110, 255),
        Sun = Color3.fromRGB(200, 255, 245),
        Ivory = Color3.fromRGB(230, 240, 255),
    },
    Animate = animateSprite,
}

PetRig.Profiles.MossGolem = {
    Joints = {
        Body = "Root",
        Head = "Body",
        ArmL = "Body",
        ArmR = "Body",
        ArmL2 = "ArmL",
        ArmR2 = "ArmR",
        LegL = "Body",
        LegR = "Body",
    },
    Attached = {},
    SeeThrough = {},
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "Body_Core" },
        Blast = "Groundbreaker",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(110, 255, 140),
        Amber = Color3.fromRGB(105, 102, 94),
        Orange = Color3.fromRGB(120, 200, 70),
        Sun = Color3.fromRGB(200, 255, 190),
        Ivory = Color3.fromRGB(225, 255, 220),
    },
    Animate = animateGolem,
}

PetRig.Profiles.JadeSpiritPanda = {
    Joints = {
        Body = "Root",
        Head = "Body",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
    },
    Attached = {},
    SeeThrough = {},
    SeeThroughGlow = { ["89edbc"] = 0.3 },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "Head_Gem", "Body_Crystal" },
        Blast = "JadeLotus",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(60, 225, 130),
        Amber = Color3.fromRGB(20, 70, 45),
        Orange = Color3.fromRGB(80, 235, 205),
        Sun = Color3.fromRGB(195, 255, 220),
        Ivory = Color3.fromRGB(230, 250, 235),
    },
    Animate = animatePanda,
}

PetRig.Profiles.JadeAntlerDeer = {
    Joints = {
        Body = "Root",
        Neck = "Body",
        Head = "Neck",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        LegFL2 = "LegFL",
        LegFR2 = "LegFR",
        LegBL2 = "LegBL",
        LegBR2 = "LegBR",
    },
    Attached = {},
    SeeThrough = {},
    SeeThroughGlow = { adedce = 0.4, ["89ffd3"] = 0.2 },
    GlowColors = {
        adedce = Color3.fromRGB(40, 200, 140),
        ["89ffd3"] = Color3.fromRGB(20, 225, 160),
        f3c461 = Color3.fromRGB(255, 160, 20),
        ["61f1d4"] = Color3.fromRGB(20, 210, 170),
    },
    Effects = {
        Motes = "Head",
        Light = "Head",
        Pulse = "Head",
        Burst = "Body",
        Sparks = { "LegFL2_Hoof", "LegFR2_Hoof", "LegBL2_Hoof", "LegBR2_Hoof" },
        Trail = "Body_Tail",
        Blast = "SacredGrove",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(45, 215, 130),
        Amber = Color3.fromRGB(25, 60, 35),
        Orange = Color3.fromRGB(90, 230, 200),
        Sun = Color3.fromRGB(200, 255, 225),
        Ivory = Color3.fromRGB(240, 240, 225),
    },
    Animate = animateDeer,
}

PetRig.Profiles.DawnPhoenix = {
    Joints = {
        Body = "Root",
        Neck = "Body",
        Head = "Neck",
        WingL = "Body",
        WingR = "Body",
        WingL2 = "WingL",
        WingR2 = "WingR",
        Tail = "Body",
        LegL = "Body",
        LegR = "Body",
    },
    Attached = {},
    SeeThrough = {},
    SeeThroughGlow = { ffe195 = 0.25 },
    GlowColors = {
        ffe195 = Color3.fromRGB(255, 170, 40),
        ffedb3 = Color3.fromRGB(255, 190, 60),
        ffe595 = Color3.fromRGB(255, 185, 50),
        ffad30 = Color3.fromRGB(255, 130, 10),
        ff8927 = Color3.fromRGB(255, 90, 0),
        ffbc59 = Color3.fromRGB(255, 140, 25),
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "Tail_TipA", "Tail_TipB", "Tail_TipC" },
        Trail = { "WingL2_Tip", "WingR2_Tip" },
        Blast = "SunriseRebirth",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 190, 70),
        Amber = Color3.fromRGB(150, 30, 25),
        Orange = Color3.fromRGB(255, 120, 40),
        Sun = Color3.fromRGB(255, 235, 170),
        Ivory = Color3.fromRGB(255, 245, 225),
    },
    Animate = animatePhoenix,
}

PetRig.Profiles.RuneSphinx = {
    Joints = {
        Body = "Root",
        Head = "Body",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        Tail = "Body",
        Tail2 = "Tail",
    },
    Attached = {},
    SeeThrough = {},
    SeeThroughGlow = { ffad3f = 0.15 },
    GlowColors = {
        ffc555 = Color3.fromRGB(255, 140, 0),
        ffc461 = Color3.fromRGB(240, 120, 10),
        ffad3f = Color3.fromRGB(255, 95, 0),
        f98e27 = Color3.fromRGB(200, 55, 0),
        fff6cb = Color3.fromRGB(255, 200, 70),
    },
    Effects = {
        Motes = "Head",
        Light = "Body",
        Pulse = "Head",
        Burst = "Body",
        Sparks = { "LegFL_Paw", "LegFR_Paw", "LegBL_Paw", "LegBR_Paw" },
        Blast = "RuneSeal",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 196, 97),
        Amber = Color3.fromRGB(60, 45, 30),
        Orange = Color3.fromRGB(255, 160, 48),
        Sun = Color3.fromRGB(255, 240, 200),
        Ivory = Color3.fromRGB(255, 250, 235),
    },
    Animate = animateSphinx,
}

PetRig.NOVA_TIME = 2.6
local NOVA_BURST_AT = 0.42

function PetRig.isRigged(petId, template)
    local profile = PetRig.Profiles[petId]
    if not profile then
        return false
    end
    for name in profile.Joints do
        if template:FindFirstChild(petId .. "_Pivot_" .. name, true) then
            return true
        end
    end
    return false
end

local function prepare(part)
    part.Anchored = false
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Massless = true
end

local function weld(part0, part1)
    local constraint = Instance.new("WeldConstraint")
    constraint.Part0 = part0
    constraint.Part1 = part1
    constraint.Parent = part1
end

local function emitter(parent, properties)
    local particles = Instance.new("ParticleEmitter")
    particles.LightInfluence = 0
    particles.LightEmission = 1
    for property, value in properties do
        particles[property] = value
    end
    particles.Parent = parent
    return particles
end

local function attachmentAt(part, position, name)
    local attachment = Instance.new("Attachment")
    attachment.Name = name
    attachment.CFrame = part.CFrame:Inverse() * CFrame.new(position)
    attachment.Parent = part
    return attachment
end

local function addEffects(rig)
    local profile = rig.profile
    local effects, colors, u = profile.Effects, profile.Colors, rig.unit

    local motes = rig.parts[effects.Motes]
    if motes then
        emitter(motes, {
            Name = "Motes",
            Texture = SPARKLE,
            Rate = 6,
            Lifetime = NumberRange.new(1.6, 2.6),
            Speed = NumberRange.new(0.3, 0.8),
            SpreadAngle = Vector2.new(180, 180),
            Acceleration = Vector3.new(0, 0.6 * u, 0),
            Size = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0),
                NumberSequenceKeypoint.new(0.3, 0.13 * u),
                NumberSequenceKeypoint.new(1, 0),
            }),
            Color = ColorSequence.new(colors.Gold, colors.Orange),
            Transparency = NumberSequence.new(0.2, 1),
        })
    end

    for _, pointName in effects.Sparks or {} do
        local attachment = rig.points[pointName]
        if attachment then
            emitter(attachment, {
                Name = "Sparks",
                Texture = SPARKLE,
                Rate = 5,
                Lifetime = NumberRange.new(0.3, 0.6),
                Speed = NumberRange.new(0.6, 1.6),
                SpreadAngle = Vector2.new(60, 60),
                Size = NumberSequence.new(0.09 * u, 0),
                Color = ColorSequence.new(colors.Sun, colors.Gold),
            })
        end
    end

    local lightPart = rig.parts[effects.Light]
    if lightPart then
        local light = Instance.new("PointLight")
        light.Name = "PulseLight"
        light.Color = colors.Gold
        light.Range = 5 * u
        light.Brightness = 1.4
        light.Shadows = false
        light.Parent = lightPart
        rig.light = light
    end

    local burstPart = rig.parts[effects.Burst]
    if burstPart then
        rig.burst = emitter(attachmentAt(burstPart, burstPart.Position, "Burst"), {
            Name = "BurstParticles",
            Texture = SPARKLE,
            Enabled = false,
            Lifetime = NumberRange.new(0.6, 1.2),
            Speed = NumberRange.new(8 * u, 16 * u),
            Drag = 4,
            SpreadAngle = Vector2.new(180, 180),
            Size = NumberSequence.new(0.35 * u, 0),
            Color = ColorSequence.new(colors.Sun, colors.Orange),
        })
    end

    rig.trails = {}
    local trailPoints = if type(effects.Trail) == "table" then effects.Trail else { effects.Trail }
    for _, pointName in trailPoints do
        local tip = rig.points[pointName]
        if not tip then
            continue
        end
        local upper = Instance.new("Attachment")
        upper.Name = "TrailTop"
        upper.CFrame = tip.CFrame * CFrame.new(0, 0.25 * u, 0)
        upper.Parent = tip.Parent
        local trail = Instance.new("Trail")
        trail.Name = "FlightTrail"
        trail.Attachment0 = tip
        trail.Attachment1 = upper
        trail.Lifetime = 0.45
        trail.LightEmission = 1
        trail.LightInfluence = 0
        trail.FaceCamera = true
        trail.Color = ColorSequence.new(colors.Sun, colors.Orange)
        trail.Transparency = NumberSequence.new(0.35, 1)
        trail.Enabled = false
        trail.Parent = tip.Parent
        table.insert(rig.trails, trail)
    end
end

function PetRig.build(model, rootPart, template, petId, place, unit)
    local profile = PetRig.Profiles[petId]
    local prefix = petId .. "_"
    local rig = {
        profile = profile,
        model = model,
        rootPart = rootPart,
        unit = unit,
        parts = {},
        motors = {},
        sides = {},
        points = {},
        pointPositions = {},
        pulseGlow = {},
        trails = {},
        deltaTime = 0,
        state = { walk = 0, fly = 0, time = math.random() * 10 },
    }

    local pivots, glows = {}, {}
    for _, piece in template:GetDescendants() do
        if not piece:IsA("BasePart") or string.sub(piece.Name, 1, #prefix) ~= prefix then
            continue
        end
        local name = string.sub(piece.Name, #prefix + 1)
        local cframe, size = place(piece)
        local pivot = string.match(name, "^Pivot_(.+)$")
        local point = string.match(name, "^Point_(.+)$")
        if pivot then
            pivots[pivot] = cframe.Position
            continue
        elseif point then
            rig.pointPositions[point] = cframe.Position
            continue
        end

        local part = piece:Clone()
        for _, child in part:GetChildren() do
            if not child:IsA("SurfaceAppearance") then
                child:Destroy()
            end
        end
        part.Name = name
        part.Size = size
        part.CFrame = cframe
        local owner, hex = string.match(name, "^(.+)_Glow_(%x%x%x%x%x%x)$")
        part.Transparency = profile.SeeThrough[name]
            or (hex and profile.SeeThroughGlow and profile.SeeThroughGlow[string.lower(hex)])
            or 0
        prepare(part)
        if hex then
            part.Color = (profile.GlowColors and profile.GlowColors[string.lower(hex)]) or Color3.fromHex(hex)
            part.Material = Enum.Material.Neon
            if part:IsA("MeshPart") then
                part.TextureID = ""
            end
            table.insert(glows, { part = part, owner = owner })
        else
            part.Material = Enum.Material.SmoothPlastic
            rig.parts[name] = part
        end
        part.Parent = model
    end

    for _, glow in glows do
        if not rig.parts[glow.owner] then
            rig.parts[glow.owner] = glow.part
            glow.carrier = true
        end
    end

    local function partFor(name)
        return if name == "Root" then rootPart else rig.parts[name]
    end
    for name, parentName in profile.Joints do
        local part, parent, pivot = rig.parts[name], partFor(parentName), pivots[name]
        if part and parent and pivot then
            local motor = Instance.new("Motor6D")
            motor.Name = name
            motor.Part0 = parent
            motor.Part1 = part
            motor.C0 = parent.CFrame:Inverse() * CFrame.new(pivot)
            motor.C1 = part.CFrame:Inverse() * CFrame.new(pivot)
            motor.Parent = part
            rig.motors[name] = motor
            rig.sides[name] = if pivot.X > 0.01 then 1 elseif pivot.X < -0.01 then -1 else 0
        else
            warn(string.format("PetRig: %s is missing the part, parent or pivot for %s", petId, tostring(name)))
        end
    end
    for name, ownerName in profile.Attached do
        local part, owner = rig.parts[name], rig.parts[ownerName]
        if part and owner then
            weld(owner, part)
        end
    end
    local pulseName = profile.Effects.Pulse
    for _, glow in glows do
        local owner = rig.parts[glow.owner]
        if not glow.carrier then
            weld(owner, glow.part)
        end
        if glow.owner == pulseName then
            table.insert(rig.pulseGlow, { part = glow.part, color = glow.part.Color })
        end
    end
    for name, position in rig.pointPositions do
        local ownerName, label = string.match(name, "^([^_]+)_(.+)$")
        local owner = ownerName and rig.parts[ownerName]
        if owner then
            rig.points[name] = attachmentAt(owner, position, label)
        end
    end

    local controller = Instance.new("AnimationController")
    controller.Parent = model
    Instance.new("Animator").Parent = controller

    addEffects(rig)
    return rig
end

local Blasts = {}

function Blasts.Sunburst(rig, fx)
    local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon

    local ringInfo = TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
    for index = 1, 20 do
        local angle = index / 20 * 2 * math.pi
        local direction = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local start = CFrame.lookAt(origin + direction * 0.8 * u, origin + direction * 2 * u)
        local segment = neon(Vector3.new(0.9 * u, 0.12 * u, 0.25 * u), start, colors.Gold)
        TweenService:Create(segment, ringInfo, {
            CFrame = start + direction * 9 * u,
            Size = Vector3.new(2.2 * u, 0.05 * u, 0.1 * u),
            Transparency = 1,
        }):Play()
    end

    local rayInfo = TweenInfo.new(0.7, Enum.EasingStyle.Quint, Enum.EasingDirection.Out)
    for index = 1, 10 do
        local angle = index / 10 * 2 * math.pi
        local direction = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0.55, math.sin(angle))).Unit
        local base = CFrame.lookAt(origin, origin + direction)
        local ray = neon(Vector3.new(0.12 * u, 0.12 * u, 0.4 * u), base * CFrame.new(0, 0, -0.4 * u), colors.Sun)
        TweenService:Create(ray, rayInfo, {
            Size = Vector3.new(0.04 * u, 0.04 * u, 5 * u),
            CFrame = base * CFrame.new(0, 0, -2.8 * u),
            Transparency = 1,
        }):Play()
    end

    local flash = neon(Vector3.one * 0.6 * u, CFrame.new(origin), colors.Ivory)
    flash.Shape = Enum.PartType.Ball
    TweenService:Create(flash, ringInfo, { Size = Vector3.one * 5 * u, Transparency = 1 }):Play()
    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 16 * u
    light.Brightness = 6
    light.Parent = flash
    TweenService:Create(light, ringInfo, { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(45)
    end
end

function Blasts.Eruption(rig, fx)
    local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon

    for index = 1, 14 do
        local angle = index / 14 * 2 * math.pi + math.random() * 0.4
        local out = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local reach = (1.6 + math.random() * 1.8) * u
        local height = (1.2 + math.random() * 1.4) * u
        local size = (0.12 + math.random() * 0.12) * u
        local drop = neon(Vector3.one * size, CFrame.new(origin), if index % 3 == 0 then colors.Sun else colors.Orange)
        drop.Shape = Enum.PartType.Ball
        local peak = origin + out * reach * 0.55 + Vector3.new(0, height, 0)
        local land = origin + out * reach - Vector3.new(0, 1.2 * u, 0)
        local rise = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
        local fall = TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
        local up = TweenService:Create(drop, rise, { CFrame = CFrame.new(peak) })
        up.Completed:Once(function()
            TweenService:Create(drop, fall, { CFrame = CFrame.new(land), Size = Vector3.one * size * 0.4, Transparency = 1, Color = colors.Amber }):Play()
        end)
        up:Play()
    end

    local rippleInfo = TweenInfo.new(0.7, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
    for index = 1, 12 do
        local angle = index / 12 * 2 * math.pi
        local out = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local base = origin - Vector3.new(0, 0.6 * u, 0)
        local start = CFrame.lookAt(base + out * 0.4 * u, base + out * 2 * u)
        local slab = neon(Vector3.new(0.5 * u, 0.06 * u, 0.5 * u), start, colors.Amber)
        TweenService:Create(slab, rippleInfo, { CFrame = start + out * 4 * u, Size = Vector3.new(1.4 * u, 0.03 * u, 0.3 * u), Transparency = 1 }):Play()
    end

    local glow = neon(Vector3.one * 0.4 * u, CFrame.new(origin), colors.Orange)
    glow.Shape = Enum.PartType.Ball
    glow.Transparency = 0.4
    local throb = TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.Out)
    TweenService:Create(glow, throb, { Size = Vector3.one * 2.2 * u, Transparency = 1 }):Play()
    local light = Instance.new("PointLight")
    light.Color = colors.Amber
    light.Range = 12 * u
    light.Brightness = 5
    light.Parent = glow
    TweenService:Create(light, throb, { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(30)
    end
end

function Blasts.SoulLantern(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon

    for index = 1, 16 do
        local angle = index / 16 * 2 * math.pi
        local radius = (0.5 + (index % 3) * 0.25) * u
        local wisp = neon(Vector3.one * 0.14 * u, CFrame.new(origin), if index % 2 == 0 then colors.Sun else colors.Gold)
        wisp.Shape = Enum.PartType.Ball
        local function at(turn, height, r)
            local a = angle + turn
            return CFrame.new(origin + Vector3.new(math.cos(a) * r, height, math.sin(a) * r))
        end
        local first = TweenService:Create(wisp, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.Out),
            { CFrame = at(2.2, 1.2 * u, radius) })
        first.Completed:Once(function()
            TweenService:Create(wisp, TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.In), {
                CFrame = at(4.4, 3.4 * u, radius * 1.6),
                Size = Vector3.one * 0.04 * u,
                Transparency = 1,
            }):Play()
        end)
        first:Play()
    end

    local pillar = neon(Vector3.new(0.2 * u, 0.5 * u, 0.5 * u), CFrame.new(origin) * CFrame.Angles(0, 0, math.pi / 2), colors.Ivory)
    pillar.Shape = Enum.PartType.Cylinder
    pillar.Transparency = 0.3
    TweenService:Create(pillar, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(7 * u, 0.15 * u, 0.15 * u),
        CFrame = CFrame.new(origin + Vector3.new(0, 3.5 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2),
        Transparency = 1,
    }):Play()

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 14 * u
    light.Brightness = 5
    light.Parent = pillar
    TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(30)
    end
end

function Blasts.HellBreath(rig, fx)
    local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
    for name, mouth in rig.points do
        local tag = string.match(name, "^Head(%a)_Mouth$")
        local head = tag and rig.parts["Head" .. tag]
        if not head then
            continue
        end
        local from = mouth.WorldPosition
        local direction = (from - head.Position)
        direction = Vector3.new(direction.X, direction.Y * 0.3, direction.Z).Unit
        for index = 1, 9 do
            task.delay(index * 0.045, function()
                local reach = (1.4 + index * 0.28) * u
                local ball = neon(Vector3.one * 0.14 * u, CFrame.new(from), if index % 3 == 0 then colors.Sun else colors.Gold)
                ball.Shape = Enum.PartType.Ball
                local spread = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 0.35 * u
                TweenService:Create(ball, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                    CFrame = CFrame.new(from + direction * reach + spread),
                    Size = Vector3.one * (0.45 + index * 0.04) * u,
                    Transparency = 1,
                    Color = colors.Amber,
                }):Play()
            end)
        end
        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 8 * u
        light.Brightness = 4
        light.Parent = head
        TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
        Debris:AddItem(light, 1)
    end
    if rig.burst then
        rig.burst:Emit(25)
    end
end

function Blasts.AuspiciousClouds(rig, fx)
    local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon

    for index = 1, 14 do
        local angle = index / 14 * 2 * math.pi
        local out = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local size = (0.35 + (index % 3) * 0.12) * u
        local puff = neon(Vector3.one * size, CFrame.new(origin + out * 0.5 * u), if index % 2 == 0 then colors.Gold else colors.Amber)
        puff.Shape = Enum.PartType.Ball
        puff.Transparency = 0.25
        local swirl = facing:VectorToWorldSpace(Vector3.new(math.cos(angle + 0.9), 0, math.sin(angle + 0.9)))
        TweenService:Create(puff, TweenInfo.new(1.1, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(origin + swirl * 4.2 * u + Vector3.new(0, (0.6 + (index % 4) * 0.35) * u, 0)),
            Size = Vector3.one * size * 2.4,
            Transparency = 1,
        }):Play()
    end

    for index = 1, 9 do
        local angle = index / 9 * 2 * math.pi + 0.3
        local out = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local base = origin + out * 1.2 * u - Vector3.new(0, 0.8 * u, 0)
        local flame = neon(Vector3.new(0.12 * u, 0.5 * u, 0.12 * u), CFrame.new(base), if index % 3 == 0 then colors.Sun else colors.Orange)
        TweenService:Create(flame, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(base + Vector3.new(0, 3.2 * u, 0) + out * 0.8 * u) * CFrame.Angles(0, angle * 2, 0.4),
            Size = Vector3.new(0.04 * u, 1.6 * u, 0.04 * u),
            Transparency = 1,
        }):Play()
    end

    local ring = neon(Vector3.new(0.1 * u, 1 * u, 1 * u), CFrame.new(origin - Vector3.new(0, 0.9 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), colors.Gold)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.35
    TweenService:Create(ring, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(0.04 * u, 9 * u, 9 * u),
        Transparency = 1,
    }):Play()

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 14 * u
    light.Brightness = 5
    light.Parent = ring
    TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(35)
    end
end

function Blasts.SporeBloom(rig, fx)
    local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon

    for index = 1, 22 do
        local dir = Vector3.new(math.random() - 0.5, math.random() * 0.8 - 0.1, math.random() - 0.5).Unit
        local size = (0.08 + math.random() * 0.12) * u
        local spore = neon(Vector3.one * size, CFrame.new(origin), if index % 3 == 0 then colors.Orange else colors.Gold)
        spore.Shape = Enum.PartType.Ball
        spore.Transparency = 0.1
        TweenService:Create(spore, TweenInfo.new(1.1 + math.random() * 0.4, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(origin + dir * (2 + math.random() * 2.5) * u + Vector3.new(0, 1 * u, 0)),
            Size = Vector3.one * size * 0.4,
            Transparency = 1,
        }):Play()
    end

    local ground = origin - Vector3.new(0, 1.6 * u, 0)
    for index = 1, 9 do
        local angle = index / 9 * 2 * math.pi + math.random() * 0.3
        local spot = ground + facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle))) * (1.6 + math.random() * 1.2) * u
        local height = (0.35 + math.random() * 0.35) * u
        local stem = neon(Vector3.new(0.08 * u, 0.02, 0.08 * u), CFrame.new(spot), colors.Ivory)
        stem.Shape = Enum.PartType.Cylinder
        stem.CFrame = CFrame.new(spot) * CFrame.Angles(0, 0, math.pi / 2)
        stem.Size = Vector3.new(0.02, 0.08 * u, 0.08 * u)
        local cap = neon(Vector3.new(0.02, 0.02, 0.02), CFrame.new(spot), if index % 2 == 0 then colors.Gold else colors.Orange)
        cap.Shape = Enum.PartType.Ball
        local grow = TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
        TweenService:Create(stem, grow, {
            Size = Vector3.new(height, 0.08 * u, 0.08 * u),
            CFrame = CFrame.new(spot + Vector3.new(0, height / 2, 0)) * CFrame.Angles(0, 0, math.pi / 2),
        }):Play()
        local pop = TweenService:Create(cap, grow, {
            Size = Vector3.new(0.4, 0.18, 0.4) * u,
            CFrame = CFrame.new(spot + Vector3.new(0, height, 0)),
        })
        pop.Completed:Once(function()
            local fade = TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
            TweenService:Create(cap, fade, { Transparency = 1 }):Play()
            TweenService:Create(stem, fade, { Transparency = 1 }):Play()
        end)
        pop:Play()
    end

    local glow = neon(Vector3.one * 0.5 * u, CFrame.new(origin), colors.Sun)
    glow.Shape = Enum.PartType.Ball
    glow.Transparency = 0.4
    TweenService:Create(glow, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 3.5 * u, Transparency = 1 }):Play()
    if rig.burst then
        rig.burst:Emit(30)
    end
end

function Blasts.Groundbreaker(rig, fx)
    local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon
    local ground = origin - Vector3.new(0, 1.3 * u, 0)

    local ring = neon(Vector3.new(0.1 * u, 1.2 * u, 1.2 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Gold)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.25
    TweenService:Create(ring, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(0.04 * u, 9 * u, 9 * u),
        Transparency = 1,
    }):Play()

    for index = 1, 10 do
        local angle = index / 10 * 2 * math.pi + math.random() * 0.3
        local out = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
        local base = ground + out * (1.2 + math.random() * 1.6) * u
        local size = Vector3.new(0.45 + math.random() * 0.25, 1 + math.random() * 0.9, 0.5 + math.random() * 0.3) * u
        local spike = Instance.new("WedgePart")
        spike.Anchored = true
        spike.CanCollide = false
        spike.CanQuery = false
        spike.CanTouch = false
        spike.CastShadow = false
        spike.Material = Enum.Material.Slate
        spike.Color = colors.Amber
        spike.Size = size
        spike.CFrame = CFrame.new(base - Vector3.new(0, size.Y, 0)) * CFrame.Angles(0, angle + math.pi / 2, 0)
            * CFrame.Angles(-0.35 - math.random() * 0.25, 0, math.random() * 0.4 - 0.2)
        spike.Parent = ring.Parent
        local up = TweenService:Create(spike, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
            CFrame = spike.CFrame + Vector3.new(0, size.Y * 0.9, 0),
        })
        up.Completed:Once(function()
            TweenService:Create(spike, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                CFrame = spike.CFrame - Vector3.new(0, size.Y, 0),
                Transparency = 1,
            }):Play()
        end)
        up:Play()

        local leaf = neon(Vector3.new(0.18, 0.04, 0.3) * u, CFrame.new(base), if index % 2 == 0 then colors.Gold else colors.Orange)
        TweenService:Create(leaf, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(base + out * 1.5 * u + Vector3.new(0, 2.5 * u, 0)) * CFrame.Angles(math.random() * 6, math.random() * 6, 0),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 9 * u
    light.Brightness = 1.6
    light.Parent = ring
    TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(25)
    end
end

function Blasts.JadeLotus(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local ground = origin - Vector3.new(0, 1.2 * u, 0)

    local function oval(size, cframe, color)
        local part = neon(size, cframe, color)
        local mesh = Instance.new("SpecialMesh")
        mesh.MeshType = Enum.MeshType.Sphere
        mesh.Parent = part
        return part
    end

    local ring = neon(Vector3.new(0.1 * u, 1.5 * u, 1.5 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.3
    TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(0.04 * u, 8 * u, 8 * u),
        Transparency = 1,
    }):Play()

    for layer, spec in { { count = 8, radius = 0.9, length = 1.6, tilt = 1.15, color = colors.Gold }, { count = 6, radius = 0.45, length = 1.2, tilt = 0.6, color = colors.Sun } } do
        for index = 1, spec.count do
            local angle = (index + layer * 0.5) / spec.count * 2 * math.pi
            local base = CFrame.new(ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * spec.radius * u) * CFrame.Angles(0, angle, 0)
            local size = Vector3.new(0.55, spec.length, 0.12) * u
            local petal = oval(size * 0.4, base * CFrame.new(0, size.Y * 0.2, 0), spec.color)
            petal.Transparency = 0.15
            TweenService:Create(petal, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                Size = size,
                CFrame = base * CFrame.Angles(spec.tilt, 0, 0) * CFrame.new(0, size.Y / 2, 0),
            }):Play()
            TweenService:Create(petal, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.6), {
                Transparency = 1,
            }):Play()
        end
    end

    for index = 1, 7 do
        local angle = index / 7 * 2 * math.pi
        local out = Vector3.new(math.sin(angle), 0, math.cos(angle))
        local shard = Instance.new("WedgePart")
        shard.Anchored = true
        shard.CanCollide = false
        shard.CanQuery = false
        shard.CanTouch = false
        shard.CastShadow = false
        shard.Material = Enum.Material.Glass
        shard.Transparency = 0.2
        shard.Color = colors.Gold
        shard.Size = Vector3.new(0.18, 0.55, 0.3) * u
        shard.CFrame = CFrame.new(ground + out * 0.6 * u) * CFrame.Angles(0, angle, 0)
        shard.Parent = ring.Parent
        local swirl = angle + 0.9
        TweenService:Create(shard, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(ground + Vector3.new(math.sin(swirl), 0, math.cos(swirl)) * 2.6 * u + Vector3.new(0, 2.2 * u, 0))
                * CFrame.Angles(math.random() * 6, swirl, math.random() * 6),
            Transparency = 1,
        }):Play()
    end

    for index = 1, 10 do
        local angle = math.random() * 2 * math.pi
        local start = ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * (0.4 + math.random()) * u + Vector3.new(0, 0.3 * u, 0)
        local leaf = oval(Vector3.new(0.12, 0.03, 0.36) * u, CFrame.new(start) * CFrame.Angles(0, angle, 0), if index % 3 == 0 then colors.Sun else colors.Gold)
        TweenService:Create(leaf, TweenInfo.new(1.3, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(start + Vector3.new(math.sin(angle), 0, math.cos(angle)) * 1.4 * u + Vector3.new(0, (1.8 + math.random()) * u, 0))
                * CFrame.Angles(math.random() * 3, angle + 2, math.random() * 3),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 10 * u
    light.Brightness = 1.8
    light.Parent = ring
    TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(25)
    end
end

function Blasts.SacredGrove(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local ground = origin - Vector3.new(0, 1.3 * u, 0)

    local ring = neon(Vector3.new(0.1 * u, 1.4 * u, 1.4 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Gold)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.3
    TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(0.04 * u, 9 * u, 9 * u),
        Transparency = 1,
    }):Play()

    local function grow(base, direction, length, width, color, delay)
        local axis = CFrame.lookAt(base, base + direction) * CFrame.Angles(-math.pi / 2, 0, 0)
        local limb = neon(Vector3.new(0.05 * u, width, width), axis * CFrame.Angles(0, 0, math.pi / 2), color)
        limb.Shape = Enum.PartType.Cylinder
        limb.Transparency = 0.1
        local stretch = TweenService:Create(limb, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, delay), {
            Size = Vector3.new(length, width, width),
            CFrame = axis * CFrame.new(0, length / 2, 0) * CFrame.Angles(0, 0, math.pi / 2),
        })
        stretch:Play()
        TweenService:Create(limb, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, delay + 0.6), {
            Transparency = 1,
        }):Play()
        return base + direction.Unit * length
    end

    for index = 1, 8 do
        local angle = index / 8 * 2 * math.pi
        local out = Vector3.new(math.sin(angle), 0, math.cos(angle))
        local base = ground + out * 2.1 * u
        local height = (1.1 + 0.3 * math.random()) * u
        local top = grow(base, Vector3.new(0, 1, 0) + out * 0.25, height, 0.12 * u, colors.Gold, 0.05 * index)
        local side = Vector3.new(-out.Z, 0, out.X)
        grow(top - Vector3.new(0, 0.35 * u, 0), Vector3.new(0, 1, 0) + side * 0.8, 0.55 * u, 0.06 * u, colors.Orange, 0.05 * index + 0.2)
        grow(top - Vector3.new(0, 0.2 * u, 0), Vector3.new(0, 1, 0) - side * 0.7, 0.45 * u, 0.06 * u, colors.Sun, 0.05 * index + 0.25)
    end

    for index = 1, 9 do
        local angle = math.random() * 2 * math.pi
        local start = ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * (0.6 + math.random() * 1.2) * u
        local shard = Instance.new("WedgePart")
        shard.Anchored = true
        shard.CanCollide = false
        shard.CanQuery = false
        shard.CanTouch = false
        shard.CastShadow = false
        shard.Material = Enum.Material.Glass
        shard.Transparency = 0.2
        shard.Color = if index % 2 == 0 then colors.Gold else colors.Orange
        shard.Size = Vector3.new(0.12, 0.35, 0.2) * u
        shard.CFrame = CFrame.new(start) * CFrame.Angles(0, angle, 0)
        shard.Parent = ring.Parent
        TweenService:Create(shard, TweenInfo.new(1.25, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(start + Vector3.new(0, (2 + math.random() * 1.2) * u, 0)) * CFrame.Angles(math.random() * 6, angle + 2.5, math.random() * 6),
            Transparency = 1,
        }):Play()
    end

    for index = 1, 10 do
        local angle = math.random() * 2 * math.pi
        local start = ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * (0.8 + math.random() * 1.5) * u + Vector3.new(0, 2.6 * u, 0)
        local leaf = neon(Vector3.new(0.1, 0.02, 0.28) * u, CFrame.new(start) * CFrame.Angles(0, angle, 0), if index % 3 == 0 then colors.Sun else colors.Gold)
        local mesh = Instance.new("SpecialMesh")
        mesh.MeshType = Enum.MeshType.Sphere
        mesh.Parent = leaf
        TweenService:Create(leaf, TweenInfo.new(1.3, Enum.EasingStyle.Sine, Enum.EasingDirection.In), {
            CFrame = CFrame.new(start - Vector3.new(0, 2.2 * u, 0) + Vector3.new(math.sin(angle), 0, math.cos(angle)) * 0.8 * u)
                * CFrame.Angles(math.random() * 3, angle + 3, math.random() * 3),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 10 * u
    light.Brightness = 1.8
    light.Parent = ring
    TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(30)
    end
end

function Blasts.SunriseRebirth(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local centre = origin + Vector3.new(0, 0.5 * u, 0)
    local ground = origin - Vector3.new(0, 1.1 * u, 0)

    local sun = neon(Vector3.one * 0.3 * u, CFrame.new(centre), colors.Sun)
    sun.Shape = Enum.PartType.Ball
    sun.Transparency = 0.35
    TweenService:Create(sun, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.one * 3.4 * u,
        Transparency = 1,
    }):Play()

    for index = 1, 14 do
        local direction = Vector3.new(math.random() - 0.5, math.random() * 0.8 - 0.15, math.random() - 0.5).Unit
        local ray = neon(Vector3.new(0.06 * u, 0.06 * u, 0.2 * u), CFrame.lookAt(centre, centre + direction), if index % 2 == 0 then colors.Gold else colors.Sun)
        ray.Transparency = 0.15
        local length = (2.2 + math.random() * 1.2) * u
        TweenService:Create(ray, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.03 * u, 0.03 * u, length),
            CFrame = CFrame.lookAt(centre, centre + direction) * CFrame.new(0, 0, -length / 2),
            Transparency = 1,
        }):Play()
    end

    local ring = neon(Vector3.new(0.1 * u, 1.2 * u, 1.2 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.3
    TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(0.04 * u, 8 * u, 8 * u),
        Transparency = 1,
    }):Play()

    for index = 1, 14 do
        local angle = index / 14 * 2 * math.pi
        local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
        local start = centre + out * 0.4 * u
        local plume = neon(Vector3.new(0.08, 0.02, 0.32) * u, CFrame.lookAt(start, start + out), if index % 3 == 0 then colors.Sun elseif index % 3 == 1 then colors.Gold else colors.Orange)
        local mesh = Instance.new("SpecialMesh")
        mesh.MeshType = Enum.MeshType.Sphere
        mesh.Parent = plume
        local swirl = angle + 1.2
        local finish = centre + Vector3.new(math.cos(swirl), 0, math.sin(swirl)) * 2.2 * u + Vector3.new(0, (1 + math.random()) * u, 0)
        TweenService:Create(plume, TweenInfo.new(1.25, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
            CFrame = CFrame.lookAt(finish, finish + Vector3.new(math.cos(swirl + 1.5), 0.3, math.sin(swirl + 1.5))),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 12 * u
    light.Brightness = 2.2
    light.Parent = sun
    TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(35)
    end
end

local RUNE_GLYPHS = {
    { { { 0, -1 }, { 0, 1 } }, { { 0, 0.2 }, { 0.6, 0.8 } }, { { 0, -0.4 }, { -0.6, 0.1 } } },
    { { { -0.5, -1 }, { -0.5, 1 } }, { { 0.5, -1 }, { 0.5, 1 } }, { { -0.5, 0.6 }, { 0.5, -0.2 } } },
    { { { 0, -1 }, { 0, 1 } }, { { -0.6, 0.4 }, { 0, 1 } }, { { 0, 1 }, { 0.6, 0.4 } } },
    { { { 0, -1 }, { 0, 0.3 } }, { { -0.6, 0.3 }, { 0.6, 0.3 } }, { { -0.6, 0.3 }, { 0, 1 } }, { { 0, 1 }, { 0.6, 0.3 } } },
    { { { -0.6, -1 }, { 0, 1 } }, { { 0, 1 }, { 0.6, -1 } }, { { -0.3, -0.1 }, { 0.3, -0.1 } } },
    { { { 0, -1 }, { 0, 1 } }, { { -0.55, -0.55 }, { 0.55, 0.55 } }, { { -0.55, 0.55 }, { 0.55, -0.55 } } },
    { { { -0.5, 1 }, { 0.5, 1 } }, { { 0, 1 }, { 0, -1 } }, { { -0.5, -1 }, { 0.5, -1 } } },
}

function Blasts.RuneSeal(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local ground = origin - Vector3.new(0, 0.95 * u, 0)

    for index, radius in { 2.2, 1.6 } do
        local ring = neon(Vector3.new(0.05 * u, 0.4 * u, 0.4 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), if index == 1 then colors.Gold else colors.Orange)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.2
        TweenService:Create(ring, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.03 * u, radius * 2 * u, radius * 2 * u),
        }):Play()
        TweenService:Create(ring, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.6), { Transparency = 1 }):Play()
    end

    for index = 1, 8 do
        local angle = index / 8 * 2 * math.pi
        local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
        local centre = ground + out * 1.9 * u + Vector3.new(0, 0.05 * u, 0)
        local frame = CFrame.lookAt(centre, centre - out) * CFrame.Angles(-math.pi / 2, 0, 0)
        local size = 0.28 * u
        for _, stroke in RUNE_GLYPHS[(index - 1) % #RUNE_GLYPHS + 1] do
            for step = 1, #stroke - 1 do
                local a, b = stroke[step], stroke[step + 1]
                local from = frame * Vector3.new(a[1] * size, 0, -a[2] * size)
                local to = frame * Vector3.new(b[1] * size, 0, -b[2] * size)
                local mid = (from + to) / 2
                local bar = neon(Vector3.new(0.05 * u, 0.03 * u, (to - from).Magnitude + 0.05 * u), CFrame.lookAt(mid, to), colors.Gold)
                local rise = Vector3.new(0, (0.7 + 0.1 * (index % 3)) * u, 0)
                TweenService:Create(bar, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.05 * index), {
                    CFrame = CFrame.new(rise) * CFrame.lookAt(mid, to),
                    Transparency = 1,
                }):Play()
            end
        end
    end

    for index = 1, 4 do
        local angle = index / 4 * 2 * math.pi + math.pi / 4
        local base = ground + Vector3.new(math.cos(angle), 0, math.sin(angle)) * 2.2 * u
        local pillar = neon(Vector3.new(0.05 * u, 0.12 * u, 0.12 * u), CFrame.new(base) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
        pillar.Shape = Enum.PartType.Cylinder
        pillar.Transparency = 0.2
        TweenService:Create(pillar, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(3 * u, 0.12 * u, 0.12 * u),
            CFrame = CFrame.new(base + Vector3.new(0, 1.5 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2),
        }):Play()
        TweenService:Create(pillar, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.7), { Transparency = 1 }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 11 * u
    light.Brightness = 2
    light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(origin), colors.Gold)
    TweenService:Create(light, TweenInfo.new(1.2), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(25)
    end
end

function Blasts.SolarCorona(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local facing = fx.facing
    local centre = origin + facing:VectorToWorldSpace(Vector3.new(0, 1.6 * u, 0.6 * u))
    local ground = origin - Vector3.new(0, 1 * u, 0)

    local core = neon(Vector3.one * 0.25 * u, CFrame.new(centre), colors.Sun)
    core.Shape = Enum.PartType.Ball
    core.Transparency = 0.2
    TweenService:Create(core, TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.one * 1.3 * u }):Play()
    TweenService:Create(core, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.55), {
        Size = Vector3.one * 2.4 * u,
        Transparency = 1,
    }):Play()

    local plane = CFrame.lookAt(centre, centre + facing.LookVector)
    for index = 1, 12 do
        local angle = index / 12 * 2 * math.pi
        local out = plane:VectorToWorldSpace(Vector3.new(math.cos(angle), math.sin(angle), 0))
        local length = (if index % 2 == 0 then 1.9 else 1.3) * u
        local ray = neon(Vector3.new(0.14 * u, 0.04 * u, 0.1 * u), CFrame.lookAt(centre, centre + out), if index % 2 == 0 then colors.Gold else colors.Orange)
        ray.Transparency = 0.1
        TweenService:Create(ray, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.12), {
            Size = Vector3.new(0.12 * u, 0.03 * u, length),
            CFrame = CFrame.lookAt(centre, centre + out) * CFrame.new(0, 0, -(0.7 * u + length / 2)),
        }):Play()
        TweenService:Create(ray, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.7), { Transparency = 1 }):Play()
    end

    local ring = neon(Vector3.new(0.08 * u, 1.2 * u, 1.2 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.25
    TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.4), {
        Size = Vector3.new(0.03 * u, 9 * u, 9 * u),
        Transparency = 1,
    }):Play()

    for index = 1, 10 do
        local angle = math.random() * 2 * math.pi
        local start = centre + plane:VectorToWorldSpace(Vector3.new(math.cos(angle), math.sin(angle), 0)) * 0.5 * u
        local flake = Instance.new("WedgePart")
        flake.Anchored = true
        flake.CanCollide = false
        flake.CanQuery = false
        flake.CanTouch = false
        flake.CastShadow = false
        flake.Material = Enum.Material.Glass
        flake.Transparency = 0.15
        flake.Color = if index % 2 == 0 then colors.Gold else colors.Orange
        flake.Size = Vector3.new(0.05, 0.22, 0.18) * u
        flake.CFrame = CFrame.new(start) * CFrame.Angles(math.random() * 6, math.random() * 6, 0)
        flake.Parent = ring.Parent
        TweenService:Create(flake, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(start + (start - centre).Unit * 2.4 * u - Vector3.new(0, 0.8 * u, 0)) * CFrame.Angles(math.random() * 6, math.random() * 6, 0),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 14 * u
    light.Brightness = 2.4
    light.Parent = core
    TweenService:Create(light, TweenInfo.new(1.2), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(35)
    end
end

local function burst(rig)
    local profile = rig.profile
    local folder = Instance.new("Folder")
    folder.Name = "PetSpecial"
    folder.Parent = rig.model.Parent or workspace

    local fx = {
        origin = (rig.parts[profile.Effects.Burst] or rig.rootPart).Position,
        facing = rig.rootPart.CFrame - rig.rootPart.Position,
        neon = function(size, cframe, color)
            local part = Instance.new("Part")
            part.Anchored = true
            part.CanCollide = false
            part.CanTouch = false
            part.CanQuery = false
            part.CastShadow = false
            part.Material = Enum.Material.Neon
            part.Color = color
            part.Size = size
            part.CFrame = cframe
            part.Parent = folder
            return part
        end,
    }
    Blasts[profile.Effects.Blast or "Sunburst"](rig, fx)
    Debris:AddItem(folder, 1.4)
end

function PetRig.nova(rig)
    if rig.nova == nil then
        rig.nova = { start = rig.state.time, fired = false }
    end
end

function PetRig.update(rig, deltaTime, state)
    local s = rig.state
    s.time += deltaTime
    rig.deltaTime = deltaTime
    local blend = math.min(1, deltaTime * 5)
    local walkTarget = if state.flying then 0 else math.clamp(state.speed / (4 * rig.unit), 0, 1)
    s.walk += (walkTarget - s.walk) * blend
    s.fly += ((if state.flying then 1 else 0) - s.fly) * blend

    local nova = 0
    if rig.nova then
        local progress = (s.time - rig.nova.start) / PetRig.NOVA_TIME
        nova = smoothstep(0, 0.3, progress) * (1 - smoothstep(0.75, 1, progress))
        if not rig.nova.fired and progress >= NOVA_BURST_AT then
            rig.nova.fired = true
            burst(rig)
        end
        if progress >= 1 then
            rig.nova = nil
        end
    end

    rig.profile.Animate(rig, s, s.walk, s.fly, nova)

    local pulse = 0.5 + 0.5 * math.sin(s.time * 2.2)
    if rig.light then
        rig.light.Brightness = 1.1 + 0.8 * pulse + (rig.profile.Effects.NovaLight or 9) * nova
    end
    for _, glow in rig.pulseGlow do
        glow.part.Color = glow.color:Lerp(Color3.new(1, 1, 1), 0.2 * pulse + 0.7 * nova)
    end

    for _, trail in rig.trails do
        trail.Enabled = s.fly > 0.5
    end
end

return PetRig

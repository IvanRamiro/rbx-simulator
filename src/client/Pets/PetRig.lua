local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
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
        local side = rig.sides[name] or 0
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

local function animateCub(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (1.4 + 6.5 * pace)
    local stride = s.stride
    local breathe = math.sin(t * 1.6)
    local tilt = math.sin(t * 0.45) ^ 3 * (1 - pace)
    local wind = math.sin(math.min(nova * 1.6, 1) * math.pi / 2)
    s.erupt = if rig.nova then (s.erupt or 0) + rig.deltaTime else 0
    local hop = smoothstep(0.55, 0.85, s.erupt) * (1 - smoothstep(0.95, 1.25, s.erupt))

    pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.05 * math.abs(math.sin(stride)) * pace - 0.06 * wind + 0.3 * hop) * u, 0)
        * CFrame.Angles(0.04 * breathe - 0.1 * pace + 0.25 * wind - 0.15 * hop, 0, 0.07 * math.sin(stride) * pace))
    pose(m.Head, CFrame.Angles(0.06 * math.sin(t * 0.9) - 0.15 * wind + 0.3 * hop, 0.25 * math.sin(t * 0.37) * (1 - pace), 0.3 * tilt))

    for _, side in { "L", "R" } do
        local phase = if side == "L" then 0 else math.pi
        local arm = m["Arm" .. side]
        local leg = m["Leg" .. side]
        local slam = (if side == "L" then 1.4 else 1.1) * wind
        if arm then
            pose(arm, CFrame.Angles(0.45 * math.sin(stride + phase) * pace - slam + 0.6 * hop, 0, 0))
        end
        if leg then
            pose(leg, CFrame.Angles(0.4 * math.sin(stride + phase + math.pi) * pace - 0.3 * hop, 0, 0))
        end
    end

    pose(m.Tail, CFrame.Angles(0.08 * math.sin(t * 2.2) + 0.25 * hop, 0.3 * math.sin(t * 1.7 + 0.5) + 0.2 * math.sin(stride) * pace, 0))
end

local function animateSkyDragon(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    s.stride = (s.stride or 0) + rig.deltaTime * (1.3 + 6 * moving)
    s.flap = (s.flap or 0) + rig.deltaTime * (1.3 + 4.5 * fly)
    local stride, beat = s.stride, math.sin(s.flap)
    local breathe = math.sin(t * 1.1)
    local gust = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)

    pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.04 * math.abs(math.sin(stride)) * moving + 0.08 * beat * fly + 0.2 * gust) * u, 0)
        * CFrame.Angles(0.03 * breathe + 0.3 * fly - 0.2 * gust, 0, 0.05 * math.sin(stride) * moving + 0.06 * math.sin(s.flap * 0.5) * fly))
    local gaze = 0.35 * math.sin(t * 0.33) * (1 - fly) * (1 - gust)
    pose(m.Neck, CFrame.Angles(0.05 * math.sin(t * 0.8) - 0.3 * fly + 0.15 * gust, gaze * 0.5, 0.04 * math.sin(t * 0.6)))
    pose(m.Head, CFrame.Angles(0.06 * math.sin(t * 1.0 + 1) - 0.15 * fly + 0.25 * gust, gaze * 0.6, 0.06 * math.sin(t * 0.5)))

    for _, side in { "L", "R" } do
        local sign = rig.sides["Wing" .. side] or 0
        local stroke = (0.75 * beat - 0.1) * fly
        local spread = 0.4 * gust
        pose(m["Wing" .. side], CFrame.Angles(0, sign * (0.06 * breathe - 0.3 * gust), sign * (0.05 * breathe + stroke + spread)))
        pose(m["Wing" .. side .. "2"], CFrame.Angles(0, sign * 0.2 * math.max(0, -beat) * fly,
            sign * (0.05 * math.sin(t * 1.1 + 0.6) + 0.45 * math.max(0, beat) * fly + 0.3 * gust)))
        local leg = m["Leg" .. side]
        if leg then
            local swing = 0.4 * math.sin(stride + (if side == "L" then 0 else math.pi)) * moving
            pose(leg, CFrame.Angles(swing - 0.8 * fly + 0.2 * gust, 0, 0))
        end
        local arm = m["Arm" .. side]
        if arm then
            local fidget = 0.08 * math.sin(t * 1.4 + (if side == "L" then 0 else 1.3))
            pose(arm, CFrame.Angles(fidget - 0.2 * math.sin(stride + (if side == "L" then math.pi else 0)) * moving + 0.7 * fly - 0.5 * gust, 0, 0))
        end
    end

    local sway = math.sin(t * 0.9)
    pose(m.Tail, CFrame.Angles(0.06 * math.sin(t * 0.7) + 0.2 * fly, 0.25 * sway, 0))
    pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 0.7 - 0.7) + 0.15 * fly, 0.4 * math.sin(t * 0.9 - 0.9), 0.1 * math.sin(t * 1.3)))
end

local function animateCrane(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    s.stride = (s.stride or 0) + rig.deltaTime * (1.1 + 4.2 * moving)
    s.flap = (s.flap or 0) + rig.deltaTime * (1 + 4 * fly)
    local stride, beat = s.stride, math.sin(s.flap)
    local breathe = math.sin(t * 0.8)
    local ascend = math.sin(math.min(nova * 1.2, 1) * math.pi / 2)
    local walk = moving * (1 - fly)
    local bob = math.sin(stride * 2)
    local tilt = math.sin(t * 0.37) ^ 3 * (1 - moving) * (1 - ascend)

    pose(m.Body, CFrame.new(0, (0.015 * breathe + 0.025 * math.abs(math.sin(stride)) * walk + 0.05 * beat * fly + 0.12 * ascend) * u, 0)
        * CFrame.Angles(0.02 * breathe + 0.04 * walk + 0.25 * fly - 0.15 * ascend, 0, 0.03 * math.sin(stride) * walk))
    local gaze = 0.4 * math.sin(t * 0.21) * (1 - moving) * (1 - ascend)
    pose(m.Neck, CFrame.Angles(0.04 * math.sin(t * 0.5) + 0.12 * bob * walk + 0.35 * fly - 0.35 * ascend, gaze * 0.45, 0.03 * math.sin(t * 0.4)))
    pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.7 + 1) - 0.1 * bob * walk - 0.2 * fly - 0.25 * ascend, gaze * 0.55, 0.22 * tilt))

    for _, side in { "L", "R" } do
        local sign = rig.sides["Wing" .. side] or 0
        local settle = 0.03 * math.sin(t * 0.9 + (if side == "L" then 0 else 0.5))
        local open = 0.8 * fly + 0.9 * ascend
        local lift = (0.7 * beat + 0.15) * fly + 0.55 * ascend
        pose(m["Wing" .. side], CFrame.Angles(0, -sign * (open + 0.03 * breathe), sign * (settle + lift)))
        local leg = m["Leg" .. side]
        if leg then
            local swing = 0.42 * math.sin(stride + (if side == "L" then 0 else math.pi)) * walk
            pose(leg, CFrame.Angles(swing + 1.1 * fly - 0.08 * ascend, 0, 0))
        end
    end

    pose(m.Tail, CFrame.Angles(0.04 * math.sin(t * 0.6) - 0.15 * fly + 0.12 * ascend, 0.08 * math.sin(t * 0.45), 0.04 * math.sin(t * 0.9)))
end


-- The Cloud Sheep (skinned): always half asleep, its hooves paddling at the air. It breathes with its whole fleece, its lobes on their own bones; its head sinks as it nods off and comes up with a
-- start; it yawns. +X swings a limb's far end forward.
local SHEEP_LEADS = { FL = 0, BR = 0.4, FR = math.pi, BL = math.pi + 0.4 }
local SHEEP_LID_HINGE = { L = Vector3.new(0.7476, 0.1035, -0.6561), R = Vector3.new(0.7476, -0.1035, 0.6561) }
local SHEEP_WOOL = { WoolTop = Vector3.new(0, 1, 0), WoolBack = Vector3.new(0, 0.1, 1), WoolChest = Vector3.new(0, 0.3, -1), WoolL = Vector3.new(-1, 0.1, 0), WoolR = Vector3.new(1, 0.1, 0) }

local function animateCloudSheep(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > 90 then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: it tucks its legs and draws in a huge breath, swelling, then lets it all go in one long sigh
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local inhale = smoothstep(0, 0.38, progress) * (1 - smoothstep(0.42, 0.56, progress))
    local sigh = smoothstep(0.41, 0.47, progress) * (1 - smoothstep(0.66, 0.95, progress))

    -- nodding off: its head sinks over seconds, its eyes close, and then it starts awake
    s.nextNod = s.nextNod or t + 4 + math.random() * 5
    local nod, startle = 0, 0
    if t >= s.nextNod then
        local a = t - s.nextNod
        if a > 4 then
            s.nextNod = t + 7 + math.random() * 8
        elseif pace < 0.25 and nova == 0 then
            nod = smoothstep(0, 3.1, a) * (1 - smoothstep(3.1, 3.28, a))
            startle = smoothstep(3.08, 3.2, a) * (1 - smoothstep(3.2, 4, a))
        else
            s.nextNod = t + 3
        end
    end
    s.nextYawn = s.nextYawn or t + 10 + math.random() * 8
    local yawn = 0
    if t >= s.nextYawn then
        local a = (t - s.nextYawn) / 2.6
        if a >= 1 then
            s.nextYawn = t + 13 + math.random() * 12
        elseif nod == 0 and pace < 0.4 and nova == 0 then
            yawn = smoothstep(0, 0.34, a) * (1 - smoothstep(0.66, 1, a))
        end
    end

    -- its breath, in the whole fleece: slow, and the lobes never quite together
    local breath = math.sin(t * 1.15)
    local index = 0
    for name, out in SHEEP_WOOL do
        index += 1
        local amount = 0.011 * (breath + 0.3 * math.sin(t * 0.7 + index * 1.7)) + 0.012 * yawn + 0.09 * inhale - 0.03 * sigh
        local back = Vector3.new(0, 0, 0.022 * pace * (if name == "WoolBack" then 1.5 else 0.6))
        local at = (out * amount + back) * u
        pose(m[name], CFrame.new(at.X, at.Y, at.Z))
    end
    pose(m.WoolCap, CFrame.new(0, (0.006 * breath + 0.03 * inhale) * u, 0))

    local hover = 0.015 * math.sin(t * 0.95) + 0.02 * fly + 0.2 * inhale + 0.08 * sigh
    pose(m.Body, CFrame.new(0, hover * u, 0) * CFrame.Angles(0.02 * math.sin(t * 0.95 - 0.8) - 0.09 * moving - 0.16 * fly + 0.14 * inhale - 0.1 * sigh, 0.03 * math.sin(t * 0.31), 0.03 * math.sin(t * 0.53)))

    -- the head hangs low; it sinks to sleep; it looks slowly about
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 3 + math.random() * 5
        s.gazeTo = (math.random() - 0.5) * 0.6
    end
    s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * (1 - nod) * (1 - nova) - (s.gaze or 0)) * math.min(1, dt * 1.2)
    pose(m.Head, CFrame.new(0, 0, (0.02 * moving) * u) * CFrame.Angles(0.012 * math.sin(t * 1.15 - 0.6) - 0.48 * nod + 0.2 * startle + 0.26 * yawn + 0.1 * moving + 0.2 * inhale - 0.04 * sigh, s.gaze, 0.1 * nod))

    -- half asleep: the lids rest low, and close as it nods off
    s.nextBlink = s.nextBlink or t + 2
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.34
        if a >= 1 then
            s.nextBlink = t + 2.5 + math.random() * 4
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local shut = math.max(blink, nod, yawn, sigh * 0.9, inhale * 0.7) * (1 - startle)
    local wide = math.rad(14) * startle
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(SHEEP_LID_HINGE[side], -math.rad(26) * shut + wide))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(SHEEP_LID_HINGE[side], math.rad(14) * shut))
        pose(m["Eye" .. side], CFrame.Angles(0, s.gaze * 0.5, 0))
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 1.9
        local flick = math.max(0, math.sin(t * 0.8 + offset)) ^ 18
        pose(m["Ear" .. side], CFrame.Angles(0.06 * math.sin(t * 1.15 + offset) - 0.34 * nod + 0.34 * startle + 0.3 * flick - 0.34 * pace, 0, sign * 0.06 * math.sin(t * 0.7 + offset)))
    end
    local open = math.max(yawn, sigh * 0.85)
    pose(m.Smile, CFrame.new(0, 0, 0.03 * open * u))
    pose(m.Mouth, CFrame.new(0, 0.006 * open * u, -0.03 * open * u))

    -- it paddles, slowly, even asleep: swimming on the air
    s.stride = (s.stride or 0) + dt * (1.5 - 0.8 * nod + 7 * moving + 3 * fly)
    local tuck = math.max(inhale, sigh * 0.7, fly * 0.55)
    local reach = (0.2 + 0.32 * pace) * (1 - tuck)
    for key, lead in SHEEP_LEADS do
        local phase = s.stride + lead
        local a, lift = math.sin(phase), math.max(0, math.cos(phase))
        if string.sub(key, 1, 1) == "F" then
            pose(m["Leg" .. key .. "1"], CFrame.Angles(reach * a + 1.0 * tuck, 0, 0))
            pose(m["Leg" .. key .. "2"], CFrame.Angles(-(0.26 + 0.7 * pace) * lift * (1 - tuck) - 1.6 * tuck, 0, 0))
            pose(m["Hoof" .. key], CFrame.Angles(-0.34 * lift - 0.6 * tuck, 0, 0))
        else
            pose(m["Leg" .. key .. "1"], CFrame.Angles(reach * a - 0.95 * tuck, 0, 0))
            pose(m["Leg" .. key .. "2"], CFrame.Angles((0.24 + 0.6 * pace) * lift * (1 - tuck) + 1.5 * tuck, 0, 0))
            pose(m["Hoof" .. key], CFrame.Angles(-0.3 * lift - 0.45 * tuck, 0, 0))
        end
    end

    pose(m.Tail, CFrame.Angles(0.08 * math.sin(t * 1.15 + 0.5) - 0.2 * pace, 0.16 * math.sin(t * 1.9) + 0.3 * math.max(0, math.sin(t * 0.37)) ^ 10 * math.sin(t * 11), 0))
end

-- The Jade Wyrm Turtle (skinned): half wyrm, half mountain, and in no hurry. Everything it does is slow and carries weight: it treads one foot at a time and the whole crag rocks over it, its long neck
-- wanders on its own, the plum and the pine sway after the shell does. Now and then it turns its neck right round to look at its garden. It stands on the ground rather than hovering (Body drops to it).
local TURTLE_LEADS = { FL = 0, BR = 0.35, FR = math.pi, BL = math.pi + 0.35 }
local TURTLE_LID_HINGE = { L = Vector3.new(0.539, 0.0867, -0.8379), R = Vector3.new(0.539, -0.0867, 0.8379) }
local TURTLE_BLINK_UPPER, TURTLE_BLINK_LOWER = math.rad(38), math.rad(16)
local TURTLE_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local TURTLE_SOLE = 0.96 -- metres from the middle of its box down to the soles of its feet
local TURTLE_PADS = { PadA = Vector3.new(-0.5, 0.2, -0.8), PadB = Vector3.new(0.6, 0.2, -0.3), PadC = Vector3.new(0, 1, 0.2) } -- which way each mass of blossom swells

local turtleRay = RaycastParams.new()
turtleRay.RespectCanCollide = true

local function dropToGround(rig, s, t, u, fly, sole)
    s.nextGround = s.nextGround or 0
    if t >= s.nextGround then
        s.nextGround = t + 0.15
        local from = rig.rootPart.Position
        local hit = workspace:Raycast(from, Vector3.new(0, -8 * u, 0), turtleRay)
        local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
        if not onCharacter then -- (a player walking under it: keep what it had)
            s.dropTo = if hit then math.clamp(from.Y - sole * u - hit.Position.Y, -0.3 * u, 2.6 * u) else 0
        end
    end
    local target = (s.dropTo or 0) * (1 - fly)
    s.drop = (s.drop or target) + (target - (s.drop or target)) * math.min(1, rig.deltaTime * 4)
    return s.drop
end

local function animateJadeWyrmTurtle(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > TURTLE_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, TURTLE_SOLE)

    -- the special: one forefoot rises, slowly, the whole mountain leaning off it; it comes down; the mountain rings; and the garden has grown
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local raise = smoothstep(0, 0.37, progress) * (1 - smoothstep(0.385, 0.425, progress))
    local plant = smoothstep(0.40, 0.43, progress) * (1 - smoothstep(0.46, 0.9, progress))
    local ring = plant * math.sin(math.max(0, progress - 0.42) * 62)
    local grown = smoothstep(0.43, 0.6, progress) * (1 - smoothstep(0.8, 1, progress))

    -- it looks back at its garden, the long way round
    s.nextGarden = s.nextGarden or t + 9 + math.random() * 8
    local garden = 0
    if t >= s.nextGarden then
        local a = (t - s.nextGarden) / 5.2
        if a >= 1 then
            s.nextGarden = t + 15 + math.random() * 14
            s.gardenSide = if math.random() < 0.5 then 1 else -1
        elseif pace < 0.2 and nova == 0 then
            garden = smoothstep(0, 0.34, a) * (1 - smoothstep(0.66, 1, a))
        else
            s.nextGarden = t + 4
        end
    end
    garden *= s.gardenSide or 1
    -- a slow chew over nothing
    s.nextChew = s.nextChew or t + 5 + math.random() * 8
    local chew = 0
    if t >= s.nextChew then
        local a = (t - s.nextChew) / 2.4
        if a >= 1 then
            s.nextChew = t + 9 + math.random() * 12
        elseif pace < 0.4 and nova == 0 then
            chew = math.abs(math.sin(a * math.pi * 3)) * math.sin(a * math.pi)
        end
    end

    -- the tread: one foot at a time. A foot rises out and forward, is set down, and the body rolls over it
    s.stride = (s.stride or 0) + dt * (3.6 * moving)
    s.swim = (s.swim or 0) + dt * 1.7 * fly
    local stride, stroke = s.stride, math.sin(s.swim)
    local breath = math.sin(t * 0.85)
    for key, lead in TURTLE_LEADS do
        local phase = stride + lead
        local a, lift = math.sin(phase), moving * math.max(0, math.cos(phase)) ^ 1.4
        local out = if string.sub(key, 2, 2) == "L" then -1 else 1 -- a turn about Z that swings this foot out and up
        local front = string.sub(key, 1, 1) == "F"
        local swingX = moving * 0.3 * a + 0.012 * math.sin(t * 0.6 + lead)
        local outZ = 0.26 * lift
        local bendZ = -0.44 * lift
        local footX = -swingX * 0.9 - 0.14 * lift
        -- on the air it rows, as sea turtles do: long slow strokes from the front, the hind feet trailing
        if front then
            swingX += fly * (0.06 + 0.5 * stroke)
            outZ += fly * (0.34 + 0.12 * stroke)
            bendZ += fly * 0.26
            footX += fly * (0.16 * stroke - 0.62)
        else
            swingX += fly * (-0.52 + 0.14 * stroke)
            outZ += fly * 0.2
            bendZ += fly * 0.12
            footX += fly * -0.5
        end
        if key == "FR" then
            swingX += 0.14 * raise
            outZ += 0.62 * raise
            bendZ -= 0.96 * raise
            footX += 0.32 * raise + 0.04 * raise * math.sin(t * 9)
        end
        pose(m["Leg" .. key .. "1"], CFrame.Angles(swingX, 0, out * outZ))
        pose(m["Leg" .. key .. "2"], CFrame.Angles(0, 0, out * bendZ))
        pose(m["Foot" .. key], CFrame.Angles(footX, 0, 0))
    end

    -- the body rolls over the foot that bears it, and a mountain doesn't bob quickly. It leans into a turn only a little
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.05, -0.1, 0.1) - (s.bank or 0)) * math.min(1, dt * 2)
    local rollOver = moving * 0.036 * math.sin(stride + 0.5)
    local fall = moving * 0.014 * math.cos(2 * stride + 0.6)
    pose(m.Body, CFrame.new(0, (-drop / u + 0.006 * breath + fall + 0.13 * raise - 0.025 * plant + 0.05 * fly + 0.014 * math.sin(s.swim + 0.8) * fly) * u, 0)
        * CFrame.Angles(0.004 * breath + 0.1 * raise - 0.05 * plant + 0.09 * fly + 0.03 * stroke * fly, 0.012 * math.sin(t * 0.27) + moving * 0.018 * math.sin(stride), rollOver + 0.1 * raise + s.bank))
    pose(m.Shell, CFrame.new(0, (0.004 * breath + 0.012 * ring) * u, 0))

    -- the neck: its gaze wanders and the neck follows late; at each joint a little less of the body's roll
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2.6 + math.random() * 4.5
        s.gazeTo = (math.random() - 0.5) * 0.9
        s.gazeUp = (math.random() - 0.5) * 0.14
    end
    local calm = (1 - pace * 0.7) * (1 - nova) * (1 - math.abs(garden))
    s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * calm - (s.gaze or 0)) * math.min(1, dt * 1.1)
    s.tip = (s.tip or 0) + ((s.gazeUp or 0) * calm - (s.tip or 0)) * math.min(1, dt * 0.9)
    local sway = moving * 0.05 * math.sin(stride - 0.6)
    local lift = 0.2 * raise - 0.1 * plant
    local reach = fly * 0.28 + moving * 0.1
    pose(m.Neck1, CFrame.Angles(0.012 * math.sin(t * 0.85 - 0.5) + lift * 0.8 - reach * 0.6, s.gaze * 0.14 + 0.28 * garden - sway, -rollOver * 0.5 - 0.06 * raise))
    pose(m.Neck2, CFrame.Angles(0.01 * math.sin(t * 0.85 - 0.9) + lift - reach * 0.7 + 0.02 * ring, s.gaze * 0.2 + 0.42 * garden - sway * 0.7, -0.04 * raise))
    pose(m.Neck3, CFrame.Angles(0.01 * math.sin(t * 0.85 - 1.3) + lift * 0.7 - reach * 0.2 + s.tip * 0.5 - 0.03 * ring + 0.1 * math.abs(garden), s.gaze * 0.26 + 0.45 * garden - sway * 0.3, 0))
    local lookUp = math.abs(garden)
    pose(m.Neck4, CFrame.Angles(s.tip * 0.5 + reach * 0.5 - lift * 0.3, s.gaze * 0.3 + 0.31 * garden, 0))
    pose(m.Head, CFrame.Angles(0.008 * math.sin(t * 0.85 - 1.8) + s.tip + reach * 0.6 - lift * 0.55 - 0.04 * ring + 0.24 * lookUp, s.gaze * 0.4 + 0.28 * garden, 0.05 * math.sin(t * 0.31) * calm))
    pose(m.Jaw, CFrame.Angles(-(0.14 * chew + 0.14 * raise + 0.24 * plant + 0.02 * math.max(0, breath)), 0, 0))

    -- old eyes: a slow blink, closing as the foot comes down, and they look about ahead of the head
    s.nextBlink = s.nextBlink or t + 2.5
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.62
        if a >= 1 then
            s.nextBlink = t + 3.2 + math.random() * 5
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local shut = math.max(blink, 0.45 * math.abs(garden), plant, 0.55 * chew)
    for _, side in { "L", "R" } do
        pose(m["Eye" .. side], CFrame.Angles(s.tip * 0.5, s.gaze * 0.7 + 0.4 * garden, 0))
        pose(m["LidU" .. side], CFrame.fromAxisAngle(TURTLE_LID_HINGE[side], -TURTLE_BLINK_UPPER * shut))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(TURTLE_LID_HINGE[side], TURTLE_BLINK_LOWER * shut))
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 1.7
        pose(m["Frill" .. side], CFrame.Angles(0.04 * math.sin(t * 1.1 + offset), sign * (0.07 * math.sin(t * 0.8 + offset) - 0.14 * pace + 0.1 * raise), 0))
    end

    -- the tail: a long lazy wave that starts at the body; on the air it trails straight
    local waveSpeed = 0.9 + 1.6 * moving + 0.8 * fly
    for k = 1, 6 do
        local f = k / 6
        pose(m["Tail" .. k], CFrame.Angles(0.012 * math.sin(t * 0.7 - k * 0.5) - 0.03 * fly + 0.03 * raise - 0.05 * ring * (1 - f),
            (0.035 + 0.04 * f) * (1 + 0.7 * moving) * math.sin(t * waveSpeed - k * 0.62), 0))
    end
    pose(m.TailTip, CFrame.Angles(0.1 * math.sin(t * 0.8) - 0.1 * fly, 0.12 * math.sin(t * 1.2 - 4), 0))

    -- the garden: a breeze of its own, and every roll of the shell reaching the trees a moment late
    s.treeLag = (s.treeLag or 0) + ((rollOver + 0.1 * raise - 0.06 * plant) - (s.treeLag or 0)) * math.min(1, dt * 2.4)
    local gust = 0.5 + 0.5 * math.sin(t * 0.37)
    local windX, windZ = 0.012 * gust * math.sin(t * 1.3), 0.012 * gust * math.sin(t * 1.05 + 1)
    local shake = 0.05 * ring + 0.1 * fly * math.sin(t * 2.1) * 0.2
    pose(m.Plum1, CFrame.Angles(windX + 0.3 * shake + 0.03 * fly, 0, s.treeLag * 0.4 + windZ))
    pose(m.Plum2, CFrame.Angles(windX * 1.4 + 0.5 * shake, 0.01 * math.sin(t * 0.7), s.treeLag * 0.7 + windZ * 1.4))
    local padIndex = 0
    for name, out in TURTLE_PADS do
        padIndex += 1
        local at = out * (0.008 * math.sin(t * 1.2 + padIndex * 1.9) + 0.055 * grown + 0.03 * ring) * u
        pose(m[name], CFrame.new(at) * CFrame.Angles(0.02 * math.sin(t * 0.9 + padIndex), 0, 0.02 * math.sin(t * 0.8 + padIndex * 2.3)))
    end
    pose(m.Pine1, CFrame.Angles(windX * 0.7 + 0.25 * shake, 0, s.treeLag * 0.45))
    for index, name in { "PineA", "PineB", "PineC" } do
        pose(m[name], CFrame.Angles(0.016 * math.sin(t * 1.05 + index * 1.4) + 0.3 * shake, 0, 0.022 * gust * math.sin(t * 0.95 + index * 2.1)))
    end

    -- petals, always a few, drifting down off the plum: more when it walks, a flurry when it stamps (Blasts.BetweenSteps)
    if not s.petals then
        s.petals = {}
        for name in TURTLE_PADS do
            local bone = rig.points[name]
            if bone then
                local petals = Instance.new("ParticleEmitter")
                petals.Name = "Petals"
                petals.Texture = "rbxassetid://87701005821132"
                petals.Rate = 0.5
                petals.Lifetime = NumberRange.new(2.6, 4)
                petals.Speed = NumberRange.new(0.15 * rig.unit, 0.5 * rig.unit)
                petals.SpreadAngle = Vector2.new(180, 180)
                petals.Acceleration = Vector3.new(0.12 * rig.unit, -0.42 * rig.unit, 0)
                petals.Drag = 0.8
                petals.Rotation = NumberRange.new(0, 360)
                petals.RotSpeed = NumberRange.new(-110, 110)
                petals.Size = NumberSequence.new(0.036 * rig.unit)
                petals.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.08, 0), NumberSequenceKeypoint.new(0.8, 0), NumberSequenceKeypoint.new(1, 1) })
                petals.LightEmission = 0
                petals.LightInfluence = 0.9
                petals.Parent = bone
                s.petals[name] = petals
            end
        end
    end
    for _, petals in s.petals do
        petals.Rate = 0.4 + 0.5 * moving
    end
end

-- The Nebula Owl (skinned; the head is its own piece, so it can turn right round under the ruff): it hovers without a sound and already knows what you are about to do. Its wings row slowly, each joint later than the last. Its head
-- doesn't drift: it snaps to a new place and holds still, as an owl's does, and now and then turns all the way round to look behind it, one brow raised. It blinks one eye at a time. Up is a turn about Z: left wing negative, right positive.
local OWL_LID_HINGE = { L = Vector3.new(0.9734, -0.1044, -0.204), R = Vector3.new(0.9734, 0.1044, 0.204) }
local OWL_BLINK_UPPER, OWL_BLINK_LOWER = math.rad(64), math.rad(22)
local OWL_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local OWL_STAR_AHEAD = Vector3.new(0, -0.05, -0.9) -- metres from the middle of its box: where the new star is born, before its breast
local OWL_GATHER_RADIUS = 0.95

-- Gas drawn in from all round a point, the first part of its special. Blasts.StarsNotYetBorn stops it when the star lights.
local function owlGather(rig, s)
    local metre = rig.meters
    local at = rig.rootPart.CFrame:PointToWorldSpace(OWL_STAR_AHEAD * metre)
    local holder = Instance.new("Part")
    holder.Name = "OwlGather"
    holder.Anchored = true
    holder.CanCollide = false
    holder.CanTouch = false
    holder.CanQuery = false
    holder.CastShadow = false
    holder.Transparency = 1
    holder.Size = Vector3.one * OWL_GATHER_RADIUS * 2 * metre
    holder.CFrame = CFrame.new(at)
    local gas = Instance.new("ParticleEmitter")
    gas.Texture = "rbxassetid://16867371255"
    gas.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    gas.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    gas.Shape = Enum.ParticleEmitterShape.Sphere
    gas.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    gas.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
    gas.Rate = 30
    gas.Lifetime = NumberRange.new(0.55, 0.7)
    gas.Speed = NumberRange.new(OWL_GATHER_RADIUS * metre / 0.62)
    gas.Rotation = NumberRange.new(0, 360)
    gas.RotSpeed = NumberRange.new(-70, 70)
    gas.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.34 * metre), NumberSequenceKeypoint.new(1, 0.16 * metre) })
    gas.Color = ColorSequence.new(Color3.fromRGB(96, 52, 225), Color3.fromRGB(235, 90, 200))
    gas.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.42), NumberSequenceKeypoint.new(0.85, 0.15), NumberSequenceKeypoint.new(1, 0.9) })
    gas.LightEmission = 0.75
    gas.LightInfluence = 0
    gas.Parent = holder
    -- what the gas is falling into: a small star, growing, so the eye is already there when it lights
    local seed = Instance.new("ParticleEmitter")
    seed.Texture = "rbxassetid://95572555201628"
    seed.Rate = 0
    seed.Lifetime = NumberRange.new(PetRig.NOVA_TIME * PetRig.NOVA_BURST)
    seed.Speed = NumberRange.new(0)
    seed.Rotation = NumberRange.new(0, 360)
    seed.RotSpeed = NumberRange.new(25, 25)
    seed.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(1, 0.72 * metre) })
    seed.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(1, 0) })
    seed.LightEmission = 1
    seed.LightInfluence = 0
    seed.Parent = Instance.new("Attachment", holder)
    seed:Emit(1)
    holder.Parent = rig.model.Parent or workspace
    Debris:AddItem(holder, PetRig.NOVA_TIME * PetRig.NOVA_BURST + 1)
    s.gather, s.starAt = gas, at
end

local function animateNebulaOwl(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > OWL_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: wings lift and spread, slowly, as gas gathers before its breast; the star lights; one great silent downstroke; and it goes back to looking unimpressed, having known all along
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local open = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.41, 0.47, progress))
    local stroke = smoothstep(0.41, 0.46, progress) * (1 - smoothstep(0.47, 0.76, progress))
    local awe = smoothstep(0.1, 0.38, progress) * (1 - smoothstep(0.5, 0.72, progress))
    if rig.nova and not rig.nova.gathering and progress < PetRig.NOVA_BURST then
        rig.nova.gathering = true
        owlGather(rig, s)
    end

    -- now and then it turns its head right round to look behind it, in no hurry to turn back
    s.nextBehind = s.nextBehind or t + 6 + math.random() * 8
    local behind = 0
    if t >= s.nextBehind then
        local a = (t - s.nextBehind) / 3.1
        if a >= 1 then
            s.nextBehind = t + 12 + math.random() * 14
            s.behindSide = if math.random() < 0.5 then 1 else -1
        elseif pace < 0.25 and nova == 0 then
            behind = smoothstep(0, 0.2, a) * (1 - smoothstep(0.78, 1, a))
        else
            s.nextBehind = t + 3
        end
    end

    -- the head doesn't drift: it snaps to a new place and holds still
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 1.4 + math.random() * 3.2
        s.gazeTo = (math.random() - 0.5) * 1.5
        s.nodTo = (math.random() - 0.5) * 0.22
        s.tiltTo = if math.random() < 0.25 then (math.random() - 0.5) * 0.8 else 0
    end
    local calm = (1 - pace * 0.8) * (1 - nova)
    local yawTo = (s.gazeTo or 0) * calm * (1 - behind) + 2.65 * behind * (s.behindSide or 1)
    local snap = math.min(1, dt * (if behind > 0 then 5 else 11))
    s.yaw = (s.yaw or 0) + (yawTo - (s.yaw or 0)) * snap
    s.nod = (s.nod or 0) + (((s.nodTo or 0) * calm + 0.12 * awe) - (s.nod or 0)) * snap
    s.tilt = (s.tilt or 0) + ((s.tiltTo or 0) * calm * (1 - behind) - (s.tilt or 0)) * snap

    -- the wings row, each joint later than the last; flying, it beats and then glides. It makes no sound and it doesn't hurry
    s.beat = (s.beat or 0) + dt * (2 + 4.4 * moving + 1.6 * fly)
    local glide = 0.45 + 0.55 * math.max(0, math.sin(t * 0.7))
    local amp = 0.13 + 0.4 * moving + 0.22 * fly * glide
    local beat = s.beat
    local base = 0.02 - 0.04 * moving + 0.06 * fly
    for _, side in { "L", "R" } do
        local up = if side == "L" then -1 else 1
        pose(m["Wing" .. side .. "1"], CFrame.Angles(0, up * (0.07 * math.cos(beat) * (amp / 0.3) - 0.12 * open), up * (base + amp * math.sin(beat) + 0.34 * open - 0.42 * stroke)))
        pose(m["Wing" .. side .. "2"], CFrame.Angles(0, 0, up * (-0.06 + 0.6 * amp * math.sin(beat - 0.7) + 0.14 * open - 0.1 * stroke)))
        pose(m["Wing" .. side .. "3"], CFrame.Angles(0, 0, up * (-0.04 + 0.7 * amp * math.sin(beat - 1.3) + 0.1 * open - 0.34 * stroke)))
        pose(m["WingP" .. side], CFrame.Angles(0, 0, up * (0.6 * amp * math.sin(beat - 1.9) + 0.2 * open - 0.36 * stroke)))
    end

    -- the body rides each stroke a moment late, and leans into going forward; the head stays level, as an owl's does
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.14, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
    local pitch = -0.22 * moving - 0.12 * fly + 0.12 * open
    local rise = 0.1 * amp * math.sin(beat - 0.9) + 0.08 * open + 0.1 * stroke
    pose(m.Body, CFrame.new(0, rise * u, 0) * CFrame.Angles(pitch + 0.015 * math.sin(beat - 1.2), 0, s.bank))
    local breath = math.sin(t * 1.1)
    pose(m.Chest, CFrame.new(0, 0.004 * breath * u, -0.006 * breath * u))
    pose(m.Head, CFrame.new(0, 0.012 * math.sin(beat - 1.5) * u, 0) * CFrame.fromEulerAnglesYXZ(-pitch * 0.85 + s.nod, s.yaw + s.bank * 0.6, s.tilt - s.bank * 0.7))

    -- its lids rest low. It blinks slowly and, more often than not, one eye at a time
    s.nextBlink = s.nextBlink or t + 2
    if t >= s.nextBlink then
        s.nextBlink = t + 2.2 + math.random() * 4.5
        s.blinkAt = t
        local r = math.random()
        s.blinkWhich = if r < 0.35 then "L" elseif r < 0.7 then "R" else "both"
    end
    local shut = 0
    if s.blinkAt and t - s.blinkAt < 0.34 then
        shut = 1 - math.abs(2 * (t - s.blinkAt) / 0.34 - 1)
    end
    s.nextBrow = s.nextBrow or t + 4
    if t >= s.nextBrow then
        s.nextBrow = t + 5 + math.random() * 7
        s.browAt, s.browSide = t, if math.random() < 0.5 then "L" else "R"
    end
    local cock = if s.browAt then smoothstep(0, 0.12, t - s.browAt) * (1 - smoothstep(1.1, 1.5, t - s.browAt)) else 0
    for _, side in { "L", "R" } do
        local up = if side == "L" then -1 else 1
        local mine = if s.blinkWhich == side or s.blinkWhich == "both" then shut else 0
        local widen = math.rad(14) * math.max(awe, behind * 0.5)
        pose(m["LidU" .. side], CFrame.fromAxisAngle(OWL_LID_HINGE[side], -OWL_BLINK_UPPER * mine + widen))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(OWL_LID_HINGE[side], OWL_BLINK_LOWER * mine))
        pose(m["Eye" .. side], CFrame.Angles(s.nod * 0.25, s.yaw * 0.08 * (1 - behind), 0))
        local raised = math.max(awe * 0.8, if s.browSide == side then cock else 0, behind * (if (s.behindSide or 1) == up then 1 else 0.2))
        pose(m["Brow" .. side], CFrame.new(0, 0.014 * raised * u, 0) * CFrame.Angles(0, 0, up * 0.2 * raised))
        -- tufts lie back at speed and prick up at anything
        local offset = if side == "L" then 0 else 1.9
        local flick = math.max(0, math.sin(t * 0.7 + offset)) ^ 16
        pose(m["Tuft" .. side], CFrame.Angles(0.05 * math.sin(t * 0.9 + offset) + 0.5 * moving + 0.26 * fly - 0.12 * awe - 0.14 * flick, 0, up * (0.04 * math.sin(t * 0.6 + offset) + 0.12 * flick)))
        -- legs trail behind it in flight, talons drawn up; at rest they hang, opening a little at the top of the special
        pose(m["Leg" .. side], CFrame.Angles(0.03 * math.sin(t * 0.8 + offset) - 0.5 * pace + 0.2 * open, 0, 0))
        pose(m["Foot" .. side], CFrame.Angles(0.05 * math.sin(t * 1.1 + offset) - 0.6 * pace + 0.28 * open, 0, 0))
    end
    pose(m.BeakLow, CFrame.Angles(-(0.3 * stroke + 0.14 * cock * (if s.browSide == "L" then 1 else 0)), 0, 0))

    -- the tail steers and fans
    local fan = 0.04 + 0.1 * open + 0.1 * fly + 0.05 * math.abs(s.bank) * 3
    pose(m.Tail, CFrame.Angles(-pitch * 0.5 + 0.04 * math.sin(beat - 2.2) - 0.1 * moving, s.bank * 0.5, s.bank * 0.4))
    pose(m.TailL, CFrame.Angles(0, -fan, 0))
    pose(m.TailR, CFrame.Angles(0, fan, 0))

    -- the new stars in its wings breathe, each its own way; a little gas always leaks from the wingtips, more as it moves
    for index, name in { "StarsL", "StarsR" } do
        local part = rig.parts[name]
        if part then
            local base2 = rig.profile.GlowColors["d6b4ff"]
            part.Color = base2:Lerp(Color3.new(1, 1, 1), 0.28 * math.max(0, math.sin(t * 1.9 + index * 2.3)) ^ 3 + 0.5 * stroke)
        end
    end
    if not s.wisps then
        s.wisps = {}
        for _, name in { "WingPL", "WingPR" } do
            local bone = rig.points[name]
            if bone then
                local gas = Instance.new("ParticleEmitter")
                gas.Name = "Gas"
                gas.Texture = "rbxassetid://16172858603"
                gas.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
                gas.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
                gas.Rate = 0.8
                gas.Lifetime = NumberRange.new(1.5, 2.3)
                gas.Speed = NumberRange.new(0.1 * rig.unit, 0.3 * rig.unit)
                gas.SpreadAngle = Vector2.new(180, 180)
                gas.Drag = 0.8
                gas.Rotation = NumberRange.new(0, 360)
                gas.RotSpeed = NumberRange.new(-14, 14)
                gas.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * rig.unit), NumberSequenceKeypoint.new(1, 0.42 * rig.unit) })
                gas.Color = ColorSequence.new(Color3.fromRGB(150, 96, 240), Color3.fromRGB(220, 110, 200))
                gas.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.62), NumberSequenceKeypoint.new(1, 1) })
                gas.LightEmission = 0.35
                gas.LightInfluence = 0.5
                gas.Parent = bone
                table.insert(s.wisps, gas)
            end
        end
    end
    for _, gas in s.wisps do
        gas.Rate = 0.8 + 2.2 * pace
    end
end

-- The Cosmic Jellyfish (skinned; its glass is its own mesh): it has no eyes and no thoughts, and yet its bell leans gently toward you wherever you stand. It swims as a real one does: the bell closes quickly, it rises, it opens slowly and sinks
-- a little, and everything below it follows late. The nebula in the bell turns slowly on its own bone, faster at each beat. A rim section's axis is its tangent: a positive turn draws the margin in.
local JELLY_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local JELLY_RIM_AXIS, JELLY_ARMS = {}, { "A0", "A1", "A2", "A3" }
for k = 0, 7 do
    local angle = -math.pi / 2 + math.rad(22.5 + 45 * k)
    JELLY_RIM_AXIS[k] = Vector3.new(math.sin(angle), 0, math.cos(angle))
end
local JELLY_TENTS = {}
for name, degrees in { FL = -45, L = 0, BL = 45, BR = 135, R = 180, FR = -135 } do
    local angle = math.rad(degrees)
    JELLY_TENTS[name] = { axis = Vector3.new(math.sin(angle), 0, math.cos(angle)), offset = degrees * 0.031 }
end
local JELLY_CHAIN = { a = 0.5, b = 1.0, c = 1.2 }

local function jellyBones()
    local bones = { "Body", "Apex", "Nebula" }
    for k = 0, 7 do
        table.insert(bones, "Rim" .. k)
    end
    for _, arm in JELLY_ARMS do
        for _, tag in { "a", "b", "c" } do
            table.insert(bones, arm .. tag)
        end
    end
    for name in JELLY_TENTS do
        for _, tag in { "a", "b", "c" } do
            table.insert(bones, "T" .. name .. tag)
        end
    end
    return bones
end

local function animateCosmicJellyfish(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > JELLY_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: the bell opens wide and slow as the nebula spins up; it closes once, hard; a ring of gas rolls off it (Blasts.RollingNebula)
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local open = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.385, 0.425, progress))
    local snap = smoothstep(0.4, 0.44, progress) * (1 - smoothstep(0.47, 0.88, progress))

    -- the beat: closes in a fifth of its time, opens slowly over half. Held still while it does its special
    s.phase = (s.phase or math.random()) + dt * (0.42 + 0.5 * moving + 0.45 * fly) * (1 - 0.9 * nova)
    local p = s.phase % 1
    local close = smoothstep(0, 0.2, p) * (1 - smoothstep(0.2, 0.72, p))
    local heave = smoothstep(0, 0.3, p) - smoothstep(0.3, 1, p)
    s.late = (s.late or 0) + (close - (s.late or 0)) * math.min(1, dt * 4)

    local draw = 0.34 * close * (1 - nova) - 0.05 - 0.24 * open + 0.52 * snap
    for k = 0, 7 do
        pose(m["Rim" .. k], CFrame.fromAxisAngle(JELLY_RIM_AXIS[k], draw + 0.022 * math.sin(t * 1.7 + k * 0.8)))
    end
    pose(m.Apex, CFrame.new(0, (0.05 * close * (1 - nova) - 0.02 * open + 0.06 * snap) * u, 0))

    -- it knows where you are: the bell leans a little toward the camera, whichever way the pet is going
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    local calm = (1 - pace) * (1 - nova)
    s.leanX = (s.leanX or 0) + (toYou.Z * 0.15 * calm - (s.leanX or 0)) * math.min(1, dt * 1.4)
    s.leanZ = (s.leanZ or 0) + (-toYou.X * 0.15 * calm - (s.leanZ or 0)) * math.min(1, dt * 1.4)

    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.2, 0.2) - (s.bank or 0)) * math.min(1, dt * 3)
    local rise = 0.05 * (1 + pace) * heave + 0.012 * math.sin(t * 0.6) - 0.05 * open + 0.3 * snap
    pose(m.Body, CFrame.new(0, rise * u, 0) * CFrame.Angles(s.leanX - 0.5 * moving - 0.6 * fly + 0.03 * math.sin(t * 0.47), 0.05 * math.sin(t * 0.23), s.leanZ + s.bank + 0.03 * math.sin(t * 0.37)))

    -- the nebula turns, faster at each beat, and burns brighter as it spins up
    s.spin = ((s.spin or 0) + dt * (0.28 + 0.9 * s.late + 0.5 * pace + 3.6 * open + 2.2 * snap)) % (2 * math.pi)
    pose(m.Nebula, CFrame.new(0, 0.012 * close * u, 0) * CFrame.Angles(0, s.spin, 0))
    local clover = rig.parts.Clover
    if clover then
        clover.Color = rig.profile.GlowColors["ffb04a"]:Lerp(Color3.fromRGB(255, 160, 70), math.max(0.6 * s.late, open, snap))
    end

    -- all below it follows late: dragged behind it as it goes, drawn in after each beat and let go; each strand on its own wave, more of it toward the tip
    local back = -(0.34 * moving + 0.42 * fly)
    local gather = 0.14 * s.late - 0.1 * open + 0.26 * snap
    local swing = 0.05 + 0.03 * pace
    for name, tent in JELLY_TENTS do
        local index = 0
        for tag, share in JELLY_CHAIN do
            index = if tag == "a" then 1 elseif tag == "b" then 2 else 3
            local wave = swing * index * 0.55 * math.sin(t * (1.2 + pace) - index * 0.9 + tent.offset)
            local across = swing * index * 0.45 * math.sin(t * 0.85 - index * 0.8 + tent.offset * 1.7)
            pose(m["T" .. name .. tag], CFrame.fromAxisAngle(tent.axis, gather * share) * CFrame.Angles(back * share + wave, 0, across))
        end
    end
    for index, arm in JELLY_ARMS do
        for tag, share in JELLY_CHAIN do
            local joint = if tag == "a" then 1 elseif tag == "b" then 2 else 3
            pose(m[arm .. tag], CFrame.Angles(back * share * 0.7 + 0.05 * joint * math.sin(t * 1.05 - joint * 0.8 + index * 1.6), 0.09 * math.sin(t * 0.5 + index * 1.3) * (1 + 0.5 * s.late), 0.05 * joint * math.sin(t * 0.8 - joint + index * 2.1)))
        end
    end

    -- a scrap of nebula sheds a little of itself as it goes
    if not s.gas then
        local bone = rig.points.Apex
        if bone then
            local gas = Instance.new("ParticleEmitter")
            gas.Name = "Gas"
            gas.Texture = "rbxassetid://16172858603"
            gas.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
            gas.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
            gas.Lifetime = NumberRange.new(1.6, 2.4)
            gas.Speed = NumberRange.new(0.1 * rig.unit, 0.3 * rig.unit)
            gas.SpreadAngle = Vector2.new(180, 180)
            gas.Drag = 0.8
            gas.Rotation = NumberRange.new(0, 360)
            gas.RotSpeed = NumberRange.new(-14, 14)
            gas.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * rig.unit), NumberSequenceKeypoint.new(1, 0.42 * rig.unit) })
            gas.Color = ColorSequence.new(Color3.fromRGB(232, 72, 128), Color3.fromRGB(128, 84, 226))
            gas.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.6), NumberSequenceKeypoint.new(1, 1) })
            gas.LightEmission = 0.4
            gas.LightInfluence = 0.5
            gas.Parent = bone
            s.gas = gas
        end
    end
    if s.gas then
        s.gas.Rate = 0.7 + 1.8 * pace
    end
end

-- The Starfall Fox (skinned): sly and quick. Its head snaps from thing to thing and its pupils get there first; it stops to watch the sky; and when nothing is looking it digs a little with its forepaws, then checks over its shoulder that nobody saw.
-- It stands and trots on the ground (`dropToGround`), and flying it stretches out in long bounds with its tail streaming behind it like a comet. Its eyelids are bands fixed all along the rim of the eye: they close by stretching, on a hinge along each eye's long axis (+ closes the upper).
local FOX_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local FOX_LID_HINGE = { L = Vector3.new(-0.692, 0.3916, 0.6064), R = Vector3.new(-0.692, -0.3916, -0.6064) }
local FOX_BLINK_UPPER, FOX_BLINK_LOWER = math.rad(9.8), math.rad(5)
local FOX_LEADS = { FL = 0, BR = 0.35, FR = math.pi, BL = math.pi + 0.35 }
local FOX_TAIL = { "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip" }
local FOX_FALL_FROM, FOX_CATCH = 0.1, 0.42 -- of the special: the falling star shows, and reaches its teeth (PetRig.NOVA_BURST)
local FOX_STAR = "rbxassetid://95572555201628"
local FOX_SOLE = 0.625 -- metres from the model's centre down to its soles: it stands on the ground (it digs, so it can't hover), and leaves it only to fly

-- The star it is going to catch, coming down out of the sky at a slant
local function foxFallingStar(rig, s)
    local metre = rig.meters
    local holder = Instance.new("Part")
    holder.Name = "FallingStar"
    holder.Anchored = true
    holder.CanCollide = false
    holder.CanTouch = false
    holder.CanQuery = false
    holder.CastShadow = false
    holder.Transparency = 1
    holder.Size = Vector3.one * 0.05
    local a, b = Instance.new("Attachment"), Instance.new("Attachment")
    a.Position, b.Position = Vector3.new(0, 0.05 * metre, 0), Vector3.new(0, -0.05 * metre, 0)
    a.Parent, b.Parent = holder, holder
    local streak = Instance.new("Trail")
    streak.Attachment0, streak.Attachment1 = a, b
    streak.FaceCamera = true
    streak.Lifetime = 0.34
    streak.LightEmission = 1
    streak.LightInfluence = 0
    streak.WidthScale = NumberSequence.new(1, 0)
    streak.Color = ColorSequence.new(Color3.fromRGB(255, 240, 200), Color3.fromRGB(120, 140, 255))
    streak.Transparency = NumberSequence.new(0, 1)
    streak.Parent = holder
    local star = Instance.new("ParticleEmitter")
    star.Texture = FOX_STAR
    star.Rate = 0
    star.Lifetime = NumberRange.new(PetRig.NOVA_TIME)
    star.Speed = NumberRange.new(0)
    star.LockedToPart = true
    star.Rotation = NumberRange.new(0, 360)
    star.RotSpeed = NumberRange.new(180, 180)
    star.Size = NumberSequence.new(0.34 * metre)
    star.LightEmission = 1
    star.LightInfluence = 0
    star.Parent = a
    holder.CFrame = CFrame.new(rig.rootPart.Position + rig.rootPart.CFrame:VectorToWorldSpace(Vector3.new(-3.2, 9, -5) * metre))
    holder.Parent = rig.model.Parent or workspace
    star:Emit(1)
    Debris:AddItem(holder, PetRig.NOVA_TIME)
    s.foxStar = holder
end

local function animateStarfallFox(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > FOX_FAR then
        if s.foxDust then
            s.foxDust.FL.Rate, s.foxDust.FR.Rate = 0, 0
        end
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, FOX_SOLE)

    -- the special: it spots a falling star and crouches, rump up, wiggling; it leaps and takes it out of the air in its teeth; it lands, and straight away it digs, and buries it
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local crouch = smoothstep(0.02, 0.18, progress) * (1 - smoothstep(0.33, 0.37, progress))
    local spring = smoothstep(0.34, 0.41, progress) * (1 - smoothstep(0.43, 0.5, progress))
    local air = smoothstep(0.34, 0.42, progress) * (1 - smoothstep(0.5, 0.6, progress))
    local fall = smoothstep(0.46, 0.53, progress) * (1 - smoothstep(0.57, 0.63, progress))
    local land = smoothstep(0.58, 0.62, progress) * (1 - smoothstep(0.63, 0.72, progress))
    local bury = smoothstep(0.66, 0.71, progress) * (1 - smoothstep(0.92, 0.99, progress))
    local gape = smoothstep(0.26, 0.36, progress) * (1 - smoothstep(0.415, 0.43, progress))
    if rig.nova and progress >= FOX_FALL_FROM and not rig.nova.starFell then
        rig.nova.starFell = true
        foxFallingStar(rig, s)
    end
    local mouth = rig.points.Mouth
    if s.foxStar and mouth then
        local q = math.clamp((progress - FOX_FALL_FROM) / (FOX_CATCH - FOX_FALL_FROM), 0, 1)
        s.foxFrom = s.foxFrom or (s.foxStar.Position - mouth.TransformedWorldCFrame.Position)
        s.foxStar.CFrame = CFrame.new(mouth.TransformedWorldCFrame.Position + s.foxFrom * (1 - q ^ 1.5))
    else
        s.foxFrom = nil
    end

    -- when nothing is going on it digs, a little furtively, and looks round to see who saw
    s.nextDig = s.nextDig or t + 8 + math.random() * 8
    local dig, glance = 0, 0
    if t >= s.nextDig then
        local a = (t - s.nextDig) / 3.6
        if a >= 1 then
            s.nextDig = t + 15 + math.random() * 14
            s.glanceSide = if math.random() < 0.5 then 1 else -1
        elseif pace < 0.25 and nova == 0 then
            dig = smoothstep(0, 0.1, a) * (1 - smoothstep(0.62, 0.72, a))
            glance = smoothstep(0.7, 0.76, a) * (1 - smoothstep(0.93, 1, a))
        else
            s.nextDig = t + 3
        end
    end
    -- and it watches the sky. It is always a little hopeful
    s.nextSky = s.nextSky or t + 4 + math.random() * 5
    local sky = 0
    if t >= s.nextSky then
        local a = (t - s.nextSky) / 3
        if a >= 1 then
            s.nextSky = t + 9 + math.random() * 10
        elseif pace < 0.25 and nova == 0 and dig == 0 and glance == 0 then
            sky = smoothstep(0, 0.1, a) * (1 - smoothstep(0.82, 1, a))
        else
            s.nextSky = t + 2
        end
    end
    local digging = math.max(dig, bury)

    -- its head doesn't wander: it snaps to something new and holds, and the pupils get there first
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 1 + math.random() * 2.6
        s.gazeTo = (math.random() - 0.5) * 1.1
        s.nodTo = (math.random() - 0.5) * 0.2
        s.tiltTo = if math.random() < 0.3 then (math.random() - 0.5) * 0.5 else 0
    end
    local calm = (1 - pace * 0.75) * (1 - nova) * (1 - digging) * (1 - sky * 0.6)
    local yawTo = (s.gazeTo or 0) * calm + 1.15 * glance * (s.glanceSide or 1)
    local snap = math.min(1, dt * 13)
    s.yaw = (s.yaw or 0) + (yawTo - (s.yaw or 0)) * snap
    s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * snap
    s.tilt = (s.tilt or 0) + (((s.tiltTo or 0) * calm + 0.16 * sky) - (s.tilt or 0)) * snap
    s.eyeYaw = (s.eyeYaw or 0) + (yawTo - (s.eyeYaw or 0)) * math.min(1, dt * 30)

    -- the body: a light trot, two beats to a stride; flying, long bounds
    s.stride = (s.stride or 0) + dt * (9 * moving + 4.2 * fly)
    local stride = s.stride
    local breath = math.sin(t * 1.3)
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.22, 0.22) - (s.bank or 0)) * math.min(1, dt * 4)
    local pitch = 0.012 * math.sin(t * 1.3 - 0.7) - 0.03 * moving + 0.05 * fly + 0.06 * fly * math.sin(stride) - 0.08 * crouch + 0.5 * spring - 0.34 * fall - 0.05 * land - 0.3 * digging
    local rise = 0.012 * moving * math.cos(2 * stride) + 0.06 * fly + 0.03 * fly * math.sin(stride - 0.8) - 0.11 * crouch + 0.92 * air - 0.09 * land - 0.1 * digging
    pose(m.Body, CFrame.new(0, rise * u - drop, 0) * CFrame.Angles(pitch, 0, s.bank + 0.018 * moving * math.sin(stride)))
    pose(m.Hips, CFrame.Angles(-0.2 * crouch + 0.06 * fly * math.sin(stride - 1), 0.1 * crouch * math.sin(t * 24) + 0.03 * moving * math.sin(stride), 0))
    pose(m.Chest, CFrame.new(0, 0.004 * breath * u, 0) * CFrame.Angles(0.05 * fly * math.sin(stride + 0.4), 0, 0))

    -- the head keeps level over all of it, and looks up at what's falling
    local upward = 0.32 * sky + 0.3 * crouch + 0.14 * air
    pose(m.Neck, CFrame.Angles(-pitch * 0.45 + 0.5 * upward - 0.14 * digging + 0.01 * breath, s.yaw * 0.42, s.tilt * 0.3))
    pose(m.Head, CFrame.Angles(-pitch * 0.45 + 0.5 * upward + s.nod - 0.16 * digging + 0.012 * moving * math.cos(2 * stride - 0.5), s.yaw * 0.58, s.tilt * 0.7 - s.bank * 0.5))
    pose(m.Jaw, CFrame.Angles(-(0.36 * gape + 0.06 * pace * (0.5 + 0.5 * math.sin(t * 7))), 0, 0))

    -- it narrows its eyes at things: the lids rest low, close further as it stalks, and open wide in the leap
    s.nextBlink = s.nextBlink or t + 2
    if t >= s.nextBlink then
        s.nextBlink = t + 1.8 + math.random() * 3.6
        s.blinkAt = t
    end
    local shut = if s.blinkAt and t - s.blinkAt < 0.2 then 1 - math.abs(2 * (t - s.blinkAt) / 0.2 - 1) else 0
    shut = math.max(shut, 0.32 * crouch, 0.22 * digging)
    local wide = math.rad(3.4) * math.max(air, sky * 0.7, glance)
    for _, side in { "L", "R" } do
        local up = if side == "L" then -1 else 1
        pose(m["LidU" .. side], CFrame.fromAxisAngle(FOX_LID_HINGE[side], FOX_BLINK_UPPER * shut - wide))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(FOX_LID_HINGE[side], -FOX_BLINK_LOWER * shut))
        pose(m["Eye" .. side], CFrame.Angles(math.clamp(0.05 * sky + 0.05 * crouch - 0.04 * digging, -0.05, 0.05), math.clamp((s.eyeYaw - s.yaw) * 0.25 + s.eyeYaw * 0.05, -0.06, 0.06), 0))
        local offset = if side == "L" then 0 else 1.9
        local flick = math.max(0, math.sin(t * 0.9 + offset)) ^ 20
        pose(m["Ear" .. side], CFrame.Angles(0.04 * math.sin(t * 1.1 + offset) + 0.42 * pace + 0.28 * digging + 0.5 * air - 0.12 * math.max(sky, crouch) - 0.26 * flick, 0, up * (0.03 * math.sin(t * 0.7 + offset) + 0.14 * flick + 0.1 * pace)))
    end

    -- the legs
    local reach = 0.55 * moving
    local sink = crouch + 0.7 * land
    for key, lead in FOX_LEADS do
        local fore = string.sub(key, 1, 1) == "F"
        local sign = if fore then 1 else -1
        local phase = stride + lead
        local swing = math.sin(phase) * reach
        local fold = math.max(0, math.cos(phase)) * moving * 0.75
        -- flying: fore and hind pairs reach and gather together
        local bound = (if fore then 0.3 + 0.55 * math.sin(stride) else -0.3 + 0.55 * math.sin(stride + 0.8)) * fly
        local boundFold = (0.5 + 0.5 * math.sin(stride + (if fore then 1.4 else 2.2))) * fly * 0.5
        -- digging: the forepaws go at it in turn, fast; the hind legs just brace
        local paw = 0
        if fore then
            local scrape = math.sin(t * 17 + (if key == "FL" then 0 else math.pi))
            paw = 0.5 + 0.34 * scrape
        end
        local stretch = air * (if fore then 1 else -1.25)
        local a = swing + bound + digging * paw + stretch - pitch * (1 - air)
        local knee = fold + boundFold + digging * (if fore then 0.45 + 0.3 * math.sin(t * 17 + (if key == "FL" then 1 else 1 + math.pi)) else 0)
        -- crouching, the paws stay planted: the forelegs fold deep, elbows up, and the hind legs barely, since the rump stays high
        local hips = if fore then 0 else 0.2 * crouch
        pose(m["Leg" .. key .. "1"], CFrame.Angles(a + hips + (if fore then -1 else 0.2) * sink, 0, 0))
        pose(m["Leg" .. key .. "2"], CFrame.Angles(-sign * knee + (if fore then 1.85 else -0.42) * sink, 0, 0))
        pose(m["Paw" .. key], CFrame.Angles(sign * knee * 0.4 + (if fore then -0.85 else 0.22) * sink - 0.3 * sign * air, 0, 0))
    end

    -- the tail: a slow wave from root to tip; at speed it streams out behind; stalking, it lashes at the very end
    local wave = 0.05 + 0.11 * moving + 0.08 * fly + 0.05 * digging
    local rate = 1.5 + 5 * moving + 2.5 * fly
    s.wave = (s.wave or 0) + dt * rate
    local stream = math.max(fly, moving * 0.35, air)
    for index, name in FOX_TAIL do
        local along = index / #FOX_TAIL
        local lash = 0.1 * crouch * along * math.sin(t * 16 - index * 0.9)
        local down = (if index <= 2 then 0.1 * stream - 0.16 * digging - 0.12 * crouch else 0.17 * stream)
        pose(m[name], CFrame.Angles(down + 0.012 * math.sin(s.wave * 0.7 - index * 0.5), wave * math.sin(s.wave - index * 0.75) * (0.55 + 0.6 * along) + lash + s.bank * 0.12, 0))
    end

    -- gold kicked up from where it digs
    if not s.foxDust and rig.points.PawFL and rig.points.PawFR then
        s.foxDust = {}
        for _, key in { "FL", "FR" } do
            local dust = Instance.new("ParticleEmitter")
            dust.Name = "GoldDust"
            dust.Texture = SPARKLE
            dust.Rate = 0
            dust.Lifetime = NumberRange.new(0.3, 0.55)
            dust.Speed = NumberRange.new(0.5 * u, 1.1 * u)
            dust.EmissionDirection = Enum.NormalId.Back
            dust.SpreadAngle = Vector2.new(35, 35)
            dust.Acceleration = Vector3.new(0, -3 * u, 0)
            dust.Size = NumberSequence.new(0.035 * u, 0)
            dust.Color = ColorSequence.new(Color3.fromRGB(255, 214, 120), Color3.fromRGB(214, 120, 28))
            dust.LightEmission = 0.5
            dust.LightInfluence = 0.5
            dust.Parent = rig.points["Paw" .. key]
            s.foxDust[key] = dust
        end
    end
    if s.foxDust then
        local rateNow = 10 * dig + 22 * bury
        s.foxDust.FL.Rate, s.foxDust.FR.Rate = rateNow, rateNow
    end
end

-- The Lantern Warden (skinned): it stoops along on two thin legs, in no hurry, with its lantern swinging on the chain and its cape following late. Its face is a mask and doesn't change: what changes is the angle of its head, held very still and then slowly tilted,
-- and the pupils behind the slits, which slide about on their own (they turn on a pivot inside the mask, so they stay behind it) and blink by drawing back into the dark. When its light dims it turns and gives the lantern a tap.
local WARDEN_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local WARDEN_SOLE = 1.145 -- metres from the middle of its box down to its toes: it walks on the ground, and leaves it only to fly
local WARDEN_GLANCE = 0.2 -- radians either way the pupils slide
local WARDEN_LEGS = { L = 0, R = math.pi }
local WARDEN_LIGHT, WARDEN_DIM = Color3.fromRGB(255, 118, 26), Color3.fromRGB(110, 46, 12)

-- The lantern hangs: a damped pendulum, driven by how the Warden is accelerating
local function wardenPendulum(rig, s, dt, fly)
    local at = rig.rootPart.Position
    local step = math.clamp(dt, 0.001, 0.05)
    local velocity = (at - (s.lastAt or at)) / step
    s.lastAt = at
    local inFrame = rig.rootPart.CFrame:VectorToObjectSpace(velocity)
    if inFrame.Magnitude > 55 then -- not movement: it was teleported, or caught up with a teleported player
        inFrame = s.lastV or Vector3.zero
    end
    -- what it feels is its acceleration, smoothed: the follow path's small corrections shouldn't reach the lantern
    local push = (inFrame - (s.lastV or inFrame)) / step
    s.lastV = inFrame
    s.push = (s.push or Vector3.zero):Lerp(push, math.min(1, step * 9))
    local forward, sideways = math.clamp(-s.push.Z, -24, 24), math.clamp(s.push.X, -24, 24)
    local unit = rig.meters
    s.swingX = s.swingX or 0
    s.swingZ = s.swingZ or 0
    s.spinX = s.spinX or 0
    s.spinZ = s.spinZ or 0
    -- a pendulum about 0.35 m long: stiffness g/L, and it settles in a few swings
    local stiff, damp = 26, 2.2
    local restX = -0.5 * fly
    s.spinX = math.clamp(s.spinX + (-stiff * (s.swingX - restX) - damp * s.spinX - 2.4 * forward / unit) * step, -4, 4)
    s.spinZ = math.clamp(s.spinZ + (-stiff * s.swingZ - damp * s.spinZ - 2.4 * sideways / unit) * step, -4, 4)
    s.swingX += s.spinX * step
    s.swingZ += s.spinZ * step
    if math.abs(s.swingX) > 0.8 then -- the chain's limit: it stops there, and doesn't store up speed against it
        s.swingX = math.clamp(s.swingX, -0.8, 0.8)
        s.spinX = 0
    end
    if math.abs(s.swingZ) > 0.6 then
        s.swingZ = math.clamp(s.swingZ, -0.6, 0.6)
        s.spinZ = 0
    end
    return s.swingX, s.swingZ
end

local function animateLanternWarden(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WARDEN_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, WARDEN_SOLE)

    -- the special: it lifts the crook and reaches for the lantern, and the flame stands up; a path of small lights runs out from its feet, winds once round it and comes back to exactly where it started; it watches them all the way, and then tilts its head
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local raise = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.62, 0.86, progress))
    local surge = smoothstep(0.36, 0.42, progress) * (1 - smoothstep(0.5, 0.86, progress))
    local round = math.clamp((progress - 0.42) / 0.42, 0, 1)
    local watching = smoothstep(0.42, 0.47, progress) * (1 - smoothstep(0.82, 0.88, progress))
    local puzzled = smoothstep(0.84, 0.9, progress) * (1 - smoothstep(0.95, 1, progress))

    -- its light sometimes sinks: it turns to it, and taps
    s.nextTap = s.nextTap or t + 9 + math.random() * 8
    local tap, sunk = 0, 0
    if t >= s.nextTap then
        local a = (t - s.nextTap) / 3.2
        if a >= 1 then
            s.nextTap = t + 13 + math.random() * 14
        elseif pace < 0.25 and nova == 0 then
            tap = smoothstep(0.08, 0.26, a) * (1 - smoothstep(0.8, 1, a))
            sunk = smoothstep(0, 0.14, a) * (1 - smoothstep(0.58, 0.64, a))
            if a > 0.5 and a < 0.62 then
                local knock = math.sin((a - 0.5) / 0.12 * math.pi * 2)
                s.spinX = (s.spinX or 0) + 5 * knock * math.min(dt, 0.05)
            end
        else
            s.nextTap = t + 3
        end
    end

    -- the head: very still, and then slowly somewhere else, at an angle no neck would choose
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2.4 + math.random() * 4
        s.gazeTo = (math.random() - 0.5) * 1.0
        s.nodTo = (math.random() - 0.5) * 0.16
        s.tiltTo = if math.random() < 0.45 then (math.random() - 0.5) * 0.7 else 0
    end
    local calm = (1 - pace * 0.7) * (1 - nova) * (1 - tap)
    local yawTo = (s.gazeTo or 0) * calm + 0.62 * tap + 0.7 * raise * (1 - watching) + 0.85 * watching * math.sin(round * 2 * math.pi)
    local nodTo = (s.nodTo or 0) * calm + 0.16 * tap + 0.44 * raise * (1 - watching) - 0.42 * watching
    local tiltTo = (s.tiltTo or 0) * calm + 0.14 * tap + 0.55 * puzzled
    local slow = math.min(1, dt * 2.8)
    s.yaw = (s.yaw or 0) + (yawTo - (s.yaw or 0)) * slow
    s.nod = (s.nod or 0) + (nodTo - (s.nod or 0)) * slow
    s.tilt = (s.tilt or 0) + (tiltTo - (s.tilt or 0)) * slow

    -- the walk: long, slow stilt steps, the cape riding a little after each
    s.stride = (s.stride or 0) + dt * 5.4 * moving
    local stride = s.stride
    local breath = math.sin(t * 0.9)
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
    local pitch = 0.008 * math.sin(t * 0.9 - 0.6) - 0.05 * moving - 0.18 * fly + 0.1 * raise
    local rise = 0.012 * moving * math.cos(2 * stride) + 0.14 * fly + 0.03 * fly * math.sin(t * 1.5) + 0.03 * raise
    pose(m.Body, CFrame.new(0, rise * u - drop, 0) * CFrame.Angles(pitch, 0.05 * moving * math.sin(stride), s.bank + 0.045 * moving * math.sin(stride)))
    pose(m.Chest, CFrame.new(0, 0.004 * breath * u, 0) * CFrame.Angles(0.012 * moving * math.cos(2 * stride - 0.6), 0, 0))
    pose(m.Neck, CFrame.Angles(-pitch * 0.4 + s.nod * 0.42, s.yaw * 0.42, s.tilt * 0.26))
    pose(m.Head, CFrame.Angles(-pitch * 0.4 + s.nod * 0.58, s.yaw * 0.58, s.tilt * 0.74 - s.bank * 0.4))
    pose(m.Hat, CFrame.Angles(0.12 * fly + 0.012 * moving * math.cos(2 * stride - 1), 0, 0.012 * moving * math.sin(stride - 0.8)))

    -- the pupils get there first, and blink by drawing back into the dark
    s.nextBlink = s.nextBlink or t + 2
    if t >= s.nextBlink then
        s.nextBlink = t + 2.5 + math.random() * 4.5
        s.blinkAt = t
    end
    local shut = if s.blinkAt and t - s.blinkAt < 0.2 then 1 - math.abs(2 * (t - s.blinkAt) / 0.2 - 1) else 0
    s.eyeYaw = (s.eyeYaw or 0) + (math.clamp((yawTo - s.yaw) * 0.9 + 0.5 * math.sin(t * 0.37) * calm, -1, 1) - (s.eyeYaw or 0)) * math.min(1, dt * 16)
    local eye = CFrame.new(0, 0, 0.03 * shut * u) * CFrame.Angles(0, s.eyeYaw * WARDEN_GLANCE, 0)
    pose(m.EyeL, eye)
    pose(m.EyeR, eye)

    -- the legs: a bird's: the knee leads, and the shin folds as it comes through
    local reach = 0.5 * moving
    for side, lead in WARDEN_LEGS do
        local phase = stride + lead
        local swing = math.sin(phase) * reach
        local fold = math.max(0, math.cos(phase)) * moving
        -- flying: they trail, one a little behind the other, toes hanging
        local trail = fly * (if side == "L" then -0.5 else -0.32) + 0.05 * fly * math.sin(t * 1.5 + lead)
        pose(m["Leg" .. side .. "1"], CFrame.Angles(swing + trail - pitch, 0, 0))
        pose(m["Leg" .. side .. "2"], CFrame.Angles(-0.9 * fold + 0.25 * fly, 0, 0))
        pose(m["Leg" .. side .. "3"], CFrame.Angles(1.0 * fold + 0.18 * fly, 0, 0))
        pose(m["Foot" .. side], CFrame.Angles(-0.5 * fold - 0.34 * fly, 0, 0))
    end

    -- the cape: its hems trail at speed, bounce with each step, and flare in the air
    local bounce = moving * math.abs(math.sin(stride - 0.5))
    for tier, key in { Mid = 0.6, Low = 1 } do
        local trail = (0.14 * moving + 0.26 * fly) * key
        local flare = (0.05 * bounce + 0.2 * fly + 0.014 * (breath + 1)) * key
        local sway = 0.05 * moving * math.sin(stride - 0.9) * key
        pose(m[tier .. "F"], CFrame.Angles(-trail + flare * 0.6, 0, sway))
        pose(m[tier .. "B"], CFrame.Angles(-trail - flare, 0, sway))
        pose(m[tier .. "L"], CFrame.Angles(-trail * 0.6, 0, sway - flare))
        pose(m[tier .. "R"], CFrame.Angles(-trail * 0.6, 0, sway + flare))
    end

    -- the crook lifts for the special and gives a little with each step; the lantern swings
    local give = 0.012 * moving * math.cos(2 * stride - 1)
    pose(m.Crook1, CFrame.Angles(0.1 * raise + give + 0.14 * fly, 0, 0))
    pose(m.Crook2, CFrame.Angles(0.22 * raise + give, 0, 0.012 * moving * math.sin(stride - 1)))
    pose(m.Crook3, CFrame.Angles(0.26 * raise + give, 0, 0.018 * moving * math.sin(stride - 1.3)))
    local swingX, swingZ = wardenPendulum(rig, s, dt, fly)
    swingX += 0.03 * math.sin(t * 0.8) - pitch * 0.5 + 0.05 * moving * math.sin(2 * stride - 1)
    swingZ += 0.024 * math.sin(t * 0.53) + 0.09 * moving * math.sin(stride - 1.2)
    pose(m.Chain1, CFrame.Angles(swingX, 0, swingZ))
    pose(m.Chain2, CFrame.Angles(swingX * 0.3, 0, swingZ * 0.3))
    pose(m.Lantern, CFrame.Angles(swingX * 0.14, 0.2 * math.sin(t * 0.31), swingZ * 0.14))

    -- its left hand goes to the lantern; flying, its right holds its hat on
    local reachUp = math.max(raise, tap)
    local knock = if tap > 0.9 then 0.1 * math.sin(t * 16) else 0
    pose(m.ArmL1, CFrame.Angles(0.742 * reachUp + 0.36 * raise + 0.012 * breath + 0.05 * moving * math.sin(stride + 1), 0.496 * reachUp, 0))
    pose(m.ArmL2, CFrame.Angles(knock, 0.083 * reachUp, 0))
    pose(m.HandL, CFrame.Angles(0.3 * reachUp, 0, 0))
    pose(m.ArmR1, CFrame.Angles(1.111 * fly + 0.012 * breath - 0.05 * moving * math.sin(stride + 1), -0.193 * fly, 0))
    pose(m.ArmR2, CFrame.Angles(0.68 * fly, -0.45 * fly, 0))
    pose(m.HandR, CFrame.Angles(0.3 * fly, 0, 0))

    -- the flame. Nobody lit it, and nobody quite controls it
    local flicker = 0.5 + 0.5 * math.sin(t * 7.3 + 2.1 * math.sin(t * 2.3))
    local strength = (0.84 + 0.16 * flicker) * (1 - 0.72 * sunk) + 0.5 * surge
    local panels = rig.parts.Panels
    if panels then
        panels.Color = if strength > 1 then WARDEN_LIGHT:Lerp(Color3.fromRGB(255, 176, 84), math.min(1, strength - 1)) else WARDEN_DIM:Lerp(WARDEN_LIGHT, strength)
    end
    if not s.wardenLight and rig.points.Flame then
        local light = Instance.new("PointLight")
        light.Name = "LanternLight"
        light.Color = Color3.fromRGB(255, 170, 90)
        light.Shadows = false
        light.Parent = rig.points.Flame
        s.wardenLight = light
        -- a few sparks drifting up, the only thing about it that hurries
        local motes = Instance.new("ParticleEmitter")
        motes.Name = "Motes"
        motes.Texture = SPARKLE
        motes.Rate = 2.2
        motes.Lifetime = NumberRange.new(1.1, 1.9)
        motes.Speed = NumberRange.new(0.1 * u, 0.26 * u)
        motes.EmissionDirection = Enum.NormalId.Top
        motes.SpreadAngle = Vector2.new(50, 50)
        motes.Acceleration = Vector3.new(0, 0.12 * u, 0)
        motes.Drag = 0.6
        motes.Size = NumberSequence.new(0.03 * u, 0)
        motes.Color = ColorSequence.new(Color3.fromRGB(255, 220, 150), Color3.fromRGB(255, 130, 50))
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Parent = rig.points.Flame
    end
    if s.wardenLight then
        s.wardenLight.Range = (2.2 + 0.9 * surge) * u
        s.wardenLight.Brightness = 1.2 * strength
    end
end

-- The Dream Moth (skinned): it flutters, never still, drifting a little off its line as a moth does; now and then it fans its wings slowly, or uncurls its tongue to taste the air. Its eyes are compound eyes with no lids:
-- what moves in them is the pseudopupil, the dark spot a real insect's eye seems to turn on you. Here it really does: each one turns, on the eye's centre, toward whoever is looking.
local MOTH_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local MOTH_REST = { L = Vector3.new(-0.3862, 0.0736, -0.9195), R = Vector3.new(0.3862, 0.0736, -0.9195) } -- where each pseudopupil points at rest, in the head's axes
local MOTH_PUPIL_TURN = 0.45 -- radians it may turn from there
local MOTH_PUPIL_SHARE = 0.55 -- and only this share of the way to the camera: each eye is half sunk in the head, so what shows of it lies outward of its centre, and a pupil turned all the way sits at the inner edge of what you see (cross-eyed)
-- how far each stretch of the coiled tongue turns: unrolling it undoes these (from tools/blender/pets/dream_moth.py, its BENDS)
local MOTH_BENDS = { 0.2938, 0.3333, 0.3963, 0.4776, 0.5747, 0.6861, 0.8106, 0.9473, 1.0956, 1.2549, 1.4247 }
local MOTH_THREADS = 5
local MOTH_THREAD_FROM, MOTH_THREAD_TO = 0.06, 0.42 -- of the special: the dream's threads drift in, and reach its tongue at the burst
local MOTH_COLOURS = { Color3.fromRGB(255, 200, 236), Color3.fromRGB(214, 180, 255), Color3.fromRGB(176, 214, 255), Color3.fromRGB(255, 226, 200), Color3.fromRGB(236, 200, 255) }

-- The faint threads of a dream nobody remembers, spiralling in to its tongue
local function mothThreads(rig, s)
    local metre = rig.meters
    s.mothThreads = {}
    local folder = rig.model.Parent or workspace
    for k = 1, MOTH_THREADS do
        local holder = Instance.new("Part")
        holder.Name = "DreamThread"
        holder.Anchored = true
        holder.CanCollide = false
        holder.CanTouch = false
        holder.CanQuery = false
        holder.CastShadow = false
        holder.Transparency = 1
        holder.Size = Vector3.one * 0.05
        local a, b = Instance.new("Attachment"), Instance.new("Attachment")
        a.Position, b.Position = Vector3.new(0, 0.018 * metre, 0), Vector3.new(0, -0.018 * metre, 0)
        a.Parent, b.Parent = holder, holder
        local trail = Instance.new("Trail")
        trail.Attachment0, trail.Attachment1 = a, b
        trail.FaceCamera = true
        trail.Lifetime = 0.55
        trail.LightEmission = 0.4
        trail.LightInfluence = 0
        trail.WidthScale = NumberSequence.new(1, 0)
        local colour = MOTH_COLOURS[k]
        trail.Color = ColorSequence.new(colour, colour:Lerp(Color3.new(1, 1, 1), 0.35))
        trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) })
        trail.Parent = holder
        holder.Parent = folder
        Debris:AddItem(holder, PetRig.NOVA_TIME)
        table.insert(s.mothThreads, { part = holder, angle = (k / MOTH_THREADS) * 2 * math.pi + math.random() * 0.6, rise = (math.random() - 0.5) * 0.9, reach = (0.75 + 0.35 * math.random()) * metre })
    end
end

local function animateDreamMoth(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > MOTH_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: its tongue uncurls; threads of a forgotten dream drift in, spiralling, to the tip of it; then one slow, great wingbeat, and its tongue curls back up
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local sipping = smoothstep(0, 0.22, progress) * (1 - smoothstep(0.56, 0.8, progress))
    local lift = smoothstep(0.3, 0.42, progress) * (1 - smoothstep(0.44, 0.52, progress))
    local stroke = smoothstep(0.44, 0.52, progress) * (1 - smoothstep(0.56, 0.78, progress))
    local stillness = smoothstep(0.08, 0.3, progress) * (1 - smoothstep(0.42, 0.5, progress))
    if rig.nova and progress >= MOTH_THREAD_FROM and not rig.nova.threaded then
        rig.nova.threaded = true
        mothThreads(rig, s)
    end
    local tip = rig.points.Tongue12
    if s.mothThreads and tip then
        local q = math.clamp((progress - MOTH_THREAD_FROM) / (MOTH_THREAD_TO - MOTH_THREAD_FROM), 0, 1)
        local at = tip.TransformedWorldCFrame.Position
        local facing = rig.rootPart.CFrame
        for _, thread in s.mothThreads do
            if thread.part.Parent then
                local away = thread.reach * (1 - q) ^ 1.3
                local angle = thread.angle + q * 1.6 * math.pi -- (slow enough that the trail stays a curve, not a zigzag)
                local offset = facing:VectorToWorldSpace(Vector3.new(math.cos(angle) * away, thread.rise * away, math.sin(angle) * away))
                thread.part.CFrame = CFrame.new(at + offset)
            end
        end
    end

    -- now and then it fans its wings slowly, and now and then it tastes the air
    s.nextFan = s.nextFan or t + 6 + math.random() * 6
    local fanning = 0
    if t >= s.nextFan then
        local a = (t - s.nextFan) / 3.4
        if a >= 1 then
            s.nextFan = t + 12 + math.random() * 10
        elseif pace < 0.3 and nova == 0 then
            fanning = smoothstep(0, 0.15, a) * (1 - smoothstep(0.85, 1, a))
        else
            s.nextFan = t + 3
        end
    end
    s.nextTaste = s.nextTaste or t + 10 + math.random() * 8
    local taste = 0
    if t >= s.nextTaste then
        local a = (t - s.nextTaste) / 2.4
        if a >= 1 then
            s.nextTaste = t + 14 + math.random() * 12
        elseif nova == 0 then
            taste = 0.6 * smoothstep(0, 0.3, a) * (1 - smoothstep(0.65, 1, a))
        end
    end
    local uncurl = math.max(sipping, taste)

    -- the wings: a quick flutter, the hindwings a moment behind; fanning, slow and deep; in the special, held still, then lifted high and brought down once
    local rate = (2.4 + 0.9 * moving + 0.6 * fly) * (1 - 0.6 * fanning) * (1 - 0.85 * stillness)
    s.beat = (s.beat or 0) + dt * rate * 2 * math.pi
    local beat = s.beat
    local amp = (0.42 + 0.14 * moving + 0.1 * fly) * (1 + 0.6 * fanning) * (1 - 0.8 * stillness)
    local base = 0.12 + 0.3 * fanning + 1.0 * lift - 0.7 * stroke
    for _, side in { "L", "R" } do
        local up = if side == "L" then -1 else 1
        pose(m["Fore" .. side .. "1"], CFrame.Angles(0, up * 0.06 * math.sin(beat - 0.6), up * (base + amp * math.sin(beat))))
        pose(m["Fore" .. side .. "2"], CFrame.Angles(0, 0, up * (0.22 * amp * math.sin(beat - 0.9) - 0.12 * stroke)))
        pose(m["Hind" .. side .. "1"], CFrame.Angles(0, 0, up * (base * 0.85 + 0.9 * amp * math.sin(beat - 0.4))))
        pose(m["Hind" .. side .. "2"], CFrame.Angles(0, 0, up * (0.2 * amp * math.sin(beat - 1.2) - 0.1 * stroke)))
    end

    -- the body rides each downstroke, and a moth never flies quite straight
    local drift = 0.03 * math.sin(t * 1.3) + 0.018 * math.sin(t * 2.9 + 1)
    local rise = 0.022 * math.sin(beat - 1.3) + 0.02 * math.sin(t * 1.7) + 0.08 * lift
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
    local pitch = -0.06 * moving - 0.04 * fly - 0.16 * sipping
    pose(m.Body, CFrame.new(drift * u, rise * u, 0) * CFrame.Angles(pitch + 0.03 * math.sin(beat - 1.6), 0.05 * math.sin(t * 0.9), s.bank - drift * 1.6))
    for index, name in { "Abd1", "Abd2", "Abd3" } do
        pose(m[name], CFrame.Angles(-0.05 * math.sin(beat - 1.8 - index * 0.5) - 0.06 * moving + 0.05 * sipping, 0.05 * math.sin(t * 1.1 - index * 0.6), 0))
    end

    -- the head: curious, cocking this way and that
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 1.5 + math.random() * 2.5
        s.gazeTo = (math.random() - 0.5) * 0.6
        s.tiltTo = (math.random() - 0.5) * 0.5
    end
    local calm = (1 - 0.6 * pace) * (1 - nova)
    local follow = math.min(1, dt * 5)
    s.yaw = (s.yaw or 0) + ((s.gazeTo or 0) * calm - (s.yaw or 0)) * follow
    s.tilt = (s.tilt or 0) + ((s.tiltTo or 0) * calm - (s.tilt or 0)) * follow
    pose(m.Head, CFrame.Angles(-pitch * 0.5 - 0.22 * sipping + 0.02 * math.sin(beat - 2), s.yaw, s.tilt))

    -- its feathery antennae: sweeping slowly, twitching, laid back at speed and in the wingbeat
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 2.1
        local twitch = math.max(0, math.sin(t * 0.8 + offset)) ^ 18
        pose(m["Ant" .. side .. "1"], CFrame.Angles(0.08 * math.sin(t * 0.9 + offset) - 0.35 * pace - 0.3 * stroke + 0.2 * twitch, 0, sign * (0.06 * math.sin(t * 0.6 + offset) + 0.1 * twitch)))
        pose(m["Ant" .. side .. "2"], CFrame.Angles(0.06 * math.sin(t * 1.3 + offset) - 0.2 * pace + 0.15 * twitch, 0, 0))
    end

    -- the tongue: coiled, or uncurling to taste or to drink
    pose(m.Tongue1, CFrame.Angles(0.3 * uncurl, 0, 0))
    for k = 1, #MOTH_BENDS do
        pose(m["Tongue" .. (k + 1)], CFrame.Angles(-MOTH_BENDS[k] * 0.92 * uncurl, 0, 0))
    end

    -- the legs hang and paddle a little
    for _, key in { "F", "M", "B" } do
        for _, side in { "L", "R" } do
            local offset = (if key == "F" then 0 elseif key == "M" then 1.3 else 2.6) + (if side == "L" then 0 else 0.7)
            pose(m["Leg" .. key .. side .. "1"], CFrame.Angles(0.08 * math.sin(t * 1.5 + offset) - 0.4 * pace, 0, 0))
            pose(m["Leg" .. key .. side .. "2"], CFrame.Angles(0.1 * math.sin(t * 1.5 + offset - 0.6) - 0.3 * pace, 0, 0))
        end
    end

    -- the pseudopupils turn toward whoever is looking, as far as they can, and drift back when nobody is in front of it
    if camera then
        for _, side in { "L", "R" } do
            local bone = rig.points["Pupil" .. side]
            if bone then
                -- in the model's own axes as the head now holds them: what the head's pose has turned (its posed frame against its rest frame, both in the world), applied to the model's frame
                local head = bone.Parent
                local turnedBy = if head and head:IsA("Bone") then head.TransformedWorldCFrame.Rotation * head.WorldCFrame.Rotation:Inverse() else CFrame.identity
                local frame = turnedBy * rig.rootPart.CFrame.Rotation
                local toward = frame:VectorToObjectSpace(camera.CFrame.Position - bone.TransformedWorldCFrame.Position)
                local rest = MOTH_REST[side]
                local want = CFrame.identity
                if toward.Magnitude > 0.01 then
                    local d = toward.Unit
                    local axis = rest:Cross(d)
                    local angle = math.acos(math.clamp(rest:Dot(d), -1, 1))
                    if axis.Magnitude > 1e-4 and angle < 1.6 then
                        want = CFrame.fromAxisAngle(axis.Unit, math.min(angle * MOTH_PUPIL_SHARE, MOTH_PUPIL_TURN))
                    end
                end
                local key = "pupil" .. side
                s[key] = (s[key] or CFrame.identity):Lerp(want, math.min(1, dt * 6))
                pose(m["Pupil" .. side], s[key])
            end
        end
    end
end

-- The Prism Armadillo (skinned): it scurries on short quick legs, sniffs at everything, rears up on its hind legs to look about, and now and then rolls up into its armour for a moment, purely to show off. Its eyes have no upper lids:
-- soft cheek pads turn up round each eye from below (a pleased squint, or all the way for a blink). Flying, it rolls up and spins through the air. Its crest prisms each drift slowly through the spectrum.
local ARMA_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local ARMA_SOLE = 0.24 -- metres from the middle of its box down to its claws: it walks on the ground
local ARMA_CHEEK = { L = Vector3.new(0.2668, -0.441, -0.8569), R = Vector3.new(-0.2668, -0.441, -0.8569) } -- each pad's hinge, through its eye's centre: a positive turn carries it up over the eye
local ARMA_BLINK, ARMA_SQUINT = 1.15, 0.5
local ARMA_LEGS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi }
local ARMA_CRESTS = 6

local function animatePrismArmadillo(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > ARMA_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, ARMA_SOLE)

    -- the special: it rolls up, spins in place faster and faster, and pops open in a flash of every colour, very pleased with itself
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local curled = smoothstep(0, 0.12, progress) * (1 - smoothstep(0.44, 0.52, progress))
    local whirl = smoothstep(0.1, 0.3, progress) * (1 - smoothstep(0.4, 0.46, progress))
    local hop = smoothstep(0.44, 0.5, progress) * (1 - smoothstep(0.52, 0.64, progress))
    local proud = smoothstep(0.5, 0.58, progress) * (1 - smoothstep(0.86, 0.98, progress))
    local flash = smoothstep(0.36, 0.43, progress) * (1 - smoothstep(0.46, 0.66, progress))
    s.whirl = ((s.whirl or 0) + dt * whirl * 2 * math.pi * 2.4) % (2 * math.pi)
    if progress == 0 then
        s.whirl = s.whirl * math.max(0, 1 - dt * 6)
    end

    -- now and then: it rolls up for a moment just to be admired; or rears up to look about
    s.nextShow = s.nextShow or t + 10 + math.random() * 8
    local show = 0
    if t >= s.nextShow then
        local a = (t - s.nextShow) / 2.6
        if a >= 1 then
            s.nextShow = t + 16 + math.random() * 14
            s.pleasedUntil = t + 1.6
        elseif pace < 0.25 and nova == 0 then
            show = smoothstep(0, 0.12, a) * (1 - smoothstep(0.7, 0.82, a))
        else
            s.nextShow = t + 3
        end
    end
    s.nextRear = s.nextRear or t + 5 + math.random() * 6
    local rear = 0
    if t >= s.nextRear then
        local a = (t - s.nextRear) / 3.2
        if a >= 1 then
            s.nextRear = t + 12 + math.random() * 12
        elseif pace < 0.25 and nova == 0 and show == 0 then
            rear = smoothstep(0, 0.2, a) * (1 - smoothstep(0.78, 1, a))
        else
            s.nextRear = t + 2
        end
    end
    local roll = math.max(curled, show, fly)

    -- the body
    s.stride = (s.stride or 0) + dt * 11 * moving
    local stride = s.stride
    local breath = math.sin(t * 1.6)
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 4)
    -- flying, it is a ball rolling forward through the air
    s.tumble = ((s.tumble or 0) + dt * fly * 2 * math.pi * 1.3) % (2 * math.pi)
    local tumble = if fly > 0.5 then s.tumble else s.tumble * fly
    local lift = 0.012 * moving * math.abs(math.sin(stride)) + 0.12 * hop + 0.04 * rear - 0.03 * roll
    pose(m.Body, CFrame.new(0, lift * u - drop, 0) * CFrame.Angles(0.25 * rear - tumble + 0.1 * hop, s.whirl, s.bank * (1 - roll) + 0.02 * moving * math.sin(stride)))

    -- the armour's joints: rolled up as far as it is (the same numbers as tools/blender/pets/prism_armadillo.py's ball()), and a little give with each step
    pose(m.Front, CFrame.Angles(-0.46 * roll + 0.75 * rear * (1 - roll) + 0.2 * proud + 0.01 * breath, 0, 0))
    pose(m.Mid, CFrame.Angles(0.3 * roll + 0.012 * moving * math.sin(2 * stride), 0, 0))
    pose(m.Back, CFrame.Angles(0.3 * roll, 0, 0))
    pose(m.Pelvis, CFrame.Angles(0.48 * roll, 0, 0))

    -- the head: sniffing, curious, tucked away when rolled
    s.nextSniff = s.nextSniff or t + 1
    if t >= s.nextSniff then
        s.nextSniff = t + 1.2 + math.random() * 2.4
        s.sniffAt = t
        s.gazeTo = (math.random() - 0.5) * 0.9
        s.nodTo = (math.random() - 0.5) * 0.25
    end
    local sniff = if s.sniffAt and t - s.sniffAt < 0.7 then math.sin((t - s.sniffAt) * 26) * (1 - (t - s.sniffAt) / 0.7) else 0
    local calm = (1 - roll) * (1 - 0.5 * moving)
    s.yaw = (s.yaw or 0) + ((s.gazeTo or 0) * calm - (s.yaw or 0)) * math.min(1, dt * 6)
    s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * math.min(1, dt * 6)
    pose(m.Neck, CFrame.Angles(-1.25 * roll - 0.35 * rear * (1 - roll) + 0.3 * proud + s.nod * 0.5, s.yaw * 0.45, 0))
    pose(m.Head, CFrame.Angles(-1.1 * roll - 0.2 * rear * (1 - roll) + 0.2 * proud + s.nod * 0.5 + 0.03 * sniff, s.yaw * 0.55, 0.1 * proud * math.sin(t * 3)))

    -- the cheek pads: a blink now and then; pleased, half up
    s.nextBlink = s.nextBlink or t + 2
    if t >= s.nextBlink then
        s.nextBlink = t + 2.5 + math.random() * 3.5
        s.blinkAt = t
    end
    local shut = if s.blinkAt and t - s.blinkAt < 0.2 then 1 - math.abs(2 * (t - s.blinkAt) / 0.2 - 1) else 0
    local pleased = math.max(proud, if s.pleasedUntil and t < s.pleasedUntil then 1 else 0)
    s.pleased = (s.pleased or 0) + (pleased - (s.pleased or 0)) * math.min(1, dt * 5)
    local cheek = math.max(ARMA_BLINK * shut, ARMA_SQUINT * s.pleased, ARMA_BLINK * roll)
    for _, side in { "L", "R" } do
        pose(m["Cheek" .. side], CFrame.fromAxisAngle(ARMA_CHEEK[side], cheek))
        local offset = if side == "L" then 0 else 1.7
        local flick = math.max(0, math.sin(t * 0.9 + offset)) ^ 18
        local sign = if side == "L" then -1 else 1
        pose(m["Ear" .. side], CFrame.Angles(0.7 * roll + 0.3 * moving - 0.25 * rear + 0.3 * flick + 0.04 * math.sin(t * 1.3 + offset), 0, sign * (0.08 * flick)))
    end

    -- the legs: a quick little trot; rearing, the forelegs lift; rolled, all folded in
    local reach = 0.45 * moving * (1 - roll)
    for key, lead in ARMA_LEGS do
        local fore = string.sub(key, 1, 1) == "F"
        local phase = stride + lead
        local swing = math.sin(phase) * reach
        local fold = math.max(0, math.cos(phase)) * moving * (1 - roll) * 0.6
        local tuck1 = if fore then -0.9 else 0.9
        local tuck2 = if fore then 1.4 else -1.2
        local reared = if fore then -0.4 * rear else 0.25 * rear
        pose(m["Leg" .. key .. "1"], CFrame.Angles(swing + tuck1 * roll + reared * (1 - roll) - 0.25 * rear * (if fore then 0 else 1), 0, 0))
        pose(m["Leg" .. key .. "2"], CFrame.Angles((if fore then -fold else fold) + tuck2 * roll, 0, 0))
        pose(m["Paw" .. key], CFrame.Angles((if fore then 0.4 * fold else -0.3 * fold), 0, 0))
    end

    -- the tail: swishing as it goes, tucked when rolled
    for index, name in { "Tail1", "Tail2", "Tail3" } do
        local tuck = ({ 0.9, 0.8, 0.7 })[index]
        pose(m[name], CFrame.Angles(tuck * roll - 0.3 * rear * (index == 1 and 1 or 0) * (1 - roll), (0.08 + 0.12 * moving) * math.sin(t * 2.4 + stride - index * 0.7) * (1 - roll), 0))
    end

    -- the crest: each prism drifting through the spectrum, a step behind the one before; flashing white-bright when it shows off
    local bright = math.max(flash, 0.6 * show * smoothstep(0.3, 0.6, show))
    for k = 1, ARMA_CRESTS do
        local part = rig.parts["Crest" .. k]
        if part then
            local hue = ((k - 1) / ARMA_CRESTS + t * 0.05 + 2 * s.whirl / (2 * math.pi)) % 1
            part.Color = Color3.fromHSV(hue, 0.62 - 0.14 * bright, 1) -- (Neon pales a colour: below about 0.45 saturation the prisms all read white)
        end
    end
end

-- The Crystal Snail (skinned): it glides on a slow wave of its foot, stretching forward and gathering itself, and leaves a faint road of crystal glints where it has been. Its eyes are on stalks with no lids:
-- like a real snail it blinks by drawing a stalk in (one at a time, in quickly, out slowly), and what it feels shows in how the stalks lean, wave and droop. Shy now and then, it draws both in and lets them out again bit by bit.
local SNAIL_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local SNAIL_SOLE = 0.2606 -- metres from the middle of its box down to its sole: it glides on the ground
local SNAIL_STALK = { L = Vector3.new(-0.2266, 0.8952, -0.3837), R = Vector3.new(0.2266, 0.8952, -0.3837) } -- each stalk's line, root to eye, in the model's axes
local SNAIL_DRAW = 0.0753 -- metres each of a stalk's two moving joints draws back when it is all the way in (tools/blender/pets/crystal_snail.py's retract())
local SNAIL_GEMS = Color3.fromRGB(70, 225, 190)

local function snailRoad(rig, s, u)
    local tip = rig.points.TailTip
    if not tip then
        return
    end
    local road = Instance.new("ParticleEmitter")
    road.Name = "CrystalRoad"
    road.Texture = SPARKLE
    road.Rate = 0
    road.Lifetime = NumberRange.new(1.6, 2.4)
    road.Speed = NumberRange.new(0)
    road.Rotation = NumberRange.new(0, 360)
    road.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.12, 0.07 * u), NumberSequenceKeypoint.new(0.7, 0.05 * u), NumberSequenceKeypoint.new(1, 0) })
    road.Color = ColorSequence.new(Color3.fromRGB(190, 255, 236), Color3.fromRGB(110, 220, 230))
    road.LightEmission = 0.6
    road.LightInfluence = 0.4
    road.Parent = tip
    s.snailRoad = road
end

local function animateCrystalSnail(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SNAIL_FAR then
        if s.snailRoad then
            s.snailRoad.Rate = 0
        end
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, SNAIL_SOLE)
    if not s.snailRoad then
        snailRoad(rig, s, u)
    end

    -- the special: it draws itself in under its shell, stalks first; its crystals brighten; a road of crystal grows up behind it; then the stalks come out, to see whether anyone noticed, and the rest of it after
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local hide = smoothstep(0.04, 0.3, progress) * (1 - smoothstep(0.66, 0.86, progress))
    local stalksIn = smoothstep(0, 0.16, progress) * (1 - smoothstep(0.5, 0.64, progress))
    local glow = smoothstep(0.18, 0.42, progress) * (1 - smoothstep(0.48, 0.8, progress))
    local peek = smoothstep(0.56, 0.66, progress) * (1 - smoothstep(0.84, 0.98, progress))

    -- shy now and then: both stalks in, and out again slowly
    s.nextShy = s.nextShy or t + 12 + math.random() * 10
    local shy = 0
    if t >= s.nextShy then
        local a = (t - s.nextShy) / 3
        if a >= 1 then
            s.nextShy = t + 16 + math.random() * 14
        elseif nova == 0 then
            shy = smoothstep(0, 0.08, a) * (1 - smoothstep(0.25, 1, a))
        end
    end
    -- it blinks one stalk at a time: in quickly, out slowly
    s.nextBlink = s.nextBlink or t + 2
    if t >= s.nextBlink then
        s.nextBlink = t + 2 + math.random() * 3.5
        s.blinkAt = t
        s.blinkSide = if math.random() < 0.5 then "L" else "R"
    end
    local blink = 0
    if s.blinkAt then
        local a = t - s.blinkAt
        blink = smoothstep(0, 0.07, a) * (1 - smoothstep(0.12, 0.5, a))
    end

    -- the gaze: the head turns slowly; the stalks wander on their own
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2 + math.random() * 3
        s.gazeTo = (math.random() - 0.5) * 0.8
        s.nodTo = (math.random() - 0.5) * 0.18
        s.tiltTo = if math.random() < 0.35 then (math.random() - 0.5) * 0.4 else 0
    end
    local calm = (1 - 0.5 * pace) * (1 - hide)
    local follow = math.min(1, dt * 2.2)
    s.yaw = (s.yaw or 0) + (((s.gazeTo or 0) * calm + 0.5 * peek * math.sin(t * 2.2)) - (s.yaw or 0)) * follow
    s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * follow
    s.tilt = (s.tilt or 0) + ((s.tiltTo or 0) * calm - (s.tilt or 0)) * follow

    -- the glide: a slow wave runs back along the foot; the front stretches forward and gathers
    s.glide = (s.glide or 0) + dt * (1 + 4 * moving)
    local wave = s.glide
    local stretch = (0.5 + 0.5 * math.sin(wave)) * moving
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.15, 0.15) - (s.bank or 0)) * math.min(1, dt * 3)
    local breath = math.sin(t * 1.1)
    pose(m.Body, CFrame.new(0, (0.004 * breath + 0.05 * fly) * u - drop, 0) * CFrame.Angles(0.06 * fly + 0.008 * breath, -s.bank * 0.6, 0.04 * fly * math.sin(t * 1.4)))
    pose(m.Front, CFrame.new(0, -0.025 * hide * u + 0.006 * moving * math.sin(wave - 0.5) * u, (0.08 * hide - 0.045 * stretch) * u)
        * CFrame.Angles(0.06 * stretch - 0.15 * hide + 0.15 * fly + 0.02 * breath, s.yaw * 0.4 + s.bank, 0))
    pose(m.Head, CFrame.Angles(0.12 * stretch - 0.35 * hide + s.nod + 0.08 * peek, s.yaw * 0.6, s.tilt))
    pose(m.Tail1, CFrame.Angles(0.025 * moving * math.sin(wave - 1.2) - 0.35 * fly, 0.08 * math.sin(t * 0.6) * (1 - moving) - s.bank, 0))
    pose(m.Tail2, CFrame.Angles(0.035 * moving * math.sin(wave - 2.2) - 0.45 * fly, 0.1 * math.sin(t * 0.6 - 0.8) * (1 - moving) - s.bank * 1.3, 0))
    pose(m.TailTip, CFrame.Angles(-0.2 * fly, 0, 0))
    pose(m.Shell, CFrame.Angles(0.02 * moving * math.sin(wave - 0.6) + 0.012 * math.sin(t * 0.7) + 0.02 * glow * math.sin(t * 38), 0, 0.025 * math.sin(t * 0.5) + 0.03 * moving * math.sin(wave * 0.5)))

    -- the stalks: each wanders, leans back at speed and in the air, forward when it peeks out; drawn in to blink, when shy, and in the special
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 2.3
        local lean = 0.12 * math.sin(t * 0.8 + offset) + 0.35 * moving + 0.5 * fly - 0.3 * peek
        local spread = sign * (0.1 * math.sin(t * 0.6 + offset) + 0.08 * peek * math.sin(t * 3 + offset))
        local drawn = math.max(if s.blinkSide == side then blink else 0, shy, stalksIn, 0.8 * hide)
        local back = SNAIL_STALK[side] * (-drawn * SNAIL_DRAW * u)
        pose(m["Stalk" .. side .. "1"], CFrame.Angles(lean, 0, spread))
        pose(m["Stalk" .. side .. "2"], CFrame.new(back) * CFrame.Angles(0.2 * lean + 0.08 * math.sin(t * 1.3 + offset), 0, sign * 0.06 * math.sin(t * 1.1 + offset)))
        pose(m["Stalk" .. side .. "3"], CFrame.new(back) * CFrame.Angles(0.05 * math.sin(t * 1.7 + offset), 0, 0))
    end

    -- the glowing crystals breathe; in the special they burn
    local gems = rig.parts.Gems
    if gems then
        gems.Color = SNAIL_GEMS:Lerp(Color3.fromRGB(200, 255, 240), 0.18 * (0.5 + 0.5 * math.sin(t * 1.4)) + 0.6 * glow)
    end
    if s.snailRoad then
        s.snailRoad.Rate = 7 * moving * (1 - fly)
    end
end

-- The Wind Sprite is one smooth skin on a skeleton, so its joints are Bones (PetRig.buildSkinned). Axes as everywhere: -Z ahead, +X to its right; its left is -X.
local WIND_LID_HINGE = { L = Vector3.new(0.9574, -0.1218, -0.2618), R = Vector3.new(0.9574, 0.1218, 0.2618) } -- both lids of an eye turn on this line
local WIND_BLINK_UPPER, WIND_BLINK_LOWER = math.rad(72), math.rad(22)
local WIND_CREST_TURN = math.rad(35) -- both hair bones turned at rest: built side-on its curl reads from the front as a stump; turned, as a curled topknot
local WIND_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest

local function windLids(m, side, upper, lower)
    local hinge = WIND_LID_HINGE[side]
    pose(m["LidU" .. side], CFrame.fromAxisAngle(hinge, -upper))
    pose(m["LidL" .. side], CFrame.fromAxisAngle(hinge, lower))
end

local function animateWindSprite(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WIND_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: it fills its cheeks, leaning back, then blows the gale out at the moment of the burst
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local inhale = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.41, 0.47, progress))
    local blow = smoothstep(0.4, 0.45, progress) * (1 - smoothstep(0.74, 0.92, progress))

    -- blinks, now and then a double
    s.nextBlink = s.nextBlink or t + 1 + math.random() * 2
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.17
        if a >= 1 then
            s.nextBlink = t + (if math.random() < 0.18 then 0.12 else 2.2 + math.random() * 3.6)
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end

    -- its eyes dart about; its head follows them, late
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 0.8 + math.random() * 2.4
        s.gazeYawTo, s.gazePitchTo = (math.random() - 0.5) * 0.62, (math.random() - 0.45) * 0.24
    end
    local calm = (1 - pace * 0.7) * (1 - nova)
    s.gazeYaw = (s.gazeYaw or 0) + ((s.gazeYawTo or 0) * calm - (s.gazeYaw or 0)) * math.min(1, dt * 24)
    s.gazePitch = (s.gazePitch or 0) + ((s.gazePitchTo or 0) * calm - (s.gazePitch or 0)) * math.min(1, dt * 24)
    s.headYaw = (s.headYaw or 0) + (s.gazeYaw * 0.65 - (s.headYaw or 0)) * math.min(1, dt * 3.5)

    -- the look it gets when it is up to something: a raised brow, narrowed eyes, a crooked smile
    s.nextSly = s.nextSly or t + 5 + math.random() * 6
    local sly = 0
    if t >= s.nextSly then
        local a = (t - s.nextSly) / 2.6
        if a >= 1 then
            s.nextSly = t + 7 + math.random() * 9
            s.slySide = if math.random() < 0.5 then 1 else -1
        else
            sly = smoothstep(0, 0.14, a) * (1 - smoothstep(0.82, 1, a))
        end
    end
    sly *= (1 - nova)
    local slySide = s.slySide or 1

    -- every so often it reaches out with one sleeve and tugs, twice, to get your attention
    s.nextTug = s.nextTug or t + 8 + math.random() * 8
    local reach, tug, tugSide = 0, 0, s.tugSide or 1
    if t >= s.nextTug then
        local a = (t - s.nextTug) / 2.1
        if a >= 1 then
            s.nextTug = t + 14 + math.random() * 12
            s.tugSide = -tugSide
        elseif pace < 0.25 and nova == 0 then
            reach = smoothstep(0, 0.2, a) * (1 - smoothstep(0.82, 1, a))
            tug = reach * math.max(0, math.sin((a - 0.22) * math.pi * 2 * 3.2)) * (if a > 0.22 and a < 0.85 then 1 else 0)
        end
    end
    local tugBody = reach * tugSide

    -- body and head
    local hover = 0.03 * math.sin(t * 1.9) + 0.012 * math.sin(t * 3.3 + 1) + 0.03 * fly + 0.2 * nova
    pose(m.Body, CFrame.new(0, hover * u, 0)
        * CFrame.Angles(0.03 * math.sin(t * 1.9 - 0.7) - 0.26 * moving - 0.5 * fly + 0.3 * inhale - 0.2 * blow - 0.1 * tug,
            0.05 * math.sin(t * 0.43) + 0.12 * tugBody,
            0.035 * math.sin(t * 0.71) - 0.09 * tugBody))
    pose(m.Head, CFrame.Angles(0.04 * math.sin(t * 1.9 - 1.6) + s.gazePitch * 0.4 + 0.14 * moving + 0.3 * fly - 0.12 * inhale + 0.2 * blow,
        s.headYaw + 0.2 * tugBody, 0.05 * math.sin(t * 0.37) * calm - 0.1 * tugBody + 0.07 * sly * slySide))

    -- the face
    local gazePitch = s.gazePitch
    local squeeze = math.max(blink, 0.82 * blow)
    local rest = math.rad(6 - 8 * inhale + 14 * sly + 5 * tug)
    local upper = rest + (WIND_BLINK_UPPER - rest) * squeeze - gazePitch * 0.35
    local lower = math.rad(7) * sly + WIND_BLINK_LOWER * squeeze
    for _, side in { "L", "R" } do
        pose(m["Eye" .. side], CFrame.Angles(gazePitch, s.gazeYaw, 0))
        windLids(m, side, upper, lower)
    end
    local browL = 0.008 * sly * (if slySide > 0 then 1.5 else -0.4) + 0.012 * inhale - 0.012 * blow
    local browR = 0.008 * sly * (if slySide < 0 then 1.5 else -0.4) + 0.012 * inhale - 0.012 * blow
    pose(m.BrowL, CFrame.new(0, browL * u, 0))
    pose(m.BrowR, CFrame.new(0, browR * u, 0))
    local pucker = math.max(inhale * 0.55, blow)
    pose(m.Smile, CFrame.new(0.006 * sly * slySide * u, 0.004 * sly * u, 0.03 * pucker * u) * CFrame.Angles(0, 0, 0.14 * sly * slySide))
    pose(m.Blow, CFrame.new(0, 0, -0.036 * pucker * u))
    local puff = inhale + 0.45 * blow
    pose(m.CheekL, CFrame.new(-0.032 * puff * u, 0, -0.026 * puff * u))
    pose(m.CheekR, CFrame.new(0.032 * puff * u, 0, -0.026 * puff * u))

    -- ears and hair take the wind
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 2.3
        local flick = math.max(0, math.sin(t * 1.1 + offset)) ^ 14
        pose(m["Ear" .. side], CFrame.Angles(0.38 * pace + 0.35 * blow + 0.04 * math.sin(t * 2.1 + offset), 0,
            sign * (0.05 * math.sin(t * 0.9 + offset) + 0.32 * flick + 0.22 * inhale - 0.14 * pace)))
    end
    pose(m.Crest1, CFrame.Angles(0.05 * math.sin(t * 1.4) + 0.2 * pace + 0.3 * blow, WIND_CREST_TURN, 0.05 * math.sin(t * 0.9)))
    pose(m.Crest2, CFrame.Angles(0.09 * math.sin(t * 1.4 - 0.9) + 0.26 * pace + 0.4 * blow, WIND_CREST_TURN, 0.08 * math.sin(t * 0.9 - 1)))

    -- the sleeves: trailing when it flies, and the tug
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        local mine = if (side == "L") == (tugSide < 0) then 1 else 0
        local idle = 0.06 * math.sin(t * 1.9 - 1 + sign)
        local lift = mine * reach * 1.15 - mine * tug * 0.42
        local trail = -0.75 * moving - 1.05 * fly + 0.5 * inhale - 0.6 * blow
        pose(m["Arm" .. side .. "1"], CFrame.Angles(idle + trail + lift, sign * -0.35 * mine * reach, sign * 0.1 * math.sin(t * 1.3) * (1 - pace)))
        pose(m["Arm" .. side .. "2"], CFrame.Angles(idle * 0.7 + trail * 0.45 + mine * reach * 0.45 - mine * tug * 0.3, 0, 0))
    end
    pose(m.Tassel, CFrame.Angles(-0.42 * pace - 0.5 * blow + 0.08 * math.sin(t * 1.9 - 1.4) + 0.3 * tug, 0, 0.1 * math.sin(t * 1.17)))

    -- its wings flutter all the time, too fast to count
    s.flap = (s.flap or 0) + dt * (42 + 14 * moving + 22 * fly + 18 * nova)
    local amplitude = 0.085 + 0.2 * moving + 0.36 * fly + 0.42 * nova
    local beat = amplitude * math.sin(s.flap)
    local flex = amplitude * 0.75 * math.sin(s.flap - 1)
    local rise = 0.05 + 0.08 * fly + 0.22 * nova
    local sweep = 0.22 * moving + 0.42 * fly - 0.2 * inhale
    pose(m.WingL, CFrame.Angles(0, -sweep, -(rise + beat)))
    pose(m.WingR, CFrame.Angles(0, sweep, rise + beat))
    pose(m.WingMidL, CFrame.Angles(0, 0, -flex))
    pose(m.WingMidR, CFrame.Angles(0, 0, flex))

    -- the curl: a wave running down it; speed and the blow unwind it, and an in-breath winds it tight
    local open = math.rad(10) * moving + math.rad(15) * fly + math.rad(17) * blow - math.rad(4) * inhale
    for k = 1, 7 do
        local f = k / 7
        pose(m["Tail" .. k], CFrame.Angles(open + 0.05 * (0.4 + f) * math.sin(t * 1.6 - k * 0.6),
            0.045 * (0.5 + f) * (1 + moving) * math.sin(t * 1.15 - k * 0.5), 0.025 * math.sin(t * 0.8 - k * 0.45)))
    end
    pose(m.TailTip, CFrame.Angles(open + 0.1 * math.sin(t * 1.6 - 5), 0, 0.05 * math.sin(t * 2.1)))
end

-- The Galaxy Manta (a skinned pet, like the Wind Sprite): waves run out along its wings and back across them; a little galaxy turns under it, on its own bones, so
-- the body can bank and roll over it. Rings turning at slightly different speeds wind and unwind the arms.
local MANTA_SPAN = { 0.10, 0.13, 0.17, 0.2 }

local function animateGalaxyManta(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WIND_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: it rears until the galaxy faces the world, gathering, then sweeps down as it is thrown open
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local rear = smoothstep(0, 0.3, progress) * (1 - smoothstep(0.62, 0.95, progress))
    local gather = smoothstep(0.08, 0.4, progress) * (1 - smoothstep(0.42, 0.47, progress))
    local sweep = smoothstep(0.41, 0.46, progress) * (1 - smoothstep(0.52, 0.85, progress))

    -- it leans into its turns, a wing dropping
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = heading - (s.heading or heading)
    turned = (turned + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    local turnRate = if dt > 0 then turned / dt else 0
    s.bank = (s.bank or 0) + (math.clamp(turnRate * 0.3, -0.6, 0.6) - (s.bank or 0)) * math.min(1, dt * 3)

    -- now and then, for no reason but joy, a slow barrel roll
    s.nextRoll = s.nextRoll or t + 9 + math.random() * 10
    local rollAngle, rollLift = 0, 0
    if t >= s.nextRoll then
        local a = (t - s.nextRoll) / 3.2
        if a >= 1 then
            s.nextRoll = t + 18 + math.random() * 16
            s.rollSide = if math.random() < 0.5 then 1 else -1
        elseif pace < 0.25 and nova == 0 then
            rollAngle = (s.rollSide or 1) * 2 * math.pi * smoothstep(0.05, 0.95, a)
            rollLift = math.sin(math.pi * a)
        else
            s.nextRoll = t + 4
        end
    end
    local calm = 1 - 0.75 * rollLift

    -- every so often it opens its mouth and spreads its horn fins, feeding on the dark
    s.nextFeed = s.nextFeed or t + 6 + math.random() * 8
    local feed = 0
    if t >= s.nextFeed then
        local a = (t - s.nextFeed) / 2.8
        if a >= 1 then
            s.nextFeed = t + 13 + math.random() * 12
        else
            feed = smoothstep(0, 0.22, a) * (1 - smoothstep(0.72, 1, a))
        end
    end
    local open = math.max(feed * (1 - pace), 0.8 * rear)

    s.flap = (s.flap or 0) + dt * (1.5 + 0.9 * moving + 1.7 * fly + 0.8 * sweep - 0.7 * gather)
    local flap = s.flap
    local hover = -0.035 * math.sin(flap + 0.7) + 0.02 * math.sin(t * 0.61) + 0.05 * fly + 0.45 * rollLift + 0.32 * rear
    pose(m.Body, CFrame.new(0, hover * u, 0)
        * CFrame.Angles(0.05 * math.sin(flap + 1.6) - 0.13 * moving - 0.24 * fly + 1.08 * rear - 0.32 * sweep, 0, s.bank + rollAngle))
    pose(m.Head, CFrame.Angles(0.035 * math.sin(flap + 0.8) + 0.06 * pace - 0.3 * rear, 0.05 * math.sin(t * 0.37), 0))

    -- the wings: each joint a little behind the last, so the beat travels out to the tip; the back of the wing follows the front
    local stroke = (0.9 + 0.35 * moving + 0.2 * fly) * calm
    local back = 0.2 * moving + 0.42 * fly - 0.2 * gather
    for k = 1, 4 do
        local beat = stroke * MANTA_SPAN[k] * math.sin(flap - k * 0.55)
        local lift = (if k == 1 then 0.1 else 0.05) * (1 - pace) * 0.4 + 0.2 * gather + 0.05 * rear - 0.3 * sweep * (k + 1) / 3
        local swing = if k == 1 then back else 0
        pose(m["WingL" .. k], CFrame.Angles(0, swing, -(beat + lift)))
        pose(m["WingR" .. k], CFrame.Angles(0, -swing, beat + lift))
        local fold = (0.12 + 0.05 * k) * math.sin(flap - k * 0.55 - 1.3) * calm + 0.14 * moving + 0.2 * fly - 0.2 * gather
        pose(m["WingRearL" .. k], CFrame.Angles(fold, 0, 0))
        pose(m["WingRearR" .. k], CFrame.Angles(fold, 0, 0))
    end

    -- the eyes turn slowly, and old: an animal watching, not a toy
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2.5 + math.random() * 4
        s.gazeTo = (math.random() - 0.5) * 0.5
    end
    s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) - (s.gaze or 0)) * math.min(1, dt * 3)
    pose(m.EyeL, CFrame.Angles(0, s.gaze, 0))
    pose(m.EyeR, CFrame.Angles(0, s.gaze, 0))

    pose(m.Smile, CFrame.new(0, 0, 0.03 * open * u))
    pose(m.Mouth, CFrame.new(0, 0, -0.036 * open * u))

    -- the horn fins furl and open; they spread as it feeds and stream back at speed
    for k = 1, 3 do
        local sway = 0.06 * math.sin(t * 0.9 - k * 0.7)
        local spread = 0.2 * open - 0.13 * k * pace * 0.5
        pose(m["HornL" .. k], CFrame.Angles(sway + 0.12 * pace, -spread, 0.03 * math.sin(t * 0.7 - k)))
        pose(m["HornR" .. k], CFrame.Angles(sway + 0.12 * pace, spread, -0.03 * math.sin(t * 0.7 - k)))
    end

    -- the tail: a slow wave, straightening with speed, tucking under as it rears
    local whip = 1 + 0.5 * moving
    local level = 0.055 * pace - 0.09 * rear
    for k = 1, 8 do
        local f = k / 8
        pose(m["Tail" .. k], CFrame.Angles(level + 0.03 * math.sin(t * 1.1 - k * 0.5) + 0.05 * sweep, whip * (0.035 + 0.05 * f) * math.sin(t * 1.7 - k * 0.62) * (1 - 0.5 * fly), 0))
    end
    pose(m.TailTip, CFrame.Angles(0, 0.1 * math.sin(t * 2.3), 0))

    -- the galaxy turns, its arms trailing. At speed it lags behind and tips; when it rears, the wheel rises and faces forward with it, spinning up
    s.spin = (s.spin or 0) + dt * (0.24 + 0.2 * pace + 3.4 * gather + 2.6 * sweep)
    local follow = CFrame.new(0, (0.82 * rear + 0.3 * rollLift) * u, (0.3 * pace - 0.62 * rear) * u) * CFrame.Angles(1.08 * rear - 0.22 * pace, 0, 0)
    pose(m.SpiralOuter, follow * CFrame.Angles(0, -s.spin, 0))
    pose(m.SpiralMid, follow * CFrame.Angles(0, -(s.spin * 1.14 + 0.14 * math.sin(t * 0.23)), 0))
    pose(m.SpiralInner, follow * CFrame.Angles(0, -(s.spin * 1.34 + 0.3 * math.sin(t * 0.17)), 0))
    s.orbit = (s.orbit or 0) + dt * (0.34 + 0.7 * nova)
    pose(m.Orbit, follow * CFrame.Angles(0, -s.orbit, 0))
end

-- The Stormhorn Kirin (skinned): a proud walker on the air. A rocking canter with a real lead, its hooves throwing sparks where they land; its head carried high and low with the
-- stride, its mane and tail on a wind only it feels, lightning flickering in the mane. It paws and tosses its head when it stands. Its joints: +X swings a limb's far end forward, and raises
-- what points ahead. Hind legs bend the other way at the stifle (Leg2) from the hock (Leg3).
local KIRIN_LEADS = { FL = 0, BR = 0.3, FR = math.pi, BL = math.pi + 0.3 }
local KIRIN_LID_HINGE = { L = Vector3.new(0.4472, -0.2227, -0.8662), R = Vector3.new(0.4472, 0.2227, 0.8662) }
local KIRIN_BLINK_UPPER, KIRIN_BLINK_LOWER = math.rad(36), math.rad(12)
local KIRIN_MANE = { A = 0, B = 0.9, C = 1.8 }

local function animateStormhornKirin(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WIND_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special: it rears, its horn raised; the forelegs come down as lightning flares through its mane
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local rear = smoothstep(0, 0.3, progress) * (1 - smoothstep(0.39, 0.46, progress))
    local slam = smoothstep(0.39, 0.46, progress) * (1 - smoothstep(0.52, 0.86, progress))

    -- now and then, standing: it paws the air and stamps, or tosses its head
    s.nextPaw = s.nextPaw or t + 5 + math.random() * 6
    local paw = 0
    if t >= s.nextPaw then
        local a = (t - s.nextPaw) / 1.9
        if a >= 1 then
            s.nextPaw = t + 10 + math.random() * 10
        elseif pace < 0.2 and nova == 0 then
            paw = math.sin(a * math.pi) * (0.65 + 0.35 * math.sin(a * math.pi * 6))
            if a > 0.8 and not s.stamped then
                s.stamped = true
                s.flickerUntil = t + 0.3
                local sparks = s.sparks and s.sparks.FR
                if sparks then
                    sparks:Emit(7)
                end
            end
        end
    else
        s.stamped = false
    end
    s.nextToss = s.nextToss or t + 8 + math.random() * 8
    local toss = 0
    if t >= s.nextToss then
        local a = (t - s.nextToss) / 1.1
        if a >= 1 then
            s.nextToss = t + 9 + math.random() * 9
        elseif pace < 0.3 and nova == 0 then
            toss = math.sin(a * math.pi) * math.sin(a * math.pi * 2.5)
        end
    end

    -- the stride
    if not s.sparks then
        s.sparks = {}
        for key in KIRIN_LEADS do
            local hoof = rig.points["Hoof" .. key]
            local sparks = hoof and hoof:FindFirstChild("Sparks")
            if sparks then
                sparks.Enabled = false -- only where a hoof lands: hot, thrown out, falling under gravity
                sparks.Texture = "rbxassetid://113649240058592"
                sparks.Orientation = Enum.ParticleOrientation.VelocityParallel
                sparks.Rotation = NumberRange.new(90)
                sparks.Speed = NumberRange.new(2.6 * rig.unit, 5 * rig.unit)
                sparks.SpreadAngle = Vector2.new(70, 70)
                sparks.Acceleration = Vector3.new(0, -8 * rig.unit, 0)
                sparks.Drag = 1.5
                sparks.Lifetime = NumberRange.new(0.2, 0.42)
                sparks.Size = NumberSequence.new(0.13 * rig.unit, 0.05 * rig.unit)
                sparks.Color = ColorSequence.new(Color3.fromRGB(225, 238, 255), Color3.fromRGB(255, 190, 110))
                s.sparks[key] = sparks
            end
        end
    end
    s.stride = (s.stride or 0) + dt * (10.5 * moving + 4.5 * fly)
    local stride = s.stride
    local rock = math.sin(stride + 0.6)
    local tuck = math.sin(math.min(fly, 1) * math.pi / 2)
    for key, lead in KIRIN_LEADS do
        local phase = stride + lead
        local a, lift = math.sin(phase), math.max(0, math.cos(phase)) ^ 1.2
        local landing = math.cos(phase)
        if moving > 0.5 and (s.lastLanding and s.lastLanding[key] or 0) > 0 and landing <= 0 and s.sparks[key] then
            s.sparks[key]:Emit(3)
        end
        s.lastLanding = s.lastLanding or {}
        s.lastLanding[key] = landing
        local sideSign = if string.sub(key, 2, 2) == "L" then 1 else -1
        local idle = 0.018 * math.sin(t * 0.8 + lead)
        local p1, p2, p3, p4
        if string.sub(key, 1, 1) == "F" then
            p1 = idle + moving * (0.52 * a + 0.05) + tuck * (0.72 + 0.14 * a) * (1 - moving) + rear * (if sideSign > 0 then 0.78 + 0.22 * math.sin(t * 11) else 0.36 - 0.22 * math.sin(t * 11)) + slam * 0.2
            p2 = moving * 0.08 + tuck * 0.18 + rear * 0.16
            p3 = -moving * (1.3 * lift + 0.08) - tuck * 1.45 - rear * (if sideSign > 0 then 1.55 else 1.1) - slam * 0.1
            p4 = -moving * (0.5 * lift + 0.08) - tuck * 0.62 - rear * 0.6
            if key == "FR" then
                p1 += 0.62 * paw
                p3 -= 1.25 * paw
                p4 -= 0.55 * paw
            end
        else
            p1 = idle + moving * (0.44 * a - 0.08) + tuck * (-0.5 + 0.12 * a) * (1 - moving) - rear * 0.8 - slam * 0.12
            p2 = moving * 0.64 * lift + tuck * 0.2 + rear * 0.12
            p3 = -moving * (0.95 * lift + 0.06) - tuck * 0.32 - rear * 0.16
            p4 = -moving * 0.46 * lift - tuck * 0.32 + rear * 0.14
        end
        pose(m["Leg" .. key .. "1"], CFrame.Angles(p1, 0, 0))
        pose(m["Leg" .. key .. "2"], CFrame.Angles(p2, 0, 0))
        pose(m["Leg" .. key .. "3"], CFrame.Angles(p3, 0, 0))
        pose(m["Hoof" .. key], CFrame.Angles(p4, 0, 0))
    end

    -- it leans into turns
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.28, 0.28) - (s.bank or 0)) * math.min(1, dt * 3)

    local hover = 0.1 + 0.012 * math.sin(t * 1.5) + moving * 0.034 * math.sin(2 * stride + 0.4) + 0.05 * fly + 0.015 * math.sin(t * 2.1) * fly + 0.2 * rear
    pose(m.Body, CFrame.new(0, hover * u, 0) * CFrame.Angles(0.006 * math.sin(t * 1.5) + moving * (0.045 * rock - 0.02) + 0.13 * fly + 0.84 * rear - 0.1 * slam, 0.02 * math.sin(t * 0.31), s.bank))
    pose(m.Hips, CFrame.Angles(-moving * 0.06 * math.sin(stride + 1.7) + 0.05 * tuck, 0.03 * math.sin(t * 0.5) * (1 - pace), 0))
    pose(m.Chest, CFrame.Angles(moving * 0.03 * math.sin(stride - 0.4), 0, 0.012 * math.sin(t * 0.8)))

    -- head and neck: its gaze wanders, its head follows slowly; low and reaching at speed
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 1.6 + math.random() * 3.2
        s.gazeTo = (math.random() - 0.5) * 0.7
    end
    local calm = (1 - pace * 0.75) * (1 - nova)
    s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * calm - (s.gaze or 0)) * math.min(1, dt * 2.2)
    local nod = moving * 0.055 * math.sin(2 * stride - 0.5)
    pose(m.Neck1, CFrame.Angles(0.012 * math.sin(t * 1.5 - 0.5) - 0.2 * moving - 0.05 * fly - 0.24 * rear + 0.14 * slam + 0.05 * toss - 0.1 * paw, s.gaze * 0.28, s.bank * 0.5))
    pose(m.Neck2, CFrame.Angles(0.012 * math.sin(t * 1.5 - 1) - 0.1 * moving - 0.17 * rear - 0.34 * slam + 0.08 * toss - 0.07 * paw + nod, s.gaze * 0.36, 0))
    pose(m.Head, CFrame.Angles(0.012 * math.sin(t * 1.5 - 1.5) + 0.22 * moving + 0.08 * fly + 0.4 * rear + 0.06 * slam - 0.2 * toss + 0.12 * paw - nod * 0.6, s.gaze * 0.5, 0.05 * math.sin(t * 0.37) * calm))
    pose(m.Jaw, CFrame.Angles(-(0.16 * rear + 0.24 * slam + 0.1 * math.max(0, toss)), 0, 0))

    -- the eye: blinks slowly, turns ahead of the head; a sterner lid when it runs
    s.nextBlink = s.nextBlink or t + 2
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.2
        if a >= 1 then
            s.nextBlink = t + (if math.random() < 0.15 then 0.14 else 2.8 + math.random() * 4)
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local rest = math.rad(4 + 7 * pace - 6 * rear)
    local upper = rest + (KIRIN_BLINK_UPPER - rest) * math.max(blink, slam * 0.25)
    local lower = KIRIN_BLINK_LOWER * blink
    for _, side in { "L", "R" } do
        pose(m["Eye" .. side], CFrame.Angles(0, s.gaze * 0.6, 0))
        pose(m["LidU" .. side], CFrame.fromAxisAngle(KIRIN_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(KIRIN_LID_HINGE[side], lower))
    end

    -- ears flick; the frills at its jaw trail
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 2.2
        local flick = math.max(0, math.sin(t * 0.9 + offset)) ^ 16
        pose(m["Ear" .. side], CFrame.Angles(-0.14 * pace - 0.3 * rear + 0.4 * flick * (1 - pace), sign * 0.12 * flick, 0))
        pose(m["Frill" .. side], CFrame.Angles(0.07 * math.sin(t * 2.4 + offset) - 0.16 * pace, sign * (0.05 * math.sin(t * 1.5 + offset) - 0.1 * pace), 0))
    end

    -- the mane on its wind: heavier at rest, streaming out as it runs, lifting up and back as it rears
    local gust = 0.5 + 0.5 * math.sin(t * 0.47)
    local waveSpeed = 2.1 + 4.2 * pace
    for cluster, phase in KIRIN_MANE do
        local base = 0.16 * (1 - pace) + 0.2 * moving - 0.12 * fly - 0.36 * rear + 0.2 * slam -- (a neck reaching forward would throw it straight up)
        local wave = (0.06 + 0.05 * gust + 0.07 * pace)
        pose(m["Mane" .. cluster .. "1"], CFrame.Angles(base + wave * math.sin(t * waveSpeed - phase), 0.05 * math.sin(t * 1.3 - phase), 0))
        pose(m["Mane" .. cluster .. "2"], CFrame.Angles(base * 0.8 + 1.5 * wave * math.sin(t * waveSpeed - phase - 1.1), 0.09 * math.sin(t * 1.3 - phase - 1), 0))
    end

    -- the tail: a slow swish at rest, a long wave at speed; it clamps down as it rears
    local droop = 0.045 * (1 - pace) - 0.02 * fly + 0.1 * rear
    for k = 1, 6 do
        local f = k / 6
        pose(m["Tail" .. k], CFrame.Angles(droop + (0.025 + 0.05 * pace) * math.sin(t * (1.7 + 3 * pace) - k * 0.65),
            (0.03 + 0.05 * f) * (1 + 0.5 * pace) * math.sin(t * (1.05 + 1.6 * pace) - k * 0.55), 0))
    end
    pose(m.TailTip, CFrame.Angles(0, 0.1 * math.sin(t * 2.4), 0))

    -- lightning flickers in the mane: a few quick stutters every so often, oftener at speed, without pause during its special
    s.nextFlicker = s.nextFlicker or t + 1
    if t >= s.nextFlicker then
        s.flickerUntil = t + 0.16 + math.random() * 0.22
        s.nextFlicker = t + (1.1 + 2.6 * math.random()) * (1 - 0.6 * pace)
    end
    local bolts = rig.parts.Bolts
    if bolts then
        local lit = nova > 0.3 or (t < (s.flickerUntil or 0) and math.sin(t * 73) > -0.35)
        bolts.Transparency = if lit then 0 else 1
    end
end

local LION_LEGS = { LegFL = 0, LegBR = 0.15, LegFR = math.pi, LegBL = math.pi + 0.15 }
local function animateLion(rig, s, moving, fly, nova)
    local m, u, t = rig.motors, rig.unit, s.time
    local pace = math.max(moving, fly)
    s.stride = (s.stride or 0) + rig.deltaTime * (0.9 + 4.6 * pace)
    local stride = s.stride
    local breathe = math.sin(t * 0.85)
    s.roar = if rig.nova then (s.roar or 0) + rig.deltaTime else 0
    local rise = smoothstep(0.0, 0.45, s.roar) * (1 - smoothstep(1.7, 2.4, s.roar))
    local open = smoothstep(0.4, 0.75, s.roar) * (1 - smoothstep(1.5, 2.1, s.roar)) * math.min(1, nova * 3)

    pose(m.Body, CFrame.new(0, (0.012 * breathe + 0.03 * math.abs(math.sin(stride)) * pace + 0.04 * rise) * u, 0)
        * CFrame.Angles(0.012 * breathe - 0.08 * rise + 0.02 * math.sin(stride * 2) * pace, 0, 0.025 * math.sin(stride) * pace))
    local gaze = 0.38 * math.sin(t * 0.17) ^ 3 * (1 - pace) * (1 - rise)
    pose(m.Head, CFrame.Angles(0.03 * math.sin(t * 0.6 + 1) + 0.06 * math.sin(stride * 2) * pace - 0.3 * rise, gaze, 0.03 * math.sin(t * 0.31) * (1 - pace)))
    if m.Jaw then
        pose(m.Jaw, CFrame.Angles(0.012 * math.max(0, breathe) + 0.5 * open, 0, 0))
    end

    for name, phase in LION_LEGS do
        local front = string.sub(name, 4, 4) == "F"
        local swing = 0.42 * math.sin(stride + phase) * pace
        local brace = if front then -0.12 * rise else 0.1 * rise
        pose(m[name], CFrame.Angles(swing + brace + (if front then -0.5 else 0.6) * fly, 0, 0))
    end

    local flick = math.max(0, math.sin(t * 0.7)) ^ 10
    pose(m.Tail, CFrame.Angles(0.06 * math.sin(t * 0.5) + 0.1 * pace - 0.15 * rise, 0.22 * math.sin(t * 0.42), 0))
    pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 0.5 - 0.8) + 0.3 * flick, 0.3 * math.sin(t * 0.42 - 1) + 0.25 * flick, 0.1 * math.sin(t * 0.9)))
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

PetRig.Profiles.MagmaCub = {
    Joints = {
        Body = "Root",
        Head = "Body",
        ArmL = "Body",
        ArmR = "Body",
        LegL = "Body",
        LegR = "Body",
        Tail = "Body",
    },
    GlowColors = {
        ffce61 = Color3.fromRGB(255, 150, 20),
        ff9b30 = Color3.fromRGB(255, 85, 0),
        ffad27 = Color3.fromRGB(255, 110, 0),
        ffda61 = Color3.fromRGB(255, 175, 30),
        ed6119 = Color3.fromRGB(220, 50, 0),
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "ArmL_Paw", "ArmR_Paw", "Head_Vent" },
        Blast = "MagmaPop",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 140, 30),
        Amber = Color3.fromRGB(40, 30, 28),
        Orange = Color3.fromRGB(255, 80, 10),
        Sun = Color3.fromRGB(255, 200, 90),
        Ivory = Color3.fromRGB(255, 235, 200),
    },
    Animate = animateCub,
}

PetRig.Profiles.AzureSkyDragon = {
    Joints = {
        Body = "Root",
        Neck = "Body",
        Head = "Neck",
        WingL = "Body",
        WingR = "Body",
        WingL2 = "WingL",
        WingR2 = "WingR",
        LegL = "Body",
        LegR = "Body",
        ArmL = "Body",
        ArmR = "Body",
        Tail = "Body",
        Tail2 = "Tail",
    },
    SeeThroughGlow = { ["95daff"] = 0.4, a0e7ff = 0.15 },
    GlowColors = {
        ["95daff"] = Color3.fromRGB(40, 150, 255),
        a0e7ff = Color3.fromRGB(30, 180, 255),
        ["27e1ff"] = Color3.fromRGB(0, 200, 255),
        ["3061ed"] = Color3.fromRGB(20, 60, 230),
        ["9559f9"] = Color3.fromRGB(110, 40, 255),
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "LegL_Foot", "LegR_Foot", "Tail2_Fan" },
        Trail = { "WingL2_Tip", "WingR2_Tip" },
        Blast = "Skyburst",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(70, 170, 255),
        Amber = Color3.fromRGB(20, 50, 140),
        Orange = Color3.fromRGB(120, 220, 255),
        Sun = Color3.fromRGB(210, 240, 255),
        Ivory = Color3.fromRGB(240, 250, 255),
    },
    Animate = animateSkyDragon,
}

PetRig.Profiles.SpiritCrane = {
    Joints = {
        Body = "Root",
        Neck = "Body",
        Head = "Neck",
        WingL = "Body",
        WingR = "Body",
        LegL = "Body",
        LegR = "Body",
        Tail = "Body",
    },
    GlowColors = {
        a0f3f1 = Color3.fromRGB(30, 215, 205),
        ["95eded"] = Color3.fromRGB(20, 195, 210),
        edce76 = Color3.fromRGB(235, 160, 30),
        ["3fe1dd"] = Color3.fromRGB(0, 185, 175),
    },
    Effects = {
        Motes = "Body",
        Light = "Body",
        Pulse = "Body",
        Burst = "Body",
        Sparks = { "Head_Crown", "Tail_Tip" },
        Trail = { "WingL_Tip", "WingR_Tip" },
        Blast = "HaloAscension",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(40, 210, 200),
        Amber = Color3.fromRGB(30, 55, 70),
        Orange = Color3.fromRGB(230, 170, 60),
        Sun = Color3.fromRGB(225, 245, 245),
        Ivory = Color3.fromRGB(250, 250, 245),
    },
    Animate = animateCrane,
}

PetRig.Profiles.CloudSheep = {
    Skinned = true,
    SkinTint = Color3.fromRGB(255, 240, 216), -- the game's light pushes its slate face to royal blue: this brings it back (seen in Studio)
    Bones = {
        "Body", "Head", "WoolCap", "Tail", "WoolTop", "WoolBack", "WoolChest", "WoolL", "WoolR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR", "Smile", "Mouth",
        "LegFL1", "LegFL2", "HoofFL", "LegFR1", "LegFR2", "HoofFR", "LegBL1", "LegBL2", "HoofBL", "LegBR1", "LegBR2", "HoofBR",
    },
    Points = { "Tail" },
    GlowColors = {
        ["f0ead8"] = Color3.fromRGB(170, 165, 150), -- the catch-light in its eye
    },
    Effects = {
        Burst = "Body",
        Trail = "Tail",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "CloudBloom",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(190, 215, 240),
        Amber = Color3.fromRGB(150, 150, 190),
        Orange = Color3.fromRGB(185, 195, 235),
        Sun = Color3.fromRGB(240, 248, 255),
        Ivory = Color3.fromRGB(250, 250, 255),
    },
    Animate = animateCloudSheep,
}

PetRig.Profiles.JadeWyrmTurtle = {
    Skinned = true,
    Bones = {
        "Body", "Shell", "Neck1", "Neck2", "Neck3", "Neck4", "Head", "Jaw", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "FrillL", "FrillR",
        "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip",
        "LegFL1", "LegFL2", "FootFL", "LegFR1", "LegFR2", "FootFR", "LegBL1", "LegBL2", "FootBL", "LegBR1", "LegBR2", "FootBR",
        "Plum1", "Plum2", "PadA", "PadB", "PadC", "Pine1", "PineA", "PineB", "PineC",
    },
    Points = { "FootFR", "TailTip", "PadA", "PadB", "PadC" },
    GlowColors = {
        ["24c0a4"] = Color3.fromRGB(26, 170, 150), -- the spring
        ["f0ead8"] = Color3.fromRGB(170, 165, 150), -- the catch-light in its eye
    },
    Effects = {
        Pulse = "Spring",
        Burst = "Body",
        Trail = "TailTip",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "BetweenSteps",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(110, 225, 180),
        Amber = Color3.fromRGB(235, 190, 110),
        Orange = Color3.fromRGB(245, 170, 195),
        Sun = Color3.fromRGB(225, 250, 235),
        Ivory = Color3.fromRGB(250, 240, 225),
    },
    Animate = animateJadeWyrmTurtle,
}

PetRig.Profiles.NebulaOwl = {
    Skinned = true,
    Bones = {
        "Body", "Chest", "Head", "BeakLow", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "BrowL", "BrowR", "TuftL", "TuftR",
        "WingL1", "WingL2", "WingL3", "WingPL", "WingR1", "WingR2", "WingR3", "WingPR", "Tail", "TailL", "TailR", "LegL", "FootL", "LegR", "FootR",
    },
    Points = { "WingPL", "WingPR" },
    GlowColors = {
        ["d6b4ff"] = Color3.fromRGB(176, 122, 255), -- the new stars in its wings
        ["f0ead8"] = Color3.fromRGB(190, 182, 160), -- the catch-lights in its eyes
    },
    Effects = {
        Burst = "Body",
        Trail = { "WingPL", "WingPR" },
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "StarsNotYetBorn",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(176, 122, 255),
        Amber = Color3.fromRGB(240, 120, 200),
        Orange = Color3.fromRGB(120, 76, 230),
        Sun = Color3.fromRGB(235, 220, 255),
        Ivory = Color3.fromRGB(245, 240, 255),
    },
    Animate = animateNebulaOwl,
}

PetRig.Profiles.CosmicJellyfish = {
    Skinned = true,
    SeeThrough = { Glass = 0.5 }, -- its bell: the nebula shows through it, and the sky through the rest
    Bones = jellyBones(),
    Points = { "Apex" },
    GlowColors = {
        ["ffb04a"] = Color3.fromRGB(255, 118, 26), -- the four horseshoes (warm gold: paler goes to lemon as Neon)
    },
    Effects = {
        Burst = "Body",
        Blast = "RollingNebula",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(245, 120, 180),
        Amber = Color3.fromRGB(255, 170, 84),
        Orange = Color3.fromRGB(128, 84, 226),
        Sun = Color3.fromRGB(255, 225, 235),
        Ivory = Color3.fromRGB(250, 240, 248),
    },
    Animate = animateCosmicJellyfish,
}

PetRig.Profiles.StarfallFox = {
    Skinned = true,
    Bones = {
        "Body", "Hips", "Chest", "Neck", "Head", "Jaw", "Mouth", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR",
        "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip",
        "LegFL1", "LegFL2", "PawFL", "LegFR1", "LegFR2", "PawFR", "LegBL1", "LegBL2", "PawBL", "LegBR1", "LegBR2", "PawBR",
    },
    Points = { "TailTip", "Mouth", "PawFL", "PawFR" },
    GlowColors = {
        ["f6ecd6"] = Color3.fromRGB(190, 182, 160), -- the catch-lights in its eyes (full white blooms over the whole eye)
    },
    Effects = {
        Burst = "Body",
        Trail = "TailTip",
        TrailWidth = 0.05, -- flying, its white brush draws a comet's thin tail
        TrailTaper = true,
        Blast = "StarInItsTeeth",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(248, 192, 92),
        Amber = Color3.fromRGB(214, 120, 28),
        Orange = Color3.fromRGB(120, 140, 255),
        Sun = Color3.fromRGB(255, 240, 200),
        Ivory = Color3.fromRGB(245, 245, 255),
    },
    Animate = animateStarfallFox,
}

PetRig.Profiles.LanternWarden = {
    Skinned = true,
    Bones = {
        "Body", "Chest", "Neck", "Head", "Hat", "EyeL", "EyeR", "Crook1", "Crook2", "Crook3", "Chain1", "Chain2", "Lantern", "Flame",
        "MidF", "MidL", "MidB", "MidR", "LowF", "LowL", "LowB", "LowR",
        "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR", "LegL1", "LegL2", "LegL3", "FootL", "LegR1", "LegR2", "LegR3", "FootR",
    },
    Points = { "Flame" },
    GlowColors = {
        ["ffc070"] = Color3.fromRGB(255, 118, 26), -- the lantern's paper (paler goes to lemon as Neon)
        ["ffe6b0"] = Color3.fromRGB(190, 170, 130), -- the catch-lights behind its mask
    },
    Effects = {
        Burst = "Body",
        Trail = "Flame",
        TrailWidth = 0.06, -- flying, the lantern draws a thin line of light behind it
        TrailTaper = true,
        Blast = "TheLongWayRound",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 176, 70),
        Amber = Color3.fromRGB(255, 130, 50),
        Orange = Color3.fromRGB(214, 90, 30),
        Sun = Color3.fromRGB(255, 225, 160),
        Ivory = Color3.fromRGB(245, 235, 210),
    },
    Animate = animateLanternWarden,
}

PetRig.Profiles.DreamMoth = {
    Skinned = true,
    Bones = {
        "Body", "Abd1", "Abd2", "Abd3", "Head", "PupilL", "PupilR", "AntL1", "AntL2", "AntR1", "AntR2",
        "ForeL1", "ForeL2", "HindL1", "HindL2", "ForeR1", "ForeR2", "HindR1", "HindR2",
        "LegFL1", "LegFL2", "LegML1", "LegML2", "LegBL1", "LegBL2", "LegFR1", "LegFR2", "LegMR1", "LegMR2", "LegBR1", "LegBR2",
        "Tongue1", "Tongue2", "Tongue3", "Tongue4", "Tongue5", "Tongue6", "Tongue7", "Tongue8", "Tongue9", "Tongue10", "Tongue11", "Tongue12",
    },
    Points = { "Tongue12", "PupilL", "PupilR", "Abd3" },
    Effects = {
        Burst = "Body",
        Trail = "Abd3",
        TrailWidth = 0.04, -- flying, a faint thread of scale dust behind it
        TrailTaper = true,
        Blast = "AForgottenDream",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(236, 190, 255),
        Amber = Color3.fromRGB(255, 196, 228),
        Orange = Color3.fromRGB(196, 168, 255),
        Sun = Color3.fromRGB(255, 236, 250),
        Ivory = Color3.fromRGB(255, 250, 255),
    },
    Animate = animateDreamMoth,
}

PetRig.Profiles.PrismArmadillo = {
    Skinned = true,
    Bones = {
        "Body", "Front", "Neck", "Head", "Mid", "Back", "Pelvis", "Tail1", "Tail2", "Tail3", "EarL", "EarR", "CheekL", "CheekR",
        "LegFL1", "LegFL2", "PawFL", "LegFR1", "LegFR2", "PawFR", "LegBL1", "LegBL2", "PawBL", "LegBR1", "LegBR2", "PawBR",
    },
    Points = { "Body" },
    GlowColors = {
        ["ff7ab4"] = Color3.fromRGB(255, 160, 200), -- the crest prisms: their colours are set each frame, these are only where they start
        ["ffc864"] = Color3.fromRGB(255, 220, 150),
        ["8cf0a0"] = Color3.fromRGB(160, 240, 180),
        ["78c8ff"] = Color3.fromRGB(150, 210, 255),
        ["a08cff"] = Color3.fromRGB(180, 160, 255),
        ["f08cff"] = Color3.fromRGB(240, 160, 255),
    },
    Effects = {
        Burst = "Body",
        Blast = "EveryColour",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(200, 170, 255),
        Amber = Color3.fromRGB(255, 180, 220),
        Orange = Color3.fromRGB(150, 210, 255),
        Sun = Color3.fromRGB(245, 240, 255),
        Ivory = Color3.fromRGB(250, 248, 255),
    },
    Animate = animatePrismArmadillo,
}

PetRig.Profiles.CrystalSnail = {
    Skinned = true,
    Bones = {
        "Body", "Tail1", "Tail2", "TailTip", "Front", "Head", "Shell",
        "StalkL1", "StalkL2", "StalkL3", "StalkR1", "StalkR2", "StalkR3",
    },
    Points = { "TailTip", "Shell" },
    GlowColors = {
        ["8ff5dc"] = Color3.fromRGB(70, 225, 190), -- the glowing crystal in each cluster (set each frame; paler goes to white as Neon)
    },
    Effects = {
        Burst = "Body",
        Blast = "AHundredYears",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(110, 230, 200),
        Amber = Color3.fromRGB(150, 240, 220),
        Orange = Color3.fromRGB(60, 170, 160),
        Sun = Color3.fromRGB(210, 255, 240),
        Ivory = Color3.fromRGB(235, 255, 250),
    },
    Animate = animateCrystalSnail,
}

PetRig.Profiles.GoldenManeLion = {
    Joints = {
        Body = "Root",
        Head = "Body",
        Jaw = "Head",
        LegFL = "Body",
        LegFR = "Body",
        LegBL = "Body",
        LegBR = "Body",
        Tail = "Body",
        Tail2 = "Tail",
    },
    GlowColors = {
        ffce61 = Color3.fromRGB(255, 140, 10),
        ffce59 = Color3.fromRGB(255, 150, 20),
    },
    Effects = {
        Motes = "Head",
        Light = "Body",
        Pulse = "Head",
        Burst = "Head",
        Sparks = { "LegFL_Paw", "LegFR_Paw", "Head_Crown" },
        Trail = "Tail2_Tuft",
        Blast = "SovereignRoar",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 180, 50),
        Amber = Color3.fromRGB(120, 60, 20),
        Orange = Color3.fromRGB(255, 120, 20),
        Sun = Color3.fromRGB(255, 225, 140),
        Ivory = Color3.fromRGB(255, 240, 210),
    },
    Animate = animateLion,
}

PetRig.NOVA_TIME = 2.6
local NOVA_BURST_AT = 0.42
PetRig.NOVA_BURST = NOVA_BURST_AT

PetRig.Profiles.WindSprite = {
    Skinned = true,
    Bones = {
        "Body", "Head", "Crest1", "Crest2", "EarL", "EarR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "BrowL", "BrowR", "CheekL", "CheekR",
        "Smile", "Blow", "ArmL1", "ArmL2", "ArmR1", "ArmR2", "WingL", "WingR", "WingMidL", "WingMidR", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "Tail7", "TailTip", "Tassel",
    },
    Points = { "TailTip", "WingTipL", "WingTipR", "Blow" },
    SkinTint = Color3.fromRGB(238, 250, 228), -- its pale maps run a little hot under the game's light
    GlowColors = {
        ["1eebb4"] = Color3.fromRGB(30, 235, 180),
        ["ffffff"] = Color3.fromRGB(165, 190, 190), -- catch-lights: full white blooms over the whole eye
    },
    Effects = {
        Motes = "Body", -- no Light: a light inside a body this pale washes all its shading out
        Pulse = "Channels",
        Burst = "Body",
        Sparks = { "WingTipL", "WingTipR" },
        Trail = "TailTip",
        TrailWidth = 0.07, -- a thread of wind off the tail's tip, not a plank
        TrailTaper = true,
        Blast = "TuggingGale",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(60, 235, 190),
        Amber = Color3.fromRGB(240, 110, 90),
        Orange = Color3.fromRGB(25, 190, 170),
        Sun = Color3.fromRGB(170, 255, 230),
        Ivory = Color3.fromRGB(235, 255, 250),
    },
    Animate = animateWindSprite,
}

PetRig.Profiles.StormhornKirin = {
    Skinned = true,
    SkinTint = Color3.fromRGB(250, 230, 198), -- the game's light pushes its slate to a royal blue: this brings the storm back (seen in Studio)
    Bones = {
        "Body", "Hips", "Chest", "Neck1", "Neck2", "Head", "Jaw", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR", "FrillL", "FrillR",
        "ManeA1", "ManeA2", "ManeB1", "ManeB2", "ManeC1", "ManeC2", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip",
        "LegFL1", "LegFL2", "LegFL3", "HoofFL", "LegFR1", "LegFR2", "LegFR3", "HoofFR", "LegBL1", "LegBL2", "LegBL3", "HoofBL", "LegBR1", "LegBR2", "LegBR3", "HoofBR",
    },
    Points = { "HoofFL", "HoofFR", "HoofBL", "HoofBR", "TailTip", "HornTip" },
    GlowColors = {
        ["4fb4ff"] = Color3.fromRGB(30, 125, 255),
        ["2a9dff"] = Color3.fromRGB(20, 110, 255),
        ["a8e0ff"] = Color3.fromRGB(120, 200, 255),
        ["f0ead8"] = Color3.fromRGB(170, 165, 150), -- the catch-light in its eye
    },
    Effects = {
        Pulse = "Horn",
        Burst = "Body",
        Sparks = { "HoofFL", "HoofFR", "HoofBL", "HoofBR" },
        Trail = "TailTip",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "ThunderAnswers",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(90, 170, 255),
        Amber = Color3.fromRGB(255, 190, 90),
        Orange = Color3.fromRGB(60, 110, 240),
        Sun = Color3.fromRGB(190, 230, 255),
        Ivory = Color3.fromRGB(235, 245, 255),
    },
    Animate = animateStormhornKirin,
}

PetRig.Profiles.GalaxyManta = {
    Skinned = true,
    Bones = {
        "Body", "Head", "EyeL", "EyeR", "Smile", "Mouth", "SpiralInner", "SpiralMid", "SpiralOuter", "Orbit",
        "HornL1", "HornL2", "HornL3", "HornR1", "HornR2", "HornR3",
        "WingL1", "WingL2", "WingL3", "WingL4", "WingR1", "WingR2", "WingR3", "WingR4",
        "WingRearL1", "WingRearL2", "WingRearL3", "WingRearL4", "WingRearR1", "WingRearR2", "WingRearR3", "WingRearR4",
        "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "Tail7", "Tail8", "TailTip",
    },
    Points = { "TailTip", "WingL4", "WingR4", "SpiralInner" },
    GlowColors = {
        ["8a6bff"] = Color3.fromRGB(104, 62, 255),
        ["ffc878"] = Color3.fromRGB(255, 118, 26), -- Neon shifts hard here: 255,92,16 reads orange, 255,142,44 lemon (seen in Studio)
        ["e6e0ff"] = Color3.fromRGB(176, 160, 255),
        ["d8d0f0"] = Color3.fromRGB(170, 165, 200), -- the catch-light in its eye: full white blooms over so small an eye
    },
    Effects = {
        Motes = "Body",
        Pulse = "Ember",
        Burst = "Body",
        Sparks = { "WingL4", "WingR4" },
        Trail = "TailTip",
        TrailWidth = 0.05,
        TrailTaper = true,
        Blast = "TurningOfTheHeavens",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(140, 100, 255),
        Amber = Color3.fromRGB(255, 180, 90),
        Orange = Color3.fromRGB(216, 72, 178),
        Sun = Color3.fromRGB(255, 214, 140),
        Ivory = Color3.fromRGB(235, 232, 255),
    },
    Animate = animateGalaxyManta,
}

function PetRig.isRigged(petId, template)
    local profile = PetRig.Profiles[petId]
    if not profile then
        return false
    end
    if profile.Skinned then
        return template:FindFirstChildWhichIsA("Bone", true) ~= nil
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

    local trailPoints = if type(effects.Trail) == "table" then effects.Trail else { effects.Trail }
    for _, pointName in trailPoints do
        local tip = rig.points[pointName]
        if not tip then
            continue
        end
        local upper = Instance.new("Attachment")
        upper.Name = "TrailTop"
        upper.CFrame = tip.CFrame * CFrame.new(0, (effects.TrailWidth or 0.25) * u, 0)
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
        if effects.TrailTaper then
            trail.WidthScale = NumberSequence.new(1, 0)
        end
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
        part.Transparency = (hex and profile.SeeThroughGlow and profile.SeeThroughGlow[string.lower(hex)]) or 0
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

-- A pet that is one skin on a skeleton. Its joints are Bones; rig.motors holds a stand-in for each, so animations pose it exactly as they
-- pose a jointed pet: a pose in the pet's axes, turned into the bone's own (a bone may rest at any angle): rest:Inverse() * pose * rest.
-- rig.unit keeps effects the size they are on other pets; rig.meters is studs per metre as built, what its own poses are written in.
function PetRig.buildSkinned(model, rootPart, template, petId, turn, scale, length)
    local profile = PetRig.Profiles[petId]
    local prefix = petId .. "_"
    local rig = {
        profile = profile,
        model = model,
        rootPart = rootPart,
        unit = length / 3,
        meters = scale,
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

    local skin = template:Clone()
    skin.Name = "Skin"
    local box = skin:GetBoundingBox()
    local bones = {}
    for _, d in skin:GetDescendants() do
        if d:IsA("Bone") then
            bones[d.Name] = d
            d.CFrame = d.CFrame.Rotation + d.CFrame.Position * scale
        elseif d:IsA("BasePart") then
            local from = d.CFrame
            d.Size *= scale
            d.CFrame = turn * (from.Rotation + (from.Position - box.Position) * scale)
            prepare(d)
            local name = if string.sub(d.Name, 1, #prefix) == prefix then string.sub(d.Name, #prefix + 1) else d.Name
            local owner, hex = string.match(name, "^(.+)_Glow_(%x%x%x%x%x%x)$")
            if hex then
                d.Color = (profile.GlowColors and profile.GlowColors[string.lower(hex)]) or Color3.fromHex(hex)
                d.Material = Enum.Material.Neon
                if d:IsA("MeshPart") then
                    d.TextureID = ""
                end
                rig.parts[owner] = d
                if owner == profile.Effects.Pulse then
                    table.insert(rig.pulseGlow, { part = d, color = d.Color })
                end
            elseif d.Name == "RootPart" then
                d.Transparency = 1 -- the importer's holder of the bones
            else
                d.Material = Enum.Material.SmoothPlastic
                rig.parts[name] = d
                if profile.SeeThrough and profile.SeeThrough[name] then
                    d.Transparency = profile.SeeThrough[name]
                end
                local look = d:FindFirstChildOfClass("SurfaceAppearance")
                if look and profile.SkinTint then
                    look.Color = profile.SkinTint
                end
            end
            -- a Weld, not a WeldConstraint: its offset is fixed now, so the root can be placed before the model is in the world
            local joint = Instance.new("Weld")
            joint.Part0 = rootPart
            joint.Part1 = d
            joint.C0 = rootPart.CFrame:ToObjectSpace(d.CFrame)
            joint.Parent = d
        end
    end
    -- Each mesh needs a Motor6D from the part that holds the bones, as the importer made them: without one the skin stays in its bind pose,
    -- whatever the bones do (seen in Studio, 2026-11-05).
    local holder = bones.Root and bones.Root.Parent
    for _, d in skin:GetChildren() do
        if d:IsA("MeshPart") and holder then
            local motor = Instance.new("Motor6D")
            motor.Name = d.Name .. "Motor6D"
            motor.Part0 = holder
            motor.Part1 = d
            motor.C0 = holder.CFrame:ToObjectSpace(d.CFrame)
            motor.Parent = d
        end
    end
    for _, child in skin:GetChildren() do
        child.Parent = model
    end
    skin:Destroy()

    local function worldOf(bone)
        local cframe = bone.CFrame
        local up = bone.Parent
        while up:IsA("Bone") do
            cframe = up.CFrame * cframe
            up = up.Parent
        end
        return up.CFrame * cframe
    end
    for _, name in profile.Bones do
        local bone = bones[name]
        if bone then
            local rest = worldOf(bone).Rotation
            local restInverse = rest:Inverse()
            rig.motors[name] = setmetatable({}, {
                __newindex = function(_, _, cframe)
                    bone.Transform = restInverse * cframe * rest
                end,
            })
        else
            warn("PetRig: " .. petId .. " has no bone " .. name)
            rig.motors[name] = {} -- poses of a missing bone land nowhere
        end
    end
    for _, name in profile.Points do
        rig.points[name] = bones[name]
    end

    addEffects(rig)
    return rig
end

local Blasts = {}


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

function Blasts.MagmaPop(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local ground = origin - Vector3.new(0, 0.6 * u, 0) + fx.facing.LookVector * 0.5 * u

    local pool = neon(Vector3.new(0.08 * u, 0.6 * u, 0.6 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
    pool.Shape = Enum.PartType.Cylinder
    pool.Transparency = 0.15
    TweenService:Create(pool, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.new(0.06 * u, 2.6 * u, 2.6 * u) }):Play()
    TweenService:Create(pool, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.5), {
        Size = Vector3.new(0.02 * u, 3.4 * u, 3.4 * u),
        Transparency = 1,
    }):Play()

    for index = 1, 9 do
        local angle = index / 9 * 2 * math.pi + math.random() * 0.4
        local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
        local size = Vector3.new(0.3 + math.random() * 0.2, 0.5 + math.random() * 0.5, 0.3 + math.random() * 0.2) * u
        local spike = Instance.new("WedgePart")
        spike.Anchored = true
        spike.CanCollide = false
        spike.CanQuery = false
        spike.CanTouch = false
        spike.CastShadow = false
        spike.Material = Enum.Material.Basalt
        spike.Color = colors.Amber
        spike.Size = size
        local base = ground + out * (0.8 + math.random() * 0.6) * u
        spike.CFrame = CFrame.new(base - Vector3.new(0, size.Y, 0)) * CFrame.Angles(0, angle + math.pi / 2, 0) * CFrame.Angles(-0.3, 0, 0)
        spike.Parent = pool.Parent
        local up = TweenService:Create(spike, TweenInfo.new(0.16, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
            CFrame = spike.CFrame + Vector3.new(0, size.Y * 0.85, 0),
        })
        up.Completed:Once(function()
            TweenService:Create(spike, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.25), {
                CFrame = spike.CFrame - Vector3.new(0, size.Y, 0),
                Transparency = 1,
            }):Play()
        end)
        up:Play()
    end

    for index = 1, 12 do
        local angle = math.random() * 2 * math.pi
        local blob = neon(Vector3.one * (0.12 + math.random() * 0.1) * u, CFrame.new(ground + Vector3.new(0, 0.2 * u, 0)), if index % 3 == 0 then colors.Sun else colors.Gold)
        blob.Shape = Enum.PartType.Ball
        local peak = ground + Vector3.new(math.cos(angle), 0, math.sin(angle)) * (0.8 + math.random()) * u + Vector3.new(0, (1.4 + math.random()) * u, 0)
        local land = peak + Vector3.new(math.cos(angle), 0, math.sin(angle)) * 0.6 * u - Vector3.new(0, (1.8 + math.random()) * u, 0)
        local rise = TweenService:Create(blob, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(peak) })
        rise.Completed:Once(function()
            TweenService:Create(blob, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                CFrame = CFrame.new(land),
                Color = colors.Amber,
                Transparency = 1,
            }):Play()
        end)
        rise:Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Orange
    light.Range = 9 * u
    light.Brightness = 2
    light.Parent = pool
    TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(30)
    end
end

function Blasts.Skyburst(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local ground = origin - Vector3.new(0, 1.1 * u, 0)

    for index, delay in { 0, 0.12, 0.24 } do
        local ring = neon(Vector3.new(0.04 * u, 0.8 * u, 0.8 * u), CFrame.new(ground + Vector3.new(0, 0.05 * index * u, 0)) * CFrame.Angles(0, 0, math.pi / 2),
            if index == 2 then colors.Sun else colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.35
        TweenService:Create(ring, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, delay), {
            Size = Vector3.new(0.02 * u, (6 + 2 * index) * u, (6 + 2 * index) * u),
            Transparency = 1,
        }):Play()
    end

    for index = 1, 3 do
        local turns, rise = 1.4, (2.6 + 0.4 * index) * u
        local phase = index / 3 * 2 * math.pi
        for step = 0, 10 do
            local f = step / 10
            local angle = phase + turns * 2 * math.pi * f
            local radius = (1.4 - 0.7 * f) * u
            local here = ground + Vector3.new(math.cos(angle) * radius, rise * f, math.sin(angle) * radius)
            local tangent = Vector3.new(-math.sin(angle), 0.35, math.cos(angle)).Unit
            local streak = neon(Vector3.new(0.05, 0.05, 0.4) * u, CFrame.lookAt(here, here + tangent), if step % 2 == 0 then colors.Orange else colors.Sun)
            streak.Transparency = 1
            local appear = 0.04 * step + 0.05 * index
            TweenService:Create(streak, TweenInfo.new(0.12, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, appear), { Transparency = 0.25 }):Play()
            TweenService:Create(streak, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, appear + 0.3), {
                Transparency = 1,
                Size = Vector3.new(0.02, 0.02, 0.6) * u,
            }):Play()
        end
    end

    for index = 1, 10 do
        local angle = math.random() * 2 * math.pi
        local start = origin + Vector3.new(math.cos(angle), 0.3, math.sin(angle)) * 0.6 * u
        local shard = Instance.new("WedgePart")
        shard.Anchored = true
        shard.CanCollide = false
        shard.CanQuery = false
        shard.CanTouch = false
        shard.CastShadow = false
        shard.Material = Enum.Material.Glass
        shard.Transparency = 0.25
        shard.Color = colors.Orange
        shard.Size = Vector3.new(0.05, 0.2, 0.14) * u
        shard.CFrame = CFrame.new(start) * CFrame.Angles(math.random() * 6, math.random() * 6, 0)
        shard.Parent = fx.neon(Vector3.one * 0.01, CFrame.new(origin), colors.Sun).Parent
        TweenService:Create(shard, TweenInfo.new(1.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = CFrame.new(start + Vector3.new(math.cos(angle) * 2.2, 1.6 + math.random(), math.sin(angle) * 2.2) * u) * CFrame.Angles(math.random() * 6, math.random() * 6, 0),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 12 * u
    light.Brightness = 2
    light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(origin), colors.Gold)
    TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(25)
    end
end

function Blasts.HaloAscension(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local footL, footR, crownPoint = rig.points.LegL_Foot, rig.points.LegR_Foot, rig.points.Head_Crown
    local ground = if footL and footR then (footL.WorldPosition + footR.WorldPosition) / 2 else origin - Vector3.new(0, 1.2 * u, 0)
    local crown = if crownPoint then crownPoint.WorldPosition else origin + Vector3.new(0, 1.5 * u, 0)
    local height = crown.Y - ground.Y + 0.3 * u

    for index, delay in { 0, 0.15, 0.3 } do
        local color = if index == 1 then colors.Gold elseif index == 2 then colors.Sun else colors.Orange
        local radius = (1.3 - 0.15 * index) * u
        local segments = 20
        for step = 1, segments do
            local angle = step / segments * 2 * math.pi + index * 0.4
            local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
            local arc = 2 * math.pi * radius / segments
            local here = ground + out * radius
            local bead = neon(Vector3.new(0.05 * u, 0.05 * u, arc * 0.8), CFrame.lookAt(here, here + out:Cross(Vector3.yAxis)), color)
            bead.Transparency = 1
            local top = Vector3.new(crown.X, ground.Y + height, crown.Z) + out * 0.3 * u
            TweenService:Create(bead, TweenInfo.new(0.1, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, delay), { Transparency = 0.2 }):Play()
            TweenService:Create(bead, TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, 0, false, delay), {
                CFrame = CFrame.lookAt(top, top + out:Cross(Vector3.yAxis)),
                Size = Vector3.new(0.03 * u, 0.03 * u, arc * 0.25),
            }):Play()
            TweenService:Create(bead, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, delay + 0.7), { Transparency = 1 }):Play()
        end
    end

    local halo = neon(Vector3.one * 0.15 * u, CFrame.new(crown), colors.Sun)
    halo.Shape = Enum.PartType.Ball
    halo.Transparency = 1
    TweenService:Create(halo, TweenInfo.new(0.15, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.75), { Transparency = 0.3 }):Play()
    TweenService:Create(halo, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.85), {
        Size = Vector3.one * 1.6 * u,
        Transparency = 1,
    }):Play()

    for index = 1, 12 do
        local angle = index / 12 * 2 * math.pi + math.random() * 0.3
        local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
        local start = crown + Vector3.new(0, 0.2 * u, 0)
        local plume = neon(Vector3.new(0.07, 0.015, 0.26) * u, CFrame.lookAt(start, start + out), if index % 3 == 0 then colors.Orange else colors.Sun)
        plume.Transparency = 1
        local mesh = Instance.new("SpecialMesh")
        mesh.MeshType = Enum.MeshType.Sphere
        mesh.Parent = plume
        local drift = angle + 0.8
        local finish = start + Vector3.new(math.cos(drift), 0, math.sin(drift)) * (1.4 + math.random() * 0.6) * u - Vector3.new(0, (0.6 + math.random() * 0.5) * u, 0)
        TweenService:Create(plume, TweenInfo.new(0.1, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.8), { Transparency = 0.15 }):Play()
        TweenService:Create(plume, TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.Out, 0, false, 0.85), {
            CFrame = CFrame.lookAt(finish, finish + Vector3.new(math.cos(drift + 1.4), -0.3, math.sin(drift + 1.4))),
            Transparency = 1,
        }):Play()
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 12 * u
    light.Brightness = 2
    light.Parent = halo
    TweenService:Create(light, TweenInfo.new(1.3), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(25)
    end
end

-- One long sigh: soft cloud leaves its whole fleece, drifting out, thinning as it goes. Real smoke, not shapes, and nothing beyond the sheep itself.
function Blasts.CloudBloom(rig, fx)
    local u = rig.unit
    local holder = fx.neon(Vector3.new(1.3, 0.9, 1.5) * u, rig.rootPart.CFrame * CFrame.new(0, 0.25 * u, 0.2 * u), Color3.new(1, 1, 1))
    holder.Transparency = 1
    local puffs = Instance.new("ParticleEmitter")
    puffs.Texture = "rbxasset://textures/particles/smoke_main.dds"
    puffs.Rate = 0
    puffs.Speed = NumberRange.new(0.5 * u, 1.4 * u)
    puffs.SpreadAngle = Vector2.new(180, 180)
    puffs.Drag = 1.8
    puffs.Lifetime = NumberRange.new(1, 1.6)
    puffs.Rotation = NumberRange.new(0, 360)
    puffs.RotSpeed = NumberRange.new(-20, 20)
    puffs.Acceleration = Vector3.new(0, 0.2 * u, 0)
    puffs.LightEmission = 0
    puffs.LightInfluence = 0.75
    puffs.Color = ColorSequence.new(Color3.fromRGB(250, 252, 255))
    puffs.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * u), NumberSequenceKeypoint.new(1, 1.05 * u) })
    puffs.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.35, 0.62), NumberSequenceKeypoint.new(1, 1) })
    puffs.Parent = holder
    puffs:Emit(20)
end

-- The foot comes down: earth thrown out along the ground where it lands, chips of stone falling back, and the plum shaken, its petals coming down all at once. All of it in the world's light.
function Blasts.BetweenSteps(rig, fx)
    local u = rig.unit
    local foot = rig.points.FootFR
    local at = if foot then foot.TransformedWorldCFrame.Position - Vector3.new(0, 0.14 * rig.meters, 0) else fx.origin
    local holder = fx.neon(Vector3.new(0.4, 0.05, 0.4) * u, CFrame.new(at), Color3.new(1, 1, 1))
    holder.Transparency = 1

    local dust = Instance.new("ParticleEmitter")
    dust.Texture = "rbxassetid://82029518693714"
    dust.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    dust.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    dust.Rate = 0
    dust.EmissionDirection = Enum.NormalId.Top
    dust.SpreadAngle = Vector2.new(88, 88)
    dust.Speed = NumberRange.new(1.2 * u, 2.6 * u)
    dust.Drag = 3.4
    dust.Lifetime = NumberRange.new(0.8, 1.25)
    dust.Rotation = NumberRange.new(0, 360)
    dust.RotSpeed = NumberRange.new(-25, 25)
    dust.Acceleration = Vector3.new(0, -0.5 * u, 0)
    dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2 * u), NumberSequenceKeypoint.new(1, 0.68 * u) })
    dust.Color = ColorSequence.new(Color3.fromRGB(198, 182, 150), Color3.fromRGB(150, 150, 130))
    dust.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.5, 0.72), NumberSequenceKeypoint.new(1, 1) })
    dust.LightEmission = 0
    dust.LightInfluence = 0.85
    dust.Parent = holder
    dust:Emit(11)

    local chips = Instance.new("ParticleEmitter")
    chips.Texture = "rbxassetid://86117030913477"
    chips.Rate = 0
    chips.EmissionDirection = Enum.NormalId.Top
    chips.SpreadAngle = Vector2.new(55, 55)
    chips.Speed = NumberRange.new(1.4 * u, 3 * u)
    chips.Acceleration = Vector3.new(0, -13 * u, 0)
    chips.Lifetime = NumberRange.new(0.45, 0.8)
    chips.Rotation = NumberRange.new(0, 360)
    chips.RotSpeed = NumberRange.new(-420, 420)
    chips.Size = NumberSequence.new(0.042 * u, 0.028 * u)
    chips.LightEmission = 0
    chips.LightInfluence = 0.9
    chips.Parent = holder
    chips:Emit(10)

    for _, petals in rig.state.petals or {} do
        petals:Emit(16)
    end
end

-- The star lights where the gas gathered: its own painted flare, a thin shell of gas thrown off, and for a moment a little of its light on the owl. Nothing else in the sky changes.
function Blasts.StarsNotYetBorn(rig, fx)
    local s, metre = rig.state, rig.meters
    if s.gather then
        s.gather.Enabled = false -- (the grown seed ends on this same frame: its lifetime is the time to the burst)
        s.gather = nil
    end
    local at = s.starAt or fx.origin
    s.starAt = nil
    local holder = fx.neon(Vector3.one * 0.05, CFrame.new(at), Color3.new(1, 1, 1))
    holder.Transparency = 1

    local flare = Instance.new("ParticleEmitter")
    flare.Texture = "rbxassetid://95572555201628"
    flare.Rate = 0
    flare.Lifetime = NumberRange.new(1.35)
    flare.Speed = NumberRange.new(0.25 * metre)
    flare.EmissionDirection = Enum.NormalId.Top
    flare.SpreadAngle = Vector2.new(4, 4)
    flare.Drag = 0.5
    flare.Rotation = NumberRange.new(0, 360)
    flare.RotSpeed = NumberRange.new(-10, 10)
    flare.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * metre), NumberSequenceKeypoint.new(0.07, 2.3 * metre), NumberSequenceKeypoint.new(0.3, 1.25 * metre), NumberSequenceKeypoint.new(1, 0.5 * metre) })
    flare.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.12), NumberSequenceKeypoint.new(1, 1) })
    flare.LightEmission = 1
    flare.LightInfluence = 0
    flare.Parent = holder
    flare:Emit(1)

    local shell = Instance.new("ParticleEmitter")
    shell.Texture = "rbxassetid://13655845087"
    shell.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    shell.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    shell.Rate = 0
    shell.Lifetime = NumberRange.new(0.85)
    shell.Speed = NumberRange.new(0)
    shell.Rotation = NumberRange.new(0, 360)
    shell.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5 * metre), NumberSequenceKeypoint.new(1, 2.6 * metre) })
    shell.Color = ColorSequence.new(Color3.fromRGB(200, 150, 255), Color3.fromRGB(120, 76, 230))
    shell.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
    shell.LightEmission = 0.7
    shell.LightInfluence = 0
    shell.Parent = holder
    shell:Emit(1)

    local light = Instance.new("PointLight")
    light.Color = Color3.fromRGB(200, 160, 255)
    light.Range = 3.2 * metre
    light.Brightness = 2.4
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
end

-- The bell closes: a ring of glowing gas rolls off its rim and sinks away below it, as the ring a real jellyfish's beat leaves in the water, with a little of the nebula torn off round it. Nothing else in the scene changes.
function Blasts.RollingNebula(rig, fx)
    local metre = rig.meters
    local at = rig.rootPart.CFrame:PointToWorldSpace(Vector3.new(0, 0.42 * metre, 0))
    local holder = fx.neon(Vector3.new(1.3, 0.05, 1.3) * metre, CFrame.new(at), Color3.new(1, 1, 1))
    holder.Transparency = 1

    local ring = Instance.new("ParticleEmitter")
    ring.Texture = "rbxassetid://13655845087"
    ring.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    ring.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
    ring.EmissionDirection = Enum.NormalId.Bottom
    ring.Shape = Enum.ParticleEmitterShape.Box
    ring.Rate = 0
    ring.SpreadAngle = Vector2.new(0, 0)
    ring.Speed = NumberRange.new(1.1 * metre)
    ring.Drag = 1.4
    ring.Lifetime = NumberRange.new(1.35)
    ring.Rotation = NumberRange.new(0, 360)
    ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.3 * metre), NumberSequenceKeypoint.new(1, 3.4 * metre) })
    ring.Color = ColorSequence.new(Color3.fromRGB(255, 70, 170), Color3.fromRGB(110, 60, 240))
    ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.25), NumberSequenceKeypoint.new(1, 1) })
    ring.LightEmission = 1
    ring.LightInfluence = 0
    ring.Parent = holder
    ring:Emit(1)

    local torn = Instance.new("ParticleEmitter")
    torn.Texture = "rbxassetid://16867371255"
    torn.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    torn.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    torn.Shape = Enum.ParticleEmitterShape.Disc
    torn.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    torn.ShapePartial = 1
    torn.EmissionDirection = Enum.NormalId.Bottom
    torn.Rate = 0
    torn.SpreadAngle = Vector2.new(24, 24)
    torn.Speed = NumberRange.new(0.5 * metre, 1 * metre)
    torn.Drag = 2
    torn.Lifetime = NumberRange.new(0.8, 1.3)
    torn.Rotation = NumberRange.new(0, 360)
    torn.RotSpeed = NumberRange.new(-30, 30)
    torn.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07 * metre), NumberSequenceKeypoint.new(1, 0.27 * metre) })
    torn.Color = ColorSequence.new(Color3.fromRGB(255, 96, 170), Color3.fromRGB(128, 84, 226))
    torn.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(0.4, 0.4), NumberSequenceKeypoint.new(1, 1) })
    torn.LightEmission = 0.7
    torn.LightInfluence = 0
    torn.Parent = holder
    torn:Emit(26)
end

-- It has the star. A flash in its teeth, a little gold falling away from its mouth, and the star stays there, held, until it goes down the hole. Nothing else in the scene changes.
function Blasts.StarInItsTeeth(rig, fx)
    local s, metre = rig.state, rig.meters
    if s.foxStar then
        s.foxStar:Destroy()
        s.foxStar = nil
    end
    local mouth = rig.points.Mouth
    if not mouth then
        return
    end
    local holder = fx.neon(Vector3.one * 0.05, CFrame.new(mouth.TransformedWorldCFrame.Position), Color3.new(1, 1, 1))
    holder.Transparency = 1

    local flash = Instance.new("ParticleEmitter")
    flash.Texture = FOX_STAR
    flash.Rate = 0
    flash.Lifetime = NumberRange.new(0.34)
    flash.Speed = NumberRange.new(0)
    flash.Rotation = NumberRange.new(0, 360)
    flash.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2 * metre), NumberSequenceKeypoint.new(0.2, 0.95 * metre), NumberSequenceKeypoint.new(1, 0.3 * metre) })
    flash.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.5, 0.2), NumberSequenceKeypoint.new(1, 1) })
    flash.LightEmission = 1
    flash.LightInfluence = 0
    flash.Parent = holder
    flash:Emit(1)

    local sparks = Instance.new("ParticleEmitter")
    sparks.Texture = SPARKLE
    sparks.Rate = 0
    sparks.Lifetime = NumberRange.new(0.45, 0.85)
    sparks.Speed = NumberRange.new(0.8 * metre, 2.2 * metre)
    sparks.SpreadAngle = Vector2.new(180, 180)
    sparks.Drag = 2.5
    sparks.Acceleration = Vector3.new(0, -2.4 * metre, 0)
    sparks.Size = NumberSequence.new(0.07 * metre, 0)
    sparks.Color = ColorSequence.new(Color3.fromRGB(255, 240, 200), Color3.fromRGB(248, 192, 92))
    sparks.LightEmission = 1
    sparks.LightInfluence = 0
    sparks.Parent = holder
    sparks:Emit(16)

    -- held in its teeth through the fall and the landing
    local held = Instance.new("ParticleEmitter")
    held.Name = "HeldStar"
    held.Texture = FOX_STAR
    held.Rate = 0
    held.Lifetime = NumberRange.new(0.82)
    held.Speed = NumberRange.new(0)
    held.LockedToPart = true
    held.Rotation = NumberRange.new(0, 360)
    held.RotSpeed = NumberRange.new(60, 60)
    held.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * metre), NumberSequenceKeypoint.new(0.8, 0.24 * metre), NumberSequenceKeypoint.new(1, 0) })
    held.LightEmission = 1
    held.LightInfluence = 0
    held.Parent = mouth
    held:Emit(1)
    Debris:AddItem(held, 1)

    local light = Instance.new("PointLight")
    light.Color = Color3.fromRGB(255, 225, 170)
    light.Range = 2.4 * metre
    light.Brightness = 2
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(0.7), { Brightness = 0 }):Play()
end

-- A path of small lights runs out from its feet, winds once round it, and comes back to exactly where it started. Follow it and you arrive. Nothing else in the scene changes.
function Blasts.TheLongWayRound(rig, fx)
    local metre = rig.meters
    local centre = rig.rootPart.Position
    local rays = RaycastParams.new()
    rays.RespectCanCollide = true
    local floor = workspace:Raycast(centre, Vector3.new(0, -8 * metre, 0), rays)
    local groundY = if floor then floor.Position.Y else centre.Y - WARDEN_SOLE * metre
    local LIGHTS, GAP = 13, 0.085
    local start = math.random() * 2 * math.pi
    local spin = if math.random() < 0.5 then 1 else -1
    for index = 1, LIGHTS do
        local q = index / (LIGHTS + 1)
        local angle = start + spin * 2 * math.pi * q
        local reach = 1.65 * metre * math.sin(math.pi * q) ^ 0.8
        local at = fx.facing:VectorToWorldSpace(Vector3.new(math.cos(angle) * reach, 0, math.sin(angle) * reach)) + centre
        local here = workspace:Raycast(Vector3.new(at.X, centre.Y + metre, at.Z), Vector3.new(0, -8 * metre, 0), rays)
        local y = (if here then here.Position.Y else groundY) + 0.03
        task.delay(index * GAP, function()
            if not rig.model.Parent then
                return
            end
            local size = 0.17 * metre * (1 - 0.3 * math.abs(q - 0.5))
            local light = fx.neon(Vector3.new(0.02, size, size), CFrame.new(at.X, y, at.Z) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(255, 118, 26))
            light.Shape = Enum.PartType.Cylinder
            TweenService:Create(light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.new(0.02, size * 0.4, size * 0.4) }):Play()
            local spark = Instance.new("ParticleEmitter")
            spark.Texture = SPARKLE
            spark.Rate = 0
            spark.Lifetime = NumberRange.new(0.4, 0.7)
            spark.Speed = NumberRange.new(0.35 * metre, 0.7 * metre)
            spark.EmissionDirection = Enum.NormalId.Right
            spark.SpreadAngle = Vector2.new(30, 30)
            spark.Size = NumberSequence.new(0.05 * metre, 0)
            spark.Color = ColorSequence.new(Color3.fromRGB(255, 225, 160), Color3.fromRGB(255, 130, 50))
            spark.LightEmission = 1
            spark.LightInfluence = 0
            spark.Parent = light
            spark:Emit(2)
        end)
    end
end

-- It drinks the dream: a soft bloom of light at its tongue's tip, and a shimmer of scale dust drifting down from its wings as it gives its one slow beat. Nothing else in the scene changes.
function Blasts.AForgottenDream(rig, fx)
    local s, metre = rig.state, rig.meters
    if s.mothThreads then
        for _, thread in s.mothThreads do
            thread.part:Destroy()
        end
        s.mothThreads = nil
    end
    local tip = rig.points.Tongue12
    local at = if tip then tip.TransformedWorldCFrame.Position else fx.origin
    local holder = fx.neon(Vector3.one * 0.05, CFrame.new(at), Color3.new(1, 1, 1))
    holder.Transparency = 1

    local bloom = Instance.new("ParticleEmitter")
    bloom.Texture = SPARKLE
    bloom.Rate = 0
    bloom.Lifetime = NumberRange.new(0.45)
    bloom.Speed = NumberRange.new(0)
    bloom.Rotation = NumberRange.new(0, 360)
    bloom.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * metre), NumberSequenceKeypoint.new(0.25, 0.42 * metre), NumberSequenceKeypoint.new(1, 0) })
    bloom.Color = ColorSequence.new(Color3.fromRGB(255, 236, 250), Color3.fromRGB(214, 180, 255))
    bloom.LightEmission = 1
    bloom.LightInfluence = 0
    bloom.Parent = holder
    bloom:Emit(1)

    -- the dust: from all over the wings, drifting down slowly, glinting
    local cloud = fx.neon(Vector3.new(1.6, 0.2, 0.9) * metre, CFrame.new(fx.origin) * fx.facing, Color3.new(1, 1, 1))
    cloud.Transparency = 1
    local dust = Instance.new("ParticleEmitter")
    dust.Texture = SPARKLE
    dust.Shape = Enum.ParticleEmitterShape.Box
    dust.Rate = 0
    dust.Lifetime = NumberRange.new(1.1, 1.6)
    dust.Speed = NumberRange.new(0.05 * metre, 0.2 * metre)
    dust.SpreadAngle = Vector2.new(180, 180)
    dust.Acceleration = Vector3.new(0, -0.35 * metre, 0)
    dust.Drag = 1.2
    dust.Rotation = NumberRange.new(0, 360)
    dust.RotSpeed = NumberRange.new(-40, 40)
    dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.04 * metre), NumberSequenceKeypoint.new(1, 0) })
    dust.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 220, 244)), ColorSequenceKeypoint.new(0.5, Color3.fromRGB(214, 190, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(190, 220, 255)) })
    dust.LightEmission = 0.8
    dust.LightInfluence = 0.2
    dust.Parent = cloud
    dust:Emit(34)

    local light = Instance.new("PointLight")
    light.Color = Color3.fromRGB(240, 200, 255)
    light.Range = 2.4 * metre
    light.Brightness = 1.6
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(0.8), { Brightness = 0 }):Play()
end

-- It pops open, and its plates split the light: a fan of thin spectral rays round it, every colour once, and a scatter of rainbow glints. Nothing else in the scene changes.
function Blasts.EveryColour(rig, fx)
    local metre = rig.meters
    local centre = fx.origin + Vector3.new(0, 0.12 * metre, 0)
    local RAYS = 7
    for k = 1, RAYS do
        local angle = (k - 1) / RAYS * 2 * math.pi + math.random() * 0.3
        local out = fx.facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0.35, math.sin(angle))).Unit
        local length = 0.75 * metre
        local colour = Color3.fromHSV((k - 1) / RAYS, 0.55, 1)
        local ray = fx.neon(Vector3.new(0.025 * metre, 0.025 * metre, length), CFrame.lookAt(centre + out * (0.25 * metre + length / 2), centre + out * metre * 3), colour)
        ray.Transparency = 0.15
        TweenService:Create(ray, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 1, CFrame = ray.CFrame + out * 0.35 * metre, Size = Vector3.new(0.01 * metre, 0.01 * metre, length * 1.3) }):Play()
    end
    local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre), Color3.new(1, 1, 1))
    holder.Transparency = 1
    local glints = Instance.new("ParticleEmitter")
    glints.Texture = SPARKLE
    glints.Rate = 0
    glints.Lifetime = NumberRange.new(0.45, 0.8)
    glints.Speed = NumberRange.new(0.8 * metre, 1.8 * metre)
    glints.SpreadAngle = Vector2.new(180, 60)
    glints.Drag = 3
    glints.Acceleration = Vector3.new(0, -1.2 * metre, 0)
    glints.Size = NumberSequence.new(0.06 * metre, 0)
    glints.Color = ColorSequence.new({
        ColorSequenceKeypoint.new(0, Color3.fromHSV(0.95, 0.5, 1)), ColorSequenceKeypoint.new(0.25, Color3.fromHSV(0.12, 0.5, 1)), ColorSequenceKeypoint.new(0.5, Color3.fromHSV(0.35, 0.5, 1)),
        ColorSequenceKeypoint.new(0.75, Color3.fromHSV(0.58, 0.5, 1)), ColorSequenceKeypoint.new(1, Color3.fromHSV(0.78, 0.5, 1)),
    })
    glints.LightEmission = 1
    glints.LightInfluence = 0
    glints.Parent = holder
    glints:Emit(22)
    local light = Instance.new("PointLight")
    light.Color = Color3.fromRGB(230, 210, 255)
    light.Range = 2.2 * metre
    light.Brightness = 1.8
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(0.7), { Brightness = 0 }):Play()
end

-- A road of crystal grows up behind it, shard by shard along the way it came, each pair springing up from the ground and fading. Nothing else in the scene changes.
function Blasts.AHundredYears(rig, fx)
    local metre = rig.meters
    local base = rig.rootPart.CFrame
    local rays = RaycastParams.new()
    rays.RespectCanCollide = true
    local floor = workspace:Raycast(base.Position, Vector3.new(0, -8 * metre, 0), rays)
    local groundY = if floor then floor.Position.Y else base.Position.Y - SNAIL_SOLE * metre
    local COUNT = 8
    local colours = { Color3.fromRGB(60, 220, 190), Color3.fromRGB(90, 205, 230), Color3.fromRGB(120, 235, 210) }
    for index = 1, COUNT do
        local q = index / COUNT
        local at = base:PointToWorldSpace(Vector3.new(0.32 * math.sin(q * math.pi * 1.3) * metre, 0, (0.45 + q * 1.8) * metre))
        local here = workspace:Raycast(Vector3.new(at.X, base.Position.Y + metre, at.Z), Vector3.new(0, -8 * metre, 0), rays)
        local y = if here then here.Position.Y else groundY
        task.delay(q * 0.4, function()
            if not rig.model.Parent then
                return
            end
            for k = 1, 2 do
                local h = (0.15 + 0.1 * math.random()) * metre * (1 - 0.35 * q)
                local w = (0.045 + 0.015 * math.random()) * metre
                local root = CFrame.new(at.X + (k - 1.5) * 0.07 * metre, y, at.Z) * CFrame.Angles((math.random() - 0.5) * 0.7, math.random() * math.pi, (math.random() - 0.5) * 0.7) * CFrame.Angles(0, math.pi / 4, 0)
                local shard = fx.neon(Vector3.new(w, 0.01 * metre, w), root, colours[(index + k) % #colours + 1])
                shard.Transparency = 0.1
                TweenService:Create(shard, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.new(w, h, w), CFrame = root * CFrame.new(0, h / 2 - 0.02 * metre, 0) }):Play()
                task.delay(0.65, function()
                    if shard.Parent then
                        TweenService:Create(shard, TweenInfo.new(0.45), { Transparency = 1, Size = Vector3.new(w * 0.5, h * 0.6, w * 0.5) }):Play()
                    end
                end)
            end
        end)
    end
    local holder = fx.neon(Vector3.one * 0.05, base * CFrame.new(0, -SNAIL_SOLE * metre * 0.6, 1.2 * metre), Color3.new(1, 1, 1))
    holder.Transparency = 1
    local glints = Instance.new("ParticleEmitter")
    glints.Texture = SPARKLE
    glints.Shape = Enum.ParticleEmitterShape.Box
    glints.Rate = 0
    glints.Lifetime = NumberRange.new(0.5, 0.9)
    glints.Speed = NumberRange.new(0.2 * metre, 0.6 * metre)
    glints.EmissionDirection = Enum.NormalId.Top
    glints.SpreadAngle = Vector2.new(50, 50)
    glints.Drag = 2
    glints.Size = NumberSequence.new(0.05 * metre, 0)
    glints.Color = ColorSequence.new(Color3.fromRGB(210, 255, 240), Color3.fromRGB(90, 220, 200))
    glints.LightEmission = 1
    glints.LightInfluence = 0
    holder.Size = Vector3.new(0.4, 0.05, 1.8) * metre
    glints.Parent = holder
    glints:Emit(18)
end

-- Three ribbons of wind leave its mouth, wind round each other as they run ahead of it, and curl up and away; rings of breath and a scatter of
-- tumbling leaves go with them.
function Blasts.TuggingGale(rig, fx)
    local colors, u, facing, neon = rig.profile.Colors, rig.unit, fx.facing, fx.neon
    local mouthBone = rig.points.Blow
    local mouth = if mouthBone then mouthBone.TransformedWorldCFrame.Position else fx.origin
    local ahead = facing:VectorToWorldSpace(Vector3.new(0, 0, -1))
    local right = facing:VectorToWorldSpace(Vector3.new(1, 0, 0))
    local up = Vector3.yAxis
    local function along(angle, f)
        local out = 1 - (1 - f) ^ 2
        local a = angle + f * 8.5
        local radius = (0.14 + 1.05 * f ^ 1.4) * u
        return mouth + ahead * (3.7 * out * u) + up * (2.6 * f ^ 2.2 * u) + right * (math.cos(a) * radius) + up * (math.sin(a) * radius)
    end

    local ribbons = {}
    for index = 1, 3 do
        local head = neon(Vector3.one * 0.05 * u, CFrame.new(mouth), colors.Sun)
        head.Shape = Enum.PartType.Ball
        head.Transparency = 1 -- only its ribbon shows
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Position = Vector3.new(0, 0.11 * u, 0)
        a1.Position = Vector3.new(0, -0.11 * u, 0)
        a0.Parent, a1.Parent = head, head
        local trail = Instance.new("Trail")
        trail.Attachment0, trail.Attachment1 = a0, a1
        trail.Lifetime = 0.42
        trail.FaceCamera = true
        trail.LightEmission = 0.7
        trail.LightInfluence = 0
        trail.Color = ColorSequence.new(colors.Sun, if index == 2 then colors.Gold else colors.Orange)
        trail.Transparency = NumberSequence.new({
            NumberSequenceKeypoint.new(0, 0.1),
            NumberSequenceKeypoint.new(0.6, 0.45),
            NumberSequenceKeypoint.new(1, 1),
        })
        trail.WidthScale = NumberSequence.new(1, 0.15)
        trail.Parent = head
        table.insert(ribbons, { part = head, angle = index / 3 * 2 * math.pi })
    end
    local started = os.clock()
    local stepper
    stepper = RunService.RenderStepped:Connect(function()
        local f = (os.clock() - started) / 1.25
        if f >= 1 or not ribbons[1].part.Parent then
            stepper:Disconnect()
            for _, ribbon in ribbons do
                if ribbon.part.Parent then
                    ribbon.part:FindFirstChildOfClass("Trail").Enabled = false
                end
            end
            return
        end
        for _, ribbon in ribbons do
            ribbon.part.CFrame = CFrame.new(along(ribbon.angle, f))
        end
    end)

    -- rings of breath, each wider and later than the last
    for index = 1, 3 do
        local delay = (index - 1) * 0.11
        local start = CFrame.lookAt(mouth + ahead * 0.2 * u, mouth + ahead * 2 * u) * CFrame.Angles(0, math.pi / 2, 0)
        local ring = neon(Vector3.new(0.05 * u, 0.3 * u, 0.3 * u), start, colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 1
        -- (a second tween on the same property cancels the first, even one still waiting out its delay: so one tween each, started late)
        task.delay(delay, function()
            if ring.Parent then
                ring.Transparency = 0.45
                TweenService:Create(ring, TweenInfo.new(0.62, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                    CFrame = start + ahead * (1.8 + index * 0.6) * u,
                    Size = Vector3.new(0.015 * u, (1.1 + index * 0.55) * u, (1.1 + index * 0.55) * u),
                    Transparency = 1,
                }):Play()
            end
        end)
    end

    -- the leaves it has picked up, coral among the green, tumbling along and lifting away
    for index = 1, 12 do
        local angle = math.random() * 2 * math.pi
        local f = 0.45 + math.random() * 0.5
        local petal = (0.09 + math.random() * 0.07) * u
        local leaf = neon(Vector3.new(0.012 * u, petal, petal), CFrame.new(mouth), if index % 4 == 0 then colors.Amber elseif index % 2 == 0 then colors.Gold else colors.Sun)
        leaf.Shape = Enum.PartType.Cylinder -- a thin disc: a petal, not a chip
        leaf.Transparency = 1
        local spin = CFrame.Angles(math.random() * 9 - 4.5, math.random() * 9 - 4.5, math.random() * 9 - 4.5)
        local goal = CFrame.new(along(angle, f) + right * (math.random() - 0.5) * 1.2 * u) * spin
        task.delay(0.02 + math.random() * 0.2, function()
            if leaf.Parent then
                leaf.Transparency = 0.05
                TweenService:Create(leaf, TweenInfo.new(1.05, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { CFrame = goal }):Play()
                task.delay(0.8, function()
                    if leaf.Parent then
                        TweenService:Create(leaf, TweenInfo.new(0.25), { Transparency = 1 }):Play()
                    end
                end)
            end
        end)
    end

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 5 * u
    light.Brightness = 0.8
    light.Parent = ribbons[1].part
    TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(14)
    end
end

-- It rears and brings its hooves down: sparks fly from all four, and lightning flares through its mane. Its own lightning only: no weather.
function Blasts.ThunderAnswers(rig, fx)
    for _, name in { "FL", "FR", "BL", "BR" } do
        local sparks = rig.state.sparks and rig.state.sparks[name]
        if sparks then
            sparks:Emit(14)
        end
    end
    rig.state.flickerUntil = rig.state.time + 0.6
end

-- The galaxy under its wings, thrown open: stars in three arms wheel outward from its heart in front of it, three of them drawing ribbons, with a ring of light going out.
function Blasts.TurningOfTheHeavens(rig, fx)
    local colors, u, facing, neon = rig.profile.Colors, rig.unit, fx.facing, fx.neon
    local heart = rig.points.SpiralInner
    local centre = if heart then heart.TransformedWorldCFrame.Position else fx.origin
    local ahead = facing:VectorToWorldSpace(Vector3.new(0, 0, -1))
    local right = facing:VectorToWorldSpace(Vector3.new(1, 0, 0))
    local up = Vector3.yAxis

    local glow = rig.profile.GlowColors
    local gold, violet, pale = glow["ffc878"], glow["8a6bff"], glow["e6e0ff"]
    local stars = {}
    for arm = 1, 3 do
        for index = 1, 16 do
            local f = index / 16
            -- a thin streak of light, turned along its path each frame: a block this size reads as confetti
            local thick = (0.042 - 0.018 * f) * u * (0.8 + 0.4 * math.random())
            local star = neon(Vector3.new(thick, thick, thick * (5 + 3 * math.random())), CFrame.new(centre),
                if f < 0.32 then gold elseif index % 5 == 0 then pale elseif index % 7 == 0 then colors.Orange else violet)
            if index % 4 == 0 then
                local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
                a0.Position = Vector3.new(0, 0.035 * u, 0)
                a1.Position = Vector3.new(0, -0.035 * u, 0)
                a0.Parent, a1.Parent = star, star
                local trail = Instance.new("Trail")
                trail.Attachment0, trail.Attachment1 = a0, a1
                trail.Lifetime = 0.34
                trail.FaceCamera = true
                trail.LightEmission = 0.8
                trail.LightInfluence = 0
                trail.Color = ColorSequence.new(pale, violet)
                trail.Transparency = NumberSequence.new(0.15, 1)
                trail.WidthScale = NumberSequence.new(1, 0.2)
                trail.Parent = star
            end
            table.insert(stars, { part = star, angle = arm / 3 * 2 * math.pi + f * 2.6 + (math.random() - 0.5) * 0.14, reach = (0.22 + 1.65 * f) * (0.94 + 0.12 * math.random()) })
        end
    end
    local started = os.clock()
    local stepper
    stepper = RunService.RenderStepped:Connect(function()
        local f = (os.clock() - started) / 1.3
        if f >= 1 or not stars[1].part.Parent then
            stepper:Disconnect()
            return
        end
        local opening = 1 - (1 - f) ^ 2.4
        for _, star in stars do
            local angle = star.angle - 3.2 * opening
            local radius = star.reach * (0.15 + 1.25 * opening) * u
            local at = centre + ahead * (0.25 + 0.9 * opening) * u + right * (math.cos(angle) * radius) + up * (math.sin(angle) * radius)
            if star.last and (at - star.last).Magnitude > 1e-3 then
                star.part.CFrame = CFrame.lookAt(at, at + (at - star.last))
            else
                star.part.CFrame = CFrame.new(at)
            end
            star.last = at
            star.part.Transparency = smoothstep(0.62, 1, f)
        end
    end)

    local flash = neon(Vector3.one * 0.3 * u, CFrame.new(centre), colors.Sun)
    flash.Shape = Enum.PartType.Ball
    flash.Transparency = 0.25
    TweenService:Create(flash, TweenInfo.new(0.42, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.5 * u, Transparency = 1 }):Play()

    local start = CFrame.lookAt(centre, centre + ahead) * CFrame.Angles(0, math.pi / 2, 0)
    local ring = neon(Vector3.new(0.03 * u, 0.5 * u, 0.5 * u), start, colors.Gold)
    ring.Shape = Enum.PartType.Cylinder
    ring.Transparency = 0.8 -- a filled disc: stronger than this, it reads as a lens across the whole view
    TweenService:Create(ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        CFrame = start + ahead * 1.2 * u,
        Size = Vector3.new(0.01 * u, 3.6 * u, 3.6 * u),
        Transparency = 1,
    }):Play()

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 6 * u
    light.Brightness = 1.2
    light.Parent = flash
    TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(18)
    end
end

function Blasts.SovereignRoar(rig, fx)
    local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
    local mouthPoint, crownPoint = rig.points.Jaw_Mouth, rig.points.Head_Crown
    local mouth = if mouthPoint then mouthPoint.WorldPosition else origin
    local crown = if crownPoint then crownPoint.WorldPosition else origin + Vector3.new(0, 0.3 * u, 0)
    local body = rig.parts.Body and rig.parts.Body.Position or rig.rootPart.Position
    local forward = (mouth - body) * Vector3.new(1, 0, 1)
    forward = if forward.Magnitude > 1e-3 then forward.Unit else fx.facing.LookVector

    for index, delay in { 0, 0.14, 0.28 } do
        local ring = neon(Vector3.new(0.04 * u, 0.3 * u, 0.3 * u), CFrame.lookAt(mouth, mouth + forward) * CFrame.Angles(0, math.pi / 2, 0),
            if index == 2 then colors.Sun else colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 1
        local finish = mouth + forward * (1.1 + 0.5 * index) * u
        TweenService:Create(ring, TweenInfo.new(0.06, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, delay), { Transparency = 0.35 }):Play()
        TweenService:Create(ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, delay), {
            CFrame = CFrame.lookAt(finish, finish + forward) * CFrame.Angles(0, math.pi / 2, 0),
            Size = Vector3.new(0.02 * u, (1.6 + 0.5 * index) * u, (1.6 + 0.5 * index) * u),
            Transparency = 1,
        }):Play()
    end

    local behind = crown - forward * 0.12 * u
    local right = forward:Cross(Vector3.yAxis).Unit
    for index = 1, 12 do
        local angle = (index - 0.5) / 12 * math.pi
        local out = (right * math.cos(angle) + Vector3.yAxis * math.sin(angle)).Unit
        local length = (if index % 2 == 0 then 0.55 else 0.4) * u
        local base = behind + out * 0.18 * u
        local ray = neon(Vector3.new(0.05 * u, 0.05 * u, 0.1 * u), CFrame.lookAt(base, base + out), if index % 2 == 0 then colors.Sun else colors.Gold)
        ray.Transparency = 1
        local tip = base + out * length * 0.5
        TweenService:Create(ray, TweenInfo.new(0.1, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.05), { Transparency = 0.2 }):Play()
        TweenService:Create(ray, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.05), {
            CFrame = CFrame.lookAt(tip, tip + out),
            Size = Vector3.new(0.025 * u, 0.025 * u, length),
        }):Play()
        TweenService:Create(ray, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.6), { Transparency = 1 }):Play()
    end

    local paws = {}
    for _, name in { "LegFL_Paw", "LegFR_Paw", "LegBL_Paw", "LegBR_Paw" } do
        if rig.points[name] then
            table.insert(paws, rig.points[name].WorldPosition)
        end
    end
    local ground = origin - Vector3.new(0, 0.8 * u, 0)
    if #paws > 0 then
        local sum = Vector3.zero
        for _, position in paws do
            sum += position
        end
        ground = sum / #paws
    end
    local stomp = neon(Vector3.new(0.04 * u, 0.5 * u, 0.5 * u), CFrame.new(ground + Vector3.new(0, 0.03 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
    stomp.Shape = Enum.PartType.Cylinder
    stomp.Transparency = 0.4
    TweenService:Create(stomp, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(0.02 * u, 3.6 * u, 3.6 * u),
        Transparency = 1,
    }):Play()

    local light = Instance.new("PointLight")
    light.Color = colors.Gold
    light.Range = 12 * u
    light.Brightness = 2.2
    light.Parent = neon(Vector3.one * 0.05, CFrame.new(mouth), colors.Gold)
    TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(25)
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
    Blasts[profile.Effects.Blast](rig, fx)
    Debris:AddItem(folder, 2) -- the longest blast (Sacred Grove's branches) has faded by 1.75 s
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

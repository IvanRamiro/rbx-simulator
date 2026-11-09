local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local PetRig = {}

local SPARKLE = "rbxasset://textures/particles/sparkles_main.dds"

-- Plays a tween once a delay has passed. A later step can't be queued with TweenInfo's DelayTime when an earlier tween on the same instance
-- changes the same property: playing the later one cancels the earlier at once, delay or not (measured in Studio, 2026-11-08). So it waits here.
local function tweenAfter(delay, instance, info, goal)
    task.delay(delay, function()
        if instance.Parent then
            TweenService:Create(instance, info, goal):Play()
        end
    end)
end

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
    gas.LockedToPart = true -- it gathers before its breast, wherever the owl goes (animateNebulaOwl moves it)
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
    seed.LockedToPart = true
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
    if s.gather and s.gather.Parent then
        -- the gas keeps before its breast as it follows its player, and the star lights there
        s.starAt = rig.rootPart.CFrame:PointToWorldSpace(OWL_STAR_AHEAD * rig.meters)
        s.gather.Parent.CFrame = CFrame.new(s.starAt)
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
    s.foxFrom = nil -- measured afresh from this star
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
    -- (only before the catch: seen first after it, the burst has gone and nothing would take the star away)
    if rig.nova and progress >= FOX_FALL_FROM and progress < FOX_CATCH and not rig.nova.starFell then
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
    local moved = at - (s.lastAt or at)
    s.lastAt = at
    local inFrame = rig.rootPart.CFrame:VectorToObjectSpace(moved / math.max(dt, 0.001))
    -- more than 20 studs in one frame is not movement (a dash at 170 studs/s is under 3): it was teleported, or caught up with a teleported player
    if moved.Magnitude > 20 then
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
        s.lastAt, s.lastV = nil, nil -- its lantern starts afresh when it comes back into view
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
    -- (only before they reach its tongue: seen first after that, the burst has gone and nothing would take them away)
    if rig.nova and progress >= MOTH_THREAD_FROM and progress < MOTH_THREAD_TO and not rig.nova.threaded then
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

-- The special's spin, as a turn at each moment of it (armaSpinAngle), so it always ends facing
-- forward: its speed rises and falls with armaWhirl, scaled to the whole number of turns nearest
-- ARMA_SPIN_RATE turns a second at full speed. ARMA_SPIN[i] is the share of the spin done by
-- progress (i - 1) / ARMA_SPIN_STEPS; armaSpin is the whole spin's length in full-speed specials.
local ARMA_SPIN_RATE, ARMA_SPIN_STEPS = 2.4, 200
local function armaWhirl(progress)
    return smoothstep(0.1, 0.3, progress) * (1 - smoothstep(0.4, 0.46, progress))
end
local ARMA_SPIN, armaSpin = { 0 }, 0
for i = 1, ARMA_SPIN_STEPS do
    armaSpin += armaWhirl((i - 0.5) / ARMA_SPIN_STEPS) / ARMA_SPIN_STEPS
    ARMA_SPIN[i + 1] = armaSpin
end
for i, done in ARMA_SPIN do
    ARMA_SPIN[i] = done / armaSpin
end
local function armaSpinAngle(progress)
    local turns = math.max(1, math.floor(ARMA_SPIN_RATE * PetRig.NOVA_TIME * armaSpin + 0.5))
    local x = math.clamp(progress, 0, 1) * ARMA_SPIN_STEPS
    local i = math.min(math.floor(x), ARMA_SPIN_STEPS - 1)
    local done = ARMA_SPIN[i + 1] + (ARMA_SPIN[i + 2] - ARMA_SPIN[i + 1]) * (x - i)
    return done * turns * 2 * math.pi
end

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
    local hop = smoothstep(0.44, 0.5, progress) * (1 - smoothstep(0.52, 0.64, progress))
    local proud = smoothstep(0.5, 0.58, progress) * (1 - smoothstep(0.86, 0.98, progress))
    local flash = smoothstep(0.36, 0.43, progress) * (1 - smoothstep(0.46, 0.66, progress))
    s.whirl = armaSpinAngle(progress) % (2 * math.pi)

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

-- The Abyss Anomalocaris (skinned): a hunter from the first sea that still swims through the air. A wave runs back along its nine pairs of flaps, each a
-- little behind the one before (the flaps are weighted by their place along the body, so where two overlap they move as one); its trunk undulates
-- with it, its tail fan steers, and it banks into its turns. Its great arms rest curled under its head, tucking in at speed and now and then
-- flexing open and shut as if tasting the water; its eyes swivel on their short stalks. Left is -X: a left flap rises with a negative turn about Z.
local ANOMALO_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local ANOMALO_FLAPS = 9
local ANOMALO_TRUNK = { "Seg4", "Seg5", "Seg6", "Seg7", "Seg8", "Seg9", "Tail" }
local ANOMALO_GLOW = Color3.fromRGB(190, 36, 146) -- deep: as Neon it blooms, and a paler magenta read as a bright pink fringe
local ANOMALO_RING = "rbxassetid://12403112662" -- a thin glowing ring with brighter arcs (also RealmAura's)

local function animateAbyssAnomalocaris(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > ANOMALO_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special, The First Hunt: the arms open wide as it draws back; it lunges, and the arms snap shut on the burst (PetRig.NOVA_BURST); it holds
    -- them shut a moment, flaps beating hard, then settles
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local open = smoothstep(0.04, 0.3, progress) * (1 - smoothstep(0.39, 0.43, progress))
    local draw = smoothstep(0.1, 0.36, progress) * (1 - smoothstep(0.37, 0.42, progress))
    local lunge = smoothstep(0.37, 0.42, progress) * (1 - smoothstep(0.5, 0.82, progress))
    local snap = smoothstep(0.4, 0.43, progress) * (1 - smoothstep(0.62, 0.9, progress))

    -- it banks into its turns
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.25, -0.45, 0.45) - (s.bank or 0)) * math.min(1, dt * 3)

    -- now and then, still, it flexes its arms open and shut, twice, as if tasting the water
    s.nextFlex = s.nextFlex or t + 7 + math.random() * 7
    local flex = 0
    if t >= s.nextFlex then
        local a = (t - s.nextFlex) / 2.4
        if a >= 1 then
            s.nextFlex = t + 12 + math.random() * 12
        elseif pace < 0.25 and nova == 0 then
            flex = math.sin(math.pi * a) * (0.5 + 0.5 * math.sin(a * math.pi * 4 - math.pi / 2))
        else
            s.nextFlex = t + 4
        end
    end

    s.swim = (s.swim or 0) + dt * (2.3 + 2.6 * pace + 3.2 * lunge)
    local swim = s.swim
    local hover = 0.022 * math.sin(t * 0.9) + 0.008 * math.sin(swim) + 0.04 * fly
    pose(m.Body, CFrame.new(0, hover * u, (0.1 * draw - 0.2 * lunge) * u)
        * CFrame.Angles(0.012 * math.sin(swim * 0.5 + 0.6) - 0.08 * pace + 0.12 * draw - 0.1 * lunge, 0, s.bank))

    -- the trunk: a slow wave back along it, stronger at speed; the tail swings out of the turn
    local sway = 0.03 + 0.045 * pace + 0.04 * lunge
    for i, name in ANOMALO_TRUNK do
        pose(m[name], CFrame.Angles(0.012 * math.sin(swim * 0.5 - i * 0.6), sway * math.sin(swim * 0.5 - i * 0.55) - s.bank * 0.06, 0))
    end
    pose(m.Seg2, CFrame.Angles(0, -0.4 * sway * math.sin(swim * 0.5 + 0.5), 0))
    pose(m.Seg1, CFrame.Angles(0.04 * draw, -0.3 * sway * math.sin(swim * 0.5 + 1), 0))
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2 + math.random() * 3
        s.gazeTo = (math.random() - 0.5) * 0.7
        s.nodTo = (math.random() - 0.5) * 0.1
    end
    local calm = (1 - 0.6 * pace) * (1 - open)
    s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * calm - (s.gaze or 0)) * math.min(1, dt * 2.5)
    s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * math.min(1, dt * 2.5)
    pose(m.Head, CFrame.Angles(s.nod + 0.06 * draw - 0.08 * lunge, s.gaze * 0.25, 0))

    -- the flaps: the wave, each flap 0.42 rad behind the one in front
    local amp = (0.15 + 0.1 * pace + 0.14 * lunge) * (1 - 0.4 * open)
    for k = 1, ANOMALO_FLAPS do
        local a = amp * math.sin(swim - (k - 1) * 0.42) + 0.03 * fly
        pose(m["FlapL" .. k], CFrame.Angles(0, 0, -a))
        pose(m["FlapR" .. k], CFrame.Angles(0, 0, a))
    end

    -- the tail fan steers: raised as it climbs, the V opening when it lunges
    pose(m.Tail, CFrame.Angles(-0.05 * pace + 0.12 * draw - 0.08 * lunge + 0.02 * math.sin(swim * 0.5 - 4.5), -s.bank * 0.35 + sway * math.sin(swim * 0.5 - 4.4), 0))
    for j = 1, 3 do
        local beat = 0.06 * math.sin(swim * 0.5 - 4.6 - j * 0.3)
        local spread = 0.12 * lunge + 0.03 * pace
        pose(m["FanL" .. j], CFrame.Angles(beat, 0, -spread))
        pose(m["FanR" .. j], CFrame.Angles(beat, 0, spread))
    end

    -- the arms: curled at rest, breathing; tucked tighter at speed; opened wide for the hunt, then snapped shut on it
    local curl = 0.06 * math.sin(t * 0.8) + 0.25 * pace - 1.0 * open + 0.55 * snap - 0.55 * flex
    local spread = 0.24 * open + 0.06 * flex - 0.04 * snap
    for i = 1, 6 do
        local bend = -curl * (0.12 + 0.09 * (i - 1))
        local reach = if i == 1 then 0.25 * lunge + 0.1 * open else 0
        pose(m["ArmL" .. i], CFrame.Angles(bend + reach, if i == 1 then spread else 0, 0))
        pose(m["ArmR" .. i], CFrame.Angles(bend + reach, if i == 1 then -spread else 0, 0))
    end

    -- the eyes swivel on their stalks; on the hunt both swing forward onto the prey
    local focus = math.max(open, 0.6 * lunge)
    pose(m.StalkL, CFrame.Angles(0, s.gaze * 0.5 + 0.08 * math.sin(t * 0.7) - 0.4 * focus, -0.06 * math.sin(t * 0.9 + 1)))
    pose(m.StalkR, CFrame.Angles(0, s.gaze * 0.5 + 0.08 * math.sin(t * 0.7 + 2) + 0.4 * focus, 0.06 * math.sin(t * 0.9 + 2.5)))
    pose(m.EyeL, CFrame.Angles(0, 0.1 * math.sin(t * 0.5), 0))
    pose(m.EyeR, CFrame.Angles(0, 0.1 * math.sin(t * 0.5 + 1.3), 0))

    -- the edges' light breathes with the wave; on the snap it flares
    local shine = 0.08 * (0.5 + 0.5 * math.sin(swim * 0.5)) + 0.55 * snap
    local colour = ANOMALO_GLOW:Lerp(Color3.fromRGB(240, 120, 205), shine)
    for _, key in { "EdgesL", "EdgesR" } do
        local edge = rig.parts[key]
        if edge then
            edge.Color = colour
        end
    end
end

-- The Voidscale Hydra (skinned): a low sprawling reptile with three necks, the middle one forking into two young heads. It walks like a monitor
-- lizard, legs swinging out in diagonal pairs, its body swaying side to side and its tail following the wave. Each neck sways on its own and each head
-- chooses its own gaze; the tongues of light flick out, each in its own time; now and then the two young heads turn on each other and hiss.
local HYDRA_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local HYDRA_SOLE = 0.2621 -- metres from the middle of its box down to its claws: it walks on the ground
local HYDRA_LIGHT = Color3.fromRGB(70, 150, 255)
local HYDRA_HEADS = { -- each head's forward line in the model's axes, how far its tongue reaches (metres), its neck and the bones that carry it
    L = { dir = Vector3.new(-0.2067, -0.0316, -0.9779), reach = 0.084, neck = { "NeckL1", "NeckL2", "NeckL3", "NeckL4" }, phase = 0 },
    R = { dir = Vector3.new(0.1787, -0.0936, -0.9794), reach = 0.084, neck = { "NeckR1", "NeckR2", "NeckR3", "NeckR4" }, phase = 2.1 },
    ML = { dir = Vector3.new(-0.2186, -0.0094, -0.9758), reach = 0.0538, neck = { "ForkL1", "ForkL2" }, phase = 4.0 },
    MR = { dir = Vector3.new(0.1998, -0.1263, -0.9717), reach = 0.0538, neck = { "ForkR1", "ForkR2" }, phase = 5.3 },
}
local HYDRA_LEGS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi } -- diagonal pairs swing together

local function animateVoidscaleHydra(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > HYDRA_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, HYDRA_SOLE)

    -- the special, The Void Between: the necks rise and draw back as a rift tears open in the air before it; at the burst all four heads strike into
    -- it, tongues out; they hold, then draw back as it closes
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local rear = smoothstep(0.04, 0.34, progress) * (1 - smoothstep(0.38, 0.43, progress))
    local strike = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.55, 0.85, progress))

    -- now and then the two young heads squabble: they turn on each other, hiss with their tongues out, shake, and turn away
    s.nextSquabble = s.nextSquabble or t + 8 + math.random() * 8
    local squabble = 0
    if t >= s.nextSquabble then
        local a = (t - s.nextSquabble) / 2.2
        if a >= 1 then
            s.nextSquabble = t + 14 + math.random() * 12
        elseif pace < 0.3 and nova == 0 then
            squabble = smoothstep(0, 0.2, a) * (1 - smoothstep(0.75, 1, a))
        else
            s.nextSquabble = t + 4
        end
    end

    -- the walk: legs out in diagonal pairs, the body swaying, the tail following
    s.stride = (s.stride or 0) + dt * (2.2 + 7.5 * moving + 2 * fly) * (if pace > 0.05 then 1 else 0.15)
    local stride = s.stride
    local sway = 0.13 * moving * math.sin(stride)
    local breath = math.sin(t * 1.3)
    pose(m.Body, CFrame.new(0, 0.005 * breath * u - drop + 0.03 * rear * u, (0.05 * rear - 0.07 * strike) * u) * CFrame.Angles(0.03 * rear - 0.03 * strike + 0.01 * breath, sway, 0.03 * moving * math.sin(stride)))
    pose(m.Chest, CFrame.Angles(0.12 * rear - 0.08 * strike, -0.6 * sway, 0))
    pose(m.Hips, CFrame.Angles(0, -0.7 * sway, 0))
    for k = 1, 5 do
        pose(m["Tail" .. k], CFrame.Angles(0.02 * math.sin(t * 0.7 - k * 0.5), (0.05 + 0.12 * moving) * math.sin(stride - 0.9 - k * 0.6) + 0.04 * math.sin(t * 0.5 - k * 0.4) * (1 - moving), 0))
    end
    for leg, lead in HYDRA_LEGS do
        local front, side = string.sub(leg, 1, 1), string.sub(leg, 2, 2)
        local phase = stride + lead
        local swing = 0.42 * moving * math.sin(phase) * (if front == "F" then 1 else -1)
        local lift = 0.32 * moving * math.max(0, math.cos(phase))
        local up = if side == "L" then -lift else lift -- a leg out to its left rises with a negative turn about Z
        pose(m["Upper" .. front .. side], CFrame.Angles(0, swing, up + (if side == "L" then 0.3 else -0.3) * fly))
        pose(m["Lower" .. front .. side], CFrame.Angles(0, 0, (if side == "L" then 0.5 else -0.5) * lift))
        pose(m["Foot" .. front .. side], CFrame.Angles(0, -0.5 * swing, (if side == "L" then -0.3 else 0.3) * lift))
    end

    -- the necks and heads: each its own sway and its own gaze
    s.gaze = s.gaze or {}
    s.tongue = s.tongue or {}
    for key, head in HYDRA_HEADS do
        local g = s.gaze[key]
        if not g or t >= g.next then
            g = { next = t + 1.6 + math.random() * 3, yaw = (math.random() - 0.5) * 0.9, pitch = (math.random() - 0.5) * 0.35, cy = g and g.cy or 0, cp = g and g.cp or 0 }
            s.gaze[key] = g
        end
        local young = key == "ML" or key == "MR"
        local toward = if key == "ML" then -1 elseif key == "MR" then 1 else 0 -- the young heads turn on each other
        local wantYaw = g.yaw * (1 - rear) * (1 - strike) + (if young then toward * 0.55 * squabble else 0)
        local wantPitch = g.pitch * (1 - rear) * (1 - strike) + (if young then 0.15 * squabble else 0)
        g.cy += (wantYaw - g.cy) * math.min(1, dt * 3)
        g.cp += (wantPitch - g.cp) * math.min(1, dt * 3)
        local n = #head.neck
        for i, name in head.neck do
            local share = i / n
            local idle = 0.05 * math.sin(t * 0.8 + head.phase + i * 0.5) * (1 - 0.5 * pace)
            local yawTo = if young then toward * 0.25 * squabble * share else 0
            pose(m[name], CFrame.Angles(0.18 * rear / n * (if i == 1 then 2 else 1) - 0.12 * strike * (if i == 1 then 1.5 else -0.6) + 0.04 * idle,
                idle + yawTo + g.cy * 0.25 / n, 0))
        end
        local shake = if young then 0.12 * squabble * math.sin(t * 34 + head.phase) else 0
        pose(m["Head" .. key], CFrame.Angles(g.cp + 0.1 * rear - 0.25 * strike, g.cy * 0.75 + shake, 0))

        -- its tongue flicks: out and in twice, quickly, every few seconds; out and held in the special and the squabble
        local tg = s.tongue[key]
        if not tg or t >= tg.next then
            tg = { at = t, next = t + 2 + math.random() * 3.5 }
            s.tongue[key] = tg
        end
        local a = (t - tg.at) / 0.5
        local flick = if a < 1 then math.max(0, math.sin(a * 2 * math.pi)) else 0
        local out = math.max(flick, strike, if young then squabble else 0)
        pose(m["Tongue" .. key], CFrame.new(head.dir * (head.reach * out * u)))
    end

    -- the eyes and tongues brighten as it strikes
    local light = HYDRA_LIGHT:Lerp(Color3.fromRGB(190, 225, 255), 0.5 * strike)
    for _, key in { "LightL", "LightR", "LightML", "LightMR" } do
        local part = rig.parts[key]
        if part then
            part.Color = light
        end
    end
end

-- The Nameless One (skinned): a tall figure with no legs, wound in pale ribbons round nothing, a hollow where its face should be with one point of light
-- floating in it, a broken halo behind its head. It floats and bobs, its streamers and scarves drifting on a current only it feels; its hood tilts
-- toward you as if it were trying to read you; now and then one arm lifts and the glowing ends of its ribbons write a loop in the air.
local NAMELESS_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local NAMELESS_HALO = Color3.fromRGB(184, 156, 255)
local NAMELESS_SPARK = Color3.fromRGB(244, 240, 255)
local NAMELESS_HEM = {} -- each streamer: the line it swings out about (its outward direction crossed with up), and its own phase
for k, degrees in { 22, 68, 112, 158, 202, 248, 292, 338 } do
    local angle = math.rad(degrees)
    NAMELESS_HEM[k - 1] = { axis = Vector3.new(math.cos(angle), 0, -math.sin(angle)), phase = (k - 1) * 0.8 }
end
local NAMELESS_TIP = { L = Vector3.new(-0.0201, -0.1086, 0.0106), R = Vector3.new(0.0201, -0.1086, 0.0106) } -- from each ArmX5 bone to its longer ribbon's tip, in metres
local NAMELESS_SOLE, NAMELESS_HOVER = 0.6081, 0.12 -- metres from the middle of its box down to its lowest streamer; how far that floats clear of the ground

-- It is taller than the height a companion is held at: lifted so its streamers float a hand's breadth clear of the ground under it, never lowered
local function namelessHover(rig, s, t, u, fly)
    s.nextGround = s.nextGround or 0
    if t >= s.nextGround then
        s.nextGround = t + 0.15
        local from = rig.rootPart.Position
        local hit = workspace:Raycast(from, Vector3.new(0, -12 * u, 0), turtleRay)
        local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
        if not onCharacter then -- (a player walking under it: keep what it had)
            s.liftTo = if hit then math.max(0, (NAMELESS_SOLE + NAMELESS_HOVER) * u - (from.Y - hit.Position.Y)) else 0
        end
    end
    local target = (s.liftTo or 0) * (1 - fly)
    s.lift = (s.lift or target) + (target - (s.lift or target)) * math.min(1, rig.deltaTime * 4)
    return s.lift
end

local function namelessGone(rig, s, gone)
    if s.gone == gone then
        return
    end
    s.gone = gone
    for _, key in { "Body", "Spark", "Halo", "QuillL", "QuillR" } do
        local part = rig.parts[key]
        if part then
            part.Transparency = gone
        end
    end
    if s.namelessLight then
        s.namelessLight.Enabled = gone < 0.9
    end
end

local function namelessPen(rig)
    local metre = rig.meters
    local holder = Instance.new("Part")
    holder.Name = "Pen"
    holder.Anchored = true
    holder.CanCollide = false
    holder.CanTouch = false
    holder.CanQuery = false
    holder.CastShadow = false
    holder.Transparency = 1
    holder.Size = Vector3.one * 0.05
    local a, b = Instance.new("Attachment"), Instance.new("Attachment")
    a.Position, b.Position = Vector3.new(0, 0.01 * metre, 0), Vector3.new(0, -0.01 * metre, 0)
    a.Parent, b.Parent = holder, holder
    local trail = Instance.new("Trail")
    trail.Attachment0, trail.Attachment1 = a, b
    trail.FaceCamera = true
    trail.Lifetime = 0.5
    trail.LightEmission = 1
    trail.LightInfluence = 0
    trail.WidthScale = NumberSequence.new(1, 0.2)
    trail.Color = ColorSequence.new(NAMELESS_SPARK, NAMELESS_HALO)
    trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
    trail.Enabled = false
    trail.Parent = holder
    holder.Parent = rig.model -- goes when the pet goes
    return { part = holder, trail = trail }
end

local function animateTheNamelessOne(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > NAMELESS_FAR then
        namelessGone(rig, s, 0)
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special, Unwritten: both arms rise, forward and apart; at the burst its writing appears round it (Blasts.Unwritten) and its hands trace it;
    -- each word is struck through; and for a moment it is gone, then back
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local raise = smoothstep(0.04, 0.36, progress) * (1 - smoothstep(0.62, 0.72, progress))
    local write = smoothstep(0.4, 0.45, progress) * (1 - smoothstep(0.6, 0.66, progress))
    local gone = smoothstep(0.64, 0.72, progress) * (1 - smoothstep(0.8, 0.9, progress))
    namelessGone(rig, s, math.floor(gone * 20 + 0.5) / 20)

    -- now and then, while it is still, one arm lifts and its glowing ends write a loop in the air
    s.penSide = s.penSide or (if math.random() < 0.5 then "L" else "R")
    s.nextWrite = s.nextWrite or t + 5 + math.random() * 6
    local pen = 0
    if t >= s.nextWrite then
        local a = (t - s.nextWrite) / 2.6
        if a >= 1 then
            s.nextWrite = t + 9 + math.random() * 9
            s.penSide = if math.random() < 0.5 then "L" else "R"
        elseif pace < 0.3 and nova == 0 then
            pen = smoothstep(0, 0.25, a) * (1 - smoothstep(0.78, 1, a))
        else
            s.nextWrite = t + 4
        end
    end

    -- it floats: a slow bob, leaning into its way when it moves, banking on turns
    local look = rig.rootPart.CFrame.LookVector
    local heading = math.atan2(-look.X, -look.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
    local bob = 0.022 * math.sin(t * 1.1) + 0.008 * math.sin(t * 2.3 + 1)
    local lift = namelessHover(rig, s, t, u, fly)
    pose(m.Hips, CFrame.new(0, (bob + 0.05 * raise) * u + lift, 0) * CFrame.Angles(-0.14 * moving - 0.22 * fly + 0.03 * raise, 0.04 * math.sin(t * 0.37), s.bank + 0.025 * math.sin(t * 0.53)))
    pose(m.Body, CFrame.Angles(0.02 * math.sin(t * 1.1 - 0.6) - 0.04 * moving, 0.03 * math.sin(t * 0.41 + 1), 0))
    pose(m.Chest, CFrame.Angles(0.015 * math.sin(t * 1.1 - 1.2) + 0.08 * raise, 0.04 * math.sin(t * 0.33 + 2), 0))

    -- the hood turns toward you and tilts, slowly, as if reading you; it watches its own hand when it writes, and looks up at its writing
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    local calm = (1 - pace) * (1 - raise) * (1 - pen)
    local wantYaw = math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) * calm + (if s.penSide == "L" then 0.45 else -0.45) * pen
    local wantPitch = math.clamp(toYou.Y, -0.5, 0.6) * 0.5 * calm - 0.3 * pen + 0.22 * raise
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
    local roll = (0.22 * math.sin(t * 0.31) + 0.06 * math.sin(t * 0.83)) * (1 - pace) * (1 - raise)
    pose(m.Neck, CFrame.Angles(0.4 * s.pitch, 0.4 * s.yaw, 0.3 * roll))
    pose(m.Head, CFrame.Angles(0.6 * s.pitch, 0.6 * s.yaw, 0.7 * roll))

    -- the point of light drifts in the hollow; the broken halo turns, fast while it writes, and burns white
    pose(m.Spark, CFrame.new(0.004 * math.sin(t * 1.7) * u, 0.003 * math.sin(t * 2.3 + 1) * u, 0))
    s.halo = ((s.halo or 0) + dt * (0.25 + 2.5 * raise + 4 * write)) % (2 * math.pi)
    pose(m.Halo, CFrame.new(0, 0.006 * math.sin(t * 0.9) * u, 0) * CFrame.Angles(0, 0, s.halo))
    local burn = NAMELESS_HALO:Lerp(NAMELESS_SPARK, math.max(0.6 * write, 0.4 * pen))
    for _, key in { "Halo", "QuillL", "QuillR" } do
        local part = rig.parts[key]
        if part then
            part.Color = burn
        end
    end
    if not s.namelessLight and rig.points.Spark then
        local light = Instance.new("PointLight")
        light.Color = NAMELESS_SPARK
        light.Range = 0.5 * u
        light.Shadows = false
        light.Parent = rig.points.Spark
        s.namelessLight = light
    end
    if s.namelessLight then
        s.namelessLight.Brightness = 0.8 + 0.3 * math.sin(t * 2.1) + 2.5 * write
    end

    -- the arms hang and sway, trail behind as it goes, rise for the special; the writing hand traces small loops
    s.pens = s.pens or {}
    for _, side in { "L", "R" } do
        local out = if side == "L" then -1 else 1 -- a positive turn about Z swings a hanging arm out to its right; to its left, a negative one
        local mine = if side == s.penSide then pen else 0
        local phase = if side == "L" then 0 else 1.7
        pose(m["Arm" .. side .. "1"], CFrame.Angles(0.04 * math.sin(t * 0.8 + phase) - 0.18 * moving - 0.25 * fly + 1.25 * raise + 1.0 * mine, 0, out * (0.03 + 0.45 * raise + 0.12 * mine)))
        pose(m["Arm" .. side .. "2"], CFrame.Angles(0.05 + 0.04 * math.sin(t * 0.8 + phase + 0.5) + 0.35 * raise + 0.75 * mine, 0, 0))
        local loop = math.max(write, mine)
        local w = t * 9 + phase
        pose(m["Arm" .. side .. "3"], CFrame.Angles(0.3 * loop * math.sin(w) + 0.05 * math.sin(t * 1.1 + phase), 0.3 * loop * math.cos(w), 0))
        pose(m["Arm" .. side .. "4"], CFrame.Angles(0.12 * math.sin(t * 1.3 + phase) - 0.25 * moving - 0.3 * fly, 0, 0.08 * math.sin(t * 1.1 + phase)))
        pose(m["Arm" .. side .. "5"], CFrame.Angles(0.16 * math.sin(t * 1.3 + phase - 0.8) - 0.3 * moving - 0.35 * fly, 0, 0.1 * math.sin(t * 1.1 + phase - 0.7)))
        local active = (mine > 0.4 or write > 0.4) and gone < 0.5
        if active and not s.pens[side] then
            s.pens[side] = namelessPen(rig)
        end
        local holder = s.pens[side]
        local bone = rig.points["Arm" .. side .. "5"]
        if holder and bone then
            holder.part.CFrame = CFrame.new(bone.TransformedWorldCFrame:PointToWorldSpace(NAMELESS_TIP[side] * u))
            holder.trail.Enabled = active
        end
    end

    -- the streamers drift out and back, each on its own wave, swirl a little, stream behind it as it goes, and flare at the burst
    for k, hem in NAMELESS_HEM do
        for i, tag in { "a", "b", "c" } do
            local outward = (0.03 + 0.03 * math.sin(t * 1.2 + hem.phase - i * 0.7)) * (1 - 0.5 * pace) + 0.14 * write
            local back = -(0.07 * moving + 0.1 * fly) * (0.6 + 0.4 * i)
            pose(m["Hem" .. k .. tag], CFrame.Angles(back, 0.05 * math.sin(t * 0.9 + hem.phase - i * 0.6), 0) * CFrame.fromAxisAngle(hem.axis, outward))
        end
    end
    -- the scarves rise and ripple on the same current, blown back as it goes
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        for i = 1, 3 do
            local wave = math.sin(t * 1.15 + (if side == "L" then 0 else 2) - i * 0.9)
            pose(m["Scarf" .. side .. i], CFrame.Angles(0.04 * i * wave + (0.08 * moving + 0.12 * fly) * (0.5 + 0.25 * i), 0.05 * math.sin(t * 0.7 - i * 0.8 + sign), sign * 0.04 * wave))
        end
    end
end

-- The Eclipse Cat (skinned): a stylized black cat with a crescent tail, after the owner's concept sheet. It walks a cat's lateral walk with its tail
-- held high; still for a few seconds, it sits, its tail lying behind it; its gaze wanders and now and then settles on you with a slow blink, the
-- way a cat tells someone it trusts them; its ears swivel on their own, its tail sways and the tip flicks; gold and violet sparkles drift off it.
local CAT_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local CAT_SOLE = 0.5573 -- metres from the middle of its box down to its paws: it walks on the ground
local CAT_LID_HINGE = { L = Vector3.new(0.8802, -0.3085, -0.3606), R = Vector3.new(0.8802, 0.3085, 0.3606) } -- both lids of an eye turn on this line
local CAT_BLINK_UPPER, CAT_BLINK_LOWER = math.rad(42), math.rad(18)
local CAT_LEADS = { BL = 0, FL = math.pi / 2, BR = math.pi, FR = 3 * math.pi / 2 } -- a lateral walk: a hind foot, then the fore on its side
-- its sit, found by a search in Blender over these joints (paws flat on the ground, the seat down): the same numbers as eclipse_cat.py's SIT
local CAT_SIT = { body = 0.38, drop = 0.045, back = 0.02, hips = 0.7, fore = -0.38, thigh = -0.4, shin = -1.1, hock = 0.42 }
local CAT_SIT_TAIL = { { 0.5, 1.1 }, { 0.2, 0.7 }, { 0, 0.6 }, { -0.1, 0.5 }, { 0, 0.4 }, { 0, 0.3 } }
local CAT_SUN, CAT_CORONA = Color3.fromRGB(255, 210, 120), Color3.fromRGB(255, 244, 214)

local function catSparkles(rig, s)
    s.sparkles = true
    local tip = rig.points.Tail6
    if not tip then
        return
    end
    local sparkles = Instance.new("ParticleEmitter")
    sparkles.Name = "Sparkles"
    sparkles.Texture = SPARKLE
    sparkles.Rate = 2.2
    sparkles.Lifetime = NumberRange.new(1.2, 2)
    sparkles.Speed = NumberRange.new(0.05 * rig.unit, 0.2 * rig.unit)
    sparkles.SpreadAngle = Vector2.new(180, 180)
    sparkles.Acceleration = Vector3.new(0, 0.12 * rig.unit, 0)
    sparkles.Drag = 1
    sparkles.Rotation = NumberRange.new(0, 360)
    sparkles.RotSpeed = NumberRange.new(-40, 40)
    sparkles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.09 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
    sparkles.Color = ColorSequence.new(Color3.fromRGB(255, 214, 130), Color3.fromRGB(176, 124, 255))
    sparkles.LightEmission = 1
    sparkles.LightInfluence = 0
    sparkles.Parent = tip
end

local function animateEclipseCat(rig, s, moving, fly, nova)
    if not s.sparkles then
        catSparkles(rig, s)
    end
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > CAT_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, CAT_SOLE)

    -- the special, Totality: it sits and looks up to the sky as the moon crosses the sun (Blasts.Totality); at totality it purrs, a tremor through
    -- it, its eyes wide; then the light comes back
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local look = smoothstep(0.04, 0.3, progress) * (1 - smoothstep(0.78, 0.95, progress))
    local purr = smoothstep(0.42, 0.47, progress) * (1 - smoothstep(0.68, 0.78, progress))

    -- it sits after a few seconds still, and for its special; it gets up as soon as it has somewhere to go
    s.still = if pace < 0.05 then (s.still or 0) + dt else 0
    local wantSit = if pace > 0.1 then 0 elseif nova > 0 or s.still > 4 then 1 else 0
    s.sit = (s.sit or 0) + (wantSit - (s.sit or 0)) * math.min(1, dt * (if wantSit > (s.sit or 0) then 2.4 else 6))
    local sit = smoothstep(0, 1, s.sit)

    -- the legs: a lateral walk; in the air a stretched leap, forelegs reaching, hind legs pushed back; folded into the sit
    s.stride = (s.stride or 0) + dt * (8.5 * moving + 2 * fly)
    for key, lead in CAT_LEADS do
        local phase = s.stride + lead
        local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
        local p1, p2, p3, p4
        if string.sub(key, 1, 1) == "F" then
            p1 = moving * 0.4 * swing + fly * 0.8
            p2 = moving * 0.1 * lift
            p3 = -moving * 0.9 * lift - fly * 0.35
            p4 = -moving * 0.3 * lift
            p1 = p1 * (1 - sit) + CAT_SIT.fore * sit
            p2, p3, p4 = p2 * (1 - sit), p3 * (1 - sit), p4 * (1 - sit)
        else
            p1 = -moving * 0.4 * swing - fly * 0.8
            p2 = moving * 0.45 * lift + fly * 0.45
            p3 = -moving * 0.6 * lift
            p4 = 0
            p1 = p1 * (1 - sit) + CAT_SIT.thigh * sit
            p2 = p2 * (1 - sit) + CAT_SIT.shin * sit
            p3 = p3 * (1 - sit) + CAT_SIT.hock * sit
        end
        pose(m["Leg" .. key .. "1"], CFrame.Angles(p1, 0, 0))
        pose(m["Leg" .. key .. "2"], CFrame.Angles(p2, 0, 0))
        pose(m["Leg" .. key .. "3"], CFrame.Angles(p3, 0, 0))
        pose(m["Paw" .. key], CFrame.Angles(p4, 0, 0))
    end

    -- the body: a slight sway with its steps, banking on turns, a purr's tremor; lowered and tipped back into the sit
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
    local breath = math.sin(t * 1.6)
    local tremor = 0.0015 * purr * math.sin(t * 62)
    pose(m.Body, CFrame.new(0, (0.003 * breath + tremor - CAT_SIT.drop * sit + 0.012 * moving * math.abs(math.sin(s.stride))) * u - drop, CAT_SIT.back * sit * u)
        * CFrame.Angles(CAT_SIT.body * sit + 0.1 * fly, 0.04 * moving * math.sin(s.stride), s.bank))
    pose(m.Hips, CFrame.Angles(CAT_SIT.hips * sit - 0.05 * fly, -0.05 * moving * math.sin(s.stride), 0))
    pose(m.Chest, CFrame.Angles(0.01 * breath, 0.03 * moving * math.sin(s.stride + 1), 0))

    -- its gaze wanders; now and then it turns to you and holds; it looks to the sky in the special; a curious tilt of the head
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2 + math.random() * 3.5
        s.atYou = math.random() < 0.45
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.9, (math.random() - 0.5) * 0.3
        s.tilt = if math.random() < 0.3 then (math.random() - 0.5) * 0.5 else 0
    end
    local calm = (1 - 0.7 * pace) * (1 - look)
    local wantYaw = if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.9, 0.9) else s.gazeYaw
    local wantPitch = if s.atYou then math.clamp(toYou.Y * 0.6, -0.3, 0.4) else s.gazePitch
    s.yaw = (s.yaw or 0) + (wantYaw * calm - (s.yaw or 0)) * math.min(1, dt * 3)
    s.pitch = (s.pitch or 0) + (wantPitch * calm - (s.pitch or 0)) * math.min(1, dt * 3)
    s.headTilt = (s.headTilt or 0) + ((s.tilt or 0) * calm - (s.headTilt or 0)) * math.min(1, dt * 2.5)
    pose(m.Neck, CFrame.Angles(0.3 * s.pitch + 0.25 * look - 0.08 * moving + 0.015 * breath, 0.4 * s.yaw, 0))
    pose(m.Head, CFrame.Angles(0.5 * s.pitch + 0.55 * look + 0.03 * moving * math.sin(2 * s.stride), 0.6 * s.yaw, s.headTilt))
    for _, side in { "L", "R" } do
        pose(m["Eye" .. side], CFrame.Angles(0.25 * s.pitch, 0.25 * s.yaw, 0))
    end

    -- the eyes: quick blinks; a slow blink when it is looking at you; content, half-lidded, when it sits; wide in the special
    s.nextBlink = s.nextBlink or t + 2
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / (if s.slowBlink then 1.4 else 0.18)
        if a >= 1 then
            s.nextBlink = t + 2.5 + math.random() * 3.5
            s.slowBlink = s.atYou and math.random() < 0.6
        else
            blink = if s.slowBlink then smoothstep(0, 0.4, a) * (1 - smoothstep(0.6, 1, a)) * 0.8 else 1 - math.abs(2 * a - 1)
        end
    end
    local close = math.max(blink, 0.22 * sit * (1 - look)) * (1 - 0.8 * look)
    local upper = CAT_BLINK_UPPER * close - math.rad(6) * look
    local lower = CAT_BLINK_LOWER * close - math.rad(4) * look
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(CAT_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(CAT_LID_HINGE[side], lower))
    end

    -- the ears: each swivels on its own now and then; laid back in the leap
    for _, side in { "L", "R" } do
        local sign = if side == "L" then -1 else 1
        local offset = if side == "L" then 0 else 2.6
        local swivel = math.max(0, math.sin(t * 0.7 + offset)) ^ 10
        pose(m["Ear" .. side], CFrame.Angles(-0.35 * fly - 0.12 * swivel, sign * (0.35 * swivel + 0.2 * fly), 0))
    end

    -- the tail: a slow sway along it, the tip flicking now and then; streaming in the leap; lying behind it in the sit
    for k = 1, 6 do
        local wave = math.sin(t * 1.1 - k * 0.55)
        local sway = (0.05 + 0.05 * k / 6) * wave * (1 - 0.6 * sit) * (1 - 0.5 * fly)
        local flick = if k >= 5 then 0.2 * math.max(0, math.sin(t * 2.3 + k)) ^ 8 else 0
        local rest = CAT_SIT_TAIL[k]
        pose(m["Tail" .. k], CFrame.Angles(rest[1] * sit - 0.1 * fly + 0.015 * math.sin(t * 0.8 - k * 0.6), rest[2] * sit + sway + flick, 0))
    end

    -- the pendant swings with it
    pose(m.Pendant, CFrame.Angles(0.15 * moving * math.sin(2 * s.stride) - 0.12 * fly + 0.03 * math.sin(t * 1.3), 0, 0.06 * math.sin(t * 0.9)))
end

-- The Shadowcoil (skinned): a shadow stoat, ink black, with wisps of smoke along its back and a tail that coils like a curl of smoke. It bounds
-- the way a stoat does, forepaws then hind paws, its back humping; still a moment, it rears up on its hind legs to look about; still a while
-- longer, it lies down curled, its tail coiled behind it, and dozes; its glances are quick and sly, its eyes darting ahead of its head; a
-- faint smoke drifts off its tail.
local SHADOW_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local SHADOW_SOLE = 0.3253 -- metres from the middle of its box down to its paws: it runs on the ground
local SHADOW_LID_HINGE = { L = Vector3.new(0.8851, -0.1728, -0.4322), R = Vector3.new(0.8851, 0.1728, 0.4322) } -- both lids of an eye turn on this line
local SHADOW_BLINK_UPPER, SHADOW_BLINK_LOWER = math.rad(62), math.rad(22)
local SHADOW_SINK = 0.7 -- metres it pours itself down into its shadow in the special: all of its height
local SHADOW_INK, SHADOW_RIM, SHADOW_EYESHINE = Color3.fromRGB(12, 7, 24), Color3.fromRGB(118, 92, 196), Color3.fromRGB(168, 255, 224)
local SHADOW_LIE_DROP = 0.097 -- metres its hips come down when it lies
-- its poses, each checked in Blender against the ground and for torn skin: the same numbers as shadowcoil.py's Gather, Stretch, REAR and LIE
local SHADOW_GATHER = {
    Hips = { -0.25, 0, 0 }, Body = { 0.2, 0, 0 }, Chest = { 0.15, 0, 0 },
    LegFL1 = { -0.6, 0, 0 }, LegFR1 = { -0.6, 0, 0 }, LegBL1 = { 0.7, 0, 0 }, LegBR1 = { 0.7, 0, 0 }, LegBL2 = { -0.4, 0, 0 }, LegBR2 = { -0.4, 0, 0 },
}
local SHADOW_STRETCH = {
    Hips = { 0.15, 0, 0 }, Body = { -0.1, 0, 0 },
    LegFL1 = { 0.75, 0, 0 }, LegFR1 = { 0.75, 0, 0 }, LegBL1 = { -0.75, 0, 0 }, LegBR1 = { -0.75, 0, 0 }, LegBL2 = { 0.4, 0, 0 }, LegBR2 = { 0.4, 0, 0 },
}
local SHADOW_REAR = {
    Body = { 1.05, 0, 0 }, Chest = { -0.15, 0, 0 }, Neck = { -0.35, 0, 0 }, Head = { -0.4, 0, 0 },
    LegFL1 = { -0.9, 0, 0 }, LegFR1 = { -0.9, 0, 0 }, LegFL2 = { 0.9, 0, 0 }, LegFR2 = { 0.9, 0, 0 }, LegFL3 = { 0.6, 0, 0 }, LegFR3 = { 0.6, 0, 0 },
}
local SHADOW_LIE = {
    Body = { 0, 0.25, 0 }, Chest = { 0, 0.3, 0 }, Shoulders = { 0, 0.3, 0 }, Neck = { 0.1, 0.35, 0 }, Head = { 0.05, 0.3, 0 },
    LegFL1 = { -0.557, 0, 0 }, LegFR1 = { -0.557, 0, 0 }, LegFL2 = { -1.459, 0, 0 }, LegFR2 = { -1.459, 0, 0 }, LegFL3 = { -0.624, 0, 0 }, LegFR3 = { -0.624, 0, 0 },
    LegBL1 = { 0.646, 0, 0 }, LegBR1 = { 0.646, 0, 0 }, LegBL2 = { -1.205, 0, 0 }, LegBR2 = { -1.205, 0, 0 }, LegBL3 = { 0.865, 0, 0 }, LegBR3 = { 0.865, 0, 0 },
    Tail1 = { 0, 0.03, 0 }, Tail2 = { 0.14, 0.03, 0 }, Tail3 = { -0.55, 0, 0 }, Tail4 = { -0.27, 0, 0 },
}

-- every bone it poses through its stances (the lids turn on their hinges on their own)
local function shadowBones()
    local bones = { "Hips", "Body", "Chest", "Shoulders", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR" }
    for k = 1, 7 do
        table.insert(bones, "Tail" .. k)
    end
    for _, key in { "FL", "FR", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(bones, "Leg" .. key .. k)
        end
        table.insert(bones, "Paw" .. key)
    end
    return bones
end
local SHADOW_BONES = shadowBones()

-- adds a stance (bone: { rx, ry, rz }), scaled by weight, into a table of wanted turns: a pet blends its poses by adding them
local function addStance(into, stance, weight)
    if weight <= 0 then
        return
    end
    for bone, a in stance do
        into[bone] = (into[bone] or Vector3.zero) + Vector3.new(a[1], a[2], a[3]) * weight
    end
end

-- a flat disc of shadow on the ground: a cylinder stood on its end; its top at `top` metres above the ground
local function shadowDisc(part, ground, top, thickness, width, metre)
    part.Size = Vector3.new(thickness * metre, width * metre, width * metre)
    part.CFrame = CFrame.new(ground + Vector3.new(0, (top - thickness / 2) * metre, 0)) * CFrame.Angles(0, 0, math.pi / 2)
end

-- its skin and the glints in its eyes go together: 0, all there; 1, gone
local function shadowGone(rig, s, gone)
    if s.gone == gone then
        return
    end
    s.gone = gone
    for _, key in { "Body", "Glints" } do
        local part = rig.parts[key]
        if part then
            part.Transparency = gone
        end
    end
    if s.smoke then
        s.smoke.Enabled = gone < 0.5
    end
end

local function shadowSmoke(rig, s)
    s.smokeMade = true
    local tip = rig.points.Tail7
    if not tip then
        return
    end
    local smoke = Instance.new("ParticleEmitter")
    smoke.Name = "Smoke"
    smoke.Texture = "rbxasset://textures/particles/smoke_main.dds"
    smoke.Rate = 2.5
    smoke.Lifetime = NumberRange.new(1.4, 2.2)
    smoke.Speed = NumberRange.new(0.02 * rig.unit, 0.08 * rig.unit)
    smoke.SpreadAngle = Vector2.new(180, 180)
    smoke.Acceleration = Vector3.new(0, 0.1 * rig.unit, 0)
    smoke.Drag = 1.5
    smoke.Rotation = NumberRange.new(0, 360)
    smoke.RotSpeed = NumberRange.new(-25, 25)
    smoke.Size = NumberSequence.new(0.08 * rig.unit, 0.3 * rig.unit)
    smoke.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.72), NumberSequenceKeypoint.new(1, 1) })
    smoke.Color = ColorSequence.new(Color3.fromRGB(84, 70, 120), Color3.fromRGB(34, 26, 52))
    smoke.LightEmission = 0
    smoke.LightInfluence = 0.6
    smoke.Parent = tip
    s.smoke = smoke
end

-- the shadow it pours itself into before the special's loop (Blasts.FirstMove carries on from it): the model's own, so it goes when the pet goes
local function shadowPool(rig)
    local pool = {}
    for _, look in { { "ShadowPool", SHADOW_INK, Enum.Material.SmoothPlastic }, { "ShadowRim", SHADOW_RIM, Enum.Material.Neon } } do
        local part = Instance.new("Part")
        part.Name = look[1]
        part.Shape = Enum.PartType.Cylinder
        part.Color = look[2]
        part.Material = look[3]
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part.Transparency = 1
        part.Size = Vector3.one * 0.05
        part.CFrame = rig.rootPart.CFrame
        part.Parent = rig.model
        table.insert(pool, part)
    end
    return pool
end

local function animateShadowcoil(rig, s, moving, fly, nova)
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special, First Move: it crouches, eyes wide; pours itself down into its own shadow and is gone; the shadow races round a loop on the
    -- ground (Blasts.FirstMove) and back; it bursts up out of it in a leap and lands where it was
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local notice = smoothstep(0, 0.08, progress) * (1 - smoothstep(0.12, 0.3, progress))
    local sink = smoothstep(0.12, 0.4, progress) * (1 - smoothstep(0.73, 0.8, progress))
    local hop = if progress > 0.76 and progress < 0.92 then math.sin(math.pi * (progress - 0.76) / 0.16) else 0
    -- (before the far check: it must come back whether or not anyone is watching)
    shadowGone(rig, s, smoothstep(0.2, 0.38, progress) * (1 - smoothstep(0.72, 0.77, progress)))
    local pooling = progress > 0.06 and progress < PetRig.NOVA_BURST
    if pooling or s.poolShown then
        s.pool = s.pool or shadowPool(rig)
        s.poolShown = pooling
        local ground = rig.rootPart.Position - Vector3.new(0, SHADOW_SOLE * u + (s.drop or 0), 0)
        local grow = smoothstep(0.08, 0.36, progress)
        shadowDisc(s.pool[1], ground, 0.02, 0.012, 0.15 + 0.65 * grow, u)
        shadowDisc(s.pool[2], ground, 0.0145, 0.014, (0.15 + 0.65 * grow) * 1.12, u)
        local show = if pooling then smoothstep(0.06, 0.2, progress) else 0
        s.pool[1].Transparency = 1 - 0.88 * show
        s.pool[2].Transparency = 1 - 0.45 * show
    end

    if not s.smokeMade then
        shadowSmoke(rig, s)
    end
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SHADOW_FAR then
        return
    end
    local drop = dropToGround(rig, s, t, u, fly, SHADOW_SOLE)
    local special = progress > 0

    -- still a moment, it rears up to look about, now and then; still a while, it lies down; it is up and away as soon as it has somewhere to go
    s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
    local wantLie = if s.still > 9 then 1 else 0
    if s.still > 2.5 and wantLie == 0 and t >= (s.nextRear or 0) then
        s.rearUntil = t + 1.8 + math.random() * 1.2
        s.nextRear = s.rearUntil + 3 + math.random() * 4
    end
    local wantRear = if s.still > 2.5 and wantLie == 0 and t < (s.rearUntil or 0) then 1 else 0
    s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1.2 else 6))
    s.rear = (s.rear or 0) + (wantRear - (s.rear or 0)) * math.min(1, dt * (if wantRear > (s.rear or 0) then 5 else 4))
    local lie, rear = smoothstep(0, 1, s.lie), smoothstep(0, 1, s.rear)

    -- the bound: gathered, back humped and hind paws under it, then stretched out, forelegs reaching; each pair folds its paws as it swings
    -- through; in the air a long stretched leap
    s.stride = (s.stride or 0) + dt * 9 * moving
    local g = math.sin(s.stride)
    local onFoot = moving * (1 - fly)
    local gathered, stretched = math.max(0, g) * onFoot + 0.5 * notice, math.max(0, -g) * onFoot
    local want = {}
    addStance(want, SHADOW_GATHER, gathered)
    addStance(want, SHADOW_STRETCH, math.min(1, stretched + 0.9 * fly + hop))
    addStance(want, SHADOW_REAR, rear)
    addStance(want, SHADOW_LIE, lie)
    local frontLift = math.max(0, -math.cos(s.stride)) * onFoot
    local hindLift = math.max(0, math.cos(s.stride)) * onFoot
    for _, side in { "L", "R" } do
        addStance(want, { ["LegF" .. side .. "2"] = { -0.3, 0, 0 }, ["LegF" .. side .. "3"] = { -0.5, 0, 0 }, ["PawF" .. side] = { -0.2, 0, 0 } }, frontLift)
        addStance(want, { ["LegB" .. side .. "2"] = { -0.35, 0, 0 }, ["LegB" .. side .. "3"] = { 0.4, 0, 0 } }, hindLift)
    end

    -- the body: banking on turns, breathing, slower and deeper lying down
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
    addStance(want, { Hips = { 0, 0, s.bank }, Chest = { 0.012 * math.sin(t * 1.7), 0, 0 }, Body = { 0.015 * lie * math.sin(t * 1.1), 0, 0 } }, 1)

    -- its gaze: quick sly glances, the eyes darting ahead and the head following; often at you; wider when it rears to look about
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 0.7 + math.random() * 1.5
        s.atYou = math.random() < 0.4
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.4, (math.random() - 0.5) * 0.3
    end
    local calm = 1 - 0.7 * pace
    local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw * (1 + 0.3 * rear)) * calm
    local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.6, -0.25, 0.35) else s.gazePitch + 0.1 * rear) * calm
    s.eyeYaw = (s.eyeYaw or 0) + (wantYaw - (s.eyeYaw or 0)) * math.min(1, dt * 14)
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 5)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 5)
    local turn = 1 - 0.5 * lie
    addStance(want, {
        Neck = { 0.3 * s.pitch - 0.06 * moving, 0.4 * s.yaw * turn, 0 },
        Head = { 0.5 * s.pitch, 0.6 * s.yaw * turn, 0 },
    }, 1)
    local eyeYaw = math.clamp(0.25 * s.yaw + (s.eyeYaw - s.yaw), -0.3, 0.3)
    addStance(want, { EyeL = { 0.25 * s.pitch, eyeYaw, 0 }, EyeR = { 0.25 * s.pitch, eyeYaw, 0 } }, 1)

    -- the ears: each twitches on its own now and then; laid back in the leap and as it goes down into its shadow
    local flat = math.max(notice, sink, 0.6 * fly)
    for _, side in { "L", "R" } do
        local sign = if side == "L" then 1 else -1
        local twitch = math.max(0, math.sin(t * 0.8 + (if side == "L" then 0 else 2.3))) ^ 12
        addStance(want, { ["Ear" .. side] = { -0.15 * twitch - 0.4 * flat, sign * (0.3 * twitch + 0.3 * flat), 0 } }, 1)
    end

    -- the tail: smoke drifting, a slow wave along it; bobbing with the bound and streaming behind it at speed; coiled behind it lying down
    for k = 1, 7 do
        local sway = (0.035 + 0.05 * k / 7) * math.sin(t * 0.9 - k * 0.55) * (1 - 0.6 * lie) * (1 - 0.5 * fly)
        local drift = 0.03 * math.sin(t * 0.6 - k * 0.7)
        local stream = (if k <= 3 then 0.07 else 0.03) * pace + (if k == 1 then 0.06 * g * onFoot else 0)
        addStance(want, { ["Tail" .. k] = { drift + stream, sway, 0 } }, 1)
    end

    for _, name in SHADOW_BONES do
        local a = want[name] or Vector3.zero
        -- (its hips rise by what each phase of the bound needs to keep every paw on or above the ground, measured in Blender)
        local lift = if name == "Hips"
            then (0.027 * gathered + 0.014 * stretched + 0.034 * frontLift - SHADOW_LIE_DROP * lie - SHADOW_SINK * sink + 0.2 * hop) * u - drop
            else 0
        pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
    end

    -- the eyes: quick blinks; a sly half-lid when it looks at you; heavy lids lying down, now and then shut a while; wide as it notices
    s.nextBlink = s.nextBlink or t + 2
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.16
        if a >= 1 then
            s.nextBlink = t + 2 + math.random() * 3
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local doze = smoothstep(0.3, 0.9, 0.5 + 0.5 * math.sin(t * 0.4))
    local close = math.max(blink, (if s.atYou then 0.22 else 0) * (1 - pace), lie * (0.55 + 0.45 * doze)) * (1 - notice)
    local upper = SHADOW_BLINK_UPPER * close - math.rad(6) * notice
    local lower = SHADOW_BLINK_LOWER * close - math.rad(5) * notice
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(SHADOW_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(SHADOW_LID_HINGE[side], lower))
    end
end

-- The Celestial Pearl Dragon (skinned): a fierce winged dragon of pearl-white nacre that holds its pearl to its chest in its right forefoot. Standing,
-- it keeps its great wings raised behind it, breathing with it, and now and then flexes them and settles; its head moves slowly and deliberately, its
-- stare holding on you; its tail sways. It never walks on three legs: to go anywhere it lifts off on heavy wingbeats and hovers low, its legs tucked,
-- its tail streaming.
local PEARL_FAR = 110 -- studs from the camera past which nobody can see it fidget: its bones rest
local PEARL_SOLE = 0.5741 -- metres from the middle of its box down to its feet: it stands on the ground
local PEARL_LID_HINGE = { L = Vector3.new(0.7386, -0.308, -0.5997), R = Vector3.new(0.7386, 0.308, 0.5997) } -- both lids of an eye turn on this line
local PEARL_BLINK_UPPER, PEARL_BLINK_LOWER = math.rad(40), math.rad(20)
local PEARL_HOVER = 0.32 -- metres it hovers above the ground when it goes anywhere
local PEARL_GLOW = Color3.fromRGB(255, 230, 214)

local function pearlWings(lift, sweep, elbow, hand, fan)
    local out = {}
    for tag, sign in { L = 1, R = -1 } do
        out["Wing" .. tag .. "1"] = { 0, sweep * sign, -lift * sign }
        out["Wing" .. tag .. "2"] = { 0, elbow * sign, 0 }
        out["Wing" .. tag .. "3"] = { 0, hand * sign, 0 }
        for j = 0, 3 do
            out["Wing" .. tag .. "F" .. (j + 1)] = { 0, fan * sign * j / 3, 0 }
        end
    end
    return out
end

-- its poses, each checked in Blender against the ground and for torn skin: the same numbers as celestial_pearl_dragon.py's FLEX, BEAT_UP, BEAT_DOWN, TUCK
-- and REAR
local PEARL_FLEX = pearlWings(-0.15, 0.1, 0, -0.2, 0.3)
local PEARL_BEAT_UP = pearlWings(0.45, -0.1, 0, 0, 0)
local PEARL_BEAT_DOWN = pearlWings(-0.7, 0.05, 0, 0.15, 0)
local PEARL_TUCK = {
    LegFL1 = { 0.5, 0, 0 }, LegFL2 = { -1.0, 0, 0 }, LegFL3 = { 0.5, 0, 0 },
    LegBL1 = { -0.6, 0, 0 }, LegBL2 = { 0.7, 0, 0 }, LegBR1 = { -0.6, 0, 0 }, LegBR2 = { 0.7, 0, 0 },
}
local PEARL_REAR = {
    Body = { 0.611, 0, 0 }, Chest = { 0.15, 0, 0 }, Neck1 = { -0.2, 0, 0 }, Neck2 = { -0.15, 0, 0 }, Head = { -0.25, 0, 0 },
    LegFL1 = { -0.386, 0, 0 }, LegFL2 = { 0.344, 0, 0 }, LegFL3 = { 0.059, 0, 0 }, ArmR2 = { 0.3, 0, 0 },
    LegBL1 = { -0.295, 0, 0 }, LegBR1 = { -0.295, 0, 0 }, LegBL2 = { 0.008, 0, 0 }, LegBR2 = { 0.008, 0, 0 }, LegBL3 = { 0.543, 0, 0 }, LegBR3 = { 0.543, 0, 0 },
    Tail1 = { -0.055, 0, 0 }, Tail2 = { -0.028, 0, 0 },
}
for bone, a in pearlWings(0.5, -0.2, 0, 0, 0) do
    PEARL_REAR[bone] = a
end
local PEARL_REAR_DROP = -0.019 -- metres its hips move in the rear

local function pearlBones()
    local bones = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "EyeL", "EyeR", "ArmR1", "ArmR2", "ArmR3", "HandR" }
    for k = 1, 6 do
        table.insert(bones, "Tail" .. k)
    end
    for _, key in { "FL", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(bones, "Leg" .. key .. k)
        end
        table.insert(bones, "Paw" .. key)
    end
    for _, tag in { "L", "R" } do
        for k = 1, 3 do
            table.insert(bones, "Wing" .. tag .. k)
        end
        for j = 1, 4 do
            table.insert(bones, "Wing" .. tag .. "F" .. j)
        end
    end
    return bones
end
local PEARL_BONES = pearlBones() -- every bone its stances pose (the lids turn on their hinges on their own)

-- where the pearl is now: the hand's bone carries it, at the offset it had at rest
local function pearlAt(rig, s)
    local hand = rig.points.HandR
    if not hand then
        return rig.rootPart.Position
    end
    if not s.pearlOffset then
        local pearl = rig.parts.Pearl
        s.pearlOffset = if pearl then hand.TransformedWorldCFrame:PointToObjectSpace(pearl.Position) else Vector3.zero
    end
    return hand.TransformedWorldCFrame:PointToWorldSpace(s.pearlOffset)
end

-- its glow: the light and the drifting motes ride on the hand's bone, where the pearl is (a skinned piece's own CFrame stays where it was bound)
local function pearlGlow(rig, s)
    local hand = rig.points.HandR
    if not hand then
        return
    end
    local at = Instance.new("Attachment")
    at.Name = "Pearl"
    at.CFrame = CFrame.new(s.pearlOffset)
    at.Parent = hand
    local light = Instance.new("PointLight")
    light.Name = "PulseLight"
    light.Color = PEARL_GLOW
    light.Range = 5 * rig.unit
    light.Brightness = 1.4
    light.Shadows = false
    light.Parent = at
    rig.light = light
    local motes = Instance.new("ParticleEmitter")
    motes.Name = "Motes"
    motes.Texture = SPARKLE
    motes.Rate = 4
    motes.Lifetime = NumberRange.new(1.2, 2)
    motes.Speed = NumberRange.new(0.05 * rig.unit, 0.2 * rig.unit)
    motes.SpreadAngle = Vector2.new(180, 180)
    motes.Acceleration = Vector3.new(0, 0.15 * rig.unit, 0)
    motes.Drag = 1
    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.08 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
    motes.Color = ColorSequence.new(Color3.fromRGB(255, 240, 214), Color3.fromRGB(196, 176, 255))
    motes.LightEmission = 1
    motes.LightInfluence = 0
    motes.Parent = at
end

local function animatePearlDragon(rig, s, moving, fly, nova)
    if not s.pearlOffset then
        pearlAt(rig, s) -- at rest, before any pose: where the pearl sits in the hand
        pearlGlow(rig, s)
    end
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > PEARL_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, PEARL_SOLE)

    -- the special, Heaven Condensed: it rears on its hind legs, wings flared, and raises the pearl to the sky; it watches heaven's light pour down into
    -- it (Blasts.HeavenCondensed); then it lunges, head and pearl thrust forward, wings snapping down, as the light bursts out of the pearl; it settles
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local rise = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.8, 0.97, progress))
    local skyward = smoothstep(0.2, 0.4, progress) * (1 - smoothstep(0.6, 0.67, progress))
    local lunge = smoothstep(0.64, 0.69, progress) * (1 - smoothstep(0.76, 0.9, progress))

    -- on the wing: heavy beats, the body lifting on each downstroke; it hovers low when it goes anywhere, higher when it flies
    s.beat = (s.beat or 0) + dt * (4.2 + 1.2 * fly) * pace
    local stroke = math.sin(s.beat)
    local up, down = math.max(0, stroke), math.max(0, -stroke)
    local hover = (PEARL_HOVER * pace + 0.03 * pace * math.cos(s.beat)) * (1 - rise)

    local want = {}
    addStance(want, PEARL_REAR, rise)
    addStance(want, PEARL_TUCK, pace * (1 - rise))
    addStance(want, PEARL_BEAT_UP, up * pace + 0.6 * rise * (1 - lunge))
    addStance(want, PEARL_BEAT_DOWN, down * pace + lunge)
    addStance(want, {
        Neck1 = { 0.1 * skyward - 0.25 * lunge, 0, 0 }, Neck2 = { 0.15 * skyward - 0.25 * lunge, 0, 0 }, Head = { 0.3 * skyward - 0.15 * lunge, 0, 0 },
        ArmR2 = { 0.15 * skyward + 0.35 * lunge, 0, 0 }, ArmR3 = { 0.2 * lunge, 0, 0 },
    }, 1)

    -- standing: it breathes, its raised wings breathing with it; now and then they flex and settle, or it tosses its head with a snort
    local breath = math.sin(t * 1.2)
    local calmness = (1 - pace) * (1 - rise)
    s.nextFlex = s.nextFlex or t + 5
    if t >= s.nextFlex then
        s.flexAt, s.flexKind = t, if math.random() < 0.6 then "wings" else "snort"
        s.nextFlex = t + 6 + math.random() * 5
    end
    local env = if s.flexAt then math.clamp((t - s.flexAt) / 1.6, 0, 1) else 1
    local flex = math.sin(math.pi * env) * calmness
    addStance(want, PEARL_FLEX, (if s.flexKind == "wings" then flex else 0))
    addStance(want, pearlWings(0.04 * breath, 0, 0, 0, 0), calmness)
    local snort = if s.flexKind == "snort" then flex else 0
    addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Head = { 0.18 * snort * math.sin(math.pi * 2 * env), 0, 0.1 * snort } }, 1)

    -- banking on turns
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.25, 0.25) - (s.bank or 0)) * math.min(1, dt * 3)
    addStance(want, { Hips = { 0.08 * pace, 0, s.bank * pace }, Body = { -0.06 * pace, 0, 0 } }, 1)

    -- its gaze: slow and deliberate, a predator's; it settles on you and holds
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 3 + math.random() * 3.5
        s.atYou = math.random() < 0.55
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.25
    end
    local calm = (1 - 0.7 * pace) * (1 - rise)
    local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.75, 0.75) else s.gazeYaw) * calm
    local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.3) else s.gazePitch) * calm
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.2)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.2)
    addStance(want, {
        Neck2 = { 0.25 * s.pitch, 0.3 * s.yaw, 0 }, Neck3 = { 0.25 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.4 * s.pitch, 0.4 * s.yaw, 0 },
        EyeL = { 0.2 * s.pitch, 0.15 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.15 * s.yaw, 0 },
    }, 1)

    -- the tail: a slow, heavy sway; streaming out behind it on the wing
    for k = 1, 6 do
        local sway = (0.03 + 0.04 * k / 6) * math.sin(t * 0.7 - k * 0.5) * (1 - 0.6 * pace)
        addStance(want, { ["Tail" .. k] = { 0.02 * math.sin(t * 0.5 - k * 0.6) + 0.05 * pace + 0.04 * pace * math.sin(s.beat - k * 0.6), sway, 0 } }, 1)
    end

    for _, name in PEARL_BONES do
        local a = want[name] or Vector3.zero
        local lift = if name == "Hips" then (hover + 0.025 * pace * down + PEARL_REAR_DROP * rise) * u - drop else 0
        pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
    end

    -- the eyes: a slow blink now and then; wide as it watches heaven's light, narrowed in the lunge
    s.nextBlink = s.nextBlink or t + 3
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.3
        if a >= 1 then
            s.nextBlink = t + 4 + math.random() * 4
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local close = math.max(blink * (1 - skyward), 0.3 * lunge)
    local upper = PEARL_BLINK_UPPER * close - math.rad(7) * skyward
    local lower = PEARL_BLINK_LOWER * close - math.rad(5) * skyward
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(PEARL_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(PEARL_LID_HINGE[side], lower))
    end
end

-- The Celestial Snow Leopard (skinned): a grown snow leopard, a hunter of the high snow. It prowls low, head level and forward, its shoulder blades
-- rolling, its huge tail held low behind it, the tip lifting in a curl; now and then it stops, sinks into a stalking crouch and stares, its haunches
-- wiggling; still a while, it lies down sphinx-like, its tail curled round beside it. Its stare is steady and intense; its ears turn on their own; its
-- tail tip twitches. In the air it stretches out in a long leap.
local LEOPARD_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local LEOPARD_SOLE = 0.297 -- metres from the middle of its box down to its paws: it walks on the ground
local LEOPARD_LID_HINGE = { L = Vector3.new(0.939, -0.1562, -0.3064), R = Vector3.new(0.939, 0.1562, 0.3064) } -- both lids of an eye turn on this line
local LEOPARD_BLINK_UPPER, LEOPARD_BLINK_LOWER = math.rad(52), math.rad(24)
local LEOPARD_ICE, LEOPARD_STAR = Color3.fromRGB(196, 232, 255), Color3.fromRGB(140, 200, 255)
local LEOPARD_LEADS = { BL = 0, FL = math.pi / 2, BR = math.pi, FR = 3 * math.pi / 2 } -- a cat's lateral walk

local function leopardLegs(f, b)
    local out = {}
    for _, side in { "L", "R" } do
        for k = 1, 3 do
            out["LegF" .. side .. k] = { f[k], 0, 0 }
            out["LegB" .. side .. k] = { b[k], 0, 0 }
        end
    end
    return out
end

local function leopardStance(base, f, b)
    for bone, a in leopardLegs(f, b) do
        base[bone] = a
    end
    return base
end

-- its stances, each searched in Blender against the ground and for torn skin: the same numbers as celestial_snow_leopard.py's CROUCH, LIE and LEAP
local LEOPARD_CROUCH = leopardStance({ Shoulders = { 0.005, 0, 0 }, Head = { 0.228, 0, 0 } }, { -0.2, -1.387, -0.2 }, { 0.354, -0.419, 0.957 })
local LEOPARD_CROUCH_DROP = 0.098
local LEOPARD_LIE = leopardStance({ Hips = { -0.158, 0, 0 }, Shoulders = { 0.265, 0, 0 }, Head = { 0.16, 0, 0 },
    Tail1 = { 0, 0.4, 0 }, Tail2 = { 0, 0.4, 0 }, Tail3 = { 0, 0.35, 0 } }, { 0.226, 1.261, -0.698 }, { 0.23, -1.026, -0.306 })
local LEOPARD_LIE_DROP = 0.182
local LEOPARD_LEAP = leopardStance({ Hips = { -0.12, 0, 0 }, Shoulders = { -0.2, 0, 0 }, Head = { 0.155, 0, 0 } }, { 0.756, -0.247, -0.29 }, { -0.511, 0.407, -0.106 })
for k = 1, 7 do
    LEOPARD_LEAP["Tail" .. k] = { -0.05, 0, 0 }
end

local function leopardBones()
    local bones = { "Hips", "Body", "Chest", "Shoulders", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR" }
    for k = 1, 7 do
        table.insert(bones, "Tail" .. k)
    end
    for _, key in { "FL", "FR", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(bones, "Leg" .. key .. k)
        end
        table.insert(bones, "Paw" .. key)
    end
    return bones
end
local LEOPARD_BONES = leopardBones() -- every bone its stances pose (the lids turn on their hinges on their own)

-- a fine frost drifts off it: its breath of the high snow, rising from its back and tail
local function leopardFrost(rig, s)
    s.frostMade = true
    local tail = rig.points.Tail4
    if not tail then
        return
    end
    local frost = Instance.new("ParticleEmitter")
    frost.Name = "Frost"
    frost.Texture = SPARKLE
    frost.Rate = 2
    frost.Lifetime = NumberRange.new(1.4, 2.2)
    frost.Speed = NumberRange.new(0.03 * rig.unit, 0.12 * rig.unit)
    frost.SpreadAngle = Vector2.new(180, 180)
    frost.Acceleration = Vector3.new(0, 0.08 * rig.unit, 0)
    frost.Drag = 1
    frost.Rotation = NumberRange.new(0, 360)
    frost.RotSpeed = NumberRange.new(-30, 30)
    frost.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.06 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
    frost.Color = ColorSequence.new(Color3.fromRGB(240, 250, 255), LEOPARD_STAR)
    frost.LightEmission = 1
    frost.LightInfluence = 0
    frost.Parent = tail
end

local function animateSnowLeopard(rig, s, moving, fly, nova)
    if not s.frostMade then
        leopardFrost(rig, s)
    end
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > LEOPARD_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, LEOPARD_SOLE)

    -- the special, Where the Sky Begins: it sinks into a crouch, its haunches wiggling, eyes fixed (progress to 0.38); it pounces up in a long leap,
    -- frost bursting from where it sprang (Blasts.WhereTheSkyBegins, at 0.42); it lands in a crouch and rises
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local gather = smoothstep(0.02, 0.2, progress) * (1 - smoothstep(0.38, 0.43, progress)) + smoothstep(0.62, 0.68, progress) * (1 - smoothstep(0.78, 0.95, progress))
    local wiggle = smoothstep(0.15, 0.22, progress) * (1 - smoothstep(0.34, 0.39, progress))
    local leap = if progress > 0.4 and progress < 0.66 then math.sin(math.pi * (progress - 0.4) / 0.26) else 0
    local special = progress > 0

    -- still a moment, it sinks into a stalking crouch and stares, now and then; still a while, it lies down; it is up as soon as it has somewhere to go
    s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
    local wantLie = if s.still > 8 then 1 else 0
    if s.still > 2.5 and wantLie == 0 and t >= (s.nextStalk or 0) then
        s.stalkUntil = t + 2 + math.random() * 1.5
        s.nextStalk = s.stalkUntil + 2.5 + math.random() * 3
    end
    local wantStalk = if s.still > 2.5 and wantLie == 0 and t < (s.stalkUntil or 0) then 1 else 0
    s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1.2 else 6))
    s.stalk = (s.stalk or 0) + (wantStalk - (s.stalk or 0)) * math.min(1, dt * (if wantStalk > (s.stalk or 0) then 3 else 4))
    local lie, stalk = smoothstep(0, 1, s.lie), smoothstep(0, 1, s.stalk)
    local crouch = math.max(stalk, gather)

    -- the prowl: a cat's lateral walk, low and smooth, the shoulder blades rolling with each forefoot; in the air a long stretched leap
    s.stride = (s.stride or 0) + dt * 7.5 * moving
    local onFoot = moving * (1 - fly) * (1 - crouch)
    local want = {}
    addStance(want, LEOPARD_CROUCH, crouch * (1 - lie))
    addStance(want, LEOPARD_LIE, lie)
    addStance(want, LEOPARD_LEAP, math.min(1, fly * 0.9 + leap))
    for key, lead in LEOPARD_LEADS do
        local phase = s.stride + lead
        local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
        local stance
        if string.sub(key, 1, 1) == "F" then
            stance = { ["Leg" .. key .. "1"] = { 0.38 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { -0.55 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { 0.25 * lift, 0, 0 },
                ["Paw" .. key] = { -0.3 * lift, 0, 0 } }
        else
            stance = { ["Leg" .. key .. "1"] = { -0.38 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { 0.45 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { -0.55 * lift, 0, 0 } }
        end
        addStance(want, stance, onFoot)
    end
    local roll = math.sin(s.stride + math.pi / 2)
    addStance(want, { Shoulders = { 0, 0.06 * roll, 0.03 * roll }, Hips = { 0, -0.05 * roll, -0.025 * roll }, Neck = { -0.05, -0.05 * roll, 0 } }, onFoot)

    -- the body: breathing, deeper lying down; banking on turns; the haunches wiggling before a pounce
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
    local breath = math.sin(t * (1.3 - 0.4 * lie))
    local wig = math.sin(t * 18) * math.max(wiggle, 0.4 * stalk * math.max(0, math.sin(t * 0.9)) ^ 6)
    addStance(want, { Hips = { 0, 0.08 * wig, s.bank * moving }, Chest = { 0.012 * breath * (1 + lie), 0, 0 } }, 1)

    -- its stare: steady and intense, holding on you; when it crouches it locks on what is ahead
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2.5 + math.random() * 3
        s.atYou = math.random() < 0.5
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.9, (math.random() - 0.5) * 0.25
    end
    local calm = (1 - 0.7 * pace) * (1 - crouch)
    local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
    local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.25, 0.3) else s.gazePitch) * calm
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
    local turn = 1 - 0.4 * lie
    addStance(want, {
        Neck = { 0.25 * s.pitch, 0.4 * s.yaw * turn, 0 }, Head = { 0.45 * s.pitch, 0.55 * s.yaw * turn, 0 },
        EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
    }, 1)

    -- the ears: each turns on its own now and then; flattened in the crouch and the leap
    local flat = math.max(crouch, 0.5 * fly, leap)
    for _, side in { "L", "R" } do
        local sign = if side == "L" then 1 else -1
        local swivel = math.max(0, math.sin(t * 0.6 + (if side == "L" then 0 else 2.7))) ^ 10
        addStance(want, { ["Ear" .. side] = { -0.15 * swivel - 0.45 * flat, sign * (0.35 * swivel + 0.25 * flat), 0 } }, 1)
    end

    -- the tail: held low and heavy behind it, the tip lifting in a curl and twitching now and then; streaming in the leap; lashing before a pounce
    for k = 1, 7 do
        local sway = (0.025 + 0.04 * k / 7) * math.sin(t * 0.8 - k * 0.5) * (1 - 0.6 * lie)
        local twitch = if k >= 6 then 0.25 * math.max(0, math.sin(t * 2.1 + k)) ^ 10 * (1 - lie) else 0
        local lash = 0.12 * math.sin(t * 9 - k * 0.7) * math.max(wiggle, 0.5 * stalk) * k / 7
        addStance(want, { ["Tail" .. k] = { 0.02 * math.sin(t * 0.5 - k * 0.6) - 0.04 * moving, sway + twitch + lash, 0 } }, 1)
    end

    for _, name in LEOPARD_BONES do
        local a = want[name] or Vector3.zero
        local lift = if name == "Hips"
            then (-LEOPARD_CROUCH_DROP * crouch * (1 - lie) - LEOPARD_LIE_DROP * lie + 0.32 * leap + 0.006 * onFoot * math.abs(math.sin(s.stride * 2))) * u - drop
            else 0
        pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
    end

    -- the eyes: slow, rare blinks; a steady stare when it crouches; heavy lids lying down
    s.nextBlink = s.nextBlink or t + 3
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.24
        if a >= 1 then
            s.nextBlink = t + 3.5 + math.random() * 4
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local doze = smoothstep(0.3, 0.9, 0.5 + 0.5 * math.sin(t * 0.35))
    local close = math.max(blink * (1 - crouch), lie * (0.35 + 0.55 * doze)) * (1 - gather)
    local upper = LEOPARD_BLINK_UPPER * close - math.rad(5) * crouch
    local lower = LEOPARD_BLINK_LOWER * close - math.rad(4) * crouch
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(LEOPARD_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(LEOPARD_LID_HINGE[side], lower))
    end
end

-- The Comet Stag (skinned): a powerful night-blue stag whose antlers sweep back like a comet's two tails, a comet's nucleus glowing on its brow. It
-- stands proud, head high, its big ears turning on their own; now and then it tosses its antlers or paws the ground; still a long while, it lies down,
-- legs folded under it. It trots on the ground; in the air it runs on nothing in long bounds, a comet's trail streaming from its brow, and comet dust
-- drifts off the tips of its antlers.
local STAG_FAR = 110 -- studs from the camera past which nobody can see it fidget: its bones rest
local STAG_SOLE = 0.7009 -- metres from the middle of its box down to its hooves: it stands on the ground
local STAG_LID_HINGE = { L = Vector3.new(0.5963, -0.1038, -0.796), R = Vector3.new(0.5963, 0.1038, 0.796) } -- both lids of an eye turn on this line
local STAG_BLINK_UPPER, STAG_BLINK_LOWER = math.rad(58), math.rad(26)
local STAG_NUCLEUS = Vector3.new(0, 0.966, -0.452) -- its brow's nucleus, in the model's axes (metres)
local STAG_TIPS = { Vector3.new(-0.285, 1.2, 0.33), Vector3.new(0.285, 1.2, 0.33) } -- the ends of its two palms, where the comet dust comes off
local STAG_ICE, STAG_ION, STAG_DUST = Color3.fromRGB(234, 246, 255), Color3.fromRGB(110, 190, 255), Color3.fromRGB(255, 214, 140)
local STAG_TROT = { FL = 0, BR = 0, FR = math.pi, BL = math.pi } -- a trot: diagonal pairs together

local function stagLegs(f, b)
    local out = {}
    for _, side in { "L", "R" } do
        for k = 1, 3 do
            out["LegF" .. side .. k] = { f[k], 0, 0 }
            out["LegB" .. side .. k] = { b[k], 0, 0 }
        end
    end
    return out
end

local function stagStance(base, f, b)
    for bone, a in stagLegs(f, b) do
        base[bone] = a
    end
    return base
end

-- its stances, each searched in Blender against the ground and for torn skin: the same numbers as comet_stag.py's REAR, LIE and LEAP
local STAG_REAR = stagStance({ Body = { 0.573, 0, 0 }, Neck1 = { -0.15, 0, 0 }, Head = { -0.038, 0, 0 } }, { -0.067, -0.169, 0.906 }, { -0.249, -0.224, 0.02 })
local STAG_REAR_DROP = 0.061
local STAG_LIE = stagStance({ Body = { -0.171, 0, 0 }, Head = { 0.27, 0, 0 } }, { 0.569, -2.153, -0.182 }, { -0.2, -1.438, 0.638 })
local STAG_LIE_DROP = 0.311
local STAG_LEAP = stagStance({ Body = { -0.039, 0, 0 }, Head = { 0.2, 0, 0 }, Tail1 = { 0.3, 0, 0 } }, { 0.679, -1.558, 0.307 }, { -0.39, 0.255, 0.091 })
local STAG_TOSS = { Neck1 = { -0.25, 0, 0 }, Neck2 = { -0.2, 0, 0 }, Head = { -0.35, 0, 0 } }
local STAG_PAW = { LegFL1 = { 0.55, 0, 0 }, LegFL2 = { -1.1, 0, 0 }, LegFL3 = { 0.3, 0, 0 }, Neck1 = { 0.1, 0, 0 }, Head = { 0.3, 0, 0 } }

local function stagBones()
    local bones = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2" }
    for _, key in { "FL", "FR", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(bones, "Leg" .. key .. k)
        end
        table.insert(bones, "Hoof" .. key)
    end
    return bones
end
local STAG_BONES = stagBones() -- every bone its stances pose (the lids turn on their hinges on their own)

-- where a point of the model, given in its axes, is at rest in the world: measured from the nucleus glow piece, which (a skinned part) stays where it
-- was bound. Called before any pose, so the head bone stands at rest too.
local function stagAtRest(rig, point)
    local nucleus = rig.parts.Nucleus
    if not nucleus then
        return nil
    end
    return nucleus.Position + rig.rootPart.CFrame:VectorToWorldSpace((point - STAG_NUCLEUS) * rig.meters)
end

-- its light, its comet trail and the dust off its antlers: all on the head's bone, so they go where its head goes
local function stagGlow(rig, s)
    s.glowMade = true
    local head = rig.points.Head
    local at = stagAtRest(rig, STAG_NUCLEUS)
    if not (head and at) then
        return
    end
    local function attach(name, world)
        local a = Instance.new("Attachment")
        a.Name = name
        a.CFrame = head.TransformedWorldCFrame:ToObjectSpace(CFrame.new(world))
        a.Parent = head
        return a
    end
    local nucleus = attach("Nucleus", at)
    s.nucleus = nucleus
    local light = Instance.new("PointLight")
    light.Name = "PulseLight"
    light.Color = STAG_ICE
    light.Range = 5 * rig.unit
    light.Brightness = 1.4
    light.Shadows = false
    light.Parent = nucleus
    rig.light = light
    -- the comet's trail, streaming back from its brow when it runs on the air
    local up = rig.rootPart.CFrame.UpVector * 0.05 * rig.meters
    local top, bottom = attach("TrailTop", at + up), attach("TrailBottom", at - up)
    local trail = Instance.new("Trail")
    trail.Name = "CometTrail"
    trail.Attachment0, trail.Attachment1 = top, bottom
    trail.Lifetime = 0.7
    trail.FaceCamera = true
    trail.LightEmission = 1
    trail.LightInfluence = 0
    trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.15) })
    trail.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, STAG_ICE), ColorSequenceKeypoint.new(0.35, STAG_ION), ColorSequenceKeypoint.new(1, STAG_DUST) })
    trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
    trail.Enabled = false
    trail.Parent = head
    s.trail = trail
    -- comet dust drifting off the tips of its antlers
    for k, tip in STAG_TIPS do
        local world = stagAtRest(rig, tip)
        local a = attach("Tip" .. k, world)
        local dust = Instance.new("ParticleEmitter")
        dust.Name = "CometDust"
        dust.Texture = SPARKLE
        dust.Rate = 3
        dust.Lifetime = NumberRange.new(0.8, 1.4)
        dust.Speed = NumberRange.new(0.05 * rig.unit, 0.15 * rig.unit)
        dust.SpreadAngle = Vector2.new(60, 60)
        dust.Acceleration = Vector3.new(0, -0.05 * rig.unit, 0)
        dust.Drag = 1.5
        dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.06 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
        dust.Color = ColorSequence.new(STAG_DUST, STAG_ION)
        dust.LightEmission = 1
        dust.LightInfluence = 0
        dust.Parent = a
    end
end

local function animateCometStag(rig, s, moving, fly, nova)
    if not s.glowMade then
        stagGlow(rig, s) -- before any pose: the head bone is at rest
    end
    local camera = workspace.CurrentCamera
    if s.trail then
        s.trail.Enabled = fly > 0.4
    end
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > STAG_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, STAG_SOLE)

    -- the special, Once in a Lifetime: it rears, forelegs striking (to 0.4); at the burst (0.42) a comet leaves its brow and arcs across the sky
    -- (Blasts.OnceInALifetime); it watches it go, head raised and turning, and comes down
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local rise = smoothstep(0.04, 0.32, progress) * (1 - smoothstep(0.55, 0.78, progress))
    local watch = smoothstep(0.42, 0.55, progress) * (1 - smoothstep(0.82, 0.97, progress))
    local special = progress > 0

    -- still a long while, it lies down; now and then it tosses its antlers or paws the ground
    s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
    local wantLie = if s.still > 10 then 1 else 0
    s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1 else 5))
    local lie = smoothstep(0, 1, s.lie)
    s.nextFidget = s.nextFidget or t + 4
    if t >= s.nextFidget then
        s.fidgetAt, s.fidgetKind = t, if math.random() < 0.55 then "toss" else "paw"
        s.nextFidget = t + 6 + math.random() * 5
    end
    local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.4, 0, 1) else 1
    local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - lie) * (1 - rise)

    -- the trot, diagonal pairs together; in the air a bounding run on nothing, the legs reaching and folding
    s.stride = (s.stride or 0) + dt * (7 * moving + 6 * fly)
    local onFoot = moving * (1 - fly)
    local want = {}
    addStance(want, STAG_REAR, rise)
    addStance(want, STAG_LIE, lie * (1 - rise))
    addStance(want, STAG_LEAP, fly * (0.55 + 0.45 * math.sin(s.stride)))
    addStance(want, STAG_TOSS, if s.fidgetKind == "toss" then fidget else 0)
    addStance(want, STAG_PAW, if s.fidgetKind == "paw" then fidget * (0.6 + 0.4 * math.sin(t * 9)) else 0)
    for key, lead in STAG_TROT do
        local phase = s.stride + lead
        local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
        local stance
        if string.sub(key, 1, 1) == "F" then
            stance = { ["Leg" .. key .. "1"] = { 0.35 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { 0.15 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { -1.0 * lift, 0, 0 },
                ["Hoof" .. key] = { -0.3 * lift, 0, 0 } }
        else
            stance = { ["Leg" .. key .. "1"] = { -0.35 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { -0.3 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { 0.6 * lift, 0, 0 } } -- (signs found by a search in Blender: this folds the hock up)
        end
        addStance(want, stance, onFoot)
    end

    -- the body: breathing, banking on turns; head high and level as it trots
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
    local breath = math.sin(t * 1.1)
    addStance(want, { Hips = { 0, 0, s.bank * pace }, Chest = { 0.012 * breath, 0, 0 }, Neck1 = { -0.05 * onFoot, 0, 0 } }, 1)

    -- its gaze: calm, watchful, now and then on you; up and across the sky after its comet
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 2.5 + math.random() * 3.5
        s.atYou = math.random() < 0.45
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
    end
    local calm = (1 - 0.7 * pace) * (1 - rise)
    local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm - 0.6 * watch * smoothstep(0.45, 0.8, progress)
    local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.25, 0.3) else s.gazePitch) * calm + 0.45 * watch
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
    addStance(want, {
        Neck2 = { 0.3 * s.pitch, 0.35 * s.yaw * (1 - 0.4 * lie), 0 }, Head = { 0.4 * s.pitch, 0.5 * s.yaw * (1 - 0.4 * lie), 0 },
        EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
    }, 1)

    -- the ears: big and turning on their own, now and then flicking; laid back on the wing
    for _, side in { "L", "R" } do
        local sign = if side == "L" then 1 else -1
        local swivel = math.max(0, math.sin(t * 0.55 + (if side == "L" then 0 else 2.4))) ^ 8
        local flick = math.max(0, math.sin(t * 3.3 + (if side == "L" then 1 else 4))) ^ 30
        addStance(want, { ["Ear" .. side] = { -0.1 * swivel + 0.15 * flick - 0.4 * fly, sign * (0.45 * swivel + 0.3 * fly), 0 } }, 1)
    end

    -- the tail: a short flick now and then; raised in the bound
    local flick = math.max(0, math.sin(t * 1.7)) ^ 16
    addStance(want, { Tail1 = { 0.4 * flick + 0.2 * fly + 0.15 * onFoot, 0.15 * math.sin(t * 7) * flick, 0 } }, 1)

    for _, name in STAG_BONES do
        local a = want[name] or Vector3.zero
        local lift = if name == "Hips"
            then (-STAG_REAR_DROP * rise - STAG_LIE_DROP * lie * (1 - rise) + 0.012 * onFoot * math.abs(math.sin(s.stride))) * u - drop
            else 0
        pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
    end

    -- the eyes: slow blinks; wide as it watches its comet go
    s.nextBlink = s.nextBlink or t + 3
    local blink = 0
    if t >= s.nextBlink then
        local a = (t - s.nextBlink) / 0.22
        if a >= 1 then
            s.nextBlink = t + 3 + math.random() * 4
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local doze = smoothstep(0.3, 0.9, 0.5 + 0.5 * math.sin(t * 0.3))
    local close = math.max(blink, lie * 0.5 * doze) * (1 - watch)
    local upper = STAG_BLINK_UPPER * close - math.rad(6) * watch
    local lower = STAG_BLINK_LOWER * close - math.rad(4) * watch
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(STAG_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(STAG_LID_HINGE[side], lower))
    end
end

-- The Sand Phantom (skinned): a desert jerboa spirit. It hops on its long hind legs, both feet together, its long tail held out behind it for balance;
-- still, it sits up tall to look about, freezes when something catches its eye, or washes its face with its tiny forepaws. Its gaze darts, quick and
-- shy; its huge ears turn on their own; fine sand streams off its tail's brush and its ears as if blown by a wind only it feels.
local SAND_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local SAND_SOLE = 0.2988 -- metres from the middle of its box down to its feet: it sits on the ground
local SAND_LID_HINGE = { L = Vector3.new(0.765, -0.0686, -0.6403), R = Vector3.new(0.765, 0.0686, 0.6403) } -- both lids of an eye turn on this line
local SAND_BLINK_UPPER, SAND_BLINK_LOWER = math.rad(62), math.rad(28)
local SAND_GOLD, SAND_PALE, SAND_DUSK = Color3.fromRGB(226, 182, 110), Color3.fromRGB(246, 226, 180), Color3.fromRGB(176, 124, 70)
local SAND_HOP = 0.16 -- metres it rises at the top of a hop
local SAND_AWAY = 0.8 -- metres to its right it re-forms in its special: clear of where it stood, and still in a following camera's view

local function sandHind(t, s, h, f)
    local out = {}
    for _, side in { "L", "R" } do
        out["LegB" .. side .. "1"], out["LegB" .. side .. "2"], out["LegB" .. side .. "3"], out["FootB" .. side] = { t, 0, 0 }, { s, 0, 0 }, { h, 0, 0 }, { f, 0, 0 }
    end
    return out
end

local function sandStance(base, hind)
    for bone, a in hind do
        base[bone] = a
    end
    return base
end

-- its stances, each searched in Blender against the ground and for torn skin: the same numbers as sand_phantom.py's CROUCH, SPRING and UPRIGHT
local SAND_CROUCH = sandStance({ Body = { -0.064, 0, 0 } }, sandHind(0.308, -0.47, 0.062, 0.3))
local SAND_CROUCH_DROP = 0.025
local SAND_SPRING = sandStance({ Body = { 0.1, 0, 0 } }, sandHind(-0.6, 0.6, -0.4, -0.5)) -- only ever with the hop's lift, which keeps its feet clear
local SAND_UPRIGHT = sandStance({ Body = { 0.261, 0, 0 }, Chest = { 0.1, 0, 0 }, Head = { -0.2, 0, 0 } }, sandHind(0.208, -0.117, -0.496, 0.019))
local SAND_UPRIGHT_RISE = 0.046
local SAND_GROOM = { ArmL1 = { 0.6, 0, 0 }, ArmL2 = { -0.6, 0, 0 }, ArmR1 = { 0.6, 0, 0 }, ArmR2 = { -0.6, 0, 0 }, Head = { 0.25, 0, 0 } }
for k = 1, 6 do
    SAND_SPRING["Tail" .. k] = { 0.05, 0, 0 }
end

local function sandBones()
    local bones = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR", "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR" }
    for k = 1, 6 do
        table.insert(bones, "Tail" .. k)
    end
    for _, side in { "L", "R" } do
        for k = 1, 3 do
            table.insert(bones, "LegB" .. side .. k)
        end
        table.insert(bones, "FootB" .. side)
    end
    return bones
end
local SAND_BONES = sandBones() -- every bone its stances pose (the lids turn on their hinges on their own)

local function sandEmitter(parent, rate, size, speed, unit)
    local sand = Instance.new("ParticleEmitter")
    sand.Name = "BlowingSand"
    sand.Texture = "rbxasset://textures/particles/smoke_main.dds"
    sand.Rate = rate
    sand.Lifetime = NumberRange.new(0.6, 1.1)
    sand.Speed = NumberRange.new(speed * 0.5 * unit, speed * unit)
    sand.SpreadAngle = Vector2.new(25, 25)
    sand.EmissionDirection = Enum.NormalId.Back
    sand.Acceleration = Vector3.new(0, -0.15 * unit, 0)
    sand.Drag = 1.2
    sand.Rotation = NumberRange.new(0, 360)
    sand.RotSpeed = NumberRange.new(-40, 40)
    sand.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, size * unit), NumberSequenceKeypoint.new(1, size * 2.5 * unit) })
    sand.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1) })
    sand.Color = ColorSequence.new(SAND_PALE, SAND_GOLD)
    sand.LightEmission = 0.1
    sand.LightInfluence = 0.8
    sand.Parent = parent
    return sand
end

-- sand streaming off its tail's brush and its ears; and, kept off until its special, the sand it blows away into
local function sandStreams(rig, s)
    s.sandMade = true
    s.streams = {}
    for name, rate in { Tail6 = 6, EarL = 1.5, EarR = 1.5 } do
        local point = rig.points[name]
        if point then
            table.insert(s.streams, sandEmitter(point, rate, 0.025, 0.18, rig.unit))
        end
    end
    local hips = rig.points.Hips
    if hips then
        local blow = sandEmitter(hips, 90, 0.07, 0.9, rig.unit)
        blow.Name = "Dissolve"
        blow.EmissionDirection = Enum.NormalId.Right
        blow.SpreadAngle = Vector2.new(50, 50)
        blow.Lifetime = NumberRange.new(0.5, 0.9)
        blow.Shape = Enum.ParticleEmitterShape.Sphere
        blow.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.6, 0.35), NumberSequenceKeypoint.new(1, 1) })
        blow.Color = ColorSequence.new(SAND_GOLD, SAND_DUSK)
        blow.LightInfluence = 0.25
        blow.Enabled = false
        s.dissolve = blow
    end
end

-- its skin and the glints in its eyes go together: 0, all there; 1, gone into sand
local function sandGone(rig, s, gone)
    if s.gone == gone then
        return
    end
    s.gone = gone
    for _, key in { "Body", "Glints" } do
        local part = rig.parts[key]
        if part then
            part.Transparency = gone
        end
    end
    for _, stream in s.streams or {} do
        stream.Enabled = gone < 0.5
    end
end

local function animateSandPhantom(rig, s, moving, fly, nova)
    if not s.sandMade then
        sandStreams(rig, s)
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

    -- the special, Mirage: it sits up tall and stares at you (to 0.18); it blows away downwind as sand and is gone (0.2-0.38); a dust devil spins up a
    -- little to its right (Blasts.Mirage, at 0.42) and it re-forms inside it (0.6-0.72), shakes the sand off (0.72-0.8) and hops back (0.8-1)
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local stare = smoothstep(0.0, 0.14, progress) * (1 - smoothstep(0.34, 0.4, progress))
    local gone = smoothstep(0.2, 0.36, progress) * (1 - smoothstep(0.6, 0.72, progress))
    local shake = if progress > 0.72 and progress < 0.8 then math.sin(math.pi * (progress - 0.72) / 0.08) else 0
    local away = if progress < 0.4 then 0 elseif progress < 0.8 then 1 else 1 - smoothstep(0.8, 1.0, progress)
    local backHop = if progress > 0.8 and progress < 1 then math.abs(math.sin(math.pi * 2 * (progress - 0.8) / 0.2)) else 0
    -- (before the far check: it must come back whether or not anyone is watching)
    sandGone(rig, s, gone)
    if s.dissolve then
        s.dissolve.Enabled = progress > 0.18 and progress < 0.36
    end

    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SAND_FAR then
        return
    end
    local pace = math.max(moving, fly)
    local drop = dropToGround(rig, s, t, u, fly, SAND_SOLE)
    local special = progress > 0

    -- still, now and then it sits up tall to look about, freezes, or washes its face
    s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
    s.nextIdle = s.nextIdle or t + 2
    if s.still > 1.5 and t >= s.nextIdle then
        local r = math.random()
        s.idleKind = if r < 0.45 then "up" elseif r < 0.75 then "freeze" else "groom"
        s.idleAt = t
        s.idleFor = if s.idleKind == "groom" then 2.2 elseif s.idleKind == "up" then 2.6 else 1.2
        s.nextIdle = t + s.idleFor + 1.5 + math.random() * 3
    end
    local idleEnv = if s.idleAt and pace < 0.05 and not special then math.clamp((t - s.idleAt) / s.idleFor, 0, 1) else 1
    local idle = math.min(1, math.sin(math.pi * idleEnv) * 2.2)
    local up = math.max(if s.idleKind == "up" then idle else 0, stare)
    local groom = if s.idleKind == "groom" then idle else 0
    local frozen = if s.idleKind == "freeze" then idle else 0

    -- the hop: both feet together, gathered on the ground, flung back in the air; in flight a long stretched leap; hopping back after its special
    s.hopPhase = (s.hopPhase or 0) + dt * (11 * moving + 6 * fly)
    local air = math.max(0, math.sin(s.hopPhase)) * moving * (1 - fly)
    local land = math.max(0, -math.sin(s.hopPhase)) * moving * (1 - fly)
    local want = {}
    addStance(want, SAND_CROUCH, math.min(1, land + 0.4 * (1 - backHop) * smoothstep(0.78, 0.82, progress) * (if progress < 1 then 1 else 0)))
    addStance(want, SAND_SPRING, math.min(1, air + 0.85 * fly + backHop))
    addStance(want, SAND_UPRIGHT, up * (1 - pace))
    addStance(want, SAND_GROOM, groom * (0.75 + 0.25 * math.sin(t * 14)))

    -- the body: quick, light breathing; banking on turns; shaking the sand off
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
    local breath = math.sin(t * 4.5) * (1 - frozen)
    local shiver = 0.25 * shake * math.sin(t * 45)
    addStance(want, { Hips = { 0, shiver * 0.4, s.bank * pace + shiver }, Chest = { 0.02 * breath, 0, -shiver * 0.8 }, Head = { 0, 0, shiver * 0.6 } }, 1)

    -- its gaze: darting, quick and shy; it stares at you before it vanishes; frozen, it holds still
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze and frozen < 0.1 then
        s.nextGaze = t + 0.4 + math.random() * 1.1
        s.atYou = math.random() < 0.35
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.4, (math.random() - 0.5) * 0.4
    end
    local look = math.max(stare, 0)
    local wantYaw = if s.atYou or look > 0 then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.9, 0.9) else s.gazeYaw
    local wantPitch = if s.atYou or look > 0 then math.clamp(toYou.Y * 0.6, -0.3, 0.4) else s.gazePitch
    local calm = (1 - 0.6 * pace) * (1 - groom)
    s.yaw = (s.yaw or 0) + (wantYaw * calm - (s.yaw or 0)) * math.min(1, dt * 12)
    s.pitch = (s.pitch or 0) + (wantPitch * calm - (s.pitch or 0)) * math.min(1, dt * 12)
    addStance(want, {
        Neck = { 0.3 * s.pitch, 0.4 * s.yaw, 0 }, Head = { 0.45 * s.pitch, 0.55 * s.yaw, 0.12 * s.yaw },
        EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
    }, 1)

    -- the ears: huge, each turning on its own; pricked up and forward when it freezes or stares; laid back in the hop and the leap
    for _, side in { "L", "R" } do
        local sign = if side == "L" then 1 else -1
        local swivel = math.max(0, math.sin(t * 0.9 + (if side == "L" then 0 else 2.2))) ^ 6
        local prick = math.max(frozen, stare)
        addStance(want, { ["Ear" .. side] = { -0.2 * swivel + 0.15 * prick - 0.35 * math.max(air, fly), sign * (0.4 * swivel * (1 - prick) + 0.2 * math.max(air, fly)), 0 } }, 1)
    end

    -- the tail: held out behind it, swaying; it swings up as it lands and down as it springs, balancing each hop; still when it freezes
    for k = 1, 6 do
        local sway = (0.03 + 0.04 * k / 6) * math.sin(t * 1.3 - k * 0.5) * (1 - frozen)
        local balance = (0.12 * land - 0.08 * air) * (k <= 2 and 1 or 0.4)
        addStance(want, { ["Tail" .. k] = { balance + 0.02 * math.sin(t * 0.8 - k * 0.6), sway, 0 } }, 1)
    end

    local awayX = SAND_AWAY * away
    for _, name in SAND_BONES do
        local a = want[name] or Vector3.zero
        local offset = Vector3.zero
        if name == "Hips" then
            local lift = SAND_HOP * air + 0.75 * SAND_HOP * backHop - SAND_CROUCH_DROP * land + SAND_UPRIGHT_RISE * up * (1 - pace)
            offset = Vector3.new(awayX * u, lift * u - drop, 0)
        end
        pose(m[name], CFrame.new(offset) * CFrame.Angles(a.X, a.Y, a.Z))
    end

    -- the eyes: quick blinks, wide as it stares, never while frozen
    s.nextBlink = s.nextBlink or t + 2
    local blink = 0
    if t >= s.nextBlink and frozen < 0.1 then
        local a = (t - s.nextBlink) / 0.14
        if a >= 1 then
            s.nextBlink = t + 1.8 + math.random() * 3
        else
            blink = 1 - math.abs(2 * a - 1)
        end
    end
    local close = blink * (1 - stare)
    local upper = SAND_BLINK_UPPER * close - math.rad(6) * math.max(stare, frozen)
    local lower = SAND_BLINK_LOWER * close - math.rad(4) * math.max(stare, frozen)
    for _, side in { "L", "R" } do
        pose(m["LidU" .. side], CFrame.fromAxisAngle(SAND_LID_HINGE[side], -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(SAND_LID_HINGE[side], lower))
    end
end

-- The Solar Butterfly (skinned): a swallowtail of sunset glass. It flies in slow, deep wingbeats with glides between, bobbing as butterflies do; still
-- a few seconds, it drifts down and lands on its legs to bask, wings spread flat to the sun, now and then closing them up over its back and opening them
-- again; its antennae sway and twitch; warm motes of stored sunlight drift off its eyespots, more after dark.
local BFLY_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local BFLY_LEGS = 0.0737 -- metres from its Body bone down to the tips of its legs (solar_butterfly.py): where it stands when it lands. Measured from the
-- bone, not the box: the importer's root part sits at the model's origin, under a pet that floats, so the box's middle is not where it seems
local BFLY_GOLD, BFLY_ROSE, BFLY_DUSK = Color3.fromRGB(255, 196, 80), Color3.fromRGB(255, 110, 90), Color3.fromRGB(150, 80, 200)
-- its wings in the game's axes (a turn about its length; L takes the opposite sign): the same numbers as solar_butterfly.py's wings(), each checked in
-- Blender for torn skin: raised to 0.95 and lowered to -0.5 in the beat, flat at -0.12 basking, closed over its back at 1.3
local BFLY_UP, BFLY_DOWN, BFLY_FLAT, BFLY_CLOSED, BFLY_GLIDE = 0.95, -0.5, -0.12, 1.3, 0.3

local function bflyWings(m, raise, bend, hindLag)
    for _, side in { "L", "R" } do
        local up = if side == "L" then -1 else 1
        pose(m["Fore" .. side .. "1"], CFrame.Angles(0, 0, up * raise))
        pose(m["Fore" .. side .. "2"], CFrame.Angles(0, 0, up * bend))
        pose(m["Hind" .. side .. "1"], CFrame.Angles(0, 0, up * (raise - hindLag)))
        pose(m["Hind" .. side .. "2"], CFrame.Angles(0, 0, up * bend * 0.8))
    end
end

-- warm motes of stored sunlight drifting off its eyespots; more after dark
local function bflyMotes(rig, s)
    s.motesMade = true
    s.motes = {}
    for _, name in { "HindL2", "HindR2" } do
        local point = rig.points[name]
        if point then
            local motes = Instance.new("ParticleEmitter")
            motes.Name = "Sunlight"
            motes.Texture = SPARKLE
            motes.Rate = 1.2
            motes.Lifetime = NumberRange.new(1.2, 2)
            motes.Speed = NumberRange.new(0.03 * rig.unit, 0.1 * rig.unit)
            motes.SpreadAngle = Vector2.new(180, 180)
            motes.Acceleration = Vector3.new(0, 0.08 * rig.unit, 0)
            motes.Drag = 1
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.07 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(BFLY_GOLD, BFLY_ROSE)
            motes.LightEmission = 1
            motes.LightInfluence = 0
            motes.Parent = point
            table.insert(s.motes, motes)
        end
    end
end

local function animateSolarButterfly(rig, s, moving, fly, nova)
    if not s.motesMade then
        bflyMotes(rig, s)
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    -- after dark it spends its sunlight a little faster
    local clock = Lighting.ClockTime
    local night = if clock < 6.2 or clock > 17.8 then 1 else 0
    for _, motes in s.motes do
        motes.Rate = 1.2 + 2.3 * night
    end
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > BFLY_FAR then
        return
    end
    local pace = math.max(moving, fly)

    -- the special, Afterglow: it rises a little and spreads its wings wide and still as the sunlight gathers in them (to 0.42); then lets it go
    -- (Blasts.Afterglow) with one slow, deep wingbeat, and flies on
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local spread = smoothstep(0.02, 0.25, progress) * (1 - smoothstep(0.42, 0.5, progress))
    local release = if progress > 0.42 and progress < 0.8 then math.sin(math.pi * (progress - 0.42) / 0.38) else 0
    local special = progress > 0

    -- still a few seconds, it drifts down and lands to bask; it takes off as soon as it has somewhere to go
    s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
    local wantLand = if s.still > 4 then 1 else 0
    s.land = (s.land or 0) + (wantLand - (s.land or 0)) * math.min(1, dt * (if wantLand > (s.land or 0) then 0.9 else 4))
    local land = smoothstep(0, 1, s.land)
    local bodyBone = rig.points.Body
    if bodyBone and not s.sole then
        s.sole = rig.rootPart.CFrame:PointToObjectSpace(bodyBone.WorldPosition).Y * -1 / u + BFLY_LEGS -- (WorldPosition leaves out its own Transform)
    end
    local drop = dropToGround(rig, s, t, u, 0, s.sole or 0.15)

    -- flight: slow, deep beats; now and then a glide with its wings held up in a shallow V
    s.nextGlide = s.nextGlide or t + 2
    if t >= s.nextGlide then
        s.glideUntil = t + 0.6 + math.random() * 0.6
        s.nextGlide = s.glideUntil + 1.6 + math.random() * 2
    end
    local gliding = if t < (s.glideUntil or 0) then 1 else 0
    s.glide = (s.glide or 0) + (gliding - (s.glide or 0)) * math.min(1, dt * 6)
    local rate = (1.7 + 0.8 * moving + 0.5 * fly) * (1 - 0.8 * s.glide) * (1 - land) * (1 - spread)
    s.beat = (s.beat or 0) + dt * rate * 2 * math.pi
    local wave = math.sin(s.beat)
    local mid, half = (BFLY_UP + BFLY_DOWN) / 2, (BFLY_UP - BFLY_DOWN) / 2
    local flying = (1 - land) * (1 - spread)
    local raise = (mid + half * wave) * (1 - s.glide) + BFLY_GLIDE * s.glide
    local bend = 0.12 * math.sin(s.beat - 0.8) * (1 - s.glide)

    -- basking: wings flat to the sun; now and then closed up over its back a while, then opened again
    s.nextClose = s.nextClose or t + 3
    if land > 0.9 and t >= s.nextClose then
        s.closeAt = t
        s.nextClose = t + 5 + math.random() * 5
    end
    local closeEnv = if s.closeAt then math.clamp((t - s.closeAt) / 2.6, 0, 1) else 1
    local closed = math.min(1, math.sin(math.pi * closeEnv) * 1.6) * land
    local bask = BFLY_FLAT + 0.05 * math.sin(t * 0.9)
    local landed = bask * (1 - closed) + BFLY_CLOSED * closed

    -- the special: held flat and wide, then one slow, deep beat as it lets the light go
    local held = BFLY_FLAT - 0.05
    local deep = BFLY_UP * math.sin(math.pi * math.clamp((progress - 0.42) / 0.38, 0, 1)) * 1.0
    local wingRaise = raise * flying + landed * land * (1 - spread) + held * spread * (1 - release) + deep * release * (if progress > 0.42 then 1 else 0)
    bflyWings(m, wingRaise, bend * flying, 0.08 * flying)

    -- the body: rides each downstroke and bobs as butterflies do; settles onto its legs when it lands; rises into its special
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
    local bob = (0.05 * math.sin(s.beat - 1.4) + 0.035 * math.sin(t * 1.3) + 0.02 * math.sin(t * 3.1 + 1)) * flying + 0.1 * spread
    local drift = 0.025 * math.sin(t * 1.1) * flying
    local lift = bob * u * (1 - land) - drop * land
    local pitch = (-0.08 * moving + 0.05 * math.sin(s.beat - 1.8)) * flying - 0.1 * spread
    pose(m.Body, CFrame.new(drift * u, lift, 0) * CFrame.Angles(pitch, 0.05 * math.sin(t * 0.8) * flying, s.bank * flying - drift * 1.5))
    for index, name in { "Abd1", "Abd2", "Abd3" } do
        pose(m[name], CFrame.Angles(-0.05 * math.sin(s.beat - 1.6 - index * 0.5) * flying + 0.04 * land * math.sin(t * 0.7 + index), 0, 0))
    end

    -- the head and antennae: it looks about, and to you; its antennae sway, now and then one twitches
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextGaze = s.nextGaze or 0
    if t >= s.nextGaze then
        s.nextGaze = t + 1.5 + math.random() * 2.5
        s.atYou = math.random() < 0.4
        s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.7, (math.random() - 0.5) * 0.3
    end
    local wantYaw = if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.5, 0.5) else s.gazeYaw
    local wantPitch = if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.3) else s.gazePitch
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 4)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 4)
    pose(m.Head, CFrame.Angles(0.5 * s.pitch, 0.5 * s.yaw, 0.1 * s.yaw))
    for _, side in { "L", "R" } do
        local sign = if side == "L" then 1 else -1
        local twitch = math.max(0, math.sin(t * 1.9 + (if side == "L" then 0 else 2.1))) ^ 16
        local sway = 0.06 * math.sin(t * 1.4 + (if side == "L" then 0 else 1.2))
        pose(m["Ant" .. side .. "1"], CFrame.Angles(0.05 * math.sin(s.beat - 2) * flying + sway - 0.1 * spread, sign * 0.05 * twitch, 0))
        pose(m["Ant" .. side .. "2"], CFrame.Angles(0.25 * twitch + 0.04 * math.sin(t * 2.3 + sign), 0, 0))
    end
end

-- The Obsidian Guardian (skinned): a gargoyle of black glass. It perches as gargoyles do, crouched with its hands on the ledge before it and its wings
-- folded up behind it, their shards hanging round it like a cloak, and keeps as still as the stone it is; then its head snaps round to watch you, its
-- brow shards lowering, and holds. Now and then it mantles, raising its wings forward over its shoulders, and settles again; its tail's point twitches.
-- When its owner goes anywhere it takes off and flies low beside them in slow, heavy beats with long glides between, and lands again the moment they stop.
local GUARD_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
local GUARD_HIPS_SOLE = 0.2458 -- metres from its Hips bone down to its talons as it perches (obsidian_guardian.py): where it stands when it lands.
-- Measured from the bone, not the box: the importer's root part sits at the model's origin, so the box's middle is not where it seems
local GUARD_HOVER = 0.9 -- metres above the ground it flies when its owner goes anywhere on foot
local GUARD_VIOLET, GUARD_PALE, GUARD_GLASS = Color3.fromRGB(154, 80, 255), Color3.fromRGB(226, 206, 255), Color3.fromRGB(34, 22, 52)
-- its poses, each checked in Blender (obsidian_guardian.py's POSES) against the ground, for torn skin, and for its wings cutting into it: at each pose and
-- along the way to it from the perch. Its left side; the right is its mirror. Glide, Up and Down are on the wing (the body pitched, the tail trailing,
-- the arms tucked); Mantle is the wings raised forward over its shoulders as it perches; Rise is the special: chest up, wings spread wide
local GUARD_FLY_BODY = {
    Hips = { -0.45, 0, 0 }, Neck = { 0.22, 0, 0 }, Head = { 0.25, 0, 0 },
    Tail1 = { -0.175, 0.199, 0 }, Tail2 = { 0.335, 1.314, 0 }, Tail3 = { -1.184, 0.181, 0 }, Tail4 = { -0.159, 0.399, 0 }, Tail5 = { -0.159, 0.714, 0 },
    ArmL1 = { 0.2, 0, -0.3 }, ArmL2 = { -1.4, 0, 0 },
}
local GUARD_GLIDE = {
    WingL1 = { 0.376, -0.61, 0.253 }, WingL2 = { 0.334, -2.985, -1.33 }, WingLS = { 0.887, 0.172, -0.13 },
    WingLF1 = { 1.14, 0.193, -0.189 }, WingLF2 = { 0.988, 0.182, -0.153 }, WingLF3 = { 0.786, 0.159, -0.109 },
}
local GUARD_UP = {
    WingL1 = { -0.169, -0.271, -0.288 }, WingL2 = { 0.48, 3.093, -1.119 }, WingLS = { 0.988, 0.182, -0.153 },
    WingLF1 = { 1.038, 0.186, -0.165 }, WingLF2 = { 0.887, 0.172, -0.13 }, WingLF3 = { 0.686, 0.145, -0.088 },
}
local GUARD_DOWN = {
    WingL1 = { 0.913, -0.676, 0.807 }, WingL2 = { 0.277, -2.802, -1.621 }, WingLS = { 0.937, 0.177, -0.142 },
    WingLF1 = { 1.191, 0.195, -0.201 }, WingLF2 = { 1.038, 0.186, -0.165 }, WingLF3 = { 0.837, 0.166, -0.119 },
}
local GUARD_MANTLE = {
    WingL1 = { -0.437, -0.647, -0.035 }, WingL2 = { -1.119, 0.447, 0.609 }, WingLS = { 0.587, 0.128, -0.07 },
    WingLF1 = { 0.488, 0.11, -0.053 }, WingLF2 = { 0.439, 0.1, -0.045 }, WingLF3 = { 0.39, 0.09, -0.038 },
}
local GUARD_RISE = {
    Body = { 0.32, 0, 0 }, Chest = { 0.12, 0, 0 }, Neck = { -0.2, 0, 0 }, Head = { -0.12, 0, 0 }, ArmL1 = { 0.25, 0, -0.2 }, ArmL2 = { -0.3, 0, 0 },
    WingL1 = { -0.696, -0.464, 0.039 }, WingL2 = { -2.721, 0.026, 1.913 }, WingLS = { 0.988, 0.182, -0.153 },
    WingLF1 = { 1.242, 0.197, -0.214 }, WingLF2 = { 1.089, 0.19, -0.177 }, WingLF3 = { 0.887, 0.172, -0.13 },
}
local GUARD_SIDED = { "Wing", "Arm", "Leg", "Brow", "Hand", "Foot" }

-- a pose's turns as CFrames, its left side mirrored onto its right (a mirror keeps a turn about X and flips those about Y and Z)
local function guardPose(stance)
    local out = {}
    for bone, a in stance do
        out[bone] = CFrame.Angles(a[1], a[2], a[3])
        for _, prefix in GUARD_SIDED do
            if string.sub(bone, 1, #prefix) == prefix and string.sub(bone, #prefix + 1, #prefix + 1) == "L" then
                out[prefix .. "R" .. string.sub(bone, #prefix + 2)] = CFrame.Angles(a[1], -a[2], -a[3])
            end
        end
    end
    return out
end
local GUARD_POSES = {
    FlyBody = guardPose(GUARD_FLY_BODY),
    Glide = guardPose(GUARD_GLIDE),
    Up = guardPose(GUARD_UP),
    Down = guardPose(GUARD_DOWN),
    Mantle = guardPose(GUARD_MANTLE),
    Rise = guardPose(GUARD_RISE),
}

local function guardBones()
    local bones = { "Hips", "Body", "Chest", "Neck", "Head", "BrowL", "BrowR" }
    for k = 1, 5 do
        table.insert(bones, "Tail" .. k)
    end
    for _, tag in { "L", "R" } do
        for _, name in { "Arm%s1", "Arm%s2", "Hand%s", "Leg%s1", "Leg%s2", "Leg%s3", "Foot%s", "Wing%s1", "Wing%s2", "Wing%s3", "Wing%sS", "Wing%sF1", "Wing%sF2", "Wing%sF3" } do
            table.insert(bones, string.format(name, tag))
        end
    end
    return bones
end
local GUARD_BONES = guardBones()
local GUARD_WINGS = {}
for _, name in GUARD_BONES do
    if string.sub(name, 1, 4) == "Wing" then
        table.insert(GUARD_WINGS, name)
    end
end

-- every bone in `into` turned the share `weight` of the way toward `stance` (by the shortest way round: its wings turn far)
local function guardToward(into, stance, weight, bones)
    if weight <= 0 then
        return
    end
    for _, name in bones do
        local target = stance[name]
        if target or weight >= 1 then
            into[name] = (into[name] or CFrame.identity):Lerp(target or CFrame.identity, weight)
        elseif into[name] then
            into[name] = into[name]:Lerp(CFrame.identity, weight)
        end
    end
end

local function animateObsidianGuardian(rig, s, moving, fly, nova)
    local camera = workspace.CurrentCamera
    if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > GUARD_FAR then
        return
    end
    local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
    local pace = math.max(moving, fly)

    -- the special, Honest Glass: it rises on its haunches, wings spread wide, and turns its face to you and holds you in it (to 0.42); its mirror flashes
    -- and gives you back to yourself (Blasts.HonestGlass); it watches the figure break, then folds its wings and settles
    local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
    local special = progress > 0
    local rise = smoothstep(0.02, 0.3, progress) * (1 - smoothstep(0.8, 0.98, progress))
    local stare = smoothstep(0.06, 0.2, progress) * (1 - smoothstep(0.7, 0.85, progress))
    local flash = if progress > 0.4 and progress < 0.56 then math.sin(math.pi * (progress - 0.4) / 0.16) else 0

    -- perched or on the wing: it takes off as soon as there is somewhere to go and lands the moment its owner stops
    s.still = if pace < 0.05 then (s.still or 0) + dt else 0
    local wantLand = if (s.still > 0.8 or special) and fly < 0.05 then 1 else 0
    s.land = (s.land or 1) + (wantLand - (s.land or 1)) * math.min(1, dt * (if wantLand > (s.land or 1) then 1.8 else 3.5))
    local land = smoothstep(0, 1, s.land)
    local flying = 1 - land
    local open = smoothstep(0.55, 1, flying) -- its beat fades in only once its wings are open: unfolding straight into a downstroke cuts through it
    local hips = rig.points.Hips
    if hips and not s.sole then
        s.sole = rig.rootPart.CFrame:PointToObjectSpace(hips.WorldPosition).Y * -1 / u + GUARD_HIPS_SOLE -- (WorldPosition leaves out its own Transform)
    end
    local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.5)

    -- on the wing: slow, heavy beats, the body lifting on each downstroke; now and then a long glide on still wings
    s.nextGlide = s.nextGlide or t + 3
    if t >= s.nextGlide then
        s.glideUntil = t + 1 + math.random() * 1.2
        s.nextGlide = s.glideUntil + 2.5 + math.random() * 3
    end
    local gliding = if t < (s.glideUntil or 0) then 1 else 0
    s.glide = (s.glide or 0) + (gliding - (s.glide or 0)) * math.min(1, dt * 3)
    s.beat = (s.beat or 0) + dt * (3.4 + 1.4 * pace) * (1 - 0.9 * s.glide) * open
    local stroke = 0.5 + 0.5 * math.sin(s.beat) -- 1 at the top of the stroke, 0 at the bottom
    local want = {}
    guardToward(want, GUARD_POSES.FlyBody, flying, GUARD_BONES)
    local wings = {}
    guardToward(wings, GUARD_POSES.Down, 1, GUARD_WINGS)
    guardToward(wings, GUARD_POSES.Up, stroke, GUARD_WINGS)
    local hold = 1 - open * (1 - s.glide)
    guardToward(wings, GUARD_POSES.Glide, hold, GUARD_WINGS)
    for _, name in GUARD_WINGS do
        want[name] = CFrame.identity:Lerp(wings[name], flying)
    end

    -- perched: still as stone. Now and then it mantles, raising its wings forward over its shoulders a while, and folds them again; now and then a shiver
    -- runs through its wings and they settle with a rattle of glass
    local perched = land * (1 - rise)
    s.nextMantle = s.nextMantle or t + 8 + math.random() * 6
    if t >= s.nextMantle and perched > 0.95 then
        s.mantleAt = t
        s.nextMantle = t + 14 + math.random() * 10
    end
    local mantleEnv = if s.mantleAt then math.clamp((t - s.mantleAt) / 4.5, 0, 1) else 1
    local mantle = smoothstep(0, 0.25, mantleEnv) * (1 - smoothstep(0.7, 1, mantleEnv)) * perched
    guardToward(want, GUARD_POSES.Mantle, mantle, GUARD_WINGS)
    s.nextShiver = s.nextShiver or t + 5
    if t >= s.nextShiver then
        s.shiverAt = t
        s.nextShiver = t + 7 + math.random() * 8
    end
    local shiverEnv = if s.shiverAt then math.clamp((t - s.shiverAt) / 0.7, 0, 1) else 1
    local shiver = math.sin(math.pi * shiverEnv) * math.sin(t * 38) * 0.035 * perched * (1 - mantle)
    for _, tag in { "L", "R" } do
        local sign = if tag == "L" then 1 else -1
        want["Wing" .. tag .. "1"] = CFrame.Angles(0, 0, shiver * sign) * want["Wing" .. tag .. "1"]
    end

    -- the special: up on its haunches, wings spread wide
    guardToward(want, GUARD_POSES.Rise, rise, GUARD_BONES)

    -- its gaze: still for seconds, then its head snaps round to a new mark and holds; most often the mark is you. In the special it holds you
    local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
    s.nextSnap = s.nextSnap or t + 2
    s.markYaw, s.markPitch = s.markYaw or 0, s.markPitch or 0 -- (straight ahead until its first snap)
    if t >= s.nextSnap then
        s.nextSnap = t + 2.5 + math.random() * 4
        s.atYou = math.random() < 0.6
        s.markYaw, s.markPitch = (math.random() - 0.5) * 1.6, (math.random() - 0.4) * 0.35
        s.snapAt = t
    end
    local atYou = s.atYou or stare > 0
    local yawToYou = math.clamp(math.atan2(-toYou.X, -toYou.Z), -1.3, 1.3)
    -- in the special it turns on its perch to face you, so its head need not turn into its own spread wings; on the wing, or rising, the head turns
    -- no more than 0.4 either way (checked in Blender: a head turned further meets the raised wings)
    s.turn = (s.turn or 0) + (yawToYou * stare * land - (s.turn or 0)) * math.min(1, dt * 4)
    local reach = 1 - 0.6 * math.max(flying, rise)
    local wantYaw = math.clamp((if atYou then yawToYou else s.markYaw) - s.turn, -reach, reach)
    local wantPitch = (if atYou then math.clamp(toYou.Y * 0.6, -0.25, 0.35) else s.markPitch) * reach
    s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 14)
    s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 14)
    want.Neck = CFrame.Angles(0.4 * s.pitch, 0.38 * s.yaw, 0) * (want.Neck or CFrame.identity)
    want.Head = CFrame.Angles(0.6 * s.pitch, 0.62 * s.yaw, 0.1 * s.yaw) * (want.Head or CFrame.identity)

    -- its brow shards: lowered for a moment as its head snaps round, lowered hard as it stares in the special, lifted as its mirror flashes
    local snapGlare = if s.snapAt then math.max(0, 1 - (t - s.snapAt) / 1.4) else 0
    local glare = math.max(snapGlare * 0.7, stare) * (1 - flash)
    for _, tag in { "L", "R" } do
        local sign = if tag == "L" then 1 else -1
        want["Brow" .. tag] = CFrame.Angles(0.2 * flash, 0, sign * (0.25 * flash - 0.3 * glare))
    end

    -- the tail: on the wing it trails, swaying slowly; perched, its point twitches now and then
    s.nextTwitch = s.nextTwitch or t + 3
    if t >= s.nextTwitch then
        s.twitchAt = t
        s.nextTwitch = t + 3 + math.random() * 5
    end
    local twitchEnv = if s.twitchAt then math.clamp((t - s.twitchAt) / 0.5, 0, 1) else 1
    local twitch = math.sin(math.pi * twitchEnv) * 0.25 * land
    for k = 1, 5 do
        local sway = 0.05 * k / 5 * math.sin(t * 1.3 - k * 0.6) * flying
        local flick = if k >= 4 then twitch * (k - 3) * 0.5 else 0
        want["Tail" .. k] = CFrame.Angles(0.03 * math.sin(s.beat - k * 0.5) * flying, sway + flick, 0) * (want["Tail" .. k] or CFrame.identity)
    end

    -- banking on its turns; low over the ground on foot, landing on its talons when it perches
    local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
    local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
    s.heading = heading
    s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
    local heave = (0.05 * (1 - stroke) * open * (1 - s.glide) + 0.03 * math.sin(t * 1.1)) * flying
    local lift = (GUARD_HOVER * (1 - fly) + heave) * flying * u - drop -- (drop is nothing while its owner flies: it keeps to their height)
    want.Hips = CFrame.new(0, lift, 0) * CFrame.Angles(0, s.turn, s.bank * flying) * (want.Hips or CFrame.identity)

    for _, name in GUARD_BONES do
        pose(m[name], want[name] or CFrame.identity)
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

-- Its hoof sparks, set up on its first frame however far it is: each model's emitters start enabled,
-- and they must throw sparks only where a hoof lands.
local function kirinSparks(rig, s)
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

local function animateStormhornKirin(rig, s, moving, fly, nova)
    if not s.sparks then
        kirinSparks(rig, s)
    end
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

PetRig.Profiles.AbyssAnomalocaris = {
    Skinned = true,
    Bones = {
        "Body", "Seg2", "Seg1", "Head", "Seg4", "Seg5", "Seg6", "Seg7", "Seg8", "Seg9", "Tail",
        "FlapL1", "FlapL2", "FlapL3", "FlapL4", "FlapL5", "FlapL6", "FlapL7", "FlapL8", "FlapL9",
        "FlapR1", "FlapR2", "FlapR3", "FlapR4", "FlapR5", "FlapR6", "FlapR7", "FlapR8", "FlapR9",
        "FanL1", "FanL2", "FanL3", "FanR1", "FanR2", "FanR3",
        "ArmL1", "ArmL2", "ArmL3", "ArmL4", "ArmL5", "ArmL6", "ArmR1", "ArmR2", "ArmR3", "ArmR4", "ArmR5", "ArmR6",
        "StalkL", "StalkR", "EyeL", "EyeR",
    },
    Points = { "Head", "ArmL5", "ArmR5" },
    GlowColors = {
        ["e040b8"] = ANOMALO_GLOW, -- the thin line along every flap's and tail blade's outer edge (set each frame)
    },
    Effects = {
        Burst = "Body",
        Blast = "TheFirstHunt",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(225, 50, 175),
        Amber = Color3.fromRGB(255, 140, 220),
        Orange = Color3.fromRGB(196, 138, 66),
        Sun = Color3.fromRGB(255, 200, 240),
        Ivory = Color3.fromRGB(255, 235, 250),
    },
    Animate = animateAbyssAnomalocaris,
}

PetRig.Profiles.VoidscaleHydra = {
    Skinned = true,
    Bones = {
        "Body", "Chest", "Hips", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5",
        "UpperFL", "LowerFL", "FootFL", "UpperBL", "LowerBL", "FootBL", "UpperFR", "LowerFR", "FootFR", "UpperBR", "LowerBR", "FootBR",
        "NeckL1", "NeckL2", "NeckL3", "NeckL4", "NeckR1", "NeckR2", "NeckR3", "NeckR4", "NeckM1", "NeckM2", "ForkL1", "ForkL2", "ForkR1", "ForkR2",
        "HeadL", "HeadR", "HeadML", "HeadMR", "TongueL", "TongueR", "TongueML", "TongueMR",
    },
    Points = { "HeadL", "HeadR", "HeadML", "HeadMR" },
    GlowColors = {
        ["5aa0ff"] = HYDRA_LIGHT, -- the eye slits and the tongues (set each frame)
    },
    Effects = {
        Burst = "Body",
        Blast = "TheVoidBetween",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(70, 150, 255),
        Amber = Color3.fromRGB(150, 200, 255),
        Orange = Color3.fromRGB(40, 70, 190),
        Sun = Color3.fromRGB(200, 225, 255),
        Ivory = Color3.fromRGB(235, 242, 255),
    },
    Animate = animateVoidscaleHydra,
}

local function namelessBones()
    local bones = { "Hips", "Body", "Chest", "Neck", "Head", "Spark", "Halo" }
    for _, side in { "L", "R" } do
        for k = 1, 5 do
            table.insert(bones, "Arm" .. side .. k)
        end
        for k = 1, 3 do
            table.insert(bones, "Scarf" .. side .. k)
        end
    end
    for k = 0, 7 do
        for _, tag in { "a", "b", "c" } do
            table.insert(bones, "Hem" .. k .. tag)
        end
    end
    return bones
end

PetRig.Profiles.TheNamelessOne = {
    Skinned = true,
    Bones = namelessBones(),
    Points = { "Chest", "Spark", "ArmL5", "ArmR5" },
    GlowColors = {
        ["f4f0ff"] = NAMELESS_SPARK, -- the point of light in the hollow
        ["b89cff"] = NAMELESS_HALO, -- the broken halo and the tips that write (set each frame)
    },
    Effects = {
        Burst = "Body",
        Blast = "Unwritten",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(200, 170, 255),
        Amber = Color3.fromRGB(150, 120, 230),
        Orange = Color3.fromRGB(90, 60, 170),
        Sun = Color3.fromRGB(240, 235, 255),
        Ivory = Color3.fromRGB(250, 248, 255),
    },
    Animate = animateTheNamelessOne,
}

local function catBones()
    local bones = { "Body", "Hips", "Chest", "Neck", "Head", "Pendant", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR" }
    for k = 1, 6 do
        table.insert(bones, "Tail" .. k)
    end
    for key in CAT_LEADS do
        for k = 1, 3 do
            table.insert(bones, "Leg" .. key .. k)
        end
        table.insert(bones, "Paw" .. key)
    end
    return bones
end

PetRig.Profiles.EclipseCat = {
    Skinned = true,
    Bones = catBones(),
    Points = { "Head", "Tail6" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        ffd27a = Color3.fromRGB(255, 196, 90), -- the crescent on its forehead
        ffd27b = Color3.fromRGB(255, 188, 84), -- the thread of gold along its tail
        b07cff = Color3.fromRGB(176, 124, 255), -- the gem under its pendant
    },
    Effects = {
        Burst = "Body",
        Blast = "Totality",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 200, 100),
        Amber = Color3.fromRGB(196, 150, 255),
        Orange = Color3.fromRGB(118, 70, 220),
        Sun = Color3.fromRGB(255, 236, 190),
        Ivory = Color3.fromRGB(245, 238, 255),
    },
    Animate = animateEclipseCat,
}

local function shadowProfileBones()
    local bones = table.clone(SHADOW_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.Shadowcoil = {
    Skinned = true,
    Bones = shadowProfileBones(),
    Points = { "Tail7" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "FirstMove",
    },
    Colors = {
        Gold = SHADOW_EYESHINE,
        Amber = SHADOW_RIM,
        Orange = Color3.fromRGB(60, 46, 96),
        Sun = Color3.fromRGB(220, 255, 240),
        Ivory = Color3.fromRGB(236, 232, 248),
    },
    Animate = animateShadowcoil,
}

local function pearlProfileBones()
    local bones = table.clone(PEARL_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.CelestialPearlDragon = {
    Skinned = true,
    Bones = pearlProfileBones(),
    SkinTint = Color3.fromRGB(200, 198, 214), -- its near-white nacre blows out in daylight: toned down, the scale rows and plates read (seen in Play)
    Points = { "HandR", "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        fff4e2 = PEARL_GLOW, -- the pearl
    },
    Effects = {
        Blast = "HeavenCondensed",
        Pulse = "Pearl", -- (its light and motes ride on the hand: pearlGlow)
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 240, 214),
        Amber = Color3.fromRGB(224, 210, 255),
        Orange = Color3.fromRGB(196, 176, 255),
        Sun = Color3.fromRGB(255, 250, 240),
        Ivory = Color3.fromRGB(246, 238, 218),
    },
    Animate = animatePearlDragon,
}

local function leopardProfileBones()
    local bones = table.clone(LEOPARD_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.CelestialSnowLeopard = {
    Skinned = true,
    Bones = leopardProfileBones(),
    Points = { "Tail4", "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "WhereTheSkyBegins",
    },
    Colors = {
        Gold = Color3.fromRGB(196, 232, 255),
        Amber = Color3.fromRGB(140, 200, 255),
        Orange = Color3.fromRGB(70, 110, 200),
        Sun = Color3.fromRGB(240, 250, 255),
        Ivory = Color3.fromRGB(246, 247, 250),
    },
    Animate = animateSnowLeopard,
}

local function stagProfileBones()
    local bones = table.clone(STAG_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.CometStag = {
    Skinned = true,
    Bones = stagProfileBones(),
    SkinTint = Color3.fromRGB(180, 184, 210), -- its night-blue hide washed out pale in daylight; deeper, the antlers keep their gold (seen in Play)
    Points = { "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        eaf6ff = Color3.fromRGB(190, 228, 255), -- the comet's nucleus on its brow: a touch of blue, or Neon blooms it to plain white
    },
    Effects = {
        Blast = "OnceInALifetime",
        Pulse = "Nucleus", -- (its light, trail and antler dust ride on the head bone: stagGlow)
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 214, 140),
        Amber = Color3.fromRGB(110, 190, 255),
        Orange = Color3.fromRGB(56, 120, 250),
        Sun = Color3.fromRGB(234, 246, 255),
        Ivory = Color3.fromRGB(226, 232, 246),
    },
    Animate = animateCometStag,
}

local function sandProfileBones()
    local bones = table.clone(SAND_BONES)
    for _, lid in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, lid)
    end
    return bones
end

PetRig.Profiles.SandPhantom = {
    Skinned = true,
    Bones = sandProfileBones(),
    Points = { "Tail6", "EarL", "EarR", "Hips" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "Mirage",
    },
    Colors = {
        Gold = Color3.fromRGB(226, 182, 110),
        Amber = Color3.fromRGB(246, 226, 180),
        Orange = Color3.fromRGB(176, 124, 70),
        Sun = Color3.fromRGB(255, 240, 210),
        Ivory = Color3.fromRGB(248, 238, 214),
    },
    Animate = animateSandPhantom,
}

PetRig.Profiles.SolarButterfly = {
    Skinned = true,
    Bones = {
        "Body", "Head", "Abd1", "Abd2", "Abd3", "AntL1", "AntL2", "AntR1", "AntR2",
        "ForeL1", "ForeL2", "HindL1", "HindL2", "ForeR1", "ForeR2", "HindR1", "HindR2",
    },
    Points = { "HindL2", "HindR2", "Head", "Body" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        ff8a1e = Color3.fromRGB(255, 138, 30), -- the sun-disc eyespots on its hindwings (saturated: Neon keeps the hue)
    },
    Effects = {
        Blast = "Afterglow",
        Pulse = "Eyespots",
        Light = "Eyespots",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 196, 80),
        Amber = Color3.fromRGB(250, 146, 38),
        Orange = Color3.fromRGB(226, 72, 36),
        Sun = Color3.fromRGB(255, 226, 150),
        Ivory = Color3.fromRGB(255, 240, 210),
    },
    Animate = animateSolarButterfly,
}

PetRig.Profiles.ObsidianGuardian = {
    Skinned = true,
    Bones = GUARD_BONES,
    Points = { "Head", "Hips", "Chest" },
    GlowColors = {
        ["9a50ff"] = GUARD_VIOLET, -- the slits of light that are its eyes (saturated: Neon keeps the hue)
    },
    Effects = {
        Blast = "HonestGlass",
        Pulse = "Eyes",
        Light = "Eyes",
        NovaLight = 3,
    },
    Colors = {
        Gold = Color3.fromRGB(176, 110, 255),
        Amber = Color3.fromRGB(150, 80, 240),
        Orange = Color3.fromRGB(90, 50, 160),
        Sun = Color3.fromRGB(226, 206, 255),
        Ivory = Color3.fromRGB(240, 232, 255),
    },
    Animate = animateObsidianGuardian,
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
    tweenAfter(0.55, core, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
        Size = Vector3.one * 2.4 * u,
        Transparency = 1,
    })

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
    tweenAfter(0.5, pool, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
        Size = Vector3.new(0.02 * u, 3.4 * u, 3.4 * u),
        Transparency = 1,
    })

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
            tweenAfter(appear + 0.3, streak, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                Transparency = 1,
                Size = Vector3.new(0.02, 0.02, 0.6) * u,
            })
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
            tweenAfter(delay + 0.7, bead, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
        end
    end

    local halo = neon(Vector3.one * 0.15 * u, CFrame.new(crown), colors.Sun)
    halo.Shape = Enum.PartType.Ball
    halo.Transparency = 1
    TweenService:Create(halo, TweenInfo.new(0.15, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.75), { Transparency = 0.3 }):Play()
    tweenAfter(0.9, halo, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.one * 1.6 * u,
        Transparency = 1,
    })

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
        tweenAfter(0.9, plume, TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
            CFrame = CFrame.lookAt(finish, finish + Vector3.new(math.cos(drift + 1.4), -0.3, math.sin(drift + 1.4))),
            Transparency = 1,
        })
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

-- The First Hunt: its arms snap shut, a few sparks fly from their spines, and two rings of magenta light ripple out from it, level, like the surface of
-- the first sea closing over the strike. Nothing else in the scene changes.
function Blasts.TheFirstHunt(rig, fx)
    local metre = rig.meters
    local base = rig.rootPart.CFrame
    local head = rig.points.Head
    local centre = if head then head.TransformedWorldCFrame.Position else fx.origin
    local level = CFrame.new(centre) * (base - base.Position)
    for k, delay in { 0, 0.18 } do
        task.delay(delay, function()
            if not rig.model.Parent then
                return
            end
            local ring = fx.neon(Vector3.new(0.6 * metre, 0.02, 0.6 * metre), level * CFrame.new(0, -0.05 * metre * k, 0), ANOMALO_GLOW)
            ring.Transparency = 1
            for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
                local gui = Instance.new("SurfaceGui")
                gui.Face = face
                gui.LightInfluence = 0
                gui.Brightness = 2.2
                gui.MaxDistance = 250
                gui.Parent = ring
                local image = Instance.new("ImageLabel")
                image.Size = UDim2.fromScale(1, 1)
                image.BackgroundTransparency = 1
                image.Image = ANOMALO_RING
                image.ImageColor3 = if k == 1 then ANOMALO_GLOW else Color3.fromRGB(255, 160, 225)
                image.Parent = gui
                TweenService:Create(image, TweenInfo.new(1.1, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { ImageTransparency = 1 }):Play()
            end
            local reach = (if k == 1 then 4.2 else 3.2) * metre
            TweenService:Create(ring, TweenInfo.new(1.1, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { Size = Vector3.new(reach, 0.02, reach) }):Play()
        end)
    end
    for _, key in { "ArmL5", "ArmR5" } do
        local bone = rig.points[key]
        if bone then
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(bone.TransformedWorldCFrame.Position), Color3.new(1, 1, 1))
            holder.Transparency = 1
            local sparks = Instance.new("ParticleEmitter")
            sparks.Texture = SPARKLE
            sparks.Rate = 0
            sparks.Lifetime = NumberRange.new(0.25, 0.5)
            sparks.Speed = NumberRange.new(0.6 * metre, 1.4 * metre)
            sparks.SpreadAngle = Vector2.new(180, 180)
            sparks.Drag = 3
            sparks.Size = NumberSequence.new(0.07 * metre, 0)
            sparks.Color = ColorSequence.new(Color3.fromRGB(255, 220, 245), ANOMALO_GLOW)
            sparks.LightEmission = 1
            sparks.LightInfluence = 0
            sparks.Parent = holder
            sparks:Emit(9)
        end
    end
end

-- The Void Between: a rift tears open in the air before it, two jagged edges of blue light drawn apart over a starry dark, the heads strike into it,
-- and it closes. Nothing else in the scene changes.
function Blasts.TheVoidBetween(rig, fx)
    local metre = rig.meters
    local base = rig.rootPart.CFrame
    local heads = {}
    for _, key in { "HeadL", "HeadR", "HeadML", "HeadMR" } do
        local bone = rig.points[key]
        if bone then
            table.insert(heads, bone.TransformedWorldCFrame.Position)
        end
    end
    local centre = base.Position
    if #heads > 0 then
        centre = Vector3.zero
        for _, p in heads do
            centre += p
        end
        centre /= #heads
    end
    local at = CFrame.new(centre + base.LookVector * 0.32 * metre) * (base - base.Position) -- just ahead of the heads, facing the way it faces
    local height = 0.55 * metre
    local STEPS = 7
    local function edge(sign)
        local points = {}
        for k = 0, STEPS do
            local f = k / STEPS
            local y = (f - 0.5) * height
            local jag = if k == 0 or k == STEPS then 0 else (if k % 2 == 0 then 0.35 else -0.35) * (0.6 + 0.4 * math.random())
            local open = math.sin(math.pi * f) ^ 0.7
            table.insert(points, { y = y, x = sign * (0.012 + 0.07 * open + 0.025 * jag * open) * metre })
        end
        return points
    end
    local pieces = {}
    for _, sign in { -1, 1 } do
        local pts = edge(sign)
        for k = 1, #pts - 1 do
            local a, b = Vector3.new(pts[k].x, pts[k].y, 0), Vector3.new(pts[k + 1].x, pts[k + 1].y, 0)
            local mid, length = (a + b) / 2, (b - a).Magnitude
            local seg = fx.neon(Vector3.new(0.012 * metre, length + 0.006 * metre, 0.012 * metre), at * CFrame.lookAt(mid, mid + (b - a), Vector3.zAxis) * CFrame.Angles(math.pi / 2, 0, 0), HYDRA_LIGHT)
            seg.Transparency = 0.05
            table.insert(pieces, { part = seg, x = mid.X })
        end
    end
    -- the dark between the edges, with its stars
    local dark = fx.neon(Vector3.new(0.1 * metre, height * 0.9, 0.004 * metre), at, Color3.fromRGB(4, 6, 22))
    dark.Material = Enum.Material.SmoothPlastic
    dark.Transparency = 0.15
    local stars = Instance.new("ParticleEmitter")
    stars.Texture = SPARKLE
    stars.Rate = 0
    stars.Lifetime = NumberRange.new(0.5, 0.9)
    stars.Speed = NumberRange.new(0.05 * metre, 0.25 * metre)
    stars.SpreadAngle = Vector2.new(180, 180)
    stars.Size = NumberSequence.new(0.035 * metre, 0)
    stars.Color = ColorSequence.new(Color3.fromRGB(230, 240, 255), HYDRA_LIGHT)
    stars.LightEmission = 1
    stars.LightInfluence = 0
    stars.Parent = dark
    stars:Emit(14)
    -- it opens wide at once, holds, and closes
    for _, piece in pieces do
        local from = piece.part.CFrame
        local inward = at:VectorToWorldSpace(Vector3.new(-piece.x, 0, 0)) -- toward the rift's middle line, in the rift's own frame
        piece.part.CFrame = from + inward * 0.7
        TweenService:Create(piece.part, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = from }):Play()
        task.delay(0.75, function()
            if piece.part.Parent then
                TweenService:Create(piece.part, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = from + inward, Transparency = 1 }):Play()
            end
        end)
    end
    TweenService:Create(dark, TweenInfo.new(0.12), { Size = Vector3.new(0.15 * metre, height * 0.9, 0.004 * metre) }):Play()
    task.delay(0.75, function()
        if dark.Parent then
            TweenService:Create(dark, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Size = Vector3.new(0.004 * metre, height * 0.9, 0.004 * metre), Transparency = 1 }):Play()
        end
    end)
end

-- Its writing: words in a hand nobody can read, written in the air round it at the height of its chest, a stroke at a time, all six at once; each struck
-- through; then the whole ring rises a little and is gone.
function Blasts.Unwritten(rig, fx)
    local metre = rig.meters
    local chest = rig.points.Chest
    local centre = (if chest then chest.TransformedWorldCFrame.Position else fx.origin) + Vector3.new(0, 0.08 * metre, 0)
    local facing = fx.facing
    local radius, span, thick = 0.6 * metre, 0.62, 0.016 * metre
    local WORDS, SAMPLES = 6, 6
    local function at(arc, height)
        local angle = arc / radius
        return centre + facing:VectorToWorldSpace(Vector3.new(math.sin(angle) * radius, height, -math.cos(angle) * radius))
    end
    local strokes = {}
    local function stroke(a, b, color, delay)
        local mid, length = (a + b) / 2, (b - a).Magnitude
        if length < 1e-3 then
            return
        end
        local seg = fx.neon(Vector3.new(thick, thick, length + thick), CFrame.lookAt(mid, b), color)
        seg.Transparency = 1
        TweenService:Create(seg, TweenInfo.new(0.06, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, delay), { Transparency = 0.05 }):Play()
        table.insert(strokes, seg)
    end
    for w = 0, WORDS - 1 do
        local letters = math.random(3, 4)
        local width = radius * span / letters -- each letter's share of the word, in studs
        local start = ((w + 0.5) / WORDS * 2 * math.pi - span / 2 + (math.random() - 0.5) * 0.15) * radius
        local base = ((math.random() - 0.5) * 0.06 - 0.03) * metre
        local points = {}
        for l = 0, letters - 1 do
            local kind = math.random()
            local h = (if kind < 0.25 then 0.13 elseif kind < 0.4 then -0.08 else 0.065) * metre
            local loop = 0.25 + 0.12 * math.random() -- past a sixth of a letter the pen runs back on itself: a loop
            for k = 0, SAMPLES - 1 do
                local turn = k / SAMPLES * 2 * math.pi
                local y = h * (1 - math.cos(turn)) / 2
                local x = (l + turn / (2 * math.pi) - loop * math.sin(turn)) * width + 0.3 * y -- leaning
                table.insert(points, at(start + x, base + y))
            end
        end
        table.insert(points, at(start + letters * width, base))
        local delay = 0.02 + w * 0.06
        for k = 1, #points - 1 do
            stroke(points[k], points[k + 1], NAMELESS_HALO, delay + k * 0.014)
        end
        -- struck through, left to right, once
        local strike = 0.6 + w * 0.03
        local middle = base + 0.035 * metre
        for j = 0, 2 do
            stroke(at(start - 0.02 * metre + j / 3 * (letters * width + 0.04 * metre), middle + j * 0.004 * metre), at(start - 0.02 * metre + (j + 1) / 3 * (letters * width + 0.04 * metre), middle + (j + 1) * 0.004 * metre), NAMELESS_SPARK, strike + j * 0.04)
        end
    end
    -- then all of it rises a little and fades
    for _, seg in strokes do
        tweenAfter(0.95, seg, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, CFrame = seg.CFrame + Vector3.new(0, 0.12 * metre, 0) })
    end
    local light = Instance.new("PointLight")
    light.Color = NAMELESS_HALO
    light.Range = 3 * metre
    light.Brightness = 2
    light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(centre), NAMELESS_HALO)
    light.Parent.Transparency = 1
    TweenService:Create(light, TweenInfo.new(1.3), { Brightness = 0 }):Play()
    if rig.burst then
        rig.burst:Emit(12)
    end
end

-- Totality: above it a gold sun, and a black moon sliding across it; at totality the corona flares in streamers, a ring of dark rolls out along the
-- ground and, for whoever is near, the world dims for a moment (not with Reduced Effects); Baily's beads on the moon's edge, the diamond ring, and the
-- light comes back. All of it faces the camera that sees it.
function Blasts.Totality(rig, fx)
    local metre = rig.meters
    local head = rig.points.Head
    local camera = workspace.CurrentCamera
    local centre = (if head then head.TransformedWorldCFrame.Position else fx.origin) + Vector3.new(0, 0.5 * metre, 0) -- just above it: in sight of a third-person camera
    local toCamera = if camera then (camera.CFrame.Position - centre).Unit else fx.facing.LookVector
    local face = CFrame.lookAt(centre, centre + toCamera)
    local right, up = face.RightVector, face.UpVector
    local radius = 0.2 * metre
    local disc = CFrame.Angles(0, math.pi / 2, 0) -- a cylinder's axis is its X: turned to face the camera
    local function fade(part, seconds, delay, to)
        tweenAfter(delay, part, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = to })
    end

    local sun = fx.neon(Vector3.new(0.01 * metre, 2 * radius, 2 * radius), face * disc, CAT_SUN)
    sun.Shape = Enum.PartType.Cylinder
    sun.Transparency = 1
    fade(sun, 0.15, 0, 0.05)
    fade(sun, 0.35, 1.05, 1)

    local moonAt = face * CFrame.new(0, 0, -0.02 * metre)
    local moon = fx.neon(Vector3.new(0.012 * metre, 2.04 * radius, 2.04 * radius), (moonAt + right * 2.4 * radius) * disc, Color3.fromRGB(6, 4, 14))
    moon.Material = Enum.Material.SmoothPlastic
    moon.Shape = Enum.PartType.Cylinder
    TweenService:Create(moon, TweenInfo.new(0.42, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = moonAt * disc }):Play()
    tweenAfter(0.85, moon, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = (moonAt - right * 2.4 * radius) * disc, Transparency = 1 })

    -- the corona at totality: streamers of light all round the moon's edge, and a thin ring
    for k = 1, 14 do
        local angle = (k / 14) * 2 * math.pi + math.random() * 0.3
        local direction = right * math.cos(angle) + up * math.sin(angle)
        local length = (0.3 + 0.45 * math.random()) * radius
        local at = centre + toCamera * (0.005 * metre) + direction * (radius + length / 2)
        local streamer = fx.neon(Vector3.new(0.012 * metre, 0.012 * metre, length), CFrame.lookAt(at, at + direction), CAT_CORONA)
        streamer.Transparency = 1
        fade(streamer, 0.08, 0.42, 0.15)
        fade(streamer, 0.4, 0.62, 1)
    end
    for k = 1, 24 do
        local a, b = (k / 24) * 2 * math.pi, ((k + 1) / 24) * 2 * math.pi
        local pa = centre + (right * math.cos(a) + up * math.sin(a)) * radius * 1.04
        local pb = centre + (right * math.cos(b) + up * math.sin(b)) * radius * 1.04
        local arc = fx.neon(Vector3.new(0.014 * metre, 0.014 * metre, (pb - pa).Magnitude), CFrame.lookAt((pa + pb) / 2, pb), CAT_CORONA)
        arc.Transparency = 1
        fade(arc, 0.08, 0.42, 0.05)
        fade(arc, 0.3, 0.95, 1)
    end

    -- Baily's beads, where the sun comes back, and then the diamond ring
    for k = -2, 2 do
        local angle = k * 0.28
        local bead = fx.neon(Vector3.one * 0.03 * metre, CFrame.new(centre + toCamera * (0.03 * metre) + (right * math.cos(angle) + up * math.sin(angle)) * radius), CAT_CORONA)
        bead.Shape = Enum.PartType.Ball
        bead.Transparency = 1
        fade(bead, 0.06, 0.85 + 0.02 * (k + 2), 0)
        fade(bead, 0.2, 1.0, 1)
    end
    local ringAt = centre + toCamera * (0.04 * metre) + right * radius
    local diamond = fx.neon(Vector3.one * 0.07 * metre, CFrame.new(ringAt), CAT_CORONA)
    diamond.Shape = Enum.PartType.Ball
    diamond.Transparency = 1
    fade(diamond, 0.06, 0.98, 0)
    fade(diamond, 0.35, 1.08, 1)
    for _, axis in { right, up } do
        local ray = fx.neon(Vector3.new(0.012 * metre, 0.012 * metre, 0.02 * metre), CFrame.lookAt(ringAt, ringAt + axis), CAT_CORONA)
        ray.Transparency = 1
        tweenAfter(0.98, ray, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0, Size = Vector3.new(0.012 * metre, 0.012 * metre, 0.9 * radius) })
        fade(ray, 0.3, 1.12, 1)
    end

    -- a ring of dark rolls out along the ground from it
    local ground = rig.rootPart.Position - Vector3.new(0, CAT_SOLE * metre, 0)
    local shade = fx.neon(Vector3.new(0.01 * metre, 0.2 * metre, 0.2 * metre), CFrame.new(ground + Vector3.new(0, 0.01 * metre, 0)) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(8, 6, 20))
    shade.Material = Enum.Material.SmoothPlastic
    shade.Shape = Enum.PartType.Cylinder
    shade.Transparency = 1
    tweenAfter(0.42, shade, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.01 * metre, 4 * metre, 4 * metre), Transparency = 0.45 })
    fade(shade, 0.45, 0.97, 1)

    -- for whoever is near: the world goes dark for a moment
    local player = Players.LocalPlayer
    if camera and (camera.CFrame.Position - centre).Magnitude < 45 and not (player and player:GetAttribute("SettingReducedEffects") == true) then
        local dim = Instance.new("ColorCorrectionEffect")
        dim.Name = "TotalityDim"
        dim.Parent = Lighting
        tweenAfter(0.42, dim, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = -0.16, Saturation = -0.35, TintColor = Color3.fromRGB(205, 196, 255) })
        tweenAfter(0.85, dim, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0, Saturation = 0, TintColor = Color3.new(1, 1, 1) })
        Debris:AddItem(dim, 1.4)
    end

    local light = Instance.new("PointLight")
    light.Color = CAT_CORONA
    light.Range = 3 * metre
    light.Brightness = 0
    light.Parent = diamond
    tweenAfter(0.98, light, TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 3 })
    tweenAfter(1.1, light, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 })
    if rig.burst then
        rig.burst:Emit(10)
    end
end

-- It is gone into its shadow (animateShadowcoil): the shadow races off round a loop along the ground, two points of eyeshine in it, leaving a
-- trail that fades; back where it began it heaves, and the Shadowcoil bursts up out of it in a spray of dark drops and smoke.
local SHADOW_RACE, SHADOW_STEPS = 0.78, 18 -- seconds round the loop; the loop's pieces
local SHADOW_LOOP_AHEAD, SHADOW_LOOP_SIDE = 1.15, 0.8 -- metres the loop reaches ahead of it and off to its right

local shadowRay = RaycastParams.new()
shadowRay.RespectCanCollide = true

function Blasts.FirstMove(rig, fx)
    local metre = rig.meters
    local start = rig.rootPart.Position - Vector3.new(0, SHADOW_SOLE * metre + (rig.state.drop or 0), 0)
    local ahead = (fx.facing.LookVector * Vector3.new(1, 0, 1)).Unit
    local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit
    local centre = start + right * SHADOW_LOOP_SIDE * metre

    -- the loop, laid on whatever ground is under it (a player's character doesn't count)
    local points = {}
    for k = 0, SHADOW_STEPS do
        local angle = (k / SHADOW_STEPS) * 2 * math.pi
        local at = centre - right * (SHADOW_LOOP_SIDE * metre * math.cos(angle)) + ahead * (SHADOW_LOOP_AHEAD * metre * math.sin(angle))
        local hit = workspace:Raycast(at + Vector3.new(0, 0.6 * metre, 0), Vector3.new(0, -1.2 * metre, 0), shadowRay)
        local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
        points[k] = if hit and not onCharacter then Vector3.new(at.X, hit.Position.Y, at.Z) else at
    end
    points[0], points[SHADOW_STEPS] = start, start
    local step = SHADOW_RACE / SHADOW_STEPS
    local race = TweenInfo.new(step, Enum.EasingStyle.Linear)

    -- the shadow and its faint violet rim (its top lower than the shadow's: the two never share a surface), off round the loop
    local pool = fx.neon(Vector3.one, CFrame.new(start), SHADOW_INK)
    pool.Material = Enum.Material.SmoothPlastic
    pool.Shape = Enum.PartType.Cylinder
    pool.Transparency = 0.12
    shadowDisc(pool, start, 0.02, 0.012, 0.8, metre)
    local rim = fx.neon(Vector3.one, CFrame.new(start), SHADOW_RIM)
    rim.Shape = Enum.PartType.Cylinder
    rim.Transparency = 0.55
    shadowDisc(rim, start, 0.0145, 0.014, 0.9, metre)
    local flat = CFrame.Angles(0, 0, math.pi / 2)
    for k = 1, SHADOW_STEPS do
        tweenAfter((k - 1) * step, pool, race, { CFrame = CFrame.new(points[k] + Vector3.new(0, 0.014 * metre, 0)) * flat })
        tweenAfter((k - 1) * step, rim, race, { CFrame = CFrame.new(points[k] + Vector3.new(0, 0.0075 * metre, 0)) * flat })
    end

    -- two points of eyeshine in it, looking where it goes, blinking once
    local function heading(k)
        local from, to = points[math.min(k, SHADOW_STEPS - 1)], points[math.min(k, SHADOW_STEPS - 1) + 1]
        local d = (to - from) * Vector3.new(1, 0, 1)
        return if d.Magnitude > 1e-3 then d.Unit else ahead
    end
    for _, side in { -1, 1 } do
        local function eyeAt(k)
            local forward = heading(k)
            local across = forward:Cross(Vector3.yAxis)
            return CFrame.new(points[k] + (forward * 0.2 + across * 0.07 * side + Vector3.new(0, 0.026, 0)) * metre)
        end
        local eye = fx.neon(Vector3.one * 0.045 * metre, eyeAt(0), SHADOW_EYESHINE)
        eye.Shape = Enum.PartType.Ball
        eye.Transparency = 1
        for k = 1, SHADOW_STEPS do
            tweenAfter((k - 1) * step, eye, race, { CFrame = eyeAt(k) })
        end
        local quick = TweenInfo.new(0.05, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
        tweenAfter(0.05, eye, TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0 })
        tweenAfter(0.42, eye, quick, { Transparency = 1 })
        tweenAfter(0.5, eye, quick, { Transparency = 0 })
        tweenAfter(0.72, eye, TweenInfo.new(0.06, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
    end

    -- the trail: a stain where it passed, fading as it shrinks; three heights in turn, so neighbouring stains never share a surface
    for k = 1, SHADOW_STEPS do
        local stain = fx.neon(Vector3.one, CFrame.new(points[k]), SHADOW_INK)
        stain.Material = Enum.Material.SmoothPlastic
        stain.Shape = Enum.PartType.Cylinder
        stain.Transparency = 1
        local top = 0.004 + 0.003 * (k % 3)
        shadowDisc(stain, points[k], top, 0.003, 0.66, metre)
        local passed = k * step
        tweenAfter(passed - 0.04, stain, TweenInfo.new(0.04, Enum.EasingStyle.Linear), { Transparency = 0.4 })
        tweenAfter(passed, stain, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            Transparency = 1,
            Size = Vector3.new(0.003 * metre, 0.15 * metre, 0.15 * metre),
        })
    end

    -- back where it began: the shadow heaves and shrinks away, its rim flashes outward, dark drops and smoke burst up
    local out = SHADOW_RACE + 0.02
    tweenAfter(out + 0.04, pool, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
        Transparency = 1,
        Size = Vector3.new(0.012 * metre, 0.1 * metre, 0.1 * metre),
    })
    tweenAfter(out, rim, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Transparency = 1,
        Size = Vector3.new(0.014 * metre, 2.2 * metre, 2.2 * metre),
    })
    for k = 1, 10 do
        local angle = (k / 10) * 2 * math.pi + math.random() * 0.4
        local outward = right * math.cos(angle) + ahead * math.sin(angle)
        local drop = fx.neon(Vector3.one * 0.07 * metre, CFrame.new(start + Vector3.new(0, 0.03 * metre, 0)), SHADOW_INK)
        drop.Material = Enum.Material.SmoothPlastic
        drop.Shape = Enum.PartType.Ball
        drop.Transparency = 1
        local top = start + outward * (0.3 + 0.1 * math.random()) * metre + Vector3.new(0, (0.3 + 0.15 * math.random()) * metre, 0)
        tweenAfter(out, drop, TweenInfo.new(0.05, Enum.EasingStyle.Linear), { Transparency = 0.05 })
        tweenAfter(out, drop, TweenInfo.new(0.28, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(top) })
        tweenAfter(out + 0.28, drop, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            CFrame = CFrame.new(start + outward * 0.6 * metre + Vector3.new(0, 0.02 * metre, 0)),
            Transparency = 1,
        })
    end
    local puff = fx.neon(Vector3.one * 0.05, CFrame.new(start), SHADOW_INK)
    puff.Transparency = 1
    local smoke = Instance.new("ParticleEmitter")
    smoke.Texture = "rbxasset://textures/particles/smoke_main.dds"
    smoke.Enabled = false
    smoke.Lifetime = NumberRange.new(0.6, 0.9)
    smoke.Speed = NumberRange.new(0.6 * metre, 1.4 * metre)
    smoke.SpreadAngle = Vector2.new(35, 35)
    smoke.EmissionDirection = Enum.NormalId.Top
    smoke.Drag = 3
    smoke.Rotation = NumberRange.new(0, 360)
    smoke.RotSpeed = NumberRange.new(-60, 60)
    smoke.Size = NumberSequence.new(0.2 * metre, 0.55 * metre)
    smoke.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) })
    smoke.Color = ColorSequence.new(Color3.fromRGB(60, 46, 96), Color3.fromRGB(20, 14, 34))
    smoke.LightEmission = 0
    smoke.LightInfluence = 0.5
    smoke.Parent = puff
    task.delay(out, function()
        if smoke.Parent then
            smoke:Emit(14)
        end
    end)
end

-- It has reared, pearl raised (animatePearlDragon). Heaven's light pours down out of the sky onto the pearl in a column, and the pearl draws it in:
-- rings closing on it, motes of light streaming into it. As it lunges, the condensed light bursts out: a flash, a ring rolling out along the ground,
-- shards of pearl light flung outward, and a glow on everything near.
local PEARL_BURST = 0.68 -- seconds from the start of the blast to the lunge (animatePearlDragon's lunge, at progress 0.68 of NOVA_TIME, from 0.42)
local PEARL_LIGHT, PEARL_LILAC, PEARL_VIOLET = Color3.fromRGB(255, 240, 214), Color3.fromRGB(196, 176, 255), Color3.fromRGB(132, 96, 250)

function Blasts.HeavenCondensed(rig, fx)
    local metre = rig.meters
    local pearl = pearlAt(rig, rig.state)
    local ground = rig.rootPart.Position - Vector3.new(0, PEARL_SOLE * metre + (rig.state.drop or 0), 0)

    -- the column: from above down onto the pearl, narrowing as it is drawn in. Two layers, as the breakthrough pillar has: a broad violet sheath and a
    -- bright core, both strong enough to read against a daytime sky (a single pale beam faded to nothing there, seen in Play)
    local sky = fx.neon(Vector3.one * 0.05, CFrame.new(pearl + Vector3.new(0, 5 * metre, 0)), PEARL_LIGHT)
    sky.Transparency = 1
    local into = fx.neon(Vector3.one * 0.05, CFrame.new(pearl), PEARL_LIGHT)
    into.Transparency = 1
    local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
    a0.Parent, a1.Parent = sky, into
    for layer = 1, 2 do
        local core = layer == 2
        local column = Instance.new("Beam")
        column.Attachment0, column.Attachment1 = a0, a1
        column.Segments = 1
        column.FaceCamera = true
        column.LightEmission = if core then 0.8 else 0.6
        column.LightInfluence = 0
        column.Brightness = if core then 2.2 else 1.6
        column.ZOffset = if core then 0.1 else 0
        column.Color = if core then ColorSequence.new(PEARL_LIGHT) else ColorSequence.new(PEARL_VIOLET, PEARL_LILAC)
        column.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.85), NumberSequenceKeypoint.new(0.3, if core then 0.1 else 0.3), NumberSequenceKeypoint.new(1, 0) })
        column.Width0, column.Width1 = 0, 0
        column.Parent = sky
        local w = if core then 0.32 else 1.1
        TweenService:Create(column, TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Width0 = w * metre, Width1 = w * 0.3 * metre }):Play()
        tweenAfter(0.3, column, TweenInfo.new(PEARL_BURST - 0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Width0 = 0, Width1 = 0 })
    end

    -- drawn in: rings closing on the pearl, and motes streaming into it from all round
    local holder = fx.neon(Vector3.one * 2.4 * metre, CFrame.new(pearl), PEARL_LIGHT)
    holder.Transparency = 1
    local rings = Instance.new("ParticleEmitter")
    rings.Texture = "rbxassetid://13655845087"
    rings.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    rings.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    rings.Shape = Enum.ParticleEmitterShape.Box
    rings.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    rings.Rate = 0
    rings.Speed = NumberRange.new(0)
    rings.Lifetime = NumberRange.new(0.32)
    rings.Rotation = NumberRange.new(0, 360)
    rings.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.6 * metre), NumberSequenceKeypoint.new(1, 0.05 * metre) })
    rings.Color = ColorSequence.new(PEARL_LIGHT, PEARL_LILAC)
    rings.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(0.5, 0.15), NumberSequenceKeypoint.new(1, 0.6) })
    rings.LightEmission = 1
    rings.LightInfluence = 0
    rings.LockedToPart = true
    rings.Parent = into
    for _, at in { 0.06, 0.2, 0.34 } do
        task.delay(at, function()
            if rings.Parent then
                rings:Emit(1)
            end
        end)
    end
    local motes = Instance.new("ParticleEmitter")
    motes.Texture = SPARKLE
    motes.Shape = Enum.ParticleEmitterShape.Sphere
    motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    motes.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
    motes.Rate = 70
    motes.Speed = NumberRange.new(2.2 * metre, 2.8 * metre)
    motes.Lifetime = NumberRange.new(0.42, 0.5)
    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(0.6, 0.09 * metre), NumberSequenceKeypoint.new(1, 0) })
    motes.Color = ColorSequence.new(PEARL_LILAC, PEARL_LIGHT)
    motes.LightEmission = 1
    motes.LightInfluence = 0
    motes.Parent = holder
    task.delay(PEARL_BURST - 0.45, function()
        motes.Enabled = false
    end)

    -- the burst, as it lunges: a flash in its hand, a ring rolling out along the ground, shards flung out, a glow on everything near
    local flash = fx.neon(Vector3.one * 0.1 * metre, CFrame.new(pearl), PEARL_LIGHT)
    flash.Shape = Enum.PartType.Ball
    flash.Transparency = 1
    tweenAfter(PEARL_BURST, flash, TweenInfo.new(0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0.1, Size = Vector3.one * 0.55 * metre })
    tweenAfter(PEARL_BURST + 0.08, flash, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.one * 0.8 * metre })
    local glow = Instance.new("PointLight")
    glow.Color = PEARL_LIGHT
    glow.Range = 5 * metre
    glow.Brightness = 0
    glow.Shadows = false
    glow.Parent = flash
    tweenAfter(PEARL_BURST, glow, TweenInfo.new(0.06), { Brightness = 6 })
    tweenAfter(PEARL_BURST + 0.06, glow, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 })

    local floor = fx.neon(Vector3.new(0.3, 0.05, 0.3) * metre, CFrame.new(ground + Vector3.new(0, 0.05 * metre, 0)), PEARL_LIGHT)
    floor.Transparency = 1
    local wave = Instance.new("ParticleEmitter")
    wave.Texture = "rbxassetid://13655845087"
    wave.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
    wave.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
    wave.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
    wave.EmissionDirection = Enum.NormalId.Top
    wave.Shape = Enum.ParticleEmitterShape.Box
    wave.Rate = 0
    wave.SpreadAngle = Vector2.new(0, 0)
    wave.Speed = NumberRange.new(0.01)
    wave.Lifetime = NumberRange.new(0.75)
    wave.Rotation = NumberRange.new(0, 360)
    wave.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6 * metre), NumberSequenceKeypoint.new(1, 5 * metre) })
    wave.Color = ColorSequence.new(PEARL_LIGHT, PEARL_LILAC)
    wave.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.5, 0.3), NumberSequenceKeypoint.new(1, 1) })
    wave.LightEmission = 1
    wave.LightInfluence = 0
    wave.Parent = floor
    task.delay(PEARL_BURST + 0.04, function()
        if wave.Parent then
            wave:Emit(1)
        end
    end)

    local facing = fx.facing.LookVector * Vector3.new(1, 0, 1)
    facing = if facing.Magnitude > 1e-3 then facing.Unit else Vector3.new(0, 0, -1)
    for k = 1, 9 do
        local angle = (k - 5) * 0.32 + (math.random() - 0.5) * 0.15
        local out = (CFrame.fromAxisAngle(Vector3.yAxis, angle) * facing) + Vector3.new(0, 0.25 + 0.35 * math.random(), 0)
        local shard = fx.neon(Vector3.new(0.035, 0.035, 0.11) * metre, CFrame.lookAt(pearl, pearl + out), if k % 2 == 0 then PEARL_LIGHT else PEARL_LILAC)
        shard.Transparency = 1
        local to = pearl + out.Unit * (1.6 + 0.6 * math.random()) * metre
        tweenAfter(PEARL_BURST, shard, TweenInfo.new(0.04), { Transparency = 0 })
        tweenAfter(PEARL_BURST, shard, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.lookAt(to, to + out) })
        tweenAfter(PEARL_BURST + 0.3, shard, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.new(0.01, 0.01, 0.04) * metre })
    end
    local sparks = Instance.new("ParticleEmitter")
    sparks.Texture = SPARKLE
    sparks.Enabled = false
    sparks.Lifetime = NumberRange.new(0.5, 0.9)
    sparks.Speed = NumberRange.new(2 * metre, 4 * metre)
    sparks.Drag = 4
    sparks.SpreadAngle = Vector2.new(180, 180)
    sparks.Size = NumberSequence.new(0.1 * metre, 0)
    sparks.Color = ColorSequence.new(PEARL_LIGHT, PEARL_LILAC)
    sparks.LightEmission = 1
    sparks.LightInfluence = 0
    sparks.Parent = flash
    task.delay(PEARL_BURST, function()
        if sparks.Parent then
            sparks:Emit(18)
        end
    end)
end

-- It springs (animateSnowLeopard): frost bursts up from where it left the ground, and ahead of it, one after another, a line of its pawprints freezes
-- into the ground, glowing ice-blue with starlight; then each print shatters into a puff of glittering snow.
local LEOPARD_PRINTS = 6
local LEOPARD_PRINT_SIZE = 2 -- its prints, twice its paw: at a pet's size, a print the size of its paw is lost on pale ground (seen in Play)
local LEOPARD_PRINT_GLOW = Color3.fromRGB(70, 160, 255)

local leopardRay = RaycastParams.new()
leopardRay.RespectCanCollide = true
-- The roads and paved floors are decoration laid over the terrain (no collision, invisible to rays) and drawn about 0.4 studs above it (measured in
-- Play with markers at stepped heights): a mark meant to lie on the ground goes that far above a terrain hit, or the paving covers it
local LEOPARD_OVER_TERRAIN = 0.45

-- where a mark on the ground goes, at a point: on whatever is under it, lifted clear of paving over terrain; nil if nothing is under it
local function leopardGroundAt(at, metre)
    local hit = workspace:Raycast(at + Vector3.new(0, 0.5 * metre, 0), Vector3.new(0, -1 * metre, 0), leopardRay)
    if not hit or (hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")) then
        return nil
    end
    return Vector3.new(at.X, hit.Position.Y + (if hit.Instance:IsA("Terrain") then LEOPARD_OVER_TERRAIN else 0.03), at.Z)
end

function Blasts.WhereTheSkyBegins(rig, fx)
    local metre = rig.meters
    local ground = rig.rootPart.Position - Vector3.new(0, LEOPARD_SOLE * metre + (rig.state.drop or 0), 0)
    local ahead = (fx.facing.LookVector * Vector3.new(1, 0, 1)).Unit
    local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit

    -- frost bursting up where it sprang, and a ring of rime across the ground
    local holder = fx.neon(Vector3.new(0.5, 0.05, 0.5) * metre, CFrame.new(ground + Vector3.new(0, 0.03 * metre, 0)), LEOPARD_ICE)
    holder.Transparency = 1
    local frost = Instance.new("ParticleEmitter")
    frost.Texture = "rbxasset://textures/particles/smoke_main.dds"
    frost.Enabled = false
    frost.Lifetime = NumberRange.new(0.6, 1)
    frost.Speed = NumberRange.new(0.8 * metre, 1.6 * metre)
    frost.SpreadAngle = Vector2.new(60, 60)
    frost.EmissionDirection = Enum.NormalId.Top
    frost.Drag = 3
    frost.Rotation = NumberRange.new(0, 360)
    frost.RotSpeed = NumberRange.new(-50, 50)
    frost.Size = NumberSequence.new(0.18 * metre, 0.5 * metre)
    frost.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
    frost.Color = ColorSequence.new(Color3.fromRGB(246, 252, 255), LEOPARD_ICE)
    frost.LightEmission = 0.3
    frost.LightInfluence = 0.4
    frost.Parent = holder
    frost:Emit(16)
    local glitter = Instance.new("ParticleEmitter")
    glitter.Texture = SPARKLE
    glitter.Enabled = false
    glitter.Lifetime = NumberRange.new(0.5, 0.9)
    glitter.Speed = NumberRange.new(1 * metre, 2.2 * metre)
    glitter.SpreadAngle = Vector2.new(70, 70)
    glitter.EmissionDirection = Enum.NormalId.Top
    glitter.Drag = 2
    glitter.Acceleration = Vector3.new(0, -1.5 * metre, 0)
    glitter.Size = NumberSequence.new(0.06 * metre, 0)
    glitter.Color = ColorSequence.new(Color3.new(1, 1, 1), LEOPARD_STAR)
    glitter.LightEmission = 1
    glitter.LightInfluence = 0
    glitter.Parent = holder
    glitter:Emit(24)
    local rimeAt = leopardGroundAt(ground, metre) or ground
    local rime = fx.neon(Vector3.new(0.008 * metre, 0.3 * metre, 0.3 * metre), CFrame.new(rimeAt) * CFrame.Angles(0, 0, math.pi / 2), LEOPARD_ICE)
    rime.Shape = Enum.PartType.Cylinder
    rime.Material = Enum.Material.Glass
    rime.Transparency = 0.35
    TweenService:Create(rime, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.008 * metre, 2.4 * metre, 2.4 * metre) }):Play()
    tweenAfter(0.35, rime, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })

    -- its pawprints, freezing into the ground ahead of it one by one: a big heel pad and four toes, staggered left and right
    for k = 1, LEOPARD_PRINTS do
        local side = if k % 2 == 0 then 1 else -1
        local at = ground + ahead * (0.45 + 0.42 * k) * metre + right * side * 0.12 * metre
        at = leopardGroundAt(at, metre) or at
        local face = CFrame.lookAt(at, at + ahead)
        local appear = 0.06 + 0.07 * k
        local pads = { { 0, 0.02, 0.09, 0.075 } }
        for j = -1.5, 1.5 do
            table.insert(pads, { j * 0.028, -0.05 - 0.012 * (1 - math.abs(j) / 1.5), 0.038, 0.042 })
        end
        for _, pad in pads do
            local k2 = LEOPARD_PRINT_SIZE
            local cf = face * CFrame.new(pad[1] * k2 * metre, 0, pad[2] * k2 * metre) * CFrame.Angles(0, 0, math.pi / 2)
            local mark = fx.neon(Vector3.new(0.004 * metre, pad[4] * k2 * metre, pad[3] * k2 * metre), cf, LEOPARD_PRINT_GLOW)
            mark.Shape = Enum.PartType.Cylinder
            mark.Transparency = 1
            tweenAfter(appear, mark, TweenInfo.new(0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0 })
            tweenAfter(appear + 0.55, mark, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
        end
        -- as it freezes in, a few motes of starlight rise off it: they show above grass, which hides anything flat on the ground
        task.delay(appear, function()
            if not holder.Parent then
                return
            end
            local glint = fx.neon(Vector3.one * 0.05, CFrame.new(at + Vector3.new(0, 0.03 * metre, 0)), LEOPARD_ICE)
            glint.Transparency = 1
            local rise = glitter:Clone()
            rise.EmissionDirection = Enum.NormalId.Top
            rise.SpreadAngle = Vector2.new(15, 15)
            rise.Speed = NumberRange.new(0.5 * metre, 0.9 * metre)
            rise.Acceleration = Vector3.zero
            rise.Drag = 3
            rise.Lifetime = NumberRange.new(0.5, 0.8)
            rise.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07 * metre), NumberSequenceKeypoint.new(1, 0) })
            rise.Color = ColorSequence.new(LEOPARD_ICE, LEOPARD_PRINT_GLOW)
            rise.Parent = glint
            rise:Emit(5)
        end)
        task.delay(appear + 0.6, function()
            if not holder.Parent then
                return
            end
            local puff = fx.neon(Vector3.one * 0.05, CFrame.new(at + Vector3.new(0, 0.02 * metre, 0)), LEOPARD_ICE)
            puff.Transparency = 1
            local snow = glitter:Clone()
            snow.Speed = NumberRange.new(0.3 * metre, 0.8 * metre)
            snow.Size = NumberSequence.new(0.045 * metre, 0)
            snow.Lifetime = NumberRange.new(0.35, 0.6) -- gone before the special's folder is (2 s)
            snow.Parent = puff
            snow:Emit(7)
        end)
    end
end

-- It has reared (animateCometStag). A comet leaves its brow: a white-hot head with a straight blue ion tail and a broad, curving gold dust tail, arcing
-- up and across the sky; at the top of its arc it bursts into a shower of glittering dust that falls slowly over the stag.
local STAG_ARC_TIME, STAG_ARC_STEPS = 1.05, 14

function Blasts.OnceInALifetime(rig, fx)
    local metre = rig.meters
    local s = rig.state
    local from = if s.nucleus then s.nucleus.WorldPosition else fx.origin
    local ahead = (fx.facing.LookVector * Vector3.new(1, 0, 1)).Unit
    local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit
    -- the arc: up from its brow and forward over its head, a little to its right, bursting above and ahead of it. Low and forward, so the burst stays in a
    -- following camera's view over the pet, wherever the pet is on screen (higher, or across to the side, it left the screen or went behind the HUD's
    -- corner panels: seen in Play and measured on screen)
    local p1 = from + Vector3.yAxis * 1.6 * metre + ahead * 0.4 * metre
    local p2 = from + Vector3.yAxis * 1.1 * metre + right * 0.5 * metre + ahead * 2.2 * metre
    local function arc(f)
        local a = from:Lerp(p1, f)
        local b = p1:Lerp(p2, f)
        return a:Lerp(b, f)
    end

    local head = fx.neon(Vector3.one * 0.14 * metre, CFrame.new(from), STAG_ICE)
    head.Shape = Enum.PartType.Ball
    local glow = Instance.new("PointLight")
    glow.Color = STAG_ICE
    glow.Range = 4 * metre
    glow.Brightness = 3
    glow.Parent = head
    local function tail(half, life, color, width)
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Position, a1.Position = Vector3.new(0, half * metre, 0), Vector3.new(0, -half * metre, 0)
        a0.Parent, a1.Parent = head, head
        local trail = Instance.new("Trail")
        trail.Attachment0, trail.Attachment1 = a0, a1
        trail.Lifetime = life
        trail.FaceCamera = true
        trail.LightEmission = 1
        trail.LightInfluence = 0
        trail.MinLength = 0
        trail.WidthScale = width
        trail.Color = color
        trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.35), NumberSequenceKeypoint.new(1, 1) })
        trail.Parent = head
    end
    tail(0.05, 0.35, ColorSequence.new(STAG_ICE, STAG_ION), NumberSequence.new(1, 0.4))                                  -- the ion tail: narrow, straight, blue
    tail(0.14, 0.6, ColorSequence.new({ ColorSequenceKeypoint.new(0, STAG_ICE), ColorSequenceKeypoint.new(0.3, STAG_DUST), ColorSequenceKeypoint.new(1, Color3.fromRGB(236, 176, 92)) }),
        NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.4, 1), NumberSequenceKeypoint.new(1, 0.6) }))   -- the dust tail: broad and gold
    local step = STAG_ARC_TIME / STAG_ARC_STEPS
    for k = 1, STAG_ARC_STEPS do
        local f = k / STAG_ARC_STEPS
        local eased = 1 - (1 - f) ^ 1.6 -- fast off its brow, slowing at the top of the arc
        tweenAfter((k - 1) * step, head, TweenInfo.new(step, Enum.EasingStyle.Linear), { CFrame = CFrame.new(arc(eased)) })
    end
    -- a flash at its brow as the comet leaves
    local flash = fx.neon(Vector3.one * 0.08 * metre, CFrame.new(from), STAG_ICE)
    flash.Shape = Enum.PartType.Ball
    TweenService:Create(flash, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.6 * metre, Transparency = 1 }):Play()

    -- the burst at the top of the arc: the head flares and goes, and its dust falls glittering
    tweenAfter(STAG_ARC_TIME, head, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.5 * metre, Transparency = 1 })
    tweenAfter(STAG_ARC_TIME, glow, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 })
    local shower = fx.neon(Vector3.one * 0.05, CFrame.new(arc(1)), STAG_DUST)
    shower.Transparency = 1
    local dust = Instance.new("ParticleEmitter")
    dust.Texture = SPARKLE
    dust.Enabled = false
    dust.Lifetime = NumberRange.new(0.5, 0.8)
    dust.Speed = NumberRange.new(0.6 * metre, 1.5 * metre)
    dust.SpreadAngle = Vector2.new(180, 180)
    dust.Acceleration = Vector3.new(0, -2 * metre, 0)
    dust.Drag = 1.5
    dust.Rotation = NumberRange.new(0, 360)
    dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * metre), NumberSequenceKeypoint.new(1, 0) })
    dust.Color = ColorSequence.new(STAG_DUST, STAG_ION)
    dust.LightEmission = 1
    dust.LightInfluence = 0
    dust.Parent = shower
    task.delay(STAG_ARC_TIME, function()
        if dust.Parent then
            dust:Emit(40)
        end
    end)
end

-- It has blown away as sand (animateSandPhantom). A dust devil spins up a little to its right, tall and twisting, a ring of sand skittering round its
-- foot; it re-forms inside it and the devil collapses in a puff as it shakes the sand off. Then it hops back.
local SAND_DEVIL_TIME = 1.0

function Blasts.Mirage(rig, fx)
    local metre = rig.meters
    local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit
    local ground = rig.rootPart.Position - Vector3.new(0, SAND_SOLE * metre + (rig.state.drop or 0), 0)
    local at = ground + right * SAND_AWAY * metre

    -- the devil: a funnel of sand, narrow at the ground and flaring at the top, spinning; its holders turn, so the sand comes off them in a twist.
    -- Dense, warm and barely lit by the world: thin and pale, the first version was nearly invisible against grass (seen in Play)
    local function funnel(width, height, y, rate, size, speed, spread)
        local holder = fx.neon(Vector3.new(width, height, width) * metre, CFrame.new(at + Vector3.new(0, y * metre, 0)), SAND_GOLD)
        holder.Transparency = 1
        local spin = TweenInfo.new(0.2, Enum.EasingStyle.Linear)
        for k = 0, math.floor(SAND_DEVIL_TIME / 0.2) do
            tweenAfter(k * 0.2, holder, spin, { CFrame = CFrame.new(holder.Position) * CFrame.Angles(0, (k + 1) * math.pi * 0.8, 0) })
        end
        local sand = Instance.new("ParticleEmitter")
        sand.Texture = "rbxasset://textures/particles/smoke_main.dds"
        sand.Shape = Enum.ParticleEmitterShape.Cylinder
        sand.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        sand.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
        sand.EmissionDirection = Enum.NormalId.Top
        sand.Rate = rate
        sand.Lifetime = NumberRange.new(0.45, 0.75)
        sand.Speed = NumberRange.new(speed * 0.6 * metre, speed * metre)
        sand.SpreadAngle = Vector2.new(spread, spread)
        sand.Drag = 1.5
        sand.Rotation = NumberRange.new(0, 360)
        sand.RotSpeed = NumberRange.new(200, 360)
        sand.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, size * metre), NumberSequenceKeypoint.new(1, size * 2.2 * metre) })
        sand.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.55, 0.15), NumberSequenceKeypoint.new(1, 1) })
        sand.Color = ColorSequence.new(SAND_DUSK:Lerp(SAND_GOLD, 0.5), SAND_DUSK)        -- a deeper ochre: it must stand out against yellow-green grass
        sand.LightEmission = 0.15
        sand.LightInfluence = 0.25
        sand.Parent = holder
        task.delay(SAND_DEVIL_TIME - 0.2, function()
            sand.Enabled = false
        end)
        return holder
    end
    local holder = funnel(0.22, 0.5, 0.25, 150, 0.2, 0.9, 10)         -- the narrow foot of it
    funnel(0.45, 0.4, 0.75, 120, 0.28, 0.7, 30)                         -- the middle
    funnel(0.8, 0.3, 1.15, 100, 0.34, 0.45, 55)                         -- the flared top
    -- three ribbons of sand winding up round it, widening as they climb: what makes a haze read as a whirlwind (seen in Play)
    local steps = 16
    local step = (SAND_DEVIL_TIME - 0.25) / steps
    for r = 0, 2 do
        local function spiral(k)
            local f = k / steps
            local angle = r * 2 * math.pi / 3 + f * 4 * math.pi
            local radius = (0.08 + 0.32 * f) * metre
            return CFrame.new(at + Vector3.new(math.cos(angle) * radius, (0.05 + 1.25 * f) * metre, math.sin(angle) * radius))
        end
        local head = fx.neon(Vector3.one * 0.05, spiral(0), SAND_GOLD)
        head.Transparency = 1
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Position, a1.Position = Vector3.new(0, 0.05 * metre, 0), Vector3.new(0, -0.05 * metre, 0)
        a0.Parent, a1.Parent = head, head
        local ribbon = Instance.new("Trail")
        ribbon.Attachment0, ribbon.Attachment1 = a0, a1
        ribbon.Lifetime = 0.35
        ribbon.FaceCamera = true
        ribbon.LightEmission = 0.2
        ribbon.LightInfluence = 0.3
        ribbon.Color = ColorSequence.new(SAND_PALE, SAND_DUSK)
        ribbon.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
        ribbon.WidthScale = NumberSequence.new(1, 0.3)
        ribbon.Parent = head
        for k = 1, steps do
            tweenAfter(0.05 * r + (k - 1) * step, head, TweenInfo.new(step, Enum.EasingStyle.Linear), { CFrame = spiral(k) })
        end
    end

    -- grains glinting in it
    local grains = Instance.new("ParticleEmitter")
    grains.Texture = SPARKLE
    grains.Shape = Enum.ParticleEmitterShape.Cylinder
    grains.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    grains.EmissionDirection = Enum.NormalId.Top
    grains.Rate = 40
    grains.Lifetime = NumberRange.new(0.5, 0.8)
    grains.Speed = NumberRange.new(1 * metre, 1.8 * metre)
    grains.SpreadAngle = Vector2.new(35, 35)
    grains.Size = NumberSequence.new(0.04 * metre, 0)
    grains.Color = ColorSequence.new(SAND_PALE)
    grains.LightEmission = 1
    grains.LightInfluence = 0
    grains.Parent = holder
    task.delay(SAND_DEVIL_TIME - 0.2, function()
        grains.Enabled = false
    end)

    -- the ring of sand round its foot, skittering out along the ground
    local foot = fx.neon(Vector3.new(0.3, 0.05, 0.3) * metre, CFrame.new(at + Vector3.new(0, 0.05 * metre, 0)), SAND_GOLD)
    foot.Transparency = 1
    local skitter = Instance.new("ParticleEmitter")
    skitter.Texture = "rbxasset://textures/particles/smoke_main.dds"
    skitter.Shape = Enum.ParticleEmitterShape.Disc
    skitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    skitter.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
    skitter.EmissionDirection = Enum.NormalId.Top
    skitter.Rate = 30
    skitter.Lifetime = NumberRange.new(0.4, 0.6)
    skitter.Speed = NumberRange.new(0.2 * metre, 0.4 * metre)
    skitter.SpreadAngle = Vector2.new(80, 80)
    skitter.Acceleration = Vector3.new(0, -1 * metre, 0)
    skitter.Size = NumberSequence.new(0.12 * metre, 0.26 * metre)
    skitter.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) })
    skitter.Color = ColorSequence.new(SAND_GOLD, SAND_DUSK)
    skitter.LightInfluence = 0.25
    skitter.Parent = foot
    task.delay(SAND_DEVIL_TIME - 0.2, function()
        skitter.Enabled = false
    end)

    -- the collapse: as it shakes off, a last puff of sand bursts out round it
    task.delay(0.8, function()
        if not holder.Parent then
            return
        end
        local puff = skitter:Clone()
        puff.Speed = NumberRange.new(0.6 * metre, 1.1 * metre)
        puff.SpreadAngle = Vector2.new(60, 60)
        puff.Parent = foot
        puff.Enabled = false
        puff:Emit(18)
    end)
end

-- It has gathered the afternoon's sunlight in its wings (animateSolarButterfly) and lets it go: a warm light flares from it and turns through sunset to
-- dusk as it fades; motes of gold drift up and out from its wings, reddening and dimming as they go; for whoever is near, the world takes on a sunset's
-- warmth for a moment, then the colour of dusk, then is itself again.
function Blasts.Afterglow(rig, fx)
    local metre = rig.meters
    local at = rig.rootPart.Position
    local holder = fx.neon(Vector3.new(1.2, 0.2, 0.8) * metre, CFrame.new(at), BFLY_GOLD)
    holder.Transparency = 1

    -- the light: a flare of noon gold, turning to sunset rose and then to dusk as it fades
    local glow = Instance.new("PointLight")
    glow.Color = BFLY_GOLD
    glow.Range = 2 * metre
    glow.Brightness = 0
    glow.Shadows = false
    glow.Parent = holder
    TweenService:Create(glow, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 5, Range = 6 * metre }):Play()
    tweenAfter(0.25, glow, TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Color = BFLY_ROSE, Brightness = 3.5 })
    tweenAfter(0.8, glow, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Color = BFLY_DUSK, Brightness = 0 })

    -- the motes: gold drifting up and outward from the wings, reddening to dusk and dimming
    local motes = Instance.new("ParticleEmitter")
    motes.Texture = SPARKLE
    motes.Enabled = false
    motes.Shape = Enum.ParticleEmitterShape.Box
    motes.Lifetime = NumberRange.new(0.9, 1.4)
    motes.Speed = NumberRange.new(0.4 * metre, 0.9 * metre)
    motes.SpreadAngle = Vector2.new(70, 70)
    motes.EmissionDirection = Enum.NormalId.Top
    motes.Drag = 1.6
    motes.Acceleration = Vector3.new(0, 0.3 * metre, 0)
    motes.Rotation = NumberRange.new(0, 360)
    motes.RotSpeed = NumberRange.new(-60, 60)
    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(0.25, 0.1 * metre), NumberSequenceKeypoint.new(1, 0) })
    motes.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, BFLY_GOLD), ColorSequenceKeypoint.new(0.5, BFLY_ROSE), ColorSequenceKeypoint.new(1, BFLY_DUSK) })
    motes.LightEmission = 1
    motes.LightInfluence = 0
    motes.Parent = holder
    motes:Emit(36)
    -- a soft glow round it, the warmth leaving its wings
    local haze = Instance.new("ParticleEmitter")
    haze.Texture = "rbxasset://textures/particles/smoke_main.dds"
    haze.Enabled = false
    haze.Lifetime = NumberRange.new(0.8, 1.1)
    haze.Speed = NumberRange.new(0.1 * metre, 0.3 * metre)
    haze.SpreadAngle = Vector2.new(180, 180)
    haze.Size = NumberSequence.new(0.5 * metre, 1.4 * metre)
    haze.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 1) })
    haze.Color = ColorSequence.new(BFLY_GOLD, BFLY_ROSE)
    haze.LightEmission = 1
    haze.LightInfluence = 0
    haze.Parent = holder
    haze:Emit(6)

    -- for whoever is near: a sunset's warmth for a moment, then dusk, then the world is itself again
    local player = Players.LocalPlayer
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - at).Magnitude < 45 and not (player and player:GetAttribute("SettingReducedEffects") == true) then
        local grade = Instance.new("ColorCorrectionEffect")
        grade.Name = "AfterglowGrade"
        grade.Parent = Lighting
        TweenService:Create(grade, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { TintColor = Color3.fromRGB(255, 226, 196), Brightness = 0.04, Saturation = 0.12 }):Play()
        tweenAfter(0.45, grade, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { TintColor = Color3.fromRGB(226, 206, 246), Brightness = -0.04, Saturation = -0.05 })
        tweenAfter(1.0, grade, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { TintColor = Color3.new(1, 1, 1), Brightness = 0, Saturation = 0 })
        Debris:AddItem(grade, 1.6)
    end
end

-- It has held you in its gaze (animateObsidianGuardian) and gives you back to yourself: its mirror face flashes, and for a moment a figure of black glass
-- stands before it in your shape, facing you; then the figure cracks and falls apart into shards of violet glass that tumble and fade. Whose shape: its
-- owner's (rig.owner, set by whoever builds it), else whoever stands nearest it.
local GUARD_MOST_PIECES = 60 -- a figure made of more parts than this keeps only the first ones (a costume of a hundred accessories costs too much)

local function guardOwnerCharacter(rig)
    local owner = rig.owner
    if owner and owner.Character and owner.Character:FindFirstChild("HumanoidRootPart") then
        return owner.Character
    end
    local best, bestDistance = nil, 30 * rig.unit
    for _, player in Players:GetPlayers() do
        local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        if root then
            local distance = (root.Position - rig.rootPart.Position).Magnitude
            if distance < bestDistance then
                best, bestDistance = player.Character, distance
            end
        end
    end
    return best
end

local function guardShatter(copy, centre, u, folder)
    local size = copy.Size
    for _ = 1, 2 do
        local shard = Instance.new("WedgePart")
        shard.Anchored = true
        shard.CanCollide = false
        shard.CanTouch = false
        shard.CanQuery = false
        shard.CastShadow = false
        shard.Material = Enum.Material.Glass
        shard.Color = GUARD_GLASS:Lerp(GUARD_VIOLET, 0.35 + 0.3 * math.random())
        shard.Reflectance = 0.3
        shard.Transparency = 0.1
        local k = math.clamp(math.min(size.X, size.Y, size.Z) / u, 0.12, 0.35)
        shard.Size = Vector3.new(0.04, 0.6 + 0.5 * math.random(), 0.45 + 0.4 * math.random()) * k * u
        local offset = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * size * 0.6
        local at = copy.CFrame * CFrame.new(offset)
        shard.CFrame = at * CFrame.Angles(math.random() * 6.28, math.random() * 6.28, math.random() * 6.28)
        shard.Parent = folder
        local away = (at.Position - centre) * Vector3.new(1, 0, 1)
        away = if away.Magnitude > 1e-3 then away.Unit else Vector3.new(math.random() - 0.5, 0, math.random() - 0.5).Unit
        local out = at.Position + away * (0.8 + 1.2 * math.random()) * u + Vector3.new(0, (0.3 + 0.4 * math.random()) * u, 0)
        local spin = CFrame.Angles(math.random() * 3, math.random() * 3, math.random() * 3)
        TweenService:Create(shard, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(out) * spin * shard.CFrame.Rotation }):Play()
        tweenAfter(0.35, shard, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            CFrame = CFrame.new(out - Vector3.new(0, (1 + 0.6 * math.random()) * u, 0) + away * 0.4 * u) * spin * spin * shard.CFrame.Rotation,
            Transparency = 1,
        })
    end
end

function Blasts.HonestGlass(rig, fx)
    local u, neon = rig.unit, fx.neon
    local facing = fx.facing.LookVector
    local head = rig.points.Head
    local face = (if head then head.TransformedWorldCFrame.Position else rig.rootPart.Position) + facing * 0.12 * rig.meters

    -- the mirror flashes: a violet-white flare at its face, a burst of glints, a light that cools to violet as it fades
    local flare = neon(Vector3.one * 0.2 * u, CFrame.new(face), GUARD_PALE)
    flare.Shape = Enum.PartType.Ball
    flare.Transparency = 0.1
    TweenService:Create(flare, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.1 * u, Transparency = 1 }):Play()
    local folder = flare.Parent
    local light = Instance.new("PointLight")
    light.Color = GUARD_PALE
    light.Range = 4.5 * u
    light.Brightness = 0
    light.Shadows = false
    light.Parent = flare
    TweenService:Create(light, TweenInfo.new(0.06), { Brightness = 2.2 }):Play() -- (a brighter or wider light washed the whole scene white in Play)
    tweenAfter(0.08, light, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0, Color = GUARD_VIOLET })
    local glints = Instance.new("ParticleEmitter")
    glints.Texture = SPARKLE
    glints.Enabled = false
    glints.Lifetime = NumberRange.new(0.4, 0.8)
    glints.Speed = NumberRange.new(1.5 * u, 3 * u)
    glints.SpreadAngle = Vector2.new(180, 180)
    glints.Drag = 3
    glints.Rotation = NumberRange.new(0, 360)
    glints.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
    glints.Color = ColorSequence.new(GUARD_PALE, GUARD_VIOLET)
    glints.LightEmission = 1
    glints.LightInfluence = 0
    glints.Parent = flare
    glints:Emit(24)

    -- the figure: whoever it shows, made of black glass, standing between it and them, facing them; not drawn with reduced effects or from far off
    local player = Players.LocalPlayer
    local camera = workspace.CurrentCamera
    local character = guardOwnerCharacter(rig)
    local ownerRoot = character and character:FindFirstChild("HumanoidRootPart")
    if not ownerRoot or not camera or (camera.CFrame.Position - face).Magnitude > 70 or (player and player:GetAttribute("SettingReducedEffects") == true) then
        return
    end
    local toOwner = (ownerRoot.Position - rig.rootPart.Position) * Vector3.new(1, 0, 1)
    if toOwner.Magnitude < 0.5 then
        toOwner = facing * Vector3.new(1, 0, 1)
    end
    local spot = rig.rootPart.Position + toOwner.Unit * math.clamp(toOwner.Magnitude * 0.45, 1.2 * u, 2.4 * u)
    local params = RaycastParams.new()
    params.FilterDescendantsInstances = { character, rig.model, folder }
    local hit = workspace:Raycast(spot + Vector3.new(0, 6 * u, 0), Vector3.new(0, -20 * u, 0), params)
    local groundY = if hit then hit.Position.Y else rig.rootPart.Position.Y - 1.5 * u
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local standing = (if humanoid then humanoid.HipHeight else 2) + ownerRoot.Size.Y / 2
    local at = Vector3.new(spot.X, groundY + standing, spot.Z)
    local target = CFrame.lookAt(at, Vector3.new(ownerRoot.Position.X, at.Y, ownerRoot.Position.Z))
    local glass = {}
    for _, piece in character:GetDescendants() do
        if #glass >= GUARD_MOST_PIECES then
            break
        end
        if piece:IsA("BasePart") and piece ~= ownerRoot and piece.Transparency < 0.95 then
            local copy = piece:Clone() -- (nil when a piece may not be copied)
            if copy then
                for _, child in copy:GetChildren() do
                    if not child:IsA("DataModelMesh") then
                        child:Destroy()
                    end
                end
                copy.Anchored = true
                copy.CanCollide = false
                copy.CanTouch = false
                copy.CanQuery = false
                copy.CastShadow = false
                copy.Material = Enum.Material.Glass
                copy.Color = GUARD_GLASS
                copy.Reflectance = 0.25
                copy.Transparency = 1
                if copy:IsA("MeshPart") then
                    copy.TextureID = ""
                end
                local mesh = copy:FindFirstChildWhichIsA("SpecialMesh")
                if mesh then
                    mesh.TextureId = ""
                end
                copy.CFrame = target * ownerRoot.CFrame:ToObjectSpace(piece.CFrame)
                copy.Parent = folder
                table.insert(glass, copy)
                TweenService:Create(copy, TweenInfo.new(0.18), { Transparency = 0.2 }):Play()
            end
        end
    end
    local glow = Instance.new("PointLight")
    glow.Color = GUARD_VIOLET
    glow.Range = 4 * u
    glow.Brightness = 1.5
    glow.Shadows = false
    glow.Parent = neon(Vector3.one * 0.05, CFrame.new(at), GUARD_VIOLET)

    -- it cracks, and falls apart into shards
    task.delay(0.55, function()
        if not folder.Parent then
            return
        end
        for _, copy in glass do
            guardShatter(copy, at, u, folder)
            copy.Transparency = 1
        end
        glow.Brightness = 3
        TweenService:Create(glow, TweenInfo.new(0.5), { Brightness = 0 }):Play()
        local burst = Instance.new("ParticleEmitter")
        burst.Texture = SPARKLE
        burst.Enabled = false
        burst.Lifetime = NumberRange.new(0.4, 0.9)
        burst.Speed = NumberRange.new(1 * u, 2.5 * u)
        burst.SpreadAngle = Vector2.new(180, 180)
        burst.Drag = 2
        burst.Acceleration = Vector3.new(0, -2 * u, 0)
        burst.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(1, 0) })
        burst.Color = ColorSequence.new(GUARD_PALE, GUARD_VIOLET)
        burst.LightEmission = 1
        burst.LightInfluence = 0
        burst.Parent = glow.Parent
        burst:Emit(30)
    end)
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
        tweenAfter(delay + 0.06, ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = CFrame.lookAt(finish, finish + forward) * CFrame.Angles(0, math.pi / 2, 0),
            Size = Vector3.new(0.02 * u, (1.6 + 0.5 * index) * u, (1.6 + 0.5 * index) * u),
            Transparency = 1,
        })
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
        tweenAfter(0.6, ray, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
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

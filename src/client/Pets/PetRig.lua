local Debris = game:GetService("Debris")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local PetRig = {}

-- (kept on the module, not as locals: the main chunk sits at Luau's 200-local limit)
PetRig.Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
PetRig.PetSounds = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("PetSounds"))
PetRig.VOICE_EVERY = { 9, 18 } -- seconds between a pet's calls while it idles in the world (PetSounds)
PetRig.Quality = require(script.Parent.Parent:WaitForChild("Quality")) -- the phone tier: other players' pets drop their lights

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
local animateSunDragon -- animateSunDragon's section below (its own locals stay in its block)
do
    function animateSunDragon(rig, s, moving, fly, nova)
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
end
local animateHellhound -- animateHellhound's section below (its own locals stay in its block)
do

    local HOUND_HEADS = { C = 0, L = 2.1, R = 4.2 }
    function animateHellhound(rig, s, moving, fly, nova)
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
end
local animateSprite -- animateSprite's section below (its own locals stay in its block)
do

    function animateSprite(rig, s, moving, fly, nova)
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
end
local animateGolem -- animateGolem's section below (its own locals stay in its block)
do

    function animateGolem(rig, s, moving, fly, nova)
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
end
local animatePanda -- animatePanda's section below (its own locals stay in its block)
do

    local PANDA_LEGS = { LegFL = 0, LegBR = 0.3, LegFR = math.pi, LegBL = math.pi + 0.3 }
    function animatePanda(rig, s, moving, fly, nova)
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
end
local animateDeer -- animateDeer's section below (its own locals stay in its block)
do

    local DEER_LEGS = { LegBL = 0, LegFL = math.pi / 2, LegBR = math.pi, LegFR = 3 * math.pi / 2 }
    function animateDeer(rig, s, moving, fly, nova)
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
end
local animatePhoenix -- animatePhoenix's section below (its own locals stay in its block)
do

    function animatePhoenix(rig, s, moving, fly, nova)
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
end
local animateSphinx -- animateSphinx's section below (its own locals stay in its block)
do

    local SPHINX_LEGS = { LegFL = 0, LegBR = 0.2, LegFR = math.pi, LegBL = math.pi + 0.2 }
    function animateSphinx(rig, s, moving, fly, nova)
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
end
local animateCub -- animateCub's section below (its own locals stay in its block)
do

    function animateCub(rig, s, moving, fly, nova)
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
end
local animateCrane -- animateCrane's section below (its own locals stay in its block)
do

    function animateCrane(rig, s, moving, fly, nova)
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
end
local animateCloudSheep -- animateCloudSheep's section below (its own locals stay in its block)
do


    -- The Cloud Sheep (skinned): always half asleep, its hooves paddling at the air. It breathes with its whole fleece, its lobes on their own bones; its head sinks as it nods off and comes up with a
    -- start; it yawns. +X swings a limb's far end forward.
    local SHEEP_LEADS = { FL = 0, BR = 0.4, FR = math.pi, BL = math.pi + 0.4 }
    local SHEEP_LID_HINGE = { L = Vector3.new(0.7476, 0.1035, -0.6561), R = Vector3.new(0.7476, -0.1035, 0.6561) }
    local SHEEP_WOOL = { WoolTop = Vector3.new(0, 1, 0), WoolBack = Vector3.new(0, 0.1, 1), WoolChest = Vector3.new(0, 0.3, -1), WoolL = Vector3.new(-1, 0.1, 0), WoolR = Vector3.new(1, 0.1, 0) }

    function animateCloudSheep(rig, s, moving, fly, nova)
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
end
local animateJadeWyrmTurtle, dropToGround, turtleRay -- animateJadeWyrmTurtle's section below (its own locals stay in its block)
do

    -- The Jade Wyrm Turtle (skinned): half wyrm, half mountain, and in no hurry. Everything it does is slow and carries weight: it treads one foot at a time and the whole crag rocks over it, its long neck
    -- wanders on its own, the plum and the pine sway after the shell does. Now and then it turns its neck right round to look at its garden. It stands on the ground rather than hovering (Body drops to it).
    local TURTLE_LEADS = { FL = 0, BR = 0.35, FR = math.pi, BL = math.pi + 0.35 }
    local TURTLE_LID_HINGE = { L = Vector3.new(0.539, 0.0867, -0.8379), R = Vector3.new(0.539, -0.0867, 0.8379) }
    local TURTLE_BLINK_UPPER, TURTLE_BLINK_LOWER = math.rad(38), math.rad(16)
    local TURTLE_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local TURTLE_SOLE = 0.96 -- metres from the middle of its box down to the soles of its feet
    local TURTLE_PADS = { PadA = Vector3.new(-0.5, 0.2, -0.8), PadB = Vector3.new(0.6, 0.2, -0.3), PadC = Vector3.new(0, 1, 0.2) } -- which way each mass of blossom swells

    turtleRay = RaycastParams.new()
    turtleRay.RespectCanCollide = true

    function dropToGround(rig, s, t, u, fly, sole)
        local from = rig.rootPart.Position
        s.nextGround = s.nextGround or 0
        if t >= s.nextGround then
            s.nextGround = t + 0.15
            local hit = workspace:Raycast(from, Vector3.new(0, -8 * u, 0), turtleRay)
            local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
            if not onCharacter then -- (a player walking under it: keep what it had)
                s.groundAt = if hit then hit.Position.Y else nil
            end
        end
        -- The ground's height eases (a step, a slope, a ledge), but the root's own rise and fall (the follow bob) is taken out every frame:
        -- eased with the ground, the bob lagged and the pet floated up off its feet and back (seen in Studio, 2026-11-10).
        local dt = math.min(1, rig.deltaTime * 4)
        if s.groundAt then
            s.ground = if s.ground then s.ground + (s.groundAt - s.ground) * dt else s.groundAt
        end
        local wantGrounded = if s.groundAt then 1 else 0
        s.grounded = if s.grounded then s.grounded + (wantGrounded - s.grounded) * dt else wantGrounded
        local height = if s.ground then math.clamp(from.Y - sole * u - s.ground, -0.3 * u, 2.6 * u) else 0
        s.drop = height * s.grounded * (1 - fly)
        return s.drop
    end

    function animateJadeWyrmTurtle(rig, s, moving, fly, nova)
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
end
local animateNebulaOwl -- animateNebulaOwl's section below (its own locals stay in its block)
do

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

    function animateNebulaOwl(rig, s, moving, fly, nova)
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
end
local animateCosmicJellyfish, jellyBones -- animateCosmicJellyfish's section below (its own locals stay in its block)
do

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

    function jellyBones()
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

    function animateCosmicJellyfish(rig, s, moving, fly, nova)
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
end
local animateStarfallFox, FOX_STAR -- animateStarfallFox's section below (its own locals stay in its block)
do

    -- The Starfall Fox (skinned): sly and quick. Its head snaps from thing to thing and its pupils get there first; it stops to watch the sky; and when nothing is looking it digs a little with its forepaws, then checks over its shoulder that nobody saw.
    -- It stands and trots on the ground (`dropToGround`), and flying it stretches out in long bounds with its tail streaming behind it like a comet. Its eyelids are bands fixed all along the rim of the eye: they close by stretching, on a hinge along each eye's long axis (+ closes the upper).
    local FOX_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local FOX_LID_HINGE = { L = Vector3.new(-0.692, 0.3916, 0.6064), R = Vector3.new(-0.692, -0.3916, -0.6064) }
    local FOX_BLINK_UPPER, FOX_BLINK_LOWER = math.rad(9.8), math.rad(5)
    local FOX_LEADS = { FL = 0, BR = 0.35, FR = math.pi, BL = math.pi + 0.35 }
    local FOX_TAIL = { "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip" }
    local FOX_FALL_FROM, FOX_CATCH = 0.1, 0.42 -- of the special: the falling star shows, and reaches its teeth (PetRig.NOVA_BURST)
    FOX_STAR = "rbxassetid://95572555201628"
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

    function animateStarfallFox(rig, s, moving, fly, nova)
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
end
local animateLanternWarden, WARDEN_SOLE -- animateLanternWarden's section below (its own locals stay in its block)
do

    -- The Lantern Warden (skinned): it stoops along on two thin legs, in no hurry, with its lantern swinging on the chain and its cape following late. Its face is a mask and doesn't change: what changes is the angle of its head, held very still and then slowly tilted,
    -- and the pupils behind the slits, which slide about on their own (they turn on a pivot inside the mask, so they stay behind it) and blink by drawing back into the dark. When its light dims it turns and gives the lantern a tap.
    local WARDEN_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    WARDEN_SOLE = 1.145 -- metres from the middle of its box down to its toes: it walks on the ground, and leaves it only to fly
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

    function animateLanternWarden(rig, s, moving, fly, nova)
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
end
local animateDreamMoth, mothThreads -- animateDreamMoth's section below (its own locals stay in its block)
do

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
    function mothThreads(rig, s)
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

    function animateDreamMoth(rig, s, moving, fly, nova)
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
end
local animatePrismArmadillo -- animatePrismArmadillo's section below (its own locals stay in its block)
do

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

    function animatePrismArmadillo(rig, s, moving, fly, nova)
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
end
local animateCrystalSnail, SNAIL_SOLE -- animateCrystalSnail's section below (its own locals stay in its block)
do

    -- The Crystal Snail (skinned): it glides on a slow wave of its foot, stretching forward and gathering itself, and leaves a faint road of crystal glints where it has been. Its eyes are on stalks with no lids:
    -- like a real snail it blinks by drawing a stalk in (one at a time, in quickly, out slowly), and what it feels shows in how the stalks lean, wave and droop. Shy now and then, it draws both in and lets them out again bit by bit.
    local SNAIL_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    SNAIL_SOLE = 0.2606 -- metres from the middle of its box down to its sole: it glides on the ground
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

    function animateCrystalSnail(rig, s, moving, fly, nova)
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
end
local animateAbyssAnomalocaris, ANOMALO_GLOW, ANOMALO_RING -- animateAbyssAnomalocaris's section below (its own locals stay in its block)
do

    -- The Abyss Anomalocaris (skinned): a hunter from the first sea that still swims through the air. A wave runs back along its nine pairs of flaps, each a
    -- little behind the one before (the flaps are weighted by their place along the body, so where two overlap they move as one); its trunk undulates
    -- with it, its tail fan steers, and it banks into its turns. Its great arms rest curled under its head, tucking in at speed and now and then
    -- flexing open and shut as if tasting the water; its eyes swivel on their short stalks. Left is -X: a left flap rises with a negative turn about Z.
    local ANOMALO_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local ANOMALO_FLAPS = 9
    local ANOMALO_TRUNK = { "Seg4", "Seg5", "Seg6", "Seg7", "Seg8", "Seg9", "Tail" }
    ANOMALO_GLOW = Color3.fromRGB(190, 36, 146) -- deep: as Neon it blooms, and a paler magenta read as a bright pink fringe
    ANOMALO_RING = "rbxassetid://12403112662" -- a thin glowing ring with brighter arcs (also RealmAura's)

    function animateAbyssAnomalocaris(rig, s, moving, fly, nova)
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
end
local animateVoidscaleHydra, HYDRA_LIGHT -- animateVoidscaleHydra's section below (its own locals stay in its block)
do

    -- The Voidscale Hydra (skinned): a low sprawling reptile with three necks, the middle one forking into two young heads. It walks like a monitor
    -- lizard, legs swinging out in diagonal pairs, its body swaying side to side and its tail following the wave. Each neck sways on its own and each head
    -- chooses its own gaze; the tongues of light flick out, each in its own time; now and then the two young heads turn on each other and hiss.
    local HYDRA_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local HYDRA_SOLE = 0.2621 -- metres from the middle of its box down to its claws: it walks on the ground
    HYDRA_LIGHT = Color3.fromRGB(70, 150, 255)
    local HYDRA_HEADS = { -- each head's forward line in the model's axes, how far its tongue reaches (metres), its neck and the bones that carry it
        L = { dir = Vector3.new(-0.2067, -0.0316, -0.9779), reach = 0.084, neck = { "NeckL1", "NeckL2", "NeckL3", "NeckL4" }, phase = 0 },
        R = { dir = Vector3.new(0.1787, -0.0936, -0.9794), reach = 0.084, neck = { "NeckR1", "NeckR2", "NeckR3", "NeckR4" }, phase = 2.1 },
        ML = { dir = Vector3.new(-0.2186, -0.0094, -0.9758), reach = 0.0538, neck = { "ForkL1", "ForkL2" }, phase = 4.0 },
        MR = { dir = Vector3.new(0.1998, -0.1263, -0.9717), reach = 0.0538, neck = { "ForkR1", "ForkR2" }, phase = 5.3 },
    }
    local HYDRA_LEGS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi } -- diagonal pairs swing together

    function animateVoidscaleHydra(rig, s, moving, fly, nova)
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
end
local animateTheNamelessOne, NAMELESS_HALO, NAMELESS_SPARK -- animateTheNamelessOne's section below (its own locals stay in its block)
do

    -- The Nameless One (skinned): a tall figure with no legs, wound in pale ribbons round nothing, a hollow where its face should be with one point of light
    -- floating in it, a broken halo behind its head. It floats and bobs, its streamers and scarves drifting on a current only it feels; its hood tilts
    -- toward you as if it were trying to read you; now and then one arm lifts and the glowing ends of its ribbons write a loop in the air.
    local NAMELESS_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    NAMELESS_HALO = Color3.fromRGB(184, 156, 255)
    NAMELESS_SPARK = Color3.fromRGB(244, 240, 255)
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

    function animateTheNamelessOne(rig, s, moving, fly, nova)
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
end
local animateEclipseCat, CAT_CORONA, CAT_LEADS, CAT_SOLE, CAT_SUN -- animateEclipseCat's section below (its own locals stay in its block)
do

    -- The Eclipse Cat (skinned): a stylized black cat with a crescent tail, after the owner's concept sheet. It walks a cat's lateral walk with its tail
    -- held high; still for a few seconds, it sits, its tail lying behind it; its gaze wanders and now and then settles on you with a slow blink, the
    -- way a cat tells someone it trusts them; its ears swivel on their own, its tail sways and the tip flicks; gold and violet sparkles drift off it.
    local CAT_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    CAT_SOLE = 0.5573 -- metres from the middle of its box down to its paws: it walks on the ground
    local CAT_LID_HINGE = { L = Vector3.new(0.8802, -0.3085, -0.3606), R = Vector3.new(0.8802, 0.3085, 0.3606) } -- both lids of an eye turn on this line
    local CAT_BLINK_UPPER, CAT_BLINK_LOWER = math.rad(42), math.rad(18)
    CAT_LEADS = { BL = 0, FL = math.pi / 2, BR = math.pi, FR = 3 * math.pi / 2 } -- a lateral walk: a hind foot, then the fore on its side
    -- its sit, found by a search in Blender over these joints (paws flat on the ground, the seat down): the same numbers as eclipse_cat.py's SIT
    local CAT_SIT = { body = 0.38, drop = 0.045, back = 0.02, hips = 0.7, fore = -0.38, thigh = -0.4, shin = -1.1, hock = 0.42 }
    local CAT_SIT_TAIL = { { 0.5, 1.1 }, { 0.2, 0.7 }, { 0, 0.6 }, { -0.1, 0.5 }, { 0, 0.4 }, { 0, 0.3 } }
    CAT_SUN, CAT_CORONA = Color3.fromRGB(255, 210, 120), Color3.fromRGB(255, 244, 214)

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

    function animateEclipseCat(rig, s, moving, fly, nova)
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
end
local animateShadowcoil, SHADOW_BONES, SHADOW_EYESHINE, SHADOW_INK, SHADOW_RIM, SHADOW_SOLE, addStance, shadowDisc -- animateShadowcoil's section below (its own locals stay in its block)
do

    -- The Shadowcoil (skinned): a shadow stoat, ink black, with wisps of smoke along its back and a tail that coils like a curl of smoke. It bounds
    -- the way a stoat does, forepaws then hind paws, its back humping; still a moment, it rears up on its hind legs to look about; still a while
    -- longer, it lies down curled, its tail coiled behind it, and dozes; its glances are quick and sly, its eyes darting ahead of its head; a
    -- faint smoke drifts off its tail.
    local SHADOW_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    SHADOW_SOLE = 0.3253 -- metres from the middle of its box down to its paws: it runs on the ground
    local SHADOW_LID_HINGE = { L = Vector3.new(0.8851, -0.1728, -0.4322), R = Vector3.new(0.8851, 0.1728, 0.4322) } -- both lids of an eye turn on this line
    local SHADOW_BLINK_UPPER, SHADOW_BLINK_LOWER = math.rad(62), math.rad(22)
    local SHADOW_SINK = 0.7 -- metres it pours itself down into its shadow in the special: all of its height
    SHADOW_INK, SHADOW_RIM, SHADOW_EYESHINE = Color3.fromRGB(12, 7, 24), Color3.fromRGB(118, 92, 196), Color3.fromRGB(168, 255, 224)
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
    SHADOW_BONES = shadowBones()

    -- adds a stance (bone: { rx, ry, rz }), scaled by weight, into a table of wanted turns: a pet blends its poses by adding them
    function addStance(into, stance, weight)
        if weight <= 0 then
            return
        end
        for bone, a in stance do
            into[bone] = (into[bone] or Vector3.zero) + Vector3.new(a[1], a[2], a[3]) * weight
        end
    end

    -- a flat disc of shadow on the ground: a cylinder stood on its end; its top at `top` metres above the ground
    function shadowDisc(part, ground, top, thickness, width, metre)
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

    function animateShadowcoil(rig, s, moving, fly, nova)
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
end
local animatePearlDragon, PEARL_BONES, PEARL_GLOW, PEARL_SOLE, pearlAt, pearlGlow -- animatePearlDragon's section below (its own locals stay in its block)
do

    -- The Celestial Pearl Dragon (skinned): a fierce winged dragon of pearl-white nacre that holds its pearl to its chest in its right forefoot. Standing,
    -- it keeps its great wings raised behind it, breathing with it, and now and then flexes them and settles; its head moves slowly and deliberately, its
    -- stare holding on you; its tail sways. It never walks on three legs: to go anywhere it lifts off on heavy wingbeats and hovers low, its legs tucked,
    -- its tail streaming.
    local PEARL_FAR = 110 -- studs from the camera past which nobody can see it fidget: its bones rest
    PEARL_SOLE = 0.5741 -- metres from the middle of its box down to its feet: it stands on the ground
    local PEARL_LID_HINGE = { L = Vector3.new(0.7386, -0.308, -0.5997), R = Vector3.new(0.7386, 0.308, 0.5997) } -- both lids of an eye turn on this line
    local PEARL_BLINK_UPPER, PEARL_BLINK_LOWER = math.rad(40), math.rad(20)
    local PEARL_HOVER = 0.32 -- metres it hovers above the ground when it goes anywhere
    PEARL_GLOW = Color3.fromRGB(255, 230, 214)

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
    PEARL_BONES = pearlBones() -- every bone its stances pose (the lids turn on their hinges on their own)

    -- where the pearl is now: the hand's bone carries it, at the offset it had at rest
    function pearlAt(rig, s)
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
    function pearlGlow(rig, s)
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

    function animatePearlDragon(rig, s, moving, fly, nova)
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
end
local animateSnowLeopard, LEOPARD_BONES, LEOPARD_ICE, LEOPARD_SOLE, LEOPARD_STAR -- animateSnowLeopard's section below (its own locals stay in its block)
do

    -- The Celestial Snow Leopard (skinned): a grown snow leopard, a hunter of the high snow. It prowls low, head level and forward, its shoulder blades
    -- rolling, its huge tail held low behind it, the tip lifting in a curl; now and then it stops, sinks into a stalking crouch and stares, its haunches
    -- wiggling; still a while, it lies down sphinx-like, its tail curled round beside it. Its stare is steady and intense; its ears turn on their own; its
    -- tail tip twitches. In the air it stretches out in a long leap.
    local LEOPARD_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    LEOPARD_SOLE = 0.297 -- metres from the middle of its box down to its paws: it walks on the ground
    local LEOPARD_LID_HINGE = { L = Vector3.new(0.939, -0.1562, -0.3064), R = Vector3.new(0.939, 0.1562, 0.3064) } -- both lids of an eye turn on this line
    local LEOPARD_BLINK_UPPER, LEOPARD_BLINK_LOWER = math.rad(52), math.rad(24)
    LEOPARD_ICE, LEOPARD_STAR = Color3.fromRGB(196, 232, 255), Color3.fromRGB(140, 200, 255)
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
    LEOPARD_BONES = leopardBones() -- every bone its stances pose (the lids turn on their hinges on their own)

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

    function animateSnowLeopard(rig, s, moving, fly, nova)
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
end
local animateCometStag, STAG_BONES, STAG_DUST, STAG_ICE, STAG_ION, stagGlow -- animateCometStag's section below (its own locals stay in its block)
do

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
    STAG_ICE, STAG_ION, STAG_DUST = Color3.fromRGB(234, 246, 255), Color3.fromRGB(110, 190, 255), Color3.fromRGB(255, 214, 140)
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
    STAG_BONES = stagBones() -- every bone its stances pose (the lids turn on their hinges on their own)

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
    function stagGlow(rig, s)
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

    function animateCometStag(rig, s, moving, fly, nova)
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
end
local animateSandPhantom, SAND_AWAY, SAND_BONES, SAND_DUSK, SAND_GOLD, SAND_PALE, SAND_SOLE -- animateSandPhantom's section below (its own locals stay in its block)
do

    -- The Sand Phantom (skinned): a desert jerboa spirit. It hops on its long hind legs, both feet together, its long tail held out behind it for balance;
    -- still, it sits up tall to look about, freezes when something catches its eye, or washes its face with its tiny forepaws. Its gaze darts, quick and
    -- shy; its huge ears turn on their own; fine sand streams off its tail's brush and its ears as if blown by a wind only it feels.
    local SAND_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    SAND_SOLE = 0.2988 -- metres from the middle of its box down to its feet: it sits on the ground
    local SAND_LID_HINGE = { L = Vector3.new(0.765, -0.0686, -0.6403), R = Vector3.new(0.765, 0.0686, 0.6403) } -- both lids of an eye turn on this line
    local SAND_BLINK_UPPER, SAND_BLINK_LOWER = math.rad(62), math.rad(28)
    SAND_GOLD, SAND_PALE, SAND_DUSK = Color3.fromRGB(226, 182, 110), Color3.fromRGB(246, 226, 180), Color3.fromRGB(176, 124, 70)
    local SAND_HOP = 0.16 -- metres it rises at the top of a hop
    SAND_AWAY = 0.8 -- metres to its right it re-forms in its special: clear of where it stood, and still in a following camera's view

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
    SAND_BONES = sandBones() -- every bone its stances pose (the lids turn on their hinges on their own)

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

    function animateSandPhantom(rig, s, moving, fly, nova)
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
end
local animateSolarButterfly, BFLY_DUSK, BFLY_GOLD, BFLY_ROSE -- animateSolarButterfly's section below (its own locals stay in its block)
do

    -- The Solar Butterfly (skinned): a swallowtail of sunset glass. It flies in slow, deep wingbeats with glides between, bobbing as butterflies do; still
    -- a few seconds, it drifts down and lands on its legs to bask, wings spread flat to the sun, now and then closing them up over its back and opening them
    -- again; its antennae sway and twitch; warm motes of stored sunlight drift off its eyespots, more after dark.
    local BFLY_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local BFLY_LEGS = 0.0737 -- metres from its Body bone down to the tips of its legs (solar_butterfly.py): where it stands when it lands. Measured from the
    -- bone, not the box: the importer's root part sits at the model's origin, under a pet that floats, so the box's middle is not where it seems
    BFLY_GOLD, BFLY_ROSE, BFLY_DUSK = Color3.fromRGB(255, 196, 80), Color3.fromRGB(255, 110, 90), Color3.fromRGB(150, 80, 200)
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

    function animateSolarButterfly(rig, s, moving, fly, nova)
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
end
local animateTimekeeperTortoise, TORT -- animateTimekeeperTortoise's section below (its own locals stay in its block)
do

    -- The Timekeeper Tortoise (skinned): an ancient giant tortoise whose shell is a sundial. It walks impossibly slowly, a deliberate diagonal step, and yet
    -- is never left behind; standing, it turns its old head slowly to look about or at you, its long white brows lifting when it does, blinks slow heavy
    -- blinks and chews on nothing; its tail sways. When its owner flies it pulls itself into its shell and drifts beside them like a stone.
    TORT = {
        FAR = 100, -- studs from the camera past which nobody can see it fidget: its bones rest
        BODY_SOLE = 0.36, -- metres from its Body bone down to the soles of its feet (timekeeper_tortoise.py): it stands on the ground
        LID_HINGE = { L = Vector3.new(0.5402, 0.1012, -0.8354), R = Vector3.new(0.5402, -0.1012, 0.8354) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(40),
        BLINK_LOWER = math.rad(16),
        GOLD = Color3.fromRGB(255, 207, 110),
        SEPIA = Color3.fromRGB(255, 236, 200),
        -- its walk, checked in Blender at eight points of its cycle: diagonal pairs; each leg swings at its shoulder, its knee lifting the foot (front legs one
        -- way, hind legs the other), the shoulder raised or lowered by the arc its swing would trace, so a planted foot stays on the ground
        LEADS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi },
        ARC = { F = { 0.0196, 0.0041 }, B = { -0.01745, 0.00385 } }, -- a foot's height through its swing's arc: a * sw + b * sw^2 (metres, at full swing)
        SWING = 0.22,
        LIFT = 0.6,
        -- pulled into its shell (checked in Blender: its face peeks out of the front opening between its folded forelegs; nothing pokes through the dome)
        TUCK = {
            Neck1 = { -0.3, 0, 0 }, Neck2 = { 0.3, 0, 0 }, Head = { 0.1, 0, 0 },
            LegFL2 = { 0.9, 0, 0 }, LegFR2 = { 0.9, 0, 0 }, LegBL2 = { -0.9, 0, 0 }, LegBR2 = { -0.9, 0, 0 },
        },
        TUCK_MOVE = { -- metres, the game's axes
            Neck1 = Vector3.new(0, -0.08, 0.22),
            LegFL1 = Vector3.new(0.05, 0.1, 0.03), LegFR1 = Vector3.new(-0.05, 0.1, 0.03), LegBL1 = Vector3.new(0.05, 0.1, -0.03), LegBR1 = Vector3.new(-0.05, 0.1, -0.03), -- (a left leg moves in along +X)
        },
        -- the special's stance: planted, its head raised and its brows up, proud
        PLANT = { Neck1 = { 0.12, 0, 0 }, Neck2 = { 0.12, 0, 0 }, Head = { 0.18, 0, 0 }, BrowL = { -0.25, 0, 0 }, BrowR = { -0.25, 0, 0 } },
        BONES = {
            "Body", "Neck1", "Neck2", "Head", "Jaw", "BrowL", "BrowR", "Tail",
            "LegFL1", "LegFL2", "FootFL", "LegFR1", "LegFR2", "FootFR", "LegBL1", "LegBL2", "FootBL", "LegBR1", "LegBR2", "FootBR",
        },
    }

    function animateTimekeeperTortoise(rig, s, moving, fly, nova)
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > TORT.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

        -- the special, Stopped Hour: it plants itself and raises its head (to 0.42; Blasts.StoppedHour), and for a heartbeat time stops: it does not move
        -- at all, not a blink; then time starts again and it settles
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local plant = smoothstep(0.03, 0.3, progress) * (1 - smoothstep(0.78, 0.98, progress))
        local stopped = if progress > 0.42 and progress < 0.72 then 1 else 0
        s.clock = (s.clock or 0) + dt * (1 - stopped) -- its own time, which stops with the world's
        local tt = s.clock

        local hips = rig.points.Body
        if hips and not s.sole then
            s.sole = rig.rootPart.CFrame:PointToObjectSpace(hips.WorldPosition).Y * -1 / u + TORT.BODY_SOLE -- (WorldPosition leaves out its own Transform)
        end
        local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.5)
        local tuck = smoothstep(0, 1, fly) * (1 - plant)

        -- the walk: slow and deliberate however fast its owner goes, and yet it keeps up
        local step = moving * (1 - tuck) * (1 - plant)
        s.step = (s.step or 0) + dt * (2.2 + 1.3 * moving) * step * (1 - stopped)
        local want, moves = {}, {}
        for key, lead in TORT.LEADS do
            local sw = math.sin(s.step + lead) * step
            local lf = math.max(0, math.cos(s.step + lead)) * step
            local a1 = TORT.SWING * sw
            local a2 = (if string.sub(key, 1, 1) == "F" then 1 else -1) * TORT.LIFT * lf
            local arc = TORT.ARC[string.sub(key, 1, 1)]
            want["Leg" .. key .. "1"] = Vector3.new(a1, 0, 0)
            want["Leg" .. key .. "2"] = Vector3.new(a2, 0, 0)
            want["Foot" .. key] = Vector3.new(-(a1 + a2), 0, 0)
            moves["Leg" .. key .. "1"] = Vector3.new(0, -(arc[1] * sw + arc[2] * sw * sw), 0)
        end

        -- looking about: slowly, as an old one does; most often at you; its brows lift when it looks at you
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 4 + math.random() * 5
            s.atYou = math.random() < 0.55
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - tuck) * (1 - 0.6 * step)
        local wantYaw = (if s.atYou or plant > 0 then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.25) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 1.2) * (1 - stopped)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 1.2) * (1 - stopped)
        local yawShare = math.clamp(s.yaw / 0.8, -1, 1) -- (as far as Blender checked: neck 0.35, head 0.45)
        local brow = (if s.atYou then 1 else 0) * calm
        s.brow = (s.brow or 0) + (brow - (s.brow or 0)) * math.min(1, dt * 2) * (1 - stopped)
        local bob = 0.04 * math.sin(s.step * 2) * step
        want.Neck1 = Vector3.new(0.02 * math.sin(tt * 0.5), 0, 0)
        want.Neck2 = Vector3.new(0.4 * s.pitch + bob, 0.35 * yawShare, 0)
        want.Head = Vector3.new(0.6 * s.pitch - bob * 0.5, 0.45 * yawShare, 0.1 * yawShare)
        want.BrowL = Vector3.new(-0.22 * s.brow + 0.03 * math.sin(tt * 0.8), 0, 0)
        want.BrowR = Vector3.new(-0.22 * s.brow + 0.03 * math.sin(tt * 0.8 + 1), 0, 0)

        -- it chews on nothing now and then
        s.nextChew = s.nextChew or t + 5
        if t >= s.nextChew then
            s.chewAt = tt
            s.nextChew = t + 6 + math.random() * 6
        end
        local chewEnv = if s.chewAt then (tt - s.chewAt) / 1.8 else 1
        local chew = if chewEnv < 1 then (0.5 - 0.5 * math.cos(chewEnv * 6 * math.pi)) * math.sin(math.pi * chewEnv) else 0
        want.Jaw = Vector3.new(-0.12 * chew * (1 - tuck), 0, 0)
        want.Tail = Vector3.new(0, 0.25 * math.sin(tt * 0.6) + 0.15 * math.sin(s.step) * step, 0)

        -- the special's stance, and the tuck
        for name, a in TORT.PLANT do
            want[name] = (want[name] or Vector3.zero) * (1 - plant) + Vector3.new(a[1], a[2], a[3]) * plant
        end
        for _, name in TORT.BONES do
            local a = TORT.TUCK[name]
            local target = if a then Vector3.new(a[1], a[2], a[3]) else Vector3.zero
            if string.sub(name, 1, 4) == "Foot" or name == "Jaw" or string.sub(name, 1, 4) == "Brow" or name == "Tail" or name == "Body" then
                target = want[name] or Vector3.zero -- (these keep their own turns when it tucks)
            end
            want[name] = (want[name] or Vector3.zero) * (1 - tuck) + target * tuck
            moves[name] = (moves[name] or Vector3.zero) * (1 - tuck) + (TORT.TUCK_MOVE[name] or Vector3.zero) * tuck
        end

        -- its body: a slow roll with its step; tucked and drifting, a slow tilt; it stands on the ground, or keeps to its owner's height when they fly
        local sway = 0.025 * math.sin(s.step) * step
        local drift = Vector3.new(0.05 * math.sin(tt * 0.7), 0, 0.04 * math.sin(tt * 0.5)) * tuck
        local lift = -drop + 0.004 * math.abs(math.sin(2 * s.step)) * step * u
        pose(m.Body, CFrame.new(0, lift, 0) * CFrame.Angles(drift.X, 0, sway + drift.Z))
        for _, name in TORT.BONES do
            if name ~= "Body" then
                local a = want[name] or Vector3.zero
                local mv = moves[name] or Vector3.zero
                pose(m[name], CFrame.new(mv * u) * CFrame.Angles(a.X, a.Y, a.Z))
            end
        end

        -- the lids: a slow, heavy blink now and then; none while time stands still
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink and stopped == 0 then
            local a = (t - s.nextBlink) / 0.6
            if a >= 1 then
                s.nextBlink = t + 4 + math.random() * 5
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local shut = math.max(blink, 0.85 * tuck)
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(TORT.LID_HINGE[side], -TORT.BLINK_UPPER * shut))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(TORT.LID_HINGE[side], TORT.BLINK_LOWER * shut))
        end
    end
end
local animateGravityImp, IMP -- animateGravityImp's section below (its own locals stay in its block)
do

    -- The Gravity Imp (skinned): a small, smug violet imp who lives on a moonlet of its own, and whichever way its feet are on it is down. It stands on top
    -- with its fists on its hips, watching you, one brow up; now and then it chuckles to itself, an ear flicks, its spade of a tail sways. Now and then it
    -- strolls forward over the front and down under its moonlet (the moonlet rising so it hangs clear of the ground), turns round to face you and hangs there
    -- upside down, smirking, then carries on over the back to the top. When its owner goes anywhere it treads its moonlet round under it like a treadmill;
    -- when they fly it sits on top, leaning back on its hands. Three pebbles circle the moonlet round its own middle.
    IMP = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        CORE_SOLE = 0.1497, -- metres from its Core bone (the moonlet's middle) down to its lowest point, standing on top (gravity_imp.py)
        -- metres from the Core down to its lowest point as it stands further round its moonlet, every 15 degrees from the top to underneath (measured in Blender)
        UNDER = { 0.1497, 0.1497, 0.1582, 0.2136, 0.256, 0.2838, 0.2923, 0.2831, 0.2942, 0.3832, 0.4584, 0.5044, 0.5168 },
        HOVER = 0.2, -- metres its moonlet hangs above the ground; a little lower as it treads along
        WALK_HOVER = 0.12,
        RADIUS = 0.15, -- the moonlet's, in metres
        STROLL = 1.1, -- radians a second it walks round its moonlet
        LID_HINGE = { L = Vector3.new(0.9395, -0.1562, -0.3049), R = Vector3.new(0.9395, 0.1562, 0.3049) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(40),
        BLINK_LOWER = math.rad(10),
        VIOLET = Color3.fromRGB(210, 140, 255),
        DEEP = Color3.fromRGB(110, 60, 190),
        STONE = Color3.fromRGB(112, 102, 90), -- the ground's own stones, earth-grey (a violet-grey read as lilac cubes under its light: seen in Play)
        DUST = Color3.fromRGB(176, 164, 140),
        -- its walk on top, as on a treadmill (searched in Blender: planted soles within 1.4 mm of resting on the moonlet): legs swing at the hips, a knee lifts
        -- a foot, a planted foot turns twice its leg's swing to lie along the moonlet's curve, the hips dip 4 mm as both feet are down
        SWING = 0.36,
        LIFT = 0.75,
        TILT = 2.0,
        DIP = 0.004,
        -- stances, each checked in Blender (gravity_imp.py's POSES) and along the slerp from one to another: turns x, y, z; then a move in metres, the game's axes
        AKIMBO = { -- fists on its hips, elbows out
            ArmL1 = { -0.0938, 0.0388, -0.4486 }, ArmL2 = { 0.0559, -0.1789, 1.2647 }, HandL = { -0.3102, 0.376, -0.8454 },
            ArmR1 = { -0.0938, -0.0388, 0.4486 }, ArmR2 = { 0.0559, 0.1789, -1.2647 }, HandR = { -0.3102, -0.376, 0.8454 },
        },
        SIT = { -- sat on top, legs out round its belly, leaning back on its hands: how it rides when its owner flies
            Hips = { 0.22, 0, 0, 0, -0.07, 0.01 },
            ArmL1 = { -0.4136, 0.1613, 0.1756 }, ArmL2 = { 0.0204, -0.0115, 0.0343 }, HandL = { 0.8306, 1.2185, -1.6622 },
            ArmR1 = { -0.4136, -0.1613, -0.1756 }, ArmR2 = { 0.0204, 0.0115, -0.0343 }, HandR = { 0.8306, -1.2185, 1.6622 },
            LegL1 = { 1.35, 0, -0.35 }, LegL2 = { -0.1, 0, 0 }, FootL = { -1.7, 0, 0 },
            LegR1 = { 1.35, 0, 0.35 }, LegR2 = { -0.1, 0, 0 }, FootR = { -1.7, 0, 0 },
        },
        STOMP = { -- its special: a sumo's stamp, its right leg out to its side (a knee forward would meet its belly), its weight on its left
            Hips = { 0, 0, -0.06, 0, -0.002, 0 },
            LegR1 = { 0.1, 0, 1.25 }, LegR2 = { 0, 0, -1.25 }, FootR = { 0, 0, 0.16 }, LegL1 = { 0, 0, 0.06 }, FootL = { 0, 0, -0.06 },
        },
        BALANCE = { -- its arms out for balance as it stamps, elbows bent up
            ArmL1 = { 0, 0, -0.85 }, ArmL2 = { 0, 0, -0.55 }, HandL = { 0, 0, -0.25 },
            ArmR1 = { 0, 0, 0.85 }, ArmR2 = { 0, 0, 0.55 }, HandR = { 0, 0, 0.25 },
        },
        LEGS = { LegL1 = true, LegL2 = true, FootL = true, LegR1 = true, LegR2 = true, FootR = true },
        -- the pebbles' orbits round the imp's own middle (each tilted about the line to where it rests, so it rests on it), and how fast each goes round
        ORBITS = {
            { Vector3.new(-0.1388, 0.9703, -0.1982), 0.9 },
            { Vector3.new(0.117, 0.9397, -0.3214), -0.7 },
            { Vector3.new(0.1511, 0.9877, 0.0405), 1.25 },
        },
        BONES = {
            "Hips", "Chest", "Head", "EarL", "EarR", "BrowL", "BrowR",
            "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR", "LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR",
            "Tail1", "Tail2", "Tail3", "Tail4",
        },
    }

    -- a stance's turn (and move) as a CFrame
    function IMP.cf(a, u)
        local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
        return move * CFrame.Angles(a[1], a[2], a[3])
    end

    -- how far below its moonlet's middle it reaches, standing this far round it (0 on top, pi underneath)
    function IMP.under(a)
        local f = a % (2 * math.pi)
        if f > math.pi then
            f = 2 * math.pi - f
        end
        local k = f / (math.pi / 12)
        local i = math.min(math.floor(k), #IMP.UNDER - 2)
        return IMP.UNDER[i + 1] + (IMP.UNDER[i + 2] - IMP.UNDER[i + 1]) * (k - i)
    end

    function animateGravityImp(rig, s, moving, fly, nova)
        if not s.lightMade then
            -- its glow follows its moonlet: hung on the Core bone (a skinned part stays where it was bound, so a light on the veins stayed behind when it rose)
            s.lightMade = true
            local core = rig.points.Core
            if core then
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = IMP.VIOLET
                light.Range = 5 * rig.unit
                light.Brightness = 1.2
                light.Shadows = false
                light.Parent = core
                rig.light = light
            end
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > IMP.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

        -- the special, Which Way Is Down: it stands (if it sat), lifts its right foot out to its side, arms out, and stamps on its moonlet at 0.42
        -- (Blasts.WhichWayIsDown); the moonlet jolts, its ears flap, the pebbles whirl; then fists back on its hips
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local active = if rig.nova then 1 else 0
        s.sit = (s.sit or 0) + (fly * (1 - active) - (s.sit or 0)) * math.min(1, dt * 3)
        local standing = 1 - smoothstep(0, 0.35, s.sit) -- (it stands before it stamps: the seat to the stamp was never checked)
        local up = smoothstep(0.06, 0.3, progress) * (1 - smoothstep(0.405, 0.425, progress)) * standing
        local balance = smoothstep(0.04, 0.2, progress) * (1 - smoothstep(0.46, 0.62, progress)) * standing
        local impact = if progress > 0.42 then math.exp(-(progress - 0.42) * 12) else 0
        local whirl = smoothstep(0.42, 0.5, progress) * (1 - smoothstep(0.7, 0.95, progress))

        -- how fast it is going, in metres a second (its root follows its owner)
        local here = rig.rootPart.Position
        local travel = if s.lastPos and dt > 0 then Vector3.new(here.X - s.lastPos.X, 0, here.Z - s.lastPos.Z).Magnitude / dt / u else 0
        s.lastPos = here
        s.speed = (s.speed or 0) + (math.min(travel, 4) - (s.speed or 0)) * math.min(1, dt * 4)

        -- strolling round its moonlet: over the front and down, turn to face you, hang a while, turn back, on over the back to the top. Anything else
        -- happening (its owner moving or flying, the special) and it hurries home to the top the short way
        s.mode = s.mode or "top"
        s.a = s.a or 0
        s.turn = s.turn or 0
        s.nextStroll = s.nextStroll or t + 10 + math.random() * 8
        local idle = moving < 0.1 and fly < 0.1 and active == 0
        local strolling = 0
        if s.mode == "top" then
            if idle and t >= s.nextStroll then
                s.mode = "down"
            end
        elseif not idle then
            s.mode = "home"
        end
        if s.mode == "down" then
            s.a = math.min(math.pi, s.a + dt * IMP.STROLL)
            strolling = 1
            if s.a >= math.pi then
                s.mode = "turn"
            end
        elseif s.mode == "turn" then
            s.turn = math.min(math.pi, s.turn + dt * 4.5)
            if s.turn >= math.pi then
                s.mode = "hang"
                s.hangUntil = t + 5 + math.random() * 4
            end
        elseif s.mode == "hang" then
            if t >= (s.hangUntil or 0) then
                s.mode = "unturn"
            end
        elseif s.mode == "unturn" then
            s.turn = math.max(0, s.turn - dt * 4.5)
            if s.turn <= 0 then
                s.mode = "up"
            end
        elseif s.mode == "up" then
            s.a = math.min(2 * math.pi, s.a + dt * IMP.STROLL)
            strolling = 1
            if s.a >= 2 * math.pi then
                s.a = 0
                s.mode = "top"
                s.nextStroll = t + 18 + math.random() * 14 -- (a lap takes 12 to 16 s: at 12 to 22 s between, it was off the top nearly half the time)
            end
        elseif s.mode == "home" then
            s.turn = math.max(0, s.turn - dt * 6)
            local home = if s.a > math.pi then 2 * math.pi else 0
            local stride = dt * 3
            if math.abs(home - s.a) <= stride then
                s.a = 0
                s.mode = "top"
                s.nextStroll = t + 10 + math.random() * 8
            else
                s.a += if home > s.a then stride else -stride
                strolling = 1
            end
        end
        local walking = moving * (1 - fly)
        local lean = 0.16 * walking * (1 - strolling) -- treading along, it stands a little forward of the top, as on a ball
        local onTop = 1 - smoothstep(0.2, 0.9, math.min(s.a, 2 * math.pi - s.a)) -- (the special caught it underneath: it stamps once it is back on top)
        up *= onTop
        balance *= onTop
        local pivot = CFrame.Angles(-(s.a + lean), 0, 0) * CFrame.Angles(0, s.turn, 0)
        pose(m.Pivot, pivot)

        -- its moonlet: hanging above the ground (higher as it goes round, so it hangs clear underneath), bobbing; turning under its feet as it treads
        -- along; a jolt when it stamps; tilting into its owner's turns
        local core = rig.points.Core
        if core and not s.sole then
            s.sole = rig.rootPart.CFrame:PointToObjectSpace(core.WorldPosition).Y * -1 / u + IMP.CORE_SOLE -- (WorldPosition leaves out its own Transform)
        end
        local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.2)
        local hover = (IMP.HOVER * (1 - walking) + IMP.WALK_HOVER * walking) * (1 - fly)
        local bob = 0.012 * math.sin(t * 1.4) + 0.004 * math.sin(t * 3.1 + 1)
        local jolt = -0.03 * impact * math.cos(math.max(0, progress - 0.42) * 45)
        local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
        local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
        s.heading = heading
        s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.25, 0.25) - (s.bank or 0)) * math.min(1, dt * 3)
        local lift = (hover + IMP.under(s.a) - IMP.UNDER[1] + bob + jolt) * u - drop
        pose(m.Core, CFrame.new(0, lift, 0) * CFrame.Angles(0, 0, s.bank))
        s.spin = (s.spin or 0) + dt * (math.min(s.speed / IMP.RADIUS, 9) * walking * (1 - strolling) + 0.25 * fly)
        pose(m.Planet, CFrame.Angles(s.spin, 0, 0))

        -- its legs: stepping as it treads along or strolls round
        local stepping = math.max(walking * (1 - strolling), strolling) * (1 - s.sit) * (1 - up)
        s.step = (s.step or 0) + dt * math.min(5 + 9 * math.max(s.speed, strolling * 0.6), 14) * stepping
        local cfs = {}
        for _, name in IMP.BONES do
            cfs[name] = CFrame.identity
        end
        for tag, lead in { L = 0, R = math.pi } do
            local sw = math.sin(s.step + lead) * stepping
            local lf = math.max(0, math.cos(s.step + lead)) * stepping
            cfs["Leg" .. tag .. "1"] = CFrame.Angles(IMP.SWING * sw, 0, 0)
            cfs["Leg" .. tag .. "2"] = CFrame.Angles(-IMP.LIFT * lf, 0, 0)
            cfs["Foot" .. tag] = CFrame.Angles(-IMP.TILT * IMP.SWING * sw + IMP.LIFT * lf * 0.6, 0, 0)
            cfs["Arm" .. tag .. "1"] = CFrame.Angles(-0.3 * sw, 0, 0)
        end

        -- where it looks: at you, mostly, smugly, or about; its head turns in its own frame, whichever way up it is
        local toYou = (rig.rootPart.CFrame * pivot):VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.5 + math.random() * 3.5
            s.atYou = math.random() < 0.6
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.1, (math.random() - 0.5) * 0.3
        end
        local wantYaw = if s.atYou or active == 1 then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw
        local wantPitch = if s.atYou or active == 1 then math.clamp(toYou.Y * 0.5, -0.28, 0.3) else s.gazePitch
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 4)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 4)
        local smug = if s.atYou or active == 1 then 1 else 0
        s.smug = (s.smug or 0) + (smug - (s.smug or 0)) * math.min(1, dt * 3)

        -- now and then a chuckle to itself: its shoulders bounce, its head tips back
        s.nextChuckle = s.nextChuckle or t + 6
        if t >= s.nextChuckle then
            s.chuckleAt = t
            s.nextChuckle = t + 7 + math.random() * 7
        end
        local ch = if s.chuckleAt then (t - s.chuckleAt) / 0.9 else 1
        local chuckle = if ch < 1 then math.sin(math.pi * ch) else 0
        cfs.Chest = CFrame.new(0, 0.002 * u * math.abs(math.sin(ch * math.pi * 6)) * chuckle, 0) * CFrame.Angles(0.04 * chuckle, 0, 0)
        cfs.Head = CFrame.Angles(math.clamp(s.pitch + 0.1 * chuckle, -0.28, 0.3), s.yaw, 0.12 * s.smug * (1 - math.abs(s.yaw) / 0.7) + 0.04 * math.sin(t * 0.7))
        cfs.BrowL = CFrame.new(0, (0.0045 * s.smug + 0.002 * up) * u, 0)
        cfs.BrowR = CFrame.new(0, (-0.0015 * s.smug + 0.002 * up) * u, 0)

        -- its ears: a little droop, a flick now and then, a bounce as it walks, perked as it winds up to stamp and flapping when it does, drooped as it
        -- sits back (within what Blender checked: droop -0.3 to 0.45, swing -0.3 to 0.3)
        s.nextFlick = s.nextFlick or t + 2
        if t >= s.nextFlick then
            s.flickAt, s.flickEar = t, if math.random() < 0.5 then "L" else "R"
            s.nextFlick = t + 2 + math.random() * 4
        end
        local fl = if s.flickAt then (t - s.flickAt) / 0.35 else 1
        local flick = if fl < 1 then math.sin(math.pi * fl) else 0
        for tag, sign in { L = 1, R = -1 } do
            local droop = 0.06 + 0.07 * math.sin(2 * s.step) * stepping + 0.15 * s.sit - 0.3 * up + 0.4 * impact
            local swing = (if s.flickEar == tag then 0.28 * flick else 0) + 0.04 * math.sin(t * 1.1 + sign)
            droop = math.clamp(droop, -0.3, 0.45)
            cfs["Ear" .. tag] = CFrame.Angles(0, sign * math.clamp(swing, -0.3, 0.3), sign * droop)
        end

        -- its tail: a lazy sway down its length, its spade flicking now and then (within what Blender checked: sway 0.45, rise -0.15 to 0.25)
        local spade = flick * 0.25
        for k = 1, 4 do
            local sway = 0.22 * math.sin(t * 1.5 - 0.6 * k) + 0.12 * math.sin(s.step) * stepping + (if k == 4 then spade else 0)
            local rise = 0.06 + 0.08 * math.sin(t * 0.8 - 0.5 * k)
            cfs["Tail" .. k] = CFrame.Angles(math.clamp(rise, -0.15, 0.25), math.clamp(sway, -0.45, 0.45), 0)
        end

        -- the stances over all that, each a slerp (CFrame:Lerp) as Blender checked them: fists on its hips unless it treads along; the seat when its
        -- owner flies (its legs swing out ahead, its hips lower after: straight, its feet swept through its moonlet); the stamp
        local akimbo = 1 - walking * (1 - strolling)
        local hips = smoothstep(0.4, 1, s.sit)
        local legs = math.min(1, s.sit / 0.5)
        cfs.Hips = CFrame.new(0, -IMP.DIP * math.sin(s.step) ^ 2 * stepping * u, 0)
        for _, name in IMP.BONES do
            local cf = cfs[name]
            local a = IMP.AKIMBO[name]
            if a then
                cf = cf:Lerp(IMP.cf(a, u), akimbo)
            end
            a = IMP.SIT[name]
            if a then
                cf = cf:Lerp(IMP.cf(a, u), if IMP.LEGS[name] then legs elseif name == "Hips" then hips else s.sit)
            end
            a = IMP.STOMP[name]
            if a then
                cf = cf:Lerp(IMP.cf(a, u), up)
            end
            a = IMP.BALANCE[name]
            if a then
                cf = cf:Lerp(IMP.cf(a, u), balance)
            end
            pose(m[name], cf)
        end

        -- the pebbles round their orbits, whirling after the stamp
        s.orbit = s.orbit or { 0, 2.1, 4.2 }
        for k, orbit in IMP.ORBITS do
            s.orbit[k] += dt * orbit[2] * (1 + 4 * whirl)
            pose(m["Pebble" .. k], CFrame.fromAxisAngle(orbit[1], s.orbit[k]))
        end

        -- the lids: a quick blink now and then; heavy-lidded the rest of the time (as it was made)
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local b = (t - s.nextBlink) / 0.18
            if b >= 1 then
                s.nextBlink = t + 2.5 + math.random() * 3
            else
                blink = 1 - math.abs(2 * b - 1)
            end
        end
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(IMP.LID_HINGE[side], -IMP.BLINK_UPPER * blink))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(IMP.LID_HINGE[side], IMP.BLINK_LOWER * blink))
        end
    end
end
local animateGlacierPuff, PUFF_FROST, PUFF_ICE -- animateGlacierPuff's section below (its own locals stay in its block)
do

    -- The Glacier Puff (skinned): a little pufferfish of glacier ice that swims through the air. It hangs half a metre up, its pectoral fins whirring, its
    -- tail sculling, its body wagging as a fish's does; its eyes wander, each its own way, and now and then both fix on you; every few seconds it gulps, and
    -- a few bubbles of frost rise from its mouth. Now and then something startles it and it half puffs, a few spines of hoarfrost pricking out of its ice,
    -- and settles again. It swims faster, nose down, when its owner goes somewhere.
    local PUFF_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local PUFF_ZONES = 8
    local PUFF_T, PUFF_S = 0.06, 0.054 -- metres each puff bone moves out at full puff, and how much further its spines slide out of the ice (glacier_puff.py)
    local PUFF_BODY_SOLE = 0.153 -- metres from its Body bone down to its lowest point (glacier_puff.py)
    local PUFF_HOVER = 0.45 -- metres above the ground it swims
    PUFF_FROST, PUFF_ICE = Color3.fromRGB(226, 244, 255), Color3.fromRGB(150, 210, 250)
    local PUFF_DIRS = {} -- each puff bone's way out, in the game's axes: round its length, 1 its left, then up, its right, down
    for k = 1, PUFF_ZONES do
        local a = 2 * math.pi * (k - 1) / PUFF_ZONES
        PUFF_DIRS[k] = Vector3.new(-math.cos(a), math.sin(a), 0)
    end

    -- frost bubbles from its mouth when it gulps
    local function puffBubbles(rig, s)
        s.bubblesMade = true
        local jaw = rig.points.Jaw
        if not jaw then
            return
        end
        local bubbles = Instance.new("ParticleEmitter")
        bubbles.Name = "FrostBubbles"
        bubbles.Texture = "rbxasset://textures/particles/explosion01_implosion_main.dds"
        bubbles.Enabled = false
        bubbles.Lifetime = NumberRange.new(0.8, 1.4)
        bubbles.Speed = NumberRange.new(0.15 * rig.unit, 0.35 * rig.unit)
        bubbles.SpreadAngle = Vector2.new(25, 25)
        bubbles.EmissionDirection = Enum.NormalId.Front
        bubbles.Acceleration = Vector3.new(0, 0.35 * rig.unit, 0)
        bubbles.Drag = 1.5
        bubbles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.025 * rig.unit), NumberSequenceKeypoint.new(0.5, 0.045 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
        bubbles.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
        bubbles.Color = ColorSequence.new(PUFF_FROST, PUFF_ICE)
        bubbles.LightEmission = 0.4
        bubbles.LightInfluence = 0.3
        bubbles.Parent = jaw
        s.bubbles = bubbles
    end

    function animateGlacierPuff(rig, s, moving, fly, nova)
        if not s.bubblesMade then
            puffBubbles(rig, s)
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > PUFF_FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)

        -- the special, Hoarfrost Bloom: it takes a great gulp of air and swells into a ball of hoarfrost spines (to 0.42; Blasts.HoarfrostBloom), hangs
        -- there turning slowly, then lets the air go in a sigh of frost bubbles and is a smooth little fish again
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local swell = smoothstep(0.08, 0.4, progress) * (1 - smoothstep(0.74, 0.94, progress))
        local gulpIn = if progress > 0.02 and progress < 0.12 then math.sin(math.pi * (progress - 0.02) / 0.1) else 0
        if progress > 0.76 and not s.sighed then
            s.sighed = true
            if s.bubbles then
                s.bubbles:Emit(14)
            end
        elseif progress == 0 then
            s.sighed = false
        end

        -- startled now and then: a quick half puff, a few spines pricking out, and it settles
        s.nextStartle = s.nextStartle or t + 12 + math.random() * 10
        if t >= s.nextStartle and progress == 0 then
            s.startleAt = t
            s.nextStartle = t + 14 + math.random() * 12
        end
        local startleEnv = if s.startleAt then (t - s.startleAt) / 1.6 else 1
        local startle = if startleEnv < 1 then smoothstep(0, 0.12, startleEnv) * (1 - smoothstep(0.45, 1, startleEnv)) * 0.5 else 0
        local puff = math.max(swell, startle)
        for k = 1, PUFF_ZONES do
            pose(m["Puff" .. k], CFrame.new(PUFF_DIRS[k] * (PUFF_T * puff * u)))
            pose(m["Spike" .. k], CFrame.new(PUFF_DIRS[k] * (PUFF_S * puff * u)))
        end

        -- swimming: its body wags as a fish's does, the tail sculling behind it, faster when it goes somewhere; puffed, it can only paddle
        local stiff = 1 - 0.7 * puff
        s.swim = (s.swim or 0) + dt * (2.4 + 4 * pace) * (1 - 0.5 * puff)
        local wag = math.sin(s.swim)
        local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
        local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
        s.heading = heading
        s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
        local bodySole = rig.points.Body
        if bodySole and not s.sole then
            s.sole = rig.rootPart.CFrame:PointToObjectSpace(bodySole.WorldPosition).Y * -1 / u + PUFF_BODY_SOLE -- (WorldPosition leaves out its own Transform)
        end
        local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.2)
        local bob = 0.03 * math.sin(t * 1.3) + 0.012 * math.sin(t * 2.9 + 1)
        local lift = (PUFF_HOVER * (1 - fly) + bob + 0.05 * swell) * u - drop
        local spin = if progress > 0.3 and progress < 0.9 then 2 * math.pi * smoothstep(0.3, 0.9, progress) else 0
        pose(m.Body, CFrame.new(0, lift, 0) * CFrame.Angles(-0.18 * pace + 0.04 * math.sin(t * 0.9), 0.09 * wag * stiff + spin, s.bank + 0.05 * math.sin(t * 0.7)))
        pose(m.Tail1, CFrame.Angles(0, -0.2 * math.sin(s.swim - 0.8) * stiff, 0))
        pose(m.Tail2, CFrame.Angles(0, -0.32 * math.sin(s.swim - 1.6) * (0.4 + 0.6 * stiff), 0))

        -- its fins: the pectorals whir, a blur of small fast beats, harder when it swims fast or is puffed; the dorsal and anal fins ripple
        s.whir = (s.whir or 0) + dt * (14 + 10 * pace + 8 * puff)
        local beat = math.sin(s.whir)
        for _, tag in { "L", "R" } do
            local sign = if tag == "L" then 1 else -1
            local back = -0.14 + 0.36 * (0.5 + 0.5 * beat) -- between 0.22 forward and -0.5 back (checked in Blender: further forward meets its cheek)
            pose(m["Fin" .. tag], CFrame.Angles(0, sign * math.clamp(back - 0.2 * pace, -0.5, 0.22), 0))
        end
        pose(m.Dorsal, CFrame.Angles(0, 0, 0.18 * math.sin(s.swim * 1.5)))
        pose(m.Anal, CFrame.Angles(0, 0, -0.18 * math.sin(s.swim * 1.5 + 0.6)))

        -- its eyes: each wanders its own way; now and then both fix on you
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.eyes = s.eyes or { L = { yaw = 0, pitch = 0, next = 0 }, R = { yaw = 0, pitch = 0, next = 0 } }
        s.nextBoth = s.nextBoth or t + 3
        if t >= s.nextBoth then
            s.bothUntil = t + 1.2 + math.random() * 1.5
            s.nextBoth = s.bothUntil + 3 + math.random() * 4
        end
        local both = t < (s.bothUntil or 0) or swell > 0.1
        for tag, eye in s.eyes do
            local sign = if tag == "L" then 1 else -1
            if t >= eye.next then
                eye.next = t + 0.6 + math.random() * 1.8
                eye.wantYaw, eye.wantPitch = (math.random() - 0.5) * 0.9, (math.random() - 0.5) * 0.5
            end
            local wy = if both then math.clamp(math.atan2(-toYou.X, -toYou.Z) * 0.5 - sign * 0.15, -0.45, 0.45) else eye.wantYaw or 0
            local wp = if both then math.clamp(toYou.Y * 0.5, -0.3, 0.3) else eye.wantPitch or 0
            eye.yaw += (wy - eye.yaw) * math.min(1, dt * 10)
            eye.pitch += (wp - eye.pitch) * math.min(1, dt * 10)
            pose(m["Eye" .. tag], CFrame.Angles(eye.pitch, eye.yaw, 0))
        end

        -- it gulps every few seconds, a few frost bubbles rising from its mouth; it takes a great gulp before it swells
        s.nextGulp = s.nextGulp or t + 2
        if t >= s.nextGulp then
            s.gulpAt = t
            s.nextGulp = t + 2.5 + math.random() * 3.5
            if s.bubbles and swell < 0.1 then
                s.bubbles:Emit(3)
            end
        end
        local gulpEnv = if s.gulpAt then (t - s.gulpAt) / 0.45 else 1
        local gulp = if gulpEnv < 1 then math.sin(math.pi * gulpEnv) else 0
        pose(m.Jaw, CFrame.Angles(-0.35 * math.max(gulp, gulpIn), 0, 0))
    end
end
local animateObsidianGuardian, GUARD_BONES, GUARD_GLASS, GUARD_PALE, GUARD_VIOLET -- animateObsidianGuardian's section below (its own locals stay in its block)
do

    -- The Obsidian Guardian (skinned): a gargoyle of black glass. It perches as gargoyles do, crouched with its hands on the ledge before it and its wings
    -- folded up behind it, their shards hanging round it like a cloak, and keeps as still as the stone it is; then its head snaps round to watch you, its
    -- brow shards lowering, and holds. Now and then it mantles, raising its wings forward over its shoulders, and settles again; its tail's point twitches.
    -- When its owner goes anywhere it takes off and flies low beside them in slow, heavy beats with long glides between, and lands again the moment they stop.
    local GUARD_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
    local GUARD_HIPS_SOLE = 0.2458 -- metres from its Hips bone down to its talons as it perches (obsidian_guardian.py): where it stands when it lands.
    -- Measured from the bone, not the box: the importer's root part sits at the model's origin, so the box's middle is not where it seems
    local GUARD_HOVER = 0.9 -- metres above the ground it flies when its owner goes anywhere on foot
    GUARD_VIOLET, GUARD_PALE, GUARD_GLASS = Color3.fromRGB(154, 80, 255), Color3.fromRGB(226, 206, 255), Color3.fromRGB(34, 22, 52)
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
    GUARD_BONES = guardBones()
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

    function animateObsidianGuardian(rig, s, moving, fly, nova)
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
end
local animateWindSprite, WIND_FAR -- animateWindSprite's section below (its own locals stay in its block)
do

    -- The Wind Sprite is one smooth skin on a skeleton, so its joints are Bones (PetRig.buildSkinned). Axes as everywhere: -Z ahead, +X to its right; its left is -X.
    local WIND_LID_HINGE = { L = Vector3.new(0.9574, -0.1218, -0.2618), R = Vector3.new(0.9574, 0.1218, 0.2618) } -- both lids of an eye turn on this line
    local WIND_BLINK_UPPER, WIND_BLINK_LOWER = math.rad(72), math.rad(22)
    local WIND_CREST_TURN = math.rad(35) -- both hair bones turned at rest: built side-on its curl reads from the front as a stump; turned, as a curled topknot
    WIND_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest

    local function windLids(m, side, upper, lower)
        local hinge = WIND_LID_HINGE[side]
        pose(m["LidU" .. side], CFrame.fromAxisAngle(hinge, -upper))
        pose(m["LidL" .. side], CFrame.fromAxisAngle(hinge, lower))
    end

    function animateWindSprite(rig, s, moving, fly, nova)
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
end
local animateGalaxyManta -- animateGalaxyManta's section below (its own locals stay in its block)
do

    -- The Galaxy Manta (a skinned pet, like the Wind Sprite): waves run out along its wings and back across them; a little galaxy turns under it, on its own bones, so
    -- the body can bank and roll over it. Rings turning at slightly different speeds wind and unwind the arms.
    local MANTA_SPAN = { 0.10, 0.13, 0.17, 0.2 }

    function animateGalaxyManta(rig, s, moving, fly, nova)
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
end
local animateStormhornKirin -- animateStormhornKirin's section below (its own locals stay in its block)
do

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

    function animateStormhornKirin(rig, s, moving, fly, nova)
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
end
local animateLion -- animateLion's section below (its own locals stay in its block)
do

    local LION_LEGS = { LegFL = 0, LegBR = 0.15, LegFR = math.pi, LegBL = math.pi + 0.15 }
    function animateLion(rig, s, moving, fly, nova)
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

PetRig.Profiles.GlacierPuff = {
    Skinned = true,
    Bones = {
        "Body", "Head", "Jaw", "EyeL", "EyeR", "Tail1", "Tail2", "FinL", "FinR", "Dorsal", "Anal",
        "Puff1", "Puff2", "Puff3", "Puff4", "Puff5", "Puff6", "Puff7", "Puff8",
        "Spike1", "Spike2", "Spike3", "Spike4", "Spike5", "Spike6", "Spike7", "Spike8",
    },
    Points = { "Body", "Jaw", "Head" },
    GlowColors = {
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "HoarfrostBloom",
        Pulse = "Glints",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(190, 230, 255),
        Amber = Color3.fromRGB(150, 210, 250),
        Orange = Color3.fromRGB(80, 150, 220),
        Sun = Color3.fromRGB(236, 248, 255),
        Ivory = Color3.fromRGB(246, 252, 255),
    },
    Animate = animateGlacierPuff,
}

PetRig.Profiles.TimekeeperTortoise = {
    Skinned = true,
    Bones = {
        "Body", "Neck1", "Neck2", "Head", "Jaw", "LidUL", "LidLL", "LidUR", "LidLR", "BrowL", "BrowR", "Tail",
        "LegFL1", "LegFL2", "FootFL", "LegFR1", "LegFR2", "FootFR", "LegBL1", "LegBL2", "FootBL", "LegBR1", "LegBR2", "FootBR",
    },
    Points = { "Body", "Head" },
    GlowColors = {
        ffcf6e = TORT.GOLD, -- the line of gold light along its gnomon's edge
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "StoppedHour",
        Pulse = "Edge",
        Light = "Edge",
        NovaLight = 2,
    },
    Colors = {
        Gold = Color3.fromRGB(255, 214, 130),
        Amber = Color3.fromRGB(230, 200, 120),
        Orange = Color3.fromRGB(176, 124, 58),
        Sun = Color3.fromRGB(255, 245, 210),
        Ivory = Color3.fromRGB(250, 244, 226),
    },
    Animate = animateTimekeeperTortoise,
}

PetRig.Profiles.GravityImp = {
    Skinned = true,
    Bones = {
        "Core", "Planet", "Pivot", "Hips", "Chest", "Head", "EarL", "EarR", "BrowL", "BrowR", "LidUL", "LidLL", "LidUR", "LidLR",
        "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR", "LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR",
        "Tail1", "Tail2", "Tail3", "Tail4", "Pebble1", "Pebble2", "Pebble3",
    },
    Points = { "Core", "Head" },
    GlowColors = {
        d28cff = IMP.VIOLET, -- the veins of gravity in its moonlet's cracks
        ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
    },
    Effects = {
        Blast = "WhichWayIsDown",
        Pulse = "Veins",
        NovaLight = 2, -- (its light hangs on its Core bone: animateGravityImp)
    },
    Colors = {
        Gold = IMP.VIOLET,
        Amber = Color3.fromRGB(186, 156, 220),
        Orange = IMP.DEEP,
        Sun = Color3.fromRGB(240, 210, 255),
        Ivory = Color3.fromRGB(246, 240, 255),
    },
    Animate = animateGravityImp,
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
        petId = petId,
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
        petId = petId,
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
                local seeThrough = profile.SeeThroughGlow and profile.SeeThroughGlow[string.lower(hex)]
                if seeThrough then
                    d.Transparency = seeThrough
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

-- It has planted itself under its gnomon (animateTimekeeperTortoise) and stops the hour: the gnomon's edge flares, a ring of hour marks lights round it
-- one after another on the ground, golden motes stop dead in the air, and for whoever is near the world fades toward an old photograph's sepia for a
-- heartbeat; then time starts again, the motes drift on and fade, the marks go out and the colour comes back.
function Blasts.StoppedHour(rig, fx)
    local u, neon = rig.unit, fx.neon
    local body = rig.points.Body
    local centre = if body then body.TransformedWorldCFrame.Position else rig.rootPart.Position
    local params = RaycastParams.new()
    params.FilterDescendantsInstances = { rig.model }
    local hit = workspace:Raycast(centre + Vector3.new(0, 2 * u, 0), Vector3.new(0, -12 * u, 0), params)
    local groundY = if hit then hit.Position.Y else centre.Y - 0.36 * rig.meters
    local ground = Vector3.new(centre.X, groundY + 0.05, centre.Z)

    -- the hour marks: twelve bars of gold light laid flat round it like a dial's, lit one after another in a quarter second, out after the stopped beat;
    -- each finds the ground under it (laid at the height of its middle, on uneven ground half of them were buried and grass hid the rest: seen in Play)
    -- as each lights, a few gold sparks rise off it and stop dead in the air with the rest of time: they show above grass, which hides anything flat
    local facing = fx.facing
    local rise = Instance.new("ParticleEmitter")
    rise.Texture = SPARKLE
    rise.Enabled = false
    rise.EmissionDirection = Enum.NormalId.Top
    rise.SpreadAngle = Vector2.new(12, 12)
    rise.Lifetime = NumberRange.new(1.2, 1.5)
    rise.Speed = NumberRange.new(2.4 * u, 3.4 * u)
    rise.Drag = 7
    rise.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(0.75, 0.08 * u), NumberSequenceKeypoint.new(1, 0) })
    rise.Color = ColorSequence.new(TORT.GOLD, TORT.SEPIA)
    rise.LightEmission = 0.9
    rise.LightInfluence = 0.1
    for k = 0, 11 do
        local a = k / 12 * 2 * math.pi
        local out = facing:VectorToWorldSpace(Vector3.new(math.sin(a), 0, -math.cos(a)))
        local long = if k % 3 == 0 then 0.55 else 0.32
        local at = leopardGroundAt(ground + out * (2.4 * u), rig.meters)
        if not at then
            continue -- nothing under it (a ledge): that hour stays dark
        end
        local mark = neon(Vector3.new(0.1 * u, 0.04, long * u), CFrame.lookAt(at, at + out), TORT.GOLD)
        mark.Transparency = 1
        tweenAfter(k * 0.022, mark, TweenInfo.new(0.08), { Transparency = 0.15 })
        tweenAfter(0.9, mark, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
        local sparks = rise:Clone()
        sparks.Parent = mark
        task.delay(k * 0.022, function()
            if sparks.Parent then
                sparks:Emit(if k % 3 == 0 then 4 else 2)
            end
        end)
    end
    rise:Destroy()

    -- the motes: gold, thrown out a little and stopped dead by their drag, hanging as time stands still, then sinking away
    local holder = neon(Vector3.one * 1.6 * u, CFrame.new(centre), TORT.GOLD)
    holder.Shape = Enum.PartType.Ball
    holder.Transparency = 1
    local motes = Instance.new("ParticleEmitter")
    motes.Texture = SPARKLE
    motes.Enabled = false
    motes.Shape = Enum.ParticleEmitterShape.Sphere
    motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    motes.Lifetime = NumberRange.new(1.4, 1.8)
    motes.Speed = NumberRange.new(0.6 * u, 1.2 * u)
    motes.SpreadAngle = Vector2.new(180, 180)
    motes.Drag = 9
    motes.Acceleration = Vector3.new(0, -0.15 * u, 0)
    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(0.7, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
    motes.Color = ColorSequence.new(TORT.GOLD, TORT.SEPIA)
    motes.LightEmission = 0.8
    motes.LightInfluence = 0.2
    motes.Parent = holder
    motes:Emit(40)

    local light = Instance.new("PointLight")
    light.Color = TORT.GOLD
    light.Range = 5 * u
    light.Brightness = 0
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(0.1), { Brightness = 1.6 }):Play()
    tweenAfter(0.8, light, TweenInfo.new(0.5), { Brightness = 0 })

    -- for whoever is near: the world fades toward sepia for the stopped beat, then its colour comes back
    local player = Players.LocalPlayer
    local camera = workspace.CurrentCamera
    if camera and (camera.CFrame.Position - centre).Magnitude < 45 and not (player and player:GetAttribute("SettingReducedEffects") == true) then
        local grade = Instance.new("ColorCorrectionEffect")
        grade.Name = "StoppedHourGrade"
        grade.Parent = Lighting
        TweenService:Create(grade, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { TintColor = TORT.SEPIA, Saturation = -0.55, Contrast = 0.06 }):Play()
        tweenAfter(0.75, grade, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { TintColor = Color3.new(1, 1, 1), Saturation = 0, Contrast = 0 })
        Debris:AddItem(grade, 1.6)
    end
end

-- It has stamped on its moonlet (animateGravityImp) and the ground round it lets go of its stones: they tear out of the ground in puffs of dust, rise to
-- circle the moonlet round its middle, spin faster and faster with violet motes drawn in after them, and are flung off to fall where they like; a
-- ripple of violet runs out along the ground. Their orbit lies outside the pebbles' and clear of the imp however it hangs (gravity_imp.py's numbers).
function Blasts.WhichWayIsDown(rig, fx)
    local u, metre, neon = rig.unit, rig.meters, fx.neon
    local core = rig.points.Core
    local function middle()
        return if core then core.TransformedWorldCFrame.Position else rig.rootPart.Position
    end
    local centre = middle()
    local params = RaycastParams.new()
    params.FilterDescendantsInstances = { rig.model }
    local hit = workspace:Raycast(centre + Vector3.new(0, 1 * u, 0), Vector3.new(0, -14 * u, 0), params)
    local groundY = if hit then hit.Position.Y else centre.Y - 0.45 * metre
    local player = Players.LocalPlayer
    local reduced = player and player:GetAttribute("SettingReducedEffects") == true
    local count = if reduced then 6 else 12

    local stones = {}
    for k = 1, count do
        local a0 = (k - 1) / count * 2 * math.pi + math.random() * 0.4
        local r0 = (1.8 + math.random() * 1.2) * u
        local at = leopardGroundAt(Vector3.new(centre.X + math.cos(a0) * r0, groundY, centre.Z + math.sin(a0) * r0), metre)
        if at then
            local size = (0.17 + math.random() * 0.13) * u
            local stone = neon(Vector3.new(size, size * (0.6 + math.random() * 0.4), size * (0.7 + math.random() * 0.5)), CFrame.new(at), IMP.STONE:Lerp(IMP.DUST, math.random() * 0.4))
            stone.Material = Enum.Material.Slate
            if not reduced then
                local dust = Instance.new("ParticleEmitter")
                dust.Texture = "rbxasset://textures/particles/smoke_main.dds"
                dust.Enabled = false
                dust.Lifetime = NumberRange.new(0.5, 0.9)
                dust.Speed = NumberRange.new(0.3 * u, 0.8 * u)
                dust.SpreadAngle = Vector2.new(70, 70)
                dust.EmissionDirection = Enum.NormalId.Top
                dust.Drag = 3
                dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15 * u), NumberSequenceKeypoint.new(1, 0.4 * u) })
                dust.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) })
                dust.Color = ColorSequence.new(IMP.DUST)
                dust.LightInfluence = 1
                dust.Parent = stone
                dust:Emit(4)
            end
            table.insert(stones, {
                part = stone,
                from = at,
                a = math.atan2(at.Z - centre.Z, at.X - centre.X),
                r = (1.65 + math.random() * 0.35) * u, -- (outside the pebbles' orbit, which reaches 1.35 u)
                h = (math.random() - 0.5) * 0.4 * u,
                turn = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 9,
            })
        end
    end

    -- a ripple of violet along the ground
    local ripple = neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(centre.X, groundY + 0.04 * u, centre.Z) * CFrame.Angles(0, 0, math.pi / 2), IMP.VIOLET)
    ripple.Shape = Enum.PartType.Cylinder
    ripple.Transparency = 0.35
    TweenService:Create(ripple, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02 * u, 5.2 * u, 5.2 * u), Transparency = 1 }):Play()

    -- violet motes drawn in toward the moonlet as the stones whirl
    local holder = neon(Vector3.one * 3.6 * u, CFrame.new(centre), IMP.VIOLET)
    holder.Shape = Enum.PartType.Ball
    holder.Transparency = 1
    if not reduced then
        local motes = Instance.new("ParticleEmitter")
        motes.Texture = SPARKLE
        motes.Shape = Enum.ParticleEmitterShape.Sphere
        motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        motes.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
        motes.Rate = 40
        motes.Lifetime = NumberRange.new(0.5, 0.7)
        motes.Speed = NumberRange.new(2 * u, 2.6 * u)
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(1, 0) })
        motes.Color = ColorSequence.new(IMP.VIOLET, IMP.DEEP)
        motes.LightEmission = 0.8
        motes.LightInfluence = 0.1
        motes.Parent = holder
        task.delay(0.9, function()
            motes.Enabled = false
        end)
    end

    -- the stones: up out of the ground to the ring (0.45 s), round it faster and faster (to 1.3 s), flung off and falling (to 1.95 s)
    local start = os.clock()
    local connection
    connection = RunService.Heartbeat:Connect(function()
        local e = os.clock() - start
        if e > 1.95 or #stones == 0 or not stones[1].part.Parent then
            connection:Disconnect()
            return
        end
        local now = middle()
        holder.Position = now
        for _, st in stones do
            local p
            if e < 1.3 then
                local orbit = if e < 0.45 then 0.8 * e else 0.36 + 1.5 * (e - 0.45) + 7.5 / 2 * (e - 0.45) ^ 2 / 0.85
                local ang = st.a + orbit
                local ring = now + Vector3.new(math.cos(ang) * st.r, st.h, math.sin(ang) * st.r)
                if e < 0.45 then
                    local f = 1 - (1 - e / 0.45) ^ 3
                    p = st.from:Lerp(ring, f) + Vector3.new(0, math.sin(math.pi * e / 0.45) * 0.3 * u, 0)
                else
                    p = ring
                end
                st.last, st.lastAng = p, ang
            else
                if not st.fling then
                    local ang = st.lastAng
                    st.fling = { at = st.last, v = Vector3.new(-math.sin(ang), 0, math.cos(ang)) * 9 * st.r * 0.35 + Vector3.new(math.cos(ang), 0, math.sin(ang)) * 1.2 * u + Vector3.new(0, 1.2 * u, 0) }
                end
                local tau = e - 1.3
                p = st.fling.at + st.fling.v * tau + Vector3.new(0, -14 * u * tau * tau, 0)
                st.part.Transparency = math.clamp((e - 1.7) / 0.25, 0, 1)
            end
            st.part.CFrame = CFrame.new(p) * CFrame.Angles(st.turn.X * e, st.turn.Y * e, st.turn.Z * e)
        end
    end)
end

-- It has swollen into a ball of hoarfrost (animateGlacierPuff): frost bursts off its spines, a flash of cold light, glittering frost scattering out and
-- drifting down, and a breath of icy mist rolling out round it.
function Blasts.HoarfrostBloom(rig, fx)
    local u, neon = rig.unit, fx.neon
    local body = rig.points.Body
    local at = if body then body.TransformedWorldCFrame.Position else rig.rootPart.Position
    -- (the holder is the size of the puffed ball, and everything leaves its surface outward: emitted from its middle, it all stopped inside the fish)
    local holder = neon(Vector3.one * 0.48 * rig.meters, CFrame.new(at), PUFF_FROST)
    holder.Shape = Enum.PartType.Ball
    holder.Transparency = 1

    local light = Instance.new("PointLight")
    light.Color = PUFF_ICE
    light.Range = 4 * u
    light.Brightness = 0
    light.Shadows = false
    light.Parent = holder
    TweenService:Create(light, TweenInfo.new(0.08), { Brightness = 1.8 }):Play()
    tweenAfter(0.1, light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 })

    -- the frost: fine glittering crystals thrown off the spines, slowing, drifting down
    local frost = Instance.new("ParticleEmitter")
    frost.Texture = SPARKLE
    frost.Enabled = false
    frost.Shape = Enum.ParticleEmitterShape.Sphere
    frost.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    frost.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
    frost.Lifetime = NumberRange.new(0.8, 1.4)
    frost.Speed = NumberRange.new(2 * u, 3.5 * u)
    frost.SpreadAngle = Vector2.new(20, 20)
    frost.Drag = 2.5
    frost.Acceleration = Vector3.new(0, -0.6 * u, 0)
    frost.Rotation = NumberRange.new(0, 360)
    frost.RotSpeed = NumberRange.new(-90, 90)
    frost.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(0.3, 0.2 * u), NumberSequenceKeypoint.new(1, 0) }) -- (smaller did not read in Play)
    frost.Color = ColorSequence.new(Color3.new(1, 1, 1), PUFF_ICE)
    frost.LightEmission = 0.8
    frost.LightInfluence = 0.2
    frost.Parent = holder
    frost:Emit(48)

    -- the mist: a breath of cold air rolling out round it and thinning away
    local mist = Instance.new("ParticleEmitter")
    mist.Texture = "rbxasset://textures/particles/smoke_main.dds"
    mist.Enabled = false
    mist.Shape = Enum.ParticleEmitterShape.Sphere
    mist.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
    mist.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
    mist.Lifetime = NumberRange.new(0.9, 1.3)
    mist.Speed = NumberRange.new(0.8 * u, 1.4 * u)
    mist.SpreadAngle = Vector2.new(15, 15)
    mist.Drag = 2.5
    mist.Rotation = NumberRange.new(0, 360)
    mist.RotSpeed = NumberRange.new(-30, 30)
    mist.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5 * u), NumberSequenceKeypoint.new(1, 1.6 * u) })
    mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 1) })
    mist.Color = ColorSequence.new(PUFF_FROST)
    mist.LightEmission = 0.2
    mist.LightInfluence = 0.6
    mist.Parent = holder
    mist:Emit(10)
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
    if PetRig.PetSounds.special(rig.petId) and rig.rootPart:IsDescendantOf(workspace) then -- (never from a portrait)
        PetRig.Sfx.play(PetRig.PetSounds.special(rig.petId), rig.rootPart)
    end
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

    -- on a phone, another player's pet gives up its point lights (a phone pays for every dynamic light; a pet makes some
    -- of its lights as it first animates, so they are looked for now and then)
    if PetRig.Quality.Low and rig.owner and rig.owner ~= Players.LocalPlayer and s.time >= (s.nextLightSweep or 0) then
        s.nextLightSweep = s.time + 2
        for _, d in rig.model:GetDescendants() do
            if d:IsA("PointLight") or d:IsA("SpotLight") then
                d.Enabled = false
            end
        end
    end

    -- now and then, its voice (in the world only: never from a portrait; never over its special)
    local every = PetRig.VOICE_EVERY
    s.nextVoice = s.nextVoice or s.time + every[1] * math.random()
    if s.time >= s.nextVoice then
        s.nextVoice = s.time + every[1] + math.random() * (every[2] - every[1])
        local voice = PetRig.PetSounds.voice(rig.petId)
        if voice and not rig.nova and rig.rootPart:IsDescendantOf(workspace) then
            PetRig.Sfx.play(voice, rig.rootPart)
        end
    end

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

-- ---------- The Crystal Beetle: all of it in one block, so its locals are freed at its end. PetRig's main chunk sits at Luau's limit of 200 locals
-- (a top-level table of the beetle's pushed it over, though twenty plain locals fitted): a new pet goes in a block of its own here. ----------
do
    -- The Crystal Beetle (skinned): a stout, proud rhinoceros beetle of indigo chitin, its wing cases domes of crystal ringed with a growth layer for every
    -- year, its great horn a quartz crystal grown a segment a year. Every piece of it is a rigid plate on its own bone, as an insect's are. It stands
    -- square on its six legs, turning its head slowly, proud; now and then it tosses its horn, shoves at nothing with its head down, flicks its clubbed
    -- antennae, settles its wing cases with a shrug. It walks in a tripod gait (three legs down, three swinging forward). When its owner flies it opens its
    -- wing cases, swings its wings out from under them and buzzes alongside, its legs hanging.
    local BEETLE = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        BODY_SOLE = 0.1097, -- metres from its Body bone down to its feet (crystal_beetle.py)
        -- its walk, checked in Blender at every quarter of its cycle: each leg swings about the upright through its hip (a planted foot keeps exactly its
        -- height), lifting at the hip and the knee as it swings forward; the front left, middle right and hind left together, then the others
        SWING = 0.3,
        LIFT = 0.22,
        KNEE = 0.3,
        LEGS = { { "L", 1, 1, 0 }, { "L", 2, 1, math.pi }, { "L", 3, 1, 0 }, { "R", 1, -1, math.pi }, { "R", 2, -1, 0 }, { "R", 3, -1, math.pi } }, -- side, pair, sign, lead
        -- stances, each checked in Blender (crystal_beetle.py's POSES) and along the slerp from one to another: turns x, y, z; then a move in metres
        FLY = { -- on the wing (its wings' own turns are built in animateCrystalBeetle: spread first, then beating)
            Body = { 0.42, 0, 0, 0, 0.05, 0 },
            ElyL = { -0.4, 0, -1.1 }, ElyR = { -0.4, 0, 1.1 },
            LegL1 = { 0, -0.15, 0.22 }, ShinL1 = { 0, 0, -0.2 }, LegL2 = { 0, 0, 0.22 }, ShinL2 = { 0, 0, -0.2 }, LegL3 = { 0, 0.15, 0.22 }, ShinL3 = { 0, 0, -0.2 },
            LegR1 = { 0, 0.15, -0.22 }, ShinR1 = { 0, 0, 0.2 }, LegR2 = { 0, 0, -0.22 }, ShinR2 = { 0, 0, 0.2 }, LegR3 = { 0, -0.15, -0.22 }, ShinR3 = { 0, 0, 0.2 },
        },
        WING_SPREAD = 1.35,
        WING_UP = 0.6, -- its wings beat mostly above level: lower, they met its legs
        WING_DOWN = 0.25,
        REAR = { -- its special, wound up: reared on its hind legs, front legs up, head back
            Body = { 0.38, 0, 0, 0, 0.094, 0.01 }, Head = { 0.2, 0, 0 },
            LegL1 = { 0, 0, -0.55 }, ShinL1 = { 0, 0, 0.45 }, LegR1 = { 0, 0, 0.55 }, ShinR1 = { 0, 0, -0.45 },
        },
        STRIKE = { -- struck: its front slammed down, its head swung down, the horn level before it (pitched to the ground, its face went in first)
            Body = { -0.12, 0, 0, 0, 0.022, 0 }, Head = { -0.5, 0, 0 },
            LegL1 = { 0, -0.25, -0.12 }, LegR1 = { 0, 0.25, 0.12 },
        },
        SHRUG = { ElyL = { -0.18, 0, -0.08 }, ElyR = { -0.18, 0, 0.08 } },
        BONES = {
            "Head", "AntL", "AntR", "ElyL", "ElyR",
            "LegL1", "ShinL1", "FootL1", "LegL2", "ShinL2", "FootL2", "LegL3", "ShinL3", "FootL3",
            "LegR1", "ShinR1", "FootR1", "LegR2", "ShinR2", "FootR2", "LegR3", "ShinR3", "FootR3",
        },
        CYAN = Color3.fromRGB(160, 245, 255),
        DEEP = Color3.fromRGB(40, 140, 175),
        PALE = Color3.fromRGB(225, 252, 255),
    }

    function BEETLE.cf(a, u)
        local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
        return move * CFrame.Angles(a[1], a[2], a[3])
    end

    local function animateCrystalBeetle(rig, s, moving, fly, nova)
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > BEETLE.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

        -- the special, Ring of Years: it lands if it is flying, rears on its hind legs (to 0.32), slams its front down (at 0.42: Blasts.RingOfYears),
        -- holds it, and settles
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local active = if rig.nova then 1 else 0
        s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 3)
        local grounded = 1 - smoothstep(0, 0.3, s.air)
        local rear = smoothstep(0.05, 0.3, progress) * (1 - smoothstep(0.37, 0.42, progress)) * grounded
        local strike = smoothstep(0.37, 0.42, progress) * (1 - smoothstep(0.62, 0.9, progress)) * grounded
        local impact = if progress > 0.42 then math.exp(-(progress - 0.42) * 14) else 0

        -- it stands on the ground, or keeps to its owner's height on the wing
        local body = rig.points.Body
        if body and not s.sole then
            s.sole = rig.rootPart.CFrame:PointToObjectSpace(body.WorldPosition).Y * -1 / u + BEETLE.BODY_SOLE -- (WorldPosition leaves out its own Transform)
        end
        local drop = dropToGround(rig, s, t, u, s.air, s.sole or 0.11)

        -- idle business: a toss of the horn, a shove with its head down, a shrug of its wing cases
        s.nextIdle = s.nextIdle or t + 4
        if t >= s.nextIdle and moving < 0.1 and s.air < 0.1 and active == 0 then
            s.idleAt, s.idleKind = t, math.random(1, 3)
            s.nextIdle = t + 6 + math.random() * 6
        end
        local idle = if s.idleAt then (t - s.idleAt) / 1.8 else 1
        local env = if idle < 1 then math.sin(math.pi * idle) else 0
        local toss = if s.idleKind == 1 then env else 0
        local shove = if s.idleKind == 2 then env else 0
        local shrug = if s.idleKind == 3 then env else 0

        -- its legs: the tripod gait as it goes, or a few plodding steps in place as it shoves
        local walking = math.max(moving, 0.5 * shove) * grounded * (1 - rear) * (1 - strike)
        s.step = (s.step or 0) + dt * (4 + 7 * moving) * walking
        local want = {}
        for _, leg in BEETLE.LEGS do
            local tag, k, sign, lead = leg[1], leg[2], leg[3], leg[4]
            local sw = math.sin(s.step + lead) * walking
            local lf = math.max(0, math.cos(s.step + lead)) * walking
            want["Leg" .. tag .. k] = CFrame.Angles(0, -BEETLE.SWING * sw * sign, -BEETLE.LIFT * lf * sign)
            want["Shin" .. tag .. k] = CFrame.Angles(0, 0, BEETLE.KNEE * lf * sign)
            want["Foot" .. tag .. k] = CFrame.identity
        end

        -- its head: slowly, proudly about, sometimes at you; tossing its horn, or down to shove
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 3 + math.random() * 4
            s.atYou = math.random() < 0.5
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.6, (math.random() - 0.4) * 0.25
        end
        local wantYaw = if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.38, 0.38) else s.gazeYaw
        local wantPitch = if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.18) else s.gazePitch
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
        local calm = (1 - rear) * (1 - strike)
        local yaw = math.clamp(s.yaw * calm + 0.3 * math.sin(idle * 2 * math.pi * 2) * toss, -0.38, 0.38)
        local pitch = math.clamp(s.pitch * calm - 0.2 * shove + 0.1 * toss, -0.2, 0.18)
        want.Head = CFrame.Angles(pitch, yaw, 0)

        -- its antennae: the clubs flick now and then
        s.nextFlick = s.nextFlick or t + 1
        if t >= s.nextFlick then
            s.flickAt = t
            s.nextFlick = t + 1.5 + math.random() * 3
        end
        local fl = if s.flickAt then (t - s.flickAt) / 0.3 else 1
        local flick = if fl < 1 then math.sin(math.pi * fl) else 0
        want.AntL = CFrame.Angles(0.15 * math.sin(t * 1.3) + 0.25 * flick, -0.2 * flick, 0)
        want.AntR = CFrame.Angles(0.15 * math.sin(t * 1.3 + 1) + 0.25 * flick, 0.2 * flick, 0)

        -- its wing cases: a shrug now and then; open on the wing (first: its wings swing out after, from under them)
        want.ElyL = BEETLE.cf(BEETLE.SHRUG.ElyL, u):Lerp(CFrame.identity, 1 - shrug)
        want.ElyR = BEETLE.cf(BEETLE.SHRUG.ElyR, u):Lerp(CFrame.identity, 1 - shrug)
        local cases = math.min(1, s.air / 0.6)
        local spread = smoothstep(0.4, 1, s.air)
        s.buzz = (s.buzz or 0) + dt * 110 * spread
        local beat = math.sin(s.buzz)
        local flap = (-BEETLE.WING_UP * math.max(beat, 0) + BEETLE.WING_DOWN * math.max(-beat, 0)) * spread
        pose(m.WingL, CFrame.Angles(0, 0, flap) * CFrame.Angles(0, -BEETLE.WING_SPREAD * spread, 0))
        pose(m.WingR, CFrame.Angles(0, 0, -flap) * CFrame.Angles(0, BEETLE.WING_SPREAD * spread, 0))

        -- the stances over all that, each a slerp (CFrame:Lerp) as Blender checked them
        for _, name in BEETLE.BONES do
            local cf = want[name] or CFrame.identity
            local a = BEETLE.FLY[name]
            if a then
                cf = cf:Lerp(BEETLE.cf(a, u), if string.sub(name, 1, 3) == "Ely" then cases else s.air)
            end
            a = BEETLE.REAR[name]
            if a then
                cf = cf:Lerp(BEETLE.cf(a, u), rear)
            end
            a = BEETLE.STRIKE[name]
            if a then
                cf = cf:Lerp(BEETLE.cf(a, u), strike)
            end
            pose(m[name], cf)
        end

        -- its body: square on the ground (dropped onto it), hovering and bobbing on the wing; rearing, slamming down, a jolt as it lands
        local hover = (0.04 * math.sin(t * 2.2) + 0.012 * math.sin(s.buzz * 0.05)) * s.air
        local bodyCf = CFrame.new(0, (hover - 0.012 * impact) * u - drop, 0)
        local stance = CFrame.identity:Lerp(BEETLE.cf(BEETLE.FLY.Body, u), s.air)
        stance = stance:Lerp(BEETLE.cf(BEETLE.REAR.Body, u), rear)
        stance = stance:Lerp(BEETLE.cf(BEETLE.STRIKE.Body, u), strike)
        pose(m.Body, bodyCf * stance)
    end

    -- It has slammed its front down (animateCrystalBeetle): a ring of crystal points bursts up out of the ground round it, one after another, one for every
    -- year it has lived; a ripple of cyan light runs out along the ground; then the points shatter into glitter and are gone.
    function Blasts.RingOfYears(rig, fx)
        local u, metre, neon = rig.unit, rig.meters, fx.neon
        local head = rig.points.Head
        local centre = if head then head.TransformedWorldCFrame.Position else rig.rootPart.Position
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(centre + Vector3.new(0, 1 * u, 0), Vector3.new(0, -12 * u, 0), params)
        local groundY = if hit then hit.Position.Y else centre.Y - 0.15 * metre
        local player = Players.LocalPlayer
        local reduced = player and player:GetAttribute("SettingReducedEffects") == true
        local count = if reduced then 8 else 14
        local facing = fx.facing

        local glitter = Instance.new("ParticleEmitter")
        glitter.Texture = SPARKLE
        glitter.Enabled = false
        glitter.Lifetime = NumberRange.new(0.4, 0.8)
        glitter.Speed = NumberRange.new(0.8 * u, 2 * u)
        glitter.SpreadAngle = Vector2.new(180, 180)
        glitter.Acceleration = Vector3.new(0, -3 * u, 0)
        glitter.Drag = 2
        glitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
        glitter.Color = ColorSequence.new(BEETLE.PALE, BEETLE.CYAN)
        glitter.LightEmission = 0.9
        glitter.LightInfluence = 0.1

        for k = 1, count do
            local a = (k - 1) / count * 2 * math.pi
            local out = facing:VectorToWorldSpace(Vector3.new(math.sin(a), 0, -math.cos(a)))
            local at = leopardGroundAt(Vector3.new(centre.X, groundY, centre.Z) + out * ((1.5 + 0.25 * (k % 2)) * u), metre)
            if at then
                local tall = (0.55 + 0.35 * math.random()) * u
                local thick = (0.14 + 0.06 * math.random()) * u
                local tilt = CFrame.lookAt(at, at + out) * CFrame.Angles(math.rad(-22), 0, 0) * CFrame.Angles(0, math.rad(45), 0) -- upright, leaning out 22 degrees, a diamond across (at -68 they lay flat: seen in Play)
                local spike = neon(Vector3.new(thick, tall, thick), tilt * CFrame.new(0, -tall * 0.6, 0), BEETLE.CYAN)
                spike.Material = Enum.Material.Glass
                spike.Transparency = 0.2
                local core = neon(Vector3.new(thick * 0.35, tall * 0.85, thick * 0.35), spike.CFrame, BEETLE.PALE)
                core.Transparency = 0.3
                local delay = (k - 1) * 0.018 -- one after another round the ring
                tweenAfter(delay, spike, TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = tilt * CFrame.new(0, tall * 0.42, 0) })
                tweenAfter(delay, core, TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = tilt * CFrame.new(0, tall * 0.42, 0) })
                tweenAfter(0.75 + delay * 0.5, spike, TweenInfo.new(0.18), { Transparency = 1, Size = Vector3.new(thick * 0.3, tall * 0.5, thick * 0.3) })
                tweenAfter(0.75 + delay * 0.5, core, TweenInfo.new(0.18), { Transparency = 1 })
                if not reduced then
                    local shards = glitter:Clone()
                    shards.Parent = spike
                    task.delay(0.75 + delay * 0.5, function()
                        if shards.Parent then
                            shards:Emit(6) -- it shatters
                        end
                    end)
                end
            end
        end
        glitter:Destroy()

        -- a ripple of cyan light along the ground
        local ripple = neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(centre.X, groundY + 0.04 * u, centre.Z) * CFrame.Angles(0, 0, math.pi / 2), BEETLE.CYAN)
        ripple.Shape = Enum.PartType.Cylinder
        ripple.Transparency = 0.35
        TweenService:Create(ripple, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02 * u, 4.2 * u, 4.2 * u), Transparency = 1 }):Play()
        local flash = neon(Vector3.one * 0.1, CFrame.new(centre), BEETLE.CYAN)
        flash.Transparency = 1
        local light = Instance.new("PointLight")
        light.Color = BEETLE.CYAN
        light.Range = 6 * u
        light.Brightness = 0
        light.Shadows = false
        light.Parent = flash
        TweenService:Create(light, TweenInfo.new(0.08), { Brightness = 2 }):Play()
        tweenAfter(0.5, light, TweenInfo.new(0.5), { Brightness = 0 })
    end

    PetRig.Profiles.CrystalBeetle = {
        Skinned = true,
        Bones = {
            "Body", "Head", "AntL", "AntR", "ElyL", "ElyR", "WingL", "WingR",
            "LegL1", "ShinL1", "FootL1", "LegL2", "ShinL2", "FootL2", "LegL3", "ShinL3", "FootL3",
            "LegR1", "ShinR1", "FootR1", "LegR2", "ShinR2", "FootR2", "LegR3", "ShinR3", "FootR3",
        },
        Points = { "Body", "Head" },
        GlowColors = {
            ["9ff4ff"] = Color3.fromRGB(159, 244, 255), -- the newest crystal: its horn's tip
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        },
        Effects = {
            Blast = "RingOfYears",
            Pulse = "Tip",
            Light = "Tip",
            NovaLight = 2,
        },
        Colors = {
            Gold = BEETLE.CYAN,
            Amber = Color3.fromRGB(214, 152, 64),
            Orange = BEETLE.DEEP,
            Sun = BEETLE.PALE,
            Ivory = Color3.fromRGB(240, 250, 255),
        },
        Animate = animateCrystalBeetle,
    }
end

-- ---------- The Thunderclaw Drake: all of it in one block, so its locals are freed at its end (the main chunk sits at Luau's limit of 200 locals) ----------
do
    -- The Thunderclaw Drake (skinned): a storm wyvern, a dragon that is a living lightning conductor. Its wings are its arms: on the ground it prowls on
    -- their wrists, its chest low and its head held high on its S of a neck, its hands folded back along its flanks with their glowing spurs above its
    -- back; an arc crackles between the copper lightning rods of its horns. Now and then it mantles (opens its folded hands part way) and a crackle
    -- leaps between its spurs, or it turns its head to watch you. It walks in diagonal pairs, a wrist with the opposite foot, its iron hooks striking
    -- sparks. To fly it lifts its wrists clear, opens its wings and beats them, its legs tucked. Its special, Called Down: it rears onto its hind legs,
    -- wings flung open, head to the sky; a bolt comes down onto its horns and it glows white-hot; it slams down onto its wrists, hands flung up over it,
    -- and the bolt bursts out of it along the ground (Blasts.CalledDown).
    local TW = {
        FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOLE = 0.6151, -- metres from the middle of its box down to its feet (thunderclaw_drake.py)
        LID_HINGE = { L = Vector3.new(0.7134, -0.2711, -0.6462), R = Vector3.new(0.7134, 0.2711, 0.6462) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(40),
        BLINK_LOWER = math.rad(16),
        HOVER = 0.3, -- metres it rises taking to the wing (thunderclaw_drake.py's HOVER: its tucked talons clear the ground all the way up)
        BEAT_IN = 0.85, -- its wings start to beat only once they are open, this far into its rise (thunderclaw_drake.py's BEAT_IN: sooner, the
        -- downstroke cut into its flank)
        STEP_RATE = 4.5, -- its walk, radians of its cycle a second standing to a slow prowl, and more at a run
        STEP_RUN = 4,
        -- where its glowing points are at rest, metres in its own axes (thunderclaw_drake.py), and the bone heads that carry them
        HEAD_AT = Vector3.new(0, 0.99, -0.336),
        ARC_AT = Vector3.new(0.0031, 1.228, -0.172),
        HORN_AT = { L = Vector3.new(-0.078, 1.192, -0.164), R = Vector3.new(0.078, 1.192, -0.164) },
        WRIST_AT = { L = Vector3.new(-0.45, 0.96, -0.15), R = Vector3.new(0.45, 0.96, -0.15) },
        HOOK_AT = { L = Vector3.new(-0.4941, 0.9753, -0.2156), R = Vector3.new(0.4941, 0.9753, -0.2156) },
        SPUR_AT = {
            L = { Vector3.new(-0.9046, 1.179, -0.0479), Vector3.new(-0.9793, 0.8928, 0.2301), Vector3.new(-0.7373, 0.6375, 0.4812) },
            R = { Vector3.new(0.9046, 1.179, -0.0479), Vector3.new(0.9793, 0.8928, 0.2301), Vector3.new(0.7373, 0.6375, 0.4812) },
        },
        -- its stances, solved in Blender (thunderclaw_drake.py's pose_tables: feet and wrists placed, wings folded) and checked there in every one and
        -- along every slerp the game makes between them (membrane against body, legs, tail and head; wing against wing; limb against limb; feet,
        -- talons and wrists on the ground): turns x, y, z, then a move in metres. A folded wing never goes straight to an open one: it lifts clear
        -- first (LIFT), then opens.
        PROWL = {
            Chest = { 0.05, 0, 0 }, FootL = { -0.1222, 0, 0 }, FootR = { -0.1222, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.03, 0 },
            LegL1 = { 0.6722, 0, 0 }, LegL2 = { -0.1529, 0, 0 }, LegL3 = { 0.1529, 0, 0 }, LegR1 = { 0.6722, 0, 0 }, LegR2 = { -0.1529, 0, 0 },
            LegR3 = { 0.1529, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, 0, 0 }, Tail2 = { 0.12, 0, 0 }, Tail3 = { 0.04, 0, 0 },
            WingL1 = { -0.4715, -1.0172, 0.9886 }, WingL2 = { -0.1649, -0.1862, -0.1086 }, WingL3 = { 0.8366, -0.2634, -1.3873 },
            WingLF1 = { 0.2826, 0.7461, -1.1865 }, WingLF2 = { -0.2065, 0.8901, -1.183 }, WingLF3 = { -0.8079, 0.8102, -0.9276 },
            WingR1 = { -0.4715, 1.0172, -0.9886 }, WingR2 = { -0.1649, 0.1862, 0.1086 }, WingR3 = { 1.9964, 0.1401, -2.0158 },
            WingRF1 = { 0.0249, -0.3555, -2.0932 }, WingRF2 = { 0.356, -0.1851, -1.646 }, WingRF3 = { 0.7317, -0.0382, -1.4007 },
        },
        LIFT = {
            Chest = { 0.03, 0, 0 }, FootL = { -0.0546, 0, 0 }, FootR = { -0.0546, 0, 0 }, Hips = { -0.3, 0, 0, 0, -0.01, 0 }, LegL1 = { 0.3546, 0, 0 },
            LegL2 = { -0.0577, 0, 0 }, LegL3 = { 0.0577, 0, 0 }, LegR1 = { 0.3546, 0, 0 }, LegR2 = { -0.0577, 0, 0 }, LegR3 = { 0.0577, 0, 0 },
            Neck1 = { 0.18, 0, 0 }, Neck2 = { 0.12, 0, 0 }, Tail1 = { 0.12, 0, 0 }, Tail2 = { 0.05, 0, 0 }, WingL1 = { -1.0356, 0.1791, 0.6779 },
            WingL2 = { -0.5828, -0.4787, -0.4352 }, WingL3 = { 1.2293, -0.6101, -0.5634 }, WingLF1 = { -0.4518, 1.2078, 0.0382 },
            WingLF2 = { -0.6032, 0.8858, 0.0827 }, WingLF3 = { -0.9049, 0.7685, 0.0829 }, WingR1 = { -1.0356, -0.1791, -0.6779 },
            WingR2 = { -0.5828, 0.4787, 0.4352 }, WingR3 = { -1.1801, -2.8489, 0.4289 }, WingRF1 = { 0.3392, 0.153, -2.6518 },
            WingRF2 = { 0.5806, -0.0727, -2.5732 }, WingRF3 = { 0.8082, -0.0145, -2.3402 },
        },
        FLY = {
            FootL = { -0.55, 0, 0 }, FootR = { -0.55, 0, 0 }, Head = { 0.44, 0, 0 }, Hips = { -0.32, 0, 0 }, LegL1 = { -1.05, 0, 0 }, LegL2 = { 1, 0, 0 },
            LegL3 = { -0.55, 0, 0 }, LegR1 = { -1.05, 0, 0 }, LegR2 = { 1, 0, 0 }, LegR3 = { -0.55, 0, 0 }, Neck1 = { -0.28, 0, 0 }, Neck2 = { -0.08, 0, 0 },
            Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.1, 0, 0 }, Tail2 = { -0.04, 0, 0 }, Tail3 = { 0.02, 0, 0 }, Tail4 = { 0.03, 0, 0 },
        },
        BEAT_UP = {
            FootL = { -0.55, 0, 0 }, FootR = { -0.55, 0, 0 }, Head = { 0.44, 0, 0 }, Hips = { -0.32, 0, 0 }, LegL1 = { -1.05, 0, 0 }, LegL2 = { 1, 0, 0 },
            LegL3 = { -0.55, 0, 0 }, LegR1 = { -1.05, 0, 0 }, LegR2 = { 1, 0, 0 }, LegR3 = { -0.55, 0, 0 }, Neck1 = { -0.28, 0, 0 }, Neck2 = { -0.08, 0, 0 },
            Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.1, 0, 0 }, Tail2 = { -0.04, 0, 0 }, Tail3 = { 0.02, 0, 0 }, Tail4 = { 0.03, 0, 0 },
            WingL1 = { 0, -0.08, -0.38 }, WingR1 = { 0, 0.08, 0.38 },
        },
        BEAT_DOWN = {
            FootL = { -0.55, 0, 0 }, FootR = { -0.55, 0, 0 }, Head = { 0.44, 0, 0 }, Hips = { -0.32, 0, 0 }, LegL1 = { -1.05, 0, 0 }, LegL2 = { 1, 0, 0 },
            LegL3 = { -0.55, 0, 0 }, LegR1 = { -1.05, 0, 0 }, LegR2 = { 1, 0, 0 }, LegR3 = { -0.55, 0, 0 }, Neck1 = { -0.28, 0, 0 }, Neck2 = { -0.08, 0, 0 },
            Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.1, 0, 0 }, Tail2 = { -0.04, 0, 0 }, Tail3 = { 0.02, 0, 0 }, Tail4 = { 0.03, 0, 0 }, WingL1 = { 0, 0.1, 0.6 },
            WingL3 = { 0, 0.25, 0 }, WingR1 = { 0, -0.1, -0.6 }, WingR3 = { 0, -0.25, 0 },
        },
        REAR = {
            Body = { 0.08, 0, 0 }, Chest = { 0.05, 0, 0 }, FootL = { 0.0691, 0, 0 }, FootR = { 0.0691, 0, 0 }, Head = { -0.07, 0, 0 },
            Hips = { 0.12, 0, 0, 0, 0.02, 0 }, LegL1 = { -0.1891, 0, 0 }, LegL2 = { 0.1359, 0, 0 }, LegL3 = { -0.1359, 0, 0 }, LegR1 = { -0.1891, 0, 0 },
            LegR2 = { 0.1359, 0, 0 }, LegR3 = { -0.1359, 0, 0 }, Neck1 = { 0.05, 0, 0 }, Neck2 = { 0.1, 0, 0 }, Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.12, 0, 0 },
            Tail2 = { -0.06, 0, 0 }, WingL1 = { 0, 0.12, -0.32 }, WingLF1 = { 0, 0.12, 0 }, WingLF3 = { 0, -0.12, 0 }, WingR1 = { 0, -0.12, 0.32 },
            WingRF1 = { 0, -0.12, 0 }, WingRF3 = { 0, 0.12, 0 },
        },
        SLAM = {
            FootL = { -0.174, 0, 0 }, FootR = { -0.174, 0, 0 }, Head = { 0.08, 0, 0 }, Hips = { -0.6, 0, 0, 0, -0.05, 0 }, LegL1 = { 0.774, 0, 0 },
            LegL2 = { -0.2565, 0, 0 }, LegL3 = { 0.2565, 0, 0 }, LegR1 = { 0.774, 0, 0 }, LegR2 = { -0.2565, 0, 0 }, LegR3 = { 0.2565, 0, 0 },
            Neck1 = { 0.2, 0, 0 }, Neck2 = { 0.16, 0, 0 }, Neck3 = { 0.04, 0, 0 }, Tail1 = { 0.3, 0, 0 }, Tail2 = { 0.16, 0, 0 }, Tail3 = { 0.06, 0, 0 },
            WingL1 = { -0.4497, -0.9314, 0.8112 }, WingL2 = { -0.215, -0.2341, -0.1447 }, WingL3 = { 0.9028, -0.2029, -1.2604 },
            WingLF1 = { -0.6162, 0.6584, -0.4194 }, WingLF2 = { -0.7861, 0.57, -0.4313 }, WingLF3 = { -0.7962, 0.5665, -0.4334 },
            WingR1 = { -0.4497, 0.9314, -0.8112 }, WingR2 = { -0.215, 0.2341, 0.1447 }, WingR3 = { 2.033, 0.0027, -2.0118 },
            WingRF1 = { 0.7304, -0.2459, -2.0381 }, WingRF2 = { 0.8964, -0.2154, -1.89 }, WingRF3 = { 0.905, -0.2115, -1.8806 },
        },
        MANTLE = {
            Chest = { 0.05, 0, 0 }, FootL = { -0.1222, 0, 0 }, FootR = { -0.1222, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.03, 0 },
            LegL1 = { 0.6722, 0, 0 }, LegL2 = { -0.1529, 0, 0 }, LegL3 = { 0.1529, 0, 0 }, LegR1 = { 0.6722, 0, 0 }, LegR2 = { -0.1529, 0, 0 },
            LegR3 = { 0.1529, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, 0, 0 }, Tail2 = { 0.12, 0, 0 }, Tail3 = { 0.04, 0, 0 },
            WingL1 = { -0.4715, -1.0172, 0.9886 }, WingL2 = { -0.1649, -0.1862, -0.1086 }, WingL3 = { 0.8366, -0.2634, -1.3873 },
            WingLF1 = { -0.15, 0.7965, -1.0964 }, WingLF2 = { -0.5021, 0.9024, -1.1025 }, WingLF3 = { -0.8079, 0.8102, -0.9276 },
            WingR1 = { -0.4715, 1.0172, -0.9886 }, WingR2 = { -0.1649, 0.1862, 0.1086 }, WingR3 = { 1.9964, 0.1401, -2.0158 },
            WingRF1 = { 0.3465, -0.2855, -1.777 }, WingRF2 = { 0.5189, -0.0954, -1.4721 }, WingRF3 = { 0.7317, -0.0382, -1.4007 },
        },
        WALK = { -- eight keys round one cycle of its prowl (thunderclaw_drake.py's walk_pose at k/8 of it)
            {
                Chest = { 0.05, 0, 0 }, FootL = { 0.0301, 0, 0 }, FootR = { -0.1894, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.018, 0 },
                LegL1 = { 0.5199, 0, 0 }, LegL2 = { -0.1199, 0, 0 }, LegL3 = { 0.1199, 0, 0 }, LegR1 = { 0.7394, 0, 0 }, LegR2 = { -0.0039, 0, 0 },
                LegR3 = { 0.0039, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, 0.0387, 0 }, Tail2 = { 0.12, 0.0591, 0 },
                Tail3 = { 0.04, 0.0518, 0 }, Tail4 = { 0, 0.0201, 0 }, WingL1 = { -0.4406, -1.2021, 0.8417 }, WingL2 = { -0.0037, -0.0046, -0.0022 },
                WingL3 = { 0.8639, -0.252, -1.2772 }, WingLF1 = { 0.3583, 0.8291, -1.2267 }, WingLF2 = { -0.181, 0.9763, -1.156 },
                WingLF3 = { -0.8312, 0.8707, -0.8325 }, WingR1 = { -0.4806, 0.9587, -1.1413 }, WingR2 = { -0.1976, 0.2179, 0.132 },
                WingR3 = { 1.9513, 0.2717, -2.0484 }, WingRF1 = { 0.1154, -0.3591, -2.0083 }, WingRF2 = { 0.4301, -0.1633, -1.5685 },
                WingRF3 = { 0.7933, 0.0095, -1.3374 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.1166, 0, 0.0025 }, FootR = { -0.1906, 0, 0.0021 }, Head = { 0.02, -0.0212, 0 },
                Hips = { -0.55, 0, 0.0212, 0, -0.03, 0 }, LegL1 = { 0.6664, -0.0134, -0.0191 }, LegL2 = { -0.3799, 0, 0 }, LegL3 = { 0.3799, 0, 0 },
                LegR1 = { 0.7405, -0.0147, -0.0177 }, LegR2 = { -0.0934, 0, 0 }, LegR3 = { 0.0934, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                Tail1 = { 0.26, 0.0598, 0 }, Tail2 = { 0.12, 0.049, 0 }, Tail3 = { 0.04, 0.0152, 0 }, Tail4 = { 0, -0.0258, 0 },
                WingL1 = { -0.5048, -1.0999, 0.8293 }, WingL2 = { -0.0937, -0.1113, -0.0596 }, WingL3 = { 0.8778, -0.2268, -1.3105 },
                WingLF1 = { 0.346, 0.7609, -1.2057 }, WingLF2 = { -0.1496, 0.9097, -1.1915 }, WingLF3 = { -0.765, 0.8294, -0.9176 },
                WingR1 = { -0.5761, 0.8027, -1.0519 }, WingR2 = { -0.3838, 0.368, 0.2735 }, WingR3 = { 2.0009, 0.1812, -1.9879 },
                WingRF1 = { 0.0312, -0.4175, -2.0935 }, WingRF2 = { 0.3668, -0.2437, -1.6254 }, WingRF3 = { 0.7408, -0.0853, -1.3603 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.2758, 0, 0.0038 }, FootR = { -0.1426, 0, 0.003 }, Head = { 0.02, -0.03, 0 },
                Hips = { -0.55, 0, 0.03, 0, -0.042, 0 }, LegL1 = { 0.8255, -0.0231, -0.024 }, LegL2 = { -0.4843, 0, 0 }, LegL3 = { 0.4843, 0, 0 },
                LegR1 = { 0.6924, -0.0196, -0.0261 }, LegR2 = { -0.2075, 0, 0 }, LegR3 = { 0.2075, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                Tail1 = { 0.26, 0.0459, 0 }, Tail2 = { 0.12, 0.0102, 0 }, Tail3 = { 0.04, -0.0303, 0 }, Tail4 = { 0, -0.0565, 0 },
                WingL1 = { -0.5401, -0.9596, 0.9207 }, WingL2 = { -0.2209, -0.2395, -0.149 }, WingL3 = { 0.8598, -0.2328, -1.3869 },
                WingLF1 = { 0.3016, 0.7021, -1.1816 }, WingLF2 = { -0.1643, 0.8493, -1.2093 }, WingLF3 = { -0.7482, 0.7859, -0.9804 },
                WingR1 = { -0.57, 0.7743, -0.9329 }, WingR2 = { -0.425, 0.3948, 0.3063 }, WingR3 = { 2.0607, 0.0538, -1.9512 },
                WingRF1 = { -0.0567, -0.4289, -2.1811 }, WingRF2 = { 0.296, -0.2813, -1.6991 }, WingRF3 = { 0.6832, -0.1465, -1.4126 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.2986, 0, 0.0025 }, FootR = { -0.0288, 0, 0.0021 }, Head = { 0.02, -0.0212, 0 },
                Hips = { -0.55, 0, 0.0212, 0, -0.03, 0 }, LegL1 = { 0.8485, -0.0166, -0.0164 }, LegL2 = { -0.2976, 0, 0 }, LegL3 = { 0.2976, 0, 0 },
                LegR1 = { 0.5787, -0.0117, -0.0199 }, LegR2 = { -0.1733, 0, 0 }, LegR3 = { 0.1733, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                Tail1 = { 0.26, 0.0051, 0 }, Tail2 = { 0.12, -0.0346, 0 }, Tail3 = { 0.04, -0.058, 0 }, Tail4 = { 0, -0.0542, 0 },
                WingL1 = { -0.5269, -0.9323, 1.0527 }, WingL2 = { -0.2334, -0.2507, -0.1582 }, WingL3 = { 0.7928, -0.2971, -1.4694 },
                WingLF1 = { 0.2186, 0.7152, -1.1682 }, WingLF2 = { -0.2556, 0.8564, -1.1865 }, WingLF3 = { -0.8385, 0.7835, -0.9572 },
                WingR1 = { -0.5181, 0.9615, -0.8404 }, WingR2 = { -0.2336, 0.2509, 0.1583 }, WingR3 = { 2.0607, 0.0043, -1.9727 },
                WingRF1 = { -0.0683, -0.3828, -2.1847 }, WingRF2 = { 0.2807, -0.2392, -1.7188 }, WingRF3 = { 0.6685, -0.1148, -1.4465 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.1894, 0, 0 }, FootR = { 0.0301, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.018, 0 },
                LegL1 = { 0.7394, 0, 0 }, LegL2 = { -0.0039, 0, 0 }, LegL3 = { 0.0039, 0, 0 }, LegR1 = { 0.5199, 0, 0 }, LegR2 = { -0.1199, 0, 0 },
                LegR3 = { 0.1199, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, -0.0387, 0 }, Tail2 = { 0.12, -0.0591, 0 },
                Tail3 = { 0.04, -0.0518, 0 }, Tail4 = { 0, -0.0201, 0 }, WingL1 = { -0.4806, -0.9587, 1.1413 }, WingL2 = { -0.1976, -0.2179, -0.132 },
                WingL3 = { 0.7504, -0.343, -1.502 }, WingLF1 = { 0.1668, 0.7495, -1.1609 }, WingLF2 = { -0.3269, 0.8842, -1.1542 },
                WingLF3 = { -0.9179, 0.7952, -0.9108 }, WingR1 = { -0.4406, 1.2021, -0.8417 }, WingR2 = { -0.0037, 0.0046, 0.0022 },
                WingR3 = { 1.9987, 0.0384, -2.0494 }, WingRF1 = { -0.0156, -0.2647, -2.119 }, WingRF2 = { 0.3156, -0.1072, -1.6994 },
                WingRF3 = { 0.698, 0.0144, -1.4788 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.1906, 0, -0.0021 }, FootR = { -0.1166, 0, -0.0025 }, Head = { 0.02, 0.0212, 0 },
                Hips = { -0.55, 0, -0.0212, 0, -0.03, 0 }, LegL1 = { 0.7405, 0.0147, 0.0177 }, LegL2 = { -0.0934, 0, 0 }, LegL3 = { 0.0934, 0, 0 },
                LegR1 = { 0.6664, 0.0134, 0.0191 }, LegR2 = { -0.3799, 0, 0 }, LegR3 = { 0.3799, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                Tail1 = { 0.26, -0.0598, 0 }, Tail2 = { 0.12, -0.049, 0 }, Tail3 = { 0.04, -0.0152, 0 }, Tail4 = { 0, 0.0258, 0 },
                WingL1 = { -0.5761, -0.8027, 1.0519 }, WingL2 = { -0.3838, -0.368, -0.2735 }, WingL3 = { 0.8326, -0.2543, -1.4376 },
                WingLF1 = { 0.2642, 0.6854, -1.1717 }, WingLF2 = { -0.1946, 0.831, -1.2102 }, WingLF3 = { -0.7689, 0.7709, -0.9952 },
                WingR1 = { -0.5048, 1.0999, -0.8293 }, WingR2 = { -0.0937, 0.1113, 0.0596 }, WingR3 = { 2.0187, 0.0571, -2.0128 },
                WingRF1 = { -0.0209, -0.3332, -2.1328 }, WingRF2 = { 0.3158, -0.1762, -1.6892 }, WingRF3 = { 0.6975, -0.0458, -1.4435 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.1426, 0, -0.003 }, FootR = { -0.2758, 0, -0.0038 }, Head = { 0.02, 0.03, 0 },
                Hips = { -0.55, 0, -0.03, 0, -0.042, 0 }, LegL1 = { 0.6924, 0.0196, 0.0261 }, LegL2 = { -0.2075, 0, 0 }, LegL3 = { 0.2075, 0, 0 },
                LegR1 = { 0.8255, 0.0231, 0.024 }, LegR2 = { -0.4843, 0, 0 }, LegR3 = { 0.4843, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                Tail1 = { 0.26, -0.0459, 0 }, Tail2 = { 0.12, -0.0102, 0 }, Tail3 = { 0.04, 0.0303, 0 }, Tail4 = { 0, 0.0565, 0 },
                WingL1 = { -0.57, -0.7743, 0.9329 }, WingL2 = { -0.425, -0.3948, -0.3063 }, WingL3 = { 0.9187, -0.1694, -1.3335 },
                WingLF1 = { 0.3626, 0.6605, -1.1816 }, WingLF2 = { -0.0835, 0.8119, -1.2363 }, WingLF3 = { -0.6528, 0.7645, -1.0302 },
                WingR1 = { -0.5401, 0.9596, -0.9207 }, WingR2 = { -0.2209, 0.2395, 0.149 }, WingR3 = { 2.0158, 0.1275, -1.9878 },
                WingRF1 = { 0.0027, -0.3969, -2.1188 }, WingRF2 = { 0.3414, -0.232, -1.6549 }, WingRF3 = { 0.7198, -0.085, -1.3914 },
            },
            {
                Chest = { 0.05, 0, 0 }, FootL = { -0.0288, 0, -0.0021 }, FootR = { -0.2986, 0, -0.0025 }, Head = { 0.02, 0.0212, 0 },
                Hips = { -0.55, 0, -0.0212, 0, -0.03, 0 }, LegL1 = { 0.5787, 0.0117, 0.0199 }, LegL2 = { -0.1733, 0, 0 }, LegL3 = { 0.1733, 0, 0 },
                LegR1 = { 0.8485, 0.0166, 0.0164 }, LegR2 = { -0.2976, 0, 0 }, LegR3 = { 0.2976, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                Tail1 = { 0.26, -0.0051, 0 }, Tail2 = { 0.12, 0.0346, 0 }, Tail3 = { 0.04, 0.058, 0 }, Tail4 = { 0, 0.0542, 0 },
                WingL1 = { -0.5181, -0.9615, 0.8404 }, WingL2 = { -0.2336, -0.2509, -0.1583 }, WingL3 = { 0.9273, -0.1682, -1.2787 },
                WingLF1 = { 0.3897, 0.7028, -1.1996 }, WingLF2 = { -0.0744, 0.8561, -1.2273 }, WingLF3 = { -0.6658, 0.7981, -0.989 },
                WingR1 = { -0.5269, 0.9323, -1.0527 }, WingR2 = { -0.2334, 0.2507, 0.1582 }, WingR3 = { 1.9754, 0.2259, -2.0162 },
                WingRF1 = { 0.0722, -0.3913, -2.0514 }, WingRF2 = { 0.3976, -0.2065, -1.5967 }, WingRF3 = { 0.7659, -0.0406, -1.3478 },
            },
        },
        BONES = {
            "Hips", "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "LidUL", "LidLL", "LidUR", "LidLR",
            "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "LegL1", "LegL2", "LegL3", "FootL", "LegR1", "LegR2", "LegR3", "FootR",
            "WingL1", "WingL2", "WingL3", "WingLF1", "WingLF2", "WingLF3", "WingR1", "WingR2", "WingR3", "WingRF1", "WingRF2", "WingRF3",
        },
        GOLD = Color3.fromRGB(255, 235, 100),
        WHITE = Color3.fromRGB(255, 250, 200),
        VIOLET = Color3.fromRGB(170, 150, 255),
    }
    TW.CARRIER = { Head = TW.HEAD_AT, WingL3 = TW.WRIST_AT.L, WingR3 = TW.WRIST_AT.R } -- the rest heads of the bones carrying them
    for _, tag in { "L", "R" } do
        for k = 1, 3 do
            TW.CARRIER["Wing" .. tag .. "F" .. k] = TW.WRIST_AT[tag] -- (every finger springs from its wrist)
        end
    end

    function TW.cf(a, u)
        if not a then
            return CFrame.identity
        end
        local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
        return move * CFrame.Angles(a[1], a[2], a[3])
    end

    -- Where each glowing point sits on the bone that carries it, worked out once while it is still at rest (a skinned piece's own CFrame stays where
    -- it was bound, so the points ride on the bones).
    function TW.initTips(rig, s)
        s.tips = {}
        local function add(key, boneName, rest)
            local bone = rig.points[boneName]
            if not bone then
                return
            end
            local head = bone.TransformedWorldCFrame
            local world = head.Position + rig.rootPart.CFrame:VectorToWorldSpace((rest - TW.CARRIER[boneName]) * rig.meters)
            s.tips[key] = { bone = bone, offset = head:PointToObjectSpace(world) }
        end
        add("Arc", "Head", TW.ARC_AT)
        for _, tag in { "L", "R" } do
            add("Horn" .. tag, "Head", TW.HORN_AT[tag])
            add("Hook" .. tag, "Wing" .. tag .. "3", TW.HOOK_AT[tag])
            for k = 1, 3 do
                add("Spur" .. tag .. k, "Wing" .. tag .. "F" .. k, TW.SPUR_AT[tag][k])
            end
        end
        -- its glow: a light where the arc is, and the sparks its hooks strike, riding on their bones
        local arc = s.tips.Arc
        if arc then
            local at = Instance.new("Attachment")
            at.Name = "ArcLight"
            at.CFrame = CFrame.new(arc.offset)
            at.Parent = arc.bone
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = TW.GOLD
            light.Range = 5 * rig.unit
            light.Brightness = 1.2
            light.Shadows = false
            light.Parent = at
            rig.light = light
        end
        s.sparks = {}
        for _, tag in { "L", "R" } do
            local hook = s.tips["Hook" .. tag]
            if hook then
                local at = Instance.new("Attachment")
                at.Name = "HookSparks"
                at.CFrame = CFrame.new(hook.offset)
                at.Parent = hook.bone
                local sparks = Instance.new("ParticleEmitter")
                sparks.Name = "Sparks"
                sparks.Texture = SPARKLE
                sparks.Enabled = false
                sparks.Lifetime = NumberRange.new(0.18, 0.35)
                sparks.Speed = NumberRange.new(0.8 * rig.unit, 1.8 * rig.unit)
                sparks.SpreadAngle = Vector2.new(70, 70)
                sparks.Acceleration = Vector3.new(0, -4 * rig.unit, 0)
                sparks.Size = NumberSequence.new(0.06 * rig.unit, 0)
                sparks.Color = ColorSequence.new(TW.WHITE, TW.GOLD)
                sparks.LightEmission = 1
                sparks.LightInfluence = 0
                sparks.Parent = at
                s.sparks[tag] = sparks
            end
        end
    end

    function TW.tipAt(s, key)
        local tip = s.tips and s.tips[key]
        return if tip then tip.bone.TransformedWorldCFrame:PointToWorldSpace(tip.offset) else nil
    end

    -- a run of lightning from a to b: kinked sideways at every step, most in the middle
    function TW.jag(a, b, steps, amp)
        local dir = b - a
        local side = dir:Cross(Vector3.yAxis)
        if side.Magnitude < 1e-4 then
            side = dir:Cross(Vector3.xAxis)
        end
        side = side.Unit
        local other = dir.Unit:Cross(side)
        local points = { a }
        for i = 1, steps - 1 do
            local t = i / steps
            local reach = amp * math.sin(math.pi * t) ^ 0.5
            table.insert(points, a + dir * t + side * (math.random() * 2 - 1) * reach + other * (math.random() * 2 - 1) * reach * 0.6)
        end
        table.insert(points, b)
        return points
    end

    -- the run drawn in Neon, flashing on after `delay`, flickering, gone after `life`
    function TW.zap(parent, points, width, color, life, delay)
        for i = 1, #points - 1 do
            local a, b = points[i], points[i + 1]
            local length = (b - a).Magnitude
            if length > 1e-3 then
                local part = Instance.new("Part")
                part.Anchored = true
                part.CanCollide = false
                part.CanTouch = false
                part.CanQuery = false
                part.CastShadow = false
                part.Material = Enum.Material.Neon
                part.Color = color
                part.Size = Vector3.new(width, width, length + width * 0.5)
                part.CFrame = CFrame.lookAt((a + b) / 2, b)
                part.Transparency = 1
                part.Parent = parent
                task.delay(delay, function()
                    if part.Parent then
                        part.Transparency = 0
                    end
                end)
                tweenAfter(delay + life * 0.35, part, TweenInfo.new(life * 0.65, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
                Debris:AddItem(part, delay + life + 0.1)
            end
        end
    end

    function TW.effectsFolder(rig)
        local folder = Instance.new("Folder")
        folder.Name = "PetSpecial"
        folder.Parent = rig.model.Parent or workspace
        Debris:AddItem(folder, 2)
        return folder
    end

    function TW.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- a crackle leaping between two of its points
    function TW.crackle(rig, a, b)
        if not a or not b or TW.reduced() then
            return
        end
        local u = rig.unit
        local folder = TW.effectsFolder(rig)
        local steps = math.clamp(math.floor((b - a).Magnitude / (0.12 * u)) + 2, 3, 9)
        TW.zap(folder, TW.jag(a, b, steps, 0.06 * u), 0.025 * u, TW.WHITE, 0.16, 0)
        TW.zap(folder, TW.jag(a, b, steps, 0.08 * u), 0.012 * u, TW.GOLD, 0.12, 0.06)
    end

    -- Called Down, the bolt: out of the sky onto the arc between its horns, a white core in a gold sheath, two forks, a flash
    function TW.bolt(rig, s)
        local target = TW.tipAt(s, "Arc")
        if not target then
            return
        end
        local u = rig.unit
        local folder = TW.effectsFolder(rig)
        local from = target + Vector3.new((math.random() - 0.5) * 3 * u, 16 * u, (math.random() - 0.5) * 3 * u)
        local points = TW.jag(from, target, 11, 0.9 * u)
        TW.zap(folder, points, 0.09 * u, TW.GOLD, 0.35, 0)
        TW.zap(folder, points, 0.04 * u, Color3.new(1, 1, 1), 0.3, 0)
        if not TW.reduced() then
            for _, k in { 4, 7 } do
                local fork = points[k] + Vector3.new((math.random() - 0.5) * 3 * u, -2.2 * u, (math.random() - 0.5) * 3 * u)
                TW.zap(folder, TW.jag(points[k], fork, 5, 0.3 * u), 0.035 * u, TW.GOLD, 0.22, 0.03)
            end
            for _, tag in { "L", "R" } do -- and on into its horns
                TW.zap(folder, TW.jag(target, TW.tipAt(s, "Horn" .. tag) or target, 3, 0.03 * u), 0.03 * u, Color3.new(1, 1, 1), 0.4, 0.02)
            end
        end
        local flash = Instance.new("Part")
        flash.Anchored = true
        flash.CanCollide = false
        flash.CanTouch = false
        flash.CanQuery = false
        flash.Transparency = 1
        flash.Size = Vector3.one * 0.05
        flash.CFrame = CFrame.new(target)
        flash.Parent = folder
        local light = Instance.new("PointLight")
        light.Color = TW.WHITE
        light.Range = 10 * u
        light.Brightness = 2.5 -- a flash, not the whole scene washed white (brighter and wider, it was: seen in Play)
        light.Shadows = false
        light.Parent = flash
        TweenService:Create(light, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
    end

    local function animateThunderclawDrake(rig, s, moving, fly, nova)
        if not s.tips then
            TW.initTips(rig, s) -- at rest, before any pose
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > TW.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

        -- the special, Called Down: it lands if it is flying; rears (through LIFT, wings opening) to 0.24; holds, head to the sky, and the bolt comes
        -- down onto its horns (0.27); strikes down (through LIFT) to its wrists from 0.38, landing at 0.42 (Blasts.CalledDown); holds; settles by 0.95
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local active = if rig.nova then 1 else 0
        s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 2.5)
        local air = s.air
        local rise = smoothstep(0.02, 0.24, progress) * active
        local strike = smoothstep(0.38, 0.42, progress) * active
        local settle = smoothstep(0.7, 0.95, progress) * active
        local impact = if active == 1 and progress > 0.42 then math.exp(-(progress - 0.42) * 16) else 0
        if active == 1 and progress >= 0.27 and s.bolted ~= rig.nova.start then
            s.bolted = rig.nova.start
            TW.bolt(rig, s)
        end

        -- it stands on the ground, or keeps to its owner's height on the wing
        local drop = dropToGround(rig, s, t, u, air, TW.SOLE)

        -- idle business, when it is still: it mantles (opens its folded hands part way, a crackle leaping between its spurs), or watches you
        local still = (1 - moving) * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
        s.nextIdle = s.nextIdle or t + 5
        if t >= s.nextIdle and still > 0.9 then
            s.idleAt, s.idleKind = t, if math.random() < 0.55 then "mantle" else "watch"
            s.nextIdle = t + 7 + math.random() * 7
        end
        local idle = if s.idleAt then (t - s.idleAt) / 2.4 else 1
        local env = if idle < 1 then math.sin(math.pi * idle) else 0
        local mantle = (if s.idleKind == "mantle" then smoothstep(0, 1, env) else 0) * still
        if s.idleKind == "mantle" and idle >= 0.35 and s.crackled ~= s.idleAt then
            s.crackled = s.idleAt
            local tag = if math.random() < 0.5 then "L" else "R"
            local k = math.random(1, 2)
            TW.crackle(rig, TW.tipAt(s, "Spur" .. tag .. k), TW.tipAt(s, "Spur" .. tag .. (k + 1)))
        end
        local watch = if s.idleKind == "watch" then env else 0

        -- its walk: eight keys round a cycle, a wrist planting with the opposite foot; each hook strikes sparks as it plants
        local walking = moving * (1 - smoothstep(0.05, 0.3, air))
        local before = s.step or 0
        s.step = before + dt * (TW.STEP_RATE + TW.STEP_RUN * moving) * walking
        local cycle = (s.step / (2 * math.pi)) % 1 * 8
        local key = math.floor(cycle)
        local frac = cycle - key
        local keyA, keyB = TW.WALK[key + 1], TW.WALK[(key + 1) % 8 + 1]
        if walking > 0.4 and s.sparks then
            local was, now = (before / (2 * math.pi)) % 1, (s.step / (2 * math.pi)) % 1
            if now < was and s.sparks.L then -- the left wrist plants at the cycle's start
                s.sparks.L:Emit(4)
            end
            if was < 0.5 and now >= 0.5 and s.sparks.R then -- the right, half a cycle on
                s.sparks.R:Emit(4)
            end
        end

        -- on the wing: its wings beat once open; it rises off the ground as they open
        s.beat = (s.beat or 0) + dt * (4.6 + 1.4 * fly) * air
        local down = 0.5 - 0.5 * math.cos(s.beat) -- 0 at the top of the stroke, 1 at the bottom
        local beating = smoothstep(TW.BEAT_IN, 1, air)
        local hover = TW.HOVER * smoothstep(0.35, 0.9, air) + 0.025 * beating * (0.5 - down)

        -- its gaze: slow, a sentinel's; it settles on you and holds; and the tail's slow sway
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 3 + math.random() * 4
            s.atYou = math.random() < 0.5
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.5
        end
        local calm = (1 - 0.6 * walking) * (1 - smoothstep(0.02, 0.1, progress) * active)
        local wantYaw = math.clamp((if s.atYou or watch > 0 then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw) * (1 + watch), -1, 1) * calm
        local wantPitch = math.clamp(if s.atYou or watch > 0 then toYou.Y * 0.8 else s.gazePitch, -0.5, 0.5) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
        local breath = math.sin(t * 1.25)

        for _, name in TW.BONES do
            if string.sub(name, 1, 3) ~= "Lid" then
                -- on the ground: the prowl, stepping as it goes, mantling now and then
                local ground = TW.cf(TW.PROWL[name], u):Lerp(TW.cf(keyA[name], u):Lerp(TW.cf(keyB[name], u), frac), walking)
                ground = ground:Lerp(TW.cf(TW.MANTLE[name], u), mantle)
                -- on the wing, and between: lifted clear (LIFT) first, then open
                local wing = TW.cf(TW.FLY[name], u):Lerp(TW.cf(TW.BEAT_UP[name], u):Lerp(TW.cf(TW.BEAT_DOWN[name], u), down), beating)
                local cf = if air < 0.5 then ground:Lerp(TW.cf(TW.LIFT[name], u), air * 2) else TW.cf(TW.LIFT[name], u):Lerp(wing, air * 2 - 1)
                -- the special over all of it: up through LIFT to the rear, down through LIFT to the slam, and back
                if active == 1 then
                    local lift, rear, slam = TW.cf(TW.LIFT[name], u), TW.cf(TW.REAR[name], u), TW.cf(TW.SLAM[name], u)
                    if strike > 0 then
                        cf = if strike < 0.5 then rear:Lerp(lift, strike * 2) else lift:Lerp(slam, strike * 2 - 1)
                        cf = cf:Lerp(ground, settle)
                    elseif rise > 0 then
                        cf = if rise < 0.5 then cf:Lerp(lift, rise * 2) else lift:Lerp(rear, rise * 2 - 1)
                    end
                end
                -- over the stance: its breath, its gaze, its tail's sway
                if name == "Chest" then
                    cf *= CFrame.Angles(0.02 * breath * (1 - air), 0, 0)
                elseif name == "Neck2" or name == "Neck3" then
                    cf *= CFrame.Angles(0.2 * s.pitch, 0.3 * s.yaw, 0)
                elseif name == "Head" then
                    cf *= CFrame.Angles(0.3 * s.pitch, 0.35 * s.yaw, 0.1 * s.yaw)
                elseif string.sub(name, 1, 4) == "Tail" then
                    local k = tonumber(string.sub(name, 5)) or 1
                    cf *= CFrame.Angles(0, (0.02 + 0.006 * k) * math.sin(t * 0.8 - 0.55 * k) * (1 - walking), 0)
                end
                if name == "Hips" then
                    cf = CFrame.new(0, (hover - 0.04 * impact) * u - drop, 0) * cf
                end
                pose(m[name], cf)
            end
        end

        -- the arc between its horns: crackling on and off; blazing in the special
        local arc = rig.parts.Arc
        if arc then
            s.nextFlicker = s.nextFlicker or 0
            if t >= s.nextFlicker then
                s.nextFlicker = t + 0.04 + math.random() * 0.06
                s.arcShow = if math.random() < 0.18 then 1 else math.random() * 0.55
            end
            arc.Transparency = if active == 1 and progress > 0.25 and progress < 0.75 then 0 else s.arcShow or 0
        end

        -- the eyes: a slow blink now and then; narrowed as the bolt strikes and as it slams down
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.28
            if a >= 1 then
                s.nextBlink = t + 3.5 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local narrow = 0.45 * smoothstep(0.25, 0.3, progress) * (1 - smoothstep(0.6, 0.8, progress)) * active
        local close = math.max(blink, narrow)
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(TW.LID_HINGE[side], -TW.BLINK_UPPER * close))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(TW.LID_HINGE[side], TW.BLINK_LOWER * close))
        end
    end

    -- It has slammed down onto its wrists (animateThunderclawDrake): the bolt it took bursts out of it along the ground, a ring of light racing out and
    -- lightning running out across the ground from where its hooks struck, sparks thrown up, a flash.
    function Blasts.CalledDown(rig, fx)
        local u, metre = rig.unit, rig.meters
        local s = rig.state
        local hooks = {}
        for _, tag in { "L", "R" } do
            local at = TW.tipAt(s, "Hook" .. tag)
            if at then
                table.insert(hooks, at)
            end
        end
        local centre = if #hooks == 2 then (hooks[1] + hooks[2]) / 2 else rig.rootPart.Position
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(centre + Vector3.new(0, 1 * u, 0), Vector3.new(0, -12 * u, 0), params)
        local groundY = if hit then hit.Position.Y else centre.Y - 0.1 * metre
        local folder = TW.effectsFolder(rig)
        local reduced = TW.reduced()

        local ripple = fx.neon(Vector3.new(0.03 * u, 0.5 * u, 0.5 * u), CFrame.new(centre.X, groundY + 0.04 * u, centre.Z) * CFrame.Angles(0, 0, math.pi / 2), TW.GOLD)
        ripple.Shape = Enum.PartType.Cylinder
        ripple.Transparency = 0.3
        TweenService:Create(ripple, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02 * u, 5 * u, 5 * u), Transparency = 1 }):Play()

        local count = if reduced then 5 else 9
        for k = 1, count do
            local angle = (k - 1) / count * 2 * math.pi + (math.random() - 0.5) * 0.4
            local out = fx.facing:VectorToWorldSpace(Vector3.new(math.sin(angle), 0, -math.cos(angle)))
            local from = hooks[(k % math.max(#hooks, 1)) + 1] or centre
            local points = { Vector3.new(from.X, groundY + 0.05 * u, from.Z) }
            local reach = (1.4 + 0.8 * math.random()) * u
            for i = 1, 9 do
                local p = from + out * reach * i / 9 + out:Cross(Vector3.yAxis) * (math.random() - 0.5) * 0.3 * u
                local ground = leopardGroundAt(Vector3.new(p.X, groundY, p.Z), metre)
                table.insert(points, if ground then ground + Vector3.new(0, 0.03 * u, 0) else Vector3.new(p.X, groundY + 0.05 * u, p.Z))
            end
            TW.zap(folder, points, 0.025 * u, TW.WHITE, 0.32, k * 0.012) -- thin and kinked: thicker, they read as pale bands, not lightning (seen in Play)
            TW.zap(folder, points, 0.05 * u, TW.GOLD, 0.26, k * 0.012)
        end

        if not reduced then
            local sparks = Instance.new("ParticleEmitter")
            sparks.Texture = SPARKLE
            sparks.Enabled = false
            sparks.Lifetime = NumberRange.new(0.3, 0.6)
            sparks.Speed = NumberRange.new(1.5 * u, 3.2 * u)
            sparks.SpreadAngle = Vector2.new(60, 60)
            sparks.Acceleration = Vector3.new(0, -5 * u, 0)
            sparks.Size = NumberSequence.new(0.09 * u, 0)
            sparks.Color = ColorSequence.new(TW.WHITE, TW.GOLD)
            sparks.LightEmission = 1
            sparks.LightInfluence = 0
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre.X, groundY + 0.1 * u, centre.Z) * CFrame.Angles(-math.pi / 2, 0, 0), TW.GOLD)
            holder.Transparency = 1
            sparks.Parent = holder
            sparks:Emit(30)
        end

        local light = Instance.new("PointLight")
        light.Color = TW.GOLD
        light.Range = 8 * u
        light.Brightness = 2
        light.Shadows = false
        local lamp = fx.neon(Vector3.one * 0.05, CFrame.new(centre.X, groundY + 0.5 * u, centre.Z), TW.GOLD)
        lamp.Transparency = 1
        light.Parent = lamp
        TweenService:Create(light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
    end

    PetRig.Profiles.ThunderclawDrake = {
        Skinned = true,
        Bones = TW.BONES,
        Points = { "Hips", "Head", "WingL3", "WingR3", "WingLF1", "WingLF2", "WingLF3", "WingRF1", "WingRF2", "WingRF3" },
        GlowColors = {
            ffe864 = Color3.fromRGB(255, 232, 100), -- the gold balls on its horns' and spurs' tips
            fffabe = Color3.fromRGB(255, 250, 190), -- the arc between its horns
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        },
        Effects = {
            Blast = "CalledDown",
            Pulse = "Tips",
            NovaLight = 2,
        },
        Colors = {
            Gold = TW.GOLD,
            Amber = Color3.fromRGB(190, 104, 54),
            Orange = Color3.fromRGB(255, 190, 90),
            Sun = TW.WHITE,
            Ivory = Color3.fromRGB(236, 240, 255),
        },
        Animate = animateThunderclawDrake,
    }
end

-- ---------- The Frostfang Serpent: all of it in one block, so its locals are freed at its end (the main chunk sits at Luau's limit of 200 locals) ----------
do
    -- The Frostfang Serpent (skinned): a frozen-hood king cobra. It rests coiled, its front reared in an S, its great hood of frosted ice spread and
    -- crowned with blades of clear ice; it stares, unblinking (a snake has no lids), its head following you; its tongue flicks; now and then it hisses,
    -- hood flared, mouth open on two glowing crystal fangs that swing down from its palate. Around it, time stops: shards of ice drift off it and hang
    -- still in the air, and now and then it sheds a pane of clear ice that slides off its coil and shatters. It never uncoils: to go anywhere it leans
    -- into a glide, its hood half folded, a ripple running round its coil, frost forming where it passes; on the wing it hovers, coiled. Its special,
    -- The Moment That Matters: it rears, hood flared, fangs out, and strikes; where it bites, a hexagon of stopped time spreads, everything in it hanging
    -- still, and then shatters (Blasts.TheMomentThatMatters).
    local FS = {
        FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOLE = 0.4331, -- metres from the middle of its box down to its coil (frostfang_serpent.py)
        HOVER_UP = 0.28, -- metres it rises on the wing
        RIPPLE = 0.07, -- radians: each coil bone's sway as the ripple runs round its coil (frostfang_serpent.py's RIPPLE, RIPPLE_STEP: checked at
        RIPPLE_STEP = 0.9, -- four phases of it and along the slerps between)
        COILS = 12,
        HEAD_AT = Vector3.new(0, 0.81, -0.17), -- its Head bone's head, metres in its own axes
        BITE_AT = Vector3.new(0, 0.785, -0.304), -- just past the end of its snout
        -- its stances, fitted in Blender (frostfang_serpent.py's pose_tables: its spine laid along a curve, carried along it without twisting) and checked
        -- there in each and along every slerp the game makes (skin against itself, ice against body, fangs and tongue against its jaw, ground)
        GLIDE = {
            Base = { -0.0004, 0, -0.0001 }, Coil1 = { 0.0004, 0, 0.0001 }, Head = { 0.1582, -0.1805, 0.3602 }, HoodL1 = { 0, 0.45, 0 },
            HoodL2 = { 0, 0.3825, 0 }, HoodR1 = { 0, -0.45, 0 }, HoodR2 = { 0, -0.3825, 0 }, Up1 = { 0.0001, 0.0008, 0.0039 }, Up2 = { 0.0586, 0.0421, 0.0011 },
            Up3 = { -0.4547, 0.147, -0.0747 }, Up4 = { -0.3282, 0.172, -0.0175 }, Up5 = { -0.0947, 0.0622, -0.0569 }, Up6 = { 0.2892, -0.0095, -0.0779 },
            Up7 = { 0.4365, -0.0358, 0.0316 },
        },
        HOVER = {
            HoodL1 = { 0, 0.2, 0 }, HoodL2 = { 0, 0.17, 0 }, HoodR1 = { 0, -0.2, 0 }, HoodR2 = { 0, -0.17, 0 },
        },
        REAR = {
            Base = { -0.0004, 0, -0.0001 }, Coil1 = { 0.0004, 0, 0.0001 }, Fangs = { 1.5359, 0, 0 }, Head = { -0.1142, -0.0435, 0.0211 },
            HoodL1 = { 0, -0.25, 0 }, HoodL2 = { 0, -0.2125, 0 }, HoodR1 = { 0, 0.25, 0 }, HoodR2 = { 0, 0.2125, 0 }, Jaw = { -0.62, 0, 0 },
            Up1 = { 0.0001, 0.0008, 0.0039 }, Up2 = { -0.0032, 0.0031, -0.0121 }, Up3 = { 0.004, -0.0056, 0.0809 }, Up4 = { -0.1414, 0.0563, 0.0459 },
            Up5 = { 0.0509, 0.043, -0.1461 }, Up6 = { 0.1458, 0.0148, -0.0478 }, Up7 = { 0.5123, -0.0035, 0.1038 },
        },
        STRIKE = {
            Base = { -0.0004, 0, -0.0001 }, Coil1 = { 0.0004, 0, 0.0001 }, Fangs = { 1.5359, 0, 0 }, Head = { 0.8838, 0.1823, 0.5587 }, HoodL1 = { 0, -0.3, 0 },
            HoodL2 = { 0, -0.255, 0 }, HoodR1 = { 0, 0.3, 0 }, HoodR2 = { 0, 0.255, 0 }, Jaw = { -0.7, 0, 0 }, Up1 = { 0.0001, 0.0008, 0.0039 },
            Up2 = { 0.0665, 0.0407, -0.0123 }, Up3 = { -0.6528, 0.2057, -0.0025 }, Up4 = { -0.6655, 0.3253, 0.0291 }, Up5 = { -0.2564, 0.1942, -0.2569 },
            Up6 = { -0.0526, 0.0489, -0.2818 }, Up7 = { 0.7032, -0.1128, 0.0112 },
        },
        HISS = {
            Fangs = { 1.5359, 0, 0 }, Head = { -0.1, 0, 0 }, HoodL1 = { 0, -0.22, 0 }, HoodL2 = { 0, -0.187, 0 }, HoodR1 = { 0, 0.22, 0 },
            HoodR2 = { 0, 0.187, 0 }, Jaw = { -0.42, 0, 0 }, Up6 = { 0.12, 0, 0 }, Up7 = { 0.12, 0, 0 },
        },
        TONGUE_UP = {
            Tongue = { 0, 0, 0, 0, 0.0075, 0 },
        },
        TONGUE = {
            Tongue = { 0, 0, 0, 0, 0.01, -0.07 },
        },
        BONES = {
            "Base", "Coil1", "Coil2", "Coil3", "Coil4", "Coil5", "Coil6", "Coil7", "Coil8", "Coil9", "Coil10", "Coil11", "Coil12",
            "Up1", "Up2", "Up3", "Up4", "Up5", "Up6", "Up7", "Head", "Jaw", "Fangs", "HoodL1", "HoodL2", "HoodR1", "HoodR2",
        },
        -- where on its coil a pane of ice may peel off: a coil bone, and its body's radius there (metres)
        SHED = { { "Coil2", 0.088 }, { "Coil4", 0.08 }, { "Coil6", 0.071 }, { "Coil8", 0.06 } },
        CORE = Color3.fromRGB(240, 252, 255),
        MAIN = Color3.fromRGB(130, 210, 255),
        DEEP = Color3.fromRGB(60, 120, 210),
        ICE = Color3.fromRGB(176, 226, 255),
    }

    function FS.cf(a, u)
        if not a then
            return CFrame.identity
        end
        local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
        return move * CFrame.Angles(a[1], a[2], a[3])
    end

    function FS.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- The ripple round its coil: each coil bone's own turn the difference from the one before, so each lies at most RIPPLE off its rest.
    function FS.ripple(phase, k)
        local function world(j)
            return if j == 0 then 0 else FS.RIPPLE * math.sin(phase - FS.RIPPLE_STEP * j)
        end
        return world(k) - world(k - 1)
    end

    -- Once, at rest: where the bite lands, carried on its Head bone; its cold light; the stopped-time shards drifting off it and the frost it leaves.
    function FS.init(rig, s)
        s.inited = true
        local head = rig.points.Head
        if head then
            local headCf = head.TransformedWorldCFrame
            local world = headCf.Position + rig.rootPart.CFrame:VectorToWorldSpace((FS.BITE_AT - FS.HEAD_AT) * rig.meters)
            s.biteOffset = headCf:PointToObjectSpace(world)
            local at = Instance.new("Attachment")
            at.Name = "ColdLight"
            at.Parent = head
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = FS.MAIN
            light.Range = 5 * rig.unit
            light.Brightness = 1
            light.Shadows = false
            light.Parent = at
            rig.light = light
            -- shards of ice that drift off it and stop: time standing still round it (they hang where they stop, so it leaves them behind as it goes)
            local shards = Instance.new("ParticleEmitter")
            shards.Name = "StoppedTime"
            shards.Texture = SPARKLE
            shards.Rate = if FS.reduced() then 0.8 else 2.5
            shards.Lifetime = NumberRange.new(2.2, 3.4)
            shards.Speed = NumberRange.new(0.6 * rig.unit, 1.4 * rig.unit)
            shards.SpreadAngle = Vector2.new(180, 180)
            shards.Drag = 7 -- out, and then still
            shards.Rotation = NumberRange.new(0, 360)
            shards.RotSpeed = NumberRange.new(0, 0)
            shards.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.08, 0.1 * rig.unit), NumberSequenceKeypoint.new(0.8, 0.09 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            shards.Color = ColorSequence.new(FS.CORE, FS.MAIN)
            shards.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.85, 0.35), NumberSequenceKeypoint.new(1, 1) })
            shards.LightEmission = 0.8
            shards.LightInfluence = 0.2
            shards.Parent = at
        end
        local base = rig.points.Base
        if base then
            local frost = Instance.new("ParticleEmitter")
            frost.Name = "Frost"
            frost.Texture = SPARKLE
            frost.Rate = 0
            frost.Lifetime = NumberRange.new(1.2, 2)
            frost.Speed = NumberRange.new(0, 0)
            frost.Acceleration = Vector3.zero
            frost.Rotation = NumberRange.new(0, 360)
            frost.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            frost.Color = ColorSequence.new(FS.CORE, FS.ICE)
            frost.Transparency = NumberSequence.new(0.35, 1)
            frost.LightEmission = 0.5
            frost.Parent = base
            s.frost = frost
        end
    end

    function FS.folder(rig)
        local folder = Instance.new("Folder")
        folder.Name = "PetSpecial"
        folder.Parent = rig.model.Parent or workspace
        Debris:AddItem(folder, 2.5)
        return folder
    end

    function FS.glass(folder, size, cframe, transparency)
        local part = Instance.new("Part")
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part.Material = Enum.Material.Glass
        part.Color = FS.ICE
        part.Transparency = transparency or 0.35
        part.Size = size
        part.CFrame = cframe
        part.Parent = folder
        return part
    end

    -- It sheds a pane of clear ice: it lifts off its coil, slides away down its side and shatters on the ground.
    function FS.shed(rig)
        if FS.reduced() then
            return
        end
        local pick = FS.SHED[math.random(1, #FS.SHED)]
        local bone = rig.points[pick[1]]
        if not bone then
            return
        end
        local u = rig.unit
        local at = bone.TransformedWorldCFrame.Position + Vector3.new(0, pick[2] * rig.meters, 0)
        local out = (at - rig.rootPart.Position) * Vector3.new(1, 0, 1)
        out = if out.Magnitude > 1e-3 then out.Unit else rig.rootPart.CFrame.RightVector
        local folder = FS.folder(rig)
        local pane = FS.glass(folder, Vector3.new(0.34 * u, 0.025 * u, 0.24 * u), CFrame.lookAt(at, at + out) * CFrame.Angles(0, 0, math.rad(8)), 0.3)
        local land = at + out * 0.45 * u - Vector3.new(0, pick[2] * rig.meters * 1.6, 0)
        TweenService:Create(pane, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            CFrame = CFrame.lookAt(land, land + out) * CFrame.Angles(math.rad(-35), 0, math.rad(20)),
        }):Play()
        local bits = Instance.new("ParticleEmitter")
        bits.Texture = SPARKLE
        bits.Enabled = false
        bits.Lifetime = NumberRange.new(0.4, 0.8)
        bits.Speed = NumberRange.new(0.8 * u, 1.8 * u)
        bits.SpreadAngle = Vector2.new(70, 70)
        bits.Acceleration = Vector3.new(0, -5 * u, 0)
        bits.Size = NumberSequence.new(0.07 * u, 0)
        bits.Color = ColorSequence.new(FS.CORE, FS.ICE)
        bits.LightEmission = 0.6
        bits.Parent = pane
        task.delay(0.7, function()
            if pane.Parent then
                bits:Emit(14) -- it shatters
                pane.Transparency = 1
            end
        end)
    end

    local function animateFrostfangSerpent(rig, s, moving, fly, nova)
        if not s.inited then
            FS.init(rig, s) -- at rest, before any pose
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > FS.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

        -- the special, The Moment That Matters: it settles if it is flying; rears, hood flared, fangs out (to 0.26); holds, swaying back, coiled to
        -- strike; strikes (0.38 to 0.42: Blasts.TheMomentThatMatters, where it bites); holds the strike; settles by 0.92
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local active = if rig.nova then 1 else 0
        s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 2.5)
        local air = s.air
        local rear = smoothstep(0.03, 0.26, progress) * active
        local strike = smoothstep(0.38, 0.42, progress) * active
        local settle = smoothstep(0.66, 0.92, progress) * active
        local coil = math.sin(math.pi * smoothstep(0.26, 0.38, progress)) * active -- drawn back, about to strike

        local drop = dropToGround(rig, s, t, u, air, FS.SOLE)

        -- gliding: it leans in, its hood half folded, a ripple running round its coil; frost forms where it passes
        local gliding = moving * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
        s.wave = (s.wave or 0) + dt * (2.2 + 4 * moving) * gliding
        if s.frost then
            s.frost.Rate = if FS.reduced() then 0 else 14 * gliding
        end

        -- idle business, when it is still: a hiss now and then, hood flared, fangs out; or a pane of ice sheds off its coil
        local still = (1 - moving) * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
        s.nextIdle = s.nextIdle or t + 6
        if t >= s.nextIdle and still > 0.9 then
            s.idleAt, s.idleKind = t, if math.random() < 0.6 then "hiss" else "shed"
            s.nextIdle = t + 9 + math.random() * 9
            if s.idleKind == "shed" then
                FS.shed(rig)
            end
        end
        local idle = if s.idleAt then (t - s.idleAt) / 1.8 else 1
        local hiss = (if s.idleKind == "hiss" and idle < 1 then smoothstep(0, 0.25, idle) * (1 - smoothstep(0.75, 1, idle)) else 0) * still

        -- its gaze: steady, a cobra's stare; it settles on you and holds; its column sways a little as it breathes
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 3 + math.random() * 4
            s.atYou = math.random() < 0.6
            s.gazeYaw = (math.random() - 0.5) * 1.4
        end
        local calm = (1 - 0.5 * gliding) * (1 - rear) * (1 - strike)
        local wantYaw = math.clamp(if s.atYou then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw, -1, 1) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 1.8)
        local sway = math.sin(t * 0.7)
        local breath = math.sin(t * 1.1)

        for _, name in FS.BONES do
            local rest = CFrame.identity
            local glide = FS.cf(FS.GLIDE[name], u)
            local cf = rest:Lerp(glide, gliding)
            local k = tonumber(string.match(name, "^Coil(%d+)$"))
            if k then
                cf *= CFrame.Angles(0, FS.ripple(s.wave, k) * gliding, 0)
            end
            cf = cf:Lerp(FS.cf(FS.HOVER[name], u), air)
            cf = cf:Lerp(FS.cf(FS.HISS[name], u), hiss)
            if active == 1 then
                local reared, struck = FS.cf(FS.REAR[name], u), FS.cf(FS.STRIKE[name], u)
                local special = if strike > 0 then reared:Lerp(struck, strike):Lerp(CFrame.identity, settle) else cf:Lerp(reared, rear)
                cf = special
            end
            -- over the stance: its breath and sway, its stare, drawn back before it strikes
            if name == "Up3" or name == "Up4" then
                cf *= CFrame.Angles(0.012 * breath, 0.03 * sway * calm, 0)
            elseif name == "Up5" or name == "Up6" or name == "Up7" then
                cf *= CFrame.Angles(-0.08 * coil, 0.25 * s.yaw, 0)
            elseif name == "Head" then
                cf *= CFrame.Angles(0.06 * coil, 0.3 * s.yaw, 0.08 * s.yaw)
            end
            if name == "Base" then
                cf = CFrame.new(0, FS.HOVER_UP * air * u - drop, 0) * cf
            end
            pose(m[name], cf)
        end

        -- its tongue: a flick now and then: up into its mouth's gap, out between its lips, back
        s.nextFlick = s.nextFlick or t + 2
        local up, out = 0, 0
        if t >= s.nextFlick then
            local a = (t - s.nextFlick) / 0.5
            if a >= 1 then
                s.nextFlick = t + 1.5 + math.random() * 3
            elseif active == 0 and hiss == 0 then
                up = smoothstep(0, 0.15, a) * (1 - smoothstep(0.85, 1, a))
                out = math.sin(math.pi * smoothstep(0.15, 0.85, a))
            end
        end
        pose(m.Tongue, FS.cf(FS.TONGUE_UP.Tongue, u):Lerp(FS.cf(FS.TONGUE.Tongue, u), out):Lerp(CFrame.identity, 1 - up))
    end

    -- It has struck (animateFrostfangSerpent): where it bit, a hexagon of stopped time spreads across the ground, everything in it hanging still: shards
    -- of ice, motes of frost; a pale flash; then it all shatters outward and is gone.
    function Blasts.TheMomentThatMatters(rig, fx)
        local u, metre = rig.unit, rig.meters
        local s = rig.state
        local head = rig.points.Head
        local bite = if head and s.biteOffset then head.TransformedWorldCFrame:PointToWorldSpace(s.biteOffset) else rig.rootPart.Position
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(bite + Vector3.new(0, 1 * u, 0), Vector3.new(0, -12 * u, 0), params)
        local groundY = if hit then hit.Position.Y else bite.Y - 0.3 * metre
        local centre = Vector3.new(bite.X, groundY, bite.Z)
        local folder = FS.folder(rig)
        local reduced = FS.reduced()

        -- the hexagon: six walls of clear ice standing round it on a line of cold light, spreading out (low and faint, it was lost in the grass: seen in Play)
        local sides = {}
        for k = 0, 5 do
            local a = k / 6 * 2 * math.pi
            local function place(r, y)
                local at = centre + Vector3.new(math.cos(a) * r, y, math.sin(a) * r)
                return CFrame.lookAt(at, centre + Vector3.new(0, y, 0))
            end
            local wall = FS.glass(folder, Vector3.new(0.35 * u, 0.9 * u, 0.05 * u), place(0.3 * u, 0.45 * u), 0.45)
            local bar = FS.glass(folder, Vector3.new(0.35 * u, 0.08 * u, 0.12 * u), place(0.3 * u, 0.04 * u), 0.1)
            bar.Material = Enum.Material.Neon
            bar.Color = FS.MAIN
            local grow = TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
            TweenService:Create(wall, grow, { CFrame = place(3 * u, 0.45 * u), Size = Vector3.new(3.1 * u, 0.9 * u, 0.05 * u) }):Play()
            TweenService:Create(bar, grow, { CFrame = place(3 * u, 0.04 * u), Size = Vector3.new(3.2 * u, 0.08 * u, 0.12 * u) }):Play()
            table.insert(sides, { wall, function(r) return place(r, 0.45 * u) end })
            table.insert(sides, { bar, function(r) return place(r, 0.04 * u) end })
        end
        -- inside it, things hang still: shards of ice in the air, and a burst of frost that stops dead
        local count = if reduced then 8 else 18
        local shards = {}
        for k = 1, count do
            local a = math.random() * 2 * math.pi
            local r = (0.4 + 2.2 * math.random()) * u
            local at = centre + Vector3.new(math.cos(a) * r, (0.3 + 1.3 * math.random()) * u, math.sin(a) * r)
            local shard = FS.glass(folder, Vector3.new(0.1, 0.4, 0.1) * u * (0.8 + 0.6 * math.random()), CFrame.new(at) * CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6), 1)
            tweenAfter(0.05 + 0.2 * math.random(), shard, TweenInfo.new(0.1), { Transparency = 0.15 })
            table.insert(shards, { shard, at, a })
        end
        if not reduced then
            local motes = Instance.new("ParticleEmitter")
            motes.Texture = SPARKLE
            motes.Enabled = false
            motes.Lifetime = NumberRange.new(1.1, 1.3)
            motes.Speed = NumberRange.new(2 * u, 5 * u)
            motes.SpreadAngle = Vector2.new(180, 60)
            motes.Drag = 25 -- flung out, and stopped dead
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(0.85, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(FS.CORE, FS.MAIN)
            motes.LightEmission = 0.8
            motes.LightInfluence = 0.2
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre + Vector3.new(0, 0.5 * u, 0)), FS.CORE)
            holder.Transparency = 1
            motes.Parent = holder
            motes:Emit(40)
        end
        -- a pale flash, and a cold light
        local flash = fx.neon(Vector3.one * 0.6 * u, CFrame.new(bite), FS.CORE)
        flash.Shape = Enum.PartType.Ball
        flash.Transparency = 0.3
        TweenService:Create(flash, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 2.4 * u, Transparency = 1 }):Play()
        local light = Instance.new("PointLight")
        light.Color = FS.MAIN
        light.Range = 9 * u
        light.Brightness = 2.2
        light.Shadows = false
        light.Parent = flash
        TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
        -- held; then it all shatters outward
        task.delay(0.95, function()
            for _, side in sides do
                local slab, place = side[1], side[2]
                if slab.Parent then
                    TweenService:Create(slab, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = place(3.8 * u), Transparency = 1 }):Play()
                end
            end
            for _, sh in shards do
                local shard, at, a = sh[1], sh[2], sh[3]
                if shard.Parent then
                    local away = at + Vector3.new(math.cos(a), 0.4, math.sin(a)) * 1.2 * u
                    TweenService:Create(shard, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                        CFrame = CFrame.new(away) * CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6), Transparency = 1,
                    }):Play()
                end
            end
        end)
    end

    PetRig.Profiles.FrostfangSerpent = {
        Skinned = true,
        Bones = (function()
            local bones = table.clone(FS.BONES)
            table.insert(bones, "Tongue")
            return bones
        end)(),
        Points = { "Head", "Base", "Coil2", "Coil4", "Coil6", "Coil8" },
        GlowColors = {
            c8f2ff = Color3.fromRGB(200, 242, 255), -- its crystal fangs
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        },
        SeeThrough = { Ice = 0.35 }, -- the blades round its hood: clear ice
        Effects = {
            Blast = "TheMomentThatMatters",
            Pulse = "Fangs",
            NovaLight = 2,
        },
        Colors = {
            Gold = FS.MAIN,
            Amber = FS.DEEP,
            Orange = FS.ICE,
            Sun = FS.CORE,
            Ivory = Color3.fromRGB(232, 246, 255),
        },
        Animate = animateFrostfangSerpent,
    }
end

do
    -- The Storm Bumblebee (skinned): a fat, fuzzy bumblebee charged with static. It hovers, bobbing, its small smoky wings a blur of a figure-eight
    -- beat; little arcs of static crackle across its fur, a spark glows at the tip of each feeler, and in the baskets of its hind legs it carries
    -- balls of stored lightning. It turns its head to look at you, twitches a feeler, pumps its abdomen as it breathes. Now and then it zips off to one
    -- side and back, throws a barrel roll for the fun of it, or shivers, every hair crackling at once. Moving, it leans into its flight, legs trailing.
    -- Its special, A Lesson Learned Once: it rises, buzzing harder, fur crackling and glowing; curls its abdomen under, its sting of light sliding out;
    -- and dives, driving the sting into the ground (at 0.42: Blasts.ALessonLearnedOnce): a crack of lightning, arcs spreading out across the ground.
    -- Then it pops back up and shakes itself off.
    local SB = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        -- its stances, each checked in Blender (storm_bumblebee.py's pose_tables: wings against body, legs against abdomen and each other, feelers,
        -- abdomen against thorax) and along every slerp between them: turns x, y, z; then a move in metres
        ZIP = {
            Abd1 = { 0.06, 0, 0 }, AntL1 = { -0.25, 0, 0 }, AntR1 = { -0.25, 0, 0 }, Body = { -0.32, 0, 0 }, Head = { 0.15, 0, 0 },
            LegL1 = { -0.2, 0, -0.12 }, LegL2 = { -0.25, 0, -0.12 }, LegL3 = { -0.28, 0, -0.22 }, LegR1 = { -0.2, 0, 0.12 }, LegR2 = { -0.25, 0, 0.12 },
            LegR3 = { -0.28, 0, 0.22 }, ShinL1 = { -0.15, 0, 0 }, ShinL2 = { -0.15, 0, 0 }, ShinL3 = { -0.12, 0, 0 }, ShinR1 = { -0.15, 0, 0 },
            ShinR2 = { -0.15, 0, 0 }, ShinR3 = { -0.12, 0, 0 },
        },
        CHARGE = {
            Abd1 = { -0.12, 0, 0 }, Abd2 = { -0.08, 0, 0 }, AntL1 = { 0.25, 0, -0.2 }, AntL2 = { 0.2, 0, 0 }, AntR1 = { 0.25, 0, 0.2 }, AntR2 = { 0.2, 0, 0 },
            Body = { 0.3, 0, 0 }, Head = { -0.1, 0, 0 },
        },
        STING = { -- nose up, abdomen curled under, its sting slid out and aimed straight down, its legs splayed out of the way
            Abd1 = { 0.2, 0, 0 }, Abd2 = { 0.52, 0, 0 }, Body = { 0.2, 0, 0 }, Head = { -0.12, 0, 0 }, LegL1 = { 0.5, 0, -0.25 }, LegL2 = { 0.3, 0, -0.45 },
            LegL3 = { 0.55, 0, -0.5 }, LegR1 = { 0.5, 0, 0.25 }, LegR2 = { 0.3, 0, 0.45 }, LegR3 = { 0.55, 0, 0.5 }, ShinL1 = { 0.4, 0, 0 },
            ShinL3 = { 0.15, 0, 0 }, ShinR1 = { 0.4, 0, 0 }, ShinR3 = { 0.15, 0, 0 }, Sting = { 0, 0, 0, 0, -0.0258, 0.0452 },
        },
        -- LOOK (checked): Head { 0.05, 0.3, 0.08 }, AntL1 { 0, 0.2, 0 }, AntR1 { 0, -0.2, 0 }: built from its gaze in animateStormBumblebee
        TWITCH = { AntL1 = { 0.2, 0.1, -0.2 }, AntL2 = { 0.3, 0, 0 } },
        -- its wings' figure-eight beat, inside the box checked at its corners: roll (up -, down +) and sweep (forward -, back +), left wing
        ROLL = { -0.6, 0.24 },
        SWEEP = { -0.4, 0.14 },
        BEAT = 26, -- beats a second: faster than the frames, it strobes into a blur
        RISE = 0.25, -- metres it climbs while it charges
        TIP_BELOW = 0.2579, -- metres from the middle of its box (the game's: its RootPart, at its origin, counts) down to its sting's tip, stinging
        STING_AT = Vector3.new(0, 0.3767, 0.3981), -- its Sting bone, metres in its own axes
        TIP_AT = Vector3.new(0, 0.345, 0.4537), -- its sting's tip, sheathed
        BONES = {
            "Body", "Head", "Abd1", "Abd2", "Sting", "AntL1", "AntL2", "AntR1", "AntR2", "WingL", "WingR",
            "LegL1", "ShinL1", "LegL2", "ShinL2", "LegL3", "ShinL3", "LegR1", "ShinR1", "LegR2", "ShinR2", "LegR3", "ShinR3",
        },
        CORE = Color3.fromRGB(255, 250, 200),
        MAIN = Color3.fromRGB(255, 220, 80),
        DEEP = Color3.fromRGB(170, 110, 255),
        ARC = Color3.fromRGB(238, 228, 255),
        TIP = Color3.fromRGB(255, 242, 160),
    }

    function SB.cf(a, u)
        if not a then
            return CFrame.identity
        end
        local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
        return move * CFrame.Angles(a[1], a[2], a[3])
    end

    function SB.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- Once, at rest: where its sting's tip is, carried on its Sting bone; its light; the static sparks off its fur.
    function SB.init(rig, s)
        s.inited = true
        local sting = rig.points.Sting
        if sting then
            local cf = sting.TransformedWorldCFrame
            local world = cf.Position + rig.rootPart.CFrame:VectorToWorldSpace((SB.TIP_AT - SB.STING_AT) * rig.meters)
            s.tipOffset = cf:PointToObjectSpace(world)
        end
        local body = rig.points.Body
        if body then
            local at = Instance.new("Attachment")
            at.Name = "Static"
            at.Parent = body
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = SB.MAIN
            light.Range = 4 * rig.unit
            light.Brightness = 1
            light.Shadows = false
            light.Parent = at
            rig.light = light
            local sparks = Instance.new("ParticleEmitter")
            sparks.Name = "StaticSparks"
            sparks.Texture = SPARKLE
            sparks.Rate = 0
            sparks.Lifetime = NumberRange.new(0.15, 0.35)
            sparks.Speed = NumberRange.new(0.6 * rig.unit, 1.6 * rig.unit)
            sparks.SpreadAngle = Vector2.new(180, 180)
            sparks.Size = NumberSequence.new(0.07 * rig.unit, 0)
            sparks.Color = ColorSequence.new(SB.CORE, SB.ARC)
            sparks.LightEmission = 1
            sparks.LightInfluence = 0
            sparks.Parent = at
            s.sparks = sparks
        end
    end

    -- The ground under it, looked up now and then (a player walking under it: keep what it had).
    function SB.groundBelow(rig, s, t)
        s.nextGround = s.nextGround or 0
        if t >= s.nextGround then
            s.nextGround = t + 0.2
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local from = rig.rootPart.Position
            local hit = workspace:Raycast(from, Vector3.new(0, -14 * rig.unit, 0), params)
            local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
            if not onCharacter then
                s.height = if hit then (from.Y - hit.Position.Y) / rig.meters else nil -- metres from the middle of its box to the ground
            end
        end
        return s.height
    end

    local function animateStormBumblebee(rig, s, moving, fly, nova)
        if not s.inited then
            SB.init(rig, s) -- at rest, before any pose
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SB.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local reduced = SB.reduced()

        -- the special, A Lesson Learned Once: it rises, charging (to 0.28); curls, its sting out (0.28 to 0.36); dives, the sting into the ground
        -- (0.36 to 0.42: Blasts.ALessonLearnedOnce); holds it there; pops back up (0.58 to 0.75) and shakes itself off (to 0.92)
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local active = if rig.nova then 1 else 0
        if active == 1 and not s.diving then
            s.diving = rig.nova.start
            local height = SB.groundBelow(rig, s, t)
            -- the dive: down until its sting's tip, curled, meets the ground (its rise has gone by then; counted in, the sting went a stud into
            -- the ground: seen in Play); no ground found: a short dip
            s.dive = if height then math.clamp(height - SB.TIP_BELOW + 0.015, 0, 2.2) else 0.3
        elseif active == 0 then
            s.diving = nil
        end
        local charge = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.3, 0.38, progress)) * active
        local curl = smoothstep(0.28, 0.36, progress) * (1 - smoothstep(0.58, 0.72, progress)) * active
        local rise = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.36, 0.42, progress)) * active
        local dive = smoothstep(0.36, 0.42, progress) * (1 - smoothstep(0.58, 0.75, progress)) * active
        local shake = if active == 1 and progress > 0.72 and progress < 0.92 then math.sin(math.pi * (progress - 0.72) / 0.2) else 0
        local stuck = if active == 1 and progress > 0.42 and progress < 0.58 then 1 else 0

        -- idle business, when it is still: a zip off to one side and back, a barrel roll, or a shiver of static
        local still = (1 - moving) * (1 - active)
        s.nextIdle = s.nextIdle or t + 5
        if t >= s.nextIdle and still > 0.9 then
            local r = math.random()
            s.idleAt, s.idleKind = t, if r < 0.45 then "zip" elseif r < 0.7 then "roll" else "shiver"
            s.zipSide = if math.random() < 0.5 then 1 else -1
            s.nextIdle = t + 6 + math.random() * 7
            if s.idleKind == "shiver" and s.sparks and not reduced then
                s.sparks:Emit(14)
            end
        end
        local idleLen = if s.idleKind == "roll" then 0.9 elseif s.idleKind == "zip" then 1.1 else 0.8
        local idle = if s.idleAt then (t - s.idleAt) / idleLen else 1
        local live = if idle < 1 then still else 0
        local zip = if s.idleKind == "zip" and idle < 1 then math.sin(math.pi * idle) * live else 0
        local roll = if s.idleKind == "roll" and idle < 1 then smoothstep(0, 1, idle) * live else 0
        local shiver = if s.idleKind == "shiver" and idle < 1 then math.sin(math.pi * idle) * live else 0

        -- its gaze: now on you, now about; a feeler twitch now and then
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2 + math.random() * 3
            s.atYou = math.random() < 0.55
            s.gazeYaw = (math.random() - 0.5) * 1.6
            s.twitchAt, s.twitchSide = t, if math.random() < 0.5 then "L" else "R"
        end
        local wantYaw = math.clamp(if s.atYou then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw, -1, 1) * (1 - active) * (1 - zip)
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
        local twitch = if s.twitchAt then math.max(0, math.sin(math.pi * math.clamp((t - s.twitchAt) / 0.35, 0, 1))) else 0

        -- the buzz: faster as it charges; the hover bob; its abdomen pumping as it breathes
        s.phase = (s.phase or 0) + dt * SB.BEAT * 2 * math.pi * (1 + 0.5 * charge)
        local bob = math.sin(t * 2.4) * 0.018 * (1 - active)
        local breath = math.sin(t * 3.1)
        local lean = math.max(moving, fly * 0.6) * (1 - active)
        local look = math.abs(s.yaw)

        for _, name in SB.BONES do
            local cf = CFrame.identity:Lerp(SB.cf(SB.ZIP[name], u), math.max(lean, zip * 0.7))
            if active == 1 then
                cf = cf:Lerp(SB.cf(SB.CHARGE[name], u), charge):Lerp(SB.cf(SB.STING[name], u), curl)
            end
            -- its gaze (LOOK, checked turned to its left; to its right, its mirror) and a feeler's twitch (TWITCH, its left; mirrored for its right)
            local side = string.match(name, "^Ant([LR])%d$")
            if name == "Head" then
                cf *= CFrame.Angles(0.05 * look, 0.3 * s.yaw, 0.08 * s.yaw)
            elseif side then
                local sign = if side == "L" then 1 else -1
                cf *= CFrame.Angles(0, 0.2 * sign * look * (if string.sub(name, -1) == "1" then 1 else 0), 0)
                if side == s.twitchSide then
                    local tw = SB.TWITCH["AntL" .. string.sub(name, -1)]
                    cf *= CFrame.Angles(tw[1] * twitch, tw[2] * sign * twitch, tw[3] * sign * twitch)
                end
            end
            if name == "Abd1" then
                cf *= CFrame.Angles(0.025 * breath, 0, 0)
            elseif name == "WingL" or name == "WingR" then
                local sign = if name == "WingL" then 1 else -1
                local rollMid, rollAmp = (SB.ROLL[1] + SB.ROLL[2]) / 2, (SB.ROLL[2] - SB.ROLL[1]) / 2
                local sweepMid, sweepAmp = (SB.SWEEP[1] + SB.SWEEP[2]) / 2, (SB.SWEEP[2] - SB.SWEEP[1]) / 2
                cf = CFrame.Angles(0, sign * (sweepMid + sweepAmp * math.cos(s.phase)), sign * (rollMid + rollAmp * math.sin(s.phase)))
            elseif name == "Body" then
                -- over the stance: the bob; the zip off to one side; the roll; the shiver; the rise, the dive and the shake
                local jitter = (shiver + 0.4 * charge + 0.6 * shake) * 0.06
                cf = CFrame.new((s.zipSide or 1) * 0.38 * zip * u, (bob + SB.RISE * rise - (s.dive or 0) * dive + 0.08 * math.sin(math.pi * roll)) * u, 0)
                    * cf
                    * CFrame.Angles(jitter * math.sin(t * 61), jitter * math.sin(t * 53 + 1), (s.zipSide or 1) * -0.3 * zip + 2 * math.pi * roll + jitter * math.sin(t * 47 + 2))
            end
            pose(m[name], cf)
        end

        -- the static: little arcs flickering across its fur, more as it charges; the sparks off it
        s.nextFlicker = s.nextFlicker or 0
        if t >= s.nextFlicker then
            s.nextFlicker = t + 0.06 + math.random() * 0.08
            local chance = 0.12 + 0.75 * math.max(charge, shiver, shake) + 0.5 * stuck
            for _, key in { "CrackleA", "CrackleB" } do
                local part = rig.parts[key]
                if part then
                    part.Transparency = if math.random() < chance then 0 else 1
                end
            end
        end
        if s.sparks then
            s.sparks.Rate = if reduced then 0 else 1.5 + 30 * charge + 12 * stuck
        end
        -- the spark at each feeler's tip and its sting, brightening as it charges
        local tips = rig.parts.Tips
        if tips then
            tips.Color = SB.TIP:Lerp(Color3.new(1, 1, 1), 0.25 + 0.25 * math.sin(t * 9) + 0.5 * charge)
        end
        local sting = rig.parts.Sting
        if sting then
            sting.Color = SB.CORE:Lerp(Color3.new(1, 1, 1), curl)
        end
    end

    -- It has driven its sting into the ground (animateStormBumblebee): a crack of light, a scorch, and arcs of lightning running out across the ground
    -- from it, forking as they go; sparks thrown up; then it all flickers out.
    function Blasts.ALessonLearnedOnce(rig, fx)
        local u = rig.unit
        local s = rig.state
        local sting = rig.points.Sting
        local tip = if sting and s.tipOffset then sting.TransformedWorldCFrame:PointToWorldSpace(s.tipOffset) else rig.rootPart.Position
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(tip + Vector3.new(0, 0.6 * u, 0), Vector3.new(0, -8 * u, 0), params)
        local ground = if hit then hit.Position else tip - Vector3.new(0, 0.2 * u, 0)
        local reduced = SB.reduced()

        -- the strike itself: a short bolt from its sting into the ground, and a flash
        local function bolt(from, to, width, color, kinks)
            local last = from
            local parts = {}
            for k = 1, kinks do
                local f = k / kinks
                local at = from:Lerp(to, f)
                if k < kinks then
                    local side = (to - from):Cross(Vector3.yAxis)
                    side = if side.Magnitude > 1e-3 then side.Unit else Vector3.xAxis
                    at += side * (math.random() - 0.5) * 0.35 * (to - from).Magnitude / kinks * 2 + Vector3.new(0, (math.random() - 0.5) * 0.05 * u, 0)
                end
                local length = (at - last).Magnitude
                if length > 1e-3 then
                    local seg = fx.neon(Vector3.new(width, width, length), CFrame.lookAt((last + at) / 2, at), color)
                    table.insert(parts, seg)
                end
                last = at
            end
            return parts
        end
        for _, seg in bolt(tip, ground, 0.1 * u, SB.CORE, 4) do
            tweenAfter(0.25, seg, TweenInfo.new(0.2), { Transparency = 1 })
        end
        local flash = fx.neon(Vector3.one * 0.4 * u, CFrame.new(ground + Vector3.new(0, 0.1 * u, 0)), SB.CORE)
        flash.Shape = Enum.PartType.Ball
        flash.Transparency = 0.2
        TweenService:Create(flash, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 2.2 * u, Transparency = 1 }):Play()
        local light = Instance.new("PointLight")
        light.Color = SB.MAIN
        light.Range = 10 * u
        light.Brightness = 2
        light.Shadows = false
        light.Parent = flash
        TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()

        -- a scorch where it struck
        local scorch = fx.neon(Vector3.new(0.02 * u, 1.3 * u, 1.3 * u), CFrame.new(ground + Vector3.new(0, 0.02 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(40, 36, 52))
        scorch.Shape = Enum.PartType.Cylinder
        scorch.Material = Enum.Material.SmoothPlastic
        scorch.Transparency = 0.25
        tweenAfter(0.9, scorch, TweenInfo.new(0.8), { Transparency = 1 })

        -- the arcs: out across the ground from it, each a run of kinked segments lit one after another, some forking
        local count = if reduced then 4 else 7
        local facing = math.random() * 2 * math.pi
        for k = 1, count do
            local a = facing + k / count * 2 * math.pi + (math.random() - 0.5) * 0.4
            local reach = (2 + 1.4 * math.random()) * u
            local from = ground + Vector3.new(0, 0.06 * u, 0)
            local to = from + Vector3.new(math.cos(a), 0, math.sin(a)) * reach
            local segs = bolt(from, to, 0.09 * u, if k % 2 == 0 then SB.ARC else SB.MAIN, 7)
            if not reduced and k % 2 == 1 then
                local mid = from:Lerp(to, 0.5)
                local b = a + (if math.random() < 0.5 then 0.6 else -0.6)
                for _, seg in bolt(mid, mid + Vector3.new(math.cos(b), 0, math.sin(b)) * reach * 0.45, 0.06 * u, SB.ARC, 4) do
                    table.insert(segs, seg)
                end
            end
            for j, seg in segs do
                seg.Transparency = 1
                tweenAfter(0.03 * j, seg, TweenInfo.new(0.05), { Transparency = 0 }) -- running out from it
                tweenAfter(0.55 + 0.03 * j, seg, TweenInfo.new(0.45), { Transparency = 1 })
            end
        end

        -- sparks thrown up
        if not reduced then
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(ground + Vector3.new(0, 0.15 * u, 0)), SB.CORE)
            holder.Transparency = 1
            local sparks = Instance.new("ParticleEmitter")
            sparks.Texture = SPARKLE
            sparks.Enabled = false
            sparks.Lifetime = NumberRange.new(0.4, 0.8)
            sparks.Speed = NumberRange.new(3 * u, 7 * u)
            sparks.SpreadAngle = Vector2.new(70, 70)
            sparks.Acceleration = Vector3.new(0, -12 * u, 0)
            sparks.Size = NumberSequence.new(0.12 * u, 0)
            sparks.Color = ColorSequence.new(SB.CORE, SB.MAIN)
            sparks.LightEmission = 1
            sparks.Parent = holder
            holder.CFrame = CFrame.lookAt(holder.Position, holder.Position + Vector3.yAxis)
            sparks:Emit(30)
        end
    end

    PetRig.Profiles.StormBumblebee = {
        Skinned = true,
        Bones = SB.BONES,
        Points = { "Body", "Head", "Abd2", "Sting" },
        GlowColors = {
            fff2a0 = SB.TIP, -- the sparks at its feelers' tips
            ffe066 = Color3.fromRGB(255, 224, 102), -- the stored lightning in its leg baskets
            fff9dc = SB.CORE, -- its sting of light
            eee4ff = SB.ARC, -- the arcs crackling across its fur
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        },
        SeeThrough = { Wings = 0.45 }, -- its wings: smoky glass, dark-veined
        Effects = {
            Blast = "ALessonLearnedOnce",
            Pulse = "Charge",
            NovaLight = 2,
        },
        Colors = {
            Gold = SB.MAIN,
            Amber = SB.DEEP,
            Orange = SB.MAIN,
            Sun = SB.CORE,
            Ivory = Color3.fromRGB(255, 252, 236),
        },
        Animate = animateStormBumblebee,
    }
end

do
    -- The Golden Kirin (skinned): a radiant celestial kirin, pearl-white, its legs dipped in gold, gold flame-scrolls on its shoulders and haunches,
    -- two gold crescent horns, long gold barbels, a mane and tail of silk ribbons, big golden sun-eyes, a sunburst arc of light behind its head and a lotus
    -- of light under each hoof: it never touches the ground. It stands proud and gentle, its silk stirring in a breeze nothing else feels, its halo
    -- rocking softly, the lotuses turning slowly under it; it looks at you; now and then it lifts a foreleg high and sets it down, bows its head, or
    -- swishes its tail; still a long while, it lies down on the air. It walks in a high-stepping prance; in the air it bounds on nothing, a ribbon of
    -- light streaming from its tail. Its special, Lotus Bloom: it rears, forelegs folded high, its halo flaring (to 0.4); at the burst (0.42:
    -- Blasts.LotusBloom) a great lotus of golden light opens on the air beneath it, a ring of light running out across the ground and motes rising; it
    -- comes down and bows.
    local KG = {
        FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOLE = 0.5325, -- metres from the middle of its box (the root at 0 to its halo's top, 1.0769) down to its lotuses (0.006): they rest on the ground
        LID_HINGE = { L = Vector3.new(0.7877, -0.052, -0.6139), R = Vector3.new(0.7877, 0.052, 0.6139) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(56),
        BLINK_LOWER = math.rad(28),
        GOLD = Color3.fromRGB(255, 214, 120),
        LIGHT = Color3.fromRGB(255, 244, 206),
        DEEP = Color3.fromRGB(236, 170, 60),
        PETAL = Color3.fromRGB(255, 168, 40),
        TROT = { FL = 0, BR = 0, FR = math.pi, BL = math.pi }, -- diagonal pairs together
        LOTUS_TURN = { FL = 0.35, FR = -0.3, BL = -0.32, BR = 0.28 }, -- how fast each lotus turns under its hoof (radians a second)
        PRANCE = { LegFL1 = { 0.7, 0, 0 }, LegFL2 = { -1.3, 0, 0 }, LegFL3 = { 0.6, 0, 0 }, Neck1 = { -0.12, 0, 0 }, Head = { 0.15, 0, 0 }, Tail1 = { 0.35, 0, 0 } },
        BOW = { Neck1 = { 0.3, 0, 0 }, Neck2 = { 0.25, 0, 0 }, Head = { 0.2, 0, 0 } },
        BONES = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2", "Tail3", "Halo" },
    }
    for _, key in { "FL", "FR", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(KG.BONES, "Leg" .. key .. k)
        end
        table.insert(KG.BONES, "Hoof" .. key)
    end

    function KG.stance(base, f, b)
        for _, side in { "L", "R" } do
            for k = 1, 3 do
                base["LegF" .. side .. k] = { f[k], 0, 0 }
                base["LegB" .. side .. k] = { b[k], 0, 0 }
            end
        end
        return base
    end

    -- its stances, each searched in Blender against the ground and for torn skin: the same numbers as golden_kirin.py's REAR, LIE and LEAP
    KG.REAR = KG.stance({ Body = { 0.5, 0, 0 }, Neck1 = { -0.15, 0, 0 }, Head = { -0.05, 0, 0 } }, { -0.1, -0.5, 1.2 }, { -0.25, -0.2, 0.05 })
    KG.REAR_DROP = 0.042
    KG.LIE = KG.stance({ Body = { -0.1, 0, 0 }, Head = { 0.25, 0, 0 } }, { 0.4, -2.1, 0 }, { -0.4, -0.65, 1.8 })
    KG.LIE_DROP = 0.19
    KG.LEAP = KG.stance({ Body = { -0.04, 0, 0 }, Head = { 0.2, 0, 0 }, Tail1 = { 0.3, 0, 0 } }, { 0.6, -1.4, 0.3 }, { -0.4, 0.25, 0.1 })

    function KG.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- its light (on the halo's bone, so it goes where its head goes), a few motes drifting off the halo, and the ribbon of light off its tail in the air
    function KG.glow(rig, s)
        s.glowMade = true
        local halo, tail = rig.points.Halo, rig.points.Tail3
        if not halo then
            return
        end
        local at = Instance.new("Attachment")
        at.Name = "HaloLight"
        at.Parent = halo
        local light = Instance.new("PointLight")
        light.Name = "PulseLight"
        light.Color = KG.GOLD
        light.Range = 5 * rig.unit
        light.Brightness = 1.2
        light.Shadows = false
        light.Parent = at
        rig.light = light
        local motes = Instance.new("ParticleEmitter")
        motes.Name = "HaloMotes"
        motes.Texture = SPARKLE
        motes.Rate = 2.5
        motes.Lifetime = NumberRange.new(1.2, 2)
        motes.Speed = NumberRange.new(0.04 * rig.unit, 0.12 * rig.unit)
        motes.SpreadAngle = Vector2.new(180, 180)
        motes.Acceleration = Vector3.new(0, 0.08 * rig.unit, 0)
        motes.Drag = 1
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.05 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
        motes.Color = ColorSequence.new(KG.LIGHT, KG.GOLD)
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Parent = at
        if tail then
            local top, bottom = Instance.new("Attachment"), Instance.new("Attachment")
            top.Position, bottom.Position = Vector3.new(0, 0.04 * rig.meters, 0), Vector3.new(0, -0.04 * rig.meters, 0)
            top.Parent, bottom.Parent = tail, tail
            local trail = Instance.new("Trail")
            trail.Name = "SilkTrail"
            trail.Attachment0, trail.Attachment1 = top, bottom
            trail.Lifetime = 0.5
            trail.FaceCamera = true
            trail.LightEmission = 1
            trail.LightInfluence = 0
            trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.2) })
            trail.Color = ColorSequence.new(KG.LIGHT, KG.GOLD)
            trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
            trail.Enabled = false
            trail.Parent = tail
            s.trail = trail
        end
    end

    local function animateGoldenKirin(rig, s, moving, fly, nova)
        if not s.glowMade then
            KG.glow(rig, s)
        end
        local camera = workspace.CurrentCamera
        if s.trail then
            s.trail.Enabled = fly > 0.4 and not KG.reduced()
        end
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > KG.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)
        local drop = dropToGround(rig, s, t, u, fly, KG.SOLE)

        -- the special, Lotus Bloom: it rears, forelegs folded high (to 0.32); at the burst (0.42) the lotus blooms under it; it comes down (0.55 to
        -- 0.75) and bows (0.7 to 0.95)
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local rise = smoothstep(0.04, 0.32, progress) * (1 - smoothstep(0.55, 0.75, progress))
        local bow = smoothstep(0.7, 0.8, progress) * (1 - smoothstep(0.86, 0.97, progress))
        local special = progress > 0

        -- still a long while, it lies down; now and then it prances in place, bows its head, or swishes its tail
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantLie = if s.still > 10 then 1 else 0
        s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1 else 5))
        local lie = smoothstep(0, 1, s.lie)
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt, s.fidgetKind = t, if r < 0.4 then "prance" elseif r < 0.7 then "bow" else "swish"
            s.nextFidget = t + 6 + math.random() * 5
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.6, 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - lie) * (1 - rise)

        -- the prance, diagonal pairs together, the forelegs lifted high at the knee; in the air a bounding run on nothing
        s.stride = (s.stride or 0) + dt * (6.5 * moving + 5.5 * fly)
        local onFoot = moving * (1 - fly)
        local want = {}
        addStance(want, KG.REAR, rise)
        addStance(want, KG.LIE, lie * (1 - rise))
        addStance(want, KG.LEAP, fly * (0.55 + 0.45 * math.sin(s.stride)))
        addStance(want, KG.PRANCE, if s.fidgetKind == "prance" then fidget else 0)
        addStance(want, KG.BOW, math.max(bow, if s.fidgetKind == "bow" then fidget else 0))
        for key, lead in KG.TROT do
            local phase = s.stride + lead
            local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
            local stance
            if string.sub(key, 1, 1) == "F" then
                stance = { ["Leg" .. key .. "1"] = { 0.3 * swing + 0.3 * lift, 0, 0 }, ["Leg" .. key .. "2"] = { 0.1 * lift, 0, 0 },
                    ["Leg" .. key .. "3"] = { -1.2 * lift, 0, 0 }, ["Hoof" .. key] = { -0.35 * lift, 0, 0 } }
            else
                stance = { ["Leg" .. key .. "1"] = { -0.3 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { -0.3 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { 0.6 * lift, 0, 0 } }
            end
            addStance(want, stance, onFoot)
        end

        -- the body: breathing, banking on turns, the head carried high as it prances
        local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
        local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
        s.heading = heading
        s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
        local breath = math.sin(t * 1.1)
        addStance(want, { Hips = { 0, 0, s.bank * pace }, Chest = { 0.012 * breath, 0, 0 }, Neck1 = { -0.06 * onFoot, 0, 0 } }, 1)

        -- its gaze: gentle, often on you; up at the sky as it rears
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.5 + math.random() * 3.5
            s.atYou = math.random() < 0.55
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - 0.7 * pace) * (1 - rise)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.25, 0.3) else s.gazePitch) * calm + 0.3 * rise
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
        addStance(want, {
            Neck2 = { 0.3 * s.pitch, 0.35 * s.yaw * (1 - 0.4 * lie), 0 }, Head = { 0.4 * s.pitch, 0.5 * s.yaw * (1 - 0.4 * lie), 0 },
            EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
        }, 1)

        -- the ears: a flick now and then; laid back on the wing
        for _, side in { "L", "R" } do
            local sign = if side == "L" then 1 else -1
            local flick = math.max(0, math.sin(t * 2.9 + (if side == "L" then 1 else 4))) ^ 30
            addStance(want, { ["Ear" .. side] = { 0.2 * flick - 0.35 * fly, sign * (0.15 * flick + 0.25 * fly), 0 } }, 1)
        end

        -- the tail: its silk always stirring, a wave running down it; swished from side to side in its fidget; raised in the bound
        local wave = 1.3 + 1.5 * pace
        local swish = if s.fidgetKind == "swish" then fidget else 0
        addStance(want, {
            Tail1 = { 0.05 * math.sin(t * 0.9) + 0.25 * fly + 0.1 * onFoot, 0.12 * math.sin(t * wave) + 0.4 * swish * math.sin(t * 6), 0 },
            Tail2 = { 0.06 * math.sin(t * 0.9 - 0.7), 0.16 * math.sin(t * wave - 0.8) + 0.4 * swish * math.sin(t * 6 - 0.8), 0 },
            Tail3 = { 0.08 * math.sin(t * 0.9 - 1.4) - 0.15 * fly, 0.2 * math.sin(t * wave - 1.6) + 0.3 * swish * math.sin(t * 6 - 1.6), 0 },
        }, 1)

        -- the halo: rocking softly behind its head
        addStance(want, { Halo = { 0, 0, 0.07 * math.sin(t * 0.6) } }, 1)

        for _, name in KG.BONES do
            local a = want[name] or Vector3.zero
            local lift = if name == "Hips"
                then (-KG.REAR_DROP * rise - KG.LIE_DROP * lie * (1 - rise) + 0.014 * onFoot * math.abs(math.sin(s.stride))) * u - drop
                else 0
            pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end
        -- the lotuses turn slowly under its hooves, coming down with it to the ground
        for key, speed in KG.LOTUS_TURN do
            pose(m["Lotus" .. key], CFrame.new(0, -drop, 0) * CFrame.Angles(0, t * speed, 0))
        end

        -- the eyes: slow blinks; dozing as it lies; wide as the lotus blooms
        local wide = smoothstep(0.38, 0.45, progress) * (1 - smoothstep(0.6, 0.75, progress))
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
        local close = math.max(blink, lie * 0.5 * doze, bow * 0.6) * (1 - wide)
        local upper = KG.BLINK_UPPER * close - math.rad(6) * wide
        local lower = KG.BLINK_LOWER * close - math.rad(5) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(KG.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(KG.LID_HINGE[side], lower))
        end
    end

    -- It has reared, its halo flaring (animateGoldenKirin): a great lotus of golden light opens on the air under it, two rings of petals unfolding outward,
    -- a ring of light running out across the ground, golden motes rising; then it all fades.
    function Blasts.LotusBloom(rig, fx)
        local u = rig.unit
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local from = rig.rootPart.Position
        local hit = workspace:Raycast(from, Vector3.new(0, -8 * u, 0), params)
        local ground = if hit then hit.Position else from - Vector3.new(0, KG.SOLE * rig.meters, 0)
        local centre = ground + Vector3.new(0, 0.06 * u, 0)
        local reduced = KG.reduced()
        local turn = math.random() * 2 * math.pi

        -- the petals: ellipsoids of light, lying out from the middle and tipped up, unfolding from a bud
        local function petals(count, reach, length, width, tilt, offset, color, delay)
            for k = 1, count do
                local a = turn + offset + (k - 1) / count * 2 * math.pi
                local out = Vector3.new(math.cos(a), 0, math.sin(a))
                local function at(r, tip)
                    return CFrame.lookAt(centre + out * r, centre + out * (r + 1)) * CFrame.Angles(tip, 0, 0)
                end
                local petal = fx.neon(Vector3.new(width, 0.04, length) * u * 0.2, at(0.05 * u, math.rad(70)), color)
                local shape = Instance.new("SpecialMesh")
                shape.MeshType = Enum.MeshType.Sphere
                shape.Parent = petal
                petal.Transparency = 0.15
                tweenAfter(delay, petal, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
                    { Size = Vector3.new(width, 0.04, length) * u, CFrame = at(reach * u, math.rad(tilt)) })
                tweenAfter(0.95 + delay, petal, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
            end
        end
        -- wider than the kirin itself (at 1.0 across it bloomed smaller than the pet: seen in Play); deeper than its gold, as Neon blooms a pale gold
        -- to white
        petals(8, 1.6, 1.8, 0.8, 18, 0, KG.PETAL, 0)
        petals(8, 0.9, 1.3, 0.6, 38, math.pi / 8, KG.GOLD, 0.08)

        -- the heart of it, and its light
        local heart = fx.neon(Vector3.one * 0.4 * u, CFrame.new(centre + Vector3.new(0, 0.15 * u, 0)), KG.LIGHT)
        heart.Shape = Enum.PartType.Ball
        heart.Transparency = 0.1
        TweenService:Create(heart, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.1 * u }):Play()
        tweenAfter(0.6, heart, TweenInfo.new(0.9), { Size = Vector3.one * 0.2 * u, Transparency = 1 })
        local light = Instance.new("PointLight")
        light.Color = KG.GOLD
        light.Range = 12 * u
        light.Brightness = 2.5
        light.Shadows = false
        light.Parent = heart
        tweenAfter(0.5, light, TweenInfo.new(1.1), { Brightness = 0 })

        -- a ring of light running out across the ground
        local ring = fx.neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(ground + Vector3.new(0, 0.03 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), KG.PETAL)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.35
        TweenService:Create(ring, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.03 * u, 10 * u, 10 * u), Transparency = 1 }):Play()

        -- golden motes rising off it
        if not reduced then
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre), KG.LIGHT)
            holder.Transparency = 1
            local motes = Instance.new("ParticleEmitter")
            motes.Texture = SPARKLE
            motes.Enabled = false
            motes.Shape = Enum.ParticleEmitterShape.Disc
            motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
            motes.Lifetime = NumberRange.new(0.8, 1.4)
            motes.Speed = NumberRange.new(0.8 * u, 2 * u)
            motes.SpreadAngle = Vector2.new(15, 15)
            motes.Acceleration = Vector3.new(0, 0.5 * u, 0)
            motes.Drag = 1.2
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(KG.LIGHT, KG.GOLD)
            motes.LightEmission = 1
            motes.LightInfluence = 0
            motes.Parent = holder
            holder.Size = Vector3.new(3 * u, 0.05, 3 * u)
            holder.CFrame = CFrame.new(centre)
            motes:Emit(36)
        end
    end

    local bones = table.clone(KG.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR", "LotusFL", "LotusFR", "LotusBL", "LotusBR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.GoldenKirin = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "Halo", "Tail3" },
        GlowColors = {
            fffaf0 = Color3.fromRGB(255, 252, 240), -- the catch-lights in its eyes
            ffe7a0 = Color3.fromRGB(255, 220, 130), -- its sunburst: warmer than drawn, or Neon blooms it to plain white
            ffd986 = Color3.fromRGB(255, 205, 110), -- the lotuses of light under its hooves
        },
        Effects = {
            Blast = "LotusBloom",
            Pulse = "Halo",
            NovaLight = 3,
        },
        Colors = {
            Gold = KG.GOLD,
            Amber = KG.DEEP,
            Orange = KG.DEEP,
            Sun = KG.LIGHT,
            Ivory = Color3.fromRGB(250, 246, 236),
        },
        Animate = animateGoldenKirin,
    }
end

do
    -- The Aqua Wisp (skinned): a small water seahorse, a current made into a creature. Sea-blue going to clear aqua, pale as foam on its belly, light
    -- netted over it; a crown of curling wave-crests, big ocean eyes, a short snout with a little round mouth, a see-through fan on its back and two
    -- little fins behind its cheeks, leafy fronds down its back, its tail curled into a spiral. It hovers upright, bobbing, its fan rippling fast as a
    -- real seahorse's does and its little fins fluttering; its tail slowly curls and lets out; it looks at you and tilts its head. Now and then it
    -- twirls round, curls its tail up tight, or blows a few bubbles. Moving, it leans into the current. Its special, Tide Spiral: it curls tight and
    -- twirls faster and faster (to 0.42); at the burst (Blasts.TideSpiral) three ribbons of water spiral up around it and burst into a shower of
    -- droplets, ripples running out across the ground; it arches up, wide-eyed, and settles.
    local AW = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        LID_HINGE = { L = Vector3.new(0.7599, -0.0683, -0.6464), R = Vector3.new(0.7599, 0.0683, 0.6464) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(56),
        BLINK_LOWER = math.rad(28),
        GLINTS = Vector3.new(0, 0.8339, -0.0725), -- the middle of its eyes' catch-lights piece, in the model's axes (metres): it stays where it was bound
        MOUTH = Vector3.new(0, 0.782, -0.198), -- the tip of its snout (aqua_wisp.py SNOUT), where its bubbles come from
        FOAM = Color3.fromRGB(236, 252, 255),
        AQUA = Color3.fromRGB(60, 196, 232),
        SEA = Color3.fromRGB(32, 128, 214),
        -- its stances, checked in Blender for torn skin (aqua_wisp.py's pose_library: CURL, LEAN, LOOK, TWIST, the fin wave and flap)
        LEAN = { Body = { -0.35, 0, 0 }, Chest = { -0.1, 0, 0 }, Head = { 0.25, 0, 0 } },
        BONES = { "Body", "Chest", "Neck", "Head", "Crest", "EyeL", "EyeR", "PecL", "PecR", "Dorsal1", "Dorsal2", "Dorsal3" },
    }
    for k = 1, 6 do
        table.insert(AW.BONES, "Tail" .. k)
    end

    function AW.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- where a point of the model (its axes, metres) is at rest in the world: measured from the catch-lights piece, which (a skinned part) stays where
    -- it was bound. Called before any pose.
    function AW.atRest(rig, point)
        local glints = rig.parts.Glints
        if not glints then
            return nil
        end
        return glints.Position + rig.rootPart.CFrame:VectorToWorldSpace((point - AW.GLINTS) * rig.meters)
    end

    -- its soft light, and where its bubbles come from: both on the head's bone
    function AW.glow(rig, s)
        s.glowMade = true
        local head = rig.points.Head
        local mouth = AW.atRest(rig, AW.MOUTH)
        if not (head and mouth) then
            return
        end
        local a = Instance.new("Attachment")
        a.Name = "Mouth"
        a.CFrame = head.TransformedWorldCFrame:ToObjectSpace(CFrame.new(mouth))
        a.Parent = head
        s.mouth = a
        local light = Instance.new("PointLight")
        light.Name = "PulseLight"
        light.Color = AW.AQUA
        light.Range = 4 * rig.unit
        light.Brightness = 0.9
        light.Shadows = false
        light.Parent = a
        rig.light = light
    end

    -- a few bubbles from its mouth, wobbling up and popping
    function AW.bubbles(rig, s, count)
        if not s.mouth or AW.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) or not rig.rootPart:IsDescendantOf(workspace) then
            return
        end
        local u = rig.unit
        for k = 1, count do
            task.delay((k - 1) * 0.22, function()
                if not s.mouth.Parent then
                    return
                end
                local size = (0.12 + 0.08 * math.random()) * u
                local from = s.mouth.WorldPosition
                local bubble = Instance.new("Part")
                bubble.Name = "Bubble"
                bubble.Shape = Enum.PartType.Ball
                bubble.Material = Enum.Material.Glass
                bubble.Color = AW.FOAM
                bubble.Transparency = 0.55
                bubble.Size = Vector3.one * size * 0.4
                bubble.Anchored = true
                bubble.CanCollide = false
                bubble.CanTouch = false
                bubble.CanQuery = false
                bubble.CastShadow = false
                bubble.CFrame = CFrame.new(from)
                bubble.Parent = rig.model
                local rise = 1.6 + 0.6 * math.random()
                local drift = Vector3.new((math.random() - 0.5) * 0.5, 0, (math.random() - 0.5) * 0.5) * u
                TweenService:Create(bubble, TweenInfo.new(rise, Enum.EasingStyle.Sine, Enum.EasingDirection.Out),
                    { CFrame = CFrame.new(from + Vector3.new(0, 1.4 * u, 0) + drift), Size = Vector3.one * size }):Play()
                tweenAfter(rise, bubble, TweenInfo.new(0.12), { Size = Vector3.one * size * 1.5, Transparency = 1 }) -- it pops
                Debris:AddItem(bubble, rise + 0.3)
            end)
        end
    end

    local function animateAquaWisp(rig, s, moving, fly, nova)
        if not s.glowMade then
            AW.glow(rig, s) -- before any pose: the head bone is at rest
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > AW.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)

        -- the special, Tide Spiral: it curls tight and twirls, faster and faster (to 0.42); at the burst it arches up, its tail flung open; it settles
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local wind = smoothstep(0.03, 0.4, progress) * (1 - smoothstep(0.42, 0.5, progress))
        local arch = smoothstep(0.41, 0.47, progress) * (1 - smoothstep(0.6, 0.85, progress))
        local spinTurns = if progress > 0 and progress < 0.42 then 2.5 * smoothstep(0.03, 0.42, progress) ^ 2 else 0
        local special = progress > 0

        -- now and then it twirls, curls its tail up tight, or blows bubbles
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget and not special then
            local r = math.random()
            s.fidgetAt, s.fidgetKind = t, if r < 0.35 then "twirl" elseif r < 0.65 then "curl" else "bubbles"
            s.nextFidget = t + 6 + math.random() * 6
            if s.fidgetKind == "bubbles" then
                AW.bubbles(rig, s, 3 + math.random(0, 2))
            end
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.4, 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - pace)
        local twirl = if s.fidgetKind == "twirl" and env < 1 then smoothstep(0, 1, env) * 2 * math.pi * (1 - pace) else 0

        local want = {}
        -- hovering upright, bobbing; leaning into the current when it moves
        local bob = math.sin(t * 1.4)
        addStance(want, AW.LEAN, pace * (0.6 + 0.4 * fly))
        addStance(want, { Body = { 0.04 * math.sin(t * 0.9) - 0.25 * arch, twirl + spinTurns * 2 * math.pi, 0.03 * math.sin(t * 0.7) } }, 1)

        -- its tail: slowly curling and letting out; tight in its fidget and its special; flung open as the spiral bursts; trailing when it moves
        local curl = 0.12 * math.sin(t * 0.8) + 0.35 * (if s.fidgetKind == "curl" then fidget else 0) + 0.45 * wind - 0.5 * arch - 0.18 * pace
        for k = 1, 6 do
            addStance(want, { ["Tail" .. k] = { -curl * (0.5 + 0.1 * k), 0.05 * math.sin(t * 1.1 - k * 0.6), 0 } }, 1)
        end

        -- its fan rippling fast, a wave running up it; its little fins fluttering; faster as it moves and as it winds up
        local beat = 18 + 10 * pace + 14 * wind
        s.beat = (s.beat or 0) + dt * beat
        local amp = 0.32 + 0.12 * pace + 0.1 * wind
        for k = 1, 3 do
            addStance(want, { ["Dorsal" .. k] = { 0, amp * math.sin(s.beat - k * 1.1), 0 } }, 1)
        end
        local flutter = math.sin(s.beat * 0.8)
        addStance(want, { PecL = { 0, 0.35 * flutter + 0.2, 0.15 * flutter }, PecR = { 0, -0.35 * flutter - 0.2, -0.15 * flutter } }, 1)

        -- its gaze: curious, often on you, the head tilting as it looks; up at the sky as the spiral bursts
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2 + math.random() * 3
            s.atYou = math.random() < 0.6
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.4
            s.tilt = (math.random() - 0.5) * 0.5
        end
        local calm = (1 - 0.6 * pace) * (1 - wind)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.3, 0.35) else s.gazePitch) * calm + 0.45 * arch
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
        s.headTilt = (s.headTilt or 0) + ((s.tilt or 0) * calm - (s.headTilt or 0)) * math.min(1, dt * 2)
        addStance(want, {
            Neck = { 0.3 * s.pitch + 0.02 * bob, 0.35 * s.yaw, 0 },
            Head = { 0.4 * s.pitch, 0.5 * s.yaw, s.headTilt },
            EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            Crest = { 0.08 * math.sin(t * 1.3), 0, 0.06 * math.sin(t * 0.9) - 0.15 * arch },
        }, 1)

        for _, name in AW.BONES do
            local a = want[name] or Vector3.zero
            local lift = if name == "Body" then (0.03 * bob + 0.05 * arch) * u else 0
            pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- the eyes: blinks; wide as the spiral bursts
        local wide = smoothstep(0.38, 0.44, progress) * (1 - smoothstep(0.65, 0.8, progress))
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.2
            if a >= 1 then
                s.nextBlink = t + 2.5 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = blink * (1 - wide)
        local upper = AW.BLINK_UPPER * close - math.rad(6) * wide
        local lower = AW.BLINK_LOWER * close - math.rad(5) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(AW.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(AW.LID_HINGE[side], lower))
        end
    end

    -- It has wound itself up, twirling (animateAquaWisp): three ribbons of water spiral up around it from the ground and burst at the top into a shower
    -- of droplets; ripples run out across the ground; then it all fades.
    local SPIRAL_TIME, SPIRAL_STEPS = 0.85, 14
    function Blasts.TideSpiral(rig, fx)
        local u = rig.unit
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local from = rig.rootPart.Position
        local hit = workspace:Raycast(from, Vector3.new(0, -10 * u, 0), params)
        local ground = if hit then hit.Position else from - Vector3.new(0, 1.5 * u, 0)
        local top = math.max(from.Y + 1.2 * u, ground.Y + 3.5 * u)
        local reduced = AW.reduced()
        local turn = math.random() * 2 * math.pi

        -- the ribbons: a bright head of water on each, a trail behind it, rising round it in a narrowing spiral
        local function spiral(k, f)
            local a = turn + (k - 1) * 2 * math.pi / 3 + f * 2.5 * math.pi
            local r = (1.7 - 0.9 * f) * u
            return Vector3.new(from.X + math.cos(a) * r, ground.Y + 0.1 * u + (top - ground.Y) * f, from.Z + math.sin(a) * r)
        end
        local step = SPIRAL_TIME / SPIRAL_STEPS
        for k = 1, 3 do
            local head = fx.neon(Vector3.one * 0.22 * u, CFrame.new(spiral(k, 0)), AW.FOAM)
            head.Shape = Enum.PartType.Ball
            local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
            a0.Position, a1.Position = Vector3.new(0, 0.14 * u, 0), Vector3.new(0, -0.14 * u, 0)
            a0.Parent, a1.Parent = head, head
            local trail = Instance.new("Trail")
            trail.Attachment0, trail.Attachment1 = a0, a1
            trail.Lifetime = 0.45
            trail.FaceCamera = true
            trail.LightEmission = 0.7
            trail.LightInfluence = 0.2
            trail.MinLength = 0
            trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.2) })
            trail.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, AW.FOAM), ColorSequenceKeypoint.new(0.4, AW.AQUA), ColorSequenceKeypoint.new(1, AW.SEA) })
            trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(1, 1) })
            trail.Parent = head
            for j = 1, SPIRAL_STEPS do
                tweenAfter((j - 1) * step, head, TweenInfo.new(step, Enum.EasingStyle.Linear), { CFrame = CFrame.new(spiral(k, j / SPIRAL_STEPS)) })
            end
            tweenAfter(SPIRAL_TIME, head, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.5 * u, Transparency = 1 })
        end

        -- the burst at the top: a splash of light, a shower of droplets falling round it
        local crown = fx.neon(Vector3.one * 0.1 * u, CFrame.new(from.X, top, from.Z), AW.FOAM)
        crown.Shape = Enum.PartType.Ball
        crown.Transparency = 1
        tweenAfter(SPIRAL_TIME, crown, TweenInfo.new(0.05), { Transparency = 0.2 })
        tweenAfter(SPIRAL_TIME + 0.05, crown, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.6 * u, Transparency = 1 })
        local light = Instance.new("PointLight")
        light.Color = AW.AQUA
        light.Range = 10 * u
        light.Brightness = 0
        light.Shadows = false
        light.Parent = crown
        tweenAfter(SPIRAL_TIME, light, TweenInfo.new(0.1), { Brightness = 2.5 })
        tweenAfter(SPIRAL_TIME + 0.15, light, TweenInfo.new(0.6), { Brightness = 0 })
        local drops = Instance.new("ParticleEmitter")
        drops.Texture = SPARKLE
        drops.Enabled = false
        drops.Lifetime = NumberRange.new(0.5, 0.8)
        drops.Speed = NumberRange.new(1.5 * u, 3.5 * u)
        drops.SpreadAngle = Vector2.new(70, 70)
        drops.Acceleration = Vector3.new(0, -9 * u, 0)
        drops.Drag = 0.5
        drops.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * u), NumberSequenceKeypoint.new(1, 0.04 * u) })
        drops.Color = ColorSequence.new(AW.FOAM, AW.AQUA)
        drops.LightEmission = 0.8
        drops.LightInfluence = 0.2
        drops.Parent = crown
        crown.CFrame = CFrame.lookAt(crown.Position, crown.Position + Vector3.yAxis)
        task.delay(SPIRAL_TIME, function()
            if drops.Parent then
                drops:Emit(if reduced then 14 else 40)
            end
        end)

        -- ripples running out across the ground, one after another
        for k = 1, (if reduced then 2 else 3) do
            local ring = fx.neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(ground + Vector3.new(0, 0.03 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), AW.AQUA)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 1
            local at = SPIRAL_TIME + 0.1 + (k - 1) * 0.15
            tweenAfter(at, ring, TweenInfo.new(0.05), { Transparency = 0.35 })
            tweenAfter(at + 0.05, ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.03 * u, (5 + k) * u, (5 + k) * u), Transparency = 1 })
        end
    end

    local bones = table.clone(AW.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.AquaWisp = {
        Skinned = true,
        Bones = bones,
        Points = { "Head" },
        GlowColors = {
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        },
        SeeThrough = { Fins = 0.35 }, -- its fan, its little fins and its fronds: clear water
        Effects = {
            Blast = "TideSpiral",
            Pulse = "Glints",
            NovaLight = 2,
        },
        Colors = {
            Gold = AW.AQUA,
            Amber = AW.SEA,
            Orange = AW.SEA,
            Sun = AW.FOAM,
            Ivory = AW.FOAM,
        },
        Animate = animateAquaWisp,
    }
end

do
    -- The Ember Wyrm (skinned): a campfire salamander. A chubby baby wyrm of charcoal crust cracked with glowing magma, ember spots down its flanks, a
    -- warm ember belly, sleepy ember eyes and coal-glow cheeks; a crest of little flames down its back and a tail tip that burns like a campfire. It
    -- sits low and content, breathing slowly, its flames flickering; it looks about, sleepy-eyed, and now and then wags its tail, sniffs the ground or
    -- stretches up proud; still a long while, it naps, its legs splayed flat and its tail curled round, its fire low. It walks with a salamander's
    -- sprawl, its body bending side to side; in the air it swims on nothing, legs swept back. Its special, Bonfire: it rears up proud and swings its
    -- burning tail up over its back (to 0.42); at the burst (Blasts.Bonfire) its campfire roars up into a bonfire, embers showering round it and a
    -- ring of fire running out across the ground; it settles, content.
    local EW = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOLE = 0.1577, -- metres from the middle of its box down to its pads: it stands on the ground (the box counts its RootPart, a 0.05 m cube
        -- at the origin reaching 0.025 m under its pads: half its height, 0.1702, floated it 1.25 cm, measured on the Volt Fox in Play)
        LID_HINGE = { L = Vector3.new(0.7722, 0.0578, -0.6328), R = Vector3.new(0.7722, -0.0578, 0.6328) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(70),
        BLINK_LOWER = math.rad(24),
        FLAME = Color3.fromRGB(255, 122, 30),
        CORE = Color3.fromRGB(255, 208, 74),
        HOT = Color3.fromRGB(255, 236, 170),
        EMBER = Color3.fromRGB(255, 92, 20),
        BONFIRE_FLAME = "rbxassetid://106209125427468", -- a cel-shaded tongue of its own fire, 4x4 looping flipbook (tools/vfx/wyrm_particles.py)
        TROT ={ FL = 0, BR = 0, FR = math.pi, BL = math.pi }, -- diagonal pairs together
        SIDE = { FL = 1, BL = 1, FR = -1, BR = -1 },
        -- its stances, each checked in Blender against the ground and for torn skin (ember_wyrm.py: NAP, PROUD, the walk, STOKE)
        NAP = { Head = { 0.12, 0.35, 0.1 }, Neck = { 0, 0.2, 0 }, Tail1 = { 0, -0.35, 0 }, Tail2 = { 0, -0.45, 0 }, Tail3 = { 0, -0.5, 0 }, Tail4 = { 0, -0.4, 0 },
            LegFL1 = { 0, 0, -0.25 }, LegBL1 = { 0, 0, -0.25 }, LegFR1 = { 0, 0, 0.25 }, LegBR1 = { 0, 0, 0.25 } },
        NAP_DROP = 0.03,
        PROUD = { Body = { 0.25, 0, 0 }, Chest = { 0.15, 0, 0 }, Neck = { -0.05, 0, 0 }, Head = { -0.2, 0, 0 }, Tail1 = { -0.15, 0, 0 },
            LegFL1 = { -0.35, 0, 0 }, LegFL2 = { 0.3, 0, 0 }, LegFR1 = { -0.35, 0, 0 }, LegFR2 = { 0.3, 0, 0 } },
        STOKE = { Tail1 = { -0.3, 0, 0 }, Tail2 = { -0.4, 0, 0 }, Tail3 = { -0.4, 0, 0 }, Tail4 = { -0.3, 0, 0 } },
        SNIFF = { Neck = { 0.25, 0, 0 }, Head = { 0.3, 0, 0 } },
        BONES = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "Tail1", "Tail2", "Tail3", "Tail4", "Campfire" },
    }
    for _, key in { "FL", "FR", "BL", "BR" } do
        table.insert(EW.BONES, "Leg" .. key .. "1")
        table.insert(EW.BONES, "Leg" .. key .. "2")
        table.insert(EW.BONES, "Hand" .. key)
    end

    function EW.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- its warm light and the embers drifting up off its campfire: both on the campfire's bone
    function EW.glow(rig, s)
        s.glowMade = true
        local fire = rig.points.Campfire
        if not fire then
            return
        end
        local a = Instance.new("Attachment")
        a.Name = "Fire"
        a.Position = Vector3.new(0, 0.08 * rig.meters, 0)
        a.Parent = fire
        s.fire = a
        local light = Instance.new("PointLight")
        light.Name = "PulseLight"
        light.Color = EW.FLAME
        light.Range = 5 * rig.unit
        light.Brightness = 1.2
        light.Shadows = false
        light.Parent = a
        rig.light = light
        if not EW.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
            local embers = Instance.new("ParticleEmitter")
            embers.Name = "Embers"
            embers.Texture = SPARKLE
            embers.Rate = 4
            embers.Lifetime = NumberRange.new(0.7, 1.3)
            embers.Speed = NumberRange.new(0.3 * rig.unit, 0.7 * rig.unit)
            embers.SpreadAngle = Vector2.new(25, 25)
            embers.Acceleration = Vector3.new(0, 0.4 * rig.unit, 0)
            embers.Drag = 1.2
            embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            embers.Color = ColorSequence.new(EW.HOT, EW.EMBER)
            embers.LightEmission = 1
            embers.LightInfluence = 0
            embers.EmissionDirection = Enum.NormalId.Top
            embers.Parent = a
            s.embers = embers
        end
    end

    local function animateEmberWyrm(rig, s, moving, fly, nova)
        if not s.glowMade then
            EW.glow(rig, s)
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > EW.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)
        local drop = dropToGround(rig, s, t, u, fly, EW.SOLE)

        -- the special, Bonfire: it rears up proud and swings its burning tail up over its back (to 0.42); the bonfire roars (0.42); it settles
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local rise = smoothstep(0.04, 0.34, progress) * (1 - smoothstep(0.55, 0.8, progress))
        local stoke = smoothstep(0.12, 0.4, progress) * (1 - smoothstep(0.6, 0.85, progress))
        local special = progress > 0

        -- still a long while, it naps; now and then it wags its tail, sniffs the ground or stretches up proud
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantNap = if s.still > 12 then 1 else 0
        s.nap = (s.nap or 0) + (wantNap - (s.nap or 0)) * math.min(1, dt * (if wantNap > (s.nap or 0) then 0.8 else 5))
        local nap = smoothstep(0, 1, s.nap)
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt, s.fidgetKind = t, if r < 0.4 then "wag" elseif r < 0.7 then "sniff" else "stretch"
            s.nextFidget = t + 6 + math.random() * 6
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.6, 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - nap) * (1 - rise)

        local want = {}
        addStance(want, EW.PROUD, math.max(rise, if s.fidgetKind == "stretch" then fidget * 0.6 else 0))
        addStance(want, EW.STOKE, stoke)
        addStance(want, EW.NAP, nap * (1 - rise))
        addStance(want, EW.SNIFF, if s.fidgetKind == "sniff" then fidget else 0)

        -- the sprawling walk: diagonal pairs reaching forward and lifted together, the body bending side to side; in the air it swims on nothing,
        -- legs swept back, its whole body waving
        s.stride = (s.stride or 0) + dt * (7 * moving + 5 * fly)
        local onFoot = moving * (1 - fly)
        local wave = math.sin(s.stride)
        addStance(want, { Hips = { 0, -0.2 * wave * onFoot - 0.25 * wave * fly, 0 }, Chest = { 0, 0.3 * wave * onFoot + 0.3 * wave * fly, 0 },
            Head = { 0, -0.2 * wave * pace, 0 } }, 1)
        for key, lead in EW.TROT do
            local phase = s.stride + lead
            local sd = EW.SIDE[key]
            local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
            addStance(want, { ["Leg" .. key .. "1"] = { 0, -sd * 0.45 * swing, -sd * 0.3 * lift } }, onFoot)
            -- swept back and tucked in the air (back is +yaw on the left, -yaw on the right; lifted, -z on the left, +z on the right)
            addStance(want, { ["Leg" .. key .. "1"] = { 0, sd * 0.6, -sd * 0.25 } }, fly)
        end

        -- breathing slowly; its head looking about, sleepy, often at you
        local breath = math.sin(t * 1.0)
        addStance(want, { Chest = { 0.02 * breath, 0, 0 }, Body = { 0.012 * breath, 0, 0 } }, 1)
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.5 + math.random() * 3.5
            s.atYou = math.random() < 0.5
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - 0.7 * pace) * (1 - rise) * (1 - 0.8 * nap)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.35) else s.gazePitch) * calm - 0.25 * rise
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
        addStance(want, {
            Neck = { 0.3 * s.pitch, 0.35 * s.yaw, 0 }, Head = { 0.4 * s.pitch, 0.5 * s.yaw, 0 },
            EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
        }, 1)

        -- its tail: a slow sway, a happy wag in its fidget, waving as it swims through the air
        local wag = if s.fidgetKind == "wag" then fidget else 0
        for k = 1, 4 do
            local sway = 0.06 * math.sin(t * 0.8 - k * 0.6) + 0.35 * wag * math.sin(t * 9 - k * 0.7) + (0.15 * onFoot + 0.3 * fly) * math.sin(s.stride - k * 0.9)
            addStance(want, { ["Tail" .. k] = { 0, sway, 0 } }, 1)
        end

        -- its campfire: flickering, a little wild
        local flick = math.sin(t * 13) * 0.6 + math.sin(t * 21 + 1.3) * 0.4
        addStance(want, { Campfire = { 0.06 * flick, 0.08 * math.sin(t * 7.3), 0.07 * math.sin(t * 11.1 + 0.4) } }, 1)

        for _, name in EW.BONES do
            local a = want[name] or Vector3.zero
            local lift = if name == "Hips" then (-EW.NAP_DROP * nap * (1 - rise) + 0.006 * onFoot * math.abs(wave)) * u - drop else 0
            pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- its flames flickering; low as it naps; the embers rising slower as it sleeps
        local flames, cores = rig.parts.Flames, rig.parts.Cores
        local flare = 0.5 + 0.5 * math.sin(t * 9 + math.sin(t * 3.7) * 2)
        if flames then
            flames.Color = EW.EMBER:Lerp(EW.FLAME, 0.6 + 0.4 * flare * (1 - 0.6 * nap))
        end
        if cores then
            cores.Color = EW.FLAME:Lerp(EW.CORE, 0.55 + 0.45 * flare * (1 - 0.6 * nap))
        end
        if s.embers then
            s.embers.Rate = 4 * (1 - 0.7 * nap) + 10 * stoke
        end

        -- the eyes: sleepy, slow blinks; closed as it naps; wide as its bonfire roars
        local wide = smoothstep(0.38, 0.45, progress) * (1 - smoothstep(0.6, 0.75, progress))
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.35
            if a >= 1 then
                s.nextBlink = t + 2.5 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = math.max(blink, nap) * (1 - wide)
        local upper = EW.BLINK_UPPER * close - math.rad(14) * wide
        local lower = EW.BLINK_LOWER * close - math.rad(6) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(EW.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(EW.LID_HINGE[side], lower))
        end
    end

    -- It has swung its tail up over its back (animateEmberWyrm): its campfire roars up into a bonfire, a column of flame with a bright heart, embers
    -- showering round it, a ring of fire running out across the ground; then it all dies down.
    function Blasts.Bonfire(rig, fx)
        local u = rig.unit
        local fire = rig.points.Campfire
        local at = if fire then fire.TransformedWorldCFrame.Position else fx.origin
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(rig.rootPart.Position, Vector3.new(0, -10 * u, 0), params)
        local ground = if hit then hit.Position else rig.rootPart.Position - Vector3.new(0, EW.SOLE * rig.meters, 0)
        local reduced = EW.reduced()

        -- the column: tongues of its own cel-shaded fire roaring up off its campfire for most of a second, big and fast at first, then dying down
        -- (painted in its flames' bands, so the texture's colour is drawn untinted). It pours from the campfire bone itself, so the column goes
        -- where its tail goes as it circles its owner; the flames left in the air stay where they rose.
        local column = Instance.new("ParticleEmitter")
        column.Texture = EW.BONFIRE_FLAME
        column.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        column.FlipbookMode = Enum.ParticleFlipbookMode.Loop
        column.FlipbookFramerate = NumberRange.new(20, 28)
        column.FlipbookStartRandom = true
        -- (the bone turns as the tail swings over: a small launch any way, and the world's up does the rising)
        column.SpreadAngle = Vector2.new(180, 180)
        column.Speed = NumberRange.new(0.6 * u, 1.4 * u)
        column.Acceleration = Vector3.new(0, 10 * u, 0)
        column.Drag = 0.8
        column.Lifetime = NumberRange.new(0.5, 0.8)
        column.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9 * u, 0.2 * u), NumberSequenceKeypoint.new(0.2, 1.45 * u, 0.25 * u),
            NumberSequenceKeypoint.new(1, 0.35 * u, 0.1 * u) }) -- wide at its foot, licking up to a point
        column.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.08, 0), NumberSequenceKeypoint.new(0.7, 0.05), NumberSequenceKeypoint.new(1, 1) })
        column.Rotation = NumberRange.new(-8, 8)
        column.RotSpeed = NumberRange.new(-15, 15)
        column.LightEmission = 0.3
        column.LightInfluence = 0
        column.Brightness = 1.3
        column.ZOffset = 0.3
        column.Rate = if reduced then 22 else 55
        if fire then
            column.Parent = fire
            Debris:AddItem(column, 2)
        else
            local base = fx.neon(Vector3.one * 0.05, CFrame.new(at), EW.FLAME)
            base.Transparency = 1
            column.Parent = base
        end
        column:Emit(if reduced then 4 else 8)
        tweenAfter(0.45, column, TweenInfo.new(0.4), { Rate = if reduced then 5 else 12 })
        task.delay(0.85, function()
            column.Enabled = false
        end)
        local light = Instance.new("PointLight")
        light.Color = EW.FLAME
        light.Range = 12 * u
        light.Brightness = 2 -- (at 3 it washed the charcoal of its own hide out to orange)
        light.Shadows = false
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(at + Vector3.new(0, 1 * u, 0)), EW.CORE)
        holder.Transparency = 1
        light.Parent = holder
        tweenAfter(0.4, light, TweenInfo.new(1.1), { Brightness = 0 })

        -- embers showering up and falling round it
        if not reduced then
            local embers = Instance.new("ParticleEmitter")
            embers.Texture = SPARKLE
            embers.Enabled = false
            embers.Lifetime = NumberRange.new(0.6, 1.1)
            embers.Speed = NumberRange.new(2.5 * u, 5 * u)
            embers.SpreadAngle = Vector2.new(35, 35)
            embers.Acceleration = Vector3.new(0, -6 * u, 0)
            embers.Drag = 0.6
            embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(1, 0) })
            embers.Color = ColorSequence.new(EW.HOT, EW.EMBER)
            embers.LightEmission = 1
            embers.LightInfluence = 0
            embers.Parent = holder
            holder.CFrame = CFrame.lookAt(holder.Position, holder.Position + Vector3.yAxis)
            embers:Emit(45)
        end

        -- a ring of fire running out across the ground
        local ring = fx.neon(Vector3.new(0.04 * u, 0.6 * u, 0.6 * u), CFrame.new(ground + Vector3.new(0, 0.04 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), EW.FLAME)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.3
        TweenService:Create(ring, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.04 * u, 8 * u, 8 * u), Transparency = 1 }):Play()
    end

    local bones = table.clone(EW.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.EmberWyrm = {
        Skinned = true,
        Bones = bones,
        Points = { "Campfire" },
        GlowColors = {
            fff4e0 = Color3.fromRGB(255, 246, 228), -- the catch-lights in its eyes
            ff7a1e = EW.FLAME, -- its flames
            ffd04a = EW.CORE, -- the bright hearts of its flames, seen through them
        },
        SeeThroughGlow = { ff7a1e = 0.35 }, -- (Neon is solid: an opaque flame hid its yellow heart)
        Effects = {
            Blast = "Bonfire",
            NovaLight = 3,
        },
        Colors = {
            Gold = EW.CORE,
            Amber = EW.EMBER,
            Orange = EW.FLAME,
            Sun = EW.HOT,
            Ivory = Color3.fromRGB(255, 220, 180),
        },
        Animate = animateEmberWyrm,
    }
end

do
    -- The Lunar Hopper (skinned): the jade rabbit of the moon. A round, soft rabbit sat up on its big flat feet, pearl white with a cool moonlit sheen;
    -- long lop ears hanging beside its full cheeks, their tips dipped in moonlight; big moonstone eyes and a crescent of moonlight on its brow; in its
    -- front paws a little jade pestle for pounding the moon's elixir. It sits breathing softly, its nose twitching, looking about with its big eyes;
    -- now and then it flicks an ear, perks both up, wiggles its tail or gives its pestle a couple of little taps; still a long while, it loafs down,
    -- ears laid back and eyes shut. It moves in soft, floaty hops that hang a moment at the top (its lore: each leap lands a little further from the
    -- ground than it should), its ears trailing, a puff of moon dust where it lands; in the air it floats, feet trailing and ears streaming. Its
    -- special, Moon Elixir: it raises its pestle and pounds three times, each stroke chiming; on the third (the burst, 0.42, Blasts.MoonElixir) the
    -- elixir bursts into light, a ring of little moons running out across the ground and motes of moonlight rising; it holds its pestle up, proud.
    local LH = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOLE = 0.2508, -- metres from the middle of its box down to its soles: it sits on the ground (the box counts its RootPart, a 0.05 m cube
        -- at the origin reaching 0.025 m under its soles: half its height, 0.2633, floated it 1.25 cm, measured on the Volt Fox in Play)
        LID_HINGE = { L = Vector3.new(0.8775, -0.1038, -0.4682), R = Vector3.new(0.8775, 0.1038, 0.4682) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(66),
        BLINK_LOWER = math.rad(22),
        MOON = Color3.fromRGB(143, 188, 255),
        GLOW = Color3.fromRGB(214, 232, 255),
        PEARL = Color3.fromRGB(244, 242, 250),
        BROW = Color3.fromRGB(70, 128, 255), -- its crescent's Neon: deeper than its moonlight blue (Neon brightens: at 8fbcff it read white)
        BROW_BRIGHT = Color3.fromRGB(125, 175, 255),
        CRESCENT = "rbxassetid://74795285586917", -- a little crescent moon of light (tools/vfx/hopper_particles.py)
        HOP_RATE = 2.0, -- hops a second at a full run
        HOP = 0.075, -- metres: how high it hops
        -- its stances (game axes; left values, the right mirrored), each checked in Blender against the ground and for torn skin (lunar_hopper.py)
        CROUCH = { Body = { -0.2, 0, 0 }, Chest = { -0.08, 0, 0 }, Head = { 0.12, 0, 0 }, EarL1 = { 0, 0.25, 0 }, EarR1 = { 0, -0.25, 0 },
            EarL2 = { -0.2, 0, 0 }, EarR2 = { -0.2, 0, 0 }, ArmL1 = { -0.2, 0, 0 }, ArmR1 = { -0.2, 0, 0 } },
        LEAP = { Body = { -0.3, 0, 0 }, Chest = { -0.1, 0, 0 }, Head = { 0.3, 0, 0 }, EarL1 = { 0, 0.35, -0.2 }, EarR1 = { 0, -0.35, 0.2 },
            EarL2 = { -0.45, 0, 0 }, EarR2 = { -0.45, 0, 0 }, LegL1 = { -0.15, 0, 0 }, LegR1 = { -0.15, 0, 0 }, FootL = { -0.3, 0, 0 }, FootR = { -0.3, 0, 0 },
            ArmL1 = { 0.2, 0, 0 }, ArmR1 = { 0.2, 0, 0 }, Tail = { -0.25, 0, 0 } },
        LOAF = { Body = { -0.14, 0, 0 }, Chest = { -0.05, 0, 0 }, Head = { -0.2, 0, 0 }, EarL1 = { 0, 0.45, 0.12 }, EarR1 = { 0, -0.45, -0.12 },
            EarL2 = { -0.3, 0, 0 }, EarR2 = { -0.3, 0, 0 }, ArmL1 = { -0.25, 0, 0 }, ArmR1 = { -0.25, 0, 0 } },
        POUND_UP = { ArmL1 = { 0.5, 0, 0 }, ArmR1 = { 0.5, 0, 0 }, ArmL2 = { 0.25, 0, 0 }, ArmR2 = { 0.25, 0, 0 }, Body = { 0.12, 0, 0 }, Head = { 0.18, 0, 0 },
            EarL1 = { 0, 0.2, -0.15 }, EarR1 = { 0, -0.2, 0.15 } },
        POUND_DOWN = { ArmL1 = { -0.25, 0, 0 }, ArmR1 = { -0.25, 0, 0 }, ArmL2 = { -0.2, 0, 0 }, ArmR2 = { -0.2, 0, 0 }, Body = { -0.15, 0, 0 }, Head = { -0.12, 0, 0 },
            EarL2 = { 0.25, 0, 0 }, EarR2 = { 0.25, 0, 0 } },
        HOVER = { LegL1 = { -0.12, 0, 0 }, LegR1 = { -0.12, 0, 0 }, FootL = { -0.3, 0, 0 }, FootR = { -0.3, 0, 0 }, EarL1 = { 0, 0.3, 0 }, EarR1 = { 0, -0.3, 0 },
            EarL2 = { -0.3, 0, 0 }, EarR2 = { -0.3, 0, 0 }, Tail = { -0.2, 0, 0 } },
        PERK = { EarL1 = { 0, 0, -0.3 }, EarR1 = { 0, 0, 0.3 }, EarL2 = { 0.2, 0, 0 }, EarR2 = { 0.2, 0, 0 } },
        BONES = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "EarL1", "EarL2", "EarR1", "EarR2", "ArmL1", "ArmL2", "PawL", "ArmR1", "ArmR2",
            "PawR", "Pestle", "LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR", "Tail" },
    }

    function LH.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- its moonlight: a soft light at its brow, a point between its paws where it grips its pestle (where its strokes chime and its elixir bursts), a
    -- puff of moon dust for its landings
    function LH.glow(rig, s)
        s.glowMade = true
        local u = rig.meters
        -- (offsets are placed in the world and carried into each bone's own frame: every bone has its own rest turn, so a fixed offset in a
        -- bone's axes lands somewhere else, as the first try at its pestle's end did)
        local head, pawL, pawR = rig.points.Head, rig.points.PawL, rig.points.PawR
        local up = rig.rootPart.CFrame.UpVector
        if head then
            local a = Instance.new("Attachment")
            a.Name = "Moonlight"
            local frame = head.TransformedWorldCFrame
            a.Position = frame:PointToObjectSpace(frame.Position + up * 0.15 * u)
            a.Parent = head
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = LH.MOON
            light.Range = 4 * rig.unit
            light.Brightness = 0.6
            light.Shadows = false
            light.Parent = a
            rig.light = light
        end
        if pawL and pawR then
            local grip = Instance.new("Attachment")
            grip.Name = "Grip"
            local mid = (pawL.TransformedWorldCFrame.Position + pawR.TransformedWorldCFrame.Position) / 2
            grip.Position = pawL.TransformedWorldCFrame:PointToObjectSpace(mid)
            grip.Parent = pawL
            rig.grip = grip
            local chime = Instance.new("ParticleEmitter")
            chime.Name = "Chime"
            chime.Texture = SPARKLE
            chime.Enabled = false
            chime.Lifetime = NumberRange.new(0.3, 0.55)
            chime.Speed = NumberRange.new(0.8 * rig.unit, 1.6 * rig.unit)
            chime.SpreadAngle = Vector2.new(180, 180)
            chime.Drag = 3
            chime.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            chime.Color = ColorSequence.new(LH.GLOW, LH.MOON)
            chime.LightEmission = 1
            chime.LightInfluence = 0
            chime.Parent = grip
            s.chime = chime
        end
        if not LH.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
            local feet = Instance.new("Attachment")
            feet.Name = "Landing"
            feet.Position = Vector3.new(0, -LH.SOLE * u, 0)
            feet.Parent = rig.rootPart
            local dust = Instance.new("ParticleEmitter")
            dust.Name = "MoonDust"
            dust.Texture = SPARKLE
            dust.Enabled = false
            dust.Lifetime = NumberRange.new(0.4, 0.8)
            dust.Speed = NumberRange.new(0.4 * rig.unit, 0.9 * rig.unit)
            dust.SpreadAngle = Vector2.new(70, 70)
            dust.Acceleration = Vector3.new(0, 0.5 * rig.unit, 0)
            dust.Drag = 2
            dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.08 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            dust.Color = ColorSequence.new(LH.GLOW, LH.MOON)
            dust.Transparency = NumberSequence.new(0.2, 1)
            dust.LightEmission = 0.8
            dust.LightInfluence = 0
            dust.EmissionDirection = Enum.NormalId.Top
            dust.Parent = feet
            s.dust = dust
        end
    end

    local function animateLunarHopper(rig, s, moving, fly, nova)
        if not s.glowMade then
            LH.glow(rig, s)
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > LH.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)
        local drop = dropToGround(rig, s, t, u, fly, LH.SOLE)

        -- the special, Moon Elixir: its pestle raised (to 0.14), three strokes (the third at the burst, 0.42), held up proud, then settling
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local raise = smoothstep(0.02, 0.14, progress) * (1 - smoothstep(0.62, 0.82, progress))
        local stroke = 0
        for _, at in { 0.2, 0.31, 0.42 } do
            stroke = math.max(stroke, math.max(0, 1 - math.abs(progress - at) / 0.035))
        end
        local proud = smoothstep(0.44, 0.52, progress) * (1 - smoothstep(0.62, 0.82, progress))
        if special then
            for k, at in { 0.2, 0.31 } do
                if progress >= at and (s.chimed or 0) < k and s.chime then
                    s.chimed = k
                    s.chime:Emit(if LH.reduced() then 4 else 10)
                end
            end
        else
            s.chimed = 0
        end

        -- still a long while, it loafs; now and then it flicks an ear, perks both up, wiggles its tail or taps its pestle
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantNap = if s.still > 12 then 1 else 0
        s.nap = (s.nap or 0) + (wantNap - (s.nap or 0)) * math.min(1, dt * (if wantNap > (s.nap or 0) then 0.8 else 5))
        local nap = smoothstep(0, 1, s.nap)
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.3 then "flick" elseif r < 0.55 then "perk" elseif r < 0.78 then "wiggle" else "tap"
            s.flickSide = if math.random() < 0.5 then 1 else -1
            s.nextFidget = t + 5 + math.random() * 6
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.4, 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - nap) * (1 - raise)

        local want = {}
        addStance(want, LH.LOAF, nap * (1 - raise))
        addStance(want, LH.POUND_UP, math.max(raise * (1 - stroke), proud))
        addStance(want, LH.POUND_DOWN, raise * stroke)
        addStance(want, LH.PERK, math.max(proud, if s.fidgetKind == "perk" then fidget else 0))
        if s.fidgetKind == "flick" then
            local side = s.flickSide or 1
            local key = if side > 0 then "L" else "R"
            local flick = fidget * (0.6 + 0.4 * math.sin(t * 18))
            addStance(want, { ["Ear" .. key .. "1"] = { 0, 0, -0.45 * side }, ["Ear" .. key .. "2"] = { 0.3, 0, -0.2 * side } }, flick)
        elseif s.fidgetKind == "tap" then
            local tap = math.max(0, math.sin(env * math.pi * 4))
            addStance(want, LH.POUND_UP, fidget * 0.45 * (1 - tap))
            addStance(want, LH.POUND_DOWN, fidget * 0.35 * tap)
        end

        -- its hops: a crouch, a floaty leap that hangs a moment at the top, a soft landing; ears trailing; moon dust where it lands. In the air it
        -- floats, feet trailing and ears streaming.
        local onFoot = moving * (1 - fly)
        s.hopAmt = (s.hopAmt or 0) + (math.min(1, onFoot * 1.6) - (s.hopAmt or 0)) * math.min(1, dt * 4)
        local hopAmt = s.hopAmt
        if hopAmt > 0.02 then
            s.hop = ((s.hop or 0) + dt * LH.HOP_RATE * math.max(0.6, hopAmt)) % 1
        else
            s.hop = 0
        end
        local p = s.hop
        local air = if p > 0.12 and p < 0.74 then (p - 0.12) / 0.62 else -1
        local arc = if air >= 0 then math.sin(math.pi * air) ^ 0.7 else 0 -- (^0.7: it hangs at the top a moment)
        local crouch = math.max(0, 1 - math.abs(p - 0.05) / 0.08, 1 - math.abs(p - 0.82) / 0.1) * hopAmt
        local leap = (if air >= 0 then math.sin(math.pi * air) else 0) * hopAmt
        local fall = (if air >= 0 then math.max(0, -math.cos(math.pi * air)) else 0) * hopAmt
        addStance(want, LH.CROUCH, crouch)
        addStance(want, LH.LEAP, leap)
        addStance(want, { EarL1 = { 0, 0, -0.3 }, EarR1 = { 0, 0, 0.3 } }, fall) -- its ears float up as it comes down
        local landed = air < 0 and p >= 0.74
        if landed and not s.landed and hopAmt > 0.4 and s.dust then
            s.dust:Emit(5)
        end
        s.landed = landed
        local float = math.sin(t * 2.2)
        addStance(want, LH.HOVER, fly)
        addStance(want, { Body = { 0.04 * float, 0, 0 }, EarL2 = { -0.15 * float, 0, 0 }, EarR2 = { -0.15 * float, 0, 0 } }, fly)

        -- breathing softly, its nose twitching now and then; its head looking about, often at you
        local breath = math.sin(t * 1.4)
        addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Body = { 0.01 * breath, 0, 0 } }, 1)
        s.nextTwitch = s.nextTwitch or t + 2
        local twitch = 0
        if t >= s.nextTwitch then
            local a = (t - s.nextTwitch) / 0.5
            if a >= 1 then
                s.nextTwitch = t + 1.5 + math.random() * 3.5
            else
                twitch = math.sin(a * math.pi * 6) * (1 - a)
            end
        end
        addStance(want, { Head = { 0.025 * twitch, 0, 0 } }, (1 - nap) * (1 - pace))
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.2 + math.random() * 3
            s.atYou = math.random() < 0.55
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.1, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - 0.7 * pace) * (1 - raise) * (1 - 0.8 * nap)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.35) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
        addStance(want, {
            Neck = { 0.15 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.3 * s.pitch, 0.4 * s.yaw, 0.1 * s.yaw },
            EyeL = { 0.25 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.25 * s.pitch, 0.25 * s.yaw, 0 },
        }, 1)

        -- its ears swaying softly; its tail: a wiggle in its fidget
        local sway = math.sin(t * 0.9)
        addStance(want, { EarL2 = { 0.05 * sway, 0, 0 }, EarR2 = { 0.05 * math.sin(t * 0.9 + 0.8), 0, 0 } }, 1 - nap)
        local wiggle = if s.fidgetKind == "wiggle" then fidget else 0
        addStance(want, { Tail = { 0, 0.45 * math.sin(t * 16), 0 } }, wiggle)

        local lift = (LH.HOP * arc * hopAmt) * u - drop
        for _, name in LH.BONES do
            local a = want[name] or Vector3.zero
            pose(m[name], CFrame.new(0, if name == "Hips" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- its crescent breathing with soft light; brightest as its elixir bursts
        local crescent = rig.parts.Crescent
        if crescent then
            crescent.Color = LH.BROW:Lerp(LH.BROW_BRIGHT, math.clamp(0.35 + 0.3 * math.sin(t * 1.3) + 0.65 * proud, 0, 1))
        end
        if rig.light then
            rig.light.Brightness = 0.6 + 1.2 * proud
        end

        -- the eyes: blinks; closed as it loafs; wide as its elixir bursts and when it perks up
        local wide = math.max(proud, if s.fidgetKind == "perk" then fidget else 0)
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.25
            if a >= 1 then
                s.nextBlink = t + 2 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = math.max(blink, nap) * (1 - wide)
        local upper = LH.BLINK_UPPER * close - math.rad(12) * wide
        local lower = LH.BLINK_LOWER * close - math.rad(6) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(LH.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(LH.LID_HINGE[side], lower))
        end
    end

    -- Its third stroke (animateLunarHopper): a little moon of elixir lifts out of its pestle and rises to hang above its head (0.35 s); it bursts: a
    -- flash of moonlight, a ring of crescent moons spilling out round it and settling across the ground, motes of moonlight rising; then it all fades.
    function Blasts.MoonElixir(rig, fx)
        local u = rig.unit
        -- where its paws grip the pestle now: through the bone's animated frame (an attachment's WorldPosition leaves the bone's pose out)
        local grip = rig.grip
        local at = if grip and grip.Parent and grip.Parent:IsA("Bone") then grip.Parent.TransformedWorldCFrame:PointToWorldSpace(grip.Position) else fx.origin
        local head = rig.points.Head
        -- (its head's bone is down at its jaw: its crown is 0.18 m above it, and the little moon hangs a hand's breadth over that)
        local top = (if head then head.TransformedWorldCFrame.Position else rig.rootPart.Position) + Vector3.new(0, 0.34 * rig.meters, 0)
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(rig.rootPart.Position, Vector3.new(0, -10 * u, 0), params)
        local ground = if hit then hit.Position else rig.rootPart.Position - Vector3.new(0, LH.SOLE * rig.meters, 0)
        local reduced = LH.reduced()
        local RISE, HANG = 0.35, 0.15

        -- the little moon: lifting out of its pestle and rising over its head, a soft light going with it
        local moon = fx.neon(Vector3.one * 0.2 * u, CFrame.new(at), LH.BROW_BRIGHT)
        moon.Shape = Enum.PartType.Ball
        moon.Transparency = 0.05
        TweenService:Create(moon, TweenInfo.new(RISE, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { CFrame = CFrame.new(top), Size = Vector3.one * 0.5 * u }):Play()
        local light = Instance.new("PointLight")
        light.Color = LH.MOON
        light.Range = 6 * u
        light.Brightness = 1.2
        light.Shadows = false
        light.Parent = moon
        tweenAfter(RISE, moon, TweenInfo.new(HANG, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Size = Vector3.one * 0.62 * u }) -- it hangs there a beat, swelling
        tweenAfter(RISE + HANG, light, TweenInfo.new(0.12), { Brightness = 3, Range = 12 * u })
        tweenAfter(RISE + HANG + 0.2, light, TweenInfo.new(0.9), { Brightness = 0 })
        -- its burst: swelling and fading in a flash (in the pale moonlight colour Neon washed white against its fur: its brighter brow blue)
        tweenAfter(RISE + HANG, moon, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 2.6 * u, Transparency = 1 })

        task.delay(RISE + HANG, function()
            if not moon.Parent then
                return
            end
            -- a ring of crescent moons spilling out from it and settling across the ground round it, each turned its own way: billboards riding
            -- tweened anchors (as particles, a tween does not carry them, and flown on speed and drag they stayed hidden in the burst)
            local count = if reduced then 5 else 8
            for k = 1, count do
                local a = (k - 1) / count * 2 * math.pi + 0.3
                local out = Vector3.new(math.cos(a), 0, math.sin(a))
                local rest = ground + out * 3.2 * u + Vector3.new(0, 0.6 * u, 0)
                local anchor = fx.neon(Vector3.one * 0.05, CFrame.new(top), LH.MOON)
                anchor.Transparency = 1
                local board = Instance.new("BillboardGui")
                board.Size = UDim2.fromScale(0.5 * u, 0.5 * u)
                board.LightInfluence = 0
                board.Brightness = 1.3
                board.Parent = anchor
                local image = Instance.new("ImageLabel")
                image.BackgroundTransparency = 1
                image.Size = UDim2.fromScale(1, 1)
                image.Image = LH.CRESCENT
                image.Rotation = math.deg(a) + 90
                image.Parent = board
                TweenService:Create(anchor, TweenInfo.new(0.9, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { CFrame = CFrame.new(rest) }):Play()
                TweenService:Create(board, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = UDim2.fromScale(1.3 * u, 1.3 * u) }):Play()
                tweenAfter(0.85, image, TweenInfo.new(0.45), { ImageTransparency = 1 })
            end
            -- motes of moonlight rising from where it burst
            if not reduced then
                local motes = Instance.new("ParticleEmitter")
                motes.Texture = SPARKLE
                motes.Enabled = false
                motes.Lifetime = NumberRange.new(0.8, 1.3)
                motes.Speed = NumberRange.new(1.5 * u, 3.5 * u)
                motes.SpreadAngle = Vector2.new(180, 180)
                motes.Acceleration = Vector3.new(0, 1.2 * u, 0)
                motes.Drag = 1.8
                motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15 * u), NumberSequenceKeypoint.new(1, 0) })
                motes.Color = ColorSequence.new(LH.GLOW, LH.MOON)
                motes.LightEmission = 1
                motes.LightInfluence = 0
                motes.Parent = moon
                motes:Emit(32)
            end
        end)
    end

    local bones = table.clone(LH.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.LunarHopper = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "PawL", "PawR" },
        GlowColors = {
            f4f8ff = Color3.fromRGB(244, 248, 255), -- the catch-lights in its eyes
            ["8fbcff"] = LH.BROW, -- the crescent on its brow
        },
        Effects = {
            Blast = "MoonElixir",
            NovaLight = 2,
        },
        Colors = {
            Gold = LH.GLOW,
            Amber = LH.MOON,
            Orange = LH.MOON,
            Sun = LH.PEARL,
            Ivory = LH.PEARL,
        },
        Animate = animateLunarHopper,
    }
end

do
    -- The Volt Fox (skinned): a thundercloud fox kit, after the raijū, the thunder beast of the old stories that runs in the storm clouds. A storm-grey
    -- kit with a big head, a short pale muzzle and great ears forked at their tips in electric blue; zigzag bolts of blue down its legs and on its
    -- cheeks; bright storm-blue eyes. Its tail is a short stalk carrying a little thundercloud of its own, lightning flickering inside it and hanging
    -- under it. It stands alert, its cloud drifting over it; it looks about, often at you; now and then it flicks an ear, sits down a while, drops
    -- into a playful bow with its cloud wagging, or looks up as its cloud rumbles; still a long while, it sits and nods off, its cloud dimming. It
    -- trots, diagonal pairs together, its cloud bobbing along behind; in the air it runs on nothing, legs stretched, its cloud trailing. Its special,
    -- Thunder Comes Home: it lifts its cloud high, the cloud billowing up dark and flashing (to 0.42); a bolt leaps from it over its head and strikes
    -- the ground in front of it (Blasts.ThunderComesHome); the strike becomes a ball of lightning that bounces back to it and leaps home into its
    -- cloud (0.81), which flashes bright; it shakes out its fur, pleased.
    local VF = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOLE = 0.2537, -- metres from the middle of its box down to its paws: it stands on the ground (the box counts its RootPart, a 0.05 m cube at
        -- the origin, so it reaches 0.025 m under its paws: half its height, 0.2662, left it floating 1.25 cm, measured in Play)
        LID_HINGE = { L = Vector3.new(0.8206, -0.1693, -0.5458), R = Vector3.new(0.8206, 0.1693, 0.5458) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(70), -- (the two add past the 94 degrees between the lids' edges: at 62 + 22 a slit of iris showed)
        BLINK_LOWER = math.rad(30),
        CLOUD_CENTRE = Vector3.new(0, 0.085, 0.03), -- metres from its Cloud bone to the middle of its cloud (game axes: up, back)
        BOLT = Color3.fromRGB(40, 160, 255), -- its lightning's Neon: deeper than its 7fe8ff paint (Neon brightens pale colours to white)
        BOLT_HOT = Color3.fromRGB(150, 228, 255),
        SPARK = Color3.fromRGB(196, 246, 255),
        STORM = Color3.fromRGB(70, 80, 112), -- its cloud's billows
        STORM_DIM = Color3.fromRGB(30, 70, 120), -- its lightning as it dozes
        STRIDE = 10, -- radians of its trot a second at a full run
        -- its trot (volt_fox.py TROT_FRONT, TROT_HIND, searched over the cycle in Blender): per leg, swing = sin(phase), lift = max(0, cos(phase));
        -- Leg1 = a*swing + b*lift, Leg2 = c*lift, Paw = d*lift + e*max(0, swing). Lifted 1.8 to 3.3 cm, planted within 5 mm of the ground.
        TROT_LEAD = { FL = 0, BR = 0, FR = math.pi, BL = math.pi }, -- diagonal pairs together
        TROT_FRONT = { 0.26, 0.62, -1.2, 0.5, -0.6 },
        TROT_HIND = { 0.3, 0, 0.75, 0.1, -0.15 },
        -- its stances (game axes; the right side mirrors y and z), each checked in Blender against the ground and for torn skin (volt_fox.py)
        SIT = { Body = { 0.36, 0, 0 }, Chest = { 0.1, 0, 0 }, Neck = { -0.12, 0, 0 }, Head = { -0.14, 0, 0 }, Tail1 = { 0.3, 0, 0 },
            LegFL1 = { -0.5, 0, 0 }, LegFR1 = { -0.5, 0, 0 }, PawFL = { 0.45, 0, 0 }, PawFR = { 0.45, 0, 0 },
            LegBL1 = { 1.55, 0, 0 }, LegBR1 = { 1.55, 0, 0 }, LegBL2 = { -2.45, 0, 0 }, LegBR2 = { -2.45, 0, 0 }, PawBL = { 0.9, 0, 0 }, PawBR = { 0.9, 0, 0 } },
        SIT_DROP = 0.042, -- metres its hips come down as it sits
        DOZE = { Neck = { -0.18, 0, 0 }, Head = { -0.24, 0.12, 0.08 }, EarL = { 0.4, 0, 0.1 }, EarR = { 0.4, 0, -0.1 }, Tail1 = { 0.12, 0, 0 } }, -- over SIT
        BOW = { Body = { -0.25, 0, 0 }, Chest = { -0.1, 0, 0 }, Neck = { 0.22, 0, 0 }, Head = { 0.22, 0, 0 }, Tail1 = { -0.45, 0, 0 },
            EarL = { -0.15, 0, 0 }, EarR = { -0.15, 0, 0 }, LegFL1 = { 0.9, 0, 0 }, LegFR1 = { 0.9, 0, 0 }, LegFL2 = { -0.1, 0, 0 }, LegFR2 = { -0.1, 0, 0 },
            PawFL = { -0.6, 0, 0 }, PawFR = { -0.6, 0, 0 }, LegBL1 = { 0.15, 0, 0 }, LegBR1 = { 0.15, 0, 0 }, PawBL = { -0.1, 0, 0 }, PawBR = { -0.1, 0, 0 } },
        RAISE = { Tail1 = { -0.6, 0, 0 }, Neck = { 0.18, 0, 0 }, Head = { 0.32, 0, 0 }, EarL = { -0.2, 0, -0.15 }, EarR = { -0.2, 0, 0.15 }, Body = { 0.08, 0, 0 } },
        FLY = { Tail1 = { 0.25, 0, 0 }, EarL = { 0.45, 0, 0 }, EarR = { 0.45, 0, 0 }, LegFL1 = { 0.5, 0, 0 }, LegFR1 = { 0.5, 0, 0 }, LegFL2 = { -0.35, 0, 0 },
            LegFR2 = { -0.35, 0, 0 }, LegBL1 = { -0.5, 0, 0 }, LegBR1 = { -0.5, 0, 0 }, LegBL2 = { 0.4, 0, 0 }, LegBR2 = { 0.4, 0, 0 } },
        LOOK_UP = { Neck = { 0.15, 0, 0 }, Head = { 0.35, 0, 0 }, EarL = { 0.3, 0, 0 }, EarR = { 0.3, 0, 0 } }, -- up at its rumbling cloud, ears back
        WATCH = { Neck = { -0.1, 0, 0 }, Head = { -0.2, 0, 0 }, EarL = { -0.2, 0, -0.1 }, EarR = { -0.2, 0, 0.1 } }, -- down at the ball of lightning, ears pricked
        FIDGET_TIME = { flick = 0.8, sit = 5, bow = 2.4, rumble = 2.2 },
        HOME = 0.81, -- the ball of lightning reaches its cloud (Blasts.ThunderComesHome: 1.0 s after the strike at 0.42 of 2.6 s)
        BONES = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2", "Cloud" },
    }
    for _, key in { "FL", "FR", "BL", "BR" } do
        table.insert(VF.BONES, "Leg" .. key .. "1")
        table.insert(VF.BONES, "Leg" .. key .. "2")
        table.insert(VF.BONES, "Paw" .. key)
    end

    function VF.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- inside its cloud: a light that flashes with its lightning, and the storm billowing out round it as it gathers itself for its special
    function VF.glow(rig, s)
        s.glowMade = true
        local cloud = rig.points.Cloud
        if not cloud then
            return
        end
        -- (placed in the world and carried into the bone's own frame: every bone has its own rest turn)
        local frame = cloud.TransformedWorldCFrame
        local root = rig.rootPart.CFrame
        local centre = frame.Position + root.UpVector * VF.CLOUD_CENTRE.Y * rig.meters - root.LookVector * VF.CLOUD_CENTRE.Z * rig.meters
        s.cloudOffset = frame:PointToObjectSpace(centre)
        local a = Instance.new("Attachment")
        a.Name = "Storm"
        a.Position = s.cloudOffset
        a.Parent = cloud
        local light = Instance.new("PointLight")
        light.Name = "StormLight"
        light.Color = VF.BOLT_HOT
        light.Range = 4 * rig.unit
        light.Brightness = 0
        light.Shadows = false
        light.Parent = a
        s.stormLight = light -- (its own, not rig.light: the shared pulse would set it every frame and wash out the flicker)
        if not VF.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
            local billow = Instance.new("ParticleEmitter")
            billow.Name = "Billow"
            billow.Texture = "rbxasset://textures/particles/smoke_main.dds"
            billow.Rate = 0
            billow.Lifetime = NumberRange.new(0.6, 1.0)
            billow.Speed = NumberRange.new(0.3 * rig.unit, 0.7 * rig.unit)
            billow.SpreadAngle = Vector2.new(180, 180)
            billow.Drag = 2
            billow.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5 * rig.unit), NumberSequenceKeypoint.new(1, 1.3 * rig.unit) })
            billow.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.45), NumberSequenceKeypoint.new(1, 1) })
            billow.Color = ColorSequence.new(VF.STORM)
            billow.RotSpeed = NumberRange.new(-40, 40)
            billow.Rotation = NumberRange.new(0, 360)
            billow.LightInfluence = 0.6
            billow.Parent = a
            s.billow = billow
        end
    end

    local function animateVoltFox(rig, s, moving, fly, nova)
        if not s.glowMade then
            VF.glow(rig, s)
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > VF.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)
        local drop = dropToGround(rig, s, t, u, fly, VF.SOLE)

        -- the special, Thunder Comes Home: its cloud lifted high and billowing, rumbling and flashing (to 0.42); the strike (0.42); it watches the
        -- ball of lightning bounce back to it, looks up as it leaps home into its cloud (0.81), and shakes out its fur
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local charge = smoothstep(0.02, 0.3, progress) * (1 - smoothstep(0.43, 0.55, progress))
        local watch = smoothstep(0.44, 0.52, progress) * (1 - smoothstep(0.66, 0.74, progress))
        local look = smoothstep(0.66, 0.76, progress) * (1 - smoothstep(0.84, 0.92, progress))
        local shake = smoothstep(0.82, 0.85, progress) * (1 - smoothstep(0.9, 0.98, progress))
        local wide = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.6, 0.72, progress))
        if not special then
            s.homeAt = nil
        end
        local home = if s.homeAt then math.exp(-(t - s.homeAt) * 5) else 0

        -- still a long while, it sits and nods off; now and then it flicks an ear, sits a while, drops into a bow or looks up at its rumbling cloud
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantDoze = if s.still > 12 then 1 else 0
        s.doze = (s.doze or 0) + (wantDoze - (s.doze or 0)) * math.min(1, dt * (if wantDoze > (s.doze or 0) then 0.8 else 5))
        local doze = smoothstep(0, 1, s.doze)
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.32 then "flick" elseif r < 0.55 then "sit" elseif r < 0.8 then "bow" else "rumble"
            s.flickSide = if math.random() < 0.5 then 1 else -1
            s.nextFidget = t + VF.FIDGET_TIME[s.fidgetKind] + 3 + math.random() * 5
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / VF.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
        local calmness = (1 - pace) * (1 - doze) * (1 - math.max(charge, watch, look))
        local fidget = (if s.fidgetKind == "sit" then smoothstep(0, 0.12, env) * (1 - smoothstep(0.88, 1, env)) else math.sin(math.pi * env)) * calmness
        local function kind(name)
            return if s.fidgetKind == name then fidget else 0
        end
        local rumble = math.max(kind("rumble"), charge)

        local want = {}
        local sitting = math.max(doze, kind("sit")) * (1 - charge)
        addStance(want, VF.SIT, sitting)
        addStance(want, VF.DOZE, doze * (1 - charge))
        addStance(want, VF.BOW, kind("bow"))
        addStance(want, VF.RAISE, charge)
        addStance(want, VF.LOOK_UP, math.max(kind("rumble"), look))
        addStance(want, VF.WATCH, watch)
        if s.fidgetKind == "flick" then
            local side = s.flickSide or 1
            local flick = kind("flick") * (0.6 + 0.4 * math.sin(t * 20))
            addStance(want, { [if side > 0 then "EarL" else "EarR"] = { 0.45, 0, 0.3 * side } }, flick)
        end

        -- its trot: diagonal pairs together, each leg lifted as it swings forward; in the air it runs on nothing, legs stretched out and paddling
        local onFoot = moving * (1 - fly)
        s.stride = (s.stride or 0) + dt * VF.STRIDE * math.max(onFoot, 0.6 * fly)
        for key, lead in VF.TROT_LEAD do
            local swing, lift = math.sin(s.stride + lead), math.max(0, math.cos(s.stride + lead))
            local k = if string.sub(key, 1, 1) == "F" then VF.TROT_FRONT else VF.TROT_HIND
            addStance(want, {
                ["Leg" .. key .. "1"] = { k[1] * swing + k[2] * lift, 0, 0 },
                ["Leg" .. key .. "2"] = { k[3] * lift, 0, 0 },
                ["Paw" .. key] = { k[4] * lift + k[5] * math.max(0, swing), 0, 0 },
            }, onFoot)
            addStance(want, { ["Leg" .. key .. "1"] = { 0.15 * swing, 0, 0 } }, fly)
        end
        addStance(want, VF.FLY, fly)
        local beat = math.sin(2 * s.stride)
        addStance(want, { Body = { 0.02 * beat, 0, 0 }, Head = { -0.03 * beat, 0, 0 } }, onFoot)

        -- breathing; its head looking about, often at you
        local breath = math.sin(t * 1.5)
        addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Body = { 0.01 * breath, 0, 0 } }, 1)
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2 + math.random() * 3
            s.atYou = math.random() < 0.55
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - 0.7 * pace) * (1 - math.max(charge, watch, look, kind("rumble"))) * (1 - 0.8 * doze)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.35) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3.5)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3.5)
        addStance(want, {
            Neck = { 0.15 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.3 * s.pitch, 0.4 * s.yaw, 0.12 * s.yaw },
            EyeL = { 0.25 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.25 * s.pitch, 0.25 * s.yaw, 0 },
        }, 1)
        -- shaking out its fur once its thunder is home
        addStance(want, { Body = { 0, 0, 0.12 * math.sin(t * 38) }, Chest = { 0, 0, -0.1 * math.sin(t * 38) }, Head = { 0, 0, 0.14 * math.sin(t * 38 + 0.6) } }, shake)

        -- its tail and cloud: drifting slowly; wagging in its bow; bobbing behind its trot; trailing in the air; shuddering as it rumbles
        local drift = math.sin(t * 0.8)
        addStance(want, { Tail1 = { 0.04 * math.sin(t * 0.6), 0.1 * drift, 0 }, Tail2 = { 0, 0.08 * math.sin(t * 0.8 - 0.7), 0 },
            Cloud = { 0.05 * math.sin(t * 1.1 - 1.2), 0.06 * math.sin(t * 0.7), 0.04 * math.sin(t * 0.9 + 0.5) } }, 1 - 0.6 * doze)
        addStance(want, { Tail1 = { 0, 0.45 * math.sin(t * 13), 0 }, Tail2 = { 0, 0.3 * math.sin(t * 13 - 0.8), 0 } }, kind("bow"))
        addStance(want, { Tail1 = { 0, 0.12 * math.sin(s.stride), 0 }, Cloud = { 0.1 * math.sin(2 * s.stride - 0.9), 0, 0.05 * math.sin(s.stride - 0.6) } }, onFoot)
        addStance(want, { Tail2 = { 0.15 * math.sin(t * 3), 0, 0 }, Cloud = { 0.08 * math.sin(t * 2.6), 0.1 * math.sin(t * 1.9), 0 } }, fly)
        local jolt = rumble * 0.05
        addStance(want, { Cloud = { jolt * math.sin(t * 47), jolt * math.sin(t * 39 + 1), jolt * math.sin(t * 53 + 2) } }, 1)

        local lift = -VF.SIT_DROP * sitting * u - drop
        for _, name in VF.BONES do
            local a = want[name] or Vector3.zero
            pose(m[name], CFrame.new(0, if name == "Hips" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- the lightning in its cloud: flickering now and then, often as it rumbles, rarely as it dozes; its light flashing with it
        s.nextFlicker = s.nextFlicker or 0
        if t >= s.nextFlicker then
            s.nextFlicker = t + 0.06 + math.random() * 0.1
            local chance = (0.1 + 0.5 * rumble) * (1 - 0.8 * doze)
            s.flash = if math.random() < chance then 1 else 0
        end
        local flash = math.max(s.flash or 0, home)
        local bolts = rig.parts.Lightning
        if bolts then
            bolts.Transparency = 0.55 * (1 - flash)
            bolts.Color = (VF.BOLT:Lerp(VF.STORM_DIM, 0.6 * doze)):Lerp(VF.BOLT_HOT, flash)
        end
        if s.stormLight then
            s.stormLight.Brightness = 1.4 * flash + 2.5 * home
            s.stormLight.Range = (4 + 6 * home) * rig.unit
        end
        if s.billow then
            s.billow.Rate = if charge > 0.05 then 18 * charge else 0
        end

        -- the eyes: blinks; shut as it dozes; wide at the strike
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.22
            if a >= 1 then
                s.nextBlink = t + 2 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = math.max(blink, doze) * (1 - wide)
        local upper = VF.BLINK_UPPER * close - math.rad(12) * wide
        local lower = VF.BLINK_LOWER * close - math.rad(6) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(VF.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(VF.LID_HINGE[side], lower))
        end
    end

    -- Its cloud lifted high (animateVoltFox): a bolt leaps from it, arcing over its head, and strikes the ground in front of it twice; the strike
    -- becomes a crackling ball of lightning (the thunder beast's own form) that bounces back to it in two hops and leaps home into its cloud.
    function Blasts.ThunderComesHome(rig, fx)
        local u, metre = rig.unit, rig.meters
        local s = rig.state
        local reduced = VF.reduced()
        local cloud = rig.points.Cloud
        local function cloudAt()
            if cloud and cloud.Parent then
                return cloud.TransformedWorldCFrame:PointToWorldSpace(s.cloudOffset or Vector3.zero)
            end
            return rig.rootPart.Position + Vector3.new(0, 0.3 * metre, 0)
        end
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local function groundAt(at)
            local hit = workspace:Raycast(at + Vector3.new(0, 0.6 * metre, 0), Vector3.new(0, -10 * u, 0), params)
            return if hit then hit.Position else Vector3.new(at.X, rig.rootPart.Position.Y - VF.SOLE * metre, at.Z)
        end
        local root = rig.rootPart.CFrame
        local strike = groundAt(root.Position + root.LookVector * 0.55 * metre)
        local from = cloudAt()

        -- the bolt: from its cloud up over its head and down into the ground, jagged all the way (each kink thrown sideways off the line), a fork
        -- or two off it; a hot core in a soft blue sleeve; it strikes, blinks out, strikes again. (With three and five kinks thrown any way it read
        -- as a smooth tent over its head, seen in Play.)
        local segments = {}
        local function jag(a, b, kinks, width, color, wander)
            local last = a
            local line = b - a
            local side = line:Cross(Vector3.yAxis)
            side = if side.Magnitude > 1e-3 then side.Unit else root.RightVector
            local across = line.Unit:Cross(side)
            for k = 1, kinks do
                local at = a:Lerp(b, k / kinks)
                if k < kinks then
                    local span = line.Magnitude / kinks
                    at += (side * (math.random() - 0.5) * 2 + across * (math.random() - 0.5)) * span * wander
                end
                local length = (at - last).Magnitude
                if length > 1e-3 then
                    local cf = CFrame.lookAt((last + at) / 2, at)
                    table.insert(segments, fx.neon(Vector3.new(width, width, length), cf, color))
                    local sleeve = fx.neon(Vector3.new(width * 3, width * 3, length + width), cf, VF.BOLT)
                    sleeve.Transparency = 0.7
                    sleeve:SetAttribute("Sleeve", true)
                    table.insert(segments, sleeve)
                end
                last = at
            end
            return last
        end
        -- it turns 0.3 m over its head bone, just clear of its ear tips. (Not over its root: the follow floats the root half a metre up and its
        -- hips are pulled back down to the ground, so a turn set off the root stood 0.8 m high, measured in Play.)
        local headBone = rig.points.Head
        local brow = if headBone then headBone.TransformedWorldCFrame.Position else root.Position
        local over = brow + Vector3.yAxis * 0.3 * metre + root.LookVector * 0.06 * metre
        jag(from, over, 5, 0.06 * u, VF.BOLT_HOT, 0.55)
        jag(over, strike, 8, 0.08 * u, VF.BOLT_HOT, 0.6)
        local forks = if reduced then 1 else 2
        for k = 1, forks do
            local base = over:Lerp(strike, 0.25 + 0.25 * k)
            local out = (root.RightVector * (if k == 1 then 1 else -1) * 0.22 - root.UpVector * 0.16) * metre
            jag(base, base + out, 4, 0.035 * u, VF.BOLT_HOT, 0.5)
        end
        for _, seg in segments do
            local shown = seg.Transparency
            task.delay(0.07, function()
                seg.Transparency = 1
            end)
            task.delay(0.11, function()
                seg.Transparency = shown
            end)
            tweenAfter(0.2, seg, TweenInfo.new(0.22), { Transparency = 1 })
        end

        -- the strike: a flash of light, sparks thrown up off the ground
        local flashHolder = fx.neon(Vector3.one * 0.05, CFrame.new(strike + Vector3.new(0, 0.3 * metre, 0)), VF.BOLT_HOT)
        flashHolder.Transparency = 1
        local light = Instance.new("PointLight")
        light.Color = VF.BOLT_HOT
        light.Range = 14 * u
        light.Brightness = 2.5 -- (at 4 it washed its grey fur out to white)
        light.Shadows = false
        light.Parent = flashHolder
        task.delay(0.07, function()
            light.Brightness = 0.4
        end)
        task.delay(0.11, function()
            light.Brightness = 2.5
        end)
        tweenAfter(0.2, light, TweenInfo.new(0.5), { Brightness = 0 })
        local sparkHolder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(strike, strike + Vector3.yAxis), VF.SPARK)
        sparkHolder.Transparency = 1
        local sparks = Instance.new("ParticleEmitter")
        sparks.Texture = SPARKLE
        sparks.Enabled = false
        sparks.Lifetime = NumberRange.new(0.3, 0.6)
        sparks.Speed = NumberRange.new(3 * u, 6 * u)
        sparks.SpreadAngle = Vector2.new(60, 60)
        sparks.Acceleration = Vector3.new(0, -14 * u, 0)
        sparks.Drag = 1
        sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * u), NumberSequenceKeypoint.new(1, 0) })
        sparks.Color = ColorSequence.new(VF.SPARK, VF.BOLT)
        sparks.LightEmission = 1
        sparks.LightInfluence = 0
        sparks.Parent = sparkHolder
        sparks:Emit(if reduced then 12 else 28)

        -- the ball of lightning: born in the strike, crackling; two hops back to it, then a leap home into its cloud
        local R = 0.07 * metre
        local ball = fx.neon(Vector3.one * 0.02 * u, CFrame.new(strike + Vector3.new(0, R, 0)), VF.BOLT)
        ball.Shape = Enum.PartType.Ball
        ball.Transparency = 0.05
        TweenService:Create(ball, TweenInfo.new(0.15, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.one * 2 * R }):Play()
        local glow = Instance.new("PointLight")
        glow.Color = VF.BOLT
        glow.Range = 6 * u
        glow.Brightness = 1.6
        glow.Shadows = false
        glow.Parent = ball
        -- its crackle: three little arcs round it, re-struck twenty times a second wherever it is
        local arcs = {}
        for k = 1, (if reduced then 2 else 3) do
            local arc = fx.neon(Vector3.new(0.03 * u, 0.03 * u, 0.1), ball.CFrame, VF.BOLT_HOT)
            arc.Transparency = 1
            arcs[k] = arc
        end
        task.spawn(function()
            while ball.Parent and ball.Transparency < 0.95 do
                local centre = ball.Position
                local r = ball.Size.X / 2
                for _, arc in arcs do
                    local a = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5)
                    local b = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5)
                    if a.Magnitude > 1e-3 and b.Magnitude > 1e-3 then
                        local p, q = centre + a.Unit * r * 1.1, centre + b.Unit * r * 1.6
                        arc.Size = Vector3.new(0.03 * u, 0.03 * u, (q - p).Magnitude)
                        arc.CFrame = CFrame.lookAt((p + q) / 2, q)
                        arc.Transparency = if math.random() < 0.75 then 0 else 1
                    end
                end
                task.wait(0.05)
            end
            for _, arc in arcs do
                arc.Transparency = 1
            end
        end)
        local function hop(to, height, time, after)
            local start = ball.Position
            local apex = (start + to) / 2 + Vector3.new(0, height, 0)
            TweenService:Create(ball, TweenInfo.new(time / 2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(apex) }):Play()
            tweenAfter(time / 2, ball, TweenInfo.new(time / 2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = CFrame.new(to) })
            task.delay(time, after)
        end
        local function landing(at)
            if reduced or not ball.Parent then
                return
            end
            local holder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(at, at + Vector3.yAxis), VF.SPARK)
            holder.Transparency = 1
            local puff = sparks:Clone()
            puff.Speed = NumberRange.new(1.5 * u, 3 * u)
            puff.Parent = holder
            puff:Emit(10)
        end
        task.delay(0.15, function()
            if not ball.Parent then
                return
            end
            local now = rig.rootPart.CFrame
            local nearer = groundAt(strike:Lerp(now.Position + now.LookVector * 0.3 * metre, 0.5)) + Vector3.new(0, R, 0)
            hop(nearer, 0.22 * metre, 0.28, function()
                landing(nearer - Vector3.new(0, R, 0))
                if not ball.Parent then
                    return
                end
                local here = rig.rootPart.CFrame
                local feet = groundAt(here.Position + here.LookVector * 0.3 * metre) + Vector3.new(0, R, 0)
                hop(feet, 0.15 * metre, 0.24, function()
                    landing(feet - Vector3.new(0, R, 0))
                    if not ball.Parent then
                        return
                    end
                    -- the leap home: rising fast into its cloud, wherever its cloud is by now
                    local leap = 0.33
                    local start = ball.Position
                    local conn
                    local began = os.clock()
                    conn = RunService.Heartbeat:Connect(function()
                        local f = math.clamp((os.clock() - began) / leap, 0, 1)
                        if not ball.Parent then
                            conn:Disconnect()
                            return
                        end
                        local target = cloudAt()
                        local e = f * f
                        ball.CFrame = CFrame.new(start:Lerp(target, e) + Vector3.new(0, 0.12 * metre * math.sin(math.pi * f), 0))
                        ball.Size = Vector3.one * 2 * R * (1 - 0.6 * e)
                        if f >= 1 then
                            conn:Disconnect()
                            ball.Transparency = 1
                            glow.Enabled = false
                            s.homeAt = s.time -- its cloud flashes (animateVoltFox)
                        end
                    end)
                end)
            end)
        end)
    end

    local bones = table.clone(VF.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.VoltFox = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "Cloud" },
        GlowColors = {
            f6fbff = Color3.fromRGB(246, 251, 255), -- the catch-lights in its eyes
            ["7fe8ff"] = VF.BOLT, -- the lightning in and under its cloud
        },
        SeeThrough = { Cloud = 0.22 }, -- its cloud: the lightning shows through it
        Effects = {
            Blast = "ThunderComesHome",
            NovaLight = 2,
        },
        Colors = {
            Gold = VF.BOLT_HOT,
            Amber = VF.BOLT,
            Orange = VF.BOLT,
            Sun = VF.SPARK,
            Ivory = Color3.fromRGB(214, 222, 236),
        },
        Animate = animateVoltFox,
    }
end

do
    -- The Astral Whale (skinned): the starsong humpback. A humpback calf: a big soft head with knobbly tubercles along its rostrum, a gentle smile
    -- arching back to its eye, a deep throat pleated from chin to navel, a small dorsal fin on a hump, wide notched flukes and long wing-like
    -- flippers knobbed along their leading edge. Its skin is the sky at dusk from the zenith down: night indigo on its back with faint stars, dusk
    -- violet, a band of rose, pearl beneath. In the grooves of its throat lie golden strings; the knobs of its flippers are small pale stars. It
    -- swims in the air in slow strokes, bobbing, flippers gliding, and looks at you often; its strings breathe softly and its stars twinkle. Now
    -- and then it spouts a puff of stardust, waves a flipper, hums (a ripple of light runs along its strings) or rolls over slowly; left alone a
    -- long while it sleeps as humpbacks do, tilted head-up, eyes shut, its strings dim. Its special, Song Between Stars: it rolls belly-up and
    -- arches into its song, its strings shimmering like a strummed harp; at the burst (Blasts.SongBetweenStars) three golden rings of sound ripple
    -- out through the air, and each faint star hanging round it chimes bright as a ring reaches it; it rolls back and spouts stardust.
    local AWH = {
        FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
        LID_HINGE = { L = Vector3.new(0.4959, -0.1035, -0.8622), R = Vector3.new(0.4959, 0.1035, 0.8622) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(66), -- (with the lower, past the 88 degrees between the lids' edges: they meet)
        BLINK_LOWER = math.rad(30),
        GLINTS = Vector3.new(0, 0.2895, -0.2392), -- the middle of its eyes' catch-lights piece, in the model's axes (metres): it stays where it was bound
        BLOWHOLE = Vector3.new(0, 0.396, -0.236), -- on top of its head (astral_whale.py BLOWHOLES)
        GOLD = Color3.fromRGB(255, 176, 48), -- its strings' Neon: a saturated gold (a pale one blooms white)
        GOLD_DIM = Color3.fromRGB(150, 92, 24),
        GOLD_HOT = Color3.fromRGB(255, 214, 120),
        STAR = Color3.fromRGB(110, 160, 255),
        STAR_HOT = Color3.fromRGB(205, 225, 255),
        DUSK = Color3.fromRGB(160, 120, 235),
        PEARL = Color3.fromRGB(236, 232, 244),
        -- its swimming stroke: each bone's share (astral_whale.py SWIM_UP / SWIM_DOWN, checked in Blender), and how far behind the head it moves
        SWIM = { { "Head", -0.06, 0 }, { "Spine1", 0.08, 0.5 }, { "Spine2", 0.14, 1.0 }, { "Tail", 0.2, 1.5 }, { "Fluke", 0.32, 2.0 } },
        -- its stances (game axes; the right flipper mirrors y and z), each checked in Blender for torn skin (astral_whale.py)
        GLIDE = { PecL1 = { 0, 0.45, -0.1 }, PecL2 = { 0, 0.15, 0 }, PecR1 = { 0, -0.45, 0.1 }, PecR2 = { 0, -0.15, 0 } },
        SING = { Head = { 0.26, 0, 0 }, Chest = { 0.08, 0, 0 }, Spine1 = { -0.1, 0, 0 }, Spine2 = { -0.14, 0, 0 }, Tail = { -0.16, 0, 0 }, Fluke = { -0.22, 0, 0 },
            PecL1 = { 0, -0.35, -0.3 }, PecL2 = { 0, -0.1, -0.15 }, PecR1 = { 0, 0.35, 0.3 }, PecR2 = { 0, 0.1, 0.15 } },
        SLEEP_TILT = 0.35, -- radians its body tilts head-up as it sleeps (at 0.6 it read as an odd lean, seen in Play)
        SLEEP_LIFT = 0.15, -- metres it rises as it tilts, so its flukes stay where they hung
        ROLL = 0.85 * math.pi, -- how far over it rolls to sing (belly-up)
        FIDGET_TIME = { spout = 1.6, wave = 2.2, hum = 2.4, roll = 2.8 },
        BONES = { "Body", "Chest", "Head", "Spine1", "Spine2", "Tail", "Fluke", "EyeL", "EyeR", "PecL1", "PecL2", "PecR1", "PecR2" },
    }

    function AWH.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- where a point of the model (its axes, metres) is at rest in the world: measured from the catch-lights piece, which (a skinned part) stays where
    -- it was bound. Called before any pose.
    function AWH.atRest(rig, point)
        local glints = rig.parts.Glints
        if not glints then
            return nil
        end
        return glints.Position + rig.rootPart.CFrame:VectorToWorldSpace((point - AWH.GLINTS) * rig.meters)
    end

    -- its blowhole, where its stardust spouts from: on its head's bone
    function AWH.glow(rig, s)
        s.glowMade = true
        local head = rig.points.Head
        local at = AWH.atRest(rig, AWH.BLOWHOLE)
        if not head or not at or AWH.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
            return
        end
        local a = Instance.new("Attachment")
        a.Name = "Blowhole"
        a.Position = head.TransformedWorldCFrame:PointToObjectSpace(at)
        a.Parent = head
        local spout = Instance.new("ParticleEmitter")
        spout.Name = "Stardust"
        spout.Texture = SPARKLE
        spout.Enabled = false
        spout.Lifetime = NumberRange.new(0.7, 1.2)
        spout.Speed = NumberRange.new(2.2 * rig.unit, 3.4 * rig.unit)
        spout.SpreadAngle = Vector2.new(14, 14)
        spout.Acceleration = Vector3.new(0, -2.2 * rig.unit, 0)
        spout.Drag = 1.2
        spout.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
        spout.Color = ColorSequence.new(AWH.STAR_HOT, AWH.DUSK)
        spout.LightEmission = 1
        spout.LightInfluence = 0
        spout.EmissionDirection = Enum.NormalId.Top
        spout.Parent = a
        s.spout = spout
    end

    local function animateAstralWhale(rig, s, moving, fly, nova)
        if not s.glowMade then
            AWH.glow(rig, s)
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > AWH.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)

        -- the special, Song Between Stars: it rolls belly-up and arches into its song (to 0.4), its strings shimmering; the burst (0.42); it rolls
        -- back (0.72 to 0.92) and spouts stardust
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local roll = smoothstep(0.03, 0.3, progress) * (1 - smoothstep(0.72, 0.92, progress))
        local sing = smoothstep(0.12, 0.38, progress) * (1 - smoothstep(0.75, 0.9, progress))
        local wide = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.62, 0.74, progress))
        if special then
            if progress >= 0.9 and not s.spouted then
                s.spouted = true
                if s.spout then
                    s.spout:Emit(18)
                end
            end
        else
            s.spouted = false
        end

        -- left alone a long while it sleeps, tilted head-up; now and then it spouts, waves a flipper, hums or rolls over
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantSleep = if s.still > 14 then 1 else 0
        s.sleep = (s.sleep or 0) + (wantSleep - (s.sleep or 0)) * math.min(1, dt * (if wantSleep > (s.sleep or 0) then 0.5 else 4))
        local sleep = smoothstep(0, 1, s.sleep)
        s.nextFidget = s.nextFidget or t + 5
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.3 then "spout" elseif r < 0.55 then "wave" elseif r < 0.8 then "hum" else "roll"
            s.waveSide = if math.random() < 0.5 then "L" else "R"
            s.spoutDone = false
            s.nextFidget = t + AWH.FIDGET_TIME[s.fidgetKind] + 5 + math.random() * 6
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / AWH.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
        local free = (1 - pace) * (1 - sleep) * (1 - roll)
        local fidget = math.sin(math.pi * env) * free
        local function kind(name)
            return if s.fidgetKind == name then fidget else 0
        end
        if s.fidgetKind == "spout" and env >= 0.35 and not s.spoutDone and free > 0.5 then
            s.spoutDone = true
            if s.spout then
                s.spout:Emit(12)
            end
        end

        local want = {}
        -- its swimming stroke: a slow wave down its spine to its flukes, stronger as it moves; asleep, barely
        s.stroke = (s.stroke or 0) + dt * (1.5 + 3.5 * pace) * (1 - 0.6 * sleep)
        local amp = (0.45 + 0.55 * pace) * (1 - 0.7 * sleep) * (1 - 0.6 * sing)
        for _, row in AWH.SWIM do
            addStance(want, { [row[1]] = { row[2] * math.sin(s.stroke - row[3]), 0, 0 } }, amp)
        end
        -- its flippers: gliding, a slow easy flap; swept back as it moves; spread wide as it sings; one waved in its fidget; drooping asleep
        local flap = 0.12 * math.sin(t * 0.9) * (1 - pace) * (1 - sleep)
        addStance(want, { PecL1 = { 0, 0, flap }, PecR1 = { 0, 0, -flap }, PecL2 = { 0, 0, 0.5 * flap }, PecR2 = { 0, 0, -0.5 * flap } }, 1)
        addStance(want, AWH.GLIDE, pace * (1 - sing))
        addStance(want, AWH.SING, sing)
        addStance(want, { PecL1 = { 0, 0, 0.22 }, PecR1 = { 0, 0, -0.22 } }, sleep)
        local wave = kind("wave")
        if wave > 0 then
            local sd = if s.waveSide == "L" then 1 else -1
            local key = "Pec" .. s.waveSide
            addStance(want, { [key .. "1"] = { 0, 0, sd * (-0.45 + 0.12 * math.sin(t * 7)) }, [key .. "2"] = { 0, 0, sd * 0.2 * math.sin(t * 7 - 0.8) } }, wave)
        end
        -- its head: looking about, often at you; lifting a little as it spouts or hums
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.5 + math.random() * 3.5
            s.atYou = math.random() < 0.6
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.8, (math.random() - 0.5) * 0.2
        end
        local calm = (1 - 0.7 * pace) * (1 - roll) * (1 - sleep)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.5, 0.5) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.15, 0.25) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
        addStance(want, { Head = { 0.25 * s.pitch + 0.12 * math.max(kind("spout"), kind("hum")), 0.3 * s.yaw, 0 }, Chest = { 0.1 * s.pitch, 0.15 * s.yaw, 0 },
            EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 } }, 1)

        -- its whole body: bobbing; rolled belly-up to sing, or slowly right over in its fidget; tilted head-up asleep
        local bob = math.sin(t * 0.8)
        local rollTurn = AWH.ROLL * roll + 2 * math.pi * smoothstep(0.1, 0.9, if s.fidgetKind == "roll" then env else 0) * (if s.fidgetKind == "roll" then 1 else 0)
        local bodyTurn = Vector3.new(0.03 * bob + AWH.SLEEP_TILT * sleep, 0.04 * math.sin(s.stroke * 0.5) * pace, rollTurn)
        local lift = (0.035 * bob + AWH.SLEEP_LIFT * sleep + 0.06 * roll) * u

        for _, name in AWH.BONES do
            local a = want[name] or Vector3.zero
            if name == "Body" then
                pose(m.Body, CFrame.new(0, lift, 0) * CFrame.Angles(a.X + bodyTurn.X, a.Y + bodyTurn.Y, a.Z + bodyTurn.Z))
            else
                pose(m[name], CFrame.Angles(a.X, a.Y, a.Z))
            end
        end

        -- its golden strings: breathing softly; a ripple of light running along them as it hums; shimmering like a strummed harp as it sings; dim
        -- asleep. Its stars twinkle, brightest as it sings.
        local hum = kind("hum")
        local strum = math.max(sing, hum)
        for k, key in { "StringsA", "StringsB" } do
            local part = rig.parts[key]
            if part then
                local rest = 0.45 + 0.25 * math.sin(t * 1.2 + k * 1.6)
                local shimmer = 0.5 + 0.5 * math.sin(t * (if sing > hum then 16 else 6) + k * math.pi)
                local glow = (rest * (1 - strum) + (0.55 + 0.45 * shimmer) * strum) * (1 - 0.6 * sleep)
                part.Color = if glow < 0.5 then AWH.GOLD_DIM:Lerp(AWH.GOLD, glow * 2) else AWH.GOLD:Lerp(AWH.GOLD_HOT, (glow - 0.5) * 2)
            end
        end
        local stars = rig.parts.Stars
        if stars then
            stars.Color = AWH.STAR:Lerp(AWH.STAR_HOT, math.clamp(0.3 + 0.25 * math.sin(t * 2.3) + 0.15 * math.sin(t * 5.1 + 1) + 0.6 * sing, 0, 1))
        end

        -- the eyes: slow blinks; shut asleep and happily as it hums; wide at the burst
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.32
            if a >= 1 then
                s.nextBlink = t + 2.5 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = math.max(blink, sleep, 0.85 * hum) * (1 - wide)
        local upper = AWH.BLINK_UPPER * close - math.rad(12) * wide
        local lower = AWH.BLINK_LOWER * close - math.rad(6) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(AWH.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(AWH.LID_HINGE[side], lower))
        end
    end

    -- It has rolled belly-up and is singing (animateAstralWhale): faint stars hang round it; three golden rings of sound ripple out from it through
    -- the air, a quarter second apart, and each star chimes bright as each ring reaches it; it all fades as the song ends.
    function Blasts.SongBetweenStars(rig, fx)
        local u = rig.unit
        local reduced = AWH.reduced()
        local chest = rig.points.Chest
        local centre = if chest then chest.TransformedWorldCFrame.Position else rig.rootPart.Position
        local RINGS = if reduced then 2 else 3
        local SEGMENTS = if reduced then 20 else 40 -- (at 28 the ring read as a polygon, seen in Play)
        local GROW, START, REACH = 1.15, 0.8 * u, 7.5 * u -- seconds a ring takes; studs from its middle it starts and ends at

        local light = Instance.new("PointLight")
        light.Color = AWH.GOLD
        light.Range = 10 * u
        light.Brightness = 2
        light.Shadows = false
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre), AWH.GOLD)
        holder.Transparency = 1
        light.Parent = holder
        tweenAfter(0.3, light, TweenInfo.new(1.3), { Brightness = 0 })

        -- the stars: faint points hanging round it in the air, at their own distances and heights
        local stars = {}
        for k = 1, (if reduced then 7 else 12) do
            local a = (k - 1) / (if reduced then 7 else 12) * 2 * math.pi + math.random() * 0.4
            local r = (2.4 + math.random() * 4.6) * u
            local at = centre + Vector3.new(math.cos(a) * r, (math.random() - 0.35) * 2.2 * u, math.sin(a) * r)
            local star = fx.neon(Vector3.one * 0.1 * u, CFrame.new(at), AWH.STAR)
            star.Shape = Enum.PartType.Ball
            star.Transparency = 1
            TweenService:Create(star, TweenInfo.new(0.3), { Transparency = 0.45 }):Play()
            stars[k] = { part = star, dist = r, rang = 0 }
        end
        local function chime(st, ring)
            st.rang = ring
            local part = st.part
            if not part.Parent then
                return
            end
            local big = (0.42 - 0.08 * ring) * u
            part.Color = AWH.STAR_HOT
            part.Size = Vector3.one * big
            part.Transparency = 0
            TweenService:Create(part, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.12 * u, Transparency = 0.4 }):Play()
            if not reduced and ring == 1 then
                local sparks = Instance.new("ParticleEmitter")
                sparks.Texture = SPARKLE
                sparks.Enabled = false
                sparks.Lifetime = NumberRange.new(0.3, 0.6)
                sparks.Speed = NumberRange.new(0.8 * u, 1.6 * u)
                sparks.SpreadAngle = Vector2.new(180, 180)
                sparks.Drag = 3
                sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
                sparks.Color = ColorSequence.new(AWH.STAR_HOT, AWH.STAR)
                sparks.LightEmission = 1
                sparks.LightInfluence = 0
                sparks.Parent = part
                sparks:Emit(6)
            end
        end

        -- the rings of sound: each a circle of short golden strokes, growing out, rippling up and down as it goes like a plucked string (flat,
        -- they read as plain yellow hoops, seen in Play), fading from hot gold to pale
        for ring = 1, RINGS do
            task.delay((ring - 1) * 0.25, function()
                if not holder.Parent then
                    return
                end
                local strokes = {}
                for i = 1, SEGMENTS do
                    local seg = fx.neon(Vector3.new(0.06 * u, 0.06 * u, 0.1), CFrame.new(centre), AWH.GOLD)
                    seg.Transparency = 1
                    strokes[i] = seg
                end
                local began = os.clock()
                local conn
                conn = RunService.Heartbeat:Connect(function()
                    if not strokes[1].Parent then
                        conn:Disconnect()
                        return
                    end
                    local now = os.clock() - began
                    local f = math.clamp(now / GROW, 0, 1)
                    local r = START + (REACH - START) * (1 - (1 - f) ^ 2)
                    local width = (0.06 - 0.035 * f) * u
                    -- the ripple: a gentle wave a few hundredths of the ring's size, settling as it spreads (a fixed 0.28 stud wobble bent the
                    -- rings into lassos, seen in Play)
                    local swell = 0.045 * r * (1 - 0.6 * f)
                    local function at(a: number)
                        return centre + Vector3.new(math.cos(a) * r, swell * math.sin(8 * a + now * 9 + ring * 1.7), math.sin(a) * r)
                    end
                    local colour = AWH.GOLD_HOT:Lerp(AWH.GOLD, math.min(1, f * 2)):Lerp(AWH.PEARL, math.max(0, f - 0.5) * 1.2)
                    for i, seg in strokes do
                        local p0, p1 = at((i - 1) / SEGMENTS * 2 * math.pi), at(i / SEGMENTS * 2 * math.pi)
                        seg.Size = Vector3.new(width, width, (p1 - p0).Magnitude * 1.06)
                        seg.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
                        seg.Transparency = 0.1 + 0.9 * f * f
                        seg.Color = colour
                    end
                    for _, st in stars do
                        if st.rang < ring and r >= st.dist then
                            chime(st, ring)
                        end
                    end
                    if f >= 1 then
                        conn:Disconnect()
                        for _, seg in strokes do
                            seg.Transparency = 1
                        end
                    end
                end)
            end)
        end
        -- the stars fade as the song ends
        for _, st in stars do
            tweenAfter(1.45, st.part, TweenInfo.new(0.4), { Transparency = 1 })
        end
    end

    local bones = table.clone(AWH.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.AstralWhale = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "Chest" },
        GlowColors = {
            f4f6ff = Color3.fromRGB(244, 246, 255), -- the catch-lights in its eyes
            ffc45c = AWH.GOLD, -- its golden strings
            a9c8ff = AWH.STAR, -- the star knobs on its flippers
        },
        Effects = {
            Blast = "SongBetweenStars",
            NovaLight = 2,
        },
        Colors = {
            Gold = AWH.GOLD,
            Amber = AWH.GOLD_DIM,
            Orange = AWH.GOLD,
            Sun = AWH.GOLD_HOT,
            Ivory = AWH.PEARL,
        },
        Animate = animateAstralWhale,
    }
end

do
    -- The Origin Serpent (skinned): the first spirit vein, a loong. Its long body corkscrews up through the air round an invisible axis, its tail
    -- trailing below like a root of light, its neck carrying its head forward over the top; faceted carp scales of dark primordial slate, the world's
    -- first Qi glowing cyan in their seams, a vein of light down each flank, a pale plated belly, a row of spines down its back. A big, fierce head:
    -- a long flat-topped muzzle with a ridge down it, heavy brows over narrowed cyan slit eyes, a jaw open on great fangs and rows of teeth, spiny
    -- cheek frills, swept stag antlers tipped in cyan, two long glowing barbels. Two Qi rings, magenta and cyan, orbit round it. A slow wave runs up
    -- its coils as it floats; light pulses up its veins from its tail to its head; it looks at you often, growling low in its jaw, its barbels
    -- swaying. Now and then it roars, snaps, flicks its tail, rises in its coil or glares at you; left alone it settles, half-lidded, its rings
    -- slowing. Its special, The First Vein: its coils rise and its head rears as light races up its veins and its rings spin up; at the burst
    -- (Blasts.TheFirstVein) it roars and a double helix of cyan and magenta light erupts from its coil into the sky.
    local OS = {
        FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
        -- metres its whole coil is raised (the Root bone): the rig centres its tall box (7.5 studs) on the follow root about 3 studs up, which left
        -- its tail tip 0.45 studs under the floor (measured in Play, 2026-11-10); raised, the tail hangs clear, about 0.7 studs over the ground
        LIFT = 0.14,
        LID_HINGE = { L = Vector3.new(0.3861, -0.3492, -0.8538), R = Vector3.new(0.3861, 0.3492, 0.8538) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(46), -- (with the lower, past the 68 degrees between its narrowed lids' edges: they meet)
        BLINK_LOWER = math.rad(28),
        QI = Color3.fromRGB(30, 205, 255), -- its veins, barbels and cyan ring (Neon: saturated; a pale cyan blooms white)
        QI_HOT = Color3.fromRGB(170, 245, 255),
        QI_DIM = Color3.fromRGB(10, 90, 130),
        MAGENTA = Color3.fromRGB(255, 60, 205),
        MAGENTA_HOT = Color3.fromRGB(255, 170, 235),
        SILVER = Color3.fromRGB(206, 216, 232),
        -- its coil's slow wave: the bones up its body, each a little behind the last (origin_serpent.py SWAY_A/B, checked in Blender for torn skin)
        WAVE = { "Tail3", "Tail4", "Core", "Body1", "Body2", "Body3", "Body4" },
        -- its stances (game axes), each checked in Blender (origin_serpent.py: ROAR, SNAP, LOOK, RISE, FLICK)
        ROAR = { Jaw = { -0.32, 0, 0 }, Head = { 0.22, 0, 0 }, Neck = { 0.1, 0, 0 } },
        SNAP = { Jaw = { 0.22, 0, 0 } }, -- (its jaw near closed: further, its fangs would meet its lower jaw)
        RISE = { Core = { 0.1, 0, 0 }, Body1 = { 0.06, 0, 0 }, Body2 = { 0.06, 0, 0 }, Neck = { -0.1, 0, 0 }, Head = { 0.1, 0, 0 } },
        FLICK = { Tail1 = { 0.4, 0.35, 0 }, Tail2 = { 0.22, 0.15, 0 } },
        GLARE = { Neck = { -0.08, 0, 0 }, Head = { -0.12, 0, 0 } },
        FIDGET_TIME = { roar = 1.8, snap = 0.9, flick = 1.4, rise = 2.4, glare = 2.6 },
        BONES = { "Core", "Body1", "Body2", "Body3", "Body4", "Neck", "Head", "Jaw", "Tail4", "Tail3", "Tail2", "Tail1", "EyeL", "EyeR", "BarbelL", "BarbelR",
            "RingA", "RingB" },
    }

    function OS.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    local function animateOriginSerpent(rig, s, moving, fly, nova)
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > OS.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)

        -- the special, The First Vein: its coils rise and its head rears (to 0.4) as light races up its veins and its rings spin up; the roar at the
        -- burst (0.42); it settles (0.7 to 0.92)
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local gather = smoothstep(0.02, 0.38, progress) * (1 - smoothstep(0.7, 0.92, progress))
        local roar = smoothstep(0.36, 0.44, progress) * (1 - smoothstep(0.62, 0.8, progress))
        local wide = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.6, 0.72, progress))

        -- left alone a long while it settles; now and then it roars, snaps, flicks its tail, rises in its coil or glares at you
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantRest = if s.still > 15 then 1 else 0
        s.rest = (s.rest or 0) + (wantRest - (s.rest or 0)) * math.min(1, dt * (if wantRest > (s.rest or 0) then 0.5 else 4))
        local rest = smoothstep(0, 1, s.rest)
        s.nextFidget = s.nextFidget or t + 5
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.22 then "roar" elseif r < 0.4 then "snap" elseif r < 0.6 then "flick" elseif r < 0.8 then "rise" else "glare"
            s.nextFidget = t + OS.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / OS.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - rest) * (1 - gather)
        local function kind(name)
            return if s.fidgetKind == name then fidget else 0
        end

        local want = {}
        -- the slow wave up its coils, quicker as it moves; barely as it rests
        s.wave = (s.wave or 0) + dt * (0.9 + 2.2 * pace + 3 * gather)
        local amp = (0.6 + 0.4 * pace) * (1 - 0.6 * rest)
        for k, name in OS.WAVE do
            addStance(want, { [name] = { 0, 0.11 * math.sin(s.wave - k * 0.75), 0.02 * math.sin(s.wave * 0.7 - k * 0.5) } }, amp)
        end
        addStance(want, { Tail1 = { 0.12 * math.sin(s.wave * 1.3 - 6), 0.25 * math.sin(s.wave * 1.1 - 6.5), 0 }, Tail2 = { 0, 0.12 * math.sin(s.wave * 1.1 - 5.8), 0 } }, 1)
        addStance(want, OS.RISE, math.max(gather, kind("rise")))
        addStance(want, OS.FLICK, kind("flick"))
        addStance(want, OS.GLARE, kind("glare") + 0.5 * rest)
        -- its head: looking about, often at you; its jaw growling a little open and shut; roaring; snapping
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2 + math.random() * 3
            s.atYou = math.random() < 0.6
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.25
        end
        local calm = (1 - 0.6 * pace) * (1 - gather) * (1 - 0.7 * rest)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.6, 0.6) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.25) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
        addStance(want, { Neck = { 0.12 * s.pitch, 0.25 * s.yaw, 0 }, Head = { 0.25 * s.pitch, 0.35 * s.yaw, 0.1 * s.yaw },
            EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 } }, 1)
        local growl = 0.05 * math.sin(t * 1.6) + 0.03 * math.sin(t * 4.3)
        addStance(want, { Jaw = { growl, 0, 0 } }, (1 - rest) * (1 - roar))
        addStance(want, OS.SNAP, rest * 0.6)
        addStance(want, OS.ROAR, math.max(roar, kind("roar")))
        local snap = kind("snap")
        if snap > 0 then
            addStance(want, OS.SNAP, if env < 0.35 then 1 else math.max(0, 1 - (env - 0.35) * 3))
            addStance(want, { Jaw = { -0.18, 0, 0 } }, if env < 0.35 then env / 0.35 * 0.6 else 0)
        end
        -- its barbels swaying, streaming as it moves
        local sway = math.sin(t * 1.3)
        addStance(want, { BarbelL = { 0.1 * sway + 0.15 * pace, 0.12 * math.sin(t * 0.9), 0.08 * sway }, BarbelR = { 0.1 * sway + 0.15 * pace, -0.12 * math.sin(t * 0.9 + 0.6), -0.08 * sway } }, 1)
        -- its rings orbiting, the magenta one way and the cyan the other; faster as it moves; spinning up in its special; slow as it rests
        s.ringA = (s.ringA or 0) + dt * (0.8 + 1.2 * pace + 7 * gather) * (1 - 0.6 * rest)
        s.ringB = (s.ringB or 0) - dt * (1.0 + 1.4 * pace + 8 * gather) * (1 - 0.6 * rest)

        local bob = math.sin(t * 0.85)
        pose(m.Root, CFrame.new(0, OS.LIFT * u, 0))
        for _, name in OS.BONES do
            local a = want[name] or Vector3.zero
            if name == "Core" then
                pose(m.Core, CFrame.new(0, (0.02 * bob + 0.04 * gather) * u, 0) * CFrame.Angles(a.X + 0.02 * bob, a.Y, a.Z))
            elseif name == "RingA" then
                pose(m.RingA, CFrame.Angles(0, s.ringA, 0))
            elseif name == "RingB" then
                pose(m.RingB, CFrame.Angles(0, s.ringB, 0))
            else
                pose(m[name], CFrame.Angles(a.X, a.Y, a.Z))
            end
        end

        -- the first Qi pulsing up its veins from its tail to its head (racing in its special); dim as it rests. Its barbels and rings glow steady.
        s.pulse = (s.pulse or 0) + dt * (1.4 + 7 * gather)
        for k, key in { "VeinA", "VeinB", "VeinC", "VeinD" } do
            local part = rig.parts[key]
            if part then
                local beat = math.max(0, math.sin(s.pulse - k * 0.9)) ^ 2
                local glow = (0.35 + 0.65 * beat) * (1 - 0.5 * rest) + 0.4 * roar
                part.Color = if glow < 0.5 then OS.QI_DIM:Lerp(OS.QI, glow * 2) else OS.QI:Lerp(OS.QI_HOT, math.min(1, (glow - 0.5) * 2))
            end
        end
        local ringA, ringB = rig.parts.RingA, rig.parts.RingB
        if ringA then
            ringA.Color = OS.MAGENTA:Lerp(OS.MAGENTA_HOT, math.clamp(0.2 * math.sin(t * 2.1) + 0.6 * gather, 0, 1))
        end
        if ringB then
            ringB.Color = OS.QI:Lerp(OS.QI_HOT, math.clamp(0.2 * math.sin(t * 2.4 + 1) + 0.6 * gather, 0, 1))
        end

        -- the eyes: slow blinks; narrowed in a glare and as it rests; wide at its roar
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
        local close = math.max(blink, 0.45 * kind("glare"), 0.55 * rest) * (1 - wide)
        local upper = OS.BLINK_UPPER * close - math.rad(10) * wide
        local lower = OS.BLINK_LOWER * close - math.rad(5) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(OS.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(OS.LID_HINGE[side], lower))
        end
    end

    -- It roars (animateOriginSerpent): a double helix of cyan and magenta light erupts from its coil and climbs into the sky, the first spirit vein
    -- opening; a flash, sparks thrown off it; then it fades as it reaches its height.
    function Blasts.TheFirstVein(rig, fx)
        local u = rig.unit
        local reduced = OS.reduced()
        local core = rig.points.Core
        local base = if core then core.TransformedWorldCFrame.Position else rig.rootPart.Position
        local SEGMENTS = if reduced then 20 else 48 -- (strokes per strand: at 26, about 10 a turn, it read as a zig-zag of sticks in Play)
        local RISE, HEIGHT, TURNS, RADIUS = 0.6, 9 * u, 2.5, 1.3 * u

        local light = Instance.new("PointLight")
        light.Color = OS.QI
        light.Range = 12 * u
        light.Brightness = 3
        light.Shadows = false
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(base), OS.QI)
        holder.Transparency = 1
        light.Parent = holder
        tweenAfter(0.25, light, TweenInfo.new(1.0), { Brightness = 0 })

        -- two strands, each a line of short glowing strokes, climbing as a helix and fading out once it has risen
        local strands = {}
        for strand = 1, 2 do
            local colour = if strand == 1 then OS.QI else OS.MAGENTA
            local strokes = {}
            for i = 1, SEGMENTS do
                local seg = fx.neon(Vector3.new(0.12 * u, 0.12 * u, 0.1), CFrame.new(base), colour)
                seg.Transparency = 1
                strokes[i] = seg
            end
            strands[strand] = strokes
        end
        local began = os.clock()
        local conn
        conn = RunService.Heartbeat:Connect(function()
            if not holder.Parent then
                conn:Disconnect()
                return
            end
            local now = os.clock() - began
            local grow = 1 - (1 - math.clamp(now / RISE, 0, 1)) ^ 3
            local fade = math.clamp((now - RISE - 0.15) / 0.75, 0, 1)
            local top = HEIGHT * grow
            for strand, strokes in strands do
                local function at(k: number)
                    local sAlong = k / SEGMENTS
                    local a = sAlong * TURNS * 2 * math.pi + (strand - 1) * math.pi + now * 6
                    local r = RADIUS * (1 - 0.55 * sAlong)
                    return base + Vector3.new(math.cos(a) * r, sAlong * top, math.sin(a) * r)
                end
                for i, seg in strokes do
                    local p0, p1 = at(i - 1), at(i)
                    local length = (p1 - p0).Magnitude
                    if length > 1e-3 then
                        local w = (0.16 - 0.1 * (i / SEGMENTS)) * u
                        seg.Size = Vector3.new(w, w, length * 1.08)
                        seg.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
                    end
                    seg.Transparency = 0.05 + 0.95 * fade
                end
            end
            if fade >= 1 then
                conn:Disconnect()
            end
        end)

        -- sparks of the first Qi thrown off it as it erupts
        if not reduced then
            local sparks = Instance.new("ParticleEmitter")
            sparks.Texture = SPARKLE
            sparks.Enabled = false
            sparks.Lifetime = NumberRange.new(0.5, 1.0)
            sparks.Speed = NumberRange.new(3 * u, 6 * u)
            sparks.SpreadAngle = Vector2.new(60, 60)
            sparks.Acceleration = Vector3.new(0, -4 * u, 0)
            sparks.Drag = 1.2
            sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * u), NumberSequenceKeypoint.new(1, 0) })
            sparks.Color = ColorSequence.new(OS.QI_HOT, OS.MAGENTA)
            sparks.LightEmission = 1
            sparks.LightInfluence = 0
            sparks.Parent = holder
            holder.CFrame = CFrame.lookAt(base, base + Vector3.yAxis)
            sparks:Emit(40)
        end
    end

    local bones = table.clone(OS.BONES)
    for _, name in { "Root", "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.OriginSerpent = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "Core" },
        GlowColors = {
            f2fbff = Color3.fromRGB(242, 251, 255), -- the catch-lights in its eyes
            ["38e0ff"] = OS.QI, -- its veins, barbels and cyan ring
            ff4fd8 = OS.MAGENTA, -- its magenta ring
        },
        Effects = {
            Blast = "TheFirstVein",
            NovaLight = 2,
        },
        Colors = {
            Gold = OS.QI_HOT,
            Amber = OS.QI,
            Orange = OS.MAGENTA,
            Sun = OS.QI_HOT,
            Ivory = OS.SILVER,
        },
        Animate = animateOriginSerpent,
    }
end

do
    -- The Azure Sky Dragon (skinned): a great dragon of the high sky, built in a glide (the owner's reference, 2026-11-12: a dragon gliding through an
    -- aurora above the clouds, jaws open). It never lands: its broad wings beat slow and heavy, its body rising on each downstroke, deeper and faster
    -- when it goes anywhere; it banks into its turns; its long spined tail waves behind it; its long neck reaches forward and turns its head to look
    -- about, often at you, under heavy brows, its glowing ice eyes narrowed; its jaw works open and shut on its teeth and the pale light in its throat
    -- breathes. Now and then it roars, snaps its jaws, banks round, lashes its tail or reaches its claws forward. Its special, Aurora Gale: it rears
    -- back, wings raised, the light gathering in its throat; then it lunges and breathes a cone of aurora wind (Blasts.AuroraGale).
    local AZ = {
        FAR = 120, -- studs from the camera past which nobody can see it fidget: its bones rest
        LID_HINGE = { L = Vector3.new(0.5938, -0.2983, -0.7473), R = Vector3.new(0.5938, 0.2983, 0.7473) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(40),
        BLINK_LOWER = math.rad(22),
        ICE = Color3.fromRGB(90, 215, 255), -- the light in its throat (Neon: saturated; its pale ice blooms white)
        ICE_HOT = Color3.fromRGB(190, 245, 255),
        ICE_DIM = Color3.fromRGB(20, 90, 140),
        AURORA = { Color3.fromRGB(40, 175, 255), Color3.fromRGB(140, 80, 255), Color3.fromRGB(30, 255, 150) }, -- its breath: ice, violet, green (Neon: saturated; the paler first picks bloomed white in Play)
        -- its moves (game axes), each checked in Blender for torn skin: the same numbers as azure_sky_dragon.py's BEAT_UP, BEAT_DOWN, ROAR, BANK, REACH
        ROAR = { Jaw = { -0.22, 0, 0 }, Head = { 0.16, 0, 0 }, Neck3 = { 0.08, 0, 0 }, Neck2 = { 0.05, 0, 0 } },
        SNAP = { Jaw = { 0.2, 0, 0 } }, -- (its jaw near shut: modelled open, it closes on its teeth)
        BANK = { Body = { 0, 0, 0.25 }, Chest = { 0, 0.1, 0.1 }, Neck2 = { 0, 0.15, 0 }, Head = { 0, 0.15, 0 } },
        REACH = { LegFL1 = { -0.5, 0, 0 }, LegFL2 = { 0.6, 0, 0 }, LegFR1 = { -0.5, 0, 0 }, LegFR2 = { 0.6, 0, 0 }, PawFL = { 0.4, 0, 0 }, PawFR = { 0.4, 0, 0 } },
        FIDGET_TIME = { roar = 1.8, snap = 0.9, bank = 2.4, lash = 1.4, reach = 1.8 },
    }

    local function azWings(lift, sweep, hand, fan)
        local out = {}
        for tag, sign in { L = 1, R = -1 } do
            out["Wing" .. tag .. "1"] = { 0, sweep * sign, -lift * sign }
            out["Wing" .. tag .. "2"] = { 0, 0, 0 }
            out["Wing" .. tag .. "3"] = { 0, hand * sign, 0 }
            for j = 0, 3 do
                out["Wing" .. tag .. "F" .. (j + 1)] = { 0, fan * sign * j / 3, 0 }
            end
        end
        return out
    end
    AZ.BEAT_UP = azWings(0.55, -0.08, -0.1, 0)
    AZ.BEAT_DOWN = azWings(-0.6, 0.06, 0.18, 0)

    function AZ.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    AZ.BONES = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw", "EyeL", "EyeR" }
    for k = 1, 6 do
        table.insert(AZ.BONES, "Tail" .. k)
    end
    for _, key in { "FL", "FR", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(AZ.BONES, "Leg" .. key .. k)
        end
        table.insert(AZ.BONES, "Paw" .. key)
    end
    for _, tag in { "L", "R" } do
        for k = 1, 3 do
            table.insert(AZ.BONES, "Wing" .. tag .. k)
        end
        for j = 1, 4 do
            table.insert(AZ.BONES, "Wing" .. tag .. "F" .. j)
        end
    end

    local function animateAzureSkyDragon(rig, s, moving, fly, nova)
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > AZ.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)

        -- the special, Aurora Gale: it rears back, wings raised, its throat's light gathering (to 0.4); at the burst (0.42) it lunges and breathes
        -- (to 0.7); it settles (to 0.9)
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local gather = smoothstep(0.02, 0.36, progress) * (1 - smoothstep(0.4, 0.46, progress))
        local breathe = smoothstep(0.4, 0.46, progress) * (1 - smoothstep(0.66, 0.88, progress))
        local wide = smoothstep(0.38, 0.44, progress) * (1 - smoothstep(0.6, 0.72, progress))

        -- now and then it roars, snaps, banks round, lashes its tail or reaches its claws forward
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget and not special then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.24 then "roar" elseif r < 0.42 then "snap" elseif r < 0.62 then "bank" elseif r < 0.82 then "lash" else "reach"
            s.nextFidget = t + AZ.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / AZ.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - 0.6 * pace) * (if special then 0 else 1)
        local function kind(name)
            return if s.fidgetKind == name then fidget else 0
        end

        -- its wings: slow, heavy beats as it glides beside you; deeper and quicker when it goes anywhere; raised as it gathers its breath, driving
        -- down as it breathes
        s.beat = (s.beat or 0) + dt * (1.7 + 2.8 * pace)
        local stroke = math.sin(s.beat)
        local up, down = math.max(0, stroke), math.max(0, -stroke)
        local amp = (0.4 + 0.6 * pace) * (1 - gather) * (1 - breathe)
        local want = {}
        addStance(want, AZ.BEAT_UP, up * amp + gather)
        addStance(want, AZ.BEAT_DOWN, down * amp + breathe)

        -- banking into its turns, and the bank fidget
        local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
        local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
        s.heading = heading
        s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
        addStance(want, { Body = { 0, 0, s.bank }, Chest = { 0, 0, 0.5 * s.bank } }, 1)
        addStance(want, AZ.BANK, kind("bank") * (if (s.fidgetAt or 0) % 2 < 1 then 1 else -1))

        -- its head: looking about, often at you; reared back as it gathers its breath, thrust forward as it breathes
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.5 + math.random() * 3
            s.atYou = math.random() < 0.55
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - 0.5 * pace) * (1 - gather) * (1 - breathe)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.45, -0.2, 0.3) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
        addStance(want, { Neck2 = { 0.2 * s.pitch, 0.3 * s.yaw, 0 }, Neck3 = { 0.2 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.35 * s.pitch, 0.35 * s.yaw, 0 },
            EyeL = { 0.2 * s.pitch, 0.15 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.15 * s.yaw, 0 } }, 1)
        addStance(want, { Neck1 = { 0.12, 0, 0 }, Neck2 = { 0.12, 0, 0 }, Head = { 0.3, 0, 0 } }, gather)
        addStance(want, { Neck1 = { -0.12, 0, 0 }, Neck2 = { -0.08, 0, 0 }, Head = { -0.1, 0, 0 } }, breathe)
        -- its jaw: working a little open and shut as it breathes; roaring; snapping shut
        local growl = 0.04 * math.sin(t * 1.4) + 0.02 * math.sin(t * 3.7)
        addStance(want, { Jaw = { growl, 0, 0 } }, (1 - kind("roar")) * (1 - breathe))
        addStance(want, AZ.ROAR, math.max(breathe, kind("roar"), 0.5 * gather))
        local snap = kind("snap")
        if snap > 0 then
            addStance(want, AZ.SNAP, if env < 0.4 then 1 else math.max(0, 1 - (env - 0.4) * 2.5))
        end
        -- its legs drawn up, paddling a little with its beats; reaching forward now and then
        local paddle = 0.06 * math.sin(s.beat + 0.6)
        addStance(want, { LegFL1 = { paddle, 0, 0 }, LegFR1 = { -paddle, 0, 0 }, LegBL1 = { -0.5 * paddle, 0, 0 }, LegBR1 = { 0.5 * paddle, 0, 0 } }, 1 - pace)
        addStance(want, AZ.REACH, kind("reach"))
        -- the tail: a slow wave running back down it; streaming out as it travels; a lash now and then
        local lash = kind("lash")
        for k = 1, 6 do
            local w = (0.05 + 0.05 * k / 6) * math.sin(t * 1.1 - k * 0.6) * (1 - 0.5 * pace) + 0.3 * lash * math.sin(math.pi * env * 2 - k * 0.4) * (k / 6)
            addStance(want, { ["Tail" .. k] = { 0.03 * math.sin(t * 0.8 - k * 0.5) + 0.03 * pace * math.sin(s.beat - k * 0.6), w, 0 } }, 1)
        end

        for _, name in AZ.BONES do
            local a = want[name] or Vector3.zero
            local lift = if name == "Hips" then (0.03 * down * amp - 0.015 * up * amp + 0.015 * math.sin(t * 0.8)) * u else 0
            pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- the light in its throat: breathing slow; gathering bright as it draws its breath, blazing as it breathes
        local throat = rig.parts.Breath
        if throat then
            local glow = 0.35 + 0.25 * math.sin(t * 1.4) + 0.65 * gather + 0.8 * breathe
            throat.Color = if glow < 0.6 then AZ.ICE_DIM:Lerp(AZ.ICE, glow / 0.6) else AZ.ICE:Lerp(AZ.ICE_HOT, math.min(1, (glow - 0.6) / 0.6))
        end

        -- the eyes: a slow blink now and then; narrowed as it gathers; wide as it breathes
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.24
            if a >= 1 then
                s.nextBlink = t + 3 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = math.max(blink, 0.4 * gather) * (1 - wide)
        local upper = AZ.BLINK_UPPER * close - math.rad(8) * wide
        local lower = AZ.BLINK_LOWER * close - math.rad(5) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(AZ.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(AZ.LID_HINGE[side], lower))
        end
    end

    -- It breathes (animateAzureSkyDragon): a cone of aurora wind pours from its jaws, ribbons of ice, violet and green light streaming out and
    -- spreading as they go; a ring of pressure bursts from its mouth; ice glitter rides the gale; a flash of cold light. Gone by 1.6 s.
    function Blasts.AuroraGale(rig, fx)
        local u = rig.unit
        local reduced = AZ.reduced()
        local forward = rig.rootPart.CFrame.LookVector
        local jaw = rig.points.Jaw
        local mouth = (if jaw then jaw.TransformedWorldCFrame.Position else rig.rootPart.Position) + forward * 0.35 * u
        local aim = (forward - Vector3.yAxis * 0.12).Unit
        local right = aim:Cross(Vector3.yAxis).Unit
        local upward = right:Cross(aim).Unit
        local STREAKS = if reduced then 10 else 22
        local REACH, SPREAD, LIFE = 7 * u, 1.9 * u, 0.9

        local light = Instance.new("PointLight")
        light.Color = AZ.ICE
        light.Range = 14 * u
        light.Brightness = 3.5
        light.Shadows = false
        local holder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(mouth, mouth + aim), AZ.ICE)
        holder.Transparency = 1
        light.Parent = holder
        tweenAfter(0.3, light, TweenInfo.new(1.0), { Brightness = 0 })

        -- the ring of pressure, rolling out from its jaws
        local ring = fx.neon(Vector3.new(0.05, 0.5 * u, 0.5 * u), CFrame.lookAt(mouth, mouth + aim) * CFrame.Angles(0, math.pi / 2, 0), AZ.ICE_HOT)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.2
        TweenService:Create(ring, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
            { Size = Vector3.new(0.05, 3.2 * u, 3.2 * u), CFrame = CFrame.lookAt(mouth + aim * 1.6 * u, mouth + aim * 3 * u) * CFrame.Angles(0, math.pi / 2, 0), Transparency = 1 }):Play()

        -- the gale: streaks of aurora light, each flying out along its own line in the cone, lengthening, then thinning away
        local streaks = {}
        for i = 1, STREAKS do
            local a = math.random() * 2 * math.pi
            local r = math.sqrt(math.random())
            local dir = (aim + (right * math.cos(a) + upward * math.sin(a)) * r * SPREAD / REACH).Unit
            local colour = AZ.AURORA[(i - 1) % #AZ.AURORA + 1]
            local seg = fx.neon(Vector3.new(0.08 * u, 0.08 * u, 0.1), CFrame.lookAt(mouth, mouth + dir), colour)
            seg.Transparency = 1
            streaks[i] = { part = seg, dir = dir, delay = math.random() * 0.25, speed = 0.8 + 0.4 * math.random() }
        end
        local began = os.clock()
        local conn
        conn = RunService.Heartbeat:Connect(function()
            if not holder.Parent then
                conn:Disconnect()
                return
            end
            local now = os.clock() - began
            local done = true
            for _, st in streaks do
                local k = math.clamp((now - st.delay) / LIFE, 0, 1)
                if k < 1 then
                    done = false
                end
                local head = REACH * (1 - (1 - k) ^ 2) * st.speed
                local tail = math.max(0, head - (0.8 + 2.2 * k) * u)
                local p0, p1 = mouth + st.dir * tail, mouth + st.dir * head
                local length = (p1 - p0).Magnitude
                if length > 1e-3 then
                    local w = (0.1 + 0.18 * k) * u
                    st.part.Size = Vector3.new(w, w * 0.4, length)
                    st.part.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
                end
                st.part.Transparency = if k <= 0 then 1 else 0.15 + 0.85 * smoothstep(0.45, 1, k)
            end
            if done then
                conn:Disconnect()
            end
        end)

        -- ice glitter riding the gale
        if not reduced then
            local glitter = Instance.new("ParticleEmitter")
            glitter.Texture = SPARKLE
            glitter.Enabled = false
            glitter.Lifetime = NumberRange.new(0.5, 0.9)
            glitter.Speed = NumberRange.new(6 * u, 10 * u)
            glitter.SpreadAngle = Vector2.new(16, 16)
            glitter.Drag = 1.5
            glitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * u), NumberSequenceKeypoint.new(1, 0) })
            glitter.Color = ColorSequence.new(AZ.ICE_HOT, AZ.AURORA[2])
            glitter.LightEmission = 1
            glitter.LightInfluence = 0
            glitter.EmissionDirection = Enum.NormalId.Front
            glitter.Parent = holder
            glitter:Emit(36)
        end
    end

    local bones = table.clone(AZ.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.AzureSkyDragon = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "Jaw" },
        GlowColors = {
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            bff4ff = AZ.ICE, -- the light in its throat (its pale ice blooms white as Neon)
        },
        Effects = {
            Blast = "AuroraGale",
            NovaLight = 2,
        },
        Colors = {
            Gold = AZ.ICE_HOT,
            Amber = AZ.ICE,
            Orange = AZ.AURORA[2],
            Sun = AZ.ICE_HOT,
            Ivory = Color3.fromRGB(220, 236, 250),
        },
        Animate = animateAzureSkyDragon,
    }
end

do
    -- The Bonefire Dragon (skinned): the bones of a dragon that refused to finish dying, held together and up off the ground by the blue soul fire
    -- burning in its ribs (bonefire_dragon.py). Every bone is rigid on its own skeleton bone. It hangs in the air in a predator's crouch, rising and
    -- sinking slowly, its bones creaking as they sway; the fire in its chest flickers up through the ribs and a point of cold light burns deep in each
    -- socket, flames streaming from them. Its head hangs low and sways, turning to look about, often at you; its heavy brows glare, and lift when it
    -- is curious; its jaw hangs open on the fire in its throat. The bare bones of its wings flex as it hovers and beat slow and heavy when it goes
    -- anywhere; its tail waves to its spiked knot. Now and then it roars, clatters its teeth, swipes a forefoot, shakes its whole frame with a rattle,
    -- or lets its fire flare. Its special, Ossuary Pyre: it rears up as the fire in its ribs blazes, then slams down; a ring of burning bone spires
    -- bursts up from the ground round it and a pillar of soul fire roars out of its chest (Blasts.OssuaryPyre).
    local BF = {
        FAR = 120, -- studs from the camera past which nobody can see it fidget: its bones rest
        SOUL = Color3.fromRGB(61, 123, 255), -- its fire (Neon: saturated; a paler blue blooms white)
        SOUL_HOT = Color3.fromRGB(200, 228, 255),
        SOUL_DEEP = Color3.fromRGB(40, 30, 150),
        EYE = Color3.fromRGB(74, 166, 255),
        EYE_HOT = Color3.fromRGB(210, 238, 255),
        BONE = Color3.fromRGB(226, 214, 188),
        SPIRE = Color3.fromRGB(176, 160, 132), -- the bone spires of its special: aged ivory, darker than its own bones so they read in daylight
        FIRE = "rbxasset://textures/particles/fire_main.dds",
        SMOKE = "rbxasset://textures/particles/smoke_main.dds",
        -- each brow turns about the line out of its socket (bonefire_dragon.py's socket frame): a positive turn lowers its front (a glare)
        BROW_AXIS = { L = Vector3.new(-0.7226, 0.3011, -0.6222), R = Vector3.new(0.7226, 0.3011, -0.6222) },
        -- its moves (game axes): the same numbers as bonefire_dragon.py's ROAR, RISE and SWIPE, each checked there
        ROAR = { Jaw = { -0.42, 0, 0 }, Head = { 0.22, 0, 0 }, Neck2 = { 0.1, 0, 0 }, Neck1 = { 0.06, 0, 0 } },
        SWIPE = { LegFL1 = { -0.55, 0.1, 0 }, LegFL2 = { 0.7, 0, 0 }, LegFL3 = { 0.4, 0, 0 }, PawFL = { 0.3, 0, 0 } },
        SLAM = { Body = { -0.12, 0, 0 }, Chest = { -0.1, 0, 0 }, Neck1 = { -0.08, 0, 0 }, Head = { -0.1, 0, 0 }, LegFL1 = { -0.35, 0, 0 },
            LegFR1 = { -0.35, 0, 0 }, LegFL2 = { 0.45, 0, 0 }, LegFR2 = { 0.45, 0, 0 } },
        FIDGET_TIME = { roar = 1.8, clatter = 1.1, swipe = 1.3, shake = 1.2, flare = 2.0 },
    }

    local function bfWings(lift, sweep, elbow, hand, fan)
        local out = {}
        for tag, sign in { L = 1, R = -1 } do
            out["Wing" .. tag .. "1"] = { 0, sweep * sign, -lift * sign }
            out["Wing" .. tag .. "2"] = { 0, elbow * sign, 0 }
            out["Wing" .. tag .. "3"] = { 0, hand * sign, 0 }
            for j = 0, 2 do
                out["Wing" .. tag .. "F" .. (j + 1)] = { 0, fan * sign * (j / 2 - 0.5), 0 }
            end
        end
        return out
    end
    BF.BEAT_UP = bfWings(0.5, -0.1, -0.25, -0.2, 0.3)
    BF.BEAT_DOWN = bfWings(-0.55, 0.12, -0.35, -0.3, 0.4)
    BF.RISE = bfWings(0.35, -0.05, -0.45, -0.4, 0.5)
    for bone, a in { Body = { 0.2, 0, 0 }, Chest = { 0.16, 0, 0 }, Neck1 = { -0.1, 0, 0 }, Head = { -0.12, 0, 0 }, LegFL1 = { 0.5, 0, 0 },
        LegFR1 = { 0.5, 0, 0 }, LegFL2 = { -0.6, 0, 0 }, LegFR2 = { -0.6, 0, 0 } } do
        BF.RISE[bone] = a
    end

    function BF.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    BF.BONES = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "Jaw", "Soul", "EyeL", "EyeR" }
    for k = 1, 6 do
        table.insert(BF.BONES, "Tail" .. k)
    end
    for _, key in { "FL", "FR", "BL", "BR" } do
        for k = 1, 3 do
            table.insert(BF.BONES, "Leg" .. key .. k)
        end
        table.insert(BF.BONES, "Paw" .. key)
    end
    for _, tag in { "L", "R" } do
        for k = 1, 3 do
            table.insert(BF.BONES, "Wing" .. tag .. k)
        end
        for j = 1, 3 do
            table.insert(BF.BONES, "Wing" .. tag .. "F" .. j)
        end
    end

    -- Its living fire, made once: flames licking up out of its chest through the ribs, embers drifting off its spine, and a flame streaming from
    -- each socket. Fewer for another player's pet on a phone, and with reduced effects.
    function BF.fires(rig)
        local soul = rig.parts.Soul
        if not soul then
            return nil
        end
        local u = rig.unit
        local few = BF.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer)
        local fires = {}
        fires.chest = emitter(soul, {
            Name = "SoulFire",
            Texture = BF.FIRE,
            Rate = if few then 7 else 15,
            Lifetime = NumberRange.new(0.45, 0.8),
            Speed = NumberRange.new(0.4 * u, 0.9 * u),
            SpreadAngle = Vector2.new(28, 28),
            Acceleration = Vector3.new(0, 1.6 * u, 0),
            Drag = 1,
            EmissionDirection = Enum.NormalId.Top,
            Rotation = NumberRange.new(0, 360),
            RotSpeed = NumberRange.new(-60, 60),
            Size = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0.42 * u),
                NumberSequenceKeypoint.new(0.5, 0.34 * u),
                NumberSequenceKeypoint.new(1, 0.06 * u),
            }),
            Color = ColorSequence.new({
                ColorSequenceKeypoint.new(0, BF.SOUL_HOT),
                ColorSequenceKeypoint.new(0.35, BF.SOUL),
                ColorSequenceKeypoint.new(1, BF.SOUL_DEEP),
            }),
            Transparency = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0.6),
                NumberSequenceKeypoint.new(0.2, 0.35),
                NumberSequenceKeypoint.new(1, 1),
            }),
            Brightness = 1.2, -- (stacked additive flames wash to white: kept low, seen in Play)
        })
        fires.chestRate = fires.chest.Rate
        if not few then
            fires.embers = emitter(soul, {
                Name = "SoulEmbers",
                Texture = SPARKLE,
                Rate = 3,
                Lifetime = NumberRange.new(1.4, 2.4),
                Speed = NumberRange.new(0.6 * u, 1.2 * u),
                SpreadAngle = Vector2.new(35, 35),
                EmissionDirection = Enum.NormalId.Top,
                Acceleration = Vector3.new(0, 0.4 * u, 0),
                Drag = 0.6,
                Size = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0),
                    NumberSequenceKeypoint.new(0.2, 0.07 * u),
                    NumberSequenceKeypoint.new(1, 0),
                }),
                Color = ColorSequence.new(BF.SOUL_HOT, BF.SOUL),
                Transparency = NumberSequence.new(0.1, 1),
            })
        end
        fires.eyes = {}
        for _, side in { "L", "R" } do
            local bone = rig.points["Eye" .. side]
            if bone then
                table.insert(fires.eyes, emitter(bone, {
                    Name = "EyeFlame",
                    Texture = BF.FIRE,
                    Rate = if few then 5 else 11,
                    Lifetime = NumberRange.new(0.25, 0.42),
                    Speed = NumberRange.new(0.15 * u, 0.35 * u),
                    SpreadAngle = Vector2.new(15, 15),
                    Acceleration = Vector3.new(0, 1.2 * u, 0),
                    Rotation = NumberRange.new(-20, 20),
                    Size = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0.1 * u),
                        NumberSequenceKeypoint.new(1, 0.02 * u),
                    }),
                    Color = ColorSequence.new(BF.EYE_HOT, BF.EYE),
                    Transparency = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0.3),
                        NumberSequenceKeypoint.new(1, 1),
                    }),
                    Brightness = 1.4,
                }))
            end
        end
        fires.eyeRate = if few then 5 else 11
        return fires
    end

    local function animateBonefireDragon(rig, s, moving, fly, nova)
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > BF.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)
        if s.fires == nil then
            s.fires = BF.fires(rig) or false
        end

        -- the special, Ossuary Pyre: it rears up, its fire blazing (to 0.4); at the burst (0.42) it slams down (to 0.62); it settles (to 0.9)
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local rise = smoothstep(0.02, 0.36, progress) * (1 - smoothstep(0.4, 0.47, progress))
        local slam = smoothstep(0.4, 0.47, progress) * (1 - smoothstep(0.6, 0.88, progress))

        -- now and then it roars, clatters its teeth, swipes a forefoot, shakes its whole frame or lets its fire flare
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget and not special then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.22 then "roar" elseif r < 0.44 then "clatter" elseif r < 0.62 then "swipe" elseif r < 0.8 then "shake" else "flare"
            s.nextFidget = t + BF.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / BF.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - 0.6 * pace) * (if special then 0 else 1)
        local function kind(name)
            return if s.fidgetKind == name then fidget else 0
        end
        local flare = kind("flare")

        local want = {}
        -- its wings: the bare bones flex slowly as it hovers; they beat slow and heavy when it goes anywhere; raised high as it rears
        s.beat = (s.beat or 0) + dt * (1.1 + 2.6 * pace)
        local stroke = math.sin(s.beat)
        local up, down = math.max(0, stroke), math.max(0, -stroke)
        local amp = (0.12 + 0.88 * pace) * (1 - rise) * (1 - slam)
        addStance(want, BF.BEAT_UP, up * amp + 0.4 * flare)
        addStance(want, BF.BEAT_DOWN, down * amp + 0.5 * slam)
        addStance(want, bfWings(0, 0, 0.06 * math.sin(t * 0.9), 0.08 * math.sin(t * 0.9 - 0.6), 0.12 * math.sin(t * 0.7)), (1 - pace) * (1 - rise))
        addStance(want, BF.RISE, rise)
        addStance(want, BF.SLAM, slam)

        -- its head: low and swaying, looking about, often at you
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2.2 + math.random() * 3
            s.atYou = math.random() < 0.55
            s.curious = s.atYou and math.random() < 0.4
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
        end
        local calm = (1 - 0.5 * pace) * (1 - rise) * (1 - slam)
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.45, -0.2, 0.3) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.2)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.2)
        local sway = 0.08 * math.sin(t * 0.55) * calm
        addStance(want, { Neck1 = { 0.15 * s.pitch, 0.3 * s.yaw + sway, 0 }, Neck2 = { 0.2 * s.pitch, 0.35 * s.yaw + sway, 0.04 * math.sin(t * 0.45) },
            Head = { 0.35 * s.pitch, 0.35 * s.yaw, 0.06 * math.sin(t * 0.4) }, EyeL = { 0.3 * s.pitch, 0.3 * s.yaw, 0 },
            EyeR = { 0.3 * s.pitch, 0.3 * s.yaw, 0 } }, 1)

        -- its jaw: hanging open on its fire, moving with its breath; roaring; its teeth clattering
        addStance(want, { Jaw = { 0.05 * math.sin(t * 1.3) + 0.02 * math.sin(t * 3.1), 0, 0 } }, (1 - kind("roar")) * (1 - slam))
        addStance(want, BF.ROAR, math.max(kind("roar"), slam, 0.5 * rise))
        local clatter = kind("clatter")
        if clatter > 0 then
            addStance(want, { Jaw = { 0.13 * math.sin(t * 34), 0, 0 }, Head = { 0.02 * math.sin(t * 34 + 1), 0, 0 } }, clatter)
        end

        -- its legs: drawn up in a crouch, the claws flexing; trailing back as it goes; a forefoot swiping now and then
        local flex = 0.07 * math.sin(t * 0.9)
        addStance(want, { LegFL1 = { flex, 0, 0 }, LegFR1 = { -flex, 0, 0 }, PawFL = { 0.12 * math.sin(t * 0.9 + 1), 0, 0 }, PawFR = { -0.12 * math.sin(t * 0.9 + 1), 0, 0 },
            LegBL1 = { 0.5 * flex, 0, 0 }, LegBR1 = { -0.5 * flex, 0, 0 } }, (1 - pace) * (1 - rise))
        addStance(want, { LegFL1 = { 0.3, 0, 0 }, LegFR1 = { 0.3, 0, 0 }, LegBL1 = { 0.35, 0, 0 }, LegBR1 = { 0.35, 0, 0 }, LegBL2 = { -0.2, 0, 0 },
            LegBR2 = { -0.2, 0, 0 } }, pace)
        addStance(want, BF.SWIPE, kind("swipe"))

        -- the tail: a slow wave running down it to its knot; streaming as it goes
        for k = 1, 6 do
            local w = (0.06 + 0.07 * k / 6) * math.sin(t * 0.9 - k * 0.55) * (1 - 0.55 * pace)
            addStance(want, { ["Tail" .. k] = { 0.035 * math.sin(t * 0.7 - k * 0.5) - 0.02 * pace, w, 0 } }, 1)
        end

        -- a shake: its whole frame rattles
        local shake = kind("shake")
        if shake > 0 then
            for k, name in { "Chest", "Neck1", "Neck2", "Head", "Jaw", "Tail2", "Tail4", "WingL1", "WingR1" } do
                addStance(want, { [name] = { 0.035 * math.sin(t * 38 + k * 1.7), 0.035 * math.sin(t * 31 + k * 2.3), 0.02 * math.sin(t * 27 + k) } }, shake)
            end
        end

        -- it rises and sinks slowly in the air; with each downstroke; up as it rears, down as it slams
        local lift = (0.025 * math.sin(t * 1.2) + 0.03 * down * amp + 0.08 * rise - 0.05 * slam) * u
        for _, name in BF.BONES do
            local a = want[name] or Vector3.zero
            local y = if name == "Hips" then lift elseif name == "Soul" then (0.008 * math.sin(t * 2.3) + 0.02 * rise) * u else 0
            pose(m[name], CFrame.new(0, y, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- its brows: a steady glare; lifted when it is curious about you; low and hard as it roars
        local glare = 0.12 + 0.2 * math.max(kind("roar"), rise, slam) - 0.3 * (if s.curious then calm else 0)
        s.glare = (s.glare or glare) + (glare - (s.glare or glare)) * math.min(1, dt * 4)
        pose(m.BrowL, CFrame.fromAxisAngle(BF.BROW_AXIS.L, s.glare))
        pose(m.BrowR, CFrame.fromAxisAngle(BF.BROW_AXIS.R, -s.glare))

        -- its fire: the eyes and throat brighten as it roars, rears and flares; the flames in its chest leap
        local heat = math.max(kind("roar"), flare, rise, slam)
        local eyes = rig.parts.Eyes
        if eyes then
            eyes.Color = BF.EYE:Lerp(BF.EYE_HOT, 0.15 + 0.15 * math.sin(t * 2.7) + 0.6 * heat)
        end
        local maw = rig.parts.Maw
        if maw then
            maw.Color = BF.SOUL_DEEP:Lerp(BF.SOUL, 0.55 + 0.2 * math.sin(t * 1.9) + 0.45 * heat)
        end
        local fires = s.fires
        if fires then
            fires.chest.Rate = fires.chestRate * (1 + 1.2 * heat)
            for _, flame in fires.eyes do
                flame.Rate = fires.eyeRate * (1 + heat)
            end
        end
    end

    -- It slams down (animateBonefireDragon): a ring of bone spires bursts up from the ground round it, each crowned with blue soul fire, and a
    -- pillar of soul fire roars up out of its chest; a flash of cold light. The spires sink back into the ground; gone by 1.6 s.
    function Blasts.OssuaryPyre(rig, fx)
        local u = rig.unit
        local reduced = BF.reduced()
        local soul = rig.parts.Soul
        local origin = if soul then soul.Position else rig.rootPart.Position

        -- the ground under it (in the world; a portrait has none, so a little below it there)
        local ground = origin - Vector3.new(0, 4 * u, 0)
        if rig.rootPart:IsDescendantOf(workspace) then
            local params = RaycastParams.new()
            local ignore = { rig.model }
            for _, player in Players:GetPlayers() do
                if player.Character then
                    table.insert(ignore, player.Character)
                end
            end
            local companions = workspace:FindFirstChild("PetCompanions")
            if companions then
                table.insert(ignore, companions)
            end
            params.FilterDescendantsInstances = ignore
            params.FilterType = Enum.RaycastFilterType.Exclude
            local hit = workspace:Raycast(origin, Vector3.new(0, -40, 0), params)
            if hit then
                ground = hit.Position
            end
        end

        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(origin), BF.SOUL)
        holder.Transparency = 1
        local folder = holder.Parent
        local light = Instance.new("PointLight")
        light.Color = BF.SOUL
        light.Range = 16 * u
        light.Brightness = 2.5
        light.Shadows = false
        light.Parent = holder
        tweenAfter(0.25, light, TweenInfo.new(1.0), { Brightness = 0 })

        -- the pillar of soul fire out of its chest
        local pillar = emitter(holder, {
            Name = "SoulPillar",
            Texture = BF.FIRE,
            Rate = 0,
            Lifetime = NumberRange.new(0.45, 0.7),
            Speed = NumberRange.new(7 * u, 11 * u),
            SpreadAngle = Vector2.new(9, 9),
            EmissionDirection = Enum.NormalId.Top,
            Drag = 2,
            Rotation = NumberRange.new(0, 360),
            RotSpeed = NumberRange.new(-90, 90),
            Size = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0.6 * u),
                NumberSequenceKeypoint.new(0.4, 0.85 * u),
                NumberSequenceKeypoint.new(1, 0.2 * u),
            }),
            Color = ColorSequence.new({
                ColorSequenceKeypoint.new(0, BF.SOUL_HOT),
                ColorSequenceKeypoint.new(0.4, BF.SOUL),
                ColorSequenceKeypoint.new(1, BF.SOUL_DEEP),
            }),
            Transparency = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0.4),
                NumberSequenceKeypoint.new(1, 1),
            }),
            Brightness = 1.3, -- (at 3, with 50 a second, it washed the whole screen white in Play)
        })
        pillar:Emit(if reduced then 10 else 20)
        if not reduced then
            pillar.Rate = 26
            task.delay(0.4, function()
                pillar.Enabled = false
            end)
        end

        -- the ring of bone spires, bursting up round it and sinking back
        local count = if reduced then 4 else 8
        local spin = math.random() * 2 * math.pi
        for k = 1, count do
            local angle = spin + k / count * 2 * math.pi
            local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
            local base = ground + out * (3.2 + 0.4 * (k % 2)) * u
            local height = (1.6 + 0.6 * ((k * 7) % 3) / 2) * u
            local tilt = CFrame.fromAxisAngle(Vector3.yAxis:Cross(out).Unit, -0.38)
            local spire = Instance.new("Part")
            spire.Anchored = true
            spire.CanCollide = false
            spire.CanTouch = false
            spire.CanQuery = false
            spire.CastShadow = false
            spire.Material = Enum.Material.Limestone -- (porous, like old bone: smooth plastic read as white eggs in the sun)
            spire.Color = BF.SPIRE
            spire.Size = Vector3.new(0.34 * u, height, 0.34 * u)
            local mesh = Instance.new("SpecialMesh")
            mesh.MeshType = Enum.MeshType.Sphere
            mesh.Parent = spire
            local sunk = CFrame.new(base) * tilt * CFrame.new(0, -height * 0.55, 0)
            local risen = CFrame.new(base) * tilt * CFrame.new(0, height * 0.32, 0)
            spire.CFrame = sunk
            spire.Parent = folder
            local delay = 0.03 * k
            tweenAfter(delay, spire, TweenInfo.new(0.16, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = risen })
            tweenAfter(delay + 0.85, spire, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = sunk })
            -- its crown of fire, and a burst of it at its root
            local tip = Instance.new("Attachment")
            tip.Position = Vector3.new(0, height * 0.42, 0)
            tip.Parent = spire
            local crown = emitter(tip, {
                Name = "SpireFire",
                Texture = BF.FIRE,
                Rate = 0,
                Lifetime = NumberRange.new(0.3, 0.5),
                Speed = NumberRange.new(0.8 * u, 1.6 * u),
                SpreadAngle = Vector2.new(18, 18),
                EmissionDirection = Enum.NormalId.Top,
                Acceleration = Vector3.new(0, 2 * u, 0),
                Size = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.38 * u),
                    NumberSequenceKeypoint.new(1, 0.06 * u),
                }),
                Color = ColorSequence.new(BF.SOUL_HOT, BF.SOUL),
                Transparency = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.35),
                    NumberSequenceKeypoint.new(1, 1),
                }),
                Brightness = 1.2,
            })
            task.delay(delay + 0.1, function()
                if crown.Parent then
                    crown.Rate = if reduced then 6 else 10
                end
            end)
            task.delay(delay + 0.8, function()
                if crown.Parent then
                    crown.Enabled = false
                end
            end)
            if not reduced then
                local root = Instance.new("Attachment")
                root.WorldPosition = base
                root.Parent = holder
                local dust = emitter(root, {
                    Name = "SpireDust",
                    Texture = BF.SMOKE,
                    Rate = 0,
                    LightEmission = 0.15,
                    Lifetime = NumberRange.new(0.5, 0.8),
                    Speed = NumberRange.new(1 * u, 2 * u),
                    SpreadAngle = Vector2.new(70, 70),
                    EmissionDirection = Enum.NormalId.Top,
                    Drag = 3,
                    Size = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0.3 * u),
                        NumberSequenceKeypoint.new(1, 0.9 * u),
                    }),
                    Color = ColorSequence.new(Color3.fromRGB(150, 160, 185)),
                    Transparency = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0.5),
                        NumberSequenceKeypoint.new(1, 1),
                    }),
                })
                task.delay(delay, function()
                    if dust.Parent then
                        dust:Emit(5)
                    end
                end)
            end
        end
    end

    local bones = table.clone(BF.BONES)
    for _, name in { "BrowL", "BrowR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.BonefireDragon = {
        Skinned = true,
        Bones = bones,
        Points = { "Head", "EyeL", "EyeR" },
        GlowColors = {
            ["3d7bff"] = BF.SOUL, -- its soul fire (and the fire in its throat)
            ["4aa6ff"] = BF.EYE, -- the cold light deep in its sockets
        },
        Effects = {
            Light = "Soul",
            Pulse = "Soul",
            Blast = "OssuaryPyre",
            NovaLight = 1.5,
        },
        Colors = {
            Gold = BF.SOUL,
            Amber = BF.SOUL_DEEP,
            Orange = BF.SOUL,
            Sun = BF.SOUL_HOT,
            Ivory = BF.BONE,
        },
        Animate = animateBonefireDragon,
    }
end

do
    -- The Echo Bat (skinned): a small, plush fruit bat of the Ancient Grove, made of rings that keep sound (the grove's growth rings and a record's
    -- grooves). Cocoa fur, a fawn face, a cream bib on its chest ringed twice like a ripple; big calla-lily trumpet ears, ivory inside and cut with
    -- grooves, three of them glowing teal with the sounds it has kept; plum wings on three long fingers. It hovers on slow, lazy wing beats, rising a
    -- little on each downstroke; its ears swivel on their own, listening; it looks about, often at you, and blinks. Now and then it cocks its head to
    -- listen, flicks an ear, or chirps (a small ring of sound out of each ear). Still a long while, it dozes on the air, eyes half shut, legs tucked,
    -- beating slower. Moving, it leans into a glide, beating harder. Its special, A Voice from a Hundred Years Ago: it draws its wings up and its ears
    -- back, listening (to 0.3); rears, head up, wings spread, ears flaring (the burst, 0.42: Blasts.HundredYearEcho): rings of sound pour out of its
    -- ears and ripple out round it; then older rings, gold, come back to it out of the distance and into its ears, which glow gold as they land.
    local EB = {
        FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
        LID_HINGE = { L = Vector3.new(0.9149, 0.1203, -0.3853), R = Vector3.new(0.9149, -0.1203, 0.3853) }, -- both lids of an eye turn on this line
        BLINK_UPPER = math.rad(76), -- (the two add past the 102 degrees between its lids' edges: at 64 + 22 a band of eye showed)
        BLINK_LOWER = math.rad(32),
        -- its ears' mouths, from each ear's bone (metres, its own axes), and the way each faces: from echo_bat.py
        EAR_AT = { L = Vector3.new(-0.0581, 0.6577, -0.0328), R = Vector3.new(0.0581, 0.6577, -0.0328) },
        MOUTH_AT = { L = Vector3.new(-0.15, 0.83, -0.1), R = Vector3.new(0.15, 0.83, -0.1) },
        MOUTH_FACING = { L = Vector3.new(-0.568, 0.613, -0.548), R = Vector3.new(0.568, 0.613, -0.548) },
        -- its stances (game axes; turns x, y, z), each checked in Blender (echo_bat.py: membranes against head, ears and trunk, wing against wing,
        -- arms against head; and along every slerp between them; no torn skin)
        FLAP_UP = { ArmL = { 0, 0.1, -0.75 }, ArmR = { 0, -0.1, 0.75 }, ForeL = { 0, 0, -0.12 }, ForeR = { 0, 0, 0.12 }, Fing1L = { 0, -0.05, -0.1 },
            Fing1R = { 0, 0.05, 0.1 }, Fing2L = { 0, -0.08, -0.08 }, Fing2R = { 0, 0.08, 0.08 }, Fing3L = { 0, -0.1, 0 }, Fing3R = { 0, 0.1, 0 },
            Body = { 0.06, 0, 0 }, EarL = { 0.1, 0, 0.05 }, EarR = { 0.1, 0, -0.05 } },
        FLAP_DOWN = { ArmL = { 0, -0.12, 0.6 }, ArmR = { 0, 0.12, -0.6 }, ForeL = { 0, 0, 0.12 }, ForeR = { 0, 0, -0.12 }, Fing1L = { 0, 0.06, 0.22 },
            Fing1R = { 0, -0.06, -0.22 }, Fing2L = { 0, 0.08, 0.22 }, Fing2R = { 0, -0.08, -0.22 }, Fing3L = { 0, 0.1, 0.18 }, Fing3R = { 0, -0.1, -0.18 },
            Body = { -0.05, 0, 0 }, EarL = { -0.08, 0, -0.04 }, EarR = { -0.08, 0, 0.04 } },
        GLIDE = { ArmL = { 0, -0.05, 0.28 }, ArmR = { 0, 0.05, -0.28 }, ForeL = { 0, 0, -0.1 }, ForeR = { 0, 0, 0.1 }, Fing1L = { 0, -0.12, 0 },
            Fing1R = { 0, 0.12, 0 }, Fing2L = { 0, -0.08, 0.05 }, Fing2R = { 0, 0.08, -0.05 }, Fing3L = { 0, -0.04, 0.1 }, Fing3R = { 0, 0.04, -0.1 },
            Body = { -0.18, 0, 0 }, Head = { 0.12, 0, 0 }, EarL = { -0.2, 0, -0.05 }, EarR = { -0.2, 0, 0.05 } },
        ECHO = { Head = { 0.32, 0, 0 }, Body = { 0.12, 0, 0 }, EarL = { -0.2, -0.15, 0.2 }, EarR = { -0.2, 0.15, -0.2 }, ArmL = { 0, -0.1, -0.35 },
            ArmR = { 0, 0.1, 0.35 }, ForeL = { 0, 0, -0.15 }, ForeR = { 0, 0, 0.15 }, Fing1L = { 0, -0.1, -0.1 }, Fing1R = { 0, 0.1, 0.1 },
            Fing2L = { 0, -0.12, 0 }, Fing2R = { 0, 0.12, 0 }, Fing3L = { 0, -0.12, 0.05 }, Fing3R = { 0, 0.12, -0.05 } },
        LISTEN = { L = { Head = { 0.08, 0.22, 0.28 }, EarL = { -0.15, -0.2, 0.1 }, EarR = { -0.05, 0.25, -0.05 } }, -- cocked to its left; its right mirrored
            R = { Head = { 0.08, -0.22, -0.28 }, EarR = { -0.15, 0.2, -0.1 }, EarL = { -0.05, -0.25, 0.05 } } },
        FLICK = { L = { EarL = { 0.3, 0.15, 0.25 } }, R = { EarR = { 0.3, -0.15, -0.25 } } },
        LEGS_TUCK = { LegL = { -0.4, 0, 0.1 }, LegR = { -0.4, 0, -0.1 } },
        BEAT = { 1.5, 2.9 }, -- wing beats a second: hovering lazily, and flying
        LIFT = 0.024, -- metres it rises on each downstroke
        BONES = { "Body", "Head", "EarL", "EarR", "EyeL", "EyeR", "ArmL", "ForeL", "HandL", "Fing1L", "Fing2L", "Fing3L", "ArmR", "ForeR", "HandR",
            "Fing1R", "Fing2R", "Fing3R", "LegL", "LegR" },
        RING = "rbxassetid://12403112662", -- a thin glowing ring with brighter arcs (also RealmAura's)
        ECHO_COLOR = Color3.fromRGB(31, 224, 198), -- the sounds it keeps: sea-glass teal
        ECHO_DIM = Color3.fromRGB(16, 150, 136),
        ECHO_BRIGHT = Color3.fromRGB(140, 255, 236),
        OLD = Color3.fromRGB(240, 192, 104), -- a voice from a hundred years ago: old gold
        RING_OUT = Color3.fromRGB(90, 255, 225), -- its rings of sound (particles: saturated, or they wash out white)
        RING_OLD, RING_OLD_DEEP = Color3.fromRGB(255, 196, 80), Color3.fromRGB(230, 150, 50),
        PLUM = Color3.fromRGB(150, 90, 120),
        IVORY = Color3.fromRGB(246, 234, 214),
    }

    function EB.reduced()
        local player = Players.LocalPlayer
        return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
    end

    -- Each ear's mouth now: where it is and the way it faces in the world, carried on its ear's bone (offsets taken at rest, in the bone's own frame).
    function EB.mouth(rig, s, side)
        local bone = rig.points["Ear" .. side]
        local m = s.mouths and s.mouths[side]
        if not bone or not m then
            local root = rig.rootPart.CFrame
            return root:PointToWorldSpace(EB.MOUTH_AT[side] * rig.meters), root:VectorToWorldSpace(EB.MOUTH_FACING[side])
        end
        local cf = bone.TransformedWorldCFrame
        return cf:PointToWorldSpace(m.at), cf:VectorToWorldSpace(m.facing)
    end

    -- Once, at rest, before any pose: each ear's mouth on its bone; a soft teal light at its head; the little rings of its chirps.
    function EB.init(rig, s)
        s.inited = true
        s.mouths = {}
        local root = rig.rootPart.CFrame
        for _, side in { "L", "R" } do
            local bone = rig.points["Ear" .. side]
            if bone then
                local cf = bone.TransformedWorldCFrame
                local world = cf.Position + root:VectorToWorldSpace((EB.MOUTH_AT[side] - EB.EAR_AT[side]) * rig.meters)
                s.mouths[side] = { at = cf:PointToObjectSpace(world), facing = cf:VectorToObjectSpace(root:VectorToWorldSpace(EB.MOUTH_FACING[side])) }
            end
        end
        local head = rig.points.Head
        if head then
            local a = Instance.new("Attachment")
            a.Name = "EchoLight"
            local frame = head.TransformedWorldCFrame
            a.Position = frame:PointToObjectSpace(frame.Position + root.UpVector * 0.25 * rig.meters)
            a.Parent = head
            local light = Instance.new("PointLight")
            light.Name = "EchoGlow"
            light.Color = EB.ECHO_COLOR
            light.Range = 4 * rig.unit
            light.Brightness = 0.35
            light.Shadows = false
            light.Parent = a
            s.light = light
        end
        if not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
            s.chirps = {}
            for _, side in { "L", "R" } do
                local a = Instance.new("Attachment")
                a.Name = "Chirp" .. side
                a.Parent = rig.rootPart
                local ring = Instance.new("ParticleEmitter")
                ring.Name = "ChirpRing"
                ring.Texture = EB.RING
                ring.Enabled = false
                ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
                ring.EmissionDirection = Enum.NormalId.Front
                ring.SpreadAngle = Vector2.zero
                ring.Lifetime = NumberRange.new(0.45)
                ring.Speed = NumberRange.new(2.6 * rig.unit)
                ring.Drag = 1.2
                ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * rig.unit), NumberSequenceKeypoint.new(1, 0.95 * rig.unit) })
                ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
                ring.Color = ColorSequence.new(EB.RING_OUT, EB.ECHO_COLOR)
                ring.LightEmission = 0.6
                ring.LightInfluence = 0
                ring.Parent = a
                s.chirps[side] = { at = a, ring = ring }
            end
        end
    end

    function EB.chirp(rig, s)
        if not s.chirps or EB.reduced() then
            return
        end
        for side, c in s.chirps do
            local at, facing = EB.mouth(rig, s, side)
            c.at.WorldCFrame = CFrame.lookAt(at, at + facing)
            c.ring:Emit(1)
        end
    end

    local function animateEchoBat(rig, s, moving, fly, nova)
        if not s.inited then
            EB.init(rig, s) -- at rest, before any pose
        end
        local camera = workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > EB.FAR then
            return
        end
        local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
        local pace = math.max(moving, fly)

        -- the special: listening, wings drawn up and ears laid back (to 0.3); rearing into its echo (to 0.42, the burst); held, its ears trembling
        -- (to 0.7); settling (to 0.95). Its ears glow bright as the rings pour out, and gold as the old ones come back in (0.84 to 0.97).
        local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
        local special = progress > 0
        local gather = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.3, 0.4, progress))
        local rear = smoothstep(0.3, 0.42, progress) * (1 - smoothstep(0.7, 0.95, progress))
        local tremble = if progress > 0.42 and progress < 0.72 then math.sin(t * 60) * (1 - (progress - 0.42) / 0.3) else 0
        local homecoming = smoothstep(0.82, 0.86, progress) * (1 - smoothstep(0.95, 1, progress))

        -- still a long while, it dozes on the air; now and then it cocks its head to listen, flicks an ear, or chirps
        s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
        local wantDoze = if s.still > 14 then 1 else 0
        s.doze = (s.doze or 0) + (wantDoze - (s.doze or 0)) * math.min(1, dt * (if wantDoze > (s.doze or 0) then 0.7 else 5))
        local doze = smoothstep(0, 1, s.doze)
        s.nextFidget = s.nextFidget or t + 4
        if t >= s.nextFidget then
            local r = math.random()
            s.fidgetAt = t
            s.fidgetKind = if r < 0.38 then "listen" elseif r < 0.68 then "flick" else "chirp"
            s.fidgetSide = if math.random() < 0.5 then "L" else "R"
            s.nextFidget = t + 4.5 + math.random() * 5.5
            s.chirped = false
        end
        local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / (if s.fidgetKind == "listen" then 2.2 else 1.1), 0, 1) else 1
        local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - doze) * (if special then 0 else 1)
        if s.fidgetKind == "chirp" and not s.chirped and env > 0.3 and fidget > 0.2 then
            s.chirped = true
            EB.chirp(rig, s)
        end

        local want = {}
        -- the wing beat: lazy as it hovers, harder as it flies, slower as it dozes; hard through its special
        local rate = (EB.BEAT[1] + (EB.BEAT[2] - EB.BEAT[1]) * pace) * (1 - 0.35 * doze) * (1 + 0.5 * rear)
        s.phase = ((s.phase or 0) + dt * rate * 2 * math.pi) % (2 * math.pi)
        local b = math.sin(s.phase)
        local amp = (0.6 + 0.35 * pace) * (1 - 0.4 * doze) * (1 - gather) + 0.4 * rear
        addStance(want, EB.FLAP_UP, math.max(0, b) * amp + 0.7 * gather)
        addStance(want, EB.FLAP_DOWN, math.max(0, -b) * amp)
        addStance(want, EB.GLIDE, pace * 0.75 * (1 - rear))
        addStance(want, EB.ECHO, rear)
        addStance(want, { Head = { -0.12, 0, 0 }, EarL = { 0.2, 0.1, -0.05 }, EarR = { 0.2, -0.1, 0.05 } }, gather) -- head down, ears back: listening
        addStance(want, { EarL = { 0, 0, 0.05 * tremble }, EarR = { 0, 0, -0.05 * tremble } }, 1)
        addStance(want, EB.LEGS_TUCK, math.max(doze, pace * 0.6))
        addStance(want, { Head = { -0.1, 0, 0 }, EarL = { 0.15, 0, 0.08 }, EarR = { 0.15, 0, -0.08 } }, doze) -- head nodding, ears drooping
        if s.fidgetKind == "listen" then
            addStance(want, EB.LISTEN[s.fidgetSide or "L"], fidget)
        elseif s.fidgetKind == "flick" then
            addStance(want, EB.FLICK[s.fidgetSide or "L"], fidget * (0.6 + 0.4 * math.sin(t * 20)))
        elseif s.fidgetKind == "chirp" then
            addStance(want, { Head = { 0.12, 0, 0 } }, fidget)
        end

        -- its ears swivel on their own, listening; its gaze: now on you, now about
        s.nextEars = s.nextEars or 0
        if t >= s.nextEars then
            s.nextEars = t + 1.2 + math.random() * 2.2
            s.earL, s.earR = (math.random() - 0.5) * 0.24, (math.random() - 0.5) * 0.24
        end
        s.earLNow = (s.earLNow or 0) + ((s.earL or 0) - (s.earLNow or 0)) * math.min(1, dt * 6)
        s.earRNow = (s.earRNow or 0) + ((s.earR or 0) - (s.earRNow or 0)) * math.min(1, dt * 6)
        local calm = (1 - 0.6 * pace) * (1 - doze) * (1 - math.max(gather, rear))
        addStance(want, { EarL = { 0, s.earLNow, 0 }, EarR = { 0, s.earRNow, 0 } }, calm)
        local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
        s.nextGaze = s.nextGaze or 0
        if t >= s.nextGaze then
            s.nextGaze = t + 2 + math.random() * 3
            s.atYou = math.random() < 0.55
            s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.4, (math.random() - 0.5) * 0.4
        end
        local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -1, 1) else s.gazeYaw) * calm
        local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.6, -0.3, 0.4) else s.gazePitch) * calm
        s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
        s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
        addStance(want, { Head = { 0.25 * s.pitch, 0.4 * s.yaw, 0.05 * s.yaw }, EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 } }, 1)
        addStance(want, { Body = { 0.015 * math.sin(t * 1.3), 0, 0 } }, 1) -- breathing

        local lift = -EB.LIFT * b * amp * u
        for _, name in EB.BONES do
            local a = want[name] or Vector3.zero
            pose(m[name], CFrame.new(0, if name == "Body" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
        end

        -- the sounds it keeps, glowing softly in its ears, a slow ripple; bright through its echo, gold as the old voice comes home
        local echo = rig.parts.Echo
        if echo then
            local ripple = 0.5 + 0.5 * math.sin(t * 1.7)
            local c = EB.ECHO_DIM:Lerp(EB.ECHO_COLOR, 0.45 + 0.55 * ripple)
            c = c:Lerp(EB.ECHO_DIM, gather * 0.8):Lerp(EB.ECHO_BRIGHT, math.max(rear * (1 - homecoming), if s.fidgetKind == "chirp" then fidget * 0.6 else 0))
            echo.Color = c:Lerp(EB.OLD, homecoming)
        end
        if s.light then
            s.light.Brightness = 0.35 + 1.6 * rear * (1 - homecoming) + 0.2 * (1 - doze) * math.sin(t * 1.7)
            s.light.Color = EB.ECHO_COLOR:Lerp(EB.OLD, homecoming)
        end

        -- the eyes: blinks; half shut as it dozes, shut as it gathers; wide through its echo and when it listens
        local wide = math.max(rear, if s.fidgetKind == "listen" then fidget else 0)
        s.nextBlink = s.nextBlink or t + 3
        local blink = 0
        if t >= s.nextBlink then
            local a = (t - s.nextBlink) / 0.22
            if a >= 1 then
                s.nextBlink = t + 2 + math.random() * 4
            else
                blink = 1 - math.abs(2 * a - 1)
            end
        end
        local close = math.max(blink, 0.92 * doze, gather) * (1 - wide) -- (dozing at 0.6, its half-shut lids read as a scowl in Play)
        local upper = EB.BLINK_UPPER * close - math.rad(10) * wide
        local lower = EB.BLINK_LOWER * close - math.rad(6) * wide
        for _, side in { "L", "R" } do
            pose(m["LidU" .. side], CFrame.fromAxisAngle(EB.LID_HINGE[side], -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(EB.LID_HINGE[side], lower))
        end
    end

    -- Its echo (animateEchoBat, the burst): rings of sound pour out of its ears, three from each, and two ripples spread round it like the rings on its
    -- chest; then, out of the distance in front of each ear, older rings, gold, come back to it and shrink into its ears: a voice from a hundred years
    -- ago. All of it gone by 1.4 s.
    function Blasts.HundredYearEcho(rig, fx)
        local u = rig.unit
        local s = rig.state
        local reduced = EB.reduced()
        local function ringEmitter(holder, life, speed, size0, size1, transparency, color, fade)
            local ring = Instance.new("ParticleEmitter")
            ring.Texture = EB.RING
            ring.Enabled = false
            ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
            ring.EmissionDirection = Enum.NormalId.Front
            ring.SpreadAngle = Vector2.zero
            ring.Lifetime = NumberRange.new(life)
            ring.Speed = NumberRange.new(speed)
            ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, size0), NumberSequenceKeypoint.new(1, size1) })
            ring.Transparency = transparency
            ring.Color = ColorSequence.new(color, fade or color)
            ring.LightEmission = 0.6 -- (at 1 they washed out near white in Play: the gold read as no colour at all)
            ring.LightInfluence = 0
            ring.Parent = holder
            return ring
        end
        local count = if reduced then 2 else 3
        for _, side in { "L", "R" } do
            local at, facing = EB.mouth(rig, s, side)
            -- out of its ear
            local out = fx.neon(Vector3.one * 0.05, CFrame.lookAt(at, at + facing), EB.ECHO_COLOR)
            out.Transparency = 1
            local rings = ringEmitter(out, 0.75, 6 * u, 0.3 * u, 2.6 * u, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05),
                NumberSequenceKeypoint.new(0.6, 0.5), NumberSequenceKeypoint.new(1, 1) }), EB.RING_OUT, EB.ECHO_COLOR)
            for k = 0, count - 1 do
                task.delay(k * 0.13, function()
                    if rings.Parent then
                        rings:Emit(1)
                    end
                end)
            end
            -- and home again: from out in front of it, back into its ear, older and gold
            local far = at + facing * 3.2 * u
            local back = fx.neon(Vector3.one * 0.05, CFrame.lookAt(far, at), EB.OLD)
            back.Transparency = 1
            local old = ringEmitter(back, 0.55, 3.2 * u / 0.55, 2 * u, 0.25 * u, NumberSequence.new({ NumberSequenceKeypoint.new(0, 1),
                NumberSequenceKeypoint.new(0.35, 0.35), NumberSequenceKeypoint.new(0.9, 0.2), NumberSequenceKeypoint.new(1, 1) }), EB.RING_OLD, EB.RING_OLD_DEEP)
            for k = 0, count - 1 do
                task.delay(0.5 + k * 0.13, function()
                    if old.Parent then
                        old:Emit(1)
                    end
                end)
            end
        end
        -- two ripples swelling round it, like the rings on its chest
        local body = rig.points.Body
        local centre = if body then body.TransformedWorldCFrame.Position else rig.rootPart.Position
        local flat = fx.neon(Vector3.one * 0.05, CFrame.lookAt(centre, centre + Vector3.yAxis), EB.ECHO_COLOR)
        flat.Transparency = 1
        local ripple = ringEmitter(flat, 0.9, 0, 0.6 * u, 5.5 * u, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) }), EB.ECHO_COLOR)
        ripple.Orientation = Enum.ParticleOrientation.FacingCamera -- (lying flat across a rise, with or without drag, it never showed in Play: facing you it swells round it)
        ripple:Emit(1)
        task.delay(0.16, function()
            if ripple.Parent then
                ripple:Emit(1)
            end
        end)
        -- a teal flash about its head
        local head = rig.points.Head
        local light = Instance.new("PointLight")
        light.Color = EB.ECHO_COLOR
        light.Range = 6 * u
        light.Brightness = 1.2 -- (at 2.2 and 9 it washed the bat and the ground round it teal in Play)
        light.Shadows = false
        light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(if head then head.TransformedWorldCFrame.Position else centre), EB.ECHO_COLOR)
        light.Parent.Transparency = 1
        TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
        -- a few motes of sound drifting off its ears
        if not reduced then
            local at = EB.mouth(rig, s, "L")
            local motes = Instance.new("ParticleEmitter")
            motes.Texture = SPARKLE
            motes.Enabled = false
            motes.Lifetime = NumberRange.new(0.6, 1.1)
            motes.Speed = NumberRange.new(0.6 * u, 1.6 * u)
            motes.SpreadAngle = Vector2.new(180, 180)
            motes.Drag = 2
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(EB.ECHO_BRIGHT, EB.ECHO_COLOR)
            motes.LightEmission = 1
            motes.LightInfluence = 0
            motes.Parent = light.Parent
            light.Parent.CFrame = CFrame.new((at + EB.mouth(rig, s, "R")) / 2)
            motes:Emit(16)
        end
    end

    local bones = table.clone(EB.BONES)
    for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
        table.insert(bones, name)
    end
    PetRig.Profiles.EchoBat = {
        Skinned = true,
        Bones = bones,
        Points = { "Body", "Head", "EarL", "EarR" },
        GlowColors = {
            ["1fe0c6"] = EB.ECHO_COLOR, -- the sounds it keeps, in the grooves of its ears
            ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
        },
        Effects = {
            Blast = "HundredYearEcho",
            NovaLight = 2,
        },
        Colors = {
            Gold = EB.ECHO_COLOR,
            Amber = EB.OLD,
            Orange = EB.PLUM,
            Sun = EB.ECHO_BRIGHT,
            Ivory = EB.IVORY,
        },
        Animate = animateEchoBat,
    }
end

return PetRig

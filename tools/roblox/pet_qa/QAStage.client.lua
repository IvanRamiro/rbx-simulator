-- QA HARNESS for the exclusive beasts' rigs (kept here, outside src, so Rojo does not sync it). Copy it into src/client/Pets/_Preview/ (never commit it there), play on a test save, and set the attributes below on the client.
-- a stage in the sky where a pet, built by the real PetModels and posed by the real PetRig.update, is driven along a
-- scripted path (speed, turn, flight) on a stepped clock, and filmed. Studio only. Attributes on the player: QAPet, QASize, QAMutation, QAScenario, QAGo (change it
-- to restart), QAFreeze (sim seconds to stop at; nil runs on), QARate, QACam (side/left/back/front/three/top/wing), QADist, QAHeight, QALook, QAFocus.
-- QAQuery (a BindableFunction in PlayerGui) returns fields of a pet's rig state for numbers.
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

if not RunService:IsStudio() then
    return
end

local p = Players.LocalPlayer
local PetModels = require(script.Parent.Parent:WaitForChild("PetModels"))
local PetRig = require(script.Parent.Parent:WaitForChild("PetRig"))
local cam = workspace.CurrentCamera

local sim = nil
local query = Instance.new("BindableFunction")
query.Name = "QAQuery"
query.Parent = p:WaitForChild("PlayerGui")
query.OnInvoke = function(modelName, keys)
    local model = workspace:FindFirstChild(modelName)
    local rig = model and PetModels.getRig(model)
    if not rig then
        return nil
    end
    if keys[1] == "bench" then -- time the animate function alone, and the whole update, over many calls
        local s = rig.state
        local n = 400
        rig.deltaTime = 1 / 60
        local t0 = os.clock()
        for _ = 1, n do
            s.time += 1 / 60
            rig.profile.Animate(rig, s, s.walk, s.fly, 0)
        end
        local a = (os.clock() - t0) / n * 1e6
        t0 = os.clock()
        for _ = 1, n do
            PetRig.update(rig, 1 / 60, { speed = sim and sim.speed or 0, flying = false })
        end
        local u = (os.clock() - t0) / n * 1e6
        return { animateUs = a, updateUs = u }
    end
    local out = {}
    for _, k in keys do
        local v = rig.state[k]
        if k == "meters" then v = rig.meters end
        if k == "costUs" then v = if sim and sim.updates and sim.updates > 0 then sim.cost / sim.updates * 1e6 else 0 end
        if type(v) == "table" then
            out[k] = table.clone(v)
        else
            out[k] = v
        end
    end
    return out
end

local ORIGIN = Vector3.new(0, 900, 0)
local stage = workspace:FindFirstChild("QAStagePart")
if not stage then
    stage = Instance.new("Part")
    stage.Name = "QAStagePart"
    stage.Anchored = true
    stage.Size = Vector3.new(4000, 2, 4000)
    stage.Position = ORIGIN - Vector3.new(0, 1, 0)
    stage.Color = Color3.fromRGB(96, 140, 84)
    stage.Material = Enum.Material.Grass
    stage.CanCollide = true
    stage.Parent = workspace
end

-- scenarios: segments { duration, speed, turn rate, flying }
local SCEN = {
    stand = { { 60, 0, 0, false } },
    walk = { { 3, 0, 0, false }, { 30, 12, 0, false } },
    walkslow = { { 2, 0, 0, false }, { 30, 4, 0, false } },
    trot = { { 2, 0, 0, false }, { 30, 20, 0, false } },
    run = { { 2, 0, 0, false }, { 30, 34, 0, false } },
    stopgo = { { 2, 0, 0, false }, { 4, 16, 0, false }, { 4, 0, 0, false }, { 4, 16, 0, false }, { 4, 0, 0, false } },
    turn = { { 2, 0, 0, false }, { 3, 16, 0, false }, { 6, 16, 1.0, false }, { 3, 16, 0, false }, { 6, 16, -1.0, false } },
    spin = { { 2, 0, 0, false }, { 8, 0, 1.5, false } },
    fly = { { 2, 0, 0, false }, { 2, 14, 0, false }, { 8, 14, 0, true }, { 3, 14, 0, false }, { 3, 0, 0, false } },
    flyturn = { { 2, 0, 0, true }, { 8, 24, 0.9, true }, { 4, 0, 0, true } },
    flyfast = { { 2, 0, 0, true }, { 30, 40, 0, true } },
}
local function sceneAt(name, t)
    local list = SCEN[name] or SCEN.stand
    local acc = 0
    for _, seg in list do
        if t < acc + seg[1] then
            return seg
        end
        acc += seg[1]
    end
    return list[#list]
end

local function build()
    if sim and sim.model then
        sim.model:Destroy()
    end
    local petId = p:GetAttribute("QAPet") or "NineTailMoonfox"
    local size = p:GetAttribute("QASize") or "Normal"
    local model, root = PetModels.build(petId, size, nil, p:GetAttribute("QAMutation"))
    local rig = PetModels.getRig(model)
    model.Parent = workspace
    sim = { model = model, root = root, rig = rig, t = 0, pos = ORIGIN + Vector3.new(0, 4, 0), yaw = 0, yawTarget = 0, speed = 0, flyAlt = 0,
        scale = model:GetAttribute("SizeScale") or 1, steps = 0 }
    root.CFrame = CFrame.new(sim.pos)
    PetRig.update(rig, 1 / 60, { speed = 0, flying = false })
end

local STEP = 1 / 60
local function step()
    local sc = p:GetAttribute("QAScenario") or "stand"
    local seg = sceneAt(sc, sim.t)
    local dt = STEP
    sim.speed += (seg[2] - sim.speed) * (1 - math.exp(-dt * 5))
    sim.yawTarget += seg[3] * dt
    sim.yaw += (sim.yawTarget - sim.yaw) * (1 - math.exp(-dt * 6))
    local fwd = Vector3.new(-math.sin(sim.yaw), 0, -math.cos(sim.yaw))
    sim.pos += fwd * sim.speed * dt
    local rise = if seg[4] then 6 * sim.scale else 0
    sim.flyAlt += (rise - sim.flyAlt) * (1 - math.exp(-dt * 3))
    local bob = math.sin(sim.t * 2 / math.sqrt(math.max(sim.scale, 1))) * 0.25 * sim.scale
    local height = (3 + 0.9) * sim.scale + sim.flyAlt + bob
    sim.pos = Vector3.new(sim.pos.X, ORIGIN.Y + height, sim.pos.Z)
    sim.root.CFrame = CFrame.new(sim.pos) * CFrame.Angles(0, sim.yaw, 0)
    if p:GetAttribute("QARest") then -- the rest pose, then any manual turns: QABone = "Name=rx,ry,rz;Name2=rx,ry,rz" (radians, the pet's axes)
        for _, b in sim.model:GetDescendants() do
            if b:IsA("Bone") then
                b.Transform = CFrame.identity
            end
        end
    else
        local c0 = os.clock()
        PetRig.update(sim.rig, dt, { speed = sim.speed, flying = seg[4] })
        sim.cost = (sim.cost or 0) + (os.clock() - c0)
        sim.updates = (sim.updates or 0) + 1
    end
    local manual = p:GetAttribute("QABone")
    if manual and manual ~= "" then
        for entry in string.gmatch(manual, "[^;]+") do
            local name, rx, ry, rz = string.match(entry, "([%w_]+)=([%-%d%.]+),([%-%d%.]+),([%-%d%.]+)")
            if name and sim.rig.motors[name] then
                sim.rig.motors[name].Transform = CFrame.Angles(tonumber(rx), tonumber(ry), tonumber(rz))
            end
        end
    end
    sim.t += dt
end

local lastGo = nil
RunService.RenderStepped:Connect(function(realDt)
    local go = p:GetAttribute("QAGo")
    if go ~= lastGo then
        lastGo = go
        if go ~= nil then
            build()
        end
    end
    if not sim or not sim.model.Parent then
        return
    end
    local freeze = p:GetAttribute("QAFreeze")
    local n = math.clamp(math.floor(realDt / STEP + 0.5), 1, 6)
    local steps = if freeze then 0 else n
    if freeze and sim.t < freeze - 1e-6 then
        steps = math.min(math.ceil((freeze - sim.t) / STEP - 1e-6), 6000)
    end
    for _ = 1, steps do
        step()
    end
    local mode = p:GetAttribute("QACam")
    if mode and sim.root then
        cam.CameraType = Enum.CameraType.Scriptable
        local dist = p:GetAttribute("QADist") or 22
        local cf = sim.root.CFrame
        local focus = cf.Position + Vector3.new(0, p:GetAttribute("QALook") or 1.5, 0) + cf.LookVector * (p:GetAttribute("QAFocus") or 0)
        local h = p:GetAttribute("QAHeight") or 5
        local eye
        if mode == "side" then eye = cf.Position + cf.RightVector * dist + Vector3.new(0, h, 0)
        elseif mode == "left" then eye = cf.Position - cf.RightVector * dist + Vector3.new(0, h, 0)
        elseif mode == "back" then eye = cf.Position + cf.LookVector * -dist + Vector3.new(0, h, 0)
        elseif mode == "front" then eye = cf.Position + cf.LookVector * dist + Vector3.new(0, h, 0)
        elseif mode == "three" then eye = cf.Position + (cf.RightVector * 0.7 + cf.LookVector * 0.7) * dist + Vector3.new(0, h, 0)
        elseif mode == "threeback" then eye = cf.Position + (cf.RightVector * 0.7 - cf.LookVector * 0.7) * dist + Vector3.new(0, h, 0)
        elseif mode == "top" then eye = cf.Position + Vector3.new(0, dist, 0.01) end
        cam.CFrame = CFrame.lookAt(eye, focus)
    end
end)

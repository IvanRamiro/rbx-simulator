-- Outfits on the client: the "Robes" button for players who own an outfit (OutfitService decides,
-- this only asks), and the sway of every worn outfit's skinned pieces near the camera.
--
-- Sway (visual only, each client animates what it sees):
--   Skirt: four bone chains (front/back, left/right). Each opens as its thigh swings into it,
--          trails the wearer's movement, lifts as they fall and breathes a little at rest.
--          Each bone follows a spring, softer toward the hem.
--   Belt:  the pendant's tassel swings sideways with movement and forward as the wearer stops.
--   Cuffs: the wide cuffs trail behind the forearm's own movement.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Hud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Hud"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))

local player = Players.LocalPlayer

local OUTFIT_TAG = "WornOutfit"
local SWAY_DISTANCE = 120
local UP = Vector3.new(0, 1, 0)

-- ---------- the Robes button (on the HUD's rail, under Pets; a gold "On" while worn) ----------
local button, setRobesBadge = Hud.railButton("RobesButton", UiTheme.Icons.Robes, "Robes", 2, "Rose")
button.Visible = false

local function owned()
    local list = player:GetAttribute("OwnedOutfits")
    return if typeof(list) == "string" and list ~= "" then string.split(list, ",") else {}
end

local function refreshButton()
    local outfits = owned()
    local wearing = player:GetAttribute("OutfitId")
    button.Visible = #outfits > 0
    setRobesBadge(if wearing then "On" else nil, "Highlight")
end

button.Activated:Connect(function()
    local outfits = owned()
    if #outfits == 0 then
        return
    end
    RemoteEvents.OutfitEvent:FireServer(if player:GetAttribute("OutfitId") then "" else outfits[1])
end)
player:GetAttributeChangedSignal("OwnedOutfits"):Connect(refreshButton)
player:GetAttributeChangedSignal("OutfitId"):Connect(refreshButton)
refreshButton()

-- ---------- sway ----------
-- the skirt's chains: their outward direction in the LowerTorso's space and the thigh that pushes them
local SECTORS = {
    FL = { dir = Vector3.new(-0.62, 0, -0.78).Unit, leg = "LeftUpperLeg", front = true },
    FR = { dir = Vector3.new(0.62, 0, -0.78).Unit, leg = "RightUpperLeg", front = true },
    BL = { dir = Vector3.new(-0.62, 0, 0.78).Unit, leg = "LeftUpperLeg", front = false },
    BR = { dir = Vector3.new(0.62, 0, 0.78).Unit, leg = "RightUpperLeg", front = false },
}
-- each chain bone's share of the swing and its spring (stiffness rad/s, damping ratio)
local CHAIN = { { share = 0.75, w = 13, z = 0.55 }, { share = 0.15, w = 9, z = 0.45 }, { share = 0.1, w = 6, z = 0.4 } }

local states = {} -- [outfit model] = state

local function spring(s, target, w, z, dt)
    local a = w * w * (target - s.x) - 2 * z * w * s.v
    s.v += a * dt
    s.x += s.v * dt
    return s.x
end

local function springVec(s, target, w, z, dt)
    local a = (target - s.x) * (w * w) - s.v * (2 * z * w)
    s.v += a * dt
    s.x += s.v * dt
    return s.x
end

-- turns `bone` by `rotation` (world space, about the bone's own pivot) on top of its rest pose
local function pose(bone, rotation)
    local parent = bone.Parent
    local parentWorld = if parent:IsA("Bone") then parent.TransformedWorldCFrame else parent.CFrame
    local rest = parentWorld * bone.CFrame
    bone.Transform = rest:ToObjectSpace(CFrame.new(rest.Position) * rotation * rest.Rotation)
end

-- finds the outfit's bones; called until it has them, since the pieces and their bones replicate
-- after the outfit itself is tagged
local function collect(state)
    local outfit, character = state.outfit, state.character
    state.chains, state.tassel, state.cuffs = {}, nil, {}
    for _, piece in outfit:GetChildren() do
        local bones = {}
        for _, d in piece:GetDescendants() do
            if d:IsA("Bone") then
                bones[d.Name] = d
            end
        end
        if piece.Name == "Skirt" then
            for name in SECTORS do
                local chain = {}
                for k = 1, 3 do
                    chain[k] = { bone = bones["Skirt" .. name .. k], s = { x = 0, v = 0 } }
                end
                if chain[1].bone then
                    state.chains[name] = chain
                end
            end
        elseif piece.Name == "Belt" and bones.Tassel1 then
            state.tassel = { bones = { bones.Tassel1, bones.Tassel2, bones.Tassel3 }, s = { x = Vector3.zero, v = Vector3.zero } }
        elseif piece.Name == "LeftCuff" or piece.Name == "RightCuff" then
            local rootBone, hemBone = bones[piece.Name .. "Root"], bones[piece.Name .. "Hem"]
            local arm = character:FindFirstChild(if piece.Name == "LeftCuff" then "LeftLowerArm" else "RightLowerArm")
            if rootBone and hemBone and arm then
                table.insert(state.cuffs, { root = rootBone, hem = hemBone, arm = arm, last = arm.Position, s = { x = Vector3.zero, v = Vector3.zero } })
            end
        end
    end
    state.ready = next(state.chains) ~= nil and state.tassel ~= nil and #state.cuffs == 2
end

local function track(outfit)
    -- worn outside the character (see OutfitService), its Character value names the wearer; with
    -- streaming the wearer can arrive after the outfit, leaving the value nil until then
    local link = outfit:WaitForChild("Character", 10)
    while link and not link.Value and outfit.Parent do
        task.wait(0.5)
    end
    if not (link and link.Value) or not CollectionService:HasTag(outfit, OUTFIT_TAG) then
        return
    end
    states[outfit] = { outfit = outfit, link = link, character = link.Value, chains = {}, cuffs = {}, phase = math.random() * 10, lastF = 0, ready = false }
end

local function untrack(outfit)
    states[outfit] = nil
end

CollectionService:GetInstanceAddedSignal(OUTFIT_TAG):Connect(function(outfit)
    task.spawn(track, outfit)
end)
CollectionService:GetInstanceRemovedSignal(OUTFIT_TAG):Connect(untrack)
for _, outfit in CollectionService:GetTagged(OUTFIT_TAG) do
    task.spawn(track, outfit)
end

local function stepOutfit(state, dt, now)
    local character = state.character
    local lower = character:FindFirstChild("LowerTorso")
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    if not (lower and rootPart) then
        return
    end
    local frame = lower.CFrame
    local velocity = frame:VectorToObjectSpace(rootPart.AssemblyLinearVelocity)
    local forward, sideways, upward = -velocity.Z, velocity.X, velocity.Y
    local fall = math.clamp(-upward * 0.012, 0, 0.5)

    for name, chain in state.chains do
        local sector = SECTORS[name]
        local leg = character:FindFirstChild(sector.leg)
        local push = 0
        if leg then
            local down = frame:VectorToObjectSpace(-leg.CFrame.UpVector)
            local pitch = math.atan2(-down.Z, -down.Y)          -- positive as the leg swings forward
            push = 0.85 * math.max(0, if sector.front then pitch else -pitch)
        end
        local trail = math.clamp((if sector.front then -forward else forward) * 0.02, -0.08, 0.45)
            + math.clamp((if sector.dir.X < 0 then sideways else -sideways) * 0.015, -0.05, 0.3)
        local breeze = 0.025 * math.sin(now * 1.3 + state.phase + #name)
        local target = math.clamp(push + trail + fall + breeze, -0.05, 0.95)
        local axis = frame:VectorToWorldSpace(sector.dir:Cross(UP)).Unit
        for k, link in chain do
            local spec = CHAIN[k]
            local angle = spring(link.s, target * spec.share, spec.w, spec.z, dt)
            pose(link.bone, CFrame.fromAxisAngle(axis, angle))
        end
    end

    if state.tassel then
        local accel = (forward - state.lastF) / math.max(dt, 1e-3)
        local target = Vector3.new(math.clamp(sideways * 0.02 + 0.06 * math.sin(now * 1.7 + state.phase), -0.5, 0.5),
            0, math.clamp(-accel * 0.006, 0, 0.6))
        local swing = springVec(state.tassel.s, target, 7, 0.35, dt)
        local rotation = CFrame.fromAxisAngle(frame.XVector, swing.Z) * CFrame.fromAxisAngle(frame.ZVector, swing.X)
        for k, bone in state.tassel.bones do
            pose(bone, if k == 1 then rotation else CFrame.new():Lerp(rotation, 0.4))
        end
    end
    state.lastF = forward

    for _, cuff in state.cuffs do
        local arm = cuff.arm
        local moved = (arm.Position - cuff.last) / math.max(dt, 1e-3)
        cuff.last = arm.Position
        local down = -arm.CFrame.UpVector
        local across = -(moved - down * moved:Dot(down))
        local target = if across.Magnitude > 1e-3 then across.Unit * math.min(0.5, across.Magnitude * 0.03) else Vector3.zero
        local trail = springVec(cuff.s, target, 9, 0.45, dt)
        if trail.Magnitude > 1e-4 then
            local axis = down:Cross(trail.Unit)
            if axis.Magnitude > 1e-4 then
                local rotation = CFrame.fromAxisAngle(axis.Unit, trail.Magnitude)
                pose(cuff.root, CFrame.new():Lerp(rotation, 0.4))
                pose(cuff.hem, CFrame.new():Lerp(rotation, 0.6))
            end
        end
    end
end

RunService.RenderStepped:Connect(function(dt)
    local camera = workspace.CurrentCamera
    if not camera then
        return
    end
    local now = os.clock()
    dt = math.min(dt, 1 / 20)
    for outfit, state in states do
        if state.link.Value and state.link.Value ~= state.character then
            -- the wearer streamed back in as new instances: find their limbs again
            state.character, state.ready = state.link.Value, false
        end
        local rootPart = state.character:FindFirstChild("HumanoidRootPart")
        if not outfit.Parent then
            states[outfit] = nil
        elseif not rootPart then
            continue -- the wearer streamed out or is respawning: the outfit is rebuilt or comes back
        elseif (rootPart.Position - camera.CFrame.Position).Magnitude < SWAY_DISTANCE then
            if not state.ready then
                collect(state)
            end
            if state.ready then
                stepOutfit(state, dt, now)
            end
        end
    end
end)

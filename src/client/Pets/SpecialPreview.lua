-- The Codex's "Watch": a copy of a beast appears in front of the player and performs its special. Only this
-- player sees it: it is built here on the client, and gone when the special ends.
--   SpecialPreview.play(petId, onDone)    false if it can't (one is already playing, no character, or the pet has no special)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))

local AHEAD = 13        -- studs in front of the player
local HOVER = 3.9       -- a pet's root above the ground, where it follows its owner (hip height and FOLLOW_HEIGHT)
local WAIT_FOR_MESHES = 6
local LEAD_IN, LEAD_OUT = 0.35, 0.45

local SpecialPreview = {}
local playing = false

function SpecialPreview.play(petId, onDone)
    local character = Players.LocalPlayer.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if playing or not root or not PetRig.Profiles[petId] then
        return false
    end
    playing = true
    task.spawn(function()
        local started = os.clock()
        while not PetPreload.isReady(petId) and os.clock() - started < WAIT_FOR_MESHES do
            PetPreload.want(petId)
            task.wait(0.1)
        end
        local model, petRoot = PetModels.build(petId)
        local rig = model and PetModels.getRig(model)
        if rig then
            rig.owner = Players.LocalPlayer
        end
        if not (rig and root.Parent) then
            if model then
                model:Destroy()
            end
            playing = false
            onDone(false)
            return
        end

        local look = root.CFrame.LookVector * Vector3.new(1, 0, 1)
        look = if look.Magnitude > 0.01 then look.Unit else Vector3.new(0, 0, -1)
        local spot = root.Position + look * AHEAD
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { character }
        local hit = workspace:Raycast(spot + Vector3.new(0, 30, 0), Vector3.new(0, -90, 0), params)
        local groundY = if hit then hit.Position.Y else root.Position.Y - 3
        local at = Vector3.new(spot.X, groundY + HOVER, spot.Z)
        petRoot.CFrame = CFrame.lookAt(at, Vector3.new(root.Position.X, at.Y, root.Position.Z)) -- pets face -Z: it faces the player
        model.Parent = workspace

        local elapsed, fired = 0, false
        local connection
        connection = RunService.RenderStepped:Connect(function(dt)
            elapsed += dt
            if not fired and elapsed >= LEAD_IN then
                fired = true
                PetRig.nova(rig)
            end
            PetRig.update(rig, dt, { speed = 0, flying = false })
            if elapsed >= LEAD_IN + PetRig.NOVA_TIME + LEAD_OUT then
                connection:Disconnect()
                model:Destroy()
                playing = false
                onDone(true)
            end
        end)
    end)
    return true
end

return SpecialPreview

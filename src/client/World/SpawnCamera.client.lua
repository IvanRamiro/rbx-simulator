-- On joining, the character first appears on the Arrival Plaza and the server moves it to its own pen's spawn pad as soon as the pen
-- is given (WorldService, PenService's PenSpawn). The camera would keep looking the way it did on the plaza; this turns it to look
-- over the player's shoulder at their pen, as it does on every later respawn at the pad.
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local spawnedAt = 0

player.CharacterAdded:Connect(function()
    spawnedAt = os.clock()
end)
if player.Character then
    spawnedAt = os.clock()
end

local function lookAtPen()
    local pen = player:GetAttribute("PenSpawn")
    if typeof(pen) ~= "CFrame" or os.clock() - spawnedAt > 20 then
        return
    end
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root then
        return
    end
    -- wait for the move to arrive (the root within a few studs of the pad), at most 3 seconds
    local deadline = os.clock() + 3
    while (root.Position - pen.Position).Magnitude > 8 and os.clock() < deadline do
        task.wait(0.1)
    end
    if (root.Position - pen.Position).Magnitude > 8 then
        return
    end
    local look = pen.LookVector
    local camera = workspace.CurrentCamera
    camera.CFrame = CFrame.lookAt(root.Position - look * 12 + Vector3.new(0, 5, 0), root.Position + look * 12 + Vector3.new(0, 1.5, 0))
end

player:GetAttributeChangedSignal("PenSpawn"):Connect(lookAtPen)
task.defer(lookAtPen)

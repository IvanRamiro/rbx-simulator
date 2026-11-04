-- Server checks for ProximityPrompt triggers: the player must be alive and within the prompt's
-- range of its part. The tolerance absorbs the gap between client and server positions.
local MovementGuard = require(script.Parent.Parent:WaitForChild("Security"):WaitForChild("MovementGuard"))

local PromptRules = {}

local DISTANCE_TOLERANCE = 6

function PromptRules.maxDistance(prompt)
    return prompt.MaxActivationDistance + DISTANCE_TOLERANCE
end

function PromptRules.isAliveAndNear(player, part, maxDistance)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 or MovementGuard.isSuspect(player) then
        return false
    end

    return (rootPart.Position - part.Position).Magnitude <= maxDistance
end

return PromptRules

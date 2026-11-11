-- Small helpers shared by the effect modules (BreakthroughEffect, CombatFx, GuardianFx, QinggongFx).
-- (The rest of the kit went with the pet aura layer it served, removed 2026-11-11.)
local AuraKit = {}

-- points: { { time, value, envelope? }, ... }
function AuraKit.numberSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, NumberSequenceKeypoint.new(point[1], point[2], point[3] or 0))
    end
    return NumberSequence.new(keypoints)
end

-- points: { { time, Color3 }, ... }
function AuraKit.colorSequence(points)
    local keypoints = {}
    for _, point in points do
        table.insert(keypoints, ColorSequenceKeypoint.new(point[1], point[2]))
    end
    return ColorSequence.new(keypoints)
end

return AuraKit

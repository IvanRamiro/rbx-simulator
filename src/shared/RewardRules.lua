-- The rules of the daily reward, shared so the window shows exactly what the server will pay
-- (GameConfig.Rewards). A day is a UTC calendar day. Stones scale by SpiritStones.RealmFactor per
-- realm, as weapon and pet prices do, so a full week stays worth about one weapon of the player's realm.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local RewardRules = {}

function RewardRules.today()
    return math.floor(os.time() / 86400)
end

-- day: 1 to #Rewards.Daily; returns its Spirit Stones and minutes of Qi
function RewardRules.daily(day, realmIndex)
    local entry = GameConfig.Rewards.Daily[day]
    local stones = entry.Stones * GameConfig.SpiritStones.RealmFactor ^ ((realmIndex or 1) - 1)
    return math.max(5, Shop.roundNice(stones)), entry.QiMinutes or 0
end

-- the streak day the next claim is: the one after yesterday's claim, or day 1 after a missed day
function RewardRules.nextDay(lastDay, streak)
    if lastDay == RewardRules.today() - 1 then
        return (streak or 0) % #GameConfig.Rewards.Daily + 1
    end
    return 1
end

return RewardRules

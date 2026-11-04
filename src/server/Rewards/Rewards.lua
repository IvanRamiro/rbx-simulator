-- A player's reward state, saved in PlayerData as Rewards: the daily streak (LastDay, Streak),
-- LastSeen (for offline Qi), the codes they've used and whether they took the group reward.
-- RewardService decides what's paid.
local Rewards = {}

local MAX_CODES = 200

local state = {}

function Rewards.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local function whole(value)
        return if typeof(value) == "number" and value == value and value >= 0 then math.floor(value) else 0
    end
    local codes = {}
    if typeof(raw.Codes) == "table" then
        for _, code in raw.Codes do
            if typeof(code) == "string" and #code <= 40 and #codes < MAX_CODES and not table.find(codes, code) then
                table.insert(codes, code)
            end
        end
    end
    return { LastDay = whole(raw.LastDay), Streak = whole(raw.Streak), LastSeen = whole(raw.LastSeen), Codes = codes,
        GroupClaimed = raw.GroupClaimed == true }
end

function Rewards.setupPlayer(player, progress)
    state[player] = Rewards.sanitize(progress and progress.Rewards)
end

function Rewards.get(player)
    return state[player]
end

-- For saving: LastSeen is always now, so a crash loses at most one autosave of offline time.
function Rewards.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    return { LastDay = data.LastDay, Streak = data.Streak, LastSeen = os.time(), Codes = data.Codes,
        GroupClaimed = data.GroupClaimed }
end

function Rewards.removePlayer(player)
    state[player] = nil
end

return Rewards

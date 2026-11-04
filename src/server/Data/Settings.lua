-- A player's settings (GameConfig.Settings): Music and Sound volume (0 to 1) and ReducedEffects.
-- Saved in PlayerData as Settings, mirrored to the player's attributes (SettingMusic, SettingSound,
-- SettingReducedEffects) for their client. They change only that player's own view and sound.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local Settings = {}

local current = {}

local function clean(key, value)
    local default = GameConfig.Settings[key]
    if typeof(default) == "number" then
        if typeof(value) == "number" and value == value then
            return math.round(math.clamp(value, 0, 1) * 10) / 10
        end
    elseif typeof(default) == "boolean" and typeof(value) == "boolean" then
        return value
    end
    return default
end

function Settings.sanitize(raw)
    local result = {}
    for key in GameConfig.Settings do
        result[key] = clean(key, if typeof(raw) == "table" then raw[key] else nil)
    end
    return result
end

function Settings.setupPlayer(player, progress)
    current[player] = Settings.sanitize(progress and progress.Settings)
    for key, value in current[player] do
        player:SetAttribute("Setting" .. key, value)
    end
end

-- Changes one setting; false for an unknown one or a player who isn't set up.
function Settings.set(player, key, value)
    if not current[player] or typeof(key) ~= "string" or GameConfig.Settings[key] == nil then
        return false
    end
    current[player][key] = clean(key, value)
    player:SetAttribute("Setting" .. key, current[player][key])
    return true
end

function Settings.exportData(player)
    return current[player]
end

function Settings.removePlayer(player)
    current[player] = nil
end

return Settings

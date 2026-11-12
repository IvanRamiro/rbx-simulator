-- A player's Spirit Beast Codex, saved in PlayerData as Codex: every beast they have ever owned (Found), the
-- rewards they have taken (Claimed), and the realm each reward was earned in (Earned: { [rewardId] = realm index }). An entry
-- is never lost: selling or fusing the pet leaves it in the book.
--
-- A reward's stones are a weapon's share of the realm it was EARNED in (release audit, 2026-11-12: paid at the claim's realm,
-- holding claims back to the top realm multiplied them up to ~37,000x and punished players who claimed at once). A reward
-- earned before Earned existed has no entry and pays at the claim's realm, as it always did.
-- CodexRules holds what counts and what it pays; PetService pays it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local Codex = {}

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local state = {} -- [player] = { found = { [petId] = true }, claimed = { [rewardId] = true }, earned = { [rewardId] = realm } }

-- The player's realm now, or nil while their rank isn't loaded (then nothing is recorded: it pays at the claim's realm).
local function realmNow(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return if rank then Shop.realmIndex(rank.Realm) else nil
end

-- Records the realm of every reward that has just become earned.
local function noteEarned(player, data)
    local realm = nil
    for _, reward in CodexRules.Rewards do
        if not data.earned[reward.Id] and not data.claimed[reward.Id] and CodexRules.isEarned(reward, data.found) then
            realm = realm or realmNow(player)
            if not realm then
                return
            end
            data.earned[reward.Id] = realm
        end
    end
end

function Codex.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local found, claimed = {}, {}
    if typeof(raw.Found) == "table" then
        for _, petId in raw.Found do
            if typeof(petId) == "string" and GameConfig.Pets[petId] and not table.find(found, petId) then
                table.insert(found, petId)
            end
        end
    end
    if typeof(raw.Claimed) == "table" then
        for _, saved in raw.Claimed do
            local id = CodexRules.savedId(saved)
            if CodexRules.reward(id) and not table.find(claimed, id) then
                table.insert(claimed, id)
            end
        end
    end
    local earned = {}
    if typeof(raw.Earned) == "table" then
        for id, realm in raw.Earned do
            local reward = CodexRules.reward(id)
            if reward and typeof(realm) == "number" and realm == realm and not table.find(claimed, reward.Id) then
                earned[reward.Id] = math.clamp(math.floor(realm), 1, #GameConfig.WeaponTiers)
            end
        end
    end
    return { Found = found, Claimed = claimed, Earned = earned }
end

function Codex.setupPlayer(player, progress)
    local saved = Codex.sanitize(progress and progress.Codex)
    local data = { found = {}, claimed = {}, earned = table.clone(saved.Earned) }
    for _, petId in saved.Found do
        data.found[petId] = true
    end
    for _, id in saved.Claimed do
        data.claimed[id] = true
    end
    if table.find(GameConfig.Codex.CreatorUserIds, player.UserId) then -- a creator's book holds every beast
        for petId in GameConfig.Pets do
            data.found[petId] = true
        end
    end
    state[player] = data
end

function Codex.removePlayer(player)
    state[player] = nil
end

function Codex.isFound(player, petId)
    local data = state[player]
    return data ~= nil and data.found[petId] == true
end

-- True when this is a new entry.
function Codex.discover(player, petId)
    local data = state[player]
    if not data or not GameConfig.Pets[petId] or data.found[petId] then
        return false
    end
    data.found[petId] = true
    noteEarned(player, data)
    return true
end

function Codex.qiPercent(player)
    local data = state[player]
    return if data then CodexRules.qiPercent(data.claimed) else 0
end

-- Marks a reward taken and returns it and the realm it pays at (where it was earned, else now); nil if it isn't earned, or was
-- taken already.
function Codex.claim(player, rewardId)
    local data = state[player]
    local reward = CodexRules.reward(rewardId)
    if not (data and reward) or data.claimed[reward.Id] or not CodexRules.isEarned(reward, data.found) then
        return nil
    end
    data.claimed[reward.Id] = true
    local realm = data.earned[reward.Id] or Shop.playerRealmIndex(player)
    data.earned[reward.Id] = nil
    return reward, realm
end

local function sorted(set)
    local list = {}
    for key in set do
        table.insert(list, key)
    end
    table.sort(list)
    return list
end

function Codex.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    return { Found = sorted(data.found), Claimed = sorted(data.claimed), Earned = table.clone(data.earned) }
end

-- owned: { [petId] = { Count, Level } }, what they hold now, for the book's pages
function Codex.publish(player, owned)
    local data = Codex.exportData(player)
    if data then
        data.Owned = owned
        RemoteEvents.CodexEvent:FireClient(player, "State", data)
    end
end

return Codex

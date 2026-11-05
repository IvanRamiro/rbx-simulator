-- The Spirit Beast Codex's contents and rewards, from GameConfig.Eggs and GameConfig.Codex, shared so the
-- window shows exactly what the server pays. A reward is claimed once:
--   "Found:<count>"   a milestone: discover that many beasts, for Spirit Stones and a lasting Qi bonus
--   "Set:<eggId>"     a page: discover everything that egg hatches, for Spirit Stones by the rarest beast on it
--
--   CodexRules.Pets, CodexRules.Total    the beasts that count: every pet an egg can hatch, by id
--   CodexRules.Eggs                      the eggs in the order they unlock (each { Id, DisplayName, RequiredRank, Pool, Guardian })
--   CodexRules.Rewards                   every reward, milestones first (each { Id, Kind, Count, EggId, QiPercent })
--   CodexRules.reward(id)                one reward, or nil
--   CodexRules.eggsOf(petId)             the eggs that hatch a pet: { { EggId, Percent } }, best chance first
--   CodexRules.count(found)              how many beasts in a [petId] = true set count toward the Codex
--   CodexRules.progress(reward, found)   how far along it is, and its goal
--   CodexRules.isEarned(reward, found)
--   CodexRules.stones(reward, realmIndex)
--   CodexRules.qiPercent(claimed)        the lasting Qi bonus of a [rewardId] = true set
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local CodexRules = {}

-- ---------- which eggs, in the order they unlock, and who guards them ----------
local guardianOf = {}
for _, guardian in GameConfig.Guardians do
    for _, eggId in guardian.Eggs do
        guardianOf[eggId] = guardian
    end
end

CodexRules.Eggs = {}
for eggId, egg in GameConfig.Eggs do
    table.insert(CodexRules.Eggs, {
        Id = eggId, DisplayName = egg.DisplayName, RequiredRank = egg.RequiredRank, Pool = egg.Pool, Guardian = guardianOf[eggId],
    })
end
local function unlockOrder(egg)
    local rank = Ranks.getRankById(egg.RequiredRank)
    return rank and Ranks.getIndex(rank.Name) or math.huge
end
table.sort(CodexRules.Eggs, function(a, b)
    local x, y = unlockOrder(a), unlockOrder(b)
    if x ~= y then
        return x < y
    end
    return a.Id < b.Id
end)

-- ---------- the beasts ----------
local eggsOfPet = {}
CodexRules.Pets = {}
for _, egg in CodexRules.Eggs do
    local total = 0
    for _, entry in egg.Pool do
        total += entry.Weight
    end
    for _, entry in egg.Pool do
        if not eggsOfPet[entry.PetId] then
            eggsOfPet[entry.PetId] = {}
            table.insert(CodexRules.Pets, entry.PetId)
        end
        table.insert(eggsOfPet[entry.PetId], { EggId = egg.Id, Percent = math.round(entry.Weight / total * 1000) / 10 })
    end
end
for _, list in eggsOfPet do
    table.sort(list, function(a, b)
        return a.Percent > b.Percent
    end)
end
CodexRules.Total = #CodexRules.Pets

function CodexRules.eggsOf(petId)
    return eggsOfPet[petId] or {}
end

function CodexRules.count(found)
    local n = 0
    for _, petId in CodexRules.Pets do
        if found[petId] then
            n += 1
        end
    end
    return n
end

-- ---------- the rewards ----------
CodexRules.Rewards = {}
local byId = {}
local function addReward(reward)
    table.insert(CodexRules.Rewards, reward)
    byId[reward.Id] = reward
end
for _, milestone in GameConfig.Codex.Milestones do
    local count = milestone.Count or CodexRules.Total -- the last has no count: it's all of them
    addReward({ Id = "Found:" .. count, Kind = "Found", Count = count, QiPercent = milestone.QiPercent, WeaponShare = milestone.WeaponShare })
end
for _, egg in CodexRules.Eggs do
    local share = 0
    for _, entry in egg.Pool do
        share = math.max(share, GameConfig.Codex.PageShare[GameConfig.Pets[entry.PetId].Rarity] or 0)
    end
    addReward({ Id = "Set:" .. egg.Id, Kind = "Set", EggId = egg.Id, QiPercent = 0, WeaponShare = share })
end

function CodexRules.reward(id)
    return if typeof(id) == "string" then byId[id] else nil
end

function CodexRules.progress(reward, found)
    if reward.Kind == "Found" then
        return CodexRules.count(found), reward.Count
    end
    local pool = GameConfig.Eggs[reward.EggId].Pool
    local n = 0
    for _, entry in pool do
        if found[entry.PetId] then
            n += 1
        end
    end
    return n, #pool
end

function CodexRules.isEarned(reward, found)
    local have, goal = CodexRules.progress(reward, found)
    return have >= goal
end

function CodexRules.stones(reward, realmIndex)
    local tier = GameConfig.WeaponTiers[math.clamp(realmIndex or 1, 1, #GameConfig.WeaponTiers)]
    return Shop.roundNice(tier.Price * reward.WeaponShare)
end

function CodexRules.qiPercent(claimed)
    local total = 0
    for _, reward in CodexRules.Rewards do
        if claimed[reward.Id] then
            total += reward.QiPercent
        end
    end
    return total
end

return CodexRules

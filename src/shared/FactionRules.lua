-- The three Murim factions (the owner, 2026-11-22): what each is, and who may join. The data is GameConfig.Faction; the server
-- (server/Factions/FactionService) decides everything, the client (client/Factions) only shows it and asks.
--
-- A pledge is for good. It is kept in its own DataStore (GameConfig.Faction.Store, key "U_<UserId>"), set once from any server, and
-- mirrored to the player's attributes:
--   Faction        the faction's id once the player has joined ("Orthodox", "Unorthodox", "Demonic"), else nil
--   FactionReady   true once the server has read the pledge (until then nil means "not known yet", not "none")
--   FactionTrial   the trial's state for a member: "Locked" (below the trial's realm), "Open" (can start), "Running" (the clock runs),
--                  "Passed" (the vault is open), "Done" (they hold the faction's weapon), else nil
--   FactionTrialEnds   the server time the running trial ends (workspace:GetServerTimeNow())
-- There is no way to leave or change a faction: nothing here, on the server or on the client, writes one over another.
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local FactionRules = {
    -- the tag on a faction's representative model (its "Faction" attribute names the faction); the dialog's prompt is on it
    RepTag = "FactionRep",
    -- the tag on each faction's vault (a model; its "Faction" attribute) where the trial's reward is taken
    VaultTag = "FactionVault",
}

local config = GameConfig.Faction

FactionRules.Order = config.Order

function FactionRules.get(id)
    return if typeof(id) == "string" then config.Factions[id] else nil
end

function FactionRules.isFaction(id)
    return FactionRules.get(id) ~= nil
end

local realms = {}
for _, rank in GameConfig.Ranks do
    if not table.find(realms, rank.Realm) then
        table.insert(realms, rank.Realm)
    end
end
assert(table.find(realms, config.JoinRealm), "GameConfig.Faction.JoinRealm is not a realm: " .. config.JoinRealm)
assert(table.find(realms, config.TrialRealm), "GameConfig.Faction.TrialRealm is not a realm: " .. config.TrialRealm)
assert(config.WeaponTier == table.find(realms, config.TrialRealm), "GameConfig.Faction.WeaponTier is not the TrialRealm's place")

-- a rank's realm place (1 = Qi Awakening), by rank name
local function realmOf(rankName)
    local rank = Ranks.getRank(rankName)
    return rank and table.find(realms, rank.Realm) or 1
end

function FactionRules.canJoin(rankName)
    return realmOf(rankName) >= table.find(realms, config.JoinRealm)
end

function FactionRules.canTrial(rankName)
    return realmOf(rankName) >= table.find(realms, config.TrialRealm)
end

function FactionRules.key(userId)
    return config.KeyPrefix .. tostring(userId)
end

-- the faction a weapon id belongs to (a secret weapon), or nil
local weaponFaction = {}
for id, info in config.Factions do
    assert(info.Weapon and info.Weapon.Id and (info.Weapon.Kind == "Sword" or info.Weapon.Kind == "Spear"), "faction " .. id .. " has no weapon")
    assert(GameConfig.Outfits[info.OutfitId] and GameConfig.Outfits[info.OutfitId].Faction == id, "faction " .. id .. "'s outfit is not its own")
    weaponFaction[info.Weapon.Id] = id
end

function FactionRules.weaponFaction(weaponId)
    return weaponFaction[weaponId]
end

-- The player's own faction as the server published it (nil: none, or not known yet: see ready).
function FactionRules.of(player)
    local id = player:GetAttribute("Faction")
    return if FactionRules.get(id) then id else nil
end

function FactionRules.ready(player)
    return player:GetAttribute("FactionReady") == true
end

-- A faction's representatives in the world (every model tagged RepTag with that Faction attribute).
function FactionRules.reps(factionId)
    local found = {}
    for _, model in CollectionService:GetTagged(FactionRules.RepTag) do
        if model:GetAttribute("Faction") == factionId and model:IsDescendantOf(workspace) then
            table.insert(found, model)
        end
    end
    return found
end

return FactionRules

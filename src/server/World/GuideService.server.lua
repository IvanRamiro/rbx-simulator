-- Seren the Guide, on the spawn plaza, opens the game to a new player (the owner, 2026-11-23: "the tutorial must be shown when the player talked to the NPC, don't show
-- the quest if the players aren't talking to the NPC, but you can guide them to talk with the NPC to show how our game works").
-- A new player has not met her: their quests, the quest panel and the first-time tutorial wait, and the client guides them to her (a card, a marker over her and the guide
-- arrow: client/World/GuideController, Quests/GuideArrow). The moment they talk to her (her prompt, the Guide attribute: triggered here, on the server, with the player alive and
-- within reach of her) the setting GuideMet turns true (Data/Settings, saved with the other settings, mirrored as the attribute SettingGuideMet), and from then on the quests run
-- (QuestService), the quest panel shows (QuestController) and the tutorial card teaches cultivating (TutorialController).
-- A player who is already past the first quest, or who has had the tutorial, has met her as far as the game is concerned: it is set for them on joining, silently, so
-- nobody who is already playing is sent back to the start.
-- The client can never set GuideMet itself (SettingsService refuses it): only this does.
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")

local Server = script.Parent.Parent
local Settings = require(Server:WaitForChild("Data"):WaitForChild("Settings"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PromptRules = require(script.Parent:WaitForChild("PromptRules"))

local function met(player)
    return player:GetAttribute("SettingGuideMet") == true
end

-- Once the player's settings and quest step are known: someone already past the start is counted as having met her. Run whenever one of the three arrives, so a returning player
-- is settled the moment their save has loaded (the "Talk to Seren" card never has time to show for them).
local function settle(player)
    local names = { "SettingGuideMet", "SettingTutorialDone", "QuestStep" }
    local function check()
        if player.Parent ~= Players or met(player) then
            return true
        end
        for _, name in names do
            if player:GetAttribute(name) == nil then
                return false
            end
        end
        local step = player:GetAttribute("QuestStep")
        if (typeof(step) == "number" and step > 1) or player:GetAttribute("SettingTutorialDone") == true then
            if Settings.set(player, "GuideMet", true) then
                PlayerData.saveSoon(player)
            end
        end
        return true
    end
    if check() then
        return
    end
    local connections = {}
    local function again()
        if check() then
            for _, connection in connections do
                connection:Disconnect()
            end
        end
    end
    for _, name in names do
        table.insert(connections, player:GetAttributeChangedSignal(name):Connect(again))
    end
end

Players.PlayerAdded:Connect(function(player)
    task.spawn(settle, player)
end)
for _, player in Players:GetPlayers() do
    task.spawn(settle, player)
end

ProximityPromptService.PromptTriggered:Connect(function(prompt, player)
    if not prompt:GetAttribute("Guide") or player:GetAttribute("SettingGuideMet") ~= false then
        return -- (not Seren's prompt, a player whose settings are not known yet, or one who has met her already)
    end
    local part = prompt.Parent
    if not (part and part:IsA("BasePart") and PromptRules.isAliveAndNear(player, part, PromptRules.maxDistance(prompt))) then
        return
    end
    if Settings.set(player, "GuideMet", true) then
        PlayerData.saveSoon(player)
        Analytics.event(player, "GuideMet")
    end
end)

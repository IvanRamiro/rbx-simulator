-- A tag before a player's name in the chat: [VIP] in gold for the VIP pass's owners (shared/PassRules; the server sets
-- "Pass_VIP"). TextChatService allows one OnIncomingMessage per client: this is the game's.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")

local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))

local VIP_TAG = '<font color="#FFCE54"><b>[VIP]</b></font> '

TextChatService.OnIncomingMessage = function(message)
    local source = message.TextSource
    local sender = source and Players:GetPlayerByUserId(source.UserId)
    if sender and PassRules.owns(sender, "VIP") then
        local properties = Instance.new("TextChatMessageProperties")
        properties.PrefixText = VIP_TAG .. message.PrefixText
        return properties
    end
    return nil
end

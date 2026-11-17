-- Tags before a player's name in the chat: [VIP] in gold for the VIP pass's owners (shared/PassRules; the server sets
-- "Pass_VIP"), then the title they wear, in its own colour (the owner, 2026-11-17: "when they talk to public the title that
-- they were wearing will show on the chat [TITLE] [PLAYER NAME]"; the server sets the player's "Title" attribute,
-- TitleService, and shared/TitleRules has its words and colour). TextChatService allows one OnIncomingMessage per client:
-- this is the game's.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")

local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local TitleRules = require(ReplicatedStorage:WaitForChild("TitleRules"))

local VIP_TAG = '<font color="#FFCE54"><b>[VIP]</b></font> '

-- a title's words are the game's own, but escape them anyway so they can never break the chat's rich text
local function escape(text)
    return (text:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"):gsub("'", "&apos;"))
end

local function titleTag(sender)
    local entry = TitleRules.ById[sender:GetAttribute("Title") or ""]
    if not entry or typeof(entry.Text) ~= "string" or entry.Text == "" then
        return ""
    end
    local color = if typeof(entry.Color) == "Color3" then entry.Color:ToHex() else "FFFFFF"
    return '<font color="#' .. color .. '"><b>[' .. escape(entry.Text) .. "]</b></font> "
end

TextChatService.OnIncomingMessage = function(message)
    local source = message.TextSource
    local sender = source and Players:GetPlayerByUserId(source.UserId)
    if not sender then
        return nil
    end
    local tags = (if PassRules.owns(sender, "VIP") then VIP_TAG else "") .. titleTag(sender)
    if tags == "" then
        return nil
    end
    local properties = Instance.new("TextChatMessageProperties")
    properties.PrefixText = tags .. message.PrefixText
    return properties
end

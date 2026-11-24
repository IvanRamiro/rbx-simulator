-- Gifting a pet to someone in the same server (the owner's improvement list, item 19, 2026-11-24: "simple player-to-player gifting"). The sender picks a pet and a player; the
-- receiver sees the offer and accepts or declines; only an accepted offer moves anything. Nothing here is new law: what may be given is the Auction House's rule
-- (AuctionChecks.item: not locked, equipped, in a pen, the last pet, a creator pet, or a Robux beast where trading those isn't allowed), and both players need the Auction House's
-- rank and account age (AuctionRules.canUse) and to be allowed the pet (AuctionRules.canOwn), so a gift can't get round either.
--   GiftEvent, client to server: "Offer", receiver's UserId, pet InstanceId | "Accept" | "Decline"
--   GiftEvent, server to client: to the receiver "Offer", { FromName, Pet = { PetId, Level, Size, Mutation }, Seconds } | "Cancelled", why
--                                to the sender "Sent", receiver's name | "Refused", why | "Accepted" | "Declined" | "Lapsed"
--                                to the receiver "Received", description
-- The move is one step in memory (PetInventory.takeRecord, then restore; if the receiver can't take it the sender gets it straight back), then both are saved at once, the sender first.
-- LIMIT: a crash in the moment between the two saves could lose the pet (never copy it: the sender's save is written without it before the receiver's holds it).
local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local AuctionRules = require(ReplicatedStorage:WaitForChild("AuctionRules"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local GiftRules = require(ReplicatedStorage:WaitForChild("GiftRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Server = script.Parent.Parent
local AuctionChecks = require(Server:WaitForChild("Auction"):WaitForChild("AuctionChecks"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))

local Event = RemoteEvents.GiftEvent
local CONFIG = GameConfig.Gifts

local sent = {}       -- [player] = gifts sent this visit
local offers = {}     -- [receiver] = { From = player, InstanceId, At }
local outgoing = {}   -- [sender] = receiver while their offer is unanswered
local paidOk = {}     -- [player] = whether this player's region allows trading Robux beasts (PolicyService)
local lastRequest = {}

local function checkPolicy(player)
    for try = 1, 3 do
        local ok, info = pcall(PolicyService.GetPolicyInfoForPlayerAsync, PolicyService, player)
        if ok and typeof(info) == "table" then
            return info.IsPaidItemTradingAllowed == true
        end
        if player.Parent ~= Players then
            return false
        end
        task.wait(try)
    end
    return false
end

Players.PlayerAdded:Connect(function(player)
    paidOk[player] = false
    task.spawn(function()
        local ok = checkPolicy(player)
        paidOk[player] = ok
    end)
end)
for _, player in Players:GetPlayers() do
    if paidOk[player] == nil then
        paidOk[player] = false
        task.spawn(function()
            paidOk[player] = checkPolicy(player)
        end)
    end
end

-- why this player can't take this pet, or nil
local function receiverIssue(receiver, pet)
    local can, why = AuctionRules.canUse(Ranks.getPlayerRankName(receiver), receiver.AccountAge)
    if not can then
        return receiver.DisplayName .. " can't trade yet. " .. tostring(why)
    end
    local own, ownWhy = AuctionRules.canOwn(Ranks.getPlayerRankName(receiver), "Pet", pet)
    if not own then
        return receiver.DisplayName .. ": " .. tostring(ownWhy)
    end
    if AuctionRules.isPaid("Pet", pet) and not paidOk[receiver] then
        return AuctionChecks.PaidText
    end
    if PetInventory.isFull(receiver) then
        return receiver.DisplayName .. "'s pet list is full."
    end
    return nil
end

-- why this pet can't be given by this player now, or nil (and the pet's record, from their snapshot)
local function senderIssue(sender, instanceId)
    local can, why = AuctionRules.canUse(Ranks.getPlayerRankName(sender), sender.AccountAge)
    if not can then
        return tostring(why)
    end
    local snapshot = PetInventory.getSnapshot(sender)
    local pets = snapshot and snapshot.Pets or {}
    local pet = nil
    for _, p in pets do
        if p.InstanceId == instanceId then
            pet = p
        end
    end
    local issue = AuctionChecks.item({ kind = "Pet", pet = pet, petCount = #pets, paidOk = paidOk[sender], isCreatorPet = pet ~= nil and PetInventory.isCreatorPet(sender, pet.PetId) })
    return issue, pet
end

local function clear(receiver)
    local offer = receiver and offers[receiver]
    if offer then
        offers[receiver] = nil
        if outgoing[offer.From] == receiver then
            outgoing[offer.From] = nil
        end
    end
    return offer
end

local function expire(receiver, offer)
    if offers[receiver] == offer then
        clear(receiver)
        if offer.From.Parent == Players then
            Event:FireClient(offer.From, "Lapsed")
        end
        if receiver.Parent == Players then
            Event:FireClient(receiver, "Cancelled", "The gift ran out of time.")
        end
    end
end

local function offer(sender, receiverId, instanceId)
    local receiver = if typeof(receiverId) == "number" then Players:GetPlayerByUserId(receiverId) else nil
    if typeof(instanceId) ~= "string" or #instanceId > 64 then
        return
    end
    if not PetInventory.isSetUp(sender) or (receiver and not PetInventory.isSetUp(receiver)) then
        Event:FireClient(sender, "Refused", "Your pets are still loading. Try again in a moment.")
        return
    end
    local petWhy, pet = senderIssue(sender, instanceId)
    if petWhy then
        Event:FireClient(sender, "Refused", petWhy)
        return
    end
    local issue = GiftRules.offerIssue({
        senderId = sender.UserId, receiverId = receiverId, receiverHere = receiver ~= nil and receiver.Parent == Players, sent = sent[sender] or 0,
        senderWaiting = outgoing[sender] ~= nil, receiverWaiting = receiver ~= nil and offers[receiver] ~= nil,
        receiverIssue = if receiver then receiverIssue(receiver, pet) else nil,
    })
    if issue then
        Event:FireClient(sender, "Refused", issue)
        return
    end
    local made = { From = sender, InstanceId = instanceId, At = os.clock() }
    offers[receiver] = made
    outgoing[sender] = receiver
    Event:FireClient(receiver, "Offer", { FromName = sender.DisplayName, Pet = { PetId = pet.PetId, Level = pet.Level, Size = pet.Size, Mutation = pet.Mutation }, Seconds = CONFIG.OfferSeconds })
    Event:FireClient(sender, "Sent", receiver.DisplayName)
    task.delay(CONFIG.OfferSeconds + 1, expire, receiver, made)
end

local function accept(receiver)
    local made = offers[receiver]
    if not made then
        return
    end
    local sender = made.From
    if GiftRules.expired(made, os.clock()) then
        expire(receiver, made)
        return
    end
    clear(receiver)
    -- everything is checked again at the moment of the move: a pet may have been equipped, locked, auctioned or fused since the offer
    if sender.Parent ~= Players then
        Event:FireClient(receiver, "Cancelled", "The sender left.")
        return
    end
    local petWhy, pet = senderIssue(sender, made.InstanceId)
    local why = petWhy or receiverIssue(receiver, pet)
    if why then
        Event:FireClient(sender, "Refused", why)
        Event:FireClient(receiver, "Cancelled", "The gift can't be given now.")
        return
    end
    local record = PetInventory.takeRecord(sender, made.InstanceId)
    if not record then
        Event:FireClient(sender, "Refused", "That pet isn't free any more.")
        Event:FireClient(receiver, "Cancelled", "The gift can't be given now.")
        return
    end
    if not PetInventory.restore(receiver, record) then
        PetInventory.restore(sender, record) -- straight back: nothing is lost
        PetInventory.publish(sender)
        Event:FireClient(sender, "Refused", receiver.DisplayName .. " can't take this pet.")
        Event:FireClient(receiver, "Cancelled", "The gift can't be given now.")
        return
    end
    sent[sender] = (sent[sender] or 0) + 1
    PetInventory.publish(sender)
    PetInventory.publish(receiver)
    Event:FireClient(sender, "Accepted", receiver.DisplayName)
    Event:FireClient(receiver, "Received", GiftRules.describe(record), sender.DisplayName)
    -- both saved now, the sender first (their save no longer holds the pet before the receiver's does)
    task.spawn(function()
        PlayerData.saveConfirmed(sender)
        PlayerData.saveConfirmed(receiver)
    end)
end

Event.OnServerEvent:Connect(function(player, kind, a, b)
    if typeof(kind) ~= "string" then
        return
    end
    local now = os.clock()
    if now - (lastRequest[player] or -math.huge) < CONFIG.AskEvery then
        return
    end
    lastRequest[player] = now
    if kind == "Offer" then
        offer(player, a, b)
    elseif kind == "Accept" then
        accept(player)
    elseif kind == "Decline" then
        local made = clear(player)
        if made and made.From.Parent == Players then
            Event:FireClient(made.From, "Declined")
        end
    end
end)

Players.PlayerRemoving:Connect(function(player)
    -- a gift waiting for them goes; a gift of theirs waiting on someone is withdrawn
    local incoming = clear(player)
    if incoming and incoming.From.Parent == Players then
        Event:FireClient(incoming.From, "Refused", player.DisplayName .. " left.")
    end
    local receiver = outgoing[player]
    if receiver then
        clear(receiver)
        if receiver.Parent == Players then
            Event:FireClient(receiver, "Cancelled", player.DisplayName .. " left.")
        end
    end
    sent[player], paidOk[player], lastRequest[player], outgoing[player] = nil, nil, nil, nil
end)

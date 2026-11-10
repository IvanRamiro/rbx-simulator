-- Who owns which of the Store's game passes (GameConfig.GamePasses; shared/PassRules says what each does). On joining, each
-- pass with a GamePassId is checked with Roblox; a purchase in the Store counts the moment Roblox confirms it. Owning one sets
-- the player's "Pass_<Id>" attribute, which the server's Qi, hatching, equipping and daily reward read through PassRules, and
-- the client's windows show; "PassesChecked" is set once every pass has been checked. The VIP title follows its pass
-- (TitleBook.setPass), and a player found not to own the slots pass has any beasts over 3 unequipped.
--
-- In Studio only, ServerStorage's "StudioTestPasses" attribute (pass ids, comma-separated, or "All") counts those passes as
-- owned, to test them before they exist on Roblox.
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Server = script.Parent.Parent
local PetInventory = require(Server:WaitForChild("Pets"):WaitForChild("PetInventory"))
local TitleBook = require(Server:WaitForChild("Titles"):WaitForChild("TitleBook"))

local CHECK_TRIES = 3
local SET_UP_WAIT = 60 -- seconds to wait for a player's pets and titles to load before applying a pass to them

local byGamePassId = {}
for _, pass in PassRules.List do
    if (pass.GamePassId or 0) > 0 then
        byGamePassId[pass.GamePassId] = pass
    end
end

local function studioPasses()
    if not RunService:IsStudio() then
        return {}
    end
    local value = ServerStorage:GetAttribute("StudioTestPasses")
    local out = {}
    if typeof(value) == "string" then
        for id in string.gmatch(value, "[^,%s]+") do
            out[id] = true
        end
    end
    return out
end

-- Whether Roblox says they own it: true, false, or nil if Roblox could not be asked.
local function ownsOnRoblox(player, gamePassId)
    for try = 1, CHECK_TRIES do
        local ok, owns = pcall(MarketplaceService.UserOwnsGamePassAsync, MarketplaceService, player.UserId, gamePassId)
        if ok then
            return owns
        end
        task.wait(try)
    end
    return nil
end

local function waitUntil(player, isReady)
    local started = os.clock()
    while not isReady(player) and player.Parent == Players and os.clock() - started < SET_UP_WAIT do
        task.wait(0.5)
    end
    return isReady(player) and player.Parent == Players
end

-- What owning (or not owning) a pass does beyond its attribute.
local function apply(player, pass, owned)
    if pass.Title then
        task.spawn(function()
            if waitUntil(player, TitleBook.isSetUp) and TitleBook.setPass(player, pass.Title, owned) then
                TitleBook.publish(player)
            end
        end)
    end
    if pass.ExtraSlots then
        task.spawn(function()
            if waitUntil(player, PetInventory.isSetUp) then
                -- owned: nothing to trim, but the client's limit changed; not owned: beasts over the limit come off
                PetInventory.trimEquipped(player)
                PetInventory.publish(player)
            end
        end)
    end
end

local function setOwned(player, pass, owned)
    player:SetAttribute("Pass_" .. pass.Id, if owned then true else nil)
    apply(player, pass, owned)
end

local function checkPlayer(player)
    local testing = studioPasses()
    for _, pass in PassRules.List do
        local owned
        if testing.All or testing[pass.Id] then
            owned = true
        elseif (pass.GamePassId or 0) > 0 then
            owned = ownsOnRoblox(player, pass.GamePassId)
        else
            owned = false -- not on sale yet: nobody owns it
        end
        if player.Parent ~= Players then
            return
        end
        if owned ~= nil then -- (Roblox could not be asked: leave it as it is rather than take anything away)
            setOwned(player, pass, owned)
        end
    end
    player:SetAttribute("PassesChecked", true)
end

MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, gamePassId, wasPurchased)
    local pass = byGamePassId[gamePassId]
    if wasPurchased and pass and player.Parent == Players and not PassRules.owns(player, pass.Id) then
        setOwned(player, pass, true)
    end
end)

Players.PlayerAdded:Connect(checkPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(checkPlayer, player)
end

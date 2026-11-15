-- The beast pens (the owner, 2026-11-15: "Just 1 pen per player, but the size for pen is upgradable like the steal an egg"). Six Beast
-- Pastures stand on a ring round the World Tree (Workspace.FloatingIslands.Yggdrasil.BeastPastures, built by ServerStorage.WorldBuild.
-- PastureBuilder); each player in the server is given a free one when their pets load, and it is freed when they leave. Their one pen
-- stands there at its level (shared/PenLayout): which pets are in it and its level are saved (PetInventory, PlayerData's Pen and
-- PenLevel) and follow the player to whichever pasture they hold.
--
-- Every client builds every pen's fence and shows its beasts itself (PenController), from ReplicatedStorage.BeastPastures.<n>: a
-- Configuration per pasture, never streamed out, with the attributes
--   Frame        CFrame   the pasture's centre on the ground (PenLayout's frame)
--   Area         string   where it is ("south meadow")
--   OwnerUserId  number   who holds it (0: nobody)
--   OwnerName    string
--   Level        number   the holder's pen level (0 while nobody holds it)
--   Pets         string   the pen's beasts, comma-separated "PetId:Size:Level"
--   Upgraded     number   the server time of the last upgrade (clients celebrate it once)
-- The server does no work per frame. A player's PastureIndex and PastureArea attributes say which pasture is theirs, and PenSpawn
-- (a world CFrame on their pen's spawn pad, facing the pen: Placements/Pastures.lua Spawn) where they spawn (WorldService).
--
-- PenEvent (client -> server), each checked here and in PetInventory, throttled:
--   ("Add", instanceId)       puts one of their pets in the pen: theirs, not equipped, not in it already, the pen not full
--   ("Remove", instanceId)    takes one out
--   ("Upgrade", fromLevel)    raises the pen a level: fromLevel must be its level now (a double press buys once), below the last;
--                             the price (Shop.penPrice) is spent from their Spirit Stones here and nowhere else
-- The answer (server -> client): ("Result", ok, message, kind) with kind "Upgraded" after an upgrade.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local Wallet = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Wallet"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))

local ServerStorage = game:GetService("ServerStorage")

local REQUEST_COOLDOWN = 0.3 -- seconds between a player's pen requests

-- The pen spots: the one table the builder reads too (ServerStorage.WorldBuild.Placements.Pastures). The built pastures in the world
-- add each spot's ground height (their Frame attribute, set on the terrain at build time).
local Spots = require(ServerStorage:WaitForChild("WorldBuild"):WaitForChild("Placements"):WaitForChild("Pastures"))

local folder = Instance.new("Folder")
folder.Name = "BeastPastures"
folder.Parent = ReplicatedStorage

local pastures = {} -- [index] = { model = Model, config = Configuration, owner = Player? }
local function findPastures()
    local islands = workspace:WaitForChild("FloatingIslands", 30)
    local hub = islands and islands:WaitForChild("Yggdrasil", 30)
    local built = hub and hub:WaitForChild("BeastPastures", 10)
    if not built then
        warn("PenService: no Workspace.FloatingIslands.Yggdrasil.BeastPastures (run PastureBuilder.build): pens are saved but not shown")
        return
    end
    for index, spot in Spots do
        local model = built:FindFirstChild("Pasture" .. index)
        local frame = model and model:GetAttribute("Frame")
        if typeof(frame) ~= "CFrame" then
            warn("PenService: pen spot " .. index .. " (" .. spot.Area .. ") isn't built: re-run PastureBuilder.build()")
        else
            local config = Instance.new("Configuration")
            config.Name = tostring(index)
            config:SetAttribute("Frame", frame)
            config:SetAttribute("Area", spot.Area)
            config:SetAttribute("OwnerUserId", 0)
            config:SetAttribute("OwnerName", "")
            config:SetAttribute("Level", 0)
            config:SetAttribute("Pets", "")
            config.Parent = folder
            pastures[index] = { model = model, config = config, owner = nil, spot = spot }
        end
    end
end
findPastures()

local function pastureOf(player)
    for index, pasture in pastures do
        if pasture.owner == player then
            return index, pasture
        end
    end
    return nil, nil
end

-- the owner's board: their name, and their pen's level and room
local function dress(pasture)
    local owner = pasture.owner
    local level = pasture.config:GetAttribute("Level")
    for _, d in pasture.model:GetDescendants() do
        if d:IsA("TextLabel") and d.Name == "OwnerName" then
            d.Text = if owner then owner.DisplayName .. "'s Pen" else "Beast Pasture"
        elseif d:IsA("TextLabel") and d.Name == "Area" then
            d.Text = if owner and level > 0
                then "LEVEL " .. level .. "  ·  " .. PenLayout.capacity(level) .. " BEASTS"
                else string.upper(pasture.config:GetAttribute("Area") or "") .. "  ·  FREE"
        end
    end
end

local function show(player)
    local _, pasture = pastureOf(player)
    if not pasture then
        return
    end
    local pets = PetInventory.penPets(player) or {}
    local entries = {}
    for _, pet in pets do
        table.insert(entries, pet.PetId .. ":" .. pet.Size .. ":" .. pet.Level)
    end
    pasture.config:SetAttribute("Level", PetInventory.penLevel(player) or 1)
    pasture.config:SetAttribute("Pets", table.concat(entries, ","))
    dress(pasture)
end
PetInventory.onPublish = show

local function assign(player)
    if pastureOf(player) or player.Parent ~= Players then
        return
    end
    for index = 1, #pastures do
        local pasture = pastures[index]
        if pasture and not pasture.owner then
            pasture.owner = player
            pasture.config:SetAttribute("OwnerUserId", player.UserId)
            pasture.config:SetAttribute("OwnerName", player.DisplayName)
            player:SetAttribute("PastureIndex", index)
            player:SetAttribute("PastureArea", pasture.config:GetAttribute("Area"))
            -- where this player spawns: on their pen's spawn pad, facing the pen (the hub's redesign, 2026-11-15). WorldService reads
            -- PenSpawn (a world CFrame) to make the pasture's SpawnLocation theirs and to bring them back there after a fall
            local spawn = pasture.spot.Spawn
            player:SetAttribute("PenSpawn", if typeof(spawn) == "Vector3"
                then pasture.config:GetAttribute("Frame") * CFrame.new(spawn) * CFrame.Angles(0, math.pi, 0) else nil)
            show(player)
            return
        end
    end
    player:SetAttribute("PastureIndex", 0) -- (every pasture is held: their pen is kept, and shown once one frees)
end

local function release(player)
    local _, pasture = pastureOf(player)
    if not pasture then
        return
    end
    pasture.owner = nil
    player:SetAttribute("PenSpawn", nil)
    pasture.config:SetAttribute("OwnerUserId", 0)
    pasture.config:SetAttribute("OwnerName", "")
    pasture.config:SetAttribute("Level", 0)
    pasture.config:SetAttribute("Pets", "")
    dress(pasture)
    -- a player who found every pasture held gets the one just freed
    for _, other in Players:GetPlayers() do
        if other ~= player and other:GetAttribute("PastureIndex") == 0 and PetInventory.isSetUp(other) then
            assign(other)
            break
        end
    end
end

local function setup(player)
    local deadline = os.clock() + 60
    while player.Parent == Players and not PetInventory.isSetUp(player) and os.clock() < deadline do
        task.wait(0.25)
    end
    if player.Parent == Players and PetInventory.isSetUp(player) then
        assign(player)
    end
end

local REFUSALS = {
    NotYours = "That pet isn't yours.",
    Equipped = "Unequip that pet first: an equipped pet walks with you.",
    Full = "Your pen is full. Upgrade it for more room.",
    Already = "That pet is already in your pen.",
    NotIn = "That pet isn't in your pen.",
}

local function upgrade(player, fromLevel)
    local level = PetInventory.penLevel(player)
    if not level or fromLevel ~= level then
        return false, "Your pen changed: try again."
    end
    if level >= PenLayout.Max then
        return false, "Your pen is as big as it gets."
    end
    local price = Shop.penPrice(level + 1)
    if not price or Wallet.exportData(player) == nil then
        return false, "That can't be done right now."
    end
    if not Wallet.spend(player, price, "PenUpgrade", "Level" .. (level + 1)) then
        return false, "You need " .. NumberFormat.compact(price) .. " Spirit Stones."
    end
    if not PetInventory.raisePen(player, level) then -- (can't fail after the checks above; never keep the stones if it did)
        Wallet.add(player, price, "PenUpgradeRefund", "Level" .. (level + 1))
        return false, "That can't be done right now."
    end
    Analytics.event(player, "PenUpgraded", level + 1)
    return true, "Pen upgraded to level " .. (level + 1) .. ": room for " .. PenLayout.capacity(level + 1) .. " beasts!"
end

local lastRequest = {}
RemoteEvents.PenEvent.OnServerEvent:Connect(function(player, action, argument)
    local now = os.clock()
    if now - (lastRequest[player] or 0) < REQUEST_COOLDOWN then
        return
    end
    lastRequest[player] = now
    if not PetInventory.isSetUp(player) then
        return
    end
    local ok, reason, kind
    if action == "Add" or action == "Remove" then
        if typeof(argument) ~= "string" then
            return
        end
        ok, reason = PetInventory.setInPen(player, argument, action == "Add")
        if ok then
            kind = action -- (the client's sound: a beast let in or out)
            local pet = PetInventory.get(player, argument)
            local definition = pet and GameConfig.Pets[pet.PetId]
            local name = if definition then definition.DisplayName else "Your pet"
            reason = if action == "Add" then name .. " is roaming in your pen." else name .. " left the pen."
        else
            reason = REFUSALS[reason] or "That can't be done."
        end
    elseif action == "Upgrade" then
        if typeof(argument) ~= "number" then
            return
        end
        ok, reason = upgrade(player, argument)
        if ok then
            kind = "Upgraded"
            local _, pasture = pastureOf(player)
            if pasture then
                pasture.config:SetAttribute("Upgraded", workspace:GetServerTimeNow())
            end
        end
    else
        return
    end
    if ok then
        PetInventory.publish(player) -- (shows the pen too: PetInventory.onPublish)
        PlayerData.saveSoon(player)
    end
    RemoteEvents.PenEvent:FireClient(player, "Result", ok, reason, kind)
end)

Players.PlayerAdded:Connect(setup)
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    release(player)
end)
for _, player in Players:GetPlayers() do
    task.spawn(setup, player)
end

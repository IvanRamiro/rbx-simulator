-- Downloads a pet's meshes and maps before it's built. A pet is many mesh pieces, fetched only when first
-- used, so without this it appears a piece at a time, or late, on a phone's connection. One pet loads at
-- a time, those wanted now first; one that takes too long counts as ready anyway, so a pet can never go
-- missing. PetCompanionController builds a pet only once it's ready: it must not build one and hold it out of the
-- world meanwhile, because pieces welded to a part don't follow it while they're outside the world.
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetMaps = require(ReplicatedStorage:WaitForChild("PetMaps"))

local PetPreload = {}

local TIMEOUT = 8 -- seconds before a wanted pet counts as ready, fetched or not

local meshFolder = ReplicatedStorage:WaitForChild("PetMeshes", 10)
-- the folder, looked for again while it's missing (it can replicate after the 10 s wait on a slow join)
local function meshes()
    meshFolder = meshFolder or ReplicatedStorage:FindFirstChild("PetMeshes")
    return meshFolder
end
local ready = {}     -- [petId] = true
local wanted = {}    -- [petId] = true: its timeout is running
local queue = {}     -- petIds, first in line first
local working = false

local function work()
    if working then
        return
    end
    working = true
    task.spawn(function()
        while #queue > 0 do
            local petId = table.remove(queue, 1)
            if not ready[petId] then
                local imported = meshes() and meshFolder:FindFirstChild(petId, true)
                -- and its colour map as a plain image too: portraits paint it on as a texture (UI/Portraits), a fetch of its own,
                -- and without it a portrait showed the beast grey for its first seconds (2026-11-12)
                local list = {}
                if imported then
                    table.insert(list, imported)
                end
                local map = PetMaps[petId]
                if type(map) == "table" then -- one map per piece (shared/PetMaps)
                    for _, id in map do
                        table.insert(list, id)
                    end
                elseif map then
                    table.insert(list, map)
                end
                if #list > 0 then
                    pcall(function()
                        ContentProvider:PreloadAsync(list)
                    end)
                end
                ready[petId] = true
            end
        end
        working = false
    end)
end

function PetPreload.isReady(petId)
    return ready[petId] == true
end

-- Fetches a pet in the background (the ones a player owns, for when they're wanted).
function PetPreload.soon(petId)
    if not ready[petId] and not table.find(queue, petId) then
        table.insert(queue, petId)
        work()
    end
end

-- A pet to be shown: ahead of anything fetched only for later, and ready within TIMEOUT whatever happens.
function PetPreload.want(petId)
    if ready[petId] or wanted[petId] then
        return
    end
    wanted[petId] = true
    task.delay(TIMEOUT, function()
        ready[petId] = true
    end)
    local index = table.find(queue, petId)
    if index then
        table.remove(queue, index)
    end
    table.insert(queue, 1, petId)
    work()
end

return PetPreload

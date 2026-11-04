-- Downloads a pet's meshes and maps before it's built. A pet is many mesh pieces, fetched only when first
-- used, so without this it appears a piece at a time, or late, on a phone's connection. One pet loads at
-- a time, those wanted now first; one that takes too long counts as ready anyway, so a pet can never go
-- missing. PetCompanionController builds a pet only once it's ready: it must not build one and hold it out of the
-- world meanwhile, because pieces welded to a part don't follow it while they're outside the world.
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetPreload = {}

local TIMEOUT = 8 -- seconds before a wanted pet counts as ready, fetched or not

local meshFolder = ReplicatedStorage:WaitForChild("PetMeshes", 10)
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
                local imported = meshFolder and meshFolder:FindFirstChild(petId, true)
                if imported then
                    pcall(function()
                        ContentProvider:PreloadAsync({ imported })
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

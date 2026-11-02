-- Runtime facts about the floating-island world. The islands themselves are built in Studio
-- (src/worldbuild) and saved in the place under Workspace.FloatingIslands; centres and radii
-- match tools/blender/world/layout.py.
local WorldConfig = {
    FolderName = "FloatingIslands",
    StartIsland = "Yggdrasil",

    Islands = {
        Yggdrasil = { Centre = Vector3.new(0, 200, 0), Radius = 250 },
        JadeGrove = { Centre = Vector3.new(-302, 200, -410), Radius = 80, Turns = 3 },
        EmberPeak = { Centre = Vector3.new(-150, 200, -606), Radius = 75, Turns = 1 },
        MoonlitIsle = { Centre = Vector3.new(180, 200, -742), Radius = 60, Turns = 0 },
        OriginAbyss = { Centre = Vector3.new(572, 200, -784), Radius = 85, Turns = 1 },
    },

    -- Yggdrasil's spawn slots (FloatingIslands.Yggdrasil.SpawnSlots): each player in the server
    -- holds one, its ring lit and their name cut into its stone
    SpawnSlots = {
        FolderName = "SpawnSlots",
        TakenColor = Color3.fromRGB(255, 180, 50),
        VacantColor = Color3.fromRGB(70, 96, 100),
        VacantTitle = "Unclaimed",
        VacantSubtitle = "A spawn slot",
    },

    -- the Ascension Stele (FloatingIslands.Yggdrasil.Leaderboard): the most Qi across every server
    Leaderboard = {
        FolderName = "Leaderboard",
        StoreName = "QiLeaderboard",  -- an OrderedDataStore: UserId -> whole Qi
        RefreshEvery = 60,           -- seconds between reads of the top entries
        WriteEvery = 120,            -- seconds between writes of a player's Qi (and once as they leave)
    },

    -- touching a part with this tag (Ember Peak's lava) returns a player to their island's checkpoint
    HazardTag = "LavaHazard",

    Safety = {
        CheckInterval = 0.25,
        -- studs below a player's last island before they return to its checkpoint: below the Root of
        -- the Island's cradle (86.5 under Yggdrasil's ground, the deepest place players stand) and
        -- above the PDS kit under Yggdrasil (its top 130.5 under), so a fall never strands anyone on it
        FallDepth = 110,
    },

    Lighting = {
        ClockTime = 14.5,
        Brightness = 2.2,
        Ambient = Color3.fromRGB(60, 70, 90),
        OutdoorAmbient = Color3.fromRGB(130, 140, 165),
        Atmosphere = {
            Density = 0.32,
            Offset = 0.2,
            Color = Color3.fromRGB(199, 220, 240),
            Decay = Color3.fromRGB(106, 132, 170),
            Glare = 0.15,
            Haze = 1.2,
        },
    },
}

-- An island's frame: its centre, turned by its quarter turns (each adds 90 degrees of bearing).
-- Island-local positions (as authored, e.g. a guardian's lair) go through it into the world.
function WorldConfig.frame(islandName)
    local island = WorldConfig.Islands[islandName]
    return CFrame.new(island.Centre) * CFrame.Angles(0, -(island.Turns or 0) * math.pi / 2, 0)
end

return WorldConfig

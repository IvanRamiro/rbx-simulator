-- Runtime facts about the floating-island world. The islands themselves are built in Studio
-- (src/worldbuild) and saved in the place under Workspace.FloatingIslands; centres and radii
-- match tools/blender/world/layout.py.
local WorldConfig = {
    FolderName = "FloatingIslands",
    StartIsland = "StartingIsland",

    Islands = {
        StartingIsland = { Centre = Vector3.new(0, 200, 0), Radius = 95 },
        JadeGrove = { Centre = Vector3.new(330, 206, -70), Radius = 80 },
        EmberPeak = { Centre = Vector3.new(-318, 222, 262), Radius = 75 },
        MoonlitIsle = { Centre = Vector3.new(80, 392, -330), Radius = 60 },
        OriginAbyss = { Centre = Vector3.new(-560, 95, -540), Radius = 85 },
    },

    -- parts tagged with this (Ember Peak's lava lake and river) send whoever touches them back
    -- to their island's checkpoint
    HazardTag = "LavaHazard",

    Safety = {
        CheckInterval = 0.25,
        -- a player this far below the island they last stood on is returned to its checkpoint
        -- (deep enough for the Root of the Island climb, about 90 studs below the surface)
        FallDepth = 160,
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

return WorldConfig
